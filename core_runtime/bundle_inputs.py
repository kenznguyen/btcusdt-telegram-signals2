"""Pure, fail-closed normalization of T0/T1 inputs into Core Bundle v1."""

from copy import deepcopy
import hashlib

import rfc8785

from core_runtime.input_bundle import compute_bundle_id, validate_bundle
from core_runtime.orderbook_contract import (
    OrderBookContractError,
    validate_snapshot,
)


class BundleInputError(ValueError):
    """Stable error raised when a producer input cannot form a Core bundle."""


_CANDLE_WINDOW_FIELDS = {
    "contractVersion", "schemaVersion", "exchange", "marketType", "symbol",
    "timeframe", "volumeUnit", "startMs", "endMs", "asOfMs",
    "generatedAtMs", "datasetVersion", "candles", "coverage", "freshness",
    "source",
}
_CANDLE_ROW_FIELDS = {
    "openTimeMs", "closeTimeMs", "open", "high", "low", "close", "volume",
    "isClosed", "availableAtMs", "availabilityKind", "quality", "source",
    "exchange", "marketType", "symbol", "timeframe",
}
_BUNDLE_CANDLE_ROW_FIELDS = _CANDLE_ROW_FIELDS - {
    "exchange", "marketType", "symbol", "timeframe",
}
_T1_FIELDS = {
    "contractVersion", "symbol", "market", "bids", "asks",
    "snapshotLastUpdateId", "firstAppliedU", "lastAppliedU",
    "sourceTimestampMs", "observedAtMs", "decisionWatermark", "generation",
    "snapshotId", "continuity", "freshness", "depth", "complete",
}
_T1_EVIDENCE_FIELDS = _T1_FIELDS - {"symbol", "bids", "asks"}
_SAFE_INTEGER = 9_007_199_254_740_991


def _fail(code):
    raise BundleInputError(code)


def _timestamp(value):
    return type(value) is int and 0 <= value <= _SAFE_INTEGER


def normalize_candle_window(payload, *, timeframe):
    """Project one validated T0 HTTP envelope into the frozen bundle window.

    The source datasetVersion, candle values and T0 coverage/freshness evidence
    are preserved verbatim; only transport identity fields are removed from
    individual candle rows.
    """
    if timeframe not in ("15m", "1h") or not isinstance(payload, dict):
        _fail("T0_ENVELOPE_INVALID")
    source_timeframe = "m15" if timeframe == "15m" else "h1"
    expected = {
        "contractVersion": "1.0.0",
        "schemaVersion": 1,
        "exchange": "binance",
        "marketType": "USDT_PERPETUAL",
        "symbol": "BTCUSDT",
        "timeframe": source_timeframe,
        "volumeUnit": "BTC_BASE_ASSET",
        "source": "ccxt.binanceusdm",
    }
    # The live HTTP client uses canonical 15m/1h names; test and legacy
    # envelope producers may use m15/h1. Both map to the same frozen identity.
    if payload.get("timeframe") in ("15m", "1h"):
        expected["timeframe"] = timeframe
    if set(payload) != _CANDLE_WINDOW_FIELDS:
        _fail("T0_ENVELOPE_FIELDS_INVALID")
    for key, value in expected.items():
        if type(payload.get(key)) is not type(value) or payload.get(key) != value:
            _fail("T0_IDENTITY_INVALID")
    if (not _timestamp(payload.get("startMs"))
            or not _timestamp(payload.get("endMs"))
            or not _timestamp(payload.get("generatedAtMs"))
            or (payload.get("asOfMs") is not None
                and not _timestamp(payload.get("asOfMs")))):
        _fail("T0_TIMESTAMP_INVALID")
    if not isinstance(payload.get("datasetVersion"), str) or not payload["datasetVersion"].strip():
        _fail("T0_DATASET_VERSION_MISSING")
    if not isinstance(payload.get("candles"), list):
        _fail("T0_CANDLES_INVALID")

    candles = []
    for row in payload["candles"]:
        if not isinstance(row, dict) or set(row) != _CANDLE_ROW_FIELDS:
            _fail("T0_CANDLE_FIELDS_INVALID")
        row_identity = {
            "exchange": "binance", "marketType": "USDT_PERPETUAL",
            "symbol": "BTCUSDT", "timeframe": source_timeframe,
        }
        if row.get("timeframe") in ("15m", "1h"):
            row_identity["timeframe"] = timeframe
        for key, value in row_identity.items():
            if type(row.get(key)) is not type(value) or row.get(key) != value:
                _fail("T0_CANDLE_IDENTITY_INVALID")
        candles.append({
            key: deepcopy(value) for key, value in row.items()
            if key in _BUNDLE_CANDLE_ROW_FIELDS
        })

    return {
        key: deepcopy(payload[key])
        for key in _CANDLE_WINDOW_FIELDS
        if key != "source" and key != "candles"
    } | {"timeframe": timeframe, "candles": candles}


