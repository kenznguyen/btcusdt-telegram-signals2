"""Append-only PAPER account history primitives for UTC equity reconstruction."""

from contextlib import closing
from decimal import Decimal, DecimalException
import hashlib
import json
from pathlib import Path
import sqlite3


MIGRATION_VERSION = 6
MIGRATION_CHECKSUM = hashlib.sha256(
    b"dual-ledger-v6:append-only-account-event-journal-market-marks-coverage-daily-baselines"
).hexdigest()
STRATEGIES = {"STRATEGY_CORE", "AI_FREQAI", "LEGACY_UNATTRIBUTED"}
DAY_MS = 86_400_000


def _stamp(value, code):
    if type(value) is not int or value < 0:
        raise ValueError(code)
    return value


def _text(value, code, limit=300):
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise ValueError(code)
    return value.strip()


def _hash(value, code):
    value = _text(value, code, 71)
    if (len(value) != 71 or not value.startswith("sha256:")
            or any(char not in "0123456789abcdef" for char in value[7:])):
        raise ValueError(code)
    return value


def _decimal(value, code, *, positive=False, nonnegative=False, signed=False):
    try:
        result = Decimal(str(value))
    except (DecimalException, TypeError, ValueError):
        raise ValueError(code) from None
    if not result.is_finite() or (positive and result <= 0) or (nonnegative and result < 0):
        raise ValueError(code)
    if not signed and result < 0 and not nonnegative:
        raise ValueError(code)
    return format(result, "f")



def _replay_decimal(value, code, *, positive=False, nonnegative=False, signed=False):
    try:
        number = Decimal(str(value))
    except (DecimalException, TypeError, ValueError):
        raise ValueError(code) from None
    if (not number.is_finite() or (positive and number <= 0)
            or (nonnegative and number < 0)
            or (not signed and not nonnegative and number < 0)):
        raise ValueError(code)
    return number


def _replay_text(number):
    rendered = format(number, "f")
    if "." in rendered:
        rendered = rendered.rstrip("0").rstrip(".")
    return rendered or "0"


