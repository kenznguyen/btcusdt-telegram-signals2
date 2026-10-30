"""Persistence invariants: no duplicate DCA, crash recovery, no cross-trade leakage."""
import os
import tempfile
import unittest
from quant_engine.dca_state import DcaStore, StateConflict


class DcaStateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmp.name, "dca.sqlite3")

    def tearDown(self):
        self.tmp.cleanup()

    def test_one_dca_per_trade_even_after_restart(self):
        with DcaStore(self.path) as store:
            self.assertTrue(store.reserve_once("BTCUSDT", "trade-1", "m15:100"))
            self.assertFalse(store.reserve_once("BTCUSDT", "trade-1", "m15:100"))
        with DcaStore(self.path) as restarted:
            self.assertFalse(restarted.reserve_once("BTCUSDT", "trade-1", "m15:101"))
            self.assertEqual(restarted.read("BTCUSDT", "trade-1")["status"], "RESERVED")

    def test_different_trade_can_reserve(self):
        with DcaStore(self.path) as store:
            self.assertTrue(store.reserve_once("BTCUSDT", "trade-1", "m15:100"))
            self.assertTrue(store.reserve_once("BTCUSDT", "trade-2", "m15:100"))

    def test_unknown_trade_or_candle_is_rejected(self):
        with DcaStore(self.path) as store:
            for t, c in [("", "a"), ("t", ""), (" ", "a")]:
                with self.assertRaises(ValueError):
                    store.reserve_once("BTCUSDT", t, c)

    def test_explicit_confirmation_idempotent_and_conflicts_closed(self):
        with DcaStore(self.path) as store:
            store.reserve_once("BTCUSDT", "trade-1", "m15:100")
            self.assertTrue(store.confirm_fill("BTCUSDT", "trade-1", "fill-100"))
            self.assertFalse(store.confirm_fill("BTCUSDT", "trade-1", "fill-100"))
            with self.assertRaises(StateConflict):
                store.confirm_fill("BTCUSDT", "trade-1", "different-fill")
            self.assertFalse(store.reserve_once("BTCUSDT", "trade-1", "m15:101"))

    def test_no_confirmation_without_reservation(self):
        with DcaStore(self.path) as store:
            with self.assertRaises(StateConflict):
                store.confirm_fill("BTCUSDT", "t", "fill-1")

    def test_nonexistent_storage_directory_does_not_fallback_to_memory(self):
        with self.assertRaises(Exception):
            DcaStore(os.path.join(self.tmp.name, "missing", "db.sqlite"))


if __name__ == "__main__":
    unittest.main()
