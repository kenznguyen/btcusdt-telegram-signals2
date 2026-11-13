"""Deterministic PAPER funding model for linear USDT-margined perpetual positions.

This module calculates simulated funding from explicitly supplied PAPER position
snapshots and public market funding-rate observations. It does not access an
exchange, account data, credentials, or the network, and it does not claim to
reproduce an actual account's funding cashflows.
"""

from decimal import Decimal, DecimalException, localcontext
import hashlib
import json


MODEL_VERSION = "paper-linear-funding-v1"
POPULATION_DEFINITION_ID = MODEL_VERSION
SOURCE = "paper_simulation:linear_usdt_perpetual"
CURRENCY = "USDT"
SYMBOL = "BTCUSDT"
STRATEGIES = {"STRATEGY_CORE", "AI_FREQAI", "LEGACY_UNATTRIBUTED"}
_POSITION_FIELDS = {
    "snapshotId", "strategyId", "symbol", "observedAtMs", "positionBase",
}
_RATE_FIELDS = {
    "eventId", "symbol", "fundingTimeMs", "fundingRate", "markPrice",
    "sourceSnapshotId",
}
_MAX_ROWS = 100_000
_DEFAULT_MAX_POSITION_AGE_MS = 60_000


def _timestamp(value, code):
    if type(value) is not int or value < 0:
        raise ValueError(code)
    return value


def _text(value, code, limit=200):
    if (not isinstance(value, str) or not value.strip()
            or len(value) > limit or not value.isprintable()):
        raise ValueError(code)
    return value


def _decimal(value, code, *, positive=False):
    if not isinstance(value, str) or not value.strip() or len(value) > 256:
        raise ValueError(code)
    try:
        result = Decimal(value)
    except (DecimalException, TypeError, ValueError):
        raise ValueError(code) from None
    if (not result.is_finite() or not -200 <= result.as_tuple().exponent <= 200
            or result.adjusted() > 200 or (positive and result <= 0)):
        raise ValueError(code)
    return result


def _decimal_text(value):
    return format(value.normalize(), "f") if value else "0"


