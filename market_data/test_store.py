import tempfile
import unittest
from pathlib import Path

from market_data.store import Candle, CandleStore, INTERVAL_MS, MAX_CANDLES, read_window


class CandleStoreTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "candles.sqlite3"
        self.store = CandleStore(self.path)
        self.step = INTERVAL_MS["15m"]

    def candle(self, slot=0, **changes):
        values = dict(timeframe="15m", open_time_ms=slot * self.step,
                      open="100.000", high="102", low="99", close="101", volume="5.00",
                      available_at_ms=(slot + 1) * self.step + 100)
        return Candle(**(values | changes))

    def window(self, count=4, **changes):
        return read_window(self.path, "BTCUSDT", "15m", 0, count * self.step, **changes)

    def test_persists_exact_decimals_and_closed_candle_identity(self):
        candle = self.candle(open="100.12345678901234567890123456789")
        self.assertEqual(self.store.insert([candle]), 1)
        CandleStore(self.path)
        row = self.window(1)["candles"][0]
        self.assertEqual(row["open"], "100.12345678901234567890123456789")
        self.assertEqual(row["volume"], "5")
        self.assertEqual(row["closeTimeMs"], self.step)
        self.assertEqual(row["exchange"], "binance")
        self.assertEqual(row["marketType"], "USDT_PERPETUAL")
        self.assertTrue(row["isClosed"])
        self.assertEqual(row["availabilityKind"], "FIRST_OBSERVED")

    def test_duplicate_reimport_preserves_first_observation_and_dataset_version(self):
        self.store.insert([self.candle()])
        before = self.window(1)
        self.assertEqual(self.store.insert([self.candle(available_at_ms=self.step + 500)]), 0)
        self.assertEqual(self.window(1)["datasetVersion"], before["datasetVersion"])
        self.assertEqual(self.window(1)["candles"][0]["availableAtMs"], self.step + 100)

    def test_conflicting_candle_rolls_back_the_whole_batch(self):
        self.store.insert([self.candle()])
        with self.assertRaises(ValueError):
            self.store.insert([self.candle(1), self.candle(close="100.5")])
        self.assertEqual(self.window(2)["coverage"]["returned"], 1)

    def test_conflicting_duplicate_in_one_batch_is_atomic(self):
        with self.assertRaises(ValueError):
            self.store.insert([self.candle(), self.candle(close="100.5")])
        self.assertEqual(self.window(1)["candles"], [])

    def test_reports_leading_internal_trailing_gaps_without_filling(self):
        self.store.insert([self.candle(1), self.candle(3)])
        result = self.window(5)
        self.assertEqual([c["openTimeMs"] for c in result["candles"]], [self.step, 3 * self.step])
        self.assertEqual(result["coverage"], {
            "expected": 5, "returned": 2, "complete": False,
            "gaps": [{"startMs": 0, "endMs": self.step},
                     {"startMs": 2 * self.step, "endMs": 3 * self.step},
                     {"startMs": 4 * self.step, "endMs": 5 * self.step}]})

    def test_as_of_filters_by_first_seen_time_without_backdating_history(self):
        self.store.insert([self.candle(available_at_ms=10 * self.step)])
        hidden = self.window(1, as_of_ms=9 * self.step)
        visible = self.window(1, as_of_ms=10 * self.step)
        self.assertEqual(hidden["candles"], [])
        self.assertTrue(visible["coverage"]["complete"])

    def test_dataset_version_changes_only_with_selected_content_or_query(self):
        empty = self.window(1)["datasetVersion"]
        self.store.insert([self.candle()])
        populated = self.window(1)["datasetVersion"]
        self.assertNotEqual(empty, populated)
        self.store.insert([self.candle(2)])
        self.assertEqual(populated, self.window(1)["datasetVersion"])

    def test_rejects_nonfinite_inconsistent_unclosed_and_oversized_values(self):
        for changes in [
            {"open": "NaN"}, {"close": "Infinity"}, {"volume": "-1"},
            {"low": "103"}, {"high": "100"}, {"open": "0"},
            {"open": "1e999999"}, {"volume": "0e999999"}, {"volume": "9" * 129},
            {"available_at_ms": self.step - 1}, {"open_time_ms": 1},
            {"open_time_ms": True}, {"available_at_ms": True},
            {"symbol": "ETHUSDT"}, {"timeframe": "1m"}, {"open": 100.0},
        ]:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.candle(**changes)

    def test_readonly_query_does_not_create_missing_database(self):
        missing = self.path.parent / "missing.sqlite3"
        with self.assertRaises(FileNotFoundError):
            read_window(missing, "BTCUSDT", "15m", 0, self.step)
        self.assertFalse(missing.exists())

    def test_rejects_unaligned_unbounded_or_wrong_market_queries(self):
        for args in [
            ("ETHUSDT", "15m", 0, self.step, None),
            ("BTCUSDT", "1m", 0, self.step, None),
            ("BTCUSDT", "15m", 1, self.step, None),
            ("BTCUSDT", "15m", 0, self.step + 1, None),
            ("BTCUSDT", "15m", 0, 0, None),
            ("BTCUSDT", "15m", 0, (MAX_CANDLES + 1) * self.step, None),
            ("BTCUSDT", "15m", 0, self.step, -1),
            ("BTCUSDT", "15m", 0, self.step, True),
        ]:
            with self.subTest(args=args), self.assertRaises(ValueError):
                read_window(self.path, *args)


if __name__ == "__main__":
    unittest.main()
