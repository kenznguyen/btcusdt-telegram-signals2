"""Signed AI OOS provenance validator contracts; all artifacts are synthetic fixtures."""
import base64
import hashlib
import json
import unittest

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from quant_system.ai_provenance_validator import verify_signed_provenance


ROLES = ("model", "dataset", "predictions", "split_protocol", "calibration_report")


class AIProvenanceValidatorTests(unittest.TestCase):
    def setUp(self):
        self.private_key = Ed25519PrivateKey.generate()
        self.public_key = self.private_key.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        self.artifacts = {role: (f"synthetic-{role}-bytes").encode() for role in ROLES}
        self.now_ms = 1_800_000_000_000
        self.manifest = {
            "schema_version": 1,
            "key_id": "offline-test-root-1",
            "model_version": "model-sha-test-v1",
            "strategy_version": "dual-ai-v1",
            "dataset_version": "dataset-sha-test-v1",
            "issued_at_ms": self.now_ms - 1000,
            "expires_at_ms": self.now_ms + 60_000,
            "temporal_split": {
                "train_end_ms": 1_700_000_000_000,
                "oos_start_ms": 1_700_000_000_001,
                "oos_end_ms": 1_710_000_000_000,
            },
            "artifacts": {
                role: {
                    "sha256": hashlib.sha256(data).hexdigest(),
                    "size_bytes": len(data),
                }
                for role, data in self.artifacts.items()
            },
        }

    def signed_envelope(self, manifest=None):
        manifest = self.manifest if manifest is None else manifest
        canonical = json.dumps(
            manifest, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
            allow_nan=False,
        ).encode()
        return {
            "manifest": manifest,
            "signature": base64.b64encode(self.private_key.sign(canonical)).decode(),
        }

    def verify(self, envelope=None, artifacts=None, keys=None, now_ms=None):
        return verify_signed_provenance(
            self.signed_envelope() if envelope is None else envelope,
            self.artifacts if artifacts is None else artifacts,
            {"offline-test-root-1": self.public_key} if keys is None else keys,
            now_ms=self.now_ms if now_ms is None else now_ms,
        )

    def test_valid_signature_hashes_and_temporal_split_are_accepted(self):
        result = self.verify()
        self.assertTrue(result.accepted)
        self.assertEqual(result.reasons, ())
        self.assertEqual(set(result.verified_artifacts), set(ROLES))
        self.assertEqual(len(result.manifest_sha256), 64)
        self.assertFalse(result.attestation_issued)

    def test_rejects_unknown_signing_key(self):
        result = self.verify(keys={})
        self.assertFalse(result.accepted)
        self.assertIn("SIGNING_KEY_UNTRUSTED", result.reasons)

    def test_rejects_tampered_manifest_signature(self):
        envelope = self.signed_envelope()
        envelope["manifest"]["strategy_version"] = "tampered"
        result = self.verify(envelope=envelope)
        self.assertFalse(result.accepted)
        self.assertIn("SIGNATURE_INVALID", result.reasons)

    def test_rejects_tampered_artifact_bytes(self):
        artifacts = dict(self.artifacts)
        artifacts["model"] = b"changed model bytes"
        result = self.verify(artifacts=artifacts)
        self.assertFalse(result.accepted)
        self.assertIn("ARTIFACT_HASH_MISMATCH:model", result.reasons)

    def test_rejects_missing_artifact(self):
        artifacts = dict(self.artifacts)
        del artifacts["predictions"]
        result = self.verify(artifacts=artifacts)
        self.assertFalse(result.accepted)
        self.assertIn("ARTIFACT_MISSING:predictions", result.reasons)

    def test_rejects_extra_artifact_role(self):
        artifacts = dict(self.artifacts, credentials=b"must-not-be-accepted")
        result = self.verify(artifacts=artifacts)
        self.assertFalse(result.accepted)
        self.assertIn("ARTIFACT_ROLE_SET_MISMATCH", result.reasons)

    def test_rejects_artifact_size_mismatch(self):
        manifest = json.loads(json.dumps(self.manifest))
        manifest["artifacts"]["dataset"]["size_bytes"] += 1
        result = self.verify(envelope=self.signed_envelope(manifest))
        self.assertFalse(result.accepted)
        self.assertIn("ARTIFACT_SIZE_MISMATCH:dataset", result.reasons)

    def test_rejects_training_window_overlapping_oos(self):
        manifest = json.loads(json.dumps(self.manifest))
        manifest["temporal_split"]["train_end_ms"] = manifest["temporal_split"]["oos_start_ms"]
        result = self.verify(envelope=self.signed_envelope(manifest))
        self.assertFalse(result.accepted)
        self.assertIn("TEMPORAL_SPLIT_INVALID", result.reasons)

    def test_rejects_invalid_oos_window(self):
        manifest = json.loads(json.dumps(self.manifest))
        manifest["temporal_split"]["oos_end_ms"] = manifest["temporal_split"]["oos_start_ms"] - 1
        result = self.verify(envelope=self.signed_envelope(manifest))
        self.assertFalse(result.accepted)
        self.assertIn("TEMPORAL_SPLIT_INVALID", result.reasons)

    def test_rejects_expired_manifest(self):
        result = self.verify(now_ms=self.manifest["expires_at_ms"])
        self.assertFalse(result.accepted)
        self.assertIn("MANIFEST_EXPIRED", result.reasons)

    def test_rejects_manifest_issued_in_the_future(self):
        result = self.verify(now_ms=self.manifest["issued_at_ms"] - 1)
        self.assertFalse(result.accepted)
        self.assertIn("MANIFEST_TIME_INVALID", result.reasons)

    def test_rejects_duplicate_json_keys(self):
        raw = b'{"manifest":{"schema_version":1,"schema_version":1},"signature":"AA=="}'
        result = self.verify(envelope=raw)
        self.assertFalse(result.accepted)
        self.assertIn("ENVELOPE_INVALID", result.reasons)

    def test_rejects_noncanonical_unknown_manifest_fields(self):
        manifest = dict(self.manifest, caller_says_oos=True)
        result = self.verify(envelope=self.signed_envelope(manifest))
        self.assertFalse(result.accepted)
        self.assertIn("MANIFEST_SCHEMA_INVALID", result.reasons)

    def test_rejects_invalid_signature_encoding(self):
        envelope = self.signed_envelope()
        envelope["signature"] = "not-base64!"
        result = self.verify(envelope=envelope)
        self.assertFalse(result.accepted)
        self.assertIn("SIGNATURE_ENCODING_INVALID", result.reasons)


if __name__ == "__main__":
    unittest.main()
