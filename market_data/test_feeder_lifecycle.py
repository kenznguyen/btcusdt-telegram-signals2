"""P1.2 contract tests: graceful shutdown and restart recovery."""
import threading
import unittest
from unittest.mock import Mock

from market_data.feeder import FeederConfig, FeederRuntime, FeederScheduler
from market_data.feeder_service import RecoveryAdapter, build_runtime

NOW = 1_800_000_000_000


class RuntimeLifecycleTest(unittest.TestCase):
    def test_stop_stops_scheduler_drains_work_then_releases_lease(self):
        events = []
        scheduler = Mock()
        scheduler.stop.side_effect = lambda: events.append("scheduler_stopped")
        scheduler.wait_for_idle.side_effect = lambda timeout=None: events.append("work_drained")
        leases = Mock()
        leases.release.side_effect = lambda owner, generation: events.append("lease_released")
        runtime = FeederRuntime(
            config=FeederConfig(), scheduler=scheduler, lease_store=leases,
            owner_id="worker-A",
        )
        runtime.lease_generation = 4
        runtime.stop()
        self.assertEqual(events, ["scheduler_stopped", "work_drained", "lease_released"])
        leases.release.assert_called_once_with("worker-A", 4)

    def test_stop_is_idempotent(self):
        scheduler, leases = Mock(), Mock()
        runtime = FeederRuntime(
            config=FeederConfig(), scheduler=scheduler, lease_store=leases,
            owner_id="worker-A",
        )
        runtime.lease_generation = 4
        runtime.stop()
        runtime.stop()
        leases.release.assert_called_once_with("worker-A", 4)

    def test_start_acquires_lease_recovers_then_marks_ready(self):
        events = []
        scheduler, leases, recovery, health = Mock(), Mock(), Mock(), Mock()
        leases.acquire.side_effect = lambda *args, **kwargs: (
            events.append("lease_acquired") or Mock(generation=8)
        )
        recovery.recover_all.side_effect = lambda: (
            events.append("recovery_completed") or True
        )
        leases.heartbeat.return_value = True
        health.mark_ready.side_effect = lambda: events.append("ready")
        runtime = FeederRuntime(
            config=FeederConfig(), scheduler=scheduler, lease_store=leases,
            recovery=recovery, health=health, owner_id="worker-B",
            event_sink=events.append,
        )
        runtime.start(now_ms=NOW)
        self.assertLess(events.index("lease_acquired"), events.index("recovery_completed"))
        self.assertLess(events.index("recovery_completed"), events.index("ready"))
        scheduler.start.assert_called_once()

    def test_start_without_lease_does_not_recover_or_become_ready(self):
        scheduler, leases, recovery, health = Mock(), Mock(), Mock(), Mock()
        leases.acquire.return_value = None
        runtime = FeederRuntime(
            config=FeederConfig(), scheduler=scheduler, lease_store=leases,
            recovery=recovery, health=health, owner_id="worker-C",
        )
        runtime.start(now_ms=NOW)
        recovery.recover_all.assert_not_called()
        health.mark_ready.assert_not_called()
        scheduler.start.assert_not_called()

    def test_incomplete_restart_recovery_keeps_readiness_false(self):
        scheduler, leases, recovery, health = Mock(), Mock(), Mock(), Mock()
        leases.acquire.return_value = Mock(generation=9)
        recovery.recover_all.return_value = False
        runtime = FeederRuntime(
            config=FeederConfig(), scheduler=scheduler, lease_store=leases,
            recovery=recovery, health=health, owner_id="worker-D",
        )
        runtime.start(now_ms=NOW)
        health.mark_ready.assert_not_called()
        scheduler.start.assert_not_called()

    def test_recovery_exception_keeps_readiness_false_and_releases_lease(self):
        scheduler, leases, recovery, health = Mock(), Mock(), Mock(), Mock()
        leases.acquire.return_value = Mock(generation=10)
        recovery.recover_all.side_effect = OSError("storage unavailable")
        runtime = FeederRuntime(
            config=FeederConfig(), scheduler=scheduler, lease_store=leases,
            recovery=recovery, health=health, owner_id="worker-E",
        )
        with self.assertRaisesRegex(OSError, "storage unavailable"):
            runtime.start(now_ms=NOW)
        health.mark_ready.assert_not_called()
        scheduler.start.assert_not_called()
        leases.release.assert_called_once_with("worker-E", 10)

    def test_losing_lease_stops_scheduler_and_blocks_future_sync(self):
        scheduler, leases = Mock(), Mock()
        runtime = FeederRuntime(
            config=FeederConfig(), scheduler=scheduler, lease_store=leases,
            owner_id="worker-F",
        )
        runtime.lease_generation = 11
        runtime.on_lease_lost()
        scheduler.stop.assert_called_once()
        runtime.run_once()
        scheduler.run_due.assert_not_called()


    def test_stop_does_not_release_lease_when_work_drain_times_out(self):
        scheduler, leases, health = Mock(), Mock(), Mock()
        scheduler.wait_for_idle.side_effect = TimeoutError("active writer did not drain")
        runtime = FeederRuntime(
            config=FeederConfig(), scheduler=scheduler, lease_store=leases,
            health=health, owner_id="worker-G",
        )
        runtime.lease_generation = 12

        with self.assertRaises(TimeoutError):
            runtime.stop()

        scheduler.stop.assert_called_once()
        leases.release.assert_not_called()
        health.mark_stopped.assert_not_called()

    def test_stop_reports_release_failure_and_marks_process_stopped(self):
        scheduler, leases, health = Mock(), Mock(), Mock()
        leases.release.return_value = False
        runtime = FeederRuntime(
            config=FeederConfig(), scheduler=scheduler, lease_store=leases,
            health=health, owner_id="worker-H",
        )
        runtime.lease_generation = 13

        with self.assertRaises(RuntimeError):
            runtime.stop()

        scheduler.stop.assert_called_once()
        scheduler.wait_for_idle.assert_called_once()
        leases.release.assert_called_once_with("worker-H", 13)
        health.mark_stopped.assert_called_once()

    def test_shutdown_marks_health_stopped_only_after_writer_drain_and_release(self):
        events = []
        scheduler, leases, health = Mock(), Mock(), Mock()
        scheduler.stop.side_effect = lambda: events.append("stop_requested")
        scheduler.wait_for_idle.side_effect = lambda timeout=None: events.append("writer_drained")
        leases.release.side_effect = lambda owner, generation: (
            events.append(("lease_released", owner, generation)) or True
        )
        health.mark_stopped.side_effect = lambda: events.append("health_stopped")
        runtime = FeederRuntime(
            config=FeederConfig(), scheduler=scheduler, lease_store=leases,
            health=health, owner_id="worker-I",
        )
        runtime.lease_generation = 14

        runtime.stop()

        self.assertEqual(events, [
            "stop_requested",
            "writer_drained",
            ("lease_released", "worker-I", 14),
            "health_stopped",
        ])

    def test_stale_runtime_cannot_release_replacement_generation(self):
        import tempfile
        from pathlib import Path
        from market_data.feeder import LeaseStore

        with tempfile.TemporaryDirectory() as directory:
            store = LeaseStore(str(Path(directory) / "leases.sqlite3"))
            old = store.acquire("worker-old", now_ms=NOW, ttl_seconds=60)
            replacement = store.acquire(
                "worker-new", now_ms=NOW + 60_001, ttl_seconds=60
            )
            scheduler, health = Mock(), Mock()
            runtime = FeederRuntime(
                config=FeederConfig(), scheduler=scheduler, lease_store=store,
                health=health, owner_id=old.owner,
            )
            runtime.lease_generation = old.generation

            with self.assertRaises(RuntimeError):
                runtime.stop()

            self.assertTrue(store.is_current(
                replacement.owner, replacement.generation, NOW + 60_002
            ))
            health.mark_stopped.assert_called_once()

    def test_run_once_after_shutdown_never_starts_another_sync(self):
        scheduler, leases = Mock(), Mock()
        runtime = FeederRuntime(
            config=FeederConfig(), scheduler=scheduler, lease_store=leases,
            owner_id="worker-J",
        )
        runtime.lease_generation = 15

        runtime.stop()
        runtime.run_once()

        scheduler.run_due.assert_not_called()




    def test_real_scheduler_stop_blocks_next_timeframe_and_drains_current_sync(self):
        entered = threading.Event()
        finish = threading.Event()
        calls = []

        def sync(timeframe, start_ms, end_ms):
            calls.append(timeframe)
            entered.set()
            if not finish.wait(2):
                raise TimeoutError("test did not release scheduler callback")
            return "committed"

        clock_ms = [NOW]
        scheduler = FeederScheduler(
            FeederConfig(timeframes=("15m", "1h")),
            clock=lambda: clock_ms[0],
            sync_callback=sync,
        )
        clock_ms[0] = NOW + 60 * 60 * 1000 + 5_000
        errors = []

        def run():
            try:
                scheduler.run_due()
            except Exception as error:
                errors.append(error)

        runner = threading.Thread(target=run)
        runner.start()
        self.assertTrue(entered.wait(1))

        scheduler.stop()
        self.assertEqual(scheduler.run_due(), {})
        self.assertFalse(scheduler.wait_for_idle(timeout=0.01))

        finish.set()
        runner.join(2)

        self.assertFalse(runner.is_alive())
        self.assertEqual(errors, [])
        self.assertEqual(calls, ["15m"])
        self.assertTrue(scheduler.wait_for_idle(timeout=1))
        self.assertEqual(scheduler.running_timeframes, frozenset())

    def test_runtime_shutdown_keeps_lease_until_real_scheduler_writer_finishes(self):
        import tempfile
        from pathlib import Path
        from market_data.feeder import LeaseStore

        entered = threading.Event()
        finish = threading.Event()
        calls = []

        def sync(timeframe, start_ms, end_ms):
            calls.append(timeframe)
            entered.set()
            if not finish.wait(3):
                raise TimeoutError("test did not release runtime writer")
            return "committed"

        with tempfile.TemporaryDirectory() as directory:
            store = LeaseStore(str(Path(directory) / "lease.sqlite3"))
            clock_ms = [NOW]
            scheduler = FeederScheduler(
                FeederConfig(timeframes=("15m", "1h")),
                clock=lambda: clock_ms[0],
                sync_callback=sync,
            )
            clock_ms[0] = NOW + 60 * 60 * 1000 + 5_000
            runtime = FeederRuntime(
                config=scheduler.config,
                scheduler=scheduler,
                lease_store=store,
                owner_id="runtime-worker",
                clock=lambda: NOW,
            )
            self.assertTrue(runtime.start(now_ms=NOW))
            self.assertTrue(entered.wait(1))

            shutdown_errors = []
            shutdown_done = threading.Event()

            def shutdown():
                try:
                    runtime.stop(timeout=2)
                except Exception as error:
                    shutdown_errors.append(error)
                finally:
                    shutdown_done.set()

            stopper = threading.Thread(target=shutdown)
            stopper.start()
            self.assertFalse(shutdown_done.wait(0.05))
            self.assertTrue(store.is_current(
                "runtime-worker", runtime.lease_generation, NOW + 1
            ))

            finish.set()
            stopper.join(2)

            self.assertFalse(stopper.is_alive())
            self.assertEqual(shutdown_errors, [])
            self.assertEqual(runtime.state, "STOPPED")
            self.assertFalse(store.is_current(
                "runtime-worker", runtime.lease_generation, NOW + 1
            ))
            self.assertEqual(calls, ["15m"])



