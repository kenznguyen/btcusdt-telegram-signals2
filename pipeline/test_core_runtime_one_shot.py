"""Contract tests for the bounded, one-shot Core PAPER runner."""

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from core_runtime.test_input_bundle_contract import valid_bundle
from core_runtime.one_shot import run_once


NOW = 1_800_000_000_000
LIMITS = {
    "maxDrawdownPct": "50",
    "maxDailyLossUsdt": "50",
    "maxExposureUsdt": "1000",
}


def producer_report(action="BUY"):
    if action == "WAIT":
        return {"action": "WAIT", "reason": "CORE_NO_ENTRY", "intent": None}
    return {
        "action": action,
        "reason": "RSI_ADX_ENTRY",
        "intent": {
            "schemaVersion": 1,
            "source": "STRATEGY_CORE",
            "exchange": "binance",
            "marketType": "USDT_PERPETUAL",
            "symbol": "BTCUSDT",
            "timeframe": "15m",
            "action": "LONG" if action == "BUY" else "SHORT",
            "reason": "RSI_ADX_ENTRY",
            "strategyVersion": "rsi-adx-smart-dca-v1",
            "datasetVersion": "sha256:" + "a" * 64,
            "inputSnapshotId": "core-input-fixture",
            "decisionAtMs": NOW,
            "validUntilMs": NOW + 30_000,
            "targetPositionBase": "0.0001" if action == "BUY" else "-0.0001",
            "limitPrice": "50001",
            "initialMarginQuote": "1",
            "candleOpenTimeMs": NOW - 900_000,
        },
    }


class CoreOneShotRunnerTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.ledger_path = root / "paper.sqlite3"
        self.ledger_path.touch()
        self.config_path = root / "paper-runner.json"
        self.bundle_path = root / "bundle-v1.json"
        self.config_path.write_text(json.dumps({
            "mode": "PAPER",
            "ai_execution_enabled": False,
            "ledger_path": str(self.ledger_path),
            "risk_limits": LIMITS,
            "max_book_age_ms": 2_000,
            "max_position_base": "0.01",
        }), encoding="utf-8")
        self.bundle = valid_bundle()
        self.bundle_path.write_text(json.dumps(self.bundle), encoding="utf-8")
        self.paper_state = {
            "positionBase": "0",
            "averageEntryPrice": "0",
            "strategyState": {
                "owner": None, "dcaUsed": False, "strategyId": "STRATEGY_CORE",
            },
        }

    def run_patched(self, report, order=None, *, risk=None, paper_state=None, submit_error=None):
        created = []
        class FakeLedger:
            def __init__(self, *args, **kwargs):
                self.submit_calls = 0
                created.append(self)

            def submit(inner, *args, **kwargs):
                inner.submit_calls += 1
                if submit_error:
                    raise submit_error
                return order or {
                    "orderId": "paper-order-1",
                    "reservationId": "reservation-1",
                    "status": "FILLED",
                    "reason": "VISIBLE_DEPTH_SIMULATION",
                }

        with (
            patch("core_runtime.one_shot._preflight", return_value={"status": "PREFLIGHT_PASS", "riskReady": True}),
            patch("paper_execution.ledger.read_account_risk_snapshot",
                  return_value=risk or self.bundle["accountRisk"]["snapshot"]),
            patch("paper_execution.ledger.read_snapshot",
                  return_value=paper_state or self.paper_state),
            patch("pipeline.core_strategy.produce", return_value=report),
            patch("paper_execution.ledger.PaperLedger", FakeLedger),
        ):
            result = run_once(self.config_path, self.bundle_path, now_ms=NOW)
        return result, created

    def test_actionable_core_signal_is_submitted_once_to_paper_ledger(self):
        result, created = self.run_patched(producer_report())
        self.assertEqual(result["runStatus"], "PAPER_ACCEPTED", result)
        self.assertEqual(result["signal"]["action"], "BUY")
        self.assertEqual(result["riskDecision"]["decision"], "ACCEPT")
        self.assertEqual(result["paperLedgerReference"]["orderId"], "paper-order-1")
        self.assertEqual(len(created), 1)
        self.assertEqual(created[0].submit_calls, 1)

    def test_no_signal_does_not_construct_or_write_paper_ledger(self):
        result, created = self.run_patched(producer_report("WAIT"))
        self.assertEqual(result["runStatus"], "NO_SIGNAL", result)
        self.assertEqual(len(created), 0)

    def test_invalid_bundle_is_rejected_before_ledger_construction(self):
        self.bundle["mode"] = "LIVE"
        self.bundle_path.write_text(json.dumps(self.bundle), encoding="utf-8")
        result, created = self.run_patched(producer_report())
        self.assertEqual(result["runStatus"], "INPUT_REJECTED")
        self.assertEqual(len(created), 0)

    def test_changed_account_risk_snapshot_is_rejected_before_submit(self):
        changed = dict(self.bundle["accountRisk"]["snapshot"])
        changed["accountEquityQuote"] = "99"
        result, created = self.run_patched(producer_report(), risk=changed)
        self.assertEqual(result["runStatus"], "INPUT_REJECTED")
        self.assertEqual(len(created), 0)

    def test_changed_core_paper_state_is_rejected_before_submit(self):
        changed = {
            "positionBase": "0.001",
            "averageEntryPrice": "50000",
            "strategyState": {
                "owner": "STRATEGY_CORE", "dcaUsed": False,
                "strategyId": "STRATEGY_CORE",
            },
        }
        result, created = self.run_patched(producer_report(), paper_state=changed)
        self.assertEqual(result["runStatus"], "INPUT_REJECTED")
        self.assertEqual(len(created), 0)

    def test_shared_risk_rejection_is_reported_without_ai_fallback(self):
        rejected = {
            "orderId": "paper-order-rejected",
            "reservationId": None,
            "status": "REJECTED",
            "reason": "KILL_SWITCH",
        }
        result, created = self.run_patched(producer_report(), order=rejected)
        self.assertEqual(result["runStatus"], "RISK_REJECTED")
        self.assertEqual(result["riskDecision"]["reason"], "KILL_SWITCH")
        self.assertEqual(len(created), 1)

    def test_transactional_risk_input_unavailable_has_distinct_result(self):
        rejected = {
            "orderId": "paper-order-risk-unavailable",
            "reservationId": None,
            "status": "REJECTED",
            "reason": "RISK_INPUTS_UNAVAILABLE",
        }
        result, created = self.run_patched(producer_report(), order=rejected)
        self.assertEqual(result["runStatus"], "RISK_UNAVAILABLE")
        self.assertEqual(result["reasonCode"], "RISK_INPUTS_UNAVAILABLE")
        self.assertEqual(len(created), 1)

    def test_ledger_exception_is_reported_as_commit_failure(self):
        result, created = self.run_patched(
            producer_report(), submit_error=RuntimeError("injected"),
        )
        self.assertEqual(result["runStatus"], "PAPER_COMMIT_FAILED")
        self.assertEqual(len(created), 1)

    def test_missing_runner_risk_limits_reject_before_ledger_construction(self):
        config = json.loads(self.config_path.read_text(encoding="utf-8"))
        del config["risk_limits"]
        self.config_path.write_text(json.dumps(config), encoding="utf-8")
        result, created = self.run_patched(producer_report())
        self.assertEqual(result["runStatus"], "INPUT_REJECTED")
        self.assertEqual(len(created), 0)

    def test_ai_execution_environment_override_is_rejected_before_ledger_construction(self):
        class NeverConstructLedger:
            def __init__(self, *args, **kwargs):
                raise AssertionError("Ledger must not be constructed")

        with (
            patch.dict("os.environ", {
                "AI_EXECUTION_ENABLED": "true",
                "BINANCE_API_KEY": "",
                "BINANCE_API_SECRET": "",
                "OKX_API_KEY": "",
                "OKX_API_SECRET": "",
            }, clear=False),
            patch("paper_execution.ledger.PaperLedger", NeverConstructLedger),
        ):
            result = run_once(self.config_path, self.bundle_path, now_ms=NOW)
        self.assertEqual(result["runStatus"], "INPUT_REJECTED")

    def test_non_object_bundle_is_rejected_without_crashing(self):
        self.bundle_path.write_text('["not-an-object"]', encoding="utf-8")
        result, created = self.run_patched(producer_report())
        self.assertEqual(result["runStatus"], "INPUT_REJECTED")
        self.assertEqual(len(created), 0)

    def test_bundle_json_duplicate_keys_are_rejected(self):
        self.bundle_path.write_text('{"contract":"x","contract":"y"}', encoding="utf-8")
        result, created = self.run_patched(producer_report())
        self.assertEqual(result["runStatus"], "INPUT_REJECTED")
        self.assertEqual(len(created), 0)



    def test_intent_prepared_callback_runs_before_paper_ledger_submit(self):
        events = []
        class OrderedLedger:
            def __init__(self, *args, **kwargs):
                pass
            def submit(self, intent, *args, **kwargs):
                events.append(("submit", intent["intentId"]))
                return {"orderId": "paper-order-ordered",
                        "reservationId": "reservation-ordered", "status": "FILLED"}

        def on_intent_prepared(intent):
            events.append(("prepared", intent["intentId"]))

        with (
            patch("core_runtime.one_shot._preflight", return_value={"status": "PREFLIGHT_PASS", "riskReady": True}),
            patch("paper_execution.ledger.read_account_risk_snapshot",
                  return_value=self.bundle["accountRisk"]["snapshot"]),
            patch("paper_execution.ledger.read_snapshot", return_value=self.paper_state),
            patch("pipeline.core_strategy.produce", return_value=producer_report()),
            patch("paper_execution.ledger.PaperLedger", OrderedLedger),
        ):
            result = run_once(self.config_path, self.bundle_path, now_ms=NOW,
                              on_intent_prepared=on_intent_prepared)

        self.assertEqual(result["runStatus"], "PAPER_ACCEPTED", result)
        self.assertEqual([event[0] for event in events], ["prepared", "submit"])
        self.assertEqual(events[0][1], events[1][1])

    def test_intent_prepared_callback_failure_aborts_before_ledger_submit(self):
        class NeverConstructLedger:
            def __init__(self, *args, **kwargs):
                raise AssertionError("Ledger must not be constructed after journal failure")

        def fail_journal(_intent):
            raise OSError("journal unavailable")

        with (
            patch("core_runtime.one_shot._preflight", return_value={"status": "PREFLIGHT_PASS", "riskReady": True}),
            patch("paper_execution.ledger.read_account_risk_snapshot",
                  return_value=self.bundle["accountRisk"]["snapshot"]),
            patch("paper_execution.ledger.read_snapshot", return_value=self.paper_state),
            patch("pipeline.core_strategy.produce", return_value=producer_report()),
            patch("paper_execution.ledger.PaperLedger", NeverConstructLedger),
        ):
            result = run_once(self.config_path, self.bundle_path, now_ms=NOW,
                              on_intent_prepared=fail_journal)

        self.assertEqual(result["runStatus"], "RUN_FAILED")
        self.assertEqual(result["reasonCode"], "INTENT_PREPARE_CALLBACK_FAILED")

    def test_missing_intent_prepared_callback_preserves_one_shot_behavior(self):
        result, created = self.run_patched(producer_report())
        self.assertEqual(result["runStatus"], "PAPER_ACCEPTED", result)
        self.assertEqual(len(created), 1)
        self.assertEqual(created[0].submit_calls, 1)

if __name__ == "__main__":
    unittest.main()
