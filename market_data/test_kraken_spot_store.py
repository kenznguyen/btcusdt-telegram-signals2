"""Contract tests for the isolated Kraken Spot SQLite store."""

import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from market_data.kraken_spot import InstrumentIdentity, SourceCandle
from market_data.kraken_spot_store import KrakenSpotSQLiteStore

START = 1_800_000_000_000
STEP = 900_000
IDENTITY = InstrumentIdentity("kraken", "SPOT", "XBTUSDT", "BTC/USDT")


def candle(opened, *, close="102", available=None, instrument=IDENTITY):
    return SourceCandle(
        instrument=instrument,
        timeframe="15m",
        open_time_ms=opened,
        open="100",
        high="105",
        low="99",
        close=close,
        volume="1.5",
        available_at_ms=available if available is not None else opened + STEP,
    )


class KrakenSpotSQLiteStoreTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.kraken_path = self.root / "kraken-spot.sqlite3"
        self.binance_path = self.root / "binance-canonical.sqlite3"
        self.store = KrakenSpotSQLiteStore(self.kraken_path, canonical_db_path=self.binance_path)

    def tearDown(self):
        self.temp.cleanup()

    def test_persists_and_reads_back_only_kraken_spot_identity(self):
        self.assertEqual(self.store.insert([candle(START)]), 1)
        result = self.store.read_window("15m", START, START + 2 * STEP)

        self.assertEqual(result["exchange"], "kraken")
        self.assertEqual(result["marketType"], "SPOT")
        self.assertEqual(result["symbol"], "BTC/USDT")
        self.assertEqual(result["coverage"], {
            "expected": 2,
            "returned": 1,
            "complete": False,
            "gaps": [{"startMs": START + STEP, "endMs": START + 2 * STEP}],
        })
        self.assertEqual(result["candles"][0]["nativeMarketId"], "XBTUSDT")
        self.assertEqual(result["candles"][0]["source"], "ccxt.kraken")
        self.assertEqual(result["candles"][0]["availableAtMs"], START + STEP)
        self.assertTrue(result["datasetVersion"].startswith("sha256:"))

    def test_repeat_insert_is_idempotent_and_preserves_first_observed_time(self):
        original = candle(START, available=START + STEP + 10)
        later_observation = candle(START, available=START + STEP + 500)

        self.assertEqual(self.store.insert([original]), 1)
        first = self.store.read_window("15m", START, START + STEP)
        self.assertEqual(self.store.insert([later_observation]), 0)
        second = self.store.read_window("15m", START, START + STEP)

        self.assertEqual(first["datasetVersion"], second["datasetVersion"])
        self.assertEqual(
            second["candles"][0]["availableAtMs"], START + STEP + 10
        )

    def test_conflicting_existing_candle_rolls_back_entire_batch(self):
        self.store.insert([candle(START)])
        conflicting = candle(START, close="103")
        new_row = candle(START + STEP)

        with self.assertRaisesRegex(ValueError, "Conflicting Kraken Spot candle"):
            self.store.insert([new_row, conflicting])

        result = self.store.read_window("15m", START, START + 2 * STEP)
        self.assertEqual([item["openTimeMs"] for item in result["candles"]], [START])

    def test_rejects_a_second_native_market_id_in_the_same_dataset(self):
        self.assertEqual(self.store.insert([candle(START)]), 1)
        alternate_identity = InstrumentIdentity(
            "kraken", "SPOT", "BTCUSDT", "BTC/USDT"
        )

        with self.assertRaisesRegex(ValueError, "native market ID"):
            self.store.insert([candle(START, instrument=alternate_identity)])

        result = self.store.read_window("15m", START, START + STEP)
        self.assertEqual(result["coverage"]["expected"], 1)
        self.assertEqual(result["coverage"]["returned"], 1)
        self.assertTrue(result["coverage"]["complete"])
        self.assertEqual(
            [item["nativeMarketId"] for item in result["candles"]],
            ["XBTUSDT"],
        )

    def test_rejects_non_kraken_or_non_spot_source_candles(self):
        wrong_sources = (
            InstrumentIdentity("binance", "USDT_PERPETUAL", "BTCUSDT", "BTC/USDT"),
            InstrumentIdentity("kraken", "FUTURES", "PI_XBTUSDT", "BTC/USDT"),
            InstrumentIdentity("kraken", "SPOT", "XBTUSD", "BTC/USD"),
        )
        for identity in wrong_sources:
            with self.subTest(identity=identity):
                with self.assertRaises(ValueError):
                    self.store.insert([candle(START, instrument=identity)])

    def test_requires_a_known_binance_path_before_opening_spot_storage(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(ValueError, "path is required"):
                KrakenSpotSQLiteStore(self.kraken_path)

    def test_refuses_to_share_the_binance_canonical_database_path(self):
        with patch.dict(os.environ, {"MARKET_DATA_DB": str(self.binance_path)}):
            with self.assertRaisesRegex(ValueError, "must be separate"):
                KrakenSpotSQLiteStore(self.binance_path)

    def test_kraken_store_does_not_create_or_modify_binance_canonical_tables(self):
        with sqlite3.connect(self.binance_path) as connection:
            connection.execute(
                "CREATE TABLE candles (exchange TEXT, market_type TEXT, symbol TEXT)"
            )
            connection.execute(
                "INSERT INTO candles VALUES ('binance', 'USDT_PERPETUAL', 'BTCUSDT')"
            )

        self.store.insert([candle(START)])

        with sqlite3.connect(self.binance_path) as connection:
            rows = connection.execute("SELECT * FROM candles").fetchall()
            tables = connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        self.assertEqual(rows, [("binance", "USDT_PERPETUAL", "BTCUSDT")])
        self.assertEqual(tables, [("candles",)])

    def test_filters_readback_by_first_observed_as_of_time(self):
        self.store.insert([candle(START, available=START + STEP + 100)])

        before_observed = self.store.read_window(
            "15m", START, START + STEP, as_of_ms=START + STEP + 99
        )
        after_observed = self.store.read_window(
            "15m", START, START + STEP, as_of_ms=START + STEP + 100
        )

        self.assertEqual(before_observed["candles"], [])
        self.assertEqual(after_observed["coverage"]["returned"], 1)

    def test_rejects_unaligned_or_oversized_read_windows(self):
        for timeframe, start, end in (
            ("5m", START, START + STEP),
            ("15m", START + 1, START + STEP),
            ("15m", START, START + 2001 * STEP),
            ("15m", START + STEP, START),
        ):
            with self.subTest(timeframe=timeframe, start=start, end=end):
                with self.assertRaises(ValueError):
                    self.store.read_window(timeframe, start, end)


    def test_read_only_open_rejects_null_or_blank_native_market_ids(self):
        for invalid_id in (None, ""):
            with self.subTest(native_market_id=invalid_id):
                malformed_path = self.root / (
                    "malformed-null.sqlite3" if invalid_id is None
                    else "malformed-blank.sqlite3"
                )
                with sqlite3.connect(malformed_path) as connection:
                    connection.execute(
                        """CREATE TABLE kraken_spot_candles (
                            exchange TEXT, market_type TEXT, native_market_id TEXT,
                            symbol TEXT, timeframe TEXT, open_time_ms INTEGER,
                            open TEXT, high TEXT, low TEXT, close TEXT,
                            volume TEXT, available_at_ms INTEGER
                        )"""
                    )
                    connection.execute(
                        """INSERT INTO kraken_spot_candles VALUES (
                            'kraken', 'SPOT', ?, 'BTC/USDT', '15m', ?,
                            '100', '105', '99', '102', '1.5', ?
                        )""",
                        (invalid_id, START, START + STEP),
                    )

                read_only_store = KrakenSpotSQLiteStore(
                    malformed_path,
                    canonical_db_path=self.binance_path,
                    initialize=False,
                )
                with self.assertRaisesRegex(ValueError, "native market ID"):
                    read_only_store.read_window("15m", START, START + STEP)


    def test_read_only_open_rejects_duplicate_candle_identities_without_unique_constraint(self):
        malformed_path = self.root / "malformed-duplicate-candles.sqlite3"
        with sqlite3.connect(malformed_path) as connection:
            connection.execute(
                """CREATE TABLE kraken_spot_candles (
                    exchange TEXT, market_type TEXT, native_market_id TEXT,
                    symbol TEXT, timeframe TEXT, open_time_ms INTEGER,
                    open TEXT, high TEXT, low TEXT, close TEXT,
                    volume TEXT, available_at_ms INTEGER
                )"""
            )
            row = (
                "kraken", "SPOT", "XBTUSDT", "BTC/USDT", "15m",
                START, "100", "105", "99", "102", "1.5", START + STEP,
            )
            connection.execute(
                "INSERT INTO kraken_spot_candles VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                row,
            )
            connection.execute(
                "INSERT INTO kraken_spot_candles VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                row,
            )

        read_only_store = KrakenSpotSQLiteStore(
            malformed_path,
            canonical_db_path=self.binance_path,
            initialize=False,
        )
        with self.assertRaisesRegex(ValueError, "duplicate candle identity"):
            read_only_store.read_window("15m", START, START + STEP)


if __name__ == "__main__":
    unittest.main()
