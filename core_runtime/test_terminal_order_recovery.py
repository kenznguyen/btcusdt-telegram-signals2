"""Recovery contracts for terminal PaperLedger order lifecycle states."""

import unittest

from core_runtime.test_continuous_runner import ContinuousCoreRunnerTest


class TerminalOrderRecoveryTest(unittest.TestCase):
    def _assert_terminal_order_is_reconciled(self, order_status):
        fixture = ContinuousCoreRunnerTest()
        fixture.setUp()
        try:
            result = fixture.runner.process_bundle(fixture.bundle_path, now_ms=fixture.NOW if hasattr(fixture, "NOW") else 1_800_000_000_000)
            cycle = fixture.journal.get_cycle(result["cycleKey"])
            self.assertEqual(cycle["status"], "PAPER_ACCEPTED")
            self.assertTrue(cycle["intentId"])
            self.assertTrue(cycle["orderId"])

            fixture.audit_events = {
                "events": [{
                    "id": 11,
                    "atMs": 1_800_000_000_001,
                    "kind": "ORDER_UPDATE",
                    "document": {
                        "intentId": cycle["intentId"],
                        "orderId": cycle["orderId"],
                        "status": order_status,
                    },
                }],
                "nextBeforeId": None,
            }

            recovered = fixture.runner.recover_incomplete(now_ms=1_800_000_000_002)
            self.assertEqual(recovered, [{
                "cycleKey": cycle["cycleKey"],
                "status": "VERIFIED",
            }])
            persisted = fixture.journal.get_cycle(cycle["cycleKey"])
            self.assertEqual(persisted["status"], "PAPER_ACCEPTED")
            self.assertEqual(persisted["orderId"], cycle["orderId"])
            self.assertEqual(fixture.calls, [(str(fixture.bundle_dir / (fixture.bundle_path.read_bytes() and __import__("hashlib").sha256(fixture.bundle_path.read_bytes()).hexdigest() + ".json")), cycle["intentId"])])
        finally:
            fixture.doCleanups()

    def test_canceled_order_reconciles_as_terminal_after_restart(self):
        self._assert_terminal_order_is_reconciled("CANCELED")

    def test_expired_order_reconciles_as_terminal_after_restart(self):
        self._assert_terminal_order_is_reconciled("EXPIRED")


if __name__ == "__main__":
    unittest.main()
