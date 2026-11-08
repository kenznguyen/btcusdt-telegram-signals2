"""Independent OOS calibration evaluator contracts; all acceptance gates are explicit."""

import unittest

from quant_system.ai_calibration_evaluator import (
    CalibrationEvaluator,
    CalibrationGatePolicy,
    CalibrationObservation,
)


class CalibrationEvaluatorTests(unittest.TestCase):
    def setUp(self):
        self.policy = CalibrationGatePolicy(
            max_ece="0.20",
            min_total_samples=32,
            min_group_samples=8,
            ece_bins=4,
            required_regimes=("TREND", "RANGE"),
        )

    @staticmethod
    def calibrated_rows():
        return [(1, ".8")] * 3 + [(0, ".8"), (1, ".2")] + [(0, ".2")] * 3

    def observations(self, *, long_trend=None, long_range=None,
                     short_trend=None, short_range=None):
        groups = {
            ("LONG", "TREND"): long_trend or self.calibrated_rows(),
            ("LONG", "RANGE"): long_range or self.calibrated_rows(),
            ("SHORT", "TREND"): short_trend or self.calibrated_rows(),
            ("SHORT", "RANGE"): short_range or self.calibrated_rows(),
        }
        return [
            CalibrationObservation(
                outcome=outcome, confidence=confidence,
                side=side, regime=regime, out_of_sample=True,
            )
            for (side, regime), rows in groups.items()
            for outcome, confidence in rows
        ]

    def test_calibrated_oos_samples_pass_explicit_policy(self):
        report = CalibrationEvaluator().evaluate(self.observations(), self.policy)
        self.assertTrue(report.accepted)
        self.assertEqual(report.sample_count, 32)
        self.assertEqual(report.group_count, 4)
        self.assertEqual(report.metrics["overall"]["ece"], 0.05)
        self.assertEqual(report.metrics["overall"]["brier_score"], 0.19)

    def test_rejects_insufficient_total_oos_samples(self):
        rows = self.observations()[:31]
        report = CalibrationEvaluator().evaluate(rows, self.policy)
        self.assertFalse(report.accepted)
        self.assertIn("TOTAL_SAMPLE_COUNT_BELOW_MINIMUM", report.reasons)

    def test_rejects_missing_directional_regime_group(self):
        rows = [x for x in self.observations() if not (x.side == "SHORT" and x.regime == "RANGE")]
        report = CalibrationEvaluator().evaluate(rows, self.policy)
        self.assertFalse(report.accepted)
        self.assertIn("GROUP_MISSING:SHORT:RANGE", report.reasons)

    def test_rejects_group_below_minimum_sample_count(self):
        rows = self.observations(short_range=[(1, ".7")])
        report = CalibrationEvaluator().evaluate(rows, self.policy)
        self.assertIn("GROUP_SAMPLE_COUNT_BELOW_MINIMUM:SHORT:RANGE", report.reasons)

    def test_rejects_non_oos_observations_instead_of_silently_filtering(self):
        rows = self.observations()
        rows[0] = CalibrationObservation(
            outcome=rows[0].outcome, confidence=rows[0].confidence,
            side=rows[0].side, regime=rows[0].regime, out_of_sample=False,
        )
        report = CalibrationEvaluator().evaluate(rows, self.policy)
        self.assertFalse(report.accepted)
        self.assertIn("NON_OOS_OBSERVATION_PRESENT", report.reasons)

    def test_rejects_ece_above_explicit_limit(self):
        rows = self.observations(long_trend=[(1, ".1")] * 4 + [(0, ".9")] * 4)
        strict = CalibrationGatePolicy(
            max_ece="0.05", min_total_samples=32, min_group_samples=8,
            ece_bins=4, required_regimes=("TREND", "RANGE"),
        )
        report = CalibrationEvaluator().evaluate(rows, strict)
        self.assertFalse(report.accepted)
        self.assertTrue(any(x.startswith("ECE_LIMIT_EXCEEDED:") for x in report.reasons))

    def test_rejects_brier_not_better_than_reference_baseline(self):
        rows = self.observations(long_trend=[(1, ".5")] * 4 + [(0, ".5")] * 4)
        report = CalibrationEvaluator().evaluate(rows, self.policy)
        self.assertIn("BRIER_NOT_BETTER_THAN_BASELINE:LONG:TREND", report.reasons)

    def test_requires_both_long_and_short_for_every_declared_regime(self):
        rows = [x for x in self.observations() if x.side != "LONG"]
        report = CalibrationEvaluator().evaluate(rows, self.policy)
        self.assertIn("GROUP_MISSING:LONG:TREND", report.reasons)
        self.assertIn("GROUP_MISSING:LONG:RANGE", report.reasons)

    def test_rejects_unknown_regime(self):
        rows = self.observations()
        rows.append(CalibrationObservation(1, ".9", "LONG", "UNKNOWN", True))
        report = CalibrationEvaluator().evaluate(rows, self.policy)
        self.assertIn("UNDECLARED_REGIME:UNKNOWN", report.reasons)

    def test_rejects_invalid_probability_or_outcome(self):
        for outcome, confidence in ((2, ".5"), (1, "NaN"), (0, "1.1"), (True, ".5")):
            with self.subTest(outcome=outcome, confidence=confidence):
                rows = self.observations()
                rows[0] = CalibrationObservation(outcome, confidence, "LONG", "TREND", True)
                report = CalibrationEvaluator().evaluate(rows, self.policy)
                self.assertFalse(report.accepted)
                self.assertIn("OBSERVATION_INVALID", report.reasons)

    def test_rejects_missing_or_invalid_gate_configuration(self):
        for policy in (
            None,
            CalibrationGatePolicy(max_ece="NaN", min_total_samples=32, min_group_samples=8,
                                  ece_bins=4, required_regimes=("TREND", "RANGE")),
            CalibrationGatePolicy(max_ece=".2", min_total_samples=0, min_group_samples=8,
                                  ece_bins=4, required_regimes=("TREND", "RANGE")),
            CalibrationGatePolicy(max_ece=".2", min_total_samples=32, min_group_samples=8,
                                  ece_bins=0, required_regimes=("TREND", "RANGE")),
            CalibrationGatePolicy(max_ece=".2", min_total_samples=8, min_group_samples=2,
                                  ece_bins=4, required_regimes=()),
        ):
            with self.subTest(policy=policy):
                report = CalibrationEvaluator().evaluate(self.observations(), policy)
                self.assertFalse(report.accepted)
                self.assertIn("GATE_POLICY_INVALID", report.reasons)

    def test_report_digest_is_deterministic_and_carries_no_trade_authorization(self):
        first = CalibrationEvaluator().evaluate(self.observations(), self.policy)
        second = CalibrationEvaluator().evaluate(self.observations(), self.policy)
        self.assertEqual(first.report_sha256, second.report_sha256)
        self.assertEqual(len(first.report_sha256), 64)
        self.assertFalse(first.trade_authorized)
        self.assertFalse(first.attestation_issued)
        self.assertEqual(len(first.input_sha256), 64)

    def test_report_digest_changes_when_input_or_gate_policy_changes(self):
        baseline = CalibrationEvaluator().evaluate(self.observations(), self.policy)
        changed_rows = self.observations(long_trend=[(1, ".9"), (0, ".1")])
        changed_input = CalibrationEvaluator().evaluate(changed_rows, self.policy)
        changed_policy = CalibrationEvaluator().evaluate(
            self.observations(),
            CalibrationGatePolicy(
                max_ece=".19", min_total_samples=32, min_group_samples=8,
                ece_bins=4, required_regimes=("TREND", "RANGE"),
            ),
        )
        self.assertNotEqual(baseline.input_sha256, changed_input.input_sha256)
        self.assertNotEqual(baseline.report_sha256, changed_input.report_sha256)
        self.assertNotEqual(baseline.report_sha256, changed_policy.report_sha256)

    def test_policy_is_explicit_and_has_no_implicit_acceptance_thresholds(self):
        with self.assertRaises(TypeError):
            CalibrationGatePolicy()


if __name__ == "__main__":
    unittest.main()
