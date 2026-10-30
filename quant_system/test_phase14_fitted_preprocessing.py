"""Phase14 RED: fitted DataSieve/label pipeline future interventions."""
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from quant_system.phase14_fitted_preprocessing import (
    PipelineCausalityError, verify_model_bundle_seal,
    verify_fitted_row_invariance,
)


class FittedFeatures:
    steps = [("const", object()), ("scaler", object()), ("di", object())]

    def transform(self, x, outlier_check=False):
        assert outlier_check
        return x * 2.0, np.ones(len(x), dtype=int), None


class LeakingFeatures(FittedFeatures):
    def transform(self, x, outlier_check=False):
        return x * 2.0 + x.mean(axis=0), np.ones(len(x), dtype=int), None


class FittedLabels:
    steps = [("scaler", object())]

    def inverse_transform(self, y):
        return y * 0.5, None, None


class LeakingLabels(FittedLabels):
    def inverse_transform(self, y):
        return y * 0.5 + y.mean(), None, None


class Phase14FittedInterventionTests(unittest.TestCase):
    def setUp(self):
        self.row = pd.DataFrame({"%-price": [1.25], "%-volume": [4.0]})
        self.future = pd.DataFrame({"%-price": [2.0, 3.0, 4.0],
                                    "%-volume": [5.0, 6.0, 7.0]})
        self.expected = [2.5, 8.0]

    def test_fitted_pipeline_same_row_despite_future_intervention(self):
        out = verify_fitted_row_invariance(
            FittedFeatures(), FittedLabels(), self.row, self.future,
            self.expected, 1)
        self.assertEqual(out["feature_comparisons"], 2)
        self.assertEqual(out["label_comparisons"], 1)

    def test_future_sensitive_feature_scaler_must_fail(self):
        with self.assertRaisesRegex(
                PipelineCausalityError, "PHASE14_FUTURE_DEPENDENT_FEATURE_PIPELINE"):
            verify_fitted_row_invariance(
                LeakingFeatures(), FittedLabels(), self.row, self.future,
                [3.5, 12.0], 1)

    def test_future_sensitive_label_scaler_must_fail(self):
        with self.assertRaisesRegex(
                PipelineCausalityError, "PHASE14_FUTURE_DEPENDENT_LABEL_PIPELINE"):
            verify_fitted_row_invariance(
                FittedFeatures(), LeakingLabels(), self.row, self.future,
                self.expected, 1)

    def test_wrong_native_lightgbm_matrix_must_fail(self):
        with self.assertRaisesRegex(
                PipelineCausalityError, "PHASE14_FITTED_X_NATIVE_MISMATCH"):
            verify_fitted_row_invariance(
                FittedFeatures(), FittedLabels(), self.row, self.future,
                [2.5, 7.9], 1)

    def test_outlier_flag_mismatch_denied(self):
        with self.assertRaisesRegex(
                PipelineCausalityError, "PHASE14_FITTED_NATIVE_FLAG_MISMATCH"):
            verify_fitted_row_invariance(
                FittedFeatures(), FittedLabels(), self.row, self.future,
                self.expected, 0)

    def test_bundle_sha_must_match_sealed_git_digest_before_pickle(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bundle = root / "candidate.joblib"
            bundle.write_bytes(b"trusted synthetic placeholder; NEVER unpickle")
            from quant_system.phase13b_matrix import matrix_digest
            metadata = root / "candidate.json"
            metadata.write_text(json.dumps({"candidate_sha256": matrix_digest(bundle),
                "source_commit_sha": "0" * 40}))
            protocol = root / "protocol.json"
            protocol.write_text('{"holdout_start_utc":"2026-11-04T00:00:00Z"}')
            seal = root / "seal.json"
            seal.write_text(json.dumps({
                "candidate_bundle_sha256": matrix_digest(bundle),
                "candidate_metadata_sha256": matrix_digest(metadata),
                "protocol_sha256": matrix_digest(protocol),
                "source_commit_sha": "0" * 40,
                "full_model_pipeline_causality_verified": False,
                "live_orders_enabled": False
            }))
            self.assertTrue(verify_model_bundle_seal(
                bundle, metadata, protocol, seal))
            bundle.write_bytes(b"tampered")
            with self.assertRaisesRegex(
                    PipelineCausalityError, "PHASE14_BUNDLE_SHA_MISMATCH"):
                verify_model_bundle_seal(bundle, metadata, protocol, seal)


if __name__ == "__main__":
    unittest.main()
