"""RED-first contracts for bounded Core Runner hardening (G2-G4)."""

import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from core_runtime.preflight import PreflightError, _preflight
from core_runtime.one_shot import _runner_policy
import core_runtime.__main__ as cli


LIMITS = {
    "maxDrawdownPct": "50",
    "maxDailyLossUsdt": "50",
    "maxExposureUsdt": "1000",
}


class RunnerHardeningPolicyTest(unittest.TestCase):
    def test_environment_limits_override_config_limits(self):
        config = {
            "risk_limits": dict(LIMITS),
            "max_book_age_ms": 2000,
            "max_position_base": "0.01",
        }
        with patch.dict(os.environ, {
            "PAPER_MAX_DRAWDOWN_PCT": "12.5",
            "PAPER_MAX_DAILY_LOSS_USDT": "7.25",
            "PAPER_MAX_EXPOSURE_USDT": "250",
        }, clear=False):
            limits, _, _ = _runner_policy(config)
        self.assertEqual(limits, {
            "maxDrawdownPct": "12.5",
            "maxDailyLossUsdt": "7.25",
            "maxExposureUsdt": "250",
        })

    def test_unset_environment_limits_preserve_config_values(self):
        config = {
            "risk_limits": dict(LIMITS),
            "max_book_age_ms": 2000,
            "max_position_base": "0.01",
        }
        with patch.dict(os.environ, {
            "PAPER_MAX_DRAWDOWN_PCT": "",
            "PAPER_MAX_DAILY_LOSS_USDT": "",
            "PAPER_MAX_EXPOSURE_USDT": "",
        }, clear=False):
            limits, _, _ = _runner_policy(config)
        self.assertEqual(limits, LIMITS)

    def test_invalid_environment_limit_fails_closed(self):
        config = {
            "risk_limits": dict(LIMITS),
            "max_book_age_ms": 2000,
            "max_position_base": "0.01",
        }
        with patch.dict(os.environ, {"PAPER_MAX_EXPOSURE_USDT": "NaN"}, clear=False):
            with self.assertRaisesRegex(PreflightError, "RUNNER_RISK_LIMIT_INVALID"):
                _runner_policy(config)

    def test_readiness_false_is_returned_only_for_explicit_exit_aware_preflight(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            ledger = root / "paper.sqlite3"
            ledger.touch()
            config = root / "paper.json"
            config.write_text(json.dumps({
                "mode": "PAPER",
                "ai_execution_enabled": False,
                "ledger_path": str(ledger),
                "risk_limits": dict(LIMITS),
                "max_book_age_ms": 2000,
            }), encoding="utf-8")
            risk = {
                "mode": "PAPER",
                "liveTradingSupported": False,
                "riskReady": False,
            }
            with patch("paper_execution.ledger.read_account_risk_snapshot", return_value=risk):
                result = _preflight(config, allow_risk_unready=True)
                self.assertFalse(result["riskReady"])
                with self.assertRaisesRegex(PreflightError, "RISK_STATE_BLOCKED"):
                    _preflight(config)

    def test_cli_exit_codes_distinguish_failure_classes(self):
        cases = (
            ({"runStatus": "NO_SIGNAL"}, 0),
            ({"runStatus": "PAPER_ACCEPTED"}, 0),
            ({"runStatus": "INPUT_REJECTED"}, 2),
            ({"runStatus": "RISK_UNAVAILABLE"}, 3),
            ({"runStatus": "INVALID_SIGNAL"}, 4),
            ({"runStatus": "RISK_REJECTED"}, 5),
            ({"runStatus": "PAPER_COMMIT_FAILED"}, 6),
            ({"runStatus": "RUN_FAILED"}, 6),
        )
        for result, expected in cases:
            with self.subTest(result=result):
                self.assertEqual(cli._exit_code_for_run_result(result), expected)


if __name__ == "__main__":
    unittest.main()
