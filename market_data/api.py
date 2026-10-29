"""Read-only canonical candle API. Collection happens separately through sync.py."""

import hmac
import json
import os
import sqlite3
import time
from pathlib import Path
from urllib.parse import parse_qs

from market_data.store import INTERVAL_MS, MAX_CANDLES, is_postgres, read_window


def candle_query(query):
    if len(query) > 2048:
        raise ValueError("Query too long")
    params = parse_qs(query, keep_blank_values=True, strict_parsing=True, max_num_fields=5)
    required = {"symbol", "timeframe", "startMs", "endMs"}
    if not required <= params.keys() or params.keys() - required - {"asOfMs"} or any(len(v) != 1 for v in params.values()):
        raise ValueError("Invalid parameters")
    values = {key: value[0] for key, value in params.items()}
    if values["symbol"] != "BTCUSDT" or values["timeframe"] not in INTERVAL_MS:
        raise ValueError("Unsupported market")

    def integer(key):
        value = values[key]
        if not value.isascii() or not value.isdigit() or len(value) > 19:
            raise ValueError("Invalid time")
        number = int(value)
        if not 0 <= number < 2**63 - 1:
            raise ValueError("Invalid time")
        return number

    start, end = integer("startMs"), integer("endMs")
    step = INTERVAL_MS[values["timeframe"]]
    if start % step or end % step or not 0 < end - start <= MAX_CANDLES * step:
        raise ValueError("Invalid or oversized window")
    return dict(symbol=values["symbol"], timeframe=values["timeframe"], start_ms=start,
                end_ms=end, as_of_ms=integer("asOfMs") if "asOfMs" in values else None)


def application(environ, start_response):
    def reply(status, body):
        data = json.dumps(body, allow_nan=False, separators=(",", ":")).encode()
        headers = [("Content-Type", "application/json; charset=utf-8"),
                   ("Content-Length", str(len(data))), ("Cache-Control", "no-store")]
        if status.startswith("405"):
            headers.append(("Allow", "GET"))
        start_response(status, headers)
        return [data]

    if environ.get("REQUEST_METHOD") != "GET":
        return reply("405 Method Not Allowed", {"error": "METHOD_NOT_ALLOWED"})
    path = environ.get("PATH_INFO", "")
    if path == "/health":
        return reply("200 OK", {"ok": True, "service": "canonical-market-data"})
    if path != "/v1/candles":
        return reply("404 Not Found", {"error": "NOT_FOUND"})
    token = os.environ.get("MARKET_DATA_TOKEN", "")
    db_path = os.environ.get("DATA_LAKE_DATABASE_URL") or os.environ.get("MARKET_DATA_DB", "")
    if not token or not db_path:
        return reply("503 Service Unavailable", {"error": "UNCONFIGURED"})
    if not hmac.compare_digest(environ.get("HTTP_AUTHORIZATION", "").encode(), ("Bearer " + token).encode()):
        return reply("401 Unauthorized", {"error": "UNAUTHORIZED"})
    try:
        query = candle_query(environ.get("QUERY_STRING", ""))
    except ValueError:
        return reply("400 Bad Request", {"error": "INVALID_QUERY"})
    try:
        if not is_postgres(db_path) and not Path(db_path).is_file():
            return reply("503 Service Unavailable", {"error": "STORE_UNAVAILABLE"})
        result = read_window(db_path, **query)
        return reply("200 OK", {**result, "generatedAtMs": time.time_ns() // 1_000_000})
    except (OSError, sqlite3.Error, ValueError):
        return reply("503 Service Unavailable", {"error": "STORE_UNAVAILABLE"})


if __name__ == "__main__":
    from wsgiref.simple_server import make_server

    with make_server("127.0.0.1", int(os.environ.get("PORT", "8788")), application) as server:
        server.serve_forever()
