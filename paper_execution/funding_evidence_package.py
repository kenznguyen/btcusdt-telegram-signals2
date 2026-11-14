"""Offline validator for D07.8 Tardis/Binance funding evidence manifests.

This validates manifest structure only. It does not read files, hash bytes,
parse provider records, acquire data, or establish source authenticity or
population completeness.
"""

import re


_TOP_LEVEL_FIELDS = {
    "schemaVersion", "packageId", "issuer", "collector", "instrument",
    "time", "coverage", "files",
}
_IDENTITY_FIELDS = {
    "symbol", "marketType", "contractType", "marginAsset", "settlementAsset",
}
_TIME_FIELDS = {
    "eventTimeField", "eventTimeUnit", "timezone", "receivedTimeField",
}
_COVERAGE_FIELDS = {
    "startAtMs", "endAtMs", "expectedSettlementTimesMs",
    "observedSettlementTimesMs", "expectedSetAuthority",
}
_FILE_FIELDS = {"path", "byteLength", "sha256", "recordCount", "mediaType"}
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _require_object(value, expected_fields, error_code):
    if not isinstance(value, dict) or set(value) != expected_fields:
        raise ValueError(error_code)


def _require_text(value, error_code):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(error_code)


def _validate_timestamp_list(values):
    if not isinstance(values, list):
        raise ValueError("FUNDING_PACKAGE_TIMESTAMPS_INVALID")
    previous = None
    for value in values:
        if type(value) is not int or value < 0:
            raise ValueError("FUNDING_PACKAGE_TIMESTAMPS_INVALID")
        if previous is not None and value <= previous:
            raise ValueError("FUNDING_PACKAGE_TIMESTAMPS_INVALID")
        previous = value


def validate_funding_evidence_manifest(manifest):
    """Validate a caller-supplied manifest and return non-authoritative counts.

    Coverage comparison is against the explicitly declared expected timestamp
    list only. That list's authority is not authenticated by this function.
    """
    _require_object(manifest, _TOP_LEVEL_FIELDS, "FUNDING_PACKAGE_SCHEMA_INVALID")
    if manifest["schemaVersion"] != "TARDIS_BINANCE_FUNDING_EVIDENCE_V1":
        raise ValueError("FUNDING_PACKAGE_SCHEMA_INVALID")
    _require_text(manifest["packageId"], "FUNDING_PACKAGE_SCHEMA_INVALID")

    issuer = manifest["issuer"]
    collector = manifest["collector"]
    _require_object(issuer, {"venue", "authority"}, "FUNDING_PACKAGE_IDENTITY_INVALID")
    _require_object(collector, {"name", "channel"}, "FUNDING_PACKAGE_IDENTITY_INVALID")
    _require_text(issuer["authority"], "FUNDING_PACKAGE_IDENTITY_INVALID")
    _require_text(collector["name"], "FUNDING_PACKAGE_IDENTITY_INVALID")
    _require_text(collector["channel"], "FUNDING_PACKAGE_IDENTITY_INVALID")
    if issuer["venue"] != "BINANCE" or collector["name"] != "TARDIS":
        raise ValueError("FUNDING_PACKAGE_IDENTITY_INVALID")

    instrument = manifest["instrument"]
    _require_object(instrument, _IDENTITY_FIELDS, "FUNDING_PACKAGE_IDENTITY_INVALID")
    if any(not isinstance(value, str) or not value.strip() for value in instrument.values()):
        raise ValueError("FUNDING_PACKAGE_IDENTITY_INVALID")
    if instrument != {
        "symbol": "BTCUSDT",
        "marketType": "USD_M_FUTURES",
        "contractType": "PERPETUAL",
        "marginAsset": "USDT",
        "settlementAsset": "USDT",
    }:
        raise ValueError("FUNDING_PACKAGE_IDENTITY_INVALID")

    time = manifest["time"]
    _require_object(time, _TIME_FIELDS, "FUNDING_PACKAGE_TIME_INVALID")
    for value in time.values():
        _require_text(value, "FUNDING_PACKAGE_TIME_INVALID")
    if time["eventTimeUnit"] != "MILLISECONDS" or time["timezone"] != "UTC":
        raise ValueError("FUNDING_PACKAGE_TIME_INVALID")
    if time["eventTimeField"] == time["receivedTimeField"]:
        raise ValueError("FUNDING_PACKAGE_TIME_INVALID")

    coverage = manifest["coverage"]
    _require_object(coverage, _COVERAGE_FIELDS, "FUNDING_PACKAGE_COVERAGE_INVALID")
    start = coverage["startAtMs"]
    end = coverage["endAtMs"]
    if type(start) is not int or type(end) is not int or start < 0 or end <= start:
        raise ValueError("FUNDING_PACKAGE_COVERAGE_INVALID")
    _require_text(coverage["expectedSetAuthority"], "FUNDING_PACKAGE_COVERAGE_INVALID")
    expected = coverage["expectedSettlementTimesMs"]
    observed = coverage["observedSettlementTimesMs"]
    _validate_timestamp_list(expected)
    _validate_timestamp_list(observed)

    for timestamp in expected:
        if not start <= timestamp < end:
            raise ValueError("FUNDING_PACKAGE_TIMESTAMP_OUT_OF_RANGE")
    for timestamp in observed:
        if not start <= timestamp < end:
            raise ValueError("FUNDING_PACKAGE_TIMESTAMP_OUT_OF_RANGE")

    files = manifest["files"]
    if not isinstance(files, list) or not files:
        raise ValueError("FUNDING_PACKAGE_FILES_INVALID")
    total_records = 0
    for item in files:
        _require_object(item, _FILE_FIELDS, "FUNDING_PACKAGE_FILES_INVALID")
        path = item["path"]
        _require_text(path, "FUNDING_PACKAGE_PATH_INVALID")
        path_parts = path.split("/")
        if path.startswith("/") or "\\" in path or any(part in {"", ".", ".."} for part in path_parts):
            raise ValueError("FUNDING_PACKAGE_PATH_INVALID")
        if type(item["byteLength"]) is not int or item["byteLength"] < 0:
            raise ValueError("FUNDING_PACKAGE_FILES_INVALID")
        if type(item["recordCount"]) is not int or item["recordCount"] < 0:
            raise ValueError("FUNDING_PACKAGE_FILES_INVALID")
        if not isinstance(item["sha256"], str) or not _SHA256_RE.fullmatch(item["sha256"]):
            raise ValueError("FUNDING_PACKAGE_DIGEST_INVALID")
        _require_text(item["mediaType"], "FUNDING_PACKAGE_FILES_INVALID")
        total_records += item["recordCount"]

    expected_set = set(expected)
    observed_set = set(observed)
    if expected_set:
        coverage_comparison = "COMPARED_TO_DECLARED_EXPECTED_SET"
        missing = sorted(expected_set - observed_set)
        unexpected = sorted(observed_set - expected_set)
    else:
        coverage_comparison = "NOT_AVAILABLE_NO_EXPECTED_SET"
        missing = []
        unexpected = []
    return {
        "status": "STRUCTURE_VALID",
        "fileCount": len(files),
        "recordCount": total_records,
        "coverageComparison": coverage_comparison,
        "missingExpectedTimestampsMs": missing,
        "unexpectedObservedTimestampsMs": unexpected,
        "completeness": "NOT_VERIFIED",
        "byteIntegrity": "NOT_CHECKED",
        "issuerAuthenticity": "NOT_VERIFIED",
        "collectorIndependence": "NOT_VERIFIED",
        "factualTruth": "NOT_VERIFIED",
    }
