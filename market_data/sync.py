"""Closed Binance USDT-perpetual OHLCV ingestion, with no trading credentials.

Each fetched page commits atomically. Earlier pages survive a later fetch error
so the explicit window can be retried; identical closed candles are idempotent.
CCXT's parsed numbers are converted with str(), without claiming to recover
precision already lost by an upstream float parser.
"""

import argparse
import json
import os
import re
import time

from market_data.store import Candle, INTERVAL_MS, MAX_CANDLES, MAX_TIMESTAMP
from market_data.storage import create_store


EXCHANGE_SYMBOL = "BTC/USDT:USDT"


def safe_exchange_error_message(error):
    """Expose useful upstream diagnostics while redacting credential material."""
    message = str(error)
    message = re.sub(r"(?i)(https?://)[^/\s@]+@", r"\1[REDACTED]@", message)
    message = re.sub(
        r"(?i)([?&](?:api[-_]?key|secret|signature|token|access_token|authorization|password)=)[^&\s]+",
        r"\1[REDACTED]",
        message,
    )
    message = re.sub(
        r"(?i)\b(authorization|x-mbx-apikey|api[-_]?key|secret|password)\b(\s*[:=]\s*)(?:bearer\s+)?[^\s,;&]+",
        r"\1\2[REDACTED]",
        message,
    )
    message = re.sub(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]+", "Bearer [REDACTED]", message)
    return message[:1000]

def validate_market(exchange):
    if exchange.id != "binanceusdm":
        raise ValueError("Only Binance USD-M futures is supported")
    market = exchange.load_markets().get(EXCHANGE_SYMBOL)
    if not isinstance(market, dict) or any(
        market.get(key) != value
        for key, value in {"symbol": EXCHANGE_SYMBOL, "id": "BTCUSDT", "base": "BTC", "quote": "USDT",
                           "settle": "USDT"}.items()
    ) or any(market.get(key) is not True for key in ("active", "swap", "linear")) or market.get("spot") is not False:
        raise ValueError("BTCUSDT is not an active linear USDT perpetual market")


def sync_window(exchange, store, timeframe, start_ms, end_ms, now_ms=None):
    """Fetch an aligned [start_ms, end_ms) window and return the inserted count.

    Missing rows remain missing. availableAtMs is the local clock immediately
    after the page response, not a reconstructed historical availability time.
    Closing is checked against both the exchange clock at sync start and the
    local observation clock; newly closed bars can wait until the next sync.
    Upstream exceptions propagate; this function never substitutes demo data.
    """
    interval = INTERVAL_MS.get(timeframe) if isinstance(timeframe, str) else None
    if interval is None or any(type(value) is not int or not 0 <= value <= MAX_TIMESTAMP or value % interval
                               for value in (start_ms, end_ms)):
        raise ValueError("Use aligned UTC millisecond timestamps and a supported timeframe")
    if not start_ms < end_ms or (end_ms - start_ms) // interval > MAX_CANDLES:
        raise ValueError("Window must contain between 1 and 2000 candles")
    validate_market(exchange)
    server_time = exchange.fetch_time()
    if type(server_time) is not int or not 0 <= server_time <= MAX_TIMESTAMP:
        raise ValueError("Invalid exchange clock")
    clock = now_ms if now_ms is not None else lambda: time.time_ns() // 1_000_000
    cursor, inserted = start_ms, 0
    while cursor < end_ms:
        limit = min(1000, (end_ms - cursor) // interval)
        page = exchange.fetch_ohlcv(EXCHANGE_SYMBOL, timeframe=timeframe, since=cursor,
                                    limit=limit, params={"endTime": end_ms - 1})
        observed_at = clock()
        if type(observed_at) is not int or not 0 <= observed_at <= MAX_TIMESTAMP:
            raise ValueError("Invalid observation clock")
        closed_through = min(server_time, observed_at)
        if not isinstance(page, (list, tuple)) or len(page) > limit:
            raise ValueError("Invalid OHLCV page")
        if not page:
            break
        previous, candles = None, []
        for row in page:
            if not isinstance(row, (list, tuple)) or len(row) != 6:
                raise ValueError("Invalid OHLCV row")
            opened = row[0]
            if type(opened) is not int or not 0 <= opened <= MAX_TIMESTAMP or opened % interval:
                raise ValueError("Invalid candle open timestamp")
            if previous is not None and opened <= previous:
                raise ValueError("OHLCV page is duplicated or out of order")
            previous = opened
            if not cursor <= opened < end_ms or opened + interval > closed_through:
                continue
            candles.append(Candle(timeframe, opened, *(str(value) for value in row[1:]),
                                  available_at_ms=observed_at))
        next_cursor = page[-1][0] + interval
        if next_cursor <= cursor:
            raise ValueError("OHLCV pagination made no progress")
        inserted += store.insert(candles)
        cursor = next_cursor
        if len(page) < limit or cursor > closed_through:
            break
    return inserted


def main():
    parser = argparse.ArgumentParser(description="Sync closed BTCUSDT perpetual candles into the canonical store")
    parser.add_argument("--backend", choices=("sqlite", "postgres"),
                        default=os.environ.get("MARKET_DATA_BACKEND", "sqlite"),
                        help="Storage backend (default: sqlite or MARKET_DATA_BACKEND)")
    parser.add_argument("--db", default=os.environ.get("MARKET_DATA_DB", ""),
                        help="SQLite database path; required only for SQLite")
    parser.add_argument("--timeframe", choices=tuple(INTERVAL_MS), required=True)
    parser.add_argument("--start-ms", type=int, required=True, help="Inclusive aligned UTC epoch milliseconds")
    parser.add_argument("--end-ms", type=int, required=True, help="Exclusive aligned UTC epoch milliseconds")
    args = parser.parse_args()
    try:
        # Optional dependency: offline API/store/tests can run without installing CCXT.
        import ccxt
    except ImportError:
        parser.exit(1, "Install requirements-market-data.txt to fetch exchange data.\n")
    try:
        exchange = ccxt.binanceusdm({"enableRateLimit": True, "timeout": 15_000})
        store = create_store(
            args.backend,
            sqlite_path=args.db,
            postgres_dsn=os.environ.get("MARKET_DATA_POSTGRES_DSN", ""),
        )
        count = sync_window(exchange, store, args.timeframe, args.start_ms, args.end_ms)
        window = store.read_window("BTCUSDT", args.timeframe, args.start_ms, args.end_ms)
    except Exception as error:
        parser.exit(1, f"Sync failed ({type(error).__name__}): {safe_exchange_error_message(error)}; earlier successful pages remain stored.\n")
    print(json.dumps({"inserted": count, "datasetVersion": window["datasetVersion"],
                      "coverage": window["coverage"]}, allow_nan=False))


if __name__ == "__main__":
    main()
