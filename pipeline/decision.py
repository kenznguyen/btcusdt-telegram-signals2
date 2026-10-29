"""Validate model/data provenance and produce paper-only target-position intents."""

import re
from decimal import localcontext
from market_data.store import Candle, INTERVAL_MS, MAX_CANDLES
from pipeline.values import identity, number, stamp


def _require(condition, reason):
    if not condition:
        raise ValueError(reason)


def _market(value):
    _require(isinstance(value, dict) and value.get("exchange") == "binance" and
             value.get("marketType") == "USDT_PERPETUAL" and value.get("symbol") == "BTCUSDT", "WRONG_MARKET")


def _canonical(window, now_ms):
    _market(window)
    _require(window.get("timeframe") == "15m", "WRONG_TIMEFRAME")
    start, end = stamp(window["startMs"]), stamp(window["endMs"])
    interval = INTERVAL_MS["15m"]
    _require(start % interval == end % interval == 0 and 0 < end-start <= MAX_CANDLES*interval,
             "INVALID_CANDLE_WINDOW")
    rows = window["candles"]
    expected = (end-start)//interval
    _require(isinstance(rows, list) and len(rows) == expected and window.get("coverage") ==
             {"expected": expected, "returned": expected, "complete": True, "gaps": []}, "CANDLE_GAPS")
    as_of = window.get("asOfMs")
    if as_of is not None:
        _require(stamp(as_of) <= now_ms, "FUTURE_CANDLE_QUERY")
    for index, row in enumerate(rows):
        _market(row)
        candle = Candle("15m", row["openTimeMs"], *(row[name] for name in ("open", "high", "low", "close", "volume")),
                        row["availableAtMs"])
        _require(all(row.get(key) == value for key, value in candle.as_dict().items()), "INVALID_CANDLE")
        _require(row["openTimeMs"] == start+index*interval and row["closeTimeMs"] <= now_ms and
                 row["availableAtMs"] <= now_ms and (as_of is None or row["availableAtMs"] <= as_of), "FUTURE_CANDLE")
    _require(0 <= now_ms-end <= 20*60_000, "STALE_CANDLES")
    payload = {key: window[key] for key in ("exchange", "marketType", "symbol", "timeframe", "startMs", "endMs", "asOfMs", "candles")}
    _require(window.get("datasetVersion") == identity("sha256:", payload), "CANDLE_HASH_MISMATCH")
    return rows[-1]


def _intelligence(snapshot, now_ms, max_age):
    _market(snapshot)
    _require(type(snapshot.get("schemaVersion")) is int and snapshot["schemaVersion"] == 1 and
             snapshot.get("quality") == "OBSERVED_ONLY", "INVALID_INTELLIGENCE")
    start, end, available = (stamp(snapshot[key]) for key in ("windowStartMs", "windowEndMs", "availableAtMs"))
    _require(start < end <= available <= now_ms and now_ms-end <= max_age, "STALE_OR_FUTURE_INTELLIGENCE")
    payload = {key: value for key, value in snapshot.items() if key != "snapshotId"}
    _require(snapshot.get("snapshotId") == identity("intelligence:", payload), "INTELLIGENCE_HASH_MISMATCH")
    coverage = snapshot["coverage"]["trades"]
    _require(coverage.get("status") == "OBSERVED" and type(coverage.get("rows")) is int and coverage["rows"] > 0 and
             type(coverage.get("tradeIdGaps")) is int and coverage["tradeIdGaps"] == 0, "TRADE_DATA_INCOMPLETE")
    last_event = stamp(coverage["lastEventAtMs"])
    _require(start <= last_event < end and now_ms-last_event <= max_age, "STALE_TRADE_EVENTS")
    buy, sell, net = number(snapshot["takerBuyQuote"]), number(snapshot["takerSellQuote"]), number(snapshot["netTakerQuote"], signed=True)
    _require(net == buy-sell and buy+sell > 0, "INVALID_TAKER_FLOW")
    return net


def _prediction(prediction, window, latest, now_ms):
    _market(prediction)
    _require(type(prediction.get("schemaVersion")) is int and prediction["schemaVersion"] == 1 and
             prediction.get("timeframe") == "15m", "INVALID_PREDICTION")
    _require(type(prediction.get("doPredict")) is int and prediction["doPredict"] == 1, "PREDICTION_NOT_ACCEPTED")
    _require(prediction.get("datasetVersion") == window["datasetVersion"], "MODEL_DATASET_MISMATCH")
    for name in ("modelVersion", "strategyVersion"):
        _require(isinstance(prediction.get(name), str) and re.fullmatch(r"[A-Za-z0-9_.:-]{1,128}", prediction[name]), "INVALID_MODEL_PROVENANCE")
    opened, closed, available, trained = (stamp(prediction[key]) for key in
        ("candleOpenTimeMs", "candleCloseTimeMs", "availableAtMs", "trainedThroughMs"))
    _require(opened == latest["openTimeMs"] and closed == latest["closeTimeMs"], "PREDICTION_CANDLE_MISMATCH")
    _require(trained <= opened, "MODEL_TRAINING_LOOKAHEAD")
    _require(latest["availableAtMs"] <= available <= now_ms and now_ms-available < 30_000, "STALE_OR_FUTURE_PREDICTION")
    _require(trained <= stamp(prediction["trainingCompletedAtMs"]) <= available, "INVALID_TRAINING_COMPLETION")
    _require(isinstance(prediction["trainingDatasetVersion"], str) and
             re.fullmatch(r"sha256:[0-9a-f]{64}", prediction["trainingDatasetVersion"]), "INVALID_TRAINING_DATASET")
    return number(prediction["predictedReturn"], signed=True)