def replay_ledger_events(snapshot, execution_events, funding_events, *, boundary_ms, coverage_watermark_at_ms):
    """Replay one ledger using strict event-time ordering and half-open UTC cutoff."""
    boundary = _stamp(boundary_ms, "ACCOUNT_HISTORY_UTC_DAY_INVALID")
    if boundary % DAY_MS:
        raise ValueError("ACCOUNT_HISTORY_UTC_DAY_INVALID")
    if not isinstance(snapshot, dict):
        raise ValueError("ACCOUNT_HISTORY_CUTOVER_SNAPSHOT_INVALID")
    snapshot_at = _stamp(
        snapshot.get("snapshot_at_ms"), "ACCOUNT_HISTORY_CUTOVER_SNAPSHOT_INVALID"
    )
    watermark = _stamp(
        coverage_watermark_at_ms, "ACCOUNT_HISTORY_COVERAGE_WATERMARK_INVALID"
    )
    if not snapshot_at < boundary <= watermark:
        raise ValueError("ACCOUNT_HISTORY_COVERAGE_WATERMARK_INVALID")

    position = _replay_decimal(
        snapshot.get("position_base"), "ACCOUNT_HISTORY_CUTOVER_SNAPSHOT_INVALID", signed=True
    )
    average = _replay_decimal(
        snapshot.get("average_entry_price"), "ACCOUNT_HISTORY_CUTOVER_SNAPSHOT_INVALID",
        nonnegative=True,
    )
    realized = _replay_decimal(
        snapshot.get("realized_pnl_quote"), "ACCOUNT_HISTORY_CUTOVER_SNAPSHOT_INVALID", signed=True
    )
    fees = _replay_decimal(
        snapshot.get("fees_quote"), "ACCOUNT_HISTORY_CUTOVER_SNAPSHOT_INVALID", nonnegative=True
    )
    funding = _replay_decimal(
        snapshot.get("funding_quote"), "ACCOUNT_HISTORY_CUTOVER_SNAPSHOT_INVALID", signed=True
    )
    if (position == 0 and average != 0) or (position != 0 and average <= 0):
        raise ValueError("ACCOUNT_HISTORY_CUTOVER_SNAPSHOT_INVALID")

    if not isinstance(execution_events, (list, tuple)) or not isinstance(funding_events, (list, tuple)):
        raise ValueError("ACCOUNT_HISTORY_EVENT_COLLECTION_INVALID")

    selected_events = []
    seen_event_ids = set()
    for event in execution_events:
        if not isinstance(event, dict):
            raise ValueError("ACCOUNT_HISTORY_EVENT_INVALID")
        event_at = _stamp(event.get("event_at_ms"), "ACCOUNT_HISTORY_EVENT_TIME_INVALID")
        recorded_at = _stamp(
            event.get("recorded_at_ms"), "ACCOUNT_HISTORY_RECORDED_TIME_INVALID"
        )
        if event_at > recorded_at:
            raise ValueError("ACCOUNT_HISTORY_EVENT_TIME_INVALID")
        if event_at <= snapshot_at:
            if recorded_at > snapshot_at:
                raise ValueError("ACCOUNT_HISTORY_LATE_EVENT")
            continue
        if event_at >= boundary:
            continue
        if recorded_at > watermark:
            raise ValueError("ACCOUNT_HISTORY_LATE_EVENT")
        event_id = _text(event.get("event_id"), "ACCOUNT_HISTORY_EVENT_ID_INVALID", 200)
        if event_id in seen_event_ids:
            raise ValueError("ACCOUNT_HISTORY_EVENT_ID_DUPLICATE")
        seen_event_ids.add(event_id)
        selected_events.append((event_at, event_id, event))

    selected_events.sort(key=lambda item: (item[0], item[1]))
    included_event_ids = []
    for _, event_id, event in selected_events:
        if event.get("event_type") != "FILL":
            raise ValueError("ACCOUNT_HISTORY_EVENT_TYPE_UNSUPPORTED")
        if event.get("fee_currency") != "USDT":
            raise ValueError("ACCOUNT_HISTORY_FEE_PROVENANCE_UNKNOWN")
        quantity = _replay_decimal(
            event.get("quantity_delta_base"), "ACCOUNT_HISTORY_FILL_QUANTITY_INVALID", signed=True
        )
        price = _replay_decimal(
            event.get("fill_price"), "ACCOUNT_HISTORY_FILL_PRICE_INVALID", positive=True
        )
        fee = _replay_decimal(
            event.get("fee_quote"), "ACCOUNT_HISTORY_FEE_PROVENANCE_UNKNOWN", nonnegative=True
        )
        if quantity == 0:
            raise ValueError("ACCOUNT_HISTORY_FILL_QUANTITY_INVALID")

        if position == 0 or (position > 0 and quantity > 0) or (position < 0 and quantity < 0):
            new_quantity = abs(position) + abs(quantity)
            average = ((abs(position) * average + abs(quantity) * price) / new_quantity)
            position += quantity
        else:
            closing_quantity = min(abs(position), abs(quantity))
            realized += closing_quantity * (price - average) * (1 if position > 0 else -1)
            next_position = position + quantity
            if next_position == 0:
                average = Decimal(0)
            elif (next_position > 0) != (position > 0):
                average = price
            position = next_position
        fees += fee
        included_event_ids.append(event_id)

    selected_funding = []
    seen_funding_ids = set()
    for event in funding_events:
        if not isinstance(event, dict):
            raise ValueError("ACCOUNT_HISTORY_FUNDING_EVENT_INVALID")
        event_at = _stamp(event.get("event_at_ms"), "FUNDING_EVENT_TIMESTAMP_INVALID")
        recorded_at = _stamp(
            event.get("recorded_at_ms"), "FUNDING_EVENT_RECORDED_TIME_INVALID"
        )
        if event_at > recorded_at:
            raise ValueError("FUNDING_EVENT_TIMESTAMP_INVALID")
        if event_at <= snapshot_at:
            if recorded_at > snapshot_at:
                raise ValueError("ACCOUNT_HISTORY_LATE_EVENT")
            continue
        if event_at >= boundary:
            continue
        if recorded_at > watermark:
            raise ValueError("ACCOUNT_HISTORY_LATE_EVENT")
        event_id = _text(
            event.get("funding_event_id", event.get("event_id")),
            "FUNDING_EVENT_ID_INVALID", 200,
        )
        if event_id in seen_funding_ids:
            raise ValueError("FUNDING_EVENT_ID_DUPLICATE")
        seen_funding_ids.add(event_id)
        amount = _replay_decimal(
            event.get("amount_quote"), "FUNDING_EVENT_AMOUNT_INVALID", signed=True
        )
        selected_funding.append((event_at, event_id, amount))
    selected_funding.sort(key=lambda item: (item[0], item[1]))
    included_funding_event_ids = []
    for _, event_id, amount in selected_funding:
        funding += amount
        included_funding_event_ids.append(event_id)

    return {
        "position_base": _replay_text(position),
        "average_entry_price": _replay_text(average),
        "realized_pnl_quote": _replay_text(realized),
        "fees_quote": _replay_text(fees),
        "funding_quote": _replay_text(funding),
        "included_event_ids": included_event_ids,
        "included_funding_event_ids": included_funding_event_ids,
        "snapshot_at_ms": snapshot_at,
        "coverage_watermark_at_ms": watermark,
        "boundary_ms": boundary,
    }



def load_daily_equity_replay_inputs(connection, *, utc_day_ms):
    """Load and validate one day's replay inputs using a read-only SQLite snapshot."""
    if not isinstance(connection, sqlite3.Connection):
        raise ValueError("ACCOUNT_HISTORY_READ_ONLY_CONNECTION_REQUIRED")
    boundary = _stamp(utc_day_ms, "ACCOUNT_HISTORY_UTC_DAY_INVALID")
    if boundary % DAY_MS:
        raise ValueError("ACCOUNT_HISTORY_UTC_DAY_INVALID")

    # query_only is connection-local; no schema or account data is changed.
    connection.execute("PRAGMA query_only=ON")
    if not connection.in_transaction:
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
    if not snapshot_at < boundary or funding_start > snapshot_at:
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
    if (effective != boundary or candle != boundary or observed < boundary
            or recorded < observed or recorded > market_watermark
            or quality != "VERIFIED"):
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


