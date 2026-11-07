"""Offline acceptance contract for a bounded T0 controlled-ingestion window.

All writes use temporary SQLite databases, synthetic exchange data, and a
lease-fenced gateway. This suite never opens a canonical database or network.
"""
import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from market_data.api import application
from market_data.feeder import LeaseStore
from market_data.store import Candle, CandleStore, INTERVAL_MS, read_window
from market_data.sync import sync_window
from market_data.write_gateway import SQLiteWriteGateway


START = 1_800_000_000_000  # UTC-aligned 15m and 1h boundary
END = START + 24 * INTERVAL_MS["1h"]


def ohlcv(open_time_ms):
    return [open_time_ms, "100.01", "103.50", "99.00", "102.25", "1.25"]


class SyntheticBinanceUSDM:
    id = "binanceusdm"

    def __init__(self, timeframe):
        self.timeframe = timeframe
        self.interval = INTERVAL_MS[timeframe]
        self.market = {
            "symbol": "BTC/USDT:USDT", "id": "BTCUSDT", "base": "BTC",
            "quote": "USDT", "settle": "USDT", "active": True,
            "swap": True, "linear": True, "spot": False,
        }
        self.fetches = 0
        self.server_time = END + 1

    def load_markets(self):
        return {self.market["symbol"]: self.market}

    def fetch_time(self):
        return self.server_time

    def fetch_ohlcv(self, symbol, timeframe, since, limit, params):
        self.fetches += 1
        self.assert_request(symbol, timeframe, since, limit, params)
        return [ohlcv(timestamp) for timestamp in range(since, min(END, since + limit * self.interval), self.interval)]

    @staticmethod
    def assert_request(symbol, timeframe, since, limit, params):
        if symbol != "BTC/USDT:USDT" or timeframe not in ("15m", "1h"):
            raise AssertionError("unexpected market request")
        if limit < 1 or params.get("endTime") != END - 1:
            raise AssertionError("unexpected bounded-window request")


class ControlledIngestionAcceptanceTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.db_path = str(Path(self.temporary.name) / "isolated-acceptance.sqlite3")
        self.candles = CandleStore(self.db_path)
        self.leases = LeaseStore(self.db_path)
        self.lease = self.leases.acquire("acceptance-test", START, ttl_seconds=10_000_000)
        self.writer = SQLiteWriteGateway(
            store=self.candles,
            lease_store=self.leases,
            owner_id="acceptance-test",
            generation_provider=lambda: self.lease.generation,
            clock=lambda: END + 2,
        )

    def test_24_hour_window_has_exact_m15_and_h1_coverage_and_idempotent_hash(self):
        observations = {}
        for timeframe, expected in (("15m", 96), ("1h", 24)):
            exchange = SyntheticBinanceUSDM(timeframe)
            inserted_first = sync_window(
                exchange, self.writer, timeframe, START, END,
                now_ms=lambda: END + 1,
            )
            first = read_window(self.db_path, "BTCUSDT", timeframe, START, END)
            inserted_second = sync_window(
                exchange, self.writer, timeframe, START, END,
                now_ms=lambda: END + 3,
            )
            second = read_window(self.db_path, "BTCUSDT", timeframe, START, END)

            self.assertEqual(inserted_first, expected)
            self.assertEqual(first["coverage"]["expected"], expected)
            self.assertEqual(first["coverage"]["returned"], expected)
            self.assertTrue(first["coverage"]["complete"])
            self.assertEqual(first["coverage"]["gaps"], [])
            self.assertEqual(inserted_second, 0)
            self.assertEqual(second["coverage"]["returned"], expected)
            self.assertTrue(second["coverage"]["complete"])
            self.assertEqual(second["datasetVersion"], first["datasetVersion"])
            observations[timeframe] = first["datasetVersion"]

        self.assertEqual(set(observations), {"15m", "1h"})

    def test_read_api_returns_http_200_and_hash_matches_canonical_read(self):
        for timeframe in ("15m", "1h"):
            exchange = SyntheticBinanceUSDM(timeframe)
            sync_window(exchange, self.writer, timeframe, START, END, now_ms=lambda: END + 1)
            canonical = read_window(self.db_path, "BTCUSDT", timeframe, START, END)
            captured = {}

            def start_response(status, headers):
                captured["status"] = status
                captured["headers"] = headers

            query = (
                f"symbol=BTCUSDT&timeframe={timeframe}"
                f"&startMs={START}&endMs={END}"
            )
            environ = {
                "REQUEST_METHOD": "GET",
                "PATH_INFO": "/v1/candles",
                "QUERY_STRING": query,
                "HTTP_AUTHORIZATION": "Bearer acceptance-test-token",
            }
            with patch.dict(os.environ, {
                "MARKET_DATA_TOKEN": "acceptance-test-token",
                "MARKET_DATA_BACKEND": "sqlite",
                "MARKET_DATA_DB": self.db_path,
            }, clear=False):
                payload = b"".join(application(environ, start_response))

            response = json.loads(payload)
            self.assertEqual(captured["status"], "200 OK")
            self.assertEqual(response["coverage"]["complete"], True)
            self.assertEqual(response["coverage"]["returned"], 96 if timeframe == "15m" else 24)
            self.assertEqual(response["datasetVersion"], canonical["datasetVersion"])

    def test_conflicting_duplicate_rolls_back_entire_batch(self):
        original = Candle("15m", START, "100", "103", "99", "102", "1", END + 1)
        self.assertEqual(self.writer.write_batch([original]), 1)
        new_candle = Candle(
            "15m", START + INTERVAL_MS["15m"],
            "100", "103", "99", "102", "1", END + 1,
        )
        conflicting = Candle(
            "15m", START, "100", "104", "99", "102", "1", END + 1,
        )

        with self.assertRaisesRegex(ValueError, "Conflicting closed candle"):
            self.writer.write_batch([new_candle, conflicting])

        result = read_window(
            self.db_path, "BTCUSDT", "15m", START,
            START + 2 * INTERVAL_MS["15m"],
        )
        self.assertEqual(result["coverage"]["returned"], 1)
        self.assertEqual(result["candles"][0]["high"], "103")
        self.assertEqual(result["candles"][0]["openTimeMs"], START)

    def test_acceptance_is_isolated_from_repository_and_canonical_paths(self):
        self.assertTrue(Path(self.db_path).is_relative_to(Path(self.temporary.name)))
        self.assertFalse(Path(self.db_path).name in ("canonical.sqlite3", "market_data.sqlite3"))


if __name__ == "__main__":
    unittest.main()
