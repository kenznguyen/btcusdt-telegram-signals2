import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from market_data.repository import (
    MarketDataUnavailable,
    SQLiteRepository,
    get_market_data_repository,
)
from market_data.store import Candle, CandleStore, INTERVAL_MS, read_window


class RepositoryContractTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "market.sqlite3"
        self.step = INTERVAL_MS["15m"]
        self.store = CandleStore(self.path)
        self.candles = [
            Candle("15m", 0, "100.000", "102", "99", "101", "5.00", self.step + 100),
            Candle("15m", 2 * self.step, "101", "103", "100", "102", "6", 3 * self.step + 200),
        ]

    def test_sqlite_repository_matches_legacy_store_contract(self):
        repository = SQLiteRepository(self.path)
        self.assertEqual(repository.insert(self.candles), 2)
        actual = repository.read_window("BTCUSDT", "15m", 0, 3 * self.step)
        expected = read_window(self.path, "BTCUSDT", "15m", 0, 3 * self.step)
        self.assertEqual(actual, expected)

    def test_repository_factory_keeps_sqlite_as_default_and_selects_postgres_explicitly(self):
        with patch.dict(os.environ, {"MARKET_DATA_DB": str(self.path)}, clear=True):
            self.assertIsInstance(get_market_data_repository(), SQLiteRepository)
        with patch.dict(os.environ, {
            "MARKET_DATA_DB": str(self.path),
            "MARKET_DATA_DATABASE_URL": "postgresql://unused",
        }, clear=True):
            repository = get_market_data_repository()
            self.assertEqual(type(repository).__name__, "PostgresRepository")
            self.assertEqual(repository.dsn, "postgresql://unused")

    def test_missing_configuration_fails_closed_without_creating_a_database(self):
        missing = Path(self.temp.name) / "must-not-be-created.sqlite3"
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(MarketDataUnavailable):
                get_market_data_repository()
        self.assertFalse(missing.exists())


if __name__ == "__main__":
    unittest.main()
