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

    def test_overlapping_or_duplicate_gap_windows_are_rejected(self):
        overlapping = [
            {"startMs": BASE, "endMs": BASE + 2 * STEP},
            {"startMs": BASE + STEP, "endMs": BASE + 3 * STEP},
        ]
        duplicate = [
            {"startMs": BASE, "endMs": BASE + STEP},
            {"startMs": BASE, "endMs": BASE + STEP},
        ]
        for gaps in (overlapping, duplicate):
            with self.subTest(gaps=gaps), self.assertRaisesRegex(
                ValueError, "coverage gaps must not overlap"
            ):
                self.planner.plan("15m", coverage(BASE, BASE + 3 * STEP, gaps))

    def test_unsupported_timeframe_fails_closed(self):
        with self.assertRaises(ValueError):
            self.planner.plan("5m", coverage(BASE, BASE + STEP))

    def test_incomplete_coverage_without_reported_gaps_fails_closed(self):
        snapshot = coverage(BASE, BASE + 2 * STEP)
        snapshot["coverage"]["complete"] = False
        with self.assertRaisesRegex(ValueError, "coverage completeness contradicts reported gaps"):
            self.planner.plan("15m", snapshot)

    def test_complete_coverage_with_reported_gaps_fails_closed(self):
        snapshot = coverage(
            BASE, BASE + 2 * STEP,
            [{"startMs": BASE, "endMs": BASE + STEP}],
        )
        snapshot["coverage"]["complete"] = True
        with self.assertRaisesRegex(ValueError, "coverage completeness contradicts reported gaps"):
            self.planner.plan("15m", snapshot)

    def test_missing_coverage_completeness_flag_fails_closed(self):
        snapshot = coverage(BASE, BASE + 2 * STEP)
        del snapshot["coverage"]["complete"]
        with self.assertRaisesRegex(ValueError, "coverage completeness contradicts reported gaps"):
            self.planner.plan("15m", snapshot)

    def test_null_coverage_completeness_flag_fails_closed(self):
        snapshot = coverage(BASE, BASE + 2 * STEP)
        snapshot["coverage"]["complete"] = None
        with self.assertRaisesRegex(ValueError, "coverage completeness contradicts reported gaps"):
            self.planner.plan("15m", snapshot)

    def test_non_boolean_coverage_completeness_flag_fails_closed(self):
        for invalid in (0, 1, "false", "true"):
            with self.subTest(invalid=invalid):
                snapshot = coverage(BASE, BASE + 2 * STEP)
                snapshot["coverage"]["complete"] = invalid
                with self.assertRaisesRegex(ValueError, "coverage completeness contradicts reported gaps"):
                    self.planner.plan("15m", snapshot)


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

    def test_partial_multi_gap_recovery_never_reports_complete(self):
        gaps = [
            {"startMs": BASE, "endMs": BASE + STEP},
            {"startMs": BASE + 2 * STEP, "endMs": BASE + 3 * STEP},
        ]
        remaining = [gaps[1]]
        sync_calls = []

        def sync_one_gap(timeframe, start_ms, end_ms):
            sync_calls.append((timeframe, start_ms, end_ms))
            # The first gap is repaired; the second remains in authoritative recheck.
            return None

        read = Mock(side_effect=[
            coverage(BASE, BASE + 3 * STEP, gaps),
            coverage(BASE, BASE + 3 * STEP, remaining),
        ])
        coordinator = RecoveryCoordinator(
            sync_callback=sync_one_gap, coverage_reader=read)

        with self.assertRaises(RecoveryIncompleteError):
            coordinator.recover("15m", BASE, BASE + 3 * STEP)

        self.assertEqual(sync_calls, [
            ("15m", BASE, BASE + STEP),
            ("15m", BASE + 2 * STEP, BASE + 3 * STEP),
        ])
        self.assertEqual(read.call_count, 2)

    def test_repeated_recovery_is_idempotent_after_snapshot_becomes_complete(self):
        gaps = [{"startMs": BASE, "endMs": BASE + STEP}]
        remaining = list(gaps)
        sync = Mock(side_effect=lambda timeframe, start_ms, end_ms: remaining.clear())

        def read_snapshot(timeframe, start_ms, end_ms):
            return coverage(start_ms, end_ms, list(remaining))

        coordinator = RecoveryCoordinator(
            sync_callback=sync, coverage_reader=read_snapshot)

        first = coordinator.recover("15m", BASE, BASE + STEP)
        second = coordinator.recover("15m", BASE, BASE + STEP)

        self.assertTrue(first.complete)
        self.assertEqual(first.recovered_windows, ((BASE, BASE + STEP),))
        self.assertTrue(second.complete)
        self.assertEqual(second.recovered_windows, ())
        sync.assert_called_once_with("15m", BASE, BASE + STEP)

    def test_retry_after_mid_batch_callback_failure_syncs_only_remaining_gap(self):
        gaps = [
            {"startMs": BASE, "endMs": BASE + STEP},
            {"startMs": BASE + STEP, "endMs": BASE + 2 * STEP},
        ]
        remaining = list(gaps)
        calls = []
        fail_second_gap_once = {"pending": True}

        def sync_one_gap(timeframe, start_ms, end_ms):
            window = (start_ms, end_ms)
            calls.append((timeframe, start_ms, end_ms))
            if window == (BASE + STEP, BASE + 2 * STEP) and fail_second_gap_once["pending"]:
                fail_second_gap_once["pending"] = False
                raise TimeoutError("injected failure after first gap was repaired")
            remaining.remove({"startMs": start_ms, "endMs": end_ms})

        def read_snapshot(timeframe, start_ms, end_ms):
            return coverage(start_ms, end_ms, list(remaining))

        coordinator = RecoveryCoordinator(
            sync_callback=sync_one_gap, coverage_reader=read_snapshot)

        with self.assertRaisesRegex(TimeoutError, "injected failure"):
            coordinator.recover("15m", BASE, BASE + 2 * STEP)

        # The first callback committed its fixture-side effect; the second gap remains.
        self.assertEqual(remaining, [gaps[1]])

        retried = coordinator.recover("15m", BASE, BASE + 2 * STEP)

        self.assertTrue(retried.complete)
        self.assertEqual(retried.recovered_windows, ((BASE + STEP, BASE + 2 * STEP),))
        self.assertEqual(remaining, [])
        self.assertEqual(calls, [
            ("15m", BASE, BASE + STEP),
            ("15m", BASE + STEP, BASE + 2 * STEP),
            ("15m", BASE + STEP, BASE + 2 * STEP),
        ])

    def test_retry_rechecks_partial_progress_inside_failed_window(self):
        remaining = [
            {"startMs": BASE, "endMs": BASE + 2 * STEP},
        ]
        calls = []
        fail_after_first_half_once = {"pending": True}

        def sync_partial_window(timeframe, start_ms, end_ms):
            calls.append((timeframe, start_ms, end_ms))
            if fail_after_first_half_once["pending"]:
                fail_after_first_half_once["pending"] = False
                remaining[:] = [
                    {"startMs": BASE + STEP, "endMs": BASE + 2 * STEP},
                ]
                raise TimeoutError("injected failure after partial window progress")
            remaining.clear()

        def read_snapshot(timeframe, start_ms, end_ms):
            return coverage(start_ms, end_ms, list(remaining))

        coordinator = RecoveryCoordinator(
            sync_callback=sync_partial_window,
            coverage_reader=read_snapshot,
        )

        with self.assertRaisesRegex(TimeoutError, "partial window progress"):
            coordinator.recover("15m", BASE, BASE + 2 * STEP)

        # The failed call is not treated as complete and the coordinator does
        # not trust its callback result; the next attempt starts from coverage.
        self.assertEqual(remaining, [
            {"startMs": BASE + STEP, "endMs": BASE + 2 * STEP},
        ])

        retried = coordinator.recover("15m", BASE, BASE + 2 * STEP)

        self.assertTrue(retried.complete)
        self.assertEqual(
            retried.recovered_windows,
            ((BASE + STEP, BASE + 2 * STEP),),
        )
        self.assertEqual(remaining, [])
        self.assertEqual(calls, [
            ("15m", BASE, BASE + 2 * STEP),
            ("15m", BASE + STEP, BASE + 2 * STEP),
        ])

    def test_invalid_initial_snapshot_shapes_fail_before_sync(self):
        invalid_snapshots = (
            None,
            [],
            {"startMs": BASE, "endMs": BASE + STEP},
            {"startMs": BASE, "endMs": BASE + STEP, "coverage": {"complete": True, "gaps": None}},
            {"startMs": BASE, "endMs": BASE + STEP, "coverage": {"complete": False, "gaps": "not-a-list"}},
            {"startMs": BASE, "endMs": BASE + STEP, "coverage": {"complete": False, "gaps": [None]}},
            {"startMs": BASE, "endMs": BASE + STEP, "coverage": {"complete": False, "gaps": [{}]}},
            {"startMs": BASE, "endMs": BASE + STEP, "coverage": {"complete": False, "gaps": [
                {"startMs": str(BASE), "endMs": BASE + STEP}
            ]}},
        )
        for snapshot in invalid_snapshots:
            with self.subTest(snapshot=snapshot):
                read = Mock(return_value=snapshot)
                sync = Mock()
                coordinator = RecoveryCoordinator(
                    sync_callback=sync, coverage_reader=read)
                with self.assertRaises(ValueError):
                    coordinator.recover("15m", BASE, BASE + STEP)
                read.assert_called_once_with("15m", BASE, BASE + STEP)
                sync.assert_not_called()

    def test_malformed_second_coverage_snapshot_fails_closed(self):
        gaps = [{"startMs": BASE, "endMs": BASE + STEP}]
        malformed_second_snapshot = {
            "startMs": BASE,
            "endMs": BASE + STEP,
            "coverage": {"gaps": []},  # missing strict completeness flag
        }
        read = Mock(side_effect=[
            coverage(BASE, BASE + STEP, gaps),
            malformed_second_snapshot,
        ])
        sync = Mock()
        coordinator = RecoveryCoordinator(
            sync_callback=sync, coverage_reader=read)

        with self.assertRaisesRegex(
            ValueError, "coverage completeness contradicts reported gaps"
        ):
            coordinator.recover("15m", BASE, BASE + STEP)

        self.assertEqual(sync.call_count, 1)
        self.assertEqual(read.call_count, 2)

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
