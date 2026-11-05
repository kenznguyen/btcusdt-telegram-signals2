"""Explicit, immutable and checksum-verified PostgreSQL migrations."""

import hashlib
from pathlib import Path

from market_data.postgres import connection


MIGRATIONS = Path(__file__).with_name("migrations")


def _assert_writer_roles_safe(database):
    """Fail closed if reserved SECURITY DEFINER roles gain login/admin powers."""
    unsafe = database.execute(
        """SELECT rolname FROM pg_roles
           WHERE rolname IN ('t0_feeder_writer', 't0_candle_writer_owner',
                             't0_feeder_lease_manager', 't0_lease_manager_owner', 't0_migrator', 't0_db_owner')
             AND (rolsuper OR rolcanlogin OR rolcreatedb OR rolcreaterole
                  OR rolreplication OR rolbypassrls)
           ORDER BY rolname"""
    ).fetchall()
    if unsafe:
        role = unsafe[0][0]
        raise RuntimeError(f"{role} must remain a restricted NOLOGIN role")

    migrator_members = database.execute(
        """SELECT member_role.rolname
           FROM pg_auth_members membership
           JOIN pg_roles granted_role ON granted_role.oid = membership.roleid
           JOIN pg_roles member_role ON member_role.oid = membership.member
           WHERE granted_role.rolname = 't0_migrator'
             AND member_role.rolname <> 't0_migrator_login'
           ORDER BY member_role.rolname"""
    ).fetchall()
    if migrator_members:
        raise RuntimeError(
            "t0_migrator may only be granted to the ephemeral t0_migrator_login role"
        )

    migrator_group_exists = database.execute(
        "SELECT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 't0_migrator')"
    ).fetchone()[0]
    if migrator_group_exists:
        database_owner_exists = database.execute(
            "SELECT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 't0_db_owner')"
        ).fetchone()[0]
        if not database_owner_exists:
            raise RuntimeError("t0_db_owner must exist when restricted migrations are enabled")
        database_owner_membership = database.execute(
            """SELECT EXISTS (
                SELECT 1 FROM pg_auth_members membership
                JOIN pg_roles granted_role ON granted_role.oid = membership.roleid
                JOIN pg_roles member_role ON member_role.oid = membership.member
                WHERE granted_role.rolname = 't0_db_owner'
                  AND member_role.rolname = 't0_migrator'
            )"""
        ).fetchone()[0]
        if not database_owner_membership:
            raise RuntimeError("t0_migrator must be a member of t0_db_owner")

        ephemeral_login = database.execute(
            """SELECT rolcanlogin, rolsuper, rolcreatedb, rolcreaterole,
                      rolreplication, rolbypassrls
               FROM pg_roles WHERE rolname = 't0_migrator_login'"""
        ).fetchone()
        if ephemeral_login is None or not ephemeral_login[0] or any(ephemeral_login[1:]):
            raise RuntimeError(
                "t0_migrator_login must exist as a restricted LOGIN role"
            )

        login_members = database.execute(
            """SELECT member_role.rolname
               FROM pg_auth_members membership
               JOIN pg_roles granted_role ON granted_role.oid = membership.roleid
               JOIN pg_roles member_role ON member_role.oid = membership.member
               WHERE granted_role.rolname = 't0_migrator_login'
               ORDER BY member_role.rolname"""
        ).fetchall()
        if login_members:
            raise RuntimeError(
                "t0_migrator_login must not be granted to other roles"
            )

        login_grants = database.execute(
            """SELECT granted_role.rolname, membership.admin_option
               FROM pg_auth_members membership
               JOIN pg_roles granted_role ON granted_role.oid = membership.roleid
               JOIN pg_roles member_role ON member_role.oid = membership.member
               WHERE member_role.rolname = 't0_migrator_login'
               ORDER BY granted_role.rolname"""
        ).fetchall()
        if login_grants != [("t0_migrator", False)]:
            raise RuntimeError(
                "t0_migrator_login may only be a member of t0_migrator"
            )

    owner_grants = database.execute(
        """SELECT granted_role.rolname, member_role.rolname
           FROM pg_auth_members membership
           JOIN pg_roles granted_role ON granted_role.oid = membership.roleid
           JOIN pg_roles member_role ON member_role.oid = membership.member
           WHERE granted_role.rolname IN ('t0_db_owner', 't0_candle_writer_owner', 't0_lease_manager_owner')
             AND member_role.rolname <> 't0_migrator'
           ORDER BY granted_role.rolname, member_role.rolname"""
    ).fetchall()
    if owner_grants:
        owner, member = owner_grants[0]
        raise RuntimeError(
            f"{owner} must not be granted to runtime or login roles (found {member})"
        )

    migrator_owner_admin_options = database.execute(
        """SELECT granted_role.rolname
           FROM pg_auth_members membership
           JOIN pg_roles granted_role ON granted_role.oid = membership.roleid
           JOIN pg_roles member_role ON member_role.oid = membership.member
           WHERE member_role.rolname = 't0_migrator'
             AND granted_role.rolname IN ('t0_candle_writer_owner', 't0_lease_manager_owner')
             AND membership.admin_option
           ORDER BY granted_role.rolname"""
    ).fetchall()
    if migrator_owner_admin_options:
        raise RuntimeError(
            "t0_migrator must not have ADMIN OPTION on database or SECURITY DEFINER owner roles"
        )

    inherited = database.execute(
        """SELECT member_role.rolname
           FROM pg_auth_members membership
           JOIN pg_roles member_role ON member_role.oid = membership.member
           WHERE member_role.rolname IN ('t0_feeder_writer', 't0_candle_writer_owner',
                                       't0_feeder_lease_manager', 't0_lease_manager_owner')
           ORDER BY member_role.rolname"""
    ).fetchall()
    if inherited:
        role = inherited[0][0]
        raise RuntimeError(f"{role} must not inherit privileges from another role")


