"""Trust-root lifecycle, revocation-state and evidence-retention policy.

This module intentionally does not implement cryptographic signature verification.
Sigstore cryptographic verification remains delegated to the pinned GitHub CLI.
"""
from __future__ import annotations

import base64
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import PurePosixPath

_SCHEMA = "p1.8.trust-snapshot.v1"
_RETENTION_SCHEMA = "p1.8.evidence-retention.v1"
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_SHA1 = re.compile(r"^[0-9a-f]{40}$")
_ROOT_COLLECTIONS = {
    "tlogs": "logId",
    "ctlogs": "logId",
    "certificateAuthorities": "certChain",
    "timestampAuthorities": "certChain",
}


def _canonical_bytes(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _parse_utc(value):
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ValueError("timestamp must be UTC with Z suffix")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise ValueError("invalid UTC timestamp") from exc
    if parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise ValueError("timestamp must be UTC")
    return parsed


def _parse_root(data):
    if not isinstance(data, bytes) or not data.strip():
        raise ValueError("empty trusted root")
    records = []
    for line in data.splitlines():
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("invalid JSONL trusted root") from exc
        if not isinstance(record, dict):
            raise ValueError("trusted-root JSONL record must be a JSON object")
        records.append(record)
    if not records:
        raise ValueError("empty trusted root")
    return records


def _root_inventory(data):
    inventory = {}
    for collection in _ROOT_COLLECTIONS:
        identities = set()
        for record in _parse_root(data):
            entries = record.get(collection, [])
            if entries is None:
                continue
            if not isinstance(entries, list):
                raise ValueError(f"trusted-root {collection} must be a list")
            for entry in entries:
                if not isinstance(entry, dict):
                    raise ValueError(f"trusted-root {collection} entry must be an object")
                if collection in ("tlogs", "ctlogs"):
                    log_id = entry.get("logId")
                    identity = log_id.get("keyId") if isinstance(log_id, dict) else None
                    if not isinstance(identity, str) or not identity:
                        identity = hashlib.sha256(_canonical_bytes(entry)).hexdigest()
                else:
                    chain = entry.get("certChain")
                    certs = chain.get("certificates", []) if isinstance(chain, dict) else []
                    cert_fingerprints = []
                    if isinstance(certs, list):
                        for cert in certs:
                            if isinstance(cert, dict) and isinstance(cert.get("rawBytes"), str):
                                cert_fingerprints.append(hashlib.sha256(cert["rawBytes"].encode("ascii")).hexdigest())
                    identity = entry.get("uri", "") + ":" + ",".join(cert_fingerprints)
                    if identity == ":":
                        identity = hashlib.sha256(_canonical_bytes(entry)).hexdigest()
                identities.add(identity)
        inventory[collection] = sorted(identities)
    return inventory


def build_trust_snapshot(
    trusted_root_bytes,
    *,
    captured_at,
    sequence,
    tuf_verified,
    previous_snapshot_sha256=None,
):
    _parse_root(trusted_root_bytes)
    captured = _parse_utc(captured_at)
    if not isinstance(sequence, int) or isinstance(sequence, bool) or sequence < 1:
        raise ValueError("sequence must be a positive integer")
    if sequence == 1 and previous_snapshot_sha256 is not None:
        raise ValueError("first snapshot cannot have a predecessor")
    if sequence > 1 and (not isinstance(previous_snapshot_sha256, str) or not _SHA256.fullmatch(previous_snapshot_sha256)):
        raise ValueError("later snapshot requires previous snapshot digest")
    if tuf_verified is not True:
        raise ValueError("TUF trust-root verification is required")
    body = {
        "schema": _SCHEMA,
        "sequence": sequence,
        "captured_at": captured.isoformat().replace("+00:00", "Z"),
        "trusted_root_sha256": hashlib.sha256(trusted_root_bytes).hexdigest(),
        "inventory": _root_inventory(trusted_root_bytes),
        "tuf_verification": "GH_CLI_TUF_VERIFIED",
        "previous_snapshot_sha256": previous_snapshot_sha256,
    }
    body["snapshot_sha256"] = hashlib.sha256(_canonical_bytes(body)).hexdigest()
    return body


def _verify_snapshot(snapshot):
    if not isinstance(snapshot, dict) or snapshot.get("schema") != _SCHEMA:
        raise ValueError("invalid trust snapshot schema")
    expected = snapshot.get("snapshot_sha256")
    if not isinstance(expected, str) or not _SHA256.fullmatch(expected):
        raise ValueError("invalid snapshot digest")
    body = {key: value for key, value in snapshot.items() if key != "snapshot_sha256"}
    actual = hashlib.sha256(_canonical_bytes(body)).hexdigest()
    if actual != expected:
        raise ValueError("snapshot digest mismatch")
    _parse_utc(snapshot.get("captured_at"))
    if snapshot.get("tuf_verification") != "GH_CLI_TUF_VERIFIED":
        raise ValueError("snapshot lacks verified TUF provenance")
    if not isinstance(snapshot.get("trusted_root_sha256"), str) or not _SHA256.fullmatch(snapshot["trusted_root_sha256"]):
        raise ValueError("invalid trusted-root digest")
    return True


def verify_snapshot_chain(snapshots):
    if not isinstance(snapshots, list) or not snapshots:
        raise ValueError("snapshot chain is empty")
    previous = None
    previous_time = None
    for expected_sequence, snapshot in enumerate(snapshots, start=1):
        _verify_snapshot(snapshot)
        if snapshot.get("sequence") != expected_sequence:
            raise ValueError("snapshot sequence gap or reorder")
        if snapshot.get("previous_snapshot_sha256") != previous:
            raise ValueError("snapshot predecessor mismatch")
        captured = _parse_utc(snapshot["captured_at"])
        if previous_time is not None and captured <= previous_time:
            raise ValueError("snapshot timestamps must increase")
        previous = snapshot["snapshot_sha256"]
        previous_time = captured
    return True


def compare_trusted_roots(previous_bytes, current_bytes):
    old_digest = hashlib.sha256(previous_bytes).hexdigest()
    new_digest = hashlib.sha256(current_bytes).hexdigest()
    old = _root_inventory(previous_bytes)
    new = _root_inventory(current_bytes)
    added = {key: sorted(set(new[key]) - set(old[key])) for key in old}
    removed = {key: sorted(set(old[key]) - set(new[key])) for key in old}
    changed = any(added[key] or removed[key] for key in old)
    return {
        "status": "ROTATION_DETECTED" if changed else ("UNCHANGED" if old_digest == new_digest else "CONTENT_CHANGED_NO_INVENTORY_CHANGE"),
        "previous_trusted_root_sha256": old_digest,
        "current_trusted_root_sha256": new_digest,
        "added": added,
        "removed": removed,
        "automatic_repin_allowed": False,
    }


def assess_snapshot_freshness(snapshot, *, now, max_age_days=30):
    _verify_snapshot(snapshot)
    if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() != timezone.utc.utcoffset(now):
        raise ValueError("now must be timezone-aware UTC")
    if not isinstance(max_age_days, int) or isinstance(max_age_days, bool) or max_age_days < 1:
        raise ValueError("max_age_days must be a positive integer")
    captured = _parse_utc(snapshot["captured_at"])
    age = now - captured
    if age.total_seconds() < 0:
        raise ValueError("trusted-root snapshot is from the future")
    age_days = age.total_seconds() / 86400
    return {
        "status": "FRESH" if age_days <= max_age_days else "REVIEW_DUE",
        "age_days": round(age_days, 6),
        "max_age_days": max_age_days,
        "historical_verification_allowed": True,
        "current_revocation_claim_allowed": False,
    }


def assess_revocation(*, mode, evidence=None):
    if mode not in ("OFFLINE", "ONLINE_TUF"):
        raise ValueError("mode must be OFFLINE or ONLINE_TUF")
    if evidence is None:
        return {
            "status": "NOT_CHECKED_OFFLINE" if mode == "OFFLINE" else "REVOCATION_STATUS_NOT_EXPOSED",
            "decision": "BLOCK_CURRENT_CLEARANCE",
            "may_claim_not_revoked": False,
            "may_admit_as_currently_cleared": False,
        }
    if not isinstance(evidence, dict):
        raise ValueError("revocation evidence must be an object")
    decision = evidence.get("decision")
    digest = evidence.get("evidence_sha256")
    review_id = evidence.get("review_id")
    reviewed_at = evidence.get("reviewed_at")
    if not isinstance(digest, str) or not _SHA256.fullmatch(digest):
        raise ValueError("invalid revocation evidence digest")
    if not isinstance(review_id, str) or not review_id.strip():
        raise ValueError("revocation evidence requires review id")
    _parse_utc(reviewed_at)
    if decision == "REVOKED":
        return {
            "status": "REVOKED",
            "decision": "REJECT",
            "evidence_sha256": digest,
            "review_id": review_id,
            "may_claim_not_revoked": False,
            "may_admit_as_currently_cleared": False,
        }
    if decision == "REVIEWED_CLEAR":
        return {
            "status": "REVIEWED_CLEAR_AUDIT_ONLY",
            "decision": "BLOCK_UNLESS_EVIDENCE_AUTHENTICITY_IS_SEPARATELY_VERIFIED",
            "evidence_sha256": digest,
            "review_id": review_id,
            "may_claim_not_revoked": False,
            "may_admit_as_currently_cleared": False,
        }
    raise ValueError("unsupported revocation decision")


def format_sha256_sidecar(digest, filename):
    if not isinstance(digest, str) or not _SHA256.fullmatch(digest):
        raise ValueError("invalid SHA-256 digest")
    if not isinstance(filename, str) or not filename or PurePosixPath(filename).name != filename:
        raise ValueError("sidecar filename must be a basename")
    return f"{digest}  {filename}\n"


def verify_sha256_sidecar(sidecar, digest, filename):
    expected = format_sha256_sidecar(digest, filename)
    if sidecar != expected:
        raise ValueError("SHA-256 sidecar mismatch")
    return True


def build_retention_manifest(files, *, source_sha, workflow_run_id, archived_at):
    if not isinstance(source_sha, str) or not _SHA1.fullmatch(source_sha):
        raise ValueError("invalid source SHA")
    if not isinstance(workflow_run_id, int) or isinstance(workflow_run_id, bool) or workflow_run_id < 1:
        raise ValueError("invalid workflow run id")
    _parse_utc(archived_at)
    if not isinstance(files, dict) or not files:
        raise ValueError("retention payload is empty")
    entries = []
    for name, payload in sorted(files.items()):
        if not isinstance(name, str) or not name:
            raise ValueError("invalid retained file path")
        path = PurePosixPath(name)
        if path.is_absolute() or ".." in path.parts:
            raise ValueError("invalid retained file path")
        if not isinstance(payload, bytes):
            raise ValueError("retained payload must be bytes")
        entries.append({"path": name, "size_bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest()})
    body = {
        "schema": _RETENTION_SCHEMA,
        "source_sha": source_sha,
        "workflow_run_id": workflow_run_id,
        "archived_at": archived_at,
        "retention_class": "GIT_HISTORY",
        "immutability": "NOT_WORM",
        "files": entries,
        "policy": "Git history plus 90-day Actions artifact; Git history is not WORM storage.",
    }
    body["manifest_sha256"] = hashlib.sha256(_canonical_bytes(body)).hexdigest()
    return body


def verify_retention_manifest(manifest, files):
    if not isinstance(manifest, dict) or manifest.get("schema") != _RETENTION_SCHEMA:
        raise ValueError("invalid retention manifest schema")
    expected = manifest.get("manifest_sha256")
    body = {key: value for key, value in manifest.items() if key != "manifest_sha256"}
    if not isinstance(expected, str) or hashlib.sha256(_canonical_bytes(body)).hexdigest() != expected:
        raise ValueError("retention manifest digest mismatch")
    if not isinstance(files, dict):
        raise ValueError("retained files must be a mapping")
    entries = manifest.get("files")
    if not isinstance(entries, list):
        raise ValueError("retention manifest files are invalid")
    if any(not isinstance(entry, dict) for entry in entries):
        raise ValueError("retention manifest entry is invalid")
    expected_paths = [entry.get("path") for entry in entries]
    if any(not isinstance(path, str) or not path for path in expected_paths):
        raise ValueError("retention manifest path is invalid")
    if len(expected_paths) != len(set(expected_paths)):
        raise ValueError("duplicate retained file path")
    if set(files) != set(expected_paths):
        raise ValueError("missing retained file or unexpected payload")
    for entry in entries:
        path = entry["path"]
        payload = files[path]
        if not isinstance(entry.get("sha256"), str) or not _SHA256.fullmatch(entry["sha256"]):
            raise ValueError(f"invalid retained file digest: {path}")
        if not isinstance(payload, bytes) or len(payload) != entry.get("size_bytes"):
            raise ValueError(f"retained file size mismatch: {path}")
        if hashlib.sha256(payload).hexdigest() != entry.get("sha256"):
            raise ValueError(f"retained file digest mismatch: {path}")
    return True
