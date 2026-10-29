"""Real PostgreSQL parity tests; require an explicitly selected test database."""

from concurrent.futures import ThreadPoolExecutor
import os
from pathlib import Path
import tempfile
import unittest
import uuid
from urllib.parse import quote, unquote, urlencode, urlsplit, urlunsplit

from futures_intelligence.import_collector import build_snapshot
from market_data.archive import archive_snapshot, init_archive, read_snapshots
from market_data.postgres import PostgresCandleStore, connection
from market_data.store import Candle, CandleStore, INTERVAL_MS, StoreUnavailable, open_store, read_window


DSN = os.environ.get("DATA_LAKE_TEST_POSTGRES", "")
REQUIRED = os.environ.get("DATA_LAKE_REQUIRE_POSTGRES") == "1"


def schema_url(location, schema):
    parts = urlsplit(location)
    if parts.scheme not in {"postgres", "postgresql"}:
        raise ValueError("PostgreSQL tests require a database URI")
    params = []
    for pair in filter(None, parts.query.split("&")):
        key, separator, value = pair.partition("=")
        if not separator:
            raise ValueError("PostgreSQL URI requires key=value parameters")
        if unquote(key) != "options":
            params.append((unquote(key), unquote(value)))
    params.append(("options", "-c search_path=" + schema))
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(params, quote_via=quote), parts.fragment))


class PostgresUriEncodingTest(unittest.TestCase):
    def test_schema_options_preserve_spaces_under_postgres_uri_decoding(self):
        uri = schema_url("postgresql://127.0.0.1/test?application_name=ci+worker&options=old", "test_schema")
        # libpq URI decoding is percent-only; parse_qs would conceal this bug by
        # applying HTML form decoding and incorrectly treating '+' as a space.
        options = dict(pair.split("=", 1) for pair in urlsplit(uri).query.split("&"))
        self.assertEqual(unquote(options["options"]), "-c search_path=test_schema")
        self.assertEqual(unquote(options["application_name"]), "ci+worker")


