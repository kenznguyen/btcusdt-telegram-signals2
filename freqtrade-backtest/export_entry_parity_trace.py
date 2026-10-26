"""Export complete Python replay trace for the genuine synthetic OHLC ENTRY scenario."""
import json
import sys
from pathlib import Path
from android_ohlc_replay import replay_ohlc
from compare_events import validate_event


def bar(timestamp, price):
    return {"timestamp_ms": timestamp, "open": float(price),
            "high": float(price + 1), "low": float(price - 1),
            "close": float(price), "volume": 10.0, "closed": True}


def main():
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python export_entry_parity_trace.py OUTPUT.json")
    hour = 3_600_000
    quarter = 900_000
    h1 = [bar(i * hour, 100 + 2 * i) for i in range(65)]
    prices = [250 - i for i in range(45)] + [205 + i for i in range(35)]
    m15 = [bar(60 * hour + i * quarter, price) for i, price in enumerate(prices)]
    _, events = replay_ohlc(m15, h1, symbol="BTCUSDT")
    if not any(event["kind"] == "ENTRY" and event["side"] == "LONG" for event in events):
        raise ValueError("No genuine LONG entry")
    for event in events:
        validate_event(event)
    Path(sys.argv[1]).write_text(json.dumps(events, indent=2, allow_nan=False) + "\n")


if __name__ == "__main__":
    main()
