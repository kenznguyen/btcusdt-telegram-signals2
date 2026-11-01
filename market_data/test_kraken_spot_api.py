"""Contract tests for the isolated Kraken Spot read-only WSGI API."""

import json
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.parse import urlencode

from market_data.kraken_spot import InstrumentIdentity, SourceCandle
from market_data.kraken_spot_store import KrakenSpotSQLiteStore
from market_data.kraken_spot_api import application

START = 1_800_000_000_000
STEP = 900_000
TOKEN = "kraken-spot-read-only-test-token"


class KrakenSpotApiTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.db = root / "kraken-spot.sqlite3"
        self.canonical = root / "binance-canonical.sqlite3"
        self.store = KrakenSpotSQLiteStore(
            self.db, canonical_db_path=self.canonical
        )
        self.store.insert([
            SourceCandle(
                instrument=InstrumentIdentity("kraken", "SPOT", "XBTUSDT", "BTC/USDT"),
                timeframe="15m",
                open_time_ms=START,
                open="100.01",
                high="101",
                low="99",
                close="100.5",
                volume="2.50",
                available_at_ms=START + STEP + 10,
            )
        ])
        self.config = {
            "KRAKEN_SPOT_DB": str(self.db),
            "KRAKEN_SPOT_CANONICAL_DB": str(self.canonical),
            "KRAKEN_SPOT_API_TOKEN": TOKEN,
        }

    def request(self, *, path="/v1/kraken-spot/candles", query=None,
                token=TOKEN, method="GET", config=None):
        if query is None:
            query = urlencode({
                "symbol": "BTC/USDT",
                "timeframe": "15m",
                "startMs": START,
                "endMs": START + 2 * STEP,
            })
        status = []
        environ = {
            "REQUEST_METHOD": method,
            "PATH_INFO": path,
            "QUERY_STRING": query,
            "HTTP_AUTHORIZATION": "Bearer " + token,
        }
        with patch.dict(os.environ, self.config if config is None else config, clear=True):
            body = b"".join(application(environ, lambda value, headers: status.append((value, headers))))
        self.assertIn(("Cache-Control", "no-store"), status[0][1])
        return int(status[0][0].split()[0]), json.loads(body)

    def test_reads_only_kraken_spot_rows_and_returns_source_provenance(self):
        code, body = self.request()
        self.assertEqual(code, 200)
        self.assertEqual(body["exchange"], "kraken")
        self.assertEqual(body["marketType"], "SPOT")
        self.assertEqual(body["symbol"], "BTC/USDT")
        self.assertEqual(body["candles"][0]["open"], "100.01")
        self.assertEqual(body["candles"][0]["nativeMarketId"], "XBTUSDT")
        self.assertEqual(body["candles"][0]["source"], "ccxt.kraken")
        self.assertEqual(body["coverage"]["expected"], 2)
        self.assertEqual(body["coverage"]["returned"], 1)
        self.assertFalse(body["coverage"]["complete"])
        self.assertIn("generatedAtMs", body)

    def test_as_of_cutoff_is_forwarded_to_spot_store(self):
        query = urlencode({
            "symbol": "BTC/USDT", "timeframe": "15m",
            "startMs": START, "endMs": START + STEP,
            "asOfMs": START + STEP + 9,
        })
        code, body = self.request(query=query)
        self.assertEqual(code, 200)
        self.assertEqual(body["candles"], [])
        self.assertFalse(body["coverage"]["complete"])

    def test_canonical_binance_endpoint_is_not_exposed_by_this_application(self):
        code, body = self.request(path="/v1/candles")
        self.assertEqual(code, 404)
        self.assertEqual(body, {"error": "NOT_FOUND"})

    def test_rejects_unauthorized_and_unconfigured_requests(self):
        self.assertEqual(self.request(token="wrong")[0], 401)
        config = dict(self.config, KRAKEN_SPOT_API_TOKEN="")
        self.assertEqual(self.request(config=config)[0], 503)
        self.assertEqual(self.request(token="wrong", method="POST")[0], 405)

    def test_invalid_query_is_rejected(self):
        base = urlencode({
            "symbol": "BTC/USDT", "timeframe": "15m",
            "startMs": START, "endMs": START + STEP,
        })
        bad = (
            base + "&symbol=BTC%2FUSDT",
            base + "&unexpected=1",
            base.replace("BTC%2FUSDT", "BTCUSDT"),
            base.replace("15m", "5m"),
            base.replace(str(START), "nan"),
            base + "&asOfMs=-1",
            urlencode({
                "symbol": "BTC/USDT", "timeframe": "15m",
                "startMs": START, "endMs": START + 2001 * STEP,
            }),
            "x=" + "a" * 2100,
        )
        for query in bad:
            with self.subTest(query=query[:100]):
                self.assertEqual(self.request(query=query)[0], 400)

    def test_missing_database_fails_closed_without_creating_it(self):
        missing = Path(self.temp.name) / "not-created.sqlite3"
        config = dict(self.config, KRAKEN_SPOT_DB=str(missing))
        code, body = self.request(config=config)
        self.assertEqual(code, 503)
        self.assertEqual(body, {"error": "STORE_UNAVAILABLE"})
        self.assertFalse(missing.exists())

    def test_health_is_scoped_to_kraken_spot_service(self):
        code, body = self.request(path="/health", token="")
        self.assertEqual(code, 200)
        self.assertEqual(body, {"ok": True, "service": "kraken-spot-market-data"})

    def test_api_does_not_modify_either_database(self):
        spot_before = self.db.stat().st_mtime_ns
        with sqlite3.connect(self.canonical) as connection:
            connection.execute(
                "CREATE TABLE candles (exchange TEXT, market_type TEXT, symbol TEXT)"
            )
            connection.execute(
                "INSERT INTO candles VALUES ('binance', 'USDT_PERPETUAL', 'BTCUSDT')"
            )
        canonical_before = self.canonical.stat().st_mtime_ns

        self.assertEqual(self.request()[0], 200)

        self.assertEqual(self.db.stat().st_mtime_ns, spot_before)
        self.assertEqual(self.canonical.stat().st_mtime_ns, canonical_before)
        with sqlite3.connect(self.canonical) as connection:
            self.assertEqual(
                connection.execute("SELECT * FROM candles").fetchall(),
                [("binance", "USDT_PERPETUAL", "BTCUSDT")],
            )


if __name__ == "__main__":
    unittest.main()
