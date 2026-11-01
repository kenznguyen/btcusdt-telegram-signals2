"""P1.2 health contract: liveness, readiness and per-timeframe freshness."""
import unittest

from market_data.feeder import FeederConfig, HealthEvaluator
from market_data.store import INTERVAL_MS

NOW = 1_800_000_000_000
M15 = INTERVAL_MS["15m"]
H1 = INTERVAL_MS["1h"]


def healthy_snapshot():
    return {
        "process_running": True,
        "startup_complete": True,
        "storage_readable": True,
        "storage_writable": True,
        "lease_valid": True,
        "fatal_error": False,
        "m15": {
            "latest_closed_candle_close_ms": NOW,
            "last_successful_sync_ms": NOW,
            "unresolved_gap_count": 0,
            "sync_error": None,
        },
        "1h": {
            "latest_closed_candle_close_ms": NOW,
            "last_successful_sync_ms": NOW,
            "unresolved_gap_count": 0,
            "sync_error": None,
        },
    }


class HealthContractTest(unittest.TestCase):
    def setUp(self):
        self.evaluator = HealthEvaluator(config=FeederConfig())

    def evaluate(self, snapshot):
        return self.evaluator.evaluate(snapshot, now_ms=NOW + 5_000)

    def test_healthy_requires_both_timeframes_storage_and_lease(self):
        result = self.evaluate(healthy_snapshot())
        self.assertEqual(result.state, "HEALTHY")
        self.assertTrue(result.live)
        self.assertTrue(result.ready)

    def test_startup_in_progress_is_not_ready(self):
        state = healthy_snapshot()
        state["startup_complete"] = False
        result = self.evaluate(state)
        self.assertEqual(result.state, "STARTING")
        self.assertTrue(result.live)
        self.assertFalse(result.ready)

    def test_m15_one_cycle_lag_is_degraded_warning(self):
        state = healthy_snapshot()
        state["m15"]["latest_closed_candle_close_ms"] = NOW - M15
        result = self.evaluate(state)
        self.assertEqual(result.state, "DEGRADED")
        self.assertFalse(result.ready)

    def test_m15_two_cycle_lag_is_stale(self):
        state = healthy_snapshot()
        state["m15"]["latest_closed_candle_close_ms"] = NOW - 2 * M15
        result = self.evaluate(state)
        self.assertEqual(result.state, "STALE")
        self.assertFalse(result.ready)

    def test_h1_two_cycle_lag_is_stale(self):
        state = healthy_snapshot()
        state["1h"]["latest_closed_candle_close_ms"] = NOW - 2 * H1
        result = self.evaluate(state)
        self.assertEqual(result.state, "STALE")
        self.assertFalse(result.ready)

    def test_unresolved_gap_blocks_readiness(self):
        state = healthy_snapshot()
        state["m15"]["unresolved_gap_count"] = 1
        result = self.evaluate(state)
        self.assertEqual(result.state, "DEGRADED")
        self.assertFalse(result.ready)

    def test_transient_timeframe_error_blocks_readiness(self):
        state = healthy_snapshot()
        state["1h"]["sync_error"] = "UPSTREAM_TIMEOUT"
        result = self.evaluate(state)
        self.assertEqual(result.state, "DEGRADED")
        self.assertFalse(result.ready)

    def test_lost_lease_keeps_process_live_but_not_ready(self):
        state = healthy_snapshot()
        state["lease_valid"] = False
        result = self.evaluate(state)
        self.assertTrue(result.live)
        self.assertFalse(result.ready)
        self.assertEqual(result.state, "DEGRADED")

    def test_storage_unavailable_is_failed_and_not_ready(self):
        state = healthy_snapshot()
        state["storage_readable"] = False
        result = self.evaluate(state)
        self.assertEqual(result.state, "FAILED")
        self.assertFalse(result.ready)

    def test_fatal_error_has_priority_over_staleness(self):
        state = healthy_snapshot()
        state["fatal_error"] = True
        state["m15"]["latest_closed_candle_close_ms"] = NOW - 3 * M15
        result = self.evaluate(state)
        self.assertEqual(result.state, "FAILED")
        self.assertFalse(result.ready)

    def test_stopped_process_is_not_live_or_ready(self):
        state = healthy_snapshot()
        state["process_running"] = False
        result = self.evaluate(state)
        self.assertEqual(result.state, "STOPPED")
        self.assertFalse(result.live)
        self.assertFalse(result.ready)


if __name__ == "__main__":
    unittest.main()
