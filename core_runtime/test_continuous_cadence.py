"""RED-first tests for Continuous Core M15 cadence and cycle identity."""

import unittest

from core_runtime.continuous_cadence import (
    cycle_key_for_bundle,
    latest_eligible_m15_open_ms,
    next_m15_deadline_ms,
    wait_until_deadline,
)
from core_runtime.test_input_bundle_contract import valid_bundle


INTERVAL_MS = 900_000


class ContinuousCadenceTest(unittest.TestCase):
    def test_cycle_key_uses_the_latest_closed_m15_candle(self):
        bundle = valid_bundle()
        expected_open = bundle["marketData"]["m15"]["candles"][-1]["openTimeMs"]
        self.assertEqual(
            cycle_key_for_bundle(bundle),
            f"binance:USDT_PERPETUAL:BTCUSDT:15m:{expected_open}:STRATEGY_CORE",
        )

    def test_latest_eligible_candle_waits_for_close_and_settlement(self):
        now = 1_800_000_000_000
        settlement = 30_000
        latest_open = latest_eligible_m15_open_ms(now, settlement_ms=settlement)
        self.assertEqual(latest_open + INTERVAL_MS + settlement,
                         (now // INTERVAL_MS) * INTERVAL_MS + settlement)
        self.assertEqual(latest_eligible_m15_open_ms(
            now + settlement - 1, settlement_ms=settlement
        ), latest_open)
        self.assertEqual(latest_eligible_m15_open_ms(
            now + settlement, settlement_ms=settlement
        ), latest_open + INTERVAL_MS)

    def test_next_deadline_is_next_closed_m15_boundary_plus_settlement(self):
        now = 1_800_000_000_123
        settlement = 45_000
        expected = ((now // INTERVAL_MS) + 1) * INTERVAL_MS + settlement
        self.assertEqual(next_m15_deadline_ms(now, settlement_ms=settlement), expected)

    def test_wait_uses_monotonic_deadline_after_wall_clock_jump(self):
        monotonic_value = [100.0]
        sleeps = []

        def monotonic():
            return monotonic_value[0]

        def sleep(seconds):
            sleeps.append(seconds)
            monotonic_value[0] += seconds

        result = wait_until_deadline(
            deadline_ms=1_000,
            wall_now_ms=0,
            monotonic=monotonic,
            sleep=sleep,
            stop_requested=lambda: False,
            max_sleep_seconds=0.25,
        )
        self.assertTrue(result)
        self.assertEqual(monotonic_value[0], 101.0)
        self.assertEqual(sleeps, [0.25, 0.25, 0.25, 0.25])

    def test_wait_stops_without_claiming_when_stop_is_requested(self):
        calls = [0]

        def stop():
            calls[0] += 1
            return calls[0] >= 2

        result = wait_until_deadline(
            deadline_ms=10_000,
            wall_now_ms=0,
            monotonic=lambda: 1.0,
            sleep=lambda _seconds: None,
            stop_requested=stop,
            max_sleep_seconds=0.1,
        )
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
