"""Synthetic-only T0 checkpoint contract oracle; no runtime/provider integration."""
from __future__ import annotations
import hashlib
import json
import re
import struct
from decimal import Decimal, InvalidOperation
from typing import Any, Iterable

INTERVAL_MS = {"15m": 900_000, "1h": 3_600_000}
MAX_TIMESTAMP = 2**63 - 1
ROW_FIELDS = {"exchange", "market_type", "symbol", "timeframe", "open_time_ms",
              "open", "high", "low", "close", "volume", "available_at_ms"}
_UNSIGNED = re.compile(r"^(?:0|[1-9][0-9]*)$")
_DECIMAL = re.compile(r"^(?:0|[1-9][0-9]*(?:\.[0-9]*[1-9])?|0\.[0-9]*[1-9])$")
_SHA256_HEX = re.compile(r"^[0-9a-f]{64}$")


def _pairs_no_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON object key: {key}")
        result[key] = value
    return result


def _validate_value(value):
    if value is None or type(value) is bool:
        return
    if isinstance(value, str):
        try:
            value.encode("utf-8", errors="strict")
        except UnicodeEncodeError as exc:
            raise ValueError("unpaired surrogate is forbidden") from exc
        return
    if type(value) in (int, float):
        raise ValueError("JSON numeric values are forbidden; encode quantities as strings")
    if isinstance(value, list):
        for item in value:
            _validate_value(item)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValueError("JSON object keys must be strings")
            _validate_value(key)
            _validate_value(item)
        return
    raise ValueError(f"unsupported JSON value type: {type(value).__name__}")


def parse_json_strict(data: bytes) -> Any:
    if not isinstance(data, bytes) or data.startswith(b"\xef\xbb\xbf"):
        raise ValueError("input must be UTF-8 bytes without BOM")
    try:
        value = json.loads(data.decode("utf-8", errors="strict"),
                           object_pairs_hook=_pairs_no_duplicates,
                           parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("invalid UTF-8 JSON") from exc
    _validate_value(value)
    return value


def _ordered(value):
    if isinstance(value, dict):
        return {k: _ordered(value[k]) for k in sorted(value, key=lambda x: x.encode("utf-16-be"))}
    if isinstance(value, list):
        return [_ordered(x) for x in value]
    return value


def canonical_json_bytes(value: Any) -> bytes:
    _validate_value(value)
    try:
        return json.dumps(_ordered(value), ensure_ascii=False, separators=(",", ":"),
                          allow_nan=False).encode("utf-8", errors="strict")
    except (UnicodeEncodeError, ValueError, TypeError) as exc:
        raise ValueError("value cannot be encoded as T0-JCS-1") from exc


def verify_canonical_bytes(data: bytes) -> Any:
    value = parse_json_strict(data)
    if canonical_json_bytes(value) != data:
        raise ValueError("input bytes are not canonical T0-JCS-1")
    return value


def _unsigned(value, field):
    if not isinstance(value, str) or not _UNSIGNED.fullmatch(value):
        raise ValueError(f"{field} must be a canonical unsigned integer string")
    result = int(value)
    if result > MAX_TIMESTAMP:
        raise ValueError(f"{field} exceeds signed 64-bit range")
    return result


def _decimal(value, field, allow_zero=False):
    if not isinstance(value, str) or not _DECIMAL.fullmatch(value):
        raise ValueError(f"{field} must be a canonical decimal string")
    try:
        number = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field} is invalid") from exc
    if not number.is_finite() or number < 0 or (number == 0 and not allow_zero):
        raise ValueError(f"{field} is outside permitted range")
    if len(number.as_tuple().digits) > 40 or not -30 <= number.as_tuple().exponent <= 30 or number.adjusted() > 30:
        raise ValueError(f"{field} exceeds Candle precision bounds")
    return number


