"""Independent live market-data acceptance using Kraken spot BTC/USDT.

This deliberately does NOT use market_data.sync or the canonical Binance
candle store/API: that schema records Binance USD-M provenance. Results from
this workflow cannot attest to Binance USD-M collector availability.
"""
import hashlib
import json
import os
import sqlite3
import sys
import time
from decimal import Decimal, InvalidOperation
from pathlib import Path

import ccxt

SYMBOL = "BTC/USDT"
EXCHANGE_ID = "kraken"
MARKET_TYPE = "SPOT"
INTERVAL_MS = {"15m": 900_000, "1h": 3_600_000}
WINDOW_MS = 24 * 3_600_000
DB_PATH = Path(os.environ.get("ALTERNATIVE_ACCEPTANCE_DB", "alternative-source-acceptance.sqlite3"))
REPORT_PATH = Path(os.environ.get("ALTERNATIVE_ACCEPTANCE_REPORT", "alternative-source-acceptance.json"))
LOG_PATH = Path(os.environ.get("ALTERNATIVE_ACCEPTANCE_LOG", "alternative-source-acceptance.log"))


def decimal_text(value, *, allow_zero=False):
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError("Invalid OHLCV decimal") from exc
    if not number.is_finite() or number < 0 or (not allow_zero and number == 0):
        raise ValueError("OHLCV decimal must be finite and nonnegative")
    result = format(number, "f")
    if "." in result:
        result = result.rstrip("0").rstrip(".")
    return result or "0"


def validate_market(exchange):
    if exchange.id != EXCHANGE_ID:
        raise ValueError("Alternative acceptance requires Kraken only")
    market = exchange.load_markets().get(SYMBOL)
    if not isinstance(market, dict):
        raise ValueError("Kraken BTC/USDT spot market is unavailable")
    expected = {"symbol": SYMBOL, "base": "BTC", "quote": "USDT"}
    if any(market.get(key) != value for key, value in expected.items()):
        raise ValueError("Unexpected Kraken BTC/USDT market identity")
    if market.get("active") is not True or market.get("spot") is not True or market.get("swap") is True:
        raise ValueError("Kraken BTC/USDT is not an active spot market")
    return market


def fetch_closed_window(exchange, timeframe, start_ms, end_ms, *, now_ms=None):
    interval = INTERVAL_MS.get(timeframe)
    if interval is None or start_ms % interval or end_ms % interval or not start_ms < end_ms:
        raise ValueError("Unsupported timeframe or unaligned window")
    expected = (end_ms - start_ms) // interval
    if expected > 2000:
        raise ValueError("Acceptance window exceeds the candle limit")

    server_time = exchange.fetch_time()
    if type(server_time) is not int or server_time < end_ms:
        raise ValueError("Kraken server clock does not cover the requested closed window")
    rows = exchange.fetch_ohlcv(SYMBOL, timeframe=timeframe, since=start_ms, limit=expected)
    observed_at = now_ms if now_ms is not None else time.time_ns() // 1_000_000
    if type(observed_at) is not int:
        raise ValueError("Invalid local observation clock")
    closed_through = min(server_time, observed_at)
    candles, previous = [], None
    for row in rows:
        if not isinstance(row, (list, tuple)) or len(row) != 6:
            raise ValueError("Invalid Kraken OHLCV row")
        opened = row[0]
        if type(opened) is not int or opened % interval:
            raise ValueError("Invalid Kraken candle timestamp")
        if previous is not None and opened <= previous:
            raise ValueError("Kraken candles are not strictly increasing")
        previous = opened
        if opened < start_ms or opened >= end_ms or opened + interval > closed_through:
            continue
        opening, high, low, close, volume = (
            decimal_text(row[1]), decimal_text(row[2]), decimal_text(row[3]),
            decimal_text(row[4]), decimal_text(row[5], allow_zero=True)
        )
        if Decimal(low) > Decimal(high) or not Decimal(low) <= Decimal(opening) <= Decimal(high) or not Decimal(low) <= Decimal(close) <= Decimal(high):
            raise ValueError("Inconsistent Kraken OHLC bounds")
        candles.append({
            "openTimeMs": opened, "open": opening, "high": high, "low": low,
            "close": close, "volume": volume, "availableAtMs": observed_at
        })
    return candles


def initialize_database(path):
    with sqlite3.connect(path) as db:
        db.execute("""CREATE TABLE IF NOT EXISTS alternative_candles (
            exchange TEXT NOT NULL, market_type TEXT NOT NULL, symbol TEXT NOT NULL,
            timeframe TEXT NOT NULL, open_time_ms INTEGER NOT NULL,
            open TEXT NOT NULL, high TEXT NOT NULL, low TEXT NOT NULL,
            close TEXT NOT NULL, volume TEXT NOT NULL, available_at_ms INTEGER NOT NULL,
            PRIMARY KEY (exchange, market_type, symbol, timeframe, open_time_ms)
        )""")


