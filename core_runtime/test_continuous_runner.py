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
        changed["createdAtMs"] += 1
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
