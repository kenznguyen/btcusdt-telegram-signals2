"""Immutable SIMULATED-only UTC daily-baseline rollover provenance."""
import hashlib
import json
import sqlite3
from decimal import Decimal, DecimalException

MIGRATION_VERSION = 11
MIGRATION_CHECKSUM = hashlib.sha256(
    b"dual-ledger-v11:simulated-utc-daily-baseline-rollover-immutable-hash-chain"
).hexdigest()
DAY_MS = 86_400_000
TABLE = "paper_simulated_daily_baseline_events"


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
                      allow_nan=False)


def _digest(value):
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _positive_decimal(raw, code):
    if not isinstance(raw, str) or not 1 <= len(raw) <= 256:
        raise sqlite3.DatabaseError(code)
    try:
        value = Decimal(raw)
    except (DecimalException, TypeError, ValueError):
        raise sqlite3.DatabaseError(code) from None
    if not value.is_finite() or value <= 0:
        raise sqlite3.DatabaseError(code)
    return format(value, "f")


def migrate_simulated_daily_baseline_rollover(connection, source_sha):
    if (not isinstance(source_sha, str) or len(source_sha) != 40
            or any(c not in "0123456789abcdef" for c in source_sha.lower())):
        raise ValueError("DUAL_LEDGER_SOURCE_SHA_REQUIRED")
    row = connection.execute(
        "SELECT checksum,status FROM paper_schema_migrations WHERE version=?",
        (MIGRATION_VERSION,),
    ).fetchone()
    if row and row != (MIGRATION_CHECKSUM, "APPLIED"):
        raise sqlite3.DatabaseError("SIMULATED_DAILY_BASELINE_MIGRATION_CHECKSUM_MISMATCH")
    connection.execute(f"""CREATE TABLE IF NOT EXISTS {TABLE} (
        event_id INTEGER PRIMARY KEY AUTOINCREMENT,
        account_id INTEGER NOT NULL REFERENCES paper_accounts(account_id),
        utc_day_ms INTEGER NOT NULL CHECK(utc_day_ms>=0 AND utc_day_ms%86400000=0),
        baseline_equity_quote TEXT NOT NULL,
        previous_utc_day_ms INTEGER NOT NULL CHECK(previous_utc_day_ms>=0 AND previous_utc_day_ms%86400000=0),
        previous_equity_quote TEXT NOT NULL,
        previous_mark_observed_at_ms INTEGER NOT NULL CHECK(previous_mark_observed_at_ms>=0),
        previous_dataset_version TEXT NOT NULL CHECK(length(trim(previous_dataset_version))>0),
        previous_event_hash TEXT NOT NULL CHECK(length(previous_event_hash)=64),
        event_hash TEXT NOT NULL UNIQUE CHECK(length(event_hash)=64),
        recorded_at_ms INTEGER NOT NULL CHECK(recorded_at_ms>=0),
        source TEXT NOT NULL CHECK(source='SIMULATED_PREVIOUS_DAY_LAST_CONFIRMED_EQUITY'),
        UNIQUE(account_id,utc_day_ms)
    )""")
    for action in ("UPDATE", "DELETE"):
        name = f"{TABLE}_immutable_{action.lower()}"
        connection.execute(f"""CREATE TRIGGER IF NOT EXISTS {name}
            BEFORE {action} ON {TABLE}
            BEGIN SELECT RAISE(ABORT,'SIMULATED_DAILY_BASELINE_EVENT_IMMUTABLE'); END""")
    objects = {(r[0], r[1]) for r in connection.execute(
        "SELECT type,name FROM sqlite_master"
    )}
    required = {("trigger", f"{TABLE}_immutable_update"),
                ("trigger", f"{TABLE}_immutable_delete")}
    columns = {r[1] for r in connection.execute(f"PRAGMA table_info({TABLE})")}
    expected = {
        "event_id", "account_id", "utc_day_ms", "baseline_equity_quote",
        "previous_utc_day_ms", "previous_equity_quote",
        "previous_mark_observed_at_ms", "previous_dataset_version",
        "previous_event_hash", "event_hash", "recorded_at_ms", "source",
    }
    if not required.issubset(objects) or columns != expected:
        raise sqlite3.DatabaseError("SIMULATED_DAILY_BASELINE_SCHEMA_INCOMPLETE")
    if row is None:
        connection.execute(
            """INSERT INTO paper_schema_migrations
               (version,name,checksum,applied_at_ms,source_sha,status)
               VALUES (?,?,?,?,?,'APPLIED')""",
            (MIGRATION_VERSION, "simulated-utc-daily-baseline-rollover",
             MIGRATION_CHECKSUM, 0, source_sha.lower()),
        )


