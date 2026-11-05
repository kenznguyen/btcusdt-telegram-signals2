"""P2 acceptance tests for explicit PaperLedger initialization and writer isolation."""
import os
from pathlib import Path
import sqlite3
import tempfile
import unittest

from paper_execution.ledger import PaperLedger
from paper_execution.writer_gate import WriterAdmissionDenied


class PaperLedgerWriterIsolationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.paper_db = self.root / "paper" / "paper.sqlite3"
        self.market_db = self.root / "market" / "market.sqlite3"

    def tearDown(self):
        self.temp.cleanup()

    def test_constructor_does_not_create_parent_database_or_schema(self):
        ledger = PaperLedger(self.paper_db)
        self.assertFalse(self.paper_db.parent.exists())
        self.assertFalse(self.paper_db.exists())
        self.assertIsNone(getattr(ledger, "gate", None))

    def test_explicit_initialize_creates_paper_schema_and_gate(self):
        ledger = PaperLedger(self.paper_db)
        result = ledger.initialize()
        self.assertIs(result, ledger)
        self.assertTrue(self.paper_db.is_file())
        self.assertIsNotNone(ledger.gate)
        with sqlite3.connect(self.paper_db) as connection:
            self.assertIsNotNone(connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='paper_state'"
            ).fetchone())

    def test_rejects_same_path_as_market_data_database(self):
        with self.assertRaises(ValueError):
            PaperLedger(self.paper_db, market_data_db_path=self.paper_db)

    def test_rejects_symlink_alias_of_market_data_database(self):
        self.market_db.parent.mkdir(parents=True)
        self.market_db.touch()
        self.paper_db.parent.mkdir(parents=True)
        self.paper_db.symlink_to(self.market_db)
        with self.assertRaises(ValueError):
            PaperLedger(self.paper_db, market_data_db_path=self.market_db)

    def test_rejects_hardlink_alias_of_market_data_database(self):
        self.market_db.parent.mkdir(parents=True)
        self.market_db.touch()
        self.paper_db.parent.mkdir(parents=True)
        os.link(self.market_db, self.paper_db)
        with self.assertRaises(ValueError):
            PaperLedger(self.paper_db, market_data_db_path=self.market_db)

    def test_environment_market_data_path_is_also_protected(self):
        self.market_db.parent.mkdir(parents=True)
        self.market_db.touch()
        previous = os.environ.get("MARKET_DATA_DB")
        os.environ["MARKET_DATA_DB"] = str(self.market_db)
        try:
            with self.assertRaises(ValueError):
                PaperLedger(self.market_db)
        finally:
            if previous is None:
                os.environ.pop("MARKET_DATA_DB", None)
            else:
                os.environ["MARKET_DATA_DB"] = previous

    def test_all_mutation_entrypoints_are_denied_while_gate_is_draining(self):
        ledger = PaperLedger(self.paper_db).initialize()
        self.assertEqual(ledger.gate.begin_drain(timeout_seconds=1).state, "DRAINED")
        with self.assertRaises(WriterAdmissionDenied):
            ledger.set_paused(True, 1_800_000_000_000)
        with self.assertRaises(WriterAdmissionDenied):
            ledger.set_killed(True, 1_800_000_000_000)
        with self.assertRaises(WriterAdmissionDenied):
            ledger.reset_kill(True, True, 1_800_000_000_000)
        with self.assertRaises(WriterAdmissionDenied):
            ledger.record_equity("100000", 1_800_000_000_000, 1_800_000_000_001, "test")

    def test_read_only_snapshot_does_not_reopen_or_write_gate(self):
        ledger = PaperLedger(self.paper_db).initialize()
        ledger.gate.begin_drain(timeout_seconds=1)
        before = self.paper_db.stat().st_mtime_ns
        ledger.snapshot()
        self.assertEqual(ledger.gate.begin_drain(timeout_seconds=1).state, "DRAINED")
        self.assertEqual(self.paper_db.stat().st_mtime_ns, before)


    def test_submit_and_cancel_are_denied_without_writer_admission(self):
        ledger = PaperLedger(self.paper_db).initialize()
        ledger.gate.begin_drain(timeout_seconds=1)
        now = 1_800_000_000_000
        intent = {
            "intentId": "p2-denied-submit",
            "symbol": "BTCUSDT",
            "exchange": "binance",
            "marketType": "USDT_PERPETUAL",
            "strategyVersion": "test",
            "modelVersion": "test",
            "datasetVersion": "test",
            "targetPositionBase": "0.1",
            "limitPrice": "100",
            "decisionAtMs": now,
            "validUntilMs": now + 30_000,
            "inputSnapshotId": "p2-book",
            "mode": "PAPER",
        }
        book = {
            "source": "hummingbot",
            "connector": "binance_perpetual",
            "symbol": "BTCUSDT",
            "observedAtMs": now,
            "bids": [{"price": "99", "quantity": "1"}],
            "asks": [{"price": "100", "quantity": "1"}],
        }
        with self.assertRaises(WriterAdmissionDenied):
            ledger.submit(intent, book, now)
        with self.assertRaises(WriterAdmissionDenied):
            ledger.cancel("paper-order-that-does-not-exist", now)


    def test_market_data_path_is_revalidated_at_explicit_initialization(self):
        ledger = PaperLedger(self.paper_db)
        previous = os.environ.get("MARKET_DATA_DB")
        os.environ["MARKET_DATA_DB"] = str(self.paper_db)
        try:
            with self.assertRaises(ValueError):
                ledger.initialize()
            self.assertFalse(self.paper_db.exists())
        finally:
            if previous is None:
                os.environ.pop("MARKET_DATA_DB", None)
            else:
                os.environ["MARKET_DATA_DB"] = previous


if __name__ == "__main__":
    unittest.main(verbosity=2)
