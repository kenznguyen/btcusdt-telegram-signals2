"""No fabricated expected fills and reliable nearest-event matching."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from reconcile_fills import reconcile


class FillReconciliationTest(unittest.TestCase):
    def test_matched_stop_fill_has_signed_difference(self):
        trade = {"pair": "BTC/USDT:USDT", "is_short": False,
                 "open_timestamp": 1000, "close_timestamp": 4000,
                 "exit_reason": "soft_sl", "close_rate": 95.0, "orders": []}
        event = {"pair": "BTC/USDT:USDT", "side": "LONG", "reason": "SOFT_SL",
                 "callback_time": 3000, "android_expected_stop_fill": 97.0}
        row = reconcile([trade], [event])[0]
        self.assertEqual(row["expected_fill_price"], 97)
        self.assertEqual(row["actual_fill_price"], 95)
        self.assertEqual(row["fill_difference"], -2)
        self.assertTrue(row["trace_match"])

    def test_unmatched_does_not_invent_expected_price(self):
        trade = {"pair": "BTC/USDT:USDT", "is_short": True,
                 "open_timestamp": 1000, "close_timestamp": 4000,
                 "exit_reason": "stop_loss", "close_rate": 105, "orders": []}
        row = reconcile([trade], [])[0]
        self.assertIsNone(row["expected_fill_price"])
        self.assertIsNone(row["fill_difference"])
        self.assertEqual(row["actual_fill_price"], 105)

    def test_trace_from_different_trade_not_matched(self):
        trade = {"pair": "BTC/USDT:USDT", "is_short": True,
                 "open_timestamp": 5000, "close_timestamp": 7000,
                 "exit_reason": "soft_sl", "close_rate": 105, "orders": []}
        event = {"pair": "BTC/USDT:USDT", "side": "SHORT", "reason": "SOFT_SL",
                 "callback_time": 3000, "android_expected_stop_fill": 104}
        self.assertFalse(reconcile([trade], [event])[0]["trace_match"])


if __name__ == "__main__":
    unittest.main()
