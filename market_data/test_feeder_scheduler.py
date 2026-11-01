"""P1.2 contract tests: UTC scheduling and closed-candle boundaries."""
import unittest
from unittest.mock import Mock
from market_data.store import INTERVAL_MS
from market_data.feeder import FeederConfig, FeederScheduler

M15 = INTERVAL_MS["15m"]
H1 = INTERVAL_MS["1h"]
BASE = 1_800_000_000_000


class Clock:
    def __init__(self, value):
        self.value = value
    def __call__(self):
        return self.value


class SchedulerContractTest(unittest.TestCase):
    def setUp(self):
        self.clock = Clock(BASE)
        self.sync = Mock()
        self.scheduler = FeederScheduler(
            config=FeederConfig(), clock=self.clock, sync_callback=self.sync
        )

    def test_approved_defaults(self):
        cfg = FeederConfig()
        self.assertEqual(cfg.poll_interval_seconds, 5)
        self.assertEqual(cfg.close_grace_seconds, 5)

    def test_m15_waits_for_five_second_close_grace(self):
        boundary = BASE - BASE % M15 + M15
        self.clock.value = boundary + 4_999
        self.assertNotIn("15m", self.scheduler.due_timeframes())
        self.clock.value = boundary + 5_000
        self.assertIn("15m", self.scheduler.due_timeframes())

    def test_h1_waits_for_close_grace(self):
        boundary = BASE - BASE % H1 + H1
        self.clock.value = boundary + 4_999
        self.assertNotIn("1h", self.scheduler.due_timeframes())
        self.clock.value = boundary + 5_000
        self.assertIn("1h", self.scheduler.due_timeframes())

    def test_running_timeframe_is_not_scheduled_twice(self):
        self.scheduler.mark_running("15m")
        self.assertNotIn("15m", self.scheduler.due_timeframes())

    def test_missed_cycles_are_coalesced_for_recovery(self):
        boundary = BASE - BASE % M15
        self.clock.value = boundary + 4 * M15 + 5_000
        start_ms, end_ms = self.scheduler.window_for("15m")
        self.assertEqual(end_ms - start_ms, 4 * M15)

    def test_invalid_config_fails_closed(self):
        with self.assertRaises(ValueError):
            FeederConfig(poll_interval_seconds=0)


if __name__ == "__main__":
    unittest.main()
