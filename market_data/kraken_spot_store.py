"""Isolated SQLite persistence for Kraken BTC/USDT Spot candles.

This store is deliberately separate from the Binance USD-M canonical store.
It accepts only validated Kraken Spot SourceCandle values and is not part of
the canonical market-data storage factory or Futures strategy interfaces.
"""

import hashlib
import json
import os
import sqlite3
from contextlib import closing
from pathlib import Path

from market_data.kraken_spot import (
    INTERVAL_MS,
    MAX_CANDLES,
    MAX_TIMESTAMP,
    InstrumentIdentity,
    SourceCandle,
)

EXCHANGE = "kraken"
MARKET_TYPE = "SPOT"
SYMBOL = "BTC/USDT"
PRICE_FIELDS = ("open", "high", "low", "close", "volume")


def _timestamp(value, label):
    if type(value) is not int or not 0 <= value <= MAX_TIMESTAMP:
        raise ValueError(f"{label} must be a nonnegative 64-bit integer")
    return value


def _database_path(value, label):
    if value is None or not str(value).strip():
        raise ValueError(f"{label} is required")
    if str(value) == ":memory:":
        raise ValueError("Kraken Spot storage requires a dedicated on-disk SQLite file")
    return Path(value).expanduser().resolve()


class KrakenSpotSQLiteStore:
    """Persist Kraken Spot candles in a dedicated, source-isolated SQLite file."""

    def __init__(self, db_path, *, canonical_db_path=None):
        self.path = _database_path(db_path, "Kraken Spot database path")
        canonical = canonical_db_path or os.environ.get("MARKET_DATA_DB")
        if not canonical:
            raise ValueError(
                "Binance canonical database path is required to verify Kraken Spot isolation"
            )
        canonical_path = _database_path(canonical, "Binance canonical database path")
        same_path = self.path == canonical_path
        if not same_path and self.path.exists() and canonical_path.exists():
            same_path = os.path.samefile(self.path, canonical_path)
        if same_path:
            raise ValueError(
                "Kraken Spot database must be separate from the Binance canonical database"
            )

        self.path.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(self.path, timeout=5)) as connection, connection:
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute(
                """CREATE TABLE IF NOT EXISTS kraken_spot_candles (
                    exchange TEXT NOT NULL CHECK (exchange = 'kraken'),
                    market_type TEXT NOT NULL CHECK (market_type = 'SPOT'),
                    native_market_id TEXT NOT NULL CHECK (length(native_market_id) > 0),
                    symbol TEXT NOT NULL CHECK (symbol = 'BTC/USDT'),
                    timeframe TEXT NOT NULL CHECK (timeframe IN ('15m', '1h')),
                    open_time_ms INTEGER NOT NULL,
                    open TEXT NOT NULL,
                    high TEXT NOT NULL,
                    low TEXT NOT NULL,
                    close TEXT NOT NULL,
                    volume TEXT NOT NULL,
                    available_at_ms INTEGER NOT NULL,
                    PRIMARY KEY (
                        exchange, market_type, native_market_id, symbol,
                        timeframe, open_time_ms
                    )
                )"""
            )

    @staticmethod
    def _validate_candle(candle):
        if not isinstance(candle, SourceCandle):
            raise ValueError("Expected validated Kraken Spot SourceCandle values")
        identity = candle.instrument
        if (
            not isinstance(identity, InstrumentIdentity)
            or identity.exchange != EXCHANGE
            or identity.market_type != MARKET_TYPE
            or identity.canonical_symbol != SYMBOL
            or not isinstance(identity.native_market_id, str)
            or not identity.native_market_id.strip()
        ):
            raise ValueError("Only Kraken BTC/USDT Spot candles can be persisted")

    def insert(self, candles):
        batch = list(candles)
        for candle in batch:
            self._validate_candle(candle)

        inserted = 0
        with closing(sqlite3.connect(self.path, timeout=5)) as connection, connection:
            connection.execute("BEGIN IMMEDIATE")
            for candle in batch:
                identity = candle.instrument
                key = (
                    identity.exchange,
                    identity.market_type,
                    identity.native_market_id,
                    identity.canonical_symbol,
                    candle.timeframe,
                    candle.open_time_ms,
                )
                existing_identity = connection.execute(
                    """SELECT native_market_id FROM kraken_spot_candles
                       WHERE exchange=? AND market_type=? AND symbol=?
                         AND native_market_id<>? LIMIT 1""",
                    (
                        identity.exchange,
                        identity.market_type,
                        identity.canonical_symbol,
                        identity.native_market_id,
                    ),
                ).fetchone()
                if existing_identity is not None:
                    raise ValueError(
                        "Kraken Spot dataset already uses a different native market ID"
                    )

                values = tuple(getattr(candle, name) for name in PRICE_FIELDS)
                existing = connection.execute(
                    """SELECT open, high, low, close, volume
                    FROM kraken_spot_candles
                    WHERE exchange=? AND market_type=? AND native_market_id=?
                      AND symbol=? AND timeframe=? AND open_time_ms=?""",
                    key,
                ).fetchone()
                if existing is not None:
                    if existing != values:
                        raise ValueError(
                            "Conflicting Kraken Spot candle; history was not overwritten"
                        )
                    # Preserve the original first-observed timestamp on retries.
                    continue
                connection.execute(
                    """INSERT INTO kraken_spot_candles (
                        exchange, market_type, native_market_id, symbol, timeframe,
                        open_time_ms, open, high, low, close, volume, available_at_ms
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    key + values + (candle.available_at_ms,),
                )
                inserted += 1
        return inserted

    def read_window(self, timeframe, start_ms, end_ms, as_of_ms=None):
        if not isinstance(timeframe, str) or timeframe not in INTERVAL_MS:
            raise ValueError("Only Kraken Spot 15m and 1h candles are supported")
        start = _timestamp(start_ms, "Window start")
        end = _timestamp(end_ms, "Window end")
        interval = INTERVAL_MS[timeframe]
        if (
            start % interval
            or end % interval
            or not 0 < end - start <= MAX_CANDLES * interval
        ):
            raise ValueError("Window must be aligned, nonempty and bounded")
        if as_of_ms is not None:
            _timestamp(as_of_ms, "As-of timestamp")

        with closing(
            sqlite3.connect(self.path.as_uri() + "?mode=ro", uri=True, timeout=5)
        ) as connection, connection:
            connection.row_factory = sqlite3.Row
            connection.execute("BEGIN")
            native_ids = connection.execute(
                """SELECT DISTINCT native_market_id FROM kraken_spot_candles
                   WHERE exchange=? AND market_type=? AND symbol=? AND timeframe=?
                     AND open_time_ms>=? AND open_time_ms<?
                     AND (? IS NULL OR available_at_ms<=?)
                   LIMIT 2""",
                (
                    EXCHANGE, MARKET_TYPE, SYMBOL, timeframe, start, end,
                    as_of_ms, as_of_ms,
                ),
            ).fetchall()
            if len(native_ids) > 1:
                raise ValueError(
                    "Kraken Spot read window contains multiple native market IDs"
                )

            rows = connection.execute(
                """SELECT exchange, market_type, native_market_id, symbol, timeframe,
                          open_time_ms, open, high, low, close, volume, available_at_ms
                   FROM kraken_spot_candles
                   WHERE exchange=? AND market_type=? AND symbol=? AND timeframe=?
                     AND open_time_ms>=? AND open_time_ms<?
                     AND (? IS NULL OR available_at_ms<=?)
                   ORDER BY open_time_ms""",
                (
                    EXCHANGE, MARKET_TYPE, SYMBOL, timeframe, start, end,
                    as_of_ms, as_of_ms,
                ),
            ).fetchall()

        candles = []
        for row in rows:
            identity = InstrumentIdentity(
                exchange=row["exchange"],
                market_type=row["market_type"],
                native_market_id=row["native_market_id"],
                canonical_symbol=row["symbol"],
            )
            candle = SourceCandle(
                instrument=identity,
                timeframe=row["timeframe"],
                open_time_ms=row["open_time_ms"],
                open=row["open"],
                high=row["high"],
                low=row["low"],
                close=row["close"],
                volume=row["volume"],
                available_at_ms=row["available_at_ms"],
            )
            candles.append(candle.as_dict())

        gaps, cursor = [], start
        for candle in candles:
            if candle["openTimeMs"] > cursor:
                gaps.append({"startMs": cursor, "endMs": candle["openTimeMs"]})
            cursor = candle["closeTimeMs"]
        if cursor < end:
            gaps.append({"startMs": cursor, "endMs": end})

        result = {
            "exchange": EXCHANGE,
            "marketType": MARKET_TYPE,
            "symbol": SYMBOL,
            "timeframe": timeframe,
            "startMs": start,
            "endMs": end,
            "asOfMs": as_of_ms,
            "candles": candles,
        }
        digest = hashlib.sha256(
            json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        result["datasetVersion"] = "sha256:" + digest
        result["coverage"] = {
            "expected": (end - start) // interval,
            "returned": len(candles),
            "complete": not gaps,
            "gaps": gaps,
        }
        return result
