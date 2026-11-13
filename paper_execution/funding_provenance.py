"""Fail-closed verification of captured funding-source evidence bytes.

This module verifies local byte readback and declared pagination structure only.
It does not authenticate an issuer, prove real-world source independence, or
promote enumeration completeness/freshness/factual truth.
"""

import hashlib
import os
import re
import stat
from pathlib import Path, PurePosixPath


_ENVELOPE_FIELDS = {
    "schemaVersion", "evidenceSnapshotId", "source", "scope",
    "snapshot", "pages", "lineage",
}
_SOURCE_FIELDS = {
    "sourceId", "sourceType", "claimedIssuer", "authorityBasis",
    "acquisitionMethod",
}
_SCOPE_FIELDS = {
    "accountRef", "instrument", "currency", "startAtMs", "endAtMs",
    "timestampSemantics", "filtersFingerprint",
}
_SNAPSHOT_FIELDS = {"asOfMs", "retrievedAtMs", "eventCutoffMs"}
_PAGE_FIELDS = {
    "ordinal", "pageId", "requestCursor", "nextCursor", "terminal",
    "requestFingerprint", "relativePath", "byteLength", "sha256",
    "recordCount", "sourceTotal",
}
_LINEAGE_FIELDS = {
    "expectedSourceSystem", "observedSourceSystem", "sharedUpstreamSystems",
}
_SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")
_MAX_PAGES = 10_000


def _require_fields(value, fields, code):
    if not isinstance(value, dict) or set(value) != fields:
        raise ValueError(code)


def _text(value, code, limit=512):
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise ValueError(code)
    return value


def _timestamp(value, code):
    if type(value) is not int or value < 0:
        raise ValueError(code)
    return value


def _count(value, code, *, optional=False):
    if optional and value is None:
        return None
    if type(value) is not int or value < 0:
        raise ValueError(code)
    return value


def _digest(value, code):
    if not isinstance(value, str) or not _SHA256.fullmatch(value):
        raise ValueError(code)
    return value


def _read_evidence_bytes(root, relative_path):
    if not isinstance(relative_path, str) or not relative_path or "\\" in relative_path:
        raise ValueError("EVIDENCE_PATH_INVALID")
    rel = PurePosixPath(relative_path)
    if rel.is_absolute() or any(part in ("", ".", "..") for part in rel.parts):
        raise ValueError("EVIDENCE_PATH_INVALID")
    root_path = Path(root).resolve(strict=True)
    if not root_path.is_dir():
        raise ValueError("EVIDENCE_ROOT_INVALID")

    candidate = root_path
    for part in rel.parts:
        candidate = candidate / part
        try:
            info = candidate.lstat()
        except OSError:
            raise FileNotFoundError("EVIDENCE_BYTES_UNAVAILABLE") from None
        if stat.S_ISLNK(info.st_mode):
            raise ValueError("EVIDENCE_PATH_INVALID")
    if not stat.S_ISREG(info.st_mode):
        raise ValueError("EVIDENCE_PATH_INVALID")
    try:
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(root_path)
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
        fd = os.open(resolved, flags)
        with os.fdopen(fd, "rb") as stream:
            return stream.read()
    except ValueError:
        raise ValueError("EVIDENCE_PATH_INVALID") from None
    except OSError:
        raise FileNotFoundError("EVIDENCE_BYTES_UNAVAILABLE") from None


