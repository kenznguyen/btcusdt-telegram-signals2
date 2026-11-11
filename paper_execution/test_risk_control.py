import sqlite3
import tempfile
import unittest
from pathlib import Path

from paper_execution.risk_control import ensure, reset_kill, risk_block_reason, set_kill, set_paused, snapshot


class PersistentRiskControlTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "risk.sqlite3"
        self.now = 1_800_000_000_000

    def connect(self):
        return sqlite3.connect(self.path)

    def test_new_database_starts_unpaused_and_not_killed(self):
        with self.connect() as db:
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
                reset_kill(db, acknowledge=False, ready=True, at_ms=self.now+1)
            self.assertEqual(risk_block_reason(db), "KILL_SWITCH")
            reset_kill(db, acknowledge=True, ready=True, at_ms=self.now+2)
            self.assertIsNone(risk_block_reason(db))

    def test_pause_and_kill_are_independent_and_kill_has_priority(self):
        with self.connect() as db:
            ensure(db)
            set_paused(db, True, self.now)
            self.assertEqual(risk_block_reason(db), "RISK_PAUSED")
            set_kill(db, True, self.now+1)
            self.assertEqual(risk_block_reason(db), "KILL_SWITCH")
            reset_kill(db, True, True, self.now+2)
            self.assertEqual(risk_block_reason(db), "RISK_PAUSED")

    def test_generic_kill_clear_is_rejected(self):
        with self.connect() as db:
            ensure(db)
            with self.assertRaises(ValueError):
                set_kill(db, False, self.now)


if __name__ == "__main__":
    unittest.main()
