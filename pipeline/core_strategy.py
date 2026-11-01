"""Native RSI/ADX/Smart-DCA Strategy Core producer.

Rules mirror the signal-only bot.py implementation. It consumes only validated,
closed BTCUSDT candles and never accesses exchange trading endpoints.
"""
import math
import os
from pipeline.values import identity, number, stamp

LEVERAGE = float(os.environ.get("LEVERAGE", "13"))
RSI_LEN = int(os.environ.get("RSI_LENGTH", "14"))
DMI_LEN = int(os.environ.get("DMI_LENGTH", "14"))
ADX_SMOOTH = int(os.environ.get("ADX_SMOOTHING", "14"))
H1_ADX_ENTRY = float(os.environ.get("H1_ADX_ENTRY", "20"))
LONG_RSI_ENTRY = float(os.environ.get("LONG_RSI_ENTRY", "30"))
SHORT_RSI_ENTRY = float(os.environ.get("SHORT_RSI_ENTRY", "70"))
LONG_RSI_TP = float(os.environ.get("LONG_RSI_TP", "76"))
SHORT_RSI_TP = float(os.environ.get("SHORT_RSI_TP", "24"))
TP_ROE = float(os.environ.get("TP_ROE", "5"))
DCA_ROE = float(os.environ.get("DCA_ROE", "-20"))
DCA_ADX = float(os.environ.get("DCA_ADX", "45"))
SHORT_DCA_RSI = float(os.environ.get("SHORT_DCA_RSI", "80"))
LONG_DCA_RSI = float(os.environ.get("LONG_DCA_RSI", "20"))
SOFT_SL_ROE = float(os.environ.get("SOFT_SL_ROE", "-35"))
EMERGENCY_SL_ROE = float(os.environ.get("EMERGENCY_SL_ROE", "-90"))
SOFT_SL_ADX = float(os.environ.get("SOFT_SL_ADX", "35"))
ENTRY_MARGIN_PCT = float(os.environ.get("ENTRY_MARGIN_PCT", "0.50"))
DCA_MARGIN_RATIO = float(os.environ.get("DCA_MARGIN_RATIO", "1.00"))


def _rma(values, length):
    out = [None] * len(values)
    valid = [i for i, value in enumerate(values) if value is not None and math.isfinite(value)]
    if len(valid) < length:
        return out
    seed_index = valid[length - 1]
    previous = sum(values[i] for i in valid[:length]) / length
    out[seed_index] = previous
    started = False
    for index, value in enumerate(values):
        if index == seed_index:
            started = True
        elif started:
            if value is not None and math.isfinite(value):
                previous = (previous * (length - 1) + value) / length
            out[index] = previous
    return out


def indicators(candles):
    rows = list(candles)
    if len(rows) < 2:
        return []
    close = [float(row["close"]) for row in rows]
    high = [float(row["high"]) for row in rows]
    low = [float(row["low"]) for row in rows]
    delta = [None] + [close[i] - close[i - 1] for i in range(1, len(rows))]
    gain = [None if value is None else max(value, 0.0) for value in delta]
    loss = [None if value is None else max(-value, 0.0) for value in delta]
    avg_gain, avg_loss = _rma(gain, RSI_LEN), _rma(loss, RSI_LEN)
    rsi = [None] * len(rows)
    for i, (up, down) in enumerate(zip(avg_gain, avg_loss)):
        if up is None or down is None:
            continue
        if down == 0:
            rsi[i] = 100.0 if up > 0 else 50.0
        else:
            rsi[i] = 100.0 - 100.0 / (1.0 + up / down)

    plus_dm, minus_dm, tr = [0.0], [0.0], [high[0] - low[0]]
    for i in range(1, len(rows)):
        up_move, down_move = high[i] - high[i - 1], low[i - 1] - low[i]
        plus_dm.append(up_move if up_move > down_move and up_move > 0 else 0.0)
        minus_dm.append(down_move if down_move > up_move and down_move > 0 else 0.0)
        tr.append(max(high[i] - low[i], abs(high[i] - close[i - 1]), abs(low[i] - close[i - 1])))
    atr, plus_smoothed, minus_smoothed = _rma(tr, DMI_LEN), _rma(plus_dm, DMI_LEN), _rma(minus_dm, DMI_LEN)
    plus_di, minus_di, dx = [None] * len(rows), [None] * len(rows), [None] * len(rows)
    for i in range(len(rows)):
        if atr[i] is None or atr[i] == 0 or plus_smoothed[i] is None or minus_smoothed[i] is None:
            continue
        plus_di[i] = 100.0 * plus_smoothed[i] / atr[i]
        minus_di[i] = 100.0 * minus_smoothed[i] / atr[i]
        denom = plus_di[i] + minus_di[i]
        if denom:
            dx[i] = 100.0 * abs(plus_di[i] - minus_di[i]) / denom
    adx = _rma(dx, ADX_SMOOTH)
    return [{"rsi": rsi[i], "adx": adx[i], "plus_di": plus_di[i], "minus_di": minus_di[i]}
            for i in range(len(rows))]