def validate_candle_row(row, timeframe=None):
    if not isinstance(row, dict) or set(row) != ROW_FIELDS:
        raise ValueError("candle row fields do not match persisted v1 schema")
    if (row["exchange"], row["market_type"], row["symbol"]) != ("binance", "USDT_PERPETUAL", "BTCUSDT"):
        raise ValueError("candle market identity mismatch")
    tf = row["timeframe"]
    if tf not in INTERVAL_MS or (timeframe is not None and tf != timeframe):
        raise ValueError("candle timeframe mismatch")
    step = INTERVAL_MS[tf]
    opening = _unsigned(row["open_time_ms"], "open_time_ms")
    available = _unsigned(row["available_at_ms"], "available_at_ms")
    if opening % step:
        raise ValueError("candle open time is off grid")
    close_boundary = opening + step
    if close_boundary > MAX_TIMESTAMP or available < close_boundary:
        raise ValueError("candle availability precedes exclusive close boundary")
    values = {k: _decimal(row[k], k, allow_zero=(k == "volume"))
              for k in ("open", "high", "low", "close", "volume")}
    if (values["low"] > values["high"] or
            not values["low"] <= values["open"] <= values["high"] or
            not values["low"] <= values["close"] <= values["high"]):
        raise ValueError("inconsistent OHLC bounds")
    return row


def canonical_row_bytes(row):
    validate_candle_row(row)
    return canonical_json_bytes(row)


def _domain_hash(domain, payload):
    if len(payload) > 2**64 - 1:
        raise ValueError("payload too large")
    return hashlib.sha256(domain + struct.pack(">Q", len(payload)) + payload).digest()


def checkpoint_object_digest(data: bytes) -> str:
    if not isinstance(data, bytes):
        raise ValueError("canonical object must be bytes")
    verify_canonical_bytes(data)
    return _domain_hash(b"T0-EVIDENCE-OBJECT-V1\0", data).hex()


def row_leaf(row):
    return _domain_hash(b"T0-CANDLE-ROW-V1\0", canonical_row_bytes(row)).hex()


def merkle_root(leaves: Iterable[bytes]) -> bytes:
    nodes = list(leaves)
    if not nodes:
        return hashlib.sha256(b"T0-EMPTY-ROWS-V1\0").digest()
    if any(not isinstance(x, bytes) or len(x) != 32 for x in nodes):
        raise ValueError("Merkle leaves must be 32-byte SHA-256 digests")
    while len(nodes) > 1:
        next_level = []
        for i in range(0, len(nodes), 2):
            if i + 1 == len(nodes):
                next_level.append(nodes[i])
            else:
                next_level.append(hashlib.sha256(
                    b"T0-MERKLE-NODE-V1\0" + nodes[i] + nodes[i + 1]).digest())
        nodes = next_level
    return nodes[0]


def candle_rows_root(rows):
    leaves, previous, timeframe = [], None, None
    if not isinstance(rows, list):
        raise ValueError("rows must be a list")
    for row in rows:
        validate_candle_row(row)
        if timeframe is not None and row["timeframe"] != timeframe:
            raise ValueError("one row tree cannot mix timeframes")
        opening = int(row["open_time_ms"])
        if previous is not None and opening <= previous:
            raise ValueError("rows must be strictly ascending and unique")
        previous, timeframe = opening, row["timeframe"]
        leaves.append(bytes.fromhex(row_leaf(row)))
    return merkle_root(leaves).hex()


def _invalid(reason):
    return {"status": "INVALID", "reason": reason}


