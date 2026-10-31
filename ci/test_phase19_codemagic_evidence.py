"""Regression: Phase19 must use SHA-pinned ORIGINAL Phase14 PREDICT NPZ.

Phase16 subset intentionally includes only FIT_TRAIN/FIT_TEST matrices;
using it for native prediction parity is invalid.
"""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]

class Phase19CodemagicEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workflow=(ROOT/"codemagic.yaml").read_text(encoding="utf8").split(
            "  dual-strategy-phase19-native-forecast-reconciliation:",1)[1]

    def test_uses_predict_witness_in_original_phase14_zip(self):
        self.assertIn(
            'research_evidence/phase14-frozen-original-evidence.zip',
            self.workflow)
        self.assertIn(
            "b64f39bd70c27c8d6abed1795ee06504c108eed42ebdab98ce375a6449b5b035",
            self.workflow)
        self.assertNotIn(
            "phase16-all-26-original-fit-evidence.zip",self.workflow)

    def test_never_fits_or_runs_holdout(self):
        self.assertNotIn("quant_system.phase16_frozen_oos",self.workflow)
        self.assertNotIn("research_evidence/frozen-oos-20261104/holdout",self.workflow)
        self.assertIn(
            "quant_system.phase19_native_forecast_reconciliation",
            self.workflow)

    def test_original_git_seal_is_pre_holdout(self):
        self.assertIn("888efb11b613b42a2badb3bc8adfa19ff090f2bb",
                      self.workflow)
        self.assertIn("409d446bb186a8e2ea0189df26057a9df7e839de",
                      self.workflow)

if __name__ == "__main__":
    unittest.main()
