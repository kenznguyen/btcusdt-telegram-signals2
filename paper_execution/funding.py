"""Append-only PAPER funding provenance and coverage ledger."""

from contextlib import closing
from decimal import Decimal, DecimalException, localcontext
import hashlib
import json
from pathlib import Path
import sqlite3


MIGRATION_VERSION = 4
MIGRATION_CHECKSUM = hashlib.sha256(
    b"dual-ledger-v4:immutable-funding-provenance-and-coverage"
).hexdigest()
CUTOVER_MIGRATION_VERSION = 5
CUTOVER_MIGRATION_CHECKSUM = hashlib.sha256(
    b"dual-ledger-v5:verified-account-equity-cutover"
).hexdigest()
STRATEGIES = {"STRATEGY_CORE", "AI_FREQAI", "LEGACY_UNATTRIBUTED"}


def _stamp(value):
    if type(value) is not int or value < 0:
        raise ValueError("FUNDING_TIMESTAMP_INVALID")
    return value


def _decimal_value(value, code, *, nonnegative=False, positive=False):
    try:
        result = Decimal(str(value))
    except (DecimalException, TypeError, ValueError):
        raise ValueError(code) from None
    if (not result.is_finite() or (nonnegative and result < 0)
            or (positive and result <= 0)):
        raise ValueError(code)
    return result


def _amount(value):
    return _decimal_value(value, "FUNDING_AMOUNT_INVALID")


def _decimal_text(value):
    return format(value.normalize(), "f") if value else "0"


def _hash(value):
    if (not isinstance(value, str) or len(value) != 71
            or not value.startswith("sha256:")
            or any(c not in "0123456789abcdef" for c in value[7:])):
        raise ValueError("FUNDING_PAYLOAD_HASH_INVALID")
    return value


def _required_text(value, code, limit=300):
    if (not isinstance(value, str) or not value.strip()
            or len(value) > limit or not value.isprintable()):
        raise ValueError(code)
    return value