def migrate(location):
    """Apply pending SQL migrations. Never called implicitly by a read or write."""
    with connection(location) as database:
        _assert_writer_roles_safe(database)
        restricted_migrator = database.execute(
            "SELECT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 't0_migrator')"
        ).fetchone()[0]
        if restricted_migrator:
            database.execute("SET ROLE t0_migrator")
        database.execute("SELECT pg_advisory_xact_lock(hashtext('market_data.schema_migrations'))")
        database.execute("CREATE SCHEMA IF NOT EXISTS market_data")
        if restricted_migrator:
            database.execute("ALTER SCHEMA market_data OWNER TO t0_db_owner")
        database.execute("""CREATE TABLE IF NOT EXISTS market_data.schema_migrations (
            migration_id TEXT PRIMARY KEY,
            checksum_sha256 TEXT NOT NULL,
            applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )""")
        if restricted_migrator:
            database.execute("ALTER TABLE market_data.schema_migrations OWNER TO t0_db_owner")
        applied = dict(database.execute(
            "SELECT migration_id, checksum_sha256 FROM market_data.schema_migrations"
        ).fetchall())
        for path in sorted(MIGRATIONS.glob("[0-9][0-9][0-9]_*.sql")):
            content = path.read_text(encoding="utf-8")
            checksum = hashlib.sha256(content.encode("utf-8")).hexdigest()
            previous = applied.get(path.name)
            if previous is not None:
                if previous != checksum:
                    raise RuntimeError("Applied migration checksum mismatch")
                continue
            database.execute(content)
            if restricted_migrator:
                database.execute("""DO $ownership$
                DECLARE item RECORD;
                BEGIN
                    FOR item IN
                        SELECT tablename
                          FROM pg_tables
                         WHERE schemaname = 'market_data'
                           AND tableowner <> 't0_db_owner'
                    LOOP
                        EXECUTE format('ALTER TABLE market_data.%I OWNER TO t0_db_owner', item.tablename);
                    END LOOP;
                END;
                $ownership$;""")
            database.execute(
                "INSERT INTO market_data.schema_migrations (migration_id, checksum_sha256) VALUES (%s, %s)",
                (path.name, checksum),
            )
        _assert_writer_roles_safe(database)
    return len(applied), len(list(MIGRATIONS.glob("[0-9][0-9][0-9]_*.sql")))
