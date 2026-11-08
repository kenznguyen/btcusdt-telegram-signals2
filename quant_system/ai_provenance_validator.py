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
from decimal import Decimal, InvalidOperation
from collections.abc import Mapping

from quant_system.ai_calibration_evaluator import (
    CalibrationEvaluator,
    CalibrationGatePolicy,
    CalibrationObservation,
)

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


def _validate_prediction_rows(predictions, manifest):
    """Validate row-level prediction timestamps and model/dataset identity."""
    if not isinstance(predictions, bytes) or not predictions:
        return ("PREDICTIONS_EMPTY",)

    split = manifest.get("temporal_split")
    if (not isinstance(split, Mapping)
            or set(split) != _REQUIRED_SPLIT_KEYS):
        return ("TEMPORAL_SPLIT_INVALID",)
    start_ms, end_ms = split["oos_start_ms"], split["oos_end_ms"]
    if (type(start_ms) is not int or type(end_ms) is not int
            or start_ms <= 0 or end_ms < start_ms):
        return ("TEMPORAL_SPLIT_INVALID",)
    expected_model = manifest["model_version"]
    expected_dataset = manifest["dataset_version"]
    required = {
        "prediction_timestamp_ms", "outcome_available_at_ms", "outcome",
        "confidence", "side", "regime", "model_version", "dataset_version",
    }
    try:
        text = predictions.decode("utf-8")
    except UnicodeDecodeError:
        return ("PREDICTION_ROW_INVALID",)

    lines = text.splitlines()
    if not lines:
        return ("PREDICTIONS_EMPTY",)
    if any(not line.strip() for line in lines):
        return ("PREDICTION_ROW_INVALID",)

    reasons = []
    for line in lines:
        try:
            row = json.loads(
                line,
                object_pairs_hook=_reject_duplicate_keys,
                parse_constant=lambda _value: (_ for _ in ()).throw(ValueError("non-finite JSON")),
            )
        except (json.JSONDecodeError, TypeError, ValueError):
            reasons.append("PREDICTION_ROW_INVALID")
            continue

        if not isinstance(row, Mapping) or set(row) != required:
            reasons.append("PREDICTION_ROW_INVALID")
            continue

        prediction_ms = row.get("prediction_timestamp_ms")
        outcome_ms = row.get("outcome_available_at_ms")
        if type(prediction_ms) is not int or not start_ms <= prediction_ms <= end_ms:
            reasons.append("PREDICTION_TIMESTAMP_OUTSIDE_OOS")
        if (type(outcome_ms) is not int or type(prediction_ms) is not int
                or outcome_ms <= prediction_ms or outcome_ms > end_ms):
            reasons.append("OUTCOME_TIMESTAMP_INVALID")

        if row.get("model_version") != expected_model:
            reasons.append("PREDICTION_MODEL_VERSION_MISMATCH")
        if row.get("dataset_version") != expected_dataset:
            reasons.append("PREDICTION_DATASET_VERSION_MISMATCH")

        if (type(row.get("outcome")) is not int or row["outcome"] not in (0, 1)
                or row.get("side") not in ("LONG", "SHORT")
                or not isinstance(row.get("regime"), str) or not row["regime"].strip()):
            reasons.append("PREDICTION_ROW_INVALID")
        try:
            confidence = Decimal(str(row.get("confidence")))
            if (isinstance(row.get("confidence"), bool) or not confidence.is_finite()
                    or confidence < 0 or confidence > 1):
                raise ValueError("invalid confidence")
        except (InvalidOperation, TypeError, ValueError):
            reasons.append("PREDICTION_ROW_INVALID")

    return tuple(sorted(set(reasons)))


