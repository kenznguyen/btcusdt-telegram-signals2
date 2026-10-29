"""Read-only BTCUSDT consumer: validate canonical API data before exposing it."""

import hashlib
from http.client import HTTPException
import json
import re
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit, urlunsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from market_data.store import (Candle, EXCHANGE, INTERVAL_MS, MARKET_TYPE,
                               MAX_CANDLES, MAX_TIMESTAMP, PRICE_FIELDS, SYMBOL)


MAX_RESPONSE_BYTES = 4 * 1024 * 1024
REQUEST_TIMEOUT_SECONDS = 15
QUERY_FIELDS = ("exchange", "marketType", "symbol", "timeframe", "startMs", "endMs", "asOfMs", "candles")


class DataLakeError(ValueError):
    """A bounded, credential-free failure code suitable for consumer diagnostics."""


def _require(condition, code):
    if not condition:
        raise DataLakeError(code)


def _stamp(value):
    _require(type(value) is int and 0 <= value <= MAX_TIMESTAMP, "INVALID_TIMESTAMP")
    return value


def _window(timeframe, start_ms, end_ms, limit=MAX_CANDLES):
    _require(isinstance(timeframe, str) and timeframe in INTERVAL_MS, "UNSUPPORTED_TIMEFRAME")
    start, end, step = _stamp(start_ms), _stamp(end_ms), INTERVAL_MS[timeframe]
    _require(start % step == end % step == 0 and 0 < end-start <= limit*step, "INVALID_WINDOW")
    return start, end, step


def _json_object(pairs):
    result = {}
    for key, value in pairs:
        _require(key not in result, "DUPLICATE_JSON_FIELD")
        result[key] = value
    return result


def _reject_constant(value):
    raise DataLakeError("INVALID_JSON_NUMBER")


def _base_url(value):
    _require(isinstance(value, str) and 1 <= len(value) <= 2048
             and all(33 <= ord(c) <= 126 for c in value) and "\\" not in value, "INVALID_BASE_URL")
    try:
        parts = urlsplit(value)
        hostname, port = parts.hostname, parts.port
        _require(parts.scheme in ("http", "https") and hostname and parts.username is None
                 and parts.password is None and not parts.query and not parts.fragment
                 and parts.path in ("", "/") and (port is None or 1 <= port <= 65535), "INVALID_BASE_URL")
        _require(hostname in ("127.0.0.1", "::1") or re.fullmatch(r"[A-Za-z0-9.-]+", hostname), "INVALID_BASE_URL")
        _require(parts.scheme == "https" or hostname in ("127.0.0.1", "::1"), "HTTPS_REQUIRED")
    except (ValueError, AttributeError):
        raise DataLakeError("INVALID_BASE_URL") from None
    return urlunsplit((parts.scheme, parts.netloc, "", "", ""))


