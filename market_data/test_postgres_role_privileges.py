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
        from psycopg import sql
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
            admin.execute(sql.SQL("CREATE ROLE {} LOGIN PASSWORD {}").format(
                sql.Identifier(cls.feeder_role), sql.Literal(cls.feeder_password)
            ))
            admin.execute(sql.SQL("CREATE ROLE {} LOGIN PASSWORD {}").format(
                sql.Identifier(cls.reader_role), sql.Literal(cls.reader_password)
            ))
            admin.execute("REVOKE ALL ON SCHEMA market_data FROM PUBLIC")
            admin.execute("REVOKE ALL ON ALL TABLES IN SCHEMA market_data FROM PUBLIC")
            admin.execute("GRANT CONNECT ON DATABASE t0_test TO " + '"' + cls.feeder_role + '"')
            admin.execute("GRANT CONNECT ON DATABASE t0_test TO " + '"' + cls.reader_role + '"')
            admin.execute("GRANT USAGE ON SCHEMA market_data TO " + '"' + cls.feeder_role + '"')
            admin.execute("GRANT USAGE ON SCHEMA market_data TO " + '"' + cls.reader_role + '"')
            admin.execute(
                "GRANT t0_feeder_writer TO " + '"' + cls.feeder_role + '"'
            )
            admin.execute(
                "GRANT t0_feeder_lease_manager TO " + '"' + cls.feeder_role + '"'
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

        self.lease_name = "binance-btcusdt-canonical"
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

    def test_feeder_cannot_acquire_or_use_an_alternate_lease_identity(self):
        from market_data.postgres import PostgresLeaseStore

        canonical = PostgresLeaseStore(self.feeder_dsn, lease_name=self.lease_name)
        lease = canonical.acquire("alternate-name-probe", ttl_seconds=30)
        self.assertIsNotNone(lease)
        with self.psycopg.connect(self.feeder_dsn, autocommit=True) as feeder:
            with self.assertRaises(self.psycopg.errors.InsufficientPrivilege):
                feeder.execute(
                    "SELECT * FROM market_data.acquire_feeder_lease(%s, %s, %s)",
                    ("attacker-created-lease", "alternate-worker", 30),
                )
            with self.assertRaises(self.psycopg.errors.InsufficientPrivilege):
                feeder.execute(
                    "SELECT market_data.write_canonical_candle(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                    ("attacker-created-lease", "alternate-name-probe", lease.generation,
                     "binance", "USDT_PERPETUAL", "BTCUSDT", "15m", self.open_time,
                     100, 102, 99, 101, 1, self.open_time + self.step + 1),
                )
        self.assertTrue(canonical.release("alternate-name-probe", lease.generation))

    def test_migration_rejects_login_granted_a_security_definer_owner_role(self):
        from market_data.migrations import migrate

        login = "t0_owner_role_probe_" + uuid.uuid4().hex[:12]
        for owner_role in ("t0_candle_writer_owner", "t0_lease_manager_owner"):
            with self.subTest(owner_role=owner_role):
                with self.psycopg.connect(DSN, autocommit=True) as admin:
                    admin.execute(f'CREATE ROLE "{login}" LOGIN')
                    admin.execute(f'GRANT {owner_role} TO "{login}"')
                    try:
                        with self.assertRaisesRegex(
                            RuntimeError, "must not be granted to runtime or login roles"
                        ):
                            migrate(DSN)
                    finally:
                        admin.execute(f'REVOKE {owner_role} FROM "{login}"')
                        admin.execute(f'DROP ROLE "{login}"')

    def test_feeder_role_can_manage_lease_and_write_only_through_gateway(self):
        from market_data.postgres import PostgresLeaseStore, PostgresWriteGateway

        leases = PostgresLeaseStore(self.feeder_dsn, lease_name=self.lease_name)
        lease = leases.acquire("least-privilege-worker", ttl_seconds=30)
        self.assertIsNotNone(lease)
        candle = self._candle()
        with self.psycopg.connect(self.feeder_dsn, autocommit=True) as feeder:
            with self.assertRaises(self.psycopg.errors.InsufficientPrivilege):
                feeder.execute("SELECT * FROM market_data.feeder_leases")
            with self.assertRaises(self.psycopg.errors.InsufficientPrivilege):
                feeder.execute(
                    "INSERT INTO market_data.feeder_leases "
                    "(lease_name, owner_id, generation, expires_at) "
                    "VALUES ('forged-lease', 'attacker', 99, clock_timestamp() + interval '1 hour')"
                )
            with self.assertRaises(self.psycopg.errors.InsufficientPrivilege):
                feeder.execute(
                    "UPDATE market_data.feeder_leases "
                    "SET owner_id='attacker', generation=generation+99, "
                    "expires_at=clock_timestamp() + interval '1 hour' "
                    "WHERE lease_name=%s",
                    (self.lease_name,),
                )
            with self.assertRaises(self.psycopg.errors.InsufficientPrivilege):
                feeder.execute(
                    "INSERT INTO market_data.candles "
                    "(exchange,market_type,symbol,timeframe,open_time_ms,"
                    "open,high,low,close,volume,available_at_ms) "
                    "VALUES ('binance','USDT_PERPETUAL','BTCUSDT','15m',"
                    "%s,100,102,99,101,1,%s)",
                    (self.open_time, self.open_time + self.step + 1),
                )
        gateway = PostgresWriteGateway(
            self.feeder_dsn,
            lease_name=self.lease_name,
            owner_id="least-privilege-worker",
            generation_provider=lambda: lease.generation,
        )
        self.assertEqual(gateway.write_batch([candle]), 1)
        with self.psycopg.connect(self.feeder_dsn, autocommit=True) as feeder:
            with self.assertRaises(self.psycopg.errors.InsufficientPrivilege):
                feeder.execute(
                    "SELECT market_data.write_canonical_candle("
                    "%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                    (
                        self.lease_name, "least-privilege-worker",
                        lease.generation + 1, "binance", "USDT_PERPETUAL",
                        "BTCUSDT", "15m", self.open_time,
                        100, 102, 99, 101, 1, self.open_time + self.step + 1,
                    ),
                )
        self.assertTrue(leases.heartbeat("least-privilege-worker", lease.generation, 30))
        self.assertTrue(leases.release("least-privilege-worker", lease.generation))

    def test_feeder_lease_api_enforces_contention_and_exact_generation(self):
        from market_data.postgres import PostgresLeaseStore

        first_store = PostgresLeaseStore(self.feeder_dsn, lease_name=self.lease_name)
        second_store = PostgresLeaseStore(self.feeder_dsn, lease_name=self.lease_name)
        first = first_store.acquire("worker-a", ttl_seconds=30)
        self.assertIsNotNone(first)
        self.assertIsNone(second_store.acquire("worker-b", ttl_seconds=30))
        self.assertFalse(second_store.heartbeat("worker-b", first.generation, 30))
        self.assertFalse(second_store.release("worker-b", first.generation))
        self.assertTrue(first_store.is_current("worker-a", first.generation))
        self.assertTrue(first_store.release("worker-a", first.generation))

        replacement = second_store.acquire("worker-b", ttl_seconds=30)
        self.assertIsNotNone(replacement)
        self.assertGreater(replacement.generation, first.generation)
        self.assertFalse(first_store.heartbeat("worker-a", first.generation, 30))
        self.assertFalse(first_store.release("worker-a", first.generation))
        self.assertTrue(second_store.is_current("worker-b", replacement.generation))
        self.assertTrue(second_store.release("worker-b", replacement.generation))

    def test_feeder_role_cannot_ddl_delete_or_truncate(self):
        with self.psycopg.connect(self.feeder_dsn, autocommit=True) as feeder:
            with self.assertRaises(self.psycopg.errors.InsufficientPrivilege):
                feeder.execute("CREATE TABLE market_data.forbidden_ddl(id integer)")
            with self.assertRaises(self.psycopg.errors.InsufficientPrivilege):
                feeder.execute("DELETE FROM market_data.candles")
            with self.assertRaises(self.psycopg.errors.InsufficientPrivilege):
                feeder.execute("TRUNCATE market_data.candles")
            with self.assertRaises(self.psycopg.errors.InsufficientPrivilege):
                feeder.execute("UPDATE market_data.candles SET close=close")
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

    def test_writer_function_has_least_privilege_owner_and_no_public_execute(self):
        with self.psycopg.connect(DSN, autocommit=True) as admin:
            owner = admin.execute(
                "SELECT r.rolsuper, r.rolcanlogin, "
                "has_schema_privilege(r.rolname, 'market_data', 'CREATE'), "
                "has_table_privilege(r.rolname, 'market_data.candles', 'INSERT'), "
                "has_table_privilege(r.rolname, 'market_data.candles', 'DELETE'), "
                "has_table_privilege(r.rolname, 'market_data.feeder_leases', 'UPDATE') "
                "FROM pg_roles r WHERE r.rolname='t0_candle_writer_owner'"
            ).fetchone()
            feeder_insert = admin.execute(
                "SELECT has_table_privilege(%s, 'market_data.candles', 'INSERT')",
                (self.feeder_role,),
            ).fetchone()[0]
            public_execute = admin.execute(
                "SELECT EXISTS ("
                "SELECT 1 FROM pg_proc p "
                "CROSS JOIN LATERAL aclexplode(COALESCE(p.proacl, acldefault('f', p.proowner))) a "
                "WHERE p.oid='market_data.write_canonical_candle("
                "text,text,bigint,text,text,text,text,bigint,numeric,numeric,numeric,numeric,numeric,bigint)'::regprocedure "
                "AND a.grantee=0 AND a.privilege_type='EXECUTE')"
            ).fetchone()[0]
            feeder_lease_select = admin.execute(
                "SELECT has_table_privilege(%s, 'market_data.feeder_leases', 'SELECT')",
                (self.feeder_role,),
            ).fetchone()[0]
            feeder_lease_insert = admin.execute(
                "SELECT has_table_privilege(%s, 'market_data.feeder_leases', 'INSERT')",
                (self.feeder_role,),
            ).fetchone()[0]
            lease_owner = admin.execute(
                "SELECT r.rolsuper, r.rolcanlogin, "
                "has_schema_privilege(r.rolname, 'market_data', 'CREATE'), "
                "has_table_privilege(r.rolname, 'market_data.feeder_leases', 'SELECT'), "
                "has_table_privilege(r.rolname, 'market_data.feeder_leases', 'INSERT'), "
                "has_table_privilege(r.rolname, 'market_data.feeder_leases', 'UPDATE'), "
                "has_table_privilege(r.rolname, 'market_data.feeder_leases', 'DELETE') "
                "FROM pg_roles r WHERE r.rolname='t0_lease_manager_owner'"
            ).fetchone()
            writer_lease_privileges = admin.execute(
                "SELECT has_table_privilege('t0_feeder_writer', 'market_data.feeder_leases', 'SELECT'), "
                "has_table_privilege('t0_feeder_writer', 'market_data.feeder_leases', 'INSERT'), "
                "has_table_privilege('t0_feeder_writer', 'market_data.feeder_leases', 'UPDATE')"
            ).fetchone()
            lease_manager_candle_privileges = admin.execute(
                "SELECT has_table_privilege('t0_feeder_lease_manager', 'market_data.candles', 'SELECT'), "
                "has_table_privilege('t0_feeder_lease_manager', 'market_data.candles', 'INSERT'), "
                "has_table_privilege('t0_feeder_lease_manager', 'market_data.candles', 'UPDATE')"
            ).fetchone()
            feeder_lease_update = admin.execute(
                "SELECT has_table_privilege(%s, 'market_data.feeder_leases', 'UPDATE')",
                (self.feeder_role,),
            ).fetchone()[0]
            lease_manager_member = admin.execute(
                "SELECT pg_has_role(%s, 't0_feeder_lease_manager', 'MEMBER')",
                (self.feeder_role,),
            ).fetchone()[0]
            public_lease_execute = admin.execute(
                "SELECT EXISTS ("
                "SELECT 1 FROM pg_proc p "
                "CROSS JOIN LATERAL aclexplode(COALESCE(p.proacl, acldefault('f', p.proowner))) a "
                "WHERE p.proname IN ('acquire_feeder_lease', 'heartbeat_feeder_lease', 'release_feeder_lease', 'is_current_feeder_lease') "
                "AND a.grantee=0 AND a.privilege_type='EXECUTE')"
            ).fetchone()[0]
        self.assertEqual(owner, (False, False, False, True, False, True))
        self.assertFalse(feeder_insert)
        self.assertFalse(feeder_lease_select)
        self.assertFalse(feeder_lease_insert)
        self.assertFalse(feeder_lease_update)
        self.assertEqual(lease_owner, (False, False, False, True, True, True, False))
        self.assertEqual(writer_lease_privileges, (False, False, False))
        self.assertEqual(lease_manager_candle_privileges, (False, False, False))
        self.assertTrue(lease_manager_member)
        self.assertFalse(public_execute)
        self.assertFalse(public_lease_execute)

    def test_fresh_migrations_run_as_restricted_temporary_migrator(self):
        from psycopg.conninfo import make_conninfo
        from market_data.migrations import migrate
        from psycopg import sql

        suffix = uuid.uuid4().hex[:10]
        database_name = "t0_migrator_" + suffix
        password = uuid.uuid4().hex
        created_roles = False
        try:
            with self.psycopg.connect(DSN, autocommit=True) as admin:
                admin.execute("CREATE ROLE t0_db_owner NOLOGIN")
                admin.execute("CREATE ROLE t0_migrator NOLOGIN")
                admin.execute(sql.SQL("CREATE ROLE t0_migrator_login LOGIN PASSWORD {}").format(sql.Literal(password)))
                created_roles = True
                admin.execute("GRANT t0_db_owner TO t0_migrator")
                admin.execute("GRANT t0_candle_writer_owner TO t0_migrator")
                admin.execute("GRANT t0_lease_manager_owner TO t0_migrator")
                admin.execute("GRANT t0_migrator TO t0_migrator_login")
                admin.execute(sql.SQL("CREATE DATABASE {} OWNER t0_db_owner").format(sql.Identifier(database_name)))
            admin_dsn = make_conninfo(DSN, dbname=database_name)
            with self.psycopg.connect(admin_dsn, autocommit=True) as admin:
                admin.execute("CREATE EXTENSION IF NOT EXISTS timescaledb")

            migrator_dsn = make_conninfo(
                DSN, user="t0_migrator_login", password=password,
                dbname=database_name,
            )
            migrate(migrator_dsn)
            with self.psycopg.connect(admin_dsn, autocommit=True) as admin:
                owners = admin.execute(
                    "SELECT p.proname, r.rolname FROM pg_proc p JOIN pg_roles r ON r.oid=p.proowner "
                    "WHERE p.proname IN ('write_canonical_candle', 'acquire_feeder_lease') ORDER BY p.proname"
                ).fetchall()
                self.assertEqual(
                    owners,
                    [("acquire_feeder_lease", "t0_lease_manager_owner"),
                     ("write_canonical_candle", "t0_candle_writer_owner")],
                )
                schema_owner = admin.execute(
                    "SELECT r.rolname FROM pg_namespace n "
                    "JOIN pg_roles r ON r.oid=n.nspowner WHERE n.nspname='market_data'"
                ).fetchone()[0]
                ledger_owner = admin.execute(
                    "SELECT r.rolname FROM pg_class c "
                    "JOIN pg_roles r ON r.oid=c.relowner "
                    "WHERE c.oid='market_data.schema_migrations'::regclass"
                ).fetchone()[0]
                table_owners = admin.execute(
                    "SELECT DISTINCT tableowner FROM pg_tables "
                    "WHERE schemaname='market_data' ORDER BY tableowner"
                ).fetchall()
                self.assertEqual(schema_owner, "t0_db_owner")
                self.assertEqual(ledger_owner, "t0_db_owner")
                self.assertEqual(table_owners, [("t0_db_owner",)])

            replacement_password = uuid.uuid4().hex
            with self.psycopg.connect(DSN, autocommit=True) as admin:
                admin.execute("REVOKE t0_migrator FROM t0_migrator_login")
                admin.execute("DROP ROLE t0_migrator_login")
                admin.execute(
                    sql.SQL("CREATE ROLE t0_migrator_login LOGIN PASSWORD {}").format(
                        sql.Literal(replacement_password)
                    )
                )
                admin.execute("GRANT t0_migrator TO t0_migrator_login")
            replacement_dsn = make_conninfo(
                DSN, user="t0_migrator_login", password=replacement_password,
                dbname=database_name,
            )
            applied_count, total_count = migrate(replacement_dsn)
            self.assertEqual(applied_count, total_count)
        finally:
            with self.psycopg.connect(DSN, autocommit=True) as admin:
                admin.execute(sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(sql.Identifier(database_name)))
                if created_roles:
                    admin.execute("DROP ROLE IF EXISTS t0_migrator_login")
                    admin.execute("DROP ROLE IF EXISTS t0_migrator")
                    admin.execute("DROP ROLE IF EXISTS t0_db_owner")

    def test_migration_runner_rejects_preexisting_privileged_writer_roles(self):
        from market_data.migrations import migrate

        for role in ("t0_candle_writer_owner", "t0_feeder_writer",
                     "t0_lease_manager_owner", "t0_feeder_lease_manager"):
            with self.subTest(role=role):
                with self.psycopg.connect(DSN, autocommit=True) as admin:
                    admin.execute(f'ALTER ROLE "{role}" SUPERUSER LOGIN')
                    try:
                        with self.assertRaisesRegex(
                            RuntimeError,
                            f"{role} must remain a restricted NOLOGIN role",
                        ):
                            migrate(DSN)
                    finally:
                        admin.execute(f'ALTER ROLE "{role}" NOSUPERUSER NOLOGIN')

    def test_migration_runner_rejects_login_enabled_migrator_group_role(self):
        from market_data.migrations import migrate

        with self.psycopg.connect(DSN, autocommit=True) as admin:
            admin.execute("CREATE ROLE t0_migrator NOLOGIN")
            admin.execute("ALTER ROLE t0_migrator LOGIN")
            try:
                with self.assertRaisesRegex(RuntimeError, "t0_migrator must remain a restricted NOLOGIN role"):
                    migrate(DSN)
            finally:
                admin.execute("ALTER ROLE t0_migrator NOLOGIN")
                admin.execute("DROP ROLE t0_migrator")

    def test_migration_runner_rejects_unapproved_t0_migrator_member(self):
        from market_data.migrations import migrate

        login = "t0_migrator_probe_" + uuid.uuid4().hex[:12]
        with self.psycopg.connect(DSN, autocommit=True) as admin:
            admin.execute("CREATE ROLE t0_migrator NOLOGIN")
            admin.execute(f'CREATE ROLE "{login}" LOGIN')
            admin.execute(f'GRANT t0_migrator TO "{login}"')
            try:
                with self.assertRaisesRegex(
                    RuntimeError, "only be granted to the ephemeral t0_migrator_login"
                ):
                    migrate(DSN)
            finally:
                admin.execute(f'REVOKE t0_migrator FROM "{login}"')
                admin.execute(f'DROP ROLE "{login}"')
                admin.execute("DROP ROLE t0_migrator")

    def test_migration_rejects_membership_granted_to_ephemeral_login(self):
        from market_data.migrations import migrate

        member = "t0_login_member_" + uuid.uuid4().hex[:12]
        with self.psycopg.connect(DSN, autocommit=True) as admin:
            admin.execute("CREATE ROLE t0_migrator NOLOGIN")
            admin.execute("CREATE ROLE t0_migrator_login LOGIN")
            admin.execute(f'CREATE ROLE "{member}" LOGIN')
            admin.execute("GRANT t0_migrator TO t0_migrator_login")
            admin.execute(f'GRANT t0_migrator_login TO "{member}"')
            try:
                with self.assertRaisesRegex(
                    RuntimeError, "t0_migrator_login must not be granted to other roles"
                ):
                    migrate(DSN)
            finally:
                admin.execute(f'REVOKE t0_migrator_login FROM "{member}"')
                admin.execute("REVOKE t0_migrator FROM t0_migrator_login")
                admin.execute(f'DROP ROLE "{member}"')
                admin.execute("DROP ROLE t0_migrator_login")
                admin.execute("DROP ROLE t0_migrator")

    def test_migration_rejects_additional_membership_on_ephemeral_login(self):
        from market_data.migrations import migrate

        extra_role = "t0_login_extra_" + uuid.uuid4().hex[:12]
        with self.psycopg.connect(DSN, autocommit=True) as admin:
            admin.execute("CREATE ROLE t0_migrator NOLOGIN")
            admin.execute("CREATE ROLE t0_migrator_login LOGIN")
            admin.execute(f'CREATE ROLE "{extra_role}" NOLOGIN')
            admin.execute("GRANT t0_migrator TO t0_migrator_login")
            admin.execute(f'GRANT "{extra_role}" TO t0_migrator_login')
            try:
                with self.assertRaisesRegex(
                    RuntimeError, "t0_migrator_login may only be a member of t0_migrator"
                ):
                    migrate(DSN)
            finally:
                admin.execute(f'REVOKE "{extra_role}" FROM t0_migrator_login')
                admin.execute("REVOKE t0_migrator FROM t0_migrator_login")
                admin.execute(f'DROP ROLE "{extra_role}"')
                admin.execute("DROP ROLE t0_migrator_login")
                admin.execute("DROP ROLE t0_migrator")

    def test_migration_rejects_admin_option_on_ephemeral_migrator_membership(self):
        from market_data.migrations import migrate

        with self.psycopg.connect(DSN, autocommit=True) as admin:
            admin.execute("CREATE ROLE t0_migrator NOLOGIN")
            admin.execute("CREATE ROLE t0_migrator_login LOGIN")
            admin.execute("GRANT t0_migrator TO t0_migrator_login WITH ADMIN OPTION")
            try:
                with self.assertRaisesRegex(
                    RuntimeError, "t0_migrator_login may only be a member of t0_migrator"
                ):
                    migrate(DSN)
            finally:
                admin.execute("REVOKE ADMIN OPTION FOR t0_migrator FROM t0_migrator_login")
                admin.execute("REVOKE t0_migrator FROM t0_migrator_login")
                admin.execute("DROP ROLE t0_migrator_login")
                admin.execute("DROP ROLE t0_migrator")

    def test_runtime_roles_have_no_schema_create_or_role_admin_privilege(self):
        with self.psycopg.connect(DSN, autocommit=True) as admin:
            feeder = admin.execute(
                "SELECT has_schema_privilege(%s, 'market_data', 'CREATE'), "
                "pg_has_role(%s, 't0_test', 'MEMBER'), "
                "has_table_privilege(%s, 'market_data.feeder_leases', 'SELECT')",
                (self.feeder_role, self.feeder_role, self.feeder_role),
            ).fetchone()
            reader = admin.execute(
                "SELECT has_schema_privilege(%s, 'market_data', 'CREATE'), "
                "has_table_privilege(%s, 'market_data.feeder_leases', 'SELECT')",
                (self.reader_role, self.reader_role),
            ).fetchone()
        self.assertEqual(feeder, (False, False, False))
        self.assertEqual(reader, (False, False))


    def test_migration_rejects_admin_option_on_migrator_owner_role_memberships(self):
        from market_data.migrations import migrate

        with self.psycopg.connect(DSN, autocommit=True) as admin:
            admin.execute("CREATE ROLE t0_db_owner NOLOGIN")
            admin.execute("CREATE ROLE t0_migrator NOLOGIN")
            admin.execute("CREATE ROLE t0_migrator_login LOGIN")
            admin.execute("GRANT t0_migrator TO t0_migrator_login")
            admin.execute("GRANT t0_db_owner TO t0_migrator WITH ADMIN OPTION")
            admin.execute("GRANT t0_candle_writer_owner TO t0_migrator WITH ADMIN OPTION")
            admin.execute("GRANT t0_lease_manager_owner TO t0_migrator WITH ADMIN OPTION")
            try:
                with self.assertRaisesRegex(
                    RuntimeError, "t0_migrator must not have ADMIN OPTION on database or SECURITY DEFINER owner roles"
                ):
                    migrate(DSN)
            finally:
                admin.execute("REVOKE t0_db_owner FROM t0_migrator")
                admin.execute("REVOKE t0_db_owner FROM t0_migrator")
                admin.execute("REVOKE t0_candle_writer_owner FROM t0_migrator")
                admin.execute("REVOKE t0_lease_manager_owner FROM t0_migrator")
                admin.execute("REVOKE t0_migrator FROM t0_migrator_login")
                admin.execute("DROP ROLE t0_migrator_login")
                admin.execute("DROP ROLE t0_migrator")
                admin.execute("DROP ROLE t0_db_owner")
                admin.execute("DROP ROLE t0_db_owner")

    def test_sql_migrations_reject_admin_option_on_migrator_owner_roles(self):
        from pathlib import Path

        migration_dir = Path(__file__).with_name("migrations")
        scripts = (
            "003_t0_database_fenced_candle_writer.sql",
            "004_t0_fenced_lease_api.sql",
        )
        with self.psycopg.connect(DSN, autocommit=True) as admin:
            admin.execute("CREATE ROLE t0_db_owner NOLOGIN")
            admin.execute("CREATE ROLE t0_migrator NOLOGIN")
            admin.execute("CREATE ROLE t0_migrator_login LOGIN")
            admin.execute("GRANT t0_migrator TO t0_migrator_login")
            admin.execute("GRANT t0_db_owner TO t0_migrator WITH ADMIN OPTION")
            admin.execute("GRANT t0_candle_writer_owner TO t0_migrator WITH ADMIN OPTION")
            admin.execute("GRANT t0_lease_manager_owner TO t0_migrator WITH ADMIN OPTION")
            try:
                for filename in scripts:
                    source = (migration_dir / filename).read_text(encoding="utf-8")
                    start = source.index("DO $role$")
                    end = source.index("$role$;", start) + len("$role$;")
                    with self.subTest(migration=filename), self.assertRaisesRegex(
                        self.psycopg.errors.InsufficientPrivilege, "ADMIN OPTION"
                    ):
                        admin.execute(source[start:end])
            finally:
                admin.execute("REVOKE t0_candle_writer_owner FROM t0_migrator")
                admin.execute("REVOKE t0_lease_manager_owner FROM t0_migrator")
                admin.execute("REVOKE t0_migrator FROM t0_migrator_login")
                admin.execute("DROP ROLE t0_migrator_login")
                admin.execute("DROP ROLE t0_migrator")

if __name__ == "__main__":
    unittest.main()
