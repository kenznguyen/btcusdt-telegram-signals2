"""Isolated SQLite backup/restore test helpers.

This module is CI test support, not a production backup utility. All paths must
remain below an explicitly supplied disposable fixture root.
"""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import tempfile
from pathlib import Path


FIXTURE_ROOT_PREFIX = "p5_4_9_backup_restore_"


class BackupVerificationError(RuntimeError):
    """A fixture path, SQLite image, manifest, or restored state failed closed."""


def _fixture_root(root):
    raw = Path(root)
    if raw.is_symlink():
        raise BackupVerificationError("Fixture root must not be a symlink")
    try:
        resolved = raw.resolve(strict=True)
    except OSError as exc:
        raise BackupVerificationError("Fixture root is unavailable") from exc
    if not resolved.is_dir() or not resolved.name.startswith(FIXTURE_ROOT_PREFIX):
        raise BackupVerificationError("Operation is restricted to a disposable P5.4.9 fixture root")
    return resolved


def _safe_path(path, root, *, must_exist=False):
    fixture_root = _fixture_root(root)
    raw = Path(path)
    candidate = raw if raw.is_absolute() else fixture_root / raw

    # Reject symlink components before resolving. This prevents a path that
    # appears below the fixture root from redirecting outside it.
    try:
        relative = candidate.relative_to(fixture_root) if candidate.is_absolute() else candidate
    except ValueError:
        relative = candidate
    if candidate.is_absolute():
        try:
            relative = candidate.relative_to(fixture_root)
        except ValueError as exc:
            raise BackupVerificationError("Path escapes the disposable fixture root") from exc
    current = fixture_root
    for part in relative.parts:
        if part in ("", "."):
            continue
        if part == "..":
            raise BackupVerificationError("Path escapes the disposable fixture root")
        current = current / part
        if current.is_symlink():
            raise BackupVerificationError("Symlink paths are not permitted in fixture operations")

    resolved = candidate.resolve(strict=must_exist)
    try:
        resolved.relative_to(fixture_root)
    except ValueError as exc:
        raise BackupVerificationError("Resolved path escapes the disposable fixture root") from exc
    if must_exist and not resolved.is_file():
        raise BackupVerificationError("Expected fixture database file is unavailable")
    return resolved


def _readonly_connection(path):
    return sqlite3.connect(path.as_uri() + "?mode=ro", uri=True, timeout=10)


def _json_value(value):
    if isinstance(value, bytes):
        return {"__bytes_hex__": value.hex()}
    return value


def _canonical_rows(rows):
    values = [[_json_value(value) for value in row] for row in rows]
    return sorted(values, key=lambda row: json.dumps(row, sort_keys=True, separators=(",", ":")))


def inspect_database(path, *, root, required_tables=(), required_rows=None):
    """Inspect a fixture DB through SQLite mode=ro; never initialize or repair it."""
    database = _safe_path(path, root, must_exist=True)
    required_rows = {} if required_rows is None else dict(required_rows)
    try:
        with _readonly_connection(database) as connection:
            connection.execute("PRAGMA query_only=ON")
            integrity = connection.execute("PRAGMA integrity_check").fetchone()
            if integrity is None or integrity[0] != "ok":
                raise BackupVerificationError("SQLite integrity_check did not return ok")
            fk_violations = connection.execute("PRAGMA foreign_key_check").fetchall()
            if fk_violations:
                raise BackupVerificationError("SQLite foreign_key_check reported violations")

            table_names = sorted(row[0] for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ))
            missing = sorted(set(required_tables) - set(table_names))
            if missing:
                raise BackupVerificationError("Required tables are missing: " + ", ".join(missing))

            for table, (column, value) in required_rows.items():
                if table not in table_names:
                    raise BackupVerificationError(f"Required singleton table is missing: {table}")
                quoted_table = '"' + table.replace('"', '""') + '"'
                quoted_column = '"' + column.replace('"', '""') + '"'
                row = connection.execute(
                    f"SELECT 1 FROM {quoted_table} WHERE {quoted_column}=? LIMIT 1", (value,)
                ).fetchone()
                if row is None:
                    raise BackupVerificationError(f"Required state row is missing: {table}.{column}={value}")

            projection = {}
            table_counts = {}
            for table in table_names:
                quoted = '"' + table.replace('"', '""') + '"'
                ddl_row = connection.execute(
                    "SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (table,)
                ).fetchone()
                rows = connection.execute(f"SELECT * FROM {quoted}").fetchall()
                projection[table] = {
                    "ddl": ddl_row[0] if ddl_row else None,
                    "rows": _canonical_rows(rows),
                }
                table_counts[table] = len(rows)

            objects = sorted(
                [list(row) for row in connection.execute(
                    """SELECT type,name,tbl_name,sql FROM sqlite_master
                       WHERE type IN ('index','trigger') AND name NOT LIKE 'sqlite_%'
                       ORDER BY type,name,tbl_name"""
                )],
                key=lambda row: (row[0], row[1], row[2]),
            )
            canonical = json.dumps(
                {"tables": projection, "objects": objects},
                sort_keys=True, separators=(",", ":"), ensure_ascii=False,
            ).encode("utf-8")
            digest = hashlib.sha256(canonical).hexdigest()
            return {
                "status": "PASS",
                "database": str(database),
                "table_names": table_names,
                "table_counts": table_counts,
                "integrity_check": integrity[0],
                "foreign_key_violations": len(fk_violations),
                "logical_sha256": digest,
            }
    except BackupVerificationError:
        raise
    except (sqlite3.DatabaseError, OSError, ValueError, TypeError) as exc:
        raise BackupVerificationError(f"Database inspection failed closed: {type(exc).__name__}") from exc


