"""G1 RED acceptance tests for the T0 single-writer Gateway.

All database activity is confined to disposable temporary SQLite files. The
suite never resolves a canonical path, contacts an exchange, or imports a
Paper writer capability.
"""
import inspect
import sqlite3
import tempfile
import threading
import unittest
from pathlib import Path

from market_data.store import Candle

try:
    from market_data.gateway import (
        CandleBatchRejected,
        GatewayStorageError,
        GatewayWriteError,
        LeaseFence,
        LeaseRejected,
        T0WriteGateway,
    )
except ModuleNotFoundError as exc:
    if exc.name != "market_data.gateway":
        raise
    CandleBatchRejected = None
    GatewayStorageError = None
    GatewayWriteError = None
    LeaseFence = None
    LeaseRejected = None
    T0WriteGateway = None


LEASE_NAME = "binance-btcusdt-canonical"
OWNER = "g1-red-test-writer"
NOW_MS = 1_800_000_000_000
LEASE_TTL_MS = 60_000
FIRST_OPEN_MS = 1_799_998_200_000
SECOND_OPEN_MS = 1_799_999_100_000


class T0GatewayG1RedTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.db = self.root / "shadow.sqlite3"
        self.now = NOW_MS
        self.owner = OWNER
        self._create_fixture_schema()
        self._seed_lease(self.owner, generation=1, expires_at_ms=self.now + LEASE_TTL_MS)

    def tearDown(self):
        self.temp.cleanup()

    def require_gateway(self):
        self.assertIsNotNone(
            T0WriteGateway,
            "CONTRACT RED: market_data.gateway.T0WriteGateway is not implemented",
        )
        self.assertIsNotNone(
            LeaseFence,
            "CONTRACT RED: market_data.gateway.LeaseFence is not implemented",
        )
        self.assertTrue(issubclass(GatewayWriteError, Exception))
        self.assertTrue(issubclass(LeaseRejected, GatewayWriteError))
        self.assertTrue(issubclass(CandleBatchRejected, GatewayWriteError))
        self.assertTrue(issubclass(GatewayStorageError, GatewayWriteError))

    def _create_fixture_schema(self, path=None):
        target = self.db if path is None else Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(str(target)) as connection:
            connection.execute(
                """CREATE TABLE candles (
                    exchange TEXT NOT NULL,
                    market_type TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    timeframe TEXT NOT NULL,
                    open_time_ms INTEGER NOT NULL,
                    open TEXT NOT NULL,
                    high TEXT NOT NULL,
                    low TEXT NOT NULL,
                    close TEXT NOT NULL,
                    volume TEXT NOT NULL,
                    available_at_ms INTEGER NOT NULL,
                    PRIMARY KEY (exchange, market_type, symbol, timeframe, open_time_ms)
                )"""
            )
            connection.execute(
                """CREATE TABLE feeder_leases (
                    lease_name TEXT PRIMARY KEY,
                    owner TEXT,
                    generation INTEGER NOT NULL CHECK(generation >= 0),
                    expires_at_ms INTEGER NOT NULL CHECK(expires_at_ms >= 0)
                )"""
            )

    def _seed_lease(self, owner, generation, expires_at_ms, path=None):
        target = self.db if path is None else Path(path)
        with sqlite3.connect(str(target)) as connection:
            connection.execute(
                "INSERT OR REPLACE INTO feeder_leases "
                "(lease_name, owner, generation, expires_at_ms) VALUES (?, ?, ?, ?)",
                (LEASE_NAME, owner, generation, expires_at_ms),
            )

    def _fence(self, owner=None, generation=1):
        return LeaseFence(
            lease_name=LEASE_NAME,
            owner_id=self.owner if owner is None else owner,
            generation=generation,
        )

    def _candle(self, opened, close="100", available_at_ms=None):
        return Candle(
            "15m",
            opened,
            "99",
            "101",
            "98",
            close,
            "1",
            available_at_ms=(
                opened + 900_000 if available_at_ms is None else available_at_ms
            ),
        )

    def _gateway(self, path=None):
        return T0WriteGateway(db_path=str(self.db if path is None else path))

    def _write(self, gateway, candles, fence=None, clock=None):
        return gateway.insert_batch(
            candles,
            lease_token=self._fence() if fence is None else fence,
            now_ms=(lambda: self.now) if clock is None else clock,
        )

    def _rows(self, sql="SELECT * FROM candles"):
        with sqlite3.connect(str(self.db)) as connection:
            return connection.execute(sql).fetchall()

    def _lease_row(self, path=None):
        target = self.db if path is None else Path(path)
        with sqlite3.connect(str(target)) as connection:
            return connection.execute(
                "SELECT owner, generation, expires_at_ms FROM feeder_leases WHERE lease_name=?",
                (LEASE_NAME,),
            ).fetchone()

    def test_g1_01_valid_lease_commits_entire_batch(self):
        self.require_gateway()
        gateway = self._gateway()
        batch = [self._candle(FIRST_OPEN_MS), self._candle(SECOND_OPEN_MS)]

        accepted = self._write(gateway, batch)

        self.assertEqual(accepted, 2)
        self.assertEqual(len(self._rows()), 2)
        gateway.close()

    def test_g1_02_expired_lease_is_rejected_without_mutation(self):
        self.require_gateway()
        gateway = self._gateway()

        with self.assertRaises(LeaseRejected):
            self._write(
                gateway,
                [self._candle(FIRST_OPEN_MS)],
                clock=lambda: self.now + LEASE_TTL_MS,
            )

        self.assertEqual(self._rows(), [])
        gateway.close()

    def test_g1_03_wrong_owner_is_rejected_without_mutation(self):
        self.require_gateway()
        gateway = self._gateway()

        with self.assertRaises(LeaseRejected):
            self._write(
                gateway,
                [self._candle(FIRST_OPEN_MS)],
                fence=self._fence(owner="forged-owner"),
            )

        self.assertEqual(self._rows(), [])
        gateway.close()

    def test_g1_04_stale_generation_is_rejected_without_mutation(self):
        self.require_gateway()
        self._seed_lease(self.owner, generation=3, expires_at_ms=self.now + LEASE_TTL_MS)
        gateway = self._gateway()

        with self.assertRaises(LeaseRejected):
            self._write(
                gateway,
                [self._candle(FIRST_OPEN_MS)],
                fence=self._fence(generation=2),
            )

        self.assertEqual(self._rows(), [])
        self.assertEqual(self._lease_row()[:2], (self.owner, 3))
        gateway.close()

    def test_g1_05_takeover_committed_first_rejects_old_fence(self):
        self.require_gateway()
        self._seed_lease("new-owner", generation=2, expires_at_ms=self.now + 120_000)
        gateway = self._gateway()

        with self.assertRaises(LeaseRejected):
            self._write(gateway, [self._candle(FIRST_OPEN_MS)])

        self.assertEqual(self._rows(), [])
        self.assertEqual(self._lease_row()[:2], ("new-owner", 2))
        gateway.close()

    def test_g1_06_writer_transaction_first_serializes_takeover(self):
        self.require_gateway()
        gateway = self._gateway()
        clock_entered = threading.Event()
        release_writer = threading.Event()
        writer_errors = []
        writer_result = []

        def blocked_clock():
            clock_entered.set()
            if not release_writer.wait(timeout=5):
                raise TimeoutError("test coordinator did not release writer")
            return self.now

        def writer():
            try:
                writer_result.append(
                    self._write(gateway, [self._candle(FIRST_OPEN_MS)], clock=blocked_clock)
                )
            except Exception as exc:
                writer_errors.append(exc)

        thread = threading.Thread(target=writer, name="g1-gateway-writer")
        thread.start()
        try:
            self.assertTrue(
                clock_entered.wait(timeout=5),
                "Gateway did not reach the initial in-transaction lease check",
            )
            with sqlite3.connect(str(self.db), timeout=0, isolation_level=None) as takeover:
                takeover.execute("PRAGMA busy_timeout=0")
                with self.assertRaises(sqlite3.OperationalError):
                    takeover.execute("BEGIN IMMEDIATE")
        finally:
            release_writer.set()
            thread.join(timeout=5)

        self.assertFalse(thread.is_alive(), "Gateway writer thread did not finish")
        self.assertEqual(writer_errors, [])
        self.assertEqual(writer_result, [1])

        with sqlite3.connect(str(self.db), isolation_level=None) as takeover:
            takeover.execute("BEGIN IMMEDIATE")
            takeover.execute(
                "UPDATE feeder_leases SET owner=?, generation=?, expires_at_ms=? WHERE lease_name=?",
                ("new-owner", 2, self.now + 120_000, LEASE_NAME),
            )
            takeover.commit()

        self.assertEqual(len(self._rows()), 1)
        self.assertEqual(self._lease_row()[:2], ("new-owner", 2))
        gateway.close()

    def test_g1_07_invalid_candle_rejects_batch_without_partial_rows(self):
        self.require_gateway()
        gateway = self._gateway()

        with self.assertRaises(CandleBatchRejected):
            self._write(gateway, [self._candle(FIRST_OPEN_MS), object()])

        self.assertEqual(self._rows(), [])
        gateway.close()

    def test_g1_08_mid_batch_sql_failure_rolls_back_all_rows(self):
        self.require_gateway()
        with sqlite3.connect(str(self.db)) as connection:
            connection.execute(
                f"""CREATE TRIGGER reject_second_candle
                    BEFORE INSERT ON candles
                    WHEN NEW.open_time_ms = {SECOND_OPEN_MS}
                    BEGIN SELECT RAISE(ABORT, 'injected G1 batch failure'); END"""
            )
        gateway = self._gateway()

        with self.assertRaises(GatewayStorageError):
            self._write(
                gateway,
                [self._candle(FIRST_OPEN_MS), self._candle(SECOND_OPEN_MS)],
            )

        self.assertEqual(self._rows(), [])
        gateway.close()

    def test_g1_09_duplicate_replay_preserves_first_observation_and_conflict_rejects(self):
        self.require_gateway()
        gateway = self._gateway()
        original = self._candle(FIRST_OPEN_MS, available_at_ms=FIRST_OPEN_MS + 900_000)
        replay = self._candle(FIRST_OPEN_MS, available_at_ms=FIRST_OPEN_MS + 1_000_000)

        self.assertEqual(self._write(gateway, [original]), 1)
        self.assertEqual(self._write(gateway, [replay]), 0)
        stored = self._rows(
            "SELECT open, high, low, close, volume, available_at_ms FROM candles"
        )
        self.assertEqual(stored, [("99", "101", "98", "100", "1", FIRST_OPEN_MS + 900_000)])

        conflicting = self._candle(FIRST_OPEN_MS, close="100.5")
        with self.assertRaises(CandleBatchRejected):
            self._write(gateway, [conflicting])

        self.assertEqual(
            self._rows("SELECT open, high, low, close, volume, available_at_ms FROM candles"),
            stored,
        )
        gateway.close()

    def test_g1_10_unavailable_database_fails_without_creating_path(self):
        self.require_gateway()
        missing = self.root / "missing-parent" / "canonical.sqlite3"
        gateway = self._gateway(missing)

        with self.assertRaises(GatewayStorageError):
            self._write(gateway, [self._candle(FIRST_OPEN_MS)])

        self.assertFalse(missing.parent.exists())
        self.assertFalse(missing.exists())
        gateway.close()

    def test_g1_11_constructor_and_read_are_side_effect_free(self):
        self.require_gateway()
        missing = self.root / "read-only-missing" / "data.sqlite3"
        missing_gateway = self._gateway(missing)
        self.assertFalse(missing.parent.exists())
        with self.assertRaises(GatewayStorageError):
            missing_gateway.read_window("BTCUSDT", "15m", 0, self.now)
        self.assertFalse(missing.parent.exists())
        self.assertFalse(missing.exists())
        missing_gateway.close()

        with sqlite3.connect(str(self.db)) as connection:
            connection.execute(
                "INSERT INTO candles VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                ("binance", "USDT_PERPETUAL", "BTCUSDT", "15m", FIRST_OPEN_MS,
                 "99", "101", "98", "100", "1", FIRST_OPEN_MS + 900_000),
            )
            before_schema = connection.execute(
                "SELECT type, name, sql FROM sqlite_master ORDER BY type, name"
            ).fetchall()
            before_rows = connection.execute("SELECT * FROM candles").fetchall()

        gateway = self._gateway()
        gateway.read_window("BTCUSDT", "15m", 0, self.now)
        with sqlite3.connect(str(self.db)) as connection:
            after_schema = connection.execute(
                "SELECT type, name, sql FROM sqlite_master ORDER BY type, name"
            ).fetchall()
            after_rows = connection.execute("SELECT * FROM candles").fetchall()

        self.assertEqual(after_schema, before_schema)
        self.assertEqual(after_rows, before_rows)
        gateway.close()

    def test_g1_12_postgres_backend_selector_is_not_exposed(self):
        self.require_gateway()
        missing = self.root / "postgres-selector-must-not-create.sqlite3"

        parameters = inspect.signature(T0WriteGateway).parameters
        self.assertEqual(tuple(parameters), ("db_path",))
        with self.assertRaises(TypeError):
            T0WriteGateway(db_path=str(missing), backend="postgres")
        self.assertFalse(missing.exists())

    def test_g1_13_empty_batch_is_strict_noop_without_clock_or_database(self):
        self.require_gateway()
        missing = self.root / "empty-batch" / "not-created.sqlite3"
        gateway = self._gateway(missing)
        clock_calls = []

        def forbidden_clock():
            clock_calls.append(True)
            raise AssertionError("empty batch must not call now_ms")

        accepted = gateway.insert_batch([], lease_token=None, now_ms=forbidden_clock)

        self.assertEqual(accepted, 0)
        self.assertEqual(clock_calls, [])
        self.assertFalse(missing.parent.exists())
        self.assertFalse(missing.exists())
        gateway.close()

    def test_g1_14a_expiry_at_final_admission_rolls_back_batch(self):
        self.require_gateway()
        gateway = self._gateway()
        clock_values = iter((self.now, self.now + LEASE_TTL_MS))

        with self.assertRaises(LeaseRejected):
            self._write(
                gateway,
                [self._candle(FIRST_OPEN_MS), self._candle(SECOND_OPEN_MS)],
                clock=lambda: next(clock_values),
            )

        self.assertEqual(self._rows(), [])
        gateway.close()

    def test_g1_14b_expiry_after_final_admission_does_not_revoke_batch(self):
        self.require_gateway()
        gateway = self._gateway()
        expires_at_ms = self.now + LEASE_TTL_MS
        clock_state = {"calls": 0, "current_ms": self.now}

        def clock():
            clock_state["calls"] += 1
            if clock_state["calls"] == 1:
                return clock_state["current_ms"]
            if clock_state["calls"] == 2:
                # Capture a still-valid final-admission timestamp, then advance
                # the external clock state to expiry before returning control.
                admitted_at_ms = expires_at_ms - 1
                clock_state["current_ms"] = expires_at_ms
                return admitted_at_ms
            raise AssertionError("Gateway rechecked the clock after final admission")

        accepted = self._write(gateway, [self._candle(FIRST_OPEN_MS)], clock=clock)

        self.assertEqual(accepted, 1)
        self.assertEqual(clock_state["current_ms"], expires_at_ms)
        self.assertGreaterEqual(clock_state["current_ms"], expires_at_ms)
        self.assertEqual(clock_state["calls"], 2)
        self.assertEqual(len(self._rows()), 1)
        gateway.close()


if __name__ == "__main__":
    unittest.main()
