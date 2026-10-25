import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from android_signal_predicates import (
    roe_for, execution_fill_price, stop_fill_price,
    closed_trade_accounting,
)


class ExecutionParityTests(unittest.TestCase):
    def test_long_and_short_roe(self):
        self.assertAlmostEqual(13.0, roe_for("LONG", 100, 101))
        self.assertAlmostEqual(13.0, roe_for("SHORT", 100, 99))

    def test_buy_sell_slippage(self):
        self.assertAlmostEqual(100.05, execution_fill_price(100, "BUY"))
        self.assertAlmostEqual(99.95, execution_fill_price(100, "SELL"))

    def test_long_stop_gap_uses_open(self):
        self.assertAlmostEqual(89.955, stop_fill_price("LONG", 95, 90))

    def test_short_stop_gap_uses_open(self):
        self.assertAlmostEqual(110.055, stop_fill_price("SHORT", 105, 110))

    def test_long_roundtrip_fees(self):
        result = closed_trade_accounting("LONG", 1, 100, 100, 110)
        self.assertAlmostEqual(10.0, result["gross"])
        self.assertAlmostEqual(0.105, result["fees"])
        self.assertAlmostEqual(9.895, result["net_pnl"])

    def test_short_roundtrip_fees(self):
        result = closed_trade_accounting("SHORT", 1, 100, 100, 90)
        self.assertAlmostEqual(10.0, result["gross"])
        self.assertAlmostEqual(0.095, result["fees"])
        self.assertAlmostEqual(9.905, result["net_pnl"])


if __name__ == "__main__":
    unittest.main()
