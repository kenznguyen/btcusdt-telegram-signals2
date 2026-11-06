from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
import json
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from paper_execution import ledger
from paper_execution.ledger import PaperLedger


class DualLedgerRedTest(unittest.TestCase):
    def fresh_account_db(self, filename, *, establish_cutover=True):
        path = Path(self.temp.name) / filename
        bootstrap = PaperLedger(path, max_position_base="1", fee_rate="0.001")
        bootstrap.record_equity(
            "100", self.now - 60_000, self.now, "sha256:dual-ledger-seed", "100"
        )
        limits = {"maxDrawdownPct": "50", "maxDailyLossUsdt": "50", "maxExposureUsdt": "1000"}
        core = PaperLedger(
            path, max_position_base="1", fee_rate="0.001",
            strategy_id="STRATEGY_CORE", source_sha="a" * 40,
            risk_limits=limits, require_risk_limits=True,
        )
        ai = PaperLedger(
            path, max_position_base="1", fee_rate="0.001",
            strategy_id="AI_FREQAI", source_sha="a" * 40,
            risk_limits=limits, require_risk_limits=True,
        )
        with sqlite3.connect(path) as connection:
            day = self.now // 86_400_000 * 86_400_000
            connection.execute(
                """UPDATE paper_account_risk_state SET high_water_mark_quote='100',
                   daily_baseline_utc_day_ms=?,daily_baseline_equity_quote='100',
                   last_equity_quote='100',last_mark_price='100',mark_observed_at_ms=?,
                   mark_candle_close_ms=?,dataset_version='sha256:dual-ledger-seed',
                   risk_ready=1,unavailable_reason=NULL,updated_at_ms=? WHERE account_id=1""",
                (day, self.now, self.now-60_000, self.now),
            )
        if establish_cutover:
            self.core, self.ai = core, ai
            ledger.record_funding_coverage(
                path, coverage_id="fixture-funding-coverage",
                start_at_ms=self.now - 86_400_000, end_at_ms=self.now,
                status="VERIFIED", source="FIXTURE_RECONCILED_HISTORY",
                source_snapshot_id="fixture:funding-history",
                payload_hash="sha256:" + "a" * 64,
                config_version="fixture-funding-v1", recorded_at_ms=self.now,
            )
            ledger.record_account_equity_cutover(
                path, cutover_id="fixture-account-cutover",
                expected_initial_capital_quote="100",
                expected_realized_pnl_quote="0", expected_fees_quote="0",
                expected_funding_quote="0", expected_account_equity_quote="100",
                mark_price="100", mark_candle_close_ms=self.now-60_000,
                mark_observed_at_ms=self.now,
                dataset_version="sha256:dual-ledger-seed",
                funding_coverage_start_at_ms=self.now-86_400_000,
                source="FIXTURE_RECONCILED_HISTORY",
                source_snapshot_id="fixture:account-cutover",
                payload_hash="sha256:" + "b" * 64,
                config_version="fixture-cutover-v1", recorded_at_ms=self.now,
            )
        if not establish_cutover:
            self.core, self.ai = core, ai
        return path

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.now = 1_800_000_000_000
        self.path = self.fresh_account_db("shared-account.sqlite3")

    def intent(self, intent_id, target, limit, snapshot_id):
        return {
            "intentId": intent_id,
            "symbol": "BTCUSDT",
            "exchange": "binance",
            "marketType": "USDT_PERPETUAL",
            "strategyVersion": "dual-ledger-red",
            "modelVersion": "red-test",
            "datasetVersion": "sha256:dual-ledger-fixture",
            "targetPositionBase": target,
            "limitPrice": limit,
            "decisionAtMs": self.now - 100,
            "validUntilMs": self.now + 30_000,
            "inputSnapshotId": snapshot_id,
            "mode": "PAPER",
        }

    def book(self, observed_at, bid="100", ask="100.1"):
        return {
            "source": "hummingbot",
            "connector": "binance_perpetual",
            "symbol": "BTCUSDT",
            "observedAtMs": observed_at,
            "bids": [{"price": bid, "quantity": "1"}],
            "asks": [{"price": ask, "quantity": "1"}],
        }

    def test_core_and_ai_hold_independent_positions_in_one_account_database(self):
        core_order = self.core.submit(
            self.intent("core-long", "0.1", "100.1", "core-book"),
            self.book(self.now),
            self.now,
        )
        ai_order = self.ai.submit(
            self.intent("ai-short", "-0.1", "100", "ai-book"),
            self.book(self.now + 1),
            self.now + 1,
        )

        self.assertEqual(core_order["status"], "FILLED", core_order)
        self.assertEqual(ai_order["status"], "FILLED", ai_order)

        self.assertEqual(
            self.core.snapshot()["positionBase"], "0.1"
        )
        self.assertEqual(
            self.ai.snapshot()["positionBase"], "-0.1"
        )

        reopened_core = PaperLedger(self.path, max_position_base="1", strategy_id="STRATEGY_CORE", source_sha="a" * 40)
        reopened_ai = PaperLedger(self.path, max_position_base="1", strategy_id="AI_FREQAI", source_sha="a" * 40)
        self.assertEqual(
            reopened_core.snapshot()["positionBase"], "0.1"
        )
        self.assertEqual(
            reopened_ai.snapshot()["positionBase"], "-0.1"
        )

    def test_entry_and_dca_reserve_one_percent_of_admission_time_equity_per_ledger(self):
        entry = self.core.submit(
            self.intent("core-entry", "0.1", "100.1", "core-entry"),
            self.book(self.now), self.now,
        )
        self.assertEqual(entry["status"], "FILLED", entry)
        dca = self.core.submit(
            self.intent("core-dca", "0.2", "100.1", "core-dca"),
            self.book(self.now+1), self.now+1, strategy_event="DCA",
        )
        self.assertEqual(dca["status"], "FILLED", dca)
        self.assertTrue(self.core.strategy_state()["dcaUsed"])
        self.assertFalse(self.ai.strategy_state()["dcaUsed"])

        with sqlite3.connect(self.path) as connection:
            rows = connection.execute(
                """SELECT reservation_kind,equity_basis_quote,reserved_margin_quote,
                          reserved_notional_quote,status
                   FROM paper_risk_reservations WHERE strategy_id='STRATEGY_CORE'
                   ORDER BY created_at_ms"""
            ).fetchall()
        self.assertEqual([row[0] for row in rows], ["ENTRY", "DCA"])
        for _, basis, margin, notional, status in rows:
            self.assertEqual(Decimal(margin), Decimal(basis)*Decimal("0.01"))
            self.assertEqual(Decimal(notional), Decimal(margin)*Decimal("13"))
            self.assertEqual(status, "CONSUMED")

        repeated_dca = self.core.submit(
            self.intent("core-dca-again", "0.3", "100.1", "core-dca-again"),
            self.book(self.now+2), self.now+2, strategy_event="DCA",
        )
        self.assertEqual(repeated_dca["reason"], "DCA_ALREADY_USED")

    def test_opposite_positions_are_counted_as_gross_exposure_without_netting(self):
        self.core.risk_limits["maxExposureUsdt"] = "15"
        self.ai.risk_limits["maxExposureUsdt"] = "15"
        core = self.core.submit(
            self.intent("gross-core", "0.1", "100.1", "gross-core"),
            self.book(self.now), self.now,
        )
        ai = self.ai.submit(
            self.intent("gross-ai", "-0.1", "100", "gross-ai"),
            self.book(self.now+1), self.now+1,
        )
        self.assertEqual(core["status"], "FILLED", core)
        self.assertEqual(ai["reason"], "MAX_EXPOSURE_LIMIT", ai)
        self.assertEqual(self.core.snapshot()["positionBase"], "0.1")
        self.assertEqual(self.ai.snapshot()["positionBase"], "0")

    def test_missing_account_risk_inputs_fail_closed(self):
        with sqlite3.connect(self.path) as connection:
            connection.execute(
                "UPDATE paper_account_risk_state SET risk_ready=0,unavailable_reason='TEST_MISSING' WHERE account_id=1"
            )
        order = self.core.submit(
            self.intent("risk-not-ready", "0.1", "100.1", "risk-not-ready"),
            self.book(self.now), self.now,
        )
        self.assertEqual(order["status"], "REJECTED")
        self.assertEqual(order["reason"], "RISK_INPUTS_UNAVAILABLE")
        self.assertEqual(self.core.snapshot()["positionBase"], "0")

    def test_kill_switch_blocks_increase_but_allows_strategy_scoped_reduction(self):
        opened = self.core.submit(
            self.intent("kill-open", "0.1", "100.1", "kill-open"),
            self.book(self.now), self.now,
        )
        self.assertEqual(opened["status"], "FILLED", opened)
        self.core.set_killed(True, self.now+1, "TEST_KILL")
        reduced = self.core.submit(
            self.intent("kill-reduce", "0.05", "100", "kill-reduce"),
            self.book(self.now+2), self.now+2, strategy_event="EXIT",
        )
        self.assertEqual(reduced["status"], "FILLED", reduced)
        self.assertEqual(self.core.snapshot()["positionBase"], "0.05")
        blocked = self.core.submit(
            self.intent("kill-increase", "0.08", "100.1", "kill-increase"),
            self.book(self.now+3), self.now+3, strategy_event="DCA",
        )
        self.assertEqual(blocked["reason"], "KILL_SWITCH")

    def test_shared_book_depth_is_reserved_across_core_and_ai(self):
        shared_book = self.book(self.now)
        shared_book["asks"] = [{"price": "100.1", "quantity": "0.15"}]
        core = self.core.submit(
            self.intent("book-core", "0.1", "100.1", "book-core"),
            shared_book, self.now,
        )
        ai = self.ai.submit(
            self.intent("book-ai", "0.1", "100.1", "book-ai"),
            shared_book, self.now,
        )
        self.assertEqual(core["filledBase"], "0.1")
        self.assertEqual(ai["status"], "PARTIALLY_FILLED", ai)
        self.assertEqual(ai["filledBase"], "0.05")
        self.assertEqual(self.ai.snapshot()["positionBase"], "0.05")
        with sqlite3.connect(self.path) as connection:
            used = connection.execute(
                """SELECT SUM(CAST(reserved_quantity AS REAL))
                   FROM paper_book_level_reservations WHERE book_id=? AND side='BUY'
                     AND price='100.1' AND status IN ('ACTIVE','CONSUMED')""",
                (connection.execute(
                    "SELECT book_id FROM paper_book_level_reservations LIMIT 1"
                ).fetchone()[0],),
            ).fetchone()[0]
        self.assertAlmostEqual(used, 0.15)

    def test_concurrent_core_ai_admissions_cannot_breach_gross_exposure(self):
        self.core.risk_limits["maxExposureUsdt"] = "15"
        self.ai.risk_limits["maxExposureUsdt"] = "15"
        def core_submit():
            return self.core.submit(
                self.intent("concurrent-core", "0.1", "100.1", "concurrent-core"),
                self.book(self.now), self.now,
            )
        def ai_submit():
            return self.ai.submit(
                self.intent("concurrent-ai", "0.1", "100.1", "concurrent-ai"),
                self.book(self.now+1), self.now+1,
            )
        with ThreadPoolExecutor(max_workers=2) as pool:
            core_future = pool.submit(core_submit)
            ai_future = pool.submit(ai_submit)
            results = [core_future.result(), ai_future.result()]
        self.assertCountEqual([result["status"] for result in results], ["FILLED", "REJECTED"])
        with sqlite3.connect(self.path) as connection:
            positions = connection.execute(
                "SELECT position_base FROM paper_strategy_ledgers WHERE account_id=1"
            ).fetchall()
        gross = sum((abs(Decimal(row[0]))*Decimal("100") for row in positions), Decimal(0))
        self.assertLessEqual(gross, Decimal("15"))


    def test_strategy_cannot_cancel_another_ledgers_pending_order(self):
        partial = self.core.submit(
            self.intent("core-pending", "0.12", "100.1", "core-pending"),
            {**self.book(self.now), "asks": [{"price": "100.1", "quantity": "0.05"}]}, self.now,
        )
        self.assertEqual(partial["status"], "PARTIALLY_FILLED", partial)
        with self.assertRaisesRegex(ValueError, "PAPER_ORDER_STRATEGY_SCOPE_MISMATCH"):
            self.ai.cancel(partial["orderId"], self.now+1)
        with sqlite3.connect(self.path) as connection:
            state = connection.execute(
                "SELECT status FROM paper_orders WHERE order_id=?", (partial["orderId"],)
            ).fetchone()
            reservation = connection.execute(
                """SELECT status,remaining_notional_quote FROM paper_risk_reservations
                   WHERE reservation_id=?""", (partial["reservationId"],)
            ).fetchone()
        self.assertEqual(state, ("PARTIALLY_FILLED",))
        self.assertEqual(reservation[0], "PARTIAL")
        self.assertGreater(Decimal(reservation[1]), Decimal("0"))

    def test_strategy_can_cancel_its_own_partial_order_and_release_remaining_reservation(self):
        partial = self.core.submit(
            self.intent("core-cancel-own", "0.12", "100.1", "core-cancel-own"),
            {**self.book(self.now), "asks": [{"price": "100.1", "quantity": "0.05"}]}, self.now,
        )
        self.assertEqual(partial["status"], "PARTIALLY_FILLED", partial)
        canceled = self.core.cancel(partial["orderId"], self.now+1)
        self.assertEqual(canceled["status"], "CANCELED")
        with sqlite3.connect(self.path) as connection:
            reservation = connection.execute(
                """SELECT status,remaining_margin_quote,remaining_notional_quote
                   FROM paper_risk_reservations WHERE reservation_id=?""",
                (partial["reservationId"],),
            ).fetchone()
        self.assertEqual(reservation, ("CONSUMED", "0", "0"))


    def test_partial_reservation_survives_reopen_and_reduces_other_strategy_capacity(self):
        self.core.risk_limits["maxExposureUsdt"] = "15"
        self.ai.risk_limits["maxExposureUsdt"] = "15"
        partial = self.core.submit(
            self.intent("core-restart-pending", "0.12", "100.1", "core-restart-pending"),
            {**self.book(self.now), "asks": [{"price": "100.1", "quantity": "0.05"}]},
            self.now,
        )
        self.assertEqual(partial["status"], "PARTIALLY_FILLED", partial)

        reopened_core = PaperLedger(
            self.path, max_position_base="1", strategy_id="STRATEGY_CORE",
            source_sha="a" * 40,
        )
        reopened_orders = reopened_core.snapshot()["orders"]
        self.assertTrue(any(
            order["intentId"] == "core-restart-pending" and
            order["status"] == "PARTIALLY_FILLED"
            for order in reopened_orders
        ))
        with sqlite3.connect(self.path) as connection:
            reservation = connection.execute(
                """SELECT status,remaining_notional_quote,remaining_margin_quote
                   FROM paper_risk_reservations WHERE reservation_id=?""",
                (partial["reservationId"],),
            ).fetchone()
        self.assertEqual(reservation[0], "PARTIAL")
        self.assertGreater(Decimal(reservation[1]), Decimal("0"))
        self.assertGreater(Decimal(reservation[2]), Decimal("0"))

        ai_order = self.ai.submit(
            self.intent("ai-after-core-pending", "0.03", "100.1", "ai-after-core-pending"),
            self.book(self.now+1), self.now+1,
        )
        self.assertEqual(ai_order["status"], "REJECTED", ai_order)
        self.assertEqual(ai_order["reason"], "MAX_EXPOSURE_LIMIT")


    def test_unattributed_legacy_exposure_blocks_all_new_strategy_entries(self):
        with sqlite3.connect(self.path) as connection:
            connection.execute(
                """UPDATE paper_strategy_ledgers
                   SET position_base='0.05',average_entry_price='100'
                   WHERE account_id=1 AND strategy_id='LEGACY_UNATTRIBUTED'"""
            )
            # Even if a stale or incorrectly restored readiness flag is set,
            # legacy ownership ambiguity must remain an independent hard stop.
            connection.execute(
                """UPDATE paper_account_risk_state
                   SET risk_ready=1,unavailable_reason=NULL WHERE account_id=1"""
            )
        order = self.core.submit(
            self.intent("core-blocked-by-legacy", "0.1", "100.1", "core-blocked-by-legacy"),
            self.book(self.now), self.now,
        )
        self.assertEqual(order["status"], "REJECTED", order)
        self.assertEqual(order["reason"], "LEGACY_UNATTRIBUTED_EXPOSURE")
        self.assertEqual(self.core.snapshot()["positionBase"], "0")


    def test_read_only_account_risk_snapshot_aggregates_both_ledgers_legacy_and_reservations(self):
        partial = self.core.submit(
            self.intent("snapshot-pending-core", "0.12", "100.1", "snapshot-pending-core"),
            {**self.book(self.now), "asks": [{"price": "100.1", "quantity": "0.05"}]},
            self.now,
        )
        self.assertEqual(partial["status"], "PARTIALLY_FILLED", partial)

        with sqlite3.connect(self.path) as connection:
            connection.execute(
                """UPDATE paper_strategy_ledgers
                   SET position_base='0.1',average_entry_price='100',
                       realized_pnl_quote='5',fees_quote='1',funding_quote='0.5',
                       initial_margin_quote='1'
                   WHERE account_id=1 AND strategy_id='STRATEGY_CORE'"""
            )
            connection.execute(
                """UPDATE paper_strategy_ledgers
                   SET position_base='-0.2',average_entry_price='110',
                       realized_pnl_quote='-2',fees_quote='0.5',funding_quote='-0.25',
                       initial_margin_quote='2'
                   WHERE account_id=1 AND strategy_id='AI_FREQAI'"""
            )
            connection.execute(
                """UPDATE paper_strategy_ledgers
                   SET position_base='0.05',average_entry_price='90'
                   WHERE account_id=1 AND strategy_id='LEGACY_UNATTRIBUTED'"""
            )
            connection.execute(
                """INSERT INTO paper_account_adjustments
                   (adjustment_id,account_id,strategy_id,adjustment_type,amount_quote,
                    source_table,source_hash,created_at_ms)
                   VALUES ('snapshot-legacy-pnl',1,'LEGACY_UNATTRIBUTED',
                           'LEGACY_REALIZED_PNL','4','test_fixture','legacy-pnl-hash',?)""",
                (self.now,),
            )
            connection.execute(
                """INSERT INTO paper_account_adjustments
                   (adjustment_id,account_id,strategy_id,adjustment_type,amount_quote,
                    source_table,source_hash,created_at_ms)
                   VALUES ('snapshot-legacy-fee',1,'LEGACY_UNATTRIBUTED',
                           'LEGACY_FEES','1','test_fixture','legacy-fee-hash',?)""",
                (self.now,),
            )
            connection.execute(
                """UPDATE paper_account_risk_state
                   SET high_water_mark_quote='110',
                       daily_baseline_utc_day_ms=?,
                       daily_baseline_equity_quote='108',
                       last_equity_quote='106.75',
                       last_mark_price='100',mark_observed_at_ms=?,
                       mark_candle_close_ms=?,dataset_version='sha256:snapshot-fixture',
                       risk_ready=1,unavailable_reason=NULL,updated_at_ms=?
                   WHERE account_id=1""",
                (self.now // 86_400_000 * 86_400_000, self.now,
                 self.now - 60_000, self.now),
            )

        self.core.set_killed(True, self.now + 1, "SNAPSHOT_TEST")
        with sqlite3.connect(self.path) as connection:
            before = connection.execute("SELECT total_changes()").fetchone()[0]
            reservation = connection.execute(
                """SELECT remaining_notional_quote,remaining_margin_quote
                   FROM paper_risk_reservations WHERE reservation_id=?""",
                (partial["reservationId"],),
            ).fetchone()
        snapshot = ledger.read_account_risk_snapshot(self.path, now_ms=self.now + 2)
        with sqlite3.connect(self.path) as connection:
            after = connection.execute("SELECT total_changes()").fetchone()[0]

        self.assertEqual(snapshot["mode"], "PAPER")
        self.assertTrue(snapshot["available"], snapshot)
        self.assertFalse(snapshot["liveTradingSupported"])
        self.assertEqual(Decimal(snapshot["accountEquityQuote"]), Decimal("106.75"))
        self.assertEqual(
            Decimal(snapshot["grossExposureQuote"]),
            Decimal("35") + Decimal(reservation[0]),
        )
        self.assertEqual(
            Decimal(snapshot["reservedMarginQuote"]),
            Decimal(reservation[1]),
        )
        self.assertEqual(Decimal(snapshot["maxDrawdownUsdt"]), Decimal("3.25"))
        self.assertEqual(Decimal(snapshot["dailyLossUsdt"]), Decimal("1.25"))
        self.assertTrue(snapshot["killSwitch"]["killed"])
        self.assertEqual(before, after, "Account risk snapshot must not write to SQLite")


    def test_snapshot_reports_unready_risk_state_without_promoting_it_to_ready(self):
        with sqlite3.connect(self.path) as connection:
            connection.execute(
                """UPDATE paper_account_risk_state
                   SET risk_ready=0,unavailable_reason='CUTOVER_NOT_RECONCILED'
                   WHERE account_id=1"""
            )
        snapshot = ledger.read_account_risk_snapshot(self.path, now_ms=self.now)
        self.assertTrue(snapshot["available"])
        self.assertFalse(snapshot["riskReady"])
        self.assertEqual(snapshot["unavailableReason"], "CUTOVER_NOT_RECONCILED")

    def test_snapshot_fails_closed_when_mark_is_stale(self):
        with sqlite3.connect(self.path) as connection:
            connection.execute(
                """UPDATE paper_account_risk_state
                   SET mark_observed_at_ms=?,mark_candle_close_ms=?
                   WHERE account_id=1""",
                (self.now - 31 * 60_000, self.now - 32 * 60_000),
            )
        with self.assertRaisesRegex(sqlite3.DatabaseError, "ACCOUNT_RISK_MARK_STALE_OR_INVALID"):
            ledger.read_account_risk_snapshot(self.path, now_ms=self.now)

    def test_snapshot_fails_closed_when_mark_is_non_finite(self):
        with sqlite3.connect(self.path) as connection:
            connection.execute(
                "UPDATE paper_account_risk_state SET last_mark_price='NaN' WHERE account_id=1"
            )
        with self.assertRaisesRegex(sqlite3.DatabaseError, "ACCOUNT_RISK_MARK_PRICE_INVALID"):
            ledger.read_account_risk_snapshot(self.path, now_ms=self.now)

    def test_snapshot_fails_closed_when_equity_does_not_reconcile(self):
        with sqlite3.connect(self.path) as connection:
            connection.execute(
                "UPDATE paper_account_risk_state SET last_equity_quote='99' WHERE account_id=1"
            )
        with self.assertRaisesRegex(sqlite3.DatabaseError, "ACCOUNT_EQUITY_RECONCILIATION_MISMATCH"):
            ledger.read_account_risk_snapshot(self.path, now_ms=self.now)


    def test_dedicated_legacy_reduction_closes_only_legacy_ledger(self):
        with sqlite3.connect(self.path) as connection:
            connection.execute(
                """UPDATE paper_strategy_ledgers
                   SET position_base='0.05',average_entry_price='90',
                       initial_margin_quote='0.35'
                   WHERE account_id=1 AND strategy_id='LEGACY_UNATTRIBUTED'"""
            )
            connection.execute(
                """UPDATE paper_account_risk_state
                   SET last_equity_quote='100.5',high_water_mark_quote='100.5'
                   WHERE account_id=1"""
            )
        self.core.set_killed(True, self.now + 1, "LEGACY_REDUCTION_KILL_SWITCH")
        before_reservations = sqlite3.connect(self.path).execute(
            "SELECT COUNT(*) FROM paper_risk_reservations"
        ).fetchone()[0]
        order = ledger.reduce_legacy_unattributed(
            self.path,
            self.intent("legacy-partial-close", "0.02", "100", "legacy-close-book"),
            self.book(self.now + 2),
            self.now + 2,
            reconciliation_id="legacy-close-review-001",
            evidence_hash="sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        )
        self.assertEqual(order["status"], "FILLED", order)
        self.assertEqual(order["strategyId"], "LEGACY_UNATTRIBUTED")
        self.assertEqual(order["strategyEvent"], "LEGACY_REDUCTION")
        with sqlite3.connect(self.path) as connection:
            journal = connection.execute(
                """SELECT strategy_id,event_type,quantity_delta_base,fill_price,fee_quote
                   FROM paper_account_event_journal WHERE intent_id=?""",
                ("legacy-partial-close",),
            ).fetchall()
        self.assertEqual(len(journal), 1)
        self.assertEqual(journal[0][0:2], ("LEGACY_UNATTRIBUTED", "FILL"))
        self.assertEqual(journal[0][2], "-0.03")
        self.assertEqual(journal[0][3], "100")
        self.assertEqual(Decimal(journal[0][4]), Decimal(order["feeQuote"]))

        replayed = ledger.reduce_legacy_unattributed(
            self.path,
            self.intent("legacy-partial-close", "0.02", "100", "legacy-close-book"),
            self.book(self.now + 2),
            self.now + 2,
            reconciliation_id="legacy-close-review-001",
            evidence_hash="sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        )
        self.assertEqual(replayed, order, "Retrying the same intent must replay, not consume depth twice")
        with sqlite3.connect(self.path) as connection:
            rows = {
                row[0]: row[1:]
                for row in connection.execute(
                    """SELECT strategy_id,position_base,realized_pnl_quote,fees_quote,
                              initial_margin_quote
                       FROM paper_strategy_ledgers WHERE account_id=1"""
                )
            }
            reservation_count = connection.execute(
                "SELECT COUNT(*) FROM paper_risk_reservations"
            ).fetchone()[0]
            audit = connection.execute(
                "SELECT document FROM paper_audit ORDER BY id DESC LIMIT 1"
            ).fetchone()[0]
        self.assertEqual(rows["LEGACY_UNATTRIBUTED"][0], "0.02")
        self.assertEqual(rows["STRATEGY_CORE"][0], "0")
        self.assertEqual(rows["AI_FREQAI"][0], "0")
        self.assertGreater(Decimal(rows["LEGACY_UNATTRIBUTED"][2]), Decimal("0"))
        self.assertLess(Decimal(rows["LEGACY_UNATTRIBUTED"][3]), Decimal("0.35"))
        self.assertEqual(reservation_count, before_reservations)
        self.assertIn("legacy-close-review-001", audit)
        self.assertIn("sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", audit)

    def test_legacy_reduction_path_rejects_increase_or_reversal_without_mutation(self):
        with sqlite3.connect(self.path) as connection:
            connection.execute(
                """UPDATE paper_strategy_ledgers
                   SET position_base='0.05',average_entry_price='100'
                   WHERE account_id=1 AND strategy_id='LEGACY_UNATTRIBUTED'"""
            )
        before = sqlite3.connect(self.path).execute(
            """SELECT position_base,realized_pnl_quote,fees_quote
               FROM paper_strategy_ledgers
               WHERE account_id=1 AND strategy_id='LEGACY_UNATTRIBUTED'"""
        ).fetchone()
        for target, intent_id in (("0.06", "legacy-increase"), ("-0.01", "legacy-reverse")):
            result = ledger.reduce_legacy_unattributed(
                self.path,
                self.intent(intent_id, target, "100.1", intent_id),
                self.book(self.now),
                self.now,
                reconciliation_id="legacy-close-review-002",
                evidence_hash="sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
            )
            self.assertEqual(result["status"], "REJECTED", result)
            self.assertEqual(result["reason"], "LEGACY_REDUCTION_ONLY")
        after = sqlite3.connect(self.path).execute(
            """SELECT position_base,realized_pnl_quote,fees_quote
               FROM paper_strategy_ledgers
               WHERE account_id=1 AND strategy_id='LEGACY_UNATTRIBUTED'"""
        ).fetchone()
        self.assertEqual(before, after)


    def test_legacy_depth_consumption_reduces_core_visible_depth_atomically(self):
        with sqlite3.connect(self.path) as connection:
            connection.execute(
                """UPDATE paper_strategy_ledgers
                   SET position_base='0.1',average_entry_price='100',
                       initial_margin_quote='0.5'
                   WHERE account_id=1 AND strategy_id='LEGACY_UNATTRIBUTED'"""
            )
            connection.execute(
                """UPDATE paper_account_risk_state
                   SET last_equity_quote='100',high_water_mark_quote='100'
                   WHERE account_id=1"""
            )
        shared_book = self.book(self.now)
        shared_book["bids"] = [{"price": "100", "quantity": "0.15"}]
        shared_book["asks"] = [{"price": "100.1", "quantity": "1"}]
        legacy_close = ledger.reduce_legacy_unattributed(
            self.path,
            self.intent("legacy-depth-close", "0", "100", "shared-depth-book"),
            shared_book,
            self.now,
            reconciliation_id="legacy-depth-review-001",
            evidence_hash="sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
        )
        self.assertEqual(legacy_close["status"], "FILLED", legacy_close)
        self.assertEqual(legacy_close["filledBase"], "0.1")

        core_short = self.core.submit(
            self.intent("core-after-legacy-close", "-0.1", "100", "shared-depth-book"),
            shared_book,
            self.now,
        )
        self.assertEqual(core_short["status"], "PARTIALLY_FILLED", core_short)
        self.assertEqual(core_short["filledBase"], "0.05")
        with sqlite3.connect(self.path) as connection:
            legacy_used = connection.execute(
                """SELECT SUM(CAST(consumed_quantity AS REAL))
                   FROM paper_legacy_book_consumptions
                   WHERE book_id=(SELECT book_id FROM paper_legacy_book_consumptions LIMIT 1)
                     AND side='SELL' AND price='100'"""
            ).fetchone()[0]
            core_used = connection.execute(
                """SELECT SUM(CAST(reserved_quantity AS REAL))
                   FROM paper_book_level_reservations
                   WHERE book_id=(SELECT book_id FROM paper_legacy_book_consumptions LIMIT 1)
                     AND side='SELL' AND price='100'
                     AND status IN ('ACTIVE','CONSUMED')"""
            ).fetchone()[0]
        self.assertAlmostEqual(legacy_used, 0.1)
        self.assertAlmostEqual(core_used, 0.05)
        self.assertAlmostEqual(legacy_used + core_used, 0.15)


    def test_manual_ledger_cannot_cancel_core_order_after_dual_migration(self):
        partial = self.core.submit(
            self.intent("core-owned-pending-for-manual", "0.12", "100.1", "manual-cancel-book"),
            {**self.book(self.now), "asks": [{"price": "100.1", "quantity": "0.05"}]},
            self.now,
        )
        self.assertEqual(partial["status"], "PARTIALLY_FILLED", partial)
        manual = PaperLedger(self.path, max_position_base="1")
        with self.assertRaisesRegex(ValueError, "PAPER_ORDER_STRATEGY_SCOPE_MISMATCH"):
            manual.cancel(partial["orderId"], self.now + 1)
        state = self.core.snapshot()["orders"]
        owned = next(order for order in state if order["intentId"] == "core-owned-pending-for-manual")
        self.assertEqual(owned["status"], "PARTIALLY_FILLED")


    def test_partial_reservation_expires_after_restart_and_releases_remaining_capacity(self):
        self.core.risk_limits["maxExposureUsdt"] = "15"
        self.ai.risk_limits["maxExposureUsdt"] = "15"
        partial = self.core.submit(
            self.intent("core-expiry-pending", "0.12", "100.1", "core-expiry-book"),
            {**self.book(self.now), "asks": [{"price": "100.1", "quantity": "0.05"}]},
            self.now,
        )
        self.assertEqual(partial["status"], "PARTIALLY_FILLED", partial)
        reopened_core = PaperLedger(
            self.path, max_position_base="1", strategy_id="STRATEGY_CORE",
            source_sha="a" * 40, risk_limits=self.core.risk_limits,
            require_risk_limits=True,
        )
        expiry_now = self.now + 30_001
        ai_intent = self.intent("ai-after-core-expiry", "-0.1", "100", "ai-after-expiry")
        ai_intent["decisionAtMs"] = expiry_now - 100
        ai_intent["validUntilMs"] = expiry_now + 30_000
        ai_order = self.ai.submit(ai_intent, self.book(expiry_now), expiry_now)
        self.assertEqual(ai_order["status"], "FILLED", ai_order)

        with sqlite3.connect(self.path) as connection:
            reservation = connection.execute(
                """SELECT status,remaining_notional_quote,remaining_margin_quote,expires_at_ms
                   FROM paper_risk_reservations WHERE reservation_id=?""",
                (partial["reservationId"],),
            ).fetchone()
            order_doc = connection.execute(
                "SELECT status,document FROM paper_orders WHERE intent_id='core-expiry-pending'"
            ).fetchone()
        self.assertEqual(reservation, ("EXPIRED", "0", "0", self.now + 30_000))
        expired_order = json.loads(order_doc[1])
        self.assertEqual(order_doc[0], "EXPIRED")
        self.assertEqual(expired_order["status"], "EXPIRED")
        self.assertEqual(expired_order["filledBase"], "0.05")
        self.assertEqual(expired_order["remainingBase"], "0.07")
        self.assertEqual(reopened_core.snapshot()["positionBase"], "0.05")
        self.assertEqual(self.ai.snapshot()["positionBase"], "-0.1")

        replay = reopened_core.submit(
            self.intent("core-expiry-pending", "0.12", "100.1", "core-expiry-book"),
            self.book(self.now), expiry_now,
        )
        self.assertEqual(replay["status"], "EXPIRED")
        self.assertEqual(replay["filledBase"], "0.05")

    def test_active_reservation_with_unknown_expiry_remains_blocking_after_restart(self):
        partial = self.core.submit(
            self.intent("core-expiry-unknown", "0.12", "100.1", "core-expiry-unknown-book"),
            {**self.book(self.now), "asks": [{"price": "100.1", "quantity": "0.05"}]},
            self.now,
        )
        self.assertEqual(partial["status"], "PARTIALLY_FILLED", partial)
        with sqlite3.connect(self.path) as connection:
            connection.execute(
                "UPDATE paper_risk_reservations SET expires_at_ms=NULL WHERE reservation_id=?",
                (partial["reservationId"],),
            )
        reopened_core = PaperLedger(
            self.path, max_position_base="1", strategy_id="STRATEGY_CORE",
            source_sha="a" * 40, risk_limits=self.core.risk_limits,
            require_risk_limits=True,
        )
        later = self.now + 30_001
        next_intent = self.intent("core-blocked-unknown-expiry", "0.13", "100.1", "new-book")
        next_intent["decisionAtMs"] = later - 100
        next_intent["validUntilMs"] = later + 30_000
        blocked = reopened_core.submit(next_intent, self.book(later), later)
        self.assertEqual(blocked["status"], "REJECTED", blocked)
        self.assertEqual(blocked["reason"], "PENDING_ORDER")
        with sqlite3.connect(self.path) as connection:
            reservation = connection.execute(
                "SELECT status,remaining_notional_quote,expires_at_ms FROM paper_risk_reservations WHERE reservation_id=?",
                (partial["reservationId"],),
            ).fetchone()
        self.assertEqual(reservation[0], "PARTIAL")
        self.assertGreater(Decimal(reservation[1]), Decimal("0"))
        self.assertIsNone(reservation[2])


    def test_funding_event_has_immutable_provenance_and_idempotent_accounting(self):
        with sqlite3.connect(self.path) as connection:
            connection.execute(
                """UPDATE paper_account_risk_state
                   SET risk_ready=1,unavailable_reason=NULL,
                       high_water_mark_quote='100',last_equity_quote='100'
                   WHERE account_id=1"""
            )

        event = ledger.record_funding_event(
            self.path,
            funding_event_id="okx-funding-core-001",
            strategy_id="STRATEGY_CORE",
            amount_quote="0.25",
            event_at_ms=self.now - 1_000,
            source="OKX_FUNDING_HISTORY",
            source_snapshot_id="okx:BTC-USDT-SWAP:funding:1800000000000",
            payload_hash="sha256:" + "a" * 64,
            recorded_at_ms=self.now,
        )
        replay = ledger.record_funding_event(
            self.path,
            funding_event_id="okx-funding-core-001",
            strategy_id="STRATEGY_CORE",
            amount_quote="0.25",
            event_at_ms=self.now - 1_000,
            source="OKX_FUNDING_HISTORY",
            source_snapshot_id="okx:BTC-USDT-SWAP:funding:1800000000000",
            payload_hash="sha256:" + "a" * 64,
            recorded_at_ms=self.now + 1,
        )
        self.assertEqual(event, replay)
        self.assertEqual(event["strategyId"], "STRATEGY_CORE")
        self.assertEqual(event["amountQuote"], "0.25")

        with sqlite3.connect(self.path) as connection:
            count = connection.execute(
                "SELECT COUNT(*) FROM paper_funding_events"
            ).fetchone()[0]
            funding = connection.execute(
                """SELECT funding_quote FROM paper_strategy_ledgers
                   WHERE account_id=1 AND strategy_id='STRATEGY_CORE'"""
            ).fetchone()[0]
            columns = {
                row[1] for row in connection.execute(
                    "PRAGMA table_info(paper_funding_events)"
                )
            }
        self.assertEqual(count, 1)
        self.assertEqual(Decimal(funding), Decimal("0.25"))
        self.assertTrue({"source", "recorded_at_ms"}.issubset(columns))
        snapshot = ledger.read_account_risk_snapshot(self.path, now_ms=self.now + 2)
        self.assertEqual(Decimal(snapshot["accountEquityQuote"]), Decimal("99.75"))

        with self.assertRaisesRegex(ValueError, "FUNDING_EVENT_ID_CONFLICT"):
            ledger.record_funding_event(
                self.path,
                funding_event_id="okx-funding-core-001",
                strategy_id="STRATEGY_CORE",
                amount_quote="0.5",
                event_at_ms=self.now - 1_000,
                source="OKX_FUNDING_HISTORY",
                source_snapshot_id="okx:BTC-USDT-SWAP:funding:1800000000000",
                payload_hash="sha256:" + "b" * 64,
                recorded_at_ms=self.now + 2,
            )

        with sqlite3.connect(self.path) as connection:
            with self.assertRaisesRegex(sqlite3.IntegrityError, "FUNDING_EVENT_IMMUTABLE"):
                connection.execute(
                    "UPDATE paper_funding_events SET amount_quote='9' WHERE funding_event_id=?",
                    ("okx-funding-core-001",),
                )
            with self.assertRaisesRegex(sqlite3.IntegrityError, "FUNDING_EVENT_IMMUTABLE"):
                connection.execute(
                    "DELETE FROM paper_funding_events WHERE funding_event_id=?",
                    ("okx-funding-core-001",),
                )

    def test_known_funding_without_strategy_owner_is_account_level_legacy_attribution(self):
        event = ledger.record_funding_event(
            self.path,
            funding_event_id="historical-funding-unowned-001",
            strategy_id="LEGACY_UNATTRIBUTED",
            amount_quote="0.4",
            event_at_ms=self.now - 10_000,
            source="RECONCILED_HISTORICAL_STATEMENT",
            source_snapshot_id="statement:account:cutover-001",
            payload_hash="sha256:" + "c" * 64,
            recorded_at_ms=self.now,
        )
        self.assertEqual(event["strategyId"], "LEGACY_UNATTRIBUTED")
        with sqlite3.connect(self.path) as connection:
            core = connection.execute(
                "SELECT funding_quote FROM paper_strategy_ledgers WHERE strategy_id='STRATEGY_CORE'"
            ).fetchone()[0]
            ai = connection.execute(
                "SELECT funding_quote FROM paper_strategy_ledgers WHERE strategy_id='AI_FREQAI'"
            ).fetchone()[0]
            legacy = connection.execute(
                "SELECT funding_quote FROM paper_strategy_ledgers WHERE strategy_id='LEGACY_UNATTRIBUTED'"
            ).fetchone()[0]
        self.assertEqual(core, "0")
        self.assertEqual(ai, "0")
        self.assertEqual(Decimal(legacy), Decimal("0.4"))

    def test_unknown_funding_coverage_fails_closed_and_disabled_policy_is_explicit(self):
        path = self.fresh_account_db(
            "unknown-and-disabled-coverage.sqlite3",
            establish_cutover=False,
        )
        unknown = ledger.record_funding_coverage(
            path,
            coverage_id="funding-history-unknown-001",
            start_at_ms=self.now - 86_400_000,
            end_at_ms=self.now,
            status="UNKNOWN",
            source="LEGACY_ACCOUNT_HISTORY",
            source_snapshot_id="legacy-history:unavailable:001",
            payload_hash="sha256:" + "d" * 64,
            config_version="funding-policy-v1",
            recorded_at_ms=self.now,
        )
        self.assertEqual(unknown["status"], "UNKNOWN")
        with sqlite3.connect(path) as connection:
            risk = connection.execute(
                "SELECT risk_ready,unavailable_reason FROM paper_account_risk_state WHERE account_id=1"
            ).fetchone()
        self.assertEqual(risk[0], 0)
        self.assertEqual(risk[1], "FUNDING_PROVENANCE_INCOMPLETE")

        disabled = ledger.record_funding_coverage(
            path,
            coverage_id="paper-funding-disabled-test-001",
            start_at_ms=self.now,
            end_at_ms=self.now + 60_000,
            status="DISABLED",
            source="PAPER_TEST_CONFIGURATION",
            source_snapshot_id="paper-config:funding-disabled:001",
            payload_hash="sha256:" + "e" * 64,
            config_version="paper-risk-config-v2",
            recorded_at_ms=self.now,
        )
        self.assertEqual(disabled["status"], "DISABLED")
        with sqlite3.connect(path) as connection:
            row = connection.execute(
                """SELECT status,source,source_snapshot_id,payload_hash,config_version
                   FROM paper_funding_coverage WHERE coverage_id=?""",
                ("paper-funding-disabled-test-001",),
            ).fetchone()
        self.assertEqual(row, (
            "DISABLED", "PAPER_TEST_CONFIGURATION",
            "paper-config:funding-disabled:001", "sha256:" + "e" * 64,
            "paper-risk-config-v2",
        ))

    def test_account_equity_cutover_rejects_unknown_funding_coverage(self):
        path = self.fresh_account_db("cutover-unknown.sqlite3", establish_cutover=False)
        ledger.record_funding_coverage(
            path,
            coverage_id="cutover-funding-unknown",
            start_at_ms=self.now - 86_400_000,
            end_at_ms=self.now,
            status="UNKNOWN",
            source="LEGACY_ACCOUNT_HISTORY",
            source_snapshot_id="legacy-history:unknown",
            payload_hash="sha256:" + "f" * 64,
            config_version="funding-policy-v1",
            recorded_at_ms=self.now,
        )
        with self.assertRaisesRegex(ValueError, "FUNDING_PROVENANCE_INCOMPLETE"):
            ledger.record_account_equity_cutover(
                path,
                cutover_id="cutover-blocked-unknown-funding",
                expected_initial_capital_quote="100",
                expected_realized_pnl_quote="0", expected_fees_quote="0",
                expected_funding_quote="0", expected_account_equity_quote="100",
                mark_price="100",
                mark_candle_close_ms=self.now - 60_000,
                mark_observed_at_ms=self.now,
                dataset_version="sha256:dual-ledger-seed",
                funding_coverage_start_at_ms=self.now - 86_400_000,
                source="RECONCILED_ACCOUNT_STATEMENT",
                source_snapshot_id="account-cutover:unknown-funding",
                payload_hash="sha256:" + "1" * 64,
                config_version="account-cutover-v1",
                recorded_at_ms=self.now,
            )
        with sqlite3.connect(path) as connection:
            risk = connection.execute(
                "SELECT risk_ready,unavailable_reason FROM paper_account_risk_state WHERE account_id=1"
            ).fetchone()
            count = connection.execute(
                "SELECT COUNT(*) FROM paper_account_equity_cutovers"
            ).fetchone()[0]
        self.assertEqual(risk, (0, "FUNDING_PROVENANCE_INCOMPLETE"))
        self.assertEqual(count, 0)

    def test_account_equity_cutover_reconciles_both_ledgers_and_legacy_once(self):
        path = self.fresh_account_db("cutover-verified.sqlite3", establish_cutover=False)
        ledger.record_funding_coverage(
            path,
            coverage_id="cutover-funding-verified",
            start_at_ms=self.now - 86_400_000,
            end_at_ms=self.now,
            status="VERIFIED",
            source="RECONCILED_ACCOUNT_STATEMENT",
            source_snapshot_id="account-statement:funding-window",
            payload_hash="sha256:" + "2" * 64,
            config_version="funding-policy-v1",
            recorded_at_ms=self.now,
        )
        ledger.record_funding_event(
            path,
            funding_event_id="cutover-core-funding",
            strategy_id="STRATEGY_CORE",
            amount_quote="0.3",
            event_at_ms=self.now - 1_000,
            source="RECONCILED_ACCOUNT_STATEMENT",
            source_snapshot_id="account-statement:core-funding",
            payload_hash="sha256:" + "7" * 64,
            recorded_at_ms=self.now,
        )
        ledger.record_funding_event(
            path,
            funding_event_id="cutover-ai-funding",
            strategy_id="AI_FREQAI",
            amount_quote="-0.1",
            event_at_ms=self.now - 1_000,
            source="RECONCILED_ACCOUNT_STATEMENT",
            source_snapshot_id="account-statement:ai-funding",
            payload_hash="sha256:" + "8" * 64,
            recorded_at_ms=self.now,
        )
        with sqlite3.connect(path) as connection:
            connection.execute(
                """UPDATE paper_strategy_ledgers SET position_base='0.1',
                   average_entry_price='90',realized_pnl_quote='2',
                   fees_quote='0.2',funding_quote='0.3'
                   WHERE account_id=1 AND strategy_id='STRATEGY_CORE'"""
            )
            connection.execute(
                """UPDATE paper_strategy_ledgers SET position_base='-0.05',
                   average_entry_price='110',realized_pnl_quote='-1',
                   fees_quote='0.1',funding_quote='-0.1'
                   WHERE account_id=1 AND strategy_id='AI_FREQAI'"""
            )
            connection.execute(
                """INSERT INTO paper_account_adjustments
                   (adjustment_id,account_id,strategy_id,adjustment_type,amount_quote,
                    source_table,source_hash,created_at_ms)
                   VALUES ('cutover-legacy-pnl',1,'LEGACY_UNATTRIBUTED',
                           'LEGACY_REALIZED_PNL','0.5','legacy_statement',?,?)""",
                ("sha256:" + "3" * 64, self.now),
            )
            connection.execute(
                """INSERT INTO paper_account_adjustments
                   (adjustment_id,account_id,strategy_id,adjustment_type,amount_quote,
                    source_table,source_hash,created_at_ms)
                   VALUES ('cutover-legacy-fees',1,'LEGACY_UNATTRIBUTED',
                           'LEGACY_FEES','0.1','legacy_statement',?,?)""",
                ("sha256:" + "4" * 64, self.now),
            )

        kwargs = {
            "cutover_id": "account-cutover-verified-001",
            "expected_initial_capital_quote": "100",
            "expected_realized_pnl_quote": "1.5",
            "expected_fees_quote": "0.4",
            "expected_funding_quote": "0.2",
            "expected_account_equity_quote": "102.4",
            "mark_price": "100",
            "mark_candle_close_ms": self.now - 60_000,
            "mark_observed_at_ms": self.now,
            "dataset_version": "sha256:dual-ledger-seed",
            "funding_coverage_start_at_ms": self.now - 86_400_000,
            "source": "RECONCILED_ACCOUNT_STATEMENT",
            "source_snapshot_id": "account-cutover:verified-001",
            "payload_hash": "sha256:" + "5" * 64,
            "config_version": "account-cutover-v1",
            "recorded_at_ms": self.now,
        }
        first = ledger.record_account_equity_cutover(path, **kwargs)
        replay = ledger.record_account_equity_cutover(path, **kwargs)
        self.assertEqual(first, replay)
        self.assertEqual(Decimal(first["accountEquityQuote"]), Decimal("102.4"))
        self.assertEqual(first["highWaterMarkQuote"], "102.4")
        self.assertEqual(first["dailyBaselineEquityQuote"], "102.4")
        self.assertEqual(first["dailyBaselineUtcDayMs"], self.now // 86_400_000 * 86_400_000)

        snapshot = ledger.read_account_risk_snapshot(path, now_ms=self.now)
        self.assertEqual(Decimal(snapshot["accountEquityQuote"]), Decimal("102.4"))
        self.assertTrue(snapshot["riskReady"])

        with sqlite3.connect(path) as connection:
            count = connection.execute(
                "SELECT COUNT(*) FROM paper_account_equity_cutovers"
            ).fetchone()[0]
            with self.assertRaisesRegex(sqlite3.IntegrityError, "ACCOUNT_EQUITY_CUTOVER_IMMUTABLE"):
                connection.execute(
                    """UPDATE paper_account_equity_cutovers SET account_equity_quote='999'
                       WHERE cutover_id=?""",
                    (kwargs["cutover_id"],),
                )
        self.assertEqual(count, 1)

        changed = dict(kwargs, payload_hash="sha256:" + "6" * 64)
        with self.assertRaisesRegex(ValueError, "ACCOUNT_EQUITY_CUTOVER_ID_CONFLICT"):
            ledger.record_account_equity_cutover(path, **changed)


    def test_unknown_funding_after_cutover_blocks_readiness_and_admission(self):
        ledger.record_funding_coverage(
            self.path,
            coverage_id="post-cutover-funding-gap",
            start_at_ms=self.now,
            end_at_ms=self.now + 30_000,
            status="UNKNOWN",
            source="LATE_HISTORY_GAP",
            source_snapshot_id="funding-gap:late-discovery",
            payload_hash="sha256:" + "9" * 64,
            config_version="funding-policy-v1",
            recorded_at_ms=self.now + 30_000,
        )
        with sqlite3.connect(self.path) as connection:
            connection.execute(
                "UPDATE paper_account_risk_state SET risk_ready=1,unavailable_reason=NULL WHERE account_id=1"
            )
        snapshot = ledger.read_account_risk_snapshot(self.path, now_ms=self.now)
        self.assertFalse(snapshot["riskReady"])
        self.assertEqual(snapshot["unavailableReason"], "FUNDING_PROVENANCE_INCOMPLETE")
        order = self.core.submit(
            self.intent("unknown-funding-after-cutover", "0.1", "100.1", "funding-gap-book"),
            self.book(self.now + 1),
            self.now + 1,
        )
        self.assertEqual(order["status"], "REJECTED")
        self.assertEqual(order["reason"], "RISK_INPUTS_UNAVAILABLE")

    def test_account_equity_cutover_rejects_overlapping_funding_coverage(self):
        path = self.fresh_account_db("overlapping-funding-coverage.sqlite3", establish_cutover=False)
        ledger.record_funding_coverage(
            path,
            coverage_id="coverage-overlap-first",
            start_at_ms=self.now - 86_400_000,
            end_at_ms=self.now - 43_200_000,
            status="VERIFIED",
            source="RECONCILED_FUNDING_STATEMENT",
            source_snapshot_id="funding-overlap:first",
            payload_hash="sha256:" + "a" * 64,
            config_version="funding-policy-v1",
            recorded_at_ms=self.now,
        )
        with self.assertRaisesRegex(ValueError, "FUNDING_COVERAGE_INTERVAL_OVERLAP"):
            ledger.record_funding_coverage(
                path,
                coverage_id="coverage-overlap-second",
                start_at_ms=self.now - 64_800_000,
                end_at_ms=self.now,
                status="VERIFIED",
                source="RECONCILED_FUNDING_STATEMENT",
                source_snapshot_id="funding-overlap:second",
                payload_hash="sha256:" + "b" * 64,
                config_version="funding-policy-v1",
                recorded_at_ms=self.now,
            )
        with sqlite3.connect(path) as connection:
            count = connection.execute(
                "SELECT COUNT(*) FROM paper_funding_coverage WHERE coverage_id=?",
                ("coverage-overlap-second",),
            ).fetchone()[0]
        self.assertEqual(count, 0)

    def test_account_equity_cutover_rejects_statement_total_mismatch(self):
        path = self.fresh_account_db("cutover-statement-mismatch.sqlite3", establish_cutover=False)
        ledger.record_funding_coverage(
            path,
            coverage_id="statement-mismatch-funding-coverage",
            start_at_ms=self.now - 86_400_000,
            end_at_ms=self.now,
            status="VERIFIED",
            source="RECONCILED_FUNDING_STATEMENT",
            source_snapshot_id="funding-statement:mismatch-window",
            payload_hash="sha256:" + "d" * 64,
            config_version="funding-policy-v1",
            recorded_at_ms=self.now,
        )
        with sqlite3.connect(path) as connection:
            connection.execute(
                """UPDATE paper_strategy_ledgers SET realized_pnl_quote='2'
                   WHERE account_id=1 AND strategy_id='STRATEGY_CORE'"""
            )

        with self.assertRaisesRegex(ValueError, "ACCOUNT_EQUITY_STATEMENT_TOTALS_MISMATCH"):
            ledger.record_account_equity_cutover(
                path,
                cutover_id="statement-total-mismatch-cutover",
                expected_initial_capital_quote="100",
                expected_realized_pnl_quote="0",
                expected_fees_quote="0",
                expected_funding_quote="0",
                expected_account_equity_quote="100",
                mark_price="100",
                mark_candle_close_ms=self.now - 60_000,
                mark_observed_at_ms=self.now,
                dataset_version="sha256:dual-ledger-seed",
                funding_coverage_start_at_ms=self.now - 86_400_000,
                source="RECONCILED_ACCOUNT_STATEMENT",
                source_snapshot_id="account-cutover:statement-mismatch",
                payload_hash="sha256:" + "e" * 64,
                config_version="account-cutover-v1",
                recorded_at_ms=self.now,
            )

        with sqlite3.connect(path) as connection:
            count = connection.execute(
                "SELECT COUNT(*) FROM paper_account_equity_cutovers"
            ).fetchone()[0]
            risk = connection.execute(
                "SELECT risk_ready FROM paper_account_risk_state WHERE account_id=1"
            ).fetchone()[0]
        self.assertEqual(count, 0)
        self.assertEqual(risk, 1, "Rejected cutover must not mutate the pre-existing readiness state")



    def test_account_equity_cutover_rejects_overlap_after_coverage_is_complete(self):
        path = self.fresh_account_db("overlap-after-complete-coverage.sqlite3", establish_cutover=False)
        ledger.record_funding_coverage(
            path,
            coverage_id="coverage-complete-window",
            start_at_ms=self.now - 86_400_000,
            end_at_ms=self.now,
            status="VERIFIED",
            source="RECONCILED_FUNDING_STATEMENT",
            source_snapshot_id="funding-overlap:complete-window",
            payload_hash="sha256:" + "f" * 64,
            config_version="funding-policy-v1",
            recorded_at_ms=self.now,
        )
        with self.assertRaisesRegex(ValueError, "FUNDING_COVERAGE_INTERVAL_OVERLAP"):
            ledger.record_funding_coverage(
                path,
                coverage_id="coverage-nested-overlap",
                start_at_ms=self.now - 60_000,
                end_at_ms=self.now - 30_000,
                status="VERIFIED",
                source="RECONCILED_FUNDING_STATEMENT",
                source_snapshot_id="funding-overlap:nested-window",
                payload_hash="sha256:" + "e" * 64,
                config_version="funding-policy-v1",
                recorded_at_ms=self.now,
            )
        with sqlite3.connect(path) as connection:
            count = connection.execute(
                "SELECT COUNT(*) FROM paper_funding_coverage WHERE coverage_id=?",
                ("coverage-nested-overlap",),
            ).fetchone()[0]
        self.assertEqual(count, 0)

    def test_account_equity_cutover_rejects_funding_coverage_gap(self):
        path = self.fresh_account_db("cutover-funding-gap.sqlite3", establish_cutover=False)
        ledger.record_funding_coverage(
            path, coverage_id="funding-gap-first",
            start_at_ms=self.now - 86_400_000, end_at_ms=self.now - 60_000,
            status="VERIFIED", source="RECONCILED_FUNDING_STATEMENT",
            source_snapshot_id="funding-gap:first", payload_hash="sha256:" + "2" * 64,
            config_version="funding-policy-v1", recorded_at_ms=self.now,
        )
        ledger.record_funding_coverage(
            path, coverage_id="funding-gap-second",
            start_at_ms=self.now - 30_000, end_at_ms=self.now,
            status="VERIFIED", source="RECONCILED_FUNDING_STATEMENT",
            source_snapshot_id="funding-gap:second", payload_hash="sha256:" + "3" * 64,
            config_version="funding-policy-v1", recorded_at_ms=self.now,
        )

        with self.assertRaisesRegex(ValueError, "FUNDING_PROVENANCE_INCOMPLETE"):
            ledger.record_account_equity_cutover(
                path, cutover_id="cutover-funding-gap",
                expected_initial_capital_quote="100", expected_realized_pnl_quote="0",
                expected_fees_quote="0", expected_funding_quote="0",
                expected_account_equity_quote="100", mark_price="100",
                mark_candle_close_ms=self.now - 60_000, mark_observed_at_ms=self.now,
                dataset_version="sha256:dual-ledger-seed",
                funding_coverage_start_at_ms=self.now - 86_400_000,
                source="RECONCILED_ACCOUNT_STATEMENT",
                source_snapshot_id="account-cutover:funding-gap",
                payload_hash="sha256:" + "4" * 64,
                config_version="account-cutover-v1", recorded_at_ms=self.now,
            )

    def test_account_equity_cutover_rejects_future_mark_observation(self):
        path = self.fresh_account_db("cutover-future-mark.sqlite3", establish_cutover=False)
        ledger.record_funding_coverage(
            path, coverage_id="future-mark-funding-coverage",
            start_at_ms=self.now - 86_400_000, end_at_ms=self.now,
            status="VERIFIED", source="RECONCILED_FUNDING_STATEMENT",
            source_snapshot_id="funding-future-mark:window",
            payload_hash="sha256:" + "5" * 64,
            config_version="funding-policy-v1", recorded_at_ms=self.now,
        )

        with self.assertRaisesRegex(ValueError, "ACCOUNT_EQUITY_CUTOVER_MARK_INVALID"):
            ledger.record_account_equity_cutover(
                path, cutover_id="cutover-future-mark",
                expected_initial_capital_quote="100", expected_realized_pnl_quote="0",
                expected_fees_quote="0", expected_funding_quote="0",
                expected_account_equity_quote="100", mark_price="100",
                mark_candle_close_ms=self.now - 60_000,
                mark_observed_at_ms=self.now + 1,
                dataset_version="sha256:dual-ledger-seed",
                funding_coverage_start_at_ms=self.now - 86_400_000,
                source="RECONCILED_ACCOUNT_STATEMENT",
                source_snapshot_id="account-cutover:future-mark",
                payload_hash="sha256:" + "6" * 64,
                config_version="account-cutover-v1", recorded_at_ms=self.now,
            )

    def test_account_equity_cutover_rejects_stale_closed_candle(self):
        path = self.fresh_account_db("cutover-stale-candle.sqlite3", establish_cutover=False)
        ledger.record_funding_coverage(
            path, coverage_id="stale-candle-funding-coverage",
            start_at_ms=self.now - 86_400_000, end_at_ms=self.now,
            status="VERIFIED", source="RECONCILED_FUNDING_STATEMENT",
            source_snapshot_id="funding-stale-candle:window",
            payload_hash="sha256:" + "7" * 64,
            config_version="funding-policy-v1", recorded_at_ms=self.now,
        )

        with self.assertRaisesRegex(ValueError, "ACCOUNT_EQUITY_CUTOVER_CANDLE_STALE"):
            ledger.record_account_equity_cutover(
                path, cutover_id="cutover-stale-candle",
                expected_initial_capital_quote="100", expected_realized_pnl_quote="0",
                expected_fees_quote="0", expected_funding_quote="0",
                expected_account_equity_quote="100", mark_price="100",
                mark_candle_close_ms=self.now - 30 * 60_000 - 1,
                mark_observed_at_ms=self.now,
                dataset_version="sha256:dual-ledger-seed",
                funding_coverage_start_at_ms=self.now - 86_400_000,
                source="RECONCILED_ACCOUNT_STATEMENT",
                source_snapshot_id="account-cutover:stale-candle",
                payload_hash="sha256:" + "8" * 64,
                config_version="account-cutover-v1", recorded_at_ms=self.now,
            )

    def test_account_equity_cutover_rejects_corrupt_funding_event_provenance(self):
        path = self.fresh_account_db("cutover-corrupt-funding-event.sqlite3", establish_cutover=False)
        ledger.record_funding_coverage(
            path, coverage_id="corrupt-event-funding-coverage",
            start_at_ms=self.now - 86_400_000, end_at_ms=self.now,
            status="VERIFIED", source="RECONCILED_FUNDING_STATEMENT",
            source_snapshot_id="funding-corrupt-event:window",
            payload_hash="sha256:" + "9" * 64,
            config_version="funding-policy-v1", recorded_at_ms=self.now,
        )
        ledger.record_funding_event(
            path, funding_event_id="corrupt-provenance-event",
            strategy_id="STRATEGY_CORE", amount_quote="0.25",
            event_at_ms=self.now - 1_000, source="OKX_FUNDING_HISTORY",
            source_snapshot_id="okx:funding:corrupt-test",
            payload_hash="sha256:" + "a" * 64, recorded_at_ms=self.now,
        )
        with sqlite3.connect(path) as connection:
            connection.execute("DROP TRIGGER paper_funding_events_immutable_update")
            connection.execute(
                "UPDATE paper_funding_events SET source='LEGACY_UNVERIFIED' WHERE funding_event_id=?",
                ("corrupt-provenance-event",),
            )

        with self.assertRaisesRegex(ValueError, "FUNDING_PROVENANCE_INCOMPLETE"):
            ledger.record_account_equity_cutover(
                path, cutover_id="cutover-corrupt-funding-event",
                expected_initial_capital_quote="100", expected_realized_pnl_quote="0",
                expected_fees_quote="0", expected_funding_quote="0.25",
                expected_account_equity_quote="99.75", mark_price="100",
                mark_candle_close_ms=self.now - 60_000, mark_observed_at_ms=self.now,
                dataset_version="sha256:dual-ledger-seed",
                funding_coverage_start_at_ms=self.now - 86_400_000,
                source="RECONCILED_ACCOUNT_STATEMENT",
                source_snapshot_id="account-cutover:corrupt-funding-event",
                payload_hash="sha256:" + "b" * 64,
                config_version="account-cutover-v1", recorded_at_ms=self.now,
            )



    def test_account_equity_cutover_replay_after_reopen_is_idempotent_and_conflict_safe(self):
        path = self.fresh_account_db("cutover-restart-replay.sqlite3", establish_cutover=False)
        ledger.record_funding_coverage(
            path,
            coverage_id="restart-replay-funding-coverage",
            start_at_ms=self.now - 86_400_000,
            end_at_ms=self.now,
            status="VERIFIED",
            source="RECONCILED_ACCOUNT_STATEMENT",
            source_snapshot_id="restart-replay:funding-window",
            payload_hash="sha256:" + "c" * 64,
            config_version="funding-policy-v1",
            recorded_at_ms=self.now,
        )
        kwargs = {
            "cutover_id": "restart-replay-cutover-001",
            "expected_initial_capital_quote": "100",
            "expected_realized_pnl_quote": "0",
            "expected_fees_quote": "0",
            "expected_funding_quote": "0",
            "expected_account_equity_quote": "100",
            "mark_price": "100",
            "mark_candle_close_ms": self.now - 60_000,
            "mark_observed_at_ms": self.now,
            "dataset_version": "sha256:dual-ledger-seed",
            "funding_coverage_start_at_ms": self.now - 86_400_000,
            "source": "RECONCILED_ACCOUNT_STATEMENT",
            "source_snapshot_id": "restart-replay:account-cutover",
            "payload_hash": "sha256:" + "d" * 64,
            "config_version": "account-cutover-v1",
            "recorded_at_ms": self.now,
        }
        first = ledger.record_account_equity_cutover(path, **kwargs)

        with sqlite3.connect(path) as connection:
            before = {
                "cutovers": connection.execute(
                    "SELECT COUNT(*) FROM paper_account_equity_cutovers"
                ).fetchone()[0],
                "audits": connection.execute(
                    "SELECT COUNT(*) FROM paper_audit WHERE kind='ACCOUNT_EQUITY_CUTOVER'"
                ).fetchone()[0],
                "risk": connection.execute(
                    """SELECT high_water_mark_quote,daily_baseline_utc_day_ms,
                              daily_baseline_equity_quote,last_equity_quote,
                              risk_ready,version
                       FROM paper_account_risk_state WHERE account_id=1"""
                ).fetchone(),
            }
        self.assertEqual(before["cutovers"], 1)
        self.assertEqual(before["audits"], 1)

        # Reopen the database and reconstruct strategy handles as after a process restart.
        reopened_core = PaperLedger(
            path, max_position_base="1", strategy_id="STRATEGY_CORE",
            source_sha="a" * 40,
        )
        reopened_ai = PaperLedger(
            path, max_position_base="1", strategy_id="AI_FREQAI",
            source_sha="a" * 40,
        )
        self.assertEqual(reopened_core.snapshot()["positionBase"], "0")
        self.assertEqual(reopened_ai.snapshot()["positionBase"], "0")
        replay = ledger.record_account_equity_cutover(path, **kwargs)
        self.assertEqual(replay, first)

        with sqlite3.connect(path) as connection:
            after_replay = {
                "cutovers": connection.execute(
                    "SELECT COUNT(*) FROM paper_account_equity_cutovers"
                ).fetchone()[0],
                "audits": connection.execute(
                    "SELECT COUNT(*) FROM paper_audit WHERE kind='ACCOUNT_EQUITY_CUTOVER'"
                ).fetchone()[0],
                "risk": connection.execute(
                    """SELECT high_water_mark_quote,daily_baseline_utc_day_ms,
                              daily_baseline_equity_quote,last_equity_quote,
                              risk_ready,version
                       FROM paper_account_risk_state WHERE account_id=1"""
                ).fetchone(),
            }
        self.assertEqual(after_replay, before, "Idempotent replay must not rewrite risk state or audit")

        conflicting = dict(kwargs, payload_hash="sha256:" + "e" * 64)
        with self.assertRaisesRegex(ValueError, "ACCOUNT_EQUITY_CUTOVER_ID_CONFLICT"):
            ledger.record_account_equity_cutover(path, **conflicting)
        with sqlite3.connect(path) as connection:
            after_conflict = {
                "cutovers": connection.execute(
                    "SELECT COUNT(*) FROM paper_account_equity_cutovers"
                ).fetchone()[0],
                "audits": connection.execute(
                    "SELECT COUNT(*) FROM paper_audit WHERE kind='ACCOUNT_EQUITY_CUTOVER'"
                ).fetchone()[0],
                "risk": connection.execute(
                    """SELECT high_water_mark_quote,daily_baseline_utc_day_ms,
                              daily_baseline_equity_quote,last_equity_quote,
                              risk_ready,version
                       FROM paper_account_risk_state WHERE account_id=1"""
                ).fetchone(),
            }
        self.assertEqual(after_conflict, before, "Conflicting replay must leave durable state unchanged")

    def test_read_account_risk_snapshot_leaves_database_bytes_unchanged(self):
        before = self.path.read_bytes()
        snapshot = ledger.read_account_risk_snapshot(self.path, now_ms=self.now)
        after = self.path.read_bytes()

        self.assertTrue(snapshot["available"], snapshot)
        self.assertTrue(snapshot["riskReady"], snapshot)
        self.assertEqual(after, before, "Read-only snapshot must not alter the SQLite database file")



    def test_account_equity_cutover_process_crash_before_commit_rolls_back_all_state(self):
        crash_points = (
            ("after_cutover_insert", 71),
            ("after_risk_state_update", 71),
            ("after_cutover_audit_insert", 71),
        )
        child_script = r"""
import json
import os
import sys
import paper_execution.funding as funding

db_path, crash_point, payload = sys.argv[1:4]
kwargs = json.loads(payload)
original_connect = funding.sqlite3.connect

class CrashConnection:
    def __init__(self, connection):
        object.__setattr__(self, "connection", connection)

    def __setattr__(self, name, value):
        if name == "connection":
            object.__setattr__(self, name, value)
        else:
            setattr(self.connection, name, value)

    def __getattr__(self, name):
        return getattr(self.connection, name)

    def __enter__(self):
        self.connection.__enter__()
        return self

    def execute(self, sql, parameters=()):
        cursor = self.connection.execute(sql, parameters)
        normalized = " ".join(sql.upper().split())
        if crash_point == "after_cutover_insert" and normalized.startswith(
            "INSERT INTO PAPER_ACCOUNT_EQUITY_CUTOVERS"
        ):
            os._exit(71)
        if crash_point == "after_risk_state_update" and normalized.startswith(
            "UPDATE PAPER_ACCOUNT_RISK_STATE SET HIGH_WATER_MARK_QUOTE"
        ):
            os._exit(71)
        if crash_point == "after_cutover_audit_insert" and (
            normalized.startswith("INSERT INTO PAPER_AUDIT")
            and "ACCOUNT_EQUITY_CUTOVER" in normalized
        ):
            os._exit(71)
        return cursor

    def __exit__(self, exc_type, exc, traceback):
        return self.connection.__exit__(exc_type, exc, traceback)

    def close(self):
        return self.connection.close()

def crash_connect(*args, **kwargs):
    return CrashConnection(original_connect(*args, **kwargs))

funding.sqlite3.connect = crash_connect
funding.record_account_equity_cutover(db_path, **kwargs)
os._exit(0)
"""
        for crash_point, expected_exit in crash_points:
            with self.subTest(crash_point=crash_point):
                path = self.fresh_account_db(
                    f"cutover-crash-{crash_point}.sqlite3",
                    establish_cutover=False,
                )
                ledger.record_funding_coverage(
                    path,
                    coverage_id=f"crash-{crash_point}-coverage",
                    start_at_ms=self.now - 86_400_000,
                    end_at_ms=self.now,
                    status="VERIFIED",
                    source="RECONCILED_ACCOUNT_STATEMENT",
                    source_snapshot_id=f"crash:{crash_point}:funding",
                    payload_hash="sha256:" + "c" * 64,
                    config_version="funding-policy-v1",
                    recorded_at_ms=self.now,
                )
                kwargs = {
                    "cutover_id": f"crash-{crash_point}-cutover",
                    "expected_initial_capital_quote": "100",
                    "expected_realized_pnl_quote": "0",
                    "expected_fees_quote": "0",
                    "expected_funding_quote": "0",
                    "expected_account_equity_quote": "100",
                    "mark_price": "100",
                    "mark_candle_close_ms": self.now - 60_000,
                    "mark_observed_at_ms": self.now,
                    "dataset_version": "sha256:dual-ledger-seed",
                    "funding_coverage_start_at_ms": self.now - 86_400_000,
                    "source": "RECONCILED_ACCOUNT_STATEMENT",
                    "source_snapshot_id": f"crash:{crash_point}:account",
                    "payload_hash": "sha256:" + "d" * 64,
                    "config_version": "account-cutover-v1",
                    "recorded_at_ms": self.now,
                }
                with sqlite3.connect(path) as connection:
                    before_risk = connection.execute(
                        """SELECT high_water_mark_quote,daily_baseline_utc_day_ms,
                                  daily_baseline_equity_quote,last_equity_quote,
                                  risk_ready,version
                           FROM paper_account_risk_state WHERE account_id=1"""
                    ).fetchone()
                completed = subprocess.run(
                    [
                        sys.executable, "-c", child_script, str(path),
                        crash_point, json.dumps(kwargs),
                    ],
                    capture_output=True,
                    text=True,
                    timeout=15,
                )
                self.assertEqual(completed.returncode, expected_exit, completed.stderr)
                with sqlite3.connect(path) as connection:
                    self.assertEqual(
                        connection.execute(
                            "SELECT COUNT(*) FROM paper_account_equity_cutovers"
                        ).fetchone()[0],
                        0,
                    )
                    self.assertEqual(
                        connection.execute(
                            """SELECT COUNT(*) FROM paper_audit
                               WHERE kind='ACCOUNT_EQUITY_CUTOVER'"""
                        ).fetchone()[0],
                        0,
                    )
                    after_crash_risk = connection.execute(
                        """SELECT high_water_mark_quote,daily_baseline_utc_day_ms,
                                  daily_baseline_equity_quote,last_equity_quote,
                                  risk_ready,version
                           FROM paper_account_risk_state WHERE account_id=1"""
                    ).fetchone()
                self.assertEqual(after_crash_risk, before_risk)

                recovered = ledger.record_account_equity_cutover(path, **kwargs)
                self.assertTrue(recovered["riskReady"])
                with sqlite3.connect(path) as connection:
                    self.assertEqual(
                        connection.execute(
                            "SELECT COUNT(*) FROM paper_account_equity_cutovers"
                        ).fetchone()[0],
                        1,
                    )
                    self.assertEqual(
                        connection.execute(
                            """SELECT COUNT(*) FROM paper_audit
                               WHERE kind='ACCOUNT_EQUITY_CUTOVER'"""
                        ).fetchone()[0],
                        1,
                    )

    def test_account_equity_cutover_process_crash_after_commit_replays_without_duplicates(self):
        child_script = r"""
import json
import os
import sys
import paper_execution.funding as funding

db_path, payload = sys.argv[1:3]
kwargs = json.loads(payload)
original_connect = funding.sqlite3.connect

class ExitAfterCommitConnection:
    def __init__(self, connection):
        object.__setattr__(self, "connection", connection)

    def __setattr__(self, name, value):
        if name == "connection":
            object.__setattr__(self, name, value)
        else:
            setattr(self.connection, name, value)

    def __getattr__(self, name):
        return getattr(self.connection, name)

    def __enter__(self):
        self.connection.__enter__()
        return self

    def execute(self, sql, parameters=()):
        return self.connection.execute(sql, parameters)

    def __exit__(self, exc_type, exc, traceback):
        result = self.connection.__exit__(exc_type, exc, traceback)
        if exc_type is None:
            os._exit(72)
        return result

    def close(self):
        return self.connection.close()

def crash_connect(*args, **kwargs):
    return ExitAfterCommitConnection(original_connect(*args, **kwargs))

funding.sqlite3.connect = crash_connect
funding.record_account_equity_cutover(db_path, **kwargs)
os._exit(0)
"""
        path = self.fresh_account_db(
            "cutover-process-crash-after-commit.sqlite3",
            establish_cutover=False,
        )
        ledger.record_funding_coverage(
            path,
            coverage_id="post-commit-crash-coverage",
            start_at_ms=self.now - 86_400_000,
            end_at_ms=self.now,
            status="VERIFIED",
            source="RECONCILED_ACCOUNT_STATEMENT",
            source_snapshot_id="post-commit-crash:funding",
            payload_hash="sha256:" + "e" * 64,
            config_version="funding-policy-v1",
            recorded_at_ms=self.now,
        )
        kwargs = {
            "cutover_id": "post-commit-crash-cutover",
            "expected_initial_capital_quote": "100",
            "expected_realized_pnl_quote": "0",
            "expected_fees_quote": "0",
            "expected_funding_quote": "0",
            "expected_account_equity_quote": "100",
            "mark_price": "100",
            "mark_candle_close_ms": self.now - 60_000,
            "mark_observed_at_ms": self.now,
            "dataset_version": "sha256:dual-ledger-seed",
            "funding_coverage_start_at_ms": self.now - 86_400_000,
            "source": "RECONCILED_ACCOUNT_STATEMENT",
            "source_snapshot_id": "post-commit-crash:account",
            "payload_hash": "sha256:" + "f" * 64,
            "config_version": "account-cutover-v1",
            "recorded_at_ms": self.now,
        }
        completed = subprocess.run(
            [sys.executable, "-c", child_script, str(path), json.dumps(kwargs)],
            capture_output=True,
            text=True,
            timeout=15,
        )
        self.assertEqual(completed.returncode, 72, completed.stderr)

        with sqlite3.connect(path) as connection:
            committed = {
                "cutovers": connection.execute(
                    "SELECT COUNT(*) FROM paper_account_equity_cutovers"
                ).fetchone()[0],
                "audits": connection.execute(
                    """SELECT COUNT(*) FROM paper_audit
                       WHERE kind='ACCOUNT_EQUITY_CUTOVER'"""
                ).fetchone()[0],
                "risk": connection.execute(
                    """SELECT high_water_mark_quote,daily_baseline_utc_day_ms,
                              daily_baseline_equity_quote,last_equity_quote,
                              risk_ready,version
                       FROM paper_account_risk_state WHERE account_id=1"""
                ).fetchone(),
            }
        self.assertEqual(committed["cutovers"], 1)
        self.assertEqual(committed["audits"], 1)
        self.assertEqual(committed["risk"][0], "100")
        self.assertEqual(committed["risk"][2], "100")
        self.assertEqual(committed["risk"][4], 1)

        replay = ledger.record_account_equity_cutover(path, **kwargs)
        self.assertEqual(replay["cutoverId"], kwargs["cutover_id"])
        with sqlite3.connect(path) as connection:
            after_replay = {
                "cutovers": connection.execute(
                    "SELECT COUNT(*) FROM paper_account_equity_cutovers"
                ).fetchone()[0],
                "audits": connection.execute(
                    """SELECT COUNT(*) FROM paper_audit
                       WHERE kind='ACCOUNT_EQUITY_CUTOVER'"""
                ).fetchone()[0],
                "risk": connection.execute(
                    """SELECT high_water_mark_quote,daily_baseline_utc_day_ms,
                              daily_baseline_equity_quote,last_equity_quote,
                              risk_ready,version
                       FROM paper_account_risk_state WHERE account_id=1"""
                ).fetchone(),
            }
        self.assertEqual(after_replay, committed)



    def test_funding_refresh_updates_equity_but_preserves_hwm_when_risk_unready(self):
        path = self.fresh_account_db(
            "funding-refresh-risk-unready.sqlite3",
            establish_cutover=False,
        )
        ledger.record_funding_coverage(
            path,
            coverage_id="risk-unready-funding-coverage",
            start_at_ms=self.now - 86_400_000,
            end_at_ms=self.now,
            status="VERIFIED",
            source="RECONCILED_FUNDING_STATEMENT",
            source_snapshot_id="risk-unready:coverage",
            payload_hash="sha256:" + "e" * 64,
            config_version="funding-policy-v1",
            recorded_at_ms=self.now,
        )
        with sqlite3.connect(path) as connection:
            connection.execute(
                """UPDATE paper_account_risk_state
                   SET risk_ready=0,unavailable_reason='TEST_NOT_READY',
                       high_water_mark_quote='100' WHERE account_id=1"""
            )

        ledger.record_funding_event(
            path,
            funding_event_id="unready-risk-funding-credit",
            strategy_id="STRATEGY_CORE",
            amount_quote="-5",
            event_at_ms=self.now - 1_000,
            source="OKX_FUNDING_HISTORY",
            source_snapshot_id="risk-unready:funding-credit",
            payload_hash="sha256:" + "a" * 64,
            recorded_at_ms=self.now,
        )

        with sqlite3.connect(path) as connection:
            high_water_mark, equity, risk_ready = connection.execute(
                """SELECT high_water_mark_quote,last_equity_quote,risk_ready
                   FROM paper_account_risk_state WHERE account_id=1"""
            ).fetchone()
        self.assertEqual(high_water_mark, "100")
        self.assertEqual(equity, "105")
        self.assertEqual(risk_ready, 0)

    def test_funding_coverage_rejects_overlap_after_cutover(self):
        path = self.path
        with self.assertRaisesRegex(ValueError, "FUNDING_COVERAGE_INTERVAL_OVERLAP"):
            ledger.record_funding_coverage(
                path,
                coverage_id="overlap-after-cutover",
                start_at_ms=self.now - 10 * 60_000,
                end_at_ms=self.now - 5 * 60_000,
                status="VERIFIED",
                source="RECONCILED_FUNDING_STATEMENT",
                source_snapshot_id="post-cutover-overlap:funding",
                payload_hash="sha256:" + "b" * 64,
                config_version="funding-policy-v1",
                recorded_at_ms=self.now,
            )
        with sqlite3.connect(path) as connection:
            count = connection.execute(
                "SELECT COUNT(*) FROM paper_funding_coverage WHERE coverage_id=?",
                ("overlap-after-cutover",),
            ).fetchone()[0]
        self.assertEqual(count, 0)

    def test_read_only_snapshot_fails_closed_on_corrupt_funding_event_provenance(self):
        path = self.path
        ledger.record_funding_event(
            path,
            funding_event_id="snapshot-corrupt-provenance-event",
            strategy_id="STRATEGY_CORE",
            amount_quote="0",
            event_at_ms=self.now - 1_000,
            source="OKX_FUNDING_HISTORY",
            source_snapshot_id="snapshot-corrupt:funding",
            payload_hash="sha256:" + "c" * 64,
            recorded_at_ms=self.now,
        )
        with sqlite3.connect(path) as connection:
            connection.execute("DROP TRIGGER paper_funding_events_immutable_update")
            connection.execute(
                """UPDATE paper_funding_events SET source='LEGACY_UNVERIFIED'
                   WHERE funding_event_id=?""",
                ("snapshot-corrupt-provenance-event",),
            )

        snapshot = ledger.read_account_risk_snapshot(path, now_ms=self.now)
        self.assertTrue(snapshot["available"], snapshot)
        self.assertFalse(snapshot["riskReady"], snapshot)
        self.assertEqual(snapshot["unavailableReason"], "FUNDING_PROVENANCE_INCOMPLETE")



    def test_read_only_snapshot_fails_closed_on_overlapping_funding_coverage(self):
        path = self.path
        with sqlite3.connect(path) as connection:
            connection.execute(
                """INSERT INTO paper_funding_coverage
                   (coverage_id,account_id,start_at_ms,end_at_ms,status,source,
                    source_snapshot_id,payload_hash,config_version,recorded_at_ms)
                   VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (
                    "snapshot-overlapping-coverage", 1,
                    self.now - 10 * 60_000, self.now - 5 * 60_000,
                    "VERIFIED", "RECONCILED_FUNDING_STATEMENT",
                    "snapshot-overlap:funding", "sha256:" + "d" * 64,
                    "funding-policy-v1", self.now,
                ),
            )

        snapshot = ledger.read_account_risk_snapshot(path, now_ms=self.now)
        self.assertTrue(snapshot["available"], snapshot)
        self.assertFalse(snapshot["riskReady"], snapshot)
        self.assertEqual(snapshot["unavailableReason"], "FUNDING_PROVENANCE_INCOMPLETE")



    def test_funding_event_rejects_missing_coverage_without_ledger_mutation(self):
        path = self.fresh_account_db(
            "funding-event-without-coverage.sqlite3",
            establish_cutover=False,
        )
        with sqlite3.connect(path) as connection:
            before = connection.execute(
                """SELECT funding_quote FROM paper_strategy_ledgers
                   WHERE account_id=1 AND strategy_id='STRATEGY_CORE'"""
            ).fetchone()[0]

        with self.assertRaisesRegex(ValueError, "FUNDING_PROVENANCE_INCOMPLETE"):
            ledger.record_funding_event(
                path,
                funding_event_id="funding-event-without-coverage",
                strategy_id="STRATEGY_CORE",
                amount_quote="0.5",
                event_at_ms=self.now - 1_000,
                source="OKX_FUNDING_HISTORY",
                source_snapshot_id="missing-coverage:funding",
                payload_hash="sha256:" + "f" * 64,
                recorded_at_ms=self.now,
            )

        with sqlite3.connect(path) as connection:
            after = connection.execute(
                """SELECT funding_quote FROM paper_strategy_ledgers
                   WHERE account_id=1 AND strategy_id='STRATEGY_CORE'"""
            ).fetchone()[0]
            count = connection.execute(
                "SELECT COUNT(*) FROM paper_funding_events WHERE funding_event_id=?",
                ("funding-event-without-coverage",),
            ).fetchone()[0]
        self.assertEqual(after, before)
        self.assertEqual(count, 0)



    def test_mark_advancement_requires_contiguous_funding_coverage_and_allows_admission(self):
        advanced_now = self.now + 5 * 60_000
        ledger.record_funding_coverage(
            self.path,
            coverage_id="mark-advance-adjacent-funding-coverage",
            start_at_ms=self.now,
            end_at_ms=self.now + 10 * 60_000,
            status="VERIFIED",
            source="RECONCILED_FUNDING_STATEMENT",
            source_snapshot_id="mark-advance:adjacent-coverage",
            payload_hash="sha256:" + "7" * 64,
            config_version="funding-policy-v1",
            recorded_at_ms=self.now + 10 * 60_000,
        )
        with sqlite3.connect(self.path) as connection:
            connection.execute(
                """UPDATE paper_account_risk_state
                   SET last_mark_price='101',mark_observed_at_ms=?,
                       mark_candle_close_ms=?,updated_at_ms=?
                   WHERE account_id=1""",
                (advanced_now, advanced_now - 60_000, advanced_now),
            )

        snapshot = ledger.read_account_risk_snapshot(self.path, now_ms=advanced_now)
        self.assertTrue(snapshot["riskReady"], snapshot)
        intent = self.intent(
            "mark-advance-covered-entry", "0.1", "100.1", "mark-advance-book"
        )
        intent["decisionAtMs"] = advanced_now - 100
        intent["validUntilMs"] = advanced_now + 30_000
        order = self.core.submit(intent, self.book(advanced_now), advanced_now)
        self.assertEqual(order["status"], "FILLED", order)

    def test_mark_advancement_beyond_funding_coverage_blocks_new_exposure(self):
        advanced_now = self.now + 5 * 60_000
        with sqlite3.connect(self.path) as connection:
            connection.execute(
                """UPDATE paper_account_risk_state
                   SET mark_observed_at_ms=?,mark_candle_close_ms=?,updated_at_ms=?
                   WHERE account_id=1""",
                (advanced_now, advanced_now - 60_000, advanced_now),
            )

        snapshot = ledger.read_account_risk_snapshot(self.path, now_ms=advanced_now)
        self.assertTrue(snapshot["available"], snapshot)
        self.assertFalse(snapshot["riskReady"], snapshot)
        self.assertEqual(snapshot["unavailableReason"], "FUNDING_PROVENANCE_INCOMPLETE")
        order = self.core.submit(
            self.intent("mark-advance-uncovered-entry", "0.1", "100.1", "mark-advance-gap-book"),
            self.book(advanced_now),
            advanced_now,
        )
        self.assertEqual(order["status"], "REJECTED", order)
        self.assertEqual(order["reason"], "RISK_INPUTS_UNAVAILABLE")

    def test_utc_day_rollover_does_not_silently_reset_daily_loss_baseline(self):
        next_day = (self.now // 86_400_000 + 1) * 86_400_000
        advanced_now = next_day + 5 * 60_000
        ledger.record_funding_coverage(
            self.path,
            coverage_id="utc-rollover-contiguous-funding-coverage",
            start_at_ms=self.now,
            end_at_ms=advanced_now,
            status="VERIFIED",
            source="RECONCILED_FUNDING_STATEMENT",
            source_snapshot_id="utc-rollover:continuous-coverage",
            payload_hash="sha256:" + "8" * 64,
            config_version="funding-policy-v1",
            recorded_at_ms=advanced_now,
        )
        with sqlite3.connect(self.path) as connection:
            connection.execute(
                """UPDATE paper_account_risk_state
                   SET mark_observed_at_ms=?,mark_candle_close_ms=?,updated_at_ms=?
                   WHERE account_id=1""",
                (advanced_now, advanced_now - 60_000, advanced_now),
            )
            previous_baseline = connection.execute(
                """SELECT daily_baseline_utc_day_ms,daily_baseline_equity_quote
                   FROM paper_account_risk_state WHERE account_id=1"""
            ).fetchone()

        with self.assertRaisesRegex(sqlite3.DatabaseError, "ACCOUNT_RISK_DAILY_BASELINE_UNAVAILABLE"):
            ledger.read_account_risk_snapshot(self.path, now_ms=advanced_now)

        order = self.core.submit(
            self.intent("utc-rollover-no-baseline-entry", "0.1", "100.1", "utc-rollover-book"),
            self.book(advanced_now),
            advanced_now,
        )
        self.assertEqual(order["status"], "REJECTED", order)
        self.assertEqual(order["reason"], "RISK_INPUTS_STALE_OR_CORRUPT")
        with sqlite3.connect(self.path) as connection:
            current_baseline = connection.execute(
                """SELECT daily_baseline_utc_day_ms,daily_baseline_equity_quote
                   FROM paper_account_risk_state WHERE account_id=1"""
            ).fetchone()
        self.assertEqual(current_baseline, previous_baseline)


    def test_account_history_v6_migration_creates_append_only_replay_tables(self):
        with sqlite3.connect(self.path) as connection:
            tables = {row[0] for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )}
            required = {
                "paper_account_event_journal", "paper_account_history_coverage",
                "paper_market_mark_history", "paper_daily_equity_baselines",
            }
            self.assertTrue(required.issubset(tables), required - tables)
            triggers = {row[0] for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='trigger'"
            )}
            self.assertTrue({
                "paper_account_event_journal_immutable_update",
                "paper_account_event_journal_immutable_delete",
                "paper_market_mark_history_immutable_update",
                "paper_market_mark_history_immutable_delete",
                "paper_daily_equity_baselines_immutable_update",
                "paper_daily_equity_baselines_immutable_delete",
            }.issubset(triggers))

    def test_account_history_event_retry_is_idempotent_and_conflict_safe(self):
        event = {
            "event_id": "history-fill-core-001", "strategy_id": "STRATEGY_CORE",
            "event_type": "FILL", "event_at_ms": self.now + 1_000,
            "quantity_delta_base": "0.1", "fill_price": "101", "fee_quote": "0.0101",
            "source": "PAPER_EXECUTION_FILL",
            "source_snapshot_id": "history-fill-snapshot-001",
            "payload_hash": "sha256:" + "1" * 64,
            "recorded_at_ms": self.now + 1_100, "order_id": "history-order-001",
            "fee_currency": "USDT",
            "intent_id": "history-intent-001",
        }
        first = ledger.record_account_history_event(self.path, **event)
        replay = ledger.record_account_history_event(self.path, **event)
        self.assertEqual(first["eventId"], replay["eventId"])
        self.assertEqual(first["payloadHash"], replay["payloadHash"])
        with self.assertRaisesRegex(ValueError, "ACCOUNT_HISTORY_EVENT_ID_CONFLICT"):
            ledger.record_account_history_event(
                self.path, **{**event, "fee_quote": "0.02"}
            )
        with sqlite3.connect(self.path) as connection:
            row = connection.execute(
                """SELECT COUNT(*),MAX(fee_quote),MAX(fee_currency) FROM paper_account_event_journal
                   WHERE event_id=?""", (event["event_id"],)
            ).fetchone()
        self.assertEqual(row, (1, "0.0101", "USDT"))

    def test_account_history_event_requires_explicit_fee_amount_and_currency(self):
        common = {
            "fee_currency": "USDT",
            "event_id": "history-fee-required", "strategy_id": "STRATEGY_CORE",
            "event_type": "FILL", "event_at_ms": self.now + 1_000,
            "quantity_delta_base": "0.1", "fill_price": "101",
            "source": "PAPER_EXECUTION_FILL",
            "source_snapshot_id": "history-fee-required-snapshot",
            "payload_hash": "sha256:" + "9" * 64,
            "recorded_at_ms": self.now + 1_100,
        }
        with self.assertRaises(TypeError):
            ledger.record_account_history_event(self.path, **common)
        missing_currency = {**common, "fee_quote": "0.01"}
        missing_currency.pop("fee_currency")
        with self.assertRaises(TypeError):
            ledger.record_account_history_event(self.path, **missing_currency)

    def test_account_history_event_rejects_non_quote_fee_currency(self):
        with self.assertRaisesRegex(ValueError, "ACCOUNT_HISTORY_FEE_CURRENCY_INVALID"):
            ledger.record_account_history_event(
                self.path,
                event_id="history-invalid-fee-currency",
                strategy_id="STRATEGY_CORE",
                event_type="FILL",
                event_at_ms=self.now + 1_000,
                recorded_at_ms=self.now + 1_100,
                quantity_delta_base="0.1",
                fill_price="101",
                fee_quote="0.01",
                fee_currency="BTC",
                source="PAPER_EXECUTION_FILL",
                source_snapshot_id="history-invalid-fee-currency-snapshot",
                payload_hash="sha256:" + "8" * 64,
            )

    def test_account_history_sql_insert_rejects_missing_fee_currency(self):
        with self.assertRaisesRegex(sqlite3.IntegrityError, "ACCOUNT_HISTORY_FEE_CURRENCY_REQUIRED"):
            with sqlite3.connect(self.path) as connection:
                connection.execute(
                    """INSERT INTO paper_account_event_journal
                       (event_id,account_id,strategy_id,event_type,event_at_ms,recorded_at_ms,
                        quantity_delta_base,fill_price,fee_quote,fee_currency,source,
                        source_snapshot_id,payload_hash,canonical_payload,created_at_ms)
                       VALUES ('missing-fee-currency',1,'STRATEGY_CORE','FILL',
                               ?,?,'0.1','100','0.01',NULL,'PAPER_TEST',
                               'missing-fee-currency-snapshot',?,'{}',?)""",
                    (self.now + 1_000, self.now + 1_100,
                     "sha256:" + "6" * 64, self.now + 1_100),
                )

    def test_account_history_event_persists_explicit_usdt_fee_currency(self):
        result = ledger.record_account_history_event(
            self.path,
            event_id="history-explicit-fee-currency",
            strategy_id="STRATEGY_CORE",
            event_type="FILL",
            event_at_ms=self.now + 1_000,
            recorded_at_ms=self.now + 1_100,
            quantity_delta_base="0.1",
            fill_price="101",
            fee_quote="0.01",
            fee_currency="USDT",
            source="PAPER_EXECUTION_FILL",
            source_snapshot_id="history-explicit-fee-currency-snapshot",
            payload_hash="sha256:" + "7" * 64,
        )
        self.assertFalse(result["idempotent"])
        with sqlite3.connect(self.path) as connection:
            row = connection.execute(
                """SELECT fee_quote,fee_currency,canonical_payload
                   FROM paper_account_event_journal WHERE event_id=?""",
                ("history-explicit-fee-currency",),
            ).fetchone()
        self.assertEqual(row[:2], ("0.01", "USDT"))
        self.assertIn('"fee_currency":"USDT"', row[2])

    def test_account_history_coverage_accepts_adjacent_and_rejects_overlap(self):
        common = {
            "stream_type": "EXECUTION", "strategy_id": "STRATEGY_CORE",
            "status": "VERIFIED", "source": "PAPER_EXECUTION_JOURNAL",
            "source_snapshot_id": "history-coverage-snapshot",
            "payload_hash": "sha256:" + "2" * 64,
            "recorded_at_ms": self.now + 10_000,
        }
        ledger.record_account_history_coverage(
            self.path, coverage_id="history-core-coverage-a",
            start_at_ms=self.now, end_at_ms=self.now + 5_000, **common,
        )
        ledger.record_account_history_coverage(
            self.path, coverage_id="history-core-coverage-b",
            start_at_ms=self.now + 5_000, end_at_ms=self.now + 10_000, **common,
        )
        with self.assertRaisesRegex(ValueError, "ACCOUNT_HISTORY_COVERAGE_OVERLAP"):
            ledger.record_account_history_coverage(
                self.path, coverage_id="history-core-coverage-overlap",
                start_at_ms=self.now + 4_000, end_at_ms=self.now + 6_000, **common,
            )

    def test_market_mark_history_requires_exact_boundary_and_is_immutable(self):
        boundary = (self.now // 86_400_000 + 1) * 86_400_000
        mark = {
            "mark_id": "history-boundary-mark-001", "effective_at_ms": boundary,
            "observed_at_ms": boundary + 1_000, "mark_price": "105",
            "candle_close_ms": boundary, "source": "VERIFIED_BOUNDARY_MARK",
            "source_snapshot_id": "history-boundary-mark-snapshot",
            "dataset_version": "sha256:boundary-dataset",
            "payload_hash": "sha256:" + "3" * 64,
            "quality_status": "VERIFIED", "recorded_at_ms": boundary + 1_000,
        }
        stored = ledger.record_market_mark_history(self.path, **mark)
        self.assertEqual(stored["effectiveAtMs"], boundary)
        with sqlite3.connect(self.path) as connection:
            with self.assertRaises(sqlite3.IntegrityError):
                connection.execute(
                    """UPDATE paper_market_mark_history SET mark_price='1'
                       WHERE mark_id=?""", (mark["mark_id"],)
                )

    def test_utc_equity_reconstruction_fails_closed_without_complete_history(self):
        boundary = (self.now // 86_400_000 + 1) * 86_400_000
        with sqlite3.connect(self.path) as connection:
            before = connection.execute(
                """SELECT daily_baseline_utc_day_ms,daily_baseline_equity_quote,
                          risk_ready,unavailable_reason
                   FROM paper_account_risk_state WHERE account_id=1"""
            ).fetchone()
        with self.assertRaisesRegex(ValueError, "ACCOUNT_HISTORY_COVERAGE_INCOMPLETE"):
            ledger.reconstruct_daily_equity_baseline(
                self.path, utc_day_ms=boundary, now_ms=boundary + 60_000,
                source_sha="b" * 40,
            )
        with sqlite3.connect(self.path) as connection:
            after = connection.execute(
                """SELECT daily_baseline_utc_day_ms,daily_baseline_equity_quote,
                          risk_ready,unavailable_reason
                   FROM paper_account_risk_state WHERE account_id=1"""
            ).fetchone()
            count = connection.execute(
                """SELECT COUNT(*) FROM paper_daily_equity_baselines
                   WHERE account_id=1 AND utc_day_ms=?""", (boundary,)
            ).fetchone()[0]
        self.assertEqual(after, before)
        self.assertEqual(count, 0)


    def test_core_partial_fills_are_journaled_per_level_in_the_order_transaction(self):
        book = {
            "source": "hummingbot", "connector": "binance_perpetual",
            "symbol": "BTCUSDT", "observedAtMs": self.now,
            "bids": [{"price": "99.9", "quantity": "1"}],
            "asks": [
                {"price": "100.1", "quantity": "0.04"},
                {"price": "100.2", "quantity": "0.06"},
            ],
        }
        order = self.core.submit(
            self.intent("history-multi-level-core-fill", "0.1", "100.2", "history-multi-level-book"),
            book, self.now,
        )
        self.assertEqual(order["status"], "FILLED", order)
        with sqlite3.connect(self.path) as connection:
            events = connection.execute(
                """SELECT strategy_id,event_type,quantity_delta_base,fill_price,fee_quote,fee_currency,
                          event_at_ms,recorded_at_ms,source_snapshot_id,payload_hash
                   FROM paper_account_event_journal
                   WHERE intent_id=? ORDER BY event_id""",
                ("history-multi-level-core-fill",),
            ).fetchall()
        self.assertEqual(len(events), 2)
        self.assertEqual({row[0] for row in events}, {"STRATEGY_CORE"})
        self.assertEqual({row[1] for row in events}, {"FILL"})
        self.assertEqual(sum((Decimal(row[2]) for row in events), Decimal(0)), Decimal("0.1"))
        self.assertEqual(sum((Decimal(row[4]) for row in events), Decimal(0)), Decimal(order["feeQuote"]))
        self.assertEqual({row[5] for row in events}, {"USDT"})
        self.assertEqual({row[6] for row in events}, {self.now})
        self.assertEqual({row[7] for row in events}, {self.now})
        self.assertEqual(len({row[8] for row in events}), 1)
        self.assertTrue(all(row[9].startswith("sha256:") for row in events))

    def test_journal_failure_rolls_back_core_order_and_position_atomically(self):
        intent_id = "history-journal-abort-core-entry"
        with sqlite3.connect(self.path) as connection:
            connection.execute(
                """CREATE TRIGGER fail_account_history_insert
                   BEFORE INSERT ON paper_account_event_journal
                   BEGIN SELECT RAISE(ABORT,'TEST_JOURNAL_WRITE_FAILURE'); END"""
            )
        with self.assertRaisesRegex(sqlite3.IntegrityError, "TEST_JOURNAL_WRITE_FAILURE"):
            self.core.submit(
                self.intent(intent_id, "0.1", "100.1", "history-journal-abort-book"),
                self.book(self.now), self.now,
            )
        with sqlite3.connect(self.path) as connection:
            order_count = connection.execute(
                "SELECT COUNT(*) FROM paper_orders WHERE intent_id=?", (intent_id,)
            ).fetchone()[0]
            position = connection.execute(
                """SELECT position_base FROM paper_strategy_ledgers
                   WHERE account_id=1 AND strategy_id='STRATEGY_CORE'"""
            ).fetchone()[0]
            event_count = connection.execute(
                "SELECT COUNT(*) FROM paper_account_event_journal WHERE intent_id=?", (intent_id,)
            ).fetchone()[0]
        self.assertEqual(order_count, 0)
        self.assertEqual(position, "0")
        self.assertEqual(event_count, 0)


    def test_read_only_daily_replay_loader_returns_verified_inputs_for_all_ledgers(self):
        boundary = (self.now // 86_400_000 + 1) * 86_400_000
        watermark = boundary + 2_000
        for strategy_id in ("AI_FREQAI", "LEGACY_UNATTRIBUTED", "STRATEGY_CORE"):
            ledger.record_account_history_coverage(
                self.path,
                coverage_id=f"replay-execution-{strategy_id.lower()}",
                stream_type="EXECUTION",
                strategy_id=strategy_id,
                start_at_ms=self.now,
                end_at_ms=boundary,
                status="VERIFIED",
                source="RECONCILED_EXECUTION_HISTORY",
                source_snapshot_id=f"execution:{strategy_id}:snapshot",
                payload_hash="sha256:" + ("1" if strategy_id == "STRATEGY_CORE" else "2" if strategy_id == "AI_FREQAI" else "3") * 64,
                recorded_at_ms=watermark,
            )
        ledger.record_account_history_coverage(
            self.path,
            coverage_id="replay-market-mark-coverage",
            stream_type="MARKET_MARK",
            strategy_id=None,
            start_at_ms=self.now,
            end_at_ms=boundary + 1,
            status="VERIFIED",
            source="RECONCILED_MARK_HISTORY",
            source_snapshot_id="market-mark:coverage-snapshot",
            payload_hash="sha256:" + "4" * 64,
            recorded_at_ms=watermark,
        )
        ledger.record_funding_coverage(
            self.path,
            coverage_id="replay-funding-coverage",
            start_at_ms=self.now,
            end_at_ms=boundary,
            status="VERIFIED",
            source="RECONCILED_FUNDING_HISTORY",
            source_snapshot_id="funding:coverage-snapshot",
            payload_hash="sha256:" + "5" * 64,
            config_version="funding-v1",
            recorded_at_ms=watermark,
        )
        ledger.record_account_history_event(
            self.path,
            event_id="replay-core-fill",
            strategy_id="STRATEGY_CORE",
            event_type="FILL",
            event_at_ms=self.now + 500,
            recorded_at_ms=self.now + 600,
            quantity_delta_base="0.1",
            fill_price="101",
            fee_quote="0.01",
            fee_currency="USDT",
            source="PAPER_EXECUTION_FILL",
            source_snapshot_id="execution:core:event",
            payload_hash="sha256:" + "6" * 64,
        )
        ledger.record_funding_event(
            self.path,
            funding_event_id="replay-core-funding",
            strategy_id="STRATEGY_CORE",
            amount_quote="0.25",
            event_at_ms=self.now + 700,
            source="RECONCILED_FUNDING_EVENT",
            source_snapshot_id="funding:event-snapshot",
            payload_hash="sha256:" + "7" * 64,
            recorded_at_ms=self.now + 800,
        )
        ledger.record_market_mark_history(
            self.path,
            mark_id="replay-exact-boundary-mark",
            effective_at_ms=boundary,
            observed_at_ms=boundary + 1_000,
            mark_price="105",
            candle_close_ms=boundary,
            source="VERIFIED_BOUNDARY_MARK",
            source_snapshot_id="market-mark:boundary-snapshot",
            dataset_version="sha256:boundary-dataset",
            payload_hash="sha256:" + "8" * 64,
            quality_status="VERIFIED",
            recorded_at_ms=boundary + 1_000,
        )

        with sqlite3.connect(self.path.as_uri() + "?mode=ro", uri=True) as connection:
            inputs = ledger.load_daily_equity_replay_inputs(connection, utc_day_ms=boundary)

        self.assertEqual(inputs["utc_day_ms"], boundary)
        self.assertEqual(inputs["cutover_id"], "fixture-account-cutover")
        self.assertEqual(set(inputs["ledgers"]), set(ledger.DUAL_STRATEGIES))
        self.assertEqual(
            inputs["ledgers"]["STRATEGY_CORE"]["execution_events"][0]["event_id"],
            "replay-core-fill",
        )
        self.assertEqual(
            inputs["ledgers"]["AI_FREQAI"]["execution_events"], []
        )
        self.assertEqual(
            inputs["funding_events"][0]["funding_event_id"], "replay-core-funding"
        )
        self.assertEqual(inputs["market_mark"]["mark_id"], "replay-exact-boundary-mark")
        self.assertEqual(
            inputs["ledgers"]["STRATEGY_CORE"]["coverage_watermark_at_ms"], watermark
        )
        self.assertEqual(inputs["funding_coverage_watermark_at_ms"], watermark)


if __name__ == "__main__":
    unittest.main()
