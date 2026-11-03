"""P5.4.9 fixture-only Backup/Restore contract tests.

Every database is created under a per-test TemporaryDirectory. The suite must
never read a runtime-selected DB path, connect to an exchange, or start a worker.
"""
import hashlib
import json
import sqlite3
import tempfile
import threading
import unittest
from unittest.mock import patch
from pathlib import Path

from market_data.feeder_status import FeederRuntimeStatusStore
from paper_execution.ledger import PaperLedger
from paper_execution.shadow_migration_fixture import (
    FIXED_NOW_MS, PAPER_TABLES, build_legacy_fixture,
)
import backup_restore_test_support as backup_support
from backup_restore_test_support import (
    BackupVerificationError,
    create_online_backup,
    inspect_database,
    atomic_backup,
    verify_backup,
    validate_split_store_manifest,
    publish_split_store_backup_set,
    derive_snapshot_identity,
    verify_split_store_backup_set,
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

    def test_wal_snapshot_respects_committed_writer_barrier(self):
        committed_before = threading.Event()
        post_epoch_transaction_ready = threading.Event()
        allow_post_epoch_commit = threading.Event()
        writer_errors = []

        def writer():
            connection = sqlite3.connect(self.source, timeout=5)
            try:
                connection.execute(
                    "INSERT INTO paper_audit(at_ms,kind,document) VALUES (?,?,?)",
                    (FIXED_NOW_MS + 201, "BARRIER_PRE_EPOCH", json.dumps({"epoch": 1})),
                )
                connection.commit()
                committed_before.set()

                connection.execute("BEGIN IMMEDIATE")
                connection.execute(
                    "INSERT INTO paper_audit(at_ms,kind,document) VALUES (?,?,?)",
                    (FIXED_NOW_MS + 202, "BARRIER_POST_EPOCH", json.dumps({"epoch": 2})),
                )
                post_epoch_transaction_ready.set()
                if not allow_post_epoch_commit.wait(timeout=5):
                    raise TimeoutError("snapshot barrier did not release writer")
                connection.commit()
            except BaseException as exc:
                writer_errors.append(exc)
                committed_before.set()
                post_epoch_transaction_ready.set()
            finally:
                connection.close()

        thread = threading.Thread(target=writer, name="fixture-wal-barrier-writer")
        thread.start()
        try:
            self.assertTrue(committed_before.wait(timeout=5))
            self.assertTrue(post_epoch_transaction_ready.wait(timeout=5))
            before_epoch = self.backup("barrier-before-post-commit.sqlite3")
            with sqlite3.connect(before_epoch) as db:
                pre_count = db.execute(
                    "SELECT COUNT(*) FROM paper_audit WHERE kind='BARRIER_PRE_EPOCH'"
                ).fetchone()[0]
                post_count = db.execute(
                    "SELECT COUNT(*) FROM paper_audit WHERE kind='BARRIER_POST_EPOCH'"
                ).fetchone()[0]
            self.assertEqual((pre_count, post_count), (1, 0))
        finally:
            allow_post_epoch_commit.set()
            thread.join(timeout=5)
        self.assertFalse(thread.is_alive(), "fixture writer did not stop")
        self.assertEqual(writer_errors, [])

        after_epoch = self.backup("barrier-after-post-commit.sqlite3")
        with sqlite3.connect(after_epoch) as db:
            pre_count = db.execute(
                "SELECT COUNT(*) FROM paper_audit WHERE kind='BARRIER_PRE_EPOCH'"
            ).fetchone()[0]
            post_count = db.execute(
                "SELECT COUNT(*) FROM paper_audit WHERE kind='BARRIER_POST_EPOCH'"
            ).fetchone()[0]
        self.assertEqual((pre_count, post_count), (1, 1))

    def test_atomic_publication_interruption_never_exposes_final_backup(self):
        destination = self.backups / "interrupted-publication.sqlite3"
        with patch.object(
            backup_support, "verify_backup",
            side_effect=BackupVerificationError("fixture injected verification interruption"),
        ):
            with self.assertRaises(BackupVerificationError):
                atomic_backup(
                    self.source, destination, root=self.root,
                    required_tables=REQUIRED_TABLES, required_rows=REQUIRED_ROWS,
                )
        self.assertFalse(destination.exists())
        self.assertEqual(list(self.backups.glob(".backup-stage-*")), [])
        self.assertEqual(list(self.backups.glob("*.sqlite3-wal")), [])
        self.assertEqual(list(self.backups.glob("*.sqlite3-shm")), [])

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

    def _reset_paper_fixture_for_replay(self):
        ledger = PaperLedger(self.source, max_position_base="1")
        with sqlite3.connect(self.source) as db:
            db.execute("DELETE FROM paper_orders")
            db.execute("DELETE FROM paper_books")
            db.execute("DELETE FROM paper_audit")
            db.execute(
                "UPDATE paper_state SET position='0',average='0',realized='0',fees='0',paused=0 WHERE id=1"
            )
            db.execute(
                "UPDATE paper_strategy_state SET owner=NULL,dca_used=0,initial_margin_quote='0' WHERE id=1"
            )
            db.execute(
                "UPDATE paper_risk_control SET paused=0,killed=0,reason=NULL,updated_at_ms=0 WHERE id=1"
            )
        return ledger

    @staticmethod
    def _replay_intent(identifier, now_ms, target="0.1"):
        return {
            "intentId": identifier, "symbol": "BTCUSDT", "exchange": "binance",
            "marketType": "USDT_PERPETUAL", "strategyVersion": "fixture-strategy-v1",
            "modelVersion": "fixture-model-v1", "datasetVersion": "sha256:fixture-dataset",
            "targetPositionBase": target, "limitPrice": "100.1",
            "decisionAtMs": now_ms - 100, "validUntilMs": now_ms + 30_000,
            "inputSnapshotId": "fixture-input-snapshot", "mode": "PAPER",
        }

    @staticmethod
    def _replay_book(now_ms):
        return {
            "source": "hummingbot", "connector": "binance_perpetual",
            "symbol": "BTCUSDT", "observedAtMs": now_ms,
            "bids": [{"price": "100", "quantity": "1"}],
            "asks": [{"price": "100.1", "quantity": "1"}],
        }

    def test_duplicate_intent_retry_after_backup_does_not_duplicate_order_or_fill(self):
        ledger = self._reset_paper_fixture_for_replay()
        now = FIXED_NOW_MS + 5_000
        intent, book = self._replay_intent("restore-replay-intent", now), self._replay_book(now)
        original = ledger.submit(intent, book, now)
        destination = self.backup("intent-replay.sqlite3")
        restored = PaperLedger(destination, max_position_base="1")

        replayed = restored.submit(intent, None, now + 90_000)
        self.assertEqual(replayed, original)
        self.assertEqual(restored.snapshot()["positionBase"], "0.1")
        with sqlite3.connect(destination) as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM paper_orders").fetchone()[0], 1)
            self.assertEqual(
                db.execute("SELECT COUNT(*) FROM paper_audit WHERE kind='SUBMIT'").fetchone()[0], 1
            )
            self.assertEqual(db.execute("SELECT COUNT(*) FROM paper_books").fetchone()[0], 1)

    def test_consumed_book_snapshot_cannot_be_reused_after_backup_restore(self):
        ledger = self._reset_paper_fixture_for_replay()
        now = FIXED_NOW_MS + 5_000
        book = self._replay_book(now)
        first = ledger.submit(self._replay_intent("book-consumer-one", now), book, now)
        self.assertEqual(first["status"], "FILLED")
        destination = self.backup("consumed-book.sqlite3")
        restored = PaperLedger(destination, max_position_base="1")

        replay = restored.submit(
            self._replay_intent("book-consumer-two", now + 1, target="0.2"),
            book, now + 1,
        )
        self.assertEqual(replay["status"], "REJECTED")
        self.assertEqual(replay["reason"], "SNAPSHOT_ALREADY_USED")
        self.assertEqual(restored.snapshot()["positionBase"], "0.1")
        with sqlite3.connect(destination) as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM paper_books").fetchone()[0], 1)

    def test_restored_kill_latch_rejects_new_paper_entry(self):
        ledger = self._reset_paper_fixture_for_replay()
        now = FIXED_NOW_MS + 5_000
        ledger.set_killed(True, now, reason="FIXTURE_RESTORE_KILL_LATCH")
        destination = self.backup("kill-latch-recovery.sqlite3")
        restored = PaperLedger(destination, max_position_base="1")

        rejected = restored.submit(
            self._replay_intent("entry-blocked-by-restored-kill", now + 1),
            self._replay_book(now + 1), now + 1,
        )
        self.assertEqual(rejected["status"], "REJECTED")
        self.assertEqual(rejected["reason"], "KILL_SWITCH")
        self.assertEqual(restored.snapshot()["positionBase"], "0")
        self.assertTrue(restored.snapshot()["riskControl"]["killed"])
        with sqlite3.connect(destination) as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM paper_books").fetchone()[0], 0)

    def test_backup_verifier_detects_schema_drift(self):
        destination = self.backup("schema-drift.sqlite3")
        with sqlite3.connect(destination) as db:
            db.execute("ALTER TABLE candles ADD COLUMN fixture_schema_drift TEXT")
        with self.assertRaises(BackupVerificationError):
            verify_backup(
                self.source, destination, root=self.root,
                required_tables=REQUIRED_TABLES, required_rows=REQUIRED_ROWS,
            )

    def test_split_store_manifest_requires_versioned_schema_metadata(self):
        missing_manifest_version = self._valid_split_store_manifest()
        del missing_manifest_version["manifest_version"]
        with self.assertRaises(BackupVerificationError):
            validate_split_store_manifest(missing_manifest_version)

        for store in ("market_data", "paper_ledger"):
            with self.subTest(store=store):
                missing_schema_version = self._valid_split_store_manifest()
                del missing_schema_version["stores"][store]["schema_version"]
                with self.assertRaises(BackupVerificationError):
                    validate_split_store_manifest(missing_schema_version)

    def test_split_store_manifest_rejects_invalid_domain_values(self):
        mutations = (
            ("boolean restore epoch", lambda value: value.update(restore_epoch=True)),
            ("floating restore epoch", lambda value: value.update(restore_epoch=4.0)),
            ("negative high water", lambda value: value["stores"]["market_data"].update(high_water_mark=-1)),
            ("boolean high water", lambda value: value["stores"]["paper_ledger"].update(high_water_mark=True)),
            ("blank snapshot id", lambda value: value["stores"]["market_data"].update(snapshot_id=" ")),
            ("blank barrier id", lambda value: value.update(snapshot_barrier_id=" ")),
            ("extra store", lambda value: value["stores"].update(unapproved_store={"snapshot_id": "x"})),
            ("zero schema version", lambda value: value["stores"]["market_data"].update(schema_version=0)),
        )
        for label, mutate in mutations:
            with self.subTest(case=label):
                candidate = self._valid_split_store_manifest()
                mutate(candidate)
                with self.assertRaises(BackupVerificationError):
                    validate_split_store_manifest(candidate)

    @staticmethod
    def _valid_split_store_manifest():
        return {
            "manifest_version": 1,
            "topology": "split_store",
            "snapshot_barrier_id": "barrier-fixture-001",
            "restore_epoch": 4,
            "stores": {
                "market_data": {
                    "barrier_id": "barrier-fixture-001",
                    "snapshot_id": "a" * 64,
                    "logical_sha256": "a" * 64,
                    "content_sha256": "b" * 64,
                    "high_water_mark": 120,
                    "schema_version": 3,
                    "table_counts": {"candles": 100, "feeder_leases": 20},
                },
                "paper_ledger": {
                    "barrier_id": "barrier-fixture-001",
                    "snapshot_id": "c" * 64,
                    "logical_sha256": "c" * 64,
                    "content_sha256": "d" * 64,
                    "high_water_mark": 44,
                    "schema_version": 5,
                    "table_counts": {"paper_orders": 44},
                },
            },
        }

    def test_split_store_partial_backup_failure_publishes_no_snapshot_set(self):
        sources, snapshot_metadata = self._split_store_sources_and_metadata("barrier-fixture-002")
        target = self.backups / "split-set"

        with self.assertRaisesRegex(RuntimeError, "injected partial split-store failure"):
            publish_split_store_backup_set(
                sources, target, root=self.root,
                snapshot_barrier_id="barrier-fixture-002",
                restore_epoch=5,
                snapshot_metadata=snapshot_metadata,
                required_tables=REQUIRED_TABLES,
                required_rows=REQUIRED_ROWS,
                fail_after_store="market_data",
            )

        self.assertFalse(target.exists())
        self.assertEqual(list(self.backups.iterdir()), [])
        self.assertFalse(any(self.backups.glob(".split-stage-*")))

    def test_split_store_backup_set_publishes_both_stores_and_manifest_together(self):
        sources, snapshot_metadata = self._split_store_sources_and_metadata("barrier-fixture-003")
        target = self.backups / "split-set"
        result = publish_split_store_backup_set(
            sources,
            target, root=self.root,
            snapshot_barrier_id="barrier-fixture-003",
            restore_epoch=6,
            snapshot_metadata=snapshot_metadata,
            required_tables=REQUIRED_TABLES,
            required_rows=REQUIRED_ROWS,
        )

        self.assertEqual(result["status"], "PASS")
        self.assertEqual(
            {path.name for path in target.iterdir()},
            {"market_data.sqlite3", "paper_ledger.sqlite3", "backup-manifest.json"},
        )
        manifest = json.loads((target / "backup-manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(validate_split_store_manifest(manifest)["status"], "PASS")

    def _split_store_sources_and_metadata(self, barrier):
        second_source = self.root / "source" / "second-fixture.sqlite3"
        create_online_backup(
            self.source, second_source, root=self.root,
            required_tables=REQUIRED_TABLES, required_rows=REQUIRED_ROWS,
        )
        with sqlite3.connect(self.source) as db:
            db.execute("PRAGMA user_version=3")
        with sqlite3.connect(second_source) as db:
            db.execute("PRAGMA user_version=5")
        sources = {"market_data": self.source, "paper_ledger": second_source}
        metadata = {}
        for name, source in sources.items():
            identity = derive_snapshot_identity(source, root=self.root)
            metadata[name] = {
                "barrier_id": barrier,
                "snapshot_id": identity["logical_sha256"],
                "high_water_mark": identity["high_water_mark"],
                "schema_version": identity["schema_version"],
            }
        return sources, metadata

    def test_split_store_manifest_binds_each_backup_content_and_schema(self):
        sources, metadata = self._split_store_sources_and_metadata("barrier-bound-001")
        target = self.backups / "bound-set"
        publish_split_store_backup_set(
            sources, target, root=self.root,
            snapshot_barrier_id="barrier-bound-001",
            restore_epoch=7, snapshot_metadata=metadata,
            required_tables=REQUIRED_TABLES, required_rows=REQUIRED_ROWS,
        )
        result = verify_split_store_backup_set(target, root=self.root)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["stores"]["market_data"]["schema_version"], 3)
        self.assertEqual(result["stores"]["paper_ledger"]["schema_version"], 5)

    def test_split_store_verifier_rejects_manifest_content_hash_tampering(self):
        sources, metadata = self._split_store_sources_and_metadata("barrier-bound-002")
        target = self.backups / "tampered-set"
        publish_split_store_backup_set(
            sources, target, root=self.root,
            snapshot_barrier_id="barrier-bound-002",
            restore_epoch=8, snapshot_metadata=metadata,
            required_tables=REQUIRED_TABLES, required_rows=REQUIRED_ROWS,
        )
        manifest_path = target / "backup-manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["stores"]["market_data"]["content_sha256"] = "0" * 64
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaises(BackupVerificationError):
            verify_split_store_backup_set(target, root=self.root)

    def test_split_store_verifier_rejects_swapped_store_databases(self):
        sources, metadata = self._split_store_sources_and_metadata("barrier-bound-003")
        target = self.backups / "swapped-set"
        publish_split_store_backup_set(
            sources, target, root=self.root,
            snapshot_barrier_id="barrier-bound-003",
            restore_epoch=9, snapshot_metadata=metadata,
            required_tables=REQUIRED_TABLES, required_rows=REQUIRED_ROWS,
        )
        market = target / "market_data.sqlite3"
        paper = target / "paper_ledger.sqlite3"
        market_bytes, paper_bytes = market.read_bytes(), paper.read_bytes()
        market.write_bytes(paper_bytes)
        paper.write_bytes(market_bytes)
        with self.assertRaises(BackupVerificationError):
            verify_split_store_backup_set(target, root=self.root)

    def test_split_store_verifier_rejects_missing_database(self):
        sources, metadata = self._split_store_sources_and_metadata("barrier-bound-004")
        target = self.backups / "missing-set"
        publish_split_store_backup_set(
            sources, target, root=self.root,
            snapshot_barrier_id="barrier-bound-004",
            restore_epoch=10, snapshot_metadata=metadata,
            required_tables=REQUIRED_TABLES, required_rows=REQUIRED_ROWS,
        )
        (target / "paper_ledger.sqlite3").unlink()
        with self.assertRaises(BackupVerificationError):
            verify_split_store_backup_set(target, root=self.root)

    def test_split_store_verifier_rejects_rehashed_semantic_database_mutation(self):
        sources, metadata = self._split_store_sources_and_metadata("barrier-bound-005")
        target = self.backups / "semantic-mismatch-set"
        publish_split_store_backup_set(
            sources, target, root=self.root,
            snapshot_barrier_id="barrier-bound-005",
            restore_epoch=11, snapshot_metadata=metadata,
            required_tables=REQUIRED_TABLES, required_rows=REQUIRED_ROWS,
        )
        database = target / "market_data.sqlite3"
        with sqlite3.connect(database) as db:
            db.execute(
                "UPDATE candles SET close='61000' "
                "WHERE rowid=(SELECT MIN(rowid) FROM candles)"
            )
        manifest_path = target / "backup-manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["stores"]["market_data"]["content_sha256"] = hashlib.sha256(
            database.read_bytes()
        ).hexdigest()
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaises(BackupVerificationError):
            verify_split_store_backup_set(target, root=self.root)

    def test_split_store_verifier_rejects_table_count_tampering(self):
        sources, metadata = self._split_store_sources_and_metadata("barrier-bound-006")
        target = self.backups / "table-count-mismatch-set"
        publish_split_store_backup_set(
            sources, target, root=self.root,
            snapshot_barrier_id="barrier-bound-006",
            restore_epoch=12, snapshot_metadata=metadata,
            required_tables=REQUIRED_TABLES, required_rows=REQUIRED_ROWS,
        )
        manifest_path = target / "backup-manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        counts = manifest["stores"]["market_data"]["table_counts"]
        first_table = sorted(counts)[0]
        counts[first_table] += 1
        manifest["stores"]["market_data"]["high_water_mark"] += 1
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaises(BackupVerificationError):
            verify_split_store_backup_set(target, root=self.root)

    def test_split_store_verifier_rejects_high_water_mark_tampering(self):
        sources, metadata = self._split_store_sources_and_metadata("barrier-bound-007")
        target = self.backups / "high-water-mismatch-set"
        publish_split_store_backup_set(
            sources, target, root=self.root,
            snapshot_barrier_id="barrier-bound-007",
            restore_epoch=13, snapshot_metadata=metadata,
            required_tables=REQUIRED_TABLES, required_rows=REQUIRED_ROWS,
        )
        manifest_path = target / "backup-manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["stores"]["paper_ledger"]["high_water_mark"] += 1
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaises(BackupVerificationError):
            verify_split_store_backup_set(target, root=self.root)

    def test_split_store_verifier_rejects_schema_version_tampering(self):
        sources, metadata = self._split_store_sources_and_metadata("barrier-bound-008")
        target = self.backups / "schema-version-mismatch-set"
        publish_split_store_backup_set(
            sources, target, root=self.root,
            snapshot_barrier_id="barrier-bound-008",
            restore_epoch=14, snapshot_metadata=metadata,
            required_tables=REQUIRED_TABLES, required_rows=REQUIRED_ROWS,
        )
        manifest_path = target / "backup-manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["stores"]["paper_ledger"]["schema_version"] += 1
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaises(BackupVerificationError):
            verify_split_store_backup_set(target, root=self.root)

    def test_split_store_manifest_requires_shared_barrier_and_epoch(self):
        valid = self._valid_split_store_manifest()
        self.assertEqual(validate_split_store_manifest(valid)["status"], "PASS")
        invalid = json.loads(json.dumps(valid))
        invalid["stores"]["paper_ledger"]["barrier_id"] = "different-barrier"
        with self.assertRaises(BackupVerificationError):
            validate_split_store_manifest(invalid)
