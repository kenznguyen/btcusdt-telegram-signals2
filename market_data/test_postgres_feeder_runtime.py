"""Runtime compatibility contracts for PostgreSQL's DB-clock lease authority.

These RED contracts ensure FeederRuntime's legacy now_ms arguments never become
PostgreSQL lease authority. The adapter must delegate expiry decisions to
PostgresLeaseStore, which uses clock_timestamp().
"""
import unittest
from unittest.mock import Mock

from market_data.feeder_service import PostgresRuntimeLeaseAdapter


class PostgresLeaseTokenSafetyTest(unittest.TestCase):
    def test_owner_capability_is_not_exposed_by_lease_repr(self):
        from datetime import datetime, timezone
        from market_data.postgres import PostgresLease

        token = "opaque-owner-capability-do-not-log"
        lease = PostgresLease(token, 7, datetime.now(timezone.utc))
        self.assertNotIn(token, repr(lease))


class PostgresRuntimeLeaseAdapterContractTest(unittest.TestCase):
    def setUp(self):
        self.backend = Mock()
        self.adapter = PostgresRuntimeLeaseAdapter(self.backend)

    def test_acquire_ignores_runtime_clock_and_delegates_ttl(self):
        lease = object()
        self.backend.acquire.return_value = lease

        result = self.adapter.acquire(
            "worker-a", now_ms=1, ttl_seconds=37
        )

        self.assertIs(result, lease)
        self.backend.acquire.assert_called_once_with("worker-a", ttl_seconds=37)

    def test_heartbeat_ignores_runtime_clock_and_delegates_generation(self):
        self.backend.heartbeat.return_value = True

        result = self.adapter.heartbeat(
            "worker-a", 9, now_ms=1, ttl_seconds=41
        )

        self.assertTrue(result)
        self.backend.heartbeat.assert_called_once_with(
            "worker-a", 9, ttl_seconds=41
        )

    def test_current_and_write_authorization_use_database_clock(self):
        self.backend.is_current.return_value = True

        self.assertTrue(self.adapter.is_current(
            "worker-a", 9, now_ms=1
        ))
        self.assertTrue(self.adapter.authorize_write(
            "worker-a", 9, now_ms=2
        ))
        self.assertEqual(self.backend.is_current.call_args_list, [
            unittest.mock.call("worker-a", 9),
            unittest.mock.call("worker-a", 9),
        ])

    def test_release_remains_bound_to_exact_owner_and_generation(self):
        self.backend.release.return_value = True

        self.assertTrue(self.adapter.release("worker-a", 9))
        self.backend.release.assert_called_once_with("worker-a", 9)


