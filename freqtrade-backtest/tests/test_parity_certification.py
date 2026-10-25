import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from parity_certification import certify


SHA = "a" * 64


class ParityCertificationTest(unittest.TestCase):
    def test_empty_traces_never_pass(self):
        result = certify([], [], source_commit="1234567", dataset_sha256=SHA)
        self.assertFalse(result["verified"])
        self.assertEqual(result["reason"], "empty_trace")

    def test_missing_dataset_fingerprint_rejected(self):
        with self.assertRaises(ValueError):
            certify([], [], source_commit="1234567", dataset_sha256="missing")

    def test_invalid_commit_rejected(self):
        with self.assertRaises(ValueError):
            certify([], [], source_commit="", dataset_sha256=SHA)


if __name__ == "__main__":
    unittest.main()
