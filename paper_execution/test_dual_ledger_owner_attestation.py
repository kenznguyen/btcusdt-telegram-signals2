"""TDD contract for bounded, non-cryptographic Dual Ledger Owner attestation."""

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from paper_execution.owner_attestation import (
    load_manual_owner_attestation,
    validate_manual_owner_attestation,
)


class ManualOwnerAttestationContractTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.manifest = {
            "sourceSha": "a" * 40,
            "fundingSnapshotId": "funding-snapshot-001",
            "fundingPayloadHash": "sha256:" + "1" * 64,
            "cutoverSnapshotId": "equity-snapshot-001",
            "cutoverPayloadHash": "sha256:" + "2" * 64,
            "markObservedAtMs": 1_800_000_000_000,
            "recordedAtMs": 1_800_000_060_000,
        }
        self.document = {
            "schemaVersion": 1,
            "attestationType": "DUAL_LEDGER_BOOTSTRAP_EVIDENCE_REVIEW",
            "attestorRole": "OWNER_DECLARATION",
            "claimScope": "FUNDING_AND_EQUITY_SNAPSHOT_REVIEW",
            "sourceSha": self.manifest["sourceSha"],
            "fundingSnapshotId": self.manifest["fundingSnapshotId"],
            "fundingPayloadHash": self.manifest["fundingPayloadHash"],
            "cutoverSnapshotId": self.manifest["cutoverSnapshotId"],
            "cutoverPayloadHash": self.manifest["cutoverPayloadHash"],
            "reviewedAtMs": 1_800_000_030_000,
            "reviewStatement": (
                "I_REVIEWED_THE_IDENTIFIED_FUNDING_AND_EQUITY_SNAPSHOTS"
            ),
            "nonClaims": [
                "FACTUAL_TRUTH",
                "FRESHNESS",
                "POPULATION_COMPLETENESS",
                "PRIVILEGED_ACTION_AUTHORIZATION",
                "SOURCE_AUTHENTICITY",
            ],
        }

    def test_accepts_exact_bounded_owner_review_and_returns_non_claims(self):
        result = validate_manual_owner_attestation(self.document, self.manifest)

        self.assertEqual(result["attestationStatus"], "MANUAL_OWNER_ATTESTATION_PRESENT")
        self.assertEqual(result["attestorRole"], "OWNER_DECLARATION")
        self.assertEqual(result["ownerIdentity"], "NOT_AUTHENTICATED")
        self.assertEqual(result["sourceAuthenticity"], "NOT_VERIFIED")
        self.assertEqual(result["factualTruth"], "NOT_VERIFIED")
        self.assertEqual(result["completeness"], "NOT_VERIFIED")
        self.assertEqual(result["freshness"], "NOT_VERIFIED")
        self.assertEqual(result["privilegedActionAuthorization"], "NOT_GRANTED")

    def test_rejects_unknown_fields(self):
        bad = dict(self.document, trusted=True)
        with self.assertRaisesRegex(ValueError, "OWNER_ATTESTATION_FIELDS_INVALID"):
            validate_manual_owner_attestation(bad, self.manifest)

    def test_rejects_non_owner_declaration(self):
        bad = dict(self.document, attestorRole="SYSTEM")
        with self.assertRaisesRegex(ValueError, "OWNER_ATTESTATION_ROLE_INVALID"):
            validate_manual_owner_attestation(bad, self.manifest)

    def test_rejects_source_sha_mismatch(self):
        bad = dict(self.document, sourceSha="b" * 40)
        with self.assertRaisesRegex(ValueError, "OWNER_ATTESTATION_BINDING_MISMATCH"):
            validate_manual_owner_attestation(bad, self.manifest)

    def test_rejects_funding_evidence_mismatch(self):
        bad = dict(self.document, fundingPayloadHash="sha256:" + "3" * 64)
        with self.assertRaisesRegex(ValueError, "OWNER_ATTESTATION_BINDING_MISMATCH"):
            validate_manual_owner_attestation(bad, self.manifest)

    def test_rejects_equity_snapshot_mismatch(self):
        bad = dict(self.document, cutoverSnapshotId="other-snapshot")
        with self.assertRaisesRegex(ValueError, "OWNER_ATTESTATION_BINDING_MISMATCH"):
            validate_manual_owner_attestation(bad, self.manifest)

    def test_rejects_future_or_pre_evidence_review_timestamp(self):
        bad = dict(self.document, reviewedAtMs=self.manifest["recordedAtMs"] + 1)
        with self.assertRaisesRegex(ValueError, "OWNER_ATTESTATION_TIME_INVALID"):
            validate_manual_owner_attestation(bad, self.manifest)
        bad = dict(self.document, reviewedAtMs=self.manifest["markObservedAtMs"] - 1)
        with self.assertRaisesRegex(ValueError, "OWNER_ATTESTATION_TIME_INVALID"):
            validate_manual_owner_attestation(bad, self.manifest)

    def test_rejects_claims_that_exceed_manual_attestation_authority(self):
        bad = dict(self.document, nonClaims=["SOURCE_AUTHENTICITY"])
        with self.assertRaisesRegex(ValueError, "OWNER_ATTESTATION_NON_CLAIMS_INVALID"):
            validate_manual_owner_attestation(bad, self.manifest)

    def test_load_checks_exact_bytes_digest_before_parsing(self):
        path = self.root / "owner-attestation.json"
        path.write_text(json.dumps(self.document), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "OWNER_ATTESTATION_DIGEST_MISMATCH"):
            load_manual_owner_attestation(
                path, "sha256:" + "0" * 64, self.manifest
            )

    def test_load_rejects_duplicate_json_keys(self):
        path = self.root / "owner-attestation.json"
        raw = b'{"schemaVersion":1,"schemaVersion":1}'
        path.write_bytes(raw)
        digest = "sha256:" + hashlib.sha256(raw).hexdigest()
        with self.assertRaisesRegex(ValueError, "OWNER_ATTESTATION_JSON_INVALID"):
            load_manual_owner_attestation(path, digest, self.manifest)

    def test_load_rejects_symlink_and_missing_file(self):
        target = self.root / "target.json"
        target.write_text("{}", encoding="utf-8")
        link = self.root / "link.json"
        link.symlink_to(target)
        digest = "sha256:" + hashlib.sha256(b"{}").hexdigest()
        with self.assertRaisesRegex(ValueError, "OWNER_ATTESTATION_FILE_UNAVAILABLE"):
            load_manual_owner_attestation(link, digest, self.manifest)
        with self.assertRaisesRegex(ValueError, "OWNER_ATTESTATION_FILE_UNAVAILABLE"):
            load_manual_owner_attestation(
                self.root / "missing.json", digest, self.manifest
            )


if __name__ == "__main__":
    unittest.main()
