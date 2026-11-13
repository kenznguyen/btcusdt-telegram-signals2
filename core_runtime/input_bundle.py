"""Pure validation for immutable Core Decision Input Bundle v1."""

from decimal import Decimal, DecimalException
import hashlib
import json
import re

import rfc8785

from core_runtime.orderbook_contract import (
    OrderBookContractError,
    validate_snapshot,
)


_SAFE_INTEGER = 9_007_199_254_740_991
_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_DECIMAL_RE = re.compile(r"^-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?$")
_TOP_LEVEL = {
    "contract", "contractVersion", "schemaVersion", "bundleId",
    "createdAtMs", "decisionAtMs", "mode", "aiExecutionEnabled",
    "strategyId", "market", "marketData", "orderBook", "paperState",
    "accountRisk",
}
_MARKET = {
    "exchange": "binance", "marketType": "USDT_PERPETUAL",
    "symbol": "BTCUSDT", "decisionTimeframe": "15m",
}
_CANDLE_FIELDS = {
    "openTimeMs", "closeTimeMs", "open", "high", "low", "close",
    "volume", "isClosed", "availableAtMs", "availabilityKind",
    "quality", "source",
}
_WINDOW_FIELDS = {
    "contractVersion", "schemaVersion", "exchange", "marketType",
    "symbol", "timeframe", "volumeUnit", "startMs", "endMs",
    "asOfMs", "generatedAtMs", "datasetVersion", "candles",
    "coverage", "freshness",
}
_COVERAGE_FIELDS = {"expected", "returned", "complete", "gaps"}
_FRESHNESS_FIELDS = {
    "latestExpectedOpenTimeMs", "latestReturnedOpenTimeMs",
    "latestCloseTimeMs", "latestAvailableAtMs", "observationAgeMs",
    "closeLagMs", "evaluable",
}


class BundleValidationError(ValueError):
    """A stable, machine-readable bundle validation failure."""


def _fail(code):
    raise BundleValidationError(code)


def _safe_int(value, code):
    if type(value) is not int or value < 0 or value > _SAFE_INTEGER:
        _fail(code)
    return value


def _walk_json(value):
    if isinstance(value, float):
        _fail("JSON_FLOAT_NOT_ALLOWED")
    if isinstance(value, int) and not isinstance(value, bool):
        if abs(value) > _SAFE_INTEGER:
            _fail("JSON_INTEGER_UNSAFE")
    elif isinstance(value, dict):
        if any(not isinstance(key, str) for key in value):
            _fail("JSON_OBJECT_KEY_INVALID")
        for item in value.values():
            _walk_json(item)
    elif isinstance(value, list):
        for item in value:
            _walk_json(item)
    elif value is not None and not isinstance(value, (str, bool, int)):
        _fail("JSON_VALUE_INVALID")


def _decimal(value, code, *, positive=False, nonnegative=False, signed=True):
    if not isinstance(value, str) or not 1 <= len(value) <= 256:
        _fail(code)
    if not _DECIMAL_RE.fullmatch(value):
        _fail(code)
    try:
        number = Decimal(value)
    except (DecimalException, ValueError):
        _fail(code)
    parts = number.as_tuple()
    if (not number.is_finite() or len(parts.digits) > 80
            or not -200 <= parts.exponent <= 200
            or (number != 0 and number.adjusted() > 200)
            or (positive and number <= 0)
            or (nonnegative and number < 0)
            or (not signed and number < 0)):
        _fail(code)
    return number


def compute_bundle_id(bundle):
    """RFC 8785 SHA-256 over the bundle excluding its top-level bundleId."""
    if not isinstance(bundle, dict):
        _fail("BUNDLE_OBJECT_INVALID")
    _walk_json(bundle)
    payload = dict(bundle)
    payload.pop("bundleId", None)
    try:
        canonical = rfc8785.dumps(payload)
    except (TypeError, ValueError, OverflowError):
        _fail("BUNDLE_CANONICALIZATION_INVALID")
    return "sha256:" + hashlib.sha256(canonical).hexdigest()


def _identity_text(value, code, *, maximum=200):
    if (not isinstance(value, str) or not value.strip()
            or len(value) > maximum or not value.isprintable()):
        _fail(code)
    return value