def _valid_window(window, timeframe, now_ms):
    if not isinstance(window, dict) or window.get("timeframe") != timeframe:
        return False
    interval = 900_000 if timeframe == "15m" else 3_600_000
    rows = window.get("candles")
    coverage = window.get("coverage", {})
    if not isinstance(rows, list) or len(rows) < 100 or coverage.get("complete") is not True:
        return False
    if coverage.get("expected") != len(rows) or coverage.get("returned") != len(rows):
        return False
    for index, row in enumerate(rows):
        if row.get("isClosed") is not True or row.get("openTimeMs") != rows[0]["openTimeMs"] + index * interval:
            return False
        if stamp(row.get("availableAtMs")) > now_ms or stamp(row.get("closeTimeMs")) > now_ms:
            return False
    return now_ms - stamp(rows[-1]["closeTimeMs"]) <= interval


def _roe(side, average, close):
    if not side or average <= 0:
        return None
    return ((close - average) / average if side == "LONG" else (average - close) / average) * LEVERAGE * 100.0


def _threshold(side, average, abs_roe):
    move = abs(abs_roe) / (100.0 * LEVERAGE)
    return average * (1.0 - move) if side == "LONG" else average * (1.0 + move)


def produce(m15_window, h1_window, paper, strategy_state, book, now_ms, *, initial_capital=100.0,
            max_position_base=0.01):
    now = stamp(now_ms)
    if not _valid_window(m15_window, "15m", now) or not _valid_window(h1_window, "1h", now):
        return {"action": "WAIT", "reason": "CORE_CANDLE_WINDOW_INCOMPLETE", "intent": None,
                "indicators": None}
    m15, h1 = m15_window["candles"], h1_window["candles"]
    m15_values, h1_values = indicators(m15), indicators(h1)
    current, previous = m15_values[-1], m15_values[-2]
    if any(current.get(key) is None for key in ("rsi", "adx")) or previous.get("rsi") is None:
        return {"action": "WAIT", "reason": "CORE_INDICATORS_WARMUP", "intent": None, "indicators": None}
    current_open = stamp(m15[-1]["openTimeMs"])
    h1_bucket = current_open // 3_600_000 * 3_600_000
    eligible = [i for i, row in enumerate(h1) if stamp(row["openTimeMs"]) < h1_bucket]
    if not eligible:
        return {"action": "WAIT", "reason": "CORE_H1_FILTER_UNAVAILABLE", "intent": None, "indicators": None}
    h1_index = eligible[-1]
    trend = h1_values[h1_index]
    if any(trend.get(key) is None for key in ("adx", "plus_di", "minus_di")):
        return {"action": "WAIT", "reason": "CORE_H1_INDICATORS_WARMUP", "intent": None, "indicators": None}

    close, high, low, candle_open = (float(m15[-1][key]) for key in ("close", "high", "low", "open"))
    rsi, prev_rsi, adx = current["rsi"], previous["rsi"], current["adx"]
    h1_plus, h1_minus, h1_adx = trend["plus_di"], trend["minus_di"], trend["adx"]
    position = float(number(paper.get("positionBase", "0"), signed=True))
    average = float(number(paper.get("averageEntryPrice", "0")))
    realized = float(number(paper.get("realizedPnlQuote", "0"), signed=True))
    fees = float(number(paper.get("feesQuote", "0")))
    owner = strategy_state.get("owner")
    dca_used = strategy_state.get("dcaUsed") is True
    side = "LONG" if position > 0 else "SHORT" if position < 0 else None
    reason, action, target, initial_margin = "CORE_NO_ENTRY", "WAIT", position, None

    if side and owner != "STRATEGY_CORE":
        long_signal = h1_plus > h1_minus and h1_adx > H1_ADX_ENTRY and prev_rsi <= LONG_RSI_ENTRY and rsi > LONG_RSI_ENTRY
        short_signal = h1_minus > h1_plus and h1_adx > H1_ADX_ENTRY and prev_rsi >= SHORT_RSI_ENTRY and rsi < SHORT_RSI_ENTRY
        action = "LONG" if long_signal else "SHORT" if short_signal else "WAIT"
        reason = "CORE_SIGNAL_BLOCKED_SHARED_POSITION" if action != "WAIT" else "CORE_POSITION_OWNED_BY_OTHER_STRATEGY"
        if action != "WAIT":
            return {"action":"BUY" if action=="LONG" else "SELL","reason":reason,"intent":None,
                    "indicators":{"rsiM15":rsi,"adxM15":adx,"plusDiH1":h1_plus,
                                  "minusDiH1":h1_minus,"adxH1":h1_adx}}
    elif side:
        roe = _roe(side, average, close)
        emergency = (low <= _threshold(side, average, abs(EMERGENCY_SL_ROE)) if side == "LONG"
                     else high >= _threshold(side, average, abs(EMERGENCY_SL_ROE)))
        reversal = (h1_minus > h1_plus if side == "LONG" else h1_plus > h1_minus) and h1_adx > SOFT_SL_ADX
        previous_candle = m15[-2]
        two_bear = candle_open > close and float(previous_candle["close"]) < float(previous_candle["open"])
        two_bull = close > candle_open and float(previous_candle["close"]) > float(previous_candle["open"])
        soft = (low <= _threshold(side, average, abs(SOFT_SL_ROE)) and reversal and two_bear if side == "LONG"
                else high >= _threshold(side, average, abs(SOFT_SL_ROE)) and reversal and two_bull)
        take_profit = ((side == "LONG" and rsi >= LONG_RSI_TP) or
                       (side == "SHORT" and rsi <= SHORT_RSI_TP)) and roe is not None and roe >= TP_ROE
        if emergency or soft or take_profit:
            action, target = "FLAT", 0
            reason = "EMERGENCY_SL" if emergency else "SOFT_SL" if soft else "TAKE_PROFIT"
        elif not dca_used and roe is not None and roe <= DCA_ROE and adx > DCA_ADX:
            dca_ok = (rsi > LONG_DCA_RSI and rsi > prev_rsi if side == "LONG"
                      else rsi < SHORT_DCA_RSI and rsi < prev_rsi)
            if dca_ok:
                margin = float(number(strategy_state.get("initialMarginQuote", "0")))
                if margin <= 0:
                    reason = "CORE_INITIAL_MARGIN_UNAVAILABLE"
                else:
                    add_qty = margin * DCA_MARGIN_RATIO * LEVERAGE / close
                    target = position + add_qty if side == "LONG" else position - add_qty
                    action, reason = ("LONG" if side == "LONG" else "SHORT"), "DCA"
            else:
                reason = "CORE_DCA_FILTER_NOT_MET"
        else:
            reason = "CORE_POSITION_HOLDING"
    elif owner in (None, "STRATEGY_CORE"):
        long_signal = h1_plus > h1_minus and h1_adx > H1_ADX_ENTRY and prev_rsi <= LONG_RSI_ENTRY and rsi > LONG_RSI_ENTRY
        short_signal = h1_minus > h1_plus and h1_adx > H1_ADX_ENTRY and prev_rsi >= SHORT_RSI_ENTRY and rsi < SHORT_RSI_ENTRY
        if long_signal or short_signal:
            account_equity = float(number(str(initial_capital))) + realized - fees
            initial_margin = account_equity * ENTRY_MARGIN_PCT
            qty = initial_margin * LEVERAGE / close
            if qty > float(number(str(max_position_base))):
                reason = "CORE_ENTRY_EXCEEDS_POSITION_LIMIT"
            else:
                action = "LONG" if long_signal else "SHORT"
                target = qty if long_signal else -qty
                reason = "RSI_ADX_ENTRY"
        else:
            reason = "CORE_NO_ENTRY"

    intent = None
    if action != "WAIT":
        if not isinstance(book, dict):
            return {"action": "BUY" if action=="LONG" else "SELL" if action=="SHORT" else "CLOSE",
                    "reason": "CORE_ORDER_BOOK_UNAVAILABLE", "intent": None,
                    "indicators": {"rsiM15": rsi, "adxM15": adx, "adxH1": h1_adx}}
        try:
            bids = book["bids"]
            asks = book["asks"]
            bid, ask = number(bids[0]["price"]), number(asks[0]["price"])
            limit_price = ask if target > position else bid if target < position else close
            if limit_price <= 0:
                raise ValueError("invalid book")
        except (KeyError, IndexError, TypeError, ValueError):
            return {"action": "WAIT", "reason": "CORE_ORDER_BOOK_INVALID", "intent": None,
                    "indicators": {"rsiM15": rsi, "adxM15": adx, "adxH1": h1_adx}}
        dataset = m15_window["datasetVersion"]
        snapshot_id = identity("core-input:", {"m15": dataset, "h1": h1_window["datasetVersion"],
            "candleOpenTimeMs": current_open, "bookObservedAtMs": book.get("observedAtMs"),
            "book": book, "owner": owner, "dcaUsed": dca_used})
        intent = {"schemaVersion": 1, "source": "STRATEGY_CORE", "exchange": "binance",
            "marketType": "USDT_PERPETUAL", "symbol": "BTCUSDT", "timeframe": "15m",
            "action": action, "reason": reason, "strategyVersion": "rsi-adx-smart-dca-v1",
            "datasetVersion": dataset, "inputSnapshotId": snapshot_id,
            "decisionAtMs": now, "validUntilMs": now + 30_000,
            "targetPositionBase": str(target), "limitPrice": str(limit_price),
            "initialMarginQuote": str(initial_margin) if initial_margin is not None else None,
            "candleOpenTimeMs": current_open}
    return {"action": "BUY" if action == "LONG" else "SELL" if action == "SHORT" else "CLOSE" if action == "FLAT" else "WAIT",
            "reason": reason, "intent": intent,
            "indicators": {"rsiM15": rsi, "adxM15": adx, "plusDiH1": h1_plus,
                           "minusDiH1": h1_minus, "adxH1": h1_adx,
                           "candleOpenTimeMs": current_open, "h1OpenTimeMs": stamp(h1[h1_index]["openTimeMs"])}}
