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
                             't0_feeder_lease_manager', 't0_lease_manager_owner', 't0_migrator')
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

    owner_grants = database.execute(
        """SELECT granted_role.rolname, member_role.rolname
           FROM pg_auth_members membership
           JOIN pg_roles granted_role ON granted_role.oid = membership.roleid
           JOIN pg_roles member_role ON member_role.oid = membership.member
           WHERE granted_role.rolname IN ('t0_candle_writer_owner', 't0_lease_manager_owner')
             AND member_role.rolname <> 't0_migrator'
           ORDER BY granted_role.rolname, member_role.rolname"""
    ).fetchall()
    if owner_grants:
        owner, member = owner_grants[0]
        raise RuntimeError(
            f"{owner} must not be granted to runtime or login roles (found {member})"
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
        database.execute("SELECT pg_advisory_xact_lock(hashtext('market_data.schema_migrations'))")
        database.execute("CREATE SCHEMA IF NOT EXISTS market_data")
        database.execute("""CREATE TABLE IF NOT EXISTS market_data.schema_migrations (
            migration_id TEXT PRIMARY KEY,
            checksum_sha256 TEXT NOT NULL,
            applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )""")
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
            database.execute(
                "INSERT INTO market_data.schema_migrations (migration_id, checksum_sha256) VALUES (%s, %s)",
                (path.name, checksum),
            )
        _assert_writer_roles_safe(database)
    return len(applied), len(list(MIGRATIONS.glob("[0-9][0-9][0-9]_*.sql")))
