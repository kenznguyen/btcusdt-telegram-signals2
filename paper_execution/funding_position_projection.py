"""Read-only PAPER position projection from cutover snapshots and execution history."""

import hashlib
import json
import re

from paper_execution.account_history import (
    STRATEGIES,
    _replay_decimal,
    _replay_text,
    _stamp,
    replay_ledger_events,
)


_CUTOVER_FIELDS = {
    "cutoverId", "strategyId", "snapshotAtMs", "positionBase",
    "averageEntryPrice", "realizedPnlQuote", "feesQuote", "fundingQuote",
    "sourceSnapshotId", "payloadHash", "canonicalPayload",
}
_EVENT_FIELDS = {
    "eventId", "strategyId", "eventType", "eventAtMs", "recordedAtMs",
    "quantityDeltaBase", "fillPrice", "feeQuote", "feeCurrency", "source",
    "sourceSnapshotId", "payloadHash", "orderId", "intentId", "sourceEventId",
    "canonicalPayload",
}
_COVERAGE_FIELDS = {
    "coverageId", "strategyId", "startAtMs", "endAtMs", "status", "source",
    "sourceSnapshotId", "payloadHash", "recordedAtMs",
}
_SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")
_MAX_ROWS = 100_000


def _text(value, code, limit=256):
    if (not isinstance(value, str) or not value.strip()
            or len(value) > limit or not value.isprintable()):
        raise ValueError(code)
    return value


def _hash(value, code):
    if not isinstance(value, str) or not _SHA256.fullmatch(value):
        raise ValueError(code)
    return value


def _digest(value):
    canonical = json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(canonical).hexdigest()


def _canonical_payload(raw, expected, code):
    if not isinstance(raw, str) or len(raw) > 100_000:
        raise ValueError(code)
    try:
        parsed = json.loads(raw)
        canonical = json.dumps(
            expected, sort_keys=True, separators=(",", ":"), allow_nan=False,
        )
    except (TypeError, ValueError):
        raise ValueError(code) from None
    if parsed != expected or raw != canonical:
        raise ValueError(code)


def _normalise_cutovers(rows):
    if not isinstance(rows, list) or len(rows) != len(STRATEGIES):
        raise ValueError("FUNDING_POSITION_CUTOVER_SET_INVALID")
    snapshots = {}
    cutover_ids = set()
    snapshot_times = set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != _CUTOVER_FIELDS:
            raise ValueError("FUNDING_POSITION_CUTOVER_SNAPSHOT_INVALID")
        cutover_id = _text(row["cutoverId"], "FUNDING_POSITION_CUTOVER_SNAPSHOT_INVALID")
        strategy = row["strategyId"]
        if not isinstance(strategy, str) or strategy not in STRATEGIES or strategy in snapshots:
            raise ValueError("FUNDING_POSITION_CUTOVER_SET_INVALID")
        snapshot_at = _stamp(
            row["snapshotAtMs"], "FUNDING_POSITION_CUTOVER_SNAPSHOT_INVALID"
        )
        position = _replay_decimal(
            row["positionBase"], "FUNDING_POSITION_CUTOVER_SNAPSHOT_INVALID", signed=True
        )
        average = _replay_decimal(
            row["averageEntryPrice"], "FUNDING_POSITION_CUTOVER_SNAPSHOT_INVALID",
            nonnegative=True,
        )
        realized = _replay_decimal(
            row["realizedPnlQuote"], "FUNDING_POSITION_CUTOVER_SNAPSHOT_INVALID",
            signed=True,
        )
        fees = _replay_decimal(
            row["feesQuote"], "FUNDING_POSITION_CUTOVER_SNAPSHOT_INVALID",
            nonnegative=True,
        )
        funding = _replay_decimal(
            row["fundingQuote"], "FUNDING_POSITION_CUTOVER_SNAPSHOT_INVALID",
            signed=True,
        )
        if ((position == 0 and average != 0) or
                (position != 0 and average <= 0)):
            raise ValueError("FUNDING_POSITION_CUTOVER_SNAPSHOT_INVALID")
        source_snapshot = _text(
            row["sourceSnapshotId"], "FUNDING_POSITION_CUTOVER_SNAPSHOT_INVALID"
        )
        payload_hash = _hash(
            row["payloadHash"], "FUNDING_POSITION_CUTOVER_SNAPSHOT_INVALID"
        )
        expected = {
            "cutoverId": cutover_id,
            "strategyId": strategy,
            "snapshotAtMs": snapshot_at,
            "positionBase": row["positionBase"],
            "averageEntryPrice": row["averageEntryPrice"],
            "realizedPnlQuote": row["realizedPnlQuote"],
            "feesQuote": row["feesQuote"],
            "fundingQuote": row["fundingQuote"],
            "sourceSnapshotId": source_snapshot,
            "payloadHash": payload_hash,
        }
        _canonical_payload(
            row["canonicalPayload"], expected,
            "FUNDING_POSITION_CUTOVER_SNAPSHOT_INVALID",
        )
        snapshots[strategy] = {
            "snapshot": {
                "position_base": _replay_text(position),
                "average_entry_price": _replay_text(average),
                "realized_pnl_quote": _replay_text(realized),
                "fees_quote": _replay_text(fees),
                "funding_quote": _replay_text(funding),
                "snapshot_at_ms": snapshot_at,
            },
            "cutover_id": cutover_id,
            "snapshot_at_ms": snapshot_at,
            "source_snapshot_id": source_snapshot,
            "payload_hash": payload_hash,
        }
        cutover_ids.add(cutover_id)
        snapshot_times.add(snapshot_at)
    if set(snapshots) != set(STRATEGIES) or len(cutover_ids) != 1 or len(snapshot_times) != 1:
        raise ValueError("FUNDING_POSITION_CUTOVER_SET_INVALID")
    return snapshots, next(iter(cutover_ids)), next(iter(snapshot_times))


