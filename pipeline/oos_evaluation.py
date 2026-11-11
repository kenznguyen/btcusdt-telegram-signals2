"""Pure offline structural validator for OOS Evaluation Evidence v1.

Validates canonical bytes, frozen F1-F3 schema, manifest binding, and locally
checkable F4 declarations. It cannot verify authoritative lineage, sample-level
embargo, reproducibility, trusted time, statistical acceptability, or admission.
"""
from datetime import datetime
from decimal import Decimal, InvalidOperation
import hashlib
import json
import re

import rfc8785

SCHEMA = "ai-calibration-oos-evaluation/v1"
EVALUATION_KIND = "OUT_OF_SAMPLE_CALIBRATION_EVALUATION"
METRIC_SCHEMA = "ai-calibration-metric-set/v1"
UNCERTAINTY_SCHEMA = "ai-calibration-uncertainty/v1"

TOP_LEVEL_FIELDS = frozenset("""
schema evaluation_id evaluation_kind model_id model_version
model_artifact_digest strategy_id strategy_version strategy_source_commit
training_dataset_id training_dataset_digest training_cutoff
calibration_dataset_id calibration_dataset_digest calibration_start calibration_end
evaluation_dataset_id evaluation_dataset_digest label_definition_id
label_definition_digest forecast_horizon_value forecast_horizon_unit
split_protocol_id split_protocol_version evaluation_start evaluation_end
eligible_sample_count excluded_sample_count exclusion_summary_digest metrics
uncertainty reliability_bins_digest baseline_definition_id baseline_metrics
evaluation_code_commit evaluation_code_digest environment_lock_digest
reproduction_command_id created_at
""".split())
METRIC_SET_FIELDS = frozenset({"schema", "items"})
METRIC_FIELDS = frozenset({"metric_id", "value", "unit", "direction", "aggregation", "sample_count"})
UNCERTAINTY_FIELDS = frozenset({"schema", "method", "resampling_unit", "interval_level", "seed_derivation", "items"})
UNCERTAINTY_ITEM_FIELDS = frozenset({"metric_id", "lower", "upper", "estimate"})

_DIGEST = re.compile(r"sha256:[0-9a-f]{64}\Z")
_IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:/-]{0,127}\Z")
_COMMIT = re.compile(r"[0-9a-f]{40}\Z")
_UNSIGNED = re.compile(r"(?:0|[1-9][0-9]*)\Z")
_TIMESTAMP = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z\Z")
# Canonical non-exponent decimal representation; this is not a metric policy.
_DECIMAL = re.compile(r"(?:0|-?(?:0\.[0-9]*[1-9]|[1-9][0-9]*(?:\.[0-9]*[1-9])?))\Z")
_DIRECTIONS = frozenset({"LOWER_IS_BETTER", "HIGHER_IS_BETTER", "DESCRIPTIVE_ONLY"})
_UINT64_MAX = 18_446_744_073_709_551_615


class OosEvidenceValidationError(ValueError):
    """An OOS record failed a deterministic structural validation check."""


def _fail(code):
    raise OosEvidenceValidationError(code)


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


def _identifier(value, field):
    if not isinstance(value, str) or _IDENTIFIER.fullmatch(value) is None:
        _fail("IDENTIFIER_INVALID:" + field)


def _digest(value, field):
    if not isinstance(value, str) or _DIGEST.fullmatch(value) is None:
        _fail("DIGEST_INVALID:" + field)


def _uint(value, field, positive=False):
    if not isinstance(value, str) or len(value) > 20 or _UNSIGNED.fullmatch(value) is None:
        _fail("UINT64_STRING_INVALID:" + field)
    parsed = int(value)
    if parsed > _UINT64_MAX or (positive and parsed == 0):
        _fail("UINT64_RANGE_INVALID:" + field)
    return parsed


def _decimal(value, field):
    if not isinstance(value, str) or _DECIMAL.fullmatch(value) is None:
        _fail("DECIMAL_STRING_INVALID:" + field)
    try:
        parsed = Decimal(value)
    except InvalidOperation:
        _fail("DECIMAL_STRING_INVALID:" + field)
    if not parsed.is_finite():
        _fail("DECIMAL_NOT_FINITE:" + field)
    return parsed


def _timestamp(value, field):
    if not isinstance(value, str) or _TIMESTAMP.fullmatch(value) is None:
        _fail("TIMESTAMP_INVALID:" + field)
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        _fail("TIMESTAMP_INVALID:" + field)


def _exact_fields(value, expected, code):
    if not isinstance(value, dict) or set(value) != expected:
        _fail(code)


