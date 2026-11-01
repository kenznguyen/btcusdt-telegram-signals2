"""Read-only FastAPI access to canonical candles and causal research datasets."""

import hmac
import os
import sqlite3
import time

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from market_data.api import candle_query
from market_data.store import INTERVAL_MS, read_window


def now_ms():
    return time.time_ns() // 1_000_000


def create_app(database=None, token=None):
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

    @app.middleware("http")
    async def response_headers(request, call_next):
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

    @app.exception_handler(HTTPException)
    async def route_error(request, error):
        code = "METHOD_NOT_ALLOWED" if error.status_code == 405 else "NOT_FOUND"
        return JSONResponse({"error": code}, status_code=error.status_code, headers=error.headers)

    @app.get("/health")
    def health():
        return {"ok": True, "service": "canonical-data-lake", "liveTradingSupported": False}

    def authorize(request: Request):
        location = database if database is not None else os.environ.get("DATA_LAKE_DATABASE_URL") or os.environ.get("MARKET_DATA_DB")
        access = token if token is not None else os.environ.get("MARKET_DATA_TOKEN", "")
        if not location or not isinstance(access, str) or not 1 <= len(access) <= 4096:
            return None, JSONResponse({"error": "UNCONFIGURED"}, status_code=503)
        auth = request.headers.getlist("authorization")
        if len(auth) != 1 or len(auth[0]) > 4103 or not hmac.compare_digest(auth[0].encode(), ("Bearer " + access).encode()):
            return None, JSONResponse({"error": "UNAUTHORIZED"}, status_code=401)
        return location, None

    @app.get("/ready")
    def ready(request: Request):
        location, error = authorize(request)
        if error is not None:
            return error
        if request.scope["query_string"]:
            return JSONResponse({"error": "INVALID_QUERY"}, status_code=400)
        from data_lake.readiness import check_readiness
        result = check_readiness(location, now_ms())
        return JSONResponse(result, status_code=200 if result["ready"] else 503)

    def read(request: Request):
        location, error = authorize(request)
        if error is not None:
            return error
        current = now_ms()
        try:
            raw_query = request.scope["query_string"]
            if len(raw_query) > 2048:
                raise ValueError("Oversized query")
            query = candle_query(raw_query.decode("ascii"))
            step = INTERVAL_MS[query["timeframe"]]
            if query["end_ms"] > current // step * step or (query["as_of_ms"] is not None and query["as_of_ms"] > current):
                raise ValueError("Future query")
        except (ValueError, UnicodeError):
            return JSONResponse({"error": "INVALID_QUERY"}, status_code=400)
        try:
            window = read_window(location, **query)
            observed = now_ms()
            if any(row["availableAtMs"] > observed for row in window["candles"]):
                raise ValueError("Future observation")
            if request.url.path == "/v1/candles":
                result = window
            elif request.url.path == "/v1/features":
                from data_lake.analytics import build_features
                result = build_features(window)
            else:
                from data_lake.analytics import CROSS_ANALYSIS_DELAY_MS, build_cross_analysis
                from market_data.archive import read_snapshots
                cutoff = query["as_of_ms"] if query["as_of_ms"] is not None else observed
                snapshots = read_snapshots(location, max(0, query["start_ms"] - 60_000),
                                           query["end_ms"] + CROSS_ANALYSIS_DELAY_MS, cutoff)
                result = build_cross_analysis(window, snapshots, as_of_ms=cutoff)
            return JSONResponse({**result, "generatedAtMs": now_ms()})
        except (OSError, sqlite3.Error, ValueError, TypeError, KeyError, OverflowError):
            code = "STORE_UNAVAILABLE" if request.url.path == "/v1/candles" else "DATA_UNAVAILABLE"
            return JSONResponse({"error": code}, status_code=503)

    for path in ("/v1/candles", "/v1/features", "/v1/cross-analysis"):
        app.add_api_route(path, read, methods=["GET"])
    return app


app = create_app()
