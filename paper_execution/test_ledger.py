from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest

from paper_execution.ledger import PaperLedger


class PaperLedgerTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "shared.sqlite3"
        self.ledger = PaperLedger(self.path, max_position_base="1", fee_rate="0.001")
        self.now = 1_800_000_000_000

    def intent(self, identifier="intent-1", target="0.1", limit="100.1"):
        return dict(intentId=identifier, symbol="BTCUSDT", exchange="binance", marketType="USDT_PERPETUAL",
                    strategyVersion="strategy-1", modelVersion="model-1", datasetVersion="sha256:dataset",
                    targetPositionBase=target, limitPrice=limit, decisionAtMs=self.now-100,
                    validUntilMs=self.now+30_000, inputSnapshotId="intel:1", mode="PAPER")

    def book(self, ask_quantity="1", time=None):
        return dict(source="hummingbot", connector="binance_perpetual", symbol="BTCUSDT",
                    observedAtMs=self.now if time is None else time,
                    bids=[dict(price="100", quantity="1")],
                    asks=[dict(price="100.1", quantity=ask_quantity)])

    def test_fills_visible_depth_and_persists_position_fee_and_identity(self):
        order = self.ledger.submit(self.intent(), self.book(), self.now)
        self.assertEqual(order["status"], "FILLED")
        self.assertEqual(order["filledBase"], "0.1")
        self.assertEqual(order["feeQuote"], "0.01001")
        state = PaperLedger(self.path).snapshot()
        self.assertEqual(state["positionBase"], "0.1")
        self.assertEqual(state["averageEntryPrice"], "100.1")
        self.assertEqual(state["feesQuote"], "0.01001")
        self.assertEqual(state["orders"][0]["orderId"], order["orderId"])
        self.assertFalse(state["liveTradingSupported"])

    def test_retry_does_not_fill_twice_even_paused_expired_or_book_missing(self):
        intent = self.intent()
        original = self.ledger.submit(intent, self.book(), self.now)
        self.ledger.set_paused(True, self.now+1)
        self.assertEqual(self.ledger.submit(intent, None, self.now+100_000), original)
        self.assertEqual(self.ledger.snapshot()["positionBase"], "0.1")
        with self.assertRaises(ValueError):
            self.ledger.submit({**intent, "targetPositionBase": "0.2"}, self.book(), self.now)

    def test_partial_fill_blocks_another_intent_until_cancel_then_requires_new_snapshot(self):
        order = self.ledger.submit(self.intent(target="0.2"), self.book("0.05"), self.now)
        self.assertEqual(order["status"], "PARTIALLY_FILLED")
        self.assertEqual(order["filledBase"], "0.05")
        self.assertEqual(order["remainingBase"], "0.15")
        rejected = self.ledger.submit(self.intent("intent-2", "0.3"), self.book(), self.now)
        self.assertEqual(rejected["reason"], "PENDING_ORDER")
        self.assertEqual(self.ledger.cancel(order["orderId"], self.now+1)["status"], "CANCELED")
        rejected = self.ledger.submit(self.intent("intent-3", "0.3"), self.book("0.05"), self.now+1)
        self.assertEqual(rejected["reason"], "SNAPSHOT_ALREADY_USED")
        filled = self.ledger.submit(self.intent("intent-4", "0.1"), self.book(time=self.now+2), self.now+2)
        self.assertEqual(filled["status"], "FILLED")
        self.assertEqual(self.ledger.snapshot()["positionBase"], "0.1")

    def test_nonmarketable_limit_remains_open_without_automatic_future_fill(self):
        order = self.ledger.submit(self.intent(limit="100"), self.book(), self.now)
        self.assertEqual(order["status"], "OPEN")
        self.assertEqual(order["filledBase"], "0")
        self.assertIsNone(order["averagePrice"])
        self.assertEqual(self.ledger.snapshot()["positionBase"], "0")
        self.assertEqual(self.ledger.cancel(order["orderId"], self.now+1)["status"], "CANCELED")
        self.assertEqual(self.ledger.cancel(order["orderId"], self.now+2)["status"], "CANCELED")

    def test_pause_expiry_spread_and_position_limit_are_persisted_rejections(self):
        self.ledger.set_paused(True, self.now)
        self.assertEqual(self.ledger.submit(self.intent(), self.book(), self.now)["reason"], "PAUSED")
        self.assertTrue(PaperLedger(self.path).snapshot()["paused"])
        self.ledger.set_paused(False, self.now)
        self.assertEqual(self.ledger.submit(self.intent("expired"), self.book(), self.now+30_001)["reason"], "EXPIRED_INTENT")
        self.assertEqual(self.ledger.submit(self.intent("large", "1.01"), self.book(), self.now)["reason"], "POSITION_LIMIT")
        book = self.book()
        book["asks"][0]["price"] = "101"
        self.assertEqual(self.ledger.submit(self.intent("spread"), book, self.now)["reason"], "SPREAD_LIMIT")

    def test_invalid_stale_future_crossed_and_duplicate_books_never_fill(self):
        bad = [None, {**self.book(), "symbol": "ETHUSDT"}, self.book(time=self.now-30_001),
               self.book(time=self.now+5_001), {**self.book(), "bids": []},
               {**self.book(), "asks": [{"price": "99", "quantity": "1"}]},
               {**self.book(), "asks": [{"price": "100.1", "quantity": "NaN"}]},
               {**self.book(), "bids": [{"price": "100", "quantity": "1"}]*2}]
        for index, book in enumerate(bad):
            with self.subTest(book=book):
                self.assertEqual(self.ledger.submit(self.intent(f"bad-{index}"), book, self.now)["status"], "REJECTED")
        self.assertEqual(self.ledger.snapshot()["positionBase"], "0")

    def test_wrong_market_live_intent_and_invalid_numbers_raise_without_ledger_effects(self):
        for changes in ({"mode": "LIVE"}, {"symbol": "ETHUSDT"}, {"targetPositionBase": "NaN"},
                        {"limitPrice": "0"}, {"decisionAtMs": True}, {"validUntilMs": self.now+120_000}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.ledger.submit({**self.intent(), **changes}, self.book(), self.now)
        self.assertEqual(self.ledger.snapshot()["orders"], [])

    def test_reduce_and_reverse_preserve_cost_basis_and_realized_pnl(self):
        self.ledger.submit(self.intent(target="0.2"), self.book(), self.now)
        book = self.book(time=self.now+1)
        book["bids"] = [{"price": "101", "quantity": "1"}]
        book["asks"] = [{"price": "101.1", "quantity": "1"}]
        self.ledger.submit(self.intent("reduce", "0.1", "101"), book, self.now+1)
        state = self.ledger.snapshot()
        self.assertEqual(state["realizedPnlQuote"], "0.09")
        self.assertEqual(state["averageEntryPrice"], "100.1")
        book["observedAtMs"] = self.now+2
        self.ledger.submit(self.intent("reverse", "-0.1", "101"), book, self.now+2)
        state = self.ledger.snapshot()
        self.assertEqual(state["positionBase"], "-0.1")
        self.assertEqual(state["realizedPnlQuote"], "0.18")
        self.assertEqual(state["averageEntryPrice"], "101")
        self.assertEqual(state["feesQuote"], "0.05032")

    def test_atomic_duplicate_concurrent_submissions_only_fill_once(self):
        intent, book = self.intent(), self.book()
        def submit(_):
            return PaperLedger(self.path, max_position_base="1").submit(intent, book, self.now)
        with ThreadPoolExecutor(max_workers=2) as pool:
            orders = list(pool.map(submit, range(2)))
        self.assertEqual(orders[0], orders[1])
        self.assertEqual(self.ledger.snapshot()["positionBase"], "0.1")
        self.assertEqual(len(self.ledger.snapshot()["orders"]), 1)

    def test_multiple_levels_fill_only_within_limit_using_quote_weighted_price(self):
        book = self.book()
        book["asks"] = [dict(price="100.1", quantity="0.03"),
                        dict(price="100.2", quantity="0.02"),
                        dict(price="100.3", quantity="1")]
        order = self.ledger.submit(self.intent(limit="100.2"), book, self.now)
        self.assertEqual(order["status"], "PARTIALLY_FILLED")
        self.assertEqual(order["filledBase"], "0.05")
        self.assertEqual(order["remainingBase"], "0.05")
        self.assertEqual(order["averagePrice"], "100.14")
        self.assertEqual(order["feeQuote"], "0.005007")

    def test_concurrent_distinct_intents_cannot_reuse_one_snapshot(self):
        book = self.book()
        intents = [self.intent("concurrent-1", "0.1"), self.intent("concurrent-2", "0.2")]
        def submit(intent):
            return PaperLedger(self.path, max_position_base="1").submit(intent, book, self.now)
        with ThreadPoolExecutor(max_workers=2) as pool:
            orders = list(pool.map(submit, intents))
        self.assertCountEqual([order["status"] for order in orders], ["FILLED", "REJECTED"])
        self.assertIn(self.ledger.snapshot()["positionBase"], {"0.1", "0.2"})

    def test_multi_level_reversal_closes_old_position_before_pricing_new_position(self):
        opening = self.book()
        opening["asks"] = [dict(price="100.02", quantity="1")]
        self.ledger.submit(self.intent(limit="100.02"), opening, self.now)
        reversing = self.book(time=self.now+1)
        reversing["bids"] = [dict(price="100", quantity="0.1"), dict(price="99", quantity="0.1")]
        reversing["asks"] = [dict(price="100.02", quantity="1")]
        order = self.ledger.submit(self.intent("reverse-levels", "-0.1", "99"), reversing, self.now+1)
        self.assertEqual(order["averagePrice"], "99.5")
        state = self.ledger.snapshot()
        self.assertEqual(state["positionBase"], "-0.1")
        self.assertEqual(state["averageEntryPrice"], "99")
        self.assertEqual(state["realizedPnlQuote"], "-0.002")

    def test_readonly_snapshot_never_creates_missing_database_or_paper_tables(self):
        from paper_execution.ledger import read_snapshot
        absent = Path(self.temp.name) / "never-created.sqlite3"
        with self.assertRaises(OSError):
            read_snapshot(absent)
        self.assertFalse(absent.exists())
        uninitialized = Path(self.temp.name) / "candles-only.sqlite3"
        with sqlite3.connect(uninitialized) as connection:
            connection.execute("CREATE TABLE candles (open_time_ms INTEGER)")
        with self.assertRaises(sqlite3.Error):
            read_snapshot(uninitialized)
        with sqlite3.connect(uninitialized) as connection:
            tables = connection.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        self.assertEqual(tables, [("candles",)])

    def test_corrupt_state_is_rejected_before_read_or_submit_and_writes_no_order(self):
        for column, value in (("position", "NaN"), ("realized", "Infinity"), ("fees", "-1"),
                              ("average", "1"), ("position", "1"), ("paused", 2),
                              ("position", "1e99999999")):
            with self.subTest(column=column, value=value):
                with sqlite3.connect(self.path) as connection:
                    connection.execute("UPDATE paper_state SET position='0',average='0',realized='0',fees='0',paused=0")
                    connection.execute(f"UPDATE paper_state SET {column}=?", (value,))
                with self.assertRaises(sqlite3.DatabaseError):
                    self.ledger.snapshot()
                with self.assertRaises(sqlite3.DatabaseError):
                    self.ledger.submit(self.intent(), self.book(), self.now)
                with sqlite3.connect(self.path) as connection:
                    self.assertEqual(connection.execute("SELECT COUNT(*) FROM paper_orders").fetchone()[0], 0)

    def test_missing_state_row_is_not_silently_reinitialized(self):
        with sqlite3.connect(self.path) as connection:
            connection.execute("DELETE FROM paper_state")
        with self.assertRaises(sqlite3.DatabaseError):
            self.ledger.snapshot()
        with self.assertRaises(sqlite3.DatabaseError):
            self.ledger.submit(self.intent(), self.book(), self.now)
        with self.assertRaises(sqlite3.DatabaseError):
            PaperLedger(self.path)
        with sqlite3.connect(self.path) as connection:
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM paper_state").fetchone()[0], 0)

    def test_explicit_local_cli_initializes_paper_state_without_changing_candles(self):
        path = Path(self.temp.name) / "initialize.sqlite3"
        with sqlite3.connect(path) as connection:
            connection.execute("CREATE TABLE candles (open_time_ms INTEGER)")
            connection.execute("INSERT INTO candles VALUES (123)")
        output = subprocess.check_output([sys.executable, "-m", "paper_execution", "--db", str(path)], text=True)
        result = json.loads(output)
        self.assertEqual(result["mode"], "PAPER")
        self.assertEqual(result["positionBase"], "0")
        self.assertFalse(result["liveTradingSupported"])
        with sqlite3.connect(path) as connection:
            self.assertEqual(connection.execute("SELECT * FROM candles").fetchall(), [(123,)])


    def test_shared_sqlite_transaction_can_rollback_paper_submit_atomically(self):
        intent = self.intent("external-transaction", "0.1")
        with self.assertRaises(RuntimeError):
            with sqlite3.connect(self.path) as connection, connection:
                connection.execute("BEGIN IMMEDIATE")
                order = self.ledger.submit(intent, self.book(), self.now, connection=connection)
                self.assertEqual(order["status"], "FILLED")
                raise RuntimeError("simulate crash before atomic commit")
        recovered = PaperLedger(self.path, max_position_base="1").snapshot()
        self.assertEqual(recovered["positionBase"], "0")
        self.assertEqual(recovered["orders"], [])

    def test_external_connection_without_active_transaction_is_rejected(self):
        with sqlite3.connect(self.path) as connection:
            with self.assertRaises(ValueError):
                self.ledger.submit(self.intent("not-transactional"), self.book(), self.now,
                                   connection=connection)
        self.assertEqual(self.ledger.snapshot()["orders"], [])


if __name__ == "__main__":
    unittest.main()
