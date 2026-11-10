"""L4-Minimum source-lineage and policy contract tests (GitHub-hosted, read-only)."""
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
MATRIX_SHA = "75db0d98134fd656d91a8545bc307c56595aebf7"
REGISTER_SHA = "cee949666da611a4efca7e7b51aea47ab4b13eff"
SUPERSEDED_MATRIX_SHA = "2ba85af550fb7e369ea39ade6d73878d78dbf6bc"
SUPERSEDED_REGISTER_SHA = "4ec993d23a7b6d282350d0dea0add0254cac87cb"

REGISTER = ROOT / "docs/evidence/T0_L4_MINIMUM_NINE_CONTROL_EVIDENCE_ACQUISITION_REGISTER_2026-11-10.md"
PLAN = ROOT / "docs/evidence/T0_L4_MINIMUM_AUTOMATION_PLAN_2026-11-10.md"
MATRIX = ROOT / "docs/evidence/p1-8/L4-MINIMUM-PROVENANCE-ACCEPTANCE-MATRIX.md"
SUPPORTING_DOCS = (
    ROOT / "docs/evidence/T0_L4_MINIMUM_POLICY_HISTORICAL_AUDIT_RECONCILIATION_2026-11-10.md",
    ROOT / "docs/evidence/T0_L4M02_SIGNER_SEPARATION_EXISTING_EVIDENCE_ASSESSMENT_2026-11-10.md",
    ROOT / "docs/evidence/T0_L4M08_CLAIM_DISCIPLINE_DOCUMENTARY_ASSESSMENT_2026-11-10.md",
    ROOT / "docs/evidence/T0_L4M10_FROZEN_BASELINE_OWNER_SELF_ASSESSMENT_READINESS_2026-11-10.md",
)


class T0L4MinimumLineageContractTests(unittest.TestCase):
    def test_register_points_to_current_acceptance_matrix_blob(self):
        self.assertIn(MATRIX_SHA, REGISTER.read_text())

    def test_automation_plan_points_to_current_register_blob(self):
        self.assertIn(REGISTER_SHA, PLAN.read_text())

    def test_automation_plan_points_to_current_matrix_blob(self):
        self.assertIn(MATRIX_SHA, PLAN.read_text())

    def test_supporting_documents_do_not_reference_superseded_blobs(self):
        for path in SUPPORTING_DOCS:
            with self.subTest(path=path.name):
                content = path.read_text()
                self.assertNotIn(SUPERSEDED_MATRIX_SHA, content)
                self.assertNotIn(SUPERSEDED_REGISTER_SHA, content)

    def test_supporting_documents_bind_to_current_matrix_and_register(self):
        expected = {
            SUPPORTING_DOCS[0]: (MATRIX_SHA,),
            SUPPORTING_DOCS[1]: (REGISTER_SHA,),
            SUPPORTING_DOCS[2]: (MATRIX_SHA, REGISTER_SHA),
            SUPPORTING_DOCS[3]: (MATRIX_SHA, REGISTER_SHA),
        }
        for path, digests in expected.items():
            with self.subTest(path=path.name):
                content = path.read_text()
                for digest in digests:
                    self.assertIn(digest, content)

    def test_matrix_keeps_approved_vps_github_custody_boundary(self):
        content = MATRIX.read_text()
        self.assertIn("No copy outside VPS and GitHub is required", content)
        self.assertIn("Simultaneous VPS+GitHub unavailability is explicitly outside", content)

    def test_matrix_keeps_nine_active_controls_and_owner_waiver(self):
        content = MATRIX.read_text()
        self.assertIn("L4M-09", content)
        self.assertIn("OWNER-WAIVED", content)
        self.assertIn("L4M-10", content)
        self.assertIn("NOT IMPLEMENTED, NOT EXECUTED, NOT ACCEPTED", content)


if __name__ == "__main__":
    unittest.main()
