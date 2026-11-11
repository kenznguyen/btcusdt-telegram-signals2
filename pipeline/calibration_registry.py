"""Read-only verification primitives for the AI calibration registry.

This module verifies exact manifest bytes, a detached Ed25519 signature against
an independently pinned public key, and the referenced artifact bytes. It does
not establish registry promotion, revocation state, OOS quality or admission.
"""
import base64
import binascii
from datetime import datetime, timedelta, timezone
import hashlib
from decimal import Decimal, InvalidOperation, localcontext
import json
import re
from pathlib import PurePosixPath

import rfc8785
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey


class CalibrationVerificationError(ValueError):
    """A calibration registry object failed a fail-closed verification check."""


MANIFEST_SCHEMA = "ai-calibration-manifest/v1"
ENVELOPE_SCHEMA = "ai-calibration-signature-envelope/v1"
CANONICALIZATION = "RFC8785-JCS"
SIGNATURE_ALGORITHM = "Ed25519"
REGISTRY_NAMESPACE = "btc-usdt/ai-calibration"
SIGNATURE_DOMAIN = b"BTCUSDT-AI-CALIBRATION-MANIFEST\x00v1\x00"

MANIFEST_FIELDS = frozenset({
    "manifest_schema", "manifest_id", "registry_namespace", "record_sequence",
    "previous_record_digest", "record_type", "calibration_id", "calibration_version",
    "artifact_path", "artifact_digest", "artifact_size_bytes", "artifact_media_type",
    "calibration_method", "method_version", "transform_schema", "model_id",
    "model_version", "model_artifact_digest", "strategy_id", "strategy_version",
    "strategy_source_commit", "training_dataset_id", "training_dataset_digest",
    "training_cutoff", "calibration_dataset_id", "calibration_dataset_digest",
    "calibration_start", "calibration_end", "label_definition_id",
    "label_definition_digest", "forecast_horizon_value", "forecast_horizon_unit",
    "sample_count", "evaluation_record_id", "evaluation_record_digest", "created_at",
    "publisher_id",
})
ENVELOPE_FIELDS = frozenset({
    "envelope_schema", "envelope_id", "manifest_id", "manifest_schema",
    "canonicalization_profile", "digest_algorithm", "manifest_digest",
    "manifest_size_bytes", "signature_algorithm", "key_id", "signer_role",
    "namespace", "signature_base64",
})
TRUST_FIELDS = frozenset({
    "key_id", "algorithm", "public_key_base64", "public_key_fingerprint",
    "signer_role", "registry_namespace", "publisher_id", "allowed_record_types",
})
_DIGEST = re.compile(r"sha256:[0-9a-f]{64}\Z")
_IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:/-]{0,127}\Z")
_UNSIGNED = re.compile(r"(?:0|[1-9][0-9]*)\Z")
_COMMIT = re.compile(r"[0-9a-f]{40}\Z")
_TIMESTAMP = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z\Z")


def _fail(reason):
    raise CalibrationVerificationError(reason)


def _reject_number(_value):
    _fail("JSON_NUMBER_NOT_ALLOWED")


def _reject_constant(_value):
    _fail("JSON_CONSTANT_NOT_ALLOWED")


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            _fail("DUPLICATE_JSON_KEY")
        result[key] = value
    return result


def _sha256(data):
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _unsigned(value, reason):
    if not isinstance(value, str) or len(value) > 20 or _UNSIGNED.fullmatch(value) is None:
        _fail(reason)
    parsed = int(value)
    if parsed > 18_446_744_073_709_551_615:
        _fail(reason)
    return parsed


def _require_string(value, reason, pattern=None):
    if not isinstance(value, str) or not value:
        _fail(reason)
    if pattern is not None and pattern.fullmatch(value) is None:
        _fail(reason)
    return value


