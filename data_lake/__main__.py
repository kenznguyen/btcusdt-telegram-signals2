"""Explicit data-lake initialization, bounded backfill and intelligence archiving."""

import argparse
import json
import os
from pathlib import Path
import time

from market_data.store import INTERVAL_MS, MAX_CANDLES, MAX_TIMESTAMP


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    initialize = commands.add_parser("init", help="Create canonical and intelligence schemas explicitly")
    archive = commands.add_parser("archive-intelligence", help="Archive one validated T1 JSON snapshot")
    backfill = commands.add_parser("backfill", help="Fetch closed candles in bounded, rate-limited pages")
    for command in (initialize, archive, backfill):
        command.add_argument("--db", help="Database path; prefer DATA_LAKE_DATABASE_URL for PostgreSQL credentials")
    archive.add_argument("--input", required=True, help="T1 snapshot JSON file, at most 64 KiB")
    backfill.add_argument("--timeframe", required=True, choices=tuple(INTERVAL_MS))
    backfill.add_argument("--start-ms", type=int, required=True)
    backfill.add_argument("--end-ms", type=int, required=True)
    args = parser.parse_args()
    location = args.db or os.environ.get("DATA_LAKE_DATABASE_URL") or os.environ.get("MARKET_DATA_DB")
    if not location:
        parser.error("Configure DATA_LAKE_DATABASE_URL or MARKET_DATA_DB, or supply --db")
    try:
        if args.command == "init":
            from market_data.store import open_store
            from market_data.archive import init_archive
            open_store(location)
            init_archive(location)
            result = {"initialized": True}
        elif args.command == "archive-intelligence":
            from market_data.archive import archive_snapshot
            with Path(args.input).open("rb") as source:
                raw = source.read(65_537)
            if len(raw) > 65_536:
                raise ValueError("Oversized snapshot")

            def unique(pairs):
                result = {}
                for key, value in pairs:
                    if key in result:
                        raise ValueError("Duplicate JSON field")
                    result[key] = value
                return result

            snapshot = json.loads(raw, object_pairs_hook=unique)
            inserted = archive_snapshot(location, snapshot, time.time_ns() // 1_000_000)
            result = {"inserted": bool(inserted), "snapshotId": snapshot["snapshotId"]}
        else:
            from market_data.store import open_store, read_window
            from market_data.sync import sync_window
            step = INTERVAL_MS[args.timeframe]
            start, end = args.start_ms, args.end_ms
            if not 0 <= start < end <= MAX_TIMESTAMP or start % step or end % step or (end - start) // step > 100_000:
                raise ValueError("Use aligned windows of at most 100000 bars")
            import ccxt
            exchange = ccxt.binanceusdm({"enableRateLimit": True, "timeout": 15_000})
            store = open_store(location)
            inserted, returned, chunks = 0, 0, 0
            cursor = start
            from data_lake.refresh import producer_lock
            with producer_lock(location):
                while cursor < end:
                    boundary = min(end, cursor + MAX_CANDLES * step)
                    inserted += sync_window(exchange, store, args.timeframe, cursor, boundary)
                    returned += read_window(location, "BTCUSDT", args.timeframe, cursor, boundary)["coverage"]["returned"]
                    chunks += 1
                    cursor = boundary
            expected = (end - start) // step
            result = {"inserted": inserted, "chunks": chunks,
                      "coverage": {"expected": expected, "returned": returned, "complete": expected == returned},
                      "availabilityKind": "FIRST_OBSERVED"}
    except KeyboardInterrupt:
        parser.exit(130, "Data-lake command interrupted.\n")
    except Exception:
        parser.exit(1, "Data-lake command failed; check configuration, dependencies and validated inputs.\n")
    print(json.dumps(result, allow_nan=False, separators=(",", ":")))


if __name__ == "__main__":
    main()
