import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from data_lake.__main__ import main


class DataLakeCliTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.database = Path(self.temp.name) / "lake.sqlite3"

    def command(self, *args):
        output, errors = io.StringIO(), io.StringIO()
        with patch.object(sys, "argv", ["data_lake", *args]), contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
            main()
        return json.loads(output.getvalue())

    def test_explicit_init_and_archive_are_idempotent_and_reject_oversized_or_future_input(self):
        from futures_intelligence.import_collector import build_snapshot
        from market_data.archive import read_snapshots

        self.assertTrue(self.command("init", "--db", str(self.database))["initialized"])
        snapshot = build_snapshot(0, 10_000, 10_001)
        path = Path(self.temp.name) / "intelligence.json"
        path.write_text(json.dumps(snapshot))
        first = self.command("archive-intelligence", "--db", str(self.database), "--input", str(path))
        second = self.command("archive-intelligence", "--db", str(self.database), "--input", str(path))
        self.assertTrue(first["inserted"])
        self.assertFalse(second["inserted"])
        self.assertEqual([snapshot], read_snapshots(self.database, 0, 20_000, 20_000))
        path.write_bytes(b" " * 65_537)
        with self.assertRaises(SystemExit) as failed:
            self.command("archive-intelligence", "--db", str(self.database), "--input", str(path))
        self.assertEqual(1, failed.exception.code)
        path.write_text(json.dumps(build_snapshot(0, 20_000, 20_001)))
        with patch("data_lake.__main__.time.time_ns", return_value=20_000 * 1_000_000), self.assertRaises(SystemExit):
            self.command("archive-intelligence", "--db", str(self.database), "--input", str(path))

    def test_long_backfill_chunks_the_window_and_keeps_exchange_rate_limiting(self):
        step, bars = 900_000, 2100
        calls = []

        class Exchange:
            id = "binanceusdm"

            def load_markets(self):
                market = dict(symbol="BTC/USDT:USDT", id="BTCUSDT", base="BTC", quote="USDT", settle="USDT",
                              active=True, swap=True, linear=True, spot=False)
                return {market["symbol"]: market}

            def fetch_time(self):
                return (bars + 1) * step

            def fetch_ohlcv(self, symbol, *, timeframe, since, limit, params):
                calls.append((since, limit, params["endTime"]))
                end = min(since + limit * step, params["endTime"] + 1)
                return [[opened, 100, 101, 99, 100.5, 2] for opened in range(since, end, step)]

        def exchange(config):
            self.assertTrue(config["enableRateLimit"])
            self.assertEqual(15_000, config["timeout"])
            return Exchange()

        with patch.dict(sys.modules, {"ccxt": SimpleNamespace(binanceusdm=exchange)}):
            result = self.command("backfill", "--db", str(self.database), "--timeframe", "15m",
                                  "--start-ms", "0", "--end-ms", str(bars * step))
        self.assertEqual(2100, result["inserted"])
        self.assertEqual(2, result["chunks"])
        self.assertEqual({"expected": 2100, "returned": 2100, "complete": True}, result["coverage"])
        self.assertEqual([1000, 1000, 100], [call[1] for call in calls])

    def test_invalid_backfill_fails_before_creating_database(self):
        with self.assertRaises(SystemExit) as failed:
            self.command("backfill", "--db", str(self.database), "--timeframe", "15m",
                         "--start-ms", "0", "--end-ms", str(100_001 * 900_000))
        self.assertEqual(1, failed.exception.code)
        self.assertFalse(self.database.exists())


if __name__ == "__main__":
    unittest.main()
