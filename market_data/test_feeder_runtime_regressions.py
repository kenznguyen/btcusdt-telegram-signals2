"""Regression tests for T0 feeder lease renewal and background failure visibility."""

import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from market_data.feeder import (
    FeederConfig,
    FeederRuntime,
    FeederScheduler,
    LeaseStore,
)
from market_data.feeder_service import build_runtime, run_service
from market_data.storage import SQLiteCandleStore
from market_data.store import INTERVAL_MS


NOW = 1_800_000_000_000


class FeederRecoveryLeaseRegressionTest(unittest.TestCase):
    def test_startup_recovery_renews_lease_across_pages_beyond_ttl(self):
        interval = INTERVAL_MS["15m"]
        def synthetic_clock():
            return NOW

        with tempfile.TemporaryDirectory(prefix="t0-recovery-lease-regression-") as directory:
            database = Path(directory) / "canonical.sqlite3"
            SQLiteCandleStore(database).initialize()
            store = Mock()
            store.path = database
            read_count = {"value": 0}

            def read_window(symbol, timeframe, start_ms, end_ms):
                read_count["value"] += 1
                gaps = []
                if read_count["value"] == 1:
                    gaps = [
                        {"startMs": start_ms, "endMs": start_ms + interval},
                        {
                            "startMs": start_ms + interval,
                            "endMs": start_ms + 2 * interval,
                        },
                    ]
                return {
                    "startMs": start_ms,
                    "endMs": end_ms,
                    "coverage": {"complete": not gaps, "gaps": gaps},
                }

            store.read_window.side_effect = read_window
            leases = LeaseStore(str(database))
            actual_heartbeat = leases.heartbeat
            heartbeat_times = []

            def record_heartbeat(owner, generation, now_ms=None, ttl_seconds=60):
                # Model two recovery pages taking 40 seconds each. The first
                # renewal extends the original lease past NOW+60s; the second
                # renewal must still succeed at NOW+80s.
                renewal_now = NOW + (len(heartbeat_times) + 1) * 40_000
                heartbeat_times.append(renewal_now)
                return actual_heartbeat(
                    owner,
                    generation,
                    now_ms=renewal_now,
                    ttl_seconds=ttl_seconds,
                )

            leases.heartbeat = record_heartbeat
            runtime = build_runtime(
                config=FeederConfig(timeframes=("15m",), lease_ttl_seconds=60),
                owner_id="recovery-over-ttl-worker",
                exchange=Mock(),
                store=store,
                lease_store=leases,
                clock=synthetic_clock,
                recovery_lookback_candles=2,
            )

            try:
                with patch("market_data.feeder_service.sync_window", return_value=1) as sync:
                    self.assertTrue(runtime.start())
                    self.assertEqual(sync.call_count, 2)

                self.assertEqual(heartbeat_times, [NOW + 40_000, NOW + 80_000])
                self.assertEqual(runtime.state, "RUNNING")
                self.assertTrue(
                    actual_heartbeat(
                        "recovery-over-ttl-worker",
                        runtime.lease_generation,
                        now_ms=NOW + 80_000,
                        ttl_seconds=60,
                    )
                )
            finally:
                runtime.stop(timeout=2)

            self.assertFalse(
                leases.is_current(
                    "recovery-over-ttl-worker",
                    runtime.lease_generation,
                    now_ms=NOW + 80_001,
                )
            )


class FeederBackgroundFailureRegressionTest(unittest.TestCase):
    def test_background_scheduler_exception_fails_runtime_and_service(self):
        with tempfile.TemporaryDirectory(prefix="t0-background-failure-regression-") as directory:
            leases = LeaseStore(str(Path(directory) / "leases.sqlite3"))
            scheduler = FeederScheduler(
                config=FeederConfig(timeframes=("15m",)),
                clock=lambda: NOW,
                sync_callback=lambda timeframe, start_ms, end_ms: 0,
                coverage_reader=lambda timeframe, start_ms, end_ms: {
                    "startMs": start_ms,
                    "endMs": end_ms,
                    "coverage": {"complete": True, "gaps": []},
                },
            )
            allow_failure = threading.Event()
            failure_finished = threading.Event()
            original_background_runner = scheduler._run_background

            def signal_after_background_runner():
                original_background_runner()
                failure_finished.set()

            def fail_after_ready(stop_event):
                if not allow_failure.wait(2):
                    raise TimeoutError("test did not release synthetic scheduler failure")
                raise OSError("synthetic background scheduler failure")

            scheduler._run_background = signal_after_background_runner
            scheduler.run_forever = fail_after_ready
            health = Mock()
            runtime = FeederRuntime(
                config=scheduler.config,
                scheduler=scheduler,
                lease_store=leases,
                owner_id="background-failure-worker",
                health=health,
                clock=lambda: NOW,
            )

            class FailureDrivenStopEvent:
                def __init__(self):
                    self.wait_count = 0

                def wait(self, timeout):
                    self.wait_count += 1
                    if self.wait_count == 1:
                        return not failure_finished.wait(timeout)
                    return True

            stop_event = FailureDrivenStopEvent()
            notifications = []
            state_at_stopping = []
            lease_valid_at_stopping = []

            def notify(message):
                notifications.append(message)
                if message == "READY=1":
                    allow_failure.set()
                elif message == "STOPPING=1":
                    state_at_stopping.append(runtime.state)
                    lease_valid_at_stopping.append(
                        leases.is_current(
                            "background-failure-worker",
                            runtime.lease_generation,
                            now_ms=NOW + 1,
                        )
                    )

            result = run_service(runtime, stop_event=stop_event, notify=notify)

            self.assertTrue(failure_finished.is_set())
            self.assertIsInstance(scheduler._thread_error, OSError)
            self.assertEqual(result, 3)
            self.assertEqual(notifications, ["READY=1", "STOPPING=1"])
            self.assertEqual(state_at_stopping, ["FAILED"])
            self.assertEqual(lease_valid_at_stopping, [True])
            health.mark_not_ready.assert_called_once()
            self.assertEqual(runtime.state, "STOPPED")
            self.assertFalse(
                leases.is_current(
                    "background-failure-worker",
                    runtime.lease_generation,
                    now_ms=NOW + 1,
                )
            )


if __name__ == "__main__":
    unittest.main()
