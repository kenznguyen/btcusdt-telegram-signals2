"""Optional PostgreSQL storage preserving the SQLite candle wire contract."""

from contextlib import contextmanager
from decimal import Decimal

from market_data.store import (Candle, EXCHANGE, MARKET_TYPE, PRICE_FIELDS,
                               StoreUnavailable, _render_window, _validate_window)


@contextmanager
def connection(location, *, read_only=False):
    """Bounded transactions; all driver failures have a secret-free message."""
    try:
        import psycopg
    except ImportError:
        raise StoreUnavailable("PostgreSQL driver is unavailable") from None
    try:
        with psycopg.connect(location, connect_timeout=5, autocommit=True) as database:
            database.execute("SET statement_timeout = 5000")
            database.execute("SET lock_timeout = 5000")
            with database.transaction():
                if read_only:
                    database.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
                yield database
    except psycopg.Error:
        raise StoreUnavailable("PostgreSQL storage is unavailable") from None


class PostgresCandleStore:
    def __init__(self, location):
        self.location = location
        with connection(location) as database:
            database.execute("""CREATE TABLE IF NOT EXISTS candles (
                exchange TEXT NOT NULL, market_type TEXT NOT NULL, symbol TEXT NOT NULL,
                timeframe TEXT NOT NULL, open_time_ms BIGINT NOT NULL,
                open NUMERIC NOT NULL, high NUMERIC NOT NULL, low NUMERIC NOT NULL,
                close NUMERIC NOT NULL, volume NUMERIC NOT NULL, available_at_ms BIGINT NOT NULL,
                PRIMARY KEY (exchange, market_type, symbol, timeframe, open_time_ms)
            )""")

    def insert(self, candles):
        batch = list(candles)
        if any(not isinstance(candle, Candle) for candle in batch):
            raise ValueError("Expected validated Candle values")
        inserted = 0
        # A common lock order prevents concurrent multi-row batches deadlocking.
        batch.sort(key=lambda candle: (candle.symbol, candle.timeframe, candle.open_time_ms))
        with connection(self.location) as database:
            for candle in batch:
                key = (EXCHANGE, MARKET_TYPE, candle.symbol, candle.timeframe, candle.open_time_ms)
                prices = tuple(Decimal(getattr(candle, name)) for name in PRICE_FIELDS)
                result = database.execute("""INSERT INTO candles
                    (exchange,market_type,symbol,timeframe,open_time_ms,open,high,low,close,volume,available_at_ms)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    ON CONFLICT (exchange,market_type,symbol,timeframe,open_time_ms) DO NOTHING
                    RETURNING open_time_ms""", key + prices + (candle.available_at_ms,)).fetchone()
                if result is not None:
                    inserted += 1
                    continue
                existing = database.execute("""SELECT open,high,low,close,volume FROM candles
                    WHERE exchange=%s AND market_type=%s AND symbol=%s AND timeframe=%s AND open_time_ms=%s""",
                    key).fetchone()
                if existing != prices:
                    raise ValueError("Conflicting closed candle; history was not overwritten")
        return inserted


def read_window(location, symbol, timeframe, start_ms, end_ms, as_of_ms=None):
    start, end, _ = _validate_window(symbol, timeframe, start_ms, end_ms, as_of_ms)
    with connection(location, read_only=True) as database:
        rows = database.execute("""SELECT timeframe,open_time_ms,open,high,low,close,
                volume,available_at_ms,symbol FROM candles
            WHERE exchange=%s AND market_type=%s AND symbol=%s AND timeframe=%s
                AND open_time_ms>=%s AND open_time_ms<%s
                AND (%s::bigint IS NULL OR available_at_ms<=%s::bigint) ORDER BY open_time_ms""",
            (EXCHANGE, MARKET_TYPE, symbol, timeframe, start, end, as_of_ms, as_of_ms)).fetchall()
        candles = [Candle(row[0], row[1], *(str(value) for value in row[2:7]), row[7], row[8]).as_dict()
                   for row in rows]
    return _render_window(symbol, timeframe, start, end, as_of_ms, candles)
