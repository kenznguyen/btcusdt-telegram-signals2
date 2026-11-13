"""RED-first integration contracts for Continuous Core orchestration."""

import json
from pathlib import Path
import tempfile
import unittest

from core_runtime.continuous_journal import ContinuousJournal, CycleConflict
from core_runtime.continuous_runner import (
    ContinuousCoreRunner,
    ContinuousInputError,
    CycleNotReady,
)
from core_runtime.input_bundle import compute_bundle_id
from core_runtime.test_input_bundle_contract import valid_bundle


NOW = 1_800_000_000_000


class ContinuousCoreRunnerTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.journal = ContinuousJournal(root / "runner-state.sqlite3")
        self.bundle_dir = root / "immutable-bundles"
        self.config = root / "paper-config.json"
        self.config.write_text(json.dumps({
            "mode": "PAPER",
            "ai_execution_enabled": False,
            "ledger_path": str(root / "paper-ledger.sqlite3"),
        }), encoding="utf-8")
        self.bundle = valid_bundle()
        self.bundle_path = root / "input-bundle.json"
        self.write_bundle(self.bundle)
        self.calls = []
        self.audit_events = {"events": [], "nextBeforeId": None}
        self.runner = self.make_runner()

    def write_bundle(self, bundle):
        self.bundle_path.write_text(
            json.dumps(bundle, separators=(",", ":")), encoding="utf-8"
        )

    def fake_run_once(self, config_path, bundle_path, *, now_ms, on_intent_prepared):
        bundle = json.loads(Path(bundle_path).read_text(encoding="utf-8"))
        intent_id = "intent:" + bundle["bundleId"]
        self.calls.append((str(bundle_path), intent_id))
        on_intent_prepared({"intentId": intent_id})
        return {
            "runId": "core-run:" + bundle["bundleId"],
            "runStatus": "PAPER_ACCEPTED",
            "paperLedgerReference": {"orderId": "paper:" + bundle["bundleId"]},
        }

    def make_runner(self, *, run_once_fn=None, audit_reader=None, settlement_ms=0):
        return ContinuousCoreRunner(
            config_path=self.config,
            journal=self.journal,
            bundle_store_dir=self.bundle_dir,
            source_sha="source-sha",
            config_sha256="config-sha256",
            settlement_ms=settlement_ms,
            max_book_age_ms=5_000,
            run_once_fn=run_once_fn or self.fake_run_once,
            audit_reader=audit_reader or self.fake_audit_reader,
            preflight_fn=lambda *_args, **_kwargs: {"status": "PREFLIGHT_PASS"},
        )

    def fake_audit_reader(self, *_args, **_kwargs):
        return self.audit_events

    def test_process_bundle_persists_intent_before_one_shot_and_terminal_state(self):
        result = self.runner.process_bundle(self.bundle_path, now_ms=NOW)
        cycle = self.journal.get_cycle(result["cycleKey"])
        self.assertEqual(result["status"], "PAPER_ACCEPTED")
        self.assertEqual(cycle["status"], "PAPER_ACCEPTED")
        self.assertEqual(cycle["intentId"], "intent:" + self.bundle["bundleId"])
        self.assertEqual(cycle["orderId"], "paper:" + self.bundle["bundleId"])
        self.assertEqual(len(self.calls), 1)

    def test_duplicate_bundle_delivery_does_not_call_one_shot_twice(self):
        first = self.runner.process_bundle(self.bundle_path, now_ms=NOW)
        second = self.runner.process_bundle(self.bundle_path, now_ms=NOW)
        self.assertEqual(first["status"], "PAPER_ACCEPTED")
        self.assertEqual(second["status"], "DUPLICATE_CYCLE")
        self.assertEqual(len(self.calls), 1)

    def test_conflicting_bundle_for_same_cycle_fails_closed(self):
        self.runner.process_bundle(self.bundle_path, now_ms=NOW)
        changed = dict(self.bundle)
        changed["createdAtMs"] -= 1
        changed["bundleId"] = compute_bundle_id(changed)
        other_path = self.bundle_path.with_name("conflicting-bundle.json")
        other_path.write_text(json.dumps(changed), encoding="utf-8")
        with self.assertRaises(CycleConflict):
            self.runner.process_bundle(other_path, now_ms=NOW)
        self.assertEqual(len(self.calls), 1)

    def test_unsettled_or_invalid_bundle_is_not_claimed(self):
        delayed = self.make_runner(settlement_ms=30_000)
        with self.assertRaises(CycleNotReady):
            delayed.process_bundle(self.bundle_path, now_ms=NOW)
        invalid = dict(self.bundle)
        invalid["mode"] = "LIVE"
        self.write_bundle(invalid)
        with self.assertRaises(ContinuousInputError):
            self.runner.process_bundle(self.bundle_path, now_ms=NOW)
        self.assertEqual(self.journal.list_cycles(), [])
        self.assertEqual(self.calls, [])

    def test_risk_rejection_is_terminal_without_fallback_or_retry(self):
        def rejected(config_path, bundle_path, *, now_ms, on_intent_prepared):
            bundle = json.loads(Path(bundle_path).read_text(encoding="utf-8"))
            on_intent_prepared({"intentId": "intent:" + bundle["bundleId"]})
            self.calls.append("risk-rejected")
            return {
                "runId": "core-run:rejected",
                "runStatus": "RISK_REJECTED",
                "paperLedgerReference": {"orderId": "paper:rejected"},
                "reasonCode": "KILL_SWITCH",
            }

        runner = self.make_runner(run_once_fn=rejected)
        result = runner.process_bundle(self.bundle_path, now_ms=NOW)
        self.assertEqual(result["status"], "RISK_REJECTED")
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(self.journal.get_cycle(result["cycleKey"])["status"],
                         "RISK_REJECTED")

    def test_crash_after_ledger_commit_is_reconciled_without_resubmission(self):
        def crash_after_intent(config_path, bundle_path, *, now_ms, on_intent_prepared):
            bundle = json.loads(Path(bundle_path).read_text(encoding="utf-8"))
            on_intent_prepared({"intentId": "intent:" + bundle["bundleId"]})
            self.calls.append("submitted")
            raise RuntimeError("injected crash after ledger commit")

        runner = self.make_runner(run_once_fn=crash_after_intent)
        interrupted = runner.process_bundle(self.bundle_path, now_ms=NOW)
        self.assertEqual(interrupted["status"], "UNKNOWN_REQUIRES_RECONCILIATION")
        cycle_key = interrupted["cycleKey"]
        intent_id = self.journal.get_cycle(cycle_key)["intentId"]
        self.audit_events = {
            "events": [{
                "id": 7,
                "atMs": NOW,
                "kind": "SUBMIT",
                "document": {
                    "intentId": intent_id,
                    "orderId": "paper:recovered",
                    "status": "FILLED",
                },
            }],
            "nextBeforeId": None,
        }
        recovered = runner.recover_incomplete(now_ms=NOW + 1)
        self.assertEqual(recovered[0]["status"], "PAPER_ACCEPTED")
        self.assertEqual(self.journal.get_cycle(cycle_key)["orderId"], "paper:recovered")
        self.assertEqual(self.calls, ["submitted"])

    def test_unreadable_ledger_blocks_recovery_without_replay(self):
        def crash_after_intent(config_path, bundle_path, *, now_ms, on_intent_prepared):
            bundle = json.loads(Path(bundle_path).read_text(encoding="utf-8"))
            on_intent_prepared({"intentId": "intent:" + bundle["bundleId"]})
            self.calls.append("attempt")
            raise RuntimeError("unknown submit outcome")

        runner = self.make_runner(
            run_once_fn=crash_after_intent,
            audit_reader=lambda *_args, **_kwargs: (_ for _ in ()).throw(
                OSError("ledger unavailable")
            ),
        )
        interrupted = runner.process_bundle(self.bundle_path, now_ms=NOW)
        self.assertEqual(interrupted["status"], "UNKNOWN_REQUIRES_RECONCILIATION")
        recovered = runner.recover_incomplete(now_ms=NOW + 1)
        self.assertEqual(recovered[0]["status"], "BLOCKED")
        self.assertEqual(self.calls, ["attempt"])


    def test_actual_paperledger_commit_is_reconciled_after_simulated_crash(self):
        import os
        from unittest.mock import patch

        import paper_execution.test_core_first_operational as operational
        from core_runtime.input_bundle import compute_bundle_id
        from core_runtime.one_shot import run_once
        from core_runtime.test_input_bundle_contract import valid_bundle
        from paper_execution.ledger import read_account_risk_snapshot, read_snapshot
        from pipeline.test_core_runtime_one_shot import producer_report

        fixture = operational.CoreFirstOperationalProofTest()
        fixture.setUp()
        try:
            bundle = valid_bundle()
            risk = read_account_risk_snapshot(fixture.path, now_ms=fixture.now)
            bundle["accountRisk"]["snapshot"] = risk
            bundle["accountRisk"]["snapshotDigest"] = (
                "sha256:" + __import__("hashlib").sha256(
                    __import__("rfc8785").dumps(risk)
                ).hexdigest()
            )
            paper = read_snapshot(fixture.path, strategy_id="STRATEGY_CORE")
            bundle["paperState"] = {
                "positionBase": paper["positionBase"],
                "averageEntryPrice": paper["averageEntryPrice"],
                "strategyState": {
                    "owner": paper["strategyState"]["owner"],
                    "dcaUsed": paper["strategyState"]["dcaUsed"],
                    "strategyId": "STRATEGY_CORE",
                },
            }
            bundle["bundleId"] = compute_bundle_id(bundle)
            root = Path(fixture.temp.name)
            config_path = root / "continuous-paper-config.json"
            bundle_path = root / "continuous-bundle-v1.json"
            config_path.write_text(json.dumps({
                "mode": "PAPER",
                "ai_execution_enabled": False,
                "ledger_path": str(fixture.path),
                "risk_limits": {
                    "maxDrawdownPct": "50",
                    "maxDailyLossUsdt": "50",
                    "maxExposureUsdt": "1000",
                },
                "max_book_age_ms": 2_000,
                "max_position_base": "0.01",
            }), encoding="utf-8")
            bundle_path.write_text(json.dumps(bundle), encoding="utf-8")
            calls = []

            def crash_after_commit(config, stored_bundle, *, now_ms, on_intent_prepared):
                result = run_once(
                    config, stored_bundle, now_ms=now_ms,
                    on_intent_prepared=on_intent_prepared,
                )
                self.assertEqual(result["runStatus"], "PAPER_ACCEPTED", result)
                calls.append(result)
                raise RuntimeError("simulated process crash after committed PaperLedger submit")

            runner = ContinuousCoreRunner(
                config_path=config_path,
                journal=ContinuousJournal(root / "continuous-journal.sqlite3"),
                bundle_store_dir=root / "immutable-bundles",
                source_sha="source-sha",
                config_sha256="config-sha256",
                settlement_ms=0,
                max_book_age_ms=2_000,
                run_once_fn=crash_after_commit,
                preflight_fn=lambda *_args, **_kwargs: {"status": "PREFLIGHT_PASS"},
            )
            with patch.dict(os.environ, {
                "AI_EXECUTION_ENABLED": "false",
                "MARKET_DATA_DB": "",
                "BINANCE_API_KEY": "",
                "BINANCE_API_SECRET": "",
                "OKX_API_KEY": "",
                "OKX_API_SECRET": "",
            }, clear=False), patch(
                "pipeline.core_strategy.produce", return_value=producer_report()
            ):
                interrupted = runner.process_bundle(bundle_path, now_ms=fixture.now)
                self.assertEqual(interrupted["status"], "UNKNOWN_REQUIRES_RECONCILIATION")
                recovered = runner.recover_incomplete(now_ms=fixture.now + 1)

            self.assertEqual(recovered[0]["status"], "PAPER_ACCEPTED")
            self.assertEqual(len(calls), 1)
            self.assertEqual(len(fixture.core.snapshot()["orders"]), 1)
            self.assertEqual(fixture.core.snapshot()["positionBase"], "0.0001")
            self.assertEqual(fixture.ai.snapshot()["positionBase"], "0")
            self.assertEqual(len(fixture.ai.snapshot()["orders"]), 0)
        finally:
            fixture.doCleanups()

    def test_delayed_scheduler_wake_selects_latest_eligible_closed_candle(self):
        delayed_now = NOW + 900_000
        wall_values = iter([NOW, NOW, delayed_now])
        monotonic_value = [1.0]
        requested = []
        stop = [False]

        def provider(candle_open):
            requested.append(candle_open)
            stop[0] = True
            return None

        result = self.runner.run_forever(
            bundle_provider=provider,
            wall_clock_ms=lambda: next(wall_values),
            monotonic=lambda: monotonic_value[0],
            sleep=lambda seconds: monotonic_value.__setitem__(
                0, monotonic_value[0] + seconds
            ),
            stop_requested=lambda: stop[0],
            max_sleep_seconds=1_000,
        )
        self.assertEqual(result, "STOPPED")
        self.assertEqual(requested, [NOW])

    def test_stop_requested_during_execution_allows_current_cycle_to_finish(self):
        holder = {}

        def stop_after_intent(config_path, bundle_path, *, now_ms, on_intent_prepared):
            bundle = json.loads(Path(bundle_path).read_text(encoding="utf-8"))
            on_intent_prepared({"intentId": "intent:" + bundle["bundleId"]})
            holder["runner"].request_stop()
            return {
                "runId": "core-run:stopped",
                "runStatus": "PAPER_ACCEPTED",
                "paperLedgerReference": {"orderId": "paper:stopped"},
            }

        runner = self.make_runner(run_once_fn=stop_after_intent)
        holder["runner"] = runner
        result = runner.process_bundle(self.bundle_path, now_ms=NOW)
        self.assertEqual(result["status"], "PAPER_ACCEPTED")
        self.assertEqual(self.journal.get_cycle(result["cycleKey"])["status"],
                         "PAPER_ACCEPTED")
        provider_calls = []
        stopped = runner.run_forever(
            bundle_provider=lambda candle_open: provider_calls.append(candle_open),
            wall_clock_ms=lambda: NOW,
            monotonic=lambda: 1.0,
            sleep=lambda _seconds: None,
            stop_requested=lambda: False,
        )
        self.assertEqual(stopped, "STOPPED")
        self.assertEqual(provider_calls, [])

    def test_ai_execution_environment_override_blocks_before_cycle_claim(self):
        import os
        from core_runtime.preflight import PreflightError, _preflight
        from unittest.mock import patch

        runner = ContinuousCoreRunner(
            config_path=self.config,
            journal=self.journal,
            bundle_store_dir=self.bundle_dir,
            source_sha="source-sha",
            config_sha256="config-sha256",
            settlement_ms=0,
            run_once_fn=self.fake_run_once,
            audit_reader=self.fake_audit_reader,
            preflight_fn=_preflight,
        )
        with patch.dict(os.environ, {
            "AI_EXECUTION_ENABLED": "true",
            "BINANCE_API_KEY": "",
            "BINANCE_API_SECRET": "",
            "OKX_API_KEY": "",
            "OKX_API_SECRET": "",
        }, clear=False):
            with self.assertRaises(PreflightError):
                runner.process_bundle(self.bundle_path, now_ms=NOW)
        self.assertEqual(self.journal.list_cycles(), [])
        self.assertEqual(self.calls, [])

    def test_stop_during_cadence_wait_does_not_request_or_claim_bundle(self):
        requested = []
        result = self.runner.run_forever(
            bundle_provider=lambda candle_open: requested.append(candle_open),
            wall_clock_ms=lambda: NOW,
            monotonic=lambda: 1.0,
            sleep=lambda _seconds: None,
            stop_requested=lambda: True,
        )
        self.assertEqual(result, "STOPPED")
        self.assertEqual(requested, [])
        self.assertEqual(self.journal.list_cycles(), [])


if __name__ == "__main__":
    unittest.main()
