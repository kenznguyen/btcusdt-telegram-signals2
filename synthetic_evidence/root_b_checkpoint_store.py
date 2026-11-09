"""Synthetic-only SQLite durability model for Root B checkpoint crash testing.

This adapter is deliberately isolated from production/runtime code. It uses only
caller-supplied temporary file paths and never discovers or opens application DBs.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Literal


class RootBIntegrityError(ValueError):
    """Persisted event, ACK, observer configuration, or checkpoint is invalid."""


class SimulatedCrash(RuntimeError):
    """A deterministic crash injected at a test-only transaction boundary."""


AppendCrashPoint = Literal["before_commit"]
CheckpointCrashPoint = Literal["after_durable_write", "after_ack"]


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")


class DurableRootBJournal:
    """File-backed SQLite model. Not a production storage or recovery adapter."""

    def __init__(self, database_path: str | Path, *, required_observers: set[str]):
        if str(database_path) == ":memory:":
            raise ValueError("durable test adapter requires a file-backed SQLite path")
        if not required_observers or any(
            not isinstance(item, str) or not item for item in required_observers
        ):
            raise ValueError("required_observers must contain non-empty observer IDs")
        self.path = Path(database_path).expanduser().resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._required_observers = frozenset(required_observers)
        self._connection = sqlite3.connect(
            str(self.path), timeout=5.0, isolation_level=None
        )
        self._connection.execute("PRAGMA foreign_keys=ON")
        self._connection.execute("PRAGMA synchronous=FULL")
        self._connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS events (
                sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT NOT NULL UNIQUE,
                event_bytes BLOB NOT NULL
            );
            CREATE TABLE IF NOT EXISTS acknowledgements (
                event_id TEXT NOT NULL REFERENCES events(event_id),
                observer_id TEXT NOT NULL,
                event_sha256 TEXT NOT NULL,
                PRIMARY KEY (event_id, observer_id)
            );
            CREATE TABLE IF NOT EXISTS checkpoints (
                checkpoint_id TEXT PRIMARY KEY,
                through_sequence INTEGER NOT NULL,
                event_log_sha256 TEXT NOT NULL,
                acknowledgement_sha256 TEXT NOT NULL,
                checkpoint_sha256 TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS checkpoint_acks (
                checkpoint_id TEXT PRIMARY KEY REFERENCES checkpoints(checkpoint_id)
            );
            """
        )
        configured = json.dumps(sorted(self._required_observers), separators=(",", ":"))
        row = self._connection.execute(
            "SELECT value FROM metadata WHERE key='required_observers'"
        ).fetchone()
        if row is None:
            self._connection.execute(
                "INSERT INTO metadata(key, value) VALUES('required_observers', ?)",
                (configured,),
            )
        elif row[0] != configured:
            self.close()
            raise RootBIntegrityError("required observer configuration changed across reopen")

    def close(self) -> None:
        connection = getattr(self, "_connection", None)
        if connection is not None:
            connection.close()
            self._connection = None

    def __enter__(self) -> "DurableRootBJournal":
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        self.close()

    def _begin(self) -> None:
        self._connection.execute("BEGIN IMMEDIATE")

    def _rollback_if_open(self) -> None:
        if self._connection is not None and self._connection.in_transaction:
            self._connection.rollback()

    def event_count(self) -> int:
        return int(self._connection.execute("SELECT COUNT(*) FROM events").fetchone()[0])

    def append_event(
        self,
        event_id: str,
        canonical_event_bytes: bytes,
        *,
        crash_at: AppendCrashPoint | None = None,
    ) -> str:
        if not isinstance(event_id, str) or not event_id:
            raise RootBIntegrityError("event_id must be a non-empty string")
        if not isinstance(canonical_event_bytes, bytes) or not canonical_event_bytes:
            raise RootBIntegrityError("event bytes must be non-empty bytes")
        if crash_at not in (None, "before_commit"):
            raise RootBIntegrityError("unknown append crash injection point")
        self._begin()
        try:
            existing = self._connection.execute(
                "SELECT event_bytes FROM events WHERE event_id=?", (event_id,)
            ).fetchone()
            if existing is not None:
                if bytes(existing[0]) != canonical_event_bytes:
                    raise RootBIntegrityError("same event ID appended with changed bytes")
                self._connection.commit()
                return "EVENT_DUPLICATE"
            self._connection.execute(
                "INSERT INTO events(event_id, event_bytes) VALUES(?, ?)",
                (event_id, sqlite3.Binary(canonical_event_bytes)),
            )
            if crash_at == "before_commit":
                raise SimulatedCrash("crash before event transaction commit")
            self._connection.commit()
            return "EVENT_APPENDED"
        except SimulatedCrash:
            # Leave the transaction open so the subprocess test can terminate
            # without cleanup; SQLite must recover the uncommitted journal.
            raise
        except BaseException:
            self._rollback_if_open()
            raise

    def event_digest(self, event_id: str) -> str:
        row = self._connection.execute(
            "SELECT event_bytes FROM events WHERE event_id=?", (event_id,)
        ).fetchone()
        if row is None:
            raise RootBIntegrityError("acknowledgement references unknown event")
        return _sha256(bytes(row[0]))

    def acknowledge(self, event_id: str, observer_id: str, event_digest: str) -> str:
        if observer_id not in self._required_observers:
            raise RootBIntegrityError("acknowledgement references unknown observer")
        expected = self.event_digest(event_id)
        if event_digest != expected:
            raise RootBIntegrityError("observer acknowledgement digest does not match event")
        self._begin()
        try:
            row = self._connection.execute(
                "SELECT event_sha256 FROM acknowledgements "
                "WHERE event_id=? AND observer_id=?",
                (event_id, observer_id),
            ).fetchone()
            if row is not None:
                if row[0] != event_digest:
                    raise RootBIntegrityError("duplicate observer ACK changed digest")
                self._connection.commit()
                return "ACK_DUPLICATE"
            self._connection.execute(
                "INSERT INTO acknowledgements(event_id, observer_id, event_sha256) "
                "VALUES(?, ?, ?)",
                (event_id, observer_id, event_digest),
            )
            self._connection.commit()
            return "ACK_RECORDED"
        except BaseException:
            self._rollback_if_open()
            raise

    def _event_log_digest(self, through_sequence: int) -> str:
        rows = self._connection.execute(
            "SELECT sequence, event_id, event_bytes FROM events "
            "WHERE sequence<=? ORDER BY sequence",
            (through_sequence,),
        ).fetchall()
        if len(rows) != through_sequence or any(
            int(row[0]) != index for index, row in enumerate(rows, 1)
        ):
            raise RootBIntegrityError("checkpoint sequence is not a contiguous event prefix")
        payload = [
            {"sequence": int(sequence), "event_id": event_id,
             "event_sha256": _sha256(bytes(event_bytes))}
            for sequence, event_id, event_bytes in rows
        ]
        return _sha256(_canonical(payload))

    def _acknowledgement_digest(self, through_sequence: int) -> str:
        events = self._connection.execute(
            "SELECT sequence, event_id FROM events WHERE sequence<=? ORDER BY sequence",
            (through_sequence,),
        ).fetchall()
        if len(events) != through_sequence:
            raise RootBIntegrityError("checkpoint sequence is not a contiguous event prefix")
        payload = []
        for sequence, event_id in events:
            rows = self._connection.execute(
                "SELECT observer_id, event_sha256 FROM acknowledgements "
                "WHERE event_id=? ORDER BY observer_id",
                (event_id,),
            ).fetchall()
            acknowledgements = {observer: digest for observer, digest in rows}
            if set(acknowledgements) != self._required_observers:
                raise RootBIntegrityError(
                    "checkpoint includes an event without all required observer ACKs"
                )
            payload.append({
                "sequence": int(sequence),
                "event_id": event_id,
                "observers": [
                    {"observer_id": observer, "event_sha256": acknowledgements[observer]}
                    for observer in sorted(self._required_observers)
                ],
            })
        return _sha256(_canonical(payload))

    @staticmethod
    def _checkpoint_digest(
        checkpoint_id: str,
        through_sequence: int,
        event_log_sha256: str,
        acknowledgement_sha256: str,
    ) -> str:
        return _sha256(_canonical({
            "checkpoint_id": checkpoint_id,
            "through_sequence": through_sequence,
            "event_log_sha256": event_log_sha256,
            "acknowledgement_sha256": acknowledgement_sha256,
        }))

    def commit_checkpoint(
        self,
        checkpoint_id: str,
        *,
        through_sequence: int,
        crash_at: CheckpointCrashPoint | None = None,
    ) -> str:
        if not isinstance(checkpoint_id, str) or not checkpoint_id:
            raise RootBIntegrityError("checkpoint_id must be a non-empty string")
        if not isinstance(through_sequence, int) or isinstance(through_sequence, bool):
            raise RootBIntegrityError("checkpoint sequence must be an integer")
        if not 1 <= through_sequence <= self.event_count():
            raise RootBIntegrityError("checkpoint sequence is outside the committed event log")
        if crash_at not in (None, "after_durable_write", "after_ack"):
            raise RootBIntegrityError("unknown checkpoint crash injection point")

        event_digest = self._event_log_digest(through_sequence)
        ack_digest = self._acknowledgement_digest(through_sequence)
        checkpoint_digest = self._checkpoint_digest(
            checkpoint_id, through_sequence, event_digest, ack_digest
        )
        candidate = (through_sequence, event_digest, ack_digest, checkpoint_digest)

        self._begin()
        try:
            existing = self._connection.execute(
                "SELECT through_sequence, event_log_sha256, acknowledgement_sha256, "
                "checkpoint_sha256 FROM checkpoints WHERE checkpoint_id=?",
                (checkpoint_id,),
            ).fetchone()
            if existing is not None:
                if tuple(existing) != candidate:
                    raise RootBIntegrityError("checkpoint ID reused with different contents")
                acknowledged = self._connection.execute(
                    "SELECT 1 FROM checkpoint_acks WHERE checkpoint_id=?",
                    (checkpoint_id,),
                ).fetchone() is not None
                if acknowledged:
                    self._connection.commit()
                    return "CHECKPOINT_ALREADY_COMMITTED"
                self._connection.commit()
            else:
                self._connection.execute(
                    "INSERT INTO checkpoints(checkpoint_id, through_sequence, "
                    "event_log_sha256, acknowledgement_sha256, checkpoint_sha256) "
                    "VALUES(?, ?, ?, ?, ?)",
                    (checkpoint_id, *candidate),
                )
                self._connection.commit()
        except BaseException:
            self._rollback_if_open()
            raise

        if crash_at == "after_durable_write":
            raise SimulatedCrash("crash after durable checkpoint commit and before ACK")

        self._begin()
        try:
            self._connection.execute(
                "INSERT OR IGNORE INTO checkpoint_acks(checkpoint_id) VALUES(?)",
                (checkpoint_id,),
            )
            self._connection.commit()
        except BaseException:
            self._rollback_if_open()
            raise

        if crash_at == "after_ack":
            raise SimulatedCrash("crash after checkpoint ACK commit")
        return "CHECKPOINT_ACK_REPLAYED" if existing is not None else "CHECKPOINT_COMMITTED"

    def checkpoint_ack_count(self, checkpoint_id: str) -> int:
        row = self._connection.execute(
            "SELECT COUNT(*) FROM checkpoint_acks WHERE checkpoint_id=?",
            (checkpoint_id,),
        ).fetchone()
        return int(row[0])

    def recover_checkpoint(self) -> dict[str, object] | None:
        rows = self._connection.execute(
            "SELECT checkpoint_id, through_sequence, event_log_sha256, "
            "acknowledgement_sha256, checkpoint_sha256 FROM checkpoints "
            "ORDER BY through_sequence, checkpoint_id"
        ).fetchall()
        if not rows:
            return None
        latest = None
        for checkpoint_id, sequence, stored_event, stored_ack, stored_digest in rows:
            sequence = int(sequence)
            if not 1 <= sequence <= self.event_count():
                raise RootBIntegrityError("stored checkpoint sequence is outside event log")
            event_digest = self._event_log_digest(sequence)
            ack_digest = self._acknowledgement_digest(sequence)
            expected = self._checkpoint_digest(
                checkpoint_id, sequence, event_digest, ack_digest
            )
            if (stored_event, stored_ack, stored_digest) != (
                event_digest, ack_digest, expected
            ):
                raise RootBIntegrityError(
                    "stored checkpoint failed recovery integrity verification"
                )
            latest = {
                "checkpoint_id": checkpoint_id,
                "through_sequence": sequence,
                "event_log_sha256": stored_event,
                "acknowledgement_sha256": stored_ack,
                "checkpoint_sha256": stored_digest,
            }
        return latest