def _normalise_events(rows, now):
    if not isinstance(rows, list) or len(rows) > _MAX_ROWS:
        raise ValueError("FUNDING_POSITION_EVENTS_INVALID")
    events_by_strategy = {strategy: [] for strategy in STRATEGIES}
    seen_ids = set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != _EVENT_FIELDS:
            raise ValueError("FUNDING_POSITION_EVENT_INVALID")
        event_id = _text(row["eventId"], "FUNDING_POSITION_EVENT_ID_INVALID", 200)
        if event_id in seen_ids:
            raise ValueError("ACCOUNT_HISTORY_EVENT_ID_DUPLICATE")
        seen_ids.add(event_id)
        strategy = row["strategyId"]
        if not isinstance(strategy, str) or strategy not in STRATEGIES:
            raise ValueError("FUNDING_POSITION_EVENT_INVALID")
        event_type = _text(row["eventType"], "FUNDING_POSITION_EVENT_INVALID", 64)
        event_at = _stamp(row["eventAtMs"], "FUNDING_POSITION_EVENT_TIME_INVALID")
        recorded_at = _stamp(
            row["recordedAtMs"], "FUNDING_POSITION_EVENT_TIME_INVALID"
        )
        if event_at > recorded_at or recorded_at > now:
            raise ValueError("FUNDING_POSITION_EVENT_TIME_INVALID")
        quantity = row["quantityDeltaBase"]
        price = row["fillPrice"]
        fee = row["feeQuote"]
        currency = _text(row["feeCurrency"], "FUNDING_POSITION_EVENT_INVALID", 16)
        source = _text(row["source"], "FUNDING_POSITION_EVENT_INVALID")
        source_snapshot = _text(
            row["sourceSnapshotId"], "FUNDING_POSITION_EVENT_INVALID"
        )
        payload_hash = _hash(
            row["payloadHash"], "FUNDING_POSITION_EVENT_DIGEST_INVALID"
        )
        order_id = _text(row["orderId"], "FUNDING_POSITION_EVENT_INVALID", 200)
        intent_id = _text(row["intentId"], "FUNDING_POSITION_EVENT_INVALID", 200)
        source_event_id = _text(
            row["sourceEventId"], "FUNDING_POSITION_EVENT_INVALID", 200
        )
        expected = {
            "eventId": event_id,
            "accountId": 1,
            "strategyId": strategy,
            "eventType": event_type,
            "eventAtMs": event_at,
            "recordedAtMs": recorded_at,
            "orderId": order_id,
            "intentId": intent_id,
            "sourceEventId": source_event_id,
            "quantityDeltaBase": quantity,
            "fillPrice": price,
            "feeQuote": fee,
            "source": source,
            "sourceSnapshotId": source_snapshot,
            "feeCurrency": currency,
        }
        _canonical_payload(
            row["canonicalPayload"], expected,
            "FUNDING_POSITION_EVENT_PAYLOAD_INVALID",
        )
        if _digest(expected) != payload_hash:
            raise ValueError("FUNDING_POSITION_EVENT_DIGEST_INVALID")
        events_by_strategy[strategy].append({
            "event_id": event_id,
            "event_type": event_type,
            "event_at_ms": event_at,
            "recorded_at_ms": recorded_at,
            "quantity_delta_base": quantity,
            "fill_price": price,
            "fee_quote": fee,
            "fee_currency": currency,
            "source": source,
            "source_snapshot_id": source_snapshot,
            "payload_hash": payload_hash,
        })
    for events in events_by_strategy.values():
        events.sort(key=lambda item: (item["event_at_ms"], item["event_id"]))
    return events_by_strategy


