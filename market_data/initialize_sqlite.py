"""Explicit, empty-only initializer for the local T0 Canonical SQLite database."""

import argparse
import json
import os
from contextlib import closing
from pathlib import Path
import sqlite3

from market_data.store import CandleStore


def _initialize_schema(path):
    CandleStore(path)
    with closing(sqlite3.connect(path, timeout=5)) as database:
        database.execute("""CREATE TABLE feeder_leases (
            lease_name TEXT PRIMARY KEY,
            owner TEXT,
            generation INTEGER NOT NULL CHECK(generation >= 0),
            expires_at_ms INTEGER NOT NULL CHECK(expires_at_ms >= 0)
        )""")
        database.execute("PRAGMA user_version = 1")
        database.commit()
        integrity = database.execute("PRAGMA integrity_check").fetchone()[0]
        if integrity != "ok":
            raise RuntimeError("SQLite integrity check failed")
        candles = database.execute("SELECT COUNT(*) FROM candles").fetchone()[0]
        leases = database.execute("SELECT COUNT(*) FROM feeder_leases").fetchone()[0]
        if candles != 0 or leases != 0:
            raise RuntimeError("New Canonical database must remain empty")


def create_canonical_database(db_path, *, initializer=None):
    """Create a brand-new empty DB; never open, migrate or overwrite an existing path."""
    target = Path(db_path).expanduser()
    if target.exists() or target.is_symlink():
        raise FileExistsError("Refusing to overwrite an existing Canonical DB path")
    target.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    descriptor = os.open(target, flags, 0o600)
    os.close(descriptor)
    try:
        (initializer or _initialize_schema)(target)
        with closing(sqlite3.connect(target.resolve().as_uri() + "?mode=ro", uri=True, timeout=5)) as database:
            tables = {row[0] for row in database.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )}
            if tables != {"candles", "feeder_leases"}:
                raise RuntimeError("Unexpected Canonical SQLite schema")
            if database.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise RuntimeError("SQLite integrity check failed")
            candles = database.execute("SELECT COUNT(*) FROM candles").fetchone()[0]
            leases = database.execute("SELECT COUNT(*) FROM feeder_leases").fetchone()[0]
            if candles or leases:
                raise RuntimeError("Canonical database initialization must not ingest data")
        return {
            "created": True,
            "database": str(target.resolve()),
            "schemaVersion": 1,
            "tables": ["candles", "feeder_leases"],
            "candles": 0,
            "leases": 0,
            "integrity": "ok",
            "feederStarted": False,
            "ingestionStarted": False,
        }
    except Exception:
        for candidate in (target, Path(str(target) + "-wal"), Path(str(target) + "-shm")):
            try:
                candidate.unlink(missing_ok=True)
            except OSError:
                pass
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", default=".data/market-data.sqlite3")
    parser.add_argument(
        "--confirm-create", action="store_true", required=True,
        help="Explicitly confirm creation of a new empty Canonical SQLite database",
    )
    args = parser.parse_args()
    try:
        report = create_canonical_database(args.db)
    except (OSError, ValueError, RuntimeError, sqlite3.Error) as error:
        parser.exit(1, f"Canonical DB initialization failed ({type(error).__name__}).\\n")
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
