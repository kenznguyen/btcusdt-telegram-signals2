"""G4 read-only runtime acceptance probe contracts; uses disposable SQLite fixtures only."""
import hashlib
import pathlib
import sqlite3
import tempfile
import unittest

from ci.t0_runtime_acceptance import inspect_sqlite_read_only
from app import app as feeder_health_app
from market_data.api import application as candle_api_application
from wsgiref.util import setup_testing_defaults

NOW = 1_800_000_000_000
LEASE_NAME = "binance-btcusdt-canonical"


def create_fixture(path, *, include_lease=True, lease_expiry=NOW + 60_000):
    connection = sqlite3.connect(path)
    connection.execute("""CREATE TABLE candles (
        exchange TEXT NOT NULL, market_type TEXT NOT NULL, symbol TEXT NOT NULL,
        timeframe TEXT NOT NULL, open_time_ms INTEGER NOT NULL,
        open TEXT NOT NULL, high TEXT NOT NULL, low TEXT NOT NULL,
        close TEXT NOT NULL, volume TEXT NOT NULL, available_at_ms INTEGER NOT NULL,
        PRIMARY KEY (exchange, market_type, symbol, timeframe, open_time_ms)
    )""")
    if include_lease:
        connection.execute("""CREATE TABLE feeder_leases (
            lease_name TEXT PRIMARY KEY, owner TEXT, generation INTEGER NOT NULL,
            expires_at_ms INTEGER NOT NULL
        )""")
        connection.execute(
            "INSERT INTO feeder_leases VALUES (?, ?, ?, ?)",
            (LEASE_NAME, "fixture-owner-secret", 7, lease_expiry),
        )
    for timeframe, interval in (("15m", 900_000), ("1h", 3_600_000)):
        open_time = (NOW // interval) * interval - interval
        connection.execute(
            "INSERT INTO candles VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            ("binance", "USDT_PERPETUAL", "BTCUSDT", timeframe, open_time,
             "100", "101", "99", "100", "1", open_time + interval + 100),
        )
    connection.commit()
    connection.close()


class ReadOnlySQLiteAcceptanceTests(unittest.TestCase):
    def test_reads_integrity_lease_and_both_timeframe_watermarks(self):
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / "canonical.sqlite3"
            create_fixture(path)
            result = inspect_sqlite_read_only(str(path), now_ms=NOW + 5_000)

        self.assertEqual(result["integrity"], "ok")
        self.assertTrue(result["lease"]["valid"])
        self.assertEqual(result["lease"]["generation"], 7)
        self.assertNotIn("fixture-owner-secret", str(result))
        self.assertEqual(set(result["timeframes"]), {"15m", "1h"})
        self.assertIsNotNone(result["timeframes"]["15m"]["latest_open_time_ms"])
        self.assertIsNotNone(result["timeframes"]["1h"]["latest_open_time_ms"])

    def test_owner_identity_is_fingerprinted_not_disclosed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / "canonical.sqlite3"
            create_fixture(path)
            result = inspect_sqlite_read_only(str(path), now_ms=NOW)
        expected = hashlib.sha256(b"fixture-owner-secret").hexdigest()[:16]
        self.assertEqual(result["lease"]["owner_fingerprint"], expected)
        self.assertNotIn("owner", result["lease"])

    def test_expired_lease_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / "canonical.sqlite3"
            create_fixture(path, lease_expiry=NOW - 1)
            result = inspect_sqlite_read_only(str(path), now_ms=NOW)
        self.assertFalse(result["lease"]["valid"])
        self.assertEqual(result["lease"]["state"], "EXPIRED")

    def test_missing_lease_table_fails_closed_without_schema_creation(self):
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / "canonical.sqlite3"
            create_fixture(path, include_lease=False)
            with self.assertRaisesRegex(RuntimeError, "feeder_leases"):
                inspect_sqlite_read_only(str(path), now_ms=NOW)
            connection = sqlite3.connect(path)
            tables = {row[0] for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )}
            connection.close()
        self.assertNotIn("feeder_leases", tables)

    def test_missing_database_is_not_created(self):
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / "missing.sqlite3"
            with self.assertRaises(FileNotFoundError):
                inspect_sqlite_read_only(str(path), now_ms=NOW)
            self.assertFalse(path.exists())

    def test_snapshot_does_not_change_database_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / "canonical.sqlite3"
            create_fixture(path)
            before = hashlib.sha256(path.read_bytes()).hexdigest()
            inspect_sqlite_read_only(str(path), now_ms=NOW)
            after = hashlib.sha256(path.read_bytes()).hexdigest()
        self.assertEqual(after, before)



    def test_detailed_feeder_health_and_candle_api_are_separate_applications(self):
        self.assertIn("/health/data", {
            rule.rule for rule in feeder_health_app.url_map.iter_rules()
        })
        environ = {}
        setup_testing_defaults(environ)
        environ.update({"REQUEST_METHOD": "GET", "PATH_INFO": "/health/data"})
        response = {}

        def start_response(status, headers):
            response["status"] = status

        body = b"".join(candle_api_application(environ, start_response))
        self.assertTrue(response["status"].startswith("404"))
        self.assertIn(b"NOT_FOUND", body)

        environ["PATH_INFO"] = "/health"
        body = b"".join(candle_api_application(environ, start_response))
        self.assertTrue(response["status"].startswith("200"))
        self.assertIn(b"canonical-market-data", body)
        self.assertNotIn(b"timeframes", body)

    def test_watermarks_report_close_lag_without_claiming_health(self):
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / "canonical.sqlite3"
            create_fixture(path)
            result = inspect_sqlite_read_only(str(path), now_ms=NOW + 5_000)
        for timeframe, interval in (("15m", 900_000), ("1h", 3_600_000)):
            item = result["timeframes"][timeframe]
            self.assertEqual(
                item["close_lag_ms"],
                NOW + 5_000 - item["latest_close_time_ms"],
            )
            self.assertEqual(item["latest_close_time_ms"],
                           item["latest_open_time_ms"] + interval)

if __name__ == "__main__":
    unittest.main()
