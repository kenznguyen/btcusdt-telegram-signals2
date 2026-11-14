"""Fail-closed structural and lineage validator for D07.9 V1."""
from __future__ import annotations
import json
import re
from datetime import datetime
from pathlib import Path
from jsonschema import Draft202012Validator, FormatChecker

_SCHEMA = json.loads(Path(__file__).with_name("schema.v1.json").read_text(encoding="utf-8"))
_VALIDATOR = Draft202012Validator(_SCHEMA, format_checker=FormatChecker())
_REQUIRED_DEPENDENCIES = {"ISSUER", "COLLECTOR", "STORAGE", "CONTROL_PLANE", "NETWORK", "TRANSFORMATION", "TIME_AUTHORITY"}
_SECRET_PATTERNS = (
    re.compile(r"(?i)\b(api[_-]?key|api[_-]?secret|password|access[_-]?token)\s*[:=]\s*[^\s,;]+"),
    re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]{8,}"),
    re.compile(r"://[^/@:\s]+:[^/@\s]+@"),
)

def _time(value):
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("timezone required")
    return parsed

def _strings(value, path="$"):
    if isinstance(value, dict):
        for key, child in value.items():
            yield from _strings(key, path + ".<key>")
            yield from _strings(child, path + "." + str(key))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _strings(child, f"{path}[{index}]")
    elif isinstance(value, str):
        yield path, value

def _safe_path(path):
    if not path or path.startswith("/") or "\\" in path:
        return False
    return all(part not in {"", ".", ".."} for part in path.split("/"))

def _result(status, errors=(), collector="NOT_VERIFIED"):
    return {
        "status": status, "errors": list(errors),
        "byteIntegrity": "NOT_VERIFIED", "collectorIndependence": collector,
        "issuerIndependence": "NOT_AVAILABLE_SAME_ISSUER",
        "observationCorroboration": "NOT_VERIFIED",
        "enumerationCompleteness": "NOT_VERIFIED", "freshness": "NOT_VERIFIED",
        "issuerAuthenticity": "NOT_VERIFIED", "globalCompleteness": "NOT_VERIFIED",
        "factualTruth": "NOT_VERIFIED",
    }

