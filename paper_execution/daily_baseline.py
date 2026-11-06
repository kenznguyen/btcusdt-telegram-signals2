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
    elif (type(risk_day) is not int or risk_day < 0 or risk_day % DAY_MS
          or not isinstance(risk_equity, str) or not 1 <= len(risk_equity) <= 256):
        raise sqlite3.DatabaseError("DAILY_BASELINE_RISK_STATE_INVALID")
    else:
        try:
            previous_equity = Decimal(risk_equity)
        except (DecimalException, TypeError, ValueError):
            raise sqlite3.DatabaseError("DAILY_BASELINE_RISK_STATE_INVALID") from None
        if (not previous_equity.is_finite() or previous_equity <= 0
                or not -200 <= previous_equity.as_tuple().exponent <= 200
                or previous_equity.adjusted() > 200):
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


def _validate_persisted_baseline(connection, *, utc_day_ms, expected_equity,
                                 cutover_id, now_ms):
    baseline = connection.execute(
        """SELECT baseline_id,baseline_equity_quote,mark_id,starting_cutover_id,
                  replay_digest,algorithm_version,source_sha,recorded_at_ms
           FROM paper_daily_equity_baselines WHERE account_id=1 AND utc_day_ms=?""",
        (utc_day_ms,),
    ).fetchone()
    if baseline is None:
        raise sqlite3.DatabaseError("DAILY_BASELINE_PREVIOUS_BASELINE_UNVERIFIED")
    (baseline_id, equity, mark_id, baseline_cutover, digest, algorithm,
     source_sha, recorded_at_ms) = baseline
    expected_id = f"daily-equity-baseline:1:{utc_day_ms}"
    try:
        _source_sha(source_sha)
    except ValueError:
        raise sqlite3.DatabaseError("DAILY_BASELINE_PREVIOUS_BASELINE_UNVERIFIED") from None
    if (baseline_id != expected_id or equity != expected_equity or not mark_id
            or baseline_cutover != cutover_id or not isinstance(algorithm, str)
            or not algorithm or not isinstance(digest, str) or len(digest) != 71
            or not digest.startswith("sha256:")
            or any(char not in "0123456789abcdef" for char in digest[7:])
            or type(recorded_at_ms) is not int
            or not utc_day_ms <= recorded_at_ms <= now_ms):
        raise sqlite3.DatabaseError("DAILY_BASELINE_PREVIOUS_BASELINE_UNVERIFIED")
    audit = connection.execute(
        """SELECT audit_id,baseline_id,event_type,replay_digest,payload_json,recorded_at_ms
           FROM paper_daily_equity_baseline_audit
           WHERE account_id=1 AND utc_day_ms=?""",
        (utc_day_ms,),
    ).fetchone()
    if audit is None:
        raise sqlite3.DatabaseError("DAILY_BASELINE_PREVIOUS_BASELINE_UNVERIFIED")
    audit_id, audit_baseline, event_type, audit_digest, payload_json, audit_recorded = audit
    try:
        payload = json.loads(payload_json)
        canonical_payload = _canonical(payload)
    except (TypeError, ValueError, json.JSONDecodeError):
        raise sqlite3.DatabaseError("DAILY_BASELINE_PREVIOUS_BASELINE_UNVERIFIED") from None
    payload_digest = "sha256:" + hashlib.sha256(payload_json.encode("utf-8")).hexdigest()
    try:
        risk_audit = payload["riskState"]
        inputs_payload = payload["inputs"]
        replay_payload = payload["replay"]
        mark = inputs_payload["market_mark"]
        audit_hwm = Decimal(risk_audit["highWaterMarkQuote"])
        audit_equity = Decimal(equity)
    except (KeyError, TypeError, ValueError, DecimalException):
        raise sqlite3.DatabaseError("DAILY_BASELINE_PREVIOUS_BASELINE_UNVERIFIED") from None
    if (not isinstance(risk_audit, dict) or not isinstance(inputs_payload, dict)
            or not isinstance(replay_payload, dict) or not isinstance(mark, dict)
            or payload.get("auditSchemaVersion") != 2
            or type(risk_audit.get("version")) is not int
            or risk_audit["version"] < 2
            or type(risk_audit.get("riskReady")) is not bool
            or risk_audit.get("dailyBaselineUtcDayMs") != utc_day_ms
            or risk_audit.get("dailyBaselineEquityQuote") != equity
            or risk_audit.get("lastEquityQuote") != equity
            or risk_audit.get("lastMarkPrice") != mark.get("mark_price")
            or risk_audit.get("markObservedAtMs") != mark.get("observed_at_ms")
            or risk_audit.get("markCandleCloseMs") != mark.get("candle_close_ms")
            or risk_audit.get("datasetVersion") != mark.get("dataset_version")
            or risk_audit.get("updatedAtMs") != recorded_at_ms
            or not audit_hwm.is_finite() or audit_hwm <= 0
            or (risk_audit["riskReady"] and audit_hwm < audit_equity)
            or audit_id != f"daily-equity-baseline-audit:1:{utc_day_ms}"
            or audit_baseline != baseline_id or event_type != "DAILY_BASELINE_CREATED"
            or audit_digest != digest or audit_recorded != recorded_at_ms
            or canonical_payload != payload_json or payload_digest != digest
            or payload.get("utcDayMs") != utc_day_ms
            or inputs_payload.get("cutover_id") != cutover_id
            or mark.get("mark_id") != mark_id
            or replay_payload.get("equity_quote") != equity
            or payload.get("algorithmVersion") != algorithm):
        raise sqlite3.DatabaseError("DAILY_BASELINE_PREVIOUS_BASELINE_UNVERIFIED")
    return baseline


