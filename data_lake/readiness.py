"""Read-only storage readiness and separate current-data freshness checks."""

import argparse
import json
import os
import sqlite3
import time

from market_data.archive import read_snapshots
from market_data.store import INTERVAL_MS, MAX_TIMESTAMP, read_window


def check_readiness(database, now_ms=None):
    current = time.time_ns() // 1_000_000 if now_ms is None else now_ms
    if type(current) is not int or not 2 * INTERVAL_MS["1h"] <= current <= MAX_TIMESTAMP:
        raise ValueError("Invalid readiness clock")
    frames = {}
    candles_ready = bool(database)
    for timeframe, step in INTERVAL_MS.items():
        result = {"expected": 2, "returned": None, "complete": False,
                  "latestCloseTimeMs": None, "latestAvailableAtMs": None}
        if database:
            try:
                end = current // step * step
                window = read_window(database, "BTCUSDT", timeframe, end - 2 * step, end, as_of_ms=current)
                latest = window["candles"][-1] if window["candles"] else None
                result.update(returned=window["coverage"]["returned"], complete=window["coverage"]["complete"],
                              latestCloseTimeMs=latest["closeTimeMs"] if latest else None,
                              latestAvailableAtMs=latest["availableAtMs"] if latest else None)
            except (OSError, sqlite3.Error, ValueError, TypeError, KeyError, OverflowError):
                candles_ready = False
        frames[timeframe] = result
    archive_ready = False
    if database:
        try:
            # This nonempty time range always queries the archive schema, even
            # when there are no observations. No schema initialization occurs.
            read_snapshots(database, current - 60_000, current, current)
            archive_ready = True
        except (OSError, sqlite3.Error, ValueError, TypeError, KeyError, OverflowError):
            pass
    configured = bool(database)
    return {"service": "canonical-data-lake", "ready": candles_ready and archive_ready,
            "checkedAtMs": current,
            "freshData": candles_ready and all(frame["complete"] for frame in frames.values()),
            "checks": {
                "candles": {"ready": candles_ready,
                            "reason": "OK" if candles_ready else "STORE_UNAVAILABLE" if configured else "UNCONFIGURED"},
                "archive": {"ready": archive_ready,
                            "reason": "OK" if archive_ready else "ARCHIVE_UNAVAILABLE" if configured else "UNCONFIGURED"}},
            "timeframes": frames}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", default=os.environ.get("DATA_LAKE_DATABASE_URL") or os.environ.get("MARKET_DATA_DB"),
                        help="Database path; prefer environment configuration for credentials")
    parser.add_argument("--require-fresh", action="store_true", help="Also require the latest two closed bars in both frames")
    args = parser.parse_args(argv)
    result = check_readiness(args.db)
    print(json.dumps(result, allow_nan=False, separators=(",", ":")))
    return 0 if result["ready"] and (result["freshData"] or not args.require_fresh) else 1


if __name__ == "__main__":
    raise SystemExit(main())
