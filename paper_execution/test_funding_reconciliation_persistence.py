"""D07 persistence and fail-closed coverage gate contract tests."""

import sqlite3
import tempfile
import unittest
from pathlib import Path

from paper_execution.funding import (
    record_account_equity_cutover,
    record_funding_coverage,
    record_funding_event,
    record_funding_reconciliation,
)
from paper_execution.ledger import PaperLedger, read_account_risk_snapshot
from risk_policy import CORE_LEVERAGE


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
            risk_limits=limits, require_risk_limits=True, leverage=str(CORE_LEVERAGE),
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

    def test_new_funding_event_rejects_legacy_unverified_source(self):
        with self.assertRaisesRegex(ValueError, "FUNDING_EVENT_SOURCE_UNVERIFIED"):
            record_funding_event(
                self.db_path,
                funding_event_id="legacy-unverified-event",
                strategy_id="STRATEGY_CORE",
                amount_quote="0.01",
                event_at_ms=self.now - 1,
                source="LEGACY_UNVERIFIED",
                source_snapshot_id="legacy-source",
                payload_hash="sha256:" + "b" * 64,
                recorded_at_ms=self.now,
            )

        with sqlite3.connect(self.db_path) as db:
            self.assertEqual(
                db.execute("SELECT COUNT(*) FROM paper_funding_events").fetchone()[0],
                0,
            )

    def test_observed_population_is_enumerated_from_persisted_funding_events(self):
        event = {
            "eventId": "funding-evt-001",
            "eventAtMs": self.now - 1,
            "amountQuote": "0.125",
            "payloadHash": "sha256:" + "7" * 64,
        }
        record_funding_event(
            self.db_path,
            funding_event_id=event["eventId"],
            strategy_id="STRATEGY_CORE",
            amount_quote=event["amountQuote"],
            event_at_ms=event["eventAtMs"],
            source="paper-test-funding",
            source_snapshot_id="paper-test-event-snapshot",
            payload_hash=event["payloadHash"],
            recorded_at_ms=self.now,
        )
        expected = dict(self.expected)
        expected["events"] = [event]

        result = record_funding_reconciliation(
            self.db_path, expected_population=expected,
            recorded_at_ms=self.now,
        )

        self.assertEqual(
            result["reconciliationStatus"], "COMPLETE_WITHIN_DECLARED_POPULATION"
        )
        self.assertEqual(result["counts"]["matched"], 1)

    def test_certificate_becomes_stale_if_new_funding_event_is_added_before_coverage(self):
        certificate = record_funding_reconciliation(
            self.db_path, expected_population=self.expected,
            recorded_at_ms=self.now,
        )
        record_funding_event(
            self.db_path,
            funding_event_id="funding-evt-late",
            strategy_id="STRATEGY_CORE",
            amount_quote="0.01",
            event_at_ms=self.now - 1,
            source="paper-test-funding",
            source_snapshot_id="paper-test-event-snapshot",
            payload_hash="sha256:" + "8" * 64,
            recorded_at_ms=self.now,
        )

        with self.assertRaisesRegex(ValueError, "FUNDING_RECONCILIATION_STALE"):
            self.coverage(reconciliation_id=certificate["reconciliationId"])

        with sqlite3.connect(self.db_path) as db:
            self.assertEqual(
                db.execute("SELECT COUNT(*) FROM paper_funding_coverage").fetchone()[0],
                0,
            )
            self.assertEqual(
                db.execute("SELECT risk_ready FROM paper_account_risk_state").fetchone()[0],
                0,
            )

    def test_verified_coverage_freezes_event_population(self):
        certificate = record_funding_reconciliation(
            self.db_path, expected_population=self.expected,
            recorded_at_ms=self.now,
        )
        self.coverage(reconciliation_id=certificate["reconciliationId"])

        with self.assertRaisesRegex(ValueError, "FUNDING_RECONCILIATION_REQUIRED"):
            record_funding_event(
                self.db_path,
                funding_event_id="funding-evt-after-coverage",
                strategy_id="STRATEGY_CORE",
                amount_quote="0.01",
                event_at_ms=self.now - 1,
                source="paper-test-funding",
                source_snapshot_id="paper-test-event-snapshot",
                payload_hash="sha256:" + "9" * 64,
                recorded_at_ms=self.now,
            )

        with sqlite3.connect(self.db_path) as db:
            self.assertEqual(
                db.execute("SELECT COUNT(*) FROM paper_funding_events").fetchone()[0],
                0,
            )

    def test_database_trigger_rejects_direct_verified_coverage_without_certificate(self):
        with sqlite3.connect(self.db_path) as db:
            with self.assertRaisesRegex(sqlite3.IntegrityError, "FUNDING_RECONCILIATION_REQUIRED"):
                db.execute(
                    """INSERT INTO paper_funding_coverage
                       (coverage_id,account_id,start_at_ms,end_at_ms,status,source,
                        source_snapshot_id,payload_hash,config_version,recorded_at_ms,
                        reconciliation_id)
                       VALUES ('direct-bypass',1,?,?, 'VERIFIED',
                        'OWNER_RECONCILED_EVIDENCE',?,?, 'paper-risk-v1',?,NULL)""",
                    (
                        self.expected["startAtMs"], self.expected["endAtMs"],
                        self.expected["snapshotId"], "sha256:" + "a" * 64, self.now,
                    ),
                )

    def test_database_trigger_rejects_event_insert_into_verified_interval(self):
        certificate = record_funding_reconciliation(
            self.db_path, expected_population=self.expected,
            recorded_at_ms=self.now,
        )
        self.coverage(reconciliation_id=certificate["reconciliationId"])

        with sqlite3.connect(self.db_path) as db:
            with self.assertRaisesRegex(sqlite3.IntegrityError, "FUNDING_RECONCILIATION_REQUIRED"):
                db.execute(
                    """INSERT INTO paper_funding_events
                       (funding_event_id,account_id,strategy_id,amount_quote,event_at_ms,
                        source_snapshot_id,payload_hash,source,recorded_at_ms)
                       VALUES ('direct-insert-event',1,'STRATEGY_CORE','0.01',?,
                               'direct-insert-source','sha256:' || printf('%064d',1),
                               'untrusted-direct-writer',?)""",
                    (self.now - 1, self.now),
                )

    def test_read_only_risk_gate_detects_direct_event_insert_after_certificate(self):
        certificate = record_funding_reconciliation(
            self.db_path, expected_population=self.expected,
            recorded_at_ms=self.now,
        )
        self.coverage(reconciliation_id=certificate["reconciliationId"])
        record_account_equity_cutover(
            self.db_path,
            cutover_id="cutover-direct-event-bypass",
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
            source_snapshot_id="equity-snapshot-bypass-test",
            payload_hash="sha256:" + "2" * 64,
            config_version="paper-risk-v1",
            recorded_at_ms=self.now,
        )
        with sqlite3.connect(self.db_path) as db:
            db.execute("DROP TRIGGER paper_funding_events_no_insert_into_verified_coverage")
            db.execute(
                """INSERT INTO paper_funding_events
                   (funding_event_id,account_id,strategy_id,amount_quote,event_at_ms,
                    source_snapshot_id,payload_hash,source,recorded_at_ms)
                   VALUES ('direct-bypass-event',1,'STRATEGY_CORE','0.01',?,
                           'direct-bypass-source','sha256:' || printf('%064d',0),
                           'untrusted-direct-writer',?)""",
                (self.now - 1, self.now),
            )

        snapshot = read_account_risk_snapshot(self.db_path, now_ms=self.now)
        self.assertFalse(snapshot["riskReady"], snapshot)
        self.assertEqual(snapshot["unavailableReason"], "FUNDING_PROVENANCE_INCOMPLETE")

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
            db.execute("DROP TRIGGER paper_funding_coverage_verified_requires_reconciliation")
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