def _prices(book, now_ms):
    _require(isinstance(book, dict) and book.get("source") == "hummingbot" and
             book.get("connector") == "binance_perpetual" and book.get("symbol") == "BTCUSDT", "WRONG_BOOK_SOURCE")
    _require(0 <= now_ms-stamp(book["observedAtMs"]) <= 30_000, "STALE_OR_FUTURE_BOOK")
    sides = []
    for name in ("bids", "asks"):
        rows = book[name]
        _require(isinstance(rows, list) and 1 <= len(rows) <= 20, "INVALID_BOOK_DEPTH")
        prices = []
        for row in rows:
            price, quantity = number(row["price"]), number(row["quantity"])
            _require(price > 0 and quantity > 0, "INVALID_BOOK_LEVEL")
            prices.append(price)
        _require(len(set(prices)) == len(prices), "DUPLICATE_BOOK_PRICE")
        sides.append(prices)
    bid, ask = max(sides[0]), min(sides[1])
    _require(bid < ask, "CROSSED_BOOK")
    return bid, ask


def evaluate(candle_window, intelligence, prediction, book, now_ms, *, target_base="0.001",
             threshold="0.002", max_input_age_ms=60_000):
    """No order is proposed unless actual model output and observed flow agree.

    Intent timestamps come from source artifacts, not the evaluation attempt.
    A re-priced limit represents a different intent but the same target position.
    Hummingbot retrieval timestamps are usable for this bounded paper simulation
    only; this function makes no claim of exchange sequence verification.
    """
    for name, value in (("CANONICAL_DATA", candle_window), ("INTELLIGENCE", intelligence),
                        ("PREDICTION", prediction), ("ORDER_BOOK", book)):
        if value is None:
            return {"action": "WAIT", "reason": name+"_UNAVAILABLE", "intent": None}
    try:
        # Match the importer precision: valid quote-flow differences can carry
        # more than Decimal's default 28 digits, including after multiplication.
        with localcontext() as context:
            context.prec = 100
            now_ms = stamp(now_ms)
            _require(type(max_input_age_ms) is int and 1 <= max_input_age_ms <= 300_000, "INVALID_MAX_AGE")
            target, cutoff = number(target_base), number(threshold)
            _require(target > 0 and cutoff > 0, "INVALID_STRATEGY_PARAMETERS")
            latest = _canonical(candle_window, now_ms)
            flow = _intelligence(intelligence, now_ms, max_input_age_ms)
            forecast = _prediction(prediction, candle_window, latest, now_ms)
            bid, ask = _prices(book, now_ms)
            _require(abs(forecast) >= cutoff, "PREDICTION_BELOW_THRESHOLD")
            _require(forecast*flow > 0, "FLOW_DIRECTION_MISMATCH")
            buy = forecast > 0
            decided = max(prediction["availableAtMs"], intelligence["availableAtMs"], book["observedAtMs"])
            expiry = min(prediction["availableAtMs"]+30_000, decided+30_000,
                         intelligence["windowEndMs"]+max_input_age_ms)
            _require(now_ms < expiry, "INTENT_EXPIRED")
            intent = {"symbol": "BTCUSDT", "exchange": "binance", "marketType": "USDT_PERPETUAL",
                      "strategyVersion": prediction["strategyVersion"], "modelVersion": prediction["modelVersion"],
                      "datasetVersion": candle_window["datasetVersion"], "targetPositionBase": str(target if buy else -target),
                      "limitPrice": str(ask if buy else bid), "decisionAtMs": decided, "validUntilMs": expiry,
                      "inputSnapshotId": intelligence["snapshotId"], "mode": "PAPER"}
            intent["intentId"] = identity("paper-intent:", {**intent, "candleOpenTimeMs": latest["openTimeMs"]})
            return {"action": "BUY" if buy else "SELL", "reason": "ALIGNED_PAPER_SIGNAL", "intent": intent}
    except (KeyError, TypeError, ValueError, OverflowError, AttributeError) as error:
        # Only fixed validation messages are exposed, never input values or paths.
        reason = str(error) if isinstance(error, ValueError) else "INVALID_INPUT"
        return {"action": "WAIT", "reason": reason or "INVALID_INPUT", "intent": None}
