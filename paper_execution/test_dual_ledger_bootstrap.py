"""TDD contract for the isolated Dual Ledger bootstrap CLI."""

import hashlib
import json
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from paper_execution.bootstrap import (
    bootstrap_paper_account,
    inspect_paper_account,
)
from paper_execution.ledger import read_account_risk_snapshot, dual_ledger_ready
from risk_policy import CORE_LEVERAGE


class DualLedgerBootstrapContractTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.now = 1_800_000_000_000
        self.source_sha = "a" * 40
        self.environment = patch.dict(os.environ, {
            "AI_EXECUTION_ENABLED": "false",
            "BINANCE_API_KEY": "",
            "BINANCE_API_SECRET": "",
            "OKX_API_KEY": "",
            "OKX_API_SECRET": "",
        })
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self.funding_evidence = self.root / "funding-evidence.json"
        self.cutover_evidence = self.root / "equity-cutover-evidence.json"
        self.funding_evidence.write_text(
            json.dumps({"snapshotId": "owner-funding-001", "coverage": "verified"}),
            encoding="utf-8",
        )
        self.cutover_evidence.write_text(
            json.dumps({"snapshotId": "owner-equity-001", "equityQuote": "100"}),
            encoding="utf-8",
        )
        self.manifest = {
            "schemaVersion": 1,
            "mode": "PAPER",
            "sourceSha": self.source_sha,
            "initialCapitalQuote": "100",
            "maxPositionBase": "0.01",
            "riskLimits": {
                "maxDrawdownPct": "50",
                "maxDailyLossUsdt": "50",
                "maxExposureUsdt": "1000",
            },
            "aiLeverage": "3",
            "markPrice": "100",
            "markCandleCloseMs": self.now - 60_000,
            "markObservedAtMs": self.now,
            "datasetVersion": "sha256:" + "1" * 64,
            "fundingCoverageStartAtMs": self.now - 86_400_000,
            "fundingCoverageId": "bootstrap-funding-coverage-001",
            "fundingSource": "OWNER_RECONCILED_EVIDENCE",
            "fundingSnapshotId": "owner-funding-001",
            "fundingEvidencePath": str(self.funding_evidence),
            "fundingPayloadHash": "sha256:" + hashlib.sha256(
                self.funding_evidence.read_bytes()
            ).hexdigest(),
            "cutoverId": "bootstrap-equity-cutover-001",
            "cutoverSource": "OWNER_RECONCILED_EVIDENCE",
            "cutoverSnapshotId": "owner-equity-001",
            "cutoverEvidencePath": str(self.cutover_evidence),
            "cutoverPayloadHash": "sha256:" + hashlib.sha256(
                self.cutover_evidence.read_bytes()
            ).hexdigest(),
            "configVersion": "paper-risk-v1",
            "recordedAtMs": self.now,
        }
        self.db_path = self.root / "paper" / "account.sqlite3"
        self.db_path.parent.mkdir()

    def test_bootstrap_creates_three_scopes_and_ready_only_after_reconciliation(self):
        result = bootstrap_paper_account(self.db_path, self.manifest)

        self.assertTrue(self.db_path.is_file())
        self.assertEqual(result["mode"], "PAPER")
        self.assertFalse(result["liveTradingSupported"])
        self.assertTrue(result["riskReady"])
        self.assertEqual(result["strategyScopes"], [
            "AI_FREQAI", "LEGACY_UNATTRIBUTED", "STRATEGY_CORE"
        ])
        self.assertEqual(result["coreLeverage"], str(CORE_LEVERAGE))
        self.assertEqual(result["aiLeverage"], "3")
        self.assertTrue(dual_ledger_ready(self.db_path))

        with sqlite3.connect(self.db_path) as db:
            rows = db.execute(
                "SELECT strategy_id FROM paper_strategy_ledgers "
                "WHERE account_id=1 ORDER BY strategy_id"
            ).fetchall()
            self.assertEqual(
                [row[0] for row in rows],
                ["AI_FREQAI", "LEGACY_UNATTRIBUTED", "STRATEGY_CORE"],
            )
            ready = db.execute(
                "SELECT risk_ready FROM paper_account_risk_state WHERE account_id=1"
            ).fetchone()
            self.assertEqual(ready, (1,))

        snapshot = read_account_risk_snapshot(self.db_path, now_ms=self.now)
        self.assertTrue(snapshot["riskReady"])
        self.assertEqual(snapshot["accountEquityQuote"], "100")

    def test_invalid_evidence_digest_fails_without_creating_database(self):
        bad = dict(self.manifest)
        bad["fundingPayloadHash"] = "sha256:" + "0" * 64

        with self.assertRaisesRegex(ValueError, "EVIDENCE_DIGEST_MISMATCH"):
            bootstrap_paper_account(self.db_path, bad)

        self.assertFalse(self.db_path.exists())
        self.assertEqual(list(self.db_path.parent.iterdir()), [])

    def test_invalid_manifest_shape_fails_without_creating_database(self):
        bad = dict(self.manifest)
        bad["unrecognized"] = "must be rejected"

        with self.assertRaisesRegex(ValueError, "BOOTSTRAP_MANIFEST_FIELDS_INVALID"):
            bootstrap_paper_account(self.db_path, bad)

        self.assertFalse(self.db_path.exists())

    def test_existing_database_is_never_migrated_or_modified(self):
        self.db_path.write_bytes(b"existing-user-data")
        before = self.db_path.read_bytes()

        with self.assertRaisesRegex(ValueError, "BOOTSTRAP_TARGET_ALREADY_EXISTS"):
            bootstrap_paper_account(self.db_path, self.manifest)

        self.assertEqual(self.db_path.read_bytes(), before)

    def test_target_cannot_alias_t0_database_or_lease_paths(self):
        t0_db = self.root / "t0.sqlite3"
        lease_db = self.root / "lease.sqlite3"
        with patch.dict(os.environ, {
            "MARKET_DATA_DB": str(t0_db),
            "T0_FEEDER_LEASE_DB": str(lease_db),
        }):
            with self.assertRaisesRegex(ValueError, "BOOTSTRAP_TARGET_PROTECTED_PATH"):
                bootstrap_paper_account(t0_db, self.manifest)
            with self.assertRaisesRegex(ValueError, "BOOTSTRAP_TARGET_PROTECTED_PATH"):
                bootstrap_paper_account(lease_db, self.manifest)

        self.assertFalse(t0_db.exists())
        self.assertFalse(lease_db.exists())

    def test_inspect_is_read_only_and_reports_ready_state(self):
        bootstrap_paper_account(self.db_path, self.manifest)
        before = self.db_path.read_bytes()

        result = inspect_paper_account(self.db_path, now_ms=self.now)

        self.assertEqual(result["mode"], "PAPER")
        self.assertTrue(result["riskReady"])
        self.assertFalse(result["liveTradingSupported"])
        self.assertEqual(self.db_path.read_bytes(), before)

    def test_stale_inspection_fails_closed_without_mutation(self):
        bootstrap_paper_account(self.db_path, self.manifest)
        before = self.db_path.read_bytes()

        result = inspect_paper_account(self.db_path, now_ms=self.now + 31 * 60_000)

        self.assertFalse(result["riskReady"])
        self.assertEqual(self.db_path.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
