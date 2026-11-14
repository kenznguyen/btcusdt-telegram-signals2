"""Synthetic tests for the D07.9 V2 explicit-unknown contract."""
import copy
import json
import unittest
from pathlib import Path

from d07_9_lineage.validator_v2 import validate_lineage_record_v2


def claim(status, value=None, basis="OWNER_REPORTED", limitation=None, refs=None):
    return {"status": status, "value": value, "basis": basis,
            "limitation": limitation, "evidenceRefs": refs or []}


def fixture():
    return {
        "schemaVersion": "SOURCE_LINEAGE_RECORD_V2",
        "recordId": "d07-9-v2-001",
        "packageId": "d07-8-tardis-btcusdt-20261101-pilot-v4",
        "createdAt": "2026-11-14T13:30:00Z",
        "subject": {
            "path": claim("KNOWN", "raw/BTCUSDT.csv.gz", "LOCAL_OBSERVATION"),
            "byteLength": claim("KNOWN", 1431960, "CRYPTOGRAPHIC_CHECK"),
            "sha256": claim("KNOWN", "71963e8235106ae36fe386ef0fbd52b078df48ea854d09d814469eddeed58a8c", "CRYPTOGRAPHIC_CHECK"),
            "preservedOriginal": claim("KNOWN", True, "LOCAL_OBSERVATION"),
            "readback": claim("KNOWN", True, "CRYPTOGRAPHIC_CHECK"),
        },
        "retrieval": {
            "channel": claim("KNOWN", "CHATGPT", "OWNER_REPORTED"),
            "actor": claim("KNOWN", "OWNER", "OWNER_REPORTED"),
            "retrievedAt": claim("UNKNOWN", limitation="Exact retrieval timestamp not evidenced"),
            "upstreamOrigin": claim("UNKNOWN", limitation="Original source before ChatGPT is unknown"),
            "otherSourceUsed": claim("KNOWN", False, "OWNER_REPORTED"),
        },
        "provider": {
            "identity": claim("UNKNOWN", limitation="No provider receipt or authenticated export metadata"),
            "dataset": claim("UNKNOWN", limitation="Dataset identity not authenticated"),
            "feed": claim("UNKNOWN", limitation="Feed identity not authenticated"),
            "venue": claim("UNKNOWN", limitation="Venue label is contextual only"),
            "requestId": claim("UNAVAILABLE", limitation="No provider request or job receipt supplied"),
        },
        "collector": {
            "identity": claim("UNKNOWN", limitation="Collector identity not evidenced"),
            "software": claim("UNKNOWN", limitation="Collector software not evidenced"),
            "execution": claim("UNKNOWN", limitation="No execution record"),
            "host": claim("UNKNOWN", limitation="Host environment not evidenced"),
            "startedAt": claim("UNKNOWN", limitation="Acquisition start time unknown"),
            "completedAt": claim("UNKNOWN", limitation="Acquisition completion time unknown"),
            "transport": claim("UNKNOWN", limitation="Pre-ChatGPT transport unknown"),
            "networkEgress": claim("UNKNOWN", limitation="Network egress not evidenced"),
        },
        "custody": {
            "events": [],
            "coverage": "NOT_VERIFIED",
        },
        "dependencies": [{
            "dependencyId": "issuer",
            "category": "ISSUER",
            "identity": claim("UNKNOWN", limitation="Issuer authenticity not independently established"),
            "sharedWithBinanceRestCapture": claim("KNOWN", True, "LOCAL_OBSERVATION"),
            "materialToCollectorSeparation": claim("UNKNOWN", limitation="Collector separation cannot be assessed"),
        }],
        "assessment": {
            "declaredBoundary": "Only the immediate ChatGPT retrieval channel and D07.8 byte identity are represented",
            "unresolvedClaims": ["upstreamOrigin", "provider.identity", "collector.identity", "custody.events",
                                 "issuer authenticity", "global completeness"],
            "reviewDisposition": "NOT_REVIEWED",
            "reviewerRef": None,
            "reviewedAt": None,
            "rationaleRef": None,
        },
        "supersedes": {"recordId": None, "reason": None},
    }


