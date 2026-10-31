import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from market_data.store import Candle, INTERVAL_MS
from market_data.storage import (
    PostgresStore,
    SQLiteCandleStore,
    StoreConfigurationError,
    create_store,
    create_store_from_env,
)


class StorageFactoryTest(unittest.TestCase):
    def test_sqlite_is_the_default_and_preserves_existing_path_configuration(self):
        with tempfile.TemporaryDirectory() as directory:
            path = str(Path(directory) / "candles.sqlite3")
            store = create_store_from_env({"MARKET_DATA_DB": path})
            self.assertIsInstance(store, SQLiteCandleStore)
            self.assertEqual(store.path, Path(path))
            self.assertFalse(Path(path).exists())

    def test_explicit_postgres_requires_dsn_and_never_falls_back_to_sqlite(self):
        with self.assertRaisesRegex(StoreConfigurationError, "MARKET_DATA_POSTGRES_DSN"):
            create_store_from_env({"MARKET_DATA_BACKEND": "postgres", "MARKET_DATA_DB": "/tmp/ignored.sqlite"})
        with self.assertRaises(StoreConfigurationError):
            create_store("unknown", sqlite_path="/tmp/candles.sqlite")

    def test_postgres_factory_is_side_effect_free_until_used(self):
        store = create_store("postgres", postgres_dsn="postgresql://user:pass@127.0.0.1:5432/test")
        self.assertIsInstance(store, PostgresStore)

    def test_sqlite_reader_does_not_create_a_missing_database(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "missing.sqlite3"
            store = create_store("sqlite", sqlite_path=str(path))
            with self.assertRaises(FileNotFoundError):
                store.read_window("BTCUSDT", "15m", 0, 900_000)
            self.assertFalse(path.exists())


    def test_sqlite_factory_ingestion_and_read_share_one_contract(self):
        with tempfile.TemporaryDirectory() as directory:
            path = str(Path(directory) / "candles.sqlite3")
            store = create_store("sqlite", sqlite_path=path)
            step = INTERVAL_MS["15m"]
            candle = Candle("15m", 0, "100", "102", "99", "101", "5", step + 1)
            self.assertEqual(store.insert([candle]), 1)
            result = store.read_window("BTCUSDT", "15m", 0, step)
            self.assertEqual(result["candles"][0]["close"], "101")
            self.assertTrue(result["coverage"]["complete"])

    def test_postgres_connection_failure_is_not_reinterpreted_as_sqlite(self):
        store = create_store("postgres", postgres_dsn="postgresql://invalid")
        with patch("market_data.storage.read_postgres_window", side_effect=RuntimeError("unavailable")):
            with self.assertRaisesRegex(RuntimeError, "unavailable"):
                store.read_window("BTCUSDT", "15m", 0, 900_000)


if __name__ == "__main__":
    unittest.main()
