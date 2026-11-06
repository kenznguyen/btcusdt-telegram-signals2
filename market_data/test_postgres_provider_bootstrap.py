"""Fresh-cluster managed-provider bootstrap acceptance.

Runs only against the dedicated disposable TimescaleDB service in CI. The
bootstrap login is intentionally not SUPERUSER; migrations run through the
restricted ephemeral t0_migrator_login identity.
"""
import os
import unittest
import uuid
from urllib.parse import urlsplit

DSN = os.environ.get("MARKET_DATA_TEST_DATABASE_URL", "")


@unittest.skipUnless(DSN, "Set MARKET_DATA_TEST_DATABASE_URL to the isolated TimescaleDB service")
class PostgresProviderBootstrapIntegrationTest(unittest.TestCase):
    def test_non_superuser_bootstrap_provisions_roles_then_restricted_migrations_run(self):
        import psycopg
        from psycopg import sql
        from psycopg.conninfo import make_conninfo
        from market_data.migrations import migrate

        self.assertEqual(os.environ.get("MARKET_DATA_TEST_DISPOSABLE"), "1")
        parsed = urlsplit(DSN)
        self.assertEqual(parsed.scheme, "postgresql")
        self.assertEqual(parsed.hostname, "127.0.0.1")
        self.assertEqual(parsed.port, 5432)
        self.assertEqual(parsed.username, "t0_test")
        self.assertEqual(parsed.path, "/t0_test")

        bootstrap_role = "t0_bootstrap_" + uuid.uuid4().hex[:10]
        bootstrap_password = uuid.uuid4().hex
        migrator_password = uuid.uuid4().hex
        database_name = "t0_bootstrap_" + uuid.uuid4().hex[:10]
        reserved_roles = (
            "t0_db_owner",
            "t0_migrator",
            "t0_migrator_login",
            "t0_feeder_writer",
            "t0_candle_writer_owner",
            "t0_feeder_lease_manager",
            "t0_lease_manager_owner",
        )
        database_created = False
        bootstrap_created = False

        try:
            # The service admin is used only to create a restricted bootstrap
            # identity and to pre-enable the provider-managed TimescaleDB extension.
            with psycopg.connect(DSN, autocommit=True) as service_admin:
                existing = service_admin.execute(
                    "SELECT rolname FROM pg_roles WHERE rolname = ANY(%s)",
                    (list(reserved_roles),),
                ).fetchall()
                self.assertEqual(existing, [], "bootstrap test requires a pristine cluster")
                service_admin.execute(
                    sql.SQL("CREATE ROLE {} LOGIN CREATEROLE CREATEDB PASSWORD {}").format(
                        sql.Identifier(bootstrap_role), sql.Literal(bootstrap_password)
                    )
                )
                bootstrap_created = True

            bootstrap_dsn = make_conninfo(
                DSN, user=bootstrap_role, password=bootstrap_password
            )
            with psycopg.connect(bootstrap_dsn, autocommit=True) as bootstrap:
                flags = bootstrap.execute(
                    "SELECT rolsuper, rolcreaterole, rolcreatedb "
                    "FROM pg_roles WHERE rolname=current_user"
                ).fetchone()
                self.assertEqual(flags, (False, True, True))

                bootstrap.execute("CREATE ROLE t0_db_owner NOLOGIN")
                bootstrap.execute("CREATE ROLE t0_migrator NOLOGIN")
                bootstrap.execute(
                    sql.SQL("CREATE ROLE t0_migrator_login LOGIN PASSWORD {}").format(
                        sql.Literal(migrator_password)
                    )
                )
                bootstrap.execute("CREATE ROLE t0_feeder_writer NOLOGIN")
                bootstrap.execute("CREATE ROLE t0_candle_writer_owner NOLOGIN")
                bootstrap.execute("CREATE ROLE t0_feeder_lease_manager NOLOGIN")
                bootstrap.execute("CREATE ROLE t0_lease_manager_owner NOLOGIN")

                bootstrap.execute("GRANT t0_db_owner TO t0_migrator")
                bootstrap.execute("GRANT t0_candle_writer_owner TO t0_migrator")
                bootstrap.execute("GRANT t0_lease_manager_owner TO t0_migrator")
                bootstrap.execute("GRANT t0_migrator TO t0_migrator_login")

                # Create the database as bootstrap-owned, then grant the
                # database CREATE capability to the non-login schema owner.
                bootstrap.execute(
                    sql.SQL("CREATE DATABASE {}").format(sql.Identifier(database_name))
                )
                database_created = True
                bootstrap.execute(
                    sql.SQL("GRANT CREATE ON DATABASE {} TO t0_db_owner").format(
                        sql.Identifier(database_name)
                    )
                )

                # Remove bootstrap's temporary role memberships before the
                # migration safety guard checks owner-role isolation.
                memberships = bootstrap.execute(
                    "SELECT granted.rolname FROM pg_auth_members membership "
                    "JOIN pg_roles granted ON granted.oid=membership.roleid "
                    "JOIN pg_roles member ON member.oid=membership.member "
                    "WHERE member.rolname=current_user"
                ).fetchall()
                for (role_name,) in memberships:
                    bootstrap.execute(
                        sql.SQL("REVOKE {} FROM CURRENT_USER").format(
                            sql.Identifier(role_name)
                        )
                    )

            database_admin_dsn = make_conninfo(DSN, dbname=database_name)
            with psycopg.connect(database_admin_dsn, autocommit=True) as service_admin:
                # Managed providers may pre-install/enable this extension as
                # a provider operation before application migrations.
                service_admin.execute("CREATE EXTENSION timescaledb")

            migrator_dsn = make_conninfo(
                DSN,
                user="t0_migrator_login",
                password=migrator_password,
                dbname=database_name,
            )
            applied, total = migrate(migrator_dsn)
            self.assertEqual(applied, total)

            with psycopg.connect(database_admin_dsn, autocommit=True) as service_admin:
                schema_owner = service_admin.execute(
                    "SELECT owner.rolname FROM pg_namespace schema "
                    "JOIN pg_roles owner ON owner.oid=schema.nspowner "
                    "WHERE schema.nspname='market_data'"
                ).fetchone()
                self.assertEqual(schema_owner, ("t0_db_owner",))

                table_owners = service_admin.execute(
                    "SELECT tablename, tableowner FROM pg_tables "
                    "WHERE schemaname='market_data' "
                    "AND tablename IN ('candles','feeder_leases','instruments','schema_migrations') "
                    "ORDER BY tablename"
                ).fetchall()
                self.assertEqual(
                    table_owners,
                    [
                        ("candles", "t0_db_owner"),
                        ("feeder_leases", "t0_db_owner"),
                        ("instruments", "t0_db_owner"),
                        ("schema_migrations", "t0_db_owner"),
                    ],
                )

                role_flags = service_admin.execute(
                    "SELECT rolname, rolsuper, rolcanlogin, rolcreatedb, rolcreaterole, "
                    "rolreplication, rolbypassrls FROM pg_roles "
                    "WHERE rolname IN "
                    "('t0_db_owner','t0_migrator','t0_candle_writer_owner','t0_lease_manager_owner') "
                    "ORDER BY rolname"
                ).fetchall()
                self.assertEqual(
                    role_flags,
                    [
                        ("t0_candle_writer_owner", False, False, False, False, False, False),
                        ("t0_db_owner", False, False, False, False, False, False),
                        ("t0_lease_manager_owner", False, False, False, False, False, False),
                        ("t0_migrator", False, False, False, False, False, False),
                    ],
                )

                function_owners = service_admin.execute(
                    "SELECT p.proname, owner.rolname FROM pg_proc p "
                    "JOIN pg_roles owner ON owner.oid=p.proowner "
                    "WHERE p.proname IN "
                    "('write_canonical_candle','acquire_feeder_lease') "
                    "ORDER BY p.proname"
                ).fetchall()
                self.assertEqual(
                    function_owners,
                    [
                        ("acquire_feeder_lease", "t0_lease_manager_owner"),
                        ("write_canonical_candle", "t0_candle_writer_owner"),
                    ],
                )

                login_memberships = service_admin.execute(
                    "SELECT granted.rolname, membership.admin_option "
                    "FROM pg_auth_members membership "
                    "JOIN pg_roles granted ON granted.oid=membership.roleid "
                    "JOIN pg_roles member ON member.oid=membership.member "
                    "WHERE member.rolname='t0_migrator_login'"
                ).fetchall()
                self.assertEqual(login_memberships, [("t0_migrator", False)])

                unsafe_owner_memberships = service_admin.execute(
                    "SELECT granted.rolname, member.rolname "
                    "FROM pg_auth_members membership "
                    "JOIN pg_roles granted ON granted.oid=membership.roleid "
                    "JOIN pg_roles member ON member.oid=membership.member "
                    "WHERE granted.rolname IN "
                    "('t0_db_owner','t0_candle_writer_owner','t0_lease_manager_owner') "
                    "AND member.rolname <> 't0_migrator'"
                ).fetchall()
                self.assertEqual(unsafe_owner_memberships, [])

        finally:
            with psycopg.connect(DSN, autocommit=True) as service_admin:
                if database_created:
                    service_admin.execute(
                        sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(
                            sql.Identifier(database_name)
                        )
                    )
                # Dropping roles also removes their cluster-level memberships.
                for role_name in (
                    "t0_migrator_login",
                    "t0_migrator",
                    "t0_db_owner",
                    "t0_feeder_writer",
                    "t0_candle_writer_owner",
                    "t0_feeder_lease_manager",
                    "t0_lease_manager_owner",
                ):
                    service_admin.execute(
                        sql.SQL("DROP ROLE IF EXISTS {}").format(
                            sql.Identifier(role_name)
                        )
                    )
                if bootstrap_created:
                    service_admin.execute(
                        sql.SQL("DROP ROLE IF EXISTS {}").format(
                            sql.Identifier(bootstrap_role)
                        )
                    )


if __name__ == "__main__":
    unittest.main()
