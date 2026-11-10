"""Read-only SQLite snapshot for the separately approved T0 G4 runtime gate.

This module never provisions schema, acquires/renews/releases leases, or writes candles.
It is not installed or invoked on the VPS by this change.
"""
import hashlib
import ipaddress
import json
import sqlite3
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import (
    HTTPRedirectHandler,
    ProxyHandler,
    Request,
    build_opener,
)

from market_data.store import INTERVAL_MS

LEASE_NAME = "binance-btcusdt-canonical"
REQUIRED_CANDLE_COLUMNS = {
    "exchange", "market_type", "symbol", "timeframe", "open_time_ms",
    "available_at_ms",
}
REQUIRED_LEASE_COLUMNS = {
    "lease_name", "owner", "generation", "expires_at_ms",
}


def _table_columns(connection, table):
    return {
        row[1] for row in connection.execute(
            "PRAGMA table_info(" + table + ")"
        ).fetchall()
    }


def inspect_sqlite_read_only(db_path, *, now_ms):
    """Return a sanitized, point-in-time SQLite/lease/watermark snapshot.

    The database must already exist. All SQL is read-only and the connection
    is opened with SQLite URI mode=ro plus PRAGMA query_only=ON.
    """
    if type(now_ms) is not int or now_ms < 0:
        raise ValueError("now_ms must be a nonnegative integer")
    path = Path(db_path).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError("canonical SQLite database does not exist")

    uri = path.as_uri() + "?mode=ro"
    try:
        connection = sqlite3.connect(uri, uri=True, timeout=5)
    except sqlite3.Error as exc:
        raise RuntimeError("canonical SQLite database is unreadable") from exc

    try:
        connection.execute("PRAGMA query_only=ON")
        if connection.execute("PRAGMA query_only").fetchone()[0] != 1:
            raise RuntimeError("SQLite query_only could not be enforced")

        integrity = connection.execute("PRAGMA integrity_check").fetchone()
        if not integrity or integrity[0] != "ok":
            raise RuntimeError("SQLite integrity check failed")

        tables = {
            row[0] for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        if "candles" not in tables:
            raise RuntimeError("required candles table is missing")
        if "feeder_leases" not in tables:
            raise RuntimeError("required feeder_leases table is missing")
        if not REQUIRED_CANDLE_COLUMNS <= _table_columns(connection, "candles"):
            raise RuntimeError("candles table schema is incompatible")
        if not REQUIRED_LEASE_COLUMNS <= _table_columns(connection, "feeder_leases"):
            raise RuntimeError("feeder_leases table schema is incompatible")

        connection.execute("BEGIN")
        lease_rows = connection.execute(
            """SELECT owner, generation, expires_at_ms
               FROM feeder_leases WHERE lease_name=?""",
            (LEASE_NAME,),
        ).fetchall()
        if len(lease_rows) > 1:
            raise RuntimeError("canonical lease identity is not unique")
        if not lease_rows:
            lease = {
                "state": "MISSING",
                "valid": False,
                "generation": None,
                "expires_at_ms": None,
                "owner_fingerprint": None,
            }
        else:
            owner, generation, expires_at_ms = lease_rows[0]
            valid_fields = (
                isinstance(owner, str) and bool(owner.strip())
                and type(generation) is int and generation >= 1
                and type(expires_at_ms) is int and expires_at_ms >= 0
            )
            valid = bool(valid_fields and expires_at_ms > now_ms)
            fingerprint = (
                hashlib.sha256(owner.encode("utf-8")).hexdigest()[:16]
                if isinstance(owner, str) and owner else None
            )
            lease = {
                "state": "VALID" if valid else (
                    "EXPIRED" if valid_fields and expires_at_ms <= now_ms
                    else "INVALID"
                ),
                "valid": valid,
                "generation": generation if type(generation) is int else None,
                "expires_at_ms": expires_at_ms if type(expires_at_ms) is int else None,
                "owner_fingerprint": fingerprint,
            }

        timeframes = {}
        for timeframe, interval_ms in INTERVAL_MS.items():
            row = connection.execute(
                """SELECT open_time_ms, available_at_ms FROM candles
                   WHERE exchange='binance' AND market_type='USDT_PERPETUAL'
                     AND symbol='BTCUSDT' AND timeframe=?
                   ORDER BY open_time_ms DESC LIMIT 1""",
                (timeframe,),
            ).fetchone()
            if row is None:
                timeframes[timeframe] = {
                    "latest_open_time_ms": None,
                    "latest_close_time_ms": None,
                    "latest_available_at_ms": None,
                    "close_lag_ms": None,
                }
                continue
            open_time_ms, available_at_ms = row
            if (type(open_time_ms) is not int or type(available_at_ms) is not int
                    or open_time_ms < 0 or available_at_ms < 0):
                raise RuntimeError("candle watermark contains invalid timestamps")
            close_time_ms = open_time_ms + interval_ms
            timeframes[timeframe] = {
                "latest_open_time_ms": open_time_ms,
                "latest_close_time_ms": close_time_ms,
                "latest_available_at_ms": available_at_ms,
                "close_lag_ms": now_ms - close_time_ms,
            }

        return {
            "integrity": "ok",
            "lease": lease,
            "timeframes": timeframes,
            "observed_at_ms": now_ms,
            "read_only": True,
        }
    except sqlite3.Error as exc:
        raise RuntimeError("read-only SQLite inspection failed") from exc
    finally:
        connection.close()


# HTTP probes are intentionally loopback-only. The detailed Flask health service
# is separately configured; it is never inferred from the candle API port.
MAX_HTTP_BODY_BYTES = 1_048_576
HTTP_TIMEOUT_SECONDS = 3


class ProbeError(RuntimeError):
    """A bounded runtime probe failed closed."""


class _RejectRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _loopback_base_url(value):
    if not isinstance(value, str) or not value.strip():
        raise ProbeError("LOOPBACK_BASE_URL_REQUIRED")
    try:
        parsed = urlsplit(value.strip())
        host = parsed.hostname
        if (parsed.scheme not in ("http", "https") or not host
                or parsed.username is not None or parsed.password is not None
                or parsed.query or parsed.fragment or parsed.path not in ("", "/")):
            raise ValueError("invalid URL structure")
        is_loopback = host.lower() == "localhost"
        if not is_loopback:
            is_loopback = ipaddress.ip_address(host).is_loopback
        if not is_loopback:
            raise ValueError("non-loopback host")
        # Accessing .port also validates malformed/out-of-range ports.
        port = parsed.port
        netloc = f"[{host}]" if ":" in host else host
        if port is not None:
            netloc += f":{port}"
        return f"{parsed.scheme}://{netloc}"
    except (ValueError, TypeError) as exc:
        raise ProbeError("URL_MUST_TARGET_LOOPBACK_WITHOUT_PATH_OR_CREDENTIALS") from exc


def _default_opener():
    # Ignore proxy environment variables and never follow redirects.
    return build_opener(ProxyHandler({}), _RejectRedirects())


def _request_json(opener, url, *, headers=None, timeout=HTTP_TIMEOUT_SECONDS):
    if type(timeout) not in (int, float) or not 0 < timeout <= 5:
        raise ProbeError("HTTP_TIMEOUT_OUT_OF_RANGE")
    request = Request(url, headers=headers or {}, method="GET")
    try:
        response = opener.open(request, timeout=timeout)
        with response:
            status = response.getcode()
            if status != 200:
                raise ProbeError(f"HTTP_STATUS_{status}")
            content_type = response.headers.get("Content-Type", "")
            if content_type.split(";", 1)[0].strip().lower() != "application/json":
                raise ProbeError("HTTP_CONTENT_TYPE_INVALID")
            raw = response.read(MAX_HTTP_BODY_BYTES + 1)
    except HTTPError as exc:
        raise ProbeError(f"HTTP_STATUS_{exc.code}") from None
    except (URLError, TimeoutError, OSError) as exc:
        raise ProbeError("HTTP_TRANSPORT_FAILED") from None
    if len(raw) > MAX_HTTP_BODY_BYTES:
        raise ProbeError("HTTP_RESPONSE_TOO_LARGE")
    try:
        body = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise ProbeError("HTTP_JSON_INVALID") from None
    if not isinstance(body, dict):
        raise ProbeError("HTTP_JSON_OBJECT_REQUIRED")
    return body


def _validate_candle_response(body, timeframe, start_ms, end_ms, as_of_ms):
    interval = INTERVAL_MS[timeframe]
    expected_open_times = [start_ms, start_ms + interval]
    if (
        body.get("exchange") != "binance"
        or body.get("marketType") != "USDT_PERPETUAL"
        or body.get("symbol") != "BTCUSDT"
        or body.get("timeframe") != timeframe
        or body.get("startMs") != start_ms
        or body.get("endMs") != end_ms
        or body.get("asOfMs") != as_of_ms
        or body.get("contractVersion") != "1.0.0"
        or body.get("schemaVersion") != 1
        or body.get("volumeUnit") != "BTC_BASE_ASSET"
        or body.get("source") != "ccxt.binanceusdm"
        or not isinstance(body.get("datasetVersion"), str)
        or not body["datasetVersion"].startswith("sha256:")
    ):
        raise ProbeError(f"{timeframe}_CONTRACT_IDENTITY_INVALID")

    coverage = body.get("coverage")
    candles = body.get("candles")
    if (
        not isinstance(coverage, dict)
        or coverage.get("expected") != 2
        or coverage.get("returned") != 2
        or coverage.get("complete") is not True
        or coverage.get("gaps") != []
        or not isinstance(candles, list)
        or len(candles) != 2
    ):
        raise ProbeError(f"{timeframe}_COVERAGE_INCOMPLETE")

    for candle, expected_open in zip(candles, expected_open_times):
        if (
            not isinstance(candle, dict)
            or candle.get("exchange") != "binance"
            or candle.get("marketType") != "USDT_PERPETUAL"
            or candle.get("symbol") != "BTCUSDT"
            or candle.get("timeframe") != timeframe
            or candle.get("openTimeMs") != expected_open
            or candle.get("closeTimeMs") != expected_open + interval
            or candle.get("isClosed") is not True
            or candle.get("availabilityKind") != "FIRST_OBSERVED"
            or candle.get("quality") != "VALIDATED"
            or candle.get("source") != "ccxt.binanceusdm"
            or type(candle.get("availableAtMs")) is not int
            or candle["availableAtMs"] > as_of_ms
        ):
            raise ProbeError(f"{timeframe}_CANDLE_PROVENANCE_INVALID")

    generated_at = body.get("generatedAtMs")
    freshness = body.get("freshness")
    if type(generated_at) is not int or not isinstance(freshness, dict):
        raise ProbeError(f"{timeframe}_FRESHNESS_MISSING")
    lag = freshness.get("closeLagMs")
    observation_age = freshness.get("observationAgeMs")
    if (
        freshness.get("evaluable") is not True
        or freshness.get("latestExpectedOpenTimeMs") != end_ms - interval
        or freshness.get("latestReturnedOpenTimeMs") != end_ms - interval
        or freshness.get("latestCloseTimeMs") != end_ms
        or type(lag) is not int or not 0 <= lag < interval
        or type(observation_age) is not int or observation_age < 0
    ):
        raise ProbeError(f"{timeframe}_FRESHNESS_NOT_HEALTHY")

    return {
        "status": "PASS",
        "returned": 2,
        "close_lag_ms": lag,
        "dataset_version": body["datasetVersion"],
    }


def probe_candle_api(base_url, token, *, now_ms, timeout=HTTP_TIMEOUT_SECONDS,
                     opener_factory=None):
    """Validate the authenticated canonical candle API over loopback only."""
    if type(now_ms) is not int or now_ms < 0:
        raise ValueError("now_ms must be a nonnegative integer")
    if (not isinstance(token, str) or not token.strip()
            or any(char in token for char in "\r\n")):
        raise ProbeError("CANDLE_API_TOKEN_REQUIRED")
    base = _loopback_base_url(base_url)
    opener = opener_factory() if opener_factory else _default_opener()

    health = _request_json(opener, base + "/health", timeout=timeout)
    if health.get("ok") is not True or health.get("service") != "canonical-market-data":
        raise ProbeError("CANDLE_API_HEALTH_INVALID")

    results = {}
    for timeframe, interval in INTERVAL_MS.items():
        end_ms = (now_ms // interval) * interval
        start_ms = end_ms - 2 * interval
        query = urlencode({
            "symbol": "BTCUSDT",
            "timeframe": timeframe,
            "startMs": start_ms,
            "endMs": end_ms,
            "asOfMs": now_ms,
        })
        body = _request_json(
            opener,
            base + "/v1/candles?" + query,
            headers={"Authorization": "Bearer " + token},
            timeout=timeout,
        )
        results[timeframe] = _validate_candle_response(
            body, timeframe, start_ms, end_ms, now_ms,
        )
    return {"status": "PASS", "health": "PASS", "timeframes": results}


def probe_feeder_health(base_url, *, now_ms, timeout=HTTP_TIMEOUT_SECONDS,
                        opener_factory=None):
    """Check the separate Flask health listener; never guess its port."""
    if type(now_ms) is not int or now_ms < 0:
        raise ValueError("now_ms must be a nonnegative integer")
    if base_url is None or (isinstance(base_url, str) and not base_url.strip()):
        return {"status": "NOT_VERIFIED", "reason": "LISTENER_NOT_CONFIGURED"}
    base = _loopback_base_url(base_url)
    opener = opener_factory() if opener_factory else _default_opener()
    body = _request_json(
        opener, base + "/health/data", timeout=timeout,
    )
    timeframes = body.get("timeframes")
    if (
        body.get("state") != "HEALTHY"
        or body.get("live") is not True
        or body.get("ready") is not True
        or not isinstance(timeframes, dict)
    ):
        raise ProbeError("FEEDER_HEALTH_NOT_READY")
    for timeframe, interval_ms in INTERVAL_MS.items():
        item = timeframes.get(timeframe)
        if (
            not isinstance(item, dict)
            or item.get("state") != "HEALTHY"
            or item.get("unresolved_gap_count") != 0
            or item.get("sync_error") is not None
            or type(item.get("age_ms")) is not int
            or not 0 <= item["age_ms"] < interval_ms
            or type(item.get("latest_closed_candle_close_ms")) is not int
            or item["latest_closed_candle_close_ms"] > now_ms
            or type(item.get("last_successful_sync_ms")) is not int
            or item["last_successful_sync_ms"] > now_ms
        ):
            raise ProbeError(f"{timeframe}_FEEDER_HEALTH_NOT_READY")
    return {
        "status": "PASS",
        "timeframes": {
            timeframe: {"status": "PASS", "state": "HEALTHY"}
            for timeframe in INTERVAL_MS
        },
    }
