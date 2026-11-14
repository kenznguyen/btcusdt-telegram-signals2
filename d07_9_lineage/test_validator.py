"""Synthetic contract tests for the D07.9 TARDIS_COLLECTOR_LINEAGE_V1 sidecar."""

import copy
import unittest

from d07_9_lineage.validator import validate_lineage_record


def fixture():
    refs = lambda prefix: prefix + "-evidence"
    return {
        "schemaVersion": "TARDIS_COLLECTOR_LINEAGE_V1",
        "recordId": "lineage-001",
        "packageId": "package-001",
        "createdAt": "2026-11-14T10:10:00Z",
        "custodian": {
            "actorRef": refs("owner"), "role": "OWNER",
            "organizationRef": None, "organizationUnavailableReason": "Individual owner",
        },
        "provider": {
            "name": "TARDIS", "dataset": "funding", "feed": "binance-usdm",
            "venue": "BINANCE", "sourceReference": refs("provider"),
        },
        "acquisition": {
            "method": "OWNER_SUPPLIED_FILE", "actorRef": refs("owner"),
            "process": "collector-process-v1", "executionRef": "acquisition-run-001",
            "hostEnvironmentRef": refs("host"),
            "startedAt": "2026-11-14T09:00:00Z", "completedAt": "2026-11-14T09:05:00Z",
            "transport": "LOCAL_TRANSFER", "channel": "owner-supplied",
            "providerPeriod": {
                "start": "2026-11-01", "end": "2026-11-02",
                "semantics": "provider daily export period", "timezone": "UTC",
            },
            "requestReference": None,
            "requestReferenceUnavailableReason": "Offline owner-supplied file",
            "networkEgressRef": None,
            "networkEgressUnavailableReason": "No network acquisition",
        },
        "rawFiles": [{
            "d07_8Path": "raw/funding.csv", "mediaType": "text/csv",
            "byteLengthAtReceipt": 128, "sha256AtReceipt": "a" * 64,
            "preservedOriginal": True,
        }],
        "custody": {
            "receiptAt": "2026-11-14T09:05:00Z", "receiptActorRef": refs("owner"),
            "storageRef": refs("storage"), "accessControlRef": refs("access"),
            "readbackStartedAt": "2026-11-14T09:05:30Z",
            "readbackAt": "2026-11-14T09:06:00Z",
            "readbackActorRef": refs("owner"), "readbackProcess": "readback-process-v1",
            "readbackRunRef": "readback-run-001",
            "readbackEnvironmentRef": refs("readback-env"),
            "readbackStorageRef": refs("storage-copy"),
            "readbackEvidenceRef": refs("readback-log"),
            "readbackFiles": [{
                "d07_8Path": "raw/funding.csv", "byteLength": 128,
                "sha256": "a" * 64, "method": "INDEPENDENT_READBACK",
            }],
            "custodyEvents": [{
                "eventId": "event-001", "eventType": "RECEIVED",
                "at": "2026-11-14T09:05:00Z", "actorRef": refs("owner"),
                "fromStorageRef": None, "toStorageRef": refs("storage"),
                "evidenceRef": refs("receipt"),
            }, {
                "eventId": "event-002", "eventType": "READ_BACK",
                "at": "2026-11-14T09:06:00Z", "actorRef": refs("owner"),
                "fromStorageRef": refs("storage-copy"), "toStorageRef": refs("readback-target"),
                "evidenceRef": refs("readback-log"),
            }],
        },
        "transformation": {
            "performed": False, "parserSourceSha": None,
            "configurationFingerprint": None, "executedAt": None,
            "fieldMappingRef": None, "normalizedOutputFiles": [],
        },
        "dependencies": [
            {
                "dependencyId": "issuer", "category": "ISSUER",
                "systemRef": "binance-issuer", "relationship": "common settlement issuer",
                "sharedWithBinanceRestCapture": "YES", "materialToCollectorSeparation": "NO",
                "evidenceRef": refs("issuer"), "unknownReason": None,
            },
            {
                "dependencyId": "collector", "category": "COLLECTOR",
                "systemRef": "tardis-collector", "relationship": "separate collector",
                "sharedWithBinanceRestCapture": "NO", "materialToCollectorSeparation": "NO",
                "evidenceRef": refs("collector"), "unknownReason": None,
            },
            {
                "dependencyId": "storage", "category": "STORAGE",
                "systemRef": "separate-storage", "relationship": "preserved copy",
                "sharedWithBinanceRestCapture": "NO", "materialToCollectorSeparation": "NO",
                "evidenceRef": refs("storage-dep"), "unknownReason": None,
            },
            {
                "dependencyId": "control", "category": "CONTROL_PLANE",
                "systemRef": "separate-control", "relationship": "independent control",
                "sharedWithBinanceRestCapture": "NO", "materialToCollectorSeparation": "NO",
                "evidenceRef": refs("control"), "unknownReason": None,
            },
            {
                "dependencyId": "network", "category": "NETWORK",
                "systemRef": "network-path", "relationship": "separate path",
                "sharedWithBinanceRestCapture": "NO", "materialToCollectorSeparation": "NO",
                "evidenceRef": refs("network"), "unknownReason": None,
            },
            {
                "dependencyId": "transform", "category": "TRANSFORMATION",
                "systemRef": "no-transform", "relationship": "no transform",
                "sharedWithBinanceRestCapture": "NO", "materialToCollectorSeparation": "NO",
                "evidenceRef": refs("transform"), "unknownReason": None,
            },
            {
                "dependencyId": "time", "category": "TIME_AUTHORITY",
                "systemRef": "utc-clock", "relationship": "time source",
                "sharedWithBinanceRestCapture": "NO", "materialToCollectorSeparation": "NO",
                "evidenceRef": refs("time"), "unknownReason": None,
            },
        ],
        "assessment": {
            "declaredBoundary": "Separate collector path relative to the identified Binance REST capture",
            "unknowns": [], "reviewDisposition": "NOT_REVIEWED",
            "reviewerRef": None, "reviewedAt": None, "rationaleRef": None,
        },
        "supersedesRecordId": None, "supersessionReason": None,
    }


