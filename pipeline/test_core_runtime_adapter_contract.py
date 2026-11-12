"""RED contract tests for the Core producer-to-validator adapter."""

import unittest


def adapt(report):
    from core_runtime.adapter import producer_report_to_signal
    return producer_report_to_signal(report)


def producer(action, intent_action=None):
    intent_action = intent_action or {"BUY": "LONG", "SELL": "SHORT", "CLOSE": "FLAT"}.get(action)
    intent = None if intent_action is None else {
        "schemaVersion": 1, "source": "STRATEGY_CORE", "exchange": "binance",
        "marketType": "USDT_PERPETUAL", "symbol": "BTCUSDT", "timeframe": "15m",
        "action": intent_action, "reason": "fixture",
        "strategyVersion": "rsi-adx-smart-dca-v1", "datasetVersion": "dataset-1",
        "inputSnapshotId": "snapshot-1", "decisionAtMs": 1000, "validUntilMs": 31000,
        "targetPositionBase": "0.01" if intent_action == "LONG" else
                              "-0.01" if intent_action == "SHORT" else "0",
        "limitPrice": "50000", "initialMarginQuote": "1", "candleOpenTimeMs": 0,
    }
    return {"action": action, "reason": "fixture-reason", "intent": intent}


class CoreProducerAdapterContractTest(unittest.TestCase):
    def test_buy_maps_to_long_and_copies_only_existing_provenance(self):
        result = adapt(producer("BUY"))
        self.assertEqual((result["schemaVersion"], result["source"], result["action"]),
                         (1, "STRATEGY_CORE", "LONG"))
        self.assertEqual(result["datasetVersion"], "dataset-1")
        self.assertEqual(result["inputSnapshotId"], "snapshot-1")
        self.assertEqual(result["targetPositionBase"], "0.01")
        self.assertEqual(result["limitPrice"], "50000")
        self.assertNotIn("initialMarginQuote", result)

    def test_sell_maps_to_short(self):
        result = adapt(producer("SELL"))
        self.assertEqual(result["action"], "SHORT")
        self.assertEqual(result["targetPositionBase"], "-0.01")

    def test_close_maps_to_flat(self):
        result = adapt(producer("CLOSE"))
        self.assertEqual(result["action"], "FLAT")
        self.assertEqual(result["targetPositionBase"], "0")

    def test_wait_preserves_reason_without_creating_intent(self):
        result = adapt({"action": "WAIT", "reason": "CORE_NO_ENTRY", "intent": None})
        self.assertEqual(result, {
            "schemaVersion": 1, "source": "STRATEGY_CORE",
            "action": "WAIT", "reason": "CORE_NO_ENTRY",
        })

    def test_action_disagreement_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "CORE_PRODUCER_ACTION_MISMATCH"):
            adapt(producer("BUY", "SHORT"))

    def test_missing_provenance_is_rejected_without_synthesis(self):
        report = producer("BUY")
        del report["intent"]["datasetVersion"]
        with self.assertRaisesRegex(ValueError, "CORE_PRODUCER_INTENT_INVALID"):
            adapt(report)


if __name__ == "__main__":
    unittest.main()