def _validate_risk_state_against_baseline(connection, *, utc_day_ms,
                                             expected_equity, cutover_id, now_ms):
    baseline = _validate_persisted_baseline(
        connection, utc_day_ms=utc_day_ms, expected_equity=expected_equity,
        cutover_id=cutover_id, now_ms=now_ms,
    )
    audit = connection.execute(
        """SELECT payload_json FROM paper_daily_equity_baseline_audit
           WHERE account_id=1 AND utc_day_ms=?""",
        (utc_day_ms,),
    ).fetchone()
    try:
        payload = json.loads(audit[0])
        risk_audit = payload["riskState"]
        baseline_equity = Decimal(baseline[1])
        baseline_hwm = Decimal(risk_audit["highWaterMarkQuote"])
        risk = connection.execute(
            """SELECT daily_baseline_utc_day_ms,daily_baseline_equity_quote,
                      last_equity_quote,last_mark_price,mark_observed_at_ms,
                      mark_candle_close_ms,dataset_version,updated_at_ms,
                      high_water_mark_quote,risk_ready,version
               FROM paper_account_risk_state WHERE account_id=1"""
        ).fetchone()
        (risk_day, daily_equity, last_equity, last_mark_price, observed_at,
         candle_close, dataset_version, updated_at, raw_hwm, risk_ready,
         risk_version) = risk
        hwm = Decimal(raw_hwm)
        last_equity_value = Decimal(last_equity)
        last_mark_value = Decimal(last_mark_price)
    except (KeyError, TypeError, ValueError, DecimalException, IndexError):
        raise sqlite3.DatabaseError(
            "DAILY_BASELINE_RISK_STATE_RECONCILIATION_FAILED"
        ) from None
    if (risk_day != utc_day_ms or daily_equity != expected_equity
            or not last_equity_value.is_finite() or last_equity_value <= 0
            or not last_mark_value.is_finite() or last_mark_value <= 0
            or updated_at is None or type(updated_at) is not int
            or updated_at < risk_audit["updatedAtMs"] or updated_at > now_ms
            or not hwm.is_finite() or hwm < baseline_hwm
            or type(risk_ready) is not int or risk_ready not in (0, 1)
            or type(risk_version) is not int
            or risk_version < risk_audit["version"]
            or (risk_ready == 1 and hwm < baseline_equity)):
        raise sqlite3.DatabaseError(
            "DAILY_BASELINE_RISK_STATE_RECONCILIATION_FAILED"
        )
    if risk_version == risk_audit["version"] and (
        updated_at != risk_audit["updatedAtMs"]
        or daily_equity != risk_audit["dailyBaselineEquityQuote"]
        or last_equity != risk_audit["lastEquityQuote"]
        or last_mark_price != risk_audit["lastMarkPrice"]
        or observed_at != risk_audit["markObservedAtMs"]
        or candle_close != risk_audit["markCandleCloseMs"]
        or dataset_version != risk_audit["datasetVersion"]
        or format(hwm, "f") != risk_audit["highWaterMarkQuote"]
        or bool(risk_ready) != risk_audit["riskReady"]
    ):
        raise sqlite3.DatabaseError(
            "DAILY_BASELINE_RISK_STATE_RECONCILIATION_FAILED"
        )
    return baseline


