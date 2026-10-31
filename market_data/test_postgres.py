"""Live TimescaleDB parity tests. Run only against a dedicated disposable test database."""

import os
import tempfile
import time
import unittest
from pathlib import Path

try:
    import psycopg
except ImportError:  # SQLite-only environments can still run the ordinary suite.
    psycopg = None

from market_data.repository import PostgresRepository, SQLiteRepository
from market_data.store import Candle, CandleStore, INTERVAL_MS


DATABASE_URL = os.environ.get("MARKET_DATA_TEST_DATABASE_URL", "")
STEP = INTERVAL_MS["15m"]


@unittest.skipUnless(psycopg is not None and DATABASE_URL, "requires Codemagic TimescaleDB test database")
class PostgresRepositoryIntegrationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with psycopg.connect(DATABASE_URL) as connection:
            database_name = connection.info.dbname
            confirmation = os.environ.get("MARKET_DATA_TEST_DB_CONFIRMATION", "")
            if "test" not in database_name.lower() or confirmation != database_name:
                raise RuntimeError(
                    "Refusing destructive integration setup: database name must contain 'test' "
                    "and MARKET_DATA_TEST_DB_CONFIRMATION must exactly match it"
                )
            migration = Path(__file__).parent / "migrations" / "001_initial_timescale.sql"
            with connection.cursor() as cursor:
                cursor.execute(migration.read_text(encoding="utf-8"), prepare=False)
        cls.repository = PostgresRepository(DATABASE_URL)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.sqlite = SQLiteRepository(Path(self.temp.name) / "market.sqlite3")
        self.step = STEP
        self.start = (time.time_ns() // 1_000_000 // self.step - 100) * self.step
        with psycopg.connect(DATABASE_URL) as connection:
            connection.execute(
                "DELETE FROM market_data.candles WHERE exchange='binance' "
                "AND market_type='USDT_PERPETUAL' AND symbol='BTCUSDT' "
                "AND timeframe='15m' AND open_time_ms BETWEEN %s AND %s",
                (self.start, self.start + 20 * self.step),
            )

    def candle(self, slot=0, **changes):
        values = dict(
            timeframe="15m",
            open_time_ms=self.start + slot * self.step,
            open="100.000",
            high="102",
            low="99",
            close="101",
            volume="5.00",
            available_at_ms=self.start + (slot + 1) * self.step + 123,
        )
        values.update(changes)
        return Candle(**values)

    def test_postgres_and_sqlite_return_identical_window_and_dataset_hash(self):
        candles = [self.candle(0), self.candle(2, open="101.25", high="103", close="102")]
        self.assertEqual(self.repository.insert(candles), 2)
        self.assertEqual(self.sqlite.insert(candles), 2)
        postgres = self.repository.read_window(
            "BTCUSDT", "15m", self.start, self.start + 3 * self.step
        )
        sqlite = self.sqlite.read_window(
            "BTCUSDT", "15m", self.start, self.start + 3 * self.step
        )
        self.assertEqual(postgres, sqlite)
        self.assertEqual(postgres["coverage"]["returned"], 2)
        self.assertFalse(postgres["coverage"]["complete"])

    def test_duplicate_keeps_first_available_time_and_conflict_rolls_back_batch(self):
        original = self.candle(0)
        self.assertEqual(self.repository.insert([original]), 1)
        before = self.repository.read_window(
            "BTCUSDT", "15m", self.start, self.start + self.step
        )
        later = self.candle(0, available_at_ms=original.available_at_ms + 10_000)
        self.assertEqual(self.repository.insert([later]), 0)
        after = self.repository.read_window(
            "BTCUSDT", "15m", self.start, self.start + self.step
        )
        self.assertEqual(after, before)

        with self.assertRaisesRegex(ValueError, "Conflicting closed candle"):
            self.repository.insert([
                self.candle(1),
                self.candle(0, close="100.5"),
            ])
        window = self.repository.read_window(
            "BTCUSDT", "15m", self.start, self.start + 2 * self.step
        )
        self.assertEqual(window["coverage"]["returned"], 1)

    def test_as_of_filter_uses_original_observation_timestamp(self):
        candle = self.candle(0)
        self.repository.insert([candle])
        hidden = self.repository.read_window(
            "BTCUSDT", "15m", self.start, self.start + self.step,
            as_of_ms=candle.available_at_ms - 1,
        )
        visible = self.repository.read_window(
            "BTCUSDT", "15m", self.start, self.start + self.step,
            as_of_ms=candle.available_at_ms,
        )
        self.assertEqual(hidden["candles"], [])
        self.assertEqual(visible["candles"][0]["availableAtMs"], candle.available_at_ms)

    def test_database_rejects_nonfinite_numeric_values(self):
        with self.assertRaises(psycopg.Error):
            with psycopg.connect(DATABASE_URL) as connection:
                connection.execute(
                    "INSERT INTO market_data.candles "
                    "(exchange, market_type, symbol, timeframe, open_time_ms, "
                    "open, high, low, close, volume, available_at_ms) "
                    "VALUES ('binance','USDT_PERPETUAL','BTCUSDT','15m',%s,"
                    "'NaN',102,99,101,5,%s)",
                    (self.start + 10 * self.step, self.start + 11 * self.step),
                )


if __name__ == "__main__":
    unittest.main()
