"""Independent contract tests for AI dynamic leverage calibration and bounds."""

from dataclasses import replace
from decimal import Decimal
import unittest

from quant_system.ai_dynamic_leverage import (
    AIDynamicLeveragePolicy,
    CalibrationAttestation,
)


class AIDynamicLeveragePolicyTests(unittest.TestCase):
    def setUp(self):
        self.policy = AIDynamicLeveragePolicy(
            min_leverage="1", max_leverage="3",
            confidence_floor="0.60", confidence_ceiling="0.90",
        )
        self.attestation = CalibrationAttestation(
            model_version="ai-model-v1",
            strategy_version="ai-strategy-v1",
            dataset_version="sha256:" + "a" * 64,
            report_sha256="b" * 64,
            protocol_sha256="c" * 64,
            validated_at_ms=1_800_000_000_000,
            expires_at_ms=1_800_086_400_000,
            out_of_sample=True,
            leakage_free=True,
            acceptance_passed=True,
        )
        self.now_ms = 1_800_000_001_000

    def calculate(self, confidence="0.75", **overrides):
        return self.policy.calculate(
            confidence=confidence,
            calibration=overrides.pop("calibration", self.attestation),
            now_ms=overrides.pop("now_ms", self.now_ms),
            model_version=overrides.pop("model_version", "ai-model-v1"),
            strategy_version=overrides.pop("strategy_version", "ai-strategy-v1"),
            dataset_version=overrides.pop("dataset_version", "sha256:" + "a" * 64),
            **overrides,
        )

    def test_linear_mapping_floor_midpoint_and_ceiling(self):
        self.assertEqual(self.calculate("0.60").leverage, Decimal("1"))
        self.assertEqual(self.calculate("0.75").leverage, Decimal("2"))
        self.assertEqual(self.calculate("0.90").leverage, Decimal("3"))

    def test_rejects_confidence_below_or_above_configured_domain(self):
        for confidence in ("0.5999", "0.9001"):
            with self.subTest(confidence=confidence):
                self.assertEqual(self.calculate(confidence).reason, "CONFIDENCE_OUT_OF_DOMAIN")

    def test_rejects_non_finite_or_non_numeric_confidence(self):
        for confidence in ("NaN", "Infinity", "-Infinity", "invalid", True, None):
            with self.subTest(confidence=confidence):
                self.assertFalse(self.calculate(confidence).accepted)

    def test_rejects_missing_calibration(self):
        result = self.calculate(calibration=None)
        self.assertEqual(result.reason, "CALIBRATION_ATTESTATION_MISSING")

    def test_rejects_failed_calibration_acceptance(self):
        result = self.calculate(calibration=replace(self.attestation, acceptance_passed=False))
        self.assertEqual(result.reason, "CALIBRATION_NOT_ACCEPTED")

    def test_rejects_non_oos_or_leaky_calibration(self):
        for changes in ({"out_of_sample": False}, {"leakage_free": False}):
            with self.subTest(changes=changes):
                result = self.calculate(calibration=replace(self.attestation, **changes))
                self.assertFalse(result.accepted)

    def test_rejects_invalid_or_missing_provenance_hashes(self):
        for changes in (
            {"report_sha256": ""},
            {"report_sha256": "not-a-digest"},
            {"protocol_sha256": "0" * 63},
            {"dataset_version": "dataset-without-digest"},
        ):
            with self.subTest(changes=changes):
                result = self.calculate(calibration=replace(self.attestation, **changes))
                self.assertEqual(result.reason, "CALIBRATION_PROVENANCE_INVALID")

    def test_rejects_model_strategy_or_dataset_mismatch(self):
        for field, value in (
            ("model_version", "other-model"),
            ("strategy_version", "other-strategy"),
            ("dataset_version", "sha256:" + "d" * 64),
        ):
            with self.subTest(field=field):
                result = self.calculate(**{field: value})
                self.assertEqual(result.reason, "CALIBRATION_PROVENANCE_MISMATCH")

    def test_rejects_future_or_expired_attestation(self):
        future = replace(self.attestation, validated_at_ms=self.now_ms + 1)
        expired = replace(self.attestation, expires_at_ms=self.now_ms)
        self.assertEqual(self.calculate(calibration=future).reason, "CALIBRATION_TIME_INVALID")
        self.assertEqual(self.calculate(calibration=expired).reason, "CALIBRATION_EXPIRED")

    def test_rejects_malformed_time_and_attestation_types(self):
        malformed = replace(self.attestation, validated_at_ms=True)
        self.assertFalse(self.calculate(calibration=malformed).accepted)
        self.assertFalse(self.calculate(calibration=object()).accepted)

    def test_rejects_missing_or_invalid_policy_bounds(self):
        invalid = (
            {},
            {"min_leverage": "0", "max_leverage": "3", "confidence_floor": "0.6", "confidence_ceiling": "0.9"},
            {"min_leverage": "3", "max_leverage": "1", "confidence_floor": "0.6", "confidence_ceiling": "0.9"},
            {"min_leverage": "1", "max_leverage": "3", "confidence_floor": "0.9", "confidence_ceiling": "0.6"},
            {"min_leverage": "1", "max_leverage": "3", "confidence_floor": "0.6", "confidence_ceiling": "0.6"},
            {"min_leverage": "NaN", "max_leverage": "3", "confidence_floor": "0.6", "confidence_ceiling": "0.9"},
        )
        for config in invalid:
            with self.subTest(config=config):
                with self.assertRaises(ValueError):
                    AIDynamicLeveragePolicy(**config)

    def test_leverage_is_always_inside_explicit_bounds(self):
        for confidence in ("0.60", "0.61", "0.70", "0.80", "0.89", "0.90"):
            result = self.calculate(confidence)
            self.assertTrue(result.accepted)
            self.assertGreaterEqual(result.leverage, Decimal("1"))
            self.assertLessEqual(result.leverage, Decimal("3"))

    def test_result_carries_calibration_provenance(self):
        result = self.calculate("0.75")
        self.assertTrue(result.accepted)
        self.assertEqual(result.model_version, "ai-model-v1")
        self.assertEqual(result.report_sha256, "b" * 64)
        self.assertEqual(result.protocol_sha256, "c" * 64)

    def test_core_leverage_is_not_an_input_or_fallback(self):
        result = self.calculate("0.75")
        self.assertEqual(result.leverage, Decimal("2"))
        self.assertFalse(hasattr(result, "core_leverage"))


if __name__ == "__main__":
    unittest.main()
