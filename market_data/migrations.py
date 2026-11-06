"""Explicit, immutable and checksum-verified PostgreSQL migrations."""

import hashlib
from pathlib import Path

from market_data.postgres import connection


MIGRATIONS = Path(__file__).with_name("migrations")


def migrate(location):
    """Apply pending SQL migrations. Never called implicitly by a read or write."""
    with connection(location) as database:
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
    return len(applied), len(list(MIGRATIONS.glob("[0-9][0-9][0-9]_*.sql")))