class D079V2Tests(unittest.TestCase):
    def test_minimal_record_with_unknown_upstream_and_empty_custody_is_structurally_valid(self):
        result = validate_lineage_record_v2(fixture())
        self.assertEqual(result["structuralStatus"], "STRUCTURE_VALID")
        self.assertEqual(result["provenanceStatus"], "NOT_VERIFIED")
        self.assertEqual(result["custodyCoverage"], "NOT_VERIFIED")

    def test_owner_reported_chatgpt_channel_does_not_verify_upstream(self):
        result = validate_lineage_record_v2(fixture())
        self.assertEqual(result["claimBasis"]["retrieval.channel"], "OWNER_REPORTED")
        self.assertEqual(result["upstreamOrigin"], "NOT_VERIFIED")
        self.assertEqual(result["providerAuthenticity"], "NOT_VERIFIED")

    def test_unknown_claim_with_reason_is_valid(self):
        self.assertEqual(validate_lineage_record_v2(fixture())["structuralStatus"], "STRUCTURE_VALID")

    def test_unknown_claim_without_limitation_is_blocked(self):
        value = fixture()
        value["retrieval"]["upstreamOrigin"]["limitation"] = None
        self.assertEqual(validate_lineage_record_v2(value)["structuralStatus"], "BLOCKED")

    def test_known_claim_with_null_value_is_blocked(self):
        value = fixture()
        value["retrieval"]["channel"]["value"] = None
        self.assertEqual(validate_lineage_record_v2(value)["structuralStatus"], "BLOCKED")

    def test_known_claim_without_basis_is_blocked(self):
        value = fixture()
        value["retrieval"]["channel"]["basis"] = None
        self.assertEqual(validate_lineage_record_v2(value)["structuralStatus"], "BLOCKED")

    def test_owner_reported_claim_is_never_promoted_to_provider_attestation(self):
        value = fixture()
        value["provider"]["identity"] = claim("KNOWN", "TARDIS", "OWNER_REPORTED")
        result = validate_lineage_record_v2(value)
        self.assertEqual(result["providerAuthenticity"], "NOT_VERIFIED")
        self.assertEqual(result["provenanceStatus"], "NOT_VERIFIED")

    def test_empty_custody_events_are_valid_but_not_verified(self):
        value = fixture()
        value["custody"]["events"] = []
        result = validate_lineage_record_v2(value)
        self.assertEqual(result["structuralStatus"], "STRUCTURE_VALID")
        self.assertEqual(result["custodyCoverage"], "NOT_VERIFIED")

    def test_invalid_known_timestamp_is_blocked(self):
        value = fixture()
        value["collector"]["startedAt"] = claim("KNOWN", "not-a-time", "LOCAL_OBSERVATION")
        result = validate_lineage_record_v2(value)
        self.assertEqual(result["structuralStatus"], "BLOCKED")

    def test_unknown_timestamps_do_not_require_invented_chronology(self):
        result = validate_lineage_record_v2(fixture())
        self.assertEqual(result["structuralStatus"], "STRUCTURE_VALID")

    def test_raw_sha_mismatch_against_manifest_is_blocked(self):
        value = fixture()
        value["subject"]["sha256"]["value"] = "0" * 64
        manifest = {"packageId": value["packageId"], "files": [{
            "path": "raw/BTCUSDT.csv.gz", "byteLength": 1431960,
            "sha256": "71963e8235106ae36fe386ef0fbd52b078df48ea854d09d814469eddeed58a8c"
        }]}
        result = validate_lineage_record_v2(value, manifest)
        self.assertEqual(result["provenanceStatus"], "BLOCKED")
        self.assertIn("D07_9_V2_RAW_DIGEST_MISMATCH", result["errors"])

    def test_exact_raw_sha_match_only_verifies_package_byte_identity(self):
        value = fixture()
        manifest = {"packageId": value["packageId"], "files": [{
            "path": "raw/BTCUSDT.csv.gz", "byteLength": 1431960,
            "sha256": value["subject"]["sha256"]["value"]
        }]}
        result = validate_lineage_record_v2(value, manifest)
        self.assertEqual(result["byteIntegrity"], "PASS_WITHIN_PACKAGE_BOUNDARY")
        self.assertEqual(result["provenanceStatus"], "NOT_VERIFIED")

    def test_unknown_properties_are_rejected(self):
        value = fixture()
        value["aggregateStatus"] = "PASS"
        self.assertEqual(validate_lineage_record_v2(value)["structuralStatus"], "BLOCKED")

    def test_known_dependency_shared_with_rest_and_material_blocks_independence(self):
        value = fixture()
        dep = value["dependencies"][0]
        dep["materialToCollectorSeparation"] = claim("KNOWN", True, "LOCAL_OBSERVATION")
        result = validate_lineage_record_v2(value)
        self.assertEqual(result["collectorIndependence"], "BLOCKED_SHARED_MATERIAL_DEPENDENCY")

    def test_v1_schema_and_validator_are_not_used_or_mutated(self):
        from pathlib import Path
        import json
        schema = json.loads((Path(__file__).parent / "schema.v1.json").read_text())
        self.assertEqual(schema["properties"]["schemaVersion"]["const"], "TARDIS_COLLECTOR_LINEAGE_V1")


    def test_current_btcusdt_v2_draft_matches_d07_8_manifest_bytes(self):
        draft_path = Path(__file__).parent / "drafts" / "btcusdt_20261101_chatgpt_retrieval.v2.draft.json"
        record = json.loads(draft_path.read_text(encoding="utf-8"))
        manifest = {
            "packageId": "d07-8-tardis-btcusdt-20261101-pilot-v4",
            "files": [
                {
                    "path": "raw/BTCUSDT.csv.gz",
                    "byteLength": 1431960,
                    "sha256": "71963e8235106ae36fe386ef0fbd52b078df48ea854d09d814469eddeed58a8c"
                },
                {
                    "path": "transforms/field-mapping.json",
                    "byteLength": 1655,
                    "sha256": "f7fe5c5aec02ebc209d0523f2de49cc5ac7ce71249740e2b0f5c19f7beb57e0c"
                }
            ]
        }
        result = validate_lineage_record_v2(record, manifest)
        self.assertEqual(result["structuralStatus"], "STRUCTURE_VALID")
        self.assertEqual(result["provenanceStatus"], "NOT_VERIFIED")
        self.assertEqual(result["byteIntegrity"], "PASS_WITHIN_PACKAGE_BOUNDARY")
        self.assertEqual(result["custodyCoverage"], "NOT_VERIFIED")
        self.assertEqual(result["providerAuthenticity"], "NOT_VERIFIED")
        self.assertEqual(result["collectorIndependence"], "NOT_VERIFIED")
        self.assertEqual(result["upstreamOrigin"], "NOT_VERIFIED")
        self.assertEqual(result["globalCompleteness"], "NOT_VERIFIED")
        self.assertEqual(result["issuerAuthenticity"], "NOT_VERIFIED")
        self.assertEqual(result["factualTruth"], "NOT_VERIFIED")


if __name__ == "__main__":
    unittest.main()
