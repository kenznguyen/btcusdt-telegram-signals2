import sqlite3
import tempfile
import unittest
from pathlib import Path

from ops.live_market_data_probe import build_window, parse_klines, persist_candles


class LiveMarketDataProbeTests(unittest.TestCase):
    def setUp(self):
        self.interval = 900_000
        self.now = 1_800_000_000_000
        self.rows = []
        start = self.now - 200 * self.interval
        for index in range(200):
            opened = start + index * self.interval
            price = 60_000 + index
            self.rows.append([
                opened, str(price), str(price + 10), str(price - 10),
                str(price + 2), "1.5", opened + self.interval - 1,
                "90000", 12, "0.7", "42000", "0",
            ])

    def test_parse_accepts_only_closed_contiguous_valid_candles(self):
        parsed = parse_klines(self.rows, "15m", self.now)
        self.assertEqual(len(parsed), 200)
        self.assertTrue(all(row["isClosed"] for row in parsed))
        self.assertEqual(parsed[-1]["closeTimeMs"], self.rows[-1][6])

    def test_parse_rejects_gaps_and_invalid_ohlc(self):
        gap = self.rows.copy()
        gap[40] = list(gap[40])
        gap[40][0] += self.interval
        gap[40][6] += self.interval
        with self.assertRaisesRegex(ValueError, "GAP"):
            parse_klines(gap, "15m", self.now)
        invalid = self.rows.copy()
        invalid[10] = list(invalid[10])
        invalid[10][2] = "1"
        with self.assertRaisesRegex(ValueError, "OHLC"):
            parse_klines(invalid, "15m", self.now)

    def test_parse_drops_current_open_candle(self):
        rows = self.rows + [[
            self.now, "60000", "60010", "59990", "60002", "1",
            self.now + self.interval - 1, "90000", 1, "0.5", "30000", "0",
        ]]
        parsed = parse_klines(rows, "15m", self.now)
        self.assertEqual(len(parsed), 200)

    def test_window_and_sqlite_persistence_preserve_dataset_fingerprint(self):
        parsed = parse_klines(self.rows, "15m", self.now)
        window = build_window(parsed, "15m")
        self.assertTrue(window["coverage"]["complete"])
        self.assertEqual(window["coverage"]["expected"], 200)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "isolated.sqlite3"
            digest = persist_candles(path, "15m", parsed)
            with sqlite3.connect(path) as db:
                integrity = db.execute("PRAGMA integrity_check").fetchone()[0]
                count = db.execute("SELECT COUNT(*) FROM candles").fetchone()[0]
            self.assertEqual(integrity, "ok")
            self.assertEqual(count, 200)
            self.assertEqual(digest, window["datasetVersion"])


if __name__ == "__main__":
    unittest.main()
