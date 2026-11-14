"""Distinct PAPER funding posting path for deterministic end-to-end reconciliation.

This module intentionally does not call the expected-population builder. It
reconstructs each settlement posting from position snapshots and captured
public market-rate observations, then persists the result through the PAPER
ledger API. Shared input lineage is not independent source evidence.
"""

from bisect import bisect_right
from decimal import Decimal, localcontext

from paper_execution.funding import record_funding_event
from paper_execution.funding_model import (
    STRATEGIES, _decimal_text, _digest, _normalise_positions, _normalise_rates,
)


MODEL_VERSION = "paper-linear-funding-v1"
POSTING_SOURCE = "paper_settlement_engine:linear_usdt_perpetual"
CURRENCY = "USDT"
_DEFAULT_MAX_POSITION_AGE_MS = 60_000


def _timestamp(value, code):
    if type(value) is not int or value < 0:
        raise ValueError(code)
    return value


def post_paper_funding_events(
    db_path, *, position_snapshots, funding_rate_events,
    start_at_ms, end_at_ms, recorded_at_ms,
    max_position_age_ms=_DEFAULT_MAX_POSITION_AGE_MS,
):
    """Post deterministic PAPER funding entries from positions and market rates.

    This is a separate posting path from the expected-population builder.
    It shares the public rate and projected-position inputs, so reconciliation
    remains DECLARED_NOT_VERIFIED rather than claiming source independence.
    Individual event writes are transactional and idempotent. If a batch stops
    partway through, no VERIFIED coverage can be issued until retry/reconciliation
    proves the complete persisted population.
    """
    start = _timestamp(start_at_ms, "FUNDING_POPULATION_START_INVALID")
    end = _timestamp(end_at_ms, "FUNDING_POPULATION_END_INVALID")
    recorded = _timestamp(recorded_at_ms, "FUNDING_EVENT_TIMESTAMP_INVALID")
    max_age = _timestamp(max_position_age_ms, "FUNDING_POSITION_MAX_AGE_INVALID")
    if start >= end or end > recorded or max_age <= 0:
        raise ValueError("FUNDING_POPULATION_INTERVAL_INVALID")

    positions = _normalise_positions(position_snapshots)
    rates = _normalise_rates(funding_rate_events, start, end)
    by_strategy = {strategy: [] for strategy in STRATEGIES}
    for position in positions:
        by_strategy[position["strategyId"]].append(position)
    times = {
        strategy: [row["observedAtMs"] for row in rows]
        for strategy, rows in by_strategy.items()
    }

    candidates = []
    with localcontext() as context:
        context.prec = 240
        for market in rates:
            settlement = market["fundingTimeMs"]
            for strategy in sorted(STRATEGIES):
                rows = by_strategy[strategy]
                index = bisect_right(times[strategy], settlement) - 1
                if index < 0:
                    raise ValueError("FUNDING_POSITION_SNAPSHOT_MISSING")
                position = rows[index]
                if settlement - position["observedAtMs"] > max_age:
                    raise ValueError("FUNDING_POSITION_SNAPSHOT_STALE")
                quantity = position["_quantity"]
                if quantity == 0:
                    continue

                amount = quantity * Decimal(market["markPrice"]) * Decimal(market["fundingRate"])
                amount_text = _decimal_text(amount)
                payload = {
                    "modelVersion": MODEL_VERSION,
                    "strategyId": strategy,
                    "positionSnapshotId": position["snapshotId"],
                    "positionObservedAtMs": position["observedAtMs"],
                    "positionBase": position["positionBase"],
                    "marketFundingEventId": market["eventId"],
                    "marketSourceSnapshotId": market["sourceSnapshotId"],
                    "fundingTimeMs": settlement,
                    "fundingRate": market["fundingRate"],
                    "markPrice": market["markPrice"],
                    "amountQuote": amount_text,
                    "currency": CURRENCY,
                }
                payload_hash = _digest(payload)
                if len(candidates) >= 100_000:
                    raise ValueError("FUNDING_POPULATION_EVENTS_INVALID")
                candidates.append({
                    "eventId": "paper-funding:" + payload_hash[7:],
                    "strategyId": strategy,
                    "eventAtMs": settlement,
                    "amountQuote": amount_text,
                    "payloadHash": payload_hash,
                    "sourceSnapshotId": market["sourceSnapshotId"],
                })

    if len(candidates) > 100_000:
        raise ValueError("FUNDING_POPULATION_EVENTS_INVALID")

    candidates.sort(key=lambda row: (row["eventAtMs"], row["eventId"]))
    posted = []
    for candidate in candidates:
        result = record_funding_event(
            db_path,
            funding_event_id=candidate["eventId"],
            strategy_id=candidate["strategyId"],
            amount_quote=candidate["amountQuote"],
            event_at_ms=candidate["eventAtMs"],
            source=POSTING_SOURCE,
            source_snapshot_id=candidate["sourceSnapshotId"],
            payload_hash=candidate["payloadHash"],
            recorded_at_ms=recorded,
        )
        posted.append({
            "eventId": candidate["eventId"],
            "strategyId": candidate["strategyId"],
            "eventAtMs": candidate["eventAtMs"],
            "amountQuote": candidate["amountQuote"],
            "payloadHash": candidate["payloadHash"],
            "idempotent": result["idempotent"],
        })
    return posted