def _canonical_manifest(manifest_bytes):
    if not isinstance(manifest_bytes, bytes) or not manifest_bytes:
        _fail("INVALID_MANIFEST_BYTES")
    try:
        decoded = manifest_bytes.decode("utf-8", errors="strict")
        if decoded.startswith("\\ufeff"):
            _fail("MANIFEST_BOM_NOT_ALLOWED")
        payload = json.loads(
            decoded,
            object_pairs_hook=_unique_object,
            parse_int=_reject_number,
            parse_float=_reject_number,
            parse_constant=_reject_constant,
        )
    except CalibrationVerificationError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError):
        _fail("INVALID_MANIFEST_JSON")
    if not isinstance(payload, dict):
        _fail("INVALID_MANIFEST_ROOT")
    try:
        canonical_bytes = rfc8785.dumps(payload)
    except Exception:
        _fail("MANIFEST_CANONICALIZATION_FAILED")
    if canonical_bytes != manifest_bytes:
        _fail("NONCANONICAL_MANIFEST")
    return payload


def _validate_manifest(payload):
    if set(payload) != MANIFEST_FIELDS:
        _fail("MANIFEST_SCHEMA_MISMATCH")
    for name, value in payload.items():
        _require_string(value, "MANIFEST_FIELD_INVALID:" + name)
    if payload["manifest_schema"] != MANIFEST_SCHEMA:
        _fail("MANIFEST_SCHEMA_UNSUPPORTED")
    if payload["registry_namespace"] != REGISTRY_NAMESPACE:
        _fail("MANIFEST_NAMESPACE_MISMATCH")
    if payload["record_type"] != "CALIBRATION_ARTIFACT":
        _fail("MANIFEST_RECORD_TYPE_UNSUPPORTED")
    for name in (
        "manifest_id", "calibration_id", "calibration_version", "calibration_method",
        "method_version", "transform_schema", "model_id", "model_version",
        "strategy_id", "strategy_version", "training_dataset_id",
        "calibration_dataset_id", "label_definition_id", "evaluation_record_id",
        "publisher_id",
    ):
        _require_string(payload[name], "MANIFEST_IDENTIFIER_INVALID:" + name, _IDENTIFIER)
    if _COMMIT.fullmatch(payload["strategy_source_commit"]) is None:
        _fail("STRATEGY_SOURCE_COMMIT_INVALID")
    for name in (
        "artifact_digest", "model_artifact_digest", "training_dataset_digest",
        "calibration_dataset_digest", "label_definition_digest",
        "evaluation_record_digest",
    ):
        if _DIGEST.fullmatch(payload[name]) is None:
            _fail("MANIFEST_DIGEST_INVALID:" + name)
    sequence = _unsigned(payload["record_sequence"], "MANIFEST_INTEGER_STRING_INVALID:record_sequence")
    artifact_size = _unsigned(payload["artifact_size_bytes"], "MANIFEST_INTEGER_STRING_INVALID:artifact_size_bytes")
    sample_count = _unsigned(payload["sample_count"], "MANIFEST_INTEGER_STRING_INVALID:sample_count")
    horizon = _unsigned(payload["forecast_horizon_value"], "MANIFEST_INTEGER_STRING_INVALID:forecast_horizon_value")
    if sequence < 1 or artifact_size < 1 or sample_count < 1 or horizon < 1:
        _fail("MANIFEST_INTEGER_RANGE_INVALID")
    previous = payload["previous_record_digest"]
    if (sequence == 1 and previous != "GENESIS") or (
        sequence > 1 and _DIGEST.fullmatch(previous) is None
    ):
        _fail("PREVIOUS_RECORD_DIGEST_INVALID")
    if payload["forecast_horizon_unit"] not in {"ms", "s", "m", "h"}:
        _fail("FORECAST_HORIZON_UNIT_INVALID")
    if payload["artifact_media_type"] not in {"application/json", "application/octet-stream"}:
        _fail("ARTIFACT_MEDIA_TYPE_INVALID")
    path = payload["artifact_path"]
    pure = PurePosixPath(path)
    if (not path.startswith("docs/registry/ai-calibration/artifacts/") or
            pure.is_absolute() or "\\\\" in path or
            any(part in {"", ".", ".."} for part in path.split("/"))):
        _fail("ARTIFACT_PATH_OUTSIDE_REGISTRY")
    parsed_times = {}
    for name in ("training_cutoff", "calibration_start", "calibration_end", "created_at"):
        value = payload[name]
        if _TIMESTAMP.fullmatch(value) is None:
            _fail("MANIFEST_TIMESTAMP_INVALID:" + name)
        try:
            parsed_times[name] = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            _fail("MANIFEST_TIMESTAMP_INVALID:" + name)
    horizon_ms = horizon * {"ms": 1, "s": 1_000, "m": 60_000, "h": 3_600_000}[
        payload["forecast_horizon_unit"]
    ]
    if parsed_times["calibration_start"] < parsed_times["training_cutoff"] + timedelta(
        milliseconds=horizon_ms
    ):
        _fail("CALIBRATION_WINDOW_NOT_OUT_OF_SAMPLE")
    if parsed_times["calibration_end"] < parsed_times["calibration_start"]:
        _fail("CALIBRATION_WINDOW_INVALID")
    if parsed_times["created_at"] < parsed_times["calibration_end"]:
        _fail("ARTIFACT_CREATED_BEFORE_CALIBRATION_END")
    return payload