def _metric_set(value, field):
    _exact_fields(value, METRIC_SET_FIELDS, "METRIC_SET_SCHEMA_MISMATCH:" + field)
    if value["schema"] != METRIC_SCHEMA:
        _fail("METRIC_SET_SCHEMA_UNSUPPORTED:" + field)
    items = value["items"]
    if not isinstance(items, list) or not items:
        _fail("METRIC_SET_ITEMS_INVALID:" + field)
    indexed = {}
    for item in items:
        _exact_fields(item, METRIC_FIELDS, "METRIC_FIELDS_MISMATCH:" + field)
        _identifier(item["metric_id"], "metric_id")
        _identifier(item["unit"], "metric_unit")
        _identifier(item["aggregation"], "metric_aggregation")
        if not isinstance(item["direction"], str) or item["direction"] not in _DIRECTIONS:
            _fail("METRIC_DIRECTION_INVALID")
        metric_value = _decimal(item["value"], "metric_value")
        sample_count = _uint(item["sample_count"], "metric_sample_count", positive=True)
        if item["metric_id"] in indexed:
            _fail("METRIC_ID_DUPLICATE:" + item["metric_id"])
        indexed[item["metric_id"]] = {
            "unit": item["unit"], "direction": item["direction"],
            "aggregation": item["aggregation"], "sample_count": sample_count,
            "value": metric_value,
        }
    return indexed


def _validate_uncertainty(value, metrics):
    _exact_fields(value, UNCERTAINTY_FIELDS, "UNCERTAINTY_FIELDS_MISMATCH")
    if value["schema"] != UNCERTAINTY_SCHEMA:
        _fail("UNCERTAINTY_SCHEMA_UNSUPPORTED")
    for field in ("method", "resampling_unit", "seed_derivation"):
        _identifier(value[field], "uncertainty_" + field)
    interval_level = _decimal(value["interval_level"], "interval_level")
    if not Decimal(0) < interval_level < Decimal(1):
        _fail("UNCERTAINTY_INTERVAL_LEVEL_OUT_OF_RANGE")
    items = value["items"]
    if not isinstance(items, list) or not items:
        _fail("UNCERTAINTY_ITEMS_INVALID")
    seen = set()
    for item in items:
        _exact_fields(item, UNCERTAINTY_ITEM_FIELDS, "UNCERTAINTY_ITEM_FIELDS_MISMATCH")
        metric_id = item["metric_id"]
        _identifier(metric_id, "uncertainty_metric_id")
        if metric_id in seen or metric_id not in metrics:
            _fail("UNCERTAINTY_METRIC_REFERENCE_INVALID")
        seen.add(metric_id)
        lower = _decimal(item["lower"], "uncertainty_lower")
        upper = _decimal(item["upper"], "uncertainty_upper")
        estimate = _decimal(item["estimate"], "uncertainty_estimate")
        if not lower <= estimate <= upper:
            _fail("UNCERTAINTY_BOUNDS_INVALID")
        if estimate != metrics[metric_id]["value"]:
            _fail("UNCERTAINTY_ESTIMATE_METRIC_MISMATCH")
    if seen != set(metrics):
        _fail("UNCERTAINTY_METRIC_COVERAGE_MISMATCH")


def _validate_baseline(primary, baseline):
    if set(primary) != set(baseline):
        _fail("BASELINE_METRIC_IDS_MISMATCH")
    for metric_id, definition in primary.items():
        other = baseline[metric_id]
        for key in ("unit", "direction", "aggregation", "sample_count"):
            if definition[key] != other[key]:
                _fail("BASELINE_METRIC_DEFINITION_MISMATCH:" + metric_id)


def _parse_record(record_bytes):
    if not isinstance(record_bytes, bytes) or not record_bytes:
        _fail("INVALID_RECORD_BYTES")
    try:
        decoded = record_bytes.decode("utf-8", errors="strict")
        if decoded.startswith("\ufeff"):
            _fail("RECORD_BOM_NOT_ALLOWED")
        payload = json.loads(
            decoded, object_pairs_hook=_unique_object,
            parse_int=_reject_number, parse_float=_reject_number,
            parse_constant=_reject_constant,
        )
    except OosEvidenceValidationError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError):
        _fail("INVALID_RECORD_JSON")
    if not isinstance(payload, dict):
        _fail("INVALID_RECORD_ROOT")
    try:
        canonical = rfc8785.dumps(payload)
    except Exception:
        _fail("RECORD_CANONICALIZATION_FAILED")
    if canonical != record_bytes:
        _fail("NONCANONICAL_RECORD_BYTES")
    return payload


