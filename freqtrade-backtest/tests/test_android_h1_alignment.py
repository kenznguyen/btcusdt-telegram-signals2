import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from android_h1_alignment import prior_h1_for_m15, aligned_indicators, HOUR_MS


def h1(hour, **values):
    return {"timestamp_ms": hour * HOUR_MS, "closed": True,
            "plus_di": 25, "minus_di": 15, "adx": 30, **values}


class H1AlignmentTests(unittest.TestCase):
    def test_same_hour_h1_is_never_used(self):
        hours = [h1(1), h1(2)]
        self.assertEqual(1 * HOUR_MS,
                         prior_h1_for_m15(2 * HOUR_MS + 900000, hours)["timestamp_ms"])

    def test_missing_prior_hour_blocks_entry(self):
        result = aligned_indicators(0, [h1(0)])
        self.assertIsNone(result["h1_adx"])

    def test_uses_latest_prior_hour(self):
        result = aligned_indicators(3 * HOUR_MS + 1800000, [h1(0), h1(1), h1(2)])
        self.assertEqual(30, result["h1_adx"])

    def test_rejects_unclosed_h1(self):
        with self.assertRaises(ValueError):
            prior_h1_for_m15(2 * HOUR_MS, [{"timestamp_ms": HOUR_MS, "closed": False}])

    def test_rejects_duplicate_hour(self):
        with self.assertRaises(ValueError):
            prior_h1_for_m15(3 * HOUR_MS, [h1(1), h1(1)])


if __name__ == "__main__":
    unittest.main()
