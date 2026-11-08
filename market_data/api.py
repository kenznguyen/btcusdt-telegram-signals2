"""Read-only canonical candle API. Collection happens separately through sync.py."""

import hmac
import json
import os
import sqlite3
import time
from urllib.parse import parse_qs

from market_data.store import INTERVAL_MS
from market_data.postgres import StoreUnavailable
from market_data.storage import create_store_from_env


MAX_API_CANDLES = 2000
VOLUME_UNIT = "BTC_BASE_ASSET"
DATA_SOURCE = "ccxt.binanceusdm"


def _freshness(candles, timeframe, start_ms, end_ms, generated_at_ms):
    interval = INTERVAL_MS[timeframe]
    latest_expected = min(end_ms - interval, (generated_at_ms // interval) * interval - interval)
    latest = candles[-1] if candles else None
    if latest is None:
        return {
            "latestExpectedOpenTimeMs": latest_expected,
            "latestReturnedOpenTimeMs": None,
            "latestCloseTimeMs": None,
            "latestAvailableAtMs": None,
            "observationAgeMs": None,
            "closeLagMs": None,
            "evaluable": False,
        }

    open_time = latest.get("openTimeMs")
    close_time = latest.get("closeTimeMs")
    available_at = latest.get("availableAtMs")
    valid_timestamps = all(
        type(value) is int and value >= 0
        for value in (open_time, close_time, available_at, generated_at_ms)
    )
    observation_age = generated_at_ms - available_at if valid_timestamps else None
    close_lag = generated_at_ms - close_time if valid_timestamps else None
    evaluable = bool(valid_timestamps and observation_age >= 0 and close_lag >= 0)
    return {
        "latestExpectedOpenTimeMs": latest_expected,
        "latestReturnedOpenTimeMs": open_time,
        "latestCloseTimeMs": close_time,
        "latestAvailableAtMs": available_at,
        "observationAgeMs": observation_age,
        "closeLagMs": close_lag,
        "evaluable": evaluable,
    }


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
    if start % step or end % step or not 0 < end - start <= MAX_API_CANDLES * step:
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
    if not token:
        return reply("503 Service Unavailable", {"error": "UNCONFIGURED"})
    backend = os.environ.get("MARKET_DATA_BACKEND", "sqlite").strip().lower()
    if backend == "sqlite" and not os.environ.get("MARKET_DATA_DB"):
        return reply("503 Service Unavailable", {"error": "UNCONFIGURED"})
    if not hmac.compare_digest(environ.get("HTTP_AUTHORIZATION", "").encode(), ("Bearer " + token).encode()):
        return reply("401 Unauthorized", {"error": "UNAUTHORIZED"})
    try:
        query = candle_query(environ.get("QUERY_STRING", ""))
    except ValueError:
        return reply("400 Bad Request", {"error": "INVALID_QUERY"})
    try:
        store = create_store_from_env()
        result = store.read_window(**query)
        generated_at_ms = time.time_ns() // 1_000_000
        return reply("200 OK", {
            **result,
            "contractVersion": "1.0.0",
            "schemaVersion": 1,
            "volumeUnit": VOLUME_UNIT,
            "source": DATA_SOURCE,
            "generatedAtMs": generated_at_ms,
            "freshness": _freshness(
                result["candles"], query["timeframe"], query["start_ms"],
                query["end_ms"], generated_at_ms,
            ),
        })
    except (OSError, sqlite3.Error, ValueError, StoreUnavailable):
        return reply("503 Service Unavailable", {"error": "STORE_UNAVAILABLE"})


if __name__ == "__main__":
    from wsgiref.simple_server import make_server

    with make_server("127.0.0.1", int(os.environ.get("PORT", "8788")), application) as server:
        server.serve_forever()
