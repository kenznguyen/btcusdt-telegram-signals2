"""Test-only direct seeding for isolated SQLite fixtures.

Production writes must use the lease-fenced write gateway. This helper is
intentionally kept under a test_ module and is only imported by test suites.
"""
import sqlite3

from market_data.store import EXCHANGE, MARKET_TYPE, Candle


def seed_candles(db_path, candles):
    rows = []
    for candle in candles:
        if not isinstance(candle, Candle):
            raise TypeError("seed_candles accepts validated Candle instances only")
        rows.append((
            EXCHANGE,
            MARKET_TYPE,
            candle.symbol,
            candle.timeframe,
            candle.open_time_ms,
            candle.open,
            candle.high,
            candle.low,
            candle.close,
            candle.volume,
            candle.available_at_ms,
        ))
    from contextlib import closing

    with closing(sqlite3.connect(db_path)) as database:
        with database:
            database.executemany(
                """INSERT INTO candles (
                    exchange, market_type, symbol, timeframe, open_time_ms,
                    open, high, low, close, volume, available_at_ms
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                rows,
            )
