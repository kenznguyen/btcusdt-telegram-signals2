"""Read-only HTTP API for the isolated Kraken BTC/USDT Spot SQLite store.

This is a separate WSGI application. It never imports or calls the canonical
Binance API, storage factory, Futures strategy, backtest, or paper execution.
"""

import hmac
import json
import os
import sqlite3
import time
from urllib.parse import parse_qs

from market_data.kraken_spot import INTERVAL_MS, MAX_CANDLES
from market_data.kraken_spot_store import KrakenSpotSQLiteStore


def candle_query(query):
    if len(query) > 2048:
        raise ValueError("Query too long")
    params = parse_qs(
        query, keep_blank_values=True, strict_parsing=True, max_num_fields=5
    )
    required = {"symbol", "timeframe", "startMs", "endMs"}
    if (
        not required <= params.keys()
        or params.keys() - required - {"asOfMs"}
        or any(len(values) != 1 for values in params.values())
    ):
        raise ValueError("Invalid parameters")

    values = {key: value[0] for key, value in params.items()}
    if values["symbol"] != "BTC/USDT" or values["timeframe"] not in INTERVAL_MS:
        raise ValueError("Unsupported Kraken Spot market")

    def integer(key):
        value = values[key]
        if not value.isascii() or not value.isdigit() or len(value) > 19:
            raise ValueError("Invalid timestamp")
        number = int(value)
        if not 0 <= number < 2**63 - 1:
            raise ValueError("Invalid timestamp")
        return number

    start, end = integer("startMs"), integer("endMs")
    step = INTERVAL_MS[values["timeframe"]]
    if start % step or end % step or not 0 < end - start <= MAX_CANDLES * step:
        raise ValueError("Invalid or oversized window")
    as_of = integer("asOfMs") if "asOfMs" in values else None
    return {
        "timeframe": values["timeframe"],
        "start_ms": start,
        "end_ms": end,
        "as_of_ms": as_of,
    }


def application(environ, start_response):
    def reply(status, body):
        data = json.dumps(body, allow_nan=False, separators=(",", ":")).encode()
        headers = [
            ("Content-Type", "application/json; charset=utf-8"),
            ("Content-Length", str(len(data))),
            ("Cache-Control", "no-store"),
        ]
        if status.startswith("405"):
            headers.append(("Allow", "GET"))
        start_response(status, headers)
        return [data]

    if environ.get("REQUEST_METHOD") != "GET":
        return reply("405 Method Not Allowed", {"error": "METHOD_NOT_ALLOWED"})

    path = environ.get("PATH_INFO", "")
    if path == "/health":
        return reply("200 OK", {"ok": True, "service": "kraken-spot-market-data"})
    if path != "/v1/kraken-spot/candles":
        return reply("404 Not Found", {"error": "NOT_FOUND"})

    token = os.environ.get("KRAKEN_SPOT_API_TOKEN", "")
    db_path = os.environ.get("KRAKEN_SPOT_DB", "")
    canonical_path = os.environ.get("KRAKEN_SPOT_CANONICAL_DB", "")
    if not token or not db_path or not canonical_path:
        return reply("503 Service Unavailable", {"error": "UNCONFIGURED"})
    supplied = environ.get("HTTP_AUTHORIZATION", "").encode()
    expected = ("Bearer " + token).encode()
    if not hmac.compare_digest(supplied, expected):
        return reply("401 Unauthorized", {"error": "UNAUTHORIZED"})

    try:
        query = candle_query(environ.get("QUERY_STRING", ""))
    except ValueError:
        return reply("400 Bad Request", {"error": "INVALID_QUERY"})

    try:
        store = KrakenSpotSQLiteStore(
            db_path,
            canonical_db_path=canonical_path,
            initialize=False,
        )
        result = store.read_window(**query)
        return reply(
            "200 OK",
            {**result, "generatedAtMs": time.time_ns() // 1_000_000},
        )
    except (OSError, sqlite3.Error, ValueError):
        return reply("503 Service Unavailable", {"error": "STORE_UNAVAILABLE"})


if __name__ == "__main__":
    from wsgiref.simple_server import make_server

    with make_server(
        "127.0.0.1", int(os.environ.get("PORT", "8790")), application
    ) as server:
        server.serve_forever()
