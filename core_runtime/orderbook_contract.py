"""Pure T1 -> T2 Order Book v1 contract logic.

Transport-agnostic and intentionally independent of T1/T0 runtime, network,
database, Core producer, PaperLedger, Shared Risk Engine and exchange APIs.
"""

from copy import deepcopy
from decimal import Decimal, DecimalException
from hashlib import sha256
import json
import re
from threading import RLock
from types import MappingProxyType

CONTRACT = "T1_T2_ORDERBOOK_V1"
SYMBOL = "BTCUSDT"
MARKET = "BINANCE_USDM_PERPETUAL"
REQUIRED_DEPTH = 20
MAX_BOOK_AGE_MS = 2_000
MAX_FUTURE_SKEW_MS = 250
MAX_REANCHOR_ATTEMPTS = 3
_DECIMAL = re.compile(r"^(?:0|[1-9][0-9]*)(?:\.[0-9]+)?$")


class OrderBookContractError(ValueError):
    """Stable fail-closed contract error."""


def _fail(code):
    raise OrderBookContractError(code)


def _timestamp(value, code):
    if type(value) is not int or value < 0 or value > 9_007_199_254_740_991:
        _fail(code)
    return value


def parse_decimal(value, *, positive=False, nonnegative=False):
    """Parse canonical decimal text only; never coerce JSON numbers/floats."""
    if not isinstance(value, str) or not 1 <= len(value) <= 256:
        _fail("DECIMAL_TEXT_REQUIRED")
    if not _DECIMAL.fullmatch(value):
        _fail("DECIMAL_TEXT_INVALID")
    try:
        number = Decimal(value)
    except (DecimalException, ValueError):
        _fail("DECIMAL_TEXT_INVALID")
    parts = number.as_tuple()
    if (not number.is_finite() or len(parts.digits) > 80
            or not -200 <= parts.exponent <= 200
            or (number != 0 and number.adjusted() > 200)
            or (positive and number <= 0)
            or (nonnegative and number < 0)):
        _fail("DECIMAL_RANGE_INVALID")
    return number


def _parse_levels(levels, *, allow_zero=False):
    if not isinstance(levels, (list, tuple)):
        _fail("BOOK_LEVELS_INVALID")
    result = {}
    for item in levels:
        if not isinstance(item, (list, tuple)) or len(item) != 2:
            _fail("BOOK_LEVEL_INVALID")
        price_text, quantity_text = item
        price = parse_decimal(price_text, positive=True)
        quantity = parse_decimal(
            quantity_text, nonnegative=allow_zero, positive=not allow_zero
        )
        if price in result:
            _fail("BOOK_LEVEL_DUPLICATE")
        if quantity != 0:
            # Decimal keys detect equivalent prices while preserving original
            # source strings for publication.
            result[price] = (price_text, quantity_text)
    return result


def _ordered_levels(level_map, side):
    rows = [(price, pair[0], pair[1]) for price, pair in level_map.items()]
    rows.sort(key=lambda row: row[0], reverse=(side == "bids"))
    return [[price_text, quantity_text] for _, price_text, quantity_text in rows]


