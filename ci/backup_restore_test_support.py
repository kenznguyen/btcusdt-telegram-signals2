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
from contextlib import closing
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
        with closing(_readonly_connection(database)) as connection:
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
        with closing(_readonly_connection(source_path)) as source_db:
            with closing(sqlite3.connect(destination_path, timeout=10)) as destination_db:
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
        # The backup image can inherit WAL mode from its source. Before
        # atomically renaming the staged file, checkpoint and switch it to
        # DELETE mode so no temporary-name -wal/-shm files are orphaned.
        with closing(sqlite3.connect(temporary_path, timeout=10)) as publication_db:
            checkpoint = publication_db.execute(
                "PRAGMA wal_checkpoint(TRUNCATE)"
            ).fetchone()
            if checkpoint is not None and checkpoint[0] != 0:
                raise BackupVerificationError("Staged backup WAL checkpoint is busy")
            journal_mode = publication_db.execute(
                "PRAGMA journal_mode=DELETE"
            ).fetchone()
            if journal_mode is None or journal_mode[0].lower() != "delete":
                raise BackupVerificationError("Staged backup could not leave WAL mode")
        for suffix in ("-wal", "-shm"):
            Path(str(temporary_path) + suffix).unlink(missing_ok=True)

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
    """Validate a versioned coordination manifest without claiming atomicity."""
    required_manifest_keys = {
        "manifest_version", "topology", "snapshot_barrier_id", "restore_epoch", "stores",
    }
    if not isinstance(manifest, dict) or set(manifest) != required_manifest_keys:
        raise BackupVerificationError("Split-store manifest is incomplete or has unknown fields")
    if type(manifest["manifest_version"]) is not int or manifest["manifest_version"] != 1:
        raise BackupVerificationError("Unsupported split-store manifest version")
    if manifest["topology"] != "split_store":
        raise BackupVerificationError("A split_store manifest is required")

    barrier = manifest["snapshot_barrier_id"]
    epoch = manifest["restore_epoch"]
    stores = manifest["stores"]
    if not isinstance(barrier, str) or not barrier.strip():
        raise BackupVerificationError("A shared snapshot barrier ID is required")
    if type(epoch) is not int or epoch < 1:
        raise BackupVerificationError("A positive monotonic restore epoch is required")
    if not isinstance(stores, dict) or set(stores) != {"market_data", "paper_ledger"}:
        raise BackupVerificationError("Both split-store snapshots are required")

    required_store_keys = {
        "barrier_id", "snapshot_id", "high_water_mark", "schema_version",
        "content_sha256", "logical_sha256", "table_counts",
    }
    for name, snapshot in stores.items():
        if not isinstance(snapshot, dict) or set(snapshot) != required_store_keys:
            raise BackupVerificationError(f"{name} snapshot metadata is incomplete or has unknown fields")
        if snapshot["barrier_id"] != barrier:
            raise BackupVerificationError("Split-store snapshots do not share the same barrier")
        snapshot_id = snapshot["snapshot_id"]
        high_water = snapshot["high_water_mark"]
        schema_version = snapshot["schema_version"]
        content_hash = snapshot["content_sha256"]
        logical_hash = snapshot["logical_sha256"]
        table_counts = snapshot["table_counts"]
        if not isinstance(snapshot_id, str) or len(snapshot_id) != 64:
            raise BackupVerificationError(f"{name} snapshot ID must be a logical SHA-256")
        if not isinstance(content_hash, str) or len(content_hash) != 64:
            raise BackupVerificationError(f"{name} content SHA-256 is invalid")
        if not isinstance(logical_hash, str) or len(logical_hash) != 64 or snapshot_id != logical_hash:
            raise BackupVerificationError(f"{name} logical snapshot identity is invalid")
        if any(ch not in "0123456789abcdef" for ch in snapshot_id + content_hash):
            raise BackupVerificationError(f"{name} snapshot digest is not lowercase hexadecimal")
        if not isinstance(table_counts, dict) or not table_counts:
            raise BackupVerificationError(f"{name} table counts are missing")
        if any(not isinstance(table, str) or type(count) is not int or count < 0
               for table, count in table_counts.items()):
            raise BackupVerificationError(f"{name} table counts contain invalid values")
        if type(high_water) is not int or high_water < 0 or high_water != sum(table_counts.values()):
            raise BackupVerificationError(f"{name} high-water mark does not match table counts")
        if type(schema_version) is not int or schema_version < 1:
            raise BackupVerificationError(f"{name} schema version is invalid")

    return {
        "status": "PASS",
        "manifest_version": manifest["manifest_version"],
        "restore_epoch": epoch,
        "snapshot_barrier_id": barrier,
        "stores": sorted(stores),
        "schema_versions": {name: stores[name]["schema_version"] for name in sorted(stores)},
        "atomicity_claim": "NOT_ESTABLISHED_BY_MANIFEST",
    }


def derive_snapshot_identity(path, *, root):
    """Derive fixture identity, schema version and row-count high-water mark."""
    report = inspect_database(path, root=root)
    database = _safe_path(path, root, must_exist=True)
    with closing(_readonly_connection(database)) as connection:
        schema_version = connection.execute("PRAGMA user_version").fetchone()[0]
    if type(schema_version) is not int or schema_version < 1:
        raise BackupVerificationError("Fixture database PRAGMA user_version must be positive")
    table_counts = report["table_counts"]
    return {
        "logical_sha256": report["logical_sha256"],
        "table_counts": table_counts,
        "high_water_mark": sum(table_counts.values()),
        "schema_version": schema_version,
    }


