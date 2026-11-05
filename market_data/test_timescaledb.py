"""Read-only PostgreSQL/TimescaleDB integration contracts.

The workflow must provide a disposable local TimescaleDB service. Test fixtures
seed rows directly; the production adapter remains read-only.
"""

import json
import os
import time
import unittest
import uuid
from urllib.parse import urlparse
from unittest.mock import patch

from market_data.api import application
from market_data.migrations import migrate
from market_data.postgres import (
    PostgresCandleStore,
    StoreUnavailable,
    connection,
    read_window as read_postgres_window,
)
from market_data.storage import create_store
from market_data.store import INTERVAL_MS

DSN = os.environ.get("MARKET_DATA_TEST_DATABASE_URL", "")
REQUIRED = os.environ.get("MARKET_DATA_REQUIRE_TIMESCALE") == "1"
DISPOSABLE = os.environ.get("MARKET_DATA_TEST_DISPOSABLE") == "1"


def _assert_disposable_test_target():
    """Fail closed unless the DSN is the dedicated local CI test database."""
    if not DISPOSABLE:
        raise RuntimeError("MARKET_DATA_TEST_DISPOSABLE=1 is required")
    parsed = urlparse(DSN)
    if (
        parsed.scheme not in {"postgres", "postgresql"}
        or parsed.hostname not in {"127.0.0.1", "localhost"}
        or parsed.port != 5432
        or parsed.username != "t0_test"
        or parsed.path != "/t0_test"
    ):
        raise RuntimeError("TimescaleDB tests require the dedicated local t0_test database")
    forbidden = (
        "MARKET_DATA_DB",
        "MARKET_DATA_POSTGRES_DSN",
        "T0_FEEDER_LEASE_DB",
        "PAPER_DB",
        "BINANCE_API_KEY",
        "BINANCE_API_SECRET",
        "OKX_API_KEY",
        "OKX_API_SECRET",
    )
    if any(os.environ.get(name) for name in forbidden):
        raise RuntimeError("Canonical storage, execution, or exchange configuration is forbidden")