def _validate_candle_window(window, timeframe, decision_at_ms):
    if not isinstance(window, dict) or set(window) != _WINDOW_FIELDS:
        _fail("CANDLE_ENVELOPE_INVALID")
    interval = 900_000 if timeframe == "15m" else 3_600_000
    if (window["contractVersion"] != "1.0.0"
            or type(window["schemaVersion"]) is not int
            or window["schemaVersion"] != 1
            or window["exchange"] != "binance"
            or window["marketType"] != "USDT_PERPETUAL"
            or window["symbol"] != "BTCUSDT"
            or window["timeframe"] != timeframe
            or window["volumeUnit"] != "BTC_BASE_ASSET"):
        _fail("CANDLE_PROVENANCE_INVALID")
    _identity_text(window["datasetVersion"], "CANDLE_DATASET_VERSION_INVALID")
    start = _safe_int(window["startMs"], "CANDLE_WINDOW_TIMESTAMP_INVALID")
    end = _safe_int(window["endMs"], "CANDLE_WINDOW_TIMESTAMP_INVALID")
    generated = _safe_int(window["generatedAtMs"], "CANDLE_WINDOW_TIMESTAMP_INVALID")
    if generated > decision_at_ms or (window["asOfMs"] is not None
            and _safe_int(window["asOfMs"], "CANDLE_WINDOW_TIMESTAMP_INVALID") > decision_at_ms):
        _fail("CANDLE_WINDOW_TIMESTAMP_INVALID")

    rows = window["candles"]
    if not isinstance(rows, list) or not 100 <= len(rows) <= 2_000:
        _fail("CANDLE_COUNT_INVALID")
    previous_open = None
    latest = None
    for row in rows:
        if not isinstance(row, dict) or set(row) != _CANDLE_FIELDS:
            _fail("CANDLE_ROW_INVALID")
        opened = _safe_int(row["openTimeMs"], "CANDLE_TIMESTAMP_INVALID")
        closed = _safe_int(row["closeTimeMs"], "CANDLE_TIMESTAMP_INVALID")
        available = _safe_int(row["availableAtMs"], "CANDLE_TIMESTAMP_INVALID")
        if (opened % interval != 0 or closed != opened + interval
                or (previous_open is not None and opened != previous_open + interval)
                or closed > decision_at_ms or available < closed
                or available > decision_at_ms):
            _fail("CANDLE_SEQUENCE_INVALID")
        if (row["isClosed"] is not True
                or row["availabilityKind"] != "FIRST_OBSERVED"
                or row["quality"] != "VALIDATED"
                or row["source"] != "ccxt.binanceusdm"):
            _fail("CANDLE_PROVENANCE_INVALID")
        prices = {
            key: _decimal(row[key], "CANDLE_DECIMAL_INVALID", positive=True)
            for key in ("open", "high", "low", "close")
        }
        _decimal(row["volume"], "CANDLE_DECIMAL_INVALID", nonnegative=True)
        if (prices["high"] < max(prices.values())
                or prices["low"] > min(prices.values())):
            _fail("CANDLE_OHLC_INVALID")
        previous_open = opened
        latest = row

    if start != rows[0]["openTimeMs"] or end != latest["closeTimeMs"]:
        _fail("CANDLE_WINDOW_BOUNDS_INVALID")
    coverage = window["coverage"]
    if (not isinstance(coverage, dict) or set(coverage) != _COVERAGE_FIELDS
            or coverage["complete"] is not True
            or type(coverage["expected"]) is not int
            or type(coverage["returned"]) is not int
            or coverage["expected"] != len(rows)
            or coverage["returned"] != len(rows)
            or coverage["gaps"] != []):
        _fail("CANDLE_COVERAGE_INVALID")

    freshness = window["freshness"]
    if not isinstance(freshness, dict) or set(freshness) != _FRESHNESS_FIELDS:
        _fail("CANDLE_FRESHNESS_INVALID")
    expected = {
        "latestExpectedOpenTimeMs": latest["openTimeMs"],
        "latestReturnedOpenTimeMs": latest["openTimeMs"],
        "latestCloseTimeMs": latest["closeTimeMs"],
        "latestAvailableAtMs": latest["availableAtMs"],
        "observationAgeMs": decision_at_ms - latest["availableAtMs"],
        "closeLagMs": decision_at_ms - latest["closeTimeMs"],
        "evaluable": True,
    }
    if freshness != expected:
        _fail("CANDLE_FRESHNESS_INVALID")
    if decision_at_ms - latest["closeTimeMs"] > interval:
        _fail("CANDLE_STALE")
    return latest


