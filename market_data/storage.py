"""Runtime storage selection shared by the read API and ingestion.

SQLite remains the default. PostgreSQL is opt-in and requires an explicit DSN.
Constructors are side-effect free; schema changes are only made by the explicit
migration command in market_data.migrations.
"""

import os
from pathlib import Path

from market_data.store import CandleStore, read_window as read_sqlite_window
from market_data.postgres import PostgresCandleStore, read_window as read_postgres_window


class StoreConfigurationError(ValueError):
    """The selected storage backend is not completely configured."""


class SQLiteCandleStore:
    """Side-effect-free SQLite facade matching the PostgreSQL adapter contract."""

    def __init__(self, db_path):
        if not db_path:
            raise StoreConfigurationError("MARKET_DATA_DB is required for SQLite")
        self.path = Path(db_path)
        self._writer = None

    def insert(self, candles):
        # Initialize the existing SQLite schema lazily, never during API reads.
        if self._writer is None:
            self._writer = CandleStore(self.path)
        return self._writer.insert(candles)

    def read_window(self, symbol, timeframe, start_ms, end_ms, as_of_ms=None):
        return read_sqlite_window(self.path, symbol, timeframe, start_ms, end_ms, as_of_ms)


class PostgresStore:
    """Unified PostgreSQL facade; never runs migrations implicitly."""

    def __init__(self, dsn):
        if not dsn:
            raise StoreConfigurationError("MARKET_DATA_POSTGRES_DSN is required for PostgreSQL")
        self._store = PostgresCandleStore(dsn)
        self.dsn = dsn

    def insert(self, candles):
        return self._store.insert(candles)

    def read_window(self, symbol, timeframe, start_ms, end_ms, as_of_ms=None):
        return read_postgres_window(self.dsn, symbol, timeframe, start_ms, end_ms, as_of_ms)


def create_store(backend="sqlite", *, sqlite_path=None, postgres_dsn=None):
    """Create the selected store. Unknown or incomplete backends fail closed."""
    if backend == "sqlite":
        return SQLiteCandleStore(sqlite_path)
    if backend == "postgres":
        return PostgresStore(postgres_dsn)
    raise StoreConfigurationError("MARKET_DATA_BACKEND must be 'sqlite' or 'postgres'")


def create_store_from_env(environ=None):
    """Select storage from environment; SQLite is the backwards-compatible default."""
    values = os.environ if environ is None else environ
    backend = values.get("MARKET_DATA_BACKEND", "sqlite").strip().lower()
    return create_store(
        backend,
        sqlite_path=values.get("MARKET_DATA_DB", ""),
        postgres_dsn=values.get("MARKET_DATA_POSTGRES_DSN", ""),
    )
