"""PostgreSQL-backed FeederRuntime lifecycle acceptance on disposable TimescaleDB.

These tests deliberately exercise the real DB-clock lease adapter and runtime
heartbeat/shutdown lifecycle. They never connect to an exchange or production DB.
"""
import os
import time
import unittest
import uuid

from market_data.feeder import FeederConfig, FeederRuntime
from market_data.feeder_service import PostgresRuntimeLeaseAdapter
from market_data.postgres import PostgresLeaseStore, connection


DSN = os.environ.get("MARKET_DATA_TEST_DATABASE_URL", "")


class _LifecycleScheduler:
    def __init__(self, *, drain=True):
        self.drain = drain
        self.started = False
        self.stopped = False

    def run_due(self):
        return {}

    def start(self):
        self.started = True
        return True

    def stop(self):
        self.stopped = True
        return True

    def wait_for_idle(self, timeout=None):
        return self.drain


@unittest.skipUnless(DSN, "Set the disposable local TimescaleDB test service")
class PostgresFeederRuntimeLifecycleIntegrationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from market_data.migrations import migrate
        from market_data.test_postgres_write_gateway import _assert_disposable_target

        _assert_disposable_target()
        cls.dsn = DSN
        migrate(cls.dsn)

    def setUp(self):
        self.lease_name = "binance-btcusdt-canonical"
        self.backend = PostgresLeaseStore(self.dsn, lease_name=self.lease_name)
        self.adapter = PostgresRuntimeLeaseAdapter(self.backend)

    def tearDown(self):
        with connection(self.dsn) as database:
            database.execute(
                "DELETE FROM market_data.feeder_leases WHERE lease_name=%s",
                (self.lease_name,),
            )

    @staticmethod
    def _runtime(adapter, owner, *, ttl=8, heartbeat=1, scheduler=None):
        config = FeederConfig(
            timeframes=("15m",),
            lease_ttl_seconds=ttl,
            lease_heartbeat_seconds=heartbeat,
        )
        return FeederRuntime(
            config=config,
            scheduler=scheduler or _LifecycleScheduler(),
            lease_store=adapter,
            owner_id=owner,
        )

    def test_heartbeat_renews_postgres_lease_using_database_clock(self):
        owner = "heartbeat-" + uuid.uuid4().hex
        runtime = self._runtime(self.adapter, owner, ttl=8, heartbeat=1)
        try:
            self.assertTrue(runtime.start())
            with connection(self.dsn, read_only=True) as database:
                before = database.execute(
                    "SELECT expires_at FROM market_data.feeder_leases WHERE lease_name=%s",
                    (self.lease_name,),
                ).fetchone()[0]
            time.sleep(1.3)
            with connection(self.dsn, read_only=True) as database:
                after = database.execute(
                    "SELECT expires_at FROM market_data.feeder_leases WHERE lease_name=%s",
                    (self.lease_name,),
                ).fetchone()[0]
            self.assertGreater(after, before)
            self.assertEqual(runtime.state, "RUNNING")
            self.assertTrue(self.backend.is_current(owner, runtime.lease_generation))
        finally:
            runtime.stop(timeout=3)

    def test_expired_runtime_lease_takeover_closes_old_runtime_readiness(self):
        old_owner = "old-" + uuid.uuid4().hex
        new_owner = "new-" + uuid.uuid4().hex
        scheduler = _LifecycleScheduler()
        runtime = self._runtime(self.adapter, old_owner, ttl=8, heartbeat=1,
                                scheduler=scheduler)
        self.assertTrue(runtime.start())
        old_generation = runtime.lease_generation
        replacement = None
        try:
            with connection(self.dsn) as database:
                database.execute(
                    """UPDATE market_data.feeder_leases
                       SET expires_at=clock_timestamp() - interval '1 second'
                       WHERE lease_name=%s AND owner_id=%s AND generation=%s""",
                    (self.lease_name, old_owner, old_generation),
                )
            replacement = self.backend.acquire(new_owner, ttl_seconds=8)
            self.assertIsNotNone(replacement)
            self.assertGreater(replacement.generation, old_generation)

            deadline = time.monotonic() + 4
            while runtime.state != "LEASE_LOST" and time.monotonic() < deadline:
                time.sleep(0.05)
            self.assertEqual(runtime.state, "LEASE_LOST")
            self.assertTrue(scheduler.stopped)
            now_ms = time.time_ns() // 1_000_000
            snapshot = runtime.health_snapshot({
                "storage_readable": True,
                "storage_writable": True,
                "startup_complete": True,
                "m15": {"latest_closed_candle_close_ms": now_ms,
                        "last_successful_sync_ms": now_ms,
                        "unresolved_gap_count": 0, "sync_error": None},
            })
            from market_data.feeder import HealthEvaluator
            health = HealthEvaluator(FeederConfig(timeframes=("15m",))).evaluate(
                snapshot, now_ms=now_ms
            )
            self.assertIs(snapshot["lease_valid"], False)
            self.assertFalse(health.ready)
            # A drained old runtime must stop cleanly without releasing or
            # disturbing the replacement owner's fencing generation.
            self.assertTrue(runtime.stop(timeout=3))
        finally:
            # Always drain/join the old runtime, including on assertion failure.
            runtime.stop(timeout=3)
            # A lost owner must never release the replacement generation.
            if replacement is not None:
                replacement_is_current = self.backend.is_current(
                    new_owner, replacement.generation
                )
                self.assertTrue(replacement_is_current)
                if replacement_is_current:
                    self.backend.release(new_owner, replacement.generation)

    def test_shutdown_drain_timeout_retains_current_lease(self):
        owner = "drain-" + uuid.uuid4().hex
        scheduler = _LifecycleScheduler(drain=False)
        runtime = self._runtime(self.adapter, owner, scheduler=scheduler)
        self.assertTrue(runtime.start())
        generation = runtime.lease_generation
        with self.assertRaises(TimeoutError):
            runtime.stop(timeout=0.01)
        self.assertTrue(self.backend.is_current(owner, generation))
        scheduler.drain = True
        self.assertTrue(runtime.stop(timeout=1))
        self.assertFalse(self.backend.is_current(owner, generation))

    def test_runtime_does_not_resume_after_transient_heartbeat_outage(self):
        from unittest.mock import Mock
        from market_data.feeder import FeederConfig, FeederRuntime
        from market_data.postgres import StoreUnavailable, connection

        class FailOnceHeartbeatAdapter:
            def __init__(self, backend):
                self.backend = PostgresRuntimeLeaseAdapter(backend)
                self.heartbeat_calls = 0

            def acquire(self, owner, *, now_ms=None, ttl_seconds=60):
                return self.backend.acquire(
                    owner, now_ms=now_ms, ttl_seconds=ttl_seconds
                )

            def heartbeat(self, owner, generation, *, now_ms=None, ttl_seconds=60):
                self.heartbeat_calls += 1
                if self.heartbeat_calls == 1:
                    raise StoreUnavailable("simulated transient PostgreSQL outage")
                return self.backend.heartbeat(
                    owner, generation, now_ms=now_ms, ttl_seconds=ttl_seconds
                )

            def release(self, owner, generation):
                return self.backend.release(owner, generation)

            def is_current(self, owner, generation, *, now_ms=None):
                return self.backend.is_current(owner, generation, now_ms=now_ms)

        old_owner = "outage-old-" + uuid.uuid4().hex
        new_owner = "outage-new-" + uuid.uuid4().hex
        old_scheduler = _LifecycleScheduler()
        health = Mock()
        flaky = FailOnceHeartbeatAdapter(self.backend)
        config = FeederConfig(
            timeframes=("15m",),
            lease_ttl_seconds=8,
            lease_heartbeat_seconds=1,
        )
        old_runtime = FeederRuntime(
            config=config,
            scheduler=old_scheduler,
            lease_store=flaky,
            owner_id=old_owner,
            health=health,
        )

        self.assertTrue(old_runtime.start())
        old_generation = old_runtime.lease_generation
        try:
            deadline = time.monotonic() + 4
            while old_runtime.state != "LEASE_LOST" and time.monotonic() < deadline:
                time.sleep(0.05)
            self.assertEqual(old_runtime.state, "LEASE_LOST")
            self.assertTrue(old_scheduler.stopped)
            health.mark_not_ready.assert_called_once()

            # The adapter now delegates to the healthy PostgreSQL backend, but
            # the old heartbeat loop has terminated and must not self-resume.
            time.sleep(1.2)
            self.assertEqual(flaky.heartbeat_calls, 1)
            self.assertEqual(old_runtime.state, "LEASE_LOST")

            with connection(self.dsn) as database:
                database.execute(
                    """UPDATE market_data.feeder_leases
                       SET expires_at=clock_timestamp() - interval '1 second'
                       WHERE lease_name=%s AND owner_id=%s AND generation=%s""",
                    (self.lease_name, old_owner, old_generation),
                )

            new_runtime = self._runtime(self.adapter, new_owner, ttl=8, heartbeat=1)
            try:
                self.assertTrue(new_runtime.start())
                self.assertGreater(new_runtime.lease_generation, old_generation)
                self.assertEqual(old_runtime.state, "LEASE_LOST")
                self.assertTrue(
                    self.backend.is_current(new_owner, new_runtime.lease_generation)
                )
                self.assertTrue(old_runtime.stop(timeout=3))
                self.assertTrue(
                    self.backend.is_current(new_owner, new_runtime.lease_generation)
                )
            finally:
                new_runtime.stop(timeout=3)
        finally:
            old_runtime.stop(timeout=3)

    def test_restart_acquires_a_strictly_new_fencing_generation(self):
        owner_one = "restart-one-" + uuid.uuid4().hex
        owner_two = "restart-two-" + uuid.uuid4().hex
        first = self._runtime(self.adapter, owner_one)
        self.assertTrue(first.start())
        first_generation = first.lease_generation
        self.assertTrue(first.stop(timeout=3))

        second = self._runtime(self.adapter, owner_two)
        try:
            self.assertTrue(second.start())
            self.assertGreater(second.lease_generation, first_generation)
            self.assertFalse(self.backend.is_current(owner_one, first_generation))
            self.assertTrue(self.backend.is_current(owner_two, second.lease_generation))
        finally:
            second.stop(timeout=3)