def verify_funding_source_evidence(envelope, evidence_root):
    """Read back and hash each declared page; return bounded verification claims.

    Malformed contracts raise ValueError. Missing/tampered files return BLOCKED
    with reason codes. Even a clean result keeps source authenticity,
    enumeration completeness, independence, freshness and factual truth unknown.
    """
    _require_fields(envelope, _ENVELOPE_FIELDS, "FUNDING_SOURCE_ENVELOPE_FIELDS_INVALID")
    if type(envelope["schemaVersion"]) is not int or envelope["schemaVersion"] != 1:
        raise ValueError("FUNDING_SOURCE_VERSION_INVALID")
    _text(envelope["evidenceSnapshotId"], "FUNDING_SOURCE_SNAPSHOT_ID_INVALID")

    source = envelope["source"]
    _require_fields(source, _SOURCE_FIELDS, "FUNDING_SOURCE_FIELDS_INVALID")
    for key in _SOURCE_FIELDS:
        _text(source[key], "FUNDING_SOURCE_FIELD_INVALID")

    scope = envelope["scope"]
    _require_fields(scope, _SCOPE_FIELDS, "FUNDING_SOURCE_SCOPE_FIELDS_INVALID")
    for key in ("accountRef", "instrument", "currency", "timestampSemantics"):
        _text(scope[key], "FUNDING_SOURCE_SCOPE_INVALID")
    start = _timestamp(scope["startAtMs"], "FUNDING_SOURCE_SCOPE_INVALID")
    end = _timestamp(scope["endAtMs"], "FUNDING_SOURCE_SCOPE_INVALID")
    if start >= end:
        raise ValueError("FUNDING_SOURCE_SCOPE_INVALID")
    _digest(scope["filtersFingerprint"], "FUNDING_SOURCE_FILTER_FINGERPRINT_INVALID")

    snapshot = envelope["snapshot"]
    _require_fields(snapshot, _SNAPSHOT_FIELDS, "FUNDING_SOURCE_SNAPSHOT_FIELDS_INVALID")
    as_of = _timestamp(snapshot["asOfMs"], "FUNDING_SOURCE_SNAPSHOT_INVALID")
    retrieved = _timestamp(snapshot["retrievedAtMs"], "FUNDING_SOURCE_SNAPSHOT_INVALID")
    cutoff = _timestamp(snapshot["eventCutoffMs"], "FUNDING_SOURCE_SNAPSHOT_INVALID")
    if as_of > retrieved or cutoff < start or cutoff > end:
        raise ValueError("FUNDING_SOURCE_SNAPSHOT_INVALID")

    pages = envelope["pages"]
    if not isinstance(pages, list) or not 1 <= len(pages) <= _MAX_PAGES:
        raise ValueError("FUNDING_SOURCE_PAGES_INVALID")

    page_ids = set()
    request_fingerprints = set()
    cursor_values = set()
    normalized_pages = []
    for index, page in enumerate(pages):
        _require_fields(page, _PAGE_FIELDS, "FUNDING_PAGE_FIELDS_INVALID")
        ordinal = _count(page["ordinal"], "FUNDING_PAGE_ORDINAL_INVALID")
        if ordinal != index:
            raise ValueError("FUNDING_PAGE_ORDER_INVALID")
        page_id = _text(page["pageId"], "FUNDING_PAGE_ID_INVALID")
        if page_id in page_ids:
            raise ValueError("FUNDING_PAGE_ID_DUPLICATE")
        page_ids.add(page_id)
        request_fingerprint = _digest(
            page["requestFingerprint"], "FUNDING_PAGE_REQUEST_FINGERPRINT_INVALID"
        )
        if request_fingerprint in request_fingerprints:
            raise ValueError("FUNDING_PAGE_REQUEST_DUPLICATE")
        request_fingerprints.add(request_fingerprint)

        request_cursor = page["requestCursor"]
        next_cursor = page["nextCursor"]
        if request_cursor is not None:
            request_cursor = _text(request_cursor, "FUNDING_PAGE_CURSOR_INVALID")
            if request_cursor in cursor_values:
                raise ValueError("FUNDING_PAGE_CURSOR_DUPLICATE")
            cursor_values.add(request_cursor)
        if next_cursor is not None:
            next_cursor = _text(next_cursor, "FUNDING_PAGE_CURSOR_INVALID")
            if next_cursor in cursor_values:
                raise ValueError("FUNDING_PAGE_CURSOR_DUPLICATE")
            cursor_values.add(next_cursor)
        if index == 0 and request_cursor is not None:
            raise ValueError("FUNDING_PAGE_CURSOR_CHAIN_INVALID")
        if index > 0 and request_cursor != pages[index - 1]["nextCursor"]:
            raise ValueError("FUNDING_PAGE_CURSOR_CHAIN_INVALID")

        if type(page["terminal"]) is not bool:
            raise ValueError("FUNDING_PAGE_TERMINAL_INVALID")
        if page["terminal"] != (index == len(pages) - 1):
            raise ValueError("FUNDING_PAGE_TERMINAL_INVALID")
        if page["terminal"] and next_cursor is not None:
            raise ValueError("FUNDING_PAGE_TERMINAL_INVALID")
        if not page["terminal"] and next_cursor is None:
            raise ValueError("FUNDING_PAGE_TERMINAL_INVALID")

        relative_path = _text(page["relativePath"], "EVIDENCE_PATH_INVALID")
        byte_length = _count(page["byteLength"], "EVIDENCE_BYTE_LENGTH_INVALID")
        digest = _digest(page["sha256"], "EVIDENCE_DIGEST_INVALID")
        record_count = _count(page["recordCount"], "FUNDING_PAGE_RECORD_COUNT_INVALID")
        source_total = _count(
            page["sourceTotal"], "FUNDING_PAGE_SOURCE_TOTAL_INVALID", optional=True
        )
        normalized_pages.append({
            "relativePath": relative_path, "byteLength": byte_length,
            "sha256": digest, "recordCount": record_count,
            "sourceTotal": source_total,
        })

    totals = {page["sourceTotal"] for page in normalized_pages if page["sourceTotal"] is not None}
    if len(totals) > 1:
        raise ValueError("FUNDING_PAGE_TOTAL_MISMATCH")
    if totals and sum(page["recordCount"] for page in normalized_pages) != next(iter(totals)):
        raise ValueError("FUNDING_PAGE_TOTAL_MISMATCH")

    lineage = envelope["lineage"]
    _require_fields(lineage, _LINEAGE_FIELDS, "FUNDING_SOURCE_LINEAGE_FIELDS_INVALID")
    expected_system = _text(lineage["expectedSourceSystem"], "FUNDING_SOURCE_LINEAGE_INVALID")
    observed_system = _text(lineage["observedSourceSystem"], "FUNDING_SOURCE_LINEAGE_INVALID")
    shared = lineage["sharedUpstreamSystems"]
    if not isinstance(shared, list) or any(
        not isinstance(item, str) or not item.strip() for item in shared
    ):
        raise ValueError("FUNDING_SOURCE_LINEAGE_INVALID")
    if len(set(shared)) != len(shared):
        raise ValueError("FUNDING_SOURCE_LINEAGE_INVALID")

    reasons = []
    bytes_ok = True
    for page in normalized_pages:
        try:
            content = _read_evidence_bytes(evidence_root, page["relativePath"])
        except FileNotFoundError:
            bytes_ok = False
            reasons.append("EVIDENCE_BYTES_UNAVAILABLE")
            continue
        if len(content) != page["byteLength"]:
            bytes_ok = False
            reasons.append("EVIDENCE_BYTE_LENGTH_MISMATCH")
        actual = "sha256:" + hashlib.sha256(content).hexdigest()
        if actual != page["sha256"]:
            bytes_ok = False
            reasons.append("EVIDENCE_DIGEST_MISMATCH")

    shared_lineage = (
        expected_system == observed_system
        or bool(shared)
    )
    if shared_lineage:
        reasons.append("FUNDING_SOURCE_LINEAGE_SHARED")

    return {
        "status": "SOURCE_BYTES_READ_BACK" if bytes_ok and not shared_lineage else "BLOCKED",
        "sourceByteIntegrity": "PASS" if bytes_ok else "FAIL",
        "sourceByteReadback": "PASS" if bytes_ok else "FAIL",
        "paginationStructure": "PASS",
        "enumerationCompleteness": "NOT_VERIFIED",
        "independence": "BLOCKED_SHARED_LINEAGE" if shared_lineage else "DECLARED_NOT_VERIFIED",
        "sourceIdentity": "NOT_VERIFIED",
        "issuerAuthenticity": "NOT_VERIFIED",
        "freshness": "NOT_VERIFIED",
        "factualTruth": "NOT_VERIFIED",
        "globalCompleteness": "NOT_VERIFIED",
        "reasonCodes": sorted(set(reasons)),
        "pageCount": len(normalized_pages),
        "recordCount": sum(page["recordCount"] for page in normalized_pages),
        "evidenceSnapshotId": envelope["evidenceSnapshotId"],
    }
