"""Fenced SQLite write gateway for canonical T0 candles.

G1 deliberately implements only the gateway primitive. Existing writer paths
are not routed through this module until the separate G2 change.
"""

import os
import sqlite3
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Callable
from urllib.parse import quote

from market_data.store import Candle, EXCHANGE, MARKET_TYPE


DEFAULT_LEASE_NAME = "binance-btcusdt-canonical"
_CANDLE_COLUMNS = (
    "exchange",
    "market_type",
    "symbol",
    "timeframe",
    "open_time_ms",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "available_at_ms",
)
_PRICE_COLUMNS = ("open", "high", "low", "close", "volume")


class GatewayWriteError(Exception):
    """Base class for typed T0 Gateway failures."""


class LeaseRejected(GatewayWriteError):
    """The supplied lease capability is missing, stale, or expired."""


class CandleBatchRejected(GatewayWriteError):
    """The candle batch is invalid or conflicts with persisted history."""


class GatewayStorageError(GatewayWriteError):
    """SQLite could not safely complete the requested gateway operation."""


@dataclass(frozen=True)
class LeaseFence:
    """Immutable capability identifying one lease owner and fencing generation."""

    lease_name: str
    owner_id: str
    generation: int


class T0WriteGateway:
    """Atomic candle writer whose lease check shares the candle transaction."""

    def __init__(self, db_path: str | os.PathLike[str]):
        # Deliberately do not resolve, stat, create, or connect to the path here.
        try:
            path = os.fspath(db_path)
        except TypeError as exc:
            raise ValueError("db_path must be a non-empty filesystem path") from exc
        if not isinstance(path, str) or not path.strip():
            raise ValueError("db_path must be a non-empty filesystem path")
        self._db_path = path

    def _connect_rw(self):
        # mode=rw is important: sqlite3.connect(path) would silently create a
        # missing database and could turn a configuration error into a new DB.
        uri = Path(self._db_path).absolute().as_uri() + "?mode=rw"
        connection = sqlite3.connect(uri, uri=True, timeout=5, isolation_level=None)
        connection.execute("PRAGMA busy_timeout=5000")
        return connection

    def _connect_ro(self):
        uri = Path(self._db_path).absolute().as_uri() + "?mode=ro"
        connection = sqlite3.connect(uri, uri=True, timeout=5)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA query_only=ON")
        return connection

    @staticmethod
    def _validate_batch(candles):
        if not isinstance(candles, Sequence):
            raise CandleBatchRejected("candles must be a sequence")
        batch = list(candles)
        if any(not isinstance(candle, Candle) for candle in batch):
            raise CandleBatchRejected("batch must contain validated Candle values")
        return batch

    @staticmethod
    def _validate_fence(lease_token):
        if not isinstance(lease_token, LeaseFence):
            raise LeaseRejected("lease_token must be a LeaseFence")
        if (not isinstance(lease_token.lease_name, str)
                or not lease_token.lease_name.strip()
                or not isinstance(lease_token.owner_id, str)
                or not lease_token.owner_id.strip()
                or type(lease_token.generation) is not int
                or lease_token.generation < 1):
            raise LeaseRejected("lease fence fields are invalid")

    @staticmethod
    def _now(now_ms):
        if not callable(now_ms):
            raise LeaseRejected("now_ms must be a zero-argument callable")
        try:
            value = now_ms()
        except Exception as exc:
            raise LeaseRejected("could not read the lease validation clock") from exc
        if type(value) is not int or value < 0:
            raise LeaseRejected("now_ms must return a nonnegative integer")
        return value

    @staticmethod
    def _assert_current_lease(connection, fence, timestamp):
        try:
            row = connection.execute(
                """SELECT owner, generation, expires_at_ms
                   FROM feeder_leases WHERE lease_name=?""",
                (fence.lease_name,),
            ).fetchone()
        except sqlite3.Error as exc:
            raise GatewayStorageError("could not read the authoritative feeder lease") from exc

        if row is None:
            raise LeaseRejected("feeder lease is missing")
        owner, generation, expires_at_ms = row
        if (owner != fence.owner_id
                or generation != fence.generation
                or expires_at_ms <= timestamp):
            raise LeaseRejected("feeder lease is stale, expired, or owned by another writer")

    @staticmethod
    def _insert_one(connection, candle):
        identity = (
            EXCHANGE,
            MARKET_TYPE,
            candle.symbol,
            candle.timeframe,
            candle.open_time_ms,
        )
        existing = connection.execute(
            """SELECT open, high, low, close, volume FROM candles
               WHERE exchange=? AND market_type=? AND symbol=?
                 AND timeframe=? AND open_time_ms=?""",
            identity,
        ).fetchone()
        prices = tuple(getattr(candle, name) for name in _PRICE_COLUMNS)

        if existing is not None:
            if tuple(existing) != prices:
                raise CandleBatchRejected(
                    "conflicting closed candle; existing history was not overwritten"
                )
            # First-observed available_at_ms is immutable on an identical replay.
            return 0

        connection.execute(
            """INSERT INTO candles (
                   exchange, market_type, symbol, timeframe, open_time_ms,
                   open, high, low, close, volume, available_at_ms
               ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            identity + prices + (candle.available_at_ms,),
        )
        return 1

    def insert_batch(
        self,
        candles: Sequence[Candle],
        *,
        lease_token: LeaseFence,
        now_ms: Callable[[], int],
    ) -> int:
        # The empty sequence is a strict no-op, even with no DB path or fence.
        if isinstance(candles, Sequence) and len(candles) == 0:
            return 0

        batch = self._validate_batch(candles)
        if not batch:
            return 0
        self._validate_fence(lease_token)
        if not callable(now_ms):
            raise LeaseRejected("now_ms must be a zero-argument callable")

        connection = None
        try:
            connection = self._connect_rw()
            connection.execute("BEGIN IMMEDIATE")

            # Initial fence check occurs only after SQLite has serialized writers.
            self._assert_current_lease(
                connection, lease_token, self._now(now_ms)
            )

            inserted = 0
            for candle in batch:
                inserted += self._insert_one(connection, candle)

            # This final check is the admission linearization point. A lease
            # expiring after this check does not revoke an admitted transaction.
            self._assert_current_lease(
                connection, lease_token, self._now(now_ms)
            )
            connection.commit()
            return inserted
        except GatewayWriteError:
            if connection is not None:
                connection.rollback()
            raise
        except (sqlite3.Error, OSError, ValueError) as exc:
            if connection is not None:
                connection.rollback()
            raise GatewayStorageError("SQLite gateway transaction failed") from exc
        finally:
            if connection is not None:
                connection.close()

    def read_window(self, symbol: str, timeframe: str, start, end):
        """Return matching candle rows as immutable mappings, without writes."""
        if not isinstance(symbol, str) or not symbol.strip():
            raise CandleBatchRejected("symbol must be a non-empty string")
        if not isinstance(timeframe, str) or not timeframe.strip():
            raise CandleBatchRejected("timeframe must be a non-empty string")
        if type(start) is not int or start < 0 or type(end) is not int or end < start:
            raise CandleBatchRejected("window bounds must be nonnegative ordered integers")

        connection = None
        try:
            connection = self._connect_ro()
            rows = connection.execute(
                """SELECT exchange, market_type, symbol, timeframe, open_time_ms,
                          open, high, low, close, volume, available_at_ms
                   FROM candles
                   WHERE symbol=? AND timeframe=? AND open_time_ms>=? AND open_time_ms<?
                   ORDER BY open_time_ms ASC""",
                (symbol, timeframe, start, end),
            ).fetchall()
            return tuple(dict(row) for row in rows)
        except GatewayWriteError:
            raise
        except (sqlite3.Error, OSError, ValueError) as exc:
            raise GatewayStorageError("SQLite gateway read failed") from exc
        finally:
            if connection is not None:
                connection.close()

    def close(self) -> None:
        """No persistent connection is held; closing is intentionally a no-op."""
        return None