def migrate_account_history(connection, source_sha):
    if (not isinstance(source_sha, str) or len(source_sha) != 40
            or any(char not in "0123456789abcdef" for char in source_sha.lower())):
        raise ValueError("DUAL_LEDGER_SOURCE_SHA_REQUIRED")
    applied = connection.execute(
        "SELECT checksum,status FROM paper_schema_migrations WHERE version=?",
        (MIGRATION_VERSION,),
    ).fetchone()
    required_tables = {
        "paper_account_event_journal", "paper_account_history_coverage",
        "paper_market_mark_history", "paper_daily_equity_baselines",
    }
    required_triggers = {
        f"{table}_immutable_{operation}"
        for table in (
            "paper_account_event_journal", "paper_account_history_coverage",
            "paper_market_mark_history", "paper_daily_equity_baselines",
        )
        for operation in ("update", "delete")
    }
    if applied:
        if applied != (MIGRATION_CHECKSUM, "APPLIED"):
            raise sqlite3.DatabaseError("ACCOUNT_HISTORY_MIGRATION_CHECKSUM_MISMATCH")
        tables = {row[0] for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )}
        triggers = {row[0] for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='trigger'"
        )}
        if not required_tables.issubset(tables) or not required_triggers.issubset(triggers):
            raise sqlite3.DatabaseError("ACCOUNT_HISTORY_SCHEMA_INCOMPLETE")
        return

    for table in required_tables:
        if connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
        ).fetchone():
            raise sqlite3.DatabaseError("ACCOUNT_HISTORY_SCHEMA_WITHOUT_MIGRATION_RECORD")

    connection.execute("""CREATE TABLE paper_account_event_journal (
        event_id TEXT PRIMARY KEY,
        account_id INTEGER NOT NULL REFERENCES paper_accounts(account_id),
        strategy_id TEXT NOT NULL CHECK(strategy_id IN
            ('STRATEGY_CORE','AI_FREQAI','LEGACY_UNATTRIBUTED')),
        event_type TEXT NOT NULL CHECK(event_type IN ('FILL','LEDGER_ADJUSTMENT')),
        event_at_ms INTEGER NOT NULL,
        recorded_at_ms INTEGER NOT NULL,
        order_id TEXT,
        intent_id TEXT,
        source_event_id TEXT,
        quantity_delta_base TEXT,
        fill_price TEXT,
        fee_quote TEXT NOT NULL,
        position_delta_base TEXT,
        average_entry_price TEXT,
        realized_pnl_delta_quote TEXT,
        fee_delta_quote TEXT,
        source TEXT NOT NULL CHECK(length(trim(source))>0),
        source_snapshot_id TEXT NOT NULL CHECK(length(trim(source_snapshot_id))>0),
        payload_hash TEXT NOT NULL CHECK(length(payload_hash)=71
            AND substr(payload_hash,1,7)='sha256:'
            AND substr(payload_hash,8) NOT GLOB '*[^0-9a-f]*'),
        canonical_payload TEXT NOT NULL,
        created_at_ms INTEGER NOT NULL,
        CHECK(event_at_ms <= recorded_at_ms),
        CHECK((event_type='FILL' AND quantity_delta_base IS NOT NULL
            AND fill_price IS NOT NULL AND CAST(quantity_delta_base AS REAL) != 0
            AND CAST(fill_price AS REAL) > 0)
          OR (event_type='LEDGER_ADJUSTMENT' AND position_delta_base IS NOT NULL
            AND average_entry_price IS NOT NULL
            AND realized_pnl_delta_quote IS NOT NULL AND fee_delta_quote IS NOT NULL))
    )""")
    connection.execute("""CREATE TABLE paper_account_history_coverage (
        coverage_id TEXT PRIMARY KEY,
        account_id INTEGER NOT NULL REFERENCES paper_accounts(account_id),
        stream_type TEXT NOT NULL CHECK(stream_type IN ('EXECUTION','MARKET_MARK')),
        strategy_id TEXT CHECK(strategy_id IS NULL OR strategy_id IN
            ('STRATEGY_CORE','AI_FREQAI','LEGACY_UNATTRIBUTED')),
        start_at_ms INTEGER NOT NULL,
        end_at_ms INTEGER NOT NULL,
        status TEXT NOT NULL CHECK(status IN ('VERIFIED','UNKNOWN')),
        source TEXT NOT NULL CHECK(length(trim(source))>0),
        source_snapshot_id TEXT NOT NULL CHECK(length(trim(source_snapshot_id))>0),
        payload_hash TEXT NOT NULL CHECK(length(payload_hash)=71
            AND substr(payload_hash,1,7)='sha256:'
            AND substr(payload_hash,8) NOT GLOB '*[^0-9a-f]*'),
        recorded_at_ms INTEGER NOT NULL,
        CHECK(start_at_ms < end_at_ms),
        CHECK((stream_type='EXECUTION' AND strategy_id IS NOT NULL)
           OR (stream_type='MARKET_MARK' AND strategy_id IS NULL))
    )""")
    connection.execute("""CREATE TABLE paper_market_mark_history (
        mark_id TEXT PRIMARY KEY,
        account_id INTEGER NOT NULL REFERENCES paper_accounts(account_id),
        effective_at_ms INTEGER NOT NULL,
        observed_at_ms INTEGER NOT NULL,
        mark_price TEXT NOT NULL,
        candle_close_ms INTEGER NOT NULL,
        source TEXT NOT NULL CHECK(length(trim(source))>0),
        source_snapshot_id TEXT NOT NULL CHECK(length(trim(source_snapshot_id))>0),
        dataset_version TEXT NOT NULL CHECK(length(trim(dataset_version))>0),
        payload_hash TEXT NOT NULL CHECK(length(payload_hash)=71
            AND substr(payload_hash,1,7)='sha256:'
            AND substr(payload_hash,8) NOT GLOB '*[^0-9a-f]*'),
        quality_status TEXT NOT NULL CHECK(quality_status IN ('VERIFIED','UNKNOWN')),
        recorded_at_ms INTEGER NOT NULL,
        UNIQUE(account_id,effective_at_ms),
        CHECK(effective_at_ms % 86400000 = 0),
        CHECK(candle_close_ms = effective_at_ms),
        CHECK(observed_at_ms >= effective_at_ms),
        CHECK(effective_at_ms <= recorded_at_ms)
    )""")
    connection.execute("""CREATE TABLE paper_daily_equity_baselines (
        baseline_id TEXT PRIMARY KEY,
        account_id INTEGER NOT NULL REFERENCES paper_accounts(account_id),
        utc_day_ms INTEGER NOT NULL,
        baseline_equity_quote TEXT NOT NULL,
        mark_id TEXT NOT NULL REFERENCES paper_market_mark_history(mark_id),
        starting_cutover_id TEXT NOT NULL REFERENCES paper_account_equity_cutovers(cutover_id),
        replay_digest TEXT NOT NULL,
        algorithm_version TEXT NOT NULL,
        source_sha TEXT NOT NULL,
        recorded_at_ms INTEGER NOT NULL,
        UNIQUE(account_id,utc_day_ms),
        CHECK(utc_day_ms % 86400000 = 0)
    )""")

    for table in required_tables:
        connection.execute(
            f"""CREATE TRIGGER {table}_immutable_update BEFORE UPDATE ON {table}
                BEGIN SELECT RAISE(ABORT,'ACCOUNT_HISTORY_IMMUTABLE'); END"""
        )
        connection.execute(
            f"""CREATE TRIGGER {table}_immutable_delete BEFORE DELETE ON {table}
                BEGIN SELECT RAISE(ABORT,'ACCOUNT_HISTORY_IMMUTABLE'); END"""
        )
    applied_at = connection.execute(
        "SELECT updated_at_ms FROM paper_account_risk_state WHERE account_id=1"
    ).fetchone()[0]
    connection.execute(
        """INSERT INTO paper_schema_migrations
           (version,name,checksum,applied_at_ms,source_sha,status)
           VALUES (6,'account_history_journal_v6',?,?,?,'APPLIED')""",
        (MIGRATION_CHECKSUM, applied_at, source_sha.lower()),
    )


