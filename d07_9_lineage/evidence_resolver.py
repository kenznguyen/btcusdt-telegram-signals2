"""Fail-closed evidence reference and independent readback gate for D07.11."""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath

_HEX_256 = re.compile(r"^[0-9a-f]{64}$")


def collect_evidence_references(value):
    """Collect unique, non-null values in fields ending in Ref or Reference."""
    found = set()

    def visit(node):
        if isinstance(node, dict):
            for key, child in node.items():
                if (key.endswith("Ref") or key.endswith("Reference")) and isinstance(child, str):
                    found.add(child)
                else:
                    visit(child)
        elif isinstance(node, list):
            for child in node:
                visit(child)

    visit(value)
    return sorted(found)


def _result(status, errors, reference_status="NOT_VERIFIED", byte_status="NOT_VERIFIED"):
    return {
        "status": status,
        "errors": sorted(set(errors)),
        "evidenceReferenceResolution": reference_status,
        "byteIntegrity": byte_status,
        "collectorIndependence": "NOT_VERIFIED",
        "issuerIndependence": "NOT_AVAILABLE_SAME_ISSUER",
        "observationCorroboration": "NOT_VERIFIED",
        "freshness": "NOT_VERIFIED",
        "enumerationCompleteness": "NOT_VERIFIED",
        "globalCompleteness": "NOT_VERIFIED",
        "issuerAuthenticity": "NOT_VERIFIED",
        "factualTruth": "NOT_VERIFIED",
    }


def _safe_relative_path(value):
    if not isinstance(value, str) or not value or "\\\\" in value:
        return False
    parts = value.split("/")
    path = PurePosixPath(value)
    return (
        not path.is_absolute()
        and all(part not in {"", ".", ".."} for part in parts)
        and not (len(parts[0]) == 2 and parts[0][1] == ":")
    )


