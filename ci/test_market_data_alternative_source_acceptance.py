import sqlite3
import tempfile
import unittest
from pathlib import Path

from ci.market_data_alternative_source_acceptance import (
    EXCHANGE_ID, SYMBOL, fetch_closed_window, initialize_database,
    persist_candles, read_dataset, validate_market
)

START = 1_800_000_000_000
STEP = 900_000


def row(opened):
    return [opened, 100.0, 105.0, 99.0, 102.0, 1.5]


class FakeKraken:
    id = "kraken"

    def __init__(self, rows=None):
        self.rows = rows or []
        self.market = {"symbol": SYMBOL, "base": "BTC", "quote": "USDT",
                       "active": True, "spot": True, "swap": False}

    def load_markets(self):
        return {SYMBOL: self.market}

    def fetch_time(self):
        return START + 10 * STEP

    def fetch_ohlcv(self, symbol, timeframe, since, limit):
        self.assertions = (symbol, timeframe, since, limit)
        return self.rows


class AlternativeSourceAcceptanceTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.db_path = Path(self.temp.name) / "alternative.sqlite3"
        initialize_database(self.db_path)

    def test_only_active_kraken_spot_btc_usdt_is_accepted(self):
        validate_market(FakeKraken())
        for exchange_id, override in (
            ("binanceusdm", {}),
            ("kraken", {"spot": False}),
            ("kraken", {"swap": True}),
            ("kraken", {"active": False}),
            ("kraken", {"quote": "USD"}),
        ):
            fake = FakeKraken()
            fake.id = exchange_id
            fake.market.update(override)
            with self.subTest(exchange=exchange_id, override=override), self.assertRaises(ValueError):
                validate_market(fake)

    def test_fetch_filters_open_candle_and_keeps_only_closed_rows(self):
        exchange = FakeKraken([row(START), row(START + STEP)])
        candles = fetch_closed_window(exchange, "15m", START, START + 2 * STEP,
                                      now_ms=START + STEP + 500)
        self.assertEqual([item["openTimeMs"] for item in candles], [START])
        self.assertEqual(candles[0]["availableAtMs"], START + 2 * STEP)
        self.assertEqual(exchange.assertions, (SYMBOL, "15m", START, 2))

    def test_persisted_readback_and_repeat_sync_are_idempotent(self):
        exchange = FakeKraken([row(START), row(START + STEP)])
        candles = fetch_closed_window(exchange, "15m", START, START + 2 * STEP,
                                      now_ms=START + 3 * STEP)
        self.assertEqual(persist_candles(self.db_path, "15m", candles), 2)
        first = read_dataset(self.db_path, "15m", START, START + 2 * STEP)
        self.assertTrue(first["coverage"]["complete"])
        later = [dict(item, availableAtMs=START + 4 * STEP) for item in candles]
        self.assertEqual(persist_candles(self.db_path, "15m", later), 0)
        second = read_dataset(self.db_path, "15m", START, START + 2 * STEP)
        self.assertEqual(first["datasetVersion"], second["datasetVersion"])
        self.assertEqual(second["candles"][0]["availableAtMs"], START + 3 * STEP)

    def test_conflicting_existing_candle_is_rejected_without_overwrite(self):
        candle = {"openTimeMs": START, "open": "100", "high": "105", "low": "99",
                  "close": "102", "volume": "1.5", "availableAtMs": START + STEP}
        persist_candles(self.db_path, "15m", [candle])
        changed = dict(candle, close="103")
        with self.assertRaisesRegex(ValueError, "Conflicting Kraken candle"):
            persist_candles(self.db_path, "15m", [changed])
        with sqlite3.connect(self.db_path) as db:
            stored = db.execute("SELECT close FROM alternative_candles").fetchone()[0]
        self.assertEqual(stored, "102")

    def test_readback_reports_gaps_instead_of_fabricating_candles(self):
        candle = {"openTimeMs": START, "open": "100", "high": "105", "low": "99",
                  "close": "102", "volume": "1.5", "availableAtMs": START + STEP}
        persist_candles(self.db_path, "15m", [candle])
        result = read_dataset(self.db_path, "15m", START, START + 3 * STEP)
        self.assertFalse(result["coverage"]["complete"])
        self.assertEqual(result["coverage"]["returned"], 1)
        self.assertEqual(len(result["coverage"]["gaps"]), 1)


if __name__ == "__main__":
    unittest.main()