def assess_partition(timeframe, start_ms, end_ms, rows, *, as_of_ms=None, input_complete=True):
    if timeframe not in INTERVAL_MS:
        return _invalid("UNSUPPORTED_TIMEFRAME")
    try:
        start, end = _unsigned(start_ms, "start_ms"), _unsigned(end_ms, "end_ms")
        as_of = None if as_of_ms is None else _unsigned(as_of_ms, "as_of_ms")
    except ValueError:
        return _invalid("INVALID_RANGE_OR_AS_OF")
    step = INTERVAL_MS[timeframe]
    if start >= end or start % step or end % step:
        return _invalid("RANGE_NOT_NONEMPTY_AND_ALIGNED")
    if not isinstance(rows, list):
        return {"status": "UNKNOWN", "reason": "ROW_INPUT_UNAVAILABLE"}
    if not isinstance(input_complete, bool):
        return _invalid("INPUT_COMPLETENESS_FLAG_INVALID")
    expected_count, previous, openings = (end - start) // step, None, []
    for row in rows:
        try:
            validate_candle_row(row, timeframe=timeframe)
            opening, available = int(row["open_time_ms"]), int(row["available_at_ms"])
        except (ValueError, TypeError, KeyError):
            return _invalid("ROW_SCHEMA_OR_CANDLE_VALIDATION_FAILED")
        if opening < start or opening >= end:
            return _invalid("ROW_OUTSIDE_PARTITION_RANGE")
        if previous is not None and opening <= previous:
            return _invalid("DUPLICATE_OR_OUT_OF_ORDER")
        if as_of is not None and available > as_of:
            return _invalid("ROW_EXCLUDED_BY_AS_OF_FILTER")
        previous = opening
        openings.append(opening)
    if not input_complete:
        return {"status": "UNKNOWN", "reason": "INPUT_BYTES_OR_PAGE_INCOMPLETE"}
    gaps, cursor = [], start
    for opening in openings:
        if opening > cursor:
            gaps.append({"start_ms": str(cursor), "end_ms": str(opening),
                         "missing_count": (opening - cursor) // step})
        cursor = opening + step
    if cursor < end:
        gaps.append({"start_ms": str(cursor), "end_ms": str(end),
                     "missing_count": (end - cursor) // step})
    return {"status": "COMPLETE" if not gaps else "INCOMPLETE",
            "expected_count": expected_count, "returned_count": len(openings), "gaps": gaps}


_PARTITION_FIELDS = {"exchange", "market_type", "symbol", "timeframe", "start_ms", "end_ms",
                     "row_count", "first_open_time_ms", "last_open_time_ms", "row_root"}


def partition_leaf(descriptor):
    if not isinstance(descriptor, dict) or set(descriptor) != _PARTITION_FIELDS:
        raise ValueError("partition descriptor fields do not match v1 schema")
    if (descriptor["exchange"], descriptor["market_type"], descriptor["symbol"]) != ("binance", "USDT_PERPETUAL", "BTCUSDT"):
        raise ValueError("partition market identity mismatch")
    tf = descriptor["timeframe"]
    if tf not in INTERVAL_MS:
        raise ValueError("partition timeframe invalid")
    step = INTERVAL_MS[tf]
    start, end = _unsigned(descriptor["start_ms"], "start_ms"), _unsigned(descriptor["end_ms"], "end_ms")
    count = _unsigned(descriptor["row_count"], "row_count")
    if start >= end or start % step or end % step or count > (end - start) // step:
        raise ValueError("partition range/count invalid")
    root = descriptor["row_root"]
    if not isinstance(root, str) or not _SHA256_HEX.fullmatch(root):
        raise ValueError("partition row_root must be lowercase SHA-256 hex")
    empty_root = hashlib.sha256(b"T0-EMPTY-ROWS-V1\0").hexdigest()
    first, last = descriptor["first_open_time_ms"], descriptor["last_open_time_ms"]
    if count == 0:
        if first is not None or last is not None or root != empty_root:
            raise ValueError("empty partition requires null boundaries and empty root")
    else:
        first, last = _unsigned(first, "first_open_time_ms"), _unsigned(last, "last_open_time_ms")
        if (root == empty_root or first < start or last >= end or first > last or
                first % step or last % step or (count == 1 and first != last) or
                (count > 1 and first == last)):
            raise ValueError("partition first/last boundaries invalid")
    return _domain_hash(b"T0-PARTITION-V1\0", canonical_json_bytes(descriptor)).hex()


def checkpoint_content_root(partitions):
    if not isinstance(partitions, list) or not partitions:
        raise ValueError("checkpoint requires at least one partition")
    rank, previous_key, previous_end, leaves = {"15m": 0, "1h": 1}, None, {}, []
    for item in partitions:
        digest = partition_leaf(item)
        key = (rank[item["timeframe"]], int(item["start_ms"]), int(item["end_ms"]))
        if previous_key is not None and key <= previous_key:
            raise ValueError("partition descriptors must be uniquely ordered")
        start = int(item["start_ms"])
        if item["timeframe"] in previous_end and start < previous_end[item["timeframe"]]:
            raise ValueError("partition ranges must not overlap within timeframe")
        previous_end[item["timeframe"]] = int(item["end_ms"])
        previous_key = key
        leaves.append(bytes.fromhex(digest))
    return merkle_root(leaves).hex()