def _digest(document):
    canonical = json.dumps(
        document, sort_keys=True, separators=(",", ":"), allow_nan=False,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(canonical).hexdigest()


def _normalise_positions(rows):
    if not isinstance(rows, list) or len(rows) > _MAX_ROWS:
        raise ValueError("FUNDING_POSITION_SNAPSHOTS_INVALID")
    normalised = []
    seen_ids = set()
    seen_strategy_times = set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != _POSITION_FIELDS:
            raise ValueError("FUNDING_POSITION_SNAPSHOT_FIELDS_INVALID")
        snapshot_id = _text(row["snapshotId"], "FUNDING_POSITION_SNAPSHOT_ID_INVALID")
        strategy = row["strategyId"]
        if not isinstance(strategy, str) or strategy not in STRATEGIES:
            raise ValueError("FUNDING_POSITION_STRATEGY_INVALID")
        if row["symbol"] != SYMBOL:
            raise ValueError("FUNDING_POSITION_SYMBOL_INVALID")
        observed = _timestamp(
            row["observedAtMs"], "FUNDING_POSITION_TIMESTAMP_INVALID"
        )
        quantity = _decimal(row["positionBase"], "FUNDING_POSITION_AMOUNT_INVALID")
        identity = (strategy, observed)
        if snapshot_id in seen_ids or identity in seen_strategy_times:
            raise ValueError("FUNDING_POSITION_SNAPSHOT_DUPLICATE")
        seen_ids.add(snapshot_id)
        seen_strategy_times.add(identity)
        normalised.append({
            "snapshotId": snapshot_id,
            "strategyId": strategy,
            "symbol": SYMBOL,
            "observedAtMs": observed,
            "positionBase": _decimal_text(quantity),
            "_quantity": quantity,
        })
    normalised.sort(key=lambda item: (
        item["strategyId"], item["observedAtMs"], item["snapshotId"],
    ))
    return normalised


def _normalise_rates(rows, start, end):
    if not isinstance(rows, list) or len(rows) > _MAX_ROWS:
        raise ValueError("FUNDING_RATE_EVENTS_INVALID")
    normalised = []
    seen_ids = set()
    seen_times = set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != _RATE_FIELDS:
            raise ValueError("FUNDING_RATE_EVENT_FIELDS_INVALID")
        event_id = _text(row["eventId"], "FUNDING_RATE_EVENT_ID_INVALID")
        if event_id in seen_ids:
            raise ValueError("FUNDING_RATE_EVENT_DUPLICATE")
        seen_ids.add(event_id)
        if row["symbol"] != SYMBOL:
            raise ValueError("FUNDING_RATE_EVENT_SYMBOL_INVALID")
        at_ms = _timestamp(
            row["fundingTimeMs"], "FUNDING_RATE_EVENT_TIMESTAMP_INVALID"
        )
        if not start <= at_ms < end:
            raise ValueError("FUNDING_RATE_EVENT_OUTSIDE_SCOPE")
        if at_ms in seen_times:
            raise ValueError("FUNDING_RATE_EVENT_DUPLICATE")
        seen_times.add(at_ms)
        rate = _decimal(row["fundingRate"], "FUNDING_RATE_VALUE_INVALID")
        mark = _decimal(row["markPrice"], "FUNDING_MARK_PRICE_INVALID", positive=True)
        snapshot_id = _text(
            row["sourceSnapshotId"], "FUNDING_RATE_SOURCE_SNAPSHOT_INVALID"
        )
        normalised.append({
            "eventId": event_id,
            "symbol": SYMBOL,
            "fundingTimeMs": at_ms,
            "fundingRate": _decimal_text(rate),
            "markPrice": _decimal_text(mark),
            "sourceSnapshotId": snapshot_id,
            "_rate": rate,
            "_mark": mark,
        })
    normalised.sort(key=lambda item: (item["fundingTimeMs"], item["eventId"]))
    return normalised


def build_expected_funding_population(
    *, start_at_ms, end_at_ms, position_snapshots, funding_rate_events,
    max_position_age_ms=_DEFAULT_MAX_POSITION_AGE_MS,
):
    """Build the D07 EXPECTED_FUNDING_EVENTS inventory for the declared interval.

    Positive amounts are funding costs (debited from PAPER equity); negative
    amounts are funding credits. For a linear USDT perpetual:
        funding_cost = signed_position_base * mark_price * funding_rate

    The latest position snapshot at or before each settlement is selected per
    strategy. Every strategy must have a sufficiently recent snapshot, including
    zero positions, otherwise the model fails closed. No rounding is applied
    beyond Decimal arithmetic; this is a deterministic PAPER model, not an
    exchange-accounting compatibility claim.
    """
    start = _timestamp(start_at_ms, "FUNDING_POPULATION_START_INVALID")
    end = _timestamp(end_at_ms, "FUNDING_POPULATION_END_INVALID")
    if start >= end:
        raise ValueError("FUNDING_POPULATION_INTERVAL_INVALID")
    max_age = _timestamp(
        max_position_age_ms, "FUNDING_POSITION_MAX_AGE_INVALID"
    )
    if max_age <= 0:
        raise ValueError("FUNDING_POSITION_MAX_AGE_INVALID")

    positions = _normalise_positions(position_snapshots)
    rates = _normalise_rates(funding_rate_events, start, end)

    with localcontext() as context:
        context.prec = 80
        expected_events = []
        for market_event in rates:
            settlement = market_event["fundingTimeMs"]
            for strategy in sorted(STRATEGIES):
                eligible = [
                    item for item in positions
                    if item["strategyId"] == strategy
                    and item["observedAtMs"] <= settlement
                ]
                if not eligible:
                    raise ValueError("FUNDING_POSITION_SNAPSHOT_MISSING")
                position_row = eligible[-1]
                age = settlement - position_row["observedAtMs"]
                if age > max_age:
                    raise ValueError("FUNDING_POSITION_SNAPSHOT_STALE")

                quantity = position_row["_quantity"]
                if quantity == 0:
                    continue
                amount = quantity * market_event["_mark"] * market_event["_rate"]
                event_payload = {
                    "modelVersion": MODEL_VERSION,
                    "strategyId": strategy,
                    "positionSnapshotId": position_row["snapshotId"],
                    "positionObservedAtMs": position_row["observedAtMs"],
                    "positionBase": position_row["positionBase"],
                    "marketFundingEventId": market_event["eventId"],
                    "marketSourceSnapshotId": market_event["sourceSnapshotId"],
                    "fundingTimeMs": settlement,
                    "fundingRate": market_event["fundingRate"],
                    "markPrice": market_event["markPrice"],
                    "amountQuote": _decimal_text(amount),
                    "currency": CURRENCY,
                }
                payload_hash = _digest(event_payload)
                expected_events.append({
                    "eventId": "paper-funding:" + payload_hash[7:],
                    "eventAtMs": settlement,
                    "amountQuote": _decimal_text(amount),
                    "payloadHash": payload_hash,
                })

    if len(expected_events) > _MAX_ROWS:
        raise ValueError("FUNDING_POPULATION_EVENTS_INVALID")
    expected_events.sort(key=lambda item: (item["eventAtMs"], item["eventId"]))
    canonical_inputs = {
        "modelVersion": MODEL_VERSION,
        "symbol": SYMBOL,
        "currency": CURRENCY,
        "startAtMs": start,
        "endAtMs": end,
        "maxPositionAgeMs": max_age,
        "positionSnapshots": [
            {key: item[key] for key in (
                "snapshotId", "strategyId", "symbol", "observedAtMs", "positionBase"
            )}
            for item in positions
        ],
        "fundingRateEvents": [
            {key: item[key] for key in (
                "eventId", "symbol", "fundingTimeMs", "fundingRate",
                "markPrice", "sourceSnapshotId",
            )}
            for item in rates
        ],
    }
    return {
        "schemaVersion": 1,
        "populationType": "EXPECTED_FUNDING_EVENTS",
        "populationDefinitionId": POPULATION_DEFINITION_ID,
        "snapshotId": _digest(canonical_inputs),
        "source": SOURCE,
        "startAtMs": start,
        "endAtMs": end,
        "currency": CURRENCY,
        "events": expected_events,
    }
