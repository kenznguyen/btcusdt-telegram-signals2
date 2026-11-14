"""Immutable provenance for the one-time SIMULATED_CAPITAL_V1 seed.

This module does not create accounts, funding events, equity marks, or enable order
admission. Callers own the surrounding transaction when composing this with account
and risk-state initialization.
"""
import hashlib
import json
import sqlite3

from paper_execution.simulated_capital import validate_simulated_capital_contract


_ORIGIN_COLUMNS = {
    "account_id", "contract_id", "schema_version", "capital_mode", "trading_mode",
    "initial_capital_quote", "quote_currency", "contract_sha256", "seed_event_id",
    "initialized_at_ms", "source", "record_sha256",
}
_SEED_COLUMNS = {
    "event_id", "account_id", "event_type", "amount_quote", "quote_currency",
    "contract_sha256", "recorded_at_ms", "source", "record_sha256",
}


def _canonical_digest(document):
    payload = json.dumps(
        document, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _reject_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("SIMULATED_ORIGIN_CONTRACT_INVALID")
        result[key] = value
    return result


def _contract(contract_bytes):
    if not isinstance(contract_bytes, bytes) or not 1 <= len(contract_bytes) <= 16_384:
        raise ValueError("SIMULATED_ORIGIN_CONTRACT_INVALID")
    try:
        raw = json.loads(
            contract_bytes.decode("utf-8"),
            object_pairs_hook=_reject_duplicate_keys,
        )
        validated = validate_simulated_capital_contract(raw)
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise ValueError("SIMULATED_ORIGIN_CONTRACT_INVALID") from None
    return validated, hashlib.sha256(contract_bytes).hexdigest()


def _schema_objects(connection):
    return {
        (kind, name) for kind, name in connection.execute(
            "SELECT type,name FROM sqlite_master"
        )
    }


def _ensure_schema(connection):
    objects = _schema_objects(connection)
    origin_exists = ("table", "paper_simulated_capital_origin") in objects
    seed_exists = ("table", "paper_simulated_capital_seed_events") in objects
    if origin_exists != seed_exists:
        raise sqlite3.DatabaseError("SIMULATED_ORIGIN_SCHEMA_INCOMPLETE")

    if not origin_exists:
        connection.execute("""CREATE TABLE paper_simulated_capital_origin (
            account_id INTEGER PRIMARY KEY,
            contract_id TEXT NOT NULL CHECK(contract_id='SIMULATED_CAPITAL_V1'),
            schema_version INTEGER NOT NULL CHECK(schema_version=1),
            capital_mode TEXT NOT NULL CHECK(capital_mode='SIMULATED'),
            trading_mode TEXT NOT NULL CHECK(trading_mode='PAPER'),
            initial_capital_quote TEXT NOT NULL CHECK(initial_capital_quote='100'),
            quote_currency TEXT NOT NULL CHECK(quote_currency='USDT'),
            contract_sha256 TEXT NOT NULL CHECK(length(contract_sha256)=64),
            seed_event_id TEXT NOT NULL UNIQUE,
            initialized_at_ms INTEGER NOT NULL CHECK(initialized_at_ms>=0),
            source TEXT NOT NULL CHECK(source='OWNER_APPROVED_SIMULATION'),
            record_sha256 TEXT NOT NULL CHECK(length(record_sha256)=64)
        )""")
        connection.execute("""CREATE TABLE paper_simulated_capital_seed_events (
            event_id TEXT PRIMARY KEY,
            account_id INTEGER NOT NULL UNIQUE
                REFERENCES paper_simulated_capital_origin(account_id),
            event_type TEXT NOT NULL CHECK(event_type='INITIAL_SIMULATED_SEED'),
            amount_quote TEXT NOT NULL CHECK(amount_quote='100'),
            quote_currency TEXT NOT NULL CHECK(quote_currency='USDT'),
            contract_sha256 TEXT NOT NULL CHECK(length(contract_sha256)=64),
            recorded_at_ms INTEGER NOT NULL CHECK(recorded_at_ms>=0),
            source TEXT NOT NULL CHECK(source='OWNER_APPROVED_SIMULATION'),
            record_sha256 TEXT NOT NULL CHECK(length(record_sha256)=64)
        )""")
        connection.execute("""CREATE TRIGGER paper_simulated_origin_immutable_update
            BEFORE UPDATE ON paper_simulated_capital_origin
            BEGIN SELECT RAISE(ABORT,'SIMULATED_ORIGIN_IMMUTABLE'); END""")
        connection.execute("""CREATE TRIGGER paper_simulated_origin_immutable_delete
            BEFORE DELETE ON paper_simulated_capital_origin
            BEGIN SELECT RAISE(ABORT,'SIMULATED_ORIGIN_IMMUTABLE'); END""")
        connection.execute("""CREATE TRIGGER paper_simulated_seed_immutable_update
            BEFORE UPDATE ON paper_simulated_capital_seed_events
            BEGIN SELECT RAISE(ABORT,'SIMULATED_SEED_IMMUTABLE'); END""")
        connection.execute("""CREATE TRIGGER paper_simulated_seed_immutable_delete
            BEFORE DELETE ON paper_simulated_capital_seed_events
            BEGIN SELECT RAISE(ABORT,'SIMULATED_SEED_IMMUTABLE'); END""")

    objects = _schema_objects(connection)
    required = {
        ("trigger", "paper_simulated_origin_immutable_update"),
        ("trigger", "paper_simulated_origin_immutable_delete"),
        ("trigger", "paper_simulated_seed_immutable_update"),
        ("trigger", "paper_simulated_seed_immutable_delete"),
    }
    if not required.issubset(objects):
        raise sqlite3.DatabaseError("SIMULATED_ORIGIN_SCHEMA_INCOMPLETE")
    origin_columns = {row[1] for row in connection.execute(
        "PRAGMA table_info(paper_simulated_capital_origin)"
    )}
    seed_columns = {row[1] for row in connection.execute(
        "PRAGMA table_info(paper_simulated_capital_seed_events)"
    )}
    if origin_columns != _ORIGIN_COLUMNS or seed_columns != _SEED_COLUMNS:
        raise sqlite3.DatabaseError("SIMULATED_ORIGIN_SCHEMA_INCOMPLETE")


def initialize_simulated_origin(
    connection, *, contract_bytes, initialized_at_ms, account_id=1,
):
    """Create or verify exactly one immutable simulated seed for an existing account.

    If no transaction is active, this function acquires BEGIN IMMEDIATE and owns
    commit/rollback. If called inside a transaction, it uses a savepoint; the caller
    must have acquired its write lock (BEGIN IMMEDIATE) before calling.
    """
    if type(account_id) is not int or account_id <= 0:
        raise ValueError("SIMULATED_ORIGIN_ACCOUNT_INVALID")
    if type(initialized_at_ms) is not int or initialized_at_ms < 0:
        raise ValueError("SIMULATED_ORIGIN_TIMESTAMP_INVALID")
    contract, contract_hash = _contract(contract_bytes)
    owns_transaction = not connection.in_transaction
    savepoint = "simulated_origin_init"
    if owns_transaction:
        connection.execute("BEGIN IMMEDIATE")
    else:
        connection.execute(f"SAVEPOINT {savepoint}")

    try:
        _ensure_schema(connection)
        account_table = connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='paper_accounts'"
        ).fetchone()
        if not account_table or not connection.execute(
            "SELECT 1 FROM paper_accounts WHERE account_id=?", (account_id,)
        ).fetchone():
            raise ValueError("SIMULATED_ORIGIN_ACCOUNT_MISSING")

        seed_event_id = f"simulated-seed:{account_id}:{contract_hash}"
        source = "OWNER_APPROVED_SIMULATION"
        existing_origin = connection.execute(
            "SELECT contract_id,schema_version,capital_mode,trading_mode,"
            "initial_capital_quote,quote_currency,contract_sha256,seed_event_id,"
            "initialized_at_ms,source,record_sha256 "
            "FROM paper_simulated_capital_origin WHERE account_id=?",
            (account_id,),
        ).fetchone()
        existing_seed = connection.execute(
            "SELECT event_id,event_type,amount_quote,quote_currency,contract_sha256,"
            "recorded_at_ms,source,record_sha256 "
            "FROM paper_simulated_capital_seed_events WHERE account_id=?",
            (account_id,),
        ).fetchone()
        if (existing_origin is None) != (existing_seed is None):
            raise ValueError("SIMULATED_ORIGIN_CONTRACT_MISMATCH")
        effective_timestamp = initialized_at_ms
        if existing_origin is not None:
            effective_timestamp = existing_origin[8]
            if type(effective_timestamp) is not int or effective_timestamp < 0:
                raise ValueError("SIMULATED_ORIGIN_CONTRACT_MISMATCH")
        origin_document = {
            "accountId": account_id,
            "contractId": contract["contractId"],
            "schemaVersion": contract["schemaVersion"],
            "capitalMode": contract["capitalMode"],
            "tradingMode": contract["tradingMode"],
            "initialCapitalQuote": contract["initialCapitalQuote"],
            "quoteCurrency": contract["quoteCurrency"],
            "contractSha256": contract_hash,
            "seedEventId": seed_event_id,
            "initializedAtMs": effective_timestamp,
            "source": source,
        }
        origin_digest = _canonical_digest(origin_document)
        seed_document = {
            "eventId": seed_event_id,
            "accountId": account_id,
            "eventType": "INITIAL_SIMULATED_SEED",
            "amountQuote": contract["initialCapitalQuote"],
            "quoteCurrency": contract["quoteCurrency"],
            "contractSha256": contract_hash,
            "recordedAtMs": effective_timestamp,
            "source": source,
        }
        seed_digest = _canonical_digest(seed_document)

        expected_origin = (
            contract["contractId"], contract["schemaVersion"], contract["capitalMode"],
            contract["tradingMode"], contract["initialCapitalQuote"],
            contract["quoteCurrency"], contract_hash, seed_event_id,
            initialized_at_ms, source, origin_digest,
        )
        expected_seed = (
            seed_event_id, "INITIAL_SIMULATED_SEED", contract["initialCapitalQuote"],
            contract["quoteCurrency"], contract_hash, initialized_at_ms, source,
            seed_digest,
        )
        if existing_origin is None and existing_seed is None:
            connection.execute(
                "INSERT INTO paper_simulated_capital_origin VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                (account_id, *expected_origin),
            )
            connection.execute(
                "INSERT INTO paper_simulated_capital_seed_events VALUES (?,?,?,?,?,?,?,?,?)",
                (seed_event_id, account_id, *expected_seed[1:]),
            )
        elif existing_origin != expected_origin or existing_seed != expected_seed:
            raise ValueError("SIMULATED_ORIGIN_CONTRACT_MISMATCH")

        if owns_transaction:
            connection.commit()
        else:
            connection.execute(f"RELEASE SAVEPOINT {savepoint}")
        return {
            "accountId": account_id,
            "contractId": contract["contractId"],
            "initialCapitalQuote": contract["initialCapitalQuote"],
            "quoteCurrency": contract["quoteCurrency"],
            "contractSha256": contract_hash,
            "seedEventId": seed_event_id,
            "initializedAtMs": effective_timestamp,
            "source": source,
            "originRecordSha256": origin_digest,
            "seedRecordSha256": seed_digest,
        }
    except Exception:
        if owns_transaction:
            connection.rollback()
        else:
            connection.execute(f"ROLLBACK TO SAVEPOINT {savepoint}")
            connection.execute(f"RELEASE SAVEPOINT {savepoint}")
        raise
