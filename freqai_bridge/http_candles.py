"""Strict read-only HTTP client for T0 Candle Contract v1 (BTCUSDT M15)."""

from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
import json
import re
import time
from urllib.parse import urlsplit

import requests


_ENDPOINT = "/v1/candles"
_INTERVAL_MS = 900_000
_MAX_BARS = 32
_MAX_BODY_BYTES = 256 * 1024
_CONNECT_TIMEOUT_S = 3
_READ_TIMEOUT_S = 5
_MAX_ATTEMPTS = 3
_BACKOFF_SECONDS = (0.25, 0.5)
_DATASET_VERSION = re.compile(r"sha256:[0-9a-f]{64}\Z")
_ENVELOPE_FIELDS = {
    "contractVersion", "schemaVersion", "exchange", "marketType", "symbol",
    "timeframe", "startMs", "endMs", "asOfMs", "candles", "datasetVersion",
    "coverage", "volumeUnit", "source", "generatedAtMs", "freshness",
}
_CANDLE_FIELDS = {
    "exchange", "marketType", "symbol", "timeframe", "openTimeMs", "closeTimeMs",
    "open", "high", "low", "close", "volume", "isClosed", "availableAtMs",
    "availabilityKind", "quality", "source",
}
_FRESHNESS_FIELDS = {
    "latestExpectedOpenTimeMs", "latestReturnedOpenTimeMs", "latestCloseTimeMs",
    "latestAvailableAtMs", "observationAgeMs", "closeLagMs", "evaluable",
}


class CandleHttpError(Exception):
    """Safe, stable error category; never includes endpoint, credentials or body."""

    def __init__(self, reason):
        self.reason = reason
        super().__init__(reason)


@dataclass(frozen=True)
class CandleHttpConfig:
    base_url: str
    token: str = field(repr=False)
    max_lag_ms: int

    def __post_init__(self):
        if not isinstance(self.base_url, str) or not self.base_url.strip():
            raise CandleHttpError("CONFIG_INVALID")
        if (not isinstance(self.token, str) or not self.token
                or len(self.token) > 4096
                or not re.fullmatch(r"[A-Za-z0-9._~+/=-]+", self.token)):
            raise CandleHttpError("CONFIG_INVALID")
        if type(self.max_lag_ms) is not int or not 1 <= self.max_lag_ms <= 120_000:
            raise CandleHttpError("CONFIG_INVALID")

        normalized_url = self.base_url.strip()
        try:
            parsed = urlsplit(normalized_url)
            port = parsed.port
        except ValueError:
            raise CandleHttpError("CONFIG_INVALID") from None
        if parsed.scheme not in ("https", "http") or not parsed.hostname:
            raise CandleHttpError("CONFIG_INVALID")
        if port is not None and not 1 <= port <= 65535:
            raise CandleHttpError("CONFIG_INVALID")
        if parsed.username is not None or parsed.password is not None or parsed.query or parsed.fragment:
            raise CandleHttpError("CONFIG_INVALID")
        loopback = parsed.hostname.lower() in ("localhost", "127.0.0.1", "::1")
        if parsed.scheme != "https" and not loopback:
            raise CandleHttpError("CONFIG_INVALID")
        if parsed.path not in ("", "/"):
            raise CandleHttpError("CONFIG_INVALID")
        object.__setattr__(self, "base_url", normalized_url.rstrip("/"))


