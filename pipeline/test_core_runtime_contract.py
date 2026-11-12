"""Black-box contract tests for the bounded Core paper one-shot runner.

The runner is intentionally not implemented in this increment. These tests
specify its CLI safety boundary without importing implementation internals.
"""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]


def isolated_env():
    env = os.environ.copy()
    for key in (
        "MARKET_DATA_DB", "T0_FEEDER_LEASE_DB", "PAPER_DB", "PAPER_TRADING_DB",
        "BINANCE_API_KEY", "BINANCE_API_SECRET", "OKX_API_KEY", "OKX_API_SECRET",
    ):
        env.pop(key, None)
    env["AI_EXECUTION_ENABLED"] = "false"
    return env


def run_core_runtime(*args):
    return subprocess.run(
        [sys.executable, "-m", "core_runtime", *map(str, args)],
        cwd=REPO_ROOT,
        env=isolated_env(),
        text=True,
        capture_output=True,
        timeout=10,
        check=False,
    )


class CoreRuntimeCliContractTest(unittest.TestCase):
    def test_help_is_available_without_starting_a_runtime_cycle(self):
        result = run_core_runtime("--help")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--config", result.stdout)

    def test_missing_config_is_rejected(self):
        result = run_core_runtime("--config", "missing-paper-config.json")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("CONFIG_NOT_FOUND", result.stderr)

    def test_live_mode_config_is_rejected_before_ledger_creation(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger = Path(directory) / "must-not-be-created.sqlite3"
            config = Path(directory) / "live.json"
            config.write_text(json.dumps({
                "mode": "LIVE",
                "ai_execution_enabled": False,
                "ledger_path": str(ledger),
            }), encoding="utf-8")

            result = run_core_runtime("--config", config)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("PAPER_MODE_REQUIRED", result.stderr)
            self.assertFalse(ledger.exists(), "invalid config must fail before opening SQLite")

    def test_ai_execution_enabled_config_is_rejected_before_ledger_creation(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger = Path(directory) / "must-not-be-created.sqlite3"
            config = Path(directory) / "ai-enabled.json"
            config.write_text(json.dumps({
                "mode": "PAPER",
                "ai_execution_enabled": True,
                "ledger_path": str(ledger),
            }), encoding="utf-8")

            result = run_core_runtime("--config", config)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("AI_EXECUTION_MUST_BE_DISABLED", result.stderr)
            self.assertFalse(ledger.exists(), "AI-enabled config must fail before opening SQLite")

    def test_missing_ledger_is_rejected_without_creating_sqlite_file(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger = Path(directory) / "missing-disposable-ledger.sqlite3"
            config = Path(directory) / "paper.json"
            config.write_text(json.dumps({
                "mode": "PAPER",
                "ai_execution_enabled": False,
                "ledger_path": str(ledger),
            }), encoding="utf-8")

            result = run_core_runtime("--config", config)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("LEDGER_FILE_REQUIRED", result.stderr)
            self.assertFalse(ledger.exists(), "preflight must reject absent ledger before SQLite open")


if __name__ == "__main__":
    unittest.main()