def append_simulated_daily_baseline_event(
    connection, *, utc_day_ms, baseline_equity_quote, previous_utc_day_ms,
    previous_equity_quote, previous_mark_observed_at_ms,
    previous_dataset_version, recorded_at_ms,
):
    from paper_execution.simulated_equity import verify_simulated_equity_origin
    origin = verify_simulated_equity_origin(connection)
    if not origin:
        raise sqlite3.DatabaseError("SIMULATED_DAILY_BASELINE_ORIGIN_REQUIRED")
    if (type(utc_day_ms) is not int or type(previous_utc_day_ms) is not int
            or utc_day_ms != previous_utc_day_ms + DAY_MS
            or utc_day_ms % DAY_MS or previous_utc_day_ms % DAY_MS
            or type(previous_mark_observed_at_ms) is not int
            or previous_mark_observed_at_ms // DAY_MS * DAY_MS != previous_utc_day_ms
            or type(recorded_at_ms) is not int or recorded_at_ms < utc_day_ms
            or not isinstance(previous_dataset_version, str)
            or not previous_dataset_version.strip()):
        raise ValueError("ACCOUNT_RISK_DAILY_BASELINE_UNAVAILABLE")
    baseline = _positive_decimal(str(baseline_equity_quote),
                                 "SIMULATED_DAILY_BASELINE_EQUITY_INVALID")
    previous_equity = _positive_decimal(str(previous_equity_quote),
                                        "SIMULATED_DAILY_BASELINE_EQUITY_INVALID")
    last = connection.execute(
        f"SELECT utc_day_ms,event_hash FROM {TABLE} WHERE account_id=1 ORDER BY utc_day_ms DESC LIMIT 1"
    ).fetchone()
    previous_hash = last[1] if last else origin["recordSha256"]
    expected_previous_day = last[0] if last else origin["utcDayMs"]
    if expected_previous_day != previous_utc_day_ms:
        raise ValueError("ACCOUNT_RISK_DAILY_BASELINE_UNAVAILABLE")
    document = {
        "accountId": 1, "utcDayMs": utc_day_ms,
        "baselineEquityQuote": baseline,
        "previousUtcDayMs": previous_utc_day_ms,
        "previousEquityQuote": previous_equity,
        "previousMarkObservedAtMs": previous_mark_observed_at_ms,
        "previousDatasetVersion": previous_dataset_version,
        "previousEventHash": previous_hash,
        "recordedAtMs": recorded_at_ms,
        "source": "SIMULATED_PREVIOUS_DAY_LAST_CONFIRMED_EQUITY",
    }
    event_hash = _digest(document)
    connection.execute(
        f"""INSERT INTO {TABLE}
            (account_id,utc_day_ms,baseline_equity_quote,previous_utc_day_ms,
             previous_equity_quote,previous_mark_observed_at_ms,
             previous_dataset_version,previous_event_hash,event_hash,
             recorded_at_ms,source)
            VALUES (1,?,?,?,?,?,?,?,?,?,'SIMULATED_PREVIOUS_DAY_LAST_CONFIRMED_EQUITY')""",
        (utc_day_ms, baseline, previous_utc_day_ms, previous_equity,
         previous_mark_observed_at_ms, previous_dataset_version, previous_hash,
         event_hash, recorded_at_ms),
    )
    return {"eventHash": event_hash, "baselineEquityQuote": baseline,
            "utcDayMs": utc_day_ms}


def verify_simulated_daily_baseline_provenance(connection, *, risk_day, risk_baseline):
    from paper_execution.simulated_equity import verify_simulated_equity_origin
    origin = verify_simulated_equity_origin(connection)
    if not origin:
        raise sqlite3.DatabaseError("SIMULATED_DAILY_BASELINE_ORIGIN_REQUIRED")
    objects = {(r[0], r[1]) for r in connection.execute(
        "SELECT type,name FROM sqlite_master"
    )}
    if (("table", TABLE) not in objects
            or ("trigger", f"{TABLE}_immutable_update") not in objects
            or ("trigger", f"{TABLE}_immutable_delete") not in objects):
        raise sqlite3.DatabaseError("SIMULATED_DAILY_BASELINE_PROVENANCE_INVALID")
    previous_day = origin["utcDayMs"]
    previous_hash = origin["recordSha256"]
    rows = connection.execute(
        f"""SELECT utc_day_ms,baseline_equity_quote,previous_utc_day_ms,
                   previous_equity_quote,previous_mark_observed_at_ms,
                   previous_dataset_version,previous_event_hash,event_hash,
                   recorded_at_ms,source
            FROM {TABLE} WHERE account_id=1 ORDER BY utc_day_ms"""
    ).fetchall()
    for row in rows:
        day, baseline, prior_day, prior_equity, prior_mark, dataset, prior_hash, event_hash, recorded, source = row
        try:
            baseline = _positive_decimal(baseline, "SIMULATED_DAILY_BASELINE_PROVENANCE_INVALID")
            prior_equity = _positive_decimal(prior_equity, "SIMULATED_DAILY_BASELINE_PROVENANCE_INVALID")
            expected = {
                "accountId": 1, "utcDayMs": day, "baselineEquityQuote": baseline,
                "previousUtcDayMs": prior_day, "previousEquityQuote": prior_equity,
                "previousMarkObservedAtMs": prior_mark,
                "previousDatasetVersion": dataset, "previousEventHash": prior_hash,
                "recordedAtMs": recorded, "source": source,
            }
            if (day != previous_day + DAY_MS or prior_day != previous_day
                    or type(prior_mark) is not int
                    or prior_mark // DAY_MS * DAY_MS != prior_day
                    or not isinstance(dataset, str) or not dataset.strip()
                    or prior_hash != previous_hash
                    or source != "SIMULATED_PREVIOUS_DAY_LAST_CONFIRMED_EQUITY"
                    or type(recorded) is not int or recorded < day
                    or event_hash != _digest(expected)):
                raise ValueError
        except (ValueError, TypeError, ArithmeticError):
            raise sqlite3.DatabaseError("SIMULATED_DAILY_BASELINE_PROVENANCE_INVALID") from None
        previous_day, previous_hash = day, event_hash
    if risk_day != previous_day:
        raise sqlite3.DatabaseError("SIMULATED_DAILY_BASELINE_PROVENANCE_INVALID")
    if rows and _positive_decimal(str(risk_baseline),
                                  "SIMULATED_DAILY_BASELINE_PROVENANCE_INVALID") != rows[-1][1]:
        raise sqlite3.DatabaseError("SIMULATED_DAILY_BASELINE_PROVENANCE_INVALID")
    if not rows and (risk_day != origin["utcDayMs"] or str(risk_baseline) != "100"):
        raise sqlite3.DatabaseError("SIMULATED_DAILY_BASELINE_PROVENANCE_INVALID")
    return True
