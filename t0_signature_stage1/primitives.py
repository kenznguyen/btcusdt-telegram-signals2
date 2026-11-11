"""Pure byte-level primitives for the synthetic-only A2.2 Stage I harness.

No signing keys, cryptographic signature verification, network or filesystem I/O
are implemented here. Floating-point JSON tokens are rejected because the
current A2.2 Stage I schemas use strings for logical integers and do not define
any floating-point field semantics.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import json
import re
from typing import Any


U64_MAX = (1 << 64) - 1
_JSON_SAFE_INTEGER_MAX = (1 << 53) - 1
_B64URL_RE = re.compile(r"[A-Za-z0-9_-]*\Z")
_U64_RE = re.compile(r"(?:0|[1-9][0-9]*)\Z")


class StageIError(ValueError):
    """Stable, machine-readable Stage I contract error."""

    def __init__(self, reason_code: str):
        self.reason_code = reason_code
        super().__init__(reason_code)


def _reject_constant(_: str) -> None:
    raise StageIError("NONCANONICAL_STATEMENT")


def _reject_float(_: str) -> None:
    raise StageIError("NONCANONICAL_STATEMENT")


def _parse_safe_integer(token: str) -> int:
    value = int(token, 10)
    if abs(value) > _JSON_SAFE_INTEGER_MAX:
        raise StageIError("NONCANONICAL_STATEMENT")
    return value


def _object_without_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise StageIError("NONCANONICAL_STATEMENT")
        result[key] = value
    return result


def _validate_unicode(value: str) -> None:
    try:
        value.encode("utf-8", "strict")
    except UnicodeEncodeError as exc:
        raise StageIError("NONCANONICAL_STATEMENT") from exc


def _quote_string(value: str) -> str:
    _validate_unicode(value)
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def _canonical_value(value: Any) -> str:
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, str):
        return _quote_string(value)
    if isinstance(value, int):
        if abs(value) > _JSON_SAFE_INTEGER_MAX:
            raise StageIError("NONCANONICAL_STATEMENT")
        return str(value)
    if isinstance(value, float):
        raise StageIError("NONCANONICAL_STATEMENT")
    if isinstance(value, list):
        return "[" + ",".join(_canonical_value(item) for item in value) + "]"
    if isinstance(value, dict):
        for key in value:
            if not isinstance(key, str):
                raise StageIError("NONCANONICAL_STATEMENT")
            _validate_unicode(key)
        ordered_keys = sorted(value, key=lambda item: item.encode("utf-16-be"))
        return "{" + ",".join(
            _quote_string(key) + ":" + _canonical_value(value[key])
            for key in ordered_keys
        ) + "}"
    raise StageIError("NONCANONICAL_STATEMENT")


def canonicalize(value: Any) -> bytes:
    """Return canonical UTF-8 JSON bytes for the restricted T0-JCS-1 subset."""
    try:
        return _canonical_value(value).encode("utf-8", "strict")
    except StageIError:
        raise
    except (TypeError, ValueError, UnicodeError, RecursionError) as exc:
        raise StageIError("NONCANONICAL_STATEMENT") from exc


def parse_canonical_json(raw: bytes) -> Any:
    """Strictly parse and require the supplied bytes already be canonical."""
    if not isinstance(raw, bytes) or raw.startswith(b"\xef\xbb\xbf"):
        raise StageIError("NONCANONICAL_STATEMENT")
    try:
        text = raw.decode("utf-8", "strict")
        value = json.loads(
            text,
            object_pairs_hook=_object_without_duplicate_keys,
            parse_constant=_reject_constant,
            parse_float=_reject_float,
            parse_int=_parse_safe_integer,
        )
        if canonicalize(value) != raw:
            raise StageIError("NONCANONICAL_STATEMENT")
        return value
    except StageIError:
        raise
    except (UnicodeError, json.JSONDecodeError, TypeError, ValueError, RecursionError) as exc:
        raise StageIError("NONCANONICAL_STATEMENT") from exc


def parse_u64(decimal: str) -> int:
    if not isinstance(decimal, str) or not _U64_RE.fullmatch(decimal):
        raise StageIError("U64_NONCANONICAL")
    if len(decimal) > 20:
        raise StageIError("U64_OVERFLOW")
    value = int(decimal, 10)
    if value > U64_MAX:
        raise StageIError("U64_OVERFLOW")
    return value


def u64be(value: int) -> bytes:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0 or value > U64_MAX:
        raise StageIError("U64_OVERFLOW")
    return value.to_bytes(8, byteorder="big", signed=False)


def b64url_encode(data: bytes) -> str:
    if not isinstance(data, bytes):
        raise TypeError("data must be bytes")
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def b64url_decode(value: str, *, allow_empty: bool = False) -> bytes:
    if not isinstance(value, str) or (not value and not allow_empty) or not _B64URL_RE.fullmatch(value):
        raise StageIError("BASE64URL_NONCANONICAL")
    if len(value) % 4 == 1:
        raise StageIError("BASE64URL_NONCANONICAL")
    padded = value + ("=" * ((4 - len(value) % 4) % 4))
    try:
        decoded = base64.b64decode(padded, altchars=b"-_", validate=True)
    except (binascii.Error, ValueError) as exc:
        raise StageIError("BASE64URL_NONCANONICAL") from exc
    if b64url_encode(decoded) != value:
        raise StageIError("BASE64URL_NONCANONICAL")
    return decoded


def domain_separated_sha256(domain: bytes, payload: bytes) -> str:
    if not isinstance(domain, bytes) or not domain.endswith(b"\x00"):
        raise ValueError("domain must be exact UTF-8 domain bytes ending in NUL")
    if not isinstance(payload, bytes):
        raise TypeError("payload must be exact bytes")
    preimage = domain + u64be(len(payload)) + payload
    return hashlib.sha256(preimage).hexdigest()


def evidence_object_digest(payload: bytes) -> str:
    return domain_separated_sha256(b"T0-EVIDENCE-OBJECT-V1\x00", payload)


def trust_policy_body_digest(payload: bytes) -> str:
    """Fail closed: the source contract's backslash/NUL encoding is ambiguous."""
    raise StageIError("DOMAIN_SEPARATOR_ENCODING_UNRESOLVED")


def anchor_object_digest(payload: bytes) -> str:
    """Fail closed: the source contract's backslash/NUL encoding is ambiguous."""
    raise StageIError("DOMAIN_SEPARATOR_ENCODING_UNRESOLVED")


def signature_envelope_digest(payload: bytes) -> str:
    """Fail closed: the A2.2 source's backslash/NUL encoding is ambiguous."""
    raise StageIError("DOMAIN_SEPARATOR_ENCODING_UNRESOLVED")
