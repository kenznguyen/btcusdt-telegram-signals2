"""Integration contracts for the PostgreSQL lease-fenced canonical writer.

These contracts verify the PostgreSQL lease-fenced writer against a disposable
local TimescaleDB service configured by the dedicated GitHub Actions job.
"""

import os
import time
import unittest
import uuid
from urllib.parse import urlparse

from market_data.store import Candle, INTERVAL_MS

DSN = os.environ.get("MARKET_DATA_TEST_DATABASE_URL", "")


def _assert_disposable_target():
    if os.environ.get("MARKET_DATA_TEST_DISPOSABLE") != "1":
        raise RuntimeError("MARKET_DATA_TEST_DISPOSABLE=1 is required")
    parsed = urlparse(DSN)
    if (
        parsed.scheme not in {"postgres", "postgresql"}
        or parsed.hostname not in {"127.0.0.1", "localhost"}
        or parsed.port != 5432
        or parsed.username != "t0_test"
        or parsed.path != "/t0_test"
    ):
        raise RuntimeError("PostgreSQL writer tests require the isolated local t0_test database")
    forbidden = (
        "MARKET_DATA_DB", "MARKET_DATA_POSTGRES_DSN", "T0_FEEDER_LEASE_DB",
        "PAPER_DB", "BINANCE_API_KEY", "BINANCE_API_SECRET",
        "OKX_API_KEY", "OKX_API_SECRET",
    )
    if any(os.environ.get(name) for name in forbidden):
        raise RuntimeError("Canonical, Paper, or exchange configuration is forbidden")