class PostgresRuntimeCompositionContractTest(unittest.TestCase):
    def test_build_runtime_routes_scheduler_and_recovery_through_one_postgres_gateway(self):
        from unittest.mock import patch
        from market_data.feeder import FeederConfig
        from market_data.feeder_service import build_runtime
        from market_data.postgres import PostgresLeaseStore, PostgresWriteGateway
        from market_data.storage import PostgresStore

        dsn = "postgresql://test:test@127.0.0.1:5432/t0_test"
        store = PostgresStore(dsn)
        lease_store = PostgresLeaseStore(dsn, lease_name="test-canonical")
        lease_store.is_current = Mock(return_value=True)
        lease_store.heartbeat = Mock(return_value=True)
        runtime = build_runtime(
            config=FeederConfig(timeframes=("15m",)),
            owner_id="worker-a",
            exchange=object(),
            store=store,
            lease_store=lease_store,
            clock=lambda: 1_800_000_000_000,
        )

        self.assertIsInstance(runtime.canonical_write_gateway, PostgresWriteGateway)
        self.assertIs(runtime.lease_store.backend, lease_store)
        self.assertEqual(runtime.canonical_write_gateway.location, dsn)
        self.assertEqual(runtime.canonical_write_gateway.lease_name, "test-canonical")
        runtime.lease_generation = 7
        observed = []

        def fake_sync(exchange_arg, gateway, timeframe, start_ms, end_ms, now_ms=None):
            observed.append(gateway)
            return 0

        with patch("market_data.feeder_service.sync_window", side_effect=fake_sync):
            runtime.scheduler.sync_callback("15m", 0, 900_000)
            coordinator = runtime.recovery.coordinators["15m"]
            coordinator.sync_callback("15m", 0, 900_000)

        self.assertEqual(len(observed), 2)
        self.assertIs(observed[0], runtime.canonical_write_gateway)
        self.assertIs(observed[1], runtime.canonical_write_gateway)
        self.assertIs(observed[0], observed[1])
        lease_store.is_current.assert_called_once_with("worker-a", 7)
        lease_store.heartbeat.assert_called_once_with("worker-a", 7, ttl_seconds=60)

    def test_build_runtime_rejects_postgres_store_with_sqlite_lease(self):
        from market_data.feeder import FeederConfig, LeaseStore
        from market_data.feeder_service import build_runtime
        from market_data.storage import PostgresStore

        sqlite_lease = LeaseStore("/tmp/isolated-test-lease.sqlite")
        with self.assertRaisesRegex(ValueError, "PostgreSQL store and lease"):
            build_runtime(
                config=FeederConfig(timeframes=("15m",)),
                owner_id="worker-a",
                exchange=object(),
                store=PostgresStore("postgresql://test:test@127.0.0.1:5432/t0_test"),
                lease_store=sqlite_lease,
                clock=lambda: 1_800_000_000_000,
            )

    def test_build_runtime_rejects_postgres_lease_on_different_dsn(self):
        from market_data.feeder import FeederConfig
        from market_data.feeder_service import build_runtime
        from market_data.postgres import PostgresLeaseStore
        from market_data.storage import PostgresStore

        with self.assertRaisesRegex(ValueError, "share the same DSN"):
            build_runtime(
                config=FeederConfig(timeframes=("15m",)),
                owner_id="worker-a",
                exchange=object(),
                store=PostgresStore("postgresql://test:test@127.0.0.1:5432/t0_a"),
                lease_store=PostgresLeaseStore("postgresql://test:test@127.0.0.1:5432/t0_b"),
                clock=lambda: 1_800_000_000_000,
            )

    def test_production_runtime_selects_postgres_lease_on_same_dsn(self):
        import sys
        from types import SimpleNamespace
        from unittest.mock import patch
        from market_data.feeder_service import build_production_runtime
        from market_data.postgres import PostgresLeaseStore, PostgresWriteGateway

        dsn = "postgresql://test:test@127.0.0.1:5432/t0_test"
        fake_ccxt = SimpleNamespace(binanceusdm=lambda options: SimpleNamespace(options=options))
        environment = {
            "MARKET_DATA_BACKEND": "postgres",
            "MARKET_DATA_POSTGRES_DSN": dsn,
            "T0_FEEDER_LEASE_NAME": "binance-btcusdt-canonical",
        }
        with patch.dict(sys.modules, {"ccxt": fake_ccxt}):
            runtime = build_production_runtime(environment)

        self.assertGreaterEqual(len(runtime.owner_id), 32)
        self.assertIsInstance(runtime.lease_store.backend, PostgresLeaseStore)
        self.assertEqual(runtime.lease_store.backend.location, dsn)
        self.assertEqual(runtime.lease_store.backend.lease_name, "binance-btcusdt-canonical")
        self.assertIsInstance(runtime.canonical_write_gateway, PostgresWriteGateway)
        self.assertEqual(runtime.canonical_write_gateway.location, dsn)


    def test_production_runtime_rejects_configured_shared_owner_id(self):
        import sys
        from types import SimpleNamespace
        from unittest.mock import patch
        from market_data.feeder_service import build_production_runtime

        fake_ccxt = SimpleNamespace(binanceusdm=lambda options: SimpleNamespace(options=options))
        environment = {
            "MARKET_DATA_BACKEND": "postgres",
            "MARKET_DATA_POSTGRES_DSN": "postgresql://test:test@127.0.0.1:5432/t0_test",
            "T0_FEEDER_OWNER_ID": "shared-seed",
        }
        with patch.dict(sys.modules, {"ccxt": fake_ccxt}):
            with self.assertRaisesRegex(ValueError, "generated per process"):
                build_production_runtime(environment)

    def test_production_runtime_generates_fresh_opaque_owner_token(self):
        import sys
        from types import SimpleNamespace
        from unittest.mock import patch
        from market_data.feeder_service import build_production_runtime

        dsn = "postgresql://test:test@127.0.0.1:5432/t0_test"
        fake_ccxt = SimpleNamespace(binanceusdm=lambda options: SimpleNamespace(options=options))
        environment = {
            "MARKET_DATA_BACKEND": "postgres",
            "MARKET_DATA_POSTGRES_DSN": dsn,
            "T0_FEEDER_LEASE_NAME": "binance-btcusdt-canonical",
        }
        with patch.dict(sys.modules, {"ccxt": fake_ccxt}):
            first = build_production_runtime(environment)
            second = build_production_runtime(environment)

        self.assertNotEqual(first.owner_id, second.owner_id)
        self.assertGreaterEqual(len(first.owner_id), 32)
        self.assertEqual(first.canonical_write_gateway.owner_id, first.owner_id)

    def test_production_runtime_rejects_noncanonical_postgres_lease_name(self):
        import sys
        from types import SimpleNamespace
        from unittest.mock import patch
        from market_data.feeder_service import build_production_runtime

        fake_ccxt = SimpleNamespace(binanceusdm=lambda options: SimpleNamespace(options=options))
        environment = {
            "MARKET_DATA_BACKEND": "postgres",
            "MARKET_DATA_POSTGRES_DSN": "postgresql://test:test@127.0.0.1:5432/t0_test",
            "T0_FEEDER_LEASE_NAME": "second-writer-lease",
        }
        with patch.dict(sys.modules, {"ccxt": fake_ccxt}):
            with self.assertRaisesRegex(ValueError, "fixed canonical lease identity"):
                build_production_runtime(environment)

    def test_production_runtime_rejects_sqlite_lease_path_for_postgres(self):
        import sys
        from types import SimpleNamespace
        from unittest.mock import patch
        from market_data.feeder_service import build_production_runtime

        fake_ccxt = SimpleNamespace(binanceusdm=lambda options: SimpleNamespace(options=options))
        environment = {
            "MARKET_DATA_BACKEND": "postgres",
            "MARKET_DATA_POSTGRES_DSN": "postgresql://test:test@127.0.0.1:5432/t0_test",
            "T0_FEEDER_LEASE_DB": "/tmp/forbidden-lease.sqlite",
        }
        with patch.dict(sys.modules, {"ccxt": fake_ccxt}):
            with self.assertRaisesRegex(ValueError, "not allowed with PostgreSQL"):
                build_production_runtime(environment)


