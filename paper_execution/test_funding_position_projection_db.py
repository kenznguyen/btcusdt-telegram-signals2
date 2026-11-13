"""Read-only SQLite adapter tests for D07 PAPER position projection."""

import hashlib
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from paper_execution.account_history import record_account_history_coverage
from paper_execution.funding import record_account_equity_cutover, record_funding_coverage
from paper_execution.funding_position_projection import load_paper_position_snapshots_from_db
from paper_execution.ledger import PaperLedger
from risk_policy import CORE_LEVERAGE


NOW = 1_800_000_000_000
SETTLEMENTS = [NOW + 1_000, NOW + 2_000]
READ_AT = NOW + 3_000
STRATEGIES = ("STRATEGY_CORE", "AI_FREQAI", "LEGACY_UNATTRIBUTED")


def digest(value):
    return "sha256:" + hashlib.sha256(value.encode()).hexdigest()


class FundingPositionProjectionDatabaseTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.db_path = Path(self.temp.name) / "paper.sqlite3"
        limits = {
            "maxDrawdownPct": "50",
            "maxDailyLossUsdt": "50",
            "maxExposureUsdt": "1000",
        }
        base = PaperLedger(self.db_path, max_position_base="0.01")
        base.record_equity(
            "100", NOW - 60_000, NOW,
            "sha256:" + "1" * 64, "100",
        )
        PaperLedger(
            self.db_path, max_position_base="0.01",
            strategy_id="STRATEGY_CORE", source_sha="a" * 40,
            risk_limits=limits, require_risk_limits=True,
            leverage=str(CORE_LEVERAGE),
        )
        PaperLedger(
            self.db_path, max_position_base="0.01",
            strategy_id="AI_FREQAI", source_sha="a" * 40,
            risk_limits=limits, require_risk_limits=True, leverage="3",
        )
        record_funding_coverage(
            self.db_path,
            coverage_id="funding-bootstrap",
            start_at_ms=NOW - 60_000,
            end_at_ms=NOW,
            status="DISABLED",
            source="PAPER_TEST_CONFIGURATION",
            source_snapshot_id="funding-bootstrap-snapshot",
            payload_hash="sha256:" + "2" * 64,
            config_version="paper-risk-v1",
            recorded_at_ms=NOW,
        )
        record_account_equity_cutover(
            self.db_path,
            cutover_id="cutover-db-001",
            expected_initial_capital_quote="100",
            expected_realized_pnl_quote="0",
            expected_fees_quote="0",
            expected_funding_quote="0",
            expected_account_equity_quote="100",
            mark_price="100",
            mark_candle_close_ms=NOW - 60_000,
            mark_observed_at_ms=NOW,
            dataset_version="T0_M15_H1_DATASET_BUNDLE_V1",
            funding_coverage_start_at_ms=NOW - 60_000,
            source="PAPER_TEST_CUTOVER",
            source_snapshot_id="cutover-source-001",
            payload_hash="sha256:" + "3" * 64,
            config_version="paper-risk-v1",
            recorded_at_ms=NOW + 1_000,
        )
        self._insert_fill("STRATEGY_CORE", "db-fill-core", NOW + 500, "0.1")
        self._insert_fill("AI_FREQAI", "db-fill-ai", NOW + 1_500, "-0.2")
        for strategy in STRATEGIES:
            record_account_history_coverage(
                self.db_path,
                coverage_id="execution-" + strategy,
                stream_type="EXECUTION",
                strategy_id=strategy,
                start_at_ms=NOW,
                end_at_ms=NOW + 2_001,
                status="VERIFIED",
                source="PAPER_EXECUTION_JOURNAL",
                source_snapshot_id="execution-source-" + strategy,
                payload_hash="sha256:" + "4" * 64,
                recorded_at_ms=READ_AT,
            )

    def _insert_fill(self, strategy, event_id, event_at, quantity):
        payload = {
            "eventId": event_id,
            "accountId": 1,
            "strategyId": strategy,
            "eventType": "FILL",
            "eventAtMs": event_at,
            "recordedAtMs": event_at + 100,
            "orderId": "order-" + event_id,
            "intentId": "intent-" + event_id,
            "sourceEventId": "source-" + event_id,
            "quantityDeltaBase": quantity,
            "fillPrice": "100",
            "feeQuote": "0.01",
            "source": "PAPER_VISIBLE_DEPTH_SIMULATION",
            "sourceSnapshotId": "book-" + event_id,
            "feeCurrency": "USDT",
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        with sqlite3.connect(self.db_path) as db:
            db.execute(
                """INSERT INTO paper_account_event_journal
                   (event_id,account_id,strategy_id,event_type,event_at_ms,recorded_at_ms,
                    order_id,intent_id,source_event_id,quantity_delta_base,fill_price,
                    fee_quote,fee_currency,source,source_snapshot_id,payload_hash,
                    canonical_payload,created_at_ms)
                   VALUES (?,1,?,'FILL',?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    event_id, strategy, event_at, event_at + 100,
                    payload["orderId"], payload["intentId"], payload["sourceEventId"],
                    quantity, "100", "0.01", "USDT", payload["source"],
                    payload["sourceSnapshotId"], digest(canonical), canonical,
                    event_at + 100,
                ),
            )

    def test_loads_actual_cutover_events_and_coverage_read_only(self):
        before = hashlib.sha256(self.db_path.read_bytes()).hexdigest()
        result = load_paper_position_snapshots_from_db(
            self.db_path, settlement_times=SETTLEMENTS, now_ms=READ_AT
        )
        after = hashlib.sha256(self.db_path.read_bytes()).hexdigest()
        by_key = {(row["strategyId"], row["observedAtMs"]): row for row in result}

        self.assertEqual(before, after)
        self.assertEqual(by_key[("STRATEGY_CORE", SETTLEMENTS[0])]["positionBase"], "0.1")
        self.assertEqual(by_key[("STRATEGY_CORE", SETTLEMENTS[1])]["positionBase"], "0.1")
        self.assertEqual(by_key[("AI_FREQAI", SETTLEMENTS[0])]["positionBase"], "0")
        self.assertEqual(by_key[("AI_FREQAI", SETTLEMENTS[1])]["positionBase"], "-0.2")
        self.assertEqual(by_key[("LEGACY_UNATTRIBUTED", SETTLEMENTS[1])]["positionBase"], "0")

    def test_missing_required_migration_fails_closed(self):
        with sqlite3.connect(self.db_path) as db:
            db.execute(
                "UPDATE paper_schema_migrations SET checksum=? WHERE version=8",
                ("0" * 64,),
            )
        with self.assertRaisesRegex(ValueError, "FUNDING_POSITION_SCHEMA_NOT_SUPPORTED"):
            load_paper_position_snapshots_from_db(
                self.db_path, settlement_times=SETTLEMENTS, now_ms=READ_AT
            )

    def test_missing_immutability_trigger_fails_closed(self):
        with sqlite3.connect(self.db_path) as db:
            db.execute("DROP TRIGGER paper_account_event_journal_immutable_update")
        with self.assertRaisesRegex(ValueError, "FUNDING_POSITION_SCHEMA_NOT_SUPPORTED"):
            load_paper_position_snapshots_from_db(
                self.db_path, settlement_times=SETTLEMENTS, now_ms=READ_AT
            )

    def test_no_cutover_before_requested_settlement_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "FUNDING_POSITION_CUTOVER_NOT_FOUND"):
            load_paper_position_snapshots_from_db(
                self.db_path, settlement_times=[NOW - 1], now_ms=READ_AT
            )

    def test_missing_database_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "FUNDING_POSITION_DATABASE_UNAVAILABLE"):
            load_paper_position_snapshots_from_db(
                self.db_path.parent / "missing.sqlite3",
                settlement_times=SETTLEMENTS,
                now_ms=READ_AT,
            )


if __name__ == "__main__":
    unittest.main()
