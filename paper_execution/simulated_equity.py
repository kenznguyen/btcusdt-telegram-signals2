"""Atomic SIMULATED-only equity origin for the dual-ledger PAPER account.

The caller must invoke this inside the same BEGIN IMMEDIATE transaction that
creates the dual-ledger account. This path is intentionally separate from
funded-account funding reconciliation and daily-baseline replay.
"""
import hashlib
import json
import sqlite3

from paper_execution.simulated_origin import initialize_simulated_origin


_TABLE = "paper_simulated_equity_origin"
_COLUMNS = {
    "account_id", "contract_sha256", "initial_equity_quote",
    "high_water_mark_quote", "utc_day_ms", "daily_baseline_equity_quote",
    "initialized_at_ms", "source", "record_sha256",
}


def _digest(document):
    raw = json.dumps(
        document, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _objects(connection):
    return set(connection.execute(
        "SELECT type,name FROM sqlite_master"
    ).fetchall())


def _ensure_schema(connection):
    objects = _objects(connection)
    if ("table", _TABLE) not in objects:
        connection.execute(f"""CREATE TABLE {_TABLE} (
            account_id INTEGER PRIMARY KEY REFERENCES paper_accounts(account_id),
            contract_sha256 TEXT NOT NULL CHECK(length(contract_sha256)=64),
            initial_equity_quote TEXT NOT NULL CHECK(initial_equity_quote='100'),
            high_water_mark_quote TEXT NOT NULL CHECK(high_water_mark_quote='100'),
            utc_day_ms INTEGER NOT NULL CHECK(utc_day_ms>=0 AND utc_day_ms%86400000=0),
            daily_baseline_equity_quote TEXT NOT NULL CHECK(daily_baseline_equity_quote='100'),
            initialized_at_ms INTEGER NOT NULL CHECK(initialized_at_ms>=0),
            source TEXT NOT NULL CHECK(source='SIMULATED_CAPITAL_ORIGIN'),
            record_sha256 TEXT NOT NULL CHECK(length(record_sha256)=64)
        )""")
        connection.execute(f"""CREATE TRIGGER {_TABLE}_immutable_update
            BEFORE UPDATE ON {_TABLE}
            BEGIN SELECT RAISE(ABORT,'SIMULATED_EQUITY_ORIGIN_IMMUTABLE'); END""")
        connection.execute(f"""CREATE TRIGGER {_TABLE}_immutable_delete
            BEFORE DELETE ON {_TABLE}
            BEGIN SELECT RAISE(ABORT,'SIMULATED_EQUITY_ORIGIN_IMMUTABLE'); END""")
    objects = _objects(connection)
    if not {
        ("trigger", f"{_TABLE}_immutable_update"),
        ("trigger", f"{_TABLE}_immutable_delete"),
    }.issubset(objects):
        raise sqlite3.DatabaseError("SIMULATED_EQUITY_ORIGIN_SCHEMA_INCOMPLETE")
    columns = {row[1] for row in connection.execute(f"PRAGMA table_info({_TABLE})")}
    if columns != _COLUMNS:
        raise sqlite3.DatabaseError("SIMULATED_EQUITY_ORIGIN_SCHEMA_INCOMPLETE")


def _require_pristine_simulated_account(connection):
    account = connection.execute(
        "SELECT mode,initial_capital,currency FROM paper_accounts WHERE account_id=1"
    ).fetchone()
    if account != ("PAPER", "100", "USDT"):
        raise ValueError("SIMULATED_ACCOUNT_IDENTITY_MISMATCH")

    required_tables = {
        "paper_strategy_ledgers", "paper_account_adjustments", "paper_orders",
        "paper_funding_events", "paper_funding_coverage",
        "paper_account_equity_cutovers",
    }
    tables = {name for kind, name in _objects(connection) if kind == "table"}
    if not required_tables.issubset(tables):
        raise sqlite3.DatabaseError("SIMULATED_ACCOUNT_PREREQUISITE_MISSING")

    if any(connection.execute(f"SELECT 1 FROM {table} LIMIT 1").fetchone()
           for table in (
               "paper_account_adjustments", "paper_orders",
               "paper_funding_events", "paper_funding_coverage",
               "paper_account_equity_cutovers",
           )):
        raise ValueError("SIMULATED_ACCOUNT_NOT_PRISTINE")

    rows = connection.execute(
        """SELECT strategy_id,position_base,average_entry_price,
                  realized_pnl_quote,fees_quote,funding_quote,initial_margin_quote
           FROM paper_strategy_ledgers WHERE account_id=1"""
    ).fetchall()
    expected = {"STRATEGY_CORE", "AI_FREQAI", "LEGACY_UNATTRIBUTED"}
    if {row[0] for row in rows} != expected or any(
        value not in ("0", "0.0", "0.00") for row in rows for value in row[1:]
    ):
        raise ValueError("SIMULATED_ACCOUNT_NOT_PRISTINE")


def initialize_simulated_equity(
    connection, *, contract_bytes, initialized_at_ms, account_id=1,
):
    """Initialize immutable origin/seed and shared risk baselines atomically.

    The surrounding transaction must already be active and acquired with
    BEGIN IMMEDIATE. The function uses a savepoint and never commits the caller's
    transaction. Existing funded-account cutover APIs are not called or altered.
    """
    if not connection.in_transaction:
        raise sqlite3.OperationalError("SIMULATED_INITIALIZATION_REQUIRES_TRANSACTION")
    if type(account_id) is not int or account_id != 1:
        raise ValueError("SIMULATED_ACCOUNT_IDENTITY_MISMATCH")
    if type(initialized_at_ms) is not int or initialized_at_ms < 0:
        raise ValueError("SIMULATED_ORIGIN_TIMESTAMP_INVALID")

    savepoint = "simulated_equity_init"
    connection.execute(f"SAVEPOINT {savepoint}")
    try:
        _ensure_schema(connection)
        existing = connection.execute(
            f"""SELECT contract_sha256,initial_equity_quote,
                       high_water_mark_quote,utc_day_ms,
                       daily_baseline_equity_quote,initialized_at_ms,
                       source,record_sha256 FROM {_TABLE} WHERE account_id=?""",
            (account_id,),
        ).fetchone()

        if existing is None:
            _require_pristine_simulated_account(connection)
            seed = initialize_simulated_origin(
                connection, contract_bytes=contract_bytes,
                initialized_at_ms=initialized_at_ms, account_id=account_id,
            )
            initialized = seed["initializedAtMs"]
            utc_day = initialized // 86_400_000 * 86_400_000
            document = {
                "accountId": account_id,
                "contractSha256": seed["contractSha256"],
                "initialEquityQuote": "100",
                "highWaterMarkQuote": "100",
                "utcDayMs": utc_day,
                "dailyBaselineEquityQuote": "100",
                "initializedAtMs": initialized,
                "source": "SIMULATED_CAPITAL_ORIGIN",
            }
            record_hash = _digest(document)
            connection.execute(
                f"INSERT INTO {_TABLE} VALUES (?,?,?,?,?,?,?,?,?)",
                (account_id, seed["contractSha256"], "100", "100", utc_day,
                 "100", initialized, "SIMULATED_CAPITAL_ORIGIN", record_hash),
            )
            risk = connection.execute(
                """SELECT risk_ready,high_water_mark_quote,
                          daily_baseline_utc_day_ms,daily_baseline_equity_quote
                   FROM paper_account_risk_state WHERE account_id=?""",
                (account_id,),
            ).fetchone()
            if risk is None or risk[0] != 0 or any(value is not None for value in risk[1:]):
                raise sqlite3.DatabaseError("SIMULATED_ACCOUNT_RISK_STATE_NOT_PRISTINE")
            connection.execute(
                """UPDATE paper_account_risk_state
                   SET high_water_mark_quote='100',daily_baseline_utc_day_ms=?,
                       daily_baseline_equity_quote='100',risk_ready=0,
                       unavailable_reason='SIMULATED_INITIAL_MARK_REQUIRED',
                       updated_at_ms=?,version=version+1
                   WHERE account_id=?""",
                (utc_day, initialized, account_id),
            )
            existing = (
                seed["contractSha256"], "100", "100", utc_day, "100",
                initialized, "SIMULATED_CAPITAL_ORIGIN", record_hash,
            )
        else:
            seed = initialize_simulated_origin(
                connection, contract_bytes=contract_bytes,
                initialized_at_ms=initialized_at_ms, account_id=account_id,
            )
            document = {
                "accountId": account_id,
                "contractSha256": existing[0],
                "initialEquityQuote": existing[1],
                "highWaterMarkQuote": existing[2],
                "utcDayMs": existing[3],
                "dailyBaselineEquityQuote": existing[4],
                "initializedAtMs": existing[5],
                "source": existing[6],
            }
            if (existing[0] != seed["contractSha256"]
                    or existing[1:7] != ("100", "100", existing[3], "100",
                                         seed["initializedAtMs"], "SIMULATED_CAPITAL_ORIGIN")
                    or existing[7] != _digest(document)):
                raise ValueError("SIMULATED_ORIGIN_CONTRACT_MISMATCH")

        connection.execute(f"RELEASE SAVEPOINT {savepoint}")
        return {
            "accountId": account_id,
            "contractSha256": existing[0],
            "initialEquityQuote": existing[1],
            "highWaterMarkQuote": existing[2],
            "utcDayMs": existing[3],
            "dailyBaselineEquityQuote": existing[4],
            "initializedAtMs": existing[5],
            "recordSha256": existing[7],
        }
    except Exception:
        connection.execute(f"ROLLBACK TO SAVEPOINT {savepoint}")
        connection.execute(f"RELEASE SAVEPOINT {savepoint}")
        raise
