"""SQLite/TimescaleDB contract parity tests; DB is supplied by Codemagic."""

import os
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from market_data.api import application
from market_data.migrations import migrate
from market_data.postgres import PostgresCandleStore, connection, read_window as read_postgres_window
from market_data.store import Candle, CandleStore, INTERVAL_MS, read_window
from market_data.sync import sync_window
from market_data.storage import create_store


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
        self.pg_store = create_store("postgres", postgres_dsn=DSN)
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


    def test_api_reads_from_postgres_and_maps_connection_failure_to_503(self):
        self.pg_store.insert([self.candle()])
        query = (f"symbol=BTCUSDT&timeframe=15m&startMs={self.start}"
                 f"&endMs={self.start+self.step}")
        environ = {
            "REQUEST_METHOD": "GET", "PATH_INFO": "/v1/candles",
            "QUERY_STRING": query, "HTTP_AUTHORIZATION": "Bearer test-token",
        }
        status = []
        with patch.dict(os.environ, {
            "MARKET_DATA_BACKEND": "postgres",
            "MARKET_DATA_POSTGRES_DSN": DSN,
            "MARKET_DATA_TOKEN": "test-token",
        }, clear=True):
            body = b"".join(application(environ, lambda value, headers: status.append(value)))
        self.assertEqual(status[0].split()[0], "200")
        import json
        payload = json.loads(body)
        self.assertEqual(payload["candles"][0]["openTimeMs"], self.start)
        self.assertEqual(payload["candles"][0]["open"], "100.12345678901234567890123456789")

        status.clear()
        with patch.dict(os.environ, {
            "MARKET_DATA_BACKEND": "postgres",
            "MARKET_DATA_POSTGRES_DSN": "postgresql://invalid:invalid@127.0.0.1:1/invalid?connect_timeout=1",
            "MARKET_DATA_TOKEN": "test-token",
        }, clear=True):
            body = b"".join(application(environ, lambda value, headers: status.append(value)))
        self.assertEqual(status[0].split()[0], "503")
        self.assertEqual(json.loads(body), {"error": "STORE_UNAVAILABLE"})

    def test_ingestion_writes_closed_candles_through_postgres_factory(self):
        start, step = self.start, self.step

        class Exchange:
            id = "binanceusdm"

            def load_markets(self):
                market = dict(symbol="BTC/USDT:USDT", id="BTCUSDT", base="BTC", quote="USDT",
                              settle="USDT", active=True, swap=True, linear=True, spot=False)
                return {market["symbol"]: market}

            def fetch_time(self):
                return start + step

            def fetch_ohlcv(self, *args, **kwargs):
                return [[start, 100, 102, 99, 101, 5]]

        inserted = sync_window(
            Exchange(), self.pg_store, "15m", start, start+step,
            now_ms=lambda: start+step,
        )
        self.assertEqual(inserted, 1)
        result = read_postgres_window(DSN, "BTCUSDT", "15m", start, start+step)
        self.assertEqual(result["coverage"]["returned"], 1)
        self.assertEqual(result["candles"][0]["close"], "101")

    def test_adapter_constructor_does_not_create_or_mutate_schema(self):
        self.assertIsInstance(PostgresCandleStore(DSN), PostgresCandleStore)


if __name__ == "__main__":
    unittest.main()
