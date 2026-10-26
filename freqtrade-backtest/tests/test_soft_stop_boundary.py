"""Verify Soft SL priority, H1 reversal, two bearish candles and accounting.

Predicate-level deterministic scenario; no market data or orders.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from android_signal_predicates import (
    entry_position, exit_reason, threshold_price, stop_fill_price,
    closed_trade_accounting, roe_for,
)


class SoftStopBoundaryTests(unittest.TestCase):
    def test_long_soft_stop_requires_h1_reversal_and_two_red_candles(self):
        pos = entry_position(100.0, "LONG", 100.0, 0)
        entry = pos["avg_entry"]
        low = threshold_price("LONG", entry, -35) - 0.01
        close = low + 0.005
        roe = roe_for("LONG", entry, close)
        args = dict(side="LONG", low=low, high=entry,
                    candle_open=entry, candle_close=close,
                    previous_open=entry + 0.5, previous_close=entry,
                    h1_plus_di=10.0, h1_minus_di=30.0, h1_adx=40.0,
                    avg_entry=entry, rsi=50.0, roe_pct=roe)
        self.assertEqual("SOFT_SL", exit_reason(**args))
        self.assertIsNone(exit_reason(**{**args, "h1_adx": 35.0}))
        self.assertIsNone(exit_reason(**{**args, "h1_plus_di": 35.0}))
        self.assertIsNone(exit_reason(**{**args, "previous_close": entry + 1.0}))
        self.assertIsNone(exit_reason(**{**args, "low": entry}))
        threshold = threshold_price("LONG", entry, -35)
        fill = stop_fill_price("LONG", threshold, entry)
        self.assertLess(fill, threshold)
        pnl = closed_trade_accounting(
            "LONG", pos["qty"], entry, pos["entry_notional"], fill)
        self.assertGreater(pnl["fees"], 0)
        self.assertLess(pnl["net_pnl"], 0)


if __name__ == "__main__":
    unittest.main()