CUTOVER_SNAPSHOT_MIGRATION_VERSION = 7
CUTOVER_SNAPSHOT_MIGRATION_CHECKSUM = hashlib.sha256(
    b"dual-ledger-v7:immutable-per-ledger-cutover-snapshots"
).hexdigest()


def migrate_cutover_ledger_snapshots(connection, source_sha):
    if (not isinstance(source_sha, str) or len(source_sha) != 40
            or any(char not in "0123456789abcdef" for char in source_sha.lower())):
        raise ValueError("DUAL_LEDGER_SOURCE_SHA_REQUIRED")
    applied = connection.execute(
        "SELECT checksum,status FROM paper_schema_migrations WHERE version=?",
        (CUTOVER_SNAPSHOT_MIGRATION_VERSION,),
    ).fetchone()
    if applied:
        if applied != (CUTOVER_SNAPSHOT_MIGRATION_CHECKSUM, "APPLIED"):
            raise sqlite3.DatabaseError("CUTOVER_SNAPSHOT_MIGRATION_CHECKSUM_MISMATCH")
        columns = {row[1] for row in connection.execute(
            "PRAGMA table_info(paper_account_cutover_ledger_snapshots)"
        )}
        triggers = {row[0] for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='trigger'"
        )}
        if not {
            "cutover_id", "strategy_id", "snapshot_at_ms", "position_base",
            "average_entry_price", "realized_pnl_quote", "fees_quote",
            "funding_quote", "source_snapshot_id", "payload_hash",
        }.issubset(columns) or not {
            "paper_account_cutover_ledger_snapshots_immutable_update",
            "paper_account_cutover_ledger_snapshots_immutable_delete",
        }.issubset(triggers):
            raise sqlite3.DatabaseError("CUTOVER_SNAPSHOT_SCHEMA_INCOMPLETE")
        return

    if connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' "
        "AND name='paper_account_cutover_ledger_snapshots'"
    ).fetchone():
        raise sqlite3.DatabaseError("CUTOVER_SNAPSHOT_SCHEMA_WITHOUT_MIGRATION_RECORD")
    connection.execute("""CREATE TABLE paper_account_cutover_ledger_snapshots (
        cutover_id TEXT NOT NULL REFERENCES paper_account_equity_cutovers(cutover_id),
        strategy_id TEXT NOT NULL CHECK(strategy_id IN
            ('STRATEGY_CORE','AI_FREQAI','LEGACY_UNATTRIBUTED')),
        snapshot_at_ms INTEGER NOT NULL,
        position_base TEXT NOT NULL,
        average_entry_price TEXT NOT NULL,
        realized_pnl_quote TEXT NOT NULL,
        fees_quote TEXT NOT NULL,
        funding_quote TEXT NOT NULL,
        source_snapshot_id TEXT NOT NULL CHECK(length(trim(source_snapshot_id))>0),
        payload_hash TEXT NOT NULL CHECK(length(payload_hash)=71
            AND substr(payload_hash,1,7)='sha256:'
            AND substr(payload_hash,8) NOT GLOB '*[^0-9a-f]*'),
        canonical_payload TEXT NOT NULL,
        created_at_ms INTEGER NOT NULL,
        PRIMARY KEY(cutover_id,strategy_id)
    )""")
    connection.execute("""CREATE TRIGGER paper_account_cutover_ledger_snapshots_immutable_update
        BEFORE UPDATE ON paper_account_cutover_ledger_snapshots
        BEGIN SELECT RAISE(ABORT,'ACCOUNT_CUTOVER_SNAPSHOT_IMMUTABLE'); END""")
    connection.execute("""CREATE TRIGGER paper_account_cutover_ledger_snapshots_immutable_delete
        BEFORE DELETE ON paper_account_cutover_ledger_snapshots
        BEGIN SELECT RAISE(ABORT,'ACCOUNT_CUTOVER_SNAPSHOT_IMMUTABLE'); END""")
    applied_at = connection.execute(
        "SELECT updated_at_ms FROM paper_account_risk_state WHERE account_id=1"
    ).fetchone()[0]
    connection.execute(
        """INSERT INTO paper_schema_migrations
           (version,name,checksum,applied_at_ms,source_sha,status)
           VALUES (7,'account_cutover_ledger_snapshots_v7',?,?,?,'APPLIED')""",
        (CUTOVER_SNAPSHOT_MIGRATION_CHECKSUM, applied_at, source_sha.lower()),
    )


