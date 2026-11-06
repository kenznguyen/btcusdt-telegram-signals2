"""Atomic immutable daily equity baseline persistence (PAPER-only)."""
import hashlib
import json
import sqlite3
from decimal import Decimal, DecimalException

from paper_execution.account_history import (
    DAY_MS, DAILY_BASELINE_AUDIT_MIGRATION_VERSION,
    DAILY_BASELINE_AUDIT_MIGRATION_CHECKSUM, _stamp,
)
from paper_execution.replay_inputs import load_daily_equity_replay_inputs
from paper_execution.replay_reconciliation import reconcile_daily_equity_replay

ALGORITHM_VERSION = "daily-equity-replay-v1"


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False)


def _source_sha(value):
    if (not isinstance(value, str) or len(value) != 40
            or any(char not in "0123456789abcdef" for char in value.lower())):
        raise ValueError("DUAL_LEDGER_SOURCE_SHA_REQUIRED")
    return value.lower()



def _require_immutable_schema(connection):
    required_tables = {
        "paper_daily_equity_baselines", "paper_daily_equity_baseline_audit",
    }
    tables = {row[0] for row in connection.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    )}
    triggers = {row[0] for row in connection.execute(
        "SELECT name FROM sqlite_master WHERE type='trigger'"
    )}
    required_triggers = {
        "paper_daily_equity_baselines_immutable_update",
        "paper_daily_equity_baselines_immutable_delete",
        "paper_daily_equity_baseline_audit_immutable_update",
        "paper_daily_equity_baseline_audit_immutable_delete",
    }
    if not required_tables.issubset(tables) or not required_triggers.issubset(triggers):
        raise sqlite3.DatabaseError("DAILY_BASELINE_IMMUTABLE_SCHEMA_INCOMPLETE")

    required_columns = {
        "paper_daily_equity_baselines": {
            "baseline_id", "account_id", "utc_day_ms", "baseline_equity_quote",
            "mark_id", "starting_cutover_id", "replay_digest", "algorithm_version",
            "source_sha", "recorded_at_ms",
        },
        "paper_daily_equity_baseline_audit": {
            "audit_id", "account_id", "utc_day_ms", "baseline_id", "event_type",
            "replay_digest", "payload_json", "recorded_at_ms",
        },
    }
    for table, required in required_columns.items():
        columns = {row[1] for row in connection.execute(f"PRAGMA table_info({table})")}
        if not required.issubset(columns):
            raise sqlite3.DatabaseError("DAILY_BASELINE_IMMUTABLE_SCHEMA_INCOMPLETE")

    unique_constraints = {
        "paper_daily_equity_baselines": ("account_id", "utc_day_ms"),
        "paper_daily_equity_baseline_audit": ("account_id", "utc_day_ms", "event_type"),
    }
    for table, expected_columns in unique_constraints.items():
        found = False
        for index in connection.execute(f"PRAGMA index_list({table})"):
            if index[2] != 1:
                continue
            index_name = index[1].replace("'", "''")
            columns = tuple(row[2] for row in connection.execute(
                f"PRAGMA index_info('{index_name}')"
            ))
            if columns == expected_columns:
                found = True
                break
        if not found:
            raise sqlite3.DatabaseError("DAILY_BASELINE_IMMUTABLE_SCHEMA_INCOMPLETE")


