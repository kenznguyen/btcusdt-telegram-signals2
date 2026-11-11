import copy
import hashlib
import unittest

import rfc8785

from pipeline.oos_evaluation import (
    OosEvidenceValidationError,
    validate_oos_evaluation_record,
)


def digest(value):
    return "sha256:" + hashlib.sha256(value).hexdigest()


def canonical(value):
    return rfc8785.dumps(value)


class OosEvaluationValidatorTest(unittest.TestCase):
    def setUp(self):
        metric = {
            "metric_id": "brier_score",
            "value": "0.2",
            "unit": "probability",
            "direction": "LOWER_IS_BETTER",
            "aggregation": "sample_mean",
            "sample_count": "100",
        }
        self.record = {
            "schema": "ai-calibration-oos-evaluation/v1",
            "evaluation_id": "oos-evaluation-test-001",
            "evaluation_kind": "OUT_OF_SAMPLE_CALIBRATION_EVALUATION",
            "model_id": "btc-model",
            "model_version": "model-v1",
            "model_artifact_digest": digest(b"model"),
            "strategy_id": "ai-strategy",
            "strategy_version": "strategy-v1",
            "strategy_source_commit": "a" * 40,
            "training_dataset_id": "training-data-v1",
            "training_dataset_digest": digest(b"training"),
            "training_cutoff": "2026-01-01T00:00:00Z",
            "calibration_dataset_id": "calibration-data-v1",
            "calibration_dataset_digest": digest(b"calibration"),
            "calibration_start": "2026-01-02T00:00:00Z",
            "calibration_end": "2026-01-03T00:00:00Z",
            "evaluation_dataset_id": "evaluation-data-v1",
            "evaluation_dataset_digest": digest(b"evaluation"),
            "label_definition_id": "direction-correct-v1",
            "label_definition_digest": digest(b"label"),
            "forecast_horizon_value": "900",
            "forecast_horizon_unit": "s",
            "split_protocol_id": "chronological-split",
            "split_protocol_version": "v1",
            "evaluation_start": "2026-01-04T00:00:00Z",
            "evaluation_end": "2026-01-05T00:00:00Z",
            "eligible_sample_count": "100",
            "excluded_sample_count": "5",
            "exclusion_summary_digest": digest(b"exclusions"),
            "metrics": {
                "schema": "ai-calibration-metric-set/v1",
                "items": [copy.deepcopy(metric)],
            },
            "uncertainty": {
                "schema": "ai-calibration-uncertainty/v1",
                "method": "bootstrap",
                "resampling_unit": "sample",
                "interval_level": "0.95",
                "seed_derivation": "fixed-test-seed-v1",
                "items": [{
                    "metric_id": "brier_score",
                    "lower": "0.1",
                    "upper": "0.3",
                    "estimate": "0.2",
                }],
            },
            "reliability_bins_digest": digest(b"reliability"),
            "baseline_definition_id": "constant-prevalence-baseline",
            "baseline_metrics": {
                "schema": "ai-calibration-metric-set/v1",
                "items": [copy.deepcopy(metric)],
            },
            "evaluation_code_commit": "b" * 40,
            "evaluation_code_digest": digest(b"evaluator"),
            "environment_lock_digest": digest(b"environment"),
            "reproduction_command_id": "reproduce-oos-v1",
            "created_at": "2026-01-06T00:00:00Z",
        }
        self.record_bytes = canonical(self.record)
        self.binding = {
            "evaluation_record_id": self.record["evaluation_id"],
            "evaluation_record_digest": digest(self.record_bytes),
        }

    def validate(self, record_bytes=None, binding=None, candidate_population_count=None):
        return validate_oos_evaluation_record(
            self.record_bytes if record_bytes is None else record_bytes,
            self.binding if binding is None else binding,
            candidate_population_count=candidate_population_count,
        )

    def assert_rejected(self, record=None, record_bytes=None, binding=None, reason=None):
        raw = record_bytes if record_bytes is not None else canonical(
            self.record if record is None else record
        )
        with self.assertRaises(OosEvidenceValidationError) as raised:
            self.validate(record_bytes=raw, binding=binding)
        if reason:
            self.assertEqual(str(raised.exception), reason)

    def test_valid_fixture_is_structural_only_and_never_admission_eligible(self):
        result = self.validate(candidate_population_count=105)
        self.assertEqual(result["record_status"], "STRUCTURE_VALID")
        self.assertEqual(result["manifest_binding_status"], "MATCHED")
        self.assertEqual(result["lineage_status"], "NOT_VERIFIED")
        self.assertEqual(result["horizon_embargo_status"], "NOT_VERIFIED")
        self.assertEqual(result["oos_evidence_status"], "NOT_VERIFIED")
        self.assertFalse(result["ai_admission_eligible"])

    def test_rejects_missing_or_unknown_top_level_fields(self):
        missing = copy.deepcopy(self.record)
        del missing["created_at"]
        self.assert_rejected(record=missing, reason="TOP_LEVEL_FIELDS_MISMATCH")
        unknown = copy.deepcopy(self.record)
        unknown["unapproved_field"] = "value"
        self.assert_rejected(record=unknown, reason="TOP_LEVEL_FIELDS_MISMATCH")

    def test_rejects_utf8_bom_invalid_utf8_and_duplicate_keys(self):
        self.assert_rejected(record_bytes=b"\xef\xbb\xbf" + self.record_bytes,
                             reason="RECORD_BOM_NOT_ALLOWED")
        self.assert_rejected(record_bytes=b"\xff", reason="INVALID_RECORD_JSON")
        duplicate = b'{"schema":"x","schema":"y"}'
        self.assert_rejected(record_bytes=duplicate, reason="DUPLICATE_JSON_KEY")

    def test_rejects_json_numbers_and_noncanonical_serialization(self):
        numeric = self.record_bytes.replace(b'"eligible_sample_count":"100"', b'"eligible_sample_count":100')
        self.assert_rejected(record_bytes=numeric, reason="JSON_NUMBER_NOT_ALLOWED")
        spaced = b" " + self.record_bytes
        self.assert_rejected(record_bytes=spaced, reason="NONCANONICAL_RECORD_BYTES")

    def test_rejects_manifest_evaluation_id_or_digest_mismatch(self):
        binding = dict(self.binding, evaluation_record_id="different-id")
        self.assert_rejected(binding=binding, reason="MANIFEST_EVALUATION_ID_MISMATCH")
        binding = dict(self.binding, evaluation_record_digest=digest(b"other"))
        self.assert_rejected(binding=binding, reason="MANIFEST_EVALUATION_DIGEST_MISMATCH")

    def test_rejects_duplicate_dataset_identity_or_digest(self):
        record = copy.deepcopy(self.record)
        record["evaluation_dataset_id"] = record["training_dataset_id"]
        self.assert_rejected(record=record, reason="DATASET_PARTITIONS_NOT_DISTINCT")
        record = copy.deepcopy(self.record)
        record["evaluation_dataset_digest"] = record["training_dataset_digest"]
        self.assert_rejected(record=record, reason="DATASET_PARTITIONS_NOT_DISTINCT")

    def test_rejects_invalid_partition_temporal_order(self):
        record = copy.deepcopy(self.record)
        record["evaluation_start"] = "2026-01-03T00:00:00Z"
        self.assert_rejected(record=record, reason="PARTITION_TIME_ORDER_INVALID")

    def test_rejects_noncanonical_or_out_of_range_counts(self):
        record = copy.deepcopy(self.record)
        record["eligible_sample_count"] = "01"
        self.assert_rejected(record=record, reason="UINT64_STRING_INVALID:eligible_sample_count")
        record = copy.deepcopy(self.record)
        record["eligible_sample_count"] = "0"
        self.assert_rejected(record=record, reason="UINT64_RANGE_INVALID:eligible_sample_count")

    def test_reconciles_candidate_population_only_when_external_count_is_supplied(self):
        with self.assertRaises(OosEvidenceValidationError) as raised:
            self.validate(candidate_population_count=104)
        self.assertEqual(str(raised.exception), "CANDIDATE_POPULATION_COUNT_MISMATCH")

    def test_rejects_invalid_metric_decimal_direction_and_duplicate_id(self):
        record = copy.deepcopy(self.record)
        record["metrics"]["items"][0]["value"] = "NaN"
        self.assert_rejected(record=record, reason="DECIMAL_STRING_INVALID:metric_value")
        record = copy.deepcopy(self.record)
        record["metrics"]["items"][0]["direction"] = "OPTIMIZE"
        self.assert_rejected(record=record, reason="METRIC_DIRECTION_INVALID")
        record = copy.deepcopy(self.record)
        record["metrics"]["items"].append(copy.deepcopy(record["metrics"]["items"][0]))
        self.assert_rejected(record=record, reason="METRIC_ID_DUPLICATE:brier_score")

    def test_rejects_incompatible_baseline_metric_definition(self):
        record = copy.deepcopy(self.record)
        record["baseline_metrics"]["items"][0]["sample_count"] = "99"
        self.assert_rejected(record=record, reason="BASELINE_METRIC_DEFINITION_MISMATCH:brier_score")

    def test_rejects_invalid_uncertainty_bounds_or_metric_estimate(self):
        record = copy.deepcopy(self.record)
        record["uncertainty"]["items"][0]["lower"] = "0.25"
        self.assert_rejected(record=record, reason="UNCERTAINTY_BOUNDS_INVALID")
        record = copy.deepcopy(self.record)
        record["uncertainty"]["items"][0]["estimate"] = "0.21"
        self.assert_rejected(record=record, reason="UNCERTAINTY_ESTIMATE_METRIC_MISMATCH")

    def test_rejects_non_string_scalar_and_invalid_commit_digest(self):
        record = copy.deepcopy(self.record)
        record["model_version"] = 1
        self.assert_rejected(record=record, reason="SCALAR_MUST_BE_STRING:model_version")
        record = copy.deepcopy(self.record)
        record["evaluation_code_commit"] = "z" * 40
        self.assert_rejected(record=record, reason="COMMIT_INVALID:evaluation_code_commit")


if __name__ == "__main__":
    unittest.main()
