import sqlite3
import tempfile
import unittest
from pathlib import Path

from paper_execution.ledger import PaperLedger


class DualLedgerMigrationRedTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "legacy-paper.sqlite3"
        self.now = 1_800_000_000_000

    def intent(self, intent_id="legacy-manual", target="0.1"):
        return {
            "intentId": intent_id,
            "symbol": "BTCUSDT",
            "exchange": "binance",
            "marketType": "USDT_PERPETUAL",
            "strategyVersion": "legacy-fixture",
            "modelVersion": "legacy-fixture",
            "datasetVersion": "sha256:legacy-fixture",
            "targetPositionBase": target,
            "limitPrice": "100.1",
            "decisionAtMs": self.now - 100,
            "validUntilMs": self.now + 30_000,
            "inputSnapshotId": "legacy-book",
            "mode": "PAPER",
        }

    def book(self):
        return {
            "source": "hummingbot",
            "connector": "binance_perpetual",
            "symbol": "BTCUSDT",
            "observedAtMs": self.now,
            "bids": [{"price": "100", "quantity": "1"}],
            "asks": [{"price": "100.1", "quantity": "1"}],
        }

    def make_legacy_database(self):
        legacy = PaperLedger(self.path, max_position_base="1", fee_rate="0.001")
        order = legacy.submit(self.intent(), self.book(), self.now, strategy_id="MANUAL")
        self.assertEqual(order["status"], "FILLED")
        legacy.record_equity(
            "100", self.now - 60_000, self.now, "sha256:legacy-equity", "100"
        )
        with sqlite3.connect(self.path) as connection:
            connection.execute(
                "UPDATE paper_strategy_state SET dca_used=1,initial_margin_quote='0.5' WHERE id=1"
            )
            state = connection.execute(
                "SELECT position,average,realized,fees FROM paper_state WHERE id=1"
            ).fetchone()
            owner = connection.execute(
                "SELECT owner,dca_used,initial_margin_quote FROM paper_strategy_state WHERE id=1"
            ).fetchone()
            order_count = connection.execute(
                "SELECT COUNT(*) FROM paper_orders"
            ).fetchone()[0]
        return state, owner, order_count

    def test_unknown_or_manual_owner_migrates_to_unattributed_and_blocks_readiness(self):
        legacy_state, legacy_owner, _ = self.make_legacy_database()

        PaperLedger(
            self.path, max_position_base="1", strategy_id="STRATEGY_CORE", source_sha="b" * 40
        )

        with sqlite3.connect(self.path) as connection:
            migrated = connection.execute(
                """SELECT position_base,average_entry_price,realized_pnl_quote,fees_quote,
                          dca_used,initial_margin_quote
                   FROM paper_strategy_ledgers
                   WHERE account_id=1 AND strategy_id='LEGACY_UNATTRIBUTED'"""
            ).fetchone()
            core = connection.execute(
                """SELECT position_base FROM paper_strategy_ledgers
                   WHERE account_id=1 AND strategy_id='STRATEGY_CORE'"""
            ).fetchone()
            ai = connection.execute(
                """SELECT position_base FROM paper_strategy_ledgers
                   WHERE account_id=1 AND strategy_id='AI_FREQAI'"""
            ).fetchone()
            risk = connection.execute(
                "SELECT risk_ready,unavailable_reason FROM paper_account_risk_state WHERE account_id=1"
            ).fetchone()
            migration = connection.execute(
                "SELECT version,status FROM paper_schema_migrations"
            ).fetchall()
            adjustments = dict(connection.execute(
                "SELECT adjustment_type,amount_quote FROM paper_account_adjustments"
            ).fetchall())
            legacy_after = connection.execute(
                "SELECT position,average,realized,fees FROM paper_state WHERE id=1"
            ).fetchone()
            owner_after = connection.execute(
                "SELECT owner,dca_used,initial_margin_quote FROM paper_strategy_state WHERE id=1"
            ).fetchone()

        self.assertEqual(migrated, (legacy_state[0], legacy_state[1], "0", "0", 1, "0.5"))
        self.assertEqual(adjustments["LEGACY_REALIZED_PNL"], legacy_state[2])
        self.assertEqual(adjustments["LEGACY_FEES"], legacy_state[3])
        self.assertEqual(core, ("0",))
        self.assertEqual(ai, ("0",))
        self.assertEqual(risk[0], 0)
        self.assertIsNotNone(risk[1])
        self.assertEqual(migration, [(1, "APPLIED")])
        self.assertEqual(legacy_after, legacy_state)
        self.assertEqual(owner_after, legacy_owner)

    def test_migration_is_idempotent_and_preserves_legacy_orders_and_tables(self):
        legacy_state, legacy_owner, order_count = self.make_legacy_database()

        PaperLedger(self.path, max_position_base="1", strategy_id="STRATEGY_CORE", source_sha="b" * 40)
        PaperLedger(self.path, max_position_base="1", strategy_id="AI_FREQAI", source_sha="b" * 40)
        PaperLedger(self.path, max_position_base="1", strategy_id="STRATEGY_CORE", source_sha="b" * 40)

        with sqlite3.connect(self.path) as connection:
            migration_count = connection.execute(
                "SELECT COUNT(*) FROM paper_schema_migrations WHERE version=1"
            ).fetchone()[0]
            current_legacy_state = connection.execute(
                "SELECT position,average,realized,fees FROM paper_state WHERE id=1"
            ).fetchone()
            current_legacy_owner = connection.execute(
                "SELECT owner,dca_used,initial_margin_quote FROM paper_strategy_state WHERE id=1"
            ).fetchone()
            current_order_count = connection.execute(
                "SELECT COUNT(*) FROM paper_orders"
            ).fetchone()[0]
            required_tables = {
                row[0] for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
            }

        self.assertEqual(migration_count, 1)
        self.assertEqual(current_legacy_state, legacy_state)
        self.assertEqual(current_legacy_owner, legacy_owner)
        self.assertEqual(current_order_count, order_count)
        self.assertTrue({
            "paper_state", "paper_strategy_state", "paper_orders", "paper_books",
            "paper_schema_migrations", "paper_accounts", "paper_strategy_ledgers",
            "paper_account_risk_state", "paper_risk_reservations",
            "paper_book_level_reservations", "paper_funding_events",
        }.issubset(required_tables))

    def test_corrupt_legacy_state_stops_migration_without_rewriting_legacy_data(self):
        self.make_legacy_database()
        with sqlite3.connect(self.path) as connection:
            connection.execute("UPDATE paper_state SET position='NaN' WHERE id=1")

        with self.assertRaises(sqlite3.DatabaseError):
            PaperLedger(self.path, max_position_base="1", strategy_id="STRATEGY_CORE")

        with sqlite3.connect(self.path) as connection:
            legacy_position = connection.execute(
                "SELECT position FROM paper_state WHERE id=1"
            ).fetchone()[0]
            migration_table = connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='paper_schema_migrations'"
            ).fetchone()

        self.assertEqual(legacy_position, "NaN")
        self.assertIsNone(migration_table)


if __name__ == "__main__":
    unittest.main()
