"""Durable, isolated SQLite journal for Continuous Core cycle claims.

This journal coordinates runner ownership of immutable candle cycles. It is
intentionally separate from T0 market-data storage and PaperLedger; PaperLedger
remains the authority for paper-order side effects.
"""

from contextlib import closing
import os
from pathlib import Path
import sqlite3


class CycleConflict(ValueError):
    """Raised when one canonical cycle key is presented with conflicting input."""


class JournalError(RuntimeError):
    """Raised when the durable journal cannot be trusted or updated safely."""


_SCHEMA_VERSION = 1
_BUSY_TIMEOUT_MS = 10_000


class ContinuousJournal:
    """SQLite-backed durable journal with atomic, idempotent cycle claims."""

    _T0_DATABASE_ENV_KEYS = ("MARKET_DATA_DB", "T0_FEEDER_LEASE_DB")

    @classmethod
    def _assert_path_isolated_from_t0(cls, candidate):
        candidate = Path(candidate).expanduser().resolve(strict=False)
        for env_key in cls._T0_DATABASE_ENV_KEYS:
            configured = os.environ.get(env_key)
            if not configured or not configured.strip():
                continue
            protected = Path(configured).expanduser().resolve(strict=False)
            if candidate == protected:
                raise JournalError("JOURNAL_MUST_NOT_SHARE_T0_DATABASE")
            try:
                if candidate.exists() and protected.exists() and os.path.samefile(
                    candidate, protected
                ):
                    raise JournalError("JOURNAL_MUST_NOT_SHARE_T0_DATABASE")
            except OSError as exc:
                raise JournalError("JOURNAL_T0_PATH_CHECK_FAILED") from exc

    def __init__(self, path):
        requested_path = Path(path).expanduser()
        self._assert_path_isolated_from_t0(requested_path)
        self.path = requested_path.resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self):
        connection = sqlite3.connect(
            self.path,
            timeout=_BUSY_TIMEOUT_MS / 1000,
            isolation_level=None,
        )
        connection.row_factory = sqlite3.Row
        connection.execute(f"PRAGMA busy_timeout={_BUSY_TIMEOUT_MS}")
        connection.execute("PRAGMA foreign_keys=ON")
        return connection

    def _initialize(self):
        try:
            with closing(self._connect()) as connection:
                connection.execute("PRAGMA journal_mode=WAL")
                connection.execute("BEGIN IMMEDIATE")
                try:
                    connection.execute(
                        """CREATE TABLE IF NOT EXISTS journal_meta (
                               singleton INTEGER PRIMARY KEY CHECK(singleton=1),
                               schema_version INTEGER NOT NULL
                           )"""
                    )
                    row = connection.execute(
                        "SELECT schema_version FROM journal_meta WHERE singleton=1"
                    ).fetchone()
                    if row is None:
                        connection.execute(
                            "INSERT INTO journal_meta(singleton,schema_version) VALUES (1,?)",
                            (_SCHEMA_VERSION,),
                        )
                    elif row["schema_version"] != _SCHEMA_VERSION:
                        raise JournalError("JOURNAL_SCHEMA_VERSION_MISMATCH")

                    connection.execute(
                        """CREATE TABLE IF NOT EXISTS continuous_cycles (
                               cycle_key TEXT PRIMARY KEY,
                               bundle_id TEXT NOT NULL,
                               bundle_sha256 TEXT NOT NULL,
                               bundle_path TEXT NOT NULL,
                               source_sha TEXT NOT NULL,
                               config_sha256 TEXT NOT NULL,
                               status TEXT NOT NULL,
                               claimed_at_ms INTEGER NOT NULL,
                               updated_at_ms INTEGER NOT NULL,
                               state_version INTEGER NOT NULL DEFAULT 1,
                               run_id TEXT,
                               intent_id TEXT,
                               order_id TEXT,
                               terminal_result TEXT
                           )"""
                    )
                    connection.execute(
                        """CREATE INDEX IF NOT EXISTS continuous_cycles_status_idx
                           ON continuous_cycles(status, claimed_at_ms)"""
                    )
                    connection.execute(
                        """CREATE TABLE IF NOT EXISTS continuous_checkpoints (
                               stream_key TEXT PRIMARY KEY,
                               candle_open_ms INTEGER NOT NULL,
                               cycle_key TEXT NOT NULL,
                               updated_at_ms INTEGER NOT NULL
                           )"""
                    )
                    connection.commit()
                except Exception:
                    connection.rollback()
                    raise
        except JournalError:
            raise
        except sqlite3.Error as exc:
            raise JournalError("JOURNAL_INITIALIZATION_FAILED") from exc

    @staticmethod
    def _required_text(value, field):
        if not isinstance(value, str) or not value.strip() or len(value) > 2048:
            raise ValueError(f"JOURNAL_{field.upper()}_INVALID")
        if not value.isprintable():
            raise ValueError(f"JOURNAL_{field.upper()}_INVALID")
        return value

    @staticmethod
    def _timestamp(value):
        if type(value) is not int or value < 0:
            raise ValueError("JOURNAL_TIMESTAMP_INVALID")
        return value

    def claim_cycle(
        self,
        cycle_key,
        bundle_id,
        bundle_sha256,
        bundle_path,
        source_sha,
        config_sha256,
        claimed_at_ms,
    ):
        """Claim a cycle once; exact duplicate delivery is a no-op."""
        values = {
            "cycle_key": self._required_text(cycle_key, "cycle_key"),
            "bundle_id": self._required_text(bundle_id, "bundle_id"),
            "bundle_sha256": self._required_text(bundle_sha256, "bundle_sha256"),
            "bundle_path": self._required_text(bundle_path, "bundle_path"),
            "source_sha": self._required_text(source_sha, "source_sha"),
            "config_sha256": self._required_text(config_sha256, "config_sha256"),
            "claimed_at_ms": self._timestamp(claimed_at_ms),
        }
        try:
            with closing(self._connect()) as connection:
                connection.execute("BEGIN IMMEDIATE")
                row = connection.execute(
                    """SELECT bundle_id,bundle_sha256,bundle_path,source_sha,config_sha256
                       FROM continuous_cycles WHERE cycle_key=?""",
                    (values["cycle_key"],),
                ).fetchone()
                if row is not None:
                    existing = tuple(row[key] for key in (
                        "bundle_id", "bundle_sha256", "bundle_path", "source_sha", "config_sha256"
                    ))
                    incoming = tuple(values[key] for key in (
                        "bundle_id", "bundle_sha256", "bundle_path", "source_sha", "config_sha256"
                    ))
                    if existing != incoming:
                        raise CycleConflict("CYCLE_INPUT_CONFLICT")
                    connection.commit()
                    return False

                connection.execute(
                    """INSERT INTO continuous_cycles (
                           cycle_key,bundle_id,bundle_sha256,bundle_path,source_sha,
                           config_sha256,status,claimed_at_ms,updated_at_ms,state_version
                       ) VALUES (?,?,?,?,?,?,'CLAIMED',?,?,1)""",
                    (
                        values["cycle_key"], values["bundle_id"], values["bundle_sha256"],
                        values["bundle_path"], values["source_sha"], values["config_sha256"],
                        values["claimed_at_ms"], values["claimed_at_ms"],
                    ),
                )
                connection.commit()
                return True
        except (CycleConflict, ValueError):
            raise
        except sqlite3.Error as exc:
            raise JournalError("JOURNAL_CLAIM_FAILED") from exc


    _TRANSITIONS = {
        "CLAIMED": {"VALIDATING", "EXECUTING", "INPUT_REJECTED", "FAILED",
                    "UNKNOWN_REQUIRES_RECONCILIATION"},
        "VALIDATING": {"EXECUTING", "NO_SIGNAL", "INPUT_REJECTED", "FAILED",
                       "UNKNOWN_REQUIRES_RECONCILIATION"},
        "EXECUTING": {"NO_SIGNAL", "PAPER_ACCEPTED", "RISK_REJECTED",
                      "INPUT_REJECTED", "FAILED", "UNKNOWN_REQUIRES_RECONCILIATION"},
        "UNKNOWN_REQUIRES_RECONCILIATION": {
            "NO_SIGNAL", "PAPER_ACCEPTED", "RISK_REJECTED", "FAILED",
        },
    }
    _TERMINAL_STATES = {
        "NO_SIGNAL", "PAPER_ACCEPTED", "RISK_REJECTED", "INPUT_REJECTED", "FAILED",
    }

    def transition_cycle(
        self,
        cycle_key,
        *,
        expected_status,
        status,
        updated_at_ms,
        run_id=None,
        intent_id=None,
        order_id=None,
        terminal_result=None,
    ):
        """Compare-and-swap a cycle state; terminal outcomes cannot be replayed."""
        cycle_key = self._required_text(cycle_key, "cycle_key")
        expected_status = self._required_text(expected_status, "expected_status")
        status = self._required_text(status, "status")
        updated_at_ms = self._timestamp(updated_at_ms)
        optional = {
            "run_id": run_id,
            "intent_id": intent_id,
            "order_id": order_id,
            "terminal_result": terminal_result,
        }
        for field, value in optional.items():
            if value is not None:
                self._required_text(value, field)
        if expected_status in self._TERMINAL_STATES:
            raise CycleConflict("CYCLE_TERMINAL")
        if status not in self._TRANSITIONS.get(expected_status, set()):
            raise ValueError("JOURNAL_TRANSITION_NOT_ALLOWED")
        if status in self._TERMINAL_STATES and terminal_result is None:
            raise ValueError("JOURNAL_TERMINAL_RESULT_REQUIRED")

        try:
            with closing(self._connect()) as connection:
                connection.execute("BEGIN IMMEDIATE")
                row = connection.execute(
                    """SELECT status,updated_at_ms,intent_id,run_id
                       FROM continuous_cycles WHERE cycle_key=?""",
                    (cycle_key,),
                ).fetchone()
                if row is None or row["status"] != expected_status:
                    raise CycleConflict("CYCLE_STATE_CONFLICT")
                if updated_at_ms < row["updated_at_ms"]:
                    raise ValueError("JOURNAL_TIMESTAMP_REGRESSION")
                if row["intent_id"] is not None and intent_id not in (None, row["intent_id"]):
                    raise CycleConflict("CYCLE_INTENT_CONFLICT")
                if row["run_id"] is not None and run_id not in (None, row["run_id"]):
                    raise CycleConflict("CYCLE_RUN_CONFLICT")
                connection.execute(
                    """UPDATE continuous_cycles
                       SET status=?,updated_at_ms=?,state_version=state_version+1,
                           run_id=COALESCE(?,run_id),
                           intent_id=COALESCE(?,intent_id),
                           order_id=COALESCE(?,order_id),
                           terminal_result=COALESCE(?,terminal_result)
                       WHERE cycle_key=? AND status=?""",
                    (
                        status, updated_at_ms, run_id, intent_id, order_id,
                        terminal_result, cycle_key, expected_status,
                    ),
                )
                if status in {"NO_SIGNAL", "PAPER_ACCEPTED", "RISK_REJECTED"}:
                    stream_key, candle_open_ms = self._checkpoint_identity(cycle_key)
                    connection.execute(
                        """INSERT INTO continuous_checkpoints(
                               stream_key,candle_open_ms,cycle_key,updated_at_ms
                           ) VALUES (?,?,?,?)
                           ON CONFLICT(stream_key) DO UPDATE SET
                               candle_open_ms=excluded.candle_open_ms,
                               cycle_key=excluded.cycle_key,
                               updated_at_ms=excluded.updated_at_ms
                           WHERE excluded.candle_open_ms >
                                 continuous_checkpoints.candle_open_ms""",
                        (stream_key, candle_open_ms, cycle_key, updated_at_ms),
                    )
                connection.commit()
                return True
        except (CycleConflict, ValueError):
            raise
        except sqlite3.Error as exc:
            raise JournalError("JOURNAL_TRANSITION_FAILED") from exc


    def record_intent(self, cycle_key, intent_id, *, updated_at_ms):
        """Persist the exact validated intent before PaperLedger can be constructed."""
        cycle_key = self._required_text(cycle_key, "cycle_key")
        intent_id = self._required_text(intent_id, "intent_id")
        updated_at_ms = self._timestamp(updated_at_ms)
        try:
            with closing(self._connect()) as connection:
                connection.execute("BEGIN IMMEDIATE")
                row = connection.execute(
                    """SELECT status,intent_id,updated_at_ms
                       FROM continuous_cycles WHERE cycle_key=?""",
                    (cycle_key,),
                ).fetchone()
                if row is None or row["status"] != "EXECUTING":
                    raise CycleConflict("CYCLE_NOT_EXECUTING")
                if updated_at_ms < row["updated_at_ms"]:
                    raise ValueError("JOURNAL_TIMESTAMP_REGRESSION")
                if row["intent_id"] is not None:
                    if row["intent_id"] != intent_id:
                        raise CycleConflict("CYCLE_INTENT_CONFLICT")
                    connection.commit()
                    return False
                connection.execute(
                    """UPDATE continuous_cycles
                       SET intent_id=?,updated_at_ms=?,state_version=state_version+1
                       WHERE cycle_key=? AND status='EXECUTING' AND intent_id IS NULL""",
                    (intent_id, updated_at_ms, cycle_key),
                )
                connection.commit()
                return True
        except (CycleConflict, ValueError):
            raise
        except sqlite3.Error as exc:
            raise JournalError("JOURNAL_INTENT_PERSIST_FAILED") from exc

    @staticmethod
    def _cycle_document(row):
        if row is None:
            return None
        return {
            "cycleKey": row["cycle_key"],
            "bundleId": row["bundle_id"],
            "bundleSha256": row["bundle_sha256"],
            "bundlePath": row["bundle_path"],
            "sourceSha": row["source_sha"],
            "configSha256": row["config_sha256"],
            "status": row["status"],
            "claimedAtMs": row["claimed_at_ms"],
            "updatedAtMs": row["updated_at_ms"],
            "stateVersion": row["state_version"],
            "runId": row["run_id"],
            "intentId": row["intent_id"],
            "orderId": row["order_id"],
            "terminalResult": row["terminal_result"],
        }


    @staticmethod
    def _checkpoint_identity(cycle_key):
        parts = cycle_key.split(":")
        if len(parts) != 6 or parts[3] != "15m" or parts[5] != "STRATEGY_CORE":
            raise ValueError("JOURNAL_CYCLE_KEY_INVALID")
        try:
            candle_open_ms = int(parts[4])
        except (TypeError, ValueError):
            raise ValueError("JOURNAL_CYCLE_KEY_INVALID") from None
        if candle_open_ms < 0:
            raise ValueError("JOURNAL_CYCLE_KEY_INVALID")
        stream_key = ":".join(parts[:4] + parts[5:])
        return stream_key, candle_open_ms

    def get_checkpoint(self, stream_key):
        stream_key = self._required_text(stream_key, "stream_key")
        try:
            with closing(self._connect()) as connection:
                row = connection.execute(
                    """SELECT stream_key,candle_open_ms,cycle_key,updated_at_ms
                       FROM continuous_checkpoints WHERE stream_key=?""",
                    (stream_key,),
                ).fetchone()
                if row is None:
                    return None
                return {
                    "streamKey": row["stream_key"],
                    "candleOpenTimeMs": row["candle_open_ms"],
                    "cycleKey": row["cycle_key"],
                    "updatedAtMs": row["updated_at_ms"],
                }
        except sqlite3.Error as exc:
            raise JournalError("JOURNAL_CHECKPOINT_READ_FAILED") from exc

    def get_cycle(self, cycle_key):
        cycle_key = self._required_text(cycle_key, "cycle_key")
        try:
            with closing(self._connect()) as connection:
                row = connection.execute(
                    "SELECT * FROM continuous_cycles WHERE cycle_key=?", (cycle_key,)
                ).fetchone()
                return self._cycle_document(row)
        except sqlite3.Error as exc:
            raise JournalError("JOURNAL_READ_FAILED") from exc

    def list_cycles(self):
        try:
            with closing(self._connect()) as connection:
                rows = connection.execute(
                    "SELECT * FROM continuous_cycles ORDER BY claimed_at_ms,cycle_key"
                ).fetchall()
                return [self._cycle_document(row) for row in rows]
        except sqlite3.Error as exc:
            raise JournalError("JOURNAL_READ_FAILED") from exc