def migrate_funding_provenance(connection, source_sha):
    """Apply additive v4 schema; v1-v3 checksums are preserved."""
    if (not isinstance(source_sha, str) or len(source_sha) != 40
            or any(c not in "0123456789abcdef" for c in source_sha.lower())):
        raise ValueError("DUAL_LEDGER_SOURCE_SHA_REQUIRED")
    applied = connection.execute(
        "SELECT checksum,status FROM paper_schema_migrations WHERE version=?",
        (MIGRATION_VERSION,),
    ).fetchone()
    if applied:
        if applied[0] != MIGRATION_CHECKSUM or applied[1] != "APPLIED":
            raise sqlite3.DatabaseError("FUNDING_PROVENANCE_MIGRATION_CHECKSUM_MISMATCH")
        columns = {r[1] for r in connection.execute(
            "PRAGMA table_info(paper_funding_events)"
        )}
        objects = set(connection.execute(
            "SELECT type,name FROM sqlite_master"
        ).fetchall())
        expected = {
            ("table", "paper_funding_coverage"),
            ("trigger", "paper_funding_events_immutable_update"),
            ("trigger", "paper_funding_events_immutable_delete"),
            ("trigger", "paper_funding_coverage_immutable_update"),
            ("trigger", "paper_funding_coverage_immutable_delete"),
        }
        if not {"source", "recorded_at_ms"}.issubset(columns) or not expected.issubset(objects):
            raise sqlite3.DatabaseError("FUNDING_PROVENANCE_SCHEMA_INCOMPLETE")
        return
    columns = {r[1] for r in connection.execute(
        "PRAGMA table_info(paper_funding_events)"
    )}
    if "source" in columns or "recorded_at_ms" in columns:
        raise sqlite3.DatabaseError("FUNDING_PROVENANCE_SCHEMA_WITHOUT_MIGRATION_RECORD")
    connection.execute(
        "ALTER TABLE paper_funding_events ADD COLUMN source TEXT NOT NULL DEFAULT 'LEGACY_UNVERIFIED'"
    )
    connection.execute(
        "ALTER TABLE paper_funding_events ADD COLUMN recorded_at_ms INTEGER NOT NULL DEFAULT 0"
    )
    connection.execute("""CREATE TABLE paper_funding_coverage (
        coverage_id TEXT PRIMARY KEY,
        account_id INTEGER NOT NULL REFERENCES paper_accounts(account_id),
        start_at_ms INTEGER NOT NULL,
        end_at_ms INTEGER NOT NULL,
        status TEXT NOT NULL CHECK(status IN ('VERIFIED','UNKNOWN','DISABLED')),
        source TEXT NOT NULL CHECK(length(trim(source))>0),
        source_snapshot_id TEXT NOT NULL CHECK(length(trim(source_snapshot_id))>0),
        payload_hash TEXT NOT NULL UNIQUE CHECK(
            length(payload_hash)=71 AND substr(payload_hash,1,7)='sha256:'
            AND substr(payload_hash,8) NOT GLOB '*[^0-9a-f]*'
        ),
        config_version TEXT NOT NULL CHECK(length(trim(config_version))>0),
        recorded_at_ms INTEGER NOT NULL,
        CHECK(start_at_ms < end_at_ms)
    )""")
    for table, label in (
        ("paper_funding_events", "FUNDING_EVENT_IMMUTABLE"),
        ("paper_funding_coverage", "FUNDING_COVERAGE_IMMUTABLE"),
    ):
        connection.execute(
            f"""CREATE TRIGGER {table}_immutable_update BEFORE UPDATE ON {table}
                BEGIN SELECT RAISE(ABORT,'{label}'); END"""
        )
        connection.execute(
            f"""CREATE TRIGGER {table}_immutable_delete BEFORE DELETE ON {table}
                BEGIN SELECT RAISE(ABORT,'{label}'); END"""
        )
    if connection.execute("SELECT 1 FROM paper_funding_events LIMIT 1").fetchone():
        connection.execute(
            """UPDATE paper_account_risk_state
               SET risk_ready=0,unavailable_reason='FUNDING_PROVENANCE_REQUIRES_RECONCILIATION',
                   version=version+1 WHERE account_id=1"""
        )
    applied_at = connection.execute(
        "SELECT updated_at_ms FROM paper_account_risk_state WHERE account_id=1"
    ).fetchone()[0]
    connection.execute(
        """INSERT INTO paper_schema_migrations
           (version,name,checksum,applied_at_ms,source_sha,status)
           VALUES (4,'funding_provenance_v4',?,?,?,'APPLIED')""",
        (MIGRATION_CHECKSUM, applied_at, source_sha.lower()),
    )


def _refresh_equity(connection, now):
    risk = connection.execute(
        """SELECT high_water_mark_quote,last_mark_price,mark_observed_at_ms,
                  mark_candle_close_ms,dataset_version,risk_ready
           FROM paper_account_risk_state WHERE account_id=1"""
    ).fetchone()
    if not risk:
        return
    try:
        mark = Decimal(risk[1])
        observed, candle = _stamp(risk[2]), _stamp(risk[3])
        if (not mark.is_finite() or mark <= 0 or observed > now
                or now - observed > 30 * 60_000 or candle > observed
                or observed - candle > 30 * 60_000
                or not isinstance(risk[4], str) or not risk[4].strip()):
            raise ValueError
        capital = Decimal(connection.execute(
            "SELECT initial_capital FROM paper_accounts WHERE account_id=1"
        ).fetchone()[0])
        ledgers = connection.execute(
            """SELECT position_base,average_entry_price,realized_pnl_quote,
                      fees_quote,funding_quote FROM paper_strategy_ledgers WHERE account_id=1"""
        ).fetchall()
        realized = fees = funding = unrealized = Decimal(0)
        for q, avg, pnl, fee, fund in ledgers:
            q, avg, pnl, fee, fund = map(Decimal, (q, avg, pnl, fee, fund))
            if any(not x.is_finite() for x in (q, avg, pnl, fee, fund)):
                raise ValueError
            realized += pnl
            fees += fee
            funding += fund
            if q:
                unrealized += q * (mark - avg)
        adjustments = connection.execute(
            "SELECT adjustment_type,amount_quote FROM paper_account_adjustments WHERE account_id=1"
        ).fetchall()
        legacy_pnl = legacy_fees = Decimal(0)
        for kind, raw in adjustments:
            amount = Decimal(raw)
            if not amount.is_finite():
                raise ValueError
            if kind == "LEGACY_REALIZED_PNL":
                legacy_pnl += amount
            elif kind == "LEGACY_FEES":
                legacy_fees += amount
            else:
                raise ValueError
        equity = capital + realized + legacy_pnl + unrealized - fees - legacy_fees - funding
        hwm = Decimal(risk[0])
        if not equity.is_finite() or equity <= 0 or not hwm.is_finite() or hwm <= 0:
            raise ValueError
        connection.execute(
            """UPDATE paper_account_risk_state
               SET last_equity_quote=?,high_water_mark_quote=?,updated_at_ms=?,
                   version=version+1 WHERE account_id=1""",
            (_decimal_text(equity), format(max(hwm, equity), "f"), now),
        )
    except (DecimalException, TypeError, ValueError, IndexError):
        connection.execute(
            """UPDATE paper_account_risk_state
               SET risk_ready=0,unavailable_reason='FUNDING_EQUITY_RECONCILIATION_FAILED',
                   updated_at_ms=?,version=version+1 WHERE account_id=1""",
            (now,),
        )



