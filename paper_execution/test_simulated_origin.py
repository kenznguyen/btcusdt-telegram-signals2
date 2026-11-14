import hashlib
import json
import sqlite3
import unittest

from paper_execution.simulated_capital import DEFAULT_SIMULATED_CAPITAL_CONTRACT
from paper_execution.simulated_origin import initialize_simulated_origin


class SimulatedOriginTest(unittest.TestCase):
    def setUp(self):
        self.connection = sqlite3.connect(":memory:")
        self.connection.execute(
            "CREATE TABLE paper_accounts (account_id INTEGER PRIMARY KEY)"
        )
        self.connection.execute("INSERT INTO paper_accounts VALUES (1)")
        self.contract_bytes = (
            json.dumps(DEFAULT_SIMULATED_CAPITAL_CONTRACT, separators=(",", ":"))
            .encode("utf-8")
        )

    def tearDown(self):
        self.connection.close()

    def initialize(self, contract_bytes=None, account_id=1):
        return initialize_simulated_origin(
            self.connection,
            contract_bytes=self.contract_bytes if contract_bytes is None else contract_bytes,
            initialized_at_ms=1_800_000_000_000,
            account_id=account_id,
        )

    def test_creates_distinct_immutable_origin_and_seed_not_funding(self):
        result = self.initialize()

        self.assertEqual(result["initialCapitalQuote"], "100")
        self.assertEqual(result["contractSha256"], hashlib.sha256(self.contract_bytes).hexdigest())
        self.assertEqual(result["source"], "OWNER_APPROVED_SIMULATION")
        self.assertEqual(
            self.connection.execute("SELECT COUNT(*) FROM paper_simulated_capital_origin").fetchone()[0],
            1,
        )
        self.assertEqual(
            self.connection.execute("SELECT COUNT(*) FROM paper_simulated_capital_seed_events").fetchone()[0],
            1,
        )
        tables = {
            row[0] for row in self.connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        self.assertNotIn("paper_funding_events", tables)

    def test_duplicate_initialization_is_idempotent_without_second_seed(self):
        first = self.initialize()
        second = initialize_simulated_origin(
            self.connection,
            contract_bytes=self.contract_bytes,
            initialized_at_ms=1_800_000_100_000,
            account_id=1,
        )

        self.assertEqual(first, second)
        self.assertEqual(second["initializedAtMs"], 1_800_000_000_000)
        self.assertEqual(
            self.connection.execute("SELECT COUNT(*) FROM paper_simulated_capital_seed_events").fetchone()[0],
            1,
        )

    def test_restart_with_different_exact_contract_bytes_fails_closed(self):
        self.initialize()
        changed_bytes = json.dumps(
            DEFAULT_SIMULATED_CAPITAL_CONTRACT, indent=2
        ).encode("utf-8")

        with self.assertRaisesRegex(ValueError, "SIMULATED_ORIGIN_CONTRACT_MISMATCH"):
            self.initialize(changed_bytes)

        self.assertEqual(
            self.connection.execute("SELECT COUNT(*) FROM paper_simulated_capital_seed_events").fetchone()[0],
            1,
        )

    def test_origin_and_seed_rows_reject_update_and_delete(self):
        self.initialize()
        with self.assertRaisesRegex(sqlite3.IntegrityError, "SIMULATED_ORIGIN_IMMUTABLE"):
            self.connection.execute(
                "UPDATE paper_simulated_capital_origin SET initial_capital_quote='200' WHERE account_id=1"
            )
        with self.assertRaisesRegex(sqlite3.IntegrityError, "SIMULATED_ORIGIN_IMMUTABLE"):
            self.connection.execute("DELETE FROM paper_simulated_capital_origin WHERE account_id=1")
        with self.assertRaisesRegex(sqlite3.IntegrityError, "SIMULATED_SEED_IMMUTABLE"):
            self.connection.execute(
                "UPDATE paper_simulated_capital_seed_events SET amount_quote='200'"
            )
        with self.assertRaisesRegex(sqlite3.IntegrityError, "SIMULATED_SEED_IMMUTABLE"):
            self.connection.execute("DELETE FROM paper_simulated_capital_seed_events")

    def test_missing_account_fails_without_creating_origin(self):
        with self.assertRaisesRegex(ValueError, "SIMULATED_ORIGIN_ACCOUNT_MISSING"):
            self.initialize(account_id=99)

        tables = {
            row[0] for row in self.connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        self.assertNotIn("paper_simulated_capital_origin", tables)

    def test_invalid_contract_fails_without_creating_origin(self):
        invalid = json.dumps({**DEFAULT_SIMULATED_CAPITAL_CONTRACT, "autoTopUp": True}).encode()

        with self.assertRaisesRegex(ValueError, "SIMULATED_CAPITAL_CAPITAL_MUTATION_FORBIDDEN"):
            self.initialize(invalid)

        tables = {
            row[0] for row in self.connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        self.assertNotIn("paper_simulated_capital_origin", tables)


if __name__ == "__main__":
    unittest.main()
