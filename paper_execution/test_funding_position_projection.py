"""TDD contract for projecting PAPER positions from cutover + execution history."""

import hashlib
import json
import unittest

from paper_execution.funding_position_projection import build_paper_position_snapshots


STRATEGIES = ("STRATEGY_CORE", "AI_FREQAI", "LEGACY_UNATTRIBUTED")
SNAPSHOT_AT = 1_000
SETTLEMENTS = [2_000, 4_000]
NOW = 6_000


def cutover(strategy, quantity, *, cutover_id="cutover-001", at=SNAPSHOT_AT):
    fields = {
        "cutoverId": cutover_id,
        "strategyId": strategy,
        "snapshotAtMs": at,
        "positionBase": quantity,
        "averageEntryPrice": "100" if quantity != "0" else "0",
        "realizedPnlQuote": "0",
        "feesQuote": "0",
        "fundingQuote": "0",
        "sourceSnapshotId": f"cutover-source-{strategy}",
        "payloadHash": "sha256:" + "a" * 64,
    }
    return {
        **fields,
        "canonicalPayload": json.dumps(fields, sort_keys=True, separators=(",", ":")),
    }


def fill(strategy, event_id, at, quantity, *, recorded=None, event_type="FILL",
         fee_currency="USDT"):
    payload = {
        "eventId": event_id,
        "accountId": 1,
        "strategyId": strategy,
        "eventType": event_type,
        "eventAtMs": at,
        "recordedAtMs": at + 1 if recorded is None else recorded,
        "orderId": "order-" + event_id,
        "intentId": "intent-" + event_id,
        "sourceEventId": "source-" + event_id,
        "quantityDeltaBase": quantity,
        "fillPrice": "100",
        "feeQuote": "0.01",
        "source": "PAPER_EXECUTION_SIMULATION",
        "sourceSnapshotId": "execution-source-" + event_id,
        "feeCurrency": fee_currency,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return {
        "eventId": event_id,
        "strategyId": strategy,
        "eventType": event_type,
        "eventAtMs": at,
        "recordedAtMs": payload["recordedAtMs"],
        "quantityDeltaBase": quantity,
        "fillPrice": "100",
        "feeQuote": "0.01",
        "feeCurrency": fee_currency,
        "source": payload["source"],
        "sourceSnapshotId": payload["sourceSnapshotId"],
        "payloadHash": "sha256:" + hashlib.sha256(canonical.encode()).hexdigest(),
        "orderId": payload["orderId"],
        "intentId": payload["intentId"],
        "sourceEventId": payload["sourceEventId"],
        "canonicalPayload": canonical,
    }


def coverage(strategy, *, start=SNAPSHOT_AT, end=5_001, status="VERIFIED",
             recorded=NOW, coverage_id=None):
    return {
        "coverageId": coverage_id or "coverage-" + strategy,
        "strategyId": strategy,
        "startAtMs": start,
        "endAtMs": end,
        "status": status,
        "source": "PAPER_EXECUTION_JOURNAL",
        "sourceSnapshotId": "execution-coverage-" + strategy,
        "payloadHash": "sha256:" + "b" * 64,
        "recordedAtMs": recorded,
    }


def baseline():
    return [
        cutover("STRATEGY_CORE", "1"),
        cutover("AI_FREQAI", "-2"),
        cutover("LEGACY_UNATTRIBUTED", "0"),
    ]


def proofs():
    return [coverage(strategy) for strategy in STRATEGIES]


class FundingPositionProjectionTest(unittest.TestCase):
    def project(self, snapshots=None, events=None, coverage_rows=None, settlements=None, now=NOW):
        return build_paper_position_snapshots(
            cutover_snapshots=baseline() if snapshots is None else snapshots,
            execution_events=[] if events is None else events,
            execution_coverage=proofs() if coverage_rows is None else coverage_rows,
            settlement_times=SETTLEMENTS if settlements is None else settlements,
            now_ms=now,
        )

    def test_projects_positions_as_of_each_settlement(self):
        events = [
            fill("STRATEGY_CORE", "fill-core-1", 1_500, "0.5"),
            fill("STRATEGY_CORE", "fill-core-2", 3_000, "-0.25"),
            fill("AI_FREQAI", "fill-ai-1", 2_500, "-1"),
        ]
        result = self.project(events=events)
        by_key = {(row["strategyId"], row["observedAtMs"]): row for row in result}

        self.assertEqual(by_key[("STRATEGY_CORE", 2_000)]["positionBase"], "1.5")
        self.assertEqual(by_key[("STRATEGY_CORE", 4_000)]["positionBase"], "1.25")
        self.assertEqual(by_key[("AI_FREQAI", 2_000)]["positionBase"], "-2")
        self.assertEqual(by_key[("AI_FREQAI", 4_000)]["positionBase"], "-3")
        self.assertEqual(by_key[("LEGACY_UNATTRIBUTED", 4_000)]["positionBase"], "0")
        self.assertTrue(all(row["snapshotId"].startswith("sha256:") for row in result))

    def test_projection_is_deterministic_under_input_order_changes(self):
        events = [
            fill("STRATEGY_CORE", "fill-core-1", 1_500, "0.5"),
            fill("AI_FREQAI", "fill-ai-1", 2_500, "-1"),
        ]
        first = self.project(events=events)
        second = self.project(
            snapshots=list(reversed(baseline())),
            events=list(reversed(events)),
            coverage_rows=list(reversed(proofs())),
        )
        self.assertEqual(first, second)

    def test_event_at_funding_boundary_is_ambiguous_and_rejected(self):
        events = [fill("STRATEGY_CORE", "fill-at-settlement", 2_000, "0.5")]
        with self.assertRaisesRegex(ValueError, "FUNDING_POSITION_BOUNDARY_AMBIGUOUS"):
            self.project(events=events)

    def test_missing_strategy_cutover_snapshot_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "FUNDING_POSITION_CUTOVER_SET_INVALID"):
            self.project(snapshots=baseline()[:-1])

    def test_mixed_cutover_ids_are_rejected(self):
        rows = baseline()
        rows[0] = cutover("STRATEGY_CORE", "1", cutover_id="other-cutover")
        with self.assertRaisesRegex(ValueError, "FUNDING_POSITION_CUTOVER_SET_INVALID"):
            self.project(snapshots=rows)

    def test_settlement_before_cutover_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "FUNDING_POSITION_BEFORE_CUTOVER"):
            self.project(settlements=[500])

    def test_missing_execution_coverage_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "FUNDING_POSITION_COVERAGE_INCOMPLETE"):
            self.project(coverage_rows=proofs()[:-1])

    def test_execution_coverage_gap_fails_closed(self):
        rows = proofs()
        rows[0:1] = [
            coverage("STRATEGY_CORE", start=1_000, end=2_500, coverage_id="core-a"),
            coverage("STRATEGY_CORE", start=3_000, end=5_001, coverage_id="core-b"),
        ]
        with self.assertRaisesRegex(ValueError, "FUNDING_POSITION_COVERAGE_INCOMPLETE"):
            self.project(coverage_rows=rows)

    def test_non_verified_coverage_fails_closed(self):
        rows = proofs()
        rows[0] = coverage("STRATEGY_CORE", status="UNKNOWN")
        with self.assertRaisesRegex(ValueError, "FUNDING_POSITION_COVERAGE_INCOMPLETE"):
            self.project(coverage_rows=rows)

    def test_future_or_unrecorded_coverage_fails_closed(self):
        rows = proofs()
        rows[0] = coverage("STRATEGY_CORE", recorded=4_000)
        with self.assertRaisesRegex(ValueError, "FUNDING_POSITION_COVERAGE_INCOMPLETE"):
            self.project(coverage_rows=rows)

    def test_tampered_execution_payload_hash_is_rejected(self):
        event = fill("STRATEGY_CORE", "fill-core-1", 1_500, "0.5")
        event["payloadHash"] = "sha256:" + "0" * 64
        with self.assertRaisesRegex(ValueError, "FUNDING_POSITION_EVENT_DIGEST_INVALID"):
            self.project(events=[event])

    def test_mismatched_canonical_execution_payload_is_rejected(self):
        event = fill("STRATEGY_CORE", "fill-core-1", 1_500, "0.5")
        event["canonicalPayload"] = "{}"
        with self.assertRaisesRegex(ValueError, "FUNDING_POSITION_EVENT_PAYLOAD_INVALID"):
            self.project(events=[event])

    def test_late_event_before_cutover_is_rejected(self):
        event = fill("STRATEGY_CORE", "late-fill", 900, "0.5", recorded=1_100)
        with self.assertRaisesRegex(ValueError, "ACCOUNT_HISTORY_LATE_EVENT"):
            self.project(events=[event])

    def test_unsupported_execution_event_type_is_rejected(self):
        event = fill("STRATEGY_CORE", "adjustment", 1_500, "0.5", event_type="LEDGER_ADJUSTMENT")
        with self.assertRaisesRegex(ValueError, "ACCOUNT_HISTORY_EVENT_TYPE_UNSUPPORTED"):
            self.project(events=[event])

    def test_unknown_fee_currency_is_rejected(self):
        event = fill("STRATEGY_CORE", "fill-core-1", 1_500, "0.5", fee_currency="BTC")
        with self.assertRaisesRegex(ValueError, "ACCOUNT_HISTORY_FEE_PROVENANCE_UNKNOWN"):
            self.project(events=[event])

    def test_duplicate_execution_event_id_is_rejected(self):
        event = fill("STRATEGY_CORE", "fill-core-1", 1_500, "0.5")
        with self.assertRaisesRegex(ValueError, "ACCOUNT_HISTORY_EVENT_ID_DUPLICATE"):
            self.project(events=[event, event])

    def test_event_outside_coverage_is_rejected(self):
        rows = proofs()
        rows[0] = coverage("STRATEGY_CORE", start=1_600, end=5_001)
        event = fill("STRATEGY_CORE", "fill-core-1", 1_500, "0.5")
        with self.assertRaisesRegex(ValueError, "FUNDING_POSITION_COVERAGE_INCOMPLETE"):
            self.project(events=[event], coverage_rows=rows)

    def test_event_recorded_after_coverage_watermark_is_rejected(self):
        rows = proofs()
        rows[0] = coverage("STRATEGY_CORE", end=4_001, recorded=4_500)
        event = fill("STRATEGY_CORE", "fill-core-1", 1_500, "0.5", recorded=4_600)
        with self.assertRaisesRegex(ValueError, "FUNDING_POSITION_EVENT_COVERAGE_INVALID"):
            self.project(events=[event], coverage_rows=rows)

    def test_duplicate_or_unsorted_settlements_are_rejected(self):
        for settlements in ([2_000, 2_000], [4_000, 2_000]):
            with self.subTest(settlements=settlements):
                with self.assertRaisesRegex(ValueError, "FUNDING_POSITION_SETTLEMENTS_INVALID"):
                    self.project(settlements=settlements)


if __name__ == "__main__":
    unittest.main()