def _validate_envelope(envelope, payload, manifest_bytes):
    if not isinstance(envelope, dict) or set(envelope) != ENVELOPE_FIELDS:
        _fail("SIGNATURE_ENVELOPE_SCHEMA_MISMATCH")
    for name, value in envelope.items():
        _require_string(value, "SIGNATURE_ENVELOPE_FIELD_INVALID:" + name)
    expected = {
        "envelope_schema": ENVELOPE_SCHEMA,
        "manifest_id": payload["manifest_id"],
        "manifest_schema": payload["manifest_schema"],
        "canonicalization_profile": CANONICALIZATION,
        "digest_algorithm": "SHA-256",
        "manifest_digest": _sha256(manifest_bytes),
        "manifest_size_bytes": str(len(manifest_bytes)),
        "signature_algorithm": SIGNATURE_ALGORITHM,
        "signer_role": "CALIBRATION_SIGNER",
        "namespace": payload["registry_namespace"],
    }
    for name, value in expected.items():
        if envelope[name] != value:
            _fail("SIGNATURE_ENVELOPE_BINDING_MISMATCH:" + name)
    if _IDENTIFIER.fullmatch(envelope["envelope_id"]) is None or _IDENTIFIER.fullmatch(
        envelope["key_id"]
    ) is None:
        _fail("SIGNATURE_ENVELOPE_IDENTIFIER_INVALID")
    try:
        signature = base64.b64decode(envelope["signature_base64"], validate=True)
    except (binascii.Error, ValueError):
        _fail("SIGNATURE_ENCODING_INVALID")
    if len(signature) != 64:
        _fail("SIGNATURE_LENGTH_INVALID")
    return signature


