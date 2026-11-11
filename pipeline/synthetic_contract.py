"""Pure, bounded parser for synthetic S1 contract fixtures; never a trust verifier."""
from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from typing import Any

SCHEMA_VERSION = "synthetic-contract-fixture/v1"
PURPOSE = "PARSER_CONTRACT_TEST_ONLY"
MAX_INPUT_BYTES = 8192
MAX_DEPTH = 8
MAX_OBJECT_MEMBERS = 32
MAX_ARRAY_ITEMS = 64
MAX_STRING_VALUE_BYTES = 1024
MAX_STRING_KEY_BYTES = 256
MAX_SCALAR_NODES = 256
D10_TYPES = frozenset({
    "SYNTHETIC_OBJECT", "SYNTHETIC_EVIDENCE", "SYNTHETIC_ISSUER_CLAIM",
    "SYNTHETIC_POLICY_CLAIM", "SYNTHETIC_INVENTORY_CLAIM",
    "SYNTHETIC_SENSITIVITY_CLAIM", "SYNTHETIC_HOLD_CLAIM",
    "SYNTHETIC_DEPENDENCY_CLAIM", "SYNTHETIC_COPY_LINEAGE_CLAIM",
    "SYNTHETIC_FRESHNESS_CLAIM", "SYNTHETIC_BINDING_CLAIM",
})
TOP_REQUIRED = frozenset({"schema_version", "fixture_id", "case_id", "fixture_type", "subject", "purpose", "claims"})
TOP_OPTIONAL = frozenset({"notes"})
SUBJECT_FIELDS = frozenset({"object_id", "version_id", "namespace"})
FIXTURE_RE = re.compile(r"syn-fixture-[A-Za-z0-9][A-Za-z0-9._-]{0,63}\Z")
SYNTHETIC_RE = re.compile(r"syn-[A-Za-z0-9][A-Za-z0-9._-]{0,95}\Z")
CASE_RE = re.compile(r"SYN-(?:0[1-9]|[12][0-9]|3[0-8])\Z")


@dataclass(frozen=True)
class ParseResult:
    value: Any | None
    reason_code: str | None
    trusted: bool = False
    execution_authorized: bool = False


class _Pairs(list):
    """Distinguishes JSON objects from arrays while preserving duplicate keys."""


class _ParseFailure(Exception):
    def __init__(self, reason_code: str):
        self.reason_code = reason_code


def _reject_constant(_value: str) -> None:
    raise _ParseFailure("PARSE_NONFINITE_NUMBER")


def _decode_json(raw: bytes) -> tuple[Any | None, str | None]:
    try:
        source = raw.decode("utf-8", "strict")
    except UnicodeDecodeError:
        return None, "PARSE_INVALID_UTF8"
    decoder = json.JSONDecoder(object_pairs_hook=_Pairs, parse_constant=_reject_constant)
    try:
        value, end = decoder.raw_decode(source.lstrip(" \t\r\n"))
    except _ParseFailure as exc:
        return None, exc.reason_code
    except (json.JSONDecodeError, RecursionError, ValueError):
        return None, "PARSE_INVALID_JSON"
    leading = len(source) - len(source.lstrip(" \t\r\n"))
    if source[leading + end:].strip(" \t\r\n"):
        return None, "PARSE_TRAILING_CONTENT"
    return value, None


def _has_duplicate_keys(node: Any) -> bool:
    if isinstance(node, _Pairs):
        seen = set()
        for key, child in node:
            if key in seen or _has_duplicate_keys(child):
                return True
            seen.add(key)
        return False
    if isinstance(node, list):
        return any(_has_duplicate_keys(child) for child in node)
    return False


