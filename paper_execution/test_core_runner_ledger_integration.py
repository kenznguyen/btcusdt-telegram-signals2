"""Disposable SQLite integration contracts for Core Runner ledger outcomes."""

import sqlite3
import unittest
from decimal import Decimal

from paper_execution.test_core_first_operational import CoreFirstOperationalProofTest


class CoreRunnerLedgerIntegrationTest(unittest.TestCase):
    def setUp(self):
        self.fixture = CoreFirstOperationalProofTest()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)

    def entry_fixture(self, suffix):
        signal = self.fixture.decide()
        self.assertEqual(signal["action"], "BUY", signal)
        intent = dict(signal["intent"])
        intent.update({
            "intentId": "core-runner-ledger-" + suffix,
            "decisionAtMs": self.fixture.now + 1,
            "validUntilMs": self.fixture.now + 30_001,
            "inputSnapshotId": "fixture:core-runner-ledger-" + suffix,
        })
        book = dict(self.fixture.book)
        book["observedAtMs"] = self.fixture.now + 1
        return intent, book

    def test_open_partially_filled_and_filled_are_distinct_paper_outcomes(self):
        # OPEN: a valid but non-crossing ask leaves the full quantity unfilled.
        open_intent, open_book = self.entry_fixture("open")
        limit = Decimal(open_intent["limitPrice"])
        open_book["asks"] = [{
            "price": str(limit * Decimal("1.001")),
            "quantity": "1",
        }]
        opened = self.fixture.core.submit(
            open_intent, open_book, self.fixture.now + 1, strategy_event="ENTRY",
        )
        self.assertEqual(opened["status"], "OPEN", opened)
        self.assertEqual(opened["filledBase"], "0")

        # PARTIALLY_FILLED: visible depth is positive but smaller than target.
        partial_intent, partial_book = self.entry_fixture("partial")
        quantity = Decimal(partial_intent["targetPositionBase"])
        partial_book["asks"] = [{
            "price": partial_intent["limitPrice"],
            "quantity": str(quantity / 2),
        }]
        partial = self.fixture.core.submit(
            partial_intent, partial_book, self.fixture.now + 1,
            strategy_event="ENTRY",
        )
        self.assertEqual(partial["status"], "PARTIALLY_FILLED", partial)
        self.assertGreater(Decimal(partial["filledBase"]), 0)
        self.assertGreater(Decimal(partial["remainingBase"]), 0)

        # FILLED: the default disposable book has sufficient visible depth.
        filled_intent, filled_book = self.entry_fixture("filled")
        filled = self.fixture.core.submit(
            filled_intent, filled_book, self.fixture.now + 1,
            strategy_event="ENTRY",
        )
        self.assertEqual(filled["status"], "FILLED", filled)
        self.assertEqual(filled["remainingBase"], "0")

    def test_idempotent_retry_returns_same_order_without_duplicate_rows(self):
        intent, book = self.entry_fixture("idempotent")
        first = self.fixture.core.submit(
            intent, book, self.fixture.now + 1, strategy_event="ENTRY",
        )
        retry = self.fixture.core.submit(
            intent, book, self.fixture.now + 1, strategy_event="ENTRY",
        )
        self.assertEqual(retry, first)
        with sqlite3.connect(self.fixture.path) as connection:
            count = connection.execute(
                "SELECT COUNT(*) FROM paper_orders WHERE intent_id=?",
                (intent["intentId"],),
            ).fetchone()[0]
        self.assertEqual(count, 1)

    def test_kill_switch_blocks_new_entry_transactionally(self):
        intent, book = self.entry_fixture("killed")
        self.fixture.core.set_killed(True, self.fixture.now + 1, "FIXTURE_KILL")
        rejected = self.fixture.core.submit(
            intent, book, self.fixture.now + 1, strategy_event="ENTRY",
        )
        self.assertEqual(rejected["status"], "REJECTED", rejected)
        self.assertEqual(rejected["reason"], "KILL_SWITCH")
        self.assertEqual(self.fixture.core.snapshot()["positionBase"], "0")

    def test_risk_unready_allows_only_a_strict_position_reduction(self):
        intent, book = self.entry_fixture("risk-unready-entry")
        entry = self.fixture.core.submit(
            intent, book, self.fixture.now + 1, strategy_event="ENTRY",
        )
        self.assertEqual(entry["status"], "FILLED", entry)
        current = Decimal(self.fixture.core.snapshot()["positionBase"])
        with sqlite3.connect(self.fixture.path) as connection:
            connection.execute(
                """UPDATE paper_account_risk_state
                   SET risk_ready=0,unavailable_reason='FIXTURE_RISK_UNREADY'
                   WHERE account_id=1"""
            )

        exit_intent = dict(intent)
        exit_intent.update({
            "intentId": "core-runner-risk-unready-exit",
            "targetPositionBase": str(current / 2),
            "decisionAtMs": self.fixture.now + 2,
            "validUntilMs": self.fixture.now + 30_002,
            "inputSnapshotId": "fixture:core-runner-risk-unready-exit",
        })
        exit_book = dict(book)
        exit_book["observedAtMs"] = self.fixture.now + 2
        exit_book["bids"] = [{
            "price": intent["limitPrice"], "quantity": "1",
        }]
        exit_book["asks"] = [{
            "price": str(Decimal(intent["limitPrice"]) + Decimal("0.01")),
            "quantity": "1",
        }]
        reduced = self.fixture.core.submit(
            exit_intent, exit_book, self.fixture.now + 2, strategy_event="EXIT",
        )
        self.assertEqual(reduced["status"], "FILLED", reduced)
        self.assertEqual(
            Decimal(self.fixture.core.snapshot()["positionBase"]), current / 2,
        )

        dca_intent = dict(intent)
        dca_intent.update({
            "intentId": "core-runner-risk-unready-dca",
            "targetPositionBase": str(current * Decimal("1.1")),
            "decisionAtMs": self.fixture.now + 3,
            "validUntilMs": self.fixture.now + 30_003,
            "inputSnapshotId": "fixture:core-runner-risk-unready-dca",
        })
        dca_book = dict(exit_book)
        dca_book["observedAtMs"] = self.fixture.now + 3
        blocked = self.fixture.core.submit(
            dca_intent, dca_book, self.fixture.now + 3, strategy_event="DCA",
        )
        self.assertEqual(blocked["status"], "REJECTED", blocked)
        self.assertEqual(blocked["reason"], "RISK_INPUTS_UNAVAILABLE")


if __name__ == "__main__":
    unittest.main()
