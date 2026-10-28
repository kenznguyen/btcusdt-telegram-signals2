"""Export complete Python replay trace for the genuine synthetic OHLC ENTRY scenario."""
import json
import sys
from pathlib import Path
from android_ohlc_replay import replay_ohlc
from compare_events import validate_event


def main():
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python export_entry_parity_trace.py OUTPUT.json")
    fixture = json.loads(
        (Path(__file__).resolve().parent / "fixtures/android_python_entry_ohlc_v1.json").read_text(encoding="utf-8")
    )
    _, events = replay_ohlc(
        fixture["candles_m15"], fixture["candles_h1"], symbol=fixture["symbol"]
    )
    if not any(event["kind"] == "ENTRY" and event["side"] == "LONG" for event in events):
        raise ValueError("No genuine LONG entry")
    for event in events:
        validate_event(event)
    Path(sys.argv[1]).write_text(json.dumps(events, indent=2, allow_nan=False) + "\n")


if __name__ == "__main__":
    main()
