"""One central collector pass; schedule this command instead of each consumer downloading."""

import argparse
from contextlib import contextmanager
import json
import os
from pathlib import Path

from market_data.store import INTERVAL_MS, MAX_CANDLES, MAX_TIMESTAMP, is_postgres, open_store, read_window
from market_data.sync import sync_window, validate_market


@contextmanager
def producer_lock(location):
    if is_postgres(location):
        from market_data.postgres import connection
        with connection(location) as database:
            if not database.execute("SELECT pg_try_advisory_xact_lock(6072026)").fetchone()[0]:
                raise ValueError("Another central collector is running")
            yield
    else:
        import fcntl
        with Path(str(location) + ".collector.lock").open("a") as lock:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            try:
                yield
            finally:
                fcntl.flock(lock.fileno(), fcntl.LOCK_UN)


def refresh_once(exchange, location, timeframes=("15m", "1h"), bars=MAX_CANDLES, now_ms=None):
    if (type(bars) is not int or not 1 <= bars <= MAX_CANDLES or not timeframes or
            any(item not in INTERVAL_MS for item in timeframes) or len(set(timeframes)) != len(timeframes)):
        raise ValueError("Use supported unique timeframes and a bounded lookback")
    store = open_store(location)
    results = []
    with producer_lock(location):
        validate_market(exchange)
        server_time = exchange.fetch_time()
        if type(server_time) is not int or not 0 <= server_time <= MAX_TIMESTAMP:
            raise ValueError("Invalid exchange clock")
        for timeframe in timeframes:
            step = INTERVAL_MS[timeframe]
            end = server_time // step * step
            start = max(0, end-bars*step)
            if start == end:
                continue
            window = read_window(location, "BTCUSDT", timeframe, start, end)
            gaps = window["coverage"]["gaps"]
            inserted = 0
            if gaps:
                # Fetch one bounded span, rather than one exchange request per isolated gap.
                inserted = sync_window(exchange, store, timeframe, gaps[0]["startMs"], gaps[-1]["endMs"], now_ms=now_ms)
                window = read_window(location, "BTCUSDT", timeframe, start, end)
            results.append({"timeframe": timeframe, "startMs": start, "endMs": end,
                            "inserted": inserted, "coverage": window["coverage"]})
    return {"symbol": "BTCUSDT", "windows": results}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", default=os.environ.get("DATA_LAKE_DATABASE_URL") or os.environ.get("MARKET_DATA_DB"))
    parser.add_argument("--timeframes", nargs="+", choices=tuple(INTERVAL_MS), default=list(INTERVAL_MS))
    parser.add_argument("--bars", type=int, default=MAX_CANDLES)
    args = parser.parse_args()
    if not args.db:
        parser.error("Set --db or DATA_LAKE_DATABASE_URL")
    try:
        import ccxt
        exchange = ccxt.binanceusdm({"enableRateLimit": True, "timeout": 15_000})
        result = refresh_once(exchange, args.db, args.timeframes, args.bars)
    except KeyboardInterrupt:
        parser.exit(130, "Collector interrupted.\n")
    except Exception:
        parser.exit(1, "Collector unavailable or already running; no replacement data was generated.\n")
    print(json.dumps(result, allow_nan=False, separators=(",", ":")))


if __name__ == "__main__":
    main()
