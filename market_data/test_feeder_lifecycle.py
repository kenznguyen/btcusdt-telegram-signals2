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
        import tempfile
        from pathlib import Path
        from unittest.mock import Mock
        from market_data.feeder import FeederRuntime

        with tempfile.TemporaryDirectory() as directory:
            db_path = Path(directory) / "canonical.sqlite3"
            db_path.touch()
            exchange, store, leases = Mock(), Mock(), Mock()
            store.path = db_path
            store.insert_fenced = Mock()
            store.initialize = Mock()
            leases.db_path = str(db_path)
            leases.lease_name = "binance-btcusdt-canonical"
            runtime = build_runtime(
                config=FeederConfig(timeframes=("15m", "1h")),
                owner_id="integration-worker", exchange=exchange,
                store=store, lease_store=leases,
                clock=lambda: NOW + 7_200_000,
            )
            self.assertIsInstance(runtime, FeederRuntime)
            self.assertIsInstance(runtime.recovery, RecoveryAdapter)
            self.assertEqual(runtime.scheduler.config.timeframes, ("15m", "1h"))
            self.assertIsNone(runtime.scheduler._thread)
            store.read_window.side_effect = (
                lambda symbol, timeframe, start_ms, end_ms: {
                    "startMs": start_ms, "endMs": end_ms,
                    "coverage": {"complete": True, "gaps": []},
                }
            )
            self.assertTrue(runtime.recovery.recover_all())
            self.assertEqual(
                [call.args[1] for call in store.read_window.call_args_list],
                ["15m", "1h"],
            )

    def test_startup_recovery_renews_lease_before_canonical_sync_attempt(self):
        import tempfile
        from pathlib import Path
        from unittest.mock import Mock, patch
        from market_data.store import INTERVAL_MS

        with tempfile.TemporaryDirectory() as directory:
            db_path = Path(directory) / "canonical.sqlite3"
            db_path.touch()
            exchange, store, leases = Mock(), Mock(), Mock()
            store.path = db_path
            store.insert_fenced = Mock()
            store.initialize = Mock()
            leases.db_path = str(db_path)
            leases.lease_name = "binance-btcusdt-canonical"
            leases.heartbeat.return_value = True
            interval = INTERVAL_MS["15m"]
            reads = {"count": 0}

            def read_window(symbol, timeframe, start_ms, end_ms):
                reads["count"] += 1
                gaps = ([{"startMs": start_ms, "endMs": start_ms + interval}]
                        if reads["count"] == 1 else [])
                return {
                    "startMs": start_ms, "endMs": end_ms,
                    "coverage": {"complete": not gaps, "gaps": gaps},
                }

            store.read_window.side_effect = read_window
            runtime = build_runtime(
                config=FeederConfig(timeframes=("15m",)),
                owner_id="recovery-worker", exchange=exchange,
                store=store, lease_store=leases,
                clock=lambda: NOW + 7_200_000,
            )
            runtime.lease_generation = 21
            with patch("market_data.feeder_service.sync_window", return_value=1):
                self.assertTrue(runtime.recovery.recover_all())
            leases.heartbeat.assert_called_once_with(
                "recovery-worker", 21,
                now_ms=NOW + 7_200_000, ttl_seconds=60,
            )

    def test_build_runtime_recovers_real_temp_sqlite_before_readiness_and_reuses_gateway(self):
        import tempfile
        from pathlib import Path
        from unittest.mock import patch

        from market_data.feeder import HealthEvaluator, LeaseStore
        from market_data.feeder_service import build_runtime
        from market_data.storage import SQLiteCandleStore
        from market_data.store import INTERVAL_MS, read_window
        from market_data.sync import sync_window

        interval = INTERVAL_MS["15m"]
        aligned_now = (NOW // interval) * interval + 5_000
        recovery_end = aligned_now - 5_000
        recovery_start = recovery_end - interval
        entered_sync = threading.Event()
        allow_sync = threading.Event()
        gateway_instances = []
        events = []
        exchange_calls = []

        class SyntheticExchange:
            id = "binanceusdm"

            def load_markets(self):
                return {
                    "BTC/USDT:USDT": {
                        "symbol": "BTC/USDT:USDT",
                        "id": "BTCUSDT",
                        "base": "BTC",
                        "quote": "USDT",
                        "settle": "USDT",
                        "active": True,
                        "swap": True,
                        "linear": True,
                        "spot": False,
                    }
                }

            def fetch_time(self):
                return aligned_now + 1_000

            def fetch_ohlcv(self, symbol, timeframe, since, limit, params):
                exchange_calls.append((symbol, timeframe, since, limit, params))
                entered_sync.set()
                if not allow_sync.wait(3):
                    raise TimeoutError("synthetic recovery barrier timed out")
                return [[since, 100.0, 101.0, 99.0, 100.5, 1.0]]

        def snapshot(db_path):
            result = read_window(
                db_path, "BTCUSDT", "15m", recovery_start, recovery_end
            )
            candle = result["candles"][-1] if result["candles"] else None
            return {
                "storage_readable": True,
                "storage_writable": True,
                "fatal_error": False,
                "m15": {
                    "latest_closed_candle_close_ms": (
                        candle["closeTimeMs"] if candle else None
                    ),
                    "last_successful_sync_ms": aligned_now if candle else None,
                    "unresolved_gap_count": len(result["coverage"]["gaps"]),
                    "sync_error": None,
                },
            }

        with tempfile.TemporaryDirectory(prefix="t0-build-runtime-") as directory:
            db_path = Path(directory) / "isolated-build-runtime.sqlite3"
            store = SQLiteCandleStore(db_path)
            leases = LeaseStore(str(db_path))
            config = FeederConfig(
                timeframes=("15m",),
                close_grace_seconds=5,
                lease_ttl_seconds=60,
                lease_heartbeat_seconds=15,
            )
            runtime = build_runtime(
                config=config,
                owner_id="build-runtime-integration",
                exchange=SyntheticExchange(),
                store=store,
                lease_store=leases,
                clock=lambda: aligned_now,
                event_sink=events.append,
                recovery_lookback_candles=1,
            )
            evaluator = HealthEvaluator(config)

            before = evaluator.evaluate(
                runtime.health_snapshot(snapshot(db_path)),
                now_ms=aligned_now + 5_000,
            )
            self.assertEqual(runtime.state, "NEW")
            self.assertEqual(before.state, "STARTING")
            self.assertFalse(before.ready)

            original_sync = sync_window

            def capture_sync(exchange, gateway, timeframe, start_ms, end_ms, now_ms=None):
                gateway_instances.append(gateway)
                return original_sync(
                    exchange, gateway, timeframe, start_ms, end_ms, now_ms=now_ms
                )

            start_results = []
            start_errors = []

            def start_runtime():
                try:
                    start_results.append(runtime.start(now_ms=aligned_now))
                except Exception as error:
                    start_errors.append(error)

            with patch("market_data.feeder_service.sync_window", side_effect=capture_sync):
                starter = threading.Thread(target=start_runtime)
                starter.start()
                try:
                    self.assertTrue(
                        entered_sync.wait(2),
                        "startup recovery never reached the synthetic exchange",
                    )
                    self.assertEqual(runtime.state, "STARTING")
                    during = evaluator.evaluate(
                        runtime.health_snapshot(snapshot(db_path)),
                        now_ms=aligned_now + 5_000,
                    )
                    self.assertEqual(during.state, "STARTING")
                    self.assertTrue(during.live)
                    self.assertFalse(during.ready)
                finally:
                    allow_sync.set()
                    starter.join(5)

                self.assertFalse(starter.is_alive(), "runtime startup did not finish")
                self.assertEqual(start_errors, [])
                self.assertEqual(start_results, [True])
                self.assertEqual(runtime.state, "RUNNING")

                recovered = read_window(
                    db_path, "BTCUSDT", "15m", recovery_start, recovery_end
                )
                self.assertTrue(recovered["coverage"]["complete"])
                self.assertEqual(recovered["coverage"]["returned"], 1)
                self.assertEqual(len(gateway_instances), 1)

                after = evaluator.evaluate(
                    runtime.health_snapshot(snapshot(db_path)),
                    now_ms=aligned_now + 5_000,
                )
                self.assertEqual(after.state, "HEALTHY")
                self.assertTrue(after.ready)

                # Exercise the scheduler's own guarded callback against the
                # same synthetic window; duplicate candle is idempotent.
                self.assertEqual(
                    runtime.scheduler.sync_callback(
                        "15m", recovery_start, recovery_end
                    ),
                    0,
                )
                self.assertEqual(len(gateway_instances), 2)
                self.assertIs(gateway_instances[0], gateway_instances[1])
                self.assertEqual(exchange_calls[0][1], "15m")
                self.assertEqual(exchange_calls[1][1], "15m")
                self.assertLess(events.index("recovery_completed"), events.index("ready"))

                self.assertTrue(runtime.stop(timeout=2))
                self.assertEqual(runtime.state, "STOPPED")
                self.assertFalse(leases.is_current(
                    "build-runtime-integration",
                    runtime.lease_generation,
                    aligned_now + 5_001,
                ))

    def test_scheduler_and_recovery_share_the_same_gateway(self):
        import tempfile
        from pathlib import Path
        from unittest.mock import Mock, patch
        from market_data.write_gateway import SQLiteWriteGateway

        with tempfile.TemporaryDirectory() as directory:
            db_path = Path(directory) / "canonical.sqlite3"
            db_path.touch()
            store, leases = Mock(), Mock()
            store.path = db_path
            store.initialize = Mock()
            leases.db_path = str(db_path)
            leases.lease_name = "binance-btcusdt-canonical"
            leases.authorize_write.return_value = True
            leases.heartbeat.return_value = True
            runtime = build_runtime(
                config=FeederConfig(timeframes=("15m",)),
                owner_id="gateway-composition-worker",
                exchange=Mock(), store=store, lease_store=leases,
                clock=lambda: NOW + 900_100,
            )
            runtime.lease_generation = 9
            with patch("market_data.feeder_service.sync_window", return_value=1) as sync:
                self.assertEqual(runtime.scheduler.sync_callback("15m", 0, 900_000), 1)
                self.assertEqual(
                    runtime.recovery.coordinators["15m"].sync_callback("15m", 0, 900_000),
                    1,
                )
            self.assertEqual(sync.call_count, 2)
            scheduler_gateway = sync.call_args_list[0].args[1]
            recovery_gateway = sync.call_args_list[1].args[1]
            self.assertIsInstance(scheduler_gateway, SQLiteWriteGateway)
            self.assertIs(scheduler_gateway, recovery_gateway)
            self.assertEqual(scheduler_gateway.db_path, str(db_path))
            leases.authorize_write.assert_called_once()
            leases.heartbeat.assert_called_once()


    def test_build_runtime_incomplete_recovery_never_opens_ready_and_releases_idle_lease(self):
        import sqlite3
        import tempfile
        from pathlib import Path

        from market_data.feeder import HealthEvaluator, LeaseStore, RecoveryIncompleteError
        from market_data.feeder_service import build_runtime
        from market_data.storage import SQLiteCandleStore
        from market_data.store import INTERVAL_MS, read_window

        interval = INTERVAL_MS["15m"]
        aligned_now = (NOW // interval) * interval + 5_000
        recovery_end = aligned_now - 5_000
        recovery_start = recovery_end - interval

        class EmptySyntheticExchange:
            id = "binanceusdm"

            def load_markets(self):
                return {
                    "BTC/USDT:USDT": {
                        "symbol": "BTC/USDT:USDT", "id": "BTCUSDT",
                        "base": "BTC", "quote": "USDT", "settle": "USDT",
                        "active": True, "swap": True, "linear": True, "spot": False,
                    }
                }

            def fetch_time(self):
                return aligned_now + 1_000

            def fetch_ohlcv(self, symbol, timeframe, since, limit, params):
                return []

        with tempfile.TemporaryDirectory(prefix="t0-recovery-incomplete-") as directory:
            db_path = Path(directory) / "isolated-incomplete.sqlite3"
            store = SQLiteCandleStore(db_path)
            leases = LeaseStore(str(db_path))
            config = FeederConfig(
                timeframes=("15m",), close_grace_seconds=5,
                lease_ttl_seconds=60, lease_heartbeat_seconds=15,
            )
            runtime = build_runtime(
                config=config, owner_id="incomplete-recovery-worker",
                exchange=EmptySyntheticExchange(), store=store,
                lease_store=leases, clock=lambda: aligned_now,
                recovery_lookback_candles=1,
            )
            evaluator = HealthEvaluator(config)

            with self.assertRaises(RecoveryIncompleteError):
                runtime.start(now_ms=aligned_now)

            self.assertEqual(runtime.state, "FAILED")
            self.assertIsNone(runtime.scheduler._thread)
            self.assertFalse(leases.is_current(
                "incomplete-recovery-worker", runtime.lease_generation,
                aligned_now + 1,
            ))
            result = read_window(
                db_path, "BTCUSDT", "15m", recovery_start, recovery_end
            )
            self.assertFalse(result["coverage"]["complete"])
            health = evaluator.evaluate(
                runtime.health_snapshot({
                    "storage_readable": True,
                    "storage_writable": True,
                    "fatal_error": False,
                    "m15": {
                        "latest_closed_candle_close_ms": None,
                        "last_successful_sync_ms": None,
                        "unresolved_gap_count": len(result["coverage"]["gaps"]),
                        "sync_error": None,
                    },
                }),
                now_ms=aligned_now + 5_000,
            )
            self.assertFalse(health.ready)
            self.assertEqual(health.state, "FAILED")

    def test_build_runtime_lease_takeover_between_recovery_pages_blocks_next_write_and_ready(self):
        import sqlite3
        import tempfile
        from pathlib import Path
        from unittest.mock import patch

        from market_data.feeder import HealthEvaluator, LeaseStore
        from market_data.feeder_service import build_runtime
        from market_data.storage import SQLiteCandleStore
        from market_data.store import INTERVAL_MS, read_window
        from market_data.sync import sync_window

        interval = INTERVAL_MS["15m"]
        aligned_now = (NOW // interval) * interval + 5_000
        recovery_end = aligned_now - 5_000
        recovery_start = recovery_end - 3 * interval
        middle_open = recovery_start + interval
        exchange_calls = []
        recovery_pages = []
        replacement_leases = []

        class SyntheticExchange:
            id = "binanceusdm"

            def load_markets(self):
                return {
                    "BTC/USDT:USDT": {
                        "symbol": "BTC/USDT:USDT", "id": "BTCUSDT",
                        "base": "BTC", "quote": "USDT", "settle": "USDT",
                        "active": True, "swap": True, "linear": True, "spot": False,
                    }
                }

            def fetch_time(self):
                return aligned_now + 1_000

            def fetch_ohlcv(self, symbol, timeframe, since, limit, params):
                exchange_calls.append((timeframe, since))
                return [[since, 100.0, 101.0, 99.0, 100.5, 1.0]]

        with tempfile.TemporaryDirectory(prefix="t0-recovery-lease-loss-") as directory:
            db_path = Path(directory) / "isolated-lease-loss.sqlite3"
            store = SQLiteCandleStore(db_path)
            store.initialize()
            leases = LeaseStore(str(db_path))
            with sqlite3.connect(db_path) as connection:
                connection.execute(
                    """INSERT INTO candles
                       (exchange, market_type, symbol, timeframe, open_time_ms,
                        open, high, low, close, volume, available_at_ms)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    ("binance", "USDT_PERPETUAL", "BTCUSDT", "15m", middle_open,
                     "100", "101", "99", "100", "1", middle_open + interval),
                )

            initial_coverage = read_window(
                db_path, "BTCUSDT", "15m", recovery_start, recovery_end
            )
            self.assertEqual(len(initial_coverage["coverage"]["gaps"]), 2)

            config = FeederConfig(
                timeframes=("15m",), close_grace_seconds=5,
                lease_ttl_seconds=60, lease_heartbeat_seconds=15,
            )
            events = []
            runtime = build_runtime(
                config=config, owner_id="recovery-owner",
                exchange=SyntheticExchange(), store=store,
                lease_store=leases, clock=lambda: aligned_now,
                event_sink=events.append,
                recovery_lookback_candles=3,
            )
            evaluator = HealthEvaluator(config)
            original_sync = sync_window

            def sync_then_transfer_lease(exchange, gateway, timeframe, start_ms, end_ms, now_ms=None):
                result = original_sync(
                    exchange, gateway, timeframe, start_ms, end_ms, now_ms=now_ms
                )
                recovery_pages.append((start_ms, end_ms, result))
                if len(recovery_pages) == 1:
                    replacement = leases.acquire(
                        "replacement-owner", now_ms=aligned_now + 60_001,
                        ttl_seconds=60,
                    )
                    replacement_leases.append(replacement)
                return result

            with patch(
                "market_data.feeder_service.sync_window",
                side_effect=sync_then_transfer_lease,
            ):
                with self.assertRaises(RuntimeError):
                    runtime.start(now_ms=aligned_now)

            self.assertEqual(len(recovery_pages), 1)
            self.assertEqual(len(exchange_calls), 1)
            self.assertEqual(runtime.state, "LEASE_LOST")
            self.assertIn("lease_lost", events)
            self.assertIsNotNone(replacement_leases[0])
            replacement = replacement_leases[0]
            self.assertTrue(leases.is_current(
                "replacement-owner", replacement.generation, aligned_now + 60_002
            ))
            self.assertFalse(leases.is_current(
                "recovery-owner", runtime.lease_generation, aligned_now + 60_002
            ))

            stored = read_window(
                db_path, "BTCUSDT", "15m", recovery_start, recovery_end
            )
            self.assertEqual(stored["coverage"]["returned"], 2)
            self.assertEqual(
                [candle["openTimeMs"] for candle in stored["candles"]],
                [recovery_start, middle_open],
            )
            health = evaluator.evaluate(
                runtime.health_snapshot({
                    "storage_readable": True,
                    "storage_writable": True,
                    "fatal_error": False,
                    "m15": {
                        "latest_closed_candle_close_ms": (
                            stored["candles"][-1]["closeTimeMs"]
                        ),
                        "last_successful_sync_ms": aligned_now,
                        "unresolved_gap_count": len(stored["coverage"]["gaps"]),
                        "sync_error": None,
                    },
                }),
                now_ms=aligned_now + 5_000,
            )
            self.assertFalse(health.ready)
            self.assertNotEqual(health.state, "HEALTHY")
            self.assertIsNone(runtime.scheduler._thread)


if __name__ == "__main__":
    unittest.main()