def _validate_response(body, timeframe, start, end, as_of, now):
    """Rebuild the store's canonical hash and coverage without filling missing bars."""
    _require(isinstance(body, dict), "INVALID_RESPONSE")
    required = set(QUERY_FIELDS) | {"datasetVersion", "coverage"}
    _require(required <= body.keys() and not body.keys()-required-{"generatedAtMs"}, "INVALID_RESPONSE_SCHEMA")
    _require((body["exchange"], body["marketType"], body["symbol"], body["timeframe"])
             == (EXCHANGE, MARKET_TYPE, SYMBOL, timeframe), "MARKET_MISMATCH")
    _require(_stamp(body["startMs"]) == start and _stamp(body["endMs"]) == end
             and body["asOfMs"] == as_of, "QUERY_MISMATCH")
    if body["asOfMs"] is not None:
        _stamp(body["asOfMs"])
    if "generatedAtMs" in body:
        _require(_stamp(body["generatedAtMs"]) <= now, "FUTURE_RESPONSE")
    records, cursor, gaps, step = body["candles"], start, [], INTERVAL_MS[timeframe]
    _require(isinstance(records, list) and len(records) <= MAX_CANDLES, "INVALID_CANDLES")
    for record in records:
        _require(isinstance(record, dict), "INVALID_CANDLE")
        try:
            candle = Candle(timeframe, record["openTimeMs"],
                            *(record[field] for field in PRICE_FIELDS), record["availableAtMs"])
        except (KeyError, TypeError, ValueError):
            raise DataLakeError("INVALID_CANDLE") from None
        _require(type(record.get("isClosed")) is bool and record == candle.as_dict(), "INVALID_CANDLE_PROVENANCE")
        opening = candle.open_time_ms
        _require(cursor <= opening < end and candle.available_at_ms <= now
                 and (as_of is None or candle.available_at_ms <= as_of), "INVALID_CANDLE_TIME")
        if opening > cursor:
            gaps.append({"startMs": cursor, "endMs": opening})
        cursor = opening + step
    if cursor < end:
        gaps.append({"startMs": cursor, "endMs": end})
    coverage = body["coverage"]
    _require(isinstance(coverage, dict) and type(coverage.get("expected")) is int
             and type(coverage.get("returned")) is int and type(coverage.get("complete")) is bool,
             "INVALID_COVERAGE")
    for gap in coverage.get("gaps", []):
        _require(isinstance(gap, dict) and set(gap) == {"startMs", "endMs"}, "INVALID_COVERAGE")
        _stamp(gap["startMs"])
        _stamp(gap["endMs"])
    expected = {"expected": (end-start)//step, "returned": len(records), "complete": not gaps, "gaps": gaps}
    _require(coverage == expected, "INVALID_COVERAGE")
    payload = {key: body[key] for key in QUERY_FIELDS}
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    _require(body["datasetVersion"] == "sha256:"+digest, "DATASET_HASH_MISMATCH")
    return body


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class DataLakeClient:
    """HTTPS (or literal loopback HTTP) client, with no exchange fallback or writes."""

    def __init__(self, base_url, token):
        self.base_url = _base_url(base_url)
        _require(isinstance(token, str) and 1 <= len(token) <= 4096
                 and all(33 <= ord(c) <= 126 for c in token), "INVALID_TOKEN")
        self._token = token
        self._opener = build_opener(_NoRedirect())

    def read_candles(self, timeframe, start_ms, end_ms, as_of_ms=None):
        start, end, _ = _window(timeframe, start_ms, end_ms)
        now = time.time_ns() // 1_000_000
        if as_of_ms is not None:
            _require(_stamp(as_of_ms) <= now, "FUTURE_AS_OF")
        params = {"symbol": SYMBOL, "timeframe": timeframe, "startMs": start, "endMs": end}
        if as_of_ms is not None:
            params["asOfMs"] = as_of_ms
        request = Request(self.base_url+"/v1/candles?"+urlencode(params), method="GET", headers={
            "Authorization": "Bearer "+self._token, "Accept": "application/json", "Accept-Encoding": "identity"})
        try:
            with self._opener.open(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
                _require(response.status == 200, "DATA_LAKE_HTTP_FAILURE")
                _require(response.headers.get_content_type() == "application/json", "INVALID_CONTENT_TYPE")
                _require(response.headers.get("Content-Encoding", "identity").lower() == "identity", "INVALID_CONTENT_ENCODING")
                size = response.headers.get("Content-Length")
                if size is not None:
                    _require(size.isascii() and size.isdigit() and int(size) <= MAX_RESPONSE_BYTES, "RESPONSE_TOO_LARGE")
                raw = response.read(MAX_RESPONSE_BYTES+1)
                _require(len(raw) <= MAX_RESPONSE_BYTES, "RESPONSE_TOO_LARGE")
                if size is not None:
                    _require(len(raw) == int(size), "TRUNCATED_RESPONSE")
            body = json.loads(raw.decode("utf-8"), object_pairs_hook=_json_object, parse_constant=_reject_constant)
            return _validate_response(body, timeframe, start, end, as_of_ms, time.time_ns() // 1_000_000)
        except DataLakeError:
            raise
        except HTTPError as exc:
            exc.close()
            raise DataLakeError("DATA_LAKE_HTTP_FAILURE") from None
        except (URLError, OSError, HTTPException, UnicodeError, ValueError, TypeError, KeyError, OverflowError, RecursionError):
            raise DataLakeError("DATA_LAKE_UNAVAILABLE_OR_INVALID") from None
