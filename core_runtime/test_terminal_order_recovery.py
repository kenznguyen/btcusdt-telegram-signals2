"""Recovery contracts for terminal PaperLedger order lifecycle states."""

import unittest

from core_runtime.test_continuous_runner import ContinuousCoreRunnerTest


NOW = 1_800_000_000_000


class TerminalOrderRecoveryTest(unittest.TestCase):
    def _assert_terminal_order_is_reconciled(self, order_status):
        fixture = ContinuousCoreRunnerTest()
        fixture.setUp()
        try:
            result = fixture.runner.process_bundle(fixture.bundle_path, now_ms=NOW)
            cycle = fixture.journal.get_cycle(result["cycleKey"])
            self.assertEqual(cycle["status"], "PAPER_ACCEPTED")
            self.assertTrue(cycle["intentId"])
            self.assertTrue(cycle["orderId"])

            fixture.audit_events = {
                "events": [{
                    "id": 11,
                    "atMs": NOW + 1,
                    "kind": "ORDER_UPDATE",
                    "document": {
                        "intentId": cycle["intentId"],
                        "orderId": cycle["orderId"],
                        "status": order_status,
                    },
                }],
                "nextBeforeId": None,
            }

            recovered = fixture.runner.recover_incomplete(now_ms=NOW + 2)
            self.assertEqual(recovered, [{
                "cycleKey": cycle["cycleKey"],
                "status": "VERIFIED",
            }])
            persisted = fixture.journal.get_cycle(cycle["cycleKey"])
            self.assertEqual(persisted["status"], "PAPER_ACCEPTED")
            self.assertEqual(persisted["orderId"], cycle["orderId"])
            self.assertEqual(len(fixture.calls), 1)
        finally:
            fixture.doCleanups()

    def test_canceled_order_reconciles_as_terminal_after_restart(self):
        self._assert_terminal_order_is_reconciled("CANCELED")

    def test_expired_order_reconciles_as_terminal_after_restart(self):
        self._assert_terminal_order_is_reconciled("EXPIRED")

    def test_unknown_order_status_remains_blocked(self):
        fixture = ContinuousCoreRunnerTest()
        fixture.setUp()
        try:
            result = fixture.runner.process_bundle(fixture.bundle_path, now_ms=NOW)
            cycle = fixture.journal.get_cycle(result["cycleKey"])
            fixture.audit_events = {
                "events": [{
                    "id": 12,
                    "atMs": NOW + 1,
                    "kind": "ORDER_UPDATE",
                    "document": {
                        "intentId": cycle["intentId"],
                        "orderId": cycle["orderId"],
                        "status": "PENDING_UNKNOWN",
                    },
                }],
                "nextBeforeId": None,
            }
            recovered = fixture.runner.recover_incomplete(now_ms=NOW + 2)
            self.assertEqual(recovered[0]["status"], "BLOCKED")
            self.assertEqual(recovered[0]["reason"], "TERMINAL_LEDGER_DISAGREEMENT")
            self.assertEqual(fixture.journal.get_cycle(cycle["cycleKey"])["status"], "PAPER_ACCEPTED")
            self.assertEqual(len(fixture.calls), 1)
        finally:
            fixture.doCleanups()


    def _assert_interrupted_order_reconciles_without_replay(self, order_status):
        fixture = ContinuousCoreRunnerTest()
        fixture.setUp()
        calls = []
        try:
            def crash_after_intent(config_path, bundle_path, *, now_ms, on_intent_prepared):
                bundle = __import__("json").loads(
                    __import__("pathlib").Path(bundle_path).read_text(encoding="utf-8")
                )
                intent_id = "intent:" + bundle["bundleId"]
                on_intent_prepared({"intentId": intent_id})
                calls.append(intent_id)
                raise RuntimeError("simulated crash after ledger commit")

            runner = fixture.make_runner(run_once_fn=crash_after_intent)
            interrupted = runner.process_bundle(fixture.bundle_path, now_ms=NOW)
            self.assertEqual(interrupted["status"], "UNKNOWN_REQUIRES_RECONCILIATION")
            cycle = fixture.journal.get_cycle(interrupted["cycleKey"])
            order_id = "paper:terminal-" + order_status.lower()
            fixture.audit_events = {
                "events": [{
                    "id": 13,
                    "atMs": NOW + 1,
                    "kind": "ORDER_UPDATE",
                    "document": {
                        "intentId": cycle["intentId"],
                        "orderId": order_id,
                        "status": order_status,
                    },
                }],
                "nextBeforeId": None,
            }

            recovered = runner.recover_incomplete(now_ms=NOW + 2)

            self.assertEqual(recovered, [{
                "cycleKey": cycle["cycleKey"],
                "status": "PAPER_ACCEPTED",
            }])
            persisted = fixture.journal.get_cycle(cycle["cycleKey"])
            self.assertEqual(persisted["status"], "PAPER_ACCEPTED")
            self.assertEqual(persisted["orderId"], order_id)
            self.assertEqual(calls, [cycle["intentId"]])
        finally:
            fixture.doCleanups()

    def test_interrupted_cycle_reconciles_canceled_order_without_replay(self):
        self._assert_interrupted_order_reconciles_without_replay("CANCELED")

    def test_interrupted_cycle_reconciles_expired_order_without_replay(self):
        self._assert_interrupted_order_reconciles_without_replay("EXPIRED")


if __name__ == "__main__":
    unittest.main()