@unittest.skipUnless(DSN or REQUIRED, "Real PostgreSQL not configured: set DATA_LAKE_TEST_POSTGRES")
class PostgresStorageTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not DSN:
            raise RuntimeError("PostgreSQL tests are required but no test database is configured")
        # A configured PostgreSQL job must fail, rather than skip, if the driver is missing.
        try:
            from psycopg import sql
            from psycopg.conninfo import make_conninfo
        except ImportError:
            raise RuntimeError("PostgreSQL tests require the psycopg driver") from None
        cls.sql, cls.make_conninfo = sql, staticmethod(make_conninfo)

    def setUp(self):
        self.schema = "test_market_data_" + uuid.uuid4().hex
        with connection(DSN) as database:
            database.execute(self.sql.SQL("CREATE SCHEMA {}").format(self.sql.Identifier(self.schema)))
        self.addCleanup(self.drop_schema)
        self.location = self.make_conninfo(DSN, options="-c search_path=" + self.schema)
        # Public dispatch intentionally uses URL prefixes. Keep the schema-scoped
        # conninfo string for the actual driver and dispatch against a URL below.
        self.store = PostgresCandleStore(self.location)
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.sqlite = Path(self.temp.name) / "data.sqlite3"
        CandleStore(self.sqlite)
        self.step = INTERVAL_MS["15m"]

    def drop_schema(self):
        with connection(DSN) as database:
            database.execute(self.sql.SQL("DROP SCHEMA {} CASCADE").format(self.sql.Identifier(self.schema)))

    def candle(self, slot=0, **changes):
        values = dict(timeframe="15m", open_time_ms=slot * self.step, open="100.12345678901234567890123456789",
                      high="102", low="99", close="101", volume="5.0000",
                      available_at_ms=(slot + 1) * self.step + 100)
        return Candle(**(values | changes))

    def postgres_window(self, count=3, as_of_ms=None):
        from market_data.postgres import read_window as read_postgres_window
        return read_postgres_window(self.location, "BTCUSDT", "15m", 0, count * self.step, as_of_ms)

    def postgres_url(self):
        return schema_url(DSN, self.schema)

    def test_exact_numeric_hash_gaps_and_asof_match_sqlite(self):
        candles = [self.candle(), self.candle(2)]
        self.assertEqual(self.store.insert(candles), 2)
        CandleStore(self.sqlite).insert(candles)
        self.assertEqual(self.postgres_window(), read_window(self.sqlite, "BTCUSDT", "15m", 0, 3 * self.step))
        self.assertEqual(self.postgres_window(as_of_ms=2 * self.step),
                         read_window(self.sqlite, "BTCUSDT", "15m", 0, 3 * self.step, 2 * self.step))

    def test_atomic_batch_conflicts_do_not_rewrite_first_observation(self):
        self.store.insert([self.candle()])
        before = self.postgres_window()
        self.assertEqual(self.store.insert([self.candle(available_at_ms=self.step + 999)]), 0)
        self.assertEqual(before, self.postgres_window())
        with self.assertRaises(ValueError):
            self.store.insert([self.candle(1), self.candle(close="100.5")])
        self.assertEqual(before, self.postgres_window())

    def test_concurrent_identical_inserts_only_commit_once(self):
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: self.store.insert([self.candle()]), range(2)))
        self.assertCountEqual(results, [0, 1])
        self.assertEqual(len(self.postgres_window()["candles"]), 1)

    def test_concurrent_conflicting_inserts_reject_one_writer(self):
        def insert(candle):
            try:
                return self.store.insert([candle])
            except ValueError:
                return "CONFLICT"
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(insert, [self.candle(), self.candle(close="100.5")]))
        self.assertCountEqual(results, [1, "CONFLICT"])
        self.assertEqual(len(self.postgres_window()["candles"]), 1)

    def test_readonly_transaction_rejects_writes_and_missing_schema_stays_missing(self):
        with self.assertRaises(StoreUnavailable):
            with connection(self.location, read_only=True) as database:
                database.execute("CREATE TABLE should_not_exist (id INTEGER)")
        with connection(self.location, read_only=True) as database:
            self.assertEqual(database.execute("SELECT current_setting('transaction_read_only')").fetchone()[0], "on")
            self.assertEqual(database.execute("SELECT current_setting('transaction_isolation')").fetchone()[0], "repeatable read")
            self.assertEqual(database.execute("SELECT current_setting('statement_timeout')").fetchone()[0], "5s")
            self.assertEqual(database.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema=%s AND table_name='should_not_exist'", (self.schema,)).fetchone()[0], 0)
        with connection(self.location) as database:
            database.execute("DROP TABLE candles")
        with self.assertRaises(StoreUnavailable):
            self.postgres_window()
        with connection(self.location, read_only=True) as database:
            self.assertEqual(database.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema=%s", (self.schema,)).fetchone()[0], 0)

    def test_archived_intelligence_parity_idempotency_and_concurrency(self):
        # Archive dispatch requires a URL; adding a query option keeps the isolated
        # schema while exercising the public PostgreSQL URL routes unchanged.
        url = self.postgres_url()
        self.assertIsInstance(open_store(url), PostgresCandleStore)
        init_archive(url)
        init_archive(self.sqlite)
        samples = [build_snapshot(0, 1000, 1200), build_snapshot(0, 1000, 1400)]
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: archive_snapshot(url, samples[0], 1500), range(2)))
        self.assertCountEqual(results, [True, False])
        archive_snapshot(url, samples[1], 1500)
        for snapshot in samples:
            archive_snapshot(self.sqlite, snapshot, 1500)
        self.assertEqual(read_snapshots(url, 0, 1500, 1300), read_snapshots(self.sqlite, 0, 1500, 1300))
        self.assertEqual(read_snapshots(url, 0, 1500, 1500), read_snapshots(self.sqlite, 0, 1500, 1500))
        self.store.insert([self.candle()])
        self.assertEqual(read_window(url, "BTCUSDT", "15m", 0, 3 * self.step), self.postgres_window())

    def test_central_producer_lock_blocks_concurrent_fetch_and_releases(self):
        from data_lake.refresh import producer_lock, refresh_once

        class NoFetchExchange:
            id = "binanceusdm"

            def __init__(self):
                self.calls = []

            def load_markets(self):
                self.calls.append("load_markets")
                raise AssertionError("A blocked collector must not contact the exchange")

            def fetch_time(self):
                self.calls.append("fetch_time")
                raise AssertionError("A blocked collector must not contact the exchange")

            def fetch_ohlcv(self, *args, **kwargs):
                self.calls.append("fetch_ohlcv")
                raise AssertionError("A blocked collector must not contact the exchange")

        url, exchange = self.postgres_url(), NoFetchExchange()
        with producer_lock(url):
            with ThreadPoolExecutor(max_workers=1) as pool:
                attempt = pool.submit(refresh_once, exchange, url, ("15m",), 1)
                with self.assertRaisesRegex(ValueError, "Another central collector is running"):
                    attempt.result(timeout=15)
            self.assertEqual(exchange.calls, [])
        # A new connection can own the transaction lock after the first commits.
        with producer_lock(url):
            self.assertEqual(exchange.calls, [])


if __name__ == "__main__":
    unittest.main()
