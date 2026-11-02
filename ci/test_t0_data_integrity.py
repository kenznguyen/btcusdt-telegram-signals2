"""T0 data-integrity and candle-continuity gate tests (read-only audit)."""
import hashlib
import sqlite3
import tempfile
import unittest
from pathlib import Path

from ci.t0_data_integrity import audit_database


CREATE_TABLE = """
CREATE TABLE candles (
    exchange TEXT, market_type TEXT, symbol TEXT, timeframe TEXT,
    open_time_ms INTEGER, open TEXT, high TEXT, low TEXT, close TEXT,
    volume TEXT, available_at_ms INTEGER,
    PRIMARY KEY (exchange, market_type, symbol, timeframe, open_time_ms)
)
"""

CREATE_TABLE_WITHOUT_IDENTITY_KEY = """
CREATE TABLE candles (
    exchange TEXT, market_type TEXT, symbol TEXT, timeframe TEXT,
    open_time_ms INTEGER, open TEXT, high TEXT, low TEXT, close TEXT,
    volume TEXT, available_at_ms INTEGER
)
"""


class T0DataIntegrityGateTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "canonical.sqlite3"
        with sqlite3.connect(self.path) as connection:
            connection.execute(CREATE_TABLE)

    def insert(self, timeframe, opened, *, available=None, open_="100", high="102",
               low="99", close="101", volume="5", symbol="BTCUSDT",
               exchange="binance", market_type="USDT_PERPETUAL"):
        interval = {"15m": 900_000, "1h": 3_600_000}[timeframe]
        with sqlite3.connect(self.path) as connection:
            connection.execute(
                "INSERT INTO candles VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (exchange, market_type, symbol, timeframe, opened, open_, high,
                 low, close, volume, opened + interval if available is None else available),
            )

    def audit(self):
        return audit_database(self.path)

    def test_valid_closed_m15_and_h1_rows_pass(self):
        self.insert("15m", 0)
        self.insert("15m", 900_000)
        self.insert("1h", 0)
        report = self.audit()
        self.assertEqual(report["result"], "PASS", report["issues"])
        self.assertEqual(report["timeframes"]["15m"]["rows"], 2)
        self.assertEqual(report["timeframes"]["1h"]["rows"], 1)

    def test_duplicate_composite_candle_identity_is_reported(self):
        with sqlite3.connect(self.path) as connection:
            connection.execute("DROP TABLE candles")
            connection.execute(CREATE_TABLE_WITHOUT_IDENTITY_KEY)
        self.insert("15m", 0)
        self.insert("15m", 0)
        report = self.audit()
        codes = {issue["code"] for issue in report["issues"]}
        self.assertIn("duplicate_candle_identity", codes)
        self.assertIn("identity_constraint_missing", codes)

    def test_schema_enforces_unique_composite_candle_identity(self):
        self.insert("15m", 0)
        report = self.audit()
        self.assertNotIn("identity_constraint_missing", {issue["code"] for issue in report["issues"]})

    def test_unaligned_and_non_monotonic_timestamps_are_reported(self):
        self.insert("15m", 900_000)
        self.insert("15m", 0)
        self.insert("15m", 900_001)
        report = self.audit()
        codes = {issue["code"] for issue in report["issues"]}
        self.assertIn("timestamp_not_aligned", codes)
        self.assertIn("candle_order_not_strict", codes)

    def test_invalid_ohlcv_bounds_and_negative_volume_are_reported(self):
        self.insert("15m", 0, open_="103", high="102")
        self.insert("15m", 900_000, volume="-1")
        report = self.audit()
        codes = {issue["code"] for issue in report["issues"]}
        self.assertIn("invalid_ohlcv", codes)

    def test_candle_observed_before_close_is_rejected(self):
        self.insert("15m", 0, available=899_999)
        report = self.audit()
        self.assertIn("candle_not_closed", {issue["code"] for issue in report["issues"]})

    def test_missing_slots_are_counted_separately_for_m15_and_h1(self):
        self.insert("15m", 0)
        self.insert("15m", 1_800_000)
        self.insert("1h", 0)
        self.insert("1h", 7_200_000)
        report = self.audit()
        self.assertEqual(report["timeframes"]["15m"]["missing_candles"], 1)
        self.assertEqual(report["timeframes"]["1h"]["missing_candles"], 1)
        self.assertIn("candle_gap", {issue["code"] for issue in report["issues"]})

    def test_noncanonical_market_identity_is_reported(self):
        self.insert("15m", 0, symbol="ETHUSDT")
        report = self.audit()
        self.assertIn("noncanonical_market_identity", {issue["code"] for issue in report["issues"]})

    def test_audit_does_not_modify_database_bytes(self):
        self.insert("15m", 0)
        before = hashlib.sha256(self.path.read_bytes()).hexdigest()
        self.audit()
        after = hashlib.sha256(self.path.read_bytes()).hexdigest()
        self.assertEqual(after, before)


if __name__ == "__main__":
    unittest.main()
