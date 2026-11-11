import base64
import copy
import hashlib
import json
import unittest

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

from pipeline.calibration_registry import (
    CalibrationVerificationError,
    apply_calibration_transform,
    calibrate_verified_prediction,
    signature_message,
    verify_calibration_manifest,
)

# RFC 8032 test-only seed; never use as a registry or production key.
TEST_ONLY_SEED = bytes.fromhex(
    "9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60"
)
TEST_ONLY_PRIVATE_KEY = Ed25519PrivateKey.from_private_bytes(TEST_ONLY_SEED)
TEST_ONLY_PUBLIC_KEY = TEST_ONLY_PRIVATE_KEY.public_key().public_bytes(
    Encoding.Raw, PublicFormat.Raw
)


def digest(data):
    return "sha256:" + hashlib.sha256(data).hexdigest()


def canonical(value):
    import rfc8785
    return rfc8785.dumps(value)


class CalibrationRegistryVerifierTest(unittest.TestCase):
    def setUp(self):
        self.artifact_object = {
            "artifact_schema": "ai-calibration-transform/v1",
            "transform_schema": "score-probability-map/v1",
            "calibration_method": "isotonic",
            "method_version": "1",
            "input_semantics": "absolute_predicted_return",
            "output_semantics": "direction_correct_probability",
            "label_definition_id": "direction-correct-at-horizon",
            "forecast_horizon_value": "900000",
            "forecast_horizon_unit": "ms",
            "knots": [
                {"score": "0", "probability": "0.5"},
                {"score": "0.01", "probability": "0.6"},
                {"score": "0.02", "probability": "0.8"},
                {"score": "0.03", "probability": "0.9"},
            ],
        }
        self.artifact = canonical(self.artifact_object)
        self.manifest = {
            "manifest_schema": "ai-calibration-manifest/v1",
            "manifest_id": "calibration-manifest-0001",
            "registry_namespace": "btc-usdt/ai-calibration",
            "record_sequence": "1",
            "previous_record_digest": "GENESIS",
            "record_type": "CALIBRATION_ARTIFACT",
            "calibration_id": "btc-direction-15m",
            "calibration_version": "v1",
            "artifact_path": "docs/registry/ai-calibration/artifacts/calibration-v1.json",
            "artifact_digest": digest(self.artifact),
            "artifact_size_bytes": str(len(self.artifact)),
            "artifact_media_type": "application/json",
            "calibration_method": "isotonic",
            "method_version": "1",
            "transform_schema": "score-probability-map/v1",
            "model_id": "btc-freqai",
            "model_version": "model-v1",
            "model_artifact_digest": digest(b"model"),
            "strategy_id": "ai-freqai",
            "strategy_version": "strategy-v1",
            "strategy_source_commit": "a" * 40,
            "training_dataset_id": "training-2026-01",
            "training_dataset_digest": digest(b"training"),
            "training_cutoff": "2026-01-01T00:00:00Z",
            "calibration_dataset_id": "calibration-2026-02",
            "calibration_dataset_digest": digest(b"calibration"),
            "calibration_start": "2026-02-01T00:00:00Z",
            "calibration_end": "2026-02-15T00:00:00Z",
            "label_definition_id": "direction-correct-at-horizon",
            "label_definition_digest": digest(b"label-v1"),
            "forecast_horizon_value": "900000",
            "forecast_horizon_unit": "ms",
            "sample_count": "10000",
            "evaluation_record_id": "evaluation-0001",
            "evaluation_record_digest": digest(b"evaluation"),
            "created_at": "2026-02-16T00:00:00Z",
            "publisher_id": "owner-calibration-publisher",
        }
        self.manifest_bytes = canonical(self.manifest)
        self.trust = {
            "key_id": "test-only-ed25519-key",
            "algorithm": "Ed25519",
            "public_key_base64": base64.b64encode(TEST_ONLY_PUBLIC_KEY).decode("ascii"),
            "public_key_fingerprint": digest(TEST_ONLY_PUBLIC_KEY),
            "signer_role": "CALIBRATION_SIGNER",
            "registry_namespace": self.manifest["registry_namespace"],
            "publisher_id": self.manifest["publisher_id"],
            "allowed_record_types": ["CALIBRATION_ARTIFACT"],
        }
        self.envelope = self.make_envelope()

    def make_envelope(self, manifest_bytes=None, manifest=None, key=TEST_ONLY_PRIVATE_KEY):
        payload = manifest if manifest is not None else self.manifest
        raw = manifest_bytes if manifest_bytes is not None else canonical(payload)
        statement = {
            "domain": "BTCUSDT-AI-CALIBRATION-MANIFEST-SIGNATURE-V1",
            "namespace": payload["registry_namespace"],
            "manifest_id": payload["manifest_id"],
            "manifest_schema": payload["manifest_schema"],
            "canonicalization_profile": "RFC8785-JCS",
            "digest_algorithm": "SHA-256",
            "manifest_digest": digest(raw),
            "manifest_size_bytes": str(len(raw)),
            "key_id": self.trust["key_id"],
            "signer_role": "CALIBRATION_SIGNER",
            "publisher_id": self.trust["publisher_id"],
        }
        signature = key.sign(signature_message(statement))
        return {
            "envelope_schema": "ai-calibration-signature-envelope/v1",
            "envelope_id": "signature-envelope-0001",
            "manifest_id": payload["manifest_id"],
            "manifest_schema": payload["manifest_schema"],
            "canonicalization_profile": "RFC8785-JCS",
            "digest_algorithm": "SHA-256",
            "manifest_digest": digest(raw),
            "manifest_size_bytes": str(len(raw)),
            "signature_algorithm": "Ed25519",
            "key_id": self.trust["key_id"],
            "signer_role": "CALIBRATION_SIGNER",
            "namespace": payload["registry_namespace"],
            "signature_base64": base64.b64encode(signature).decode("ascii"),
        }

    def verify(self, manifest_bytes=None, envelope=None, artifact=None, trust=None):
        return verify_calibration_manifest(
            self.manifest_bytes if manifest_bytes is None else manifest_bytes,
            self.envelope if envelope is None else envelope,
            self.artifact if artifact is None else artifact,
            self.trust if trust is None else trust,
        )

    def test_valid_exact_bytes_signature_pin_and_artifact_are_verified(self):
        result = self.verify()
        self.assertEqual(result["verification_status"], "SIGNATURE_VERIFIED_ONLY")
        self.assertEqual(result["manifest_digest"], digest(self.manifest_bytes))
        self.assertEqual(result["artifact_digest"], digest(self.artifact))
        self.assertEqual(result["key_id"], self.trust["key_id"])

    def test_noncanonical_manifest_bytes_are_rejected_before_signature_check(self):
        noncanonical = json.dumps(self.manifest, indent=2).encode("utf-8")
        envelope = self.make_envelope(manifest_bytes=noncanonical)
        with self.assertRaisesRegex(CalibrationVerificationError, "NONCANONICAL_MANIFEST"):
            self.verify(manifest_bytes=noncanonical, envelope=envelope)

    def test_duplicate_json_keys_are_rejected(self):
        raw = b'{"manifest_schema":"ai-calibration-manifest/v1","manifest_schema":"evil"}'
        with self.assertRaisesRegex(CalibrationVerificationError, "DUPLICATE_JSON_KEY"):
            self.verify(manifest_bytes=raw)

    def test_json_numbers_are_rejected_and_decimal_fields_are_strings(self):
        invalid = copy.deepcopy(self.manifest)
        invalid["sample_count"] = 10000
        raw = canonical(invalid)
        envelope = self.make_envelope(manifest_bytes=raw, manifest=invalid)
        with self.assertRaisesRegex(CalibrationVerificationError, "JSON_NUMBER_NOT_ALLOWED"):
            self.verify(manifest_bytes=raw, envelope=envelope)

    def test_unknown_or_missing_manifest_fields_are_rejected(self):
        invalid = copy.deepcopy(self.manifest)
        invalid["unreviewed_extension"] = "value"
        raw = canonical(invalid)
        with self.assertRaisesRegex(CalibrationVerificationError, "MANIFEST_SCHEMA_MISMATCH"):
            self.verify(manifest_bytes=raw, envelope=self.make_envelope(raw, invalid))
        invalid = copy.deepcopy(self.manifest)
        invalid.pop("publisher_id")
        raw = canonical(invalid)
        with self.assertRaisesRegex(CalibrationVerificationError, "MANIFEST_SCHEMA_MISMATCH"):
            self.verify(manifest_bytes=raw, envelope=self.make_envelope(raw, invalid))

    def test_manifest_mutation_and_signature_mutation_are_rejected(self):
        changed = copy.deepcopy(self.manifest)
        changed["model_version"] = "attacker-model"
        raw = canonical(changed)
        with self.assertRaises(CalibrationVerificationError):
            self.verify(manifest_bytes=raw)
        envelope = copy.deepcopy(self.envelope)
        envelope["signature_base64"] = base64.b64encode(b"x" * 64).decode("ascii")
        with self.assertRaisesRegex(CalibrationVerificationError, "INVALID_ED25519_SIGNATURE"):
            self.verify(envelope=envelope)

    def test_artifact_digest_and_exact_size_are_verified(self):
        with self.assertRaisesRegex(CalibrationVerificationError, "ARTIFACT_DIGEST_MISMATCH"):
            self.verify(artifact=b"x" * len(self.artifact))
        invalid = copy.deepcopy(self.manifest)
        invalid["artifact_size_bytes"] = str(len(self.artifact) + 1)
        raw = canonical(invalid)
        with self.assertRaisesRegex(CalibrationVerificationError, "ARTIFACT_SIZE_MISMATCH"):
            self.verify(manifest_bytes=raw, envelope=self.make_envelope(raw, invalid))

    def test_public_key_fingerprint_must_match_independent_pin(self):
        invalid = copy.deepcopy(self.trust)
        invalid["public_key_fingerprint"] = digest(b"wrong-key")
        with self.assertRaisesRegex(CalibrationVerificationError, "PUBLIC_KEY_PIN_MISMATCH"):
            self.verify(trust=invalid)

    def test_unknown_key_or_scope_mismatch_is_rejected(self):
        invalid = copy.deepcopy(self.trust)
        invalid["key_id"] = "untrusted-key"
        with self.assertRaisesRegex(CalibrationVerificationError, "KEY_ID_NOT_PINNED"):
            self.verify(trust=invalid)
        invalid = copy.deepcopy(self.trust)
        invalid["registry_namespace"] = "other-namespace"
        with self.assertRaisesRegex(CalibrationVerificationError, "KEY_SCOPE_MISMATCH"):
            self.verify(trust=invalid)

    def test_manifest_publisher_must_match_the_independently_pinned_signer(self):
        invalid = copy.deepcopy(self.trust)
        invalid["publisher_id"] = "different-publisher"
        with self.assertRaisesRegex(CalibrationVerificationError, "KEY_SCOPE_MISMATCH"):
            self.verify(trust=invalid)

    def test_envelope_digest_length_namespace_and_algorithm_are_bound(self):
        for field, value in (
            ("manifest_digest", digest(b"wrong")),
            ("manifest_size_bytes", "1"),
            ("namespace", "other-namespace"),
            ("signature_algorithm", "Ed25519ph"),
            ("canonicalization_profile", "JSON-SORTED"),
            ("key_id", "different-key"),
            ("signer_role", "ROOT"),
        ):
            envelope = copy.deepcopy(self.envelope)
            envelope[field] = value
            with self.subTest(field=field):
                with self.assertRaises(CalibrationVerificationError):
                    self.verify(envelope=envelope)

    def test_registry_sequence_requires_a_predecessor_after_genesis(self):
        invalid = copy.deepcopy(self.manifest)
        invalid["record_sequence"] = "2"
        raw = canonical(invalid)
        with self.assertRaisesRegex(CalibrationVerificationError, "PREVIOUS_RECORD_DIGEST_INVALID"):
            self.verify(manifest_bytes=raw, envelope=self.make_envelope(raw, invalid))

    def test_calibration_window_obeys_horizon_embargo_and_precedes_artifact_creation(self):
        invalid = copy.deepcopy(self.manifest)
        invalid["calibration_start"] = "2026-01-01T00:14:59Z"
        raw = canonical(invalid)
        with self.assertRaisesRegex(CalibrationVerificationError, "CALIBRATION_WINDOW_NOT_OUT_OF_SAMPLE"):
            self.verify(manifest_bytes=raw, envelope=self.make_envelope(raw, invalid))
        invalid = copy.deepcopy(self.manifest)
        invalid["created_at"] = "2026-02-14T00:00:00Z"
        raw = canonical(invalid)
        with self.assertRaisesRegex(CalibrationVerificationError, "ARTIFACT_CREATED_BEFORE_CALIBRATION_END"):
            self.verify(manifest_bytes=raw, envelope=self.make_envelope(raw, invalid))

    def test_verified_bundle_derives_and_binds_per_inference_confidence(self):
        result = calibrate_verified_prediction(
            self.manifest_bytes, self.envelope, self.artifact, self.trust, "0.015"
        )
        self.assertEqual(result["verificationStatus"], "SIGNATURE_VERIFIED_ONLY")
        self.assertEqual(result["calibratedConfidence"], "0.7")
        self.assertEqual(result["manifestDigest"], digest(self.manifest_bytes))
        self.assertEqual(result["calibrationArtifactHash"], digest(self.artifact))
        self.assertEqual(result["modelVersion"], self.manifest["model_version"])
        self.assertEqual(result["strategyVersion"], self.manifest["strategy_version"])
        self.assertEqual(result["trainingDatasetVersion"],
                         self.manifest["training_dataset_digest"])
        self.assertEqual(result["labelDefinition"], self.manifest["label_definition_id"])
        self.assertEqual(result["forecastHorizonMs"], 900000)

    def test_transform_rejects_out_of_range_scores_and_nonmonotonic_maps(self):
        with self.assertRaisesRegex(CalibrationVerificationError, "RAW_DIRECTION_SCORE_OUTSIDE_CALIBRATION_RANGE"):
            apply_calibration_transform(self.artifact, "0.04")
        invalid = copy.deepcopy(self.artifact_object)
        invalid["knots"][2]["probability"] = "0.55"
        with self.assertRaisesRegex(CalibrationVerificationError, "CALIBRATION_TRANSFORM_NOT_MONOTONIC"):
            apply_calibration_transform(canonical(invalid), "0.015")

    def test_transform_schema_and_manifest_method_must_match(self):
        invalid = copy.deepcopy(self.artifact_object)
        invalid["calibration_method"] = "platt"
        raw = canonical(invalid)
        manifest = copy.deepcopy(self.manifest)
        manifest["artifact_digest"] = digest(raw)
        manifest["artifact_size_bytes"] = str(len(raw))
        manifest_bytes = canonical(manifest)
        envelope = self.make_envelope(manifest_bytes, manifest)
        with self.assertRaisesRegex(CalibrationVerificationError, "CALIBRATION_TRANSFORM_MANIFEST_MISMATCH"):
            calibrate_verified_prediction(
                manifest_bytes, envelope, raw, self.trust, "0.015"
            )

    def test_transform_decimal_and_duplicate_knot_fields_are_rejected(self):
        invalid = copy.deepcopy(self.artifact_object)
        invalid["knots"][1]["score"] = "NaN"
        with self.assertRaisesRegex(CalibrationVerificationError, "CALIBRATION_TRANSFORM_DECIMAL_INVALID"):
            apply_calibration_transform(canonical(invalid), "0.015")

    def test_verifier_does_not_claim_registry_approval_or_admission(self):
        result = self.verify()
        self.assertNotIn("approved", result)
        self.assertNotIn("active", result)
        self.assertNotIn("admission_eligible", result)


    def test_manifest_utf8_bom_is_rejected_with_explicit_reason(self):
        with self.assertRaisesRegex(CalibrationVerificationError, "MANIFEST_BOM_NOT_ALLOWED"):
            self.verify(manifest_bytes=bytes.fromhex("efbbbf") + self.manifest_bytes)

    def test_transform_utf8_bom_is_rejected_with_explicit_reason(self):
        with self.assertRaisesRegex(CalibrationVerificationError, "ARTIFACT_BOM_NOT_ALLOWED"):
            apply_calibration_transform(bytes.fromhex("efbbbf") + self.artifact, "0.015")


if __name__ == "__main__":
    unittest.main()