def validate_oos_evaluation_record(record_bytes, manifest_binding, candidate_population_count=None):
    """Validate frozen structure and local consistency; never assert OOS VERIFIED.

    manifest_binding is an independently obtained mapping containing
    evaluation_record_id and evaluation_record_digest. candidate_population_count
    is optional external arithmetic input, not authoritative lineage evidence.
    """
    payload = _parse_record(record_bytes)
    _exact_fields(payload, TOP_LEVEL_FIELDS, "TOP_LEVEL_FIELDS_MISMATCH")
    for field, value in payload.items():
        if field not in {"metrics", "baseline_metrics", "uncertainty"} and not isinstance(value, str):
            _fail("SCALAR_MUST_BE_STRING:" + field)

    if payload["schema"] != SCHEMA:
        _fail("SCHEMA_UNSUPPORTED")
    if payload["evaluation_kind"] != EVALUATION_KIND:
        _fail("EVALUATION_KIND_UNSUPPORTED")
    if not isinstance(manifest_binding, dict):
        _fail("MANIFEST_BINDING_REQUIRED")
    if payload["evaluation_id"] != manifest_binding.get("evaluation_record_id"):
        _fail("MANIFEST_EVALUATION_ID_MISMATCH")
    expected_digest = manifest_binding.get("evaluation_record_digest")
    _digest(expected_digest, "manifest_evaluation_record_digest")
    actual_digest = "sha256:" + hashlib.sha256(record_bytes).hexdigest()
    if actual_digest != expected_digest:
        _fail("MANIFEST_EVALUATION_DIGEST_MISMATCH")

    for field in (
        "evaluation_id", "model_id", "model_version", "strategy_id",
        "strategy_version", "training_dataset_id", "calibration_dataset_id",
        "evaluation_dataset_id", "label_definition_id", "forecast_horizon_unit",
        "split_protocol_id", "split_protocol_version", "baseline_definition_id",
        "reproduction_command_id",
    ):
        _identifier(payload[field], field)
    for field in (
        "model_artifact_digest", "training_dataset_digest",
        "calibration_dataset_digest", "evaluation_dataset_digest",
        "label_definition_digest", "exclusion_summary_digest",
        "reliability_bins_digest", "evaluation_code_digest",
        "environment_lock_digest",
    ):
        _digest(payload[field], field)
    for field in ("strategy_source_commit", "evaluation_code_commit"):
        if _COMMIT.fullmatch(payload[field]) is None:
            _fail("COMMIT_INVALID:" + field)

    eligible = _uint(payload["eligible_sample_count"], "eligible_sample_count", positive=True)
    excluded = _uint(payload["excluded_sample_count"], "excluded_sample_count")
    _uint(payload["forecast_horizon_value"], "forecast_horizon_value", positive=True)

    training_cutoff = _timestamp(payload["training_cutoff"], "training_cutoff")
    calibration_start = _timestamp(payload["calibration_start"], "calibration_start")
    calibration_end = _timestamp(payload["calibration_end"], "calibration_end")
    evaluation_start = _timestamp(payload["evaluation_start"], "evaluation_start")
    evaluation_end = _timestamp(payload["evaluation_end"], "evaluation_end")
    _timestamp(payload["created_at"], "created_at")
    if not training_cutoff < calibration_start <= calibration_end < evaluation_start <= evaluation_end:
        _fail("PARTITION_TIME_ORDER_INVALID")

    dataset_ids = (
        payload["training_dataset_id"], payload["calibration_dataset_id"],
        payload["evaluation_dataset_id"],
    )
    dataset_digests = (
        payload["training_dataset_digest"], payload["calibration_dataset_digest"],
        payload["evaluation_dataset_digest"],
    )
    if len(set(dataset_ids)) != 3 or len(set(dataset_digests)) != 3:
        _fail("DATASET_PARTITIONS_NOT_DISTINCT")

    if candidate_population_count is not None:
        if isinstance(candidate_population_count, bool) or not isinstance(candidate_population_count, int):
            _fail("CANDIDATE_POPULATION_COUNT_INVALID")
        if candidate_population_count < 0 or eligible + excluded != candidate_population_count:
            _fail("CANDIDATE_POPULATION_COUNT_MISMATCH")

    primary = _metric_set(payload["metrics"], "metrics")
    baseline = _metric_set(payload["baseline_metrics"], "baseline_metrics")
    _validate_baseline(primary, baseline)
    _validate_uncertainty(payload["uncertainty"], primary)

    return {
        "record_status": "STRUCTURE_VALID",
        "manifest_binding_status": "MATCHED",
        "partition_declaration_status": "LOCALLY_CONSISTENT",
        "lineage_status": "NOT_VERIFIED",
        "sample_identity_status": "NOT_VERIFIED",
        "horizon_embargo_status": "NOT_VERIFIED",
        "reproducibility_status": "NOT_VERIFIED",
        "statistical_policy_status": "NOT_EVALUATED",
        "oos_evidence_status": "NOT_VERIFIED",
        "ai_admission_eligible": False,
        "record_digest": actual_digest,
    }
