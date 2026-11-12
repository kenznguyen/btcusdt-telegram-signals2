"""Bounded, read-only Binance USD-M BTCUSDT data probe.

Writes only to an explicitly supplied disposable SQLite path. It never uses
exchange credentials, trading endpoints, T0 storage, or paper submission.
"""
import argparse
import hashlib
import json
import math
import sqlite3
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from pipeline.core_strategy import produce

BASE_URL = "https://fapi.binance.com"
INTERVALS = {"15m": 900_000, "1h": 3_600_000}
LIMIT = 250
USER_AGENT = "btcquant-core-operational-probe/1.0"


def _finite_positive(value, field, *, allow_zero=False):
    try:
        parsed = float(value)
    except (TypeError, ValueError, OverflowError):
        raise ValueError("INVALID_" + field.upper()) from None
    if not math.isfinite(parsed) or parsed < 0 or (parsed == 0 and not allow_zero):
        raise ValueError("INVALID_" + field.upper())
    return parsed


def parse_klines(payload, timeframe, server_time_ms):
    if timeframe not in INTERVALS or not isinstance(payload, list):
        raise ValueError("INVALID_KLINE_PAYLOAD")
    interval = INTERVALS[timeframe]
    parsed = []
    previous_open = None
    for raw in payload:
        if not isinstance(raw, list) or len(raw) < 12:
            raise ValueError("INVALID_KLINE_ROW")
        try:
            opened, closed = int(raw[0]), int(raw[6])
        except (TypeError, ValueError, OverflowError):
            raise ValueError("INVALID_KLINE_TIMESTAMP") from None
        if opened < 0 or closed != opened + interval - 1:
            raise ValueError("INVALID_KLINE_INTERVAL")
        if previous_open is not None and opened != previous_open + interval:
            raise ValueError("KLINE_GAP_OR_ORDER")
        previous_open = opened
        open_price = _finite_positive(raw[1], "open")
        high = _finite_positive(raw[2], "high")
        low = _finite_positive(raw[3], "low")
        close = _finite_positive(raw[4], "close")
        volume = _finite_positive(raw[5], "volume", allow_zero=True)
        _finite_positive(raw[7], "quote_volume", allow_zero=True)
        if high < max(open_price, close) or low > min(open_price, close) or low > high:
            raise ValueError("INVALID_OHLC")
        if closed >= server_time_ms:
            continue
        parsed.append({
            "openTimeMs": opened, "closeTimeMs": closed,
            "availableAtMs": server_time_ms,
            "open": str(raw[1]), "high": str(raw[2]), "low": str(raw[3]),
            "close": str(raw[4]), "volume": str(raw[5]), "isClosed": True,
        })
    if len(parsed) < 100:
        raise ValueError("INSUFFICIENT_CLOSED_CANDLES")
    for index in range(1, len(parsed)):
        if parsed[index]["openTimeMs"] != parsed[index - 1]["openTimeMs"] + interval:
            raise ValueError("KLINE_GAP_OR_ORDER")
    return parsed


def build_window(candles, timeframe):
    if timeframe not in INTERVALS or len(candles) < 100:
        raise ValueError("INSUFFICIENT_WINDOW")
    canonical = json.dumps(candles, sort_keys=True, separators=(",", ":"), allow_nan=False)
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return {
        "timeframe": timeframe, "candles": candles,
        "coverage": {"expected": len(candles), "returned": len(candles), "complete": True},
        "datasetVersion": "sha256:" + digest,
    }


