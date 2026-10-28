import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from funding_timeline_audit import funding_ledger

class FundingTimelineAuditTest(unittest.TestCase):
    def test_dca_uses_only_fills_before_observation(self):
        trades = [
            {"open_timestamp": 0, "close_timestamp": 30000, "is_short": False,
             "funding_fees": -0.5, "orders": [
                {"ft_is_entry": True, "order_filled_timestamp": 0, "amount": 1},
                {"ft_is_entry": True, "order_filled_timestamp": 15000, "amount": 1}]},
            {"open_timestamp": 0, "close_timestamp": 30000, "is_short": True,
             "funding_fees": 0.5, "orders": [
                {"ft_is_entry": True, "order_filled_timestamp": 0, "amount": 1}]},
        ]
        funding = [{"timestamp_ms": 10000, "rate": .01},
                   {"timestamp_ms": 20000, "rate": .02}]
        mark = [{"timestamp_ms": 10000, "price": 100},
                {"timestamp_ms": 20000, "price": 110}]
        report = funding_ledger(trades, funding, mark)
        self.assertAlmostEqual(-5.4, report["per_trade"][0]["estimated_total_usdt"])
        self.assertAlmostEqual(3.2, report["per_trade"][1]["estimated_total_usdt"])
        self.assertEqual(4, len(report["events"]))
        self.assertFalse(report["funding_settlement_timestamps_verified"])

    def test_never_lookahead_mark(self):
        trades = [{"open_timestamp": 0, "close_timestamp": 30000,
                   "is_short": True, "funding_fees": 0,
                   "orders": [{"ft_is_entry": True, "order_filled_timestamp": 0, "amount": 1}]}]
        result = funding_ledger(trades, [{"timestamp_ms": 10000, "rate": .01}],
                                [{"timestamp_ms": 20000, "price": 100}])
        self.assertEqual([], result["events"])

if __name__ == "__main__":
    unittest.main()
