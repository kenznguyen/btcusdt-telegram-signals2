"""P1 scheduler contract: UTC boundaries, coalescing and independent timeframes."""
import unittest
from unittest.mock import Mock

from market_data.store import INTERVAL_MS, MAX_CANDLES
from market_data.feeder import (
    FeederConfig, FeederScheduler, SchedulerExecutionError,
)

M15 = INTERVAL_MS["15m"]
H1 = INTERVAL_MS["1h"]
BASE = 1_800_000_000_000


class FakeClock:
    def __init__(self, value):
        self.value = value

    def __call__(self):
        return self.value


class FakeStopEvent:
    def __init__(self):
        self.stopped = False
        self.waits = []

    def is_set(self):
        return self.stopped

    def wait(self, timeout):
        self.waits.append(timeout)
        self.stopped = True
        return True


class SchedulerContractTest(unittest.TestCase):
    def setUp(self):
        self.clock = FakeClock(BASE)
        self.sync = Mock()
        self.scheduler = FeederScheduler(
            config=FeederConfig(), clock=self.clock, sync_callback=self.sync
        )

    def test_approved_poll_and_close_grace_defaults(self):
        config = FeederConfig()
        self.assertEqual(config.poll_interval_seconds, 5)
        self.assertEqual(config.close_grace_seconds, 5)

    def test_m15_waits_until_five_seconds_after_utc_close(self):
        close = BASE + M15
        self.clock.value = close + 4_999
        self.assertNotIn("15m", self.scheduler.due_timeframes())
        self.clock.value = close + 5_000
        self.assertIn("15m", self.scheduler.due_timeframes())

    def test_h1_waits_until_five_seconds_after_hour_close(self):
        close = BASE + H1
        self.clock.value = close + 4_999
        self.assertNotIn("1h", self.scheduler.due_timeframes())
        self.clock.value = close + 5_000
        self.assertIn("1h", self.scheduler.due_timeframes())

    def test_m15_and_h1_are_scheduled_independently(self):
        self.clock.value = BASE + H1 + 5_000
        due = self.scheduler.due_timeframes()
        self.assertIn("15m", due)
        self.assertIn("1h", due)

    def test_running_timeframe_is_not_scheduled_twice(self):
        self.scheduler.mark_running("15m")
        self.assertNotIn("15m", self.scheduler.due_timeframes())

    def test_completed_slot_is_not_retriggered_by_every_poll(self):
        close = BASE + M15
        self.clock.value = close + 5_000
        self.scheduler.mark_running("15m")
        self.scheduler.mark_completed("15m", close)
        self.assertNotIn("15m", self.scheduler.due_timeframes())

    def test_missed_cycles_are_coalesced_into_a_single_bounded_window(self):
        self.clock.value = BASE + 4 * M15 + 5_000
        start_ms, end_ms = self.scheduler.window_for("15m")
        self.assertEqual(start_ms % M15, 0)
        self.assertEqual(end_ms % M15, 0)
        self.assertEqual(end_ms - start_ms, 4 * M15)
        self.assertLessEqual(end_ms, self.clock.value)

    def test_large_catch_up_window_is_bounded_to_store_sync_limit(self):
        self.clock.value = BASE + (MAX_CANDLES + 5) * M15 + 5_000
        start_ms, end_ms = self.scheduler.window_for("15m")
        self.assertEqual(end_ms - start_ms, MAX_CANDLES * M15)

    def test_run_due_calls_only_the_injected_sync_callback(self):
        self.clock.value = BASE + M15 + 5_000
        self.sync.return_value = 1
        outcomes = self.scheduler.run_due()
        self.assertEqual(outcomes, {"15m": 1})
        self.sync.assert_called_once_with("15m", BASE, BASE + M15)

    def test_m15_failure_does_not_prevent_due_h1_sync(self):
        self.clock.value = BASE + H1 + 5_000

        def sync(timeframe, start_ms, end_ms):
            if timeframe == "15m":
                raise TimeoutError("temporary upstream failure")
            return 7

        self.scheduler.sync_callback = sync
        with self.assertRaises(SchedulerExecutionError) as raised:
            self.scheduler.run_due()
        self.assertIn("15m", raised.exception.failures)
        self.assertEqual(raised.exception.completed, {"1h": 7})
        self.assertEqual(self.scheduler.last_completed_end_ms["1h"], BASE + H1)
        self.assertEqual(self.scheduler.last_completed_end_ms["15m"], BASE)

    def test_failed_sync_does_not_advance_timeframe_watermark(self):
        self.clock.value = BASE + M15 + 5_000
        self.sync.side_effect = TimeoutError("offline")
        with self.assertRaises(SchedulerExecutionError):
            self.scheduler.run_due()
        self.assertEqual(self.scheduler.last_completed_end_ms["15m"], BASE)
        self.assertNotIn("15m", self.scheduler.running_timeframes)

    def test_run_forever_uses_configured_poll_interval(self):
        stop_event = FakeStopEvent()
        self.scheduler.run_forever(stop_event)
        self.assertEqual(stop_event.waits, [5])

    def test_invalid_timeframe_is_rejected(self):
        with self.assertRaises(ValueError):
            self.scheduler.window_for("5m")

    def test_invalid_config_fails_closed(self):
        with self.assertRaises(ValueError):
            FeederConfig(poll_interval_seconds=0)

    def test_invalid_or_unclosed_completion_boundary_is_rejected(self):
        self.scheduler.mark_running("15m")
        with self.assertRaises(ValueError):
            self.scheduler.mark_completed("15m", BASE + 1)
        with self.assertRaises(ValueError):
            self.scheduler.mark_completed("15m", BASE + M15 + 1)


if __name__ == "__main__":
    unittest.main()
