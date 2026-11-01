"""P1.2 contract tests: gap planning and recovery boundaries."""
import unittest
from market_data.store import INTERVAL_MS
from market_data.feeder import RecoveryPlanner

BASE = 1_800_000_000_000
STEP = INTERVAL_MS["15m"]


class RecoveryPlannerContractTest(unittest.TestCase):
    def setUp(self):
        self.planner = RecoveryPlanner()

    def test_complete_coverage_needs_no_recovery(self):
        coverage = {"startMs": BASE, "endMs": BASE + 2 * STEP,
                    "coverage": {"complete": True, "gaps": []}}
        self.assertEqual(self.planner.plan("15m", coverage), [])

    def test_each_reported_gap_becomes_an_aligned_window(self):
        coverage = {"startMs": BASE, "endMs": BASE + 4 * STEP,
                    "coverage": {"complete": False, "gaps": [
                        {"startMs": BASE + STEP, "endMs": BASE + 3 * STEP}
                    ]}}
        self.assertEqual(self.planner.plan("15m", coverage),
                         [(BASE + STEP, BASE + 3 * STEP)])

    def test_unaligned_or_out_of_range_gap_is_rejected(self):
        for gap in ({"startMs": BASE + 1, "endMs": BASE + STEP},
                    {"startMs": BASE + STEP, "endMs": BASE}):
            coverage = {"startMs": BASE, "endMs": BASE + 2 * STEP,
                        "coverage": {"complete": False, "gaps": [gap]}}
            with self.subTest(gap=gap), self.assertRaises(ValueError):
                self.planner.plan("15m", coverage)

    def test_repeated_planning_is_deterministic_until_store_is_rechecked(self):
        coverage = {"startMs": BASE, "endMs": BASE + 2 * STEP,
                    "coverage": {"complete": False, "gaps": [
                        {"startMs": BASE, "endMs": BASE + STEP}
                    ]}}
        expected = [(BASE, BASE + STEP)]
        self.assertEqual(self.planner.plan("15m", coverage), expected)
        self.assertEqual(self.planner.plan("15m", coverage), expected)

    def test_unsupported_timeframe_fails_closed(self):
        with self.assertRaises(ValueError):
            self.planner.plan("5m", {"coverage": {"complete": False, "gaps": []}})


if __name__ == "__main__":
    unittest.main()
