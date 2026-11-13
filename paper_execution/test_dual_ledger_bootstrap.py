"""TDD contract for the isolated Dual Ledger bootstrap CLI."""

import hashlib
import json
import os
import sqlite3
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from paper_execution.bootstrap import (
    bootstrap_paper_account,
    inspect_paper_account,
)
from paper_execution.__main__ import _current_source_sha, main as paper_cli_main
from paper_execution.ledger import read_account_risk_snapshot, dual_ledger_ready
from risk_policy import CORE_LEVERAGE


def write_json(path, value):
    raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    path.write_bytes(raw)
    return "sha256:" + hashlib.sha256(raw).hexdigest()


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
        self.owner_attestation = self.root / "owner-attestation.json"
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
            "fundingPayloadHash": "",
            "cutoverId": "bootstrap-equity-cutover-001",
            "cutoverSource": "OWNER_RECONCILED_EVIDENCE",
            "cutoverSnapshotId": "owner-equity-001",
            "cutoverEvidencePath": str(self.cutover_evidence),
            "cutoverPayloadHash": "",
            "ownerAttestationPath": str(self.owner_attestation),
            "ownerAttestationPayloadHash": "",
            "configVersion": "paper-risk-v1",
            "recordedAtMs": self.now,
        }
        funding_document = {
            "snapshotId": "owner-funding-001",
            "status": "VERIFIED",
            "startAtMs": self.now - 86_400_000,
            "endAtMs": self.now,
            "source": "OWNER_RECONCILED_EVIDENCE",
            "configVersion": "paper-risk-v1",
            "fundingByStrategy": {
                "STRATEGY_CORE": "0",
                "AI_FREQAI": "0",
                "LEGACY_UNATTRIBUTED": "0",
            },
        }
        cutover_document = {
            "snapshotId": "owner-equity-001",
            "initialCapitalQuote": "100",
            "realizedPnlQuote": "0",
            "feesQuote": "0",
            "fundingQuote": "0",
            "accountEquityQuote": "100",
            "markPrice": "100",
            "markCandleCloseMs": self.now - 60_000,
            "markObservedAtMs": self.now,
            "datasetVersion": "sha256:" + "1" * 64,
            "fundingCoverageStartAtMs": self.now - 86_400_000,
            "source": "OWNER_RECONCILED_EVIDENCE",
            "configVersion": "paper-risk-v1",
        }
        self.manifest["fundingPayloadHash"] = write_json(
            self.funding_evidence, funding_document
        )
        self.manifest["cutoverPayloadHash"] = write_json(
            self.cutover_evidence, cutover_document
        )
        owner_attestation = {
            "schemaVersion": 1,
            "attestationType": "DUAL_LEDGER_BOOTSTRAP_EVIDENCE_REVIEW",
            "attestorRole": "OWNER_DECLARATION",
            "claimScope": "FUNDING_AND_EQUITY_SNAPSHOT_REVIEW",
            "sourceSha": self.source_sha,
            "fundingSnapshotId": "owner-funding-001",
            "fundingPayloadHash": self.manifest["fundingPayloadHash"],
            "cutoverSnapshotId": "owner-equity-001",
            "cutoverPayloadHash": self.manifest["cutoverPayloadHash"],
            "reviewedAtMs": self.now,
            "reviewStatement": "I_REVIEWED_THE_IDENTIFIED_FUNDING_AND_EQUITY_SNAPSHOTS",
            "nonClaims": [
                "FACTUAL_TRUTH",
                "FRESHNESS",
                "POPULATION_COMPLETENESS",
                "PRIVILEGED_ACTION_AUTHORIZATION",
                "SOURCE_AUTHENTICITY",
            ],
        }
        self.manifest["ownerAttestationPayloadHash"] = write_json(
            self.owner_attestation, owner_attestation
        )
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

    def test_funding_evidence_content_must_match_manifest_even_with_valid_hash(self):
        evidence = json.loads(self.funding_evidence.read_text(encoding="utf-8"))
        evidence["status"] = "UNKNOWN"
        bad = dict(self.manifest)
        bad["fundingPayloadHash"] = write_json(self.funding_evidence, evidence)

        with self.assertRaisesRegex(ValueError, "BOOTSTRAP_EVIDENCE_CONTENT_MISMATCH"):
            bootstrap_paper_account(self.db_path, bad)

        self.assertFalse(self.db_path.exists())

    def test_equity_evidence_totals_must_match_manifest_even_with_valid_hash(self):
        evidence = json.loads(self.cutover_evidence.read_text(encoding="utf-8"))
        evidence["accountEquityQuote"] = "999"
        bad = dict(self.manifest)
        bad["cutoverPayloadHash"] = write_json(self.cutover_evidence, evidence)

        with self.assertRaisesRegex(ValueError, "BOOTSTRAP_EVIDENCE_CONTENT_MISMATCH"):
            bootstrap_paper_account(self.db_path, bad)

        self.assertFalse(self.db_path.exists())

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

    def test_source_sha_check_rejects_dirty_worktree(self):
        responses = [
            SimpleNamespace(stdout=self.source_sha),
            SimpleNamespace(stdout=" M paper_execution/bootstrap.py\\n"),
        ]
        with patch(
            "paper_execution.__main__.subprocess.run",
            side_effect=responses,
        ):
            with self.assertRaisesRegex(ValueError, "BOOTSTRAP_SOURCE_TREE_DIRTY"):
                _current_source_sha()

    def test_cli_bootstrap_requires_exact_checked_out_source_sha(self):
        manifest_path = self.root / "bootstrap-manifest.json"
        write_json(manifest_path, self.manifest)
        output = StringIO()

        with patch(
            "paper_execution.__main__.subprocess.run",
            side_effect=[SimpleNamespace(stdout="b" * 40), SimpleNamespace(stdout="")],
        ), redirect_stdout(output):
            with self.assertRaisesRegex(ValueError, "BOOTSTRAP_SOURCE_SHA_MISMATCH"):
                paper_cli_main([
                    "--db", str(self.db_path),
                    "--bootstrap-manifest", str(manifest_path),
                ])

        self.assertFalse(self.db_path.exists())

    def test_cli_bootstrap_and_inspect_use_the_expected_modes(self):
        manifest_path = self.root / "bootstrap-manifest.json"
        write_json(manifest_path, self.manifest)
        output = StringIO()

        with patch(
            "paper_execution.__main__.subprocess.run",
            side_effect=[SimpleNamespace(stdout=self.source_sha), SimpleNamespace(stdout="")],
        ), redirect_stdout(output):
            self.assertEqual(paper_cli_main([
                "--db", str(self.db_path),
                "--bootstrap-manifest", str(manifest_path),
            ]), 0)

        created = json.loads(output.getvalue())
        self.assertTrue(created["riskReady"])
        before = self.db_path.read_bytes()
        inspected_output = StringIO()
        with redirect_stdout(inspected_output):
            self.assertEqual(paper_cli_main([
                "--db", str(self.db_path), "--inspect", "--now-ms", str(self.now),
            ]), 0)
        inspected = json.loads(inspected_output.getvalue())
        self.assertTrue(inspected["riskReady"])
        self.assertTrue(inspected["readOnly"])
        self.assertEqual(self.db_path.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