@unittest.skipUnless(
    __import__("os").environ.get("MARKET_DATA_TEST_DATABASE_URL"),
    "Set the disposable local TimescaleDB test service",
)
class PostgresFeederRuntimeIntegrationTest(unittest.TestCase):
    """Exercise the real runtime composition against disposable TimescaleDB."""

    @classmethod
    def setUpClass(cls):
        from market_data.test_postgres_write_gateway import DSN, _assert_disposable_target
        cls.dsn = DSN
        _assert_disposable_target()
        from market_data.migrations import migrate
        migrate(cls.dsn)

    def test_runtime_recovers_and_scheduler_reuses_postgres_fenced_gateway(self):
        import time
        import uuid
        from unittest.mock import patch
        from market_data.feeder import FeederConfig
        from market_data.feeder_service import build_runtime
        from market_data.postgres import PostgresLeaseStore, PostgresWriteGateway, connection
        from market_data.storage import PostgresStore
        from market_data.store import EXCHANGE, INTERVAL_MS, MARKET_TYPE

        timeframe = "15m"
        interval = INTERVAL_MS[timeframe]
        now_ms = (int(time.time() * 1000) // interval) * interval + 5_000
        recovery_end = now_ms - 5_000
        recovery_start = recovery_end - interval
        lease_name = "binance-btcusdt-canonical"
        owner = "runtime-integration-worker"
        store = PostgresStore(self.dsn)
        leases = PostgresLeaseStore(self.dsn, lease_name=lease_name)
        exchange_calls = []

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
                return now_ms

            def fetch_ohlcv(self, symbol, timeframe, since, limit, params):
                exchange_calls.append((symbol, timeframe, since, limit, params))
                return [[since, 100.0, 101.0, 99.0, 100.5, 1.0]]

        config = FeederConfig(
            timeframes=(timeframe,), close_grace_seconds=5,
            lease_ttl_seconds=60, lease_heartbeat_seconds=15,
        )
        runtime = build_runtime(
            config=config, owner_id=owner, exchange=SyntheticExchange(),
            store=store, lease_store=leases, clock=lambda: now_ms,
            recovery_lookback_candles=1,
        )
        gateway_instances = []
        from market_data.sync import sync_window as real_sync_window

        def capture_sync(exchange, gateway, frame, start_ms, end_ms, now_ms=None):
            gateway_instances.append(gateway)
            return real_sync_window(
                exchange, gateway, frame, start_ms, end_ms, now_ms=now_ms
            )

        try:
            self.assertIsInstance(runtime.canonical_write_gateway, PostgresWriteGateway)
            with patch("market_data.feeder_service.sync_window", side_effect=capture_sync):
                self.assertTrue(runtime.start(now_ms=now_ms))
                self.assertEqual(runtime.state, "RUNNING")
                recovered = store.read_window(
                    "BTCUSDT", timeframe, recovery_start, recovery_end
                )
                self.assertTrue(recovered["coverage"]["complete"])
                self.assertEqual(recovered["coverage"]["returned"], 1)
                self.assertEqual(
                    runtime.scheduler.sync_callback(timeframe, recovery_start, recovery_end),
                    0,
                )
            self.assertEqual(len(gateway_instances), 2)
            self.assertIs(gateway_instances[0], runtime.canonical_write_gateway)
            self.assertIs(gateway_instances[1], runtime.canonical_write_gateway)
            self.assertEqual(len(exchange_calls), 2)
            self.assertTrue(runtime.stop(timeout=3))
            self.assertFalse(leases.is_current(owner, runtime.lease_generation))
            with connection(self.dsn, read_only=True) as database:
                rows = database.execute(
                    """SELECT count(*) FROM market_data.candles
                       WHERE exchange=%s AND market_type=%s AND symbol='BTCUSDT'
                         AND timeframe=%s AND open_time_ms=%s""",
                    (EXCHANGE, MARKET_TYPE, timeframe, recovery_start),
                ).fetchone()[0]
            self.assertEqual(rows, 1)
        finally:
            if runtime.state not in ("STOPPED", "NEW"):
                runtime.stop(timeout=3)
            with connection(self.dsn) as database:
                database.execute(
                    """DELETE FROM market_data.candles
                       WHERE symbol='BTCUSDT' AND timeframe=%s AND open_time_ms=%s""",
                    (timeframe, recovery_start),
                )
                database.execute(
                    "DELETE FROM market_data.feeder_leases WHERE lease_name=%s",
                    (lease_name,),
                )
