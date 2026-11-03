"""P5.3.11.5 G2 Gateway contract and isolated regression tests.

All database tests use disposable SQLite files created inside TemporaryDirectory.
No test resolves MARKET_DATA_DB, accesses a canonical DB, contacts an exchange,
or starts FeederRuntime. G2 pagination and clock checks exercise the concrete
Gateway path; G1 fencing behavior remains GREEN regression coverage.
"""
import ast
import inspect
import os
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from market_data import feeder, feeder_service, store, sync
from market_data.gateway import (
    CandleBatchRejected,
    GatewayStorageError,
    LeaseFence,
    LeaseRejected,
    T0WriteGateway,
)
from market_data.store import Candle, INTERVAL_MS


START = 1_800_000_000_000
STEP = INTERVAL_MS["15m"]
LEASE = LeaseFence("binance-btcusdt-canonical", "g2-test-owner", 7)


def candle_row(opened, close="102.25"):
    return [opened, 100.01, 103.5, 99.0, close, 1.25]


def candle(opened, close="102.25", available=None):
    return Candle(
        "15m", opened, "100.01", "103.5", "99.0", close, "1.25",
        available if available is not None else opened + STEP,
    )


def create_shadow_db(path, *, owner=LEASE.owner_id, generation=LEASE.generation,
                     expires_at=START + 10_000_000_000):
    with sqlite3.connect(path) as connection:
        connection.executescript(
            """
            CREATE TABLE candles (
                exchange TEXT NOT NULL, market_type TEXT NOT NULL,
                symbol TEXT NOT NULL, timeframe TEXT NOT NULL,
                open_time_ms INTEGER NOT NULL, open TEXT NOT NULL,
                high TEXT NOT NULL, low TEXT NOT NULL, close TEXT NOT NULL,
                volume TEXT NOT NULL, available_at_ms INTEGER NOT NULL,
                PRIMARY KEY (exchange, market_type, symbol, timeframe, open_time_ms)
            );
            CREATE TABLE feeder_leases (
                lease_name TEXT PRIMARY KEY, owner TEXT,
                generation INTEGER NOT NULL, expires_at_ms INTEGER NOT NULL
            );
            """
        )
        connection.execute(
            "INSERT INTO feeder_leases VALUES (?, ?, ?, ?)",
            (LEASE.lease_name, owner, generation, expires_at),
        )


class ExchangeDouble:
    id = "binanceusdm"

    def __init__(self, pages):
        self.pages = list(pages)
        self.calls = []
        self.server_time = START + 3000 * STEP
        self.market = {
            "symbol": "BTC/USDT:USDT", "id": "BTCUSDT", "base": "BTC",
            "quote": "USDT", "settle": "USDT", "active": True,
            "swap": True, "linear": True, "spot": False,
        }

    def load_markets(self):
        return {"BTC/USDT:USDT": self.market}

    def fetch_time(self):
        return self.server_time

    def fetch_ohlcv(self, symbol, timeframe, since, limit, params):
        self.calls.append((symbol, timeframe, since, limit, params))
        page = self.pages.pop(0)
        if isinstance(page, Exception):
            raise page
        return page


