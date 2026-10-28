"""Window partitioning remains chronological and non-overlapping."""
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from walkforward_windows import make_windows


class WalkforwardWindowsTest(unittest.TestCase):
    def test_three_consecutive_windows_cover_exactly_360_days(self):
        windows = make_windows(datetime(2026, 10, 28, tzinfo=timezone.utc))
        self.assertEqual(3, len(windows))
        self.assertEqual(["20251102-20260302", "20260302-20260630", "20260630-20261028"],
                         [w["timerange"] for w in windows])
        self.assertEqual(windows[0]["end_exclusive_utc"], windows[1]["start_utc"])
        self.assertEqual(windows[1]["end_exclusive_utc"], windows[2]["start_utc"])
        self.assertTrue(all(not w["training_or_reoptimization"] for w in windows))

    def test_no_naive_timestamp(self):
        with self.assertRaises(ValueError):
            make_windows(datetime(2026, 10, 28))


if __name__ == "__main__":
    unittest.main()