def _normalise_coverage(rows, now):
    if not isinstance(rows, list) or len(rows) > _MAX_ROWS:
        raise ValueError("FUNDING_POSITION_COVERAGE_INVALID")
    coverage_by_strategy = {strategy: [] for strategy in STRATEGIES}
    seen_ids = set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != _COVERAGE_FIELDS:
            raise ValueError("FUNDING_POSITION_COVERAGE_INVALID")
        coverage_id = _text(row["coverageId"], "FUNDING_POSITION_COVERAGE_INVALID", 200)
        if coverage_id in seen_ids:
            raise ValueError("FUNDING_POSITION_COVERAGE_INVALID")
        seen_ids.add(coverage_id)
        strategy = row["strategyId"]
        if not isinstance(strategy, str) or strategy not in STRATEGIES:
            raise ValueError("FUNDING_POSITION_COVERAGE_INVALID")
        start = _stamp(row["startAtMs"], "FUNDING_POSITION_COVERAGE_INVALID")
        end = _stamp(row["endAtMs"], "FUNDING_POSITION_COVERAGE_INVALID")
        recorded = _stamp(
            row["recordedAtMs"], "FUNDING_POSITION_COVERAGE_INVALID"
        )
        source = _text(row["source"], "FUNDING_POSITION_COVERAGE_INVALID")
        source_snapshot = _text(
            row["sourceSnapshotId"], "FUNDING_POSITION_COVERAGE_INVALID"
        )
        payload_hash = _hash(
            row["payloadHash"], "FUNDING_POSITION_COVERAGE_INVALID"
        )
        coverage_by_strategy[strategy].append({
            "coverage_id": coverage_id,
            "start_at_ms": start,
            "end_at_ms": end,
            "status": row["status"],
            "source": source,
            "source_snapshot_id": source_snapshot,
            "payload_hash": payload_hash,
            "recorded_at_ms": recorded,
        })
    for proofs in coverage_by_strategy.values():
        proofs.sort(key=lambda item: (
            item["start_at_ms"], item["end_at_ms"], item["coverage_id"],
        ))
    return coverage_by_strategy


def _coverage_chain(proofs, snapshot_at, required_end, now):
    selected = [
        item for item in proofs
        if item["end_at_ms"] > snapshot_at and item["start_at_ms"] < required_end
    ]
    cursor = snapshot_at
    previous_end = None
    for item in selected:
        start = item["start_at_ms"]
        end = item["end_at_ms"]
        recorded = item["recorded_at_ms"]
        if (recorded > now or start >= end or end > recorded
                or item["status"] != "VERIFIED"
                or (previous_end is not None and start < previous_end)
                or start > cursor):
            raise ValueError("FUNDING_POSITION_COVERAGE_INCOMPLETE")
        cursor = max(cursor, end)
        previous_end = end
    if cursor < required_end:
        raise ValueError("FUNDING_POSITION_COVERAGE_INCOMPLETE")
    return selected, max(item["recorded_at_ms"] for item in selected)


