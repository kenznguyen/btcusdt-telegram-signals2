"""Fail-closed validator for D07.9 V2 explicit-unknown lineage assertions."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

_SCHEMA = json.loads(Path(__file__).with_name("schema.v2.json").read_text(encoding="utf-8"))
Draft202012Validator.check_schema(_SCHEMA)
_VALIDATOR = Draft202012Validator(_SCHEMA, format_checker=FormatChecker())


def _known_claims(value, path="$"):
    if isinstance(value, dict):
        if set(("status", "value", "basis", "limitation", "evidenceRefs")).issubset(value):
            yield path, value
            return
        for key, child in value.items():
            yield from _known_claims(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _known_claims(child, f"{path}[{index}]")


def _parse_timestamp(value):
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("timezone-aware timestamp required")
    return parsed


def _base_result(structural_status, errors=()):
    return {
        "structuralStatus": structural_status,
        "provenanceStatus": "NOT_VERIFIED" if structural_status == "STRUCTURE_VALID" else "BLOCKED",
        "errors": list(errors),
        "custodyCoverage": "NOT_VERIFIED",
        "byteIntegrity": "NOT_VERIFIED",
        "collectorIndependence": "NOT_VERIFIED",
        "providerAuthenticity": "NOT_VERIFIED",
        "upstreamOrigin": "NOT_VERIFIED",
        "issuerAuthenticity": "NOT_VERIFIED",
        "globalCompleteness": "NOT_VERIFIED",
        "factualTruth": "NOT_VERIFIED",
        "claimBasis": {},
    }


def validate_lineage_record_v2(record, d07_8_manifest=None):
    """Validate V2 declarations; compare bytes only when a D07.8 manifest is supplied.

    This function does not resolve evidenceRefs, authenticate their index, or
    infer provider/collector identity from OWNER_REPORTED assertions.
    """
    errors = sorted(
        _VALIDATOR.iter_errors(record),
        key=lambda error: (list(error.path), error.message),
    )
    if errors:
        return _base_result("BLOCKED", [
            f"SCHEMA:{'/'.join(str(part) for part in error.path) or '$'}:{error.message}"
            for error in errors
        ])

    result = _base_result("STRUCTURE_VALID")
    result["claimBasis"] = {
        path.lstrip("$."): claim["basis"]
        for path, claim in _known_claims(record)
    }

    # Validate known timestamps and chronology only when both values are known.
    for path, claim in _known_claims(record):
        if path.endswith((".createdAt", ".retrievedAt", ".startedAt", ".completedAt", ".at", ".reviewedAt")):
            if claim["status"] == "KNOWN":
                try:
                    _parse_timestamp(claim["value"])
                except (TypeError, ValueError, OverflowError):
                    result["structuralStatus"] = "BLOCKED"
                    result["provenanceStatus"] = "BLOCKED"
                    result["errors"].append(f"D07_9_V2_TIMESTAMP_INVALID:{path}")
    if result["errors"]:
        return result

    # A known, reversed collector interval is contradictory evidence.
    started = record["collector"]["startedAt"]
    completed = record["collector"]["completedAt"]
    if started["status"] == completed["status"] == "KNOWN":
        if _parse_timestamp(started["value"]) > _parse_timestamp(completed["value"]):
            result["provenanceStatus"] = "BLOCKED"
            result["errors"].append("D07_9_V2_ACQUISITION_CHRONOLOGY_INVALID")
            return result

    # Custody events may be empty; absence never causes fabricated events.
    events = record["custody"]["events"]
    if events:
        parsed_events = []
        try:
            parsed_events = [_parse_timestamp(event["at"]) for event in events]
        except (TypeError, ValueError, OverflowError):
            result["provenanceStatus"] = "BLOCKED"
            result["errors"].append("D07_9_V2_CUSTODY_TIMESTAMP_INVALID")
            return result
        if parsed_events != sorted(parsed_events):
            result["provenanceStatus"] = "BLOCKED"
            result["errors"].append("D07_9_V2_CUSTODY_CHRONOLOGY_INVALID")
            return result
        result["custodyCoverage"] = "DECLARED_EVENTS_PRESENT_NOT_AUTHENTICATED"

    # A known shared, material dependency blocks a positive collector-separation claim.
    for dependency in record["dependencies"]:
        shared = dependency["sharedWithBinanceRestCapture"]
        material = dependency["materialToCollectorSeparation"]
        if (shared["status"] == material["status"] == "KNOWN"
                and shared["value"] is True and material["value"] is True):
            result["collectorIndependence"] = "BLOCKED_SHARED_MATERIAL_DEPENDENCY"
            result["provenanceStatus"] = "BLOCKED"
            result["errors"].append("D07_9_V2_SHARED_MATERIAL_DEPENDENCY")
            return result

    # Package-byte comparison is a narrow cryptographic result, not source provenance.
    if d07_8_manifest is not None:
        if not isinstance(d07_8_manifest, dict) or d07_8_manifest.get("packageId") != record["packageId"]:
            result["provenanceStatus"] = "BLOCKED"
            result["errors"].append("D07_9_V2_PACKAGE_ID_MISMATCH")
            return result
        path_claim = record["subject"]["path"]
        length_claim = record["subject"]["byteLength"]
        digest_claim = record["subject"]["sha256"]
        if not all(item["status"] == "KNOWN" for item in (path_claim, length_claim, digest_claim)):
            result["errors"].append("D07_9_V2_RAW_METADATA_NOT_KNOWN")
        else:
            entries = [
                item for item in d07_8_manifest.get("files", [])
                if item.get("path") == path_claim["value"]
            ]
            if len(entries) != 1:
                result["provenanceStatus"] = "BLOCKED"
                result["errors"].append("D07_9_V2_RAW_PATH_NOT_UNIQUE_IN_MANIFEST")
                return result
            entry = entries[0]
            if entry.get("byteLength") != length_claim["value"]:
                result["provenanceStatus"] = "BLOCKED"
                result["errors"].append("D07_9_V2_RAW_LENGTH_MISMATCH")
                return result
            if entry.get("sha256") != digest_claim["value"]:
                result["provenanceStatus"] = "BLOCKED"
                result["errors"].append("D07_9_V2_RAW_DIGEST_MISMATCH")
                return result
            result["byteIntegrity"] = "PASS_WITHIN_PACKAGE_BOUNDARY"

    # Even a cryptographic package match cannot prove origin, collector identity,
    # custody, provider authenticity, completeness or truth.
    return result
