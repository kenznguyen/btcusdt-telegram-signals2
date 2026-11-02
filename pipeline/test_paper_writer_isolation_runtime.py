"""Runtime contracts for pipeline Paper budget writes and DB isolation.

Only temporary SQLite files are used. No canonical path, exchange or credentials.
"""
import inspect
import sqlite3
import tempfile
import unittest
from pathlib import Path

from pipeline.api import control_permit

try:
    from paper_execution.writer_gate import PaperWriterGate, WriterGateError
except ModuleNotFoundError as exc:
    if exc.name != "paper_execution.writer_gate":
        raise
    PaperWriterGate = WriterGateError = None


class PipelinePaperWriterIsolationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.t0_db = root / "t0.sqlite3"
        self.paper_db = root / "paper.sqlite3"
        with sqlite3.connect(str(self.t0_db)) as db:
            db.execute("CREATE TABLE candles (open_time_ms INTEGER PRIMARY KEY)")
            db.execute("INSERT INTO candles VALUES (123)")
        self.gate = PaperWriterGate(scope="paper_only") if PaperWriterGate else None

    def tearDown(self):
        self.temp.cleanup()

    def tables(self, path):
        if not path.exists():
            return set()
        with sqlite3.connect(str(path)) as db:
            return {row[0] for row in db.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )}

    def test_pipeline_control_permit_contract_is_present(self):
        self.assertIsNotNone(PaperWriterGate,
            "CONTRACT RED: PaperWriterGate module/API is not implemented")
        parameters = inspect.signature(control_permit).parameters
        self.assertIn("writer_gate", parameters,
            "CONTRACT RED: control_permit must require PaperWriterGate")
        self.assertIn("paper_db_path", parameters,
            "CONTRACT RED: control_permit must receive the isolated PAPER_DB path")

    @unittest.skipIf(PaperWriterGate is None, "Paper Writer Gate absent; explicit contract RED covers this")
    def test_control_permit_fails_closed_when_gate_is_drained_without_db_mutation(self):
        self.gate.begin_drain(timeout_seconds=0.1)
        before_t0 = self.tables(self.t0_db)
        with self.assertRaises(WriterGateError):
            control_permit(1_800_000_000_000, writer_gate=self.gate,
                           paper_db_path=str(self.paper_db))
        self.assertFalse(self.paper_db.exists(),
            "A denied writer must not create/open the Paper DB")
        self.assertEqual(self.tables(self.t0_db), before_t0)
        self.assertEqual(self.tables(self.paper_db), set())

    @unittest.skipIf(PaperWriterGate is None, "Paper Writer Gate absent; explicit contract RED covers this")
    def test_open_gate_writes_budget_only_to_paper_db(self):
        permitted = control_permit(1_800_000_000_000, writer_gate=self.gate,
                                   paper_db_path=str(self.paper_db))
        self.assertTrue(permitted)
        self.assertIn("paper_control_budget", self.tables(self.paper_db))
        self.assertEqual(self.tables(self.t0_db), {"candles"})
        with sqlite3.connect(str(self.paper_db)) as db:
            used = db.execute(
                "SELECT used FROM paper_control_budget WHERE minute=?",
                (1_800_000_000_000 // 60_000,),
            ).fetchone()[0]
        self.assertEqual(used, 1)

    @unittest.skipIf(PaperWriterGate is None, "Paper Writer Gate absent; explicit contract RED covers this")
    def test_control_permit_requires_explicit_paper_path_and_never_falls_back_to_t0(self):
        with self.assertRaises((TypeError, ValueError)):
            control_permit(1_800_000_000_000, writer_gate=self.gate,
                           paper_db_path="")
        self.assertEqual(self.tables(self.t0_db), {"candles"})
        self.assertFalse(self.paper_db.exists())


if __name__ == "__main__":
    unittest.main()
