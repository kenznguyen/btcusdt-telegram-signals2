from pathlib import Path
import tempfile
import unittest

from data_lake.refresh import producer_lock, refresh_once
from market_data.store import CandleStore, read_window


class CollectorTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "lake.sqlite3"
        self.end = 1_800_000_000_000
        owner = self

        class Exchange:
            id = "binanceusdm"
            requests = []
            fail = False

            def load_markets(self):
                return {"BTC/USDT:USDT": dict(symbol="BTC/USDT:USDT", id="BTCUSDT", base="BTC", quote="USDT",
                    settle="USDT", active=True, swap=True, linear=True, spot=False)}

            def fetch_time(self):
                return owner.end

            def fetch_ohlcv(self, symbol, *, timeframe, since, limit, params):
                self.requests.append((timeframe, since, limit))
                if self.fail:
                    raise OSError("Upstream unavailable")
                return [[instant, 100, 101, 99, 100.5, 2] for instant in range(since, params["endTime"]+1, 900_000)][:limit]

        self.exchange = Exchange()

    def refresh(self):
        return refresh_once(self.exchange, self.path, ("15m",), 3, now_ms=lambda: self.end+5)

    def test_only_missing_closed_span_is_downloaded_and_observation_is_preserved(self):
        first = self.refresh()
        self.assertEqual(first["windows"][0]["inserted"], 3)
        self.assertTrue(first["windows"][0]["coverage"]["complete"])
        self.assertEqual(len(self.exchange.requests), 1)
        self.assertEqual(self.refresh()["windows"][0]["inserted"], 0)
        self.assertEqual(len(self.exchange.requests), 1)
        self.end += 900_000
        self.assertEqual(self.refresh()["windows"][0]["inserted"], 1)
        self.assertEqual(self.exchange.requests[-1][2], 1)
        window = read_window(self.path, "BTCUSDT", "15m", self.end-1_800_000, self.end)
        self.assertEqual(window["candles"][0]["availableAtMs"], self.end-900_000+5)

    def test_single_producer_lock_prevents_another_exchange_fetch(self):
        CandleStore(self.path)
        with producer_lock(self.path):
            with self.assertRaises(BlockingIOError):
                self.refresh()
        self.assertEqual(self.exchange.requests, [])
        self.assertEqual(self.refresh()["windows"][0]["inserted"], 3)

    def test_fetch_failure_remains_missing_and_later_pass_recovers(self):
        self.exchange.fail = True
        with self.assertRaises(OSError):
            self.refresh()
        self.assertEqual(read_window(self.path, "BTCUSDT", "15m", self.end-2_700_000, self.end)["candles"], [])
        self.exchange.fail = False
        self.assertTrue(self.refresh()["windows"][0]["coverage"]["complete"])

    def test_invalid_parameters_do_not_call_exchange(self):
        for frames, bars in ((("5m",), 1), (("15m", "15m"), 1), (("15m",), 2001), (("15m",), True)):
            with self.subTest(frames=frames, bars=bars), self.assertRaises(ValueError):
                refresh_once(self.exchange, self.path, frames, bars)
        self.assertFalse(self.path.exists())


if __name__ == "__main__":
    unittest.main()
