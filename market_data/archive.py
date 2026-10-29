"""Bounded, immutable T1 snapshot archive for SQLite or PostgreSQL."""

from contextlib import closing, contextmanager
import json
from pathlib import Path
import sqlite3

from futures_intelligence.import_collector import validate_snapshot
from market_data import store


MAX_SNAPSHOT_BYTES = 64 * 1024
MAX_ARCHIVE_ROWS = 10_000
MAX_QUERY_BYTES = 8 * 1024 * 1024


@contextmanager
def _connection(location, *, write=False, initialize=False):
    if store.is_postgres(location):
        from market_data.postgres import connection
        with connection(location, read_only=not write) as database:
            yield database, "%s", "octet_length(document)"
        return
    path = Path(location).resolve()
    if initialize:
        path.parent.mkdir(parents=True, exist_ok=True)
    elif not path.is_file():
        raise store.StoreUnavailable("Snapshot archive is unavailable")
    mode = "rwc" if initialize else "rw" if write else "ro"
    try:
        with closing(sqlite3.connect(path.as_uri() + "?mode=" + mode, uri=True, timeout=5)) as database, database:
            database.execute("BEGIN IMMEDIATE" if write else "BEGIN")
            yield database, "?", "length(CAST(document AS BLOB))"
    except sqlite3.Error:
        raise store.StoreUnavailable("Snapshot archive is unavailable") from None


def init_archive(location):
    """Create archive schema explicitly. Reads and inserts never initialize it."""
    with _connection(location, write=True, initialize=True) as (database, _, __):
        database.execute("""CREATE TABLE IF NOT EXISTS intelligence_snapshots (
            snapshot_id TEXT PRIMARY KEY, available_at_ms BIGINT NOT NULL,
            window_end_ms BIGINT NOT NULL, document TEXT NOT NULL)""")
        database.execute("""CREATE INDEX IF NOT EXISTS intelligence_snapshot_availability
            ON intelligence_snapshots(available_at_ms, snapshot_id)""")


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate snapshot JSON key")
        result[key] = value
    return result


def _decode(document, now_ms):
    if not isinstance(document, str) or len(document.encode("utf-8")) > MAX_SNAPSHOT_BYTES:
        raise ValueError("Snapshot exceeds document limit")
    try:
        snapshot = json.loads(document, object_pairs_hook=_unique)
        validate_snapshot(snapshot, now_ms)
    except (ValueError, KeyError, TypeError, OverflowError, RecursionError):
        raise ValueError("Invalid archived snapshot") from None
    return snapshot


def archive_snapshot(location, snapshot, now_ms):
    """Validate and insert once, retaining the original artifact and availability."""
    store._integer(now_ms)
    try:
        document = json.dumps(snapshot, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    except (ValueError, TypeError, OverflowError, RecursionError):
        raise ValueError("Invalid snapshot JSON") from None
    value = _decode(document, now_ms)
    params = (value["snapshotId"], value["availableAtMs"], value["windowEndMs"], document)
    with _connection(location, write=True) as (database, marker, length):
        placeholders = ",".join([marker] * 4)
        inserted = database.execute(f"""INSERT INTO intelligence_snapshots
            (snapshot_id,available_at_ms,window_end_ms,document) VALUES ({placeholders})
            ON CONFLICT(snapshot_id) DO NOTHING""", params).rowcount
        if inserted == 1:
            return True
        # Read the existing length before fetching an at-rest document.
        existing_size = database.execute(f"SELECT {length} FROM intelligence_snapshots WHERE snapshot_id={marker}",
                                         (value["snapshotId"],)).fetchone()
        if existing_size is None or existing_size[0] > MAX_SNAPSHOT_BYTES:
            raise ValueError("Conflicting archived snapshot")
        previous = database.execute(f"""SELECT snapshot_id,available_at_ms,window_end_ms,document
            FROM intelligence_snapshots WHERE snapshot_id={marker}""", (value["snapshotId"],)).fetchone()
        if tuple(previous) != params:
            raise ValueError("Conflicting archived snapshot")
        return False


def read_snapshots(location, start_ms, end_ms, as_of_ms):
    """Read observations in inclusive availability bounds without truncation."""
    start, end, asof = (store._integer(value) for value in (start_ms, end_ms, as_of_ms))
    if start > end:
        raise ValueError("Snapshot query has reversed bounds")
    upper = min(end, asof)
    if upper < start:
        return []
    with _connection(location) as (database, marker, length):
        where = f"available_at_ms>={marker} AND available_at_ms<={marker} AND window_end_ms<={marker}"
        params = (start, upper, end)
        count, total, largest = database.execute(f"""SELECT COUNT(*),COALESCE(SUM({length}),0),
            COALESCE(MAX({length}),0) FROM intelligence_snapshots WHERE {where}""", params).fetchone()
        if count > MAX_ARCHIVE_ROWS or total > MAX_QUERY_BYTES or largest > MAX_SNAPSHOT_BYTES:
            raise ValueError("Snapshot query exceeds archive limits")
        rows = database.execute(f"""SELECT snapshot_id,available_at_ms,window_end_ms,document
            FROM intelligence_snapshots WHERE {where} ORDER BY available_at_ms,snapshot_id""", params).fetchall()
        result = []
        for identifier, available, window_end, document in rows:
            snapshot = _decode(document, asof)
            if (identifier, available, window_end) != (snapshot["snapshotId"], snapshot["availableAtMs"], snapshot["windowEndMs"]):
                raise ValueError("Archived snapshot metadata mismatch")
            result.append(snapshot)
        return result