def build_paper_position_snapshots(
    *, cutover_snapshots, execution_events, execution_coverage,
    settlement_times, now_ms,
):
    """Project signed PAPER position quantities immediately before settlements.

    The cutover snapshots are the baseline. Only immutable FILL events after
    that baseline and strictly before each settlement are replayed. Each
    settlement requires contiguous VERIFIED EXECUTION coverage through
    settlement+1ms. A fill exactly at settlement is rejected as ambiguous.
    """
    now = _stamp(now_ms, "FUNDING_POSITION_NOW_INVALID")
    if (not isinstance(settlement_times, list) or not settlement_times
            or len(settlement_times) > _MAX_ROWS):
        raise ValueError("FUNDING_POSITION_SETTLEMENTS_INVALID")
    settlements = [
        _stamp(item, "FUNDING_POSITION_SETTLEMENTS_INVALID")
        for item in settlement_times
    ]
    if any(left >= right for left, right in zip(settlements, settlements[1:])):
        raise ValueError("FUNDING_POSITION_SETTLEMENTS_INVALID")
    if settlements[-1] >= now:
        raise ValueError("FUNDING_POSITION_SETTLEMENTS_INVALID")

    snapshots, cutover_id, snapshot_at = _normalise_cutovers(cutover_snapshots)
    if settlements[0] <= snapshot_at:
        raise ValueError("FUNDING_POSITION_BEFORE_CUTOVER")
    events = _normalise_events(execution_events, now)
    coverage = _normalise_coverage(execution_coverage, now)

    output = []
    for settlement in settlements:
        if settlement + 1 > now:
            raise ValueError("FUNDING_POSITION_COVERAGE_INCOMPLETE")
        for strategy in sorted(STRATEGIES):
            proofs, watermark = _coverage_chain(
                coverage[strategy], snapshot_at, settlement + 1, now
            )
            strategy_events = events[strategy]
            for event in strategy_events:
                if event["event_at_ms"] == settlement:
                    raise ValueError("FUNDING_POSITION_BOUNDARY_AMBIGUOUS")
                if snapshot_at < event["event_at_ms"] < settlement:
                    matches = [
                        proof for proof in proofs
                        if proof["start_at_ms"] <= event["event_at_ms"] < proof["end_at_ms"]
                    ]
                    if len(matches) != 1 or event["recorded_at_ms"] > matches[0]["recorded_at_ms"]:
                        raise ValueError("FUNDING_POSITION_EVENT_COVERAGE_INVALID")

            replayed = replay_ledger_events(
                snapshots[strategy]["snapshot"],
                strategy_events,
                [],
                boundary_ms=settlement,
                coverage_watermark_at_ms=watermark,
                require_utc_boundary=False,
            )
            included_ids = set(replayed["included_event_ids"])
            included = [
                {"eventId": event["event_id"], "payloadHash": event["payload_hash"]}
                for event in strategy_events if event["event_id"] in included_ids
            ]
            proof_identity = [
                {
                    "coverageId": proof["coverage_id"],
                    "startAtMs": proof["start_at_ms"],
                    "endAtMs": proof["end_at_ms"],
                    "payloadHash": proof["payload_hash"],
                    "recordedAtMs": proof["recorded_at_ms"],
                }
                for proof in proofs
            ]
            snapshot_identity = {
                "projectionVersion": "paper-position-asof-v1",
                "cutoverId": cutover_id,
                "strategyId": strategy,
                "settlementTimeMs": settlement,
                "cutoverPayloadHash": snapshots[strategy]["payload_hash"],
                "executionEvents": included,
                "executionCoverage": proof_identity,
            }
            output.append({
                "snapshotId": _digest(snapshot_identity),
                "strategyId": strategy,
                "symbol": "BTCUSDT",
                "observedAtMs": settlement,
                "positionBase": replayed["position_base"],
            })
    return output
