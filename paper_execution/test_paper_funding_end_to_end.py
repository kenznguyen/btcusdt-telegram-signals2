"""Offline end-to-end PAPER funding pipeline contract tests."""

import hashlib
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from paper_execution.account_history import record_account_history_coverage
from paper_execution.binance_public_funding import parse_binance_usdm_funding_rate_page
from paper_execution.funding import (
    record_account_equity_cutover,
    record_funding_coverage,
    record_funding_reconciliation,
)
from paper_execution.funding_model import build_expected_funding_population
from paper_execution.funding_position_projection import load_paper_position_snapshots_from_db
from paper_execution.funding_provenance import verify_funding_source_evidence
from paper_execution.ledger import PaperLedger
from paper_execution.paper_funding_posting import post_paper_funding_events
from risk_policy import CORE_LEVERAGE


NOW = 1_800_000_000_000
SETTLEMENTS = [NOW + 1_000, NOW + 2_000]
END = SETTLEMENTS[-1] + 1
READ_AT = NOW + 3_000
STRATEGIES = ("STRATEGY_CORE", "AI_FREQAI", "LEGACY_UNATTRIBUTED")


def digest_bytes(value):
    return "sha256:" + hashlib.sha256(value).hexdigest()


def digest_document(value):
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return digest_bytes(encoded)


class PaperFundingEndToEndTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.db_path = self.root / "paper.sqlite3"
        limits = {
            "maxDrawdownPct": "50",
            "maxDailyLossUsdt": "50",
            "maxExposureUsdt": "1000",
        }
        base = PaperLedger(self.db_path, max_position_base="0.01")
        base.record_equity("100", NOW - 60_000, NOW, "sha256:" + "1" * 64, "100")
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
            self.db_path, coverage_id="funding-bootstrap",
            start_at_ms=NOW - 60_000, end_at_ms=NOW,
            status="DISABLED", source="PAPER_TEST_CONFIGURATION",
            source_snapshot_id="funding-bootstrap-snapshot",
            payload_hash="sha256:" + "2" * 64,
            config_version="paper-risk-v1", recorded_at_ms=NOW,
        )
        record_account_equity_cutover(
            self.db_path, cutover_id="cutover-e2e-001",
            expected_initial_capital_quote="100",
            expected_realized_pnl_quote="0", expected_fees_quote="0",
            expected_funding_quote="0", expected_account_equity_quote="100",
            mark_price="100", mark_candle_close_ms=NOW - 60_000,
            mark_observed_at_ms=NOW, dataset_version="T0_M15_H1_DATASET_BUNDLE_V1",
            funding_coverage_start_at_ms=NOW - 60_000,
            source="PAPER_TEST_CUTOVER", source_snapshot_id="cutover-source-e2e",
            payload_hash="sha256:" + "3" * 64,
            config_version="paper-risk-v1", recorded_at_ms=NOW + 100,
        )
        self._insert_fill("STRATEGY_CORE", "fill-core", NOW + 500, "0.1")
        self._insert_fill("AI_FREQAI", "fill-ai", NOW + 1_500, "-0.2")
        for strategy in STRATEGIES:
            record_account_history_coverage(
                self.db_path, coverage_id="execution-" + strategy,
                stream_type="EXECUTION", strategy_id=strategy,
                start_at_ms=NOW, end_at_ms=END,
                status="VERIFIED", source="PAPER_EXECUTION_JOURNAL",
                source_snapshot_id="execution-source-" + strategy,
                payload_hash="sha256:" + "4" * 64, recorded_at_ms=READ_AT,
            )

        self.raw_page = json.dumps([
            {"symbol": "BTCUSDT", "fundingRate": "0.0001",
             "fundingTime": SETTLEMENTS[0], "markPrice": "100", "rateType": "Regular"},
            {"symbol": "BTCUSDT", "fundingRate": "-0.0001",
             "fundingTime": SETTLEMENTS[1], "markPrice": "100", "rateType": "Regular"},
        ], separators=(",", ":")).encode("utf-8")
        (self.root / "funding-page.json").write_bytes(self.raw_page)
        self.page_digest = digest_bytes(self.raw_page)
        self.envelope = {
            "schemaVersion": 1,
            "evidenceSnapshotId": "public-funding-snapshot-e2e",
            "source": {
                "sourceId": "binance-usdm-public-funding",
                "sourceType": "public_market_data",
                "claimedIssuer": "Binance",
                "authorityBasis": "public USD-M funding history endpoint",
                "acquisitionMethod": "captured response fixture",
            },
            "scope": {
                "accountRef": "PAPER",
                "instrument": "BTCUSDT",
                "currency": "USDT",
                "startAtMs": NOW,
                "endAtMs": END,
                "timestampSemantics": "fundingTime event timestamp in milliseconds",
                "filtersFingerprint": "sha256:" + "5" * 64,
            },
            "snapshot": {
                "asOfMs": READ_AT, "retrievedAtMs": READ_AT, "eventCutoffMs": END,
            },
            "pages": [{
                "ordinal": 0, "pageId": "page-e2e-0",
                "requestCursor": None, "nextCursor": None, "terminal": True,
                "requestFingerprint": "sha256:" + "6" * 64,
                "relativePath": "funding-page.json",
                "byteLength": len(self.raw_page), "sha256": self.page_digest,
                "recordCount": 2, "sourceTotal": 2,
            }],
            "lineage": {
                "expectedSourceSystem": "binance-public-market-data",
                "observedSourceSystem": "paper-ledger-simulator",
                "sharedUpstreamSystems": ["binance-public-market-data"],
            },
        }

    def _insert_fill(self, strategy, event_id, event_at, quantity):
        payload = {
            "eventId": event_id, "accountId": 1, "strategyId": strategy,
            "eventType": "FILL", "eventAtMs": event_at, "recordedAtMs": event_at + 100,
            "orderId": "order-" + event_id, "intentId": "intent-" + event_id,
            "sourceEventId": "source-" + event_id, "quantityDeltaBase": quantity,
            "fillPrice": "100", "feeQuote": "0.01",
            "source": "PAPER_VISIBLE_DEPTH_SIMULATION",
            "sourceSnapshotId": "book-" + event_id, "feeCurrency": "USDT",
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
                (event_id, strategy, event_at, event_at + 100,
                 payload["orderId"], payload["intentId"], payload["sourceEventId"],
                 quantity, "100", "0.01", "USDT", payload["source"],
                 payload["sourceSnapshotId"], digest_bytes(canonical.encode()),
                 canonical, event_at + 100),
            )

    def test_public_bytes_to_position_model_posting_reconciliation_and_coverage(self):
        evidence = verify_funding_source_evidence(self.envelope, self.root)
        self.assertEqual(evidence["sourceByteIntegrity"], "PASS")
        self.assertEqual(evidence["sourceByteReadback"], "PASS")
        self.assertEqual(evidence["independence"], "BLOCKED_SHARED_LINEAGE")

        rates = parse_binance_usdm_funding_rate_page(
            self.raw_page, evidence_snapshot_id=self.envelope["evidenceSnapshotId"],
            expected_sha256=self.page_digest, expected_byte_length=len(self.raw_page),
            start_at_ms=NOW, end_at_ms=END, expected_record_count=2,
        )
        positions = load_paper_position_snapshots_from_db(
            self.db_path, settlement_times=SETTLEMENTS, now_ms=READ_AT,
        )
        expected = build_expected_funding_population(
            start_at_ms=NOW, end_at_ms=END,
            position_snapshots=positions, funding_rate_events=rates,
        )

        posted = post_paper_funding_events(
            self.db_path, position_snapshots=positions, funding_rate_events=rates,
            start_at_ms=NOW, end_at_ms=END, recorded_at_ms=READ_AT,
        )
        self.assertEqual(len(posted), 3)
        self.assertEqual(len(post_paper_funding_events(
            self.db_path, position_snapshots=positions, funding_rate_events=rates,
            start_at_ms=NOW, end_at_ms=END, recorded_at_ms=READ_AT,
        )), 3)

        reconciliation = record_funding_reconciliation(
            self.db_path, expected_population=expected, recorded_at_ms=READ_AT,
        )
        self.assertEqual(
            reconciliation["reconciliationStatus"], "COMPLETE_WITHIN_DECLARED_POPULATION",
        )
        self.assertEqual(reconciliation["counts"], {
            "expected": 3, "observed": 3, "matched": 3,
            "missing": 0, "unexpected": 0, "duplicate": 0,
        })
        self.assertEqual(reconciliation["independence"], "DECLARED_NOT_VERIFIED")
        self.assertEqual(reconciliation["globalCompleteness"], "NOT_VERIFIED")

        coverage = record_funding_coverage(
            self.db_path, coverage_id="funding-e2e-coverage",
            start_at_ms=NOW, end_at_ms=END, status="VERIFIED",
            source="PAPER_PUBLIC_RATE_RECONCILED",
            source_snapshot_id=expected["snapshotId"],
            payload_hash="sha256:" + "7" * 64,
            config_version="paper-risk-v1", recorded_at_ms=READ_AT,
            reconciliation_id=reconciliation["reconciliationId"],
        )
        self.assertEqual(coverage["status"], "VERIFIED")
        with sqlite3.connect(self.db_path) as db:
            count = db.execute(
                "SELECT COUNT(*) FROM paper_funding_events WHERE account_id=1"
            ).fetchone()[0]
            self.assertEqual(count, 3)


if __name__ == "__main__":
    unittest.main()
