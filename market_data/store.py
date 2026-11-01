"""Canonical, closed Binance USD-M candles stored without price rounding."""

import hashlib
import json
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path


INTERVAL_MS = {"15m": 900_000, "1h": 3_600_000}
MAX_CANDLES = 2000
MAX_TIMESTAMP = 2**63 - 1
EXCHANGE, MARKET_TYPE, SYMBOL = "binance", "USDT_PERPETUAL", "BTCUSDT"
PRICE_FIELDS = ("open", "high", "low", "close", "volume")


def _integer(value):
    if type(value) is not int or not 0 <= value <= MAX_TIMESTAMP:
        raise ValueError("Timestamp must be a nonnegative 64-bit integer")
    return value


def _decimal(value, allow_zero=False):
    if not isinstance(value, str) or not 1 <= len(value) <= 128:
        raise ValueError("Price and volume must be bounded decimal strings")
    try:
        number = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError("Invalid decimal") from exc
    if not number.is_finite() or len(number.as_tuple().digits) > 40:
        raise ValueError("Decimal must be finite and bounded")
    if not -30 <= number.as_tuple().exponent <= 30 or number.adjusted() > 30:
        raise ValueError("Decimal exponent is outside supported precision")
    if number < 0 or (not allow_zero and number == 0):
        raise ValueError("Invalid price or volume")
    # Decimal.normalize() can round at the active precision; format does not.
    normalized = format(number, "f")
    if "." in normalized:
        normalized = normalized.rstrip("0").rstrip(".")
    return "0" if number == 0 else normalized


@dataclass(frozen=True)
class Candle:
    timeframe: str
    open_time_ms: int
    open: str
    high: str
    low: str
    close: str
    volume: str
    available_at_ms: int
    symbol: str = SYMBOL

    def __post_init__(self):
        if not isinstance(self.timeframe, str) or self.timeframe not in INTERVAL_MS or self.symbol != SYMBOL:
            raise ValueError("Only BTCUSDT perpetual 15m/1h candles are supported")
        interval = INTERVAL_MS[self.timeframe]
        opening, available = _integer(self.open_time_ms), _integer(self.available_at_ms)
        if opening % interval or available < opening + interval:
            raise ValueError("Candle must be aligned and closed before observation")
        for name in PRICE_FIELDS:
            object.__setattr__(self, name, _decimal(getattr(self, name), allow_zero=name == "volume"))
        low, high = Decimal(self.low), Decimal(self.high)
        if low > high or not low <= Decimal(self.open) <= high or not low <= Decimal(self.close) <= high:
            raise ValueError("Inconsistent candle OHLC bounds")

    def as_dict(self):
        return {
            "exchange": EXCHANGE, "marketType": MARKET_TYPE, "symbol": self.symbol,
            "timeframe": self.timeframe, "openTimeMs": self.open_time_ms,
            "closeTimeMs": self.open_time_ms + INTERVAL_MS[self.timeframe],
            **{name: getattr(self, name) for name in PRICE_FIELDS},
            "isClosed": True, "availableAtMs": self.available_at_ms,
            "availabilityKind": "FIRST_OBSERVED", "quality": "VALIDATED",
            "source": "ccxt.binanceusdm",
        }


