"""Fail-closed evidence reference and independent readback gate for D07.11.

This module verifies retained local evidence files against a supplied, normalized
reference index and D07.8 raw-file metadata. It does not authenticate issuers,
review evidence meaning, or prove collector independence.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath


_HEX_256 = re.compile(r"^[0-9a-f]{64}$")


def collect_evidence_references(value):
    """Return sorted unique non-null values in fields ending in Ref/Reference."""
    found = set()

    def visit(node):
        if isinstance(node, dict):
            for key, child in node.items():
                if (key.endswith("Ref") or key.endswith("Reference")) and isinstance(child, str) and child.strip():
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
    path = PurePosixPath(value)
    return not path.is_absolute() and all(part not in {"", ".", ".."} for part in path.parts)


def _independent_read(evidence_root, relative_path, timeout_seconds):
    worker = Path(__file__).with_name("readback_worker.py")
    repo_root = Path(__file__).resolve().parents[1]
    request = json.dumps({"root": str(Path(evidence_root).resolve()), "path": relative_path})
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


def _validate_descriptor(descriptor):
    if not isinstance(descriptor, dict):
        return False
    length, digest = descriptor.get("byteLength"), descriptor.get("sha256")
    return (
        isinstance(length, int) and not isinstance(length, bool) and length >= 0
        and isinstance(digest, str) and _HEX_256.fullmatch(digest) is not None
    )


def resolve_lineage_record(
    *,
    record,
    d07_8_package,
    evidence_root,
    reference_index,
    manifest_file_metadata,
    timeout_seconds=5,
):
    """Resolve all non-null Ref/Reference fields and independently re-hash raw files.

    manifest_file_metadata is a normalized raw-only view of D07.8 files[],
    keyed by exact relative path, with byteLength and sha256 fields.
    """
    errors = []
    if not isinstance(record, dict) or not isinstance(d07_8_package, dict):
        return _result("BLOCKED", ["LINEAGE_OR_PACKAGE_ENVELOPE_INVALID"])
    if record.get("packageId") != d07_8_package.get("packageId"):
        return _result("BLOCKED", ["D07_8_PACKAGE_ID_MISMATCH"])
    if not isinstance(reference_index, dict) or not isinstance(manifest_file_metadata, dict):
        return _result("BLOCKED", ["RESOLVER_INDEX_INVALID"])

    root = Path(evidence_root)
    if not root.exists() or not root.is_dir():
        return _result("NOT_VERIFIED", ["EVIDENCE_ROOT_UNAVAILABLE"])

    refs = collect_evidence_references(record)
    for reference in refs:
        descriptor = reference_index.get(reference)
        if descriptor is None:
            errors.append("EVIDENCE_REFERENCE_MISSING:" + reference)
            continue
        if not _validate_descriptor(descriptor):
            errors.append("EVIDENCE_REFERENCE_DESCRIPTOR_INVALID:" + reference)
            continue
        relative = descriptor.get("path")
        if not _safe_relative_path(relative):
            errors.append("EVIDENCE_REFERENCE_PATH_UNSAFE:" + reference)
            continue
        actual, error = _independent_read(root, relative, timeout_seconds)
        if error:
            errors.append(error + ":" + reference)
            continue
        if actual != {"byteLength": descriptor["byteLength"], "sha256": descriptor["sha256"]}:
            errors.append("EVIDENCE_REFERENCE_CONTENT_MISMATCH:" + reference)

    raw_files = record.get("rawFiles")
    custody = record.get("custody")
    readback_files = custody.get("readbackFiles") if isinstance(custody, dict) else None
    package_files = d07_8_package.get("files")
    if not isinstance(raw_files, list) or not isinstance(readback_files, list) or not isinstance(package_files, list):
        return _result("BLOCKED", errors + ["RAW_FILE_INVENTORY_INVALID"])

    package_raw_paths = {
        item.get("path") for item in package_files
        if isinstance(item, dict) and isinstance(item.get("path"), str) and item["path"].startswith("raw/")
    }
    raw_paths = [item.get("d07_8Path") for item in raw_files if isinstance(item, dict)]
    readback_paths = [item.get("d07_8Path") for item in readback_files if isinstance(item, dict)]
    if (
        len(raw_paths) != len(raw_files) or len(readback_paths) != len(readback_files)
        or len(raw_paths) != len(set(raw_paths)) or len(readback_paths) != len(set(readback_paths))
        or set(raw_paths) != package_raw_paths or set(readback_paths) != set(raw_paths)
    ):
        return _result("BLOCKED", errors + ["D07_8_RAW_PATH_SET_MISMATCH"],
                       "NOT_VERIFIED", "BLOCKED")

    if set(manifest_file_metadata) != package_raw_paths:
        return _result("NOT_VERIFIED", errors + ["D07_8_RAW_METADATA_INCOMPLETE"],
                       "PASS" if not any(x.startswith("EVIDENCE_REFERENCE_MISSING:") for x in errors) else "NOT_VERIFIED",
                       "NOT_VERIFIED")

    readback_by_path = {item["d07_8Path"]: item for item in readback_files}
    for raw in raw_files:
        path = raw["d07_8Path"]
        manifest = manifest_file_metadata.get(path)
        readback = readback_by_path[path]
        if not _validate_descriptor(manifest):
            errors.append("D07_8_RAW_METADATA_INVALID:" + path)
            continue
        if (
            raw.get("byteLengthAtReceipt") != manifest["byteLength"]
            or raw.get("sha256AtReceipt") != manifest["sha256"]
            or readback.get("byteLength") != manifest["byteLength"]
            or readback.get("sha256") != manifest["sha256"]
        ):
            errors.append("RAW_DECLARATION_MANIFEST_MISMATCH:" + path)
            continue
        if not _safe_relative_path(path):
            errors.append("RAW_PATH_UNSAFE:" + path)
            continue
        actual, error = _independent_read(root, path, timeout_seconds)
        if error:
            errors.append(error + ":" + path)
        elif actual != manifest:
            errors.append("RAW_CONTENT_MANIFEST_MISMATCH:" + path)

    ref_errors = [x for x in errors if x.startswith("EVIDENCE_REFERENCE_") or "READBACK_" in x or "SYMLINK" in x]
    if any("UNSAFE" in x or "MISMATCH" in x or "INVALID" in x or "SYMLINK" in x for x in errors):
        return _result("BLOCKED", errors,
                       "BLOCKED" if any(x.startswith("EVIDENCE_REFERENCE_") for x in errors) else "PASS",
                       "BLOCKED" if any(x.startswith(("RAW_", "D07_8_RAW", "RAW_CONTENT")) for x in errors) else "NOT_VERIFIED")
    if errors:
        return _result("NOT_VERIFIED", errors, "NOT_VERIFIED" if ref_errors else "PASS", "NOT_VERIFIED")
    return _result("PASS", [], "PASS", "PASS")