def create_online_backup(source, destination, *, root, required_tables=(), required_rows=None):
    """Create a SQLite Online Backup API image inside the fixture root."""
    source_path = _safe_path(source, root, must_exist=True)
    destination_path = _safe_path(destination, root, must_exist=False)
    if source_path == destination_path:
        raise BackupVerificationError("Source and backup destination must differ")
    if destination_path.exists():
        raise FileExistsError(destination_path)
    if not destination_path.parent.is_dir():
        raise BackupVerificationError("Backup destination parent must already exist")
    try:
        with _readonly_connection(source_path) as source_db:
            with sqlite3.connect(destination_path, timeout=10) as destination_db:
                source_db.backup(destination_db, pages=128, sleep=0.01)
                destination_db.commit()
        # A successful API return is not enough; validate the completed image.
        inspect_database(
            destination_path, root=root,
            required_tables=required_tables, required_rows=required_rows,
        )
        return destination_path
    except Exception:
        try:
            destination_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise


def verify_backup(source, backup, *, root, required_tables=(), required_rows=None):
    source_report = inspect_database(
        source, root=root, required_tables=required_tables, required_rows=required_rows,
    )
    backup_report = inspect_database(
        backup, root=root, required_tables=required_tables, required_rows=required_rows,
    )
    if source_report["logical_sha256"] != backup_report["logical_sha256"]:
        raise BackupVerificationError("Backup logical projection differs from source")
    return {
        "status": "PASS",
        "source_logical_sha256": source_report["logical_sha256"],
        "backup_logical_sha256": backup_report["logical_sha256"],
        "table_counts": backup_report["table_counts"],
        "integrity_check": backup_report["integrity_check"],
        "foreign_key_violations": backup_report["foreign_key_violations"],
    }


def atomic_backup(source, destination, *, root, required_tables=(), required_rows=None):
    """Stage, verify, and atomically publish a new fixture backup in one directory."""
    destination_path = _safe_path(destination, root, must_exist=False)
    if destination_path.exists():
        raise FileExistsError(destination_path)
    if not destination_path.parent.is_dir():
        raise BackupVerificationError("Publication directory must already exist")
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=".backup-stage-", suffix=".sqlite3", dir=destination_path.parent,
    )
    os.close(descriptor)
    temporary_path = Path(temporary_name)
    temporary_path.unlink()
    try:
        create_online_backup(
            source, temporary_path, root=root,
            required_tables=required_tables, required_rows=required_rows,
        )
        result = verify_backup(
            source, temporary_path, root=root,
            required_tables=required_tables, required_rows=required_rows,
        )
        os.replace(temporary_path, destination_path)
        return result
    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise


def validate_split_store_manifest(manifest):
    """Validate coordination metadata without claiming cross-database atomicity."""
    if not isinstance(manifest, dict) or manifest.get("topology") != "split_store":
        raise BackupVerificationError("A split_store manifest is required")
    barrier = manifest.get("snapshot_barrier_id")
    epoch = manifest.get("restore_epoch")
    stores = manifest.get("stores")
    if not isinstance(barrier, str) or not barrier.strip():
        raise BackupVerificationError("A shared snapshot barrier ID is required")
    if type(epoch) is not int or epoch < 1:
        raise BackupVerificationError("A positive monotonic restore epoch is required")
    if not isinstance(stores, dict) or set(stores) != {"market_data", "paper_ledger"}:
        raise BackupVerificationError("Both split-store snapshots are required")
    for name, snapshot in stores.items():
        if not isinstance(snapshot, dict):
            raise BackupVerificationError(f"Invalid {name} snapshot metadata")
        if snapshot.get("barrier_id") != barrier:
            raise BackupVerificationError("Split-store snapshots do not share the same barrier")
        snapshot_id = snapshot.get("snapshot_id")
        high_water = snapshot.get("high_water_mark")
        if not isinstance(snapshot_id, str) or not snapshot_id.strip():
            raise BackupVerificationError(f"{name} snapshot ID is missing")
        if type(high_water) is not int or high_water < 0:
            raise BackupVerificationError(f"{name} high-water mark is invalid")
    return {
        "status": "PASS",
        "restore_epoch": epoch,
        "snapshot_barrier_id": barrier,
        "stores": sorted(stores),
        "atomicity_claim": "NOT_ESTABLISHED_BY_MANIFEST",
    }
