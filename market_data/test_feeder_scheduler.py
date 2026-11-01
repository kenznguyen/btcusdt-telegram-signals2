"""P1.2 contract tests: UTC scheduler and closed-candle boundaries."""
import unittest
from unittest.mock import Mock

from market_data.store import INTERVAL_MS
from market_data.feeder import FeederConfig, FeederScheduler

M15 = INTERVAL_MS["15m"]
H1 = INTERVAL_MS["1h"]
BASE = 1_800_000_000_000


class FakeClock:
    def __init__(self, value):
        self.value = value
    def __call__(self):
        return self.value


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
        close = BASE - BASE % M15 + M15
        self.clock.value = close + 4_999
        self.assertNotIn("15m", self.scheduler.due_timeframes())
        self.clock.value = close + 5_000
        self.assertIn("15m", self.scheduler.due_timeframes())

    def test_h1_waits_until_five_seconds_after_hour_close(self):
        close = BASE - BASE % H1 + H1
        self.clock.value = close + 4_999
        self.assertNotIn("1h", self.scheduler.due_timeframes())
        self.clock.value = close + 5_000
        self.assertIn("1h", self.scheduler.due_timeframes())

    def test_m15_and_h1_are_scheduled_independently(self):
        close = BASE - BASE % H1 + H1 + 5_000
        self.clock.value = close
        due = self.scheduler.due_timeframes()
        self.assertIn("15m", due)
        self.assertIn("1h", due)

    def test_running_timeframe_is_not_scheduled_twice(self):
        self.scheduler.mark_running("15m")
        self.assertNotIn("15m", self.scheduler.due_timeframes())

    def test_completed_slot_is_not_retriggered_by_every_poll(self):
        close = BASE - BASE % M15 + M15 + 5_000
        self.clock.value = close
        self.scheduler.mark_completed("15m", close - 5_000)
        self.assertNotIn("15m", self.scheduler.due_timeframes())

    def test_missed_cycles_are_coalesced_into_a_single_bounded_window(self):
        boundary = BASE - BASE % M15
        self.clock.value = boundary + 4 * M15 + 5_000
        start_ms, end_ms = self.scheduler.window_for("15m")
        self.assertEqual(start_ms % M15, 0)
        self.assertEqual(end_ms % M15, 0)
        self.assertEqual(end_ms - start_ms, 4 * M15)
        self.assertLessEqual(end_ms, self.clock.value)

    def test_invalid_timeframe_is_rejected(self):
        with self.assertRaises(ValueError):
            self.scheduler.window_for("5m")

    def test_invalid_config_fails_closed(self):
        with self.assertRaises(ValueError):
            FeederConfig(poll_interval_seconds=0)


if __name__ == "__main__":
    unittest.main()
