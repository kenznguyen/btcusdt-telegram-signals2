"""Least-privilege PostgreSQL role acceptance on disposable TimescaleDB only.

The test creates isolated login roles and grants derived from the current T0
runtime SQL. It never uses production DSNs, exchange credentials, or Paper DB.
"""
import os
import unittest
import uuid
from urllib.parse import quote, urlsplit, urlunsplit

DSN = os.environ.get("MARKET_DATA_TEST_DATABASE_URL", "")


def _disposable_dsn_for_role(username, password):
    parsed = urlsplit(DSN)
    return urlunsplit((
        parsed.scheme,
        f"{quote(username)}:{quote(password)}@{parsed.hostname}:{parsed.port}",
        parsed.path,
        parsed.query,
        parsed.fragment,
    ))


@unittest.skipUnless(DSN, "Set the disposable local TimescaleDB test service")
class PostgresRolePrivilegeIntegrationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from market_data.test_postgres_write_gateway import _assert_disposable_target
        _assert_disposable_target()
        import psycopg
        from market_data.migrations import migrate

        migrate(DSN)
        cls.psycopg = psycopg
        cls.suffix = uuid.uuid4().hex[:12]
        cls.feeder_role = "t0_feeder_" + cls.suffix
        cls.reader_role = "t0_reader_" + cls.suffix
        cls.feeder_password = uuid.uuid4().hex
        cls.reader_password = uuid.uuid4().hex
        cls.feeder_dsn = _disposable_dsn_for_role(cls.feeder_role, cls.feeder_password)
        cls.reader_dsn = _disposable_dsn_for_role(cls.reader_role, cls.reader_password)

        with psycopg.connect(DSN, autocommit=True) as admin:
            admin.execute(
                f'CREATE ROLE "{cls.feeder_role}" LOGIN PASSWORD %s',
                (cls.feeder_password,),
            )
            admin.execute(
                f'CREATE ROLE "{cls.reader_role}" LOGIN PASSWORD %s',
                (cls.reader_password,),
            )
            admin.execute("REVOKE ALL ON SCHEMA market_data FROM PUBLIC")
            admin.execute("REVOKE ALL ON ALL TABLES IN SCHEMA market_data FROM PUBLIC")
            admin.execute("GRANT CONNECT ON DATABASE t0_test TO " + '"' + cls.feeder_role + '"')
            admin.execute("GRANT CONNECT ON DATABASE t0_test TO " + '"' + cls.reader_role + '"')
            admin.execute("GRANT USAGE ON SCHEMA market_data TO " + '"' + cls.feeder_role + '"')
            admin.execute("GRANT USAGE ON SCHEMA market_data TO " + '"' + cls.reader_role + '"')
            admin.execute(
                "GRANT SELECT, INSERT, UPDATE ON market_data.feeder_leases TO "
                + '"' + cls.feeder_role + '"'
            )
            admin.execute(
                "GRANT SELECT, INSERT ON market_data.candles TO "
                + '"' + cls.feeder_role + '"'
            )
            admin.execute(
                "GRANT SELECT ON market_data.candles TO " + '"' + cls.reader_role + '"'
            )

    @classmethod
    def tearDownClass(cls):
        with cls.psycopg.connect(DSN, autocommit=True) as admin:
            admin.execute("DROP OWNED BY " + '"' + cls.feeder_role + '"')
            admin.execute("DROP OWNED BY " + '"' + cls.reader_role + '"')
            admin.execute("DROP ROLE " + '"' + cls.feeder_role + '"')
            admin.execute("DROP ROLE " + '"' + cls.reader_role + '"')

    def setUp(self):
        import time
        from market_data.store import INTERVAL_MS

        self.lease_name = "role-test-" + uuid.uuid4().hex
        step = INTERVAL_MS["15m"]
        self.open_time = (int(time.time() * 1000) // step) * step - step
        self.step = step

    def tearDown(self):
        from market_data.postgres import connection

        with connection(DSN) as admin:
            admin.execute(
                "DELETE FROM market_data.candles WHERE symbol='BTCUSDT' AND timeframe='15m' AND open_time_ms=%s",
                (self.open_time,),
            )
            admin.execute(
                "DELETE FROM market_data.feeder_leases WHERE lease_name=%s",
                (self.lease_name,),
            )

    def _candle(self):
        from market_data.store import Candle

        return Candle(
            "15m", self.open_time, "100", "102", "99", "101", "1",
            self.open_time + self.step + 1,
        )

    def test_feeder_role_can_manage_lease_and_write_only_through_gateway(self):
        from market_data.postgres import PostgresLeaseStore, PostgresWriteGateway

        leases = PostgresLeaseStore(self.feeder_dsn, lease_name=self.lease_name)
        lease = leases.acquire("least-privilege-worker", ttl_seconds=30)
        self.assertIsNotNone(lease)
        gateway = PostgresWriteGateway(
            self.feeder_dsn,
            lease_name=self.lease_name,
            owner_id="least-privilege-worker",
            generation_provider=lambda: lease.generation,
        )
        self.assertEqual(gateway.write_batch([self._candle()]), 1)
        self.assertTrue(leases.heartbeat("least-privilege-worker", lease.generation, 30))
        self.assertTrue(leases.release("least-privilege-worker", lease.generation))

    def test_feeder_role_cannot_ddl_delete_or_truncate(self):
        with self.psycopg.connect(self.feeder_dsn, autocommit=True) as feeder:
            with self.assertRaises(self.psycopg.errors.InsufficientPrivilege):
                feeder.execute("CREATE TABLE market_data.forbidden_ddl(id integer)")
            with self.assertRaises(self.psycopg.errors.InsufficientPrivilege):
                feeder.execute("DELETE FROM market_data.candles")
            with self.assertRaises(self.psycopg.errors.InsufficientPrivilege):
                feeder.execute("TRUNCATE market_data.candles")
            with self.assertRaises(self.psycopg.errors.InsufficientPrivilege):
                feeder.execute("CREATE TABLE public.forbidden_public_ddl(id integer)")

    def test_reader_role_can_read_candles_but_cannot_write_or_read_lease(self):
        from market_data.postgres import PostgresLeaseStore, PostgresWriteGateway

        leases = PostgresLeaseStore(self.feeder_dsn, lease_name=self.lease_name)
        lease = leases.acquire("reader-boundary-worker", ttl_seconds=30)
        self.assertIsNotNone(lease)
        gateway = PostgresWriteGateway(
            self.feeder_dsn,
            lease_name=self.lease_name,
            owner_id="reader-boundary-worker",
            generation_provider=lambda: lease.generation,
        )
        self.assertEqual(gateway.write_batch([self._candle()]), 1)

        with self.psycopg.connect(self.reader_dsn, autocommit=True) as reader:
            row = reader.execute(
                "SELECT count(*) FROM market_data.candles WHERE open_time_ms=%s",
                (self.open_time,),
            ).fetchone()
            self.assertEqual(row[0], 1)
            with self.assertRaises(self.psycopg.errors.InsufficientPrivilege):
                reader.execute("SELECT * FROM market_data.feeder_leases")
            with self.assertRaises(self.psycopg.errors.InsufficientPrivilege):
                reader.execute("INSERT INTO market_data.candles "
                               "(exchange,market_type,symbol,timeframe,open_time_ms,"
                               "open,high,low,close,volume,available_at_ms) "
                               "VALUES ('binance','USDT_PERPETUAL','BTCUSDT','15m',"
                               "%s,100,102,99,101,1,%s)",
                               (self.open_time + self.step,
                                self.open_time + 2 * self.step + 1))
            with self.assertRaises(self.psycopg.errors.InsufficientPrivilege):
                reader.execute("UPDATE market_data.candles SET close=close "
                               "WHERE open_time_ms=%s", (self.open_time,))

        self.assertTrue(leases.release("reader-boundary-worker", lease.generation))

    def test_runtime_roles_have_no_schema_create_or_role_admin_privilege(self):
        with self.psycopg.connect(DSN, autocommit=True) as admin:
            feeder = admin.execute(
                "SELECT has_schema_privilege(%s, 'market_data', 'CREATE'), "
                "pg_has_role(%s, 't0_test', 'MEMBER')",
                (self.feeder_role, self.feeder_role),
            ).fetchone()
            reader = admin.execute(
                "SELECT has_schema_privilege(%s, 'market_data', 'CREATE'), "
                "has_table_privilege(%s, 'market_data.feeder_leases', 'SELECT')",
                (self.reader_role, self.reader_role),
            ).fetchone()
        self.assertEqual(feeder, (False, False))
        self.assertEqual(reader, (False, False))


if __name__ == "__main__":
    unittest.main()
