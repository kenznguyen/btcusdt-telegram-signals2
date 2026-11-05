"""Process-safe, Paper-only writer admission and drain gate.

The gate uses a durable SQLite coordinator plus an OS lock held for the
lifetime of each admitted writer. It never opens or creates the Paper data DB
during initialization or admission.
"""
from contextlib import contextmanager
from dataclasses import dataclass
import os
import platform
import sqlite3
import time
from pathlib import Path
import secrets
import sys
from typing import Iterator


_ALLOWED_SETTLEMENTS = {
    "ABORTED/NOT_STARTED",
    "COMPLETED",
    "FAILED_ROLLED_BACK",
}


class WriterGateError(RuntimeError):
    """Base class for fail-closed writer-gate errors."""


class WriterAdmissionDenied(WriterGateError):
    """The gate is not OPEN or the requested path is not the configured Paper DB."""


class WriterTokenInvalid(WriterGateError):
    """A token is foreign, released, stale, or absent from coordinator state."""


class WriterLockTimeout(WriterGateError):
    """An OS lock could not be acquired within the requested timeout."""


@dataclass(frozen=True)
class DrainResult:
    state: str


class _OSLock:
    """One OS lock handle; POSIX supports shared writers, Windows serializes them."""

    def __init__(self, path: Path, *, exclusive: bool, timeout_seconds: float):
        self.path = path
        self.exclusive = exclusive
        self.timeout_seconds = timeout_seconds
        self.fd = None

    def acquire(self):
        system = platform.system()
        if system not in {"Linux", "Darwin", "Windows"}:
            raise WriterGateError("No verified writer-lock adapter for this platform")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.fd = os.open(self.path, os.O_CREAT | os.O_RDWR, 0o600)
        deadline = time.monotonic() + self.timeout_seconds
        try:
            if system in {"Linux", "Darwin"}:
                import fcntl

                operation = fcntl.LOCK_EX if self.exclusive else fcntl.LOCK_SH
                while True:
                    try:
                        fcntl.flock(self.fd, operation | fcntl.LOCK_NB)
                        return self
                    except BlockingIOError:
                        if time.monotonic() >= deadline:
                            raise WriterLockTimeout("Timed out acquiring Paper writer lock")
                        time.sleep(min(0.01, max(0, deadline - time.monotonic())))
            else:
                import msvcrt

                if os.fstat(self.fd).st_size == 0:
                    os.write(self.fd, b"0")
                while True:
                    try:
                        os.lseek(self.fd, 0, os.SEEK_SET)
                        msvcrt.locking(self.fd, msvcrt.LK_NBLCK, 1)
                        return self
                    except OSError:
                        if time.monotonic() >= deadline:
                            raise WriterLockTimeout("Timed out acquiring Paper writer lock")
                        time.sleep(min(0.01, max(0, deadline - time.monotonic())))
        except BaseException:
            self.close()
            raise

    def close(self):
        if self.fd is None:
            return
        fd, self.fd = self.fd, None
        try:
            system = platform.system()
            if system == "Windows":
                import msvcrt

                os.lseek(fd, 0, os.SEEK_SET)
                try:
                    msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
                except OSError:
                    pass
            elif system in {"Linux", "Darwin"}:
                import fcntl

                fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            os.close(fd)


class WriterToken:
    """Opaque, process-local capability. The held OS lock is intentionally unpicklable."""

    __slots__ = ("_gate_id", "_generation", "_token_id", "_scope", "_lock", "_released")

    def __init__(self, gate_id, generation, token_id, lock):
        self._gate_id = gate_id
        self._generation = generation
        self._token_id = token_id
        self._scope = "paper_only"
        self._lock = lock
        self._released = False

    @property
    def generation(self):
        return self._generation

    def __reduce__(self):
        raise TypeError("Paper writer tokens cannot be serialized or transferred")