class CandleHttpClient:
    """Fetch and fully validate one bounded M15 window; never falls back."""

    def __init__(self, config, session=None, sleep=None, clock_ms=None):
        if not isinstance(config, CandleHttpConfig):
            raise CandleHttpError("CONFIG_INVALID")
        self.config = config
        self.session = session if session is not None else requests.Session()
        self.sleep = sleep if sleep is not None else time.sleep
        self.clock_ms = clock_ms if clock_ms is not None else lambda: time.time_ns() // 1_000_000
        self.url = config.base_url.rstrip("/") + _ENDPOINT

    @staticmethod
    def _timestamp(value):
        return type(value) is int and 0 <= value < 2**63 - 1

    @staticmethod
    def _decimal(value, *, allow_zero=False):
        if not isinstance(value, str) or not 1 <= len(value) <= 128:
            raise CandleHttpError("CANDLE_INVALID")
        try:
            number = Decimal(value)
        except (InvalidOperation, ValueError):
            raise CandleHttpError("CANDLE_INVALID") from None
        if not number.is_finite() or len(number.as_tuple().digits) > 40:
            raise CandleHttpError("CANDLE_INVALID")
        if not -30 <= number.as_tuple().exponent <= 30 or number.adjusted() > 30:
            raise CandleHttpError("CANDLE_INVALID")
        if number < 0 or (not allow_zero and number == 0):
            raise CandleHttpError("CANDLE_INVALID")
        return number

    @staticmethod
    def _unique_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate JSON key")
            result[key] = value
        return result

    def _request(self, start_ms, end_ms, as_of_ms):
        params = {
            "symbol": "BTCUSDT",
            "timeframe": "15m",
            "startMs": start_ms,
            "endMs": end_ms,
            "asOfMs": as_of_ms,
        }
        headers = {
            "Authorization": "Bearer " + self.config.token,
            "Accept": "application/json",
            "Accept-Encoding": "identity",
            "Cache-Control": "no-store",
        }
        for attempt in range(_MAX_ATTEMPTS):
            response = None
            try:
                response = self.session.get(
                    self.url,
                    params=params,
                    headers=headers,
                    timeout=(_CONNECT_TIMEOUT_S, _READ_TIMEOUT_S),
                    stream=True,
                    allow_redirects=False,
                    verify=True,
                )
                status = response.status_code
                if status == 503 and attempt < _MAX_ATTEMPTS - 1:
                    response.close()
                    self.sleep(_BACKOFF_SECONDS[attempt])
                    continue
                if status != 200:
                    if status == 401:
                        reason = "AUTH_REJECTED"
                    elif status == 503:
                        reason = "HTTP_UNAVAILABLE"
                    else:
                        reason = "HTTP_UNAVAILABLE"
                    raise CandleHttpError(reason)
                content_type = response.headers.get("Content-Type", "")
                media_type = content_type.split(";", 1)[0].strip().lower()
                if media_type != "application/json":
                    raise CandleHttpError("CONTRACT_UNSUPPORTED")
                content_encoding = response.headers.get("Content-Encoding", "identity").strip().lower()
                if content_encoding not in ("", "identity"):
                    raise CandleHttpError("CONTRACT_UNSUPPORTED")
                content_length = response.headers.get("Content-Length")
                if content_length is not None:
                    try:
                        declared_length = int(content_length)
                    except ValueError:
                        raise CandleHttpError("CONTRACT_UNSUPPORTED") from None
                    if declared_length < 0:
                        raise CandleHttpError("CONTRACT_UNSUPPORTED")
                    if declared_length > _MAX_BODY_BYTES:
                        raise CandleHttpError("RESPONSE_TOO_LARGE")
                body = bytearray()
                for chunk in response.iter_content(chunk_size=8192):
                    if not chunk:
                        continue
                    body.extend(chunk)
                    if len(body) > _MAX_BODY_BYTES:
                        raise CandleHttpError("RESPONSE_TOO_LARGE")
                try:
                    decoded = bytes(body).decode("utf-8", errors="strict")
                    payload = json.loads(decoded, object_pairs_hook=self._unique_object,
                                         parse_constant=lambda _: (_ for _ in ()).throw(ValueError("invalid constant")))
                except (UnicodeDecodeError, json.JSONDecodeError, ValueError, TypeError):
                    raise CandleHttpError("CONTRACT_UNSUPPORTED") from None
                if not isinstance(payload, dict):
                    raise CandleHttpError("CONTRACT_UNSUPPORTED")
                return payload
            except CandleHttpError:
                raise
            except requests.exceptions.SSLError:
                raise CandleHttpError("HTTP_UNAVAILABLE") from None
            except (requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout,
                    requests.exceptions.ConnectionError, requests.exceptions.ChunkedEncodingError) as error:
                if attempt >= _MAX_ATTEMPTS - 1:
                    reason = "HTTP_TIMEOUT" if isinstance(error, requests.exceptions.Timeout) else "HTTP_UNAVAILABLE"
                    raise CandleHttpError(reason) from None
                self.sleep(_BACKOFF_SECONDS[attempt])
            except requests.exceptions.RequestException:
                raise CandleHttpError("HTTP_UNAVAILABLE") from None
            finally:
                if response is not None:
                    response.close()
        raise CandleHttpError("HTTP_UNAVAILABLE")

    def fetch(self, start_ms, end_ms, as_of_ms):
        if not all(self._timestamp(value) for value in (start_ms, end_ms, as_of_ms)):
            raise CandleHttpError("RANGE_MISMATCH")
        if start_ms % _INTERVAL_MS or end_ms % _INTERVAL_MS:
            raise CandleHttpError("RANGE_MISMATCH")
        slots = (end_ms - start_ms) // _INTERVAL_MS
        if not 1 <= slots <= _MAX_BARS:
            raise CandleHttpError("RANGE_MISMATCH")

        payload = self._request(start_ms, end_ms, as_of_ms)
        self._validate(payload, start_ms, end_ms, as_of_ms, slots)
        return payload

    def _validate(self, payload, start_ms, end_ms, as_of_ms, slots):
        if set(payload) != _ENVELOPE_FIELDS:
            raise CandleHttpError("CONTRACT_UNSUPPORTED")
        if payload["contractVersion"] != "1.0.0" or type(payload["schemaVersion"]) is not int or payload["schemaVersion"] != 1:
            raise CandleHttpError("CONTRACT_UNSUPPORTED")

        identity = {
            "exchange": "binance",
            "marketType": "USDT_PERPETUAL",
            "symbol": "BTCUSDT",
            "timeframe": "15m",
            "startMs": start_ms,
            "endMs": end_ms,
            "asOfMs": as_of_ms,
            "volumeUnit": "BTC_BASE_ASSET",
            "source": "ccxt.binanceusdm",
        }
        for key, expected in identity.items():
            if type(payload.get(key)) is not type(expected) or payload.get(key) != expected:
                raise CandleHttpError("IDENTITY_MISMATCH" if key in ("exchange", "marketType", "symbol", "timeframe", "volumeUnit", "source") else "RANGE_MISMATCH")

        dataset_version = payload["datasetVersion"]
        if not isinstance(dataset_version, str) or not _DATASET_VERSION.fullmatch(dataset_version):
            raise CandleHttpError("CONTRACT_UNSUPPORTED")

        coverage = payload["coverage"]
        if not isinstance(coverage, dict) or set(coverage) != {"expected", "returned", "complete", "gaps"}:
            raise CandleHttpError("COVERAGE_INCOMPLETE")
        if (type(coverage["expected"]) is not int or coverage["expected"] != slots
                or type(coverage["returned"]) is not int or coverage["returned"] != slots
                or coverage["complete"] is not True or coverage["gaps"] != []):
            raise CandleHttpError("COVERAGE_INCOMPLETE")

        generated = payload["generatedAtMs"]
        if not self._timestamp(generated):
            raise CandleHttpError("FRESHNESS_UNAVAILABLE")
        try:
            now = self.clock_ms()
        except Exception:
            raise CandleHttpError("FRESHNESS_UNAVAILABLE") from None
        if not self._timestamp(now) or as_of_ms > now or generated > now:
            raise CandleHttpError("FRESHNESS_UNAVAILABLE")

        candles = payload["candles"]
        if not isinstance(candles, list) or len(candles) != slots:
            raise CandleHttpError("COVERAGE_INCOMPLETE")
        expected_open_times = list(range(start_ms, end_ms, _INTERVAL_MS))
        for candle, expected_open in zip(candles, expected_open_times):
            if not isinstance(candle, dict) or set(candle) != _CANDLE_FIELDS:
                raise CandleHttpError("CANDLE_INVALID")
            candle_identity = {
                "exchange": "binance", "marketType": "USDT_PERPETUAL",
                "symbol": "BTCUSDT", "timeframe": "15m", "source": "ccxt.binanceusdm",
            }
            if any(candle.get(k) != v or type(candle.get(k)) is not str for k, v in candle_identity.items()):
                raise CandleHttpError("CANDLE_INVALID")
            opened = candle["openTimeMs"]
            closed = candle["closeTimeMs"]
            available = candle["availableAtMs"]
            if (not self._timestamp(opened) or not self._timestamp(closed)
                    or not self._timestamp(available) or opened != expected_open
                    or closed != opened + _INTERVAL_MS or candle["isClosed"] is not True
                    or candle["availabilityKind"] != "FIRST_OBSERVED"
                    or candle["quality"] != "VALIDATED"
                    or available < closed or available > as_of_ms or available > generated):
                raise CandleHttpError("CANDLE_INVALID")
            prices = {name: self._decimal(candle[name]) for name in ("open", "high", "low", "close")}
            volume = self._decimal(candle["volume"], allow_zero=True)
            if not (prices["low"] <= min(prices["open"], prices["close"])
                    <= max(prices["open"], prices["close"]) <= prices["high"]) or volume < 0:
                raise CandleHttpError("CANDLE_INVALID")

        if not isinstance(payload["freshness"], dict) or set(payload["freshness"]) != _FRESHNESS_FIELDS:
            raise CandleHttpError("FRESHNESS_UNAVAILABLE")
        freshness = payload["freshness"]
        latest = candles[-1]
        latest_values = {
            "latestReturnedOpenTimeMs": latest["openTimeMs"],
            "latestCloseTimeMs": latest["closeTimeMs"],
            "latestAvailableAtMs": latest["availableAtMs"],
            "observationAgeMs": generated - latest["availableAtMs"],
            "closeLagMs": generated - latest["closeTimeMs"],
        }
        if (not self._timestamp(freshness["latestExpectedOpenTimeMs"])
                or any(type(freshness.get(k)) is not int or freshness.get(k) != v for k, v in latest_values.items())
                or freshness.get("evaluable") is not True):
            raise CandleHttpError("FRESHNESS_UNAVAILABLE")
        ingestion_lag = latest["availableAtMs"] - latest["closeTimeMs"]
        if ingestion_lag < 0:
            raise CandleHttpError("FRESHNESS_UNAVAILABLE")
        if ingestion_lag > self.config.max_lag_ms:
            raise CandleHttpError("FRESHNESS_EXCEEDED")
