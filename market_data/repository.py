"""Small repository boundary for the canonical candle contract."""

import os
from decimal import Decimal

from market_data.store import Candle, CandleStore, build_window, read_window, validate_window


class MarketDataUnavailable(RuntimeError):
    """No configured market-data backend or the backend cannot be reached."""


class MarketDataRepositoryError(RuntimeError):
    """A configured backend failed without exposing driver-specific details."""


class SQLiteRepository:
    """Backward-compatible adapter over the existing SQLite store."""

    def __init__(self, db_path):
        if not isinstance(db_path, (str, os.PathLike)) or not os.fspath(db_path):
            raise MarketDataUnavailable("SQLite market-data path is not configured")
        self.db_path = os.fspath(db_path)

    def insert(self, candles):
        return CandleStore(self.db_path).insert(candles)

    def read_window(self, symbol, timeframe, start_ms, end_ms, as_of_ms=None):
        return read_window(self.db_path, symbol, timeframe, start_ms, end_ms, as_of_ms)


class PostgresRepository:
    """PostgreSQL/TimescaleDB adapter; schema creation is an explicit migration."""

    def __init__(self, dsn):
        if not isinstance(dsn, str) or not dsn.strip():
            raise MarketDataUnavailable("PostgreSQL market-data URL is not configured")
        self.dsn = dsn

    def _driver(self):
        try:
            import psycopg
            from psycopg.rows import dict_row
        except ImportError as error:
            raise MarketDataUnavailable("Install the market-data PostgreSQL adapter dependency") from error
        return psycopg, dict_row

    @staticmethod
    def _decimal_text(value):
        number = value if isinstance(value, Decimal) else Decimal(str(value))
        if not number.is_finite():
            raise MarketDataRepositoryError("Stored candle contains a non-finite decimal")
        text = format(number, "f")
        if "." in text:
            text = text.rstrip("0").rstrip(".")
        return "0" if number == 0 else text

    def insert(self, candles):
        batch = list(candles)
        if any(not isinstance(candle, Candle) for candle in batch):
            raise ValueError("Expected validated Candle values")
        psycopg, _ = self._driver()
        inserted = 0
        try:
            with psycopg.connect(self.dsn) as connection:
                with connection.cursor() as cursor:
                    for candle in batch:
                        key = (
                            "binance", "USDT_PERPETUAL", candle.symbol,
                            candle.timeframe, candle.open_time_ms,
                        )
                        prices = tuple(getattr(candle, name) for name in
                                       ("open", "high", "low", "close", "volume"))
                        cursor.execute(
                            """INSERT INTO market_data.candles (
                                exchange, market_type, symbol, timeframe, open_time_ms,
                                open, high, low, close, volume, available_at_ms
                            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                            ON CONFLICT (exchange, market_type, symbol, timeframe, open_time_ms)
                            DO NOTHING RETURNING 1""",
                            key + prices + (candle.available_at_ms,),
                        )
                        if cursor.fetchone() is not None:
                            inserted += 1
                            continue
                        cursor.execute(
                            """SELECT open, high, low, close, volume
                               FROM market_data.candles
                               WHERE exchange=%s AND market_type=%s AND symbol=%s
                                 AND timeframe=%s AND open_time_ms=%s""",
                            key,
                        )
                        existing = cursor.fetchone()
                        if existing is None:
                            raise MarketDataRepositoryError("Candle conflict could not be reconciled")
                        stored = tuple(self._decimal_text(existing[name]) for name in
                                       ("open", "high", "low", "close", "volume"))
                        if stored != prices:
                            raise ValueError("Conflicting closed candle; history was not overwritten")
            return inserted
        except ValueError:
            raise
        except psycopg.Error as error:
            raise MarketDataRepositoryError("PostgreSQL market-data write failed") from error

    def read_window(self, symbol, timeframe, start_ms, end_ms, as_of_ms=None):
        start, end, _ = validate_window(symbol, timeframe, start_ms, end_ms, as_of_ms)
        psycopg, dict_row = self._driver()
        try:
            with psycopg.connect(self.dsn) as connection:
                with connection.cursor(row_factory=dict_row) as cursor:
                    cursor.execute(
                        """SELECT timeframe, open_time_ms, open, high, low, close,
                                  volume, available_at_ms, symbol
                           FROM market_data.candles
                           WHERE exchange='binance' AND market_type='USDT_PERPETUAL'
                             AND symbol=%s AND timeframe=%s
                             AND open_time_ms >= %s AND open_time_ms < %s
                             AND (%s::BIGINT IS NULL OR available_at_ms <= %s)
                           ORDER BY open_time_ms""",
                        (symbol, timeframe, start, end, as_of_ms, as_of_ms),
                    )
                    rows = cursor.fetchall()
            candles = [
                Candle(
                    timeframe=row["timeframe"],
                    open_time_ms=row["open_time_ms"],
                    open=self._decimal_text(row["open"]),
                    high=self._decimal_text(row["high"]),
                    low=self._decimal_text(row["low"]),
                    close=self._decimal_text(row["close"]),
                    volume=self._decimal_text(row["volume"]),
                    available_at_ms=row["available_at_ms"],
                    symbol=row["symbol"],
                )
                for row in rows
            ]
            return build_window(symbol, timeframe, start, end, candles, as_of_ms)
        except ValueError:
            raise
        except psycopg.Error as error:
            raise MarketDataRepositoryError("PostgreSQL market-data read failed") from error


def get_market_data_repository(environ=None):
    """Select PostgreSQL for market data only; otherwise retain SQLite as default."""
    environment = os.environ if environ is None else environ
    dsn = environment.get("MARKET_DATA_DATABASE_URL")
    if dsn:
        return PostgresRepository(dsn)
    db_path = environment.get("MARKET_DATA_DB")
    if db_path:
        return SQLiteRepository(db_path)
    raise MarketDataUnavailable("No market-data backend is configured")