def package():
    return {
        "packageId": "package-001",
        "files": [
            {"path": "raw/funding.csv"},
            {"path": "derived/normalized.csv"},
        ],
    }


class D079LineageValidatorTests(unittest.TestCase):
    def check_blocked(self, record, package_value=None, **kwargs):
        result = validate_lineage_record(record, package_value or package(), **kwargs)
        self.assertEqual(result["status"], "BLOCKED", result)
        self.assertTrue(result["errors"])

    def test_01_valid_unreviewed_record_never_promotes_byte_or_collector_status(self):
        result = validate_lineage_record(fixture(), package())
        self.assertEqual(result["status"], "NOT_VERIFIED")
        self.assertEqual(result["byteIntegrity"], "NOT_VERIFIED")
        self.assertEqual(result["collectorIndependence"], "NOT_VERIFIED")

    def test_02_reviewed_distinct_collector_path_is_scoped_and_issuer_stays_shared(self):
        value = fixture()
        value["assessment"].update({
            "reviewDisposition": "SUPPORTED_WITHIN_BOUNDARY",
            "reviewerRef": "reviewer-evidence",
            "reviewedAt": "2026-11-14T10:15:00Z",
            "rationaleRef": "review-rationale-evidence",
        })
        result = validate_lineage_record(value, package())
        self.assertEqual(result["status"], "NOT_VERIFIED")
        self.assertEqual(result["declaredReviewDisposition"], "SUPPORTED_WITHIN_BOUNDARY")
        self.assertEqual(result["evidenceReferenceResolution"], "NOT_VERIFIED")
        self.assertEqual(result["collectorIndependence"], "NOT_VERIFIED")
        self.assertEqual(result["issuerIndependence"], "NOT_AVAILABLE_SAME_ISSUER")
        self.assertEqual(result["byteIntegrity"], "NOT_VERIFIED")

    def test_03_rejects_missing_schema_version(self):
        value = fixture(); del value["schemaVersion"]; self.check_blocked(value)

    def test_04_rejects_unknown_schema_version(self):
        value = fixture(); value["schemaVersion"] = "V2"; self.check_blocked(value)

    def test_05_rejects_unknown_v1_fields(self):
        value = fixture(); value["unexpected"] = True; self.check_blocked(value)

    def test_06_rejects_duplicate_record_id_when_registry_is_supplied(self):
        self.check_blocked(fixture(), seen_record_ids={"lineage-001"})

    def test_07_rejects_empty_package_id(self):
        value = fixture(); value["packageId"] = ""; self.check_blocked(value)

    def test_08_rejects_package_id_not_bound_to_d07_8(self):
        self.check_blocked(fixture(), {"packageId": "other", "files": [{"path": "raw/funding.csv"}]})

    def test_09_rejects_omitted_raw_file_from_complete_manifest_raw_set(self):
        p = {"packageId": "package-001", "files": [{"path": "raw/a.csv"}, {"path": "raw/b.csv"}]}
        self.check_blocked(fixture(), p)

    def test_10_rejects_duplicate_raw_file_paths(self):
        value = fixture(); value["rawFiles"].append(copy.deepcopy(value["rawFiles"][0])); self.check_blocked(value)

    def test_11_rejects_path_traversal(self):
        value = fixture(); value["rawFiles"][0]["d07_8Path"] = "raw/../outside.csv"; self.check_blocked(value)

    def test_12_rejects_derived_file_misclassified_as_raw(self):
        value = fixture(); value["rawFiles"][0]["d07_8Path"] = "derived/normalized.csv"; self.check_blocked(value)

    def test_13_rejects_receipt_and_readback_path_set_mismatch(self):
        value = fixture(); value["custody"]["readbackFiles"] = []; self.check_blocked(value)

    def test_14_null_request_reference_requires_unavailable_reason(self):
        value = fixture(); value["acquisition"]["requestReferenceUnavailableReason"] = None; self.check_blocked(value)

    def test_15_present_request_reference_forbids_unavailable_reason(self):
        value = fixture(); value["acquisition"]["requestReference"] = "request-1"; self.check_blocked(value)

    def test_16_rejects_reversed_or_timezone_naive_acquisition_timestamps(self):
        value = fixture(); value["acquisition"]["completedAt"] = "2026-11-14T08:00:00Z"; self.check_blocked(value)
        value = fixture(); value["acquisition"]["startedAt"] = "2026-11-14T09:00:00"; self.check_blocked(value)

    def test_17_rejects_custody_readback_before_acquisition_completion(self):
        value = fixture(); value["custody"]["readbackStartedAt"] = "2026-11-14T09:04:00Z"; self.check_blocked(value)

    def test_18_rejects_readback_run_reusing_acquisition_execution(self):
        value = fixture(); value["custody"]["readbackRunRef"] = value["acquisition"]["executionRef"]; self.check_blocked(value)

    def test_19_rejects_same_acquisition_and_readback_process(self):
        value = fixture(); value["custody"]["readbackProcess"] = value["acquisition"]["process"]; self.check_blocked(value)

    def test_20_shared_material_dependency_blocks_positive_collector_claim(self):
        value = fixture()
        value["dependencies"][1]["sharedWithBinanceRestCapture"] = "YES"
        value["dependencies"][1]["materialToCollectorSeparation"] = "YES"
        value["assessment"].update({"reviewDisposition": "SUPPORTED_WITHIN_BOUNDARY",
            "reviewerRef": "reviewer", "reviewedAt": "2026-11-14T10:15:00Z", "rationaleRef": "rationale"})
        result = validate_lineage_record(value, package())
        self.assertEqual(result["status"], "BLOCKED")

    def test_21_unknown_materiality_fails_closed_as_not_verified(self):
        value = fixture(); value["dependencies"][1]["materialToCollectorSeparation"] = "UNKNOWN"
        value["dependencies"][1]["unknownReason"] = "Materiality cannot yet be independently assessed"
        result = validate_lineage_record(value, package())
        self.assertEqual(result["status"], "NOT_VERIFIED")

    def test_22_missing_dependency_category_prevents_positive_disposition(self):
        value = fixture(); value["dependencies"] = value["dependencies"][:-1]
        result = validate_lineage_record(value, package())
        self.assertEqual(result["status"], "NOT_VERIFIED")

    def test_23_positive_disposition_requires_reviewer_time_and_rationale(self):
        value = fixture(); value["assessment"]["reviewDisposition"] = "SUPPORTED_WITHIN_BOUNDARY"
        self.check_blocked(value)

    def test_24_rejects_secret_material_in_evidence_fields(self):
        value = fixture(); value["custodian"]["actorRef"] = "api_key=abcdef123456"; self.check_blocked(value)

    def test_25_transformation_false_requires_empty_provenance(self):
        value = fixture(); value["transformation"]["parserSourceSha"] = "a" * 40; self.check_blocked(value)

    def test_26_transformation_true_requires_complete_provenance(self):
        value = fixture(); value["transformation"]["performed"] = True; self.check_blocked(value)

    def test_27_supersession_fields_must_be_paired(self):
        value = fixture(); value["supersedesRecordId"] = "old-record"; self.check_blocked(value)

    def test_28_rejects_provider_or_venue_substitution(self):
        value = fixture(); value["provider"]["venue"] = "BYBIT"; self.check_blocked(value)

    def test_29_rejects_duplicate_or_non_chronological_custody_events(self):
        value = fixture(); value["custody"]["custodyEvents"].append(copy.deepcopy(value["custody"]["custodyEvents"][0]))
        self.check_blocked(value)

    def test_30_empty_dependencies_cannot_support_positive_claim(self):
        value = fixture(); value["dependencies"] = []
        value["assessment"].update({"reviewDisposition": "SUPPORTED_WITHIN_BOUNDARY",
            "reviewerRef": "reviewer", "reviewedAt": "2026-11-14T10:15:00Z", "rationaleRef": "rationale"})
        result = validate_lineage_record(value, package())
        self.assertEqual(result["status"], "NOT_VERIFIED")

    def test_31_binance_issuer_commonality_never_becomes_issuer_independence(self):
        value = fixture(); value["assessment"]["reviewDisposition"] = "NOT_REVIEWED"
        result = validate_lineage_record(value, package())
        self.assertEqual(result["issuerIndependence"], "NOT_AVAILABLE_SAME_ISSUER")

    def test_32_caller_cannot_supply_aggregate_pass_or_extra_dimensions(self):
        value = fixture(); value["aggregateStatus"] = "PASS"; self.check_blocked(value)

    def test_33_unknown_dependency_requires_explicit_reason(self):
        value = fixture()
        value["dependencies"][1]["materialToCollectorSeparation"] = "UNKNOWN"
        result = validate_lineage_record(value, package())
        self.assertEqual(result["status"], "BLOCKED")

    def test_34_normalized_outputs_cannot_overwrite_raw_namespace(self):
        value = fixture()
        value["transformation"] = {
            "performed": True, "parserSourceSha": "b" * 40,
            "configurationFingerprint": "config-sha256",
            "executedAt": "2026-11-14T09:07:00Z",
            "fieldMappingRef": "mapping-evidence",
            "normalizedOutputFiles": [{
                "path": "raw/normalized.csv", "byteLength": 12,
                "sha256": "c" * 64, "mediaType": "text/csv",
            }],
        }
        self.check_blocked(value)

    def test_35_readback_must_begin_after_custody_receipt(self):
        value = fixture()
        value["custody"]["readbackStartedAt"] = "2026-11-14T09:04:30Z"
        self.check_blocked(value)

    def test_36_unknown_reference_literal_is_rejected(self):
        value = fixture()
        value["provider"]["sourceReference"] = "UNKNOWN"
        self.check_blocked(value)

    def test_37_json_schema_is_valid_draft_2020_12(self):
        from jsonschema import Draft202012Validator
        from pathlib import Path
        import json
        schema = json.loads((Path(__file__).parent / "schema.v1.json").read_text())
        Draft202012Validator.check_schema(schema)


if __name__ == "__main__":
    unittest.main()
