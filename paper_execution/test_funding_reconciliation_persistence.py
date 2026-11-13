"""D07 persistence and fail-closed coverage gate contract tests."""

import sqlite3
import tempfile
import unittest
from pathlib import Path

from paper_execution.funding import (
    record_account_equity_cutover,
    record_funding_coverage,
    record_funding_reconciliation,
)
from paper_execution.ledger import PaperLedger


class FundingReconciliationPersistenceTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.db_path = Path(self.temp.name) / "paper.sqlite3"
        self.now = 1_800_000_000_000
        limits = {
            "maxDrawdownPct": "50",
            "maxDailyLossUsdt": "50",
            "maxExposureUsdt": "1000",
        }
        base = PaperLedger(self.db_path, max_position_base="0.01")
        base.record_equity(
            "100", self.now - 60_000, self.now,
            "sha256:" + "1" * 64, "100",
        )
        PaperLedger(
            self.db_path, max_position_base="0.01",
            strategy_id="STRATEGY_CORE", source_sha="a" * 40,
            risk_limits=limits, require_risk_limits=True, leverage="1",
        )
        PaperLedger(
            self.db_path, max_position_base="0.01",
            strategy_id="AI_FREQAI", source_sha="a" * 40,
            risk_limits=limits, require_risk_limits=True, leverage="3",
        )
        self.expected = {
            "schemaVersion": 1,
            "populationType": "EXPECTED_FUNDING_EVENTS",
            "populationDefinitionId": "owner-statement-enumeration-v1",
            "snapshotId": "funding-statement-001",
            "source": "owner-funding-statement",
            "startAtMs": self.now - 86_400_000,
            "endAtMs": self.now,
            "currency": "USDT",
            "events": [],
        }

    def coverage(self, *, reconciliation_id=None, status="VERIFIED"):
        return record_funding_coverage(
            self.db_path,
            coverage_id="coverage-001",
            start_at_ms=self.expected["startAtMs"],
            end_at_ms=self.expected["endAtMs"],
            status=status,
            source="OWNER_RECONCILED_EVIDENCE",
            source_snapshot_id=self.expected["snapshotId"],
            payload_hash="sha256:" + "2" * 64,
            config_version="paper-risk-v1",
            recorded_at_ms=self.now,
            reconciliation_id=reconciliation_id,
        )

    def test_persists_reconciliation_and_allows_only_matching_verified_coverage(self):
        result = record_funding_reconciliation(
            self.db_path, expected_population=self.expected,
            recorded_at_ms=self.now,
        )

        self.assertEqual(
            result["reconciliationStatus"], "COMPLETE_WITHIN_DECLARED_POPULATION"
        )
        self.assertEqual(result["globalCompleteness"], "NOT_VERIFIED")
        self.assertEqual(result["independence"], "DECLARED_NOT_VERIFIED")
        coverage = self.coverage(reconciliation_id=result["reconciliationId"])
        self.assertEqual(coverage["reconciliationId"], result["reconciliationId"])

        with sqlite3.connect(self.db_path) as db:
            saved = db.execute(
                "SELECT status,expected_snapshot_id,start_at_ms,end_at_ms "
                "FROM paper_funding_reconciliations WHERE reconciliation_id=?",
                (result["reconciliationId"],),
            ).fetchone()
            self.assertEqual(saved, (
                "COMPLETE_WITHIN_DECLARED_POPULATION",
                self.expected["snapshotId"],
                self.expected["startAtMs"],
                self.expected["endAtMs"],
            ))
            audit = db.execute(
                "SELECT COUNT(*) FROM paper_audit "
                "WHERE kind='FUNDING_POPULATION_RECONCILIATION'"
            ).fetchone()[0]
            self.assertEqual(audit, 1)

    def test_verified_coverage_without_certificate_is_rejected_without_write(self):
        with self.assertRaisesRegex(ValueError, "FUNDING_RECONCILIATION_REQUIRED"):
            self.coverage()

        with sqlite3.connect(self.db_path) as db:
            self.assertEqual(
                db.execute("SELECT COUNT(*) FROM paper_funding_coverage").fetchone()[0],
                0,
            )

    def test_blocked_certificate_cannot_authorize_verified_coverage(self):
        expected = dict(self.expected)
        expected["events"] = [{
            "eventId": "missing-event",
            "eventAtMs": self.now - 1,
            "amountQuote": "0.01",
            "payloadHash": "sha256:" + "3" * 64,
        }]
        result = record_funding_reconciliation(
            self.db_path, expected_population=expected,
            recorded_at_ms=self.now,
        )

        self.assertEqual(result["reconciliationStatus"], "BLOCKED")
        with self.assertRaisesRegex(ValueError, "FUNDING_RECONCILIATION_NOT_COMPLETE"):
            self.coverage(reconciliation_id=result["reconciliationId"])

    def test_certificate_is_append_only(self):
        result = record_funding_reconciliation(
            self.db_path, expected_population=self.expected,
            recorded_at_ms=self.now,
        )
        with sqlite3.connect(self.db_path) as db:
            with self.assertRaisesRegex(sqlite3.IntegrityError, "FUNDING_RECONCILIATION_IMMUTABLE"):
                db.execute(
                    "DELETE FROM paper_funding_reconciliations WHERE reconciliation_id=?",
                    (result["reconciliationId"],),
                )

    def test_cutover_rejects_legacy_verified_coverage_without_reconciliation(self):
        with sqlite3.connect(self.db_path) as db:
            db.execute(
                """INSERT INTO paper_funding_coverage
                   (coverage_id,account_id,start_at_ms,end_at_ms,status,source,
                    source_snapshot_id,payload_hash,config_version,recorded_at_ms,
                    reconciliation_id)
                   VALUES ('legacy-coverage',1,?,?, 'VERIFIED',
                    'OWNER_RECONCILED_EVIDENCE','legacy-snapshot',?,'paper-risk-v1',?,NULL)""",
                (
                    self.expected["startAtMs"], self.expected["endAtMs"],
                    "sha256:" + "4" * 64, self.now,
                ),
            )

        with self.assertRaisesRegex(ValueError, "FUNDING_RECONCILIATION_REQUIRED"):
            record_account_equity_cutover(
                self.db_path,
                cutover_id="cutover-001",
                expected_initial_capital_quote="100",
                expected_realized_pnl_quote="0",
                expected_fees_quote="0",
                expected_funding_quote="0",
                expected_account_equity_quote="100",
                mark_price="100",
                mark_candle_close_ms=self.now - 60_000,
                mark_observed_at_ms=self.now,
                dataset_version="sha256:" + "1" * 64,
                funding_coverage_start_at_ms=self.expected["startAtMs"],
                source="OWNER_RECONCILED_EVIDENCE",
                source_snapshot_id="equity-snapshot-001",
                payload_hash="sha256:" + "5" * 64,
                config_version="paper-risk-v1",
                recorded_at_ms=self.now,
            )


if __name__ == "__main__":
    unittest.main()
