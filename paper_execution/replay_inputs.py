"""Read-only, provenance-checked inputs for deterministic daily equity replay."""

import json
import sqlite3
from decimal import Decimal

from paper_execution.account_history import (
    DAY_MS,
    MIGRATION_VERSION,
    MIGRATION_CHECKSUM,
    CUTOVER_SNAPSHOT_MIGRATION_VERSION,
    CUTOVER_SNAPSHOT_MIGRATION_CHECKSUM,
    FEE_PROVENANCE_MIGRATION_VERSION,
    FEE_PROVENANCE_MIGRATION_CHECKSUM,
    STRATEGIES,
    _stamp,
    _text,
    _hash,
    _replay_decimal,
    _replay_text,
)


def load_daily_equity_replay_inputs(connection, *, utc_day_ms, now_ms):
    """Load and validate one day's replay inputs using a read-only SQLite snapshot."""
    if not isinstance(connection, sqlite3.Connection):
        raise ValueError("ACCOUNT_HISTORY_READ_ONLY_CONNECTION_REQUIRED")
    boundary = _stamp(utc_day_ms, "ACCOUNT_HISTORY_UTC_DAY_INVALID")
    now = _stamp(now_ms, "ACCOUNT_HISTORY_NOW_INVALID")
    if boundary % DAY_MS or now < boundary:
        raise ValueError("ACCOUNT_HISTORY_UTC_DAY_INVALID")

    # Require a clean transaction boundary so caller-owned uncommitted writes
    # cannot leak into the replay snapshot.
    if connection.in_transaction:
        raise ValueError("ACCOUNT_HISTORY_READ_ONLY_TRANSACTION_REQUIRED")
    connection.execute("PRAGMA query_only=ON")
    connection.execute("BEGIN")

    from paper_execution.funding import (
        MIGRATION_VERSION as FUNDING_VERSION,
        MIGRATION_CHECKSUM as FUNDING_CHECKSUM,
        CUTOVER_MIGRATION_VERSION as FUNDING_CUTOVER_VERSION,
        CUTOVER_MIGRATION_CHECKSUM as FUNDING_CUTOVER_CHECKSUM,
    )

    required_migrations = (
        (MIGRATION_VERSION, MIGRATION_CHECKSUM, "ACCOUNT_HISTORY_MIGRATION_NOT_APPLIED"),
        (CUTOVER_SNAPSHOT_MIGRATION_VERSION, CUTOVER_SNAPSHOT_MIGRATION_CHECKSUM,
         "CUTOVER_SNAPSHOT_MIGRATION_NOT_APPLIED"),
        (FEE_PROVENANCE_MIGRATION_VERSION, FEE_PROVENANCE_MIGRATION_CHECKSUM,
         "ACCOUNT_HISTORY_FEE_PROVENANCE_MIGRATION_NOT_APPLIED"),
        (FUNDING_VERSION, FUNDING_CHECKSUM, "FUNDING_PROVENANCE_MIGRATION_NOT_APPLIED"),
        (FUNDING_CUTOVER_VERSION, FUNDING_CUTOVER_CHECKSUM,
         "ACCOUNT_EQUITY_CUTOVER_MIGRATION_NOT_APPLIED"),
    )
    for version, checksum, error in required_migrations:
        row = connection.execute(
            "SELECT checksum,status FROM paper_schema_migrations WHERE version=?",
            (version,),
        ).fetchone()
        if row != (checksum, "APPLIED"):
            raise sqlite3.DatabaseError(error)

    cutovers = connection.execute(
        """SELECT cutover_id,mark_observed_at_ms,funding_coverage_start_at_ms
           FROM paper_account_equity_cutovers WHERE account_id=1"""
    ).fetchall()
    if len(cutovers) != 1:
        raise ValueError("ACCOUNT_EQUITY_CUTOVER_REQUIRED")
    cutover_id, snapshot_at, funding_start = cutovers[0]
    snapshot_at = _stamp(snapshot_at, "ACCOUNT_HISTORY_CUTOVER_SNAPSHOT_INVALID")
    funding_start = _stamp(funding_start, "FUNDING_COVERAGE_START_INVALID")
    if not snapshot_at < boundary or funding_start > snapshot_at or snapshot_at > now:
        raise ValueError("ACCOUNT_HISTORY_CUTOVER_BOUNDARY_INVALID")

    snapshot_rows = connection.execute(
        """SELECT strategy_id,snapshot_at_ms,position_base,average_entry_price,
                  realized_pnl_quote,fees_quote,funding_quote,source_snapshot_id,
                  payload_hash,canonical_payload
           FROM paper_account_cutover_ledger_snapshots
           WHERE cutover_id=? ORDER BY strategy_id""",
        (cutover_id,),
    ).fetchall()
    if {row[0] for row in snapshot_rows} != STRATEGIES or len(snapshot_rows) != len(STRATEGIES):
        raise ValueError("ACCOUNT_HISTORY_CUTOVER_LEDGER_SET_INVALID")

    ledgers = {}
    for row in snapshot_rows:
        (strategy_id, recorded_snapshot_at, position, average, realized, fees,
         funding, source_snapshot_id, payload_hash, canonical_payload) = row
        if recorded_snapshot_at != snapshot_at:
            raise ValueError("ACCOUNT_HISTORY_CUTOVER_SNAPSHOT_INVALID")
        source_snapshot_id = _text(
            source_snapshot_id, "ACCOUNT_HISTORY_SNAPSHOT_INVALID"
        )
        payload_hash = _hash(payload_hash, "ACCOUNT_HISTORY_PAYLOAD_HASH_INVALID")
        snapshot = {
            "position_base": _replay_text(_replay_decimal(
                position, "ACCOUNT_HISTORY_CUTOVER_SNAPSHOT_INVALID", signed=True
            )),
            "average_entry_price": _replay_text(_replay_decimal(
                average, "ACCOUNT_HISTORY_CUTOVER_SNAPSHOT_INVALID", nonnegative=True
            )),
            "realized_pnl_quote": _replay_text(_replay_decimal(
                realized, "ACCOUNT_HISTORY_CUTOVER_SNAPSHOT_INVALID", signed=True
            )),
            "fees_quote": _replay_text(_replay_decimal(
                fees, "ACCOUNT_HISTORY_CUTOVER_SNAPSHOT_INVALID", nonnegative=True
            )),
            "funding_quote": _replay_text(_replay_decimal(
                funding, "ACCOUNT_HISTORY_CUTOVER_SNAPSHOT_INVALID", signed=True
            )),
            "snapshot_at_ms": snapshot_at,
        }
        if ((Decimal(snapshot["position_base"]) == 0 and
             Decimal(snapshot["average_entry_price"]) != 0) or
            (Decimal(snapshot["position_base"]) != 0 and
             Decimal(snapshot["average_entry_price"]) <= 0)):
            raise ValueError("ACCOUNT_HISTORY_CUTOVER_SNAPSHOT_INVALID")
        try:
            payload = json.loads(canonical_payload)
        except (TypeError, ValueError):
            raise ValueError("ACCOUNT_HISTORY_CUTOVER_SNAPSHOT_INVALID") from None
        expected_payload = {
            "cutoverId": cutover_id, "strategyId": strategy_id,
            "snapshotAtMs": snapshot_at, "positionBase": position,
            "averageEntryPrice": average, "realizedPnlQuote": realized,
            "feesQuote": fees, "fundingQuote": funding,
            "sourceSnapshotId": source_snapshot_id, "payloadHash": payload_hash,
        }
        if payload != expected_payload:
            raise ValueError("ACCOUNT_HISTORY_CUTOVER_SNAPSHOT_INVALID")
        ledgers[strategy_id] = {
            "snapshot": snapshot,
            "execution_events": [],
            "coverage": [],
        }

    def coverage_chain(stream_type, strategy_id, required_start, required_end):
        rows = connection.execute(
            """SELECT coverage_id,start_at_ms,end_at_ms,status,source,
                      source_snapshot_id,payload_hash,recorded_at_ms
               FROM paper_account_history_coverage
               WHERE account_id=1 AND stream_type=? AND strategy_id IS ?
                 AND end_at_ms>? AND start_at_ms<?
               ORDER BY start_at_ms,end_at_ms,coverage_id""",
            (stream_type, strategy_id, required_start, required_end),
        ).fetchall()
        cursor = required_start
        previous_end = None
        proofs = []
        for coverage_id, start, end, status, source, source_snapshot, digest, recorded in rows:
            start = _stamp(start, "ACCOUNT_HISTORY_COVERAGE_TIME_INVALID")
            end = _stamp(end, "ACCOUNT_HISTORY_COVERAGE_TIME_INVALID")
            recorded = _stamp(recorded, "ACCOUNT_HISTORY_RECORDED_TIME_INVALID")
            if recorded > now:
                raise ValueError("ACCOUNT_HISTORY_EVIDENCE_FROM_FUTURE")
            if (start >= end or end > recorded or status != "VERIFIED"
                    or (previous_end is not None and start < previous_end)
                    or start > cursor):
                raise ValueError("ACCOUNT_HISTORY_COVERAGE_INCOMPLETE")
            proof = {
                "coverage_id": _text(coverage_id, "ACCOUNT_HISTORY_COVERAGE_ID_INVALID"),
                "start_at_ms": start, "end_at_ms": end, "status": status,
                "source": _text(source, "ACCOUNT_HISTORY_SOURCE_INVALID"),
                "source_snapshot_id": _text(
                    source_snapshot, "ACCOUNT_HISTORY_SNAPSHOT_INVALID"
                ),
                "payload_hash": _hash(digest, "ACCOUNT_HISTORY_PAYLOAD_HASH_INVALID"),
                "recorded_at_ms": recorded,
            }
            proofs.append(proof)
            cursor = max(cursor, end)
            previous_end = end
        if cursor < required_end:
            raise ValueError("ACCOUNT_HISTORY_COVERAGE_INCOMPLETE")
        return proofs, max(item["recorded_at_ms"] for item in proofs)

    for strategy_id in sorted(STRATEGIES):
        proofs, watermark = coverage_chain(
            "EXECUTION", strategy_id, snapshot_at, boundary
        )
        ledgers[strategy_id]["coverage"] = proofs
        ledgers[strategy_id]["coverage_watermark_at_ms"] = watermark
        rows = connection.execute(
            """SELECT event_id,event_type,event_at_ms,recorded_at_ms,
                      quantity_delta_base,fill_price,fee_quote,fee_currency,
                      source,source_snapshot_id,payload_hash,order_id,intent_id,
                      source_event_id,position_delta_base,average_entry_price,
                      realized_pnl_delta_quote,fee_delta_quote
               FROM paper_account_event_journal
               WHERE account_id=1 AND strategy_id=? AND event_at_ms<?
               ORDER BY event_at_ms,event_id""",
            (strategy_id, boundary),
        ).fetchall()
        for row in rows:
            (event_id, event_type, event_at, recorded_at, quantity, price, fee,
             currency, source, source_snapshot, digest, order_id, intent_id,
             source_event_id, adjustment_position, adjustment_average,
             adjustment_pnl, adjustment_fee) = row
            event_at = _stamp(event_at, "ACCOUNT_HISTORY_EVENT_TIME_INVALID")
            recorded_at = _stamp(recorded_at, "ACCOUNT_HISTORY_RECORDED_TIME_INVALID")
            if event_at > recorded_at:
                raise ValueError("ACCOUNT_HISTORY_EVENT_TIME_INVALID")
            if event_at <= snapshot_at:
                if recorded_at > snapshot_at:
                    raise ValueError("ACCOUNT_HISTORY_LATE_EVENT")
                continue
            matches = [
                item for item in proofs
                if item["start_at_ms"] <= event_at < item["end_at_ms"]
            ]
            if len(matches) != 1 or recorded_at > matches[0]["recorded_at_ms"]:
                raise ValueError("ACCOUNT_HISTORY_LATE_EVENT")
            if event_type != "FILL":
                raise ValueError("ACCOUNT_HISTORY_EVENT_TYPE_UNSUPPORTED")
            event = {
                "event_id": _text(event_id, "ACCOUNT_HISTORY_EVENT_ID_INVALID", 200),
                "event_type": event_type, "event_at_ms": event_at,
                "recorded_at_ms": recorded_at,
                "quantity_delta_base": quantity, "fill_price": price,
                "fee_quote": fee, "fee_currency": currency,
                "source": _text(source, "ACCOUNT_HISTORY_SOURCE_INVALID"),
                "source_snapshot_id": _text(
                    source_snapshot, "ACCOUNT_HISTORY_SNAPSHOT_INVALID"
                ),
                "payload_hash": _hash(digest, "ACCOUNT_HISTORY_PAYLOAD_HASH_INVALID"),
                "order_id": order_id, "intent_id": intent_id,
                "source_event_id": source_event_id,
            }
            ledgers[strategy_id]["execution_events"].append(event)

    funding_proofs, funding_watermark = [], 0
    funding_rows = connection.execute(
        """SELECT coverage_id,start_at_ms,end_at_ms,status,source,source_snapshot_id,
                  payload_hash,config_version,recorded_at_ms
           FROM paper_funding_coverage WHERE account_id=1
             AND end_at_ms>? AND start_at_ms<?
           ORDER BY start_at_ms,end_at_ms,coverage_id""",
        (snapshot_at, boundary),
    ).fetchall()
    cursor, previous_end = snapshot_at, None
    for coverage_id, start, end, status, source, source_snapshot, digest, config, recorded in funding_rows:
        start = _stamp(start, "FUNDING_COVERAGE_INTERVAL_INVALID")
        end = _stamp(end, "FUNDING_COVERAGE_INTERVAL_INVALID")
        recorded = _stamp(recorded, "FUNDING_COVERAGE_RECORDED_TIME_INVALID")
        if recorded > now:
            raise ValueError("ACCOUNT_HISTORY_EVIDENCE_FROM_FUTURE")
        if (start >= end or end > recorded or status != "VERIFIED"
                or (previous_end is not None and start < previous_end)
                or start > cursor):
            raise ValueError("FUNDING_PROVENANCE_INCOMPLETE")
        funding_proofs.append({
            "coverage_id": _text(coverage_id, "FUNDING_COVERAGE_ID_INVALID"),
            "start_at_ms": start, "end_at_ms": end, "status": status,
            "source": _text(source, "FUNDING_SOURCE_REQUIRED"),
            "source_snapshot_id": _text(source_snapshot, "FUNDING_SOURCE_SNAPSHOT_REQUIRED"),
            "payload_hash": _hash(digest, "FUNDING_PAYLOAD_HASH_INVALID"),
            "config_version": _text(config, "FUNDING_CONFIG_VERSION_REQUIRED"),
            "recorded_at_ms": recorded,
        })
        cursor, previous_end = max(cursor, end), end
    if cursor < boundary:
        raise ValueError("FUNDING_PROVENANCE_INCOMPLETE")
    funding_watermark = max(item["recorded_at_ms"] for item in funding_proofs)

    funding_events = []
    funding_rows = connection.execute(
        """SELECT funding_event_id,strategy_id,amount_quote,event_at_ms,
                  source_snapshot_id,payload_hash,source,recorded_at_ms
           FROM paper_funding_events WHERE account_id=1 AND event_at_ms<?
           ORDER BY event_at_ms,funding_event_id""",
        (boundary,),
    ).fetchall()
    for event_id, strategy_id, amount, event_at, source_snapshot, digest, source, recorded in funding_rows:
        event_at = _stamp(event_at, "FUNDING_EVENT_TIMESTAMP_INVALID")
        recorded = _stamp(recorded, "FUNDING_EVENT_RECORDED_TIME_INVALID")
        if event_at > recorded:
            raise ValueError("FUNDING_EVENT_TIMESTAMP_INVALID")
        if recorded > now:
            raise ValueError("ACCOUNT_HISTORY_EVIDENCE_FROM_FUTURE")
        if event_at <= snapshot_at:
            if recorded > snapshot_at:
                raise ValueError("ACCOUNT_HISTORY_LATE_EVENT")
            continue
        matches = [
            item for item in funding_proofs
            if item["start_at_ms"] <= event_at < item["end_at_ms"]
        ]
        if len(matches) != 1 or recorded > matches[0]["recorded_at_ms"]:
            raise ValueError("ACCOUNT_HISTORY_LATE_EVENT")
        if source == "LEGACY_UNVERIFIED":
            raise ValueError("FUNDING_PROVENANCE_INCOMPLETE")
        funding_events.append({
            "funding_event_id": _text(event_id, "FUNDING_EVENT_ID_INVALID", 200),
            "strategy_id": strategy_id,
            "amount_quote": _replay_text(_replay_decimal(
                amount, "FUNDING_EVENT_AMOUNT_INVALID", signed=True
            )),
            "event_at_ms": event_at, "recorded_at_ms": recorded,
            "source": _text(source, "FUNDING_SOURCE_REQUIRED"),
            "source_snapshot_id": _text(
                source_snapshot, "FUNDING_SOURCE_SNAPSHOT_REQUIRED"
            ),
            "payload_hash": _hash(digest, "FUNDING_PAYLOAD_HASH_INVALID"),
        })

    market_proofs, market_watermark = coverage_chain(
        "MARKET_MARK", None, snapshot_at, boundary + 1
    )
    mark_rows = connection.execute(
        """SELECT mark_id,effective_at_ms,observed_at_ms,mark_price,candle_close_ms,
                  source,source_snapshot_id,dataset_version,payload_hash,
                  quality_status,recorded_at_ms
           FROM paper_market_mark_history
           WHERE account_id=1 AND effective_at_ms=?""",
        (boundary,),
    ).fetchall()
    if len(mark_rows) != 1:
        raise ValueError("ACCOUNT_HISTORY_BOUNDARY_MARK_MISSING")
    (mark_id, effective, observed, mark_price, candle, source, source_snapshot,
     dataset, digest, quality, recorded) = mark_rows[0]
    effective = _stamp(effective, "ACCOUNT_HISTORY_MARK_TIME_INVALID")
    observed = _stamp(observed, "ACCOUNT_HISTORY_MARK_TIME_INVALID")
    candle = _stamp(candle, "ACCOUNT_HISTORY_MARK_TIME_INVALID")
    recorded = _stamp(recorded, "ACCOUNT_HISTORY_RECORDED_TIME_INVALID")
    if observed > now or recorded > now:
        raise ValueError("ACCOUNT_HISTORY_EVIDENCE_FROM_FUTURE")
    if (effective != boundary or candle != boundary or observed < boundary
            or observed - boundary > 30 * 60_000 or recorded < observed
            or recorded > market_watermark or quality != "VERIFIED"):
        raise ValueError("ACCOUNT_HISTORY_BOUNDARY_MARK_INVALID")
    market_mark = {
        "mark_id": _text(mark_id, "ACCOUNT_HISTORY_MARK_ID_INVALID", 200),
        "effective_at_ms": effective, "observed_at_ms": observed,
        "mark_price": _replay_text(_replay_decimal(
            mark_price, "ACCOUNT_HISTORY_MARK_PRICE_INVALID", positive=True
        )),
        "candle_close_ms": candle,
        "source": _text(source, "ACCOUNT_HISTORY_SOURCE_INVALID"),
        "source_snapshot_id": _text(source_snapshot, "ACCOUNT_HISTORY_SNAPSHOT_INVALID"),
        "dataset_version": _text(dataset, "ACCOUNT_HISTORY_DATASET_INVALID"),
        "payload_hash": _hash(digest, "ACCOUNT_HISTORY_PAYLOAD_HASH_INVALID"),
        "quality_status": quality, "recorded_at_ms": recorded,
        "coverage": market_proofs,
    }

    for strategy_id in ledgers:
        ledgers[strategy_id]["funding_events"] = [
            event for event in funding_events if event["strategy_id"] == strategy_id
        ]
        ledgers[strategy_id]["funding_coverage"] = funding_proofs
        ledgers[strategy_id]["funding_coverage_watermark_at_ms"] = funding_watermark

    return {
        "utc_day_ms": boundary,
        "cutover_id": cutover_id,
        "cutover_snapshot_at_ms": snapshot_at,
        "ledgers": ledgers,
        "funding_events": funding_events,
        "funding_coverage": funding_proofs,
        "funding_coverage_watermark_at_ms": funding_watermark,
        "market_mark": market_mark,
    }
