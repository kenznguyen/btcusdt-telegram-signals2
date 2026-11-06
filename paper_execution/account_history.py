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