FEE_PROVENANCE_MIGRATION_VERSION = 8
FEE_PROVENANCE_MIGRATION_CHECKSUM = hashlib.sha256(
    b"dual-ledger-v8:explicit-fee-amount-and-quote-currency"
).hexdigest()


def migrate_fee_currency_provenance(connection, source_sha):
    if (not isinstance(source_sha, str) or len(source_sha) != 40
            or any(char not in "0123456789abcdef" for char in source_sha.lower())):
        raise ValueError("DUAL_LEDGER_SOURCE_SHA_REQUIRED")
    applied = connection.execute(
        "SELECT checksum,status FROM paper_schema_migrations WHERE version=?",
        (FEE_PROVENANCE_MIGRATION_VERSION,),
    ).fetchone()
    columns = {row[1] for row in connection.execute(
        "PRAGMA table_info(paper_account_event_journal)"
    )}
    triggers = {row[0] for row in connection.execute(
        "SELECT name FROM sqlite_master WHERE type='trigger'"
    )}
    trigger_name = "paper_account_event_journal_fee_currency_required"
    if applied:
        if applied != (FEE_PROVENANCE_MIGRATION_CHECKSUM, "APPLIED"):
            raise sqlite3.DatabaseError("FEE_PROVENANCE_MIGRATION_CHECKSUM_MISMATCH")
        if "fee_currency" not in columns or trigger_name not in triggers:
            raise sqlite3.DatabaseError("FEE_PROVENANCE_SCHEMA_INCOMPLETE")
        return
    if "fee_currency" in columns or trigger_name in triggers:
        raise sqlite3.DatabaseError("FEE_PROVENANCE_SCHEMA_WITHOUT_MIGRATION_RECORD")
    connection.execute("ALTER TABLE paper_account_event_journal ADD COLUMN fee_currency TEXT")
    connection.execute("""CREATE TRIGGER paper_account_event_journal_fee_currency_required
        BEFORE INSERT ON paper_account_event_journal
        WHEN NEW.fee_currency IS NULL OR NEW.fee_currency != 'USDT'
        BEGIN SELECT RAISE(ABORT,'ACCOUNT_HISTORY_FEE_CURRENCY_REQUIRED'); END""")
    applied_at = connection.execute(
        "SELECT updated_at_ms FROM paper_account_risk_state WHERE account_id=1"
    ).fetchone()[0]
    connection.execute(
        """INSERT INTO paper_schema_migrations
           (version,name,checksum,applied_at_ms,source_sha,status)
           VALUES (8,'account_history_fee_provenance_v8',?,?,?,'APPLIED')""",
        (FEE_PROVENANCE_MIGRATION_CHECKSUM, applied_at, source_sha.lower()),
    )


def _connect(path):
    path = Path(path).resolve()
    if not path.is_file():
        raise FileNotFoundError("Paper ledger is unavailable")
    db = sqlite3.connect(path, timeout=10)
    db.execute("PRAGMA foreign_keys=ON")
    return db


