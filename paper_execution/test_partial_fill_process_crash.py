"""Kill real PaperLedger partial-fill transactions and prove SQLite atomic recovery."""

import multiprocessing
import sqlite3
import unittest
from decimal import Decimal
from pathlib import Path

from paper_execution.ledger import PaperLedger


RISK_LIMITS = {
    "maxDrawdownPct": "50",
    "maxDailyLossUsdt": "50",
    "maxExposureUsdt": "1000",
}


def _partial_fill_crash_worker(
    database_path, intent, book, now_ms, checkpoint_name, checkpoint_reached,
    release_checkpoint,
):
    ledger = PaperLedger(
        database_path,
        max_position_base="1",
        fee_rate="0.001",
        strategy_id="STRATEGY_CORE",
        source_sha="c" * 40,
        risk_limits=RISK_LIMITS,
        require_risk_limits=True,
        apply_migrations=False,
    )
    original_connect = ledger.connect

    def connect_with_checkpoint(*, create=None):
        connection = original_connect(create=create)

        def checkpoint(name):
            if name == checkpoint_name:
                checkpoint_reached.set()
                release_checkpoint.wait(120)
            return 0

        connection.create_function("paper_crash_checkpoint", 1, checkpoint)
        return connection

    ledger.connect = connect_with_checkpoint
    ledger.submit(intent, book, now_ms, strategy_event="ENTRY")


