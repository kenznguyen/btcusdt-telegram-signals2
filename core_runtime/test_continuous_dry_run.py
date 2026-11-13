"""No-side-effect static dry-run contracts for the Continuous Core Runner."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from core_runtime.continuous_dry_run import (
    ContinuousDryRunError,
    inspect_continuous_dry_run,
)


class ContinuousDryRunTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.ledger = self.root / "paper-ledger.sqlite3"
        self.ledger.write_bytes(b"disposable placeholder; must not be opened")
        self.config = self.root / "paper-config.json"
        self.config.write_text(
            """{"mode":"PAPER","ai_execution_enabled":false,"ledger_path":"paper-ledger.sqlite3","risk_limits":{"maxDrawdownPct":"10","maxDailyLossUsdt":"10","maxExposureUsdt":"100"},"max_book_age_ms":2000,"max_position_base":"0.01"}""",
            encoding="utf-8",
        )
        self.journal = self.root / "runner-state" / "journal.sqlite3"
        self.bundle_store = self.root / "runner-state" / "bundles"
        self.runner_parent = self.journal.parent
        self.runner_parent.mkdir()
        self.env = {
            "AI_EXECUTION_ENABLED": "false",
            "MARKET_DATA_DB": "",
            "T0_FEEDER_LEASE_DB": "",
            "BINANCE_API_KEY": "",
            "BINANCE_API_SECRET": "",
            "OKX_API_KEY": "",
            "OKX_API_SECRET": "",
        }

    def test_valid_static_dry_run_does_not_create_or_modify_runner_state(self):
        before = sorted(str(path.relative_to(self.root)) for path in self.root.rglob("*"))
        ledger_before = self.ledger.read_bytes()

        result = inspect_continuous_dry_run(
            self.config,
            journal_path=self.journal,
            bundle_store_dir=self.bundle_store,
            environ=self.env,
        )

        after = sorted(str(path.relative_to(self.root)) for path in self.root.rglob("*"))
        self.assertEqual(result["status"], "DRY_RUN_CONFIG_VALIDATED")
        self.assertEqual(result["decisionCycle"], "NOT_RUN")
        self.assertEqual(result["ledgerContentsVerified"], False)
        self.assertEqual(result["journalCreated"], False)
        self.assertEqual(result["bundleStoreCreated"], False)
        self.assertEqual(result["oneShotInvoked"], False)
        self.assertEqual(before, after)
        self.assertEqual(self.ledger.read_bytes(), ledger_before)

    def test_dry_run_requires_explicit_ai_execution_false(self):
        env = dict(self.env)
        env.pop("AI_EXECUTION_ENABLED")
        with self.assertRaisesRegex(ContinuousDryRunError, "AI_EXECUTION_MUST_BE_EXPLICITLY_DISABLED"):
            inspect_continuous_dry_run(
                self.config, journal_path=self.journal,
                bundle_store_dir=self.bundle_store, environ=env,
            )

    def test_dry_run_rejects_exchange_credentials(self):
        env = dict(self.env, BINANCE_API_KEY="present")
        with self.assertRaisesRegex(ContinuousDryRunError, "EXCHANGE_CREDENTIALS_FORBIDDEN"):
            inspect_continuous_dry_run(
                self.config, journal_path=self.journal,
                bundle_store_dir=self.bundle_store, environ=env,
            )

    def test_dry_run_rejects_journal_alias_to_t0_database(self):
        env = dict(self.env, MARKET_DATA_DB=str(self.ledger))
        with self.assertRaisesRegex(ContinuousDryRunError, "RUNNER_PATH_OVERLAPS_PROTECTED_DATA"):
            inspect_continuous_dry_run(
                self.config, journal_path=self.ledger,
                bundle_store_dir=self.bundle_store, environ=env,
            )

    def test_dry_run_rejects_lease_database_alias(self):
        lease = self.root / "t0-lease.sqlite3"
        lease.write_bytes(b"protected")
        env = dict(self.env, T0_FEEDER_LEASE_DB=str(lease))
        with self.assertRaisesRegex(ContinuousDryRunError, "RUNNER_PATH_OVERLAPS_PROTECTED_DATA"):
            inspect_continuous_dry_run(
                self.config, journal_path=lease,
                bundle_store_dir=self.bundle_store, environ=env,
            )

    def test_dry_run_rejects_runner_paths_that_overlap_ledger(self):
        with self.assertRaisesRegex(ContinuousDryRunError, "RUNNER_PATH_OVERLAPS_PROTECTED_DATA"):
            inspect_continuous_dry_run(
                self.config, journal_path=self.ledger,
                bundle_store_dir=self.bundle_store, environ=self.env,
            )

    def test_dry_run_rejects_missing_parent_without_creating_it(self):
        missing = self.root / "must-not-be-created"
        with self.assertRaisesRegex(ContinuousDryRunError, "RUNNER_PATH_PARENT_REQUIRED"):
            inspect_continuous_dry_run(
                self.config, journal_path=missing / "journal.sqlite3",
                bundle_store_dir=missing / "bundles", environ=self.env,
            )
        self.assertFalse(missing.exists())

    def test_cli_static_dry_run_does_not_create_runner_state(self):
        env = dict(os.environ)
        for key in (
            "MARKET_DATA_DB", "T0_FEEDER_LEASE_DB",
            "BINANCE_API_KEY", "BINANCE_API_SECRET",
            "OKX_API_KEY", "OKX_API_SECRET",
        ):
            env.pop(key, None)
        env["AI_EXECUTION_ENABLED"] = "false"
        before = sorted(str(path.relative_to(self.root)) for path in self.root.rglob("*"))
        result = subprocess.run(
            [
                sys.executable, "-m", "core_runtime",
                "--config", str(self.config),
                "--dry-run",
                "--journal-path", str(self.journal),
                "--bundle-store-dir", str(self.bundle_store),
            ],
            cwd=Path(__file__).resolve().parents[1],
            env=env, text=True, capture_output=True, timeout=10, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "DRY_RUN_CONFIG_VALIDATED")
        self.assertFalse(payload["ledgerContentsRead"])
        self.assertEqual(payload["persistentStateMutation"], "NONE")
        after = sorted(str(path.relative_to(self.root)) for path in self.root.rglob("*"))
        self.assertEqual(before, after)

    def test_dry_run_rejects_base_config_without_runner_policy(self):
        base = self.root / "base.json"
        base.write_text(
            """{"mode":"PAPER","ai_execution_enabled":false,"ledger_path":"paper-ledger.sqlite3"}""",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(ContinuousDryRunError, "RUNNER_CONFIG_REQUIRED"):
            inspect_continuous_dry_run(
                base, journal_path=self.journal,
                bundle_store_dir=self.bundle_store, environ=self.env,
            )


if __name__ == "__main__":
    unittest.main()
