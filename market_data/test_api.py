import json
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from market_data.api import application
from market_data.store import Candle, CandleStore, INTERVAL_MS
from market_data.sync import sync_window


class CandleApiTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.db = Path(self.temp.name) / "candles.sqlite3"
        self.interval = INTERVAL_MS["15m"]
        self.start = 1_800_000_000_000 // self.interval * self.interval
        store = CandleStore(self.db)
        store.insert([Candle("15m", self.start, "100.01", "101", "99", "100.5", "2.50", self.start + self.interval + 7)])
        self.config = {"MARKET_DATA_DB": str(self.db), "MARKET_DATA_TOKEN": "read-only-token"}

    def request(self, query=None, token="read-only-token", method="GET", path="/v1/candles"):
        query = query if query is not None else f"symbol=BTCUSDT&timeframe=15m&startMs={self.start}&endMs={self.start + 2*self.interval}"
        status = []
        environ = {"REQUEST_METHOD": method, "PATH_INFO": path, "QUERY_STRING": query,
                   "HTTP_AUTHORIZATION": "Bearer " + token}
        with patch.dict(os.environ, self.config, clear=True):
            body = b"".join(application(environ, lambda s, h: status.append((s, h))))
        self.assertIn(("Cache-Control", "no-store"), status[0][1])
        return int(status[0][0].split()[0]), json.loads(body)

    def test_reads_persisted_decimal_candles_and_reports_gap(self):
        code, body = self.request()
        self.assertEqual(code, 200)
        self.assertEqual(body["exchange"], "binance")
        self.assertEqual(body["marketType"], "USDT_PERPETUAL")
        self.assertEqual(body["candles"][0]["open"], "100.01")
        self.assertTrue(body["candles"][0]["isClosed"])
        self.assertEqual(body["coverage"]["expected"], 2)
        self.assertEqual(body["coverage"]["returned"], 1)
        self.assertFalse(body["coverage"]["complete"])
        self.assertEqual(body["coverage"]["gaps"], [{"startMs": self.start + self.interval, "endMs": self.start + 2*self.interval}])

    def test_as_of_does_not_backdate_imported_history(self):
        query = f"symbol=BTCUSDT&timeframe=15m&startMs={self.start}&endMs={self.start+self.interval}&asOfMs={self.start+self.interval}"
        code, body = self.request(query)
        self.assertEqual(code, 200)
        self.assertEqual(body["candles"], [])
        self.assertFalse(body["coverage"]["complete"])

    def test_shared_lake_configuration_takes_precedence_over_local_path(self):
        self.config["DATA_LAKE_DATABASE_URL"] = str(self.db)
        missing = Path(self.temp.name) / "unused-local.sqlite3"
        self.config["MARKET_DATA_DB"] = str(missing)
        code, body = self.request()
        self.assertEqual(code, 200)
        self.assertEqual(body["candles"][0]["close"], "100.5")
        self.assertFalse(missing.exists())

    def test_missing_auth_or_store_fails_without_creating_database(self):
        self.assertEqual(self.request(token="wrong")[0], 401)
        self.config["MARKET_DATA_TOKEN"] = ""
        self.assertEqual(self.request()[0], 503)
        self.config["MARKET_DATA_TOKEN"] = "read-only-token"
        missing = Path(self.temp.name) / "absent.sqlite3"
        self.config["MARKET_DATA_DB"] = str(missing)
        code, body = self.request()
        self.assertEqual(code, 503)
        self.assertFalse(missing.exists())
        self.assertNotIn(str(missing), json.dumps(body))

    def test_invalid_duplicate_unbounded_and_unknown_parameters(self):
        base = f"symbol=BTCUSDT&timeframe=15m&startMs={self.start}&endMs={self.start+self.interval}"
        for query in (base + "&symbol=ETHUSDT", base + "&token=secret", base.replace("BTCUSDT", "ETHUSDT"),
                      base.replace("15m", "1d"), base.replace(str(self.start), "nan"),
                      base + "&asOfMs=-1", base.replace(str(self.start+self.interval), str(self.start+2001*self.interval)),
                      "x=" + "a"*2100):
            with self.subTest(query=query[:100]):
                self.assertEqual(self.request(query)[0], 400)

    def test_read_only_methods_and_process_health(self):
        self.assertEqual(self.request(method="POST")[0], 405)
        self.assertEqual(self.request(path="/v1/orders")[0], 404)
        code, body = self.request(path="/health", token="")
        self.assertEqual(code, 200)
        self.assertEqual(body, {"ok": True, "service": "canonical-market-data"})

    def test_corrupt_stored_prices_are_not_served_as_validated(self):
        with sqlite3.connect(self.db) as connection:
            connection.execute("UPDATE candles SET high='0'")
        code, body = self.request()
        self.assertEqual(code, 503)
        self.assertEqual(body, {"error": "STORE_UNAVAILABLE"})

    def test_sync_to_reopened_api_preserves_gaps_and_observation_time(self):
        start, step = self.start, self.interval

        class Exchange:
            id = "binanceusdm"

            def load_markets(self):
                market = dict(symbol="BTC/USDT:USDT", id="BTCUSDT", base="BTC", quote="USDT",
                              settle="USDT", active=True, swap=True, linear=True, spot=False)
                return {market["symbol"]: market}

            def fetch_time(self):
                return start + step

            def fetch_ohlcv(self, *args, **kwargs):
                return [[start, 100, 101, 99, 100.5, 2.5],
                        [start + step, 100, 102, 99, 101, 3]]

        path = Path(self.temp.name) / "pipeline.sqlite3"
        inserted = sync_window(Exchange(), CandleStore(path), "15m", start, start+2*step,
                               now_ms=lambda: start+3*step)
        self.assertEqual(inserted, 1)
        self.config["MARKET_DATA_DB"] = str(path)
        code, result = self.request()
        self.assertEqual(code, 200)
        self.assertEqual(result["coverage"]["returned"], 1)
        self.assertFalse(result["coverage"]["complete"])
        self.assertEqual(result["candles"][0]["availableAtMs"], start+3*step)
        self.assertEqual(result["candles"][0]["availabilityKind"], "FIRST_OBSERVED")


if __name__ == "__main__":
    unittest.main()