class RuntimeIntegrationContractTest(unittest.TestCase):
    def test_recovery_adapter_recovers_each_configured_timeframe(self):
        calls = []
        class Coordinator:
            def __init__(self, timeframe):
                self.timeframe = timeframe
            def recover(self, timeframe, start_ms, end_ms):
                calls.append((self.timeframe, timeframe, start_ms, end_ms))
                return type("Result", (), {"complete": True})()

        now = NOW + 7_200_000 + 5_000
        adapter = RecoveryAdapter(
            coordinators={"15m": Coordinator("15m"), "1h": Coordinator("1h")},
            clock=lambda: now,
            lookback_candles=4,
            close_grace_seconds=5,
        )
        self.assertTrue(adapter.recover_all())
        self.assertEqual([call[0] for call in calls], ["15m", "1h"])
        self.assertTrue(all(call[0] == call[1] for call in calls))
        self.assertEqual(calls[0][3] % 900_000, 0)
        self.assertEqual(calls[1][3] % 3_600_000, 0)
        self.assertEqual(calls[0][3] - calls[0][2], 4 * 900_000)
        self.assertEqual(calls[1][3] - calls[1][2], 4 * 3_600_000)

    def test_recovery_adapter_fails_closed_on_incomplete_result(self):
        class Coordinator:
            def recover(self, *args):
                return type("Result", (), {"complete": False})()
        adapter = RecoveryAdapter(
            coordinators={"15m": Coordinator()},
            clock=lambda: NOW + 900_000,
            lookback_candles=2,
        )
        self.assertFalse(adapter.recover_all())

    def test_build_runtime_composes_scheduler_and_recovery_without_starting_process(self):
        from unittest.mock import Mock
        from market_data.feeder import FeederRuntime
        exchange, store, leases = Mock(), Mock(), Mock()
        runtime = build_runtime(
            config=FeederConfig(timeframes=("15m", "1h")),
            owner_id="integration-worker",
            exchange=exchange,
            store=store,
            lease_store=leases,
            clock=lambda: NOW + 7_200_000,
        )
        self.assertIsInstance(runtime, FeederRuntime)
        self.assertIsInstance(runtime.recovery, RecoveryAdapter)
        self.assertEqual(runtime.scheduler.config.timeframes, ("15m", "1h"))
        self.assertIsNone(runtime.scheduler._thread)
        # RecoveryCoordinator validates that coverage bounds echo the
        # requested aligned window; a fixed 0..900000 fixture is invalid for
        # the current bounded lookback window.
        store.read_window.side_effect = (
            lambda symbol, timeframe, start_ms, end_ms: {
                "startMs": start_ms,
                "endMs": end_ms,
                "coverage": {"complete": True, "gaps": []},
            }
        )
        self.assertTrue(runtime.recovery.recover_all())
        self.assertEqual(
            [call.args[1] for call in store.read_window.call_args_list],
            ["15m", "1h"],
        )


    def test_startup_recovery_renews_lease_before_canonical_sync_attempt(self):
        from unittest.mock import Mock, patch
        from market_data.store import INTERVAL_MS
        exchange, store, leases = Mock(), Mock(), Mock()
        leases.heartbeat.return_value = True
        interval = INTERVAL_MS["15m"]
        reads = {"count": 0}
        def read_window(symbol, timeframe, start_ms, end_ms):
            reads["count"] += 1
            gaps = ([{"startMs": start_ms, "endMs": start_ms + interval}]
                    if reads["count"] == 1 else [])
            return {
                "startMs": start_ms,
                "endMs": end_ms,
                "coverage": {"complete": not gaps, "gaps": gaps},
            }
        store.read_window.side_effect = read_window
        runtime = build_runtime(
            config=FeederConfig(timeframes=("15m",)),
            owner_id="recovery-worker",
            exchange=exchange,
            store=store,
            lease_store=leases,
            clock=lambda: NOW + 7_200_000,
        )
        runtime.lease_generation = 21
        with patch("market_data.feeder_service.sync_window", return_value=1):
            self.assertTrue(runtime.recovery.recover_all())
        leases.heartbeat.assert_called_once_with(
            "recovery-worker", 21,
            now_ms=NOW + 7_200_000,
            ttl_seconds=60,
        )


    def test_recovery_lease_is_revalidated_before_scheduler_becomes_ready(self):
        scheduler, leases, recovery, health = Mock(), Mock(), Mock(), Mock()
        leases.acquire.return_value = Mock(generation=31)
        leases.heartbeat.return_value = False
        recovery.recover_all.return_value = True
        runtime = FeederRuntime(
            config=FeederConfig(), scheduler=scheduler, lease_store=leases,
            recovery=recovery, health=health, owner_id="worker-after-recovery",
            clock=lambda: NOW + 61_000,
        )

        self.assertFalse(runtime.start(now_ms=NOW))

        self.assertEqual(runtime.state, "LEASE_LOST")
        leases.heartbeat.assert_called_once_with(
            "worker-after-recovery", 31, now_ms=NOW + 61_000, ttl_seconds=60
        )
        scheduler.start.assert_not_called()
        health.mark_ready.assert_not_called()

    def test_shutdown_after_lease_takeover_does_not_release_replacement_or_raise(self):
        import tempfile
        from pathlib import Path
        from market_data.feeder import LeaseStore

        with tempfile.TemporaryDirectory() as directory:
            leases = LeaseStore(str(Path(directory) / "leases.sqlite3"))
            old = leases.acquire("old-writer", now_ms=NOW, ttl_seconds=60)
            replacement = leases.acquire("new-writer", now_ms=NOW + 60_001, ttl_seconds=60)
            scheduler = Mock()
            runtime = FeederRuntime(
                config=FeederConfig(), scheduler=scheduler, lease_store=leases,
                owner_id=old.owner,
            )
            runtime.lease_generation = old.generation
            runtime.on_lease_lost()

            self.assertTrue(runtime.stop())
            self.assertEqual(runtime.state, "STOPPED")
            self.assertTrue(leases.is_current(
                replacement.owner, replacement.generation, NOW + 60_002
            ))

    def test_production_factory_rejects_postgres_before_constructing_runtime(self):
        import sys
        from types import SimpleNamespace
        from unittest.mock import patch
        from market_data.feeder_service import build_production_runtime

        with patch.dict(sys.modules, {"ccxt": SimpleNamespace(binanceusdm=Mock())}):
            with self.assertRaisesRegex(ValueError, "requires SQLite"):
                build_production_runtime({
                    "MARKET_DATA_BACKEND": "postgres",
                    "MARKET_DATA_DB": "/tmp/canonical.sqlite3",
                })

    def test_production_factory_rejects_separate_lease_database(self):
        import sys
        from types import SimpleNamespace
        from unittest.mock import patch
        from market_data.feeder_service import build_production_runtime

        with patch.dict(sys.modules, {"ccxt": SimpleNamespace(binanceusdm=Mock())}):
            with self.assertRaisesRegex(ValueError, "same file"):
                build_production_runtime({
                    "MARKET_DATA_BACKEND": "sqlite",
                    "MARKET_DATA_DB": "/tmp/canonical.sqlite3",
                    "T0_FEEDER_LEASE_DB": "/tmp/leases.sqlite3",
                })


if __name__ == "__main__":
    unittest.main()