def migrate_account_equity_cutover(connection, source_sha):
    if (not isinstance(source_sha, str) or len(source_sha) != 40
            or any(c not in "0123456789abcdef" for c in source_sha.lower())):
        raise ValueError("DUAL_LEDGER_SOURCE_SHA_REQUIRED")
    migration = connection.execute(
        "SELECT checksum,status FROM paper_schema_migrations WHERE version=4"
    ).fetchone()
    if migration != (MIGRATION_CHECKSUM, "APPLIED"):
        raise sqlite3.DatabaseError("ACCOUNT_EQUITY_CUTOVER_PREREQUISITE_MISSING")
    applied = connection.execute(
        "SELECT checksum,status FROM paper_schema_migrations WHERE version=5"
    ).fetchone()
    if applied:
        if applied != (CUTOVER_MIGRATION_CHECKSUM, "APPLIED"):
            raise sqlite3.DatabaseError("ACCOUNT_EQUITY_CUTOVER_MIGRATION_CHECKSUM_MISMATCH")
        columns = {row[1] for row in connection.execute(
            "PRAGMA table_info(paper_account_equity_cutovers)"
        )}
        triggers = {
            row[0] for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='trigger'"
            )
        }
        required_columns = {
            "reconciled_realized_pnl_quote", "reconciled_fees_quote",
            "reconciled_funding_quote", "expected_account_equity_quote",
        }
        if (not required_columns.issubset(columns)
                or not {
                    "paper_account_equity_cutovers_immutable_update",
                    "paper_account_equity_cutovers_immutable_delete",
                }.issubset(triggers)):
            raise sqlite3.DatabaseError("ACCOUNT_EQUITY_CUTOVER_SCHEMA_INCOMPLETE")
        return
    connection.execute("""CREATE TABLE paper_account_equity_cutovers (
        cutover_id TEXT PRIMARY KEY,
        account_id INTEGER NOT NULL REFERENCES paper_accounts(account_id),
        initial_capital_quote TEXT NOT NULL,
        account_equity_quote TEXT NOT NULL,
        mark_price TEXT NOT NULL,
        mark_candle_close_ms INTEGER NOT NULL,
        mark_observed_at_ms INTEGER NOT NULL,
        dataset_version TEXT NOT NULL,
        funding_coverage_start_at_ms INTEGER NOT NULL,
        funding_coverage_end_at_ms INTEGER NOT NULL,
        source TEXT NOT NULL,
        source_snapshot_id TEXT NOT NULL,
        payload_hash TEXT NOT NULL UNIQUE,
        config_version TEXT NOT NULL,
        high_water_mark_quote TEXT NOT NULL,
        daily_baseline_utc_day_ms INTEGER NOT NULL,
        daily_baseline_equity_quote TEXT NOT NULL,
        reconciled_realized_pnl_quote TEXT NOT NULL,
        reconciled_fees_quote TEXT NOT NULL,
        reconciled_funding_quote TEXT NOT NULL,
        expected_account_equity_quote TEXT NOT NULL,
        recorded_at_ms INTEGER NOT NULL
    )""")
    connection.execute("""CREATE TRIGGER paper_account_equity_cutovers_immutable_update
        BEFORE UPDATE ON paper_account_equity_cutovers
        BEGIN SELECT RAISE(ABORT,'ACCOUNT_EQUITY_CUTOVER_IMMUTABLE'); END""")
    connection.execute("""CREATE TRIGGER paper_account_equity_cutovers_immutable_delete
        BEFORE DELETE ON paper_account_equity_cutovers
        BEGIN SELECT RAISE(ABORT,'ACCOUNT_EQUITY_CUTOVER_IMMUTABLE'); END""")
    applied_at = connection.execute(
        "SELECT updated_at_ms FROM paper_account_risk_state WHERE account_id=1"
    ).fetchone()[0]
    connection.execute(
        """INSERT INTO paper_schema_migrations
           (version,name,checksum,applied_at_ms,source_sha,status)
           VALUES (5,'account_equity_cutover_v5',?,?,?,'APPLIED')""",
        (CUTOVER_MIGRATION_CHECKSUM, applied_at, source_sha.lower()),
    )


