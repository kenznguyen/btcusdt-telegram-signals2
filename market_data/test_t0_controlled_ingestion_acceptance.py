"""Offline T0 controlled-ingestion acceptance contract.

All writes target a temporary SQLite database. Exchange responses are synthetic;
this suite never opens a network connection or uses canonical storage.
"""
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from market_data.api import application
from market_data.feeder import LeaseStore
from market_data.store import CandleStore, INTERVAL_MS, read_window
from market_data.sync import EXCHANGE_SYMBOL, sync_window
from market_data.write_gateway import SQLiteWriteGateway


START_MS = 1_800_000_000_000  # UTC boundary aligned to both 15m and 1h
WINDOW_MS = 24 * 60 * 60 * 1000
END_MS = START_MS + WINDOW_MS


class SyntheticBinanceUSDm:
    """Deterministic CCXT-shaped exchange double; no network methods."""

    id = "binanceusdm"

    def __init__(self):
        self.calls = []

    def load_markets(self):
        return {
            EXCHANGE_SYMBOL: {
                "symbol": EXCHANGE_SYMBOL,
                "id": "BTCUSDT",
                "base": "BTC",
                "quote": "USDT",
                "settle": "USDT",
                "active": True,
                "swap": True,
                "linear": True,
                "spot": False,
            }
        }

    def fetch_time(self):
        return END_MS + 10_000

    def fetch_ohlcv(self, symbol, timeframe, since, limit, params):
        self.calls.append((symbol, timeframe, since, limit, params))
        interval = INTERVAL_MS[timeframe]
        count = min(limit, (END_MS - since) // interval)
        return [
            [since + index * interval, 100.0, 102.0, 99.0, 101.0, 1.25]
            for index in range(count)
        ]


def call_api(query, token):
    captured = {}

    def start_response(status, headers):
        captured["status"] = status
        captured["headers"] = headers

    environ = {
        "REQUEST_METHOD": "GET",
        "PATH_INFO": "/v1/candles",
        "QUERY_STRING": query,
        "HTTP_AUTHORIZATION": "Bearer " + token,
    }
    body = b"".join(application(environ, start_response))
    return captured["status"], json.loads(body)


class T0ControlledIngestionOfflineAcceptanceTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.db_path = str(Path(self.temp.name) / "isolated-acceptance.sqlite3")
        self.candle_store = CandleStore(self.db_path)
        self.lease_store = LeaseStore(self.db_path)
        self.lease = self.lease_store.acquire(
            "offline-acceptance", START_MS, ttl_seconds=200_000
        )
        self.gateway = SQLiteWriteGateway(
            store=self.candle_store,
            lease_store=self.lease_store,
            owner_id="offline-acceptance",
            generation_provider=lambda: self.lease.generation,
            clock=lambda: END_MS + 2,
        )
        self.exchange = SyntheticBinanceUSDm()

    def test_24h_m15_h1_ingestion_is_complete_idempotent_and_api_hash_matches(self):
        expected = {"15m": 96, "1h": 24}
        first_hashes = {}

        for timeframe, expected_count in expected.items():
            with self.subTest(timeframe=timeframe):
                inserted = sync_window(
                    self.exchange,
                    self.gateway,
                    timeframe,
                    START_MS,
                    END_MS,
                    now_ms=lambda: END_MS + 1,
                )
                self.assertEqual(inserted, expected_count)

                first = read_window(
                    self.db_path, "BTCUSDT", timeframe, START_MS, END_MS
                )
                self.assertEqual(first["exchange"], "binance")
                self.assertEqual(first["marketType"], "USDT_PERPETUAL")
                self.assertEqual(first["coverage"]["expected"], expected_count)
                self.assertEqual(first["coverage"]["returned"], expected_count)
                self.assertTrue(first["coverage"]["complete"])
                self.assertEqual(first["coverage"]["gaps"], [])
                self.assertEqual(
                    [candle["openTimeMs"] for candle in first["candles"]],
                    list(range(START_MS, END_MS, INTERVAL_MS[timeframe])),
                )
                self.assertTrue(all(candle["isClosed"] for candle in first["candles"]))
                first_hashes[timeframe] = first["datasetVersion"]

                # A repeat sync must be a no-op and preserve first-observed data.
                second_inserted = sync_window(
                    self.exchange,
                    self.gateway,
                    timeframe,
                    START_MS,
                    END_MS,
                    now_ms=lambda: END_MS + 2,
                )
                self.assertEqual(second_inserted, 0)
                second = read_window(
                    self.db_path, "BTCUSDT", timeframe, START_MS, END_MS
                )
                self.assertEqual(second["datasetVersion"], first_hashes[timeframe])

                token = "offline-test-token"
                query = (
                    f"symbol=BTCUSDT&timeframe={timeframe}"
                    f"&startMs={START_MS}&endMs={END_MS}"
                )
                with patch.dict(os.environ, {
                    "MARKET_DATA_TOKEN": token,
                    "MARKET_DATA_BACKEND": "sqlite",
                    "MARKET_DATA_DB": self.db_path,
                }, clear=False):
                    status, payload = call_api(query, token)

                self.assertEqual(status, "200 OK")
                self.assertEqual(payload["datasetVersion"], first_hashes[timeframe])
                self.assertEqual(payload["coverage"]["returned"], expected_count)
                self.assertTrue(payload["coverage"]["complete"])

        # The only exchange used in this test is the deterministic local double.
        self.assertEqual(
            {call[1] for call in self.exchange.calls},
            {"15m", "1h"},
        )
        self.assertTrue(Path(self.db_path).is_file())


if __name__ == "__main__":
    unittest.main(verbosity=2)
