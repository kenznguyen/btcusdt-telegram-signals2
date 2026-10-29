import contextlib
import io
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import unittest
import uuid
from unittest.mock import patch

from data_lake.readiness import check_readiness, main
from market_data.archive import init_archive
from market_data.store import Candle, CandleStore, INTERVAL_MS, open_store


class ReadinessTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.database = Path(self.temp.name) / "lake.sqlite3"
        self.now = 1_800_000_000_000

    def initialize(self):
        CandleStore(self.database)
        init_archive(self.database)

    def insert_recent(self, available=None):
        candles = []
        for timeframe, step in INTERVAL_MS.items():
            end = self.now // step * step
            for opened in (end - 2 * step, end - step):
                candles.append(Candle(timeframe, opened, "100", "101", "99", "100.5", "2",
                                      opened + step if available is None else available))
        CandleStore(self.database).insert(candles)

    def test_empty_initialized_store_is_ready_without_fabricating_fresh_data(self):
        self.initialize()
        before = self.database.read_bytes()
        result = check_readiness(self.database, self.now)
        self.assertTrue(result["ready"])
        self.assertFalse(result["freshData"])
        self.assertTrue(result["checks"]["archive"]["ready"])
        self.assertEqual(before, self.database.read_bytes())
        for frame in result["timeframes"].values():
            self.assertEqual(0, frame["returned"])
            self.assertFalse(frame["complete"])
            self.assertIsNone(frame["latestCloseTimeMs"])

    def test_missing_store_and_schema_fail_without_creating_or_disclosing_paths(self):
        result = check_readiness(self.database, self.now)
        self.assertFalse(result["ready"])
        self.assertIsNone(result["timeframes"]["15m"]["returned"])
        self.assertFalse(self.database.exists())
        self.assertNotIn(str(self.database), json.dumps(result))
        CandleStore(self.database)
        result = check_readiness(self.database, self.now)
        self.assertFalse(result["ready"])
        self.assertTrue(result["checks"]["candles"]["ready"])
        self.assertFalse(result["checks"]["archive"]["ready"])
        with sqlite3.connect(self.database) as connection:
            tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        self.assertEqual({"candles"}, tables)

    def test_current_known_bars_are_fresh_and_future_observations_remain_missing(self):
        self.initialize()
        self.insert_recent()
        result = check_readiness(self.database, self.now)
        self.assertTrue(result["ready"])
        self.assertTrue(result["freshData"])
        self.assertEqual(self.now, result["timeframes"]["15m"]["latestCloseTimeMs"])
        with sqlite3.connect(self.database) as connection:
            connection.execute("UPDATE candles SET available_at_ms=?", (self.now + 1,))
        result = check_readiness(self.database, self.now)
        self.assertTrue(result["ready"])
        self.assertFalse(result["freshData"])
        self.assertEqual(0, result["timeframes"]["15m"]["returned"])

    def test_corrupt_selected_rows_and_database_errors_are_not_ready_or_secret_leaks(self):
        self.initialize()
        self.insert_recent()
        with sqlite3.connect(self.database) as connection:
            connection.execute("UPDATE candles SET high='0'")
        result = check_readiness(self.database, self.now)
        self.assertFalse(result["ready"])
        self.assertFalse(result["freshData"])
        secret = "postgresql://reader:secret-password@db/lake"
        with patch("data_lake.readiness.read_window", side_effect=OSError(secret)), \
                patch("data_lake.readiness.read_snapshots", side_effect=OSError(secret)):
            failed = check_readiness(secret, self.now)
        self.assertFalse(failed["ready"])
        self.assertNotIn("secret-password", json.dumps(failed))

    def test_cli_readiness_and_optional_freshness_have_distinct_exit_statuses(self):
        self.initialize()
        with patch.dict(os.environ, {"DATA_LAKE_DATABASE_URL": str(self.database)}, clear=True), \
                contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(0, main([]))
            self.assertEqual(1, main(["--require-fresh"]))
        reports = [json.loads(line) for line in output.getvalue().splitlines()]
        self.assertEqual(2, len(reports))
        self.assertTrue(all(report["ready"] and not report["freshData"] for report in reports))
        self.assertNotIn(str(self.database), output.getvalue())
        self.assertFalse(check_readiness(None, self.now)["ready"])
        with self.assertRaises(ValueError):
            check_readiness(self.database, True)


@unittest.skipUnless(os.environ.get("DATA_LAKE_TEST_POSTGRES") or os.environ.get("DATA_LAKE_REQUIRE_POSTGRES") == "1",
                     "Real PostgreSQL not configured for readiness integration")
class PostgresReadinessTest(unittest.TestCase):
    def test_real_postgres_readiness_does_not_initialize_and_checks_both_frames(self):
        from psycopg import sql
        from market_data.postgres import connection
        from market_data.test_postgres import schema_url

        location = os.environ.get("DATA_LAKE_TEST_POSTGRES")
        if not location:
            raise RuntimeError("PostgreSQL readiness test is required but database is unconfigured")
        schema = "test_readiness_" + uuid.uuid4().hex
        with connection(location) as database:
            database.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))

        def cleanup():
            with connection(location) as database:
                database.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))

        self.addCleanup(cleanup)
        scoped = schema_url(location, schema)
        now = 1_800_000_000_000
        self.assertFalse(check_readiness(scoped, now)["ready"])
        with connection(scoped, read_only=True) as database:
            self.assertEqual(0, database.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema=%s", (schema,)).fetchone()[0])
        store = open_store(scoped)
        init_archive(scoped)
        empty = check_readiness(scoped, now)
        self.assertTrue(empty["ready"])
        self.assertFalse(empty["freshData"])
        for timeframe, step in INTERVAL_MS.items():
            end = now // step * step
            store.insert([Candle(timeframe, opened, "100", "101", "99", "100.5", "2", opened + step)
                          for opened in (end - 2 * step, end - step)])
        self.assertTrue(check_readiness(scoped, now)["freshData"])


if __name__ == "__main__":
    unittest.main()
