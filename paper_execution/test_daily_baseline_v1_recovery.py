"""Read-only evidence contract for legacy daily baseline v1 recovery."""
import copy
import unittest

from paper_execution.daily_baseline_v1_recovery import (
    assess_daily_baseline_v1_recovery_manifest,
)


def complete_manifest():
    boundary = (1_800_000_000_000 // 86_400_000 + 1) * 86_400_000
    cutover = boundary - 86_400_000
    digest = "sha256:" + "a" * 64
    source_digest = "sha256:" + "b" * 64
    return {
        "baseline": {
            "baseline_id": f"daily-equity-baseline:1:{boundary}",
            "utc_day_ms": boundary,
            "equity_quote": "100",
            "mark_id": "mark:boundary",
            "cutover_id": "cutover:verified",
            "replay_digest": digest,
            "algorithm_version": "daily-equity-replay-v1",
        },
        "audit": {
            "audit_id": f"daily-equity-baseline-audit:1:{boundary}",
            "event_type": "DAILY_BASELINE_CREATED",
            "replay_digest": digest,
            "canonical": True,
            "digest_verified": True,
            "replay_equity_quote": "100",
            "mark_id": "mark:boundary",
            "cutover_id": "cutover:verified",
            "algorithm_version": "daily-equity-replay-v1",
        },
        "cutover": {
            "cutover_id": "cutover:verified",
            "cutover_at_ms": cutover,
            "verified": True,
            "immutable": True,
            "ledger_snapshots": {
                "STRATEGY_CORE": True,
                "AI_FREQAI": True,
                "LEGACY_UNATTRIBUTED": True,
            },
        },
        "execution": {
            "status": "VERIFIED",
            "start_at_ms": cutover,
            "end_at_ms": boundary,
            "all_events_provenanced": True,
            "all_fees_explicit_usdt": True,
            "no_late_events": True,
            "all_ledgers_complete": True,
        },
        "funding": {
            "status": "VERIFIED",
            "start_at_ms": cutover,
            "end_at_ms": boundary,
            "all_events_provenanced": True,
            "no_unknown_amounts": True,
        },
        "mark": {
            "mark_id": "mark:boundary",
            "effective_at_ms": boundary,
            "verified": True,
            "source_snapshot_id": "snapshot:market",
            "dataset_version": "dataset:v1",
            "payload_hash": source_digest,
            "raw_payload_bytes_rehashed": True,
        },
        "risk_state": {
            "independently_verified": True,
            "utc_day_ms": boundary,
            "equity_quote": "100",
            "high_water_mark_quote": "105",
            "version": 7,
            "risk_ready": True,
            "mark_id": "mark:boundary",
            "source_snapshot_id": "snapshot:risk-state",
            "payload_hash": source_digest,
            "raw_payload_bytes_rehashed": True,
        },
    }


class DailyBaselineV1RecoveryEvidenceContractTest(unittest.TestCase):
    def test_complete_evidence_is_only_eligible_for_manual_review(self):
        result = assess_daily_baseline_v1_recovery_manifest(complete_manifest())
        self.assertEqual(result["status"], "ELIGIBLE_FOR_MANUAL_REVIEW")
        self.assertTrue(result["eligible_for_manual_review"])
        self.assertFalse(result["migration_authorized"])
        self.assertFalse(result["mutation_performed"])
        self.assertEqual(result["missing_evidence"], [])
        self.assertEqual(result["contradictions"], [])

    def test_missing_execution_funding_and_raw_source_evidence_blocks(self):
        manifest = complete_manifest()
        manifest["execution"]["no_late_events"] = False
        manifest["funding"]["status"] = "UNKNOWN"
        manifest["mark"]["raw_payload_bytes_rehashed"] = False
        result = assess_daily_baseline_v1_recovery_manifest(manifest)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertFalse(result["eligible_for_manual_review"])
        self.assertTrue(any("execution.no_late_events" in item for item in result["missing_evidence"]))
        self.assertTrue(any("funding.status" in item for item in result["missing_evidence"]))
        self.assertTrue(any("mark.raw_payload_bytes_rehashed" in item for item in result["missing_evidence"]))

    def test_missing_one_ledger_cutover_snapshot_blocks(self):
        manifest = complete_manifest()
        manifest["cutover"]["ledger_snapshots"]["LEGACY_UNATTRIBUTED"] = False
        result = assess_daily_baseline_v1_recovery_manifest(manifest)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertTrue(any("LEGACY_UNATTRIBUTED" in item for item in result["missing_evidence"]))

    def test_baseline_audit_equity_mark_and_cutover_conflicts_block(self):
        manifest = complete_manifest()
        manifest["audit"]["replay_equity_quote"] = "101"
        manifest["audit"]["mark_id"] = "mark:other"
        manifest["cutover"]["cutover_id"] = "cutover:other"
        result = assess_daily_baseline_v1_recovery_manifest(manifest)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertIn("audit.replay_equity_quote != baseline.equity_quote", result["contradictions"])
        self.assertIn("audit.mark_id != baseline.mark_id", result["contradictions"])
        self.assertIn("cutover.cutover_id != baseline.cutover_id", result["contradictions"])

    def test_risk_state_hwm_version_day_and_mark_conflicts_block(self):
        manifest = complete_manifest()
        manifest["risk_state"]["high_water_mark_quote"] = "99"
        manifest["risk_state"]["version"] = 0
        manifest["risk_state"]["utc_day_ms"] += 86_400_000
        manifest["risk_state"]["mark_id"] = "mark:other"
        result = assess_daily_baseline_v1_recovery_manifest(manifest)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertGreaterEqual(len(result["contradictions"]), 3)

    def test_invalid_types_and_nonfinite_amounts_are_not_coerced(self):
        manifest = complete_manifest()
        manifest["execution"]["all_fees_explicit_usdt"] = "true"
        manifest["risk_state"]["high_water_mark_quote"] = "NaN"
        manifest["risk_state"]["version"] = "7"
        result = assess_daily_baseline_v1_recovery_manifest(manifest)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertGreaterEqual(len(result["missing_evidence"]), 2)

    def test_manifest_is_not_mutated_by_read_only_assessment(self):
        manifest = complete_manifest()
        before = copy.deepcopy(manifest)
        assess_daily_baseline_v1_recovery_manifest(manifest)
        self.assertEqual(manifest, before)


if __name__ == "__main__":
    unittest.main()
