"""Dedicated SQLite persistence for Bybit BTCUSDT Linear shadow candles."""
import hashlib
import json
import os
import sqlite3
from contextlib import closing
from pathlib import Path

from market_data.bybit_linear import (
    BybitLinearCandle, EXCHANGE, INTERVAL_MS, MARKET_TYPE, MAX_CANDLES, SYMBOL,
)


def _path(value, label):
    if value is None or not str(value).strip() or str(value) == ":memory:":
        raise ValueError(f"{label} must be a dedicated on-disk SQLite path")
    return Path(value).expanduser().resolve()


class BybitLinearSQLiteStore:
    def __init__(self, db_path, *, canonical_db_path=None):
        self.path = _path(db_path, "Bybit shadow database")
        canonical = canonical_db_path or os.environ.get("MARKET_DATA_DB")
        if not canonical:
            raise ValueError("Binance canonical database path is required for isolation")
        canonical_path = _path(canonical, "Binance canonical database")
        same = self.path == canonical_path
        if not same and self.path.exists() and canonical_path.exists():
            same = os.path.samefile(self.path, canonical_path)
        if same:
            raise ValueError("Bybit shadow database must be separate from Binance canonical storage")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(self.path, timeout=5)) as db, db:
            db.execute("PRAGMA journal_mode=WAL")
            db.execute("""CREATE TABLE IF NOT EXISTS bybit_linear_candles (
                exchange TEXT NOT NULL CHECK(exchange='bybit'),
                market_type TEXT NOT NULL CHECK(market_type='LINEAR_PERPETUAL'),
                category TEXT NOT NULL CHECK(category='linear'),
                symbol TEXT NOT NULL CHECK(symbol='BTCUSDT'),
                timeframe TEXT NOT NULL CHECK(timeframe IN ('15m','1h')),
                open_time_ms INTEGER NOT NULL,
                open TEXT NOT NULL, high TEXT NOT NULL, low TEXT NOT NULL,
                close TEXT NOT NULL, volume_btc TEXT NOT NULL,
                turnover_usdt TEXT NOT NULL, available_at_ms INTEGER NOT NULL,
                PRIMARY KEY(exchange, market_type, category, symbol, timeframe, open_time_ms)
            )""")

    @staticmethod
    def _validate(candle):
        if not isinstance(candle, BybitLinearCandle):
            raise ValueError("Only validated BybitLinearCandle values can be stored")

    def insert(self, candles):
        batch = list(candles)
        for item in batch:
            self._validate(item)
        count = 0
        with closing(sqlite3.connect(self.path, timeout=5)) as db, db:
            db.execute("BEGIN IMMEDIATE")
            for item in batch:
                values = (
                    EXCHANGE, MARKET_TYPE, "linear", SYMBOL, item.timeframe,
                    item.open_time_ms, item.open, item.high, item.low, item.close,
                    item.volume_btc, item.turnover_usdt,
                )
                old = db.execute("""SELECT open,high,low,close,volume_btc,turnover_usdt
                    FROM bybit_linear_candles
                    WHERE exchange=? AND market_type=? AND category=? AND symbol=?
                    AND timeframe=? AND open_time_ms=?""", values[:6]).fetchone()
                if old is not None:
                    if old != values[6:]:
                        raise ValueError("Conflicting Bybit candle; existing history is immutable")
                    continue
                db.execute("""INSERT INTO bybit_linear_candles VALUES
                    (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    values + (item.available_at_ms,))
                count += 1
        return count

    def read_window(self, timeframe, start_ms, end_ms):
        interval = INTERVAL_MS.get(timeframe)
        if interval is None or type(start_ms) is not int or type(end_ms) is not int:
            raise ValueError("Invalid Bybit read window")
        if start_ms % interval or end_ms % interval or not 0 < end_ms-start_ms <= MAX_CANDLES*interval:
            raise ValueError("Bybit read window must be aligned and bounded")
        with closing(sqlite3.connect(self.path.as_uri()+"?mode=ro", uri=True)) as db:
            db.row_factory = sqlite3.Row
            rows = db.execute("""SELECT * FROM bybit_linear_candles
                WHERE exchange=? AND market_type=? AND category=? AND symbol=?
                AND timeframe=? AND open_time_ms>=? AND open_time_ms<?
                ORDER BY open_time_ms""",
                (EXCHANGE, MARKET_TYPE, "linear", SYMBOL, timeframe, start_ms, end_ms)).fetchall()
        candles = [{
            "exchange": row["exchange"], "marketType": row["market_type"],
            "category": row["category"], "symbol": row["symbol"],
            "timeframe": row["timeframe"], "openTimeMs": row["open_time_ms"],
            "closeTimeMs": row["open_time_ms"]+interval,
            "open": row["open"], "high": row["high"], "low": row["low"],
            "close": row["close"], "volumeBtc": row["volume_btc"],
            "turnoverUsdt": row["turnover_usdt"], "isClosed": True,
            "availableAtMs": row["available_at_ms"], "availabilityKind": "FIRST_OBSERVED",
            "source": "bybit.v5.market.kline",
        } for row in rows]
        gaps, cursor = [], start_ms
        for item in candles:
            if item["openTimeMs"] > cursor:
                gaps.append({"startMs": cursor, "endMs": item["openTimeMs"]})
            cursor = item["closeTimeMs"]
        if cursor < end_ms:
            gaps.append({"startMs": cursor, "endMs": end_ms})
        result = {
            "exchange": EXCHANGE, "marketType": MARKET_TYPE, "category": "linear",
            "symbol": SYMBOL, "timeframe": timeframe, "startMs": start_ms,
            "endMs": end_ms, "candles": candles,
        }
        digest = hashlib.sha256(json.dumps(result, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        result["datasetVersion"] = "sha256:"+digest
        result["coverage"] = {
            "expected": (end_ms-start_ms)//interval, "returned": len(candles),
            "complete": not gaps, "gaps": gaps,
        }
        return result