def persist_candles(path, timeframe, candles):
    inserted = 0
    with sqlite3.connect(path) as db:
        db.execute("BEGIN IMMEDIATE")
        for candle in candles:
            key = (EXCHANGE_ID, MARKET_TYPE, SYMBOL, timeframe, candle["openTimeMs"])
            values = tuple(candle[name] for name in ("open", "high", "low", "close", "volume"))
            existing = db.execute("""SELECT open, high, low, close, volume FROM alternative_candles
                WHERE exchange=? AND market_type=? AND symbol=? AND timeframe=? AND open_time_ms=?""", key).fetchone()
            if existing is not None:
                if existing != values:
                    raise ValueError("Conflicting Kraken candle; stored history was not overwritten")
                continue
            db.execute("INSERT INTO alternative_candles VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                       key + values + (candle["availableAtMs"],))
            inserted += 1
    return inserted


def read_dataset(path, timeframe, start_ms, end_ms):
    interval = INTERVAL_MS[timeframe]
    with sqlite3.connect(path) as db:
        rows = db.execute("""SELECT open_time_ms, open, high, low, close, volume, available_at_ms
            FROM alternative_candles WHERE exchange=? AND market_type=? AND symbol=?
            AND timeframe=? AND open_time_ms>=? AND open_time_ms<? ORDER BY open_time_ms""",
            (EXCHANGE_ID, MARKET_TYPE, SYMBOL, timeframe, start_ms, end_ms)).fetchall()
    candles = [{
        "openTimeMs": row[0], "open": row[1], "high": row[2], "low": row[3],
        "close": row[4], "volume": row[5], "availableAtMs": row[6]
    } for row in rows]
    gaps, cursor = [], start_ms
    for candle in candles:
        if candle["openTimeMs"] > cursor:
            gaps.append({"startMs": cursor, "endMs": candle["openTimeMs"]})
        cursor = candle["openTimeMs"] + interval
    if cursor < end_ms:
        gaps.append({"startMs": cursor, "endMs": end_ms})
    payload = {
        "exchange": EXCHANGE_ID, "marketType": MARKET_TYPE, "symbol": SYMBOL,
        "timeframe": timeframe, "startMs": start_ms, "endMs": end_ms,
        "candles": candles
    }
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return {
        **payload, "datasetVersion": "sha256:" + digest,
        "coverage": {"expected": (end_ms - start_ms) // interval,
                     "returned": len(candles), "complete": not gaps, "gaps": gaps}
    }


def run_acceptance():
    exchange = ccxt.kraken({"enableRateLimit": True})
    try:
        validate_market(exchange)
        server_time = exchange.fetch_time()
        hour = INTERVAL_MS["1h"]
        end_ms = (server_time // hour - 1) * hour
        start_ms = end_ms - WINDOW_MS
        initialize_database(DB_PATH)
        report = {
            "sourceSha": os.environ.get("CM_COMMIT", "recorded-by-workflow"),
            "exchange": EXCHANGE_ID, "marketType": MARKET_TYPE, "symbol": SYMBOL,
            "window": {"startMs": start_ms, "endMs": end_ms},
            "storage": "isolated-sqlite", "timeframes": {},
            "scope": {
                "validates": ["Kraken spot OHLCV retrieval", "closed-candle validation",
                              "isolated persistence", "repeat-sync idempotency", "persisted readback and dataset hash"],
                "doesNotValidate": ["Binance USD-M collector", "Binance API availability",
                                    "canonical Binance PostgreSQL storage", "canonical /v1/candles API"]
            }
        }
        for timeframe in ("15m", "1h"):
            first_rows = fetch_closed_window(exchange, timeframe, start_ms, end_ms)
            inserted = persist_candles(DB_PATH, timeframe, first_rows)
            first = read_dataset(DB_PATH, timeframe, start_ms, end_ms)
            if not first["coverage"]["complete"]:
                raise RuntimeError(f"{timeframe}: first Kraken sync has incomplete coverage")
            repeat_rows = fetch_closed_window(exchange, timeframe, start_ms, end_ms)
            repeat_inserted = persist_candles(DB_PATH, timeframe, repeat_rows)
            second = read_dataset(DB_PATH, timeframe, start_ms, end_ms)
            if repeat_inserted != 0 or first["datasetVersion"] != second["datasetVersion"]:
                raise RuntimeError(f"{timeframe}: repeat sync was not idempotent")
            report["timeframes"][timeframe] = {
                "inserted": inserted, "repeatInserted": repeat_inserted,
                "datasetVersion": first["datasetVersion"],
                "coverage": first["coverage"], "persistedReadback": "PASS",
                "idempotency": "PASS"
            }
            print(f"{timeframe}: coverage=PASS returned={first['coverage']['returned']} "
                  f"repeat_inserted={repeat_inserted} hash={first['datasetVersion']}")
        report["result"] = "PASS"
        REPORT_PATH.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        print(f"report={REPORT_PATH}")
        print("ALTERNATIVE_SOURCE_ACCEPTANCE=PASS")
    finally:
        exchange.close()


if __name__ == "__main__":
    try:
        run_acceptance()
    except Exception as exc:
        print(f"ALTERNATIVE_SOURCE_ACCEPTANCE=FAIL: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise
