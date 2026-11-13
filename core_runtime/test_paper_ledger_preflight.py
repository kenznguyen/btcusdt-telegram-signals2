"""Read-only PaperLedger preflight contract for the Continuous Core P3 gate."""

import hashlib
import json
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core_runtime.paper_ledger_preflight import (
    PaperLedgerPreflightError,
    inspect_paper_ledger_preflight,
)
from paper_execution.test_core_first_operational import CoreFirstOperationalProofTest


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class PaperLedgerPreflightTest(unittest.TestCase):
    def setUp(self):
        self.fixture = CoreFirstOperationalProofTest(
            "test_core_signal_flows_through_shared_risk_into_paper_ledger"
        )
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.path = self.fixture.path
        self.now = self.fixture.now
        self.root = Path(self.fixture.temp.name)
        self.config = self.root / "paper-config.json"
        self.config.write_text(json.dumps({
            "mode": "PAPER",
            "ai_execution_enabled": False,
            "ledger_path": str(self.path),
        }), encoding="utf-8")
        self.env = {
            "AI_EXECUTION_ENABLED": "false",
            "MARKET_DATA_DB": "",
            "T0_FEEDER_LEASE_DB": "",
            "BINANCE_API_KEY": "",
            "BINANCE_API_SECRET": "",
            "OKX_API_KEY": "",
            "OKX_API_SECRET": "",
        }

    def test_ready_ledger_is_reported_without_database_byte_changes(self):
        before = digest(self.path)
        result = inspect_paper_ledger_preflight(
            self.config, now_ms=self.now, environ=self.env,
        )
        self.assertEqual(result["status"], "PAPER_LEDGER_READY")
        self.assertEqual(result["mode"], "PAPER")
        self.assertIs(result["liveTradingSupported"], False)
        self.assertIs(result["riskReady"], True)
        self.assertIs(result["killSwitch"]["killed"], False)
        self.assertIs(result["killSwitch"]["paused"], False)
        self.assertEqual(result["decisionCycle"], "NOT_RUN")
        self.assertEqual(result["persistentStateMutation"], "NONE")
        self.assertEqual(digest(self.path), before)

    def test_active_kill_switch_blocks_preflight_without_database_byte_changes(self):
        with sqlite3.connect(self.path) as db:
            db.execute(
                "UPDATE paper_risk_control SET killed=1,reason='TEST_KILL' WHERE id=1"
            )
        before = digest(self.path)
        with self.assertRaisesRegex(
            PaperLedgerPreflightError, "PAPER_KILL_SWITCH_ACTIVE"
        ):
            inspect_paper_ledger_preflight(
                self.config, now_ms=self.now, environ=self.env,
            )
        self.assertEqual(digest(self.path), before)

    def test_paused_ledger_blocks_preflight_without_database_byte_changes(self):
        with sqlite3.connect(self.path) as db:
            db.execute(
                "UPDATE paper_risk_control SET paused=1,reason='TEST_PAUSE' WHERE id=1"
            )
        before = digest(self.path)
        with self.assertRaisesRegex(
            PaperLedgerPreflightError, "PAPER_RISK_PAUSED"
        ):
            inspect_paper_ledger_preflight(
                self.config, now_ms=self.now, environ=self.env,
            )
        self.assertEqual(digest(self.path), before)

    def test_risk_not_ready_blocks_preflight_without_database_byte_changes(self):
        with sqlite3.connect(self.path) as db:
            db.execute(
                "UPDATE paper_account_risk_state SET risk_ready=0 WHERE account_id=1"
            )
        before = digest(self.path)
        with self.assertRaisesRegex(
            PaperLedgerPreflightError, "RISK_STATE_BLOCKED"
        ):
            inspect_paper_ledger_preflight(
                self.config, now_ms=self.now, environ=self.env,
            )
        self.assertEqual(digest(self.path), before)

    def test_missing_or_incomplete_ledger_fails_closed(self):
        path = self.root / "incomplete.sqlite3"
        with sqlite3.connect(path) as db:
            db.execute("CREATE TABLE disposable_probe(value TEXT)")
        config = self.root / "incomplete-config.json"
        config.write_text(json.dumps({
            "mode": "PAPER", "ai_execution_enabled": False,
            "ledger_path": str(path),
        }), encoding="utf-8")
        before = digest(path)
        with self.assertRaises(PaperLedgerPreflightError):
            inspect_paper_ledger_preflight(config, now_ms=self.now, environ=self.env)
        self.assertEqual(digest(path), before)

    def test_explicit_ai_disable_and_empty_exchange_credentials_are_required(self):
        env = dict(self.env)
        env["AI_EXECUTION_ENABLED"] = "true"
        with self.assertRaisesRegex(
            PaperLedgerPreflightError, "AI_EXECUTION_MUST_BE_EXPLICITLY_DISABLED"
        ):
            inspect_paper_ledger_preflight(
                self.config, now_ms=self.now, environ=env,
            )
        env = dict(self.env, BINANCE_API_KEY="present")
        with self.assertRaisesRegex(
            PaperLedgerPreflightError, "EXCHANGE_CREDENTIALS_FORBIDDEN"
        ):
            inspect_paper_ledger_preflight(
                self.config, now_ms=self.now, environ=env,
            )


if __name__ == "__main__":
    unittest.main()
