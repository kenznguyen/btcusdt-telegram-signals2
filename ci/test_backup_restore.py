"""P5.4.9 fixture-only Backup/Restore contract tests.

Every database is created under a per-test TemporaryDirectory. The suite must
never read a runtime-selected DB path, connect to an exchange, or start a worker.
"""
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from market_data.feeder_status import FeederRuntimeStatusStore
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
        self.assertEqual(before["logical_sha256"], after["logical_sha256"])

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

    def test_round_trip_preserves_all_domain_cursors_and_lease_generation(self):
        destination = self.backup("domain-cursors.sqlite3")
        with sqlite3.connect(self.source) as source_db, sqlite3.connect(destination) as backup_db:
            queries = {
                "candles": "SELECT timeframe,MAX(open_time_ms),COUNT(*) FROM candles GROUP BY timeframe ORDER BY timeframe",
                "paper_orders": "SELECT status,COUNT(*) FROM paper_orders GROUP BY status ORDER BY status",
                "paper_audit": "SELECT MAX(at_ms),COUNT(*) FROM paper_audit",
                "paper_equity_history": "SELECT MAX(observed_at_ms),COUNT(*) FROM paper_equity_history",
                "feeder_leases": "SELECT owner,generation,expires_at_ms FROM feeder_leases ORDER BY lease_name",
            }
            for name, query in queries.items():
                self.assertEqual(
                    source_db.execute(query).fetchall(),
                    backup_db.execute(query).fetchall(),
                    msg=f"logical domain cursor mismatch: {name}",
                )
            lease = backup_db.execute(
                "SELECT owner,generation FROM feeder_leases WHERE lease_name=?",
                ("binance-btcusdt-canonical",),
            ).fetchone()
        self.assertEqual(lease, ("fixture-owner-A", 7))

    def test_kill_latch_and_pause_state_survive_restore_independently(self):
        with sqlite3.connect(self.source) as db:
            db.execute("UPDATE paper_state SET paused=1 WHERE id=1")
            db.execute(
                "UPDATE paper_risk_control SET paused=0,killed=1,reason='FIXTURE_KILL_SWITCH' WHERE id=1"
            )
        destination = self.backup("kill-pause.sqlite3")
        with sqlite3.connect(destination) as restored:
            paper_paused = restored.execute(
                "SELECT paused FROM paper_state WHERE id=1"
            ).fetchone()[0]
            risk_paused, killed, reason = restored.execute(
                "SELECT paused,killed,reason FROM paper_risk_control WHERE id=1"
            ).fetchone()
        self.assertEqual(paper_paused, 1)
        self.assertEqual(risk_paused, 0)
        self.assertEqual(killed, 1)
        self.assertEqual(reason, "FIXTURE_KILL_SWITCH")

    def test_stale_lease_generation_cannot_publish_runtime_status(self):
        status = FeederRuntimeStatusStore(self.source)
        self.assertFalse(status.publish(
            "fixture-owner-A", 6, "RUNNING",
            now_ms=FIXED_NOW_MS + 6 * 60_001, recovery_complete=True,
        ))
        with sqlite3.connect(self.source) as db:
            row = db.execute(
                "SELECT generation FROM feeder_runtime_status WHERE lease_name=?",
                ("binance-btcusdt-canonical",),
            ).fetchone()
        self.assertEqual(row, (7,))

    def test_current_lease_generation_can_publish_only_after_recovery_complete(self):
        status = FeederRuntimeStatusStore(self.source)
        now = FIXED_NOW_MS + 6 * 60_001 + 1_000
        self.assertTrue(status.publish(
            "fixture-owner-A", 7, "STARTING",
            now_ms=now, recovery_complete=False,
        ))
        starting = status.snapshot(now)
        self.assertFalse(starting["startup_complete"])
        self.assertTrue(status.publish(
            "fixture-owner-A", 7, "RUNNING",
            now_ms=now + 1, recovery_complete=True,
        ))
        running = status.snapshot(now + 1)
        self.assertTrue(running["startup_complete"])
        self.assertTrue(running["lease_valid"])

    def test_backup_verifier_detects_kill_latch_rollback(self):
        destination = self.backup("kill-latch-tampered.sqlite3")
        with sqlite3.connect(destination) as db:
            db.execute(
                "UPDATE paper_risk_control SET killed=0,reason=NULL WHERE id=1"
            )
        with self.assertRaises(BackupVerificationError):
            verify_backup(
                self.source, destination, root=self.root,
                required_tables=REQUIRED_TABLES, required_rows=REQUIRED_ROWS,
            )

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
