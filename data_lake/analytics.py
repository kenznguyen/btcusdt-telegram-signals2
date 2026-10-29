"""Causal candle features and descriptive point-in-time flow associations.

All arithmetic uses Decimal, and publication times are never replaced by event
times. No interpolation, prediction, event calendar or continuous tape is inferred.
"""

from bisect import bisect_right
from decimal import Decimal, localcontext

from futures_intelligence.import_collector import validate_snapshot
from market_data.store import Candle, INTERVAL_MS, MAX_CANDLES
from pipeline.values import identity, stamp


FEATURE_VERSION = "causal-v2"
MAX_SNAPSHOTS = 10_000
MAX_SNAPSHOT_AGE_MS = 60_000
CROSS_ANALYSIS_DELAY_MS = 60_000
FEATURE_DEFINITIONS = {
    "return1": "close / previous close - 1; 2 contiguous closes",
    "sma20": "arithmetic mean of the latest 20 contiguous closes",
    "volatility20": "population standard deviation of 20 simple returns; 21 contiguous closes",
    "rsi14": "Wilder RSI: seed with 14 simple price changes, then smooth by 1/14; flat gain/loss is null",
    "plusDi14": "Wilder +DI: 14 true-range/directional-movement intervals; first value on bar 15; zero true range is null",
    "minusDi14": "Wilder -DI: 14 true-range/directional-movement intervals; first value on bar 15; zero true range is null",
    "adx14": "Wilder ADX: mean of 14 consecutive defined DX values, then smooth by 1/14; first value on bar 28; undefined DX resets warmup",
}


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _text(value):
    if value == 0:
        return "0"
    result = format(value, "f")
    return result.rstrip("0").rstrip(".") if "." in result else result


