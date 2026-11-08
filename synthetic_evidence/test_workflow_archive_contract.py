"""Regression contracts for the P1.8 GitHub Actions archive job."""

import unittest
from pathlib import Path


WORKFLOW_PATH = (
    Path(__file__).resolve().parents[1]
    / ".github"
    / "workflows"
    / "p1-8-synthetic-evidence.yml"
)


class ArchiveJobCheckoutContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
        if "  archive-evidence:\n" not in workflow:
            raise AssertionError("archive-evidence job is missing")
        cls.archive_job = workflow.split("  archive-evidence:\n", 1)[1]

    def test_archive_job_fetches_exact_source_sha_with_bounded_history(self):
        self.assertIn(
            'git fetch --no-tags --depth=1 origin "$SOURCE_SHA"',
            self.archive_job,
            "archive job must fetch the triggering source commit explicitly",
        )

    def test_archive_job_proves_source_is_ancestor_of_checked_out_branch_head(self):
        self.assertIn(
            'gh api "repos/${GITHUB_REPOSITORY}/compare/${SOURCE_SHA}...${BRANCH_HEAD}" --jq .status',
            self.archive_job,
            "archive job must verify source-to-branch ancestry through GitHub compare",
        )
        self.assertIn(
            'test "$comparison_status" = "ahead" -o "$comparison_status" = "identical"',
            self.archive_job,
            "archive must fail closed unless branch head contains the triggering source",
        )

    def test_archive_job_exposes_token_for_authenticated_ancestry_check(self):
        self.assertIn("GH_TOKEN: ${{ github.token }}", self.archive_job)


if __name__ == "__main__":
    unittest.main()
