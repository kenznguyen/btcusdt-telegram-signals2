"""Export canonical Python replay trace for shared emergency-exit fixture."""
import json
import sys
from pathlib import Path

from android_ohlc_replay import replay_ohlc
from android_state_replay import ReplayState
from compare_events import validate_event


def main():
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python export_emergency_parity_trace.py OUTPUT.json")
    fixture = json.loads((Path(__file__).parent / "fixtures/android_python_emergency_exit_v1.json").read_text())
    state, events = replay_ohlc(
        fixture["candles_m15"], fixture["candles_h1"],
        ReplayState(fixture["initial_balance"], fixture["initial_position"]),
        symbol=fixture["symbol"])
    if len(events) != 1 or state.position is not None:
        raise ValueError("Emergency fixture must close exactly one position")
    for event in events:
        validate_event(event)
    Path(sys.argv[1]).write_text(json.dumps(events, indent=2, allow_nan=False) + "\n")


if __name__ == "__main__":
    main()
