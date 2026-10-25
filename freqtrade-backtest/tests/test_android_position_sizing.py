import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from android_signal_predicates import entry_position, dca_position


class PositionSizingTests(unittest.TestCase):
    def test_initial_margin_is_half_balance_without_cash_debit(self):
        position = entry_position(100, "LONG", 100, 900000)
        self.assertEqual(50, position["initial_margin"])
        self.assertAlmostEqual(650, position["entry_notional"])
        self.assertAlmostEqual(650 / 100.05, position["qty"])
        self.assertFalse(position["dca_used"])

    def test_dca_adds_same_margin_and_weighted_price_once(self):
        initial = entry_position(100, "LONG", 100, 900000)
        after = dca_position(initial, 100, 95)
        self.assertTrue(after["dca_used"])
        self.assertEqual(50, after["dca_margin"])
        self.assertAlmostEqual(1300, after["entry_notional"])
        self.assertGreater(after["qty"], initial["qty"])
        self.assertLess(after["avg_entry"], initial["avg_entry"])
        self.assertEqual(after, dca_position(after, 100, 90))

    def test_dca_is_blocked_when_reserved_margin_unavailable(self):
        initial = entry_position(100, "SHORT", 100, 900000)
        self.assertEqual(initial, dca_position(initial, 99, 95))

    def test_entry_rejects_invalid_side(self):
        with self.assertRaises(ValueError):
            entry_position(100, "FLAT", 100, 900000)


if __name__ == "__main__":
    unittest.main()
