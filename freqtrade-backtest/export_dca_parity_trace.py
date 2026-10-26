"""Export Python DCA trace for the exact Android GenuineOhlcDcaTest series."""
import json
import sys
from pathlib import Path
from android_indicators import indicator_series
from android_signal_predicates import entry_position
from android_ohlc_replay import replay_ohlc, M15_MS
from android_state_replay import ReplayState
from compare_events import validate_event


def main():
    if len(sys.argv) != 2:
        raise SystemExit("Usage: export_dca_parity_trace.py OUTPUT.json")
    prices = [100.0]
    for i in range(1, 130):
        prices.append(prices[-1] + (0.65 if i % 6 == 5 else -0.45))
    candles = [
        {"timestamp_ms": i * M15_MS, "open": float(price),
         "high": float(price + 0.1), "low": float(price - 0.1),
         "close": float(price), "volume": 10.0, "closed": True}
        for i, price in enumerate(prices)
    ]
    points = indicator_series(candles)
    target = next(
        i for i in range(1, len(candles))
        if points[i]["rsi"] is not None and points[i-1]["rsi"] is not None
        and points[i]["adx"] is not None and points[i]["adx"] > 45
        and points[i]["rsi"] > 20 and points[i]["rsi"] > points[i-1]["rsi"]
    )
    initial = entry_position(100.0, "LONG", candles[target]["close"] / 0.98, 0)
    _, events = replay_ohlc(candles[:target+1], [], ReplayState(100.0, initial))
    if len(events) != 1 or events[0]["kind"] != "DCA":
        raise ValueError("Expected exactly one genuine OHLC DCA")
    for event in events:
        validate_event(event)
    Path(sys.argv[1]).write_text(json.dumps(events, indent=2, allow_nan=False) + "\n")


if __name__ == "__main__":
    main()
