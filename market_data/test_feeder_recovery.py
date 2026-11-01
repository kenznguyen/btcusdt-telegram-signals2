"""P1.2 contract tests: gap planning and recovery orchestration."""
import unittest
from unittest.mock import Mock

from market_data.store import INTERVAL_MS
from market_data.feeder import RecoveryPlanner, RecoveryCoordinator, RecoveryIncompleteError

BASE = 1_800_000_000_000
STEP = INTERVAL_MS["15m"]


def coverage(start, end, gaps=()):
    return {
        "startMs": start,
        "endMs": end,
        "coverage": {"complete": not gaps, "gaps": list(gaps)},
    }


class RecoveryPlannerContractTest(unittest.TestCase):
    def setUp(self):
        self.planner = RecoveryPlanner()

    def test_complete_coverage_needs_no_recovery(self):
        self.assertEqual(self.planner.plan(
            "15m", coverage(BASE, BASE + 2 * STEP)), [])

    def test_each_reported_gap_becomes_an_aligned_window(self):
        gaps = [{"startMs": BASE + STEP, "endMs": BASE + 3 * STEP}]
        self.assertEqual(
            self.planner.plan("15m", coverage(BASE, BASE + 4 * STEP, gaps)),
            [(BASE + STEP, BASE + 3 * STEP)],
        )

    def test_multiple_gaps_are_returned_in_chronological_order(self):
        gaps = [
            {"startMs": BASE + 3 * STEP, "endMs": BASE + 4 * STEP},
            {"startMs": BASE, "endMs": BASE + STEP},
        ]
        self.assertEqual(
            self.planner.plan("15m", coverage(BASE, BASE + 5 * STEP, gaps)),
            [(BASE, BASE + STEP), (BASE + 3 * STEP, BASE + 4 * STEP)],
        )

    def test_unaligned_or_out_of_range_gap_is_rejected(self):
        for gap in (
            {"startMs": BASE + 1, "endMs": BASE + STEP},
            {"startMs": BASE + STEP, "endMs": BASE},
            {"startMs": BASE - STEP, "endMs": BASE},
            {"startMs": BASE + STEP, "endMs": BASE + 3 * STEP},
        ):
            with self.subTest(gap=gap), self.assertRaises(ValueError):
                self.planner.plan("15m", coverage(BASE, BASE + 2 * STEP, [gap]))

    def test_unsupported_timeframe_fails_closed(self):
        with self.assertRaises(ValueError):
            self.planner.plan("5m", coverage(BASE, BASE + STEP))


class RecoveryCoordinatorContractTest(unittest.TestCase):
    def test_complete_store_coverage_does_not_call_sync(self):
        read = Mock(return_value=coverage(BASE, BASE + 2 * STEP))
        sync = Mock()
        coordinator = RecoveryCoordinator(sync_callback=sync, coverage_reader=read)
        result = coordinator.recover("15m", BASE, BASE + 2 * STEP)
        self.assertTrue(result.complete)
        sync.assert_not_called()

    def test_recovery_calls_sync_window_for_each_gap_then_rechecks_store(self):
        gaps = [
            {"startMs": BASE, "endMs": BASE + STEP},
            {"startMs": BASE + 2 * STEP, "endMs": BASE + 3 * STEP},
        ]
        read = Mock(side_effect=[
            coverage(BASE, BASE + 3 * STEP, gaps),
            coverage(BASE, BASE + 3 * STEP),
        ])
        sync = Mock()
        coordinator = RecoveryCoordinator(sync_callback=sync, coverage_reader=read)
        result = coordinator.recover("15m", BASE, BASE + 3 * STEP)
        self.assertTrue(result.complete)
        self.assertEqual(sync.call_args_list, [
            unittest.mock.call("15m", BASE, BASE + STEP),
            unittest.mock.call("15m", BASE + 2 * STEP, BASE + 3 * STEP),
        ])
        self.assertEqual(read.call_count, 2)

    def test_recovery_does_not_report_success_if_gaps_remain(self):
        gaps = [{"startMs": BASE, "endMs": BASE + STEP}]
        read = Mock(side_effect=[
            coverage(BASE, BASE + 2 * STEP, gaps),
            coverage(BASE, BASE + 2 * STEP, gaps),
        ])
        coordinator = RecoveryCoordinator(
            sync_callback=Mock(), coverage_reader=read)
        with self.assertRaises(RecoveryIncompleteError):
            coordinator.recover("15m", BASE, BASE + 2 * STEP)

    def test_sync_failure_propagates_and_never_marks_recovery_complete(self):
        gaps = [{"startMs": BASE, "endMs": BASE + STEP}]
        sync = Mock(side_effect=TimeoutError("upstream unavailable"))
        coordinator = RecoveryCoordinator(
            sync_callback=sync,
            coverage_reader=Mock(return_value=coverage(BASE, BASE + STEP, gaps)),
        )
        with self.assertRaisesRegex(TimeoutError, "upstream unavailable"):
            coordinator.recover("15m", BASE, BASE + STEP)

    def test_recovery_uses_only_the_injected_canonical_sync_callback(self):
        gaps = [{"startMs": BASE, "endMs": BASE + STEP}]
        sync = Mock()
        read = Mock(side_effect=[
            coverage(BASE, BASE + STEP, gaps),
            coverage(BASE, BASE + STEP),
        ])
        coordinator = RecoveryCoordinator(sync_callback=sync, coverage_reader=read)
        coordinator.recover("15m", BASE, BASE + STEP)
        self.assertEqual(sync.call_count, 1)


if __name__ == "__main__":
    unittest.main()
