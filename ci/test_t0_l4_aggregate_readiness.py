"""Fail-closed contracts for L4M-10 aggregate readiness; never issue owner acceptance."""
import unittest

from ci.t0_l4_aggregate_readiness import evaluate_aggregate, ACTIVE_CONTROL_IDS

PASS_CONTROLS = {control_id: "PASS" for control_id in ACTIVE_CONTROL_IDS}
CURRENT_CONTROLS = {
    "L4M-01": "PARTIAL",
    "L4M-02": "NOT VERIFIED",
    "L4M-03": "PARTIAL — DESIGN ONLY / NOT IMPLEMENTED",
    "L4M-04": "PARTIAL — SYNTHETIC/CI ONLY",
    "L4M-05": "PARTIAL — SYNTHETIC MODEL ONLY",
    "L4M-06": "PARTIAL — SYNTHETIC POLICY ONLY",
    "L4M-07": "PARTIAL — SYNTHETIC MODEL ONLY",
    "L4M-08": "DOCUMENTARY PASS ONLY",
    "L4M-10": "NOT VERIFIED / PENDING OWNER ASSESSMENT",
}
BASELINE_ID = "T0-L4-BASELINE-2026-11-12-001"
BASELINE_SHA = "a" * 64


def valid_owner_disposition(**overrides):
    value = {
        "schema_version": "T0_L4_OWNER_DISPOSITION_V1",
        "decision": "ACCEPT",
        "baseline_id": BASELINE_ID,
        "baseline_sha256": BASELINE_SHA,
        "assessor_identity": "owner@example.invalid",
        "assessor_role": "SYSTEM_OWNER",
        "conflict_disclosure": "NONE",
        "disposition_timestamp": "2026-11-12T12:00:00Z",
    }
    value.update(overrides)
    return value


class AggregateReadinessTests(unittest.TestCase):
    def test_current_crosswalk_is_blocked_and_excludes_waived_l4m09(self):
        result = evaluate_aggregate(CURRENT_CONTROLS)
        self.assertEqual("BLOCKED / NOT VERIFIED", result["aggregate_verdict"])
        self.assertEqual(9, result["active_control_count"])
        self.assertNotIn("L4M-09", result["controls"])
        self.assertIn("ACTIVE_CONTROLS_NOT_ALL_PASS", result["reason_codes"])
        self.assertIn("FROZEN_BASELINE_REQUIRED", result["reason_codes"])
        self.assertIn("OWNER_DISPOSITION_REQUIRED", result["reason_codes"])

    def test_rejects_missing_or_extra_active_control_ids(self):
        missing = dict(PASS_CONTROLS)
        del missing["L4M-04"]
        self.assertIn("CONTROL_SET_MISMATCH", evaluate_aggregate(missing)["reason_codes"])
        extra = dict(PASS_CONTROLS, **{"L4M-09": "OWNER-WAIVED / NOT MANDATORY"})
        self.assertIn("CONTROL_SET_MISMATCH", evaluate_aggregate(extra)["reason_codes"])

    def test_unknown_or_partial_status_never_counts_as_pass(self):
        controls = dict(PASS_CONTROLS)
        controls["L4M-03"] = "UNKNOWN"
        result = evaluate_aggregate(controls, baseline_id=BASELINE_ID, baseline_sha256=BASELINE_SHA)
        self.assertEqual("BLOCKED / NOT VERIFIED", result["aggregate_verdict"])
        self.assertIn("ACTIVE_CONTROLS_NOT_ALL_PASS", result["reason_codes"])

    def test_all_controls_pass_without_frozen_baseline_is_not_accepted(self):
        result = evaluate_aggregate(PASS_CONTROLS)
        self.assertEqual("BLOCKED / NOT VERIFIED", result["aggregate_verdict"])
        self.assertIn("FROZEN_BASELINE_REQUIRED", result["reason_codes"])

    def test_frozen_baseline_without_owner_disposition_is_not_accepted(self):
        result = evaluate_aggregate(PASS_CONTROLS, baseline_id=BASELINE_ID, baseline_sha256=BASELINE_SHA)
        self.assertEqual("BLOCKED / NOT VERIFIED", result["aggregate_verdict"])
        self.assertIn("OWNER_DISPOSITION_REQUIRED", result["reason_codes"])

    def test_mismatched_owner_disposition_baseline_fails_closed(self):
        disposition = valid_owner_disposition(baseline_sha256="b" * 64)
        result = evaluate_aggregate(
            PASS_CONTROLS, baseline_id=BASELINE_ID, baseline_sha256=BASELINE_SHA,
            owner_disposition=disposition,
        )
        self.assertEqual("BLOCKED / NOT VERIFIED", result["aggregate_verdict"])
        self.assertIn("OWNER_DISPOSITION_BASELINE_MISMATCH", result["reason_codes"])

    def test_structurally_valid_owner_disposition_still_requires_manual_finalization(self):
        result = evaluate_aggregate(
            PASS_CONTROLS, baseline_id=BASELINE_ID, baseline_sha256=BASELINE_SHA,
            owner_disposition=valid_owner_disposition(),
        )
        self.assertEqual("OWNER_DISPOSITION_PRESENT — MANUAL FINALIZATION REQUIRED", result["aggregate_verdict"])
        self.assertTrue(result["owner_disposition_structurally_valid"])
        self.assertEqual("NOT_VERIFIED_BY_THIS_CHECK", result["owner_identity_authentication"])
        self.assertFalse(result["claims_l4_minimum_accepted"])

    def test_rejected_owner_disposition_never_becomes_acceptance(self):
        result = evaluate_aggregate(
            PASS_CONTROLS, baseline_id=BASELINE_ID, baseline_sha256=BASELINE_SHA,
            owner_disposition=valid_owner_disposition(decision="REJECT"),
        )
        self.assertEqual("OWNER_REJECTED", result["aggregate_verdict"])
        self.assertFalse(result["claims_l4_minimum_accepted"])

    def test_missing_assessor_or_conflict_disclosure_is_invalid(self):
        for changes in (
            {"assessor_identity": ""},
            {"assessor_role": ""},
            {"conflict_disclosure": ""},
            {"disposition_timestamp": "2026-11-12T12:00:00"},
        ):
            with self.subTest(changes=changes):
                result = evaluate_aggregate(
                    PASS_CONTROLS, baseline_id=BASELINE_ID, baseline_sha256=BASELINE_SHA,
                    owner_disposition=valid_owner_disposition(**changes),
                )
                self.assertIn("OWNER_DISPOSITION_INVALID", result["reason_codes"])

    def test_baseline_digest_must_be_sha256(self):
        result = evaluate_aggregate(PASS_CONTROLS, baseline_id=BASELINE_ID, baseline_sha256="not-a-digest")
        self.assertIn("FROZEN_BASELINE_REQUIRED", result["reason_codes"])


if __name__ == "__main__":
    unittest.main()
