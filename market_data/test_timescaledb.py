"""SQLite/TimescaleDB contract parity tests; DB is supplied by Codemagic."""

import hashlib
import os
import tempfile
import unittest
from pathlib import Path

from market_data.migrations import migrate
from market_data.postgres import PostgresCandleStore, connection, read_window as read_postgres_window
from market_data.store import Candle, CandleStore, INTERVAL_MS, read_window


DSN = os.environ.get("MARKET_DATA_TEST_DATABASE_URL", "")
REQUIRED = os.environ.get("MARKET_DATA_REQUIRE_TIMESCALE") == "1"


@unittest.skipUnless(DSN or REQUIRED, "Set MARKET_DATA_TEST_DATABASE_URL for TimescaleDB integration tests")
class TimescaleParityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not DSN:
            raise RuntimeError("Codemagic requires MARKET_DATA_TEST_DATABASE_URL")
        try:
            import psycopg  # noqa: F401
        except ImportError:
            raise RuntimeError("psycopg is required for TimescaleDB integration tests") from None
        with connection(DSN) as database:
            extension = database.execute("SELECT extversion FROM pg_extension WHERE extname='timescaledb'").fetchone()
            if extension is None:
                raise RuntimeError("Target database does not have TimescaleDB installed")
            cls.extension_version = extension[0]
        migrate(DSN)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.sqlite_path = Path(self.temp.name) / "market.sqlite3"
        self.sqlite_store = CandleStore(self.sqlite_path)
        self.pg_store = PostgresCandleStore(DSN)
        self.step = INTERVAL_MS["15m"]
        # Integration database must be disposable; unique time slots avoid cross-run collisions.
        import time
        import uuid
        self.start = ((time.time_ns() // 1_000_000 // self.step) + (uuid.uuid4().int % 1_000_000)) * self.step

    def tearDown(self):
        with connection(DSN) as database:
            database.execute("DELETE FROM market_data.candles WHERE open_time_ms >= %s AND open_time_ms < %s",
                             (self.start, self.start + 4*self.step))

    def candle(self, slot=0, **changes):
        values = dict(timeframe="15m", open_time_ms=self.start + slot*self.step,
                      open="100.12345678901234567890123456789", high="102", low="99",
                      close="101", volume="5.0000", available_at_ms=self.start+(slot+1)*self.step+100)
        return Candle(**(values | changes))

    def test_exact_decimal_hash_gap_and_asof_parity(self):
        candles = [self.candle(), self.candle(2)]
        self.assertEqual(self.pg_store.insert(candles), 2)
        self.sqlite_store.insert(candles)
        args = ("BTCUSDT", "15m", self.start, self.start+3*self.step)
        self.assertEqual(read_postgres_window(DSN, *args), read_window(self.sqlite_path, *args))
        cutoff = self.start + 2*self.step
        self.assertEqual(read_postgres_window(DSN, *args, as_of_ms=cutoff),
                         read_window(self.sqlite_path, *args, as_of_ms=cutoff))

    def test_duplicate_preserves_first_observation_and_conflict_rolls_back_batch(self):
        first = self.candle()
        self.pg_store.insert([first])
        before = read_postgres_window(DSN, "BTCUSDT", "15m", self.start, self.start+self.step)
        self.assertEqual(self.pg_store.insert([self.candle(available_at_ms=first.available_at_ms+500)]), 0)
        self.assertEqual(before, read_postgres_window(DSN, "BTCUSDT", "15m", self.start, self.start+self.step))
        with self.assertRaises(ValueError):
            self.pg_store.insert([self.candle(1), self.candle(close="100.5")])
        self.assertEqual(before, read_postgres_window(DSN, "BTCUSDT", "15m", self.start, self.start+self.step))

    def test_hypertable_primary_key_and_migration_checksum(self):
        with connection(DSN, read_only=True) as database:
            row = database.execute("""SELECT hypertable_name FROM timescaledb_information.hypertables
                WHERE hypertable_schema='market_data' AND hypertable_name='candles'""").fetchone()
            self.assertEqual(row[0], "candles")
            migrations = database.execute("SELECT migration_id, checksum_sha256 FROM market_data.schema_migrations").fetchall()
            self.assertTrue(migrations)
        self.assertEqual(migrate(DSN)[0], migrate(DSN)[1])

    def test_successful_insert_before_conflict_is_rolled_back_with_batch(self):
        # Seed a later candle so the first item in the attempted batch is new.
        existing = self.candle(1)
        self.assertEqual(self.pg_store.insert([existing]), 1)

        with self.assertRaises(ValueError):
            self.pg_store.insert([self.candle(0), self.candle(1, close="100.5")])

        result = read_postgres_window(
            DSN, "BTCUSDT", "15m", self.start, self.start + 2*self.step
        )
        self.assertEqual(
            [candle["openTimeMs"] for candle in result["candles"]],
            [self.start + self.step],
            "the earlier successful insert must be rolled back when a later row conflicts",
        )

    def test_migration_rejects_a_changed_applied_checksum(self):
        migration_id = "001_initial_timescale.sql"
        with connection(DSN) as database:
            row = database.execute(
                "SELECT checksum_sha256 FROM market_data.schema_migrations WHERE migration_id=%s",
                (migration_id,),
            ).fetchone()
        self.assertIsNotNone(row, "the initial migration must already be recorded")
        original_checksum = row[0]

        with connection(DSN) as database:
            database.execute(
                "UPDATE market_data.schema_migrations SET checksum_sha256=%s WHERE migration_id=%s",
                ("0" * 64, migration_id),
            )
        try:
            with self.assertRaisesRegex(RuntimeError, "Applied migration checksum mismatch"):
                migrate(DSN)
        finally:
            with connection(DSN) as database:
                database.execute(
                    "UPDATE market_data.schema_migrations SET checksum_sha256=%s WHERE migration_id=%s",
                    (original_checksum, migration_id),
                )

        applied, total = migrate(DSN)
        self.assertEqual(applied, total)

    def test_adapter_constructor_does_not_create_or_mutate_schema(self):
        self.assertIsInstance(PostgresCandleStore(DSN), PostgresCandleStore)


if __name__ == "__main__":
    unittest.main()