def _plain_and_validate_structure(node: Any, depth: int = 0) -> tuple[Any, str | None, int]:
    """Convert duplicate-checked pairs and enforce D11 structural limits."""
    if isinstance(node, _Pairs):
        level = depth + 1
        if level > MAX_DEPTH:
            return None, "LIMIT_DEPTH", 0
        if len(node) > MAX_OBJECT_MEMBERS:
            return None, "LIMIT_OBJECT_MEMBERS", 0
        result = {}
        seen = set()
        scalars = 0
        for key, child in node:
            if key in seen:
                return None, "PARSE_DUPLICATE_KEY", 0
            seen.add(key)
            if any(0xD800 <= ord(char) <= 0xDFFF for char in key):
                return None, "PARSE_INVALID_UNICODE", 0
            key_bytes = len(key.encode("utf-8"))
            if key_bytes > MAX_STRING_KEY_BYTES:
                return None, "LIMIT_STRING_KEY_BYTES", 0
            converted, reason, count = _plain_and_validate_structure(child, level)
            if reason:
                return None, reason, 0
            result[key] = converted
            scalars += count
        return result, None, scalars
    if isinstance(node, list):
        level = depth + 1
        if level > MAX_DEPTH:
            return None, "LIMIT_DEPTH", 0
        if len(node) > MAX_ARRAY_ITEMS:
            return None, "LIMIT_ARRAY_ITEMS", 0
        result = []
        scalars = 0
        for child in node:
            converted, reason, count = _plain_and_validate_structure(child, level)
            if reason:
                return None, reason, 0
            result.append(converted)
            scalars += count
        return result, None, scalars
    if isinstance(node, str):
        if any(0xD800 <= ord(char) <= 0xDFFF for char in node):
            return None, "PARSE_INVALID_UNICODE", 0
        if len(node.encode("utf-8")) > MAX_STRING_VALUE_BYTES:
            return None, "LIMIT_STRING_VALUE_BYTES", 0
        return node, None, 1
    if type(node) in (int, float, bool) or node is None:
        if type(node) is float and not math.isfinite(node):
            return None, "PARSE_NONFINITE_NUMBER", 0
        return node, None, 1
    return None, "PARSE_INVALID_JSON", 0


def _schema_reason(value: Any) -> str | None:
    if type(value) is not dict:
        return "SCHEMA_TYPE_MISMATCH"
    fields = set(value)
    if fields - (TOP_REQUIRED | TOP_OPTIONAL):
        return "SCHEMA_FIELD_UNKNOWN"
    if not TOP_REQUIRED.issubset(fields):
        return "SCHEMA_FIELD_MISSING"
    if type(value["schema_version"]) is not str or value["schema_version"] != SCHEMA_VERSION:
        return "SCHEMA_VERSION_UNSUPPORTED"
    if type(value["purpose"]) is not str or value["purpose"] != PURPOSE:
        return "SCHEMA_PURPOSE_UNSUPPORTED"
    if type(value["fixture_id"]) is not str:
        return "SCHEMA_TYPE_MISMATCH"
    if not FIXTURE_RE.fullmatch(value["fixture_id"]):
        return "SCHEMA_SYNTHETIC_ID_INVALID"
    if type(value["case_id"]) is not str:
        return "SCHEMA_TYPE_MISMATCH"
    if not CASE_RE.fullmatch(value["case_id"]):
        return "SCHEMA_VALUE_OUT_OF_RANGE"
    if type(value["fixture_type"]) is not str:
        return "SCHEMA_TYPE_MISMATCH"
    if value["fixture_type"] not in D10_TYPES:
        return "SCHEMA_VALUE_OUT_OF_RANGE"
    subject = value["subject"]
    if type(subject) is not dict:
        return "SCHEMA_TYPE_MISMATCH"
    subject_fields = set(subject)
    if subject_fields - SUBJECT_FIELDS:
        return "SCHEMA_FIELD_UNKNOWN"
    if subject_fields != SUBJECT_FIELDS:
        return "SCHEMA_FIELD_MISSING"
    if any(type(subject[key]) is not str for key in SUBJECT_FIELDS):
        return "SCHEMA_TYPE_MISMATCH"
    if any(not SYNTHETIC_RE.fullmatch(subject[key]) for key in SUBJECT_FIELDS):
        return "SCHEMA_SYNTHETIC_ID_INVALID"
    # No non-empty claims schema has been ratified for the selected S1 cases.
    if type(value["claims"]) is not dict or value["claims"]:
        return "SCHEMA_TYPE_MISMATCH"
    if "notes" in value:
        if type(value["notes"]) is not str:
            return "SCHEMA_TYPE_MISMATCH"
        if not SYNTHETIC_RE.fullmatch(value["notes"]):
            return "SCHEMA_SYNTHETIC_ID_INVALID"
    return None


def parse_fixture(raw: bytes) -> ParseResult:
    """Parse one synthetic fixture. Exactly one fixed reason code is returned."""
    if type(raw) is not bytes:
        return ParseResult(None, "INPUT_NOT_BYTES")
    if len(raw) > MAX_INPUT_BYTES:
        return ParseResult(None, "LIMIT_RAW_BYTES")
    parsed, reason = _decode_json(raw)
    if reason:
        return ParseResult(None, reason)
    try:
        if _has_duplicate_keys(parsed):
            return ParseResult(None, "PARSE_DUPLICATE_KEY")
    except RecursionError:
        return ParseResult(None, "LIMIT_DEPTH")
    value, reason, scalar_count = _plain_and_validate_structure(parsed)
    if reason:
        return ParseResult(None, reason)
    if scalar_count > MAX_SCALAR_NODES:
        return ParseResult(None, "LIMIT_SCALAR_NODES")
    reason = _schema_reason(value)
    if reason:
        return ParseResult(None, reason)
    return ParseResult(value, None)
