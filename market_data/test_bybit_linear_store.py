import sqlite3
import tempfile
import unittest
from pathlib import Path

from market_data.bybit_linear import BybitLinearCandle
from market_data.bybit_linear_store import BybitLinearSQLiteStore

START=1_800_000_000_000
STEP=900_000


def candle(opened, close="102", available=None):
    return BybitLinearCandle("15m",opened,"100","105","99",close,"1.25","125",
        available if available is not None else opened+STEP)


class BybitLinearStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        root=Path(self.temp.name)
        self.shadow=root/"bybit-shadow.sqlite3"
        self.canonical=root/"binance.sqlite3"
        self.store=BybitLinearSQLiteStore(self.shadow,canonical_db_path=self.canonical)
    def tearDown(self):
        self.temp.cleanup()

    def test_persists_only_bybit_linear_and_reports_gaps_and_hash(self):
        self.assertEqual(self.store.insert([candle(START)]),1)
        result=self.store.read_window("15m",START,START+2*STEP)
        self.assertEqual(result["exchange"],"bybit")
        self.assertEqual(result["marketType"],"LINEAR_PERPETUAL")
        self.assertEqual(result["candles"][0]["volumeBtc"],"1.25")
        self.assertFalse(result["coverage"]["complete"])
        self.assertTrue(result["datasetVersion"].startswith("sha256:"))

    def test_repeat_is_idempotent_and_preserves_first_observation(self):
        self.assertEqual(self.store.insert([candle(START,available=START+STEP+1)]),1)
        self.assertEqual(self.store.insert([candle(START,available=START+STEP+9)]),0)
        result=self.store.read_window("15m",START,START+STEP)
        self.assertEqual(result["candles"][0]["availableAtMs"],START+STEP+1)

    def test_conflict_rolls_back_new_rows_in_same_batch(self):
        self.store.insert([candle(START)])
        with self.assertRaisesRegex(ValueError,"immutable"):
            self.store.insert([candle(START+STEP),candle(START,close="103")])
        result=self.store.read_window("15m",START,START+2*STEP)
        self.assertEqual([x["openTimeMs"] for x in result["candles"]],[START])

    def test_refuses_binance_canonical_database_path(self):
        with self.assertRaisesRegex(ValueError,"separate"):
            BybitLinearSQLiteStore(self.canonical,canonical_db_path=self.canonical)

    def test_does_not_modify_binance_canonical_database(self):
        with sqlite3.connect(self.canonical) as db:
            db.execute("CREATE TABLE candles (exchange TEXT, symbol TEXT)")
            db.execute("INSERT INTO candles VALUES ('binance','BTCUSDT')")
        before=self.canonical.stat().st_mtime_ns
        self.store.insert([candle(START)])
        self.assertEqual(self.canonical.stat().st_mtime_ns,before)
        with sqlite3.connect(self.canonical) as db:
            self.assertEqual(db.execute("SELECT * FROM candles").fetchall(),[("binance","BTCUSDT")])


if __name__ == "__main__":
    unittest.main()
