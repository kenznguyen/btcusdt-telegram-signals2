"""Offline contract tests for the D07.8 funding evidence package manifest."""

import unittest

from paper_execution.funding_evidence_package import validate_funding_evidence_manifest


def manifest():
    return {
        "schemaVersion": "TARDIS_BINANCE_FUNDING_EVIDENCE_V1",
        "packageId": "fixture-001",
        "issuer": {"venue": "BINANCE", "authority": "Binance USD-M Futures"},
        "collector": {"name": "TARDIS", "channel": "BINANCE_USDM_WEBSOCKET"},
        "instrument": {
            "symbol": "BTCUSDT", "marketType": "USD_M_FUTURES",
            "contractType": "PERPETUAL", "marginAsset": "USDT", "settlementAsset": "USDT",
        },
        "time": {
            "eventTimeField": "funding_timestamp", "eventTimeUnit": "MILLISECONDS",
            "timezone": "UTC", "receivedTimeField": "local_timestamp",
        },
        "coverage": {
            "startAtMs": 1000, "endAtMs": 3000,
            "expectedSettlementTimesMs": [1000, 2000],
            "observedSettlementTimesMs": [1000, 2000],
            "expectedSetAuthority": "OWNER_SUPPLIED_REFERENCE_SCHEDULE",
        },
        "files": [{
            "path": "raw/binance-btcusdt.csv", "byteLength": 128,
            "sha256": "a" * 64, "recordCount": 2, "mediaType": "text/csv",
        }],
    }


class FundingEvidencePackageContractTest(unittest.TestCase):
    def test_valid_manifest_reports_exact_file_and_coverage_metadata(self):
        result = validate_funding_evidence_manifest(manifest())
        self.assertEqual(result["status"], "STRUCTURE_VALID")
        self.assertEqual(result["fileCount"], 1)
        self.assertEqual(result["recordCount"], 2)
        self.assertEqual(result["missingExpectedTimestampsMs"], [])
        self.assertEqual(result["unexpectedObservedTimestampsMs"], [])
        self.assertEqual(result["completeness"], "NOT_VERIFIED")

    def test_rejects_unknown_or_missing_top_level_fields(self):
        value = manifest()
        value["extra"] = True
        with self.assertRaisesRegex(ValueError, "FUNDING_PACKAGE_SCHEMA_INVALID"):
            validate_funding_evidence_manifest(value)

    def test_rejects_wrong_venue_or_collector_channel(self):
        value = manifest()
        value["issuer"]["venue"] = "BYBIT"
        with self.assertRaisesRegex(ValueError, "FUNDING_PACKAGE_IDENTITY_INVALID"):
            validate_funding_evidence_manifest(value)

    def test_rejects_path_traversal(self):
        value = manifest()
        value["files"][0]["path"] = "../outside.csv"
        with self.assertRaisesRegex(ValueError, "FUNDING_PACKAGE_PATH_INVALID"):
            validate_funding_evidence_manifest(value)

    def test_rejects_malformed_digest(self):
        value = manifest()
        value["files"][0]["sha256"] = "not-a-digest"
        with self.assertRaisesRegex(ValueError, "FUNDING_PACKAGE_DIGEST_INVALID"):
            validate_funding_evidence_manifest(value)

    def test_rejects_invalid_half_open_coverage_range(self):
        value = manifest()
        value["coverage"]["endAtMs"] = 1000
        with self.assertRaisesRegex(ValueError, "FUNDING_PACKAGE_COVERAGE_INVALID"):
            validate_funding_evidence_manifest(value)

    def test_reports_missing_expected_events_without_claiming_completeness(self):
        value = manifest()
        value["coverage"]["observedSettlementTimesMs"] = [1000]
        result = validate_funding_evidence_manifest(value)
        self.assertEqual(result["missingExpectedTimestampsMs"], [2000])
        self.assertEqual(result["completeness"], "NOT_VERIFIED")

    def test_does_not_report_observed_events_as_unexpected_when_no_schedule_was_supplied(self):
        value = manifest()
        value["coverage"]["expectedSettlementTimesMs"] = []
        result = validate_funding_evidence_manifest(value)
        self.assertEqual(result["coverageComparison"], "NOT_AVAILABLE_NO_EXPECTED_SET")
        self.assertEqual(result["missingExpectedTimestampsMs"], [])
        self.assertEqual(result["unexpectedObservedTimestampsMs"], [])

    def test_rejects_duplicate_or_unsorted_settlement_timestamps(self):
        value = manifest()
        value["coverage"]["observedSettlementTimesMs"] = [2000, 1000]
        with self.assertRaisesRegex(ValueError, "FUNDING_PACKAGE_TIMESTAMPS_INVALID"):
            validate_funding_evidence_manifest(value)

    def test_rejects_observed_timestamp_outside_declared_range(self):
        value = manifest()
        value["coverage"]["observedSettlementTimesMs"] = [3000]
        with self.assertRaisesRegex(ValueError, "FUNDING_PACKAGE_TIMESTAMP_OUT_OF_RANGE"):
            validate_funding_evidence_manifest(value)

    def test_rejects_numeric_or_boolean_timestamp_values(self):
        value = manifest()
        value["coverage"]["expectedSettlementTimesMs"] = [True, 2000]
        with self.assertRaisesRegex(ValueError, "FUNDING_PACKAGE_TIMESTAMPS_INVALID"):
            validate_funding_evidence_manifest(value)


if __name__ == "__main__":
    unittest.main()
