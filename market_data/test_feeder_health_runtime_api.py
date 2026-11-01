"""Integration contract: the HTTP health API must observe a real feeder runtime via shared SQLite state.

These tests deliberately do not inject T0_HEALTH_SNAPSHOT_PROVIDER. The feeder and
Flask API use the same SQLite file, just as separate production processes do.
"""
import tempfile
import threading
import unittest
from pathlib import Path

from app import app
from market_data.feeder import FeederConfig, FeederRuntime, FeederScheduler, LeaseStore
from market_data.store import Candle, CandleStore, INTERVAL_MS
from market_data.feeder_status import FeederRuntimeStatusStore

NOW = 1_800_000_000_000


class Recovery:
    def __init__(self, result=True, entered=None, release=None):
        self.result = result
        self.entered = entered
        self.release = release

    def recover_all(self):
        if self.entered is not None:
            self.entered.set()
        if self.release is not None and not self.release.wait(3):
            raise TimeoutError("test did not release recovery")
        return self.result


class FeederHealthRuntimeApiIntegrationTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.temp.name) / "t0.sqlite3")
        self.leases = LeaseStore(self.db_path)
        self.status = FeederRuntimeStatusStore(self.db_path)
        self._seed_closed_candles()
        self.previous_db = app.config.get("T0_HEALTH_RUNTIME_STATUS_DB")
        self.previous_provider = app.config.get("T0_HEALTH_SNAPSHOT_PROVIDER")
        self.previous_clock = app.config.get("T0_HEALTH_CLOCK")
        app.config.pop("T0_HEALTH_SNAPSHOT_PROVIDER", None)
        app.config["T0_HEALTH_RUNTIME_STATUS_DB"] = self.db_path
        app.config["T0_HEALTH_CLOCK"] = lambda: NOW + 5_000
        self.client = app.test_client()

    def tearDown(self):
        if self.previous_db is None:
            app.config.pop("T0_HEALTH_RUNTIME_STATUS_DB", None)
        else:
            app.config["T0_HEALTH_RUNTIME_STATUS_DB"] = self.previous_db
        if self.previous_provider is None:
            app.config.pop("T0_HEALTH_SNAPSHOT_PROVIDER", None)
        else:
            app.config["T0_HEALTH_SNAPSHOT_PROVIDER"] = self.previous_provider
        if self.previous_clock is None:
            app.config.pop("T0_HEALTH_CLOCK", None)
        else:
            app.config["T0_HEALTH_CLOCK"] = self.previous_clock
        self.temp.cleanup()

    def _seed_closed_candles(self):
        store = CandleStore(self.db_path)
        candles = []
        for timeframe in ("15m", "1h"):
            interval = INTERVAL_MS[timeframe]
            candles.append(Candle(
                timeframe=timeframe,
                open_time_ms=NOW - interval,
                open="100", high="101", low="99", close="100.5",
                volume="10", available_at_ms=NOW,
            ))
        store.insert(candles)

    def _runtime(self, recovery=None, owner="health-api-worker"):
        config = FeederConfig(
            poll_interval_seconds=3600,
            lease_ttl_seconds=60,
            lease_heartbeat_seconds=15,
        )
        scheduler = FeederScheduler(
            config=config,
            clock=lambda: NOW,
            sync_callback=lambda timeframe, start_ms, end_ms: None,
        )
        return FeederRuntime(
            config=config,
            scheduler=scheduler,
            lease_store=self.leases,
            owner_id=owner,
            recovery=recovery or Recovery(True),
            status_store=self.status,
            clock=lambda: NOW,
        )

    def test_api_reports_starting_while_real_runtime_recovery_is_in_progress(self):
        entered, release = threading.Event(), threading.Event()
        runtime = self._runtime(Recovery(True, entered, release))
        errors = []

        def start_runtime():
            try:
                runtime.start(now_ms=NOW)
            except Exception as error:
                errors.append(error)

        worker = threading.Thread(target=start_runtime)
        worker.start()
        self.assertTrue(entered.wait(1))
        response = self.client.get("/health/ready")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.get_json()["state"], "STARTING")
        self.assertFalse(response.get_json()["ready"])
        release.set()
        worker.join(2)
        self.assertFalse(worker.is_alive())
        self.assertEqual(errors, [])
        runtime.stop()

    def test_api_reports_healthy_only_after_recovery_and_current_lease(self):
        runtime = self._runtime()
        self.assertTrue(runtime.start(now_ms=NOW))
        response = self.client.get("/health/ready")
        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertEqual(body["state"], "HEALTHY")
        self.assertTrue(body["ready"])
        self.assertEqual(body["timeframes"]["15m"]["state"], "HEALTHY")
        self.assertEqual(body["timeframes"]["1h"]["state"], "HEALTHY")
        runtime.stop()

    def test_api_reports_lease_lost_from_real_runtime_and_blocks_readiness(self):
        runtime = self._runtime()
        self.assertTrue(runtime.start(now_ms=NOW))
        runtime.on_lease_lost()
        response = self.client.get("/health/ready")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.get_json()["state"], "LEASE_LOST")
        self.assertTrue(response.get_json()["live"])
        self.assertFalse(response.get_json()["ready"])
        runtime.stop()

    def test_api_reports_failed_when_startup_recovery_is_incomplete(self):
        runtime = self._runtime(Recovery(False))
        self.assertFalse(runtime.start(now_ms=NOW))
        response = self.client.get("/health/ready")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.get_json()["state"], "FAILED")
        self.assertFalse(response.get_json()["ready"])

    def test_api_reports_stopped_after_real_runtime_shutdown(self):
        runtime = self._runtime()
        self.assertTrue(runtime.start(now_ms=NOW))
        runtime.stop()
        response = self.client.get("/health/live")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.get_json()["state"], "STOPPED")
        self.assertFalse(response.get_json()["live"])
        self.assertFalse(response.get_json()["ready"])

    def test_old_generation_cannot_overwrite_replacement_runtime_status(self):
        first = self.leases.acquire("old-owner", now_ms=NOW, ttl_seconds=60)
        self.assertTrue(self.status.publish(
            "old-owner", first.generation, "STARTING", now_ms=NOW,
            recovery_complete=False,
        ))
        replacement = self.leases.acquire(
            "new-owner", now_ms=NOW + 60_001, ttl_seconds=60
        )
        self.assertIsNotNone(replacement)
        self.assertFalse(self.status.publish(
            "old-owner", first.generation, "STOPPED", now_ms=NOW + 60_002,
            recovery_complete=False,
        ))
        self.assertTrue(self.status.publish(
            "new-owner", replacement.generation, "STARTING",
            now_ms=NOW + 60_002, recovery_complete=False,
        ))
        response = self.client.get("/health/ready")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.get_json()["state"], "STARTING")


if __name__ == "__main__":
    unittest.main()
