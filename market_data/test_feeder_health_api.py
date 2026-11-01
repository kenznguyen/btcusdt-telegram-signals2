"""P1.7 HTTP contract for T0 liveness, readiness and data freshness endpoints."""
import unittest

from app import app
from market_data.store import INTERVAL_MS

NOW = 1_800_000_000_000


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


class FeederHealthApiContractTest(unittest.TestCase):
    def setUp(self):
        self.snapshot = healthy_snapshot()
        self.previous_provider = app.config.get("T0_HEALTH_SNAPSHOT_PROVIDER")
        app.config["T0_HEALTH_SNAPSHOT_PROVIDER"] = lambda: self.snapshot
        app.config["T0_HEALTH_CLOCK"] = lambda: NOW + 5_000
        self.client = app.test_client()

    def tearDown(self):
        if self.previous_provider is None:
            app.config.pop("T0_HEALTH_SNAPSHOT_PROVIDER", None)
        else:
            app.config["T0_HEALTH_SNAPSHOT_PROVIDER"] = self.previous_provider
        app.config.pop("T0_HEALTH_CLOCK", None)

    def test_liveness_endpoint_reports_process_alive_independently(self):
        response = self.client.get("/health/live")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["state"], "HEALTHY")
        self.assertTrue(response.get_json()["live"])

    def test_readiness_endpoint_is_200_only_when_all_dependencies_are_ready(self):
        response = self.client.get("/health/ready")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.get_json()["ready"])

        self.snapshot["lease_valid"] = False
        response = self.client.get("/health/ready")
        self.assertEqual(response.status_code, 503)
        self.assertFalse(response.get_json()["ready"])
        self.assertEqual(response.get_json()["state"], "DEGRADED")

    def test_data_endpoint_exposes_independent_m15_and_h1_freshness(self):
        response = self.client.get("/health/data")
        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertEqual(body["timeframes"]["15m"]["state"], "HEALTHY")
        self.assertEqual(body["timeframes"]["1h"]["state"], "HEALTHY")
        self.assertEqual(body["timeframes"]["15m"]["latest_closed_candle_close_ms"], NOW)
        self.assertEqual(body["timeframes"]["1h"]["latest_closed_candle_close_ms"], NOW)

    def test_data_endpoint_marks_m15_one_cycle_lag_as_degraded(self):
        self.snapshot["m15"]["latest_closed_candle_close_ms"] = NOW - INTERVAL_MS["15m"]
        response = self.client.get("/health/data")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.get_json()["timeframes"]["15m"]["state"], "DEGRADED")

    def test_data_endpoint_marks_h1_two_cycle_lag_as_stale(self):
        self.snapshot["1h"]["latest_closed_candle_close_ms"] = NOW - 2 * INTERVAL_MS["1h"]
        response = self.client.get("/health/data")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.get_json()["timeframes"]["1h"]["state"], "STALE")

    def test_aggregate_health_endpoint_combines_live_ready_and_timeframes(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertTrue(body["live"])
        self.assertTrue(body["ready"])
        self.assertEqual(body["state"], "HEALTHY")
        self.assertIn("timeframes", body)

    def test_aggregate_health_returns_503_when_storage_is_unavailable(self):
        self.snapshot["storage_readable"] = False
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.get_json()["state"], "FAILED")

    def test_stopped_process_is_not_live_or_ready(self):
        self.snapshot["process_running"] = False
        self.assertEqual(self.client.get("/health/live").status_code, 503)
        self.assertEqual(self.client.get("/health/ready").status_code, 503)

    def test_missing_snapshot_provider_fails_readiness_closed(self):
        app.config.pop("T0_HEALTH_SNAPSHOT_PROVIDER", None)
        response = self.client.get("/health/ready")
        self.assertEqual(response.status_code, 503)
        self.assertFalse(response.get_json()["ready"])


if __name__ == "__main__":
    unittest.main()
