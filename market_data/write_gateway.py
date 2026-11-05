"""Single authority for canonical Binance USD-M candle writes.

SQLite lease validation and candle insertion share one BEGIN IMMEDIATE
transaction. ShadowWriteGateway deliberately performs no persistence.
"""
from contextlib import closing
from pathlib import Path
import sqlite3

from market_data.store import Candle, EXCHANGE, MARKET_TYPE, PRICE_FIELDS


class WriteGatewayError(RuntimeError):
    """Canonical write authority is unavailable or invalid."""


class SQLiteWriteGateway:
    """Atomic, lease-fenced writer for the Binance canonical SQLite database."""

    def __init__(self, *, store, lease_store, owner_id, generation_provider, clock):
        if not callable(generation_provider):
            raise TypeError("generation_provider must be callable")
        if not callable(clock):
            raise TypeError("clock must be callable")
        if not isinstance(owner_id, str) or not owner_id.strip():
            raise ValueError("owner_id must be a non-empty string")
        store_path = getattr(store, "path", None)
        lease_path = getattr(lease_store, "db_path", None)
        if store_path is None or lease_path is None:
            raise ValueError("Gateway requires a filesystem SQLite store and lease store")
        if Path(store_path).resolve() != Path(lease_path).resolve():
            raise ValueError("Candle store and lease must share the same SQLite database")
        lease_name = getattr(lease_store, "lease_name", None)
        if not isinstance(lease_name, str) or not lease_name.strip():
            raise ValueError("lease store must expose a valid lease_name")
        resolved_path = Path(store_path).resolve()
        if not resolved_path.is_file():
            raise FileNotFoundError("Canonical SQLite database must already exist before Gateway construction")
        self.db_path = str(resolved_path)
        self.db_uri = resolved_path.as_uri() + "?mode=rw"
        self.lease_name = lease_name
        self.owner_id = owner_id
        self.generation_provider = generation_provider
        self.clock = clock

    @staticmethod
    def _now(clock):
        value = clock()
        if type(value) is not int or value < 0:
            raise ValueError("Gateway clock must return a nonnegative integer")
        return value

    def write_batch(self, candles):
        batch = list(candles)
        if any(not isinstance(candle, Candle) for candle in batch):
            raise ValueError("Expected validated Candle values")
        generation = self.generation_provider()
        if type(generation) is not int or generation < 1:
            raise PermissionError("Feeder lease is unavailable; canonical write rejected")

        inserted = 0
        with closing(sqlite3.connect(self.db_uri, uri=True, timeout=5, isolation_level=None)) as connection:
            connection.execute("PRAGMA busy_timeout=5000")
            try:
                connection.execute("BEGIN IMMEDIATE")
                observed_now = self._now(self.clock)
                lease = connection.execute(
                    """SELECT 1 FROM feeder_leases
                       WHERE lease_name=? AND owner=? AND generation=? AND expires_at_ms>?""",
                    (self.lease_name, self.owner_id, generation, observed_now),
                ).fetchone()
                if lease is None:
                    raise PermissionError("Feeder lease is not current; canonical write rejected")

                for candle in batch:
                    key = (
                        EXCHANGE, MARKET_TYPE, candle.symbol,
                        candle.timeframe, candle.open_time_ms,
                    )
                    prices = tuple(getattr(candle, name) for name in PRICE_FIELDS)
                    existing = connection.execute(
                        """SELECT open, high, low, close, volume FROM candles
                           WHERE exchange=? AND market_type=? AND symbol=?
                             AND timeframe=? AND open_time_ms=?""",
                        key,
                    ).fetchone()
                    if existing is not None:
                        if existing != prices:
                            raise ValueError("Conflicting closed candle; history was not overwritten")
                        continue
                    connection.execute(
                        "INSERT INTO candles VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        key + prices + (candle.available_at_ms,),
                    )
                    inserted += 1

                commit_now = self._now(self.clock)
                still_current = connection.execute(
                    """SELECT 1 FROM feeder_leases
                       WHERE lease_name=? AND owner=? AND generation=? AND expires_at_ms>?""",
                    (self.lease_name, self.owner_id, generation, commit_now),
                ).fetchone()
                if still_current is None:
                    raise PermissionError("Feeder lease expired before commit; canonical write rejected")
                connection.commit()
                return inserted
            except Exception:
                connection.rollback()
                raise


class ShadowWriteGateway:
    """Explicit no-persistence sink for manual, read-only shadow inspection."""

    shadow_only = True

    def write_batch(self, candles):
        batch = list(candles)
        if any(not isinstance(candle, Candle) for candle in batch):
            raise ValueError("Expected validated Candle values")
        return len(batch)
