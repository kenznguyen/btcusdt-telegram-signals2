"""Fail-closed Ed25519 verification for isolated synthetic event evidence.

This module verifies signatures over caller-supplied canonical event bytes. It
contains no signing API, private-key storage, persistence, or runtime integration.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timezone

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey


PUBLIC_KEY_BYTES = 32
SIGNATURE_BYTES = 64
_REVOCATION_STATES = {"CLEAR", "REVOKED", "UNKNOWN"}


class SignatureVerificationError(ValueError):
    """A fail-closed signature or key-policy rejection with a stable code."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class KeyRecord:
    """Synthetic public-key registry record; never contains private key material."""

    public_key: bytes
    status: str
    valid_from: datetime
    valid_until: datetime
    revocation_status: str
    revocation_evidence_verified: bool


def _require_utc(value: datetime, field: str) -> None:
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise SignatureVerificationError("REJECT_KEY_METADATA", f"{field} must be timezone-aware")
    if value.utcoffset() != timezone.utc.utcoffset(value):
        raise SignatureVerificationError("REJECT_KEY_METADATA", f"{field} must be UTC")


def verify_event_signature(
    event_bytes: bytes,
    signature: bytes,
    key_id: str,
    registry: Mapping[str, KeyRecord],
    *,
    at_time: datetime,
) -> bool:
    """Verify exact event bytes using a trusted, currently eligible public key.

    Validity is a half-open interval [valid_from, valid_until). Any missing,
    unknown, malformed, expired, revoked, or unverified trust state is rejected.
    """
    if not isinstance(event_bytes, bytes):
        raise SignatureVerificationError("REJECT_EVENT_BYTES", "event bytes must be bytes")
    if not isinstance(signature, bytes) or len(signature) != SIGNATURE_BYTES:
        raise SignatureVerificationError("REJECT_SIGNATURE_FORMAT", "Ed25519 signature must be exactly 64 bytes")
    if not isinstance(key_id, str) or not key_id:
        raise SignatureVerificationError("REJECT_UNKNOWN_KEY", "key ID must be a non-empty string")
    if not isinstance(registry, Mapping):
        raise SignatureVerificationError("REJECT_KEY_REGISTRY", "key registry must be a mapping")
    record = registry.get(key_id)
    if record is None:
        raise SignatureVerificationError("REJECT_UNKNOWN_KEY", "key ID is not present in the trusted registry")
    if not isinstance(record, KeyRecord):
        raise SignatureVerificationError("REJECT_KEY_METADATA", "registry entry has an unsupported record type")

    if record.status == "REVOKED" or record.revocation_status == "REVOKED":
        raise SignatureVerificationError("REJECT_REVOKED_KEY", "signing key is revoked")
    if record.status != "ACTIVE":
        raise SignatureVerificationError("REJECT_KEY_STATUS", "signing key is not active")
    if record.revocation_status not in _REVOCATION_STATES:
        raise SignatureVerificationError("REJECT_REVOCATION_UNKNOWN", "revocation state is missing or unknown")
    if record.revocation_status == "UNKNOWN":
        raise SignatureVerificationError("REJECT_REVOCATION_UNKNOWN", "revocation state is unknown")
    if record.revocation_evidence_verified is not True:
        raise SignatureVerificationError(
            "REJECT_REVOCATION_UNVERIFIED", "revocation evidence has not been verified"
        )

    _require_utc(at_time, "verification time")
    _require_utc(record.valid_from, "valid_from")
    _require_utc(record.valid_until, "valid_until")
    if record.valid_until <= record.valid_from:
        raise SignatureVerificationError("REJECT_KEY_METADATA", "key validity interval is empty or reversed")
    if at_time < record.valid_from:
        raise SignatureVerificationError("REJECT_KEY_NOT_YET_VALID", "signing key is not yet valid")
    if at_time >= record.valid_until:
        raise SignatureVerificationError("REJECT_KEY_EXPIRED", "signing key validity interval has ended")

    if not isinstance(record.public_key, bytes) or len(record.public_key) != PUBLIC_KEY_BYTES:
        raise SignatureVerificationError("REJECT_PUBLIC_KEY", "Ed25519 public key must be exactly 32 bytes")
    try:
        public_key = Ed25519PublicKey.from_public_bytes(record.public_key)
    except (TypeError, ValueError) as exc:
        raise SignatureVerificationError("REJECT_PUBLIC_KEY", "invalid Ed25519 public key") from exc

    try:
        public_key.verify(signature, event_bytes)
    except (InvalidSignature, TypeError, ValueError) as exc:
        raise SignatureVerificationError("REJECT_SIGNATURE", "event signature verification failed") from exc
    return True
