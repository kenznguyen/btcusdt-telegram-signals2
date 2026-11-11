"""Read the same closed-candle window used by the common paper API."""

import argparse
import time

from freqai_bridge.exporter import write_artifact
from market_data.store import INTERVAL_MS, read_window
from pipeline.values import stamp


def canonical_context(database, now_ms=None, bars=2):
    now = stamp(time.time_ns() // 1_000_000 if now_ms is None else now_ms)
    if type(bars) is not int or not 1 <= bars <= 32:
        raise ValueError("Canonical context must contain 1 to 32 bars")
    step = INTERVAL_MS["15m"]
    end = now // step * step
    window = read_window(database, "BTCUSDT", "15m", end-bars*step, end, as_of_ms=None)
    if not window["coverage"]["complete"]:
        raise ValueError("Canonical inference window contains gaps")
    if any(candle["availableAtMs"] > now for candle in window["candles"]):
        raise ValueError("Canonical inference data is not yet available")
    return window


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", required=True)
    parser.add_argument("--output", default=".data/canonical-window.json")
    parser.add_argument("--bars", type=int, default=2)
    args = parser.parse_args()
    try:
        window = canonical_context(args.db, bars=args.bars)
        write_artifact(args.output, window)
    except (OSError, ValueError) as error:
        parser.exit(1, f"Canonical context unavailable ({type(error).__name__}).\n")
    print(window["datasetVersion"])


if __name__ == "__main__":
    main()
