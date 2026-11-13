"""Offline parser for captured Binance USDⓈ-M BTCUSDT funding-rate pages.

No HTTP client, credentials, account data or network access is used here.
The caller must first verify the page bytes against the D07.2 provenance
envelope; this parser independently rechecks byte length and SHA-256.
"""

import hashlib
import json
import re
from decimal import Decimal, DecimalException


_SYMBOL = "BTCUSDT"
_RECORD_FIELDS = {"symbol", "fundingRate", "fundingTime", "markPrice", "rateType"}
_SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")
_MAX_PAGE_BYTES = 5_000_000
_MAX_PAGE_RECORDS = 1_000


class _DuplicateJsonKey(Exception):
    pass


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateJsonKey
        result[key] = value
    return result


def _text(value, code, *, limit=256):
    if (not isinstance(value, str) or not value.strip()
            or len(value) > limit or not value.isprintable()):
        raise ValueError(code)
    return value


def _timestamp(value, code):
    if type(value) is not int or value < 0:
        raise ValueError(code)
    return value


def _decimal(value, code, *, positive=False):
    if not isinstance(value, str) or not value.strip() or len(value) > 256:
        raise ValueError(code)
    try:
        number = Decimal(value)
    except (DecimalException, TypeError, ValueError):
        raise ValueError(code) from None
    if (not number.is_finite() or len(number.as_tuple().digits) > 80
            or not -200 <= number.as_tuple().exponent <= 200
            or number.adjusted() > 200 or (positive and number <= 0)):
        raise ValueError(code)
    return value


def parse_binance_usdm_funding_rate_page(
    raw_page, *, evidence_snapshot_id, expected_sha256, expected_byte_length,
    start_at_ms, end_at_ms, expected_record_count=None,
):
    """Parse one captured /fapi/v1/fundingRate response page.

    The API's startTime/endTime parameters are inclusive; this parser consumes
    the caller's canonical half-open scope [start_at_ms, end_at_ms). It accepts
    only BTCUSDT Regular funding records. Special rate records are rejected.
    """
    if not isinstance(raw_page, bytes) or not raw_page or len(raw_page) > _MAX_PAGE_BYTES:
        raise ValueError("BINANCE_FUNDING_PAGE_BYTES_INVALID")
    if type(expected_byte_length) is not int or expected_byte_length < 0:
        raise ValueError("BINANCE_FUNDING_PAGE_LENGTH_INVALID")
    if len(raw_page) != expected_byte_length:
        raise ValueError("BINANCE_FUNDING_PAGE_LENGTH_MISMATCH")
    if not isinstance(expected_sha256, str) or not _SHA256.fullmatch(expected_sha256):
        raise ValueError("BINANCE_FUNDING_PAGE_DIGEST_INVALID")
    actual_digest = "sha256:" + hashlib.sha256(raw_page).hexdigest()
    if actual_digest != expected_sha256:
        raise ValueError("BINANCE_FUNDING_PAGE_DIGEST_MISMATCH")

    snapshot_id = _text(evidence_snapshot_id, "BINANCE_FUNDING_SNAPSHOT_ID_INVALID")
    start = _timestamp(start_at_ms, "BINANCE_FUNDING_SCOPE_INVALID")
    end = _timestamp(end_at_ms, "BINANCE_FUNDING_SCOPE_INVALID")
    if start >= end:
        raise ValueError("BINANCE_FUNDING_SCOPE_INVALID")
    if expected_record_count is not None and (
        type(expected_record_count) is not int or expected_record_count < 0
    ):
        raise ValueError("BINANCE_FUNDING_PAGE_COUNT_INVALID")

    try:
        decoded = raw_page.decode("utf-8")
        records = json.loads(decoded, object_pairs_hook=_unique_object)
    except _DuplicateJsonKey:
        raise ValueError("BINANCE_FUNDING_JSON_DUPLICATE_KEY") from None
    except (UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError):
        raise ValueError("BINANCE_FUNDING_JSON_INVALID") from None

    if not isinstance(records, list):
        raise ValueError("BINANCE_FUNDING_PAGE_SCHEMA_INVALID")
    if len(records) > _MAX_PAGE_RECORDS:
        raise ValueError("BINANCE_FUNDING_PAGE_TOO_LARGE")
    if expected_record_count is not None and len(records) != expected_record_count:
        raise ValueError("BINANCE_FUNDING_PAGE_COUNT_MISMATCH")

    events = []
    previous_time = None
    for record in records:
        if not isinstance(record, dict) or set(record) != _RECORD_FIELDS:
            raise ValueError("BINANCE_FUNDING_RECORD_FIELDS_INVALID")
        if record["symbol"] != _SYMBOL:
            raise ValueError("BINANCE_FUNDING_SYMBOL_INVALID")
        if record["rateType"] != "Regular":
            raise ValueError("BINANCE_FUNDING_RATE_TYPE_UNSUPPORTED")
        funding_time = _timestamp(
            record["fundingTime"], "BINANCE_FUNDING_TIME_INVALID"
        )
        if not start <= funding_time < end:
            raise ValueError("BINANCE_FUNDING_TIME_OUTSIDE_SCOPE")
        if previous_time is not None:
            if funding_time == previous_time:
                raise ValueError("BINANCE_FUNDING_TIME_DUPLICATE")
            if funding_time < previous_time:
                raise ValueError("BINANCE_FUNDING_PAGE_ORDER_INVALID")
        previous_time = funding_time
        rate = _decimal(record["fundingRate"], "BINANCE_FUNDING_RATE_INVALID")
        mark = _decimal(
            record["markPrice"], "BINANCE_FUNDING_MARK_PRICE_INVALID", positive=True
        )
        events.append({
            "eventId": f"binance-usdm-funding:{_SYMBOL}:{funding_time}",
            "symbol": _SYMBOL,
            "fundingTimeMs": funding_time,
            "fundingRate": rate,
            "markPrice": mark,
            "sourceSnapshotId": snapshot_id,
        })
    return events
