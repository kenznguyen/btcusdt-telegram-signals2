"""Export canonical Python LONG Take Profit trace from real M15 RSI."""
import json
import sys
from pathlib import Path
from android_signal_predicates import entry_position
from android_ohlc_replay import replay_ohlc, M15_MS
from android_state_replay import ReplayState
from compare_events import validate_event


def main():
    if len(sys.argv) != 2:
        raise SystemExit("Usage: export_tp_parity_trace.py OUTPUT.json")
    candles = [
        {"timestamp_ms": i * M15_MS, "open": 100.0 + 0.25 * i,
         "high": 100.1 + 0.25 * i, "low": 99.9 + 0.25 * i,
         "close": 100.0 + 0.25 * i, "volume": 10.0, "closed": True}
        for i in range(85)
    ]
    initial = entry_position(100.0, "LONG", 100.0, 0)
    state, events = replay_ohlc(candles, [], ReplayState(100.0, initial))
    if len(events) != 1 or events[0]["kind"] != "TP" or state.position is not None:
        raise ValueError("Expected exactly one LONG TP")
    for event in events:
        validate_event(event)
    Path(sys.argv[1]).write_text(json.dumps(events, indent=2, allow_nan=False) + "\n")


if __name__ == "__main__":
    main()