class PaperWriterGate:
    """Durable cross-process writer gate scoped exclusively to one PAPER_DB."""

    def __init__(self, paper_db_path: str):
        self.paper_db_path = Path(paper_db_path).expanduser().resolve()
        self.coordinator_path = self.paper_db_path.with_name(
            self.paper_db_path.name + ".writer-gate.sqlite3"
        )
        self.lock_path = self.paper_db_path.with_name(
            self.paper_db_path.name + ".writer-gate.lock"
        )
        self._gate_id = None

    @classmethod
    def initialize(cls, *, paper_db_path: str) -> "PaperWriterGate":
        if not isinstance(paper_db_path, (str, os.PathLike)) or not str(paper_db_path).strip():
            raise ValueError("An explicit PAPER_DB path is required")
        if platform.system() not in {"Linux", "Darwin", "Windows"}:
            raise WriterGateError("No verified writer-lock adapter for this platform")
        gate = cls(str(paper_db_path))
        gate.coordinator_path.parent.mkdir(parents=True, exist_ok=True)
        with gate._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                """CREATE TABLE IF NOT EXISTS paper_writer_gate_state (
                    singleton INTEGER PRIMARY KEY CHECK(singleton=1),
                    gate_id TEXT NOT NULL,
                    state TEXT NOT NULL CHECK(state IN ('OPEN','DRAINING','DRAINED')),
                    generation INTEGER NOT NULL CHECK(generation > 0),
                    updated_at_ms INTEGER NOT NULL
                )"""
            )
            connection.execute(
                """CREATE TABLE IF NOT EXISTS paper_writer_gate_tokens (
                    token_id TEXT PRIMARY KEY,
                    gate_id TEXT NOT NULL,
                    generation INTEGER NOT NULL,
                    scope TEXT NOT NULL CHECK(scope='paper_only'),
                    pid INTEGER NOT NULL,
                    admitted_at_ms INTEGER NOT NULL
                )"""
            )
            row = connection.execute(
                "SELECT gate_id,state,generation FROM paper_writer_gate_state WHERE singleton=1"
            ).fetchone()
            if row is None:
                gate_id = secrets.token_hex(16)
                connection.execute(
                    "INSERT INTO paper_writer_gate_state VALUES (1,?,'OPEN',1,?)",
                    (gate_id, time.time_ns() // 1_000_000),
                )
                gate._gate_id = gate_id
            else:
                gate._gate_id = row[0]
            connection.commit()
        return gate

    def _connect(self):
        connection = sqlite3.connect(self.coordinator_path, timeout=10)
        connection.execute("PRAGMA busy_timeout=10000")
        return connection

    def _state(self, connection):
        row = connection.execute(
            "SELECT gate_id,state,generation FROM paper_writer_gate_state WHERE singleton=1"
        ).fetchone()
        if row is None or row[0] != self._gate_id:
            raise WriterGateError("Paper writer coordinator identity is invalid")
        return row[1], row[2]

    def _lock(self, *, exclusive: bool, timeout_seconds: float):
        if type(timeout_seconds) not in (int, float) or timeout_seconds < 0:
            raise ValueError("timeout_seconds must be non-negative")
        return _OSLock(
            self.lock_path, exclusive=exclusive, timeout_seconds=float(timeout_seconds)
        ).acquire()

    def admit_writer(self, *, timeout_seconds: float = 10.0) -> WriterToken:
        lock = self._lock(exclusive=False, timeout_seconds=timeout_seconds)
        try:
            with self._connect() as connection:
                connection.execute("BEGIN IMMEDIATE")
                state, generation = self._state(connection)
                if state != "OPEN":
                    connection.rollback()
                    raise WriterAdmissionDenied("Paper writer admission is closed")
                token_id = secrets.token_hex(24)
                connection.execute(
                    """INSERT INTO paper_writer_gate_tokens
                       (token_id,gate_id,generation,scope,pid,admitted_at_ms)
                       VALUES (?,?,?,?,?,?)""",
                    (
                        token_id, self._gate_id, generation, "paper_only",
                        os.getpid(), time.time_ns() // 1_000_000,
                    ),
                )
                connection.commit()
            return WriterToken(self._gate_id, generation, token_id, lock)
        except BaseException:
            lock.close()
            raise

    def validate_writer_token(self, token: WriterToken) -> None:
        if (
            not isinstance(token, WriterToken)
            or token._gate_id != self._gate_id
            or token._scope != "paper_only"
            or token._released
        ):
            raise WriterTokenInvalid("Paper writer token is invalid")
        with self._connect() as connection:
            state, generation = self._state(connection)
            if token._generation != generation or state not in {"OPEN", "DRAINING"}:
                raise WriterTokenInvalid("Paper writer token generation is stale")
            row = connection.execute(
                """SELECT 1 FROM paper_writer_gate_tokens
                   WHERE token_id=? AND gate_id=? AND generation=? AND scope='paper_only'""",
                (token._token_id, self._gate_id, token._generation),
            ).fetchone()
            if row is None:
                raise WriterTokenInvalid("Paper writer token is not active")

    def release_writer(self, token: WriterToken) -> bool:
        if not isinstance(token, WriterToken) or token._gate_id != self._gate_id:
            raise WriterTokenInvalid("Cannot release a foreign Paper writer token")
        if token._released:
            return False
        removed = False
        try:
            with self._connect() as connection:
                connection.execute("BEGIN IMMEDIATE")
                cursor = connection.execute(
                    """DELETE FROM paper_writer_gate_tokens
                       WHERE token_id=? AND gate_id=? AND generation=? AND scope='paper_only'""",
                    (token._token_id, self._gate_id, token._generation),
                )
                removed = cursor.rowcount == 1
                connection.commit()
            return removed
        finally:
            token._released = True
            token._lock.close()

    def _complete_drain(self, timeout_seconds: float) -> DrainResult:
        lock = self._lock(exclusive=True, timeout_seconds=timeout_seconds)
        try:
            with self._connect() as connection:
                connection.execute("BEGIN IMMEDIATE")
                state, _ = self._state(connection)
                if state == "OPEN":
                    raise WriterGateError("Drain state was unexpectedly reopened")
                # Exclusive OS lock proves no admitted writer retains its lock.
                connection.execute("DELETE FROM paper_writer_gate_tokens WHERE gate_id=?", (self._gate_id,))
                connection.execute(
                    "UPDATE paper_writer_gate_state SET state='DRAINED',updated_at_ms=? WHERE singleton=1",
                    (time.time_ns() // 1_000_000,),
                )
                connection.commit()
            return DrainResult("DRAINED")
        finally:
            lock.close()

    def begin_drain(self, *, timeout_seconds: float) -> DrainResult:
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            state, _ = self._state(connection)
            if state == "OPEN":
                connection.execute(
                    "UPDATE paper_writer_gate_state SET state='DRAINING',updated_at_ms=? WHERE singleton=1",
                    (time.time_ns() // 1_000_000,),
                )
            connection.commit()
        if state == "DRAINED":
            return DrainResult("DRAINED")
        try:
            return self._complete_drain(timeout_seconds)
        except WriterLockTimeout:
            return DrainResult("DRAIN_TIMEOUT")

    def wait_for_drain(self, *, timeout_seconds: float) -> DrainResult:
        with self._connect() as connection:
            state, _ = self._state(connection)
        if state == "OPEN":
            raise WriterGateError("Cannot wait for a drain that has not started")
        if state == "DRAINED":
            return DrainResult("DRAINED")
        try:
            return self._complete_drain(timeout_seconds)
        except WriterLockTimeout:
            return DrainResult("DRAIN_TIMEOUT")

    def reopen(self, *, authorized: bool, settled_outcome: str) -> None:
        if authorized is not True or settled_outcome not in _ALLOWED_SETTLEMENTS:
            raise WriterGateError("Explicit authorization and a settled outcome are required")
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            state, generation = self._state(connection)
            active = connection.execute(
                "SELECT COUNT(*) FROM paper_writer_gate_tokens WHERE gate_id=?",
                (self._gate_id,),
            ).fetchone()[0]
            if state != "DRAINED" or active != 0:
                connection.rollback()
                raise WriterGateError("Reopen requires DRAINED and zero active writer tokens")
            connection.execute(
                """UPDATE paper_writer_gate_state
                   SET state='OPEN',generation=?,updated_at_ms=? WHERE singleton=1""",
                (generation + 1, time.time_ns() // 1_000_000),
            )
            connection.commit()

    @contextmanager
    def writer_transaction(self, *, paper_db_path: str) -> Iterator[sqlite3.Connection]:
        requested = Path(paper_db_path).expanduser().resolve()
        if requested != self.paper_db_path:
            raise WriterAdmissionDenied("Writer transaction path does not match configured PAPER_DB")
        token = self.admit_writer()
        connection = None
        try:
            if not self.paper_db_path.is_file():
                raise FileNotFoundError("PAPER_DB must be explicitly initialized before writing")
            uri = self.paper_db_path.as_uri() + "?mode=rw"
            connection = sqlite3.connect(uri, uri=True, timeout=10)
            connection.execute("BEGIN IMMEDIATE")
            self.validate_writer_token(token)
            yield connection
            self.validate_writer_token(token)
            connection.commit()
        except BaseException:
            if connection is not None:
                connection.rollback()
            raise
        finally:
            if connection is not None:
                connection.close()
            self.release_writer(token)