def _require_migration(db):
    row = db.execute(
        "SELECT checksum,status FROM paper_schema_migrations WHERE version=?",
        (MIGRATION_VERSION,),
    ).fetchone()
    if row != (MIGRATION_CHECKSUM, "APPLIED"):
        raise sqlite3.DatabaseError("ACCOUNT_HISTORY_MIGRATION_NOT_APPLIED")
    fee_row = db.execute(
        "SELECT checksum,status FROM paper_schema_migrations WHERE version=?",
        (FEE_PROVENANCE_MIGRATION_VERSION,),
    ).fetchone()
    if fee_row != (FEE_PROVENANCE_MIGRATION_CHECKSUM, "APPLIED"):
        raise sqlite3.DatabaseError("ACCOUNT_HISTORY_FEE_PROVENANCE_MIGRATION_NOT_APPLIED")


def record_account_history_event(
    db_path, *, event_id, strategy_id, event_type, event_at_ms, source,
    source_snapshot_id, payload_hash, recorded_at_ms, fee_quote, fee_currency,
    quantity_delta_base=None, fill_price=None, order_id=None, intent_id=None,
    source_event_id=None, position_delta_base=None, average_entry_price=None,
    realized_pnl_delta_quote=None, fee_delta_quote=None,
):
    event_id = _text(event_id, "ACCOUNT_HISTORY_EVENT_ID_INVALID", 200)
    if strategy_id not in STRATEGIES:
        raise ValueError("ACCOUNT_HISTORY_STRATEGY_INVALID")
    if event_type not in {"FILL", "LEDGER_ADJUSTMENT"}:
        raise ValueError("ACCOUNT_HISTORY_EVENT_TYPE_INVALID")
    event_at = _stamp(event_at_ms, "ACCOUNT_HISTORY_EVENT_TIME_INVALID")
    recorded = _stamp(recorded_at_ms, "ACCOUNT_HISTORY_RECORDED_TIME_INVALID")
    if event_at > recorded:
        raise ValueError("ACCOUNT_HISTORY_EVENT_TIME_INVALID")
    source = _text(source, "ACCOUNT_HISTORY_SOURCE_INVALID")
    snapshot = _text(source_snapshot_id, "ACCOUNT_HISTORY_SNAPSHOT_INVALID")
    digest = _hash(payload_hash, "ACCOUNT_HISTORY_PAYLOAD_HASH_INVALID")
    fee = _decimal(fee_quote, "ACCOUNT_HISTORY_FEE_INVALID", nonnegative=True)
    currency = _text(fee_currency, "ACCOUNT_HISTORY_FEE_CURRENCY_INVALID", 10)
    if currency != "USDT":
        raise ValueError("ACCOUNT_HISTORY_FEE_CURRENCY_INVALID")
    values = {
        "event_id": event_id, "strategy_id": strategy_id, "event_type": event_type,
        "event_at_ms": event_at, "recorded_at_ms": recorded, "order_id": order_id,
        "intent_id": intent_id, "source_event_id": source_event_id,
        "quantity_delta_base": None, "fill_price": None, "fee_quote": fee,
        "fee_currency": currency, "position_delta_base": None, "average_entry_price": None,
        "realized_pnl_delta_quote": None, "fee_delta_quote": None,
        "source": source, "source_snapshot_id": snapshot, "payload_hash": digest,
    }
    if event_type == "FILL":
        quantity = _decimal(quantity_delta_base, "ACCOUNT_HISTORY_FILL_QUANTITY_INVALID", signed=True)
        price = _decimal(fill_price, "ACCOUNT_HISTORY_FILL_PRICE_INVALID", positive=True)
        if Decimal(quantity) == 0:
            raise ValueError("ACCOUNT_HISTORY_FILL_QUANTITY_INVALID")
        values["quantity_delta_base"], values["fill_price"] = quantity, price
    else:
        values["position_delta_base"] = _decimal(
            position_delta_base, "ACCOUNT_HISTORY_ADJUSTMENT_POSITION_INVALID", signed=True
        )
        values["average_entry_price"] = _decimal(
            average_entry_price, "ACCOUNT_HISTORY_ADJUSTMENT_AVERAGE_INVALID", nonnegative=True
        )
        values["realized_pnl_delta_quote"] = _decimal(
            realized_pnl_delta_quote, "ACCOUNT_HISTORY_ADJUSTMENT_PNL_INVALID", signed=True
        )
        values["fee_delta_quote"] = _decimal(
            fee_delta_quote, "ACCOUNT_HISTORY_ADJUSTMENT_FEE_INVALID", signed=True
        )
    for key, value in (("order_id", order_id), ("intent_id", intent_id), ("source_event_id", source_event_id)):
        if value is not None:
            values[key] = _text(value, "ACCOUNT_HISTORY_EVENT_REFERENCE_INVALID", 200)
    canonical = json.dumps(values, sort_keys=True, separators=(",", ":"), allow_nan=False)
    with closing(_connect(db_path)) as db, db:
        db.execute("BEGIN IMMEDIATE")
        _require_migration(db)
        prior = db.execute(
            "SELECT canonical_payload,payload_hash FROM paper_account_event_journal WHERE event_id=?",
            (event_id,),
        ).fetchone()
        if prior:
            if prior != (canonical, digest):
                raise ValueError("ACCOUNT_HISTORY_EVENT_ID_CONFLICT")
            return {"eventId": event_id, "payloadHash": digest, "idempotent": True}
        columns = ["account_id", *values.keys(), "canonical_payload", "created_at_ms"]
        db.execute(
            f"INSERT INTO paper_account_event_journal ({','.join(columns)}) VALUES ({','.join('?' for _ in columns)})",
            (1, *values.values(), canonical, recorded),
        )
    return {"eventId": event_id, "payloadHash": digest, "idempotent": False}


