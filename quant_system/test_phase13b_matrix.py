"""Phase13B: actual LightGBM matrix capture must be byte-verifiable and fail closed."""
import hashlib
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from quant_system.phase13b_matrix import (
    MatrixEvidenceError, record_matrix, read_matrix, matrix_digest
)

class MatrixEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.rows = pd.DataFrame({
            "%-price": [0.1, 0.2, 0.3],
            "%-volume": [1.1, 1.2, 1.3],
        })

    def tearDown(self):
        self.tmp.cleanup()

    def record(self, stage="FIT_TRAIN", x=None, times=None):
        return record_matrix(
            self.root, stage=stage, fold="test-fold",
            model_sha="sha256:" + "a" * 64,
            features=self.rows if x is None else x,
            timestamps=[900000, 1800000, 2700000] if times is None else times,
            labels=np.array([0.1, 0.2, 0.3]) if stage != "PREDICT" else None,
            weights=np.array([1., 1., 1.]) if stage != "PREDICT" else None,
            flags=np.array([1, 0, 1]) if stage == "PREDICT" else None,
        )

    def test_fit_matrix_roundtrip_all_real_values(self):
        event = self.record()
        stored = read_matrix(self.root, event)
        self.assertEqual(event["n_features"], 2)
        self.assertEqual(event["n_rows"], 3)
        self.assertEqual(stored["columns"], ["%-price", "%-volume"])
        self.assertTrue(np.array_equal(stored["values"], self.rows.to_numpy()))
        self.assertEqual(stored["timestamps"], [900000, 1800000, 2700000])
        self.assertEqual(stored["weights"], [1., 1., 1.])
        self.assertEqual(stored["labels"], [0.1, 0.2, 0.3])

    def test_predict_matrix_and_flags_bound_to_same_rows(self):
        event = self.record(stage="PREDICT")
        result = read_matrix(self.root, event)
        self.assertEqual(result["flags"], [1, 0, 1])
        self.assertEqual(result["labels"], [])
        self.assertEqual(result["weights"], [])

    def test_target_column_rejected_before_capture(self):
        bad = self.rows.copy()
        bad["&-future_return"] = .9
        with self.assertRaisesRegex(MatrixEvidenceError, "TARGET"):
            self.record(x=bad)

    def test_infinite_or_missing_feature_rejected(self):
        bad = self.rows.copy()
        bad.loc[0, "%-price"] = float("nan")
        with self.assertRaisesRegex(MatrixEvidenceError, "NONFINITE"):
            self.record(x=bad)

    def test_tampered_matrix_digest_rejected(self):
        event = self.record()
        path = self.root / event["path"]
        with path.open("ab") as f:
            f.write(b"modified")
        with self.assertRaisesRegex(MatrixEvidenceError, "SHA_MISMATCH"):
            read_matrix(self.root, event)

    def test_training_timestamps_must_be_ascending(self):
        with self.assertRaisesRegex(MatrixEvidenceError, "TIME"):
            self.record(times=[900000, 2700000, 1800000])

    def test_read_prevents_path_traversal(self):
        event = self.record()
        event["path"] = "../other.npz"
        with self.assertRaisesRegex(MatrixEvidenceError, "PATH"):
            read_matrix(self.root, event)

    def test_duplicate_capture_cannot_silently_overwrite(self):
        self.record()
        with self.assertRaisesRegex(MatrixEvidenceError, "DUPLICATE"):
            self.record()

if __name__ == "__main__":
    unittest.main()
