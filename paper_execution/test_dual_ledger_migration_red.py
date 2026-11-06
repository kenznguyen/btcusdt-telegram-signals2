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
        self.assertEqual(migration, [(1, "APPLIED"), (2, "APPLIED"), (3, "APPLIED"), (4, "APPLIED"), (5, "APPLIED"), (6, "APPLIED")])
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
            "paper_legacy_book_consumptions",
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


    def test_v2_legacy_book_consumption_migration_is_additive_and_idempotent(self):
        legacy_state, legacy_owner, order_count = self.make_legacy_database()
        PaperLedger(
            self.path, max_position_base="1", strategy_id="STRATEGY_CORE",
            source_sha="c" * 40,
        )
        with sqlite3.connect(self.path) as connection:
            migrations = connection.execute(
                "SELECT version,name,checksum,status FROM paper_schema_migrations ORDER BY version"
            ).fetchall()
            columns = {
                row[1] for row in connection.execute(
                    "PRAGMA table_info(paper_legacy_book_consumptions)"
                )
            }
            foreign_keys = connection.execute(
                "PRAGMA foreign_key_list(paper_legacy_book_consumptions)"
            ).fetchall()
            unique_indexes = []
            for index in connection.execute(
                "PRAGMA index_list(paper_legacy_book_consumptions)"
            ).fetchall():
                if index[2]:
                    unique_indexes.append({
                        row[2] for row in connection.execute(
                            f"PRAGMA index_info({index[1]})"
                        )
                    })
            preserved = connection.execute(
                "SELECT position,average,realized,fees FROM paper_state WHERE id=1"
            ).fetchone()
            owner = connection.execute(
                "SELECT owner,dca_used,initial_margin_quote FROM paper_strategy_state WHERE id=1"
            ).fetchone()
            orders = connection.execute(
                "SELECT COUNT(*) FROM paper_orders"
            ).fetchone()[0]

        self.assertEqual([row[0] for row in migrations], [1, 2, 3, 4, 5, 6])
        self.assertEqual(migrations[1][1], "legacy_book_depth_v2")
        self.assertEqual(len(migrations[1][2]), 64)
        self.assertEqual(migrations[1][3], "APPLIED")
        self.assertTrue({
            "consumption_id", "account_id", "intent_id", "book_id", "side",
            "price", "consumed_quantity", "reconciliation_id", "evidence_hash",
            "created_at_ms",
        }.issubset(columns))
        self.assertTrue(any(
            row[2] == "paper_orders" and row[3] == "intent_id"
            for row in foreign_keys
        ))
        self.assertIn({"intent_id", "book_id", "side", "price"}, unique_indexes)
        self.assertEqual(preserved, legacy_state)
        self.assertEqual(owner, legacy_owner)
        self.assertEqual(orders, order_count)

        PaperLedger(
            self.path, max_position_base="1", strategy_id="AI_FREQAI",
            source_sha="c" * 40,
        )
        PaperLedger(
            self.path, max_position_base="1", strategy_id="STRATEGY_CORE",
            source_sha="c" * 40,
        )
        with sqlite3.connect(self.path) as connection:
            counts = connection.execute(
                "SELECT version,COUNT(*) FROM paper_schema_migrations GROUP BY version ORDER BY version"
            ).fetchall()
            preserved_after_reopen = connection.execute(
                "SELECT position,average,realized,fees FROM paper_state WHERE id=1"
            ).fetchone()
        self.assertEqual(counts, [(1, 1), (2, 1), (3, 1), (4, 1), (5, 1), (6, 1)])
        self.assertEqual(preserved_after_reopen, legacy_state)


    def test_v2_legacy_book_consumptions_are_immutable_and_hash_format_is_enforced(self):
        self.make_legacy_database()
        PaperLedger(
            self.path, max_position_base="1", strategy_id="STRATEGY_CORE",
            source_sha="d" * 40,
        )
        with sqlite3.connect(self.path) as connection:
            connection.execute("PRAGMA foreign_keys=ON")
            connection.execute(
                """INSERT INTO paper_orders
                   (intent_id,payload_hash,order_id,status,document)
                   VALUES ('legacy-invalid-evidence','payload','legacy-invalid-order','REJECTED','{}')"""
            )
            with self.assertRaises(sqlite3.IntegrityError):
                connection.execute(
                    """INSERT INTO paper_legacy_book_consumptions
                       (consumption_id,account_id,intent_id,book_id,side,price,
                        consumed_quantity,reconciliation_id,evidence_hash,created_at_ms)
                       VALUES ('invalid-hash',1,'legacy-invalid-evidence','book-invalid',
                               'SELL','100','0.01','reconcile-invalid',?,?)""",
                    ("sha256:" + "g" * 64, self.now),
                )
            connection.execute(
                """INSERT INTO paper_orders
                   (intent_id,payload_hash,order_id,status,document)
                   VALUES ('legacy-valid-evidence','payload','legacy-valid-order','REJECTED','{}')"""
            )
            connection.execute(
                """INSERT INTO paper_legacy_book_consumptions
                   (consumption_id,account_id,intent_id,book_id,side,price,
                    consumed_quantity,reconciliation_id,evidence_hash,created_at_ms)
                   VALUES ('valid-consumption',1,'legacy-valid-evidence','book-valid',
                           'SELL','100','0.01','reconcile-valid',?,?)""",
                ("sha256:" + "a" * 64, self.now),
            )
            with self.assertRaisesRegex(sqlite3.IntegrityError, "LEGACY_BOOK_CONSUMPTION_IMMUTABLE"):
                connection.execute(
                    "UPDATE paper_legacy_book_consumptions SET consumed_quantity='0.02' WHERE consumption_id='valid-consumption'"
                )
            with self.assertRaisesRegex(sqlite3.IntegrityError, "LEGACY_BOOK_CONSUMPTION_IMMUTABLE"):
                connection.execute(
                    "DELETE FROM paper_legacy_book_consumptions WHERE consumption_id='valid-consumption'"
                )
            row = connection.execute(
                "SELECT consumed_quantity,evidence_hash FROM paper_legacy_book_consumptions WHERE consumption_id='valid-consumption'"
            ).fetchone()
        self.assertEqual(row, ("0.01", "sha256:" + "a" * 64))


    def test_v3_reservation_expiry_migration_is_additive_and_idempotent(self):
        self.make_legacy_database()
        PaperLedger(
            self.path, max_position_base="1", strategy_id="STRATEGY_CORE",
            source_sha="e" * 40,
        )
        with sqlite3.connect(self.path) as connection:
            migrations = connection.execute(
                "SELECT version,name,status FROM paper_schema_migrations ORDER BY version"
            ).fetchall()
            columns = {
                row[1] for row in connection.execute(
                    "PRAGMA table_info(paper_risk_reservations)"
                )
            }
            indexes = {
                row[1] for row in connection.execute(
                    "PRAGMA index_list(paper_risk_reservations)"
                )
            }
        self.assertEqual(migrations, [
            (1, "dual_ledger_v1", "APPLIED"),
            (2, "legacy_book_depth_v2", "APPLIED"),
            (3, "reservation_expiry_v3", "APPLIED"),
            (4, "funding_provenance_v4", "APPLIED"),
            (5, "account_equity_cutover_v5", "APPLIED"),
            (6, "account_history_journal_v6", "APPLIED"),
        ])
        self.assertIn("expires_at_ms", columns)
        self.assertIn("paper_risk_reservations_expiry", indexes)

        PaperLedger(
            self.path, max_position_base="1", strategy_id="AI_FREQAI",
            source_sha="e" * 40,
        )
        PaperLedger(
            self.path, max_position_base="1", strategy_id="STRATEGY_CORE",
            source_sha="e" * 40,
        )
        with sqlite3.connect(self.path) as connection:
            counts = connection.execute(
                "SELECT version,COUNT(*) FROM paper_schema_migrations GROUP BY version ORDER BY version"
            ).fetchall()
        self.assertEqual(counts, [(1, 1), (2, 1), (3, 1), (4, 1), (5, 1)])


if __name__ == "__main__":
    unittest.main()
