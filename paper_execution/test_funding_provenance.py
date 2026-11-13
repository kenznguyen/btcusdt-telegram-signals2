"""D07.2 synthetic source-byte readback and pagination contract tests."""

import hashlib
import tempfile
import unittest
from pathlib import Path

from paper_execution.funding_provenance import verify_funding_source_evidence


class FundingSourceEvidenceTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.pages = [b'{"events":[{"id":"f-1"}]}', b'{"events":[{"id":"f-2"}]}']
        for index, content in enumerate(self.pages):
            (self.root / f"page-{index}.json").write_bytes(content)
        self.envelope = {
            "schemaVersion": 1,
            "evidenceSnapshotId": "synthetic-snapshot-001",
            "source": {
                "sourceId": "synthetic-exporter",
                "sourceType": "SYNTHETIC_FIXTURE",
                "claimedIssuer": "fixture-issuer",
                "authorityBasis": "synthetic test fixture only",
                "acquisitionMethod": "prebuilt fixture bytes",
            },
            "scope": {
                "accountRef": "synthetic-account",
                "instrument": "BTCUSDT",
                "currency": "USDT",
                "startAtMs": 100,
                "endAtMs": 200,
                "timestampSemantics": "event-time-ms",
                "filtersFingerprint": "sha256:" + "1" * 64,
            },
            "snapshot": {
                "asOfMs": 190,
                "retrievedAtMs": 195,
                "eventCutoffMs": 200,
            },
            "pages": [
                {
                    "ordinal": 0, "pageId": "p0", "requestCursor": None,
                    "nextCursor": "cursor-1", "terminal": False,
                    "requestFingerprint": "sha256:" + "2" * 64,
                    "relativePath": "page-0.json", "byteLength": len(self.pages[0]),
                    "sha256": "sha256:" + hashlib.sha256(self.pages[0]).hexdigest(),
                    "recordCount": 1, "sourceTotal": 2,
                },
                {
                    "ordinal": 1, "pageId": "p1", "requestCursor": "cursor-1",
                    "nextCursor": None, "terminal": True,
                    "requestFingerprint": "sha256:" + "3" * 64,
                    "relativePath": "page-1.json", "byteLength": len(self.pages[1]),
                    "sha256": "sha256:" + hashlib.sha256(self.pages[1]).hexdigest(),
                    "recordCount": 1, "sourceTotal": 2,
                },
            ],
            "lineage": {
                "expectedSourceSystem": "independent-fixture-export",
                "observedSourceSystem": "paper-ledger-fixture",
                "sharedUpstreamSystems": [],
            },
        }

    def test_exact_bytes_and_complete_declared_cursor_chain_read_back(self):
        result = verify_funding_source_evidence(self.envelope, self.root)

        self.assertEqual(result["status"], "SOURCE_BYTES_READ_BACK")
        self.assertEqual(result["sourceByteIntegrity"], "PASS")
        self.assertEqual(result["sourceByteReadback"], "PASS")
        self.assertEqual(result["paginationStructure"], "PASS")
        self.assertEqual(result["enumerationCompleteness"], "NOT_VERIFIED")
        self.assertEqual(result["independence"], "DECLARED_NOT_VERIFIED")
        self.assertEqual(result["issuerAuthenticity"], "NOT_VERIFIED")
        self.assertEqual(result["freshness"], "NOT_VERIFIED")

    def test_missing_evidence_fails_closed(self):
        (self.root / "page-1.json").unlink()
        result = verify_funding_source_evidence(self.envelope, self.root)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(result["sourceByteReadback"], "FAIL")
        self.assertIn("EVIDENCE_BYTES_UNAVAILABLE", result["reasonCodes"])

    def test_tampered_evidence_fails_digest_check(self):
        (self.root / "page-0.json").write_bytes(b"tampered")
        result = verify_funding_source_evidence(self.envelope, self.root)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(result["sourceByteIntegrity"], "FAIL")
        self.assertIn("EVIDENCE_DIGEST_MISMATCH", result["reasonCodes"])

    def test_byte_length_mismatch_fails_closed(self):
        self.envelope["pages"][0]["byteLength"] += 1
        result = verify_funding_source_evidence(self.envelope, self.root)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertIn("EVIDENCE_BYTE_LENGTH_MISMATCH", result["reasonCodes"])

    def test_path_traversal_is_rejected(self):
        self.envelope["pages"][0]["relativePath"] = "../outside.json"
        with self.assertRaisesRegex(ValueError, "EVIDENCE_PATH_INVALID"):
            verify_funding_source_evidence(self.envelope, self.root)

    def test_absolute_path_is_rejected(self):
        self.envelope["pages"][0]["relativePath"] = str(self.root / "page-0.json")
        with self.assertRaisesRegex(ValueError, "EVIDENCE_PATH_INVALID"):
            verify_funding_source_evidence(self.envelope, self.root)

    def test_symlink_evidence_is_rejected(self):
        target = self.root / "page-0.json"
        link = self.root / "linked.json"
        link.symlink_to(target)
        self.envelope["pages"][0]["relativePath"] = "linked.json"
        with self.assertRaisesRegex(ValueError, "EVIDENCE_PATH_INVALID"):
            verify_funding_source_evidence(self.envelope, self.root)

    def test_repeated_page_id_is_rejected(self):
        self.envelope["pages"][1]["pageId"] = "p0"
        with self.assertRaisesRegex(ValueError, "FUNDING_PAGE_ID_DUPLICATE"):
            verify_funding_source_evidence(self.envelope, self.root)

    def test_repeated_request_fingerprint_is_rejected(self):
        self.envelope["pages"][1]["requestFingerprint"] = self.envelope["pages"][0]["requestFingerprint"]
        with self.assertRaisesRegex(ValueError, "FUNDING_PAGE_REQUEST_DUPLICATE"):
            verify_funding_source_evidence(self.envelope, self.root)

    def test_cursor_gap_is_rejected(self):
        self.envelope["pages"][1]["requestCursor"] = "wrong-cursor"
        with self.assertRaisesRegex(ValueError, "FUNDING_PAGE_CURSOR_CHAIN_INVALID"):
            verify_funding_source_evidence(self.envelope, self.root)

    def test_premature_terminal_page_is_rejected(self):
        self.envelope["pages"][0]["terminal"] = True
        with self.assertRaisesRegex(ValueError, "FUNDING_PAGE_TERMINAL_INVALID"):
            verify_funding_source_evidence(self.envelope, self.root)

    def test_missing_terminal_marker_is_rejected(self):
        self.envelope["pages"][1]["terminal"] = False
        with self.assertRaisesRegex(ValueError, "FUNDING_PAGE_TERMINAL_INVALID"):
            verify_funding_source_evidence(self.envelope, self.root)

    def test_inconsistent_source_totals_are_rejected(self):
        self.envelope["pages"][1]["sourceTotal"] = 3
        with self.assertRaisesRegex(ValueError, "FUNDING_PAGE_TOTAL_MISMATCH"):
            verify_funding_source_evidence(self.envelope, self.root)

    def test_declared_shared_lineage_blocks_independence(self):
        self.envelope["lineage"]["sharedUpstreamSystems"] = ["same-export-database"]
        result = verify_funding_source_evidence(self.envelope, self.root)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(result["independence"], "BLOCKED_SHARED_LINEAGE")
        self.assertIn("FUNDING_SOURCE_LINEAGE_SHARED", result["reasonCodes"])

    def test_same_expected_and_observed_system_blocks_independence(self):
        self.envelope["lineage"]["observedSourceSystem"] = "independent-fixture-export"
        result = verify_funding_source_evidence(self.envelope, self.root)
        self.assertEqual(result["independence"], "BLOCKED_SHARED_LINEAGE")

    def test_invalid_scope_is_rejected(self):
        self.envelope["scope"]["endAtMs"] = self.envelope["scope"]["startAtMs"]
        with self.assertRaisesRegex(ValueError, "FUNDING_SOURCE_SCOPE_INVALID"):
            verify_funding_source_evidence(self.envelope, self.root)

    def test_unknown_envelope_fields_are_rejected(self):
        self.envelope["trusted"] = True
        with self.assertRaisesRegex(ValueError, "FUNDING_SOURCE_ENVELOPE_FIELDS_INVALID"):
            verify_funding_source_evidence(self.envelope, self.root)


if __name__ == "__main__":
    unittest.main()