def _validate_trust(trust, envelope, payload):
    if not isinstance(trust, dict) or set(trust) != TRUST_FIELDS:
        _fail("TRUST_CONFIGURATION_SCHEMA_MISMATCH")
    for name in ("key_id", "algorithm", "public_key_base64", "public_key_fingerprint",
                 "signer_role", "registry_namespace", "publisher_id"):
        _require_string(trust[name], "TRUST_CONFIGURATION_INVALID:" + name)
    if trust["key_id"] != envelope["key_id"]:
        _fail("KEY_ID_NOT_PINNED")
    if trust["algorithm"] != SIGNATURE_ALGORITHM:
        _fail("TRUST_ALGORITHM_UNSUPPORTED")
    if trust["signer_role"] != envelope["signer_role"] or trust[
        "registry_namespace"
    ] != payload["registry_namespace"] or trust["registry_namespace"] != envelope["namespace"] or trust[
        "publisher_id"
    ] != payload["publisher_id"]:
        _fail("KEY_SCOPE_MISMATCH")
    allowed = trust["allowed_record_types"]
    if not isinstance(allowed, list) or not all(isinstance(x, str) for x in allowed):
        _fail("TRUST_RECORD_SCOPE_INVALID")
    if payload["record_type"] not in allowed:
        _fail("KEY_RECORD_TYPE_NOT_AUTHORIZED")
    try:
        public_bytes = base64.b64decode(trust["public_key_base64"], validate=True)
    except (binascii.Error, ValueError):
        _fail("PUBLIC_KEY_ENCODING_INVALID")
    if len(public_bytes) != 32:
        _fail("PUBLIC_KEY_LENGTH_INVALID")
    if _DIGEST.fullmatch(trust["public_key_fingerprint"]) is None or _sha256(
        public_bytes
    ) != trust["public_key_fingerprint"]:
        _fail("PUBLIC_KEY_PIN_MISMATCH")
    try:
        public_key = Ed25519PublicKey.from_public_bytes(public_bytes)
    except ValueError:
        _fail("PUBLIC_KEY_INVALID")
    return public_key


def signature_message(statement):
    """Return the versioned, purpose-separated Ed25519 message bytes."""
    if not isinstance(statement, dict):
        _fail("SIGNATURE_STATEMENT_INVALID")
    try:
        canonical_statement = rfc8785.dumps(statement)
    except Exception:
        _fail("SIGNATURE_STATEMENT_INVALID")
    return SIGNATURE_DOMAIN + canonical_statement


def verify_calibration_manifest(manifest_bytes, signature_envelope, artifact_bytes, trust_config):
    """Verify manifest JCS bytes, detached Ed25519 signature and exact artifact bytes.

    A successful result is signature/integrity evidence only. It does not prove
    publisher promotion, current registry state, trusted time, OOS quality or
    AI trade admission.
    """
    payload = _validate_manifest(_canonical_manifest(manifest_bytes))
    if not isinstance(artifact_bytes, bytes):
        _fail("INVALID_ARTIFACT_BYTES")
    if len(artifact_bytes) != int(payload["artifact_size_bytes"]):
        _fail("ARTIFACT_SIZE_MISMATCH")
    if _sha256(artifact_bytes) != payload["artifact_digest"]:
        _fail("ARTIFACT_DIGEST_MISMATCH")
    signature = _validate_envelope(signature_envelope, payload, manifest_bytes)
    public_key = _validate_trust(trust_config, signature_envelope, payload)
    statement = {
        "domain": "BTCUSDT-AI-CALIBRATION-MANIFEST-SIGNATURE-V1",
        "namespace": payload["registry_namespace"],
        "manifest_id": payload["manifest_id"],
        "manifest_schema": payload["manifest_schema"],
        "canonicalization_profile": CANONICALIZATION,
        "digest_algorithm": "SHA-256",
        "manifest_digest": _sha256(manifest_bytes),
        "manifest_size_bytes": str(len(manifest_bytes)),
        "key_id": signature_envelope["key_id"],
        "signer_role": signature_envelope["signer_role"],
        "publisher_id": payload["publisher_id"],
    }
    try:
        public_key.verify(signature, signature_message(statement))
    except InvalidSignature:
        _fail("INVALID_ED25519_SIGNATURE")
    return {
        "verification_status": "SIGNATURE_VERIFIED_ONLY",
        "manifest_id": payload["manifest_id"],
        "manifest_digest": _sha256(manifest_bytes),
        "artifact_digest": payload["artifact_digest"],
        "artifact_size_bytes": payload["artifact_size_bytes"],
        "key_id": signature_envelope["key_id"],
        "signer_role": signature_envelope["signer_role"],
        "registry_namespace": payload["registry_namespace"],
    }


