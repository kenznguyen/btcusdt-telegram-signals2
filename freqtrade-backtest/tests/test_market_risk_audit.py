"""Liquidation accounting contract; no conjectured maintenance margin."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from market_risk_audit import audit_liquidations

class LiquidationAuditTest(unittest.TestCase):
    def test_short_liquidation_occurs_before_recorded_stop(self):
        trade = {
            "pair": "BTC/USDT:USDT", "exit_reason": "liquidation", "is_short": True,
            "open_date": "2026-02-24 15:45:00+00:00",
            "close_date": "2026-02-25 16:45:00+00:00",
            "open_rate": 63716.1, "close_rate": 68080.3,
            "stop_loss_abs": 68127.2, "profit_abs": -81.9568167,
            "funding_fees": 0.0,
        }
        item = audit_liquidations([trade])[0]
        self.assertTrue(item["liquidation_before_stop"])
        self.assertAlmostEqual(item["liquidation_minus_stop_price"], -46.9)
        self.assertFalse(item["liquidation_formula_verified"])

    def test_no_liquidation_event(self):
        self.assertEqual([], audit_liquidations([{"exit_reason": "tp"}]))

if __name__ == "__main__":
    unittest.main()
