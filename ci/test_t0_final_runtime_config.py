"""Contract tests for the manual, read-only T0 runtime configuration audit."""

import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from ci.t0_final_runtime_config import audit_runtime_config, render_report


class FinalRuntimeConfigurationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.data_dir = self.root / ".data"
        self.data_dir.mkdir()
        self.db_path = self.data_dir / "btcusdt.sqlite3"
        self.env = {
            "MARKET_DATA_BACKEND": "sqlite",
            "MARKET_DATA_DB": str(self.db_path),
            "T0_FEEDER_LEASE_DB": str(self.db_path),
        }

    def tearDown(self):
        self.temp.cleanup()

    def test_valid_config_without_database_does_not_create_database(self):
        report = audit_runtime_config(self.env, repo_root=self.root)

        self.assertTrue(report["ok"], report)
        self.assertEqual(report["database"]["state"], "NOT_INITIALIZED")
        self.assertFalse(self.db_path.exists())
        self.assertIn("T0_FINAL_RUNTIME_CONFIGURATION=PASS", render_report(report))

    def test_rejects_lease_database_that_differs_from_canonical_database(self):
        other = self.data_dir / "lease.sqlite3"
        env = dict(self.env, T0_FEEDER_LEASE_DB=str(other))

        report = audit_runtime_config(env, repo_root=self.root)

        self.assertFalse(report["ok"])
        self.assertIn("same file", " ".join(report["errors"]))

    def test_rejects_non_sqlite_backend_for_production_feeder(self):
        report = audit_runtime_config(
            dict(self.env, MARKET_DATA_BACKEND="postgres"),
            repo_root=self.root,
        )

        self.assertFalse(report["ok"])
        self.assertTrue(any("SQLite" in error for error in report["errors"]))

    def test_rejects_invalid_numeric_feeder_configuration(self):
        report = audit_runtime_config(
            dict(self.env, T0_FEEDER_LEASE_HEARTBEAT_SECONDS="60"),
            repo_root=self.root,
        )

        self.assertFalse(report["ok"])
        self.assertFalse(report["checks"]["runtime_parameters"])\n        self.assertTrue(any("numeric settings" in error for error in report["errors"]))

    def test_existing_database_is_audited_read_only_and_requires_core_tables(self):
        with sqlite3.connect(self.db_path) as connection:
            connection.execute("CREATE TABLE candles (id INTEGER PRIMARY KEY)")
            connection.execute("""CREATE TABLE feeder_leases (
                lease_name TEXT PRIMARY KEY, owner TEXT, generation INTEGER NOT NULL,
                expires_at_ms INTEGER NOT NULL
            )""")
        before = self.db_path.read_bytes()

        report = audit_runtime_config(self.env, repo_root=self.root)

        self.assertTrue(report["ok"], report)
        self.assertEqual(report["database"]["state"], "EXISTING_SCHEMA_VALID")
        self.assertEqual(self.db_path.read_bytes(), before)

    def test_existing_database_missing_lease_table_fails_closed(self):
        with sqlite3.connect(self.db_path) as connection:
            connection.execute("CREATE TABLE candles (id INTEGER PRIMARY KEY)")

        report = audit_runtime_config(self.env, repo_root=self.root)

        self.assertFalse(report["ok"])
        self.assertTrue(any("feeder_leases" in error for error in report["errors"]))

    def test_report_never_contains_database_path_or_owner_identifier(self):
        secret_path = str(self.db_path)
        env = dict(self.env, T0_FEEDER_OWNER_ID="private-owner-identifier")

        report = audit_runtime_config(env, repo_root=self.root)
        rendered = render_report(report)

        self.assertNotIn(secret_path, rendered)
        self.assertNotIn("private-owner-identifier", rendered)
        self.assertEqual(json.loads(rendered)["ok"], report["ok"])


if __name__ == "__main__":
    unittest.main()