def _validate_book(book, decision_at_ms, max_book_age_ms):
    required = {
        "source", "connector", "symbol", "observedAtMs", "bids", "asks",
        "t1Evidence",
    }
    if not isinstance(book, dict) or set(book) != required:
        _fail("ORDER_BOOK_INVALID")
    if (book["source"], book["connector"], book["symbol"]) != (
            "t1", "binance_usdm_perpetual", "BTCUSDT"):
        _fail("ORDER_BOOK_PROVENANCE_INVALID")

    observed = _safe_int(book["observedAtMs"], "ORDER_BOOK_TIMESTAMP_INVALID")
    if observed > decision_at_ms:
        _fail("ORDER_BOOK_TIMESTAMP_INVALID")
    if decision_at_ms - observed > max_book_age_ms:
        _fail("ORDER_BOOK_STALE")

    evidence = book["t1Evidence"]
    evidence_fields = {
        "contractVersion", "market", "snapshotLastUpdateId", "firstAppliedU",
        "lastAppliedU", "sourceTimestampMs", "observedAtMs",
        "decisionWatermark", "generation", "snapshotId", "continuity",
        "freshness", "depth", "complete",
    }
    if not isinstance(evidence, dict) or set(evidence) != evidence_fields:
        _fail("ORDER_BOOK_T1_EVIDENCE_INVALID")
    if evidence["observedAtMs"] != observed:
        _fail("ORDER_BOOK_T1_EVIDENCE_INVALID")

    projected = {}
    for side in ("bids", "asks"):
        levels = book[side]
        if not isinstance(levels, list) or not 1 <= len(levels) <= 20:
            _fail("ORDER_BOOK_LEVEL_INVALID")
        rows = []
        for level in levels:
            if not isinstance(level, dict) or set(level) != {"price", "quantity"}:
                _fail("ORDER_BOOK_LEVEL_INVALID")
            _decimal(level["price"], "ORDER_BOOK_LEVEL_INVALID", positive=True)
            _decimal(level["quantity"], "ORDER_BOOK_LEVEL_INVALID", positive=True)
            rows.append([level["price"], level["quantity"]])
        projected[side] = rows

    snapshot = {
        "contractVersion": evidence["contractVersion"],
        "symbol": book["symbol"],
        "market": evidence["market"],
        "bids": projected["bids"],
        "asks": projected["asks"],
        "snapshotLastUpdateId": evidence["snapshotLastUpdateId"],
        "firstAppliedU": evidence["firstAppliedU"],
        "lastAppliedU": evidence["lastAppliedU"],
        "sourceTimestampMs": evidence["sourceTimestampMs"],
        "observedAtMs": evidence["observedAtMs"],
        "decisionWatermark": evidence["decisionWatermark"],
        "generation": evidence["generation"],
        "snapshotId": evidence["snapshotId"],
        "continuity": evidence["continuity"],
        "freshness": evidence["freshness"],
        "depth": evidence["depth"],
        "complete": evidence["complete"],
    }
    identity = dict(snapshot)
    identity.pop("snapshotId")
    expected_snapshot_id = "sha256:" + hashlib.sha256(
        json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    if evidence["snapshotId"] != expected_snapshot_id:
        _fail("ORDER_BOOK_T1_SNAPSHOT_ID_MISMATCH")

    try:
        accepted = validate_snapshot(snapshot, decision_at_ms=decision_at_ms)
    except OrderBookContractError as exc:
        _fail("ORDER_BOOK_T1_" + str(exc))

    if accepted["bids"] != projected["bids"] or accepted["asks"] != projected["asks"]:
        _fail("ORDER_BOOK_T1_PROJECTION_MISMATCH")


def _validate_paper_state(state):
    if not isinstance(state, dict) or set(state) != {
        "positionBase", "averageEntryPrice", "strategyState"
    }:
        _fail("CORE_STATE_INVALID")
    position = _decimal(state["positionBase"], "CORE_STATE_INVALID")
    average = _decimal(state["averageEntryPrice"], "CORE_STATE_INVALID", nonnegative=True)
    if (position == 0 and average != 0) or (position != 0 and average <= 0):
        _fail("CORE_STATE_INVALID")
    strategy = state["strategyState"]
    if not isinstance(strategy, dict) or set(strategy) != {"owner", "dcaUsed", "strategyId"}:
        _fail("CORE_STATE_INVALID")
    if (strategy["owner"] not in (None, "STRATEGY_CORE")
            or strategy["strategyId"] != "STRATEGY_CORE"
            or type(strategy["dcaUsed"]) is not bool):
        _fail("CORE_STATE_INVALID")


def _validate_account_risk(account_risk):
    if not isinstance(account_risk, dict) or set(account_risk) != {"snapshotDigest", "snapshot"}:
        _fail("RISK_SNAPSHOT_INVALID")
    snapshot = account_risk["snapshot"]
    if not isinstance(snapshot, dict):
        _fail("RISK_SNAPSHOT_INVALID")
    digest_value = account_risk["snapshotDigest"]
    if not isinstance(digest_value, str) or not _DIGEST_RE.fullmatch(digest_value):
        _fail("RISK_SNAPSHOT_DIGEST_INVALID")
    try:
        actual = "sha256:" + hashlib.sha256(rfc8785.dumps(snapshot)).hexdigest()
    except (TypeError, ValueError, OverflowError):
        _fail("RISK_SNAPSHOT_INVALID")
    if (snapshot.get("mode") != "PAPER"
            or snapshot.get("liveTradingSupported") is not False
            or snapshot.get("available") is not True
            or type(snapshot.get("riskReady")) is not bool):
        _fail("RISK_SNAPSHOT_UNAVAILABLE")
    if actual != digest_value:
        _fail("RISK_SNAPSHOT_DIGEST_MISMATCH")


def validate_bundle(bundle, *, max_book_age_ms):
    """Validate the frozen bundle without I/O, database access, or strategy execution."""
    if type(max_book_age_ms) is not int or not 0 < max_book_age_ms <= _SAFE_INTEGER:
        _fail("MAX_BOOK_AGE_INVALID")
    if not isinstance(bundle, dict) or set(bundle) != _TOP_LEVEL:
        _fail("BUNDLE_FIELDS_INVALID")
    _walk_json(bundle)
    if (bundle["contract"] != "CORE_DECISION_INPUT_BUNDLE"
            or bundle["contractVersion"] != "1.0.0"
            or type(bundle["schemaVersion"]) is not int
            or bundle["schemaVersion"] != 1):
        _fail("BUNDLE_CONTRACT_INVALID")
    created = _safe_int(bundle["createdAtMs"], "BUNDLE_TIMESTAMP_INVALID")
    decision = _safe_int(bundle["decisionAtMs"], "BUNDLE_TIMESTAMP_INVALID")
    if created > decision:
        _fail("BUNDLE_TIMESTAMP_INVALID")
    if (bundle["mode"] != "PAPER" or bundle["aiExecutionEnabled"] is not False
            or bundle["strategyId"] != "STRATEGY_CORE"):
        _fail("PAPER_ONLY_GUARD_FAILED")
    if bundle["market"] != _MARKET:
        _fail("MARKET_IDENTITY_INVALID")
    market_data = bundle["marketData"]
    if (not isinstance(market_data, dict)
            or set(market_data) != {"sourceContract", "m15", "h1"}
            or market_data["sourceContract"] != "T0_READ_ONLY_CANDLE_V1"):
        _fail("CANDLE_SOURCE_CONTRACT_INVALID")
    m15_latest = _validate_candle_window(market_data["m15"], "15m", decision)
    h1_latest = _validate_candle_window(market_data["h1"], "1h", decision)
    m15_bucket = m15_latest["openTimeMs"] // 3_600_000 * 3_600_000
    if h1_latest["openTimeMs"] >= m15_bucket or h1_latest["closeTimeMs"] > m15_bucket:
        _fail("H1_CANDLE_NOT_ELIGIBLE")
    _validate_book(bundle["orderBook"], decision, max_book_age_ms)
    _validate_paper_state(bundle["paperState"])
    _validate_account_risk(bundle["accountRisk"])
    expected_id = compute_bundle_id(bundle)
    if (not isinstance(bundle["bundleId"], str)
            or not _DIGEST_RE.fullmatch(bundle["bundleId"])
            or bundle["bundleId"] != expected_id):
        _fail("BUNDLE_ID_MISMATCH")
    return {
        "status": "BUNDLE_VALID",
        "bundleId": expected_id,
        "strategyId": "STRATEGY_CORE",
        "decisionAtMs": decision,
        "maxBookAgeMs": max_book_age_ms,
        "m15DatasetVersion": market_data["m15"]["datasetVersion"],
        "h1DatasetVersion": market_data["h1"]["datasetVersion"],
        "accountRiskSnapshotDigest": bundle["accountRisk"]["snapshotDigest"],
    }