def validate_snapshot(snapshot, *, decision_at_ms):
    """Validate a published snapshot using frozen V1 thresholds."""
    _timestamp(decision_at_ms, "DECISION_TIMESTAMP_INVALID")
    required = {
        "contractVersion", "symbol", "market", "bids", "asks",
        "snapshotLastUpdateId", "firstAppliedU", "lastAppliedU",
        "sourceTimestampMs", "observedAtMs", "decisionWatermark",
        "generation", "snapshotId", "continuity", "freshness",
        "depth", "complete",
    }
    if not isinstance(snapshot, dict) or set(snapshot) != required:
        _fail("SNAPSHOT_SCHEMA_INVALID")
    if (snapshot["contractVersion"] != CONTRACT or snapshot["symbol"] != SYMBOL
            or snapshot["market"] != MARKET or snapshot["complete"] is not True
            or snapshot["continuity"] != "VERIFIED"
            or snapshot["freshness"] != "FRESH"):
        _fail("SNAPSHOT_IDENTITY_INVALID")

    for key in ("snapshotLastUpdateId", "firstAppliedU", "lastAppliedU",
                "decisionWatermark", "generation"):
        _timestamp(snapshot[key], "SNAPSHOT_SEQUENCE_INVALID")
    if (snapshot["generation"] < 1
            or snapshot["firstAppliedU"] > snapshot["snapshotLastUpdateId"] + 1
            or snapshot["lastAppliedU"] <= snapshot["snapshotLastUpdateId"]
            or snapshot["firstAppliedU"] > snapshot["lastAppliedU"]):
        _fail("SNAPSHOT_SEQUENCE_INVALID")
    if snapshot["decisionWatermark"] != snapshot["lastAppliedU"]:
        _fail("WATERMARK_MISMATCH")
    if not isinstance(snapshot["snapshotId"], str) or not snapshot["snapshotId"]:
        _fail("SNAPSHOT_ID_INVALID")

    source_time = _timestamp(snapshot["sourceTimestampMs"], "TIMESTAMP_INVALID")
    observed_time = _timestamp(snapshot["observedAtMs"], "TIMESTAMP_INVALID")
    for key, value in (("source", source_time), ("observation", observed_time)):
        if value > decision_at_ms + MAX_FUTURE_SKEW_MS:
            _fail("TIMESTAMP_FUTURE")
        if value <= decision_at_ms and decision_at_ms - value > MAX_BOOK_AGE_MS:
            _fail("SOURCE_STALE" if key == "source" else "OBSERVATION_STALE")

    bids = _parse_levels(snapshot["bids"])
    asks = _parse_levels(snapshot["asks"])
    bid_rows = _ordered_levels(bids, "bids")
    ask_rows = _ordered_levels(asks, "asks")
    if bid_rows != snapshot["bids"] or ask_rows != snapshot["asks"]:
        _fail("BOOK_LEVEL_ORDER_INVALID")
    if (len(bid_rows) < REQUIRED_DEPTH or len(ask_rows) < REQUIRED_DEPTH
            or not isinstance(snapshot["depth"], dict)
            or snapshot["depth"] != {"bids": len(bid_rows), "asks": len(ask_rows)}):
        _fail("DEPTH_INVALID")
    if Decimal(bid_rows[0][0]) >= Decimal(ask_rows[0][0]):
        _fail("SPREAD_INVALID")

    normalized = deepcopy(snapshot)
    normalized["bids"] = bid_rows
    normalized["asks"] = ask_rows
    return normalized


