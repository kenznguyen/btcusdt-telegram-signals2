"""TDD contract tests for bounded L4M-08 claim-discipline validation."""
import unittest

from ci.t0_l4_claim_discipline import ClaimDisciplineError, audit_crosswalk

EXPECTED = {
    1: "PARTIAL",
    2: "NOT VERIFIED",
    3: "PARTIAL — DESIGN ONLY / NOT IMPLEMENTED",
    4: "PARTIAL — SYNTHETIC/CI ONLY",
    5: "PARTIAL — SYNTHETIC MODEL ONLY",
    6: "PARTIAL — SYNTHETIC POLICY ONLY",
    7: "PARTIAL — SYNTHETIC MODEL ONLY",
    8: "DOCUMENTARY PASS ONLY",
    9: "OWNER-WAIVED / NOT MANDATORY",
    10: "NOT VERIFIED / PENDING OWNER ASSESSMENT",
}


def make_crosswalk(statuses=None, aggregate="AGGREGATE BLOCKED"):
    statuses = dict(EXPECTED if statuses is None else statuses)
    lines = [
        "# T0 L4-Minimum — Control-to-Source Crosswalk",
        f"Status: DERIVED CROSSWALK ONLY — NO CONTROL ACCEPTANCE — {aggregate}",
        "",
        "| Control | Sources | CI | Disposition |",
        "|---|---|---|---|",
    ]
    for number, status in statuses.items():
        label = "Independent reviewer" if number == 9 else "Control"
        evidence = {
            1: "No complete owner-controlled package.",
            7: "No WORM/immutability claim is made.",
        }.get(number, "source")
        lines.append(f"| **L4M-{number:02d} {label}** | {evidence} | CI | **{status}** |")
    lines.extend([
        "",
        "L4M-07: No WORM/immutability claim is made.",
        "L4M-04: Owner-run offline verification is NOT VERIFIED.",
        "L4M-01: Owner custody is NOT VERIFIED.",
        "L4M-10: Owner acceptance is NOT VERIFIED.",
    ])
    return "\n".join(lines) + "\n"


class ClaimDisciplineTests(unittest.TestCase):
    def test_accepts_bounded_current_crosswalk_without_promoting_controls(self):
        result = audit_crosswalk(make_crosswalk(), source_commit="a" * 40)
        self.assertEqual("PASS", result["verdict"])
        self.assertEqual("BLOCKED / NOT VERIFIED", result["aggregate"])
        self.assertEqual(9, result["active_control_count"])
        self.assertEqual("OWNER-WAIVED / NOT MANDATORY", result["controls"]["L4M-09"])
        self.assertEqual("DOCUMENTARY PASS ONLY", result["controls"]["L4M-08"])
        self.assertEqual("a" * 40, result["source_commit"])

    def test_rejects_missing_control_row(self):
        statuses = dict(EXPECTED)
        del statuses[4]
        with self.assertRaisesRegex(ClaimDisciplineError, "CONTROL_SET_MISMATCH"):
            audit_crosswalk(make_crosswalk(statuses))

    def test_rejects_duplicate_control_row(self):
        text = make_crosswalk() + "| **L4M-01 duplicate** | source | CI | **PARTIAL** |\n"
        with self.assertRaisesRegex(ClaimDisciplineError, "DUPLICATE_CONTROL"):
            audit_crosswalk(text)

    def test_rejects_unsupported_control_status_promotion(self):
        statuses = dict(EXPECTED)
        statuses[1] = "PASS"
        with self.assertRaisesRegex(ClaimDisciplineError, "CONTROL_STATUS_UNSUPPORTED"):
            audit_crosswalk(make_crosswalk(statuses))

    def test_rejects_aggregate_pass_claim(self):
        with self.assertRaisesRegex(ClaimDisciplineError, "AGGREGATE_STATUS_UNSUPPORTED"):
            audit_crosswalk(make_crosswalk(aggregate="AGGREGATE PASS"))

    def test_rejects_l4m09_as_mandatory_or_passed(self):
        statuses = dict(EXPECTED)
        statuses[9] = "PASS"
        with self.assertRaisesRegex(ClaimDisciplineError, "CONTROL_STATUS_UNSUPPORTED"):
            audit_crosswalk(make_crosswalk(statuses))

    def test_rejects_unsupported_worm_claim(self):
        text = make_crosswalk().replace(
            "No WORM/immutability claim is made.",
            "WORM: PASS",
        )
        with self.assertRaisesRegex(ClaimDisciplineError, "UNSUPPORTED_ASSURANCE_CLAIM"):
            audit_crosswalk(text)

    def test_rejects_independent_assurance_claim(self):
        text = make_crosswalk() + "\nIndependent assurance: PASS\n"
        with self.assertRaisesRegex(ClaimDisciplineError, "UNSUPPORTED_ASSURANCE_CLAIM"):
            audit_crosswalk(text)

    def test_rejects_owner_acceptance_claim(self):
        text = make_crosswalk() + "\nOwner acceptance: PASS\n"
        with self.assertRaisesRegex(ClaimDisciplineError, "UNSUPPORTED_ASSURANCE_CLAIM"):
            audit_crosswalk(text)

    def test_rejects_runtime_acceptance_claim(self):
        text = make_crosswalk() + "\nRuntime accepted\n"
        with self.assertRaisesRegex(ClaimDisciplineError, "UNSUPPORTED_ASSURANCE_CLAIM"):
            audit_crosswalk(text)

    def test_rejects_missing_owner_only_disclaimers(self):
        text = make_crosswalk().replace("No complete owner-controlled package", "Package").replace("Owner custody is NOT VERIFIED.", "Owner custody.")
        with self.assertRaisesRegex(ClaimDisciplineError, "REQUIRED_LIMITATION_MISSING"):
            audit_crosswalk(text)


if __name__ == "__main__":
    unittest.main()