class PartialFillProcessCrashRecoveryTest(unittest.TestCase):
    def setUp(self):
        from paper_execution.test_core_first_operational import CoreFirstOperationalProofTest

        self.fixture = CoreFirstOperationalProofTest(
            "test_core_signal_flows_through_shared_risk_into_paper_ledger"
        )
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)

    def _partial_fill_input(self, suffix):
        signal = self.fixture.decide()
        self.assertEqual(signal["action"], "BUY", signal)
        intent = dict(signal["intent"])
        intent.update({
            "intentId": "partial-fill-crash-" + suffix,
            "decisionAtMs": self.fixture.now + 1,
            "validUntilMs": self.fixture.now + 30_001,
            "inputSnapshotId": "fixture:partial-fill-crash-" + suffix,
        })
        target = Decimal(intent["targetPositionBase"])
        self.assertGreater(target, 0)
        book = dict(self.fixture.book)
        book["observedAtMs"] = self.fixture.now + 1
        book["asks"] = [{
            "price": intent["limitPrice"],
            "quantity": str(target / 2),
        }]
        return intent, book

    def _copy_database(self, destination):
        with sqlite3.connect(self.fixture.path) as source, sqlite3.connect(destination) as target:
            source.backup(target)

    @staticmethod
    def _state(database_path, intent_id):
        with sqlite3.connect(database_path, timeout=10) as connection:
            connection.execute("PRAGMA foreign_keys=ON")
            integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
            foreign_key_errors = connection.execute("PRAGMA foreign_key_check").fetchall()
            strategy_state = connection.execute(
                """SELECT position_base,average_entry_price,realized_pnl_quote,
                          fees_quote,dca_used,initial_margin_quote,version
                   FROM paper_strategy_ledgers
                   WHERE account_id=1 AND strategy_id='STRATEGY_CORE'"""
            ).fetchone()
            risk_state = connection.execute(
                """SELECT last_equity_quote,high_water_mark_quote,updated_at_ms,version
                   FROM paper_account_risk_state WHERE account_id=1"""
            ).fetchone()
            journal_count = connection.execute(
                "SELECT COUNT(*) FROM paper_account_event_journal WHERE intent_id=?",
                (intent_id,),
            ).fetchone()[0]
            order_count = connection.execute(
                "SELECT COUNT(*) FROM paper_orders WHERE intent_id=?",
                (intent_id,),
            ).fetchone()[0]
            reservation_count = connection.execute(
                "SELECT COUNT(*) FROM paper_risk_reservations WHERE intent_id=?",
                (intent_id,),
            ).fetchone()[0]
            book_reservation_count = connection.execute(
                """SELECT COUNT(*) FROM paper_book_level_reservations level
                   JOIN paper_risk_reservations reservation
                     ON reservation.reservation_id=level.reservation_id
                   WHERE reservation.intent_id=?""",
                (intent_id,),
            ).fetchone()[0]
            audit_count = connection.execute(
                """SELECT COUNT(*) FROM paper_audit
                   WHERE kind='SUBMIT' AND instr(document,?)>0""",
                (intent_id,),
            ).fetchone()[0]
        return {
            "integrity": integrity,
            "foreign_key_errors": foreign_key_errors,
            "strategy_state": strategy_state,
            "risk_state": risk_state,
            "journal_count": journal_count,
            "order_count": order_count,
            "reservation_count": reservation_count,
            "book_reservation_count": book_reservation_count,
            "audit_count": audit_count,
        }

    def _crash_at_checkpoint(self, checkpoint_name, suffix):
        intent, book = self._partial_fill_input(suffix)
        database_path = Path(self.fixture.temp.name) / (suffix + ".sqlite3")
        self._copy_database(database_path)

        trigger_name = "crash_" + suffix.replace("-", "_")
        if checkpoint_name == "after_fill_journal":
            trigger_sql = f"""
                CREATE TRIGGER {trigger_name}
                AFTER INSERT ON paper_account_event_journal
                WHEN NEW.intent_id='{intent["intentId"]}'
                BEGIN
                    SELECT paper_crash_checkpoint('after_fill_journal');
                END
            """
        elif checkpoint_name == "before_commit":
            trigger_sql = f"""
                CREATE TRIGGER {trigger_name}
                AFTER INSERT ON paper_audit
                WHEN NEW.kind='SUBMIT'
                  AND instr(NEW.document, '"intentId":"{intent["intentId"]}"')>0
                BEGIN
                    SELECT paper_crash_checkpoint('before_commit');
                END
            """
        else:
            self.fail("Unsupported crash checkpoint")

        with sqlite3.connect(database_path) as connection:
            connection.execute(trigger_sql)

        baseline = self._state(database_path, intent["intentId"])
        self.assertEqual(baseline["integrity"], "ok")
        self.assertEqual(baseline["journal_count"], 0)
        self.assertEqual(baseline["order_count"], 0)
        self.assertEqual(baseline["reservation_count"], 0)
        self.assertEqual(baseline["book_reservation_count"], 0)
        self.assertEqual(baseline["audit_count"], 0)

        context = multiprocessing.get_context("spawn")
        checkpoint_reached = context.Event()
        release_checkpoint = context.Event()
        process = context.Process(
            target=_partial_fill_crash_worker,
            args=(
                str(database_path), intent, book, self.fixture.now + 1,
                checkpoint_name, checkpoint_reached, release_checkpoint,
            ),
        )
        process.start()
        try:
            self.assertTrue(
                checkpoint_reached.wait(timeout=20),
                f"writer did not reach {checkpoint_name}; exit={process.exitcode}",
            )
            process.terminate()
            process.join(timeout=10)
            self.assertFalse(process.is_alive(), "partial-fill writer survived termination")
        finally:
            release_checkpoint.set()
            if process.is_alive():
                process.kill()
                process.join(timeout=5)

        self.assertIsNotNone(process.exitcode)
        self.assertNotEqual(process.exitcode, 0, "writer exited normally instead of being killed")

        after_crash = self._state(database_path, intent["intentId"])
        self.assertEqual(after_crash, baseline)
        self.assertEqual(after_crash["integrity"], "ok")
        self.assertEqual(after_crash["foreign_key_errors"], [])

        recovered = PaperLedger(
            database_path,
            max_position_base="1",
            fee_rate="0.001",
            strategy_id="STRATEGY_CORE",
            source_sha="c" * 40,
            risk_limits=RISK_LIMITS,
            require_risk_limits=True,
            apply_migrations=False,
        )
        self.assertEqual(recovered.snapshot()["positionBase"], "0")

        with sqlite3.connect(database_path) as connection:
            connection.execute(f"DROP TRIGGER {trigger_name}")

        retried = recovered.submit(
            intent, book, self.fixture.now + 1, strategy_event="ENTRY",
        )
        self.assertEqual(retried["status"], "PARTIALLY_FILLED", retried)
        self.assertGreater(Decimal(retried["filledBase"]), 0)
        self.assertGreater(Decimal(retried["remainingBase"]), 0)
        committed = self._state(database_path, intent["intentId"])
        self.assertEqual(committed["integrity"], "ok")
        self.assertEqual(committed["foreign_key_errors"], [])
        self.assertEqual(committed["journal_count"], 1)
        self.assertEqual(committed["order_count"], 1)
        self.assertEqual(committed["reservation_count"], 1)
        self.assertEqual(committed["book_reservation_count"], 1)
        self.assertEqual(committed["audit_count"], 1)
        self.assertGreater(Decimal(committed["strategy_state"][0]), 0)

    def test_process_kill_after_fill_journal_insert_rolls_back_partial_fill(self):
        self._crash_at_checkpoint("after_fill_journal", "after-journal")

    def test_process_kill_after_all_writes_before_commit_rolls_back_partial_fill(self):
        self._crash_at_checkpoint("before_commit", "before-commit")


if __name__ == "__main__":
    unittest.main()
