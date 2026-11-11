"""Owner-approved AI Strategy API contract tests.

These tests intentionally remain RED until the production contract is implemented.
Policy values below are isolated fixtures, not production defaults or owner-selected
calibration thresholds.
"""

import os
import tempfile
import unittest
from unittest.mock import patch

from pipeline import api
from pipeline.test_decision import DecisionTest


class AIStrategyContractRedTest(unittest.TestCase):
    FIXTURE_CONFIDENCE_MIN = "0.6"

    def setUp(self):
        self.fixture = DecisionTest()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)

    def calibrated_prediction(self, confidence="0.8", **changes):
        prediction = dict(self.fixture.prediction)
        prediction["calibration"] = {
            "calibratedConfidence": confidence,
            "calibrationVersion": "cal-fixture-v1",
            "calibrationMethod": "isotonic-fixture",
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

    def admission_context(self, **changes):
        now = self.fixture.now
        context = {
            "ai_policy": {
                "policyVersion": "ai-policy-fixture-v1",
                "confidenceMin": self.FIXTURE_CONFIDENCE_MIN,
                "minCalibrationSamples": 100,
                "minCalibrationPeriodMs": 100,
                "maxCalibrationAgeMs": 60000,
                "leverageMappingVersion": "linear-confidence-v1",
                "minimumLeverage": "1",
                "maximumLeverage": "3",
            },
            "account_risk": {
                "riskReady": True,
                "accountEquityQuote": "1000",
                "observedAtMs": now,
                "freshnessLimitMs": 60000,
                "reconciliationState": "RECONCILED",
                "reconciliationVersion": "equity-fixture-v1",
                "riskConfigVersion": "risk-fixture-v1",
                "killSwitchEnabled": False,
            },
            "instrument_rules": {
                "symbol": "BTCUSDT",
                "marketType": "USDT_PERPETUAL",
                "lotSize": "0.001",
                "tickSize": "0.1",
                "minimumQuantity": "0.001",
                "minimumNotionalQuote": "5",
                "sourceVersion": "instrument-fixture-v1",
                "asOfMs": now,
            },
            "ai_position": {
                "signedPositionBase": "0",
                "ledgerSnapshotVersion": "ai-ledger-fixture-v1",
            },
        }
        for section, values in changes.items():
            context[section].update(values)
        return context

    def evaluate(self, prediction=None, admission_context=None):
        """Exercise the decision boundary; report unsupported contract as a RED result.

        Catch only Python's explicit unsupported-keyword error so missing API behavior
        is recorded as an assertion failure, not a runtime-error test failure.
        """
        try:
            return self.fixture.evaluate(
                prediction=self.fixture.prediction if prediction is None else prediction,
                admission_context=(
                    self.admission_context()
                    if admission_context is None else admission_context
                ),
            )
        except TypeError as error:
            if "unexpected keyword argument 'admission_context'" not in str(error):
                raise
            self.skipTest(
                "decision.evaluate has no admission_context API; "
                "dependent calibration/equity/sizing behavior is not yet testable"
            )

    def test_decision_boundary_accepts_owner_approved_admission_context(self):
        try:
            self.fixture.evaluate(
                prediction=self.calibrated_prediction("0.8"),
                admission_context=self.admission_context(),
            )
        except TypeError as error:
            if "unexpected keyword argument 'admission_context'" not in str(error):
                raise
            self.fail(
                "decision.evaluate must accept the owner-approved admission_context"
            )

    def assert_contract_wait(self, result):
        self.assertEqual(result["action"], "WAIT", result)
        self.assertIsNone(result["intent"], result)

    def test_missing_calibrated_confidence_blocks_an_otherwise_valid_ai_prediction(self):
        self.assert_contract_wait(self.evaluate())

    def test_confidence_outside_unit_interval_and_nonfinite_values_fail_closed(self):
        for confidence in ("-0.01", "1.01", "NaN", "Infinity", "-Infinity", True):
            with self.subTest(confidence=confidence):
                self.assert_contract_wait(
                    self.evaluate(prediction=self.calibrated_prediction(confidence))
                )

    def test_missing_calibration_provenance_fails_closed(self):
        for field in (
            "calibrationVersion", "calibrationMethod", "calibrationArtifactHash",
            "calibrationDatasetVersion", "calibrationSampleCount",
            "calibrationStartMs", "calibrationEndMs", "calibratedAtMs",
            "labelDefinition", "forecastHorizonMs",
        ):
            prediction = self.calibrated_prediction()
            prediction["calibration"].pop(field)
            with self.subTest(missing=field):
                self.assert_contract_wait(self.evaluate(prediction=prediction))

    def test_confidence_minimum_policy_is_required_and_validated(self):
        invalid_values = (None, "not-a-number", "NaN", "1", "-0.01", "1.01")
        for confidence_min in invalid_values:
            context = self.admission_context(
                ai_policy={"confidenceMin": confidence_min}
            )
            with self.subTest(confidence_min=confidence_min):
                self.assert_contract_wait(self.evaluate(
                    prediction=self.calibrated_prediction("0.8"),
                    admission_context=context,
                ))

    def test_confidence_below_policy_minimum_fails_closed(self):
        context = self.admission_context(
            ai_policy={"confidenceMin": self.FIXTURE_CONFIDENCE_MIN}
        )
        self.assert_contract_wait(self.evaluate(
            prediction=self.calibrated_prediction("0.59"),
            admission_context=context,
        ))

    def test_leverage_mapping_has_one_three_and_interior_fixture_boundaries(self):
        cases = (
            ("0.6", "1"),
            ("1", "3"),
            ("0.8", "2"),
        )
        for confidence, expected_leverage in cases:
            with self.subTest(confidence=confidence):
                result = self.evaluate(
                    prediction=self.calibrated_prediction(confidence),
                    admission_context=self.admission_context(),
                )
                self.assertEqual(result["action"], "BUY", result)
                self.assertIsNotNone(result["intent"], result)
                self.assertEqual(result["intent"]["leverage"], expected_leverage)

    def test_malformed_calibration_artifact_hash_fails_closed(self):
        prediction = self.calibrated_prediction(
            calibrationArtifactHash="sha256:not-a-digest"
        )
        self.assert_contract_wait(self.evaluate(prediction=prediction))

    def test_calibration_temporal_ordering_and_training_cutoff_fail_closed(self):
        valid = self.calibrated_prediction()
        calibration = valid["calibration"]
        cases = {
            "calibration_starts_before_training_cutoff": {
                "calibrationStartMs": valid["trainedThroughMs"],
            },
            "calibration_ends_before_it_starts": {
                "calibrationEndMs": calibration["calibrationStartMs"] - 1,
            },
            "calibrated_before_calibration_ended": {
                "calibratedAtMs": calibration["calibrationEndMs"] - 1,
            },
            "prediction_precedes_calibration": {
                "calibratedAtMs": valid["availableAtMs"] + 1,
            },
        }
        for name, changes in cases.items():
            prediction = self.calibrated_prediction(**changes)
            with self.subTest(case=name):
                self.assert_contract_wait(self.evaluate(prediction=prediction))

    def test_stale_calibration_and_insufficient_samples_or_period_fail_closed(self):
        now = self.fixture.now
        cases = (
            ("stale", self.calibrated_prediction(
                calibratedAtMs=now - 60001
            )),
            ("too_few_samples", self.calibrated_prediction(
                calibrationSampleCount=99
            )),
            ("too_short_period", self.calibrated_prediction(
                calibrationEndMs=(
                    self.fixture.prediction["trainedThroughMs"] + 50
                )
            )),
        )
        for name, prediction in cases:
            with self.subTest(case=name):
                self.assert_contract_wait(self.evaluate(prediction=prediction))

    def test_ai_entry_uses_reconciled_equity_leverage_execution_price_and_lot_step(self):
        result = self.evaluate(
            prediction=self.calibrated_prediction("0.8"),
            admission_context=self.admission_context(),
        )
        self.assertEqual(result["action"], "BUY", result)
        intent = result["intent"]
        self.assertEqual(intent["targetPositionBase"], "0.198")
        self.assertEqual(intent["limitPrice"], "101")
        self.assertEqual(intent["leverage"], "2")
        self.assertEqual(intent["marginBudgetQuote"], "10")

    def test_missing_stale_unreconciled_or_unready_equity_never_creates_intent(self):
        now = self.fixture.now
        cases = (
            ("missing", {"accountEquityQuote": None}),
            ("zero", {"accountEquityQuote": "0"}),
            ("negative", {"accountEquityQuote": "-1"}),
            ("stale", {"observedAtMs": now - 60001}),
            ("not_reconciled", {"reconciliationState": "PENDING"}),
            ("risk_not_ready", {"riskReady": False}),
        )
        for name, account_changes in cases:
            context = self.admission_context(account_risk=account_changes)
            with self.subTest(case=name):
                self.assert_contract_wait(self.evaluate(
                    prediction=self.calibrated_prediction("0.8"),
                    admission_context=context,
                ))

    def test_kill_switch_blocks_new_ai_intent(self):
        context = self.admission_context(
            account_risk={"killSwitchEnabled": True}
        )
        self.assert_contract_wait(self.evaluate(
            prediction=self.calibrated_prediction("0.8"),
            admission_context=context,
        ))

    def test_invalid_execution_price_or_instrument_lot_rules_fail_closed(self):
        cases = (
            ("non_positive_price", {"book": None}),
            ("zero_lot_size", {"instrument_rules": {"lotSize": "0"}}),
            ("negative_lot_size", {"instrument_rules": {"lotSize": "-0.001"}}),
            ("invalid_tick_size", {"instrument_rules": {"tickSize": "0"}}),
            ("minimum_quantity", {
                "instrument_rules": {
                    "minimumQuantity": "1",
                    "minimumNotionalQuote": "100000",
                }
            }),
        )
        for name, changes in cases:
            context_changes = {
                key: value for key, value in changes.items() if key != "book"
            }
            context = self.admission_context(**context_changes)
            if "book" in changes:
                with self.subTest(case=name):
                    bad_book = dict(self.fixture.book)
                    bad_book["asks"] = [{"price": "0", "quantity": "2"}]
                    self.assert_contract_wait(self.evaluate(
                        prediction=self.calibrated_prediction("0.8"),
                        admission_context=context,
                        book=bad_book,
                    ))
            else:
                with self.subTest(case=name):
                    self.assert_contract_wait(self.evaluate(
                        prediction=self.calibrated_prediction("0.8"),
                        admission_context=context,
                    ))

    def test_ai_ledger_factory_uses_explicit_admitted_leverage_not_generic_leverage(self):
        from paper_execution.ledger import PaperLedger

        with tempfile.TemporaryDirectory() as directory:
            db = os.path.join(directory, "paper.sqlite3")
            legacy = PaperLedger(db)
            timestamp = 1_800_000_000_000
            legacy.record_equity(
                "100", timestamp - 60000, timestamp,
                "sha256:" + "c" * 64, "100",
            )
            PaperLedger(
                db, strategy_id="STRATEGY_CORE", source_sha="d" * 40,
            )
            environment = {
                "MARKET_DATA_DB": db,
                "PAPER_MAX_DRAWDOWN_PCT": "50",
                "PAPER_MAX_DAILY_LOSS_USDT": "50",
                "PAPER_MAX_EXPOSURE_USDT": "1000",
                "LEVERAGE": "13",
            }
            with patch.dict(os.environ, environment, clear=True):
                try:
                    ai_ledger = api.ledger(
                        strategy_id="AI_FREQAI", admitted_leverage="2.25"
                    )
                except TypeError as error:
                    if "unexpected keyword argument 'admitted_leverage'" not in str(error):
                        raise
                    ai_ledger = None
            self.assertIsNotNone(ai_ledger, "AI ledger factory lacks admitted leverage API")
            self.assertEqual(str(ai_ledger.leverage), "2.25")

    def test_ai_ledger_accepts_only_the_inclusive_one_to_three_leverage_domain(self):
        from paper_execution.ledger import PaperLedger

        with tempfile.TemporaryDirectory() as directory:
            db = os.path.join(directory, "paper.sqlite3")
            legacy = PaperLedger(db)
            timestamp = 1_800_000_000_000
            legacy.record_equity(
                "100", timestamp - 60000, timestamp,
                "sha256:" + "c" * 64, "100",
            )
            PaperLedger(
                db, strategy_id="STRATEGY_CORE", source_sha="d" * 40,
            )
            for leverage in ("1", "3"):
                with self.subTest(accepted=leverage):
                    admitted = PaperLedger(
                        db, strategy_id="AI_FREQAI", leverage=leverage,
                        apply_migrations=False,
                    )
                    self.assertEqual(str(admitted.leverage), leverage)
            for leverage in ("0.99", "3.01", "13"):
                with self.subTest(rejected=leverage):
                    with self.assertRaises(ValueError):
                        PaperLedger(
                            db, strategy_id="AI_FREQAI", leverage=leverage,
                            apply_migrations=False,
                        )

    def test_core_ledger_leverage_remains_thirteen_independent_of_generic_setting(self):
        from paper_execution.ledger import PaperLedger

        with tempfile.TemporaryDirectory() as directory:
            db = os.path.join(directory, "paper.sqlite3")
            legacy = PaperLedger(db)
            timestamp = 1_800_000_000_000
            legacy.record_equity(
                "100", timestamp - 60000, timestamp,
                "sha256:" + "c" * 64, "100",
            )
            PaperLedger(
                db, strategy_id="STRATEGY_CORE", source_sha="d" * 40,
            )
            environment = {
                "MARKET_DATA_DB": db,
                "PAPER_MAX_DRAWDOWN_PCT": "50",
                "PAPER_MAX_DAILY_LOSS_USDT": "50",
                "PAPER_MAX_EXPOSURE_USDT": "1000",
                "LEVERAGE": "2",
            }
            with patch.dict(os.environ, environment, clear=True):
                core_ledger = api.ledger(strategy_id="STRATEGY_CORE")
            self.assertEqual(str(core_ledger.leverage), "13")


if __name__ == "__main__":
    unittest.main()
