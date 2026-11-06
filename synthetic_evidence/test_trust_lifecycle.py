import hashlib
import json
import unittest
from datetime import datetime, timezone, timedelta

from synthetic_evidence.trust_lifecycle import (
    assess_revocation,
    assess_snapshot_freshness,
    build_retention_manifest,
    build_trust_snapshot,
    compare_trusted_roots,
    verify_retention_manifest,
    verify_snapshot_chain,
)


def root_bytes(rekor_key="rekor-key-a", fulcio_key="fulcio-root-a"):
    record = {
        "mediaType": "application/vnd.dev.sigstore.trustedroot+json;version=0.1",
        "tlogs": [{"logId": {"keyId": rekor_key}, "baseUrl": "https://rekor.example"}],
        "certificateAuthorities": [
            {"uri": "https://fulcio.example", "certChain": {"certificates": [{"rawBytes": fulcio_key}]}}
        ],
        "ctlogs": [],
        "timestampAuthorities": [],
    }
    return (json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n").encode()


class TrustLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 11, 7, 12, 0, tzinfo=timezone.utc)
        self.root_a = root_bytes()
        self.root_b = root_bytes(rekor_key="rekor-key-b", fulcio_key="fulcio-root-b")


    def test_decodes_historical_compressed_root_only_when_digest_matches(self):
        import base64
        import gzip
        from synthetic_evidence.trust_lifecycle import decode_pinned_root_snapshot
        encoded = base64.b64encode(gzip.compress(self.root_a, mtime=0))
        digest = hashlib.sha256(self.root_a).hexdigest()
        self.assertEqual(decode_pinned_root_snapshot(encoded, digest), self.root_a)
        with self.assertRaisesRegex(ValueError, "digest mismatch"):
            decode_pinned_root_snapshot(encoded, "0" * 64)

    def test_rejects_corrupt_historical_compressed_root(self):
        import base64
        from synthetic_evidence.trust_lifecycle import decode_pinned_root_snapshot
        with self.assertRaisesRegex(ValueError, "compressed root snapshot"):
            decode_pinned_root_snapshot(base64.b64encode(b"not-gzip"), "0" * 64)

    def test_builds_a_source_bound_snapshot_with_root_digest(self):
        snapshot = build_trust_snapshot(
            self.root_a,
            captured_at="2026-11-07T12:00:00Z",
            sequence=1,
            tuf_verified=True,
        )
        self.assertEqual(snapshot["trusted_root_sha256"], hashlib.sha256(self.root_a).hexdigest())
        self.assertEqual(snapshot["sequence"], 1)
        self.assertEqual(snapshot["tuf_verification"], "GH_CLI_TUF_VERIFIED")
        self.assertRegex(snapshot["snapshot_sha256"], r"^[0-9a-f]{64}$")

    def test_rejects_naive_or_non_utc_snapshot_timestamps(self):
        with self.assertRaisesRegex(ValueError, "UTC"):
            build_trust_snapshot(self.root_a, captured_at="2026-11-07T12:00:00", sequence=1, tuf_verified=True)
        with self.assertRaisesRegex(ValueError, "UTC"):
            build_trust_snapshot(self.root_a, captured_at="2026-11-07T19:00:00+07:00", sequence=1, tuf_verified=True)

    def test_detects_trust_material_rotation_without_rewriting_history(self):
        old = build_trust_snapshot(self.root_a, captured_at="2026-11-01T00:00:00Z", sequence=1, tuf_verified=True)
        new = build_trust_snapshot(
            self.root_b,
            captured_at="2026-11-07T12:00:00Z",
            sequence=2,
            previous_snapshot_sha256=old["snapshot_sha256"],
            tuf_verified=True,
        )
        diff = compare_trusted_roots(self.root_a, self.root_b)
        self.assertEqual(diff["status"], "ROTATION_DETECTED")
        self.assertTrue(diff["added"])
        self.assertTrue(diff["removed"])
        self.assertNotEqual(old["trusted_root_sha256"], new["trusted_root_sha256"])

    def test_snapshot_chain_rejects_tampered_manifest(self):
        first = build_trust_snapshot(self.root_a, captured_at="2026-11-01T00:00:00Z", sequence=1, tuf_verified=True)
        second = build_trust_snapshot(
            self.root_b, captured_at="2026-11-07T12:00:00Z", sequence=2,
            previous_snapshot_sha256=first["snapshot_sha256"], tuf_verified=True
        )
        self.assertTrue(verify_snapshot_chain([first, second]))
        tampered = dict(second)
        tampered["trusted_root_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "snapshot digest"):
            verify_snapshot_chain([first, tampered])

    def test_snapshot_chain_rejects_missing_predecessor_and_sequence_gap(self):
        first = build_trust_snapshot(self.root_a, captured_at="2026-11-01T00:00:00Z", sequence=1, tuf_verified=True)
        third = build_trust_snapshot(
            self.root_b, captured_at="2026-11-07T12:00:00Z", sequence=3,
            previous_snapshot_sha256=first["snapshot_sha256"], tuf_verified=True
        )
        with self.assertRaisesRegex(ValueError, "sequence"):
            verify_snapshot_chain([first, third])

    def test_freshness_is_review_due_without_invalidating_historical_verification(self):
        snapshot = build_trust_snapshot(self.root_a, captured_at="2026-10-01T00:00:00Z", sequence=1, tuf_verified=True)
        result = assess_snapshot_freshness(snapshot, now=self.now, max_age_days=30)
        self.assertEqual(result["status"], "REVIEW_DUE")
        self.assertTrue(result["historical_verification_allowed"])
        self.assertFalse(result["current_revocation_claim_allowed"])

    def test_offline_verification_never_claims_current_revocation_clearance(self):
        result = assess_revocation(mode="OFFLINE", evidence=None)
        self.assertEqual(result["status"], "NOT_CHECKED_OFFLINE")
        self.assertFalse(result["may_claim_not_revoked"])
        self.assertFalse(result["may_admit_as_currently_cleared"])

    def test_online_trust_root_refresh_does_not_invent_revocation_status(self):
        result = assess_revocation(mode="ONLINE_TUF", evidence=None)
        self.assertEqual(result["status"], "REVOCATION_STATUS_NOT_EXPOSED")
        self.assertFalse(result["may_claim_not_revoked"])

    def test_explicit_revoked_evidence_fails_closed(self):
        evidence = {
            "decision": "REVOKED",
            "evidence_sha256": "a" * 64,
            "review_id": "SEC-2026-001",
            "reviewed_at": "2026-11-07T11:00:00Z",
        }
        result = assess_revocation(mode="OFFLINE", evidence=evidence)
        self.assertEqual(result["status"], "REVOKED")
        self.assertEqual(result["decision"], "REJECT")

    def test_reviewed_clearance_requires_traceable_evidence(self):
        evidence = {
            "decision": "REVIEWED_CLEAR",
            "evidence_sha256": "b" * 64,
            "review_id": "SEC-2026-002",
            "reviewed_at": "2026-11-07T11:00:00Z",
        }
        result = assess_revocation(mode="OFFLINE", evidence=evidence)
        self.assertEqual(result["status"], "REVIEWED_CLEAR_AUDIT_ONLY")
        self.assertEqual(result["decision"], "BLOCK_UNLESS_EVIDENCE_AUTHENTICITY_IS_SEPARATELY_VERIFIED")
        evidence["evidence_sha256"] = "invalid"
        with self.assertRaisesRegex(ValueError, "evidence digest"):
            assess_revocation(mode="OFFLINE", evidence=evidence)


    def test_sha256_sidecar_is_a_real_newline_terminated_checksum_line(self):
        from synthetic_evidence.trust_lifecycle import format_sha256_sidecar, verify_sha256_sidecar
        digest = "c" * 64
        sidecar = format_sha256_sidecar(digest, "trusted_root.jsonl")
        self.assertEqual(sidecar, f"{digest}  trusted_root.jsonl\n")
        self.assertTrue(verify_sha256_sidecar(sidecar, digest, "trusted_root.jsonl"))
        with self.assertRaisesRegex(ValueError, "sidecar mismatch"):
            verify_sha256_sidecar(sidecar.replace("\n", "\\n"), digest, "trusted_root.jsonl")

    def test_retention_manifest_records_every_file_digest_and_git_history_class(self):
        files = {
            "synthetic-evidence-bundle.zip": b"subject",
            "synthetic-evidence-attestation.bundle.json": b"bundle",
            "trusted_root.jsonl": self.root_a,
        }
        manifest = build_retention_manifest(
            files,
            source_sha="1" * 40,
            workflow_run_id=42305379372,
            archived_at="2026-11-07T12:00:00Z",
        )
        self.assertEqual(manifest["retention_class"], "GIT_HISTORY")
        self.assertEqual(len(manifest["files"]), 3)
        self.assertTrue(verify_retention_manifest(manifest, files))
        self.assertIn("NOT_WORM", manifest["immutability"])
    
    def test_retention_verification_rejects_missing_or_changed_payload(self):
        files = {"subject.zip": b"subject", "bundle.json": b"bundle", "root.jsonl": self.root_a}
        manifest = build_retention_manifest(
            files, source_sha="2" * 40, workflow_run_id=42305379372,
            archived_at="2026-11-07T12:00:00Z"
        )
        with self.assertRaisesRegex(ValueError, "missing retained file"):
            verify_retention_manifest(manifest, {"subject.zip": b"subject"})
        changed = dict(files)
        changed["subject.zip"] = b"substituted"
        with self.assertRaisesRegex(ValueError, "digest mismatch"):
            verify_retention_manifest(manifest, changed)


if __name__ == "__main__":
    unittest.main()