def _validate_rollover_predecessor(connection, *, boundary, now, risk_day,
                                   risk_equity, cutover_id, cutover_mark_at_ms,
                                   cutover_equity):
    expected_previous_day = boundary - DAY_MS
    if risk_day != expected_previous_day:
        raise ValueError("DAILY_BASELINE_DAY_GAP_REQUIRES_RECONCILIATION")
    cutover_day = cutover_mark_at_ms // DAY_MS * DAY_MS
    if risk_day < cutover_day:
        raise sqlite3.DatabaseError("DAILY_BASELINE_PREVIOUS_BASELINE_UNVERIFIED")
    prior = connection.execute(
        "SELECT 1 FROM paper_daily_equity_baselines WHERE account_id=1 AND utc_day_ms=?",
        (risk_day,),
    ).fetchone()
    if risk_day == cutover_day and prior is None:
        if risk_equity != cutover_equity:
            raise sqlite3.DatabaseError("DAILY_BASELINE_PREVIOUS_BASELINE_UNVERIFIED")
        return
    _validate_risk_state_against_baseline(
        connection, utc_day_ms=risk_day, expected_equity=risk_equity,
        cutover_id=cutover_id, now_ms=now,
    )

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
        risk_day, risk_equity, risk_ready, _, hwm = _risk_state(connection)
        existing_target = connection.execute(
            "SELECT 1 FROM paper_daily_equity_baselines WHERE account_id=1 AND utc_day_ms=?",
            (boundary,),
        ).fetchone()
        if existing_target is None:
            cutovers = connection.execute(
                """SELECT cutover_id,mark_observed_at_ms,account_equity_quote
                   FROM paper_account_equity_cutovers WHERE account_id=1"""
            ).fetchall()
            if len(cutovers) != 1:
                raise sqlite3.DatabaseError("DAILY_BASELINE_PREVIOUS_BASELINE_UNVERIFIED")
            cutover_id, cutover_mark_at_ms, cutover_equity = cutovers[0]
            if type(cutover_mark_at_ms) is not int or not isinstance(cutover_equity, str):
                raise sqlite3.DatabaseError("DAILY_BASELINE_PREVIOUS_BASELINE_UNVERIFIED")
            _validate_rollover_predecessor(
                connection, boundary=boundary, now=now, risk_day=risk_day,
                risk_equity=risk_equity, cutover_id=cutover_id,
                cutover_mark_at_ms=cutover_mark_at_ms, cutover_equity=cutover_equity,
            )
        inputs = load_daily_equity_replay_inputs(
            connection, utc_day_ms=boundary, now_ms=now, _transaction_owned=True
        )
        replay = reconcile_daily_equity_replay(inputs)
        equity = Decimal(replay["equity_quote"])
        if not equity.is_finite() or equity <= 0:
            raise ValueError("DAILY_BASELINE_EQUITY_INVALID")

        payload = {"algorithmVersion": ALGORITHM_VERSION,
                   "utcDayMs": boundary, "inputs": inputs, "replay": replay}
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
        risk_day, risk_equity, risk_ready, risk_version, hwm = _risk_state(connection)

        if existing:
            expected = (baseline_id, replay["equity_quote"],
                        inputs["market_mark"]["mark_id"], inputs["cutover_id"])
            if existing[:4] != expected or existing[5] != ALGORITHM_VERSION:
                raise ValueError("DAILY_BASELINE_REPLAY_CONFLICT")
            try:
                _source_sha(existing[6])
            except ValueError:
                raise sqlite3.DatabaseError("DAILY_BASELINE_ROW_INVALID") from None
            baseline_recorded = existing[7]
            if type(baseline_recorded) is not int or not boundary <= baseline_recorded <= now:
                raise sqlite3.DatabaseError("DAILY_BASELINE_ROW_INVALID")
            _validate_persisted_baseline(
                connection, utc_day_ms=boundary,
                expected_equity=replay["equity_quote"],
                cutover_id=inputs["cutover_id"], now_ms=now,
            )
            stored_payload = json.loads(audit[4]) if audit else {}
            if stored_payload.get("inputs") != inputs or stored_payload.get("replay") != replay:
                raise ValueError("DAILY_BASELINE_REPLAY_CONFLICT")
            if (risk_day is None or risk_day < boundary
                    or risk_day > now // DAY_MS * DAY_MS):
                raise sqlite3.DatabaseError("DAILY_BASELINE_RISK_STATE_RECONCILIATION_FAILED")
            if risk_day == boundary:
                _validate_risk_state_against_baseline(
                    connection, utc_day_ms=boundary,
                    expected_equity=replay["equity_quote"],
                    cutover_id=inputs["cutover_id"], now_ms=now,
                )
            if risk_day > boundary:
                cutover_row = connection.execute(
                    """SELECT cutover_id FROM paper_account_equity_cutovers
                       WHERE account_id=1"""
                ).fetchone()
                if cutover_row is None:
                    raise sqlite3.DatabaseError("DAILY_BASELINE_RISK_STATE_RECONCILIATION_FAILED")
                _validate_risk_state_against_baseline(
                    connection, utc_day_ms=risk_day, expected_equity=risk_equity,
                    cutover_id=cutover_row[0], now_ms=now,
                )
            connection.commit()
            return {"baseline_id": baseline_id, "utc_day_ms": boundary,
                    "baseline_equity_quote": replay["equity_quote"],
                    "replay_digest": existing[4], "idempotent": True,
                    "risk_ready": bool(risk_ready)}

        if audit is not None:
            raise sqlite3.DatabaseError("DAILY_BASELINE_AUDIT_ORPHANED")
        if risk_day is not None and (type(risk_day) is not int or risk_day >= boundary):
            raise ValueError("DAILY_BASELINE_RISK_STATE_CONFLICT")

        mark = inputs["market_mark"]
        next_hwm = max(hwm, equity) if risk_ready else hwm
        risk_state_audit = {
            "dailyBaselineUtcDayMs": boundary,
            "dailyBaselineEquityQuote": replay["equity_quote"],
            "lastEquityQuote": replay["equity_quote"],
            "lastMarkPrice": mark["mark_price"],
            "markObservedAtMs": mark["observed_at_ms"],
            "markCandleCloseMs": mark["candle_close_ms"],
            "datasetVersion": mark["dataset_version"],
            "highWaterMarkQuote": format(next_hwm, "f"),
            "riskReady": bool(risk_ready),
            "updatedAtMs": now,
            "version": risk_version + 1,
        }
        payload.update(auditSchemaVersion=2, riskState=risk_state_audit)
        payload_json = _canonical(payload)
        replay_digest = "sha256:" + hashlib.sha256(payload_json.encode("utf-8")).hexdigest()

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