def record_account_equity_cutover(
    db_path, *, cutover_id, expected_initial_capital_quote,
    expected_realized_pnl_quote, expected_fees_quote, expected_funding_quote,
    expected_account_equity_quote, mark_price, mark_candle_close_ms,
    mark_observed_at_ms, dataset_version,
    funding_coverage_start_at_ms, source, source_snapshot_id, payload_hash,
    config_version, recorded_at_ms,
):
    path = Path(db_path).resolve()
    if not path.is_file():
        raise FileNotFoundError("Paper ledger is unavailable")
    cutover_id = _required_text(cutover_id, "ACCOUNT_EQUITY_CUTOVER_ID_INVALID", 200)
    expected_capital = _decimal_value(
        expected_initial_capital_quote, "ACCOUNT_EQUITY_CAPITAL_INVALID", positive=True
    )
    expected_realized = _decimal_value(
        expected_realized_pnl_quote, "ACCOUNT_EQUITY_REALIZED_INVALID"
    )
    expected_fees = _decimal_value(
        expected_fees_quote, "ACCOUNT_EQUITY_FEES_INVALID", nonnegative=True
    )
    expected_funding = _decimal_value(
        expected_funding_quote, "ACCOUNT_EQUITY_FUNDING_INVALID"
    )
    expected_equity = _decimal_value(
        expected_account_equity_quote, "ACCOUNT_EQUITY_EXPECTED_INVALID", positive=True
    )
    mark = _decimal_value(mark_price, "ACCOUNT_EQUITY_MARK_INVALID", positive=True)
    candle, observed = _stamp(mark_candle_close_ms), _stamp(mark_observed_at_ms)
    coverage_start, recorded = _stamp(funding_coverage_start_at_ms), _stamp(recorded_at_ms)
    if mark <= 0 or candle > observed or observed > recorded or recorded - observed > 30 * 60_000:
        raise ValueError("ACCOUNT_EQUITY_CUTOVER_MARK_INVALID")
    if observed - candle > 30 * 60_000:
        raise ValueError("ACCOUNT_EQUITY_CUTOVER_CANDLE_STALE")
    dataset = _required_text(dataset_version, "ACCOUNT_EQUITY_CUTOVER_DATASET_REQUIRED", 300)
    source = _required_text(source, "ACCOUNT_EQUITY_CUTOVER_SOURCE_REQUIRED")
    snapshot = _required_text(source_snapshot_id, "ACCOUNT_EQUITY_CUTOVER_SNAPSHOT_REQUIRED")
    digest = _hash(payload_hash)
    config = _required_text(config_version, "ACCOUNT_EQUITY_CUTOVER_CONFIG_REQUIRED", 200)
    if coverage_start >= observed:
        raise ValueError("FUNDING_PROVENANCE_INCOMPLETE")

    with closing(sqlite3.connect(path, timeout=10)) as db, db, localcontext() as ctx:
        ctx.prec = 80
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("BEGIN IMMEDIATE")
        migration = db.execute(
            "SELECT checksum,status FROM paper_schema_migrations WHERE version=5"
        ).fetchone()
        if migration is None or tuple(migration) != (CUTOVER_MIGRATION_CHECKSUM, "APPLIED"):
            raise sqlite3.DatabaseError("ACCOUNT_EQUITY_CUTOVER_MIGRATION_NOT_APPLIED")
        prior = db.execute(
            "SELECT * FROM paper_account_equity_cutovers WHERE cutover_id=?",
            (cutover_id,),
        ).fetchone()
        request_identity = (
            format(expected_capital, "f"), format(expected_realized, "f"),
            format(expected_fees, "f"), format(expected_funding, "f"),
            format(expected_equity, "f"), format(mark, "f"), candle, observed,
            dataset, coverage_start, source, snapshot, digest, config,
        )
        if prior:
            stored_identity = (
                prior["initial_capital_quote"], prior["reconciled_realized_pnl_quote"],
                prior["reconciled_fees_quote"], prior["reconciled_funding_quote"],
                prior["expected_account_equity_quote"], prior["mark_price"],
                prior["mark_candle_close_ms"], prior["mark_observed_at_ms"],
                prior["dataset_version"], prior["funding_coverage_start_at_ms"],
                prior["source"], prior["source_snapshot_id"], prior["payload_hash"],
                prior["config_version"],
            )
            if stored_identity != request_identity:
                raise ValueError("ACCOUNT_EQUITY_CUTOVER_ID_CONFLICT")
            return {
                "cutoverId": cutover_id, "accountEquityQuote": prior["account_equity_quote"],
                "highWaterMarkQuote": prior["high_water_mark_quote"],
                "dailyBaselineEquityQuote": prior["daily_baseline_equity_quote"],
                "dailyBaselineUtcDayMs": prior["daily_baseline_utc_day_ms"],
                "riskReady": bool(db.execute(
                    "SELECT risk_ready FROM paper_account_risk_state WHERE account_id=1"
                ).fetchone()[0]), "mode": "PAPER",
            }
        if db.execute("SELECT 1 FROM paper_account_equity_cutovers LIMIT 1").fetchone():
            raise ValueError("ACCOUNT_EQUITY_CUTOVER_ALREADY_ESTABLISHED")
        if db.execute(
            "SELECT 1 FROM paper_account_risk_state WHERE account_id=1"
        ).fetchone() is None:
            raise sqlite3.DatabaseError("ACCOUNT_EQUITY_CUTOVER_RISK_STATE_MISSING")
        account = db.execute(
            "SELECT initial_capital FROM paper_accounts WHERE account_id=1"
        ).fetchone()
        if account is None or Decimal(account[0]) != expected_capital:
            raise ValueError("ACCOUNT_EQUITY_CAPITAL_RECONCILIATION_MISMATCH")
        coverage = db.execute(
            """SELECT start_at_ms,end_at_ms,status,source FROM paper_funding_coverage
               WHERE start_at_ms < ? AND end_at_ms > ?
               ORDER BY start_at_ms,end_at_ms""",
            (observed, coverage_start),
        ).fetchall()
        cursor = coverage_start
        for row in coverage:
            start, end, status, coverage_source = row
            if start > cursor or status == "UNKNOWN":
                raise ValueError("FUNDING_PROVENANCE_INCOMPLETE")
            if status == "DISABLED" and coverage_source != "PAPER_TEST_CONFIGURATION":
                raise ValueError("FUNDING_PROVENANCE_INCOMPLETE")
            cursor = max(cursor, end)
            if cursor >= observed:
                break
        if cursor < observed:
            raise ValueError("FUNDING_PROVENANCE_INCOMPLETE")

        ledgers = db.execute(
            """SELECT strategy_id,position_base,average_entry_price,realized_pnl_quote,
                      fees_quote,funding_quote FROM paper_strategy_ledgers WHERE account_id=1"""
        ).fetchall()
        if {row["strategy_id"] for row in ledgers} != STRATEGIES:
            raise ValueError("ACCOUNT_EQUITY_LEDGER_SET_INVALID")
        realized = fees = funding_total = unrealized = Decimal(0)
        for row in ledgers:
            qty, average, pnl, fee, fund = map(Decimal, (
                row["position_base"], row["average_entry_price"],
                row["realized_pnl_quote"], row["fees_quote"], row["funding_quote"],
            ))
            if any(not value.is_finite() for value in (qty, average, pnl, fee, fund)):
                raise ValueError("ACCOUNT_EQUITY_LEDGER_CORRUPT")
            if (qty == 0 and average != 0) or (qty != 0 and average <= 0) or fee < 0:
                raise ValueError("ACCOUNT_EQUITY_LEDGER_CORRUPT")
            realized += pnl
            fees += fee
            funding_total += fund
            if qty:
                unrealized += qty * (mark - average)
            events = db.execute(
                """SELECT amount_quote,source,source_snapshot_id,payload_hash
                   FROM paper_funding_events WHERE account_id=1 AND strategy_id=?""",
                (row["strategy_id"],),
            ).fetchall()
            event_total = Decimal(0)
            for event in events:
                amount = Decimal(event["amount_quote"])
                if (not amount.is_finite() or event["source"] == "LEGACY_UNVERIFIED"
                        or not event["source_snapshot_id"] or not event["payload_hash"]
                        or event["event_at_ms"] < coverage_start
                        or event["event_at_ms"] > observed):
                    raise ValueError("FUNDING_PROVENANCE_INCOMPLETE")
                event_total += amount
            if event_total != fund:
                raise ValueError("FUNDING_LEDGER_EVENT_RECONCILIATION_MISMATCH")

        legacy_pnl = legacy_fees = Decimal(0)
        for kind, raw in db.execute(
            """SELECT adjustment_type,amount_quote FROM paper_account_adjustments
               WHERE account_id=1 AND strategy_id='LEGACY_UNATTRIBUTED'"""
        ):
            amount = Decimal(raw)
            if not amount.is_finite():
                raise ValueError("ACCOUNT_EQUITY_LEGACY_ADJUSTMENT_INVALID")
            if kind == "LEGACY_REALIZED_PNL":
                legacy_pnl += amount
            elif kind == "LEGACY_FEES" and amount >= 0:
                legacy_fees += amount
            else:
                raise ValueError("ACCOUNT_EQUITY_LEGACY_ADJUSTMENT_INVALID")
        reconciled_realized = realized + legacy_pnl
        reconciled_fees = fees + legacy_fees
        if (reconciled_realized != expected_realized or reconciled_fees != expected_fees
                or funding_total != expected_funding):
            raise ValueError("ACCOUNT_EQUITY_STATEMENT_TOTALS_MISMATCH")
        equity = expected_capital + reconciled_realized + unrealized - reconciled_fees - funding_total
        if not equity.is_finite() or equity <= 0 or equity != expected_equity:
            raise ValueError("ACCOUNT_EQUITY_RECONCILIATION_FAILED")
        day = observed // 86_400_000 * 86_400_000
        db.execute(
            """INSERT INTO paper_account_equity_cutovers
               (cutover_id,account_id,initial_capital_quote,account_equity_quote,
                mark_price,mark_candle_close_ms,mark_observed_at_ms,dataset_version,
                funding_coverage_start_at_ms,funding_coverage_end_at_ms,source,
                source_snapshot_id,payload_hash,config_version,high_water_mark_quote,
                daily_baseline_utc_day_ms,daily_baseline_equity_quote,
                reconciled_realized_pnl_quote,reconciled_fees_quote,
                reconciled_funding_quote,expected_account_equity_quote,recorded_at_ms)
               VALUES (?,1,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (cutover_id, format(expected_capital, "f"), _decimal_text(equity),
             format(mark, "f"), candle, observed, dataset, coverage_start, observed,
             source, snapshot, digest, config, _decimal_text(equity), day,
             _decimal_text(equity), format(reconciled_realized, "f"),
             format(reconciled_fees, "f"), format(funding_total, "f"),
             _decimal_text(expected_equity), recorded),
        )
        db.execute(
            """UPDATE paper_account_risk_state SET high_water_mark_quote=?,
               daily_baseline_utc_day_ms=?,daily_baseline_equity_quote=?,
               last_equity_quote=?,last_mark_price=?,mark_observed_at_ms=?,
               mark_candle_close_ms=?,dataset_version=?,risk_ready=1,
               unavailable_reason=NULL,updated_at_ms=?,version=version+1
               WHERE account_id=1""",
            (_decimal_text(equity), day, _decimal_text(equity), _decimal_text(equity),
             format(mark, "f"), observed, candle, dataset, recorded),
        )
        result = {
            "cutoverId": cutover_id, "accountEquityQuote": _decimal_text(equity),
            "highWaterMarkQuote": _decimal_text(equity),
            "dailyBaselineEquityQuote": _decimal_text(equity),
            "dailyBaselineUtcDayMs": day, "riskReady": True, "mode": "PAPER",
        }
        db.execute(
            "INSERT INTO paper_audit(at_ms,kind,document) VALUES (?, 'ACCOUNT_EQUITY_CUTOVER', ?)",
            (recorded, json.dumps(result, allow_nan=False)),
        )
        return result

def record_funding_event(
    db_path, *, funding_event_id, strategy_id, amount_quote, event_at_ms,
    source, source_snapshot_id, payload_hash, recorded_at_ms,
):
    path = Path(db_path).resolve()
    if not path.is_file():
        raise FileNotFoundError("Paper ledger is unavailable")
    if strategy_id not in STRATEGIES:
        raise ValueError("FUNDING_STRATEGY_INVALID")
    event_id = _required_text(funding_event_id, "FUNDING_EVENT_ID_INVALID", 200)
    amount, event_at, recorded = _amount(amount_quote), _stamp(event_at_ms), _stamp(recorded_at_ms)
    if event_at > recorded:
        raise ValueError("FUNDING_EVENT_TIMESTAMP_INVALID")
    source = _required_text(source, "FUNDING_SOURCE_REQUIRED")
    snapshot = _required_text(source_snapshot_id, "FUNDING_SOURCE_SNAPSHOT_REQUIRED")
    digest = _hash(payload_hash)
    with closing(sqlite3.connect(path, timeout=10)) as db, db, localcontext() as ctx:
        ctx.prec = 80
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("BEGIN IMMEDIATE")
        migration = db.execute(
            "SELECT checksum,status FROM paper_schema_migrations WHERE version=4"
        ).fetchone()
        if migration != (MIGRATION_CHECKSUM, "APPLIED"):
            raise sqlite3.DatabaseError("FUNDING_PROVENANCE_MIGRATION_NOT_APPLIED")
        old = db.execute(
            """SELECT strategy_id,amount_quote,event_at_ms,source_snapshot_id,
                      payload_hash,source,recorded_at_ms
               FROM paper_funding_events WHERE funding_event_id=?""", (event_id,)
        ).fetchone()
        if old:
            if old[:6] != (strategy_id, format(amount, "f"), event_at, snapshot, digest, source):
                raise ValueError("FUNDING_EVENT_ID_CONFLICT")
            return {"fundingEventId": event_id, "strategyId": strategy_id,
                    "amountQuote": old[1], "eventAtMs": event_at, "source": source,
                    "sourceSnapshotId": snapshot, "payloadHash": digest,
                    "recordedAtMs": old[6], "mode": "PAPER"}
        if db.execute("SELECT 1 FROM paper_funding_events WHERE payload_hash=?", (digest,)).fetchone():
            raise ValueError("FUNDING_EVENT_PAYLOAD_DUPLICATE")
        row = db.execute(
            "SELECT funding_quote FROM paper_strategy_ledgers WHERE account_id=1 AND strategy_id=?",
            (strategy_id,),
        ).fetchone()
        if row is None:
            raise sqlite3.DatabaseError("FUNDING_STRATEGY_LEDGER_MISSING")
        current = Decimal(row[0])
        if not current.is_finite():
            raise sqlite3.DatabaseError("FUNDING_LEDGER_STATE_CORRUPT")
        db.execute(
            """INSERT INTO paper_funding_events
               (funding_event_id,account_id,strategy_id,amount_quote,event_at_ms,
                source_snapshot_id,payload_hash,source,recorded_at_ms)
               VALUES (?,1,?,?,?,?,?,?,?)""",
            (event_id, strategy_id, format(amount, "f"), event_at, snapshot, digest, source, recorded),
        )
        db.execute(
            """UPDATE paper_strategy_ledgers SET funding_quote=?,updated_at_ms=?,version=version+1
               WHERE account_id=1 AND strategy_id=?""",
            (format(current + amount, "f"), recorded, strategy_id),
        )
        _refresh_equity(db, recorded)
        audit = {"fundingEventId": event_id, "strategyId": strategy_id,
                 "amountQuote": format(amount, "f"), "eventAtMs": event_at,
                 "source": source, "sourceSnapshotId": snapshot,
                 "payloadHash": digest, "recordedAtMs": recorded, "mode": "PAPER"}
        db.execute("INSERT INTO paper_audit(at_ms,kind,document) VALUES (?, 'FUNDING_EVENT', ?)",
                   (recorded, json.dumps(audit, allow_nan=False)))
        return audit


def record_funding_coverage(
    db_path, *, coverage_id, start_at_ms, end_at_ms, status, source,
    source_snapshot_id, payload_hash, config_version, recorded_at_ms,
):
    path = Path(db_path).resolve()
    if not path.is_file():
        raise FileNotFoundError("Paper ledger is unavailable")
    coverage_id = _required_text(coverage_id, "FUNDING_COVERAGE_ID_INVALID", 200)
    start, end, recorded = _stamp(start_at_ms), _stamp(end_at_ms), _stamp(recorded_at_ms)
    if start >= end or (status != "DISABLED" and end > recorded):
        raise ValueError("FUNDING_COVERAGE_INTERVAL_INVALID")
    if status not in {"VERIFIED", "UNKNOWN", "DISABLED"}:
        raise ValueError("FUNDING_COVERAGE_STATUS_INVALID")
    source = _required_text(source, "FUNDING_SOURCE_REQUIRED")
    snapshot = _required_text(source_snapshot_id, "FUNDING_SOURCE_SNAPSHOT_REQUIRED")
    config = _required_text(config_version, "FUNDING_CONFIG_VERSION_REQUIRED", 200)
    digest = _hash(payload_hash)
    if status == "DISABLED" and source != "PAPER_TEST_CONFIGURATION":
        raise ValueError("FUNDING_DISABLED_REQUIRES_PAPER_TEST_EVIDENCE")
    with closing(sqlite3.connect(path, timeout=10)) as db, db:
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("BEGIN IMMEDIATE")
        migration = db.execute(
            "SELECT checksum,status FROM paper_schema_migrations WHERE version=4"
        ).fetchone()
        if migration != (MIGRATION_CHECKSUM, "APPLIED"):
            raise sqlite3.DatabaseError("FUNDING_PROVENANCE_MIGRATION_NOT_APPLIED")
        old = db.execute(
            """SELECT start_at_ms,end_at_ms,status,source,source_snapshot_id,
                      payload_hash,config_version,recorded_at_ms
               FROM paper_funding_coverage WHERE coverage_id=?""", (coverage_id,)
        ).fetchone()
        expected = (start, end, status, source, snapshot, digest, config)
        if old:
            if old[:7] != expected:
                raise ValueError("FUNDING_COVERAGE_ID_CONFLICT")
            return {"coverageId": coverage_id, "startAtMs": start, "endAtMs": end,
                    "status": status, "source": source, "sourceSnapshotId": snapshot,
                    "payloadHash": digest, "configVersion": config, "recordedAtMs": old[7]}
        if db.execute("SELECT 1 FROM paper_funding_coverage WHERE payload_hash=?", (digest,)).fetchone():
            raise ValueError("FUNDING_COVERAGE_PAYLOAD_DUPLICATE")
        db.execute(
            """INSERT INTO paper_funding_coverage
               (coverage_id,account_id,start_at_ms,end_at_ms,status,source,
                source_snapshot_id,payload_hash,config_version,recorded_at_ms)
               VALUES (?,1,?,?,?,?,?,?,?,?)""",
            (coverage_id, start, end, status, source, snapshot, digest, config, recorded),
        )
        if status == "UNKNOWN":
            db.execute(
                """UPDATE paper_account_risk_state
                   SET risk_ready=0,unavailable_reason='FUNDING_PROVENANCE_INCOMPLETE',
                       updated_at_ms=?,version=version+1 WHERE account_id=1""", (recorded,)
            )
        audit = {"coverageId": coverage_id, "startAtMs": start, "endAtMs": end,
                 "status": status, "source": source, "sourceSnapshotId": snapshot,
                 "payloadHash": digest, "configVersion": config, "mode": "PAPER"}
        db.execute("INSERT INTO paper_audit(at_ms,kind,document) VALUES (?, 'FUNDING_COVERAGE', ?)",
                   (recorded, json.dumps(audit, allow_nan=False)))
        return {**audit, "recordedAtMs": recorded}
