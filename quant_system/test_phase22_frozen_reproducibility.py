"""Phase22 RED/GREEN tests for exact frozen-model provenance reproducibility."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from quant_system.phase22_frozen_reproducibility import (
    FrozenReproducibilityError,
    verify_preserved_snapshot,
    verify_oos_eligibility,
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
            "latest_observed_label_end_ms": 1792964700000,
            "ordered_feature_columns": ["%-feature-a", "%-feature-b"],
            "sealed_in_git": False,
            "oos_certified": False,
        }), encoding="utf8")
        self.protocol.write_text(json.dumps({
            "protocol": "PHASE13B_PROSPECTIVE_FROZEN_MODEL_OOS",
            "status": "PRE_REGISTERED_PROTOCOL_CANDIDATE_NOT_SEALED",
            "holdout_start_utc": "2026-11-04T00:00:00Z",
            "holdout_end_utc": "2026-12-04T00:00:00Z",
            "holdout_days": 30,
            "model_identifier": "chart-pro-okx-shadow-v1",
            "sealed_in_git": False,
            "frozen_model_policy": {
                "retrain_inside_holdout": False,
                "tune_parameters_using_holdout": False,
                "change_strategy_or_features_after_seal": False,
                "reuse_existing_trained_model_with_fitted_datasieve_and_label_pipeline": True,
                "all_training_labels_end_before_holdout_start": True,
                "freeze_all_feature_scalers_and_outlier_transformers": True,
            },
            "data": {
                "only_closed_candles": True,
                "exact_holdout_15m_rows": 2880,
                "no_backfill_of_missing_holdout_candles": True,
                "no_use_of_holdout_rows_for_training_or_scalers": True,
            },
            "evaluation": {
                "no_real_orders": True,
                "automatic_promotion_allowed": False,
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

    def _verify_current_files(self):
        with patch.multiple(
            "quant_system.phase22_frozen_reproducibility",
            REGISTERED_BUNDLE_SHA=self.registered["bundle"],
            REGISTERED_METADATA_SHA=self.registered["metadata"],
            REGISTERED_PROTOCOL_SHA=self.registered["protocol"],
            REGISTERED_SOURCE_COMMIT=self.registered["source"],
            REGISTERED_FEATURE_COUNT=2,
        ):
            return verify_preserved_snapshot(
                self.bundle, self.original, self.metadata, self.protocol, self.seal,
            )

    def verify(self):
        return self._verify_current_files()

    def _verify_oos_current_files(self):
        with patch.multiple(
            "quant_system.phase22_frozen_reproducibility",
            REGISTERED_BUNDLE_SHA=self.registered["bundle"],
            REGISTERED_METADATA_SHA=self.registered["metadata"],
            REGISTERED_PROTOCOL_SHA=self.registered["protocol"],
            REGISTERED_SOURCE_COMMIT=self.registered["source"],
            REGISTERED_FEATURE_COUNT=2,
        ):
            return verify_oos_eligibility(
                self.bundle, self.original, self.metadata, self.protocol, self.seal,
                self.attestation, self.github_proof,
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
        self.assertFalse(report["pre_holdout_attestation_verified"])

    def test_unsealed_historical_bundle_reproduces_but_oos_gate_rejects(self):
        report = self.verify()
        self.assertTrue(report["exact_original_bundle_bytes_verified"])
        self.assertFalse(report["independent_oos_verified"])
        self.attestation = self.root / "attestation.json"
        self.github_proof = self.root / "github-commit.json"
        self.attestation.write_text("{}", encoding="utf8")
        self.github_proof.write_text("{}", encoding="utf8")
        with self.assertRaisesRegex(FrozenReproducibilityError, "PHASE22_PROTOCOL_NOT_SEALED"):
            self._verify_oos_current_files()

    def _write_valid_attestation_and_github_proof(self):
        protocol = json.loads(self.protocol.read_text(encoding="utf8"))
        protocol.update({
            "status": "SEALED_BY_EXTERNAL_ATTESTATION",
            "sealed_in_git": True,
            "source_commit_sha": self.registered["source"],
            "frozen_model_bundle_sha256": self.registered["bundle"].removeprefix("sha256:"),
            "frozen_model_metadata_sha256": self.registered["metadata"].removeprefix("sha256:"),
        })
        self.protocol.write_text(json.dumps(protocol), encoding="utf8")
        self.registered["protocol"] = "sha256:" + hashlib.sha256(self.protocol.read_bytes()).hexdigest()
        seal = json.loads(self.seal.read_text(encoding="utf8"))
        seal["protocol_sha256"] = self.registered["protocol"]
        self.seal.write_text(json.dumps(seal), encoding="utf8")
        attestation = {
            "attestation_type": "PHASE13B_PRE_HOLDOUT_EXTERNAL_ATTESTATION",
            "source_commit_sha": self.registered["source"],
            "model_bundle_sha256": self.registered["bundle"].removeprefix("sha256:"),
            "model_metadata_sha256": self.registered["metadata"].removeprefix("sha256:"),
            "protocol_sha256": self.registered["protocol"].removeprefix("sha256:"),
            "holdout_start_utc": "2026-11-04T00:00:00Z",
            "holdout_end_utc": "2026-12-04T00:00:00Z",
            "holdout_retraining_allowed": False,
            "holdout_tuning_allowed": False,
            "independent_oos_verified": False,
            "oos_certified": False,
            "ai_promotion_eligible": False,
            "live_orders_enabled": False,
        }
        proof = {
            "sha": "f9591bcda1b11f15a549f397aa211259346ed3f9",
            "commit": {"committer": {"date": "2026-10-31T16:18:24Z"}},
            "files": [{"filename": "research_evidence/frozen-model/phase13b-20261104/pre-holdout-attestation.json"}],
        }
        self.attestation = self.root / "attestation.json"
        self.github_proof = self.root / "github-commit.json"
        self.attestation.write_text(json.dumps(attestation), encoding="utf8")
        self.github_proof.write_text(json.dumps(proof), encoding="utf8")

    def verify_with_attestation(self):
        self._write_valid_attestation_and_github_proof()
        with patch.multiple(
            "quant_system.phase22_frozen_reproducibility",
            REGISTERED_BUNDLE_SHA=self.registered["bundle"],
            REGISTERED_METADATA_SHA=self.registered["metadata"],
            REGISTERED_PROTOCOL_SHA=self.registered["protocol"],
            REGISTERED_SOURCE_COMMIT=self.registered["source"],
            REGISTERED_FEATURE_COUNT=2,
        ):
            return verify_preserved_snapshot(
                self.bundle, self.original, self.metadata, self.protocol, self.seal,
                self.attestation, self.github_proof,
            )

    def test_unsealed_historical_protocol_is_rejected(self):
        self._write_valid_attestation_and_github_proof()
        protocol = json.loads(self.protocol.read_text(encoding="utf8"))
        protocol["status"] = "PRE_REGISTERED_PROTOCOL_CANDIDATE_NOT_SEALED"
        self.protocol.write_text(json.dumps(protocol), encoding="utf8")
        self.registered["protocol"] = "sha256:" + hashlib.sha256(self.protocol.read_bytes()).hexdigest()
        seal = json.loads(self.seal.read_text(encoding="utf8"))
        seal["protocol_sha256"] = self.registered["protocol"]
        self.seal.write_text(json.dumps(seal), encoding="utf8")
        attestation = json.loads(self.attestation.read_text(encoding="utf8"))
        attestation["protocol_sha256"] = self.registered["protocol"].removeprefix("sha256:")
        self.attestation.write_text(json.dumps(attestation), encoding="utf8")
        with self.assertRaisesRegex(FrozenReproducibilityError, "PHASE22_PROTOCOL_NOT_SEALED"):
            self._verify_oos_current_files()

    def test_protocol_null_provenance_hashes_are_rejected(self):
        self._write_valid_attestation_and_github_proof()
        protocol = json.loads(self.protocol.read_text(encoding="utf8"))
        protocol["frozen_model_bundle_sha256"] = None
        self.protocol.write_text(json.dumps(protocol), encoding="utf8")
        self.registered["protocol"] = "sha256:" + hashlib.sha256(self.protocol.read_bytes()).hexdigest()
        seal = json.loads(self.seal.read_text(encoding="utf8"))
        seal["protocol_sha256"] = self.registered["protocol"]
        self.seal.write_text(json.dumps(seal), encoding="utf8")
        attestation = json.loads(self.attestation.read_text(encoding="utf8"))
        attestation["protocol_sha256"] = self.registered["protocol"].removeprefix("sha256:")
        self.attestation.write_text(json.dumps(attestation), encoding="utf8")
        with self.assertRaisesRegex(FrozenReproducibilityError, "PHASE22_PROTOCOL_PROVENANCE_MISSING"):
            self._verify_oos_current_files()

    def test_attestation_cannot_enable_oos_or_ai_promotion(self):
        self._write_valid_attestation_and_github_proof()
        attestation = json.loads(self.attestation.read_text(encoding="utf8"))
        attestation["ai_promotion_eligible"] = True
        self.attestation.write_text(json.dumps(attestation), encoding="utf8")
        with self.assertRaisesRegex(FrozenReproducibilityError, "PHASE22_ATTESTATION_PROVENANCE_MISMATCH"):
            self._verify_oos_current_files()

    def test_missing_github_commit_proof_is_rejected(self):
        self._write_valid_attestation_and_github_proof()
        self.github_proof.write_text("{}", encoding="utf8")
        with self.assertRaisesRegex(FrozenReproducibilityError, "PHASE22_GITHUB_COMMIT_PROOF_MISSING"):
            self._verify_oos_current_files()

    def test_github_attestation_commit_must_precede_holdout(self):
        self._write_valid_attestation_and_github_proof()
        proof = json.loads(self.github_proof.read_text(encoding="utf8"))
        proof["commit"]["committer"]["date"] = "2026-11-04T00:00:00Z"
        self.github_proof.write_text(json.dumps(proof), encoding="utf8")
        with self.assertRaisesRegex(FrozenReproducibilityError, "PHASE22_ATTESTATION_NOT_PRE_HOLDOUT"):
            self._verify_oos_current_files()

    def test_github_proof_must_name_attestation_file(self):
        self._write_valid_attestation_and_github_proof()
        proof = json.loads(self.github_proof.read_text(encoding="utf8"))
        proof["files"] = [{"filename": "unrelated.txt"}]
        self.github_proof.write_text(json.dumps(proof), encoding="utf8")
        with self.assertRaisesRegex(FrozenReproducibilityError, "PHASE22_GITHUB_COMMIT_PROOF_MISSING"):
            self._verify_oos_current_files()

    def test_one_byte_bundle_tampering_is_rejected(self):
        self.verify()
        self.bundle.write_bytes(self.bundle.read_bytes() + b"x")
        with self.assertRaisesRegex(FrozenReproducibilityError, "PHASE22_BUNDLE_SHA_MISMATCH"):
            self._verify_current_files()

    def test_preserved_bundle_must_match_original_archive_bytes(self):
        self.verify()
        self.original.write_bytes(b"different original bytes")
        with self.assertRaisesRegex(FrozenReproducibilityError, "PHASE22_ORIGINAL_BYTES_MISMATCH"):
            self._verify_current_files()

    def test_metadata_tampering_is_rejected(self):
        self.verify()
        self.metadata.write_text(self.metadata.read_text() + " ", encoding="utf8")
        with self.assertRaisesRegex(FrozenReproducibilityError, "PHASE22_METADATA_SHA_MISMATCH"):
            self._verify_current_files()

    def test_protocol_tampering_is_rejected(self):
        self.verify()
        self.protocol.write_text(self.protocol.read_text().replace("2026-12-04", "2026-12-05"), encoding="utf8")
        with self.assertRaisesRegex(FrozenReproducibilityError, "PHASE22_PROTOCOL_SHA_MISMATCH"):
            self._verify_current_files()

    def test_holdout_policy_must_remain_frozen_and_paper_only(self):
        self.verify()
        seal = json.loads(self.seal.read_text(encoding="utf8"))
        seal["live_orders_enabled"] = True
        self.seal.write_text(json.dumps(seal), encoding="utf8")
        with self.assertRaisesRegex(FrozenReproducibilityError, "PHASE22_UNSAFE_SEAL"):
            self._verify_current_files()

    def test_feature_schema_must_be_unique_and_match_seal_count(self):
        self.verify()
        metadata = json.loads(self.metadata.read_text(encoding="utf8"))
        metadata["ordered_feature_columns"] = ["%-feature-a", "%-feature-a"]
        self.metadata.write_text(json.dumps(metadata), encoding="utf8")
        self.registered["metadata"] = "sha256:" + hashlib.sha256(self.metadata.read_bytes()).hexdigest()

        # Keep the fixture's provenance chain internally consistent so this
        # regression reaches feature-schema validation instead of failing early.
        protocol = json.loads(self.protocol.read_text(encoding="utf8"))
        protocol["frozen_model_metadata_sha256"] = self.registered["metadata"].removeprefix("sha256:")
        self.protocol.write_text(json.dumps(protocol), encoding="utf8")
        self.registered["protocol"] = "sha256:" + hashlib.sha256(self.protocol.read_bytes()).hexdigest()

        seal = json.loads(self.seal.read_text(encoding="utf8"))
        seal["candidate_metadata_sha256"] = self.registered["metadata"]
        seal["protocol_sha256"] = self.registered["protocol"]
        self.seal.write_text(json.dumps(seal), encoding="utf8")

        attestation = json.loads(self.attestation.read_text(encoding="utf8"))
        attestation["model_metadata_sha256"] = self.registered["metadata"].removeprefix("sha256:")
        attestation["protocol_sha256"] = self.registered["protocol"].removeprefix("sha256:")
        self.attestation.write_text(json.dumps(attestation), encoding="utf8")

        with self.assertRaisesRegex(FrozenReproducibilityError, "PHASE22_INVALID_FEATURE_SCHEMA"):
            self._verify_current_files()


if __name__ == "__main__":
    unittest.main()
