"""Codemagic must accept Phase16 workflows while frozen OOS remains locked.

This test uses only Python stdlib so it can run before pinned FreqAI install.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


class Phase16CodemagicYamlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (ROOT / "codemagic.yaml").read_text(encoding="utf8")
        cls.frozen = cls.source.split(
            "  dual-strategy-frozen-30d-oos:", 1)[1]

    def test_no_empty_approval_variable_accepted_by_codemagic(self):
        self.assertNotRegex(
            self.frozen,
            r'(?m)^\s+PHASE16_APPROVAL_COMMIT:\s*(""|\x27\x27)?\s*$')
        self.assertRegex(
            self.frozen,
            r'(?m)^\s+PHASE16_APPROVAL_COMMIT:\s*"409d446bb186a8e2ea0189df26057a9df7e839de"\s*$')

    def test_approval_is_a_40_character_git_sha_and_placeholder_is_denied(self):
        self.assertIn(
            '[[ "$PHASE16_APPROVAL_COMMIT" =~ ^[0-9a-f]{40}$ ]]',
            self.frozen)
        self.assertIn(
            "OOS_ALL_26_FOLD_RELEASE_GATE_NOT_SIGNED",
            self.frozen)
        self.assertIn(
            '[[ "$PHASE16_APPROVAL_COMMIT" == "409d446bb186a8e2ea0189df26057a9df7e839de" ]]',
            self.frozen)
        self.assertTrue(
            re.fullmatch(r"[0-9a-f]{40}",
                         "409d446bb186a8e2ea0189df26057a9df7e839de"))

    def test_oos_still_locked_until_december_4(self):
        self.assertIn("1796342400", self.frozen)
        self.assertIn(
            "OOS_WINDOW_NOT_COMPLETE_UNTIL_2026_12_04_UTC",
            self.frozen)

    def test_phase16_original_26_fold_job_is_unchanged(self):
        self.assertIn(
            "  dual-strategy-phase16-all-26-original-fit:",
            self.source)
        self.assertIn(
            "quant_system.phase16_all_fold_fit",
            self.source)


if __name__ == "__main__":
    unittest.main()
