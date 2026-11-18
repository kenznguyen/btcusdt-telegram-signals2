import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from paper_execution import kill_reset_service
from paper_execution.kill_reset_service import _issue_kill_reset_evidence
from paper_execution.risk_control import (ensure, reset_kill, risk_block_reason, set_kill, set_paused, snapshot)


class PersistentRiskControlTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "risk.sqlite3"
        self.key_path = Path(self.temp.name) / "kill-reset-signing.key"
        self.key_path.write_bytes(b"test-only-kill-reset-signing-key-32-bytes")
        self.key_path.chmod(0o600)
        self.key_patch = patch.object(kill_reset_service, "KILL_RESET_SIGNING_KEY_PATH", self.key_path)
        self.key_patch.start()
        self.addCleanup(self.key_patch.stop)
        self.now = 1_800_000_000_000

    def connect(self):
        return sqlite3.connect(self.path)

    def readiness(self, checked_at_ms):
        return _issue_kill_reset_evidence(
            checked_at_ms=checked_at_ms,
            checks={"closedCandles": True, "orderBook": True,
                    "noPendingPaperOrders": True, "accountRiskReady": True},
            candle_evidence={"datasetVersion": "sha256:"+"a"*64,
                             "closeTimeMs": checked_at_ms-900_000,
                             "availableAtMs": checked_at_ms-1_000},
            book_evidence={"snapshotDigest": "sha256:"+"b"*64,
                           "observedAtMs": checked_at_ms-100},
        )

    def test_new_database_starts_unpaused_and_not_killed(self):
        with self.connect() as db:
            ensure(db)
            self.assertIsNone(risk_block_reason(db))
            self.assertEqual(snapshot(db)["mode"], "PAPER")

    def test_kill_latch_persists_and_blocks_until_acknowledged_ready_reset(self):
        with self.connect() as db:
            ensure(db)
            set_kill(db, True, self.now, "DAILY_LOSS_LIMIT")
            self.assertEqual(risk_block_reason(db), "KILL_SWITCH")
        with self.connect() as db:
            self.assertTrue(snapshot(db)["killed"])
            with self.assertRaises(ValueError):
                reset_kill(db, acknowledge=False, readiness_evidence=self.readiness(self.now+1), at_ms=self.now+1)
            with self.assertRaises(ValueError):
                reset_kill(db, acknowledge=True, readiness_evidence={"ready": True}, at_ms=self.now+1)
            self.assertEqual(risk_block_reason(db), "KILL_SWITCH")
            evidence = self.readiness(self.now+2)
            reset_kill(db, acknowledge=True, readiness_evidence=evidence, at_ms=self.now+2)
            self.assertIsNone(risk_block_reason(db))
            with self.assertRaises(ValueError):
                reset_kill(db, acknowledge=True, readiness_evidence=evidence, at_ms=self.now+3)

    def test_stale_readiness_evidence_cannot_clear_kill_latch(self):
        with self.connect() as db:
            ensure(db)
            set_kill(db, True, self.now, "TEST_KILL")
            evidence = self.readiness(self.now+1)
            with self.assertRaisesRegex(ValueError, "server-issued readiness evidence"):
                reset_kill(db, True, evidence, self.now+5_002)
            self.assertEqual(risk_block_reason(db), "KILL_SWITCH")

    def test_pause_and_kill_are_independent_and_kill_has_priority(self):
        with self.connect() as db:
            ensure(db)
            set_paused(db, True, self.now)
            self.assertEqual(risk_block_reason(db), "RISK_PAUSED")
            set_kill(db, True, self.now+1)
            self.assertEqual(risk_block_reason(db), "KILL_SWITCH")
            reset_kill(db, True, self.readiness(self.now+2), self.now+2)
            self.assertEqual(risk_block_reason(db), "RISK_PAUSED")

    def test_generic_kill_clear_is_rejected(self):
        with self.connect() as db:
            ensure(db)
            with self.assertRaises(ValueError):
                set_kill(db, False, self.now)


    def test_missing_singleton_row_fails_closed(self):
        with self.connect() as db:
            ensure(db)
            db.execute("DELETE FROM paper_risk_control WHERE id=1")
            with self.assertRaisesRegex(sqlite3.DatabaseError, "RISK_CONTROL_STATE_MISSING"):
                risk_block_reason(db)

    def test_corrupt_latch_flags_fail_closed(self):
        with self.connect() as db:
            ensure(db)
            db.execute("PRAGMA ignore_check_constraints=ON")
            db.execute("UPDATE paper_risk_control SET killed=2 WHERE id=1")
            with self.assertRaisesRegex(sqlite3.DatabaseError, "RISK_CONTROL_STATE_CORRUPT"):
                risk_block_reason(db)
            with self.assertRaisesRegex(sqlite3.DatabaseError, "RISK_CONTROL_STATE_CORRUPT"):
                snapshot(db)


    def test_read_only_snapshot_fails_closed_when_kill_state_is_missing(self):
        with self.connect() as db:
            with self.assertRaisesRegex(sqlite3.DatabaseError, "RISK_CONTROL_STATE_MISSING"):
                snapshot(db)


if __name__ == "__main__":
    unittest.main()
