"""Owner-approved AI Strategy contract tests. Intentionally RED until implementation exists."""

import inspect
import os
import tempfile
import unittest
from unittest.mock import patch

from pipeline import api, decision
from pipeline.test_decision import DecisionTest


class AIStrategyContractRedTest(unittest.TestCase):
    def setUp(self):
        self.fixture = DecisionTest()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)

    def calibrated_prediction(self, confidence="0.8", **changes):
        prediction = dict(self.fixture.prediction)
        prediction["calibration"] = {
            "calibratedConfidence": confidence,
            "calibrationVersion": "cal-v1",
            "calibrationMethod": "isotonic",
            "calibrationArtifactHash": "sha256:" + "b" * 64,
            "calibrationDatasetVersion": "sha256:" + "c" * 64,
            "calibrationSampleCount": 1000,
            "calibrationStartMs": self.fixture.prediction["trainedThroughMs"] + 1,
            "calibrationEndMs": self.fixture.prediction["trainedThroughMs"] + 500,
            "calibratedAtMs": self.fixture.prediction["availableAtMs"] - 1,
            "labelDefinition": "direction_correct_at_horizon",
            "forecastHorizonMs": 900000,
        }
        prediction["calibration"].update(changes)
        return prediction

    def evaluate(self, prediction=None, **kwargs):
        return self.fixture.evaluate(
            prediction=self.fixture.prediction if prediction is None else prediction,
            **kwargs,
        )

    def test_missing_calibrated_confidence_blocks_an_otherwise_valid_ai_prediction(self):
        result = self.evaluate()
        self.assertEqual(result["action"], "WAIT", result)
        self.assertIsNone(result["intent"], result)

    def test_confidence_outside_unit_interval_and_nonfinite_values_fail_closed(self):
        for confidence in ("-0.01", "1.01", "NaN", "Infinity", "-Infinity", True):
            with self.subTest(confidence=confidence):
                result = self.evaluate(prediction=self.calibrated_prediction(confidence))
                self.assertEqual(result["action"], "WAIT", result)
                self.assertIsNone(result["intent"], result)

    def test_missing_calibration_provenance_fails_closed(self):
        for field in (
            "calibrationVersion", "calibrationMethod", "calibrationArtifactHash",
            "calibrationDatasetVersion", "calibrationSampleCount",
            "calibrationStartMs", "calibrationEndMs", "calibratedAtMs",
            "labelDefinition", "forecastHorizonMs",
        ):
            calibration = self.calibrated_prediction()["calibration"]
            calibration.pop(field)
            prediction = dict(self.fixture.prediction, calibration=calibration)
            with self.subTest(missing=field):
                result = self.evaluate(prediction=prediction)
                self.assertEqual(result["action"], "WAIT", result)
                self.assertIsNone(result["intent"], result)

    def test_ai_ledger_uses_ai_policy_leverage_not_generic_leverage(self):
        self.assertIn("admitted_leverage", inspect.signature(api.ledger).parameters)
        with tempfile.TemporaryDirectory() as directory:
            db = os.path.join(directory, "paper.sqlite3")
            environment = {
                "MARKET_DATA_DB": db,
                "PAPER_MAX_DRAWDOWN_PCT": "50",
                "PAPER_MAX_DAILY_LOSS_USDT": "50",
                "PAPER_MAX_EXPOSURE_USDT": "1000",
                "LEVERAGE": "13",
            }
            from paper_execution import ledger as ledger_module
            with patch.dict(os.environ, environment, clear=True), \
                 patch.object(ledger_module, "dual_ledger_ready", return_value=True), \
                 patch.object(ledger_module, "PaperLedger") as constructor:
                api.ledger(strategy_id="AI_FREQAI", admitted_leverage="2.25")
            self.assertEqual(constructor.call_args.kwargs["leverage"], "2.25")

    def test_ai_entry_is_sized_from_reconciled_equity_leverage_limit_price_and_lot_step(self):
        required = {"account_equity_quote", "confidence_min", "lot_size", "current_position_base"}
        self.assertTrue(required.issubset(inspect.signature(decision.evaluate).parameters))
        prediction = self.calibrated_prediction("0.8")
        result = self.evaluate(
            prediction=prediction,
            account_equity_quote="1000",
            confidence_min="0.6",
            lot_size="0.001",
            current_position_base="0",
        )
        self.assertEqual(result["action"], "BUY", result)
        self.assertEqual(result["intent"]["targetPositionBase"], "0.198")
        self.assertEqual(result["intent"]["leverage"], "2")
        self.assertEqual(result["intent"]["marginBudgetQuote"], "10")

    def test_ai_ledger_rejects_leverage_outside_approved_one_to_three_range(self):
        from paper_execution.ledger import PaperLedger

        with tempfile.TemporaryDirectory() as directory:
            db = os.path.join(directory, "paper.sqlite3")
            legacy = PaperLedger(db)
            timestamp = 1_800_000_000_000
            legacy.record_equity(
                "100", timestamp - 60_000, timestamp,
                "sha256:" + "c" * 64, "100",
            )
            PaperLedger(
                db, strategy_id="STRATEGY_CORE", source_sha="d" * 40,
            )
            for leverage in ("0.99", "3.01", "13"):
                with self.subTest(leverage=leverage):
                    with self.assertRaises(ValueError):
                        PaperLedger(
                            db, strategy_id="AI_FREQAI", leverage=leverage,
                            apply_migrations=False,
                        )

    def test_missing_or_stale_reconciled_equity_never_creates_an_ai_intent(self):
        required = {"account_equity_quote", "confidence_min", "lot_size", "current_position_base"}
        self.assertTrue(required.issubset(inspect.signature(decision.evaluate).parameters))
        prediction = self.calibrated_prediction("0.8")
        for equity in (None, "0", "-1"):
            with self.subTest(equity=equity):
                result = self.evaluate(
                    prediction=prediction,
                    account_equity_quote=equity,
                    confidence_min="0.6",
                    lot_size="0.001",
                    current_position_base="0",
                )
                self.assertEqual(result["action"], "WAIT", result)
                self.assertIsNone(result["intent"], result)


if __name__ == "__main__":
    unittest.main()
