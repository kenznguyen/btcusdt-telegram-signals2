"""Synthetic-only Ed25519 verification fault model.

Public keys are supplied by the caller. This module does not generate, persist,
rotate, or provision signing keys and is not a production trust/key service.
"""
from __future__ import annotations

from collections.abc import Collection, Mapping

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey


class SignatureVerificationError(ValueError):
    """Base error for synthetic signature verification failures."""


class InvalidSignatureError(SignatureVerificationError):
    """The signature does not verify for the supplied message and public key."""


class UnknownSigningKeyError(SignatureVerificationError):
    """The key identifier is not present in the supplied public-key registry."""


class RevokedSigningKeyError(SignatureVerificationError):
    """The key identifier is explicitly revoked and cannot verify signatures."""


def verify_ed25519_signature(
    message: bytes,
    signature: bytes,
    *,
    key_id: str,
    public_keys: Mapping[str, bytes],
    revoked_key_ids: Collection[str] = (),
) -> bool:
    """Verify a message using an explicitly supplied active Ed25519 public key.

    Revocation is checked before registry lookup so a revoked identifier remains
    rejected even if its public-key material has already been retired.
    """
    if not isinstance(message, bytes):
        raise SignatureVerificationError("message must be bytes")
    if not isinstance(signature, bytes) or len(signature) != 64:
        raise InvalidSignatureError("Ed25519 signature must be exactly 64 bytes")
    if not isinstance(key_id, str) or not key_id:
        raise SignatureVerificationError("key_id must be a non-empty string")
    if not isinstance(public_keys, Mapping):
        raise SignatureVerificationError("public_keys must be a key-to-public-bytes mapping")
    if key_id in revoked_key_ids:
        raise RevokedSigningKeyError(f"signing key is revoked: {key_id}")

    public_key_bytes = public_keys.get(key_id)
    if public_key_bytes is None:
        raise UnknownSigningKeyError(f"unknown signing key: {key_id}")
    if not isinstance(public_key_bytes, bytes) or len(public_key_bytes) != 32:
        raise SignatureVerificationError("Ed25519 public key must be exactly 32 bytes")

    try:
        public_key = Ed25519PublicKey.from_public_bytes(public_key_bytes)
        public_key.verify(signature, message)
    except InvalidSignature as exc:
        raise InvalidSignatureError("Ed25519 signature verification failed") from exc
    except ValueError as exc:
        raise SignatureVerificationError("invalid Ed25519 public key bytes") from exc
    return True