class G2WriterRoutingRedTests(unittest.TestCase):
    def setUp(self):
        self.observed_at = START + 100 * STEP
        self.lease_now = START + 100 * STEP + 123

    def test_g2_01_sync_window_requires_gateway_parameter(self):
        parameters = inspect.signature(sync.sync_window).parameters
        self.assertIn("gateway", parameters)
        self.assertIs(parameters["gateway"].default, inspect.Parameter.empty)

    def test_g2_02_sync_window_requires_lease_fence_parameter(self):
        parameters = inspect.signature(sync.sync_window).parameters
        self.assertIn("lease_token", parameters)
        self.assertIs(parameters["lease_token"].default, inspect.Parameter.empty)

    def test_g2_03_sync_window_requires_separate_lease_clock(self):
        parameters = inspect.signature(sync.sync_window).parameters
        self.assertIn("lease_clock", parameters)
        self.assertIs(parameters["lease_clock"].default, inspect.Parameter.empty)

    def test_g2_04_sync_window_routes_through_gateway_insert_batch(self):
        source = inspect.getsource(sync.sync_window)
        self.assertIn("insert_batch", source)
        self.assertNotIn("store.insert(", source)
        self.assertNotIn("store.insert_fenced(", source)

    def test_g2_05_feeder_passes_typed_lease_capability_to_gateway_path(self):
        runtime_source = inspect.getsource(feeder.FeederRuntime)
        builder_source = inspect.getsource(feeder_service.build_runtime)
        self.assertIn("LeaseFence", runtime_source + builder_source)
        self.assertIn("gateway", inspect.signature(feeder_service.build_runtime).parameters)
        self.assertIn("insert_batch", builder_source)

    def test_g2_06_stale_generation_is_rejected_by_real_gateway(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "stale.sqlite3"
            create_shadow_db(database, generation=LEASE.generation + 1)
            gateway = T0WriteGateway(str(database))
            with self.assertRaises(LeaseRejected):
                gateway.insert_batch(
                    [candle(START)], lease_token=LEASE,
                    now_ms=lambda: self.lease_now,
                )
            with sqlite3.connect(database) as connection:
                self.assertEqual(connection.execute("SELECT COUNT(*) FROM candles").fetchone()[0], 0)

    def test_g2_07_expiry_at_final_admission_rolls_back_gateway_batch(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "expiry.sqlite3"
            create_shadow_db(database, expires_at=self.lease_now + 60_000)
            gateway = T0WriteGateway(str(database))
            clock_values = iter((self.lease_now, self.lease_now + 60_000))
            with self.assertRaises(LeaseRejected):
                gateway.insert_batch(
                    [candle(START)], lease_token=LEASE,
                    now_ms=lambda: next(clock_values),
                )
            with sqlite3.connect(database) as connection:
                self.assertEqual(connection.execute("SELECT COUNT(*) FROM candles").fetchone()[0], 0)

    def test_g2_08_recovery_builder_uses_gateway_backed_sync_callback(self):
        source = inspect.getsource(feeder_service.build_runtime)
        self.assertIn("LeaseFence", source)
        self.assertIn("gateway", source)
        self.assertIn("insert_batch", source)

    def test_g2_09_cli_sync_requires_explicit_lease_capability(self):
        tree = ast.parse(inspect.getsource(sync.main))
        calls = [
            node for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "sync_window"
        ]
        self.assertTrue(calls, "CLI must retain an explicit ingestion entrypoint")
        for call in calls:
            keywords = {item.arg for item in call.keywords}
            self.assertIn("lease_token", keywords)
            self.assertIn("lease_clock", keywords)

    def test_g2_10_legacy_unfenced_store_insert_is_not_called_by_sync(self):
        tree = ast.parse(inspect.getsource(sync.sync_window))
        legacy_calls = [
            node for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "insert"
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "store"
        ]
        self.assertEqual(legacy_calls, [])

    def test_g2_11_legacy_insert_fenced_is_not_an_alternate_sync_route(self):
        tree = ast.parse(inspect.getsource(sync.sync_window))
        source = inspect.getsource(sync.sync_window)
        legacy_calls = [
            node for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "insert_fenced"
        ]
        self.assertEqual(legacy_calls, [])
        self.assertNotIn('getattr(store, "insert_fenced"', source)

    def test_g2_12_runtime_lease_and_writer_paths_do_not_create_schema(self):
        runtime_sources = (
            inspect.getsource(feeder.LeaseStore._transaction),
            inspect.getsource(store.CandleStore.__init__),
        )
        for source in runtime_sources:
            normalized = " ".join(source.upper().split())
            self.assertNotIn("CREATE TABLE", normalized)
            self.assertNotIn("CREATE INDEX", normalized)

        self.assertTrue(callable(getattr(store.CandleStore, "initialize_schema", None)))
        self.assertTrue(callable(getattr(feeder.LeaseStore, "initialize_schema", None)))
        with tempfile.TemporaryDirectory() as directory:
            untouched = Path(directory) / "constructor-must-not-create.sqlite3"
            store.CandleStore(untouched)
            feeder.LeaseStore(str(untouched))
            self.assertFalse(untouched.exists())

    def test_g2_13_gateway_conflict_rejection_propagates_without_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "conflict.sqlite3"
            create_shadow_db(database)
            gateway = T0WriteGateway(str(database))
            self.assertEqual(
                gateway.insert_batch([candle(START)], lease_token=LEASE,
                                     now_ms=lambda: self.lease_now),
                1,
            )
            with self.assertRaises(CandleBatchRejected):
                gateway.insert_batch(
                    [candle(START, close="102.50")], lease_token=LEASE,
                    now_ms=lambda: self.lease_now,
                )
            with sqlite3.connect(database) as connection:
                self.assertEqual(
                    connection.execute("SELECT close FROM candles").fetchone()[0],
                    "102.25",
                )

    def test_g2_14_identical_duplicate_is_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "duplicate.sqlite3"
            create_shadow_db(database)
            gateway = T0WriteGateway(str(database))
            self.assertEqual(
                gateway.insert_batch([candle(START)], lease_token=LEASE,
                                     now_ms=lambda: self.lease_now),
                1,
            )
            self.assertEqual(
                gateway.insert_batch([candle(START, available=START + STEP + 99)],
                                     lease_token=LEASE, now_ms=lambda: self.lease_now),
                0,
            )
            with sqlite3.connect(database) as connection:
                self.assertEqual(connection.execute("SELECT COUNT(*) FROM candles").fetchone()[0], 1)

    def test_g2_15_empty_batch_is_gateway_noop_without_database(self):
        gateway = T0WriteGateway("/path/that/must/not/be/opened.sqlite3")
        self.assertEqual(
            gateway.insert_batch([], lease_token=None, now_ms=None),
            0,
        )

    def test_g2_16_pagination_preserves_first_page_when_second_page_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "pagination.sqlite3"
            create_shadow_db(database)
            gateway = T0WriteGateway(str(database))
            first = [candle_row(START + index * STEP) for index in range(1000)]
            exchange = ExchangeDouble([first, RuntimeError("second page fetch failed")])
            observed = START + 2000 * STEP
            with self.assertRaisesRegex(RuntimeError, "second page fetch failed"):
                sync.sync_window(
                    exchange, "15m", START, START + 1001 * STEP,
                    gateway=gateway, lease_token=LEASE,
                    now_ms=lambda: observed, lease_clock=lambda: self.lease_now,
                )
            self.assertEqual(len(exchange.calls), 2)
            rows = gateway.read_window("BTCUSDT", "15m", START, START + 1000 * STEP)
            self.assertEqual(len(rows), 1000)

    def test_g2_17_observation_clock_is_independent_of_exchange_clock(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "observation-clock.sqlite3"
            create_shadow_db(database)
            gateway = T0WriteGateway(str(database))
            exchange = ExchangeDouble([[candle_row(START)]])
            observed = START + 100 * STEP
            self.assertNotEqual(observed, exchange.server_time)

            self.assertEqual(
                sync.sync_window(
                    exchange, "15m", START, START + STEP,
                    gateway=gateway, lease_token=LEASE,
                    now_ms=lambda: observed, lease_clock=lambda: self.lease_now,
                ),
                1,
            )
            rows = gateway.read_window("BTCUSDT", "15m", START, START + STEP)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["available_at_ms"], observed)
    def test_g2_18_postgres_backend_is_not_available_to_canonical_sync_cli(self):
        source = inspect.getsource(sync.main)
        self.assertNotIn('"postgres"', source)
        self.assertNotIn('choices=("sqlite", "postgres")', source)
        with self.assertRaisesRegex(TypeError, "T0WriteGateway"):
            sync.sync_window(
                None, "15m", START, START + STEP,
                gateway=object(), lease_token=LEASE,
                lease_clock=lambda: self.lease_now,
            )
        with patch.dict(os.environ, {"MARKET_DATA_BACKEND": "postgres"}, clear=True), patch.object(
            sys, "argv", ["sync.py"]
        ):
            with self.assertRaises(SystemExit) as exit_info:
                sync.main()
        self.assertEqual(exit_info.exception.code, 2)


    def test_g2_19_sync_window_rejects_duck_typed_gateway(self):
        class DuckGateway:
            def insert_batch(self, candles, *, lease_token, now_ms):
                return len(candles)

        with self.assertRaisesRegex(TypeError, "T0WriteGateway"):
            sync.sync_window(
                None, "15m", START, START + STEP,
                gateway=DuckGateway(), lease_token=LEASE,
                lease_clock=lambda: self.lease_now,
            )

    def test_g2_20_build_runtime_rejects_duck_typed_gateway(self):
        class DuckGateway:
            def insert_batch(self, candles, *, lease_token, now_ms):
                return len(candles)

        with self.assertRaisesRegex(TypeError, "T0WriteGateway"):
            feeder_service.build_runtime(
                config=feeder.FeederConfig(timeframes=("15m",)),
                owner_id=LEASE.owner_id,
                exchange=ExchangeDouble([]),
                store=Mock(),
                gateway=DuckGateway(),
                lease_store=Mock(),
            )

    def test_g2_21_runtime_uses_independent_observation_and_lease_clocks(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "runtime-clocks.sqlite3"
            create_shadow_db(database)
            gateway = T0WriteGateway(str(database))
            exchange = ExchangeDouble([[candle_row(START)]])
            lease_store = Mock()
            lease_store.lease_name = LEASE.lease_name
            lease_store.heartbeat.return_value = True
            observed_at = START + 100 * STEP
            lease_now = START + 100 * STEP + 321
            lease_clock_calls = []

            def lease_clock():
                lease_clock_calls.append(lease_now)
                return lease_now

            config = feeder.FeederConfig(timeframes=("15m",))
            runtime = feeder_service.build_runtime(
                config=config,
                owner_id=LEASE.owner_id,
                exchange=exchange,
                store=Mock(),
                gateway=gateway,
                lease_store=lease_store,
                observation_clock=lambda: observed_at,
                lease_clock=lease_clock,
            )
            runtime.lease_generation = LEASE.generation

            runtime.scheduler.sync_callback("15m", START, START + STEP)

            lease_store.heartbeat.assert_called_once_with(
                LEASE.owner_id, LEASE.generation,
                now_ms=lease_now, ttl_seconds=config.lease_ttl_seconds,
            )
            rows = gateway.read_window("BTCUSDT", "15m", START, START + STEP)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["available_at_ms"], observed_at)
            self.assertGreaterEqual(len(lease_clock_calls), 3)
            self.assertEqual(runtime.scheduler.clock(), lease_now)
            self.assertEqual(runtime.recovery.clock(), lease_now)
            self.assertEqual(runtime.clock(), lease_now)

    def test_g2_22_gateway_write_does_not_create_missing_database(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "must-remain-absent.sqlite3"
            gateway = T0WriteGateway(database)
            with self.assertRaises(GatewayStorageError):
                gateway.insert_batch(
                    [candle(START)], lease_token=LEASE,
                    now_ms=lambda: self.lease_now,
                )
            self.assertFalse(database.exists())


if __name__ == "__main__":
    unittest.main()
