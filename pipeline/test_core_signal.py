import unittest

from pipeline.core_signal import validate


class StrategyCoreSignalTest(unittest.TestCase):
    def setUp(self):
        self.now = 1_800_000_000_000
        self.report = {
            "schemaVersion": 1, "source": "STRATEGY_CORE",
            "exchange": "binance", "marketType": "USDT_PERPETUAL",
            "symbol": "BTCUSDT", "timeframe": "15m", "action": "LONG",
            "reason": "RSI_ADX_ENTRY", "strategyVersion": "rsi-adx-smart-dca-v1",
            "datasetVersion": "sha256:" + "a" * 64, "inputSnapshotId": "sha256:" + "b" * 64,
            "decisionAtMs": self.now - 1000, "validUntilMs": self.now + 20_000,
            "targetPositionBase": "0.001", "limitPrice": "65000",
        }

    def test_core_long_signal_is_independent_and_becomes_paper_intent(self):
        result = validate(self.report, self.now)
        self.assertEqual(result["action"], "BUY")
        self.assertEqual(result["source"], "STRATEGY_CORE")
        self.assertEqual(result["intent"]["modelVersion"], "strategy-core")
        self.assertEqual(result["intent"]["targetPositionBase"], "0.001")

    def test_core_short_signal_is_normalized_to_sell(self):
        report = {**self.report, "action": "SHORT", "targetPositionBase": "-0.001"}
        self.assertEqual(validate(report, self.now)["action"], "SELL")

    def test_missing_or_stale_core_artifact_never_creates_intent(self):
        self.assertIsNone(validate(None, self.now)["intent"])
        stale = {**self.report, "validUntilMs": self.now - 1}
        result = validate(stale, self.now)
        self.assertEqual(result["action"], "WAIT")
        self.assertIsNone(result["intent"])

    def test_core_source_market_and_direction_are_validated(self):
        for change in ({"source": "AI"}, {"symbol": "ETHUSDT"},
                       {"action": "LONG", "targetPositionBase": "-0.001"},
                       {"limitPrice": "NaN"}):
            result = validate({**self.report, **change}, self.now)
            self.assertEqual(result["action"], "WAIT")
            self.assertIsNone(result["intent"])

    def test_wait_is_a_valid_independent_core_result(self):
        result = validate({**self.report, "action": "WAIT", "reason": "NO_ENTRY"}, self.now)
        self.assertEqual(result["reason"], "NO_ENTRY")
        self.assertIsNone(result["intent"])


if __name__ == "__main__":
    unittest.main()
