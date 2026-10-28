"""ENTRY parity edge cases: threshold crossing and closed H1 confirmation.

These are predicate-level tests; they do not certify a complete OHLC replay.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from android_signal_predicates import entry_side
from android_h1_alignment import aligned_indicators, HOUR_MS


class EntryBoundaryTests(unittest.TestCase):
    def test_long_requires_cross_above_thirty(self):
        self.assertEqual("LONG", entry_side(30.0, 30.0001, 25.0, 10.0, 21.0))
        self.assertIsNone(entry_side(30.0, 30.0, 25.0, 10.0, 21.0))
        self.assertIsNone(entry_side(31.0, 32.0, 25.0, 10.0, 21.0))

    def test_short_requires_cross_below_seventy(self):
        self.assertEqual("SHORT", entry_side(70.0, 69.9999, 10.0, 25.0, 21.0))
        self.assertIsNone(entry_side(70.0, 70.0, 10.0, 25.0, 21.0))
        self.assertIsNone(entry_side(69.0, 68.0, 10.0, 25.0, 21.0))

    def test_h1_adx_must_exceed_twenty(self):
        self.assertIsNone(entry_side(30, 31, 25, 10, 20))
        self.assertEqual("LONG", entry_side(30, 31, 25, 10, 20.0001))

    def test_h1_di_must_have_strict_direction(self):
        self.assertIsNone(entry_side(30, 31, 20, 20, 40))
        self.assertIsNone(entry_side(70, 69, 20, 20, 40))

    def test_current_hour_is_excluded_even_if_marked_closed(self):
        h1 = [
            {"timestamp_ms": 0, "closed": True, "plus_di": 10, "minus_di": 30, "adx": 30},
            {"timestamp_ms": HOUR_MS, "closed": True, "plus_di": 30, "minus_di": 10, "adx": 30},
        ]
        aligned = aligned_indicators(HOUR_MS + 900000, h1)
        self.assertEqual(10, aligned["h1_plus_di"])
        self.assertIsNone(entry_side(30, 31, aligned["h1_plus_di"],
                                     aligned["h1_minus_di"], aligned["h1_adx"]))


if __name__ == "__main__":
    unittest.main()
