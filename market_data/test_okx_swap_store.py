import sqlite3
import tempfile
import unittest
from pathlib import Path
from market_data.okx_swap import OkxSwapCandle
from market_data.okx_swap_store import OkxSwapSQLiteStore

START=1_800_000_000_000
STEP=900_000

def candle(opened,close="102",available=None):
    return OkxSwapCandle("15m",opened,"100","105","99",close,"1.25","125",
                         available if available is not None else opened+STEP)

class OkxSwapStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        root=Path(self.temp.name)
        self.shadow=root/"okx-shadow.sqlite3"; self.canonical=root/"binance.sqlite3"
        self.store=OkxSwapSQLiteStore(self.shadow,canonical_db_path=self.canonical)
    def tearDown(self): self.temp.cleanup()

    def test_persists_isolated_okx_swap_and_reports_coverage_hash(self):
        self.assertEqual(self.store.insert([candle(START)]),1)
        result=self.store.read_window("15m",START,START+2*STEP)
        self.assertEqual(result["exchange"],"okx")
        self.assertEqual(result["symbol"],"BTC-USDT-SWAP")
        self.assertEqual(result["candles"][0]["volumeBtc"],"1.25")
        self.assertFalse(result["coverage"]["complete"])
        self.assertTrue(result["datasetVersion"].startswith("sha256:"))

    def test_retry_is_idempotent_and_keeps_first_observation(self):
        self.assertEqual(self.store.insert([candle(START,available=START+STEP+1)]),1)
        self.assertEqual(self.store.insert([candle(START,available=START+STEP+9)]),0)
        self.assertEqual(self.store.read_window("15m",START,START+STEP)["candles"][0]["availableAtMs"],START+STEP+1)

    def test_conflict_rolls_back_prior_insert_in_batch(self):
        self.store.insert([candle(START)])
        with self.assertRaisesRegex(ValueError,"immutable"):
            self.store.insert([candle(START+STEP),candle(START,close="103")])
        rows=self.store.read_window("15m",START,START+2*STEP)["candles"]
        self.assertEqual([x["openTimeMs"] for x in rows],[START])

    def test_refuses_canonical_path_and_never_writes_to_it(self):
        with self.assertRaisesRegex(ValueError,"separate"):
            OkxSwapSQLiteStore(self.canonical,canonical_db_path=self.canonical)
        with sqlite3.connect(self.canonical) as db:
            db.execute("CREATE TABLE sentinel (value TEXT)")
            db.execute("INSERT INTO sentinel VALUES ('binance')")
        before=self.canonical.stat().st_mtime_ns
        self.store.insert([candle(START)])
        self.assertEqual(self.canonical.stat().st_mtime_ns,before)
        with sqlite3.connect(self.canonical) as db:
            self.assertEqual(db.execute("SELECT value FROM sentinel").fetchall(),[("binance",)])

if __name__=="__main__": unittest.main()
