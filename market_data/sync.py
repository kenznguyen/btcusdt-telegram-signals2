"""Closed Binance USDT-perpetual OHLCV ingestion, with no trading credentials.

Each fetched page commits atomically. Earlier pages survive a later fetch error
so the explicit window can be retried; identical closed candles are idempotent.
CCXT's parsed numbers are converted with str(), without claiming to recover
precision already lost by an upstream float parser.
"""

import argparse
import json
import os
import time

from market_data.store import Candle, INTERVAL_MS, MAX_CANDLES, MAX_TIMESTAMP
from market_data.storage import create_store
from market_data.gateway import LeaseFence, T0WriteGateway


EXCHANGE_SYMBOL = "BTC/USDT:USDT"


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


def sync_window(
    exchange,
    gateway,
    timeframe,
    start_ms,
    end_ms,
    *,
    lease_token,
    lease_clock,
    now_ms=None,
):
    """Fetch closed candles and write each page only through the fenced Gateway.

    Each page commits atomically. Earlier pages survive a later fetch error.
    Observation time is persisted as available_at_ms; lease_clock is evaluated
    independently by the Gateway at transaction admission.
    """
    if not callable(getattr(gateway, "insert_batch", None)):
        raise TypeError("gateway must provide insert_batch()")
    if not isinstance(lease_token, LeaseFence):
        raise TypeError("lease_token must be a LeaseFence")
    if not callable(lease_clock):
        raise TypeError("lease_clock must be a zero-argument callable")

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
    observation_clock = now_ms if now_ms is not None else lambda: time.time_ns() // 1_000_000
    cursor, inserted = start_ms, 0
    while cursor < end_ms:
        limit = min(1000, (end_ms - cursor) // interval)
        page = exchange.fetch_ohlcv(
            EXCHANGE_SYMBOL, timeframe=timeframe, since=cursor,
            limit=limit, params={"endTime": end_ms - 1},
        )
        observed_at = observation_clock()
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
            candles.append(Candle(
                timeframe, opened, *(str(value) for value in row[1:]),
                available_at_ms=observed_at,
            ))
        next_cursor = page[-1][0] + interval
        if next_cursor <= cursor:
            raise ValueError("OHLCV pagination made no progress")
        inserted += gateway.insert_batch(
            candles,
            lease_token=lease_token,
            now_ms=lease_clock,
        )
        cursor = next_cursor
        if len(page) < limit or cursor > closed_through:
            break
    return inserted

def main():
    parser = argparse.ArgumentParser(
        description="Sync closed BTCUSDT perpetual candles through the fenced SQLite Gateway"
    )
    parser.add_argument("--db", default=os.environ.get("MARKET_DATA_DB", ""),
                        help="Existing SQLite canonical database path")
    parser.add_argument("--lease-name", default=os.environ.get(
        "T0_FEEDER_LEASE_NAME", "binance-btcusdt-canonical"))
    parser.add_argument("--lease-owner", default=os.environ.get("T0_FEEDER_OWNER_ID", ""))
    parser.add_argument("--lease-generation", type=int,
                        default=os.environ.get("T0_FEEDER_LEASE_GENERATION"))
    parser.add_argument("--timeframe", choices=tuple(INTERVAL_MS), required=True)
    parser.add_argument("--start-ms", type=int, required=True,
                        help="Inclusive aligned UTC epoch milliseconds")
    parser.add_argument("--end-ms", type=int, required=True,
                        help="Exclusive aligned UTC epoch milliseconds")
    args = parser.parse_args()
    if not args.lease_owner or args.lease_generation is None or args.lease_generation < 1:
        parser.error("an active lease requires T0_FEEDER_OWNER_ID and T0_FEEDER_LEASE_GENERATION")

    try:
        import ccxt
    except ImportError:
        parser.exit(1, "Install requirements-market-data.txt to fetch exchange data.\\n")
    try:
        exchange = ccxt.binanceusdm({"enableRateLimit": True, "timeout": 15_000})
        gateway = T0WriteGateway(args.db)
        reader = create_store("sqlite", sqlite_path=args.db)
        lease_token = LeaseFence(args.lease_name, args.lease_owner, args.lease_generation)
        observation_clock = lambda: time.time_ns() // 1_000_000
        lease_clock = lambda: time.time_ns() // 1_000_000
        count = sync_window(
            exchange, gateway, args.timeframe, args.start_ms, args.end_ms,
            lease_token=lease_token, lease_clock=lease_clock,
            now_ms=observation_clock,
        )
        window = reader.read_window("BTCUSDT", args.timeframe, args.start_ms, args.end_ms)
    except Exception as error:
        parser.exit(1, f"Sync failed ({type(error).__name__}); earlier successful pages remain stored.\\n")
    print(json.dumps({"inserted": count, "datasetVersion": window["datasetVersion"],
                      "coverage": window["coverage"]}, allow_nan=False))

if __name__ == "__main__":
    main()
