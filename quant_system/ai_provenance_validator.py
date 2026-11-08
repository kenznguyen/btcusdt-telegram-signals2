"""Offline verification of signed AI OOS provenance envelopes.

Trust roots are supplied by the caller; this module embeds no signing keys and
never issues calibration or trading attestations.
"""
from dataclasses import dataclass
import base64
import binascii
import hashlib
import json
import re
from collections.abc import Mapping

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey


_REQUIRED_MANIFEST_KEYS = {
    "schema_version", "key_id", "model_version", "strategy_version",
    "dataset_version", "issued_at_ms", "expires_at_ms", "temporal_split",
    "artifacts",
}
_REQUIRED_SPLIT_KEYS = {"train_end_ms", "oos_start_ms", "oos_end_ms"}
_REQUIRED_ARTIFACT_ROLES = {
    "model", "dataset", "predictions", "split_protocol", "calibration_report",
}
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class ProvenanceVerification:
    accepted: bool
    reasons: tuple[str, ...]
    key_id: str | None
    manifest_sha256: str
    verified_artifacts: tuple[str, ...]
    attestation_issued: bool = False


def _reject_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _parse_envelope(envelope):
    if isinstance(envelope, (bytes, str)):
        raw = envelope.decode("utf-8") if isinstance(envelope, bytes) else envelope
        parsed = json.loads(raw, object_pairs_hook=_reject_duplicate_keys)
    else:
        parsed = envelope
    if not isinstance(parsed, Mapping) or set(parsed) != {"manifest", "signature"}:
        raise ValueError("envelope must contain manifest and signature only")
    return parsed["manifest"], parsed["signature"]


def _canonical_json(value):
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _valid_identity(value):
    return isinstance(value, str) and bool(value.strip()) and len(value) <= 256


def verify_signed_provenance(envelope, artifacts, trusted_public_keys, *, now_ms):
    """Verify signature, trusted key, exact artifact bytes and OOS chronology.

    trusted_public_keys maps key IDs to raw 32-byte Ed25519 public keys. The
    caller must load this mapping from an independently protected trust store.
    A passing result is provenance verification only, not trade authorization.
    """
    reasons = []
    try:
        manifest, signature_text = _parse_envelope(envelope)
    except (UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError):
        return ProvenanceVerification(False, ("ENVELOPE_INVALID",), None, "", ())

    if not isinstance(manifest, Mapping) or set(manifest) != _REQUIRED_MANIFEST_KEYS:
        return ProvenanceVerification(False, ("MANIFEST_SCHEMA_INVALID",), None, "", ())
    try:
        canonical = _canonical_json(manifest)
    except (TypeError, ValueError):
        return ProvenanceVerification(False, ("MANIFEST_SCHEMA_INVALID",), None, "", ())
    manifest_sha256 = hashlib.sha256(canonical).hexdigest()
    key_id = manifest.get("key_id")
    if not _valid_identity(key_id):
        return ProvenanceVerification(False, ("MANIFEST_SCHEMA_INVALID",), None, manifest_sha256, ())
    if not isinstance(trusted_public_keys, Mapping) or key_id not in trusted_public_keys:
        return ProvenanceVerification(False, ("SIGNING_KEY_UNTRUSTED",), key_id, manifest_sha256, ())

    try:
        if not isinstance(signature_text, str):
            raise ValueError("signature must be base64 text")
        signature = base64.b64decode(signature_text, validate=True)
    except (ValueError, binascii.Error):
        return ProvenanceVerification(False, ("SIGNATURE_ENCODING_INVALID",), key_id, manifest_sha256, ())
    try:
        public_key_bytes = trusted_public_keys[key_id]
        if not isinstance(public_key_bytes, bytes) or len(public_key_bytes) != 32:
            raise ValueError("invalid Ed25519 public key")
        Ed25519PublicKey.from_public_bytes(public_key_bytes).verify(signature, canonical)
    except (InvalidSignature, ValueError, TypeError):
        return ProvenanceVerification(False, ("SIGNATURE_INVALID",), key_id, manifest_sha256, ())

    if type(manifest.get("schema_version")) is not int or manifest["schema_version"] != 1:
        reasons.append("MANIFEST_SCHEMA_INVALID")
    for field in ("model_version", "strategy_version", "dataset_version"):
        if not _valid_identity(manifest.get(field)):
            reasons.append("MANIFEST_SCHEMA_INVALID")

    issued, expires = manifest.get("issued_at_ms"), manifest.get("expires_at_ms")
    if (type(now_ms) is not int or now_ms <= 0 or type(issued) is not int
            or type(expires) is not int or issued <= 0 or expires <= issued or issued > now_ms):
        reasons.append("MANIFEST_TIME_INVALID")
    elif now_ms >= expires:
        reasons.append("MANIFEST_EXPIRED")

    split = manifest.get("temporal_split")
    if not isinstance(split, Mapping) or set(split) != _REQUIRED_SPLIT_KEYS:
        reasons.append("TEMPORAL_SPLIT_INVALID")
    else:
        train_end, oos_start, oos_end = (split.get("train_end_ms"), split.get("oos_start_ms"), split.get("oos_end_ms"))
        if (any(type(value) is not int or value <= 0 for value in (train_end, oos_start, oos_end))
                or not (train_end < oos_start <= oos_end)):
            reasons.append("TEMPORAL_SPLIT_INVALID")

    manifest_artifacts = manifest.get("artifacts")
    if (not isinstance(manifest_artifacts, Mapping)
            or set(manifest_artifacts) != _REQUIRED_ARTIFACT_ROLES):
        reasons.append("ARTIFACT_ROLE_SET_MISMATCH")
    if not isinstance(artifacts, Mapping) or set(artifacts) != _REQUIRED_ARTIFACT_ROLES:
        reasons.append("ARTIFACT_ROLE_SET_MISMATCH")
    elif isinstance(manifest_artifacts, Mapping):
        for role in sorted(_REQUIRED_ARTIFACT_ROLES):
            descriptor, data = manifest_artifacts.get(role), artifacts.get(role)
            if not isinstance(descriptor, Mapping) or set(descriptor) != {"sha256", "size_bytes"}:
                reasons.append(f"ARTIFACT_DESCRIPTOR_INVALID:{role}")
                continue
            if not isinstance(data, bytes):
                reasons.append(f"ARTIFACT_MISSING:{role}")
                continue
            expected_hash, expected_size = descriptor.get("sha256"), descriptor.get("size_bytes")
            if not isinstance(expected_hash, str) or not _SHA256.fullmatch(expected_hash):
                reasons.append(f"ARTIFACT_DESCRIPTOR_INVALID:{role}")
                continue
            if type(expected_size) is not int or expected_size <= 0:
                reasons.append(f"ARTIFACT_DESCRIPTOR_INVALID:{role}")
                continue
            if len(data) != expected_size:
                reasons.append(f"ARTIFACT_SIZE_MISMATCH:{role}")
                continue
            if hashlib.sha256(data).hexdigest() != expected_hash:
                reasons.append(f"ARTIFACT_HASH_MISMATCH:{role}")
                continue
            verified.append(role)

    return ProvenanceVerification(
        accepted=not reasons, reasons=tuple(sorted(set(reasons))), key_id=key_id,
        manifest_sha256=manifest_sha256, verified_artifacts=tuple(verified),
        attestation_issued=False,
    )