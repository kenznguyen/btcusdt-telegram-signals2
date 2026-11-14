"""Read-only and fail-closed contract tests for account-wide risk snapshots."""

import hashlib
import sqlite3
import tempfile
import unittest
from pathlib import Path

from paper_execution.ledger import read_account_risk_snapshot
from paper_execution.test_core_first_operational import CoreFirstOperationalProofTest


def database_digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class AccountRiskSnapshotReadOnlyTest(unittest.TestCase):
    def setUp(self):
        self.fixture = CoreFirstOperationalProofTest(
            "test_core_signal_flows_through_shared_risk_into_paper_ledger"
        )
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.path = self.fixture.path
        self.now = self.fixture.now

    def test_ready_account_snapshot_is_returned_without_changing_database_bytes(self):
        before = database_digest(self.path)

        snapshot = read_account_risk_snapshot(self.path, now_ms=self.now)

        after = database_digest(self.path)
        self.assertTrue(snapshot["riskReady"], snapshot)
        self.assertEqual(snapshot["mode"], "PAPER")
        self.assertIs(snapshot["liveTradingSupported"], False)
        self.assertEqual(snapshot["accountEquityQuote"], "1400")
        self.assertEqual(after, before, "read-only risk snapshot must not mutate database bytes")

    def test_incomplete_existing_database_fails_closed_without_initialization_or_mutation(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "incomplete.sqlite3"
            with sqlite3.connect(path) as connection:
                connection.execute("CREATE TABLE disposable_probe (value TEXT)")
            before = database_digest(path)

            with self.assertRaises(sqlite3.DatabaseError) as raised:
                read_account_risk_snapshot(path, now_ms=self.now)
            self.assertIn("paper_schema_migrations", str(raised.exception))

            self.assertEqual(database_digest(path), before)
            with sqlite3.connect(f"file:{path}?mode=ro", uri=True) as connection:
                tables = {
                    row[0] for row in connection.execute(
                        "SELECT name FROM sqlite_master WHERE type='table'"
                    )
                }
            self.assertEqual(tables, {"disposable_probe"})

    def test_corrupt_account_risk_state_fails_closed_without_further_mutation(self):
        with sqlite3.connect(self.path) as connection:
            connection.execute("PRAGMA ignore_check_constraints=ON")
            connection.execute(
                "UPDATE paper_account_risk_state SET risk_ready=7 WHERE account_id=1"
            )
        before = database_digest(self.path)

        with self.assertRaisesRegex(
            sqlite3.DatabaseError, "ACCOUNT_RISK_STATE_MISSING_OR_CORRUPT"
        ):
            read_account_risk_snapshot(self.path, now_ms=self.now)

        self.assertEqual(database_digest(self.path), before)


if __name__ == "__main__":
    unittest.main()
