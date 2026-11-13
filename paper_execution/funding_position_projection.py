"""Read-only PAPER position projection from cutover snapshots and execution history."""

import hashlib
import json
import re
import sqlite3
from bisect import bisect_right
from contextlib import closing
from decimal import localcontext
from pathlib import Path

from paper_execution.account_history import (
    STRATEGIES, _replay_decimal, _replay_text, _stamp,
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
            "position_decimal": position,
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
        quantity_decimal = _replay_decimal(
            quantity, "ACCOUNT_HISTORY_FILL_QUANTITY_INVALID", signed=True
        )
        price_decimal = _replay_decimal(
            price, "ACCOUNT_HISTORY_FILL_PRICE_INVALID", positive=True
        )
        fee_decimal = _replay_decimal(
            fee, "ACCOUNT_HISTORY_FEE_PROVENANCE_UNKNOWN", nonnegative=True
        )
        if (len(quantity_decimal.as_tuple().digits) > 80
                or len(price_decimal.as_tuple().digits) > 80
                or len(fee_decimal.as_tuple().digits) > 80
                or quantity_decimal == 0):
            raise ValueError("FUNDING_POSITION_EVENT_INVALID")
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
            "_quantity": quantity_decimal,
            "_price": price_decimal,
            "_fee": fee_decimal,
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


def _chain_digest(previous, entry):
    return _digest({"previous": previous, "entry": entry})


def build_paper_position_snapshots(
    *, cutover_snapshots, execution_events, execution_coverage,
    settlement_times, now_ms,
):
    """Project signed PAPER positions immediately before ordered settlements.

    The cutover snapshots are the baseline. Only immutable FILL events after
    that baseline and strictly before each settlement are replayed. Every
    settlement requires contiguous, non-overlapping VERIFIED EXECUTION
    coverage through settlement+1ms. A fill exactly at settlement is rejected
    because its ordering relative to the funding event is ambiguous.

    Events and coverage are consumed incrementally across sorted settlements;
    each event and coverage row is processed at most once per strategy.
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
    with localcontext() as context:
        context.prec = 240
        for strategy in sorted(STRATEGIES):
            strategy_events = events[strategy]
            strategy_coverage = coverage[strategy]
            event_index = 0
            coverage_index = 0
            selected_proofs = []
            proof_starts = []
            coverage_cursor = snapshot_at
            previous_coverage_end = None
            coverage_watermark = 0
            coverage_digest = _digest({
                "projectionVersion": "paper-position-asof-v1",
                "cutoverId": cutover_id,
                "strategyId": strategy,
                "snapshotAtMs": snapshot_at,
            })
            event_digest = _digest({
                "projectionVersion": "paper-position-asof-v1-events",
                "cutoverId": cutover_id,
                "strategyId": strategy,
            })
            event_count = 0
            position = snapshots[strategy]["position_decimal"]

            for settlement in settlements:
                required_end = settlement + 1
                if required_end > now:
                    raise ValueError("FUNDING_POSITION_COVERAGE_INCOMPLETE")

                while (coverage_index < len(strategy_coverage)
                       and strategy_coverage[coverage_index]["start_at_ms"] < required_end):
                    proof = strategy_coverage[coverage_index]
                    coverage_index += 1
                    start_at = proof["start_at_ms"]
                    end_at = proof["end_at_ms"]
                    recorded_at = proof["recorded_at_ms"]
                    if end_at <= snapshot_at:
                        continue
                    if (recorded_at > now or start_at >= end_at or end_at > recorded_at
                            or proof["status"] != "VERIFIED"
                            or (previous_coverage_end is not None
                                and start_at < previous_coverage_end)
                            or start_at > coverage_cursor):
                        raise ValueError("FUNDING_POSITION_COVERAGE_INCOMPLETE")
                    coverage_cursor = max(coverage_cursor, end_at)
                    previous_coverage_end = end_at
                    coverage_watermark = max(coverage_watermark, recorded_at)
                    selected_proofs.append(proof)
                    proof_starts.append(start_at)
                    coverage_digest = _chain_digest(coverage_digest, {
                        "coverageId": proof["coverage_id"],
                        "startAtMs": start_at,
                        "endAtMs": end_at,
                        "payloadHash": proof["payload_hash"],
                        "recordedAtMs": recorded_at,
                    })

                if coverage_cursor < required_end or coverage_watermark < settlement:
                    raise ValueError("FUNDING_POSITION_COVERAGE_INCOMPLETE")

                while (event_index < len(strategy_events)
                       and strategy_events[event_index]["event_at_ms"] < settlement):
                    event = strategy_events[event_index]
                    event_index += 1
                    event_at = event["event_at_ms"]
                    if event_at <= snapshot_at:
                        if event["recorded_at_ms"] > snapshot_at:
                            raise ValueError("ACCOUNT_HISTORY_LATE_EVENT")
                        continue

                    proof_index = bisect_right(proof_starts, event_at) - 1
                    if proof_index < 0:
                        raise ValueError("FUNDING_POSITION_EVENT_COVERAGE_INVALID")
                    proof = selected_proofs[proof_index]
                    if (not proof["start_at_ms"] <= event_at < proof["end_at_ms"]
                            or event["recorded_at_ms"] > proof["recorded_at_ms"]):
                        raise ValueError("FUNDING_POSITION_EVENT_COVERAGE_INVALID")
                    if event["event_type"] != "FILL":
                        raise ValueError("ACCOUNT_HISTORY_EVENT_TYPE_UNSUPPORTED")
                    if event["fee_currency"] != "USDT":
                        raise ValueError("ACCOUNT_HISTORY_FEE_PROVENANCE_UNKNOWN")

                    position += event["_quantity"]
                    event_count += 1
                    event_digest = _chain_digest(event_digest, {
                        "eventId": event["event_id"],
                        "payloadHash": event["payload_hash"],
                    })

                if (event_index < len(strategy_events)
                        and strategy_events[event_index]["event_at_ms"] == settlement):
                    raise ValueError("FUNDING_POSITION_BOUNDARY_AMBIGUOUS")

                snapshot_identity = {
                    "projectionVersion": "paper-position-asof-v1",
                    "cutoverId": cutover_id,
                    "strategyId": strategy,
                    "settlementTimeMs": settlement,
                    "cutoverPayloadHash": snapshots[strategy]["payload_hash"],
                    "executionEventsDigest": event_digest,
                    "executionEventCount": event_count,
                    "executionCoverageDigest": coverage_digest,
                    "coverageWatermarkAtMs": coverage_watermark,
                }
                output.append({
                    "snapshotId": _digest(snapshot_identity),
                    "strategyId": strategy,
                    "symbol": "BTCUSDT",
                    "observedAtMs": settlement,
                    "positionBase": _replay_text(position),
                })
    output.sort(key=lambda row: (row["observedAtMs"], row["strategyId"]))
    return output


def load_paper_position_snapshots_from_db(db_path, *, settlement_times, now_ms):
    """Load cutover, execution journal and coverage from SQLite in read-only mode.

    The loader requires the append-only schema migrations and triggers used by
    the PaperLedger. It never migrates, writes, repairs or creates a database.
    """
    now = _stamp(now_ms, "FUNDING_POSITION_NOW_INVALID")
    if (not isinstance(settlement_times, list) or not settlement_times
            or len(settlement_times) > _MAX_ROWS
            or any(type(item) is not int or item < 0 for item in settlement_times)
            or any(left >= right for left, right in zip(settlement_times, settlement_times[1:]))
            or settlement_times[-1] >= now):
        raise ValueError("FUNDING_POSITION_SETTLEMENTS_INVALID")
    first_settlement = settlement_times[0]
    last_settlement = settlement_times[-1]
    required_end = last_settlement + 1

    try:
        path = Path(db_path).expanduser().resolve(strict=True)
    except (OSError, TypeError, ValueError):
        raise ValueError("FUNDING_POSITION_DATABASE_UNAVAILABLE") from None
    if not path.is_file():
        raise ValueError("FUNDING_POSITION_DATABASE_UNAVAILABLE")

    from paper_execution import account_history, funding

    expected_migrations = {
        funding.MIGRATION_VERSION: funding.MIGRATION_CHECKSUM,
        funding.CUTOVER_MIGRATION_VERSION: funding.CUTOVER_MIGRATION_CHECKSUM,
        funding.RECONCILIATION_MIGRATION_VERSION: funding.RECONCILIATION_MIGRATION_CHECKSUM,
        account_history.MIGRATION_VERSION: account_history.MIGRATION_CHECKSUM,
        account_history.CUTOVER_SNAPSHOT_MIGRATION_VERSION:
            account_history.CUTOVER_SNAPSHOT_MIGRATION_CHECKSUM,
        account_history.FEE_PROVENANCE_MIGRATION_VERSION:
            account_history.FEE_PROVENANCE_MIGRATION_CHECKSUM,
    }
    required_columns = {
        "paper_account_equity_cutovers": {
            "cutover_id", "account_id", "mark_observed_at_ms", "recorded_at_ms",
        },
        "paper_account_cutover_ledger_snapshots": {
            "cutover_id", "strategy_id", "snapshot_at_ms", "position_base",
            "average_entry_price", "realized_pnl_quote", "fees_quote",
            "funding_quote", "source_snapshot_id", "payload_hash", "canonical_payload",
        },
        "paper_account_event_journal": {
            "event_id", "account_id", "strategy_id", "event_type", "event_at_ms",
            "recorded_at_ms", "order_id", "intent_id", "source_event_id",
            "quantity_delta_base", "fill_price", "fee_quote", "fee_currency",
            "source", "source_snapshot_id", "payload_hash", "canonical_payload",
        },
        "paper_account_history_coverage": {
            "coverage_id", "account_id", "stream_type", "strategy_id",
            "start_at_ms", "end_at_ms", "status", "source",
            "source_snapshot_id", "payload_hash", "recorded_at_ms",
        },
    }
    required_triggers = {
        "paper_account_equity_cutovers_immutable_update",
        "paper_account_equity_cutovers_immutable_delete",
        "paper_account_cutover_ledger_snapshots_immutable_update",
        "paper_account_cutover_ledger_snapshots_immutable_delete",
        "paper_account_event_journal_immutable_update",
        "paper_account_event_journal_immutable_delete",
        "paper_account_history_coverage_immutable_update",
        "paper_account_history_coverage_immutable_delete",
        "paper_account_event_journal_fee_currency_required",
    }

    try:
        uri = path.as_uri() + "?mode=ro"
        with closing(sqlite3.connect(uri, uri=True, timeout=5)) as db:
            db.row_factory = sqlite3.Row
            db.execute("PRAGMA query_only=ON")
            db.execute("BEGIN")

            migrations = {
                row["version"]: (row["checksum"], row["status"])
                for row in db.execute(
                    "SELECT version,checksum,status FROM paper_schema_migrations"
                ).fetchall()
            }
            for version, checksum in expected_migrations.items():
                if migrations.get(version) != (checksum, "APPLIED"):
                    raise ValueError("FUNDING_POSITION_SCHEMA_NOT_SUPPORTED")

            tables = {
                row["name"] for row in db.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            }
            triggers = {
                row["name"] for row in db.execute(
                    "SELECT name FROM sqlite_master WHERE type='trigger'"
                ).fetchall()
            }
            if not set(required_columns).issubset(tables) or not required_triggers.issubset(triggers):
                raise ValueError("FUNDING_POSITION_SCHEMA_NOT_SUPPORTED")
            for table, columns in required_columns.items():
                actual = {
                    row["name"] for row in db.execute(f"PRAGMA table_info({table})").fetchall()
                }
                if not columns.issubset(actual):
                    raise ValueError("FUNDING_POSITION_SCHEMA_NOT_SUPPORTED")

            cutover = db.execute(
                """SELECT cutover_id,mark_observed_at_ms,recorded_at_ms
                   FROM paper_account_equity_cutovers
                   WHERE account_id=1 AND mark_observed_at_ms < ?
                   ORDER BY mark_observed_at_ms DESC,cutover_id DESC LIMIT 1""",
                (first_settlement,),
            ).fetchone()
            if cutover is None:
                raise ValueError("FUNDING_POSITION_CUTOVER_NOT_FOUND")
            if cutover["recorded_at_ms"] > now:
                raise ValueError("FUNDING_POSITION_CUTOVER_NOT_READY")
            cutover_id = cutover["cutover_id"]
            snapshot_at = cutover["mark_observed_at_ms"]

            snapshot_rows = db.execute(
                """SELECT cutover_id,strategy_id,snapshot_at_ms,position_base,
                          average_entry_price,realized_pnl_quote,fees_quote,funding_quote,
                          source_snapshot_id,payload_hash,canonical_payload
                   FROM paper_account_cutover_ledger_snapshots
                   WHERE cutover_id=? ORDER BY strategy_id""",
                (cutover_id,),
            ).fetchall()
            cutover_snapshots = [{
                "cutoverId": row["cutover_id"],
                "strategyId": row["strategy_id"],
                "snapshotAtMs": row["snapshot_at_ms"],
                "positionBase": row["position_base"],
                "averageEntryPrice": row["average_entry_price"],
                "realizedPnlQuote": row["realized_pnl_quote"],
                "feesQuote": row["fees_quote"],
                "fundingQuote": row["funding_quote"],
                "sourceSnapshotId": row["source_snapshot_id"],
                "payloadHash": row["payload_hash"],
                "canonicalPayload": row["canonical_payload"],
            } for row in snapshot_rows]

            event_rows = db.execute(
                """SELECT event_id,strategy_id,event_type,event_at_ms,recorded_at_ms,
                          quantity_delta_base,fill_price,fee_quote,fee_currency,source,
                          source_snapshot_id,payload_hash,order_id,intent_id,
                          source_event_id,canonical_payload
                   FROM paper_account_event_journal
                   WHERE account_id=1 AND event_at_ms <= ?
                   ORDER BY event_at_ms,event_id""",
                (last_settlement,),
            ).fetchall()
            execution_events = [{
                "eventId": row["event_id"],
                "strategyId": row["strategy_id"],
                "eventType": row["event_type"],
                "eventAtMs": row["event_at_ms"],
                "recordedAtMs": row["recorded_at_ms"],
                "quantityDeltaBase": row["quantity_delta_base"],
                "fillPrice": row["fill_price"],
                "feeQuote": row["fee_quote"],
                "feeCurrency": row["fee_currency"],
                "source": row["source"],
                "sourceSnapshotId": row["source_snapshot_id"],
                "payloadHash": row["payload_hash"],
                "orderId": row["order_id"],
                "intentId": row["intent_id"],
                "sourceEventId": row["source_event_id"],
                "canonicalPayload": row["canonical_payload"],
            } for row in event_rows]

            coverage_rows = db.execute(
                """SELECT coverage_id,strategy_id,start_at_ms,end_at_ms,status,
                          source,source_snapshot_id,payload_hash,recorded_at_ms
                   FROM paper_account_history_coverage
                   WHERE account_id=1 AND stream_type='EXECUTION'
                     AND end_at_ms > ? AND start_at_ms < ?
                   ORDER BY start_at_ms,end_at_ms,coverage_id""",
                (snapshot_at, required_end),
            ).fetchall()
            execution_coverage = [{
                "coverageId": row["coverage_id"],
                "strategyId": row["strategy_id"],
                "startAtMs": row["start_at_ms"],
                "endAtMs": row["end_at_ms"],
                "status": row["status"],
                "source": row["source"],
                "sourceSnapshotId": row["source_snapshot_id"],
                "payloadHash": row["payload_hash"],
                "recordedAtMs": row["recorded_at_ms"],
            } for row in coverage_rows]

            return build_paper_position_snapshots(
                cutover_snapshots=cutover_snapshots,
                execution_events=execution_events,
                execution_coverage=execution_coverage,
                settlement_times=settlement_times,
                now_ms=now,
            )
    except ValueError:
        raise
    except (sqlite3.Error, OSError, OverflowError):
        raise ValueError("FUNDING_POSITION_DATABASE_READ_FAILED") from None