class CandleStore:
    def __init__(self, db_path):
        self.path = Path(db_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(self.path, timeout=5)) as connection:
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute("""CREATE TABLE IF NOT EXISTS candles (
                exchange TEXT NOT NULL, market_type TEXT NOT NULL, symbol TEXT NOT NULL,
                timeframe TEXT NOT NULL, open_time_ms INTEGER NOT NULL,
                open TEXT NOT NULL, high TEXT NOT NULL, low TEXT NOT NULL,
                close TEXT NOT NULL, volume TEXT NOT NULL, available_at_ms INTEGER NOT NULL,
                PRIMARY KEY (exchange, market_type, symbol, timeframe, open_time_ms)
            )""")
            connection.commit()

    @staticmethod
    def _insert_batch(connection, batch):
        inserted = 0
        for candle in batch:
            key = (EXCHANGE, MARKET_TYPE, candle.symbol, candle.timeframe, candle.open_time_ms)
            prices = tuple(getattr(candle, name) for name in PRICE_FIELDS)
            existing = connection.execute("""SELECT open, high, low, close, volume FROM candles
                WHERE exchange=? AND market_type=? AND symbol=? AND timeframe=? AND open_time_ms=?""", key).fetchone()
            if existing is not None:
                if existing != prices:
                    raise ValueError("Conflicting closed candle; history was not overwritten")
                continue
            connection.execute("INSERT INTO candles VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                               key + prices + (candle.available_at_ms,))
            inserted += 1
        return inserted

    @staticmethod
    def _validated_batch(candles):
        batch = list(candles)
        if any(not isinstance(candle, Candle) for candle in batch):
            raise ValueError("Expected validated Candle values")
        return batch

    def insert(self, candles):
        batch = self._validated_batch(candles)
        with closing(sqlite3.connect(self.path, timeout=5)) as connection, connection:
            connection.execute("BEGIN IMMEDIATE")
            return self._insert_batch(connection, batch)

    def insert_fenced(self, candles, *, owner, generation, now_ms,
                      lease_name="binance-btcusdt-canonical"):
        """Atomically validate the current SQLite lease and commit a candle batch.

        BEGIN IMMEDIATE serializes this transaction against lease takeover,
        heartbeat and release transactions in LeaseStore. The lease check and
        every candle insert therefore share one SQLite write transaction.
        """
        if not isinstance(owner, str) or not owner.strip():
            raise ValueError("owner must be a non-empty string")
        if type(generation) is not int or generation < 1:
            raise ValueError("generation must be a positive integer")
        if not callable(now_ms):
            raise TypeError("now_ms must be callable")
        if not isinstance(lease_name, str) or not lease_name.strip():
            raise ValueError("lease_name must be a non-empty string")
        timestamp = now_ms()
        if type(timestamp) is not int or timestamp < 0:
            raise ValueError("now_ms must return a nonnegative integer")
        batch = self._validated_batch(candles)
        with closing(sqlite3.connect(self.path, timeout=5, isolation_level=None)) as connection:
            connection.execute("PRAGMA busy_timeout=5000")
            connection.execute("BEGIN IMMEDIATE")
            try:
                try:
                    lease = connection.execute(
                        """SELECT 1 FROM feeder_leases
                           WHERE lease_name=? AND owner=? AND generation=? AND expires_at_ms>?""",
                        (lease_name, owner, generation, timestamp),
                    ).fetchone()
                except sqlite3.OperationalError as error:
                    if "no such table" in str(error).lower():
                        raise PermissionError("Canonical write blocked: lease record is missing") from error
                    raise
                if lease is None:
                    raise PermissionError("Canonical write blocked: lease is stale, expired, or missing")
                inserted = self._insert_batch(connection, batch)
                connection.commit()
                return inserted
            except Exception:
                connection.rollback()
                raise


def read_window(db_path, symbol, timeframe, start_ms, end_ms, as_of_ms=None):
    if symbol != SYMBOL or not isinstance(timeframe, str) or timeframe not in INTERVAL_MS:
        raise ValueError("Unsupported market or timeframe")
    start, end = _integer(start_ms), _integer(end_ms)
    interval = INTERVAL_MS[timeframe]
    if start % interval or end % interval or not 0 < end - start <= MAX_CANDLES * interval:
        raise ValueError("Window must be aligned, nonempty and bounded")
    if as_of_ms is not None:
        _integer(as_of_ms)
    path = Path(db_path).resolve()
    if not path.is_file():
        raise FileNotFoundError("Candle database is unavailable")
    with closing(sqlite3.connect(path.as_uri() + "?mode=ro", uri=True, timeout=5)) as connection, connection:
        connection.row_factory = sqlite3.Row
        connection.execute("BEGIN")
        rows = connection.execute("""SELECT timeframe, open_time_ms, open, high, low, close,
                volume, available_at_ms, symbol FROM candles
            WHERE exchange=? AND market_type=? AND symbol=? AND timeframe=?
                AND open_time_ms>=? AND open_time_ms<?
                AND (? IS NULL OR available_at_ms<=?) ORDER BY open_time_ms""",
            (EXCHANGE, MARKET_TYPE, symbol, timeframe, start, end, as_of_ms, as_of_ms)).fetchall()
        candles = [Candle(**dict(row)).as_dict() for row in rows]
    gaps, cursor = [], start
    for candle in candles:
        if candle["openTimeMs"] > cursor:
            gaps.append({"startMs": cursor, "endMs": candle["openTimeMs"]})
        cursor = candle["closeTimeMs"]
    if cursor < end:
        gaps.append({"startMs": cursor, "endMs": end})
    result = {
        "exchange": EXCHANGE, "marketType": MARKET_TYPE, "symbol": symbol,
        "timeframe": timeframe, "startMs": start, "endMs": end,
        "asOfMs": as_of_ms, "candles": candles,
    }
    version = hashlib.sha256(json.dumps(result, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    result["datasetVersion"] = "sha256:" + version
    result["coverage"] = {"expected": (end - start) // interval, "returned": len(candles),
                          "complete": not gaps, "gaps": gaps}
    return result