@unittest.skipUnless(DSN, "Set the disposable local TimescaleDB test service")
class PostgresConnectionTimeoutContractTest(unittest.TestCase):
    def test_connection_timeout_bounds_concurrent_unresponsive_handshakes(self):
        import socket
        import threading
        from concurrent.futures import ThreadPoolExecutor
        from market_data.postgres import StoreUnavailable, connection

        connection_count = 3
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener.bind(("127.0.0.1", 0))
        listener.listen(connection_count)
        listener.settimeout(8)
        port = listener.getsockname()[1]
        release_server = threading.Event()
        accepted = []
        server_errors = []

        def hold_startup_handshakes():
            try:
                for _ in range(connection_count):
                    client, _ = listener.accept()
                    accepted.append(client)
                release_server.wait(8)
            except Exception as error:
                server_errors.append(error)
            finally:
                for client in accepted:
                    client.close()
                listener.close()

        server = threading.Thread(target=hold_startup_handshakes, daemon=True)
        server.start()
        dsn = (
            f"postgresql://timeout_test:timeout_test@127.0.0.1:{port}/t0_timeout"
            "?sslmode=disable"
        )

        def attempt_connection():
            with connection(dsn):
                self.fail("unresponsive PostgreSQL handshake unexpectedly succeeded")

        started = time.monotonic()
        try:
            with ThreadPoolExecutor(max_workers=connection_count) as pool:
                futures = [pool.submit(attempt_connection) for _ in range(connection_count)]
                for future in futures:
                    with self.assertRaises(StoreUnavailable):
                        future.result(timeout=7)
            elapsed = time.monotonic() - started
            self.assertEqual(len(accepted), connection_count)
            self.assertLess(elapsed, 7.0)
            self.assertFalse(server_errors)
        finally:
            release_server.set()
            server.join(timeout=1)


if __name__ == "__main__":
    unittest.main()
