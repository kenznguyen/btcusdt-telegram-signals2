from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from market_data.store import CandleStore, INTERVAL_MS, read_window
from market_data.sync import safe_exchange_error_message, sync_window
import ccxt


SYMBOL = "BTC/USDT:USDT"
START = 1_800_000_000_000
STEP = INTERVAL_MS["15m"]


def row(timestamp):
    return [timestamp, 100.01, 103.5, 99.0, 102.25, 1.25]


class Exchange:
    id = "binanceusdm"

    def __init__(self, pages):
        self.pages = list(pages)
        self.calls = []
        self.server_time = START + 10_000 * STEP
        self.time_calls = 0
        self.market = {"symbol": SYMBOL, "id": "BTCUSDT", "base": "BTC", "quote": "USDT",
                       "settle": "USDT", "active": True, "swap": True, "linear": True, "spot": False}

    def load_markets(self):
        return {SYMBOL: self.market}

    def fetch_time(self):
        self.time_calls += 1
        return self.server_time

    def fetch_ohlcv(self, symbol, timeframe, since, limit, params):
        self.calls.append((symbol, timeframe, since, limit, params))
        value = self.pages.pop(0)
        if isinstance(value, Exception):
            raise value
        return value


class CandleSyncTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = str(Path(self.directory.name) / "candles.sqlite3")
        self.store = CandleStore(self.path)

    def test_exact_futures_market_and_response_observation_time(self):
        received = START + 4 * STEP + 1234
        exchange = Exchange([[row(START), row(START + STEP)]])
        self.assertEqual(sync_window(exchange, self.store, "15m", START, START + 2 * STEP,
                                     now_ms=lambda: received), 2)
        self.assertEqual(exchange.calls, [(SYMBOL, "15m", START, 2, {"endTime": START + 2 * STEP - 1})])
        data = read_window(self.path, "BTCUSDT", "15m", START, START + 2 * STEP)
        self.assertTrue(data["coverage"]["complete"])
        self.assertEqual(data["candles"][0]["availableAtMs"], received)
        self.assertEqual(data["candles"][0]["open"], "100.01")
        self.assertEqual(exchange.time_calls, 1)

    def test_local_clock_ahead_does_not_close_an_open_exchange_candle(self):
        exchange = Exchange([[row(START), row(START + STEP)]])
        exchange.server_time = START + STEP + 1000
        observed_at = START + 3 * STEP
        self.assertEqual(sync_window(exchange, self.store, "15m", START, START + 2 * STEP,
                                     now_ms=lambda: observed_at), 1)
        data = read_window(self.path, "BTCUSDT", "15m", START, START + 2 * STEP)
        self.assertEqual(data["candles"][0]["availableAtMs"], observed_at)
        self.assertEqual(data["coverage"]["returned"], 1)
        self.assertEqual(exchange.time_calls, 1)

    def test_invalid_exchange_clock_is_rejected_before_ohlcv_fetch(self):
        for server_time in (None, True, -1, 1.0, 2 ** 63):
            with self.subTest(server_time=server_time):
                exchange = Exchange([])
                exchange.server_time = server_time
                with self.assertRaises(ValueError):
                    sync_window(exchange, self.store, "15m", START, START + STEP)
                self.assertEqual(exchange.calls, [])

    def test_paginates_bounded_requests_without_rewriting_first_observation(self):
        exchange = Exchange([[row(START + i * STEP) for i in range(1000)],
                             [row(START + 1000 * STEP)]])
        end = START + 1001 * STEP
        clock = iter([end + 1, end + 2])
        self.assertEqual(sync_window(exchange, self.store, "15m", START, end,
                                     now_ms=lambda: next(clock)), 1001)
        self.assertEqual([call[3] for call in exchange.calls], [1000, 1])
        self.assertEqual(exchange.calls[1][2], START + 1000 * STEP)
        duplicate = Exchange([[row(START)]])
        self.assertEqual(sync_window(duplicate, self.store, "15m", START, START + STEP,
                                     now_ms=lambda: end + 999), 0)
        first = read_window(self.path, "BTCUSDT", "15m", START, START + STEP)
        self.assertEqual(first["candles"][0]["availableAtMs"], end + 1)

    def test_skips_open_and_outside_window_candles_and_preserves_gaps(self):
        exchange = Exchange([[row(START - STEP), row(START), row(START + 2 * STEP),
                              row(START + 3 * STEP)]])
        end = START + 4 * STEP
        self.assertEqual(sync_window(exchange, self.store, "15m", START, end,
                                     now_ms=lambda: START + 2 * STEP + 1), 1)
        data = read_window(self.path, "BTCUSDT", "15m", START, end)
        self.assertFalse(data["coverage"]["complete"])
        self.assertEqual(data["coverage"]["returned"], 1)

    def test_rejects_spot_wrong_contract_and_inactive_market_before_fetch(self):
        for override in ({"spot": True}, {"id": "ETHUSDT"}, {"linear": False}, {"active": False}, {"swap": 1}):
            with self.subTest(override=override):
                exchange = Exchange([])
                exchange.market.update(override)
                with self.assertRaises(ValueError):
                    sync_window(exchange, self.store, "15m", START, START + STEP)
                self.assertEqual(exchange.calls, [])

    def test_bad_page_is_not_partially_committed_and_no_progress_fails(self):
        bad = row(START + STEP)
        bad[2] = 1
        invalid_pages = [[row(START), bad], [row(START + STEP), row(START)],
                         [row(START), row(START)], [row(START - STEP)], [[START, 100]]]
        for page in invalid_pages:
            with self.subTest(page=page):
                with self.assertRaises(ValueError):
                    sync_window(Exchange([page]), self.store, "15m", START, START + 2 * STEP,
                                now_ms=lambda: START + 3 * STEP)
                self.assertEqual(read_window(self.path, "BTCUSDT", "15m", START,
                                             START + 2 * STEP)["candles"], [])

    def test_exchange_not_available_reports_original_message_without_credentials(self):
        message = (
            "GET https://user:password@fapi.binance.com/fapi/v1/klines"
            "?symbol=BTCUSDT&apiKey=query-secret&signature=signed-secret "
            "X-MBX-APIKEY: header-secret Authorization: Bearer bearer-secret "
            "connection timed out"
        )
        error = ccxt.ExchangeNotAvailable(message)
        with self.assertRaises(ccxt.ExchangeNotAvailable) as raised:
            sync_window(Exchange([error]), self.store, "15m", START, START + STEP)

        diagnostic = safe_exchange_error_message(raised.exception)

        self.assertIn("connection timed out", diagnostic)
        self.assertIn("BTCUSDT", diagnostic)
        for secret in ("password", "query-secret", "signed-secret", "header-secret", "bearer-secret"):
            with self.subTest(secret=secret):
                self.assertNotIn(secret, diagnostic)
        self.assertIn("apiKey=[REDACTED]", diagnostic)
        self.assertIn("signature=[REDACTED]", diagnostic)
        self.assertIn("Authorization: [REDACTED]", diagnostic)

    def test_upstream_failure_propagates_and_empty_page_leaves_missing_data(self):
        with self.assertRaisesRegex(OSError, "offline"):
            sync_window(Exchange([OSError("offline")]), self.store, "15m", START, START + STEP)
        self.assertEqual(sync_window(Exchange([[]]), self.store, "15m", START, START + STEP), 0)
        self.assertFalse(read_window(self.path, "BTCUSDT", "15m", START, START + STEP)["coverage"]["complete"])

    def test_invalid_range_fails_before_network_and_module_help_needs_no_ccxt(self):
        exchange = Exchange([])
        for timeframe, start, end in (("1m", START, START + STEP), ("15m", START + 1, START + STEP),
                                      ("15m", START, START), ("15m", START, START + 2001 * STEP)):
            with self.subTest(timeframe=timeframe, start=start, end=end), self.assertRaises(ValueError):
                sync_window(exchange, self.store, timeframe, start, end)
        result = subprocess.run([sys.executable, "-m", "market_data.sync", "--help"],
                                capture_output=True, text=True, check=True)
        self.assertIn("--start-ms", result.stdout)
        self.assertEqual(exchange.calls, [])


if __name__ == "__main__":
    unittest.main()
