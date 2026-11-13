"""One-shot, read-only T1 Order Book V1 HTTP client for T2."""

from dataclasses import dataclass, field
import json
import re
from urllib.parse import urlsplit

import requests

from core_runtime.orderbook_contract import (
    OrderBookContractError,
    validate_snapshot,
)


_ROUTE = "/internal/v1/orderbook/btcusdt"
_DEFAULT_MAX_RESPONSE_BYTES = 65_536
_MAX_ALLOWED_RESPONSE_BYTES = 65_536
_SAFE_INTEGER = 9_007_199_254_740_991
_TOKEN = re.compile(r"[A-Za-z0-9._~+/-]+=*\\Z")


class OrderBookHttpError(RuntimeError):
    """Stable, credential-safe error returned by the transport boundary."""

    def __init__(self, code, *, contract_code=None):
        self.code = code
        self.contract_code = contract_code
        super().__init__(code)


@dataclass(frozen=True)
class OrderBookHttpConfig:
    """Loopback-only T1 endpoint configuration with bounded resource limits."""

    base_url: str
    token: str = field(repr=False)
    timeout_connect_s: float = 0.25
    timeout_read_s: float = 0.5
    max_response_bytes: int = _DEFAULT_MAX_RESPONSE_BYTES

    def __post_init__(self):
        if not isinstance(self.base_url, str) or not self.base_url.strip():
            raise OrderBookHttpError("CONFIG_INVALID")
        if (not isinstance(self.token, str) or not self.token
                or len(self.token) > 4096 or not _TOKEN.fullmatch(self.token)):
            raise OrderBookHttpError("CONFIG_INVALID")
        for value in (self.timeout_connect_s, self.timeout_read_s):
            if (isinstance(value, bool) or not isinstance(value, (int, float))
                    or not 0 < value <= 5):
                raise OrderBookHttpError("CONFIG_INVALID")
        if (type(self.max_response_bytes) is not int
                or not 1 <= self.max_response_bytes <= _MAX_ALLOWED_RESPONSE_BYTES):
            raise OrderBookHttpError("CONFIG_INVALID")

        normalized = self.base_url.strip()
        try:
            parsed = urlsplit(normalized)
            port = parsed.port
        except ValueError:
            raise OrderBookHttpError("CONFIG_INVALID") from None
        if (parsed.scheme != "http" or parsed.hostname != "127.0.0.1"
                or parsed.username is not None or parsed.password is not None
                or parsed.query or parsed.fragment or parsed.path not in ("", "/")
                or (port is not None and not 1 <= port <= 65535)):
            raise OrderBookHttpError("CONFIG_INVALID")
        object.__setattr__(self, "base_url", normalized.rstrip("/"))


class OrderBookHttpClient:
    """Fetch exactly one T1 snapshot per call; never retries or falls back."""

    def __init__(self, config, *, session=None):
        if not isinstance(config, OrderBookHttpConfig):
            raise OrderBookHttpError("CONFIG_INVALID")
        self.config = config
        self.session = session if session is not None else requests.Session()
        self.url = config.base_url + _ROUTE

    @staticmethod
    def _unique_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate JSON key")
            result[key] = value
        return result

    @staticmethod
    def _reject_json_constant(_value):
        raise ValueError("non-standard JSON constant")

    def fetch(self, *, decision_at_ms):
        """Perform one bounded GET and pass its complete document to V1 validation."""
        if (type(decision_at_ms) is not int
                or not 0 <= decision_at_ms <= _SAFE_INTEGER):
            raise OrderBookHttpError("DECISION_TIMESTAMP_INVALID")

        response = None
        try:
            response = self.session.get(
                self.url,
                headers={
                    "Authorization": "Bearer " + self.config.token,
                    "Accept": "application/json",
                    "Accept-Encoding": "identity",
                    "Cache-Control": "no-store",
                },
                timeout=(self.config.timeout_connect_s, self.config.timeout_read_s),
                stream=True,
                allow_redirects=False,
                verify=True,
            )
            status = response.status_code
            if status == 401:
                raise OrderBookHttpError("AUTH_REJECTED")
            if status != 200:
                raise OrderBookHttpError("HTTP_UNAVAILABLE")

            headers = response.headers
            media_type = headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
            if media_type != "application/json":
                raise OrderBookHttpError("RESPONSE_CONTENT_TYPE_INVALID")
            encoding = headers.get("Content-Encoding", "identity").strip().lower()
            if encoding not in ("", "identity"):
                raise OrderBookHttpError("RESPONSE_ENCODING_INVALID")

            declared_length = headers.get("Content-Length")
            if declared_length is not None:
                if not re.fullmatch(r"[0-9]+", str(declared_length).strip()):
                    raise OrderBookHttpError("RESPONSE_LENGTH_INVALID")
                if int(declared_length) > self.config.max_response_bytes:
                    raise OrderBookHttpError("RESPONSE_TOO_LARGE")

            body = bytearray()
            for chunk in response.iter_content(chunk_size=8192):
                if not chunk:
                    continue
                if not isinstance(chunk, bytes):
                    raise OrderBookHttpError("RESPONSE_BODY_INVALID")
                body.extend(chunk)
                if len(body) > self.config.max_response_bytes:
                    raise OrderBookHttpError("RESPONSE_TOO_LARGE")

            try:
                decoded = bytes(body).decode("utf-8", errors="strict")
                snapshot = json.loads(
                    decoded,
                    object_pairs_hook=self._unique_object,
                    parse_constant=self._reject_json_constant,
                )
            except (UnicodeDecodeError, json.JSONDecodeError, ValueError,
                    TypeError, RecursionError):
                raise OrderBookHttpError("RESPONSE_JSON_INVALID") from None

            if not isinstance(snapshot, dict):
                raise OrderBookHttpError("RESPONSE_JSON_INVALID")
        except OrderBookHttpError:
            raise
        except requests.exceptions.Timeout:
            raise OrderBookHttpError("HTTP_TIMEOUT") from None
        except requests.exceptions.ConnectionError:
            raise OrderBookHttpError("HTTP_UNAVAILABLE") from None
        except requests.exceptions.RequestException:
            raise OrderBookHttpError("HTTP_UNAVAILABLE") from None
        finally:
            if response is not None:
                response.close()

        try:
            return validate_snapshot(snapshot, decision_at_ms=decision_at_ms)
        except OrderBookContractError as exc:
            code = str(exc) or "SNAPSHOT_INVALID"
            raise OrderBookHttpError("SNAPSHOT_INVALID", contract_code=code) from None