def persist_candles(db_path, timeframe, candles):
    path = Path(db_path).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    window = build_window(candles, timeframe)
    with sqlite3.connect(path, timeout=10) as db:
        db.execute("PRAGMA journal_mode=DELETE")
        db.execute("""CREATE TABLE IF NOT EXISTS candles (
            symbol TEXT NOT NULL, timeframe TEXT NOT NULL, open_time_ms INTEGER NOT NULL,
            close_time_ms INTEGER NOT NULL, available_at_ms INTEGER NOT NULL,
            open TEXT NOT NULL, high TEXT NOT NULL, low TEXT NOT NULL,
            close TEXT NOT NULL, volume TEXT NOT NULL, is_closed INTEGER NOT NULL,
            dataset_version TEXT NOT NULL,
            PRIMARY KEY(symbol,timeframe,open_time_ms)
        )""")
        db.executemany("""INSERT OR REPLACE INTO candles VALUES
            ('BTCUSDT',?,?,?,?,?,?,?,?,?,?,?)""", [
            (timeframe, row["openTimeMs"], row["closeTimeMs"], row["availableAtMs"],
             row["open"], row["high"], row["low"], row["close"], row["volume"],
             1, window["datasetVersion"]) for row in candles
        ])
        db.commit()
        integrity = db.execute("PRAGMA integrity_check").fetchone()[0]
        if integrity != "ok":
            raise sqlite3.DatabaseError("SQLITE_INTEGRITY_CHECK_FAILED")
    return window["datasetVersion"]


def _get_json(path, params=None):
    url = BASE_URL + path
    if params:
        url += "?" + urlencode(params)
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    last_error = None
    for attempt in range(3):
        try:
            with urlopen(request, timeout=15) as response:
                if response.status != 200:
                    raise RuntimeError("BINANCE_HTTP_" + str(response.status))
                return json.loads(response.read(2_000_000).decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, OSError, ValueError) as error:
            last_error = error
            if isinstance(error, HTTPError) and error.code not in (418, 429, 500, 502, 503, 504):
                break
            if attempt < 2:
                time.sleep(1 + attempt)
    raise RuntimeError("BINANCE_PUBLIC_API_UNAVAILABLE: " + type(last_error).__name__) from None


def collect(db_path):
    payloads = {
        timeframe: _get_json("/fapi/v1/klines", {"symbol": "BTCUSDT", "interval": timeframe, "limit": LIMIT})
        for timeframe in ("15m", "1h")
    }
    server_time = _get_json("/fapi/v1/time")
    now_ms = int(server_time["serverTime"])
    windows = {}
    for timeframe, payload in payloads.items():
        candles = parse_klines(payload, timeframe, now_ms)
        windows[timeframe] = build_window(candles, timeframe)
        persisted = persist_candles(db_path, timeframe, candles)
        if persisted != windows[timeframe]["datasetVersion"]:
            raise RuntimeError("DATASET_FINGERPRINT_MISMATCH")
    with sqlite3.connect(db_path) as db:
        integrity = db.execute("PRAGMA integrity_check").fetchone()[0]
        count = db.execute("SELECT COUNT(*) FROM candles").fetchone()[0]
    if integrity != "ok" or count != sum(len(item["candles"]) for item in windows.values()):
        raise RuntimeError("PERSISTED_DATA_VERIFICATION_FAILED")
    return windows, now_ms, count


def run(db_path):
    windows, now_ms, row_count = collect(db_path)
    result = produce(
        windows["15m"], windows["1h"],
        {"positionBase": "0", "averageEntryPrice": "0", "realizedPnlQuote": "0", "feesQuote": "0"},
        {"owner": None, "dcaUsed": False}, None, now_ms,
        account_equity_quote=None,
    )
    return {
        "status": "PASS",
        "source": "BINANCE_USDM_PUBLIC_REST",
        "symbol": "BTCUSDT",
        "serverTimeMs": now_ms,
        "database": str(Path(db_path).resolve()),
        "sqliteIntegrity": "ok",
        "persistedRows": row_count,
        "windows": {
            timeframe: {
                "closedCandles": len(window["candles"]),
                "firstOpenTimeMs": window["candles"][0]["openTimeMs"],
                "lastCloseTimeMs": window["candles"][-1]["closeTimeMs"],
                "datasetVersion": window["datasetVersion"],
            } for timeframe, window in windows.items()
        },
        "core": {
            "action": result["action"], "reason": result["reason"],
            "indicators": result["indicators"],
            "intentCreated": result["intent"] is not None,
        },
        "paperSubmit": "NOT_ATTEMPTED_NO_AUTHENTICATED_BOOK_OR_EQUITY",
        "liveTrading": False,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", required=True, help="Disposable isolated SQLite path")
    args = parser.parse_args()
    print(json.dumps(run(args.db), sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
