from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
import sqlite3
import tempfile
import unittest
from pathlib import Path

from paper_execution import ledger
from paper_execution.ledger import PaperLedger


class DualLedgerRedTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "shared-account.sqlite3"
        self.now = 1_800_000_000_000
        bootstrap = PaperLedger(self.path, max_position_base="1", fee_rate="0.001")
        bootstrap.record_equity("100", self.now - 60_000, self.now, "sha256:dual-ledger-seed", "100")
        limits = {"maxDrawdownPct": "50", "maxDailyLossUsdt": "50", "maxExposureUsdt": "1000"}
        self.core = PaperLedger(self.path, max_position_base="1", fee_rate="0.001",
                                strategy_id="STRATEGY_CORE", source_sha="a" * 40,
                                risk_limits=limits, require_risk_limits=True)
        self.ai = PaperLedger(self.path, max_position_base="1", fee_rate="0.001",
                              strategy_id="AI_FREQAI", source_sha="a" * 40,
                              risk_limits=limits, require_risk_limits=True)
        with sqlite3.connect(self.path) as connection:
            day = self.now // 86_400_000 * 86_400_000
            connection.execute(
                """UPDATE paper_account_risk_state SET high_water_mark_quote='100',
                   daily_baseline_utc_day_ms=?,daily_baseline_equity_quote='100',
                   last_equity_quote='100',last_mark_price='100',mark_observed_at_ms=?,
                   mark_candle_close_ms=?,dataset_version='sha256:dual-ledger-seed',
                   risk_ready=1,unavailable_reason=NULL,updated_at_ms=? WHERE account_id=1""",
                (day, self.now, self.now-60_000, self.now),
            )

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
        before_reservations = sqlite3.connect(self.path).execute(
            "SELECT COUNT(*) FROM paper_risk_reservations"
        ).fetchone()[0]
        order = ledger.reduce_legacy_unattributed(
            self.path,
            self.intent("legacy-partial-close", "0.02", "100", "legacy-close-book"),
            self.book(self.now),
            self.now,
            reconciliation_id="legacy-close-review-001",
            evidence_hash="sha256:legacy-close-evidence-001",
        )
        self.assertEqual(order["status"], "FILLED", order)
        self.assertEqual(order["strategyId"], "LEGACY_UNATTRIBUTED")
        self.assertEqual(order["strategyEvent"], "LEGACY_REDUCTION")

        replayed = ledger.reduce_legacy_unattributed(
            self.path,
            self.intent("legacy-partial-close", "0.02", "100", "legacy-close-book"),
            self.book(self.now),
            self.now,
            reconciliation_id="legacy-close-review-001",
            evidence_hash="sha256:legacy-close-evidence-001",
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
        self.assertIn("sha256:legacy-close-evidence-001", audit)

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
                evidence_hash="sha256:legacy-close-evidence-002",
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
            evidence_hash="sha256:legacy-depth-evidence-001",
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


if __name__ == "__main__":
    unittest.main()
