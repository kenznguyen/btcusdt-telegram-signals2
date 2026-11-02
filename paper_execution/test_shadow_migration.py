"""P5.2.4 Shadow split-migration contract tests.

All databases are temporary fixtures. The migration API is intentionally exercised
through its public contract; this module must not access canonical paths or runtime
environment variables.
"""
import hashlib
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from paper_execution.shadow_migration_fixture import (
    PAPER_CONFIG, PAPER_TABLES, build_legacy_fixture,
)

# Implemented in the GREEN phase after these contract tests exist.
from paper_execution.shadow_migration import migrate_shadow, verify_shadow_migration


class ShadowMigrationContractTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="p5_2_4_shadow_")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "source" / "legacy_combined.sqlite3"
        self.t0 = self.root / "staging" / "t0_shadow.sqlite3"
        self.paper = self.root / "staging" / "paper_shadow.sqlite3"
        self.manifests = self.root / "manifests"
        self.fixture = build_legacy_fixture(self.source)
        self.migration_id = "p5-2-4-fixture-migration-001"

    def migrate(self, **kwargs):
        args = dict(
            source_db=self.source,
            t0_target_db=self.t0,
            paper_target_db=self.paper,
            manifest_dir=self.manifests,
            migration_id=self.migration_id,
            paper_config=PAPER_CONFIG,
        )
        args.update(kwargs)
        return migrate_shadow(**args)

    def verify(self, **kwargs):
        args = dict(
            source_db=self.source,
            t0_target_db=self.t0,
            paper_target_db=self.paper,
            manifest_dir=self.manifests,
            migration_id=self.migration_id,
            paper_config=PAPER_CONFIG,
        )
        args.update(kwargs)
        return verify_shadow_migration(**args)

    @staticmethod
    def tables(path):
        with sqlite3.connect(path) as db:
            return {row[0] for row in db.execute(
                "SELECT name FROM sqlite_master WHERE type='table'")}

    @staticmethod
    def counts(path, names):
        with sqlite3.connect(path) as db:
            return {name: db.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0]
                    for name in names}

    def test_A01_fixture_uses_real_schema_and_expected_paper_table_set(self):
        self.assertEqual(set(PAPER_TABLES), {
            "paper_state", "paper_orders", "paper_books", "paper_audit",
            "paper_strategy_state", "paper_risk_control", "paper_equity_history",
            "paper_daily_baselines", "paper_account_config",
        })
        self.assertTrue(set(PAPER_TABLES).issubset(self.tables(self.source)))
        with sqlite3.connect(self.source) as db:
            for timeframe, interval, expected_count in (("15m", 900_000, 12), ("1h", 3_600_000, 6)):
                rows = db.execute(
                    "SELECT open_time_ms FROM candles WHERE timeframe=? ORDER BY open_time_ms",
                    (timeframe,),
                ).fetchall()
                self.assertEqual(len(rows), expected_count)
                self.assertTrue(all(
                    rows[index][0] - rows[index - 1][0] == interval
                    for index in range(1, len(rows))
                ), f"{timeframe} source candles must be contiguous")
            lease_ddl = db.execute(
                "SELECT sql FROM sqlite_master WHERE type='table' AND name='feeder_leases'"
            ).fetchone()[0]
            self.assertIn("CHECK(generation >= 0)", lease_ddl)
            self.assertIn("CHECK(expires_at_ms >= 0)", lease_ddl)
            runtime_ddl = db.execute(
                "SELECT sql FROM sqlite_master WHERE type='table' AND name='feeder_runtime_status'"
            ).fetchone()[0]
            self.assertIn("CHECK(generation >= 1)", runtime_ddl)
            self.assertIn("CHECK(recovery_complete IN (0,1))", runtime_ddl)

    def test_A02_inventory_includes_every_user_table_and_sqlite_sequence(self):
        result = self.migrate()
        inventory = json.loads((self.manifests / "source_manifest.json").read_text())
        with sqlite3.connect(self.source) as db:
            actual = {row[0] for row in db.execute(
                "SELECT name FROM sqlite_master WHERE type='table'")}
        self.assertEqual(set(inventory["tables"]), actual)
        self.assertIn("sqlite_sequence", actual)
        self.assertEqual(result["status"], "PASS")

    def test_A03_source_snapshot_manifest_has_integrity_and_sha256(self):
        self.migrate()
        manifest = json.loads((self.manifests / "source_manifest.json").read_text())
        self.assertEqual(manifest["integrity_check"], "ok")
        self.assertEqual(manifest["database_sha256"],
                         hashlib.sha256(self.source.read_bytes()).hexdigest())

    def test_A04_effective_paper_config_is_explicit_and_fingerprinted(self):
        self.migrate()
        manifest = json.loads((self.manifests / "migration_manifest.json").read_text())
        self.assertEqual(manifest["paper_config"], PAPER_CONFIG)
        self.assertEqual(self.fixture["paper_config"], PAPER_CONFIG)
        with sqlite3.connect(self.source) as db:
            self.assertEqual(
                db.execute("SELECT initial_capital FROM paper_account_config WHERE id=1").fetchone(),
                (PAPER_CONFIG["initial_capital"],),
            )
        self.assertTrue(manifest["paper_config_sha256"])

    def test_B01_all_nine_paper_tables_exist_only_in_paper_target(self):
        self.migrate()
        self.assertTrue(set(PAPER_TABLES).issubset(self.tables(self.paper)))
        self.assertTrue(set(PAPER_TABLES).isdisjoint(self.tables(self.t0)))

    def test_B02_control_budget_moves_to_paper_target(self):
        self.migrate()
        self.assertIn("paper_control_budget", self.tables(self.paper))
        self.assertNotIn("paper_control_budget", self.tables(self.t0))

    def test_B03_each_paper_table_row_count_matches_source(self):
        self.migrate()
        expected = self.counts(self.source, PAPER_TABLES + ("paper_control_budget",))
        actual = self.counts(self.paper, PAPER_TABLES + ("paper_control_budget",))
        self.assertEqual(actual, expected)

    def test_B04_each_paper_table_row_fingerprint_matches_source(self):
        result = self.migrate()
        self.assertEqual(result["status"], "PASS", "migration must complete before fingerprint comparison")
        self.assertTrue(set(PAPER_TABLES + ("paper_control_budget",)).issubset(
            self.tables(self.paper)), "empty target must not produce a vacuous fingerprint PASS")
        manifest = json.loads((self.manifests / "migration_manifest.json").read_text())
        source_fp = manifest["paper_row_fingerprints"]["source"]
        target_fp = manifest["paper_row_fingerprints"]["target"]
        self.assertEqual(set(source_fp), set(PAPER_TABLES + ("paper_control_budget",)))
        self.assertEqual(set(target_fp), set(PAPER_TABLES + ("paper_control_budget",)))
        self.assertEqual(source_fp, target_fp)

    def test_B05_indexes_and_triggers_are_preserved_for_paper_objects(self):
        self.migrate()
        def objects(path):
            with sqlite3.connect(path) as db:
                return set(db.execute("""SELECT type,name,tbl_name,sql FROM sqlite_master
                    WHERE type IN ('index','trigger') AND tbl_name LIKE 'paper_%'"""))
        source = objects(self.source)
        target = objects(self.paper)
        self.assertEqual(source, target)
        source_names = {row[1] for row in source}
        self.assertIn("paper_order_status", source_names)
        self.assertIn("paper_equity_time", source_names)
        self.assertTrue(any(name.startswith("sqlite_autoindex_paper_orders_")
                            for name in source_names))
        self.assertTrue(any(name.startswith("sqlite_autoindex_paper_audit_")
                            for name in source_names))

    def test_B06_foreign_key_check_and_integrity_check_pass_on_both_targets(self):
        result = self.migrate()
        self.assertEqual(result["status"], "PASS", "migration must complete before DB checks")
        t0_tables = self.tables(self.t0)
        paper_tables = self.tables(self.paper)
        self.assertTrue({"candles", "feeder_leases", "feeder_runtime_status"}.issubset(t0_tables))
        self.assertTrue(set(PAPER_TABLES + ("paper_control_budget",)).issubset(paper_tables))
        self.assertTrue(t0_tables, "T0 target must not be an empty SQLite database")
        self.assertTrue(paper_tables, "Paper target must not be an empty SQLite database")
        for path in (self.t0, self.paper):
            with sqlite3.connect(path) as db:
                self.assertEqual(db.execute("PRAGMA integrity_check").fetchone()[0], "ok")
                self.assertEqual(db.execute("PRAGMA foreign_key_check").fetchall(), [])

    def test_B07_autoincrement_sequence_is_preserved_for_paper_audit_and_equity(self):
        self.migrate()
        with sqlite3.connect(self.source) as source, sqlite3.connect(self.paper) as target:
            for name in ("paper_audit", "paper_equity_history"):
                source_ddl = source.execute(
                    "SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (name,)
                ).fetchone()[0]
                target_ddl = target.execute(
                    "SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (name,)
                ).fetchone()[0]
                self.assertIn("AUTOINCREMENT", source_ddl.upper())
                self.assertIn("AUTOINCREMENT", target_ddl.upper())
                source_max = source.execute(f"SELECT COALESCE(MAX(id),0) FROM {name}").fetchone()[0]
                target_max = target.execute(f"SELECT COALESCE(MAX(id),0) FROM {name}").fetchone()[0]
                source_seq = source.execute(
                    "SELECT seq FROM sqlite_sequence WHERE name=?", (name,)
                ).fetchone()
                target_seq = target.execute(
                    "SELECT seq FROM sqlite_sequence WHERE name=?", (name,)
                ).fetchone()
                self.assertIsNotNone(source_seq)
                self.assertIsNotNone(target_seq)
                self.assertGreaterEqual(source_seq[0], source_max)
                self.assertGreaterEqual(target_seq[0], target_max)
                self.assertEqual(target_seq, source_seq)

    def test_C01_open_position_cost_basis_fees_and_realized_pnl_are_preserved(self):
        self.migrate()
        with sqlite3.connect(self.paper) as db:
            self.assertEqual(db.execute(
                "SELECT position,average,realized,fees FROM paper_state WHERE id=1"
            ).fetchone(), ("0.001", "60000", "1.25", "0.03"))

    def test_C02_strategy_owner_and_dca_used_flag_remain_set(self):
        self.migrate()
        with sqlite3.connect(self.paper) as db:
            self.assertEqual(db.execute(
                "SELECT owner,dca_used FROM paper_strategy_state WHERE id=1"
            ).fetchone(), ("STRATEGY_CORE", 1))

    def test_C03_open_order_identity_payload_and_document_are_preserved(self):
        self.migrate()
        with sqlite3.connect(self.paper) as db:
            row = db.execute("SELECT intent_id,payload_hash,order_id,status,document "
                             "FROM paper_orders WHERE intent_id='fixture-open'").fetchone()
        self.assertEqual(row[:4], ("fixture-open", "sha256:" + "2" * 64,
                                   "fixture-open", "OPEN"))
        self.assertEqual(json.loads(row[4])["orderId"], "fixture-open")

    def test_C04_filled_order_and_fee_relationships_are_preserved(self):
        self.migrate()
        with sqlite3.connect(self.paper) as db:
            row = db.execute("SELECT status,document FROM paper_orders "
                             "WHERE intent_id='fixture-filled'").fetchone()
        self.assertEqual(row[0], "FILLED")
        self.assertEqual(json.loads(row[1])["feeQuote"], "0.03")

    def test_C05_kill_switch_latch_remains_active_without_automatic_resume(self):
        self.migrate()
        with sqlite3.connect(self.paper) as db:
            self.assertEqual(db.execute(
                "SELECT killed,reason FROM paper_risk_control WHERE id=1"
            ).fetchone(), (1, "FIXTURE_KILL_SWITCH"))

    def test_C06_equity_high_water_mark_and_daily_baselines_are_preserved(self):
        self.migrate()
        with sqlite3.connect(self.paper) as db:
            self.assertEqual(db.execute(
                "SELECT equity,high_water_mark,drawdown_usdt FROM paper_equity_history"
            ).fetchone(), ("101.27", "102", "0.73"))
            self.assertEqual(db.execute("SELECT COUNT(*) FROM paper_daily_baselines").fetchone()[0], 2)

    def test_C07_audit_event_order_and_ids_are_preserved(self):
        self.migrate()
        with sqlite3.connect(self.source) as source, sqlite3.connect(self.paper) as target:
            self.assertEqual(source.execute(
                "SELECT id,at_ms,kind,document FROM paper_audit ORDER BY id").fetchall(),
                target.execute(
                "SELECT id,at_ms,kind,document FROM paper_audit ORDER BY id").fetchall())

    def test_D01_runtime_status_remains_in_t0_target(self):
        self.migrate()
        self.assertIn("feeder_runtime_status", self.tables(self.t0))
        self.assertNotIn("feeder_runtime_status", self.tables(self.paper))

    def test_D02_feeder_lease_owner_and_generation_remain_in_t0_target(self):
        self.migrate()
        with sqlite3.connect(self.t0) as db:
            self.assertEqual(db.execute(
                "SELECT owner,generation FROM feeder_leases WHERE lease_name=?",
                ("binance-btcusdt-canonical",)).fetchone(), ("fixture-owner-A", 7))

    def test_D03_candle_rows_and_logical_fingerprints_remain_unchanged(self):
        self.migrate()
        self.assertEqual(self.counts(self.t0, ("candles",))["candles"],
                         self.counts(self.source, ("candles",))["candles"])
        manifest = json.loads((self.manifests / "migration_manifest.json").read_text())
        self.assertEqual(manifest["t0_candle_fingerprint"]["source"],
                         manifest["t0_candle_fingerprint"]["target"])

    def test_D04_paper_and_t0_targets_are_independent_files_and_domains(self):
        self.migrate()
        self.assertNotEqual(self.t0.resolve(), self.paper.resolve())
        self.assertTrue(set(PAPER_TABLES).isdisjoint(self.tables(self.t0)))
        self.assertIn("candles", self.tables(self.t0))
        self.assertNotIn("candles", self.tables(self.paper))

    def test_E01_source_sha_mismatch_fails_closed_without_valid_verdict(self):
        self.migrate()
        with sqlite3.connect(self.source) as db:
            db.execute("UPDATE paper_state SET realized='999' WHERE id=1")
        with self.assertRaises((ValueError, RuntimeError)):
            self.verify()
        
    def assert_successful_migration_precondition(self):
        result = self.migrate()
        self.assertEqual(result["status"], "PASS",
                         "destructive negative test requires a completed baseline migration")
        verification = self.verify()
        self.assertEqual(verification["status"], "PASS",
                         "baseline migration must verify before fault injection")
        self.assertTrue(set(PAPER_TABLES + ("paper_control_budget",)).issubset(
            self.tables(self.paper)))
        self.assertTrue({"candles", "feeder_leases", "feeder_runtime_status"}.issubset(
            self.tables(self.t0)))
        return result

    def test_E02_missing_paper_table_fails_closed(self):
        self.assert_successful_migration_precondition()
        with sqlite3.connect(self.paper) as db:
            db.execute("DROP TABLE paper_books")
        with self.assertRaises((ValueError, RuntimeError)):
            self.verify()

    def test_E03_target_row_mutation_is_detected_by_fingerprint(self):
        self.assert_successful_migration_precondition()
        with sqlite3.connect(self.paper) as db:
            db.execute("UPDATE paper_state SET realized='999' WHERE id=1")
        with self.assertRaises((ValueError, RuntimeError)):
            self.verify()

    def test_E04_new_unresolved_candle_gap_is_detected_before_acceptance(self):
        self.assert_successful_migration_precondition()
        with sqlite3.connect(self.t0) as db:
            db.execute(
                "DELETE FROM candles WHERE timeframe='15m' AND open_time_ms=?",
                (self.fixture["m15_gap_mutation_open_time_ms"],),
            )
        with self.assertRaises((ValueError, RuntimeError)):
            self.verify()

    def test_E05_repeated_migration_id_is_idempotent_and_does_not_duplicate_rows(self):
        first = self.assert_successful_migration_precondition()
        before = self.counts(self.paper, PAPER_TABLES + ("paper_control_budget",))
        second = self.migrate()
        after = self.counts(self.paper, PAPER_TABLES + ("paper_control_budget",))
        self.assertEqual(before, after)
        self.assertEqual(first["migration_id"], second["migration_id"])

    def test_E06_injected_mid_copy_failure_rolls_back_staging_targets(self):
        with self.assertRaises(Exception):
            self.migrate(failpoint="after_paper_copy_before_commit")
        for path in (self.t0, self.paper):
            if path.exists():
                with sqlite3.connect(path) as db:
                    self.assertEqual(db.execute("PRAGMA integrity_check").fetchone()[0], "ok")
                    self.assertEqual(db.execute(
                        "SELECT COUNT(*) FROM sqlite_master WHERE type='table'"
                    ).fetchone()[0], 0)

    def test_E07_active_feeder_lease_blocks_migration(self):
        with self.assertRaises((PermissionError, RuntimeError)):
            self.migrate(require_released_lease=True)

    def test_E08_undrained_paper_writer_blocks_migration(self):
        with self.assertRaises((PermissionError, RuntimeError)):
            self.migrate(paper_writer_drained=False)


if __name__ == "__main__":
    unittest.main()