def record_account_history_coverage(
    db_path, *, coverage_id, stream_type, strategy_id, start_at_ms, end_at_ms,
    status, source, source_snapshot_id, payload_hash, recorded_at_ms,
):
    coverage_id = _text(coverage_id, "ACCOUNT_HISTORY_COVERAGE_ID_INVALID", 200)
    if stream_type not in {"EXECUTION", "MARKET_MARK"}:
        raise ValueError("ACCOUNT_HISTORY_STREAM_INVALID")
    if (stream_type == "EXECUTION" and strategy_id not in STRATEGIES
            or stream_type == "MARKET_MARK" and strategy_id is not None):
        raise ValueError("ACCOUNT_HISTORY_COVERAGE_OWNER_INVALID")
    start = _stamp(start_at_ms, "ACCOUNT_HISTORY_COVERAGE_TIME_INVALID")
    end = _stamp(end_at_ms, "ACCOUNT_HISTORY_COVERAGE_TIME_INVALID")
    recorded = _stamp(recorded_at_ms, "ACCOUNT_HISTORY_RECORDED_TIME_INVALID")
    if start >= end or end > recorded:
        raise ValueError("ACCOUNT_HISTORY_COVERAGE_TIME_INVALID")
    if status not in {"VERIFIED", "UNKNOWN"}:
        raise ValueError("ACCOUNT_HISTORY_COVERAGE_STATUS_INVALID")
    source = _text(source, "ACCOUNT_HISTORY_SOURCE_INVALID")
    snapshot = _text(source_snapshot_id, "ACCOUNT_HISTORY_SNAPSHOT_INVALID")
    digest = _hash(payload_hash, "ACCOUNT_HISTORY_PAYLOAD_HASH_INVALID")
    with closing(_connect(db_path)) as db, db:
        db.execute("BEGIN IMMEDIATE")
        _require_migration(db)
        prior = db.execute(
            "SELECT stream_type,strategy_id,start_at_ms,end_at_ms,status,source,source_snapshot_id,payload_hash "
            "FROM paper_account_history_coverage WHERE coverage_id=?", (coverage_id,)
        ).fetchone()
        identity = (stream_type, strategy_id, start, end, status, source, snapshot, digest)
        if prior:
            if prior != identity:
                raise ValueError("ACCOUNT_HISTORY_COVERAGE_ID_CONFLICT")
            return {"coverageId": coverage_id, "idempotent": True}
        overlap = db.execute(
            """SELECT 1 FROM paper_account_history_coverage
               WHERE account_id=1 AND stream_type=? AND strategy_id IS ?
                 AND start_at_ms < ? AND end_at_ms > ? LIMIT 1""",
            (stream_type, strategy_id, end, start),
        ).fetchone()
        if overlap:
            raise ValueError("ACCOUNT_HISTORY_COVERAGE_OVERLAP")
        db.execute(
            """INSERT INTO paper_account_history_coverage
               (coverage_id,account_id,stream_type,strategy_id,start_at_ms,end_at_ms,
                status,source,source_snapshot_id,payload_hash,recorded_at_ms)
               VALUES (?,1,?,?,?,?,?,?,?,?,?)""",
            (coverage_id, stream_type, strategy_id, start, end, status,
             source, snapshot, digest, recorded),
        )
    return {"coverageId": coverage_id, "idempotent": False}