def verify_split_store_backup_set(destination, *, root):
    """Read-only verification binding manifest fields to both actual DB images."""
    root_path = _fixture_root(root)
    directory = _safe_path(destination, root_path, must_exist=False)
    if not directory.exists() or not directory.is_dir():
        raise BackupVerificationError("Split-store backup set must be a directory")
    expected_files = {"market_data.sqlite3", "paper_ledger.sqlite3", "backup-manifest.json"}
    actual_files = {item.name for item in directory.iterdir()}
    if actual_files != expected_files:
        raise BackupVerificationError("Split-store backup set has missing or unexpected files")
    try:
        manifest = json.loads((directory / "backup-manifest.json").read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError) as exc:
        raise BackupVerificationError("Split-store manifest cannot be read") from exc
    manifest_report = validate_split_store_manifest(manifest)
    verified = {}
    for name in ("market_data", "paper_ledger"):
        database = directory / f"{name}.sqlite3"
        metadata = manifest["stores"][name]
        identity = derive_snapshot_identity(database, root=root_path)
        content_hash = hashlib.sha256(database.read_bytes()).hexdigest()
        if metadata["snapshot_id"] != identity["logical_sha256"]:
            raise BackupVerificationError(f"{name} snapshot ID does not match database contents")
        if metadata["logical_sha256"] != identity["logical_sha256"]:
            raise BackupVerificationError(f"{name} logical hash does not match database contents")
        if metadata["content_sha256"] != content_hash:
            raise BackupVerificationError(f"{name} content hash does not match database image")
        if metadata["high_water_mark"] != identity["high_water_mark"]:
            raise BackupVerificationError(f"{name} high-water mark does not match database rows")
        if metadata["schema_version"] != identity["schema_version"]:
            raise BackupVerificationError(f"{name} schema version does not match PRAGMA user_version")
        if metadata["table_counts"] != identity["table_counts"]:
            raise BackupVerificationError(f"{name} table counts do not match database contents")
        verified[name] = {
            "logical_sha256": identity["logical_sha256"],
            "content_sha256": content_hash,
            "high_water_mark": identity["high_water_mark"],
            "schema_version": identity["schema_version"],
            "table_counts": identity["table_counts"],
        }
    return {
        "status": "PASS",
        "manifest": manifest_report,
        "stores": verified,
    }


def publish_split_store_backup_set(
    sources, destination, *, root, snapshot_barrier_id, restore_epoch,
    snapshot_metadata, required_tables=(), required_rows=None, fail_after_store=None,
):
    """Fixture-only staged publication for two SQLite snapshots.

    The helper exercises failure cleanup and one-directory publication semantics
    on the CI filesystem. It is not a production multi-store backup coordinator
    and does not establish cross-database snapshot atomicity.
    """
    fixture_root = _fixture_root(root)
    destination_path = _safe_path(destination, fixture_root, must_exist=False)
    if destination_path.exists():
        raise FileExistsError(destination_path)
    if not destination_path.parent.is_dir():
        raise BackupVerificationError("Split-store publication parent must already exist")
    expected_stores = {"market_data", "paper_ledger"}
    if not isinstance(sources, dict) or set(sources) != expected_stores:
        raise BackupVerificationError("Both approved split-store sources are required")
    if not isinstance(snapshot_metadata, dict) or set(snapshot_metadata) != expected_stores:
        raise BackupVerificationError("Metadata for both approved stores is required")
    if fail_after_store not in (None, "market_data", "paper_ledger"):
        raise BackupVerificationError("Unknown fixture failure-injection point")

    manifest = {
        "manifest_version": 1,
        "topology": "split_store",
        "snapshot_barrier_id": snapshot_barrier_id,
        "restore_epoch": restore_epoch,
        "stores": snapshot_metadata,
    }
    staging_path = Path(tempfile.mkdtemp(
        prefix=".split-stage-", dir=destination_path.parent,
    ))
    try:
        bound_stores = {}
        for name in ("market_data", "paper_ledger"):
            staged_backup = staging_path / f"{name}.sqlite3"
            atomic_backup(
                sources[name], staged_backup, root=fixture_root,
                required_tables=required_tables, required_rows=required_rows,
            )
            identity = derive_snapshot_identity(staged_backup, root=fixture_root)
            expected = snapshot_metadata[name]
            if expected["barrier_id"] != snapshot_barrier_id:
                raise BackupVerificationError(f"{name} snapshot barrier metadata mismatch")
            for field in ("snapshot_id", "high_water_mark", "schema_version"):
                if expected[field] != identity[
                    "logical_sha256" if field == "snapshot_id" else field
                ]:
                    raise BackupVerificationError(f"{name} {field} does not match backup contents")
            bound_stores[name] = {
                "barrier_id": snapshot_barrier_id,
                "snapshot_id": identity["logical_sha256"],
                "logical_sha256": identity["logical_sha256"],
                "content_sha256": hashlib.sha256(staged_backup.read_bytes()).hexdigest(),
                "high_water_mark": identity["high_water_mark"],
                "schema_version": identity["schema_version"],
                "table_counts": identity["table_counts"],
            }
            if fail_after_store == name:
                raise RuntimeError("injected partial split-store failure")

        manifest["stores"] = bound_stores
        validate_split_store_manifest(manifest)
        manifest_path = staging_path / "backup-manifest.json"
        manifest_path.write_text(
            json.dumps(manifest, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
        os.replace(staging_path, destination_path)
        return {
            "status": "PASS",
            "destination": str(destination_path),
            "stores": ["market_data", "paper_ledger"],
            "manifest": manifest,
            "atomicity_claim": "FIXTURE_DIRECTORY_PUBLICATION_ONLY",
        }
    except Exception:
        import shutil
        shutil.rmtree(staging_path, ignore_errors=True)
        raise