def _validate_window(window):
    """Recheck the public read_window contract, including its content identity."""
    _require(isinstance(window, dict), "Invalid candle window")
    _require(all(key in window for key in ("exchange", "marketType", "symbol", "timeframe", "startMs", "endMs",
                 "asOfMs", "candles", "coverage", "datasetVersion")), "Missing canonical window field")
    _require(window.get("exchange") == "binance" and window.get("marketType") == "USDT_PERPETUAL"
             and window.get("symbol") == "BTCUSDT", "Unsupported candle market")
    timeframe = window.get("timeframe")
    _require(isinstance(timeframe, str) and timeframe in INTERVAL_MS, "Unsupported candle timeframe")
    start, end = stamp(window.get("startMs")), stamp(window.get("endMs"))
    step = INTERVAL_MS[timeframe]
    _require(start % step == end % step == 0 and 0 < end-start <= MAX_CANDLES*step,
             "Invalid candle window bounds")
    as_of = window.get("asOfMs")
    if as_of is not None:
        stamp(as_of)
    rows = window.get("candles")
    _require(isinstance(rows, list) and len(rows) <= (end-start)//step, "Invalid candle row count")
    cursor, gaps = start, []
    for row in rows:
        _require(isinstance(row, dict), "Invalid candle row")
        try:
            candle = Candle(timeframe, row["openTimeMs"],
                            *(row[key] for key in ("open", "high", "low", "close", "volume")),
                            row["availableAtMs"])
        except (KeyError, TypeError) as error:
            raise ValueError("Invalid candle row") from error
        _require(row == candle.as_dict(), "Invalid canonical candle")
        opened = row["openTimeMs"]
        _require(cursor <= opened < end, "Unordered or out-of-window candle")
        _require(as_of is None or row["availableAtMs"] <= as_of, "Candle unavailable at query time")
        if opened > cursor:
            gaps.append({"startMs": cursor, "endMs": opened})
        cursor = row["closeTimeMs"]
    if cursor < end:
        gaps.append({"startMs": cursor, "endMs": end})
    expected_coverage = {"expected": (end-start)//step, "returned": len(rows),
                         "complete": not gaps, "gaps": gaps}
    _require(window.get("coverage") == expected_coverage, "Invalid candle coverage")
    payload = {key: window.get(key) for key in
               ("exchange", "marketType", "symbol", "timeframe", "startMs", "endMs", "asOfMs", "candles")}
    _require(window.get("datasetVersion") == identity("sha256:", payload), "Candle dataset hash mismatch")
    return rows


def _envelope(window):
    return {"schemaVersion": 1, **{key: window[key] for key in
            ("exchange", "marketType", "symbol", "timeframe", "startMs", "endMs", "asOfMs", "datasetVersion")},
            "featureVersion": FEATURE_VERSION, "coverage": window["coverage"]}


def build_features(window):
    """Return seven fixed causal-v2 features for validated, closed candle rows.

    Gaps reset all state. RSI, DMI and ADX retain every observation since the
    latest gap in their dependency sets, including actual availability times.
    """
    candles = _validate_window(window)
    result = {**_envelope(window), "featureDefinitions": dict(FEATURE_DEFINITIONS), "rows": []}
    with localcontext() as context:
        context.prec = 100
        closes, returns, observations = [], [], []
        previous_close_time = None
        segment_available = 0
        average_gain = average_loss = None
        previous_high = previous_low = None
        true_range = plus_movement = minus_movement = Decimal(0)
        dx_seed, adx = [], None
        for candle in candles:
            if candle["openTimeMs"] != previous_close_time:
                closes, returns, observations = [], [], []
                average_gain = average_loss = None
                segment_available = 0
                previous_high = previous_low = None
                true_range = plus_movement = minus_movement = Decimal(0)
                dx_seed, adx = [], None
            close = Decimal(candle["close"])
            high, low = Decimal(candle["high"]), Decimal(candle["low"])
            prior_close = closes[-1] if closes else None
            closes.append(close)
            observations.append(candle["availableAtMs"])
            segment_available = max(segment_available, observations[-1])
            values = dict.fromkeys(FEATURE_DEFINITIONS)
            reasons = {name: "INSUFFICIENT_CONTIGUOUS_CANDLES" for name in values}
            used_at = observations[-1]
            if prior_close is not None:
                change = close-prior_close
                returns.append(close/prior_close-1)
                values["return1"] = returns[-1]
                used_at = max(used_at, observations[-2])
                gain, loss = max(change, Decimal(0)), max(-change, Decimal(0))
                if len(returns) == 14:
                    changes = [right-left for left, right in zip(closes, closes[1:])]
                    average_gain = sum((max(value, Decimal(0)) for value in changes), Decimal(0))/14
                    average_loss = sum((max(-value, Decimal(0)) for value in changes), Decimal(0))/14
                elif len(returns) > 14:
                    average_gain = (average_gain*13+gain)/14
                    average_loss = (average_loss*13+loss)/14
                if average_gain is not None:
                    used_at = max(used_at, segment_available)
                    if average_gain == average_loss == 0:
                        reasons["rsi14"] = "ZERO_GAIN_AND_LOSS"
                    else:
                        values["rsi14"] = (Decimal(100) if average_loss == 0 else
                                           100-100/(1+average_gain/average_loss))
                tr = max(high-low, abs(high-prior_close), abs(low-prior_close))
                up, down = high-previous_high, previous_low-low
                plus = up if up > 0 and up > down else Decimal(0)
                minus = down if down > 0 and down > up else Decimal(0)
                if len(returns) <= 14:
                    true_range += tr
                    plus_movement += plus
                    minus_movement += minus
                else:
                    true_range = true_range-true_range/14+tr
                    plus_movement = plus_movement-plus_movement/14+plus
                    minus_movement = minus_movement-minus_movement/14+minus
                if len(returns) >= 14:
                    used_at = max(used_at, segment_available)
                    dx = None
                    if true_range == 0:
                        for name in ("plusDi14", "minusDi14", "adx14"):
                            reasons[name] = "ZERO_TRUE_RANGE"
                    else:
                        values["plusDi14"] = 100*plus_movement/true_range
                        values["minusDi14"] = 100*minus_movement/true_range
                        total_di = values["plusDi14"]+values["minusDi14"]
                        if total_di == 0:
                            reasons["adx14"] = "ZERO_DIRECTIONAL_MOVEMENT"
                        else:
                            dx = 100*abs(values["plusDi14"]-values["minusDi14"])/total_di
                    if dx is None:
                        dx_seed, adx = [], None
                    elif adx is not None:
                        adx = (adx*13+dx)/14
                    else:
                        dx_seed.append(dx)
                        reasons["adx14"] = "INSUFFICIENT_CONSECUTIVE_DX_VALUES"
                        if len(dx_seed) == 14:
                            adx = sum(dx_seed, Decimal(0))/14
                    values["adx14"] = adx
            if len(closes) >= 20:
                values["sma20"] = sum(closes[-20:], Decimal(0))/20
                used_at = max(used_at, max(observations[-20:]))
            if len(returns) >= 20:
                samples = returns[-20:]
                mean = sum(samples, Decimal(0))/20
                values["volatility20"] = (sum(((value-mean)**2 for value in samples), Decimal(0))/20).sqrt()
                used_at = max(used_at, max(observations[-21:]))
            reasons = {name: reason for name, reason in reasons.items() if values[name] is None}
            result["rows"].append({"candleOpenTimeMs": candle["openTimeMs"],
                                   "candleCloseTimeMs": candle["closeTimeMs"],
                                   "featureAvailableAtMs": used_at,
                                   **{name: None if value is None else _text(value) for name, value in values.items()},
                                   "unavailableReasons": reasons})
            previous_close_time = candle["closeTimeMs"]
            previous_high, previous_low = high, low
    return result


def _correlation(rows, feature, metric):
    pairs = [(Decimal(row[feature]), Decimal(row[metric])) for row in rows
             if row["pointInTimeEligible"] and row[feature] is not None and row[metric] is not None]
    count = len(pairs)
    result = {"value": None, "sampleCount": count, "excludedCount": len(rows)-count,
              "reason": "INSUFFICIENT_SAMPLES"}
    if count < 3:
        return result
    mean_x = sum((x for x, _ in pairs), Decimal(0))/count
    mean_y = sum((y for _, y in pairs), Decimal(0))/count
    centered = [(x-mean_x, y-mean_y) for x, y in pairs]
    sum_x = sum((x*x for x, _ in centered), Decimal(0))
    sum_y = sum((y*y for _, y in centered), Decimal(0))
    if sum_x == 0 or sum_y == 0:
        return {**result, "reason": "ZERO_VARIANCE"}
    covariance = sum((x*y for x, y in centered), Decimal(0))
    value = covariance/(sum_x*sum_y).sqrt()
    return {**result, "value": _text(max(Decimal(-1), min(Decimal(1), value))), "reason": None}


def build_cross_analysis(window, snapshots, *, as_of_ms=None):
    """Describe associations at a fixed clock 60 seconds after each bar closes.

    as_of_ms defaults to window.asOfMs; absent that, it is the latest candle
    close/observation (or window end for an empty window). Callers serving a
    live query should supply their bounded server/query time explicitly.
    """
    features = build_features(window)
    if as_of_ms is None:
        as_of_ms = window["asOfMs"]
    if as_of_ms is None:
        as_of_ms = max([window["endMs"]] + [row["availableAtMs"] for row in window["candles"]])
    stamp(as_of_ms)
    _require(all(row["availableAtMs"] <= as_of_ms for row in window["candles"]),
             "Candle unavailable at analysis time")
    _require(isinstance(snapshots, (list, tuple)) and len(snapshots) <= MAX_SNAPSHOTS,
             "Snapshot query must be bounded")
    reports = [validate_snapshot(snapshot, as_of_ms) for snapshot in snapshots]
    reports.sort(key=lambda item: (item["availableAtMs"], item["windowEndMs"], item["snapshotId"]))
    published = [item["availableAtMs"] for item in reports]
    joined = []
    for feature in features["rows"]:
        closed = feature["candleCloseTimeMs"]
        analysis_at = stamp(closed+CROSS_ANALYSIS_DELAY_MS)
        pending = analysis_at > as_of_ms
        index = bisect_right(published, analysis_at)-1 if not pending else -1
        snapshot = reports[index] if index >= 0 else None
        reason = ("ANALYSIS_TIME_NOT_REACHED" if pending else
                  "SNAPSHOT_NOT_YET_AVAILABLE" if reports else "NO_SNAPSHOT")
        if snapshot is not None:
            trades = snapshot["coverage"]["trades"]
            if not 0 <= analysis_at-snapshot["windowEndMs"] <= MAX_SNAPSHOT_AGE_MS:
                reason = "STALE_SNAPSHOT"
            elif trades["status"] != "OBSERVED":
                reason = "NO_OBSERVED_TRADES"
            elif trades["tradeIdGaps"] != 0:
                reason = "TRADE_ID_GAPS"
            elif not 0 <= analysis_at-trades["lastEventAtMs"] <= MAX_SNAPSHOT_AGE_MS:
                reason = "STALE_TRADE_EVENTS"
            else:
                reason = "MATCHED_OBSERVED_ONLY"
        matched = reason == "MATCHED_OBSERVED_ONLY"
        eligible = matched and feature["featureAvailableAtMs"] <= analysis_at and not pending
        row = {**feature, "analysisAtMs": analysis_at, "snapshotId": snapshot["snapshotId"] if snapshot else None,
               "snapshotAvailableAtMs": snapshot["availableAtMs"] if snapshot else None,
               "snapshotWindowEndMs": snapshot["windowEndMs"] if snapshot else None,
               "lastTradeEventAtMs": snapshot["coverage"]["trades"]["lastEventAtMs"] if snapshot else None,
               "snapshotQuality": snapshot["quality"] if snapshot else None,
               "joinReason": reason, "pointInTimeEligible": eligible,
               "analysisReason": ("ANALYSIS_TIME_NOT_REACHED" if pending else
                                  "FEATURE_NOT_AVAILABLE_AT_ANALYSIS_TIME" if feature["featureAvailableAtMs"] > analysis_at else
                                  None if matched else reason),
               "netTakerQuote": snapshot["netTakerQuote"] if matched else None,
               "fundingRate": snapshot["fundingRate"] if matched else None,
               "fundingAtMs": snapshot["fundingAtMs"] if matched else None,
               "metricReasons": {}}
        for metric in ("netTakerQuote", "fundingRate"):
            if row[metric] is None:
                row["metricReasons"][metric] = (reason if not matched else
                    "FUNDING_"+snapshot["coverage"]["funding"]["status"])
        joined.append(row)
    with localcontext() as context:
        context.prec = 100
        correlations = {"return1VsNetTakerQuote": _correlation(joined, "return1", "netTakerQuote"),
                        "return1VsFundingRate": _correlation(joined, "return1", "fundingRate"),
                        "adx14VsFundingRate": _correlation(joined, "adx14", "fundingRate")}
    return {**_envelope(window), "asOfMs": as_of_ms, "descriptiveOnly": True,
            "alignmentDelayMs": CROSS_ANALYSIS_DELAY_MS,
            "descriptiveNotPrediction": "Associations use observations available 60 seconds after each candle closes; they are not predictions or evidence of causation.",
            "snapshotCount": len(reports), "maximumSnapshotAgeMs": MAX_SNAPSHOT_AGE_MS,
            "rows": joined, "correlations": correlations}