def validate_lineage_record(record, d07_8_package, *, seen_record_ids=None):
    """Validate declarations only; never reads refs or raw bytes."""
    schema_errors = sorted(_VALIDATOR.iter_errors(record), key=lambda e: list(e.path))
    if schema_errors:
        return _result("BLOCKED", [
            f"SCHEMA:{'/'.join(str(p) for p in e.path) or '$'}:{e.message}"
            for e in schema_errors
        ])
    if not isinstance(d07_8_package, dict) or not isinstance(d07_8_package.get("packageId"), str):
        return _result("BLOCKED", ["D07_8_PACKAGE_ENVELOPE_INVALID"])
    if record["packageId"] != d07_8_package["packageId"]:
        return _result("BLOCKED", ["D07_8_PACKAGE_ID_MISMATCH"])
    if seen_record_ids and record["recordId"] in seen_record_ids:
        return _result("BLOCKED", ["D07_9_RECORD_ID_DUPLICATE"])

    errors = []
    for path, text in _strings(record):
        if any(pattern.search(text) for pattern in _SECRET_PATTERNS):
            errors.append(f"SECRET_MATERIAL_DETECTED:{path}")
        if path.endswith("Ref") and text.strip().upper() == "UNKNOWN":
            errors.append(f"UNRESOLVED_REFERENCE_LITERAL:{path}")
    if errors:
        return _result("BLOCKED", errors)

    acquisition, custody = record["acquisition"], record["custody"]
    assessment, transformation = record["assessment"], record["transformation"]
    try:
        started, completed = _time(acquisition["startedAt"]), _time(acquisition["completedAt"])
        created, receipt = _time(record["createdAt"]), _time(custody["receiptAt"])
        readback_started, readback_done = _time(custody["readbackStartedAt"]), _time(custody["readbackAt"])
    except (TypeError, ValueError, OverflowError):
        return _result("BLOCKED", ["D07_9_TIMESTAMP_INVALID"])
    if started > completed or created < completed or receipt < completed:
        errors.append("D07_9_ACQUISITION_EVENT_ORDER_INVALID")
    if readback_started < completed or readback_done < readback_started:
        errors.append("D07_9_READBACK_EVENT_ORDER_INVALID")
    if custody["readbackRunRef"] == acquisition["executionRef"]:
        errors.append("D07_9_READBACK_REUSES_ACQUISITION_EXECUTION")
    if custody["readbackProcess"] == acquisition["process"]:
        errors.append("D07_9_READBACK_PROCESS_NOT_DISTINCT")

    custodian = record["custodian"]
    if custodian["organizationRef"] is None:
        if custodian["role"] != "OWNER" or not custodian["organizationUnavailableReason"]:
            errors.append("D07_9_CUSTODIAN_ORGANIZATION_NULLABILITY_INVALID")
    elif custodian["organizationUnavailableReason"] is not None:
        errors.append("D07_9_CUSTODIAN_ORGANIZATION_REASON_CONFLICT")
    for ref_key, reason_key in (
        ("requestReference", "requestReferenceUnavailableReason"),
        ("networkEgressRef", "networkEgressUnavailableReason"),
    ):
        ref_value, reason = acquisition[ref_key], acquisition[reason_key]
        if ref_value is None and (not isinstance(reason, str) or not reason.strip()):
            errors.append(f"D07_9_{ref_key.upper()}_REASON_REQUIRED")
        if ref_value is not None and reason is not None:
            errors.append(f"D07_9_{ref_key.upper()}_REASON_CONFLICT")

    if assessment["reviewDisposition"] == "NOT_REVIEWED":
        if any(assessment[k] is not None for k in ("reviewerRef", "reviewedAt", "rationaleRef")):
            errors.append("D07_9_UNREVIEWED_METADATA_MUST_BE_NULL")
    elif any(assessment[k] is None for k in ("reviewerRef", "reviewedAt", "rationaleRef")):
        errors.append("D07_9_REVIEW_EVIDENCE_REQUIRED")
    if (record["supersedesRecordId"] is None) != (record["supersessionReason"] is None):
        errors.append("D07_9_SUPERSESSION_PAIR_INVALID")

    if transformation["performed"] is False:
        if any(transformation[k] is not None for k in (
            "parserSourceSha", "configurationFingerprint", "executedAt", "fieldMappingRef"
        )) or transformation["normalizedOutputFiles"]:
            errors.append("D07_9_TRANSFORMATION_FALSE_HAS_PROVENANCE")
    else:
        if any(transformation[k] is None for k in (
            "parserSourceSha", "configurationFingerprint", "executedAt", "fieldMappingRef"
        )) or not transformation["normalizedOutputFiles"]:
            errors.append("D07_9_TRANSFORMATION_PROVENANCE_INCOMPLETE")
        if transformation["parserSourceSha"] and not re.fullmatch(r"[0-9a-f]{40,64}", transformation["parserSourceSha"]):
            errors.append("D07_9_PARSER_SOURCE_SHA_INVALID")

    files = d07_8_package.get("files")
    if not isinstance(files, list) or not all(isinstance(x, dict) and isinstance(x.get("path"), str) for x in files):
        return _result("BLOCKED", ["D07_8_FILE_INVENTORY_INVALID"])
    package_paths = [x["path"] for x in files]
    if len(package_paths) != len(set(package_paths)) or any(not _safe_path(p) for p in package_paths):
        return _result("BLOCKED", ["D07_8_FILE_INVENTORY_PATH_INVALID"])
    expected_raw = {p for p in package_paths if p.startswith("raw/")}
    raw = record["rawFiles"]
    raw_paths = [x["d07_8Path"] for x in raw]
    readback = custody["readbackFiles"]
    readback_paths = [x["d07_8Path"] for x in readback]
    if any(not _safe_path(p) or not p.startswith("raw/") for p in raw_paths):
        errors.append("D07_9_RAW_PATH_INVALID")
    if len(raw_paths) != len(set(raw_paths)):
        errors.append("D07_9_RAW_PATH_DUPLICATE")
    if set(raw_paths) != expected_raw:
        errors.append("D07_9_RAW_FILE_SET_MISMATCH")
    if len(readback_paths) != len(set(readback_paths)) or set(readback_paths) != set(raw_paths):
        errors.append("D07_9_READBACK_PATH_SET_MISMATCH")
    receipt_by_path = {x["d07_8Path"]: x for x in raw}
    for item in readback:
        source = receipt_by_path.get(item["d07_8Path"])
        if source and (item["byteLength"] != source["byteLengthAtReceipt"] or item["sha256"] != source["sha256AtReceipt"]):
            errors.append("D07_9_READBACK_DECLARATION_MISMATCH")

    events = custody["custodyEvents"]
    event_ids = [x["eventId"] for x in events]
    if len(event_ids) != len(set(event_ids)):
        errors.append("D07_9_CUSTODY_EVENT_ID_DUPLICATE")
    previous = None
    for event in events:
        try:
            event_time = _time(event["at"])
        except (TypeError, ValueError, OverflowError):
            errors.append("D07_9_CUSTODY_EVENT_TIMESTAMP_INVALID")
            continue
        if previous is not None and event_time < previous:
            errors.append("D07_9_CUSTODY_EVENT_ORDER_INVALID")
        previous = event_time
        if event["eventType"] in {"COPIED", "TRANSFERRED"} and (
            not event["fromStorageRef"] or not event["toStorageRef"]
        ):
            errors.append("D07_9_CUSTODY_TRANSFER_ENDPOINT_REQUIRED")
    if errors:
        return _result("BLOCKED", errors)

    dependencies = record["dependencies"]
    ids = [x["dependencyId"] for x in dependencies]
    categories = {x["category"] for x in dependencies}
    if len(ids) != len(set(ids)):
        return _result("BLOCKED", ["D07_9_DEPENDENCY_ID_DUPLICATE"])
    if not dependencies or categories != _REQUIRED_DEPENDENCIES:
        return _result("NOT_VERIFIED", ["D07_9_DEPENDENCY_INVENTORY_INCOMPLETE"])
    if any(x["sharedWithBinanceRestCapture"] == "YES" and x["materialToCollectorSeparation"] == "YES" for x in dependencies):
        return _result("BLOCKED", ["D07_9_SHARED_MATERIAL_DEPENDENCY"])
    unresolved = [
        x for x in dependencies
        if x["materialToCollectorSeparation"] == "UNKNOWN"
        or (x["sharedWithBinanceRestCapture"] == "UNKNOWN" and x["materialToCollectorSeparation"] in {"YES", "UNKNOWN"})
        or (x["materialToCollectorSeparation"] == "NO" and not x["evidenceRef"])
    ]
    if unresolved or assessment["unknowns"]:
        return _result("NOT_VERIFIED", ["D07_9_DEPENDENCY_OR_REVIEW_UNKNOWN"])
    if assessment["reviewDisposition"] == "BLOCKED":
        return _result("BLOCKED", ["D07_9_REVIEW_DISPOSITION_BLOCKED"])
    if assessment["reviewDisposition"] != "SUPPORTED_WITHIN_BOUNDARY":
        return _result("NOT_VERIFIED", ["D07_9_REVIEW_NOT_ACCEPTED"])
    return _result("SUPPORTED_WITHIN_BOUNDARY", collector="SUPPORTED_WITHIN_BOUNDARY")
