"""P5.4.9 fixture-only Backup/Restore contract tests.

Every database is created under a per-test TemporaryDirectory. The suite must
never read a runtime-selected DB path, connect to an exchange, or start a worker.
"""
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from paper_execution.shadow_migration_fixture import (
    FIXED_NOW_MS, PAPER_TABLES, build_legacy_fixture,
)
from backup_restore_test_support import (
    BackupVerificationError,
    create_online_backup,
    inspect_database,
    atomic_backup,
    verify_backup,
    validate_split_store_manifest,
)

REQUIRED_TABLES = (
    "candles", "feeder_leases", "feeder_runtime_status",
    *PAPER_TABLES, "paper_control_budget",
)
REQUIRED_ROWS = {
    "paper_state": ("id", 1),
    "paper_strategy_state": ("id", 1),
    "paper_risk_control": ("id", 1),
    "paper_account_config": ("id", 1),
}


class BackupRestoreFixtureTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="p5_4_9_backup_restore_")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "source" / "fixture.sqlite3"
        self.source.parent.mkdir()
        self.fixture = build_legacy_fixture(self.source)
        self.backups = self.root / "backups"
        self.backups.mkdir()

    def backup(self, name="snapshot.sqlite3"):
        destination = self.backups / name
        create_online_backup(
            self.source, destination, root=self.root,
            required_tables=REQUIRED_TABLES, required_rows=REQUIRED_ROWS,
        )
        return destination

    def test_fixture_contains_all_four_logical_domains(self):
        report = inspect_database(
            self.source, root=self.root,
            required_tables=REQUIRED_TABLES, required_rows=REQUIRED_ROWS,
        )
        self.assertEqual(report["status"], "PASS")
        self.assertTrue({"candles", "feeder_leases"}.issubset(report["table_names"]))
        self.assertTrue(set(PAPER_TABLES).issubset(report["table_names"]))
        self.assertEqual(report["integrity_check"], "ok")
        self.assertEqual(report["foreign_key_violations"], 0)
        self.assertEqual(self.fixture["fixed_now_ms"], FIXED_NOW_MS)

    def test_online_backup_preserves_schema_rows_and_domain_state(self):
        destination = self.backup()
        result = verify_backup(
            self.source, destination, root=self.root,
            required_tables=REQUIRED_TABLES, required_rows=REQUIRED_ROWS,
        )
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["source_logical_sha256"], result["backup_logical_sha256"])
        self.assertEqual(result["table_counts"]["paper_audit"], 5)
        self.assertEqual(result["table_counts"]["candles"], 18)

    def test_wal_backup_excludes_uncommitted_writer_transaction(self):
        writer = sqlite3.connect(self.source, timeout=5)
        self.addCleanup(writer.close)
        writer.execute("BEGIN IMMEDIATE")
        writer.execute(
            "INSERT INTO paper_audit(at_ms,kind,document) VALUES (?,?,?)",
            (FIXED_NOW_MS + 99, "UNCOMMITTED_SENTINEL", json.dumps({"pending": True})),
        )

        snapshot = self.backup("during-writer.sqlite3")
        with sqlite3.connect(snapshot) as db:
            count = db.execute(
                "SELECT COUNT(*) FROM paper_audit WHERE kind='UNCOMMITTED_SENTINEL'"
            ).fetchone()[0]
        self.assertEqual(count, 0)

        writer.commit()
        committed = self.backup("after-commit.sqlite3")
        with sqlite3.connect(committed) as db:
            count = db.execute(
                "SELECT COUNT(*) FROM paper_audit WHERE kind='UNCOMMITTED_SENTINEL'"
            ).fetchone()[0]
        self.assertEqual(count, 1)

    def test_read_only_verifier_does_not_mutate_source(self):
        before = inspect_database(
            self.source, root=self.root,
            required_tables=REQUIRED_TABLES, required_rows=REQUIRED_ROWS,
        )
        with self.assertRaises(sqlite3.OperationalError):
            with sqlite3.connect(self.source.as_uri() + "?mode=ro", uri=True) as db:
                db.execute("DELETE FROM paper_audit")
        after = inspect_database(
            self.source, root=self.root,
            required_tables=REQUIRED_TABLES, required_rows=REQUIRED_ROWS,
        )
        self.assertEqual(before["source_logical_sha256"], after["source_logical_sha256"])

    def test_missing_required_table_fails_closed(self):
        damaged = self.backups / "missing-table.sqlite3"
        create_online_backup(self.source, damaged, root=self.root)
        with sqlite3.connect(damaged) as db:
            db.execute("DROP TABLE paper_strategy_state")
        with self.assertRaises(BackupVerificationError):
            inspect_database(
                damaged, root=self.root,
                required_tables=REQUIRED_TABLES, required_rows=REQUIRED_ROWS,
            )

    def test_missing_required_singleton_row_fails_closed(self):
        damaged = self.backups / "missing-risk-row.sqlite3"
        create_online_backup(self.source, damaged, root=self.root)
        with sqlite3.connect(damaged) as db:
            db.execute("DELETE FROM paper_risk_control WHERE id=1")
        with self.assertRaises(BackupVerificationError):
            inspect_database(
                damaged, root=self.root,
                required_tables=REQUIRED_TABLES, required_rows=REQUIRED_ROWS,
            )

    def test_logical_tampering_is_detected(self):
        damaged = self.backups / "tampered.sqlite3"
        create_online_backup(self.source, damaged, root=self.root)
        with sqlite3.connect(damaged) as db:
            db.execute("UPDATE paper_state SET realized='999' WHERE id=1")
        with self.assertRaises(BackupVerificationError):
            verify_backup(
                self.source, damaged, root=self.root,
                required_tables=REQUIRED_TABLES, required_rows=REQUIRED_ROWS,
            )

    def test_corrupt_database_is_rejected(self):
        damaged = self.backups / "corrupt.sqlite3"
        damaged.write_bytes(b"not a sqlite database")
        with self.assertRaises(BackupVerificationError):
            inspect_database(
                damaged, root=self.root,
                required_tables=REQUIRED_TABLES, required_rows=REQUIRED_ROWS,
            )

    def test_atomic_backup_publishes_only_verified_snapshot(self):
        destination = self.backups / "published.sqlite3"
        result = atomic_backup(
            self.source, destination, root=self.root,
            required_tables=REQUIRED_TABLES, required_rows=REQUIRED_ROWS,
        )
        self.assertEqual(result["status"], "PASS")
        self.assertTrue(destination.is_file())
        self.assertFalse(list(self.backups.glob(".backup-stage-*")))
        with self.assertRaises(FileExistsError):
            atomic_backup(
                self.source, destination, root=self.root,
                required_tables=REQUIRED_TABLES, required_rows=REQUIRED_ROWS,
            )

    def test_paths_outside_fixture_root_are_rejected(self):
        outside = self.root.parent / "outside-backup.sqlite3"
        with self.assertRaises(BackupVerificationError):
            create_online_backup(self.source, outside, root=self.root)

    def test_symlinked_destination_is_rejected(self):
        outside = self.root.parent / "outside-target.sqlite3"
        outside.write_bytes(b"do-not-touch")
        link = self.backups / "linked.sqlite3"
        link.symlink_to(outside)
        with self.assertRaises(BackupVerificationError):
            create_online_backup(self.source, link, root=self.root)
        self.assertEqual(outside.read_bytes(), b"do-not-touch")

    def test_split_store_manifest_requires_shared_barrier_and_epoch(self):
        valid = {
            "topology": "split_store",
            "snapshot_barrier_id": "barrier-fixture-001",
            "restore_epoch": 4,
            "stores": {
                "market_data": {
                    "barrier_id": "barrier-fixture-001",
                    "snapshot_id": "market-snapshot-001",
                    "high_water_mark": 120,
                },
                "paper_ledger": {
                    "barrier_id": "barrier-fixture-001",
                    "snapshot_id": "paper-snapshot-001",
                    "high_water_mark": 44,
                },
            },
        }
        self.assertEqual(validate_split_store_manifest(valid)["status"], "PASS")
        invalid = json.loads(json.dumps(valid))
        invalid["stores"]["paper_ledger"]["barrier_id"] = "different-barrier"
        with self.assertRaises(BackupVerificationError):
            validate_split_store_manifest(invalid)
