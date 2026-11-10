"""Isolated end-to-end T0 sync -> SQLite -> read-only API -> T2 HTTP consumer tests."""

import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch
from wsgiref.simple_server import make_server
from threading import Thread

from freqai_bridge.context import canonical_context
from freqai_bridge.http_candles import CandleHttpClient, CandleHttpConfig, CandleHttpError
from market_data.api import application
from market_data.feeder import LeaseStore
from market_data.store import CandleStore, INTERVAL_MS
from market_data.sync import sync_window
from market_data.write_gateway import SQLiteWriteGateway


STEP = INTERVAL_MS["15m"]
TOKEN = "g3-isolated-read-only-token"


def candle_row(open_time_ms):
    return [open_time_ms, 100.01, 103.5, 99.0, 102.25, 1.25]


class SyntheticBinanceUsdM:
    id = "binanceusdm"

    def __init__(self, rows, server_time_ms):
        self.rows = list(rows)
        self.server_time_ms = server_time_ms
        self.calls = []

    def load_markets(self):
        market = {
            "symbol": "BTC/USDT:USDT", "id": "BTCUSDT", "base": "BTC",
            "quote": "USDT", "settle": "USDT", "active": True,
            "swap": True, "linear": True, "spot": False,
        }
        return {market["symbol"]: market}

    def fetch_time(self):
        return self.server_time_ms

    def fetch_ohlcv(self, symbol, timeframe, since, limit, params):
        self.calls.append((symbol, timeframe, since, limit, params))
        return self.rows


class SQLiteT0ToT2DataFlowTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.db_path = Path(self.temp.name) / "isolated-market-data.sqlite3"

        # Keep the requested two-bar window safely behind wall-clock time so
        # the local API's generatedAtMs and the consumer clock are monotonic.
        wall_now = time.time_ns() // 1_000_000
        self.end_ms = ((wall_now - 180_000) // STEP) * STEP
        self.start_ms = self.end_ms - 2 * STEP
        self.as_of_ms = self.end_ms + 60_000
        self.observed_at_ms = self.end_ms + 30_000

        CandleStore(self.db_path)
        leases = LeaseStore(str(self.db_path))
        lease = leases.acquire("g3-isolated-test", self.start_ms, ttl_seconds=3600)
        self.gateway = SQLiteWriteGateway(
            store=CandleStore(self.db_path),
            lease_store=leases,
            owner_id="g3-isolated-test",
            generation_provider=lambda: lease.generation,
            clock=lambda: self.observed_at_ms,
        )

        self.server = make_server("127.0.0.1", 0, application)
        self.server_thread = Thread(target=self.server.serve_forever, daemon=True)
        self.server_thread.start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        self.base_url = f"http://127.0.0.1:{self.server.server_port}"

    def _consume(self, rows):
        exchange = SyntheticBinanceUsdM(rows, self.as_of_ms)
        inserted = sync_window(
            exchange, self.gateway, "15m", self.start_ms, self.end_ms,
            now_ms=lambda: self.observed_at_ms,
        )
        client = CandleHttpClient(
            CandleHttpConfig(
                base_url=self.base_url,
                token=TOKEN,
                max_lag_ms=120_000,
            ),
            clock_ms=lambda: time.time_ns() // 1_000_000,
        )
        with patch.dict(os.environ, {
            "MARKET_DATA_BACKEND": "sqlite",
            "MARKET_DATA_DB": str(self.db_path),
            "MARKET_DATA_TOKEN": TOKEN,
        }, clear=True):
            result = canonical_context(
                now_ms=self.as_of_ms,
                bars=2,
                client=client,
            )
        return inserted, exchange, result

    def test_sync_sqlite_api_and_t2_http_consumer_preserve_canonical_data(self):
        inserted, exchange, result = self._consume([
            candle_row(self.start_ms),
            candle_row(self.start_ms + STEP),
        ])

        self.assertEqual(inserted, 2)
        self.assertEqual(len(exchange.calls), 1)
        self.assertEqual(result["contractVersion"], "1.0.0")
        self.assertEqual(result["exchange"], "binance")
        self.assertEqual(result["marketType"], "USDT_PERPETUAL")
        self.assertEqual(result["symbol"], "BTCUSDT")
        self.assertEqual(result["timeframe"], "15m")
        self.assertEqual(result["startMs"], self.start_ms)
        self.assertEqual(result["endMs"], self.end_ms)
        self.assertEqual(result["asOfMs"], self.as_of_ms)
        self.assertEqual(result["coverage"], {
            "expected": 2, "returned": 2, "complete": True, "gaps": [],
        })
        self.assertEqual(len(result["candles"]), 2)
        self.assertEqual(result["candles"][0]["open"], "100.01")
        self.assertEqual(result["candles"][1]["openTimeMs"], self.start_ms + STEP)
        self.assertTrue(all(row["isClosed"] and row["quality"] == "VALIDATED"
                            for row in result["candles"]))
        self.assertTrue(all(row["availabilityKind"] == "FIRST_OBSERVED"
                            for row in result["candles"]))
        self.assertEqual(result["candles"][0]["availableAtMs"], self.observed_at_ms)
        self.assertRegex(result["datasetVersion"], r"^sha256:[0-9a-f]{64}$")
        self.assertTrue(result["freshness"]["evaluable"])

    def test_t2_http_consumer_fails_closed_when_sqlite_coverage_has_a_gap(self):
        with self.assertRaises(CandleHttpError) as caught:
            self._consume([candle_row(self.start_ms)])
        self.assertEqual(caught.exception.reason, "COVERAGE_INCOMPLETE")


if __name__ == "__main__":
    unittest.main()