def _risk_state(connection):
    rows = connection.execute(
        """SELECT daily_baseline_utc_day_ms,daily_baseline_equity_quote,
                  risk_ready,version,high_water_mark_quote
           FROM paper_account_risk_state WHERE account_id=1"""
    ).fetchall()
    if (len(rows) != 1 or type(rows[0][2]) is not int
            or rows[0][2] not in (0, 1) or type(rows[0][3]) is not int
            or rows[0][3] < 1):
        raise sqlite3.DatabaseError("DAILY_BASELINE_RISK_STATE_INVALID")
    risk_day, risk_equity, risk_ready, version, raw_hwm = rows[0]
    if risk_day is None:
        if risk_equity is not None:
            raise sqlite3.DatabaseError("DAILY_BASELINE_RISK_STATE_INVALID")
    elif type(risk_day) is not int or not isinstance(risk_equity, str):
        raise sqlite3.DatabaseError("DAILY_BASELINE_RISK_STATE_INVALID")
    else:
        try:
            previous_equity = Decimal(risk_equity)
        except (DecimalException, TypeError, ValueError):
            raise sqlite3.DatabaseError("DAILY_BASELINE_RISK_STATE_INVALID") from None
        if not previous_equity.is_finite() or previous_equity <= 0:
            raise sqlite3.DatabaseError("DAILY_BASELINE_RISK_STATE_INVALID")
    if not isinstance(raw_hwm, str) or not 1 <= len(raw_hwm) <= 256:
        raise sqlite3.DatabaseError("DAILY_BASELINE_RISK_STATE_INVALID")
    try:
        hwm = Decimal(raw_hwm)
    except (DecimalException, TypeError, ValueError):
        raise sqlite3.DatabaseError("DAILY_BASELINE_RISK_STATE_INVALID") from None
    if (not hwm.is_finite() or hwm <= 0
            or not -200 <= hwm.as_tuple().exponent <= 200
            or hwm.adjusted() > 200):
        raise sqlite3.DatabaseError("DAILY_BASELINE_RISK_STATE_INVALID")
    return risk_day, risk_equity, risk_ready, version, hwm