def record_market_mark_history(
    db_path, *, mark_id, effective_at_ms, observed_at_ms, mark_price,
    candle_close_ms, source, source_snapshot_id, dataset_version,
    payload_hash, quality_status, recorded_at_ms,
):
    mark_id = _text(mark_id, "ACCOUNT_HISTORY_MARK_ID_INVALID", 200)
    effective = _stamp(effective_at_ms, "ACCOUNT_HISTORY_MARK_TIME_INVALID")
    observed = _stamp(observed_at_ms, "ACCOUNT_HISTORY_MARK_TIME_INVALID")
    candle = _stamp(candle_close_ms, "ACCOUNT_HISTORY_MARK_TIME_INVALID")
    recorded = _stamp(recorded_at_ms, "ACCOUNT_HISTORY_RECORDED_TIME_INVALID")
    if (effective % DAY_MS or candle != effective or observed < effective
            or effective > recorded):
        raise ValueError("ACCOUNT_HISTORY_MARK_NOT_EXACT_UTC_BOUNDARY")
    price = _decimal(mark_price, "ACCOUNT_HISTORY_MARK_PRICE_INVALID", positive=True)
    source = _text(source, "ACCOUNT_HISTORY_SOURCE_INVALID")
    snapshot = _text(source_snapshot_id, "ACCOUNT_HISTORY_SNAPSHOT_INVALID")
    dataset = _text(dataset_version, "ACCOUNT_HISTORY_DATASET_INVALID")
    digest = _hash(payload_hash, "ACCOUNT_HISTORY_PAYLOAD_HASH_INVALID")
    if quality_status not in {"VERIFIED", "UNKNOWN"}:
        raise ValueError("ACCOUNT_HISTORY_MARK_QUALITY_INVALID")
    with closing(_connect(db_path)) as db, db:
        db.execute("BEGIN IMMEDIATE")
        _require_migration(db)
        prior = db.execute(
            "SELECT effective_at_ms,observed_at_ms,mark_price,candle_close_ms,source,"
            "source_snapshot_id,dataset_version,payload_hash,quality_status,recorded_at_ms "
            "FROM paper_market_mark_history WHERE mark_id=?", (mark_id,)
        ).fetchone()
        identity = (effective, observed, price, candle, source, snapshot, dataset, digest, quality_status, recorded)
        if prior:
            if prior != identity:
                raise ValueError("ACCOUNT_HISTORY_MARK_ID_CONFLICT")
            return {"markId": mark_id, "effectiveAtMs": effective, "idempotent": True}
        try:
            db.execute(
                """INSERT INTO paper_market_mark_history
                   (mark_id,account_id,effective_at_ms,observed_at_ms,mark_price,candle_close_ms,
                    source,source_snapshot_id,dataset_version,payload_hash,quality_status,recorded_at_ms)
                   VALUES (?,1,?,?,?,?,?,?,?,?,?,?)""",
                (mark_id, effective, observed, price, candle, source, snapshot,
                 dataset, digest, quality_status, recorded),
            )
        except sqlite3.IntegrityError as exc:
            raise ValueError("ACCOUNT_HISTORY_MARK_BOUNDARY_CONFLICT") from exc
    return {"markId": mark_id, "effectiveAtMs": effective, "idempotent": False}


def reconstruct_daily_equity_baseline(db_path, *, utc_day_ms, now_ms, source_sha):
    boundary = _stamp(utc_day_ms, "ACCOUNT_HISTORY_UTC_DAY_INVALID")
    now = _stamp(now_ms, "ACCOUNT_HISTORY_NOW_INVALID")
    if boundary % DAY_MS or now < boundary:
        raise ValueError("ACCOUNT_HISTORY_UTC_DAY_INVALID")
    if (not isinstance(source_sha, str) or len(source_sha) != 40
            or any(char not in "0123456789abcdef" for char in source_sha.lower())):
        raise ValueError("DUAL_LEDGER_SOURCE_SHA_REQUIRED")
    with closing(_connect(db_path)) as db, db:
        db.execute("BEGIN IMMEDIATE")
        _require_migration(db)
        cutover = db.execute(
            """SELECT cutover_id,mark_observed_at_ms FROM paper_account_equity_cutovers
               WHERE account_id=1 LIMIT 1"""
        ).fetchone()
        if cutover is None:
            raise ValueError("ACCOUNT_EQUITY_CUTOVER_REQUIRED")
        start = cutover[1]
        for strategy_id in sorted(STRATEGIES):
            cursor = start
            rows = db.execute(
                """SELECT start_at_ms,end_at_ms,status FROM paper_account_history_coverage
                   WHERE account_id=1 AND stream_type='EXECUTION' AND strategy_id=?
                     AND end_at_ms>? AND start_at_ms<? ORDER BY start_at_ms,end_at_ms""",
                (strategy_id, start, boundary),
            ).fetchall()
            for row_start, row_end, status in rows:
                if row_start > cursor or status != "VERIFIED":
                    raise ValueError("ACCOUNT_HISTORY_COVERAGE_INCOMPLETE")
                cursor = max(cursor, row_end)
            if cursor < boundary:
                raise ValueError("ACCOUNT_HISTORY_COVERAGE_INCOMPLETE")
        cursor = start
        mark_coverage = db.execute(
            """SELECT start_at_ms,end_at_ms,status FROM paper_account_history_coverage
               WHERE account_id=1 AND stream_type='MARKET_MARK' AND strategy_id IS NULL
                 AND end_at_ms>? AND start_at_ms<? ORDER BY start_at_ms,end_at_ms""",
            (start, boundary),
        ).fetchall()
        for row_start, row_end, status in mark_coverage:
            if row_start > cursor or status != "VERIFIED":
                raise ValueError("ACCOUNT_HISTORY_COVERAGE_INCOMPLETE")
            cursor = max(cursor, row_end)
        if cursor < boundary:
            raise ValueError("ACCOUNT_HISTORY_COVERAGE_INCOMPLETE")
        mark = db.execute(
            """SELECT mark_id FROM paper_market_mark_history
               WHERE account_id=1 AND effective_at_ms=? AND quality_status='VERIFIED'""",
            (boundary,),
        ).fetchone()
        if mark is None:
            raise ValueError("ACCOUNT_HISTORY_BOUNDARY_MARK_MISSING")
        raise ValueError("ACCOUNT_HISTORY_REPLAY_NOT_IMPLEMENTED")