_TRANSFORM_FIELDS = frozenset({
    "artifact_schema", "transform_schema", "calibration_method", "method_version",
    "input_semantics", "output_semantics", "label_definition_id",
    "forecast_horizon_value", "forecast_horizon_unit", "knots",
})
_DECIMAL = re.compile(r"(?:0|[1-9][0-9]*)(?:\.[0-9]+)?\Z")


def _canonical_transform(artifact_bytes):
    if not isinstance(artifact_bytes, bytes) or not artifact_bytes:
        _fail("INVALID_ARTIFACT_BYTES")
    try:
        decoded = artifact_bytes.decode("utf-8", errors="strict")
        if decoded.startswith("\\ufeff"):
            _fail("ARTIFACT_BOM_NOT_ALLOWED")
        transform = json.loads(
            decoded,
            object_pairs_hook=_unique_object,
            parse_int=_reject_number,
            parse_float=_reject_number,
            parse_constant=_reject_constant,
        )
        canonical_bytes = rfc8785.dumps(transform)
    except CalibrationVerificationError:
        raise
    except Exception:
        _fail("INVALID_CALIBRATION_TRANSFORM_JSON")
    if not isinstance(transform, dict) or canonical_bytes != artifact_bytes:
        _fail("NONCANONICAL_CALIBRATION_TRANSFORM")
    if set(transform) != _TRANSFORM_FIELDS:
        _fail("CALIBRATION_TRANSFORM_SCHEMA_MISMATCH")
    for name in _TRANSFORM_FIELDS - {"knots"}:
        if not isinstance(transform[name], str) or not transform[name]:
            _fail("CALIBRATION_TRANSFORM_FIELD_INVALID:" + name)
    if transform["artifact_schema"] != "ai-calibration-transform/v1" or transform[
        "transform_schema"
    ] != "score-probability-map/v1":
        _fail("CALIBRATION_TRANSFORM_SCHEMA_UNSUPPORTED")
    if transform["input_semantics"] != "absolute_predicted_return" or transform[
        "output_semantics"
    ] != "direction_correct_probability":
        _fail("CALIBRATION_TRANSFORM_SEMANTICS_MISMATCH")
    if transform["forecast_horizon_unit"] not in {"ms", "s", "m", "h"}:
        _fail("CALIBRATION_TRANSFORM_HORIZON_INVALID")
    if _UNSIGNED.fullmatch(transform["forecast_horizon_value"]) is None:
        _fail("CALIBRATION_TRANSFORM_HORIZON_INVALID")
    knots = transform["knots"]
    if not isinstance(knots, list) or len(knots) < 2 or len(knots) > 4096:
        _fail("CALIBRATION_TRANSFORM_KNOTS_INVALID")
    parsed = []
    previous_score = None
    previous_probability = None
    for knot in knots:
        if not isinstance(knot, dict) or set(knot) != {"score", "probability"}:
            _fail("CALIBRATION_TRANSFORM_KNOT_INVALID")
        values = []
        for name in ("score", "probability"):
            raw = knot[name]
            if not isinstance(raw, str) or _DECIMAL.fullmatch(raw) is None:
                _fail("CALIBRATION_TRANSFORM_DECIMAL_INVALID")
            try:
                values.append(Decimal(raw))
            except InvalidOperation:
                _fail("CALIBRATION_TRANSFORM_DECIMAL_INVALID")
        score, probability = values
        if not Decimal("0") <= probability <= Decimal("1"):
            _fail("CALIBRATION_TRANSFORM_PROBABILITY_INVALID")
        if previous_score is not None and score <= previous_score:
            _fail("CALIBRATION_TRANSFORM_SCORE_NOT_STRICTLY_INCREASING")
        if previous_probability is not None and probability < previous_probability:
            _fail("CALIBRATION_TRANSFORM_NOT_MONOTONIC")
        parsed.append((score, probability))
        previous_score, previous_probability = score, probability
    return transform, parsed