def persist_daily_equity_baseline(connection, *, utc_day_ms, now_ms, source_sha):
    """Revalidate, replay, and persist one UTC baseline plus audit atomically."""
    if not isinstance(connection, sqlite3.Connection):
        raise ValueError("DAILY_BASELINE_SQLITE_CONNECTION_REQUIRED")
    boundary = _stamp(utc_day_ms, "ACCOUNT_HISTORY_UTC_DAY_INVALID")
    now = _stamp(now_ms, "ACCOUNT_HISTORY_NOW_INVALID")
    source = _source_sha(source_sha)
    if boundary % DAY_MS or now < boundary:
        raise ValueError("ACCOUNT_HISTORY_UTC_DAY_INVALID")
    if connection.in_transaction:
        raise ValueError("DAILY_BASELINE_CLEAN_TRANSACTION_REQUIRED")
    if connection.execute("PRAGMA query_only").fetchone()[0] != 0:
        raise ValueError("DAILY_BASELINE_WRITABLE_CONNECTION_REQUIRED")
    if connection.execute("PRAGMA foreign_keys").fetchone()[0] != 1:
        raise ValueError("DAILY_BASELINE_FOREIGN_KEYS_REQUIRED")

    connection.execute("BEGIN IMMEDIATE")
    try:
        migration = connection.execute(
            "SELECT checksum,status FROM paper_schema_migrations WHERE version=?",
            (DAILY_BASELINE_AUDIT_MIGRATION_VERSION,),
        ).fetchone()
        if migration != (DAILY_BASELINE_AUDIT_MIGRATION_CHECKSUM, "APPLIED"):
            raise sqlite3.DatabaseError("DAILY_BASELINE_AUDIT_MIGRATION_NOT_APPLIED")
        _require_immutable_schema(connection)
        inputs = load_daily_equity_replay_inputs(
            connection, utc_day_ms=boundary, now_ms=now, _transaction_owned=True
        )
        replay = reconcile_daily_equity_replay(inputs)
        equity = Decimal(replay["equity_quote"])
        if not equity.is_finite() or equity <= 0:
            raise ValueError("DAILY_BASELINE_EQUITY_INVALID")

        payload = {"algorithmVersion": ALGORITHM_VERSION,
                   "utcDayMs": boundary, "inputs": inputs, "replay": replay}
        payload_json = _canonical(payload)
        replay_digest = "sha256:" + hashlib.sha256(payload_json.encode("utf-8")).hexdigest()
        baseline_id = f"daily-equity-baseline:1:{boundary}"
        audit_id = f"daily-equity-baseline-audit:1:{boundary}"

        existing = connection.execute(
            """SELECT baseline_id,baseline_equity_quote,mark_id,starting_cutover_id,
                      replay_digest,algorithm_version,source_sha,recorded_at_ms
               FROM paper_daily_equity_baselines WHERE account_id=1 AND utc_day_ms=?""",
            (boundary,),
        ).fetchone()
        audit = connection.execute(
            """SELECT audit_id,baseline_id,event_type,replay_digest,payload_json,recorded_at_ms
               FROM paper_daily_equity_baseline_audit
               WHERE account_id=1 AND utc_day_ms=?""",
            (boundary,),
        ).fetchone()
        risk_day, risk_equity, risk_ready, _, hwm = _risk_state(connection)

        if existing:
            expected = (baseline_id, replay["equity_quote"],
                        inputs["market_mark"]["mark_id"], inputs["cutover_id"],
                        replay_digest, ALGORITHM_VERSION)
            if existing[:6] != expected:
                raise ValueError("DAILY_BASELINE_REPLAY_CONFLICT")
            try:
                _source_sha(existing[6])
            except ValueError:
                raise sqlite3.DatabaseError("DAILY_BASELINE_ROW_INVALID") from None
            baseline_recorded = existing[7]
            if type(baseline_recorded) is not int or not boundary <= baseline_recorded <= now:
                raise sqlite3.DatabaseError("DAILY_BASELINE_ROW_INVALID")
            if audit != (audit_id, baseline_id, "DAILY_BASELINE_CREATED",
                         replay_digest, payload_json, baseline_recorded):
                raise sqlite3.DatabaseError("DAILY_BASELINE_AUDIT_RECONCILIATION_FAILED")
            if risk_day != boundary or risk_equity != replay["equity_quote"]:
                raise sqlite3.DatabaseError("DAILY_BASELINE_RISK_STATE_RECONCILIATION_FAILED")
            connection.commit()
            return {"baseline_id": baseline_id, "utc_day_ms": boundary,
                    "baseline_equity_quote": replay["equity_quote"],
                    "replay_digest": replay_digest, "idempotent": True,
                    "risk_ready": bool(risk_ready)}

        if audit is not None:
            raise sqlite3.DatabaseError("DAILY_BASELINE_AUDIT_ORPHANED")
        if risk_day is not None and (type(risk_day) is not int or risk_day >= boundary):
            raise ValueError("DAILY_BASELINE_RISK_STATE_CONFLICT")

        connection.execute(
            """INSERT INTO paper_daily_equity_baselines
               (baseline_id,account_id,utc_day_ms,baseline_equity_quote,mark_id,
                starting_cutover_id,replay_digest,algorithm_version,source_sha,recorded_at_ms)
               VALUES (?,1,?,?,?,?,?,?,?,?)""",
            (baseline_id, boundary, replay["equity_quote"],
             inputs["market_mark"]["mark_id"], inputs["cutover_id"],
             replay_digest, ALGORITHM_VERSION, source, now),
        )
        connection.execute(
            """INSERT INTO paper_daily_equity_baseline_audit
               (audit_id,account_id,utc_day_ms,baseline_id,event_type,replay_digest,
                payload_json,recorded_at_ms)
               VALUES (?,1,?,?, 'DAILY_BASELINE_CREATED',?,?,?)""",
            (audit_id, boundary, baseline_id, replay_digest, payload_json, now),
        )
        mark = inputs["market_mark"]
        next_hwm = max(hwm, equity) if risk_ready else hwm
        updated = connection.execute(
            """UPDATE paper_account_risk_state
               SET daily_baseline_utc_day_ms=?,daily_baseline_equity_quote=?,
                   last_equity_quote=?,last_mark_price=?,mark_observed_at_ms=?,
                   mark_candle_close_ms=?,dataset_version=?,high_water_mark_quote=?,
                   updated_at_ms=?,version=version+1
               WHERE account_id=1""",
            (boundary, replay["equity_quote"], replay["equity_quote"],
             mark["mark_price"], mark["observed_at_ms"], mark["candle_close_ms"],
             mark["dataset_version"], format(next_hwm, "f"), now),
        )
        if updated.rowcount != 1:
            raise sqlite3.DatabaseError("DAILY_BASELINE_RISK_STATE_UPDATE_FAILED")
        connection.commit()
        return {"baseline_id": baseline_id, "utc_day_ms": boundary,
                "baseline_equity_quote": replay["equity_quote"],
                "replay_digest": replay_digest, "idempotent": False,
                "risk_ready": bool(risk_ready)}
    except BaseException:
        if connection.in_transaction:
            connection.rollback()
        raise
