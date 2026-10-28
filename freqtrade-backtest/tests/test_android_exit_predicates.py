import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from android_signal_predicates import (
    take_profit_signal, dca_signal, emergency_stop_triggered,
    soft_stop_triggered, threshold_price,
)


class ExitPredicateTests(unittest.TestCase):
    def test_long_tp_requires_both_rsi_and_roe(self):
        self.assertTrue(take_profit_signal("LONG", 76, 5))
        self.assertFalse(take_profit_signal("LONG", 75.99, 5))
        self.assertFalse(take_profit_signal("LONG", 76, 4.99))

    def test_short_tp_is_symmetric(self):
        self.assertTrue(take_profit_signal("SHORT", 24, 5))
        self.assertFalse(take_profit_signal("SHORT", 25, 5))

    def test_long_dca_requires_adx_strict_and_rising_rsi(self):
        self.assertTrue(dca_signal("LONG", -20, 45.1, 22, 21))
        self.assertFalse(dca_signal("LONG", -20, 45, 22, 21))
        self.assertFalse(dca_signal("LONG", -20, 46, 22, 22))

    def test_short_dca_requires_falling_rsi(self):
        self.assertTrue(dca_signal("SHORT", -20, 46, 75, 76))
        self.assertFalse(dca_signal("SHORT", -19, 46, 75, 76))

    def test_emergency_stop_checks_intrabar_extremes(self):
        threshold = threshold_price("LONG", 100, -90)
        self.assertTrue(emergency_stop_triggered("LONG", threshold, 101, 100))
        self.assertFalse(emergency_stop_triggered("LONG", threshold + 0.01, 101, 100))
        short_threshold = threshold_price("SHORT", 100, -90)
        self.assertTrue(emergency_stop_triggered("SHORT", 99, short_threshold, 100))

    def test_soft_stop_needs_h1_reversal_and_two_bearish_candles(self):
        threshold = threshold_price("LONG", 100, -35)
        self.assertTrue(soft_stop_triggered("LONG", threshold, 101, 100, 99,
                                            101, 100, 15, 25, 36, 100))
        self.assertFalse(soft_stop_triggered("LONG", threshold, 101, 100, 99,
                                             101, 100, 15, 25, 35, 100))

    def test_invalid_side_is_rejected(self):
        with self.assertRaises(ValueError):
            threshold_price("FLAT", 100, -90)


if __name__ == "__main__":
    unittest.main()