def _t1_source_document(snapshot):
    if not isinstance(snapshot, dict):
        _fail("T1_SNAPSHOT_INVALID")
    # Accept either the native T1 snapshot document or the already projected
    # Core Bundle wire shape; both are revalidated by the frozen T1 contract.
    if set(snapshot) == _T1_FIELDS:
        native = deepcopy(snapshot)
    elif set(snapshot) == {
        "source", "connector", "symbol", "observedAtMs", "bids", "asks",
        "t1Evidence",
    }:
        if (snapshot.get("source") != "t1"
                or snapshot.get("connector") != "binance_usdm_perpetual"
                or not isinstance(snapshot.get("t1Evidence"), dict)
                or set(snapshot["t1Evidence"]) != _T1_EVIDENCE_FIELDS):
            _fail("T1_PROVENANCE_INVALID")
        native = {
            **deepcopy(snapshot["t1Evidence"]),
            "symbol": snapshot["symbol"],
            "market": snapshot["t1Evidence"].get("market"),
            "bids": [[row.get("price"), row.get("quantity")]
                     for row in snapshot["bids"] if isinstance(row, dict)],
            "asks": [[row.get("price"), row.get("quantity")]
                     for row in snapshot["asks"] if isinstance(row, dict)],
        }
        if (len(native["bids"]) != len(snapshot["bids"])
                or len(native["asks"]) != len(snapshot["asks"])):
            _fail("T1_LEVEL_INVALID")
    else:
        _fail("T1_SNAPSHOT_FIELDS_INVALID")
    if set(native) != _T1_FIELDS:
        _fail("T1_SNAPSHOT_FIELDS_INVALID")
    return native


def normalize_orderbook_snapshot(snapshot, *, decision_at_ms=None):
    """Validate T1 continuity, identity, depth, freshness and snapshot hash."""
    native = _t1_source_document(snapshot)
    if decision_at_ms is None:
        decision_at_ms = native.get("observedAtMs")
    if not _timestamp(decision_at_ms):
        _fail("T1_DECISION_TIMESTAMP_INVALID")
    try:
        accepted = validate_snapshot(native, decision_at_ms=decision_at_ms)
    except OrderBookContractError as exc:
        raise BundleInputError("T1_" + str(exc)) from None
    return {
        "source": "t1",
        "connector": "binance_usdm_perpetual",
        "symbol": accepted["symbol"],
        "observedAtMs": accepted["observedAtMs"],
        "bids": [
            {"price": price, "quantity": quantity}
            for price, quantity in accepted["bids"]
        ],
        "asks": [
            {"price": price, "quantity": quantity}
            for price, quantity in accepted["asks"]
        ],
        "t1Evidence": {
            key: deepcopy(accepted[key]) for key in _T1_EVIDENCE_FIELDS
        },
    }


def build_core_bundle(*, decision_at_ms, m15_payload, h1_payload,
                      orderbook_snapshot, paper_snapshot,
                      account_risk_snapshot):
    """Build and validate an immutable PAPER Core bundle without I/O or writes."""
    if not _timestamp(decision_at_ms):
        _fail("DECISION_TIMESTAMP_INVALID")
    if not isinstance(account_risk_snapshot, dict):
        _fail("RISK_SNAPSHOT_INVALID")
    risk = deepcopy(account_risk_snapshot)
    if (risk.get("mode") != "PAPER"
            or risk.get("liveTradingSupported") is not False
            or risk.get("available") is not True
            or risk.get("riskReady") is not True):
        _fail("RISK_NOT_READY")
    kill_switch = risk.get("killSwitch")
    if (not isinstance(kill_switch, dict)
            or type(kill_switch.get("enabled")) is not bool
            or kill_switch["enabled"] is not False):
        _fail("KILL_SWITCH_NOT_CLEAR")

    m15 = normalize_candle_window(m15_payload, timeframe="15m")
    h1 = normalize_candle_window(h1_payload, timeframe="1h")
    book = normalize_orderbook_snapshot(
        orderbook_snapshot, decision_at_ms=decision_at_ms
    )
    try:
        risk_digest = "sha256:" + hashlib.sha256(rfc8785.dumps(risk)).hexdigest()
    except (TypeError, ValueError, OverflowError):
        _fail("RISK_SNAPSHOT_INVALID")

    bundle = {
        "contract": "CORE_DECISION_INPUT_BUNDLE",
        "contractVersion": "1.0.0",
        "schemaVersion": 1,
        "bundleId": "sha256:" + "0" * 64,
        "createdAtMs": decision_at_ms,
        "decisionAtMs": decision_at_ms,
        "mode": "PAPER",
        "aiExecutionEnabled": False,
        "strategyId": "STRATEGY_CORE",
        "market": {
            "exchange": "binance",
            "marketType": "USDT_PERPETUAL",
            "symbol": "BTCUSDT",
            "decisionTimeframe": "15m",
        },
        "marketData": {
            "sourceContract": "T0_READ_ONLY_CANDLE_V1",
            "m15": m15,
            "h1": h1,
        },
        "orderBook": book,
        "paperState": deepcopy(paper_snapshot),
        "accountRisk": {
            "snapshotDigest": risk_digest,
            "snapshot": risk,
        },
    }
    bundle["bundleId"] = compute_bundle_id(bundle)
    try:
        validate_bundle(bundle, max_book_age_ms=2_000)
    except Exception as exc:
        # Keep the builder fail-closed and expose stable contract errors only.
        code = str(exc) or "BUNDLE_VALIDATION_FAILED"
        raise BundleInputError(code) from None
    return bundle
