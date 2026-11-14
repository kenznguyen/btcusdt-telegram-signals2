"""RED-first contracts for bounded Core Runner hardening (G2-G4)."""

import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from core_runtime.preflight import PreflightError, _preflight
from core_runtime.one_shot import _runner_policy, run_once
from core_runtime.test_input_bundle_contract import valid_bundle
from pipeline.test_core_runtime_one_shot import NOW, producer_report
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

    def test_unknown_config_risk_limit_key_fails_closed(self):
        config = {
            "risk_limits": {**LIMITS, "maxDrawdownPercent": "25"},
            "max_book_age_ms": 2000,
            "max_position_base": "0.01",
        }
        with patch.dict(os.environ, {
            "PAPER_MAX_DRAWDOWN_PCT": "",
            "PAPER_MAX_DAILY_LOSS_USDT": "",
            "PAPER_MAX_EXPOSURE_USDT": "",
        }, clear=False):
            with self.assertRaisesRegex(PreflightError, "RUNNER_RISK_LIMITS_REQUIRED"):
                _runner_policy(config)

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
                "max_position_base": "0.01",
            }), encoding="utf-8")
            risk = {
                "mode": "PAPER",
                "liveTradingSupported": False,
                "riskReady": False,
            }
            with patch("core_runtime.preflight.read_account_risk_snapshot", return_value=risk):
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



class RunnerRiskUnreadyDecisionTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.ledger_path = root / "paper.sqlite3"
        self.ledger_path.touch()
        self.config_path = root / "paper.json"
        self.bundle_path = root / "bundle.json"
        self.config_path.write_text(json.dumps({
            "mode": "PAPER",
            "ai_execution_enabled": False,
            "ledger_path": str(self.ledger_path),
            "risk_limits": dict(LIMITS),
            "max_book_age_ms": 2000,
            "max_position_base": "0.01",
        }), encoding="utf-8")
        self.bundle = valid_bundle()
        self.bundle["accountRisk"]["snapshot"]["riskReady"] = False
        self.bundle_path.write_text(json.dumps(self.bundle), encoding="utf-8")

    def test_entry_is_blocked_before_ledger_construction_when_risk_is_unready(self):
        class NeverConstructLedger:
            def __init__(self, *args, **kwargs):
                raise AssertionError("ENTRY must be rejected before ledger construction")

        paper_state = self.bundle["paperState"]
        with (
            patch("core_runtime.one_shot._preflight", return_value={"riskReady": False}),
            patch("core_runtime.one_shot.validate_bundle", return_value={"strategyId": "STRATEGY_CORE"}),
            patch("paper_execution.ledger.read_account_risk_snapshot",
                  return_value=self.bundle["accountRisk"]["snapshot"]),
            patch("paper_execution.ledger.read_snapshot", return_value=paper_state),
            patch("pipeline.core_strategy.produce", return_value=producer_report("BUY")),
            patch("paper_execution.ledger.PaperLedger", NeverConstructLedger),
            patch.dict(os.environ, {
                "PAPER_MAX_DRAWDOWN_PCT": "",
                "PAPER_MAX_DAILY_LOSS_USDT": "",
                "PAPER_MAX_EXPOSURE_USDT": "",
            }, clear=False),
        ):
            result = run_once(self.config_path, self.bundle_path, now_ms=NOW)
        self.assertEqual(result["runStatus"], "RISK_UNAVAILABLE")
        self.assertEqual(result["reasonCode"], "RISK_STATE_BLOCKED")

    def test_valid_position_reducing_exit_can_reach_shared_paper_ledger(self):
        paper_state = {
            "positionBase": "0.0002",
            "averageEntryPrice": "50000",
            "strategyState": {
                "owner": "STRATEGY_CORE",
                "dcaUsed": False,
                "strategyId": "STRATEGY_CORE",
            },
        }
        self.bundle["paperState"] = paper_state
        self.bundle_path.write_text(json.dumps(self.bundle), encoding="utf-8")
        report = producer_report("BUY")
        report["intent"]["targetPositionBase"] = "0.0001"
        submitted = []

        class RecordingLedger:
            def __init__(self, *args, **kwargs):
                pass

            def submit(self, intent, book, now, *, strategy_event=None):
                submitted.append((intent, strategy_event))
                return {
                    "orderId": "paper-exit-fixture",
                    "reservationId": "paper-exit-reservation",
                    "status": "FILLED",
                }

        with (
            patch("core_runtime.one_shot._preflight", return_value={"riskReady": False}),
            patch("core_runtime.one_shot.validate_bundle", return_value={"strategyId": "STRATEGY_CORE"}),
            patch("paper_execution.ledger.read_account_risk_snapshot",
                  return_value=self.bundle["accountRisk"]["snapshot"]),
            patch("paper_execution.ledger.read_snapshot", return_value=paper_state),
            patch("pipeline.core_strategy.produce", return_value=report),
            patch("paper_execution.ledger.PaperLedger", RecordingLedger),
            patch.dict(os.environ, {
                "PAPER_MAX_DRAWDOWN_PCT": "",
                "PAPER_MAX_DAILY_LOSS_USDT": "",
                "PAPER_MAX_EXPOSURE_USDT": "",
            }, clear=False),
        ):
            result = run_once(self.config_path, self.bundle_path, now_ms=NOW)
        self.assertEqual(result["runStatus"], "PAPER_ACCEPTED", result)
        self.assertEqual(len(submitted), 1)
        self.assertEqual(submitted[0][1], "EXIT")
        self.assertEqual(submitted[0][0]["targetPositionBase"], "0.0001")


class ProtectedLedgerPathParityTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.ledger = root / "paper.sqlite3"
        self.ledger.touch()
        self.config = root / "paper.json"
        self.config.write_text(json.dumps({
            "mode": "PAPER",
            "ai_execution_enabled": False,
            "ledger_path": str(self.ledger),
        }), encoding="utf-8")
        self.clean_env = {
            "AI_EXECUTION_ENABLED": "false",
            "MARKET_DATA_DB": "",
            "T0_FEEDER_LEASE_DB": "",
            "PAPER_DB": "",
            "PAPER_TRADING_DB": "",
            "BINANCE_API_KEY": "",
            "BINANCE_API_SECRET": "",
            "OKX_API_KEY": "",
            "OKX_API_SECRET": "",
        }

    def test_one_shot_preflight_rejects_every_t0_database_alias(self):
        for key in ("MARKET_DATA_DB", "T0_FEEDER_LEASE_DB"):
            with self.subTest(key=key), patch.dict(os.environ, {
                **self.clean_env, key: str(self.ledger),
            }, clear=False):
                with self.assertRaisesRegex(PreflightError, "T0_LEDGER_PATH_FORBIDDEN"):
                    _preflight(self.config)

    def test_one_shot_preflight_rejects_t0_parent_child_path_overlap(self):
        for protected in (self.ledger.parent, self.ledger.parent / "nested"):
            with self.subTest(protected=protected), patch.dict(os.environ, {
                **self.clean_env, "T0_FEEDER_LEASE_DB": str(protected),
            }, clear=False):
                with self.assertRaisesRegex(PreflightError, "T0_LEDGER_PATH_FORBIDDEN"):
                    _preflight(self.config)

    def test_one_shot_preflight_requires_paper_database_aliases_to_match(self):
        for key in ("PAPER_DB", "PAPER_TRADING_DB"):
            with self.subTest(key=key), patch.dict(os.environ, {
                **self.clean_env, key: str(self.ledger.parent / "other.sqlite3"),
            }, clear=False):
                with self.assertRaisesRegex(PreflightError, "LEDGER_PATH_ENV_MISMATCH"):
                    _preflight(self.config)

    def test_one_shot_preflight_accepts_exact_paper_database_aliases(self):
        from unittest.mock import patch as mock_patch
        risk = {"mode": "PAPER", "liveTradingSupported": False, "riskReady": True}
        with (
            patch.dict(os.environ, {
                **self.clean_env,
                "PAPER_DB": str(self.ledger),
                "PAPER_TRADING_DB": str(self.ledger),
            }, clear=False),
            mock_patch("core_runtime.preflight.read_account_risk_snapshot", return_value=risk),
        ):
            result = _preflight(self.config)
        self.assertTrue(result["riskReady"])


if __name__ == "__main__":
    unittest.main()
