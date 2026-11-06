"""RED contract for immutable per-ledger cutover snapshots (migration v7)."""
import sqlite3
import unittest

from paper_execution.test_dual_ledger_red import DualLedgerRedTest


class AccountCutoverSnapshotV7Test(unittest.TestCase):
    def setUp(self):
        self.fixture = DualLedgerRedTest("test_core_and_ai_hold_independent_positions_in_one_account_database")
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.path = self.fixture.path

    def test_verified_cutover_persists_one_immutable_snapshot_per_ledger(self):
        with sqlite3.connect(self.path) as db:
            rows = db.execute(
                """SELECT strategy_id,position_base,average_entry_price,
                          realized_pnl_quote,fees_quote,funding_quote
                   FROM paper_account_cutover_ledger_snapshots
                   WHERE cutover_id='fixture-account-cutover'
                   ORDER BY strategy_id"""
            ).fetchall()
        self.assertEqual(
            [row[0] for row in rows],
            ["AI_FREQAI", "LEGACY_UNATTRIBUTED", "STRATEGY_CORE"],
        )
        self.assertEqual(len(rows), 3)
        for row in rows:
            self.assertEqual(row[1:], ("0", "0", "0", "0", "0"))

    def test_cutover_snapshot_rows_reject_update_and_delete(self):
        with sqlite3.connect(self.path) as db:
            with self.assertRaises(sqlite3.IntegrityError):
                db.execute(
                    """UPDATE paper_account_cutover_ledger_snapshots
                       SET position_base='9'
                       WHERE cutover_id='fixture-account-cutover'
                         AND strategy_id='STRATEGY_CORE'"""
                )
            db.rollback()
            with self.assertRaises(sqlite3.IntegrityError):
                db.execute(
                    """DELETE FROM paper_account_cutover_ledger_snapshots
                       WHERE cutover_id='fixture-account-cutover'"""
                )

    def test_snapshot_records_are_tied_to_exact_cutover_time_and_hash(self):
        with sqlite3.connect(self.path) as db:
            columns = {row[1] for row in db.execute(
                "PRAGMA table_info(paper_account_cutover_ledger_snapshots)"
            )}
            self.assertTrue({
                "cutover_id", "strategy_id", "snapshot_at_ms",
                "position_base", "average_entry_price", "realized_pnl_quote",
                "fees_quote", "funding_quote", "source_snapshot_id",
                "payload_hash",
            }.issubset(columns))
            rows = db.execute(
                """SELECT DISTINCT snapshot_at_ms,source_snapshot_id,payload_hash
                   FROM paper_account_cutover_ledger_snapshots
                   WHERE cutover_id='fixture-account-cutover'"""
            ).fetchall()
        self.assertEqual(rows, [(self.fixture.now, "fixture:account-cutover", "sha256:" + "b" * 64)])


