import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from export_freqtrade_events import export_events

class FreqtradeEventExportTest(unittest.TestCase):
    def test_dca_and_soft_stop_are_distinct(self):
        trade = {
            "is_short": True, "exit_reason": "soft_sl",
            "orders": [
                {"ft_is_entry": True, "order_filled_timestamp": 1000, "safe_price": 100, "amount": 1},
                {"ft_is_entry": True, "order_filled_timestamp": 2000, "safe_price": 105, "amount": 1},
                {"ft_is_entry": False, "order_filled_timestamp": 3000, "safe_price": 103, "amount": 2},
            ]
        }
        events = export_events([trade])
        self.assertEqual(["ENTRY", "DCA", "SOFT_SL"], [e["type"] for e in events])
        self.assertTrue(all(e["side"] == "SHORT" for e in events))

    def test_liquidation_not_labeled_emergency_stop(self):
        trade = {"is_short": False, "exit_reason": "liquidation",
                 "orders": [{"ft_is_entry": True, "order_filled_timestamp": 1, "safe_price": 100, "amount": 1},
                            {"ft_is_entry": False, "order_filled_timestamp": 2, "safe_price": 90, "amount": 1}]}
        self.assertEqual("LIQUIDATION", export_events([trade])[-1]["type"])

if __name__ == "__main__":
    unittest.main()
