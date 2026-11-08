"""Fail-closed tests for the independent AI label/direction contract V1."""
import json
import unittest
from decimal import Decimal

from quant_system.ai_label_direction_contract import (
    ContractValidationError,
    parse_ai_label_direction_contract,
)


def valid_contract():
    return {
        "schema_version": 1,
        "contract_id": "btc-usdt-ai-label-direction-v1",
        "model_id": "btc-usdt-independent-ai-v1",
        "market": {
            "exchange": "binance",
            "market_type": "USDT_PERPETUAL",
            "symbol": "BTCUSDT",
        },
        "label": {
            "horizon_m15_candles": 4,
            "decision_price_basis": "decision_m15_close",
            "outcome_price_basis": "horizon_m15_close",
            "label_end_rule": "decision_candle_open_plus_horizon_m15_candles",
            "outcome_available_at_rule": "outcome_candle_first_observed_after_exclusive_close",
            "formula_id": "forward_return_v1",
        },
        "direction": {
            "short_threshold": "-0.002",
            "long_threshold": "0.002",
            "neutral_action": "ABSTAIN",
        },
        "features": {
            "timeframes": ["15m", "1h"],
            "cutoff_semantics": "closed_validated_first_observed_available_by_prediction",
        },
        "confidence": {
            "source": "separate_calibration_artifact",
        },
    }


class AILabelDirectionContractTests(unittest.TestCase):
    def test_parses_complete_contract_without_inventing_thresholds(self):
        payload = valid_contract()
        result = parse_ai_label_direction_contract(payload)

        self.assertEqual(result.contract_id, payload["contract_id"])
        self.assertEqual(result.horizon_m15_candles, 4)
        self.assertEqual(result.short_threshold, Decimal("-0.002"))
        self.assertEqual(result.long_threshold, Decimal("0.002"))
        self.assertEqual(result.feature_timeframes, ("15m", "1h"))
        self.assertEqual(result.neutral_action, "ABSTAIN")

    def test_accepts_canonical_json_bytes(self):
        result = parse_ai_label_direction_contract(
            json.dumps(valid_contract(), sort_keys=True, separators=(",", ":")).encode()
        )
        self.assertEqual(result.model_id, "btc-usdt-independent-ai-v1")

    def test_rejects_missing_horizon_instead_of_defaulting(self):
        payload = valid_contract()
        del payload["label"]["horizon_m15_candles"]
        with self.assertRaises(ContractValidationError):
            parse_ai_label_direction_contract(payload)

    def test_rejects_boolean_horizon(self):
        payload = valid_contract()
        payload["label"]["horizon_m15_candles"] = True
        with self.assertRaises(ContractValidationError):
            parse_ai_label_direction_contract(payload)

    def test_rejects_non_positive_horizon(self):
        payload = valid_contract()
        payload["label"]["horizon_m15_candles"] = 0
        with self.assertRaises(ContractValidationError):
            parse_ai_label_direction_contract(payload)

    def test_rejects_missing_price_basis(self):
        payload = valid_contract()
        payload["label"]["decision_price_basis"] = ""
        with self.assertRaises(ContractValidationError):
            parse_ai_label_direction_contract(payload)

    def test_rejects_missing_outcome_availability_semantics(self):
        payload = valid_contract()
        payload["label"]["outcome_available_at_rule"] = None
        with self.assertRaises(ContractValidationError):
            parse_ai_label_direction_contract(payload)

    def test_rejects_thresholds_without_neutral_interval(self):
        payload = valid_contract()
        payload["direction"]["short_threshold"] = "0.002"
        payload["direction"]["long_threshold"] = "0.002"
        with self.assertRaises(ContractValidationError):
            parse_ai_label_direction_contract(payload)

    def test_rejects_non_finite_threshold(self):
        payload = valid_contract()
        payload["direction"]["long_threshold"] = "NaN"
        with self.assertRaises(ContractValidationError):
            parse_ai_label_direction_contract(payload)

    def test_rejects_sign_only_direction_policy(self):
        payload = valid_contract()
        payload["direction"]["neutral_action"] = "NONE"
        with self.assertRaises(ContractValidationError):
            parse_ai_label_direction_contract(payload)

    def test_requires_both_m15_and_h1_as_features(self):
        payload = valid_contract()
        payload["features"]["timeframes"] = ["15m"]
        with self.assertRaises(ContractValidationError):
            parse_ai_label_direction_contract(payload)

    def test_rejects_duplicate_json_keys(self):
        raw = b'{"schema_version":1,"schema_version":1}'
        with self.assertRaises(ContractValidationError):
            parse_ai_label_direction_contract(raw)

    def test_rejects_unknown_fields(self):
        payload = valid_contract()
        payload["direction"]["threshold_from_oos"] = True
        with self.assertRaises(ContractValidationError):
            parse_ai_label_direction_contract(payload)

    def test_rejects_regression_output_as_confidence(self):
        payload = valid_contract()
        payload["confidence"]["source"] = "predicted_return"
        with self.assertRaises(ContractValidationError):
            parse_ai_label_direction_contract(payload)


if __name__ == "__main__":
    unittest.main()
