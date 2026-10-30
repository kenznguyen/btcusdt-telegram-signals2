"""Unbound crash recovery must never create a new intent or retry an order."""
import os
import sqlite3
import tempfile
import unittest
from quant_engine.dca_state import DcaStore, StateConflict

class UnboundRecoveryTests(unittest.TestCase):
    def test_reservation_without_intent_is_blocked_after_restart(self):
        with tempfile.TemporaryDirectory() as folder:
            path=os.path.join(folder,"dca.sqlite")
            with DcaStore(path) as store:
                self.assertTrue(store.reserve_once("BTCUSDT","trade-1","candle-1"))
            with DcaStore(path) as rebooted:
                status=rebooted.recovery_status("BTCUSDT","trade-1")
                self.assertEqual(status["status"],"RESERVED_UNBOUND")
                self.assertTrue(status["manual_review_required"])
                self.assertFalse(status["may_submit"])
                self.assertFalse(rebooted.reserve_once("BTCUSDT","trade-1","candle-2"))
                with self.assertRaises(StateConflict):
                    rebooted.reconcile_paper_fill("BTCUSDT","trade-1",os.path.join(folder,"paper.sqlite"))
                self.assertEqual(rebooted.recovery_status("BTCUSDT","trade-1"),status)
                self.assertEqual(rebooted.db.execute("SELECT COUNT(*) FROM dca_intent_binding").fetchone()[0],0)

    def test_bound_unconfirmed_reservation_also_blocks_new_submission(self):
        with tempfile.TemporaryDirectory() as folder:
            path=os.path.join(folder,"dca.sqlite")
            with DcaStore(path) as store:
                store.reserve_once("BTCUSDT","t","c")
                store.bind_paper_intent("BTCUSDT","t","paper-intent-1","LONG")
            with DcaStore(path) as recovered:
                s=recovered.recovery_status("BTCUSDT","t")
                self.assertEqual(s["status"],"RESERVED_BOUND")
                self.assertFalse(s["may_submit"])
                self.assertTrue(s["manual_review_required"])

    def test_unknown_trade_is_not_treated_as_safe_to_submit(self):
        with tempfile.TemporaryDirectory() as folder:
            with DcaStore(os.path.join(folder,"dca.sqlite")) as store:
                self.assertEqual(store.recovery_status("BTCUSDT","missing")["status"],"UNKNOWN")
                self.assertFalse(store.recovery_status("BTCUSDT","missing")["may_submit"])

if __name__=="__main__":
    unittest.main()
