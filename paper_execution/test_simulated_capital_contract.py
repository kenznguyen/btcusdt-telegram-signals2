import json
import unittest
from pathlib import Path

from paper_execution.simulated_capital import (
    DEFAULT_SIMULATED_CAPITAL_CONTRACT,
    validate_simulated_capital_contract,
)


class SimulatedCapitalContractTest(unittest.TestCase):
    def test_machine_contract_matches_validator_defaults(self):
        path = Path(__file__).parent / "contracts" / "simulated_capital_v1.json"
        contract = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(contract, DEFAULT_SIMULATED_CAPITAL_CONTRACT)
        validate_simulated_capital_contract(contract)

    def test_approved_contract_is_valid(self):
        result = validate_simulated_capital_contract(DEFAULT_SIMULATED_CAPITAL_CONTRACT)
        self.assertEqual(result["initialCapitalQuote"], "100")
        self.assertEqual(result["riskLimits"]["maxDrawdownPct"], "10")
        self.assertEqual(result["riskLimits"]["maxDailyLossUsdt"], "2")
        self.assertEqual(result["riskLimits"]["maxExposureUsdt"], "10")
        self.assertEqual(result["riskLimits"]["maxOrderMarginPct"], "1")

    def test_rejects_live_or_ai_execution(self):
        for field, value in (
            ("liveTradingSupported", True),
            ("aiExecutionEnabled", True),
        ):
            with self.subTest(field=field):
                contract = {**DEFAULT_SIMULATED_CAPITAL_CONTRACT, field: value}
                with self.assertRaisesRegex(ValueError, "SIMULATED_CAPITAL_EXECUTION_BOUNDARY"):
                    validate_simulated_capital_contract(contract)

    def test_rejects_capital_reset_or_auto_top_up(self):
        for field in ("resetOnRestart", "autoTopUp"):
            with self.subTest(field=field):
                contract = {**DEFAULT_SIMULATED_CAPITAL_CONTRACT, field: True}
                with self.assertRaisesRegex(ValueError, "SIMULATED_CAPITAL_CAPITAL_MUTATION_FORBIDDEN"):
                    validate_simulated_capital_contract(contract)

    def test_rejects_unapproved_capital_and_risk_limits(self):
        for field, value in (
            ("initialCapitalQuote", "101"),
            ("quoteCurrency", "USD"),
        ):
            with self.subTest(field=field):
                contract = {**DEFAULT_SIMULATED_CAPITAL_CONTRACT, field: value}
                with self.assertRaises(ValueError):
                    validate_simulated_capital_contract(contract)

        limits = {**DEFAULT_SIMULATED_CAPITAL_CONTRACT["riskLimits"], "maxDailyLossUsdt": "2.1"}
        contract = {**DEFAULT_SIMULATED_CAPITAL_CONTRACT, "riskLimits": limits}
        with self.assertRaisesRegex(ValueError, "SIMULATED_CAPITAL_RISK_LIMITS_INVALID"):
            validate_simulated_capital_contract(contract)

    def test_rejects_unknown_or_missing_fields(self):
        contract = {**DEFAULT_SIMULATED_CAPITAL_CONTRACT, "unexpected": 1}
        with self.assertRaisesRegex(ValueError, "SIMULATED_CAPITAL_FIELDS_INVALID"):
            validate_simulated_capital_contract(contract)
        contract = dict(DEFAULT_SIMULATED_CAPITAL_CONTRACT)
        del contract["initialCapitalQuote"]
        with self.assertRaisesRegex(ValueError, "SIMULATED_CAPITAL_FIELDS_INVALID"):
            validate_simulated_capital_contract(contract)


if __name__ == "__main__":
    unittest.main()