def _validate_calibration_report(predictions, report_bytes, manifest):
    """Recompute calibration metrics and both evaluator fingerprints from signed rows."""
    if not isinstance(report_bytes, bytes) or not report_bytes:
        return ("CALIBRATION_REPORT_INVALID",)
    try:
        report = json.loads(
            report_bytes.decode("utf-8"),
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=lambda _value: (_ for _ in ()).throw(ValueError("non-finite JSON")),
        )
    except (UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError):
        return ("CALIBRATION_REPORT_INVALID",)

    required_report_keys = {
        "schema_version", "policy", "accepted", "reasons", "sample_count",
        "group_count", "metrics", "input_sha256", "report_sha256",
        "trade_authorized", "attestation_issued",
    }
    if not isinstance(report, Mapping) or set(report) != required_report_keys:
        return ("CALIBRATION_REPORT_INVALID",)
    if type(report.get("schema_version")) is not int or report["schema_version"] != 1:
        return ("CALIBRATION_REPORT_INVALID",)

    policy_payload = report.get("policy")
    policy_keys = {
        "max_ece", "min_total_samples", "min_group_samples",
        "ece_bins", "required_regimes",
    }
    if not isinstance(policy_payload, Mapping) or set(policy_payload) != policy_keys:
        return ("CALIBRATION_REPORT_INVALID",)
    try:
        max_ece = Decimal(str(policy_payload["max_ece"]))
        regimes = policy_payload["required_regimes"]
        if (not max_ece.is_finite() or max_ece != Decimal("0.05")
                or type(policy_payload["min_total_samples"]) is not int
                or policy_payload["min_total_samples"] != 1000
                or type(policy_payload["min_group_samples"]) is not int
                or policy_payload["min_group_samples"] != 200
                or type(policy_payload["ece_bins"]) is not int
                or not 1 <= policy_payload["ece_bins"] <= 100
                or not isinstance(regimes, list) or not regimes
                or any(not isinstance(item, str) or not item.strip() for item in regimes)
                or len(set(regimes)) != len(regimes)):
            return ("CALIBRATION_POLICY_NOT_APPROVED",)
    except (InvalidOperation, TypeError, ValueError):
        return ("CALIBRATION_POLICY_NOT_APPROVED",)

    try:
        rows_text = predictions.decode("utf-8")
        lines = rows_text.splitlines()
        if not lines or any(not line.strip() for line in lines):
            return ("CALIBRATION_INPUT_INVALID",)
        observations = []
        split = manifest.get("temporal_split")
        if not isinstance(split, Mapping) or set(split) != _REQUIRED_SPLIT_KEYS:
            return ("TEMPORAL_SPLIT_INVALID",)
        start_ms, end_ms = split["oos_start_ms"], split["oos_end_ms"]
        if type(start_ms) is not int or type(end_ms) is not int:
            return ("TEMPORAL_SPLIT_INVALID",)
        for line in lines:
            row = json.loads(
                line,
                object_pairs_hook=_reject_duplicate_keys,
                parse_constant=lambda _value: (_ for _ in ()).throw(ValueError("non-finite JSON")),
            )
            if not isinstance(row, Mapping):
                return ("CALIBRATION_INPUT_INVALID",)
            prediction_ms = row.get("prediction_timestamp_ms")
            outcome_ms = row.get("outcome_available_at_ms")
            if (type(prediction_ms) is not int or not start_ms <= prediction_ms <= end_ms
                    or type(outcome_ms) is not int or outcome_ms <= prediction_ms
                    or outcome_ms > end_ms):
                return ("CALIBRATION_INPUT_INVALID",)
            if (row.get("model_version") != manifest.get("model_version")
                    or row.get("dataset_version") != manifest.get("dataset_version")):
                return ("CALIBRATION_INPUT_INVALID",)
            observations.append(CalibrationObservation(
                outcome=row.get("outcome"),
                confidence=row.get("confidence"),
                side=row.get("side"),
                regime=row.get("regime"),
                out_of_sample=True,
            ))
    except (UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError):
        return ("CALIBRATION_INPUT_INVALID",)

    policy = CalibrationGatePolicy(
        max_ece=policy_payload["max_ece"],
        min_total_samples=policy_payload["min_total_samples"],
        min_group_samples=policy_payload["min_group_samples"],
        ece_bins=policy_payload["ece_bins"],
        required_regimes=tuple(regimes),
    )
    evaluation = CalibrationEvaluator().evaluate(observations, policy)
    expected = {
        "schema_version": 1,
        "policy": {
            "max_ece": format(max_ece, "f"),
            "min_total_samples": policy.min_total_samples,
            "min_group_samples": policy.min_group_samples,
            "ece_bins": policy.ece_bins,
            "required_regimes": list(policy.required_regimes),
        },
        "accepted": evaluation.accepted,
        "reasons": list(evaluation.reasons),
        "sample_count": evaluation.sample_count,
        "group_count": evaluation.group_count,
        "metrics": evaluation.metrics,
        "input_sha256": evaluation.input_sha256,
        "report_sha256": evaluation.report_sha256,
        "trade_authorized": False,
        "attestation_issued": False,
    }
    if report != expected or not evaluation.accepted:
        return ("CALIBRATION_REPORT_MISMATCH",)
    return ()


def verify_signed_provenance(envelope, artifacts, trusted_public_keys, *, now_ms):
    """Verify signature, trusted key, exact artifact bytes and OOS chronology.

    trusted_public_keys maps key IDs to raw 32-byte Ed25519 public keys. The
    caller must load this mapping from an independently protected trust store.
    A passing result is provenance verification only, not trade authorization.
    """
    reasons = []
    verified = []
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
    if not isinstance(artifacts, Mapping):
        reasons.append("ARTIFACT_ROLE_SET_MISMATCH")
    else:
        if set(artifacts) != _REQUIRED_ARTIFACT_ROLES:
            reasons.append("ARTIFACT_ROLE_SET_MISMATCH")
        if isinstance(manifest_artifacts, Mapping):
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

    if isinstance(artifacts, Mapping) and "predictions" in artifacts:
        prediction_data = artifacts["predictions"]
        reasons.extend(_validate_prediction_rows(prediction_data, manifest))
        if "calibration_report" in artifacts:
            reasons.extend(_validate_calibration_report(
                prediction_data, artifacts["calibration_report"], manifest
            ))

    return ProvenanceVerification(
        accepted=not reasons, reasons=tuple(sorted(set(reasons))), key_id=key_id,
        manifest_sha256=manifest_sha256, verified_artifacts=tuple(verified),
        attestation_issued=False,
    )