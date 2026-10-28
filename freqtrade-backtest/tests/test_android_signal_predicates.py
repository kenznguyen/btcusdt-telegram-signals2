import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from android_signal_predicates import entry_side


class EntryParityPredicateTests(unittest.TestCase):
    def test_long_rsi_cross_and_h1_trend(self):
        self.assertEqual("LONG", entry_side(30, 31, 25, 15, 21))

    def test_short_rsi_cross_and_h1_trend(self):
        self.assertEqual("SHORT", entry_side(70, 69, 15, 25, 21))

    def test_rsi_must_cross_not_just_be_above(self):
        self.assertIsNone(entry_side(31, 32, 25, 15, 21))

    def test_adx_boundary_is_strict(self):
        self.assertIsNone(entry_side(30, 31, 25, 15, 20))

    def test_di_tie_blocks_entry(self):
        self.assertIsNone(entry_side(30, 31, 20, 20, 25))

    def test_missing_prior_h1_indicators_blocks_entry(self):
        self.assertIsNone(entry_side(30, 31, None, None, None))

    def test_long_threshold_requires_cross_above(self):
        self.assertIsNone(entry_side(30, 30, 25, 15, 21))

    def test_short_threshold_requires_cross_below(self):
        self.assertIsNone(entry_side(70, 70, 15, 25, 21))


if __name__ == "__main__":
    unittest.main()