def reanchor(rest_snapshot, events, *, generation, decision_at_ms):
    """Build a candidate from a fresh REST anchor and a verified diff chain."""
    _timestamp(generation, "GENERATION_INVALID")
    if generation < 1 or not isinstance(rest_snapshot, dict):
        _fail("REST_ANCHOR_INVALID")
    anchor = _timestamp(rest_snapshot.get("lastUpdateId"), "REST_ANCHOR_INVALID")
    source_time = _timestamp(rest_snapshot.get("sourceTimestampMs"), "REST_ANCHOR_INVALID")
    observed_time = _timestamp(rest_snapshot.get("observedAtMs"), "REST_ANCHOR_INVALID")
    bids = _parse_levels(rest_snapshot.get("bids"))
    asks = _parse_levels(rest_snapshot.get("asks"))
    if not isinstance(events, (list, tuple)):
        _fail("DIFF_EVENTS_INVALID")

    watermark = anchor
    first_applied = None
    last_source_time = source_time
    last_observed_time = observed_time
    for event in events:
        if not isinstance(event, dict):
            _fail("DIFF_EVENT_INVALID")
        first = _timestamp(event.get("U"), "DIFF_EVENT_INVALID")
        final = _timestamp(event.get("u"), "DIFF_EVENT_INVALID")
        previous = _timestamp(event.get("pu"), "DIFF_EVENT_INVALID")
        if final < first:
            _fail("DIFF_EVENT_INVALID")
        if final <= watermark:
            continue
        if first_applied is None:
            if not first <= anchor + 1 <= final:
                _fail("ANCHOR_BRIDGE_INVALID")
            first_applied = first
        elif previous != watermark:
            _fail("SEQUENCE_GAP")

        for side, key in ((bids, "b"), (asks, "a")):
            updates = event.get(key, [])
            if not isinstance(updates, (list, tuple)):
                _fail("DIFF_EVENT_INVALID")
            seen = set()
            for item in updates:
                if not isinstance(item, (list, tuple)) or len(item) != 2:
                    _fail("DIFF_EVENT_INVALID")
                price_text, quantity_text = item
                price = parse_decimal(price_text, positive=True)
                quantity = parse_decimal(quantity_text, nonnegative=True)
                if price in seen:
                    _fail("BOOK_LEVEL_DUPLICATE")
                seen.add(price)
                if quantity == 0:
                    side.pop(price, None)
                else:
                    side[price] = (price_text, quantity_text)

        watermark = final
        last_source_time = _timestamp(event.get("E"), "DIFF_TIMESTAMP_INVALID")
        last_observed_time = _timestamp(event.get("observedAtMs"), "DIFF_TIMESTAMP_INVALID")

    if first_applied is None:
        _fail("ANCHOR_BRIDGE_MISSING")
    bid_rows = _ordered_levels(bids, "bids")
    ask_rows = _ordered_levels(asks, "asks")
    candidate = {
        "contractVersion": CONTRACT,
        "symbol": SYMBOL,
        "market": MARKET,
        "bids": bid_rows,
        "asks": ask_rows,
        "snapshotLastUpdateId": anchor,
        "firstAppliedU": first_applied,
        "lastAppliedU": watermark,
        "sourceTimestampMs": last_source_time,
        "observedAtMs": last_observed_time,
        "decisionWatermark": watermark,
        "generation": generation,
        "snapshotId": "",
        "continuity": "VERIFIED",
        "freshness": "FRESH",
        "depth": {"bids": len(bid_rows), "asks": len(ask_rows)},
        "complete": True,
    }
    identity = dict(candidate)
    identity.pop("snapshotId")
    candidate["snapshotId"] = "sha256:" + sha256(
        json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return validate_snapshot(candidate, decision_at_ms=decision_at_ms)


def reanchor_with_retries(snapshot_provider, events_provider, *, generation, decision_at_ms):
    """Acquire at most three independent anchors; publish no failed candidate."""
    last_error = None
    for attempt in range(MAX_REANCHOR_ATTEMPTS):
        try:
            return reanchor(
                snapshot_provider(attempt),
                events_provider(attempt),
                generation=generation,
                decision_at_ms=decision_at_ms,
            )
        except Exception as exc:
            last_error = exc
    raise OrderBookContractError("REANCHOR_EXHAUSTED") from last_error


def _freeze(value):
    if isinstance(value, dict):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    return value


class SnapshotSlot:
    """In-process atomic pointer-swap model; not a T1 transport implementation."""

    def __init__(self):
        self._lock = RLock()
        self._snapshot = None
        self._minimum_generation = 1

    def read(self):
        with self._lock:
            return self._snapshot

    def invalidate(self, reason):
        if not isinstance(reason, str) or not reason:
            _fail("INVALIDATION_REASON_REQUIRED")
        with self._lock:
            if self._snapshot is not None:
                self._minimum_generation = max(
                    self._minimum_generation, self._snapshot["generation"] + 1
                )
            self._snapshot = None

    def publish(self, snapshot, *, decision_at_ms):
        accepted = validate_snapshot(snapshot, decision_at_ms=decision_at_ms)
        with self._lock:
            if accepted["generation"] != self._minimum_generation:
                _fail("GENERATION_FENCED")
            self._snapshot = _freeze(accepted)
            self._minimum_generation += 1
            return self._snapshot


def run_after_book_validation(snapshot, *, decision_at_ms, producer,
                              paper_ledger, shared_risk_engine):
    """Standalone gate primitive; deliberately not connected to a Core runner."""
    accepted = validate_snapshot(snapshot, decision_at_ms=decision_at_ms)
    produced = producer(accepted)
    risk_result = shared_risk_engine(produced)
    if risk_result is False:
        return risk_result
    return paper_ledger(produced, accepted)
