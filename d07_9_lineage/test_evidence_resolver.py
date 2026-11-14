"""Synthetic contract tests for D07.11 evidence resolution and readback."""
import hashlib
import tempfile
import unittest
from pathlib import Path

from d07_9_lineage.evidence_resolver import resolve_lineage_record


def digest(data):
    return hashlib.sha256(data).hexdigest()


def make_case(root):
    root = Path(root)
    raw = b"synthetic funding rows\\n"
    evidence = b"synthetic retained evidence\\n"
    (root / "raw").mkdir()
    (root / "refs").mkdir()
    (root / "raw" / "funding.csv").write_bytes(raw)
    (root / "refs" / "evidence.txt").write_bytes(evidence)
    refs = [
        "custodian-owner", "provider-source", "acquisition-actor", "acquisition-run",
        "host-env", "receipt-actor", "storage", "access-policy", "readback-actor",
        "readback-run", "readback-env", "readback-copy", "readback-log",
        "custody-event-actor", "custody-event-proof", "dependency-proof",
        "reviewer-proof", "review-rationale",
    ]
    record = {
        "custodian": {"actorRef": "custodian-owner", "organizationRef": None},
        "provider": {"sourceReference": "provider-source"},
        "acquisition": {
            "actorRef": "acquisition-actor", "executionRef": "acquisition-run",
            "hostEnvironmentRef": "host-env", "requestReference": None,
            "networkEgressRef": None,
        },
        "rawFiles": [{
            "d07_8Path": "raw/funding.csv", "byteLengthAtReceipt": len(raw),
            "sha256AtReceipt": digest(raw), "preservedOriginal": True,
        }],
        "custody": {
            "receiptActorRef": "receipt-actor", "storageRef": "storage",
            "accessControlRef": "access-policy", "readbackActorRef": "readback-actor",
            "readbackRunRef": "readback-run", "readbackEnvironmentRef": "readback-env",
            "readbackStorageRef": "readback-copy", "readbackEvidenceRef": "readback-log",
            "readbackFiles": [{
                "d07_8Path": "raw/funding.csv", "byteLength": len(raw),
                "sha256": digest(raw), "method": "INDEPENDENT_READBACK",
            }],
            "custodyEvents": [{
                "actorRef": "custody-event-actor", "evidenceRef": "custody-event-proof",
            }],
        },
        "transformation": {"fieldMappingRef": None},
        "dependencies": [{"evidenceRef": "dependency-proof"}],
        "assessment": {"reviewerRef": "reviewer-proof", "rationaleRef": "review-rationale"},
    }
    index = {
        ref: {"path": "refs/evidence.txt", "byteLength": len(evidence), "sha256": digest(evidence)}
        for ref in refs
    }
    package = {"packageId": "synthetic-package", "files": [{"path": "raw/funding.csv"}]}
    manifest = {"raw/funding.csv": {"byteLength": len(raw), "sha256": digest(raw)}}
    return record, package, index, manifest, raw, evidence


class D0711EvidenceResolverTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.record, self.package, self.index, self.manifest, self.raw, self.evidence = make_case(self.root)

    def tearDown(self):
        self.temp.cleanup()

    def resolve(self, **overrides):
        args = {
            "record": self.record,
            "d07_8_package": self.package,
            "evidence_root": self.root,
            "reference_index": self.index,
            "manifest_file_metadata": self.manifest,
        }
        args.update(overrides)
        return resolve_lineage_record(**args)

    def test_01_resolves_all_refs_and_independently_reads_raw_bytes(self):
        result = self.resolve()
        self.assertEqual(result["status"], "PASS", result)
        self.assertEqual(result["evidenceReferenceResolution"], "PASS")
        self.assertEqual(result["byteIntegrity"], "PASS")
        self.assertEqual(result["collectorIndependence"], "NOT_VERIFIED")

    def test_02_missing_reference_fails_closed(self):
        index = dict(self.index)
        index.pop("provider-source")
        result = self.resolve(reference_index=index)
        self.assertEqual(result["status"], "NOT_VERIFIED")
        self.assertIn("EVIDENCE_REFERENCE_MISSING", result["errors"])

    def test_03_reference_target_missing_fails_closed(self):
        index = dict(self.index)
        index["provider-source"] = dict(index["provider-source"], path="refs/missing.txt")
        result = self.resolve(reference_index=index)
        self.assertEqual(result["status"], "NOT_VERIFIED")

    def test_04_reference_digest_mismatch_fails_closed(self):
        index = dict(self.index)
        index["provider-source"] = dict(index["provider-source"], sha256="0" * 64)
        result = self.resolve(reference_index=index)
        self.assertEqual(result["status"], "BLOCKED")

    def test_05_path_traversal_is_rejected(self):
        index = dict(self.index)
        index["provider-source"] = dict(index["provider-source"], path="../outside.txt")
        result = self.resolve(reference_index=index)
        self.assertEqual(result["status"], "BLOCKED")

    def test_06_absolute_path_is_rejected(self):
        index = dict(self.index)
        index["provider-source"] = dict(index["provider-source"], path=str(self.root / "refs/evidence.txt"))
        result = self.resolve(reference_index=index)
        self.assertEqual(result["status"], "BLOCKED")

    def test_07_symlink_target_is_rejected(self):
        link = self.root / "refs" / "linked.txt"
        link.symlink_to(self.root / "refs" / "evidence.txt")
        index = dict(self.index)
        index["provider-source"] = dict(index["provider-source"], path="refs/linked.txt")
        result = self.resolve(reference_index=index)
        self.assertEqual(result["status"], "BLOCKED")

    def test_08_raw_manifest_hash_mismatch_blocks_integrity(self):
        manifest = dict(self.manifest)
        manifest["raw/funding.csv"] = {"byteLength": len(self.raw), "sha256": "f" * 64}
        result = self.resolve(manifest_file_metadata=manifest)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(result["byteIntegrity"], "BLOCKED")

    def test_09_raw_receipt_hash_mismatch_blocks_integrity(self):
        self.record["rawFiles"][0]["sha256AtReceipt"] = "e" * 64
        result = self.resolve()
        self.assertEqual(result["status"], "BLOCKED")

    def test_10_manifest_raw_file_missing_is_not_verified(self):
        result = self.resolve(manifest_file_metadata={})
        self.assertEqual(result["status"], "NOT_VERIFIED")

    def test_11_reference_length_mismatch_blocks(self):
        index = dict(self.index)
        index["provider-source"] = dict(index["provider-source"], byteLength=1)
        result = self.resolve(reference_index=index)
        self.assertEqual(result["status"], "BLOCKED")

    def test_12_raw_readback_declaration_mismatch_blocks(self):
        self.record["custody"]["readbackFiles"][0]["sha256"] = "d" * 64
        result = self.resolve()
        self.assertEqual(result["status"], "BLOCKED")

    def test_13_duplicate_reference_index_path_does_not_skip_checks(self):
        index = dict(self.index)
        index["provider-source"] = dict(index["provider-source"], path="refs/../refs/evidence.txt")
        result = self.resolve(reference_index=index)
        self.assertEqual(result["status"], "BLOCKED")


if __name__ == "__main__":
    unittest.main()
