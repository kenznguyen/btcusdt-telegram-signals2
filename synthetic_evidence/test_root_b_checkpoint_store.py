"""Durable Root B checkpoint adapter tests; synthetic-only, temporary SQLite files."""
from __future__ import annotations

import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from synthetic_evidence.root_b_checkpoint_store import (
    DurableRootBJournal,
    RootBIntegrityError,
    SimulatedCrash,
)


class DurableRootBCheckpointTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="p1-8-18-root-b-")
        self.addCleanup(self.temp.cleanup)
        self.db = Path(self.temp.name) / "journal.sqlite3"
        self.observers = {"observer-a", "observer-b"}
        self.journal = DurableRootBJournal(self.db, required_observers=self.observers)

    def _seed(self, journal=None):
        journal = journal or self.journal
        journal.append_event("evt-1", b'{"event_id":"evt-1","value":1}')
        journal.append_event("evt-2", b'{"event_id":"evt-2","value":2}')
        for event_id in ("evt-1", "evt-2"):
            digest = journal.event_digest(event_id)
            journal.acknowledge(event_id, "observer-a", digest)
            journal.acknowledge(event_id, "observer-b", digest)

    def _crash_child(self, script: str, expected_exit: int = 73):
        env = dict(os.environ)
        env["PYTHONPATH"] = str(Path.cwd()) + os.pathsep + env.get("PYTHONPATH", "")
        result = subprocess.run(
            [sys.executable, "-c", script, str(self.db)],
            cwd=Path.cwd(),
            env=env,
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
        self.assertEqual(result.returncode, expected_exit, result.stderr)

    def test_database_is_file_backed_and_integrity_check_passes(self):
        self._seed()
        self.journal.close()
        reopened = DurableRootBJournal(self.db, required_observers=self.observers)
        self.addCleanup(reopened.close)
        with sqlite3.connect(self.db) as con:
            self.assertEqual(con.execute("PRAGMA integrity_check").fetchone()[0], "ok")
        self.assertEqual(reopened.event_count(), 2)

    def test_process_death_before_event_transaction_commit_rolls_back_event(self):
        script = """
import os, sys
from synthetic_evidence.root_b_checkpoint_store import DurableRootBJournal, SimulatedCrash
j = DurableRootBJournal(sys.argv[1], required_observers={"observer-a", "observer-b"})
try:
    j.append_event("crash-event", b'{"event_id":"crash-event"}', crash_at="before_commit")
except SimulatedCrash:
    os._exit(73)
os._exit(74)
"""
        self._crash_child(script)
        reopened = DurableRootBJournal(self.db, required_observers=self.observers)
        self.addCleanup(reopened.close)
        self.assertEqual(reopened.event_count(), 0)

    def test_process_death_after_checkpoint_commit_before_ack_recovers_checkpoint(self):
        self._seed()
        self.journal.close()
        script = """
import os, sys
from synthetic_evidence.root_b_checkpoint_store import DurableRootBJournal, SimulatedCrash
j = DurableRootBJournal(sys.argv[1], required_observers={"observer-a", "observer-b"})
try:
    j.commit_checkpoint("cp-1", through_sequence=2, crash_at="after_durable_write")
except SimulatedCrash:
    os._exit(73)
os._exit(74)
"""
        self._crash_child(script)
        reopened = DurableRootBJournal(self.db, required_observers=self.observers)
        self.addCleanup(reopened.close)
        recovered = reopened.recover_checkpoint()
        self.assertEqual(recovered["checkpoint_id"], "cp-1")
        self.assertEqual(recovered["through_sequence"], 2)
        self.assertEqual(reopened.checkpoint_ack_count("cp-1"), 0)
        self.assertEqual(
            reopened.commit_checkpoint("cp-1", through_sequence=2),
            "CHECKPOINT_ACK_REPLAYED",
        )
        self.assertEqual(reopened.checkpoint_ack_count("cp-1"), 1)

    def test_process_death_after_checkpoint_ack_is_idempotent_after_reopen(self):
        self._seed()
        self.journal.close()
        script = """
import os, sys
from synthetic_evidence.root_b_checkpoint_store import DurableRootBJournal, SimulatedCrash
j = DurableRootBJournal(sys.argv[1], required_observers={"observer-a", "observer-b"})
try:
    j.commit_checkpoint("cp-acked", through_sequence=2, crash_at="after_ack")
except SimulatedCrash:
    os._exit(73)
os._exit(74)
"""
        self._crash_child(script)
        reopened = DurableRootBJournal(self.db, required_observers=self.observers)
        self.addCleanup(reopened.close)
        self.assertEqual(reopened.checkpoint_ack_count("cp-acked"), 1)
        self.assertEqual(
            reopened.commit_checkpoint("cp-acked", through_sequence=2),
            "CHECKPOINT_ALREADY_COMMITTED",
        )
        self.assertEqual(reopened.checkpoint_ack_count("cp-acked"), 1)

    def test_checkpoint_rejects_incomplete_observer_quorum(self):
        self.journal.append_event("evt-1", b'{"event_id":"evt-1"}')
        digest = self.journal.event_digest("evt-1")
        self.journal.acknowledge("evt-1", "observer-a", digest)
        with self.assertRaises(RootBIntegrityError):
            self.journal.commit_checkpoint("cp-incomplete", through_sequence=1)
        self.assertIsNone(self.journal.recover_checkpoint())

    def test_recovery_fails_closed_when_persisted_event_bytes_are_corrupted(self):
        self._seed()
        self.journal.commit_checkpoint("cp-1", through_sequence=2)
        self.journal.close()
        with sqlite3.connect(self.db) as con:
            con.execute(
                "UPDATE events SET event_bytes=? WHERE event_id=?",
                (b'{"event_id":"evt-1","value":999}', "evt-1"),
            )
        reopened = DurableRootBJournal(self.db, required_observers=self.observers)
        self.addCleanup(reopened.close)
        with self.assertRaises(RootBIntegrityError):
            reopened.recover_checkpoint()

    def test_reopen_rejects_changed_required_observer_configuration(self):
        self.journal.close()
        with self.assertRaises(RootBIntegrityError):
            DurableRootBJournal(self.db, required_observers={"observer-a"})

    def test_memory_database_is_rejected(self):
        with self.assertRaises(ValueError):
            DurableRootBJournal(":memory:", required_observers=self.observers)


if __name__ == "__main__":
    unittest.main()
