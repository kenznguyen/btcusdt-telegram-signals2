"""Contracts keeping Common API paper state separate from canonical T0 storage."""

import os
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from pipeline import api


class PaperStorageIsolationTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.t0 = self.root / "t0-market.sqlite3"
        self.paper = self.root / "paper.sqlite3"
        with sqlite3.connect(self.t0) as connection:
            connection.execute("CREATE TABLE canonical_candles (id INTEGER PRIMARY KEY)")

    def configured(self, **overrides):
        values = {
            "MARKET_DATA_BACKEND": "sqlite",
            "MARKET_DATA_DB": str(self.t0),
            "PAPER_DB": str(self.paper),
            "PAPER_MAX_DRAWDOWN_PCT": "95",
            "PAPER_MAX_DAILY_LOSS_USDT": "95",
            "PAPER_MAX_EXPOSURE_USDT": "1000",
        }
        values.update(overrides)
        return patch.dict(os.environ, values, clear=True)

    def test_paper_database_requires_an_explicit_independent_path(self):
        with self.configured(PAPER_DB=""):
            with self.assertRaisesRegex(ValueError, "PAPER_DB_REQUIRED"):
                api.paper_db_path()

    def test_paper_database_rejects_the_exact_t0_path(self):
        with self.configured(PAPER_DB=str(self.t0)):
            with self.assertRaisesRegex(ValueError, "PAPER_DB_MUST_BE_SEPARATE_FROM_T0"):
                api.paper_db_path()

    def test_paper_database_rejects_a_symlink_alias_of_t0(self):
        alias = self.root / "paper-alias.sqlite3"
        alias.symlink_to(self.t0)
        with self.configured(PAPER_DB=str(alias)):
            with self.assertRaisesRegex(ValueError, "PAPER_DB_MUST_BE_SEPARATE_FROM_T0"):
                api.paper_db_path()

    def test_paper_database_resolves_to_the_separate_configured_file(self):
        with self.configured():
            self.assertEqual(Path(api.paper_db_path()), self.paper.resolve())

    def test_control_budget_is_written_only_to_the_paper_database(self):
        self.paper.touch()
        with self.configured():
            self.assertTrue(api.control_permit(60_000))
        with sqlite3.connect(self.t0) as connection:
            tables = {row[0] for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )}
        with sqlite3.connect(self.paper) as connection:
            paper_tables = {row[0] for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )}
        self.assertIn("canonical_candles", tables)
        self.assertNotIn("paper_control_budget", tables)
        self.assertIn("paper_control_budget", paper_tables)

    def test_ledger_constructor_receives_only_the_paper_database_path(self):
        with self.configured():
            with patch("paper_execution.ledger.PaperLedger") as constructor:
                api.ledger()
        self.assertEqual(Path(constructor.call_args.args[0]), self.paper.resolve())


if __name__ == "__main__":
    unittest.main()
