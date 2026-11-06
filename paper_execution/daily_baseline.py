"""Atomic immutable daily equity baseline persistence (PAPER-only)."""
import hashlib
import json
import sqlite3
from decimal import Decimal

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
                      replay_digest,algorithm_version
               FROM paper_daily_equity_baselines WHERE account_id=1 AND utc_day_ms=?""",
            (boundary,),
        ).fetchone()
        audit = connection.execute(
            """SELECT audit_id,baseline_id,event_type,replay_digest,payload_json
               FROM paper_daily_equity_baseline_audit
               WHERE account_id=1 AND utc_day_ms=?""",
            (boundary,),
        ).fetchone()
        risk = connection.execute(
            """SELECT daily_baseline_utc_day_ms,daily_baseline_equity_quote,
                      risk_ready,version
               FROM paper_account_risk_state WHERE account_id=1"""
        ).fetchall()
        if len(risk) != 1 or type(risk[0][2]) is not int or risk[0][2] not in (0, 1):
            raise sqlite3.DatabaseError("DAILY_BASELINE_RISK_STATE_INVALID")
        risk_day, risk_equity, risk_ready, _ = risk[0]

        if existing:
            expected = (baseline_id, replay["equity_quote"],
                        inputs["market_mark"]["mark_id"], inputs["cutover_id"],
                        replay_digest, ALGORITHM_VERSION)
            if existing != expected:
                raise ValueError("DAILY_BASELINE_REPLAY_CONFLICT")
            if audit != (audit_id, baseline_id, "DAILY_BASELINE_CREATED",
                         replay_digest, payload_json):
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
        updated = connection.execute(
            """UPDATE paper_account_risk_state
               SET daily_baseline_utc_day_ms=?,daily_baseline_equity_quote=?,
                   updated_at_ms=?,version=version+1
               WHERE account_id=1""",
            (boundary, replay["equity_quote"], now),
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
