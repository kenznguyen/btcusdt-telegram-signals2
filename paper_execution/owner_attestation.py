"""Bounded manual Owner declaration for Dual Ledger funding/equity evidence review.

This contract records a human declaration only. It does not authenticate identity,
source issuers, factual truth, completeness, freshness, or privileged authority.
"""

import hashlib
import json
from pathlib import Path


ATTESTATION_FIELDS = {
    "schemaVersion",
    "attestationType",
    "attestorRole",
    "claimScope",
    "sourceSha",
    "fundingSnapshotId",
    "fundingPayloadHash",
    "cutoverSnapshotId",
    "cutoverPayloadHash",
    "reviewedAtMs",
    "reviewStatement",
    "nonClaims",
}
NON_CLAIMS = [
    "FACTUAL_TRUTH",
    "FRESHNESS",
    "POPULATION_COMPLETENESS",
    "PRIVILEGED_ACTION_AUTHORIZATION",
    "SOURCE_AUTHENTICITY",
]
MAX_ATTESTATION_BYTES = 65_536


def _reject_duplicate_json_keys(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("duplicate")
        value[key] = item
    return value


def _required_text(value, code, *, maximum=300):
    if (not isinstance(value, str) or not value.strip()
            or len(value) > maximum or not value.isprintable()):
        raise ValueError(code)
    return value.strip()


def _payload_hash(value):
    value = _required_text(value, "OWNER_ATTESTATION_HASH_INVALID", maximum=71)
    if (len(value) != 71 or not value.startswith("sha256:")
            or any(char not in "0123456789abcdef" for char in value[7:])):
        raise ValueError("OWNER_ATTESTATION_HASH_INVALID")
    return value


def validate_manual_owner_attestation(document, manifest):
    """Validate exact claim binding while preserving explicit non-claims."""
    if not isinstance(document, dict) or set(document) != ATTESTATION_FIELDS:
        raise ValueError("OWNER_ATTESTATION_FIELDS_INVALID")
    if type(document["schemaVersion"]) is not int or document["schemaVersion"] != 1:
        raise ValueError("OWNER_ATTESTATION_VERSION_UNSUPPORTED")
    if document["attestationType"] != "DUAL_LEDGER_BOOTSTRAP_EVIDENCE_REVIEW":
        raise ValueError("OWNER_ATTESTATION_TYPE_INVALID")
    if document["attestorRole"] != "OWNER_DECLARATION":
        raise ValueError("OWNER_ATTESTATION_ROLE_INVALID")
    if document["claimScope"] != "FUNDING_AND_EQUITY_SNAPSHOT_REVIEW":
        raise ValueError("OWNER_ATTESTATION_SCOPE_INVALID")
    if document["reviewStatement"] != (
        "I_REVIEWED_THE_IDENTIFIED_FUNDING_AND_EQUITY_SNAPSHOTS"
    ):
        raise ValueError("OWNER_ATTESTATION_STATEMENT_INVALID")
    if document["nonClaims"] != NON_CLAIMS:
        raise ValueError("OWNER_ATTESTATION_NON_CLAIMS_INVALID")

    bindings = (
        ("sourceSha", "sourceSha"),
        ("fundingSnapshotId", "fundingSnapshotId"),
        ("fundingPayloadHash", "fundingPayloadHash"),
        ("cutoverSnapshotId", "cutoverSnapshotId"),
        ("cutoverPayloadHash", "cutoverPayloadHash"),
    )
    for attestation_field, manifest_field in bindings:
        value = _required_text(
            document[attestation_field], "OWNER_ATTESTATION_BINDING_MISMATCH"
        )
        expected = _required_text(
            manifest.get(manifest_field), "OWNER_ATTESTATION_BINDING_MISMATCH"
        )
        if value != expected:
            raise ValueError("OWNER_ATTESTATION_BINDING_MISMATCH")
    _payload_hash(document["fundingPayloadHash"])
    _payload_hash(document["cutoverPayloadHash"])

    reviewed = document["reviewedAtMs"]
    observed = manifest.get("markObservedAtMs")
    recorded = manifest.get("recordedAtMs")
    if (type(reviewed) is not int or type(observed) is not int
            or type(recorded) is not int or not observed <= reviewed <= recorded):
        raise ValueError("OWNER_ATTESTATION_TIME_INVALID")

    return {
        "attestationStatus": "MANUAL_OWNER_ATTESTATION_PRESENT",
        "attestorRole": "OWNER_DECLARATION",
        "ownerIdentity": "NOT_AUTHENTICATED",
        "sourceAuthenticity": "NOT_VERIFIED",
        "factualTruth": "NOT_VERIFIED",
        "completeness": "NOT_VERIFIED",
        "freshness": "NOT_VERIFIED",
        "privilegedActionAuthorization": "NOT_GRANTED",
        "cryptographicSignature": "NOT_USED",
    }


def load_manual_owner_attestation(path_value, expected_digest, manifest):
    """Read and validate a bounded attestation file by exact-byte digest."""
    path = Path(path_value).expanduser()
    if path.is_symlink() or not path.is_file():
        raise ValueError("OWNER_ATTESTATION_FILE_UNAVAILABLE")
    try:
        raw = path.read_bytes()
    except OSError:
        raise ValueError("OWNER_ATTESTATION_FILE_UNAVAILABLE") from None
    if not raw or len(raw) > MAX_ATTESTATION_BYTES:
        raise ValueError("OWNER_ATTESTATION_SIZE_INVALID")

    expected = _payload_hash(expected_digest)
    actual = "sha256:" + hashlib.sha256(raw).hexdigest()
    if actual != expected:
        raise ValueError("OWNER_ATTESTATION_DIGEST_MISMATCH")
    try:
        document = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_reject_duplicate_json_keys,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
        raise ValueError("OWNER_ATTESTATION_JSON_INVALID") from None
    return validate_manual_owner_attestation(document, manifest)