@unittest.skipUnless(DSN or REQUIRED, "Set the isolated TimescaleDB test service to run integration tests")
class TimescaleReadOnlyIntegrationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not DSN:
            raise RuntimeError("MARKET_DATA_TEST_DATABASE_URL is required")
        _assert_disposable_test_target()
        try:
            import psycopg  # noqa: F401
        except ImportError:
            raise RuntimeError("psycopg is required for TimescaleDB integration tests") from None

        migrate(DSN)
        with connection(DSN, read_only=True) as database:
            extension = database.execute(
                "SELECT extversion FROM pg_extension WHERE extname='timescaledb'"
            ).fetchone()
            if extension is None:
                raise RuntimeError("The disposable test database lacks TimescaleDB")
            cls.extension_version = extension[0]

        applied, total = migrate(DSN)
        if applied != total:
            raise RuntimeError("TimescaleDB migrations did not reach the expected version")

    def setUp(self):
        self.step = INTERVAL_MS["15m"]
        self.start = (
            (time.time_ns() // 1_000_000 // self.step) + (uuid.uuid4().int % 1_000_000)
        ) * self.step

    def tearDown(self):
        with connection(DSN) as database:
            database.execute(
                """DELETE FROM market_data.candles
                   WHERE open_time_ms >= %s AND open_time_ms < %s""",
                (self.start, self.start + 4 * self.step),
            )

    def candle(self, slot=0, **changes):
        values = {
            "timeframe": "15m",
            "open_time_ms": self.start + slot * self.step,
            "open": "100.12345678901234567890123456789",
            "high": "102",
            "low": "99",
            "close": "101",
            "volume": "5.0000",
            "available_at_ms": self.start + (slot + 1) * self.step + 100,
        }
        return values | changes

    def seed(self, *candles):
        with connection(DSN) as database:
            for candle in candles:
                database.execute(
                    """INSERT INTO market_data.candles
                       (exchange, market_type, symbol, timeframe, open_time_ms,
                        open, high, low, close, volume, available_at_ms)
                       VALUES ('binance', 'USDT_PERPETUAL', 'BTCUSDT', %s, %s,
                               %s, %s, %s, %s, %s, %s)""",
                    (
                        candle["timeframe"], candle["open_time_ms"], candle["open"],
                        candle["high"], candle["low"], candle["close"],
                        candle["volume"], candle["available_at_ms"],
                    ),
                )

    def test_read_window_preserves_decimal_values_gaps_and_asof(self):
        self.seed(self.candle(), self.candle(2))
        args = ("BTCUSDT", "15m", self.start, self.start + 3 * self.step)
        result = read_postgres_window(DSN, *args)

        self.assertEqual(result["candles"][0]["open"], "100.12345678901234567890123456789")
        self.assertEqual(result["coverage"]["expected"], 3)
        self.assertEqual(result["coverage"]["returned"], 2)
        self.assertFalse(result["coverage"]["complete"])
        self.assertEqual(result["coverage"]["gaps"], [
            {"startMs": self.start + self.step, "endMs": self.start + 2 * self.step}
        ])
        self.assertTrue(result["datasetVersion"].startswith("sha256:"))

        cutoff = self.start + self.step + 200
        asof = read_postgres_window(DSN, *args, as_of_ms=cutoff)
        self.assertEqual(len(asof["candles"]), 1)
        self.assertEqual(asof["candles"][0]["openTimeMs"], self.start)

    def test_adapter_is_read_only_and_does_not_mutate_schema_on_construction(self):
        with connection(DSN, read_only=True) as database:
            before = database.execute(
                "SELECT count(*) FROM information_schema.tables WHERE table_schema='market_data'"
            ).fetchone()[0]
        adapter = PostgresCandleStore(DSN)
        facade = create_store("postgres", postgres_dsn=DSN)
        self.assertIsInstance(adapter, PostgresCandleStore)
        self.assertFalse(hasattr(adapter, "insert"))
        self.assertFalse(hasattr(adapter, "write_batch"))
        self.assertTrue(callable(facade.read_window))
        with connection(DSN, read_only=True) as database:
            after = database.execute(
                "SELECT count(*) FROM information_schema.tables WHERE table_schema='market_data'"
            ).fetchone()[0]
        self.assertEqual(before, after)

    def test_read_only_connection_rejects_mutation(self):
        self.seed(self.candle())
        with self.assertRaises(StoreUnavailable):
            with connection(DSN, read_only=True) as database:
                database.execute(
                    """UPDATE market_data.candles SET close=%s
                       WHERE symbol='BTCUSDT' AND timeframe='15m' AND open_time_ms=%s""",
                    ("100.5", self.start),
                )
        result = read_postgres_window(
            DSN, "BTCUSDT", "15m", self.start, self.start + self.step
        )
        self.assertEqual(result["candles"][0]["close"], "101")

    def test_hypertable_and_migration_checksum_are_consistent(self):
        with connection(DSN, read_only=True) as database:
            row = database.execute(
                """SELECT hypertable_name FROM timescaledb_information.hypertables
                   WHERE hypertable_schema='market_data' AND hypertable_name='candles'"""
            ).fetchone()
            migrations = database.execute(
                "SELECT migration_id, checksum_sha256 FROM market_data.schema_migrations"
            ).fetchall()
        self.assertEqual(row[0], "candles")
        self.assertTrue(migrations)
        applied, total = migrate(DSN)
        self.assertEqual(applied, total)

    def test_migration_rejects_changed_checksum_and_recovers(self):
        migration_id = "001_initial_timescale.sql"
        with connection(DSN, read_only=True) as database:
            row = database.execute(
                "SELECT checksum_sha256 FROM market_data.schema_migrations WHERE migration_id=%s",
                (migration_id,),
            ).fetchone()
        self.assertIsNotNone(row)
        original_checksum = row[0]

        with connection(DSN) as database:
            database.execute(
                "UPDATE market_data.schema_migrations SET checksum_sha256=%s WHERE migration_id=%s",
                ("0" * 64, migration_id),
            )
        try:
            with self.assertRaisesRegex(RuntimeError, "Applied migration checksum mismatch"):
                migrate(DSN)
        finally:
            with connection(DSN) as database:
                database.execute(
                    "UPDATE market_data.schema_migrations SET checksum_sha256=%s WHERE migration_id=%s",
                    (original_checksum, migration_id),
                )
        applied, total = migrate(DSN)
        self.assertEqual(applied, total)

    def test_api_reads_postgres_and_maps_connection_failure_to_503(self):
        self.seed(self.candle())
        query = (
            f"symbol=BTCUSDT&timeframe=15m&startMs={self.start}"
            f"&endMs={self.start + self.step}"
        )
        environ = {
            "REQUEST_METHOD": "GET",
            "PATH_INFO": "/v1/candles",
            "QUERY_STRING": query,
            "HTTP_AUTHORIZATION": "Bearer test-token",
        }
        status = []
        with patch.dict(os.environ, {
            "MARKET_DATA_BACKEND": "postgres",
            "MARKET_DATA_POSTGRES_DSN": DSN,
            "MARKET_DATA_TOKEN": "test-token",
        }, clear=True):
            body = b"".join(application(environ, lambda value, headers: status.append(value)))
        self.assertEqual(status[0].split()[0], "200")
        payload = json.loads(body)
        self.assertEqual(payload["candles"][0]["openTimeMs"], self.start)
        self.assertEqual(payload["candles"][0]["open"], "100.12345678901234567890123456789")

        status.clear()
        with patch.dict(os.environ, {
            "MARKET_DATA_BACKEND": "postgres",
            "MARKET_DATA_POSTGRES_DSN": "postgresql://invalid:invalid@127.0.0.1:1/invalid?connect_timeout=1",
            "MARKET_DATA_TOKEN": "test-token",
        }, clear=True):
            body = b"".join(application(environ, lambda value, headers: status.append(value)))
        self.assertEqual(status[0].split()[0], "503")
        self.assertEqual(json.loads(body), {"error": "STORE_UNAVAILABLE"})


if __name__ == "__main__":
    unittest.main()
