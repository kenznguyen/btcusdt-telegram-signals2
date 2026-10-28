"""Offline OHLC replay wiring: M15 RSI/DMI/ADX and strictly prior H1 DMI/ADX.

All candle timestamps are UTC open times in milliseconds. No exchange I/O.
Outputs are diagnostic, not parity-certified Freqtrade results.
"""
from android_indicators import indicator_series
from android_h1_alignment import HOUR_MS, aligned_indicators
from android_state_replay import ReplayState, step

M15_MS = 900_000


def _validate(candles, timeframe_ms, label):
    previous = None
    for candle in candles:
        timestamp = candle["timestamp_ms"]
        if type(timestamp) is not int or timestamp < 0 or timestamp % timeframe_ms:
            raise ValueError(f"Invalid {label} candle timestamp")
        if previous is not None and timestamp <= previous:
            raise ValueError(f"{label} timestamps must increase strictly")
        if not candle.get("closed", False):
            raise ValueError(f"Unclosed {label} candle")
        previous = timestamp


def replay_ohlc(m15, h1, initial_state=None, symbol="BTCUSDT"):
    """Replay chronological CLOSED candles, returning final state and event trace.

    A missing preceding M15 candle is rejected rather than silently allowing
    stale previous-RSI/two-candle confirmation to create false signals.
    """
    if not isinstance(symbol, str) or not symbol.strip():
        raise ValueError("Missing symbol")
    _validate(m15, M15_MS, "M15")
    _validate(h1, HOUR_MS, "H1")
    m15_indicators = indicator_series(m15)
    h1_indicators = indicator_series(h1)
    enriched_h1 = [
        {**candle, **point} for candle, point in zip(h1, h1_indicators)
    ]
    state = initial_state if initial_state is not None else ReplayState()
    events = []
    for i in range(1, len(m15)):
        candle = m15[i]
        previous = m15[i - 1]
        if candle["timestamp_ms"] - previous["timestamp_ms"] != M15_MS:
            raise ValueError("Missing M15 candle; refuse discontinuous replay")
        point = m15_indicators[i]
        prior = m15_indicators[i - 1]
        indicators = {
            "rsi": point["rsi"],
            "previous_rsi": prior["rsi"],
            "adx": point["adx"],
            **aligned_indicators(candle["timestamp_ms"], enriched_h1),
        }
        before = state
        state, event = step(state, candle, previous, indicators)
        if event is not None:
            is_exit = event["kind"] in ("TP", "SOFT_SL", "EMERGENCY_SL")
            position = before.position if is_exit else state.position
            if position is None:
                raise ValueError("Missing position snapshot for event")
            events.append({
                "timestamp_ms": candle["timestamp_ms"],
                "symbol": symbol,
                "kind": event["kind"],
                "side": event["side"],
                "price": event["price"],
                "quantity": position["qty"],
                "avg_entry": position["avg_entry"],
                "margin": position["initial_margin"] + position["dca_margin"],
                "roe_pct": event["roe_pct"],
                "balance": state.balance,
                "net_pnl": event.get("net_pnl"),
                "fees": event.get("fees"),
            })
    return state, events
