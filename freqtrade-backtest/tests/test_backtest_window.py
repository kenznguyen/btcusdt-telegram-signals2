import sys
import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backtest_window import build_window, check_candle_window


class BacktestWindowTest(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 10, 28, 9, 0, tzinfo=timezone.utc)

    def test_180_days_with_warmup(self):
        window = build_window(180, self.now)
        self.assertEqual(window["days"], 180)
        self.assertEqual(window["download_days"], 187)
        self.assertEqual(window["start"], "20260501")
        self.assertEqual(window["end_exclusive"], "20261029")

    def test_supported_windows(self):
        for days in (90, 180, 360):
            self.assertEqual(build_window(days, self.now)["days"], days)

    def test_reject_unsupported_window(self):
        with self.assertRaises(ValueError):
            build_window(45, self.now)

    def test_reject_short_history(self):
        w = build_window(90, self.now)
        recent = [self.now - timedelta(days=i) for i in range(30)]
        with self.assertRaisesRegex(ValueError, "insufficient"):
            check_candle_window(recent, w, "15m")

    def test_accept_sufficient_coverage(self):
        w = build_window(90, self.now)
        dates = [w["start_time"] - timedelta(days=7),
                 self.now - timedelta(minutes=15)]
        result = check_candle_window(dates, w, "15m")
        self.assertEqual(result["days_requested"], 90)
        self.assertTrue(result["coverage_ok"])

    def test_reject_stale_history(self):
        w = build_window(90, self.now)
        dates = [w["start_time"] - timedelta(days=5),
                 self.now - timedelta(days=7)]
        with self.assertRaisesRegex(ValueError, "stale"):
            check_candle_window(dates, w, "1h")


if __name__ == "__main__":
    unittest.main()