@unittest.skipUnless(DSN, "Set the disposable local TimescaleDB test service")
class PostgresWriteGatewayIntegrationTest(unittest.TestCase):
    """Required PostgreSQL writer and lease lifecycle behavior."""

    @classmethod
    def setUpClass(cls):
        _assert_disposable_target()
        from market_data.migrations import migrate

        migrate(DSN)
        try:
            import psycopg  # noqa: F401
        except ImportError:
            raise RuntimeError("psycopg is required for PostgreSQL writer contract tests") from None

    def setUp(self):
        from market_data.postgres import PostgresLeaseStore

        self.lease_name = "binance-btcusdt-canonical"
        self.leases = PostgresLeaseStore(DSN, lease_name=self.lease_name)
        self.owner = "writer-a"
        self.lease = self.leases.acquire(self.owner, ttl_seconds=30)
        self.assertIsNotNone(self.lease)
        self.step = INTERVAL_MS["15m"]
        self.open_time = (int(time.time() * 1000) // self.step) * self.step - 2 * self.step

    def tearDown(self):
        from market_data.postgres import connection

        with connection(DSN) as database:
            database.execute(
                "DELETE FROM market_data.candles WHERE open_time_ms >= %s AND open_time_ms < %s",
                (self.open_time, self.open_time + 4 * self.step),
            )
            database.execute(
                "DELETE FROM market_data.feeder_leases WHERE lease_name=%s",
                (self.lease_name,),
            )

    def candle(self, *, close="101", open_time=None):
        start = self.open_time if open_time is None else open_time
        return Candle(
            "15m", start, "100.12345678901234567890123456789",
            "102", "99", close, "5.00000000000000000001",
            start + self.step + 1,
        )

    def gateway(self, owner=None, generation=None):
        from market_data.postgres import PostgresWriteGateway

        return PostgresWriteGateway(
            DSN,
            lease_name=self.lease_name,
            owner_id=owner or self.owner,
            generation_provider=lambda: self.lease.generation if generation is None else generation,
        )

    def test_current_owner_and_generation_commit_complete_batch(self):
        gateway = self.gateway()
        self.assertEqual(gateway.write_batch([self.candle()]), 1)
        from market_data.postgres import read_window

        result = read_window(
            DSN, "BTCUSDT", "15m", self.open_time, self.open_time + self.step
        )
        self.assertEqual(len(result["candles"]), 1)
        self.assertEqual(result["candles"][0]["open"], "100.12345678901234567890123456789")
        self.assertEqual(result["candles"][0]["volume"], "5.00000000000000000001")

    def test_wrong_owner_and_stale_generation_are_rejected_without_rows(self):
        from market_data.postgres import PostgresWriteGateway, connection

        wrong_owner = PostgresWriteGateway(
            DSN, lease_name=self.lease_name, owner_id="not-the-owner",
            generation_provider=lambda: self.lease.generation,
        )
        with self.assertRaises(PermissionError):
            wrong_owner.write_batch([self.candle()])
        stale_generation = self.gateway(generation=self.lease.generation + 1)
        with self.assertRaises(PermissionError):
            stale_generation.write_batch([self.candle()])
        with connection(DSN, read_only=True) as database:
            count = database.execute(
                "SELECT count(*) FROM market_data.candles WHERE open_time_ms=%s",
                (self.open_time,),
            ).fetchone()[0]
        self.assertEqual(count, 0)

    def test_expired_lease_is_rejected_using_database_time(self):
        from market_data.postgres import PostgresLeaseStore, connection

        expired = PostgresLeaseStore(DSN, lease_name=self.lease_name)
        self.assertTrue(expired.release(self.owner, self.lease.generation))
        short = expired.acquire("short-owner", ttl_seconds=1)
        self.assertIsNotNone(short)
        time.sleep(1.2)
        gateway = self.gateway(owner="short-owner", generation=short.generation)
        with self.assertRaises(PermissionError):
            gateway.write_batch([self.candle()])
        with connection(DSN, read_only=True) as database:
            count = database.execute(
                "SELECT count(*) FROM market_data.candles WHERE open_time_ms=%s",
                (self.open_time,),
            ).fetchone()[0]
        self.assertEqual(count, 0)

    def test_identical_duplicate_is_idempotent_and_conflict_rolls_back(self):
        from market_data.postgres import connection

        gateway = self.gateway()
        self.assertEqual(gateway.write_batch([self.candle()]), 1)
        self.assertEqual(gateway.write_batch([self.candle()]), 0)
        second_open = self.open_time + self.step
        second = self.candle(open_time=second_open)
        with self.assertRaises(ValueError):
            gateway.write_batch([second, self.candle(close="100.5")])
        with connection(DSN, read_only=True) as database:
            rows = database.execute(
                "SELECT open_time_ms, close FROM market_data.candles WHERE open_time_ms IN (%s, %s) ORDER BY open_time_ms",
                (self.open_time, second_open),
            ).fetchall()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][0], self.open_time)
        self.assertEqual(str(rows[0][1]), "101")
        
    def test_connection_termination_during_batch_rolls_back_prior_rows(self):
        from concurrent.futures import ThreadPoolExecutor
        from market_data.postgres import StoreUnavailable, connection

        second_open = self.open_time + self.step
        with connection(DSN) as database:
            database.execute(f"""
                CREATE OR REPLACE FUNCTION market_data.pg_red_disconnect_insert()
                RETURNS trigger LANGUAGE plpgsql AS $t0_disconnect$
                BEGIN
                    IF NEW.open_time_ms = {second_open} THEN
                        PERFORM pg_sleep(8);
                    END IF;
                    RETURN NEW;
                END $t0_disconnect$
            """)
            database.execute("""
                CREATE TRIGGER pg_red_disconnect_insert
                BEFORE INSERT ON market_data.candles
                FOR EACH ROW EXECUTE FUNCTION market_data.pg_red_disconnect_insert()
            """)

        try:
            gateway = self.gateway()
            with ThreadPoolExecutor(max_workers=1) as pool:
                write_future = pool.submit(
                    gateway.write_batch,
                    [
                        self.candle(open_time=self.open_time),
                        self.candle(open_time=second_open),
                    ],
                )

                backend_pid = None
                deadline = time.monotonic() + 4
                while time.monotonic() < deadline and backend_pid is None:
                    with connection(DSN, read_only=True) as database:
                        row = database.execute(
                            """
                            SELECT pid
                            FROM pg_stat_activity
                            WHERE datname = current_database()
                              AND state = 'active'
                              AND pid <> pg_backend_pid()
                              AND query LIKE '%write_canonical_candle%'
                            ORDER BY query_start DESC
                            LIMIT 1
                            """
                        ).fetchone()
                    if row is not None:
                        backend_pid = row[0]
                    else:
                        time.sleep(0.05)

                self.assertIsNotNone(
                    backend_pid,
                    "writer backend did not enter the second-row trigger",
                )
                with connection(DSN) as database:
                    terminated = database.execute(
                        "SELECT pg_terminate_backend(%s)", (backend_pid,)
                    ).fetchone()[0]
                self.assertTrue(terminated)

                with self.assertRaises(StoreUnavailable):
                    write_future.result(timeout=5)

            with connection(DSN, read_only=True) as database:
                count = database.execute(
                    """
                    SELECT count(*)
                    FROM market_data.candles
                    WHERE open_time_ms IN (%s, %s)
                    """,
                    (self.open_time, second_open),
                ).fetchone()[0]
            self.assertEqual(count, 0)
        finally:
            with connection(DSN) as database:
                database.execute(
                    "DROP TRIGGER IF EXISTS pg_red_disconnect_insert ON market_data.candles"
                )
                database.execute(
                    "DROP FUNCTION IF EXISTS market_data.pg_red_disconnect_insert()"
                )

    def test_sigkill_writer_process_rolls_back_batch_and_allows_new_generation(self):
        import os
        import signal
        import subprocess
        import sys
        from market_data.postgres import PostgresLeaseStore, connection

        second_open = self.open_time + self.step
        with connection(DSN) as database:
            database.execute(f"""
                CREATE OR REPLACE FUNCTION market_data.pg_red_process_kill_insert()
                RETURNS trigger LANGUAGE plpgsql AS $t0_process_kill$
                BEGIN
                    IF NEW.open_time_ms = {second_open} THEN
                        PERFORM pg_sleep(3);
                    END IF;
                    RETURN NEW;
                END $t0_process_kill$
            """)
            database.execute("""
                CREATE TRIGGER pg_red_process_kill_insert
                BEFORE INSERT ON market_data.candles
                FOR EACH ROW EXECUTE FUNCTION market_data.pg_red_process_kill_insert()
            """)

        process = None
        try:
            script = """
import os
from market_data.postgres import PostgresWriteGateway
from market_data.store import Candle

step = 900_000
start = int(os.environ["T0_TEST_OPEN_TIME"])
candles = [
    Candle("15m", start, "100", "102", "99", "101", "5", start + step + 1),
    Candle("15m", start + step, "100", "102", "99", "101", "5", start + 2 * step + 1),
]
gateway = PostgresWriteGateway(
    os.environ["T0_TEST_DSN"],
    lease_name="binance-btcusdt-canonical",
    owner_id=os.environ["T0_TEST_OWNER"],
    generation_provider=lambda: int(os.environ["T0_TEST_GENERATION"]),
)
gateway.write_batch(candles)
"""
            environment = dict(os.environ)
            environment.update({
                "T0_TEST_DSN": DSN,
                "T0_TEST_OWNER": self.owner,
                "T0_TEST_GENERATION": str(self.lease.generation),
                "T0_TEST_OPEN_TIME": str(self.open_time),
            })
            process = subprocess.Popen(
                [sys.executable, "-c", script],
                env=environment,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            backend_pid = None
            deadline = time.monotonic() + 5
            while time.monotonic() < deadline and backend_pid is None:
                with connection(DSN, read_only=True) as database:
                    row = database.execute(
                        """
                        SELECT pid
                        FROM pg_stat_activity
                        WHERE datname = current_database()
                          AND state = 'active'
                          AND pid <> pg_backend_pid()
                          AND query LIKE '%write_canonical_candle%'
                        ORDER BY query_start DESC
                        LIMIT 1
                        """
                    ).fetchone()
                if row is not None:
                    backend_pid = row[0]
                else:
                    time.sleep(0.05)

            self.assertIsNotNone(
                backend_pid,
                "child writer did not enter the second-row trigger",
            )
            process.kill()
            self.assertEqual(process.wait(timeout=5), -signal.SIGKILL)

            deadline = time.monotonic() + 8
            backend_still_active = True
            while time.monotonic() < deadline and backend_still_active:
                with connection(DSN, read_only=True) as database:
                    row = database.execute(
                        "SELECT 1 FROM pg_stat_activity WHERE pid=%s",
                        (backend_pid,),
                    ).fetchone()
                backend_still_active = row is not None
                if backend_still_active:
                    time.sleep(0.05)
            self.assertFalse(backend_still_active, "terminated writer backend did not exit")

            with connection(DSN, read_only=True) as database:
                count = database.execute(
                    """
                    SELECT count(*)
                    FROM market_data.candles
                    WHERE open_time_ms IN (%s, %s)
                    """,
                    (self.open_time, second_open),
                ).fetchone()[0]
            self.assertEqual(count, 0)

            self.assertTrue(self.leases.release(self.owner, self.lease.generation))
            replacement = self.leases.acquire("writer-after-sigkill", ttl_seconds=30)
            self.assertIsNotNone(replacement)
            self.assertGreater(replacement.generation, self.lease.generation)
            self.assertTrue(
                self.leases.is_current("writer-after-sigkill", replacement.generation)
            )
        finally:
            if process is not None and process.poll() is None:
                process.kill()
                process.wait(timeout=5)
            with connection(DSN) as database:
                database.execute(
                    "DROP TRIGGER IF EXISTS pg_red_process_kill_insert ON market_data.candles"
                )
                database.execute(
                    "DROP FUNCTION IF EXISTS market_data.pg_red_process_kill_insert()"
                )

    def test_interrupted_migration_rolls_back_and_retry_applies_cleanly(self):
        import tempfile
        from concurrent.futures import ThreadPoolExecutor
        from pathlib import Path
        import psycopg
        from psycopg import sql
        from psycopg.conninfo import make_conninfo
        import market_data.migrations as migration_module
        from market_data.migrations import migrate
        from market_data.postgres import StoreUnavailable

        database_name = "t0_migration_" + uuid.uuid4().hex[:12]
        application_name = "t0-migration-interrupt-" + uuid.uuid4().hex[:8]
        target_dsn = make_conninfo(
            DSN, dbname=database_name, application_name=application_name
        )
        original_migrations = migration_module.MIGRATIONS
        database_created = False

        try:
            with psycopg.connect(DSN, autocommit=True) as admin:
                admin.execute(
                    sql.SQL("CREATE DATABASE {}").format(sql.Identifier(database_name))
                )
            database_created = True

            with tempfile.TemporaryDirectory(prefix="t0-migrations-") as temporary:
                migration_dir = Path(temporary)
                (migration_dir / "001_probe.sql").write_text(
                    """
                    CREATE TABLE market_data.migration_probe (
                        id INTEGER PRIMARY KEY
                    );
                    INSERT INTO market_data.migration_probe VALUES (1);
                    """,
                    encoding="utf-8",
                )
                (migration_dir / "002_delayed_probe.sql").write_text(
                    """
                    CREATE TABLE market_data.interrupted_probe (
                        id INTEGER PRIMARY KEY
                    );
                    SELECT pg_sleep(4);
                    INSERT INTO market_data.interrupted_probe VALUES (2);
                    """,
                    encoding="utf-8",
                )
                migration_module.MIGRATIONS = migration_dir

                with ThreadPoolExecutor(max_workers=1) as pool:
                    migration_future = pool.submit(migrate, target_dsn)
                    backend_pid = None
                    deadline = time.monotonic() + 3
                    while time.monotonic() < deadline and backend_pid is None:
                        with psycopg.connect(DSN, autocommit=True) as admin:
                            row = admin.execute(
                                """
                                SELECT pid
                                FROM pg_stat_activity
                                WHERE datname=%s
                                  AND application_name=%s
                                  AND state='active'
                                  AND position('pg_sleep(4)' IN query) > 0
                                LIMIT 1
                                """,
                                (database_name, application_name),
                            ).fetchone()
                        if row is not None:
                            backend_pid = row[0]
                        else:
                            time.sleep(0.05)

                    self.assertIsNotNone(
                        backend_pid,
                        "migration did not reach the deterministic delay statement",
                    )
                    with psycopg.connect(DSN, autocommit=True) as admin:
                        cancelled = admin.execute(
                            "SELECT pg_cancel_backend(%s)", (backend_pid,)
                        ).fetchone()[0]
                    self.assertTrue(cancelled)
                    with self.assertRaises(StoreUnavailable):
                        migration_future.result(timeout=5)

                with psycopg.connect(target_dsn, autocommit=True) as database:
                    schema_exists = database.execute(
                        "SELECT EXISTS (SELECT 1 FROM pg_namespace WHERE nspname='market_data')"
                    ).fetchone()[0]
                self.assertFalse(schema_exists, "interrupted migration left partial schema state")

                self.assertEqual(migrate(target_dsn), (0, 2))
                with psycopg.connect(target_dsn, autocommit=True) as database:
                    migration_rows = database.execute(
                        "SELECT migration_id FROM market_data.schema_migrations ORDER BY migration_id"
                    ).fetchall()
                    probe_rows = database.execute(
                        "SELECT id FROM market_data.migration_probe"
                    ).fetchall()
                    delayed_rows = database.execute(
                        "SELECT id FROM market_data.interrupted_probe"
                    ).fetchall()
                self.assertEqual(
                    migration_rows,
                    [("001_probe.sql",), ("002_delayed_probe.sql",)],
                )
                self.assertEqual(probe_rows, [(1,)])
                self.assertEqual(delayed_rows, [(2,)])
                self.assertEqual(migrate(target_dsn), (2, 2))
        finally:
            migration_module.MIGRATIONS = original_migrations
            if database_created:
                with psycopg.connect(DSN, autocommit=True) as admin:
                    admin.execute(
                        "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                        "WHERE datname=%s AND pid<>pg_backend_pid()",
                        (database_name,),
                    )
                    admin.execute(
                        sql.SQL("DROP DATABASE IF EXISTS {}").format(
                            sql.Identifier(database_name)
                        )
                    )

    def test_invalid_middle_candle_is_rejected_before_any_write(self):
        from market_data.postgres import connection

        # Bypass the value-object constructor to prove the Gateway revalidates
        # every candle before opening a transaction or writing any row.
        invalid = object.__new__(Candle)
        for name, value in {
            "timeframe": "15m", "open_time_ms": self.open_time + self.step,
            "open": "100", "high": "99", "low": "101", "close": "100",
            "volume": "1", "available_at_ms": self.open_time + 2 * self.step + 1,
            "symbol": "BTCUSDT",
        }.items():
            object.__setattr__(invalid, name, value)
        with self.assertRaises(ValueError):
            self.gateway().write_batch([self.candle(), invalid])
        with connection(DSN, read_only=True) as database:
            count = database.execute(
                "SELECT count(*) FROM market_data.candles WHERE open_time_ms IN (%s, %s)",
                (self.open_time, self.open_time + self.step),
            ).fetchone()[0]
        self.assertEqual(count, 0)

    def test_takeover_waits_for_writer_transaction_and_old_generation_is_fenced(self):
        from market_data.postgres import PostgresLeaseStore, connection

        # A database trigger holds the writer transaction beyond lease expiry.
        # The lease row lock must prevent a replacement generation from taking
        # over until the old transaction rolls back at its final DB-clock check.
        with connection(DSN) as database:
            database.execute("""
                CREATE OR REPLACE FUNCTION market_data.pg_red_delay_insert()
                RETURNS trigger LANGUAGE plpgsql AS $$
                BEGIN
                    PERFORM pg_sleep(1.5);
                    RETURN NEW;
                END $$;
            """)
            database.execute("""
                CREATE TRIGGER pg_red_delay_insert
                BEFORE INSERT ON market_data.candles
                FOR EACH ROW EXECUTE FUNCTION market_data.pg_red_delay_insert()
            """)
        try:
            leases = PostgresLeaseStore(DSN, lease_name=self.lease_name)
            self.assertTrue(leases.release(self.owner, self.lease.generation))
            short = leases.acquire(self.owner, ttl_seconds=1)
            gateway = self.gateway(generation=short.generation)
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                write_future = pool.submit(gateway.write_batch, [self.candle()])
                time.sleep(0.2)
                # This call must block on the lease row until the writer's
                # expired transaction rolls back, then increment generation.
                replacement = PostgresLeaseStore(
                    DSN, lease_name=self.lease_name
                ).acquire("writer-b", ttl_seconds=30)
                with self.assertRaises(PermissionError):
                    write_future.result(timeout=5)
            self.assertIsNotNone(replacement)
            self.assertGreater(replacement.generation, short.generation)
            stale = self.gateway(generation=short.generation)
            with self.assertRaises(PermissionError):
                stale.write_batch([self.candle(open_time=self.open_time + self.step)])
        finally:
            with connection(DSN) as database:
                database.execute("DROP TRIGGER IF EXISTS pg_red_delay_insert ON market_data.candles")
                database.execute("DROP FUNCTION IF EXISTS market_data.pg_red_delay_insert()")

    def test_lease_heartbeat_and_release_are_generation_bound(self):
        from market_data.postgres import PostgresLeaseStore

        self.assertTrue(self.leases.is_current(self.owner, self.lease.generation))
        self.assertTrue(self.leases.heartbeat(self.owner, self.lease.generation, ttl_seconds=30))
        self.assertFalse(self.leases.heartbeat(self.owner, self.lease.generation + 1, ttl_seconds=30))
        self.assertTrue(self.leases.release(self.owner, self.lease.generation))
        self.assertFalse(self.leases.is_current(self.owner, self.lease.generation))


if __name__ == "__main__":
    unittest.main()