def _decimal_text(value):
    text = format(value.normalize(), "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


def apply_calibration_transform(artifact_bytes, raw_score):
    """Apply a verified-format monotone score/probability map without extrapolation."""
    transform, knots = _canonical_transform(artifact_bytes)
    if not isinstance(raw_score, str) or _DECIMAL.fullmatch(raw_score) is None:
        _fail("RAW_DIRECTION_SCORE_INVALID")
    score = Decimal(raw_score)
    if score < knots[0][0] or score > knots[-1][0]:
        _fail("RAW_DIRECTION_SCORE_OUTSIDE_CALIBRATION_RANGE")
    for knot_score, probability in knots:
        if score == knot_score:
            return _decimal_text(probability)
    for (left_score, left_probability), (right_score, right_probability) in zip(knots, knots[1:]):
        if left_score < score < right_score:
            with localcontext() as context:
                context.prec = 40
                value = left_probability + (score-left_score) * (
                    right_probability-left_probability
                ) / (right_score-left_score)
            return _decimal_text(value)
    _fail("RAW_DIRECTION_SCORE_NOT_CALIBRATABLE")


def calibrate_verified_prediction(
    manifest_bytes, signature_envelope, artifact_bytes, trust_config, raw_direction_score
):
    """Verify the signed bundle and derive per-inference confidence from its exact transform."""
    verification = verify_calibration_manifest(
        manifest_bytes, signature_envelope, artifact_bytes, trust_config
    )
    manifest = _validate_manifest(_canonical_manifest(manifest_bytes))
    transform, _ = _canonical_transform(artifact_bytes)
    if transform["transform_schema"] != manifest["transform_schema"] or transform[
        "calibration_method"
    ] != manifest["calibration_method"] or transform["method_version"] != manifest[
        "method_version"
    ]:
        _fail("CALIBRATION_TRANSFORM_MANIFEST_MISMATCH")
    if transform["label_definition_id"] != manifest["label_definition_id"] or transform[
        "forecast_horizon_value"
    ] != manifest["forecast_horizon_value"] or transform[
        "forecast_horizon_unit"
    ] != manifest["forecast_horizon_unit"]:
        _fail("CALIBRATION_TRANSFORM_LABEL_HORIZON_MISMATCH")
    horizon_ms = int(manifest["forecast_horizon_value"]) * {
        "ms": 1, "s": 1_000, "m": 60_000, "h": 3_600_000
    }[manifest["forecast_horizon_unit"]]

    def epoch_ms(value):
        parsed = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=timezone.utc
        )
        delta = parsed - datetime(1970, 1, 1, tzinfo=timezone.utc)
        return delta.days * 86_400_000 + delta.seconds * 1_000 + delta.microseconds // 1_000

    confidence = apply_calibration_transform(artifact_bytes, raw_direction_score)
    return {
        "verificationStatus": verification["verification_status"],
        "manifestId": manifest["manifest_id"],
        "manifestDigest": verification["manifest_digest"],
        "calibrationVersion": manifest["calibration_version"],
        "calibrationMethod": manifest["calibration_method"],
        "calibrationArtifactHash": verification["artifact_digest"],
        "calibrationDatasetVersion": manifest["calibration_dataset_digest"],
        "calibrationSampleCount": int(manifest["sample_count"]),
        "calibrationStartMs": epoch_ms(manifest["calibration_start"]),
        "calibrationEndMs": epoch_ms(manifest["calibration_end"]),
        "calibratedAtMs": epoch_ms(manifest["created_at"]),
        "modelVersion": manifest["model_version"],
        "strategyVersion": manifest["strategy_version"],
        "trainingDatasetVersion": manifest["training_dataset_digest"],
        "labelDefinition": manifest["label_definition_id"],
        "forecastHorizonMs": horizon_ms,
        "calibratedConfidence": confidence,
        "registryNamespace": manifest["registry_namespace"],
        "publisherId": manifest["publisher_id"],
    }
