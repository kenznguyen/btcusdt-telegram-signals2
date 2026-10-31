"""Apply versioned PostgreSQL schema migrations with checksum fail-closed behavior."""

import hashlib
import json
import os
from pathlib import Path


MIGRATIONS = Path(__file__).parent / "migrations"


class MigrationChecksumMismatch(RuntimeError):
    """An already-applied migration file was changed."""


def apply_schema_migrations(dsn):
    if not isinstance(dsn, str) or not dsn.strip():
        raise ValueError("PostgreSQL migration URL is required")
    try:
        import psycopg
    except ImportError as error:
        raise RuntimeError("Install psycopg to apply PostgreSQL migrations") from error

    files = sorted(MIGRATIONS.glob("*.sql"))
    if not files:
        raise RuntimeError("No market-data schema migrations were found")
    applied = []
    try:
        with psycopg.connect(dsn) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_advisory_xact_lock(0, hashtext(%s))",
                               ("market_data.schema_migrations",))
                for path in files:
                    sql = path.read_text(encoding="utf-8")
                    checksum = hashlib.sha256(sql.encode("utf-8")).hexdigest()
                    cursor.execute("SELECT to_regclass('market_data.schema_migrations')")
                    history_exists = cursor.fetchone()[0] is not None
                    if history_exists:
                        cursor.execute(
                            "SELECT checksum_sha256 FROM market_data.schema_migrations WHERE migration_id=%s",
                            (path.name,),
                        )
                        previous = cursor.fetchone()
                        if previous is not None:
                            if previous[0] != checksum:
                                raise MigrationChecksumMismatch(
                                    f"Applied migration checksum changed: {path.name}"
                                )
                            continue
                    cursor.execute(sql, prepare=False)
                    cursor.execute(
                        """INSERT INTO market_data.schema_migrations
                           (migration_id, checksum_sha256) VALUES (%s, %s)""",
                        (path.name, checksum),
                    )
                    applied.append(path.name)
        return applied
    except MigrationChecksumMismatch:
        raise
    except psycopg.Error as error:
        from market_data.repository import MarketDataRepositoryError
        raise MarketDataRepositoryError("PostgreSQL schema migration failed") from error


def main():
    dsn = os.environ.get("MARKET_DATA_DATABASE_URL", "")
    if not dsn:
        raise SystemExit("Set MARKET_DATA_DATABASE_URL in the environment; do not pass credentials as arguments.")
    print(json.dumps({"applied": apply_schema_migrations(dsn)}, separators=(",", ":")))


if __name__ == "__main__":
    main()