def _independent_read(evidence_root, relative_path, timeout_seconds):
    worker = Path(__file__).with_name("readback_worker.py")
    repo_root = Path(__file__).resolve().parents[1]
    request = json.dumps({"root": str(Path(evidence_root).resolve()), "path": relative_path})
    try:
        completed = subprocess.run(
            [sys.executable, str(worker)],
            input=request,
            text=True,
            capture_output=True,
            cwd=str(repo_root),
            env={"PYTHONPATH": str(repo_root)},
            timeout=timeout_seconds,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None, "READBACK_WORKER_UNAVAILABLE"
    try:
        response = json.loads(completed.stdout)
    except (json.JSONDecodeError, TypeError):
        return None, "READBACK_WORKER_INVALID_RESPONSE"
    if completed.returncode != 0 or response.get("ok") is not True:
        error = response.get("error", "READBACK_WORKER_FAILED")
        if error in {"UNSAFE_RELATIVE_PATH", "SYMLINK_PATH_FORBIDDEN", "PATH_ESCAPES_EVIDENCE_ROOT",
                     "EVIDENCE_TARGET_NOT_REGULAR_FILE"}:
            return None, error
        return None, "READBACK_TARGET_UNAVAILABLE"
    return {"byteLength": response.get("byteLength"), "sha256": response.get("sha256")}, None


def _valid_descriptor(value):
    if not isinstance(value, dict):
        return False
    length, digest = value.get("byteLength"), value.get("sha256")
    return (
        isinstance(length, int) and not isinstance(length, bool) and length > 0
        and isinstance(digest, str) and _HEX_256.fullmatch(digest) is not None
    )


def _disposition(reference_errors, raw_errors):
    hard_tokens = ("UNSAFE", "MISMATCH", "INVALID", "SYMLINK", "PATH_ESCAPES")
    reference_status = (
        "BLOCKED" if any(any(token in item for token in hard_tokens) for item in reference_errors)
        else ("NOT_VERIFIED" if reference_errors else "PASS")
    )
    byte_status = (
        "BLOCKED" if any(any(token in item for token in hard_tokens) for item in raw_errors)
        else ("NOT_VERIFIED" if raw_errors else "PASS")
    )
    if "BLOCKED" in {reference_status, byte_status}:
        overall = "BLOCKED"
    elif "NOT_VERIFIED" in {reference_status, byte_status}:
        overall = "NOT_VERIFIED"
    else:
        overall = "PASS"
    return overall, reference_status, byte_status


def resolve_lineage_record(
    *,
    record,
    d07_8_package,
    evidence_root,
    reference_index,
    timeout_seconds=5,
):
    """Resolve sidecar refs and independently hash raw files against D07.8 files[].

    D07.8 files[] is authoritative for each raw path, byteLength and sha256.
    PASS applies only to reference resolution and raw-byte equality. It never
    promotes collector independence or any issuer/completeness/truth claim.
    """
    if not isinstance(record, dict) or not isinstance(d07_8_package, dict):
        return _result("BLOCKED", ["LINEAGE_OR_PACKAGE_ENVELOPE_INVALID"])
    if record.get("packageId") != d07_8_package.get("packageId"):
        return _result("BLOCKED", ["D07_8_PACKAGE_ID_MISMATCH"])
    if not isinstance(reference_index, dict):
        return _result("BLOCKED", ["RESOLVER_INDEX_INVALID"])

    root = Path(evidence_root)
    if not root.exists() or not root.is_dir():
        return _result("NOT_VERIFIED", ["EVIDENCE_ROOT_UNAVAILABLE"])

    reference_errors = []
    for reference in collect_evidence_references(record):
        if not reference.strip():
            reference_errors.append("EVIDENCE_REFERENCE_EMPTY")
            continue
        descriptor = reference_index.get(reference)
        if descriptor is None:
            reference_errors.append("EVIDENCE_REFERENCE_MISSING:" + reference)
            continue
        if not _valid_descriptor(descriptor):
            reference_errors.append("EVIDENCE_REFERENCE_DESCRIPTOR_INVALID:" + reference)
            continue
        relative = descriptor.get("path")
        if not _safe_relative_path(relative):
            reference_errors.append("EVIDENCE_REFERENCE_PATH_UNSAFE:" + reference)
            continue
        actual, error = _independent_read(root, relative, timeout_seconds)
        if error:
            reference_errors.append(error + ":" + reference)
        elif actual != {"byteLength": descriptor["byteLength"], "sha256": descriptor["sha256"]}:
            reference_errors.append("EVIDENCE_REFERENCE_CONTENT_MISMATCH:" + reference)

    raw_errors = []
    raw_files = record.get("rawFiles")
    custody = record.get("custody")
    readback_files = custody.get("readbackFiles") if isinstance(custody, dict) else None
    package_files = d07_8_package.get("files")
    if not isinstance(raw_files, list) or not isinstance(readback_files, list) or not isinstance(package_files, list):
        return _result("BLOCKED", reference_errors + ["RAW_FILE_INVENTORY_INVALID"],
                       "BLOCKED" if reference_errors else "PASS", "BLOCKED")

    package_raw_files = {}
    for item in package_files:
        if not isinstance(item, dict) or not isinstance(item.get("path"), str):
            return _result("BLOCKED", reference_errors + ["D07_8_FILE_ENTRY_INVALID"],
                           "BLOCKED" if reference_errors else "PASS", "BLOCKED")
        if item["path"].startswith("raw/"):
            if item["path"] in package_raw_files:
                return _result("BLOCKED", reference_errors + ["D07_8_RAW_PATH_DUPLICATE"],
                               "BLOCKED" if reference_errors else "PASS", "BLOCKED")
            package_raw_files[item["path"]] = item

    raw_paths = [item.get("d07_8Path") for item in raw_files if isinstance(item, dict)]
    readback_paths = [item.get("d07_8Path") for item in readback_files if isinstance(item, dict)]
    if (
        len(raw_paths) != len(raw_files) or len(readback_paths) != len(readback_files)
        or len(raw_paths) != len(set(raw_paths)) or len(readback_paths) != len(set(readback_paths))
        or set(raw_paths) != set(package_raw_files) or set(readback_paths) != set(raw_paths)
    ):
        raw_errors.append("D07_8_RAW_PATH_SET_MISMATCH")
    else:
        readback_by_path = {item["d07_8Path"]: item for item in readback_files}
        for raw in raw_files:
            path = raw["d07_8Path"]
            manifest_file = package_raw_files[path]
            manifest = {
                "byteLength": manifest_file.get("byteLength"),
                "sha256": manifest_file.get("sha256"),
            }
            readback = readback_by_path[path]
            if not isinstance(manifest_file.get("byteLength"), int) or "sha256" not in manifest_file:
                raw_errors.append("D07_8_RAW_METADATA_INCOMPLETE:" + path)
                continue
            if not _valid_descriptor(manifest):
                raw_errors.append("D07_8_RAW_METADATA_INVALID:" + path)
                continue
            if readback.get("method") != "INDEPENDENT_READBACK" or raw.get("preservedOriginal") is not True:
                raw_errors.append("RAW_CUSTODY_DECLARATION_INVALID:" + path)
                continue
            if (
                raw.get("byteLengthAtReceipt") != manifest["byteLength"]
                or raw.get("sha256AtReceipt") != manifest["sha256"]
                or readback.get("byteLength") != manifest["byteLength"]
                or readback.get("sha256") != manifest["sha256"]
            ):
                raw_errors.append("RAW_DECLARATION_MANIFEST_MISMATCH:" + path)
                continue
            if not _safe_relative_path(path):
                raw_errors.append("RAW_PATH_UNSAFE:" + path)
                continue
            actual, error = _independent_read(root, path, timeout_seconds)
            if error:
                raw_errors.append(error + ":" + path)
            elif actual != manifest:
                raw_errors.append("RAW_CONTENT_MANIFEST_MISMATCH:" + path)

    overall, reference_status, byte_status = _disposition(reference_errors, raw_errors)
    return _result(overall, reference_errors + raw_errors, reference_status, byte_status)
