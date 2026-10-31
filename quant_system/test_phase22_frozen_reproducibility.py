"""Phase22 RED tests: reproducibility of the exact Git-preserved frozen model."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from quant_system.phase22_frozen_reproducibility import (
    FrozenReproducibilityError,
    verify_preserved_snapshot,
)


class Phase22FrozenReproducibilityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.bundle = self.root / "preserved.joblib"
        self.original = self.root / "original.joblib"
        self.metadata = self.root / "metadata.json"
        self.protocol = self.root / "protocol.json"
        self.seal = self.root / "seal.json"
        self.bundle.write_bytes(b"immutable synthetic model bytes")
        self.original.write_bytes(b"immutable synthetic model bytes")
        self.metadata.write_text(json.dumps({
            "schemaVersion": 1,
            "candidate_sha256": "sha256:" + hashlib.sha256(self.bundle.read_bytes()).hexdigest(),
            "model_sha256": "sha256:" + "a" * 64,
            "model_identifier": "chart-pro-okx-shadow-v1",
            "source_commit_sha": "082edc082996425f61f48c952be41fb037564103",
            "training_end_ms": 1792965600000,
            "ordered_feature_columns": ["%-feature-a", "%-feature-b"],
            "sealed_in_git": False,
            "oos_certified": False,
        }), encoding="utf8")
        self.protocol.write_text(json.dumps({
            "protocol": "PHASE13B_PROSPECTIVE_FROZEN_MODEL_OOS",
            "holdout_start_utc": "2026-11-04T00:00:00Z",
            "holdout_end_utc": "2026-12-04T00:00:00Z",
            "model_identifier": "chart-pro-okx-shadow-v1",
            "sealed_in_git": False,
            "frozen_model_policy": {
                "retrain_inside_holdout": False,
                "tune_parameters_using_holdout": False,
            },
            "certification": {
                "independent_oos_verified": False,
                "oos_certified": False,
                "ai_promotion_eligible": False,
                "live_orders_enabled": False,
            },
        }), encoding="utf8")
        metadata_sha = "sha256:" + hashlib.sha256(self.metadata.read_bytes()).hexdigest()
        protocol_sha = "sha256:" + hashlib.sha256(self.protocol.read_bytes()).hexdigest()
        self.seal.write_text(json.dumps({
            "type": "PHASE13B_PRE_HOLDOUT_SHA256_SEAL",
            "candidate_bundle_sha256": "sha256:" + hashlib.sha256(self.bundle.read_bytes()).hexdigest(),
            "candidate_metadata_sha256": metadata_sha,
            "protocol_sha256": protocol_sha,
            "source_commit_sha": "082edc082996425f61f48c952be41fb037564103",
            "model_booster_sha256": "sha256:" + "a" * 64,
            "model_identifier": "chart-pro-okx-shadow-v1",
            "training_end_ms": 1792965600000,
            "feature_column_count": 2,
            "holdout_start_utc": "2026-11-04T00:00:00Z",
            "holdout_end_utc": "2026-12-04T00:00:00Z",
            "holdout_retraining_allowed": False,
            "holdout_tuning_allowed": False,
            "independent_oos_verified": False,
            "oos_certified": False,
            "ai_promotion_eligible": False,
            "live_orders_enabled": False,
        }), encoding="utf8")
        self.registered = {
            "bundle": "sha256:" + hashlib.sha256(self.bundle.read_bytes()).hexdigest(),
            "metadata": metadata_sha,
            "protocol": protocol_sha,
            "source": "082edc082996425f61f48c952be41fb037564103",
        }

    def verify(self):
        with patch.multiple(
            "quant_system.phase22_frozen_reproducibility",
            REGISTERED_BUNDLE_SHA=self.registered["bundle"],
            REGISTERED_METADATA_SHA=self.registered["metadata"],
            REGISTERED_PROTOCOL_SHA=self.registered["protocol"],
            REGISTERED_SOURCE_COMMIT=self.registered["source"],
        ):
            return verify_preserved_snapshot(
                self.bundle, self.original, self.metadata, self.protocol, self.seal
            )

    def test_exact_preserved_bytes_and_provenance_are_verified(self):
        report = self.verify()
        self.assertTrue(report["exact_original_bundle_bytes_verified"])
        self.assertEqual(report["candidate_bundle_sha256"], self.registered["bundle"])
        self.assertEqual(report["source_commit_sha"], self.registered["source"])
        self.assertFalse(report["independent_oos_verified"])
        self.assertFalse(report["oos_certified"])
        self.assertFalse(report["ai_promotion_eligible"])
        self.assertFalse(report["live_orders_enabled"])

    def test_one_byte_bundle_tampering_is_rejected(self):
        self.bundle.write_bytes(self.bundle.read_bytes() + b"x")
        with self.assertRaisesRegex(FrozenReproducibilityError, "PHASE22_BUNDLE_SHA_MISMATCH"):
            self.verify()

    def test_preserved_bundle_must_match_original_archive_bytes(self):
        self.original.write_bytes(b"different original bytes")
        with self.assertRaisesRegex(FrozenReproducibilityError, "PHASE22_ORIGINAL_BYTES_MISMATCH"):
            self.verify()

    def test_metadata_tampering_is_rejected(self):
        self.metadata.write_text(self.metadata.read_text() + " ", encoding="utf8")
        with self.assertRaisesRegex(FrozenReproducibilityError, "PHASE22_METADATA_SHA_MISMATCH"):
            self.verify()

    def test_protocol_tampering_is_rejected(self):
        self.protocol.write_text(self.protocol.read_text().replace("2026-12-04", "2026-12-05"), encoding="utf8")
        with self.assertRaisesRegex(FrozenReproducibilityError, "PHASE22_PROTOCOL_SHA_MISMATCH"):
            self.verify()

    def test_holdout_policy_must_remain_frozen_and_paper_only(self):
        seal = json.loads(self.seal.read_text(encoding="utf8"))
        seal["live_orders_enabled"] = True
        self.seal.write_text(json.dumps(seal), encoding="utf8")
        with self.assertRaisesRegex(FrozenReproducibilityError, "PHASE22_UNSAFE_SEAL"):
            self.verify()

    def test_feature_schema_must_be_unique_and_match_seal_count(self):
        metadata = json.loads(self.metadata.read_text(encoding="utf8"))
        metadata["ordered_feature_columns"] = ["%-feature-a", "%-feature-a"]
        self.metadata.write_text(json.dumps(metadata), encoding="utf8")
        self.registered["metadata"] = "sha256:" + hashlib.sha256(self.metadata.read_bytes()).hexdigest()
        seal = json.loads(self.seal.read_text(encoding="utf8"))
        seal["candidate_metadata_sha256"] = self.registered["metadata"]
        self.seal.write_text(json.dumps(seal), encoding="utf8")
        with self.assertRaisesRegex(FrozenReproducibilityError, "PHASE22_INVALID_FEATURE_SCHEMA"):
            self.verify()


if __name__ == "__main__":
    unittest.main()
