import os
import json
import multiprocessing
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
import sqlite3
import tempfile
from decimal import Decimal, localcontext
import unittest
from pathlib import Path
from unittest.mock import patch

from paper_execution import ledger as ledger_module
from paper_execution.ledger import PaperLedger
from pipeline.api import core_decide


def candles(count, interval, end_ms):
    start = end_ms - count * interval
    rows = []
    for index in range(count):
        opened = start + index * interval
        close = 100.0 + index * 0.1
        rows.append({
            "openTimeMs": opened,
            "closeTimeMs": opened + interval,
            "availableAtMs": opened + interval,
            "open": str(close - 0.05),
            "high": str(close + 0.2),
            "low": str(close - 0.2),
            "close": str(close),
            "volume": "1",
            "isClosed": True,
        })
    return rows


def window(rows, timeframe):
    return {
        "timeframe": timeframe,
        "candles": rows,
        "coverage": {"expected": len(rows), "returned": len(rows), "complete": True},
        "datasetVersion": "sha256:" + ("a" if timeframe == "15m" else "b") * 64,
    }


def _multiprocess_core_entry_worker(database_path, intent, book, now, barrier, result_queue):
    try:
        ledger = PaperLedger(
            database_path, max_position_base="1", fee_rate="0.001",
            strategy_id="STRATEGY_CORE", source_sha="c" * 40,
            risk_limits={
                "maxDrawdownPct": "50",
                "maxDailyLossUsdt": "50",
                "maxExposureUsdt": "1000",
            },
            require_risk_limits=True, apply_migrations=False,
        )
        barrier.wait(timeout=15)
        order = ledger.submit(
            intent, book, now, strategy_event="ENTRY"
        )
        result_queue.put({"ok": True, "order": order})
    except BaseException as exc:
        result_queue.put({"ok": False, "error": repr(exc)})
        raise


def _hold_sqlite_write_transaction(database_path, acquired_event):
    connection = sqlite3.connect(database_path, timeout=10)
    try:
        connection.execute("BEGIN IMMEDIATE")
        connection.execute(
            "INSERT INTO process_crash_probe(marker) VALUES ('uncommitted')"
        )
        acquired_event.set()
        multiprocessing.Event().wait(60)
    finally:
        connection.close()


def _hold_sqlite_write_lock_until_released(database_path, acquired_event, release_event):
    connection = sqlite3.connect(database_path, timeout=10)
    try:
        connection.execute("BEGIN IMMEDIATE")
        connection.execute(
            "INSERT INTO process_crash_probe(marker) VALUES ('lock-holder-uncommitted')"
        )
        acquired_event.set()
        if not release_event.wait(30):
            raise TimeoutError("test did not release SQLite writer lock")
        connection.rollback()
    finally:
        connection.close()


class CoreFirstOperationalProofTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.now = 1_800_000_000_000
        self.m15_rows = candles(120, 900_000, self.now)
        current_open = self.m15_rows[-1]["openTimeMs"]
        h1_end = current_open // 3_600_000 * 3_600_000
        self.h1_rows = candles(120, 3_600_000, h1_end)
        self.m15 = window(self.m15_rows, "15m")
        self.h1 = window(self.h1_rows, "1h")
        self.close = float(self.m15_rows[-1]["close"])
        self.book = {
            "source": "hummingbot",
            "connector": "binance_perpetual",
            "symbol": "BTCUSDT",
            "observedAtMs": self.now,
            "bids": [{"price": str(self.close - 0.01), "quantity": "1"}],
            "asks": [{"price": str(self.close + 0.01), "quantity": "1"}],
        }

        self.path = Path(self.temp.name) / "core-first-paper.sqlite3"
        bootstrap = PaperLedger(self.path, max_position_base="1", fee_rate="0.001")
        bootstrap.record_equity(
            "100", self.now - 60_000, self.now,
            "sha256:core-first-seed", "100",
        )
        self.core = PaperLedger(
            self.path, max_position_base="1", fee_rate="0.001",
            strategy_id="STRATEGY_CORE", source_sha="c" * 40,
            risk_limits={
                "maxDrawdownPct": "50",
                "maxDailyLossUsdt": "50",
                "maxExposureUsdt": "1000",
            },
            require_risk_limits=True,
        )
        self.ai = PaperLedger(
            self.path, max_position_base="1", fee_rate="0.001",
            strategy_id="AI_FREQAI", source_sha="c" * 40, leverage="3",
            risk_limits={
                "maxDrawdownPct": "50",
                "maxDailyLossUsdt": "50",
                "maxExposureUsdt": "1000",
            },
            require_risk_limits=True,
        )
        day = self.now // 86_400_000 * 86_400_000
        with sqlite3.connect(self.path) as connection:
            connection.execute(
                """UPDATE paper_account_risk_state SET high_water_mark_quote='100',
                   daily_baseline_utc_day_ms=?,daily_baseline_equity_quote='100',
                   last_equity_quote='100',last_mark_price=?,mark_observed_at_ms=?,
                   mark_candle_close_ms=?,dataset_version='sha256:core-first-seed',
                   risk_ready=1,unavailable_reason=NULL,updated_at_ms=? WHERE account_id=1""",
                (day, str(self.close), self.now, self.now - 60_000, self.now),
            )
        ledger_module.record_funding_coverage(
            self.path, coverage_id="core-first-funding-coverage",
            start_at_ms=self.now - 86_400_000, end_at_ms=self.now,
            status="VERIFIED", source="FIXTURE_RECONCILED_HISTORY",
            source_snapshot_id="fixture:core-first-funding",
            payload_hash="sha256:" + "d" * 64,
            config_version="fixture-funding-v1", recorded_at_ms=self.now,
        )
        ledger_module.record_account_equity_cutover(
            self.path, cutover_id="core-first-cutover",
            expected_initial_capital_quote="100",
            expected_realized_pnl_quote="0", expected_fees_quote="0",
            expected_funding_quote="0", expected_account_equity_quote="100",
            mark_price=str(self.close), mark_candle_close_ms=self.now - 60_000,
            mark_observed_at_ms=self.now,
            dataset_version="sha256:core-first-seed",
            funding_coverage_start_at_ms=self.now - 86_400_000,
            source="FIXTURE_RECONCILED_HISTORY",
            source_snapshot_id="fixture:core-first-cutover",
            payload_hash="sha256:" + "e" * 64,
            config_version="fixture-cutover-v1", recorded_at_ms=self.now,
        )

    def core_indicators(self, adx=30.0):
        m15_values = [{"rsi": 20.0, "adx": 25.0} for _ in self.m15_rows]
        m15_values[-2] = {"rsi": 29.0, "adx": 25.0}
        m15_values[-1] = {"rsi": 35.0, "adx": adx}
        h1_values = [
            {"plus_di": 40.0, "minus_di": 10.0, "adx": 30.0}
            for _ in self.h1_rows
        ]
        return m15_values, h1_values

    def decide(self, *, m15=None, book=None, adx=30.0, indicator_values=None, now_ms=None):
        decision_at = self.now if now_ms is None else now_ms
        with patch.dict(os.environ, {
            "MARKET_DATA_DB": str(self.path),
            "PAPER_MAX_POSITION_BASE": "1",
            "AI_EXECUTION_ENABLED": "false",
        }, clear=False), patch(
            "pipeline.api.market_window", side_effect=[m15 or self.m15, self.h1]
        ), patch(
            "pipeline.core_strategy.indicators",
            side_effect=indicator_values if indicator_values is not None else self.core_indicators(adx)
        ):
            return core_decide(decision_at, book or self.book)

    def test_core_signal_flows_through_shared_risk_into_paper_ledger(self):
        signal = self.decide()
        self.assertEqual(signal["source"], "STRATEGY_CORE", signal)
        self.assertEqual(signal["action"], "BUY", signal)
        self.assertIsNotNone(signal["intent"], signal)

        order = self.core.submit(
            signal["intent"], self.book, self.now, strategy_event="ENTRY"
        )
        self.assertEqual(order["status"], "FILLED", order)
        self.assertEqual(
            self.core.snapshot()["positionBase"],
            signal["intent"]["targetPositionBase"],
        )
        self.assertEqual(self.ai.snapshot()["positionBase"], "0")

        with sqlite3.connect(self.path) as connection:
            reservation = connection.execute(
                """SELECT equity_basis_quote,reserved_margin_quote,
                          reserved_notional_quote,status
                   FROM paper_risk_reservations
                   WHERE strategy_id='STRATEGY_CORE' AND intent_id=?""",
                (signal["intent"]["intentId"],),
            ).fetchone()
            ai_orders = connection.execute(
                "SELECT COUNT(*) FROM paper_orders WHERE strategy_id='AI_FREQAI'"
            ).fetchone()[0]
        self.assertIsNotNone(reservation)
        basis, margin, notional, status = reservation
        self.assertLessEqual(Decimal(margin), Decimal(basis) * Decimal("0.01"))
        self.assertGreater(Decimal(margin), Decimal(basis) * Decimal("0.0099"))
        self.assertEqual(Decimal(notional), Decimal(margin) * Decimal("13"))
        self.assertEqual(status, "CONSUMED")
        self.assertEqual(ai_orders, 0)

        replay = self.core.submit(
            signal["intent"], self.book, self.now, strategy_event="ENTRY"
        )
        self.assertEqual(replay, order)
        self.assertEqual(len(self.core.snapshot()["orders"]), 1)

    def test_post_entry_account_equity_snapshot_is_ready_for_smart_dca(self):
        signal = self.decide()
        self.assertEqual(signal["action"], "BUY", signal)
        entry = self.core.submit(
            signal["intent"], self.book, self.now, strategy_event="ENTRY"
        )
        self.assertEqual(entry["status"], "FILLED", entry)

        from paper_execution.ledger import read_account_risk_snapshot
        risk = read_account_risk_snapshot(self.path, now_ms=self.now)
        self.assertTrue(risk["riskReady"], risk)
        from paper_execution.ledger import dual_ledger_ready, read_snapshot
        self.assertTrue(dual_ledger_ready(self.path))
        self.assertEqual(
            read_snapshot(self.path, strategy_id="STRATEGY_CORE")["strategyState"]["strategyId"],
            "STRATEGY_CORE",
        )

        # Move the closed M15 price against the open long position to exercise
        # the real Smart DCA decision and paper submission path.
        dca_rows = [dict(row) for row in self.m15_rows]
        dca_close = self.close * 0.97
        dca_rows[-1].update(
            open=str(self.close * 0.975),
            high=str(self.close * 0.98),
            low=str(self.close * 0.96),
            close=str(dca_close),
        )
        dca_window = window(dca_rows, "15m")
        dca_window["datasetVersion"] = "sha256:" + "f" * 64
        dca_book = {
            "source": "hummingbot",
            "connector": "binance_perpetual",
            "symbol": "BTCUSDT",
            "observedAtMs": self.now,
            "bids": [{"price": str(dca_close - 0.01), "quantity": "1"}],
            "asks": [{"price": str(dca_close + 0.01), "quantity": "1"}],
        }
        from paper_execution.ledger import read_account_risk_snapshot as read_risk
        risk_diagnostics = []
        def diagnostic_risk_reader(db_path, *, now_ms):
            try:
                result = read_risk(db_path, now_ms=now_ms)
                risk_diagnostics.append({"riskReady": result.get("riskReady"), "reason": result.get("unavailableReason"), "equity": result.get("accountEquityQuote"), "equityExponent": Decimal(result["accountEquityQuote"]).as_tuple().exponent})
                return result
            except Exception as error:
                risk_diagnostics.append({"error": repr(error)})
                raise
        with patch("paper_execution.ledger.read_account_risk_snapshot", side_effect=diagnostic_risk_reader):
            dca_signal = self.decide(m15=dca_window, book=dca_book, adx=50.0)
        self.assertEqual(dca_signal["source"], "STRATEGY_CORE", dca_signal)
        self.assertEqual(dca_signal["action"], "BUY", dca_signal)
        self.assertEqual(dca_signal["reason"], "DCA", {"signal": dca_signal, "riskDiagnostics": risk_diagnostics})
        self.assertIsNotNone(dca_signal["intent"], dca_signal)

        dca = self.core.submit(
            dca_signal["intent"], dca_book, self.now, strategy_event="DCA"
        )
        self.assertEqual(dca["status"], "FILLED", dca)
        self.assertTrue(self.core.strategy_state()["dcaUsed"])
        self.assertEqual(self.ai.snapshot()["positionBase"], "0")

        with sqlite3.connect(self.path) as connection:
            reservations = connection.execute(
                """SELECT equity_basis_quote,reserved_margin_quote,
                          reserved_notional_quote,status
                   FROM paper_risk_reservations
                   WHERE strategy_id='STRATEGY_CORE' ORDER BY created_at_ms"""
            ).fetchall()
        self.assertEqual(len(reservations), 2)
        for basis, margin, notional, status in reservations:
            with localcontext() as context:
                context.prec = 80
                self.assertLessEqual(Decimal(margin), Decimal(basis) * Decimal("0.01"))
                self.assertGreater(Decimal(margin), Decimal(basis) * Decimal("0.0099"))
                self.assertEqual(Decimal(notional), Decimal(margin) * Decimal("13"))
            self.assertEqual(status, "CONSUMED")


    def test_full_core_position_lifecycle_exit_pnl_fees_equity_and_post_exit_kill(self):
        # ENTRY through the real Core signal adapter and shared paper ledger.
        entry_signal = self.decide()
        self.assertEqual(entry_signal["action"], "BUY", entry_signal)
        entry = self.core.submit(
            entry_signal["intent"], self.book, self.now, strategy_event="ENTRY"
        )
        self.assertEqual(entry["status"], "FILLED", entry)

        # Smart DCA through the real RSI/ADX decision path.
        dca_rows = [dict(row) for row in self.m15_rows]
        dca_close = self.close * 0.97
        dca_rows[-1].update(
            open=str(self.close * 0.975),
            high=str(self.close * 0.98),
            low=str(self.close * 0.96),
            close=str(dca_close),
        )
        dca_window = window(dca_rows, "15m")
        dca_window["datasetVersion"] = "sha256:" + "f" * 64
        dca_book = {
            "source": "hummingbot", "connector": "binance_perpetual",
            "symbol": "BTCUSDT", "observedAtMs": self.now,
            "bids": [{"price": str(dca_close - 0.01), "quantity": "1"}],
            "asks": [{"price": str(dca_close + 0.01), "quantity": "1"}],
        }
        dca_signal = self.decide(m15=dca_window, book=dca_book, adx=50.0)
        self.assertEqual(dca_signal["action"], "BUY", dca_signal)
        self.assertEqual(dca_signal["reason"], "DCA", dca_signal)
        dca = self.core.submit(
            dca_signal["intent"], dca_book, self.now, strategy_event="DCA"
        )
        self.assertEqual(dca["status"], "FILLED", dca)
        self.assertTrue(self.core.strategy_state()["dcaUsed"])

        # Mark the still-open position above its weighted cost basis and prove
        # unrealized PnL is included in account equity before EXIT.
        from paper_execution.ledger import read_account_risk_snapshot
        average = Decimal(self.core.snapshot()["averageEntryPrice"])
        mark_price = (average * Decimal("1.05")).quantize(Decimal("0.000000000001"))
        mark_at = self.now
        account_ledger = PaperLedger(
            self.path, max_position_base="1", fee_rate="0.001",
            source_sha="c" * 40,
        )
        with sqlite3.connect(self.path) as connection:
            capital_raw = connection.execute(
                "SELECT initial_capital FROM paper_accounts WHERE account_id=1"
            ).fetchone()[0]
            ledger_rows = connection.execute(
                """SELECT position_base,average_entry_price,realized_pnl_quote,
                          fees_quote,funding_quote
                   FROM paper_strategy_ledgers WHERE account_id=1"""
            ).fetchall()
            adjustment_rows = connection.execute(
                """SELECT adjustment_type,amount_quote FROM paper_account_adjustments
                   WHERE account_id=1"""
            ).fetchall()
        with localcontext() as context:
            context.prec = 80
            equity_probe = Decimal(capital_raw)
            for raw_qty, raw_avg, raw_realized, raw_fee, raw_funding in ledger_rows:
                qty, avg = Decimal(raw_qty), Decimal(raw_avg)
                equity_probe += Decimal(raw_realized) - Decimal(raw_fee) - Decimal(raw_funding)
                equity_probe += qty * (mark_price - avg) if qty else Decimal("0")
            for kind, amount in adjustment_rows:
                equity_probe += Decimal(amount) if kind == "LEGACY_REALIZED_PNL" else -Decimal(amount)
        self.assertGreater(equity_probe, Decimal("0"), {
            "capital": capital_raw, "ledgerRows": ledger_rows,
            "adjustments": adjustment_rows, "mark": str(mark_price),
            "equityProbe": str(equity_probe),
        })
        account_ledger.record_account_mark(
            str(mark_price), self.now - 60_000, mark_at,
            "sha256:" + "9" * 64, "100",
        )
        risk_before_exit = read_account_risk_snapshot(self.path, now_ms=mark_at)
        self.assertTrue(risk_before_exit["riskReady"], risk_before_exit)
        self.assertGreater(
            Decimal(risk_before_exit["positions"]["STRATEGY_CORE"]["unrealizedPnlQuote"]),
            Decimal("0"),
        )
        self.assertGreater(Decimal(risk_before_exit["accountEquityQuote"]), Decimal("100"))

        # Ask Strategy Core itself to emit FLAT/CLOSE via its take-profit rule.
        exit_rows = [dict(row) for row in self.m15_rows]
        exit_rows[-1].update(
            open=str(mark_price * Decimal("0.999")),
            high=str(mark_price * Decimal("1.001")),
            low=str(mark_price * Decimal("0.998")),
            close=str(mark_price),
        )
        exit_window = window(exit_rows, "15m")
        exit_window["datasetVersion"] = "sha256:" + "8" * 64
        exit_now = self.now
        exit_book = {
            "source": "hummingbot", "connector": "binance_perpetual",
            "symbol": "BTCUSDT", "observedAtMs": exit_now,
            "bids": [{"price": str(mark_price), "quantity": "1"}],
            "asks": [{"price": str(mark_price + Decimal("0.01")), "quantity": "1"}],
        }
        exit_m15_indicators = [
            {"rsi": 20.0, "adx": 25.0} for _ in self.m15_rows
        ]
        exit_m15_indicators[-2] = {"rsi": 70.0, "adx": 25.0}
        exit_m15_indicators[-1] = {"rsi": 90.0, "adx": 25.0}
        exit_h1_indicators = [
            {"plus_di": 40.0, "minus_di": 10.0, "adx": 30.0}
            for _ in self.h1_rows
        ]
        from paper_execution.ledger import dual_ledger_ready, read_snapshot
        self.assertTrue(dual_ledger_ready(self.path))
        exit_paper_snapshot = read_snapshot(self.path, strategy_id="STRATEGY_CORE")
        self.assertNotEqual(exit_paper_snapshot["positionBase"], "0")
        self.assertEqual(exit_paper_snapshot["strategyState"]["owner"], "STRATEGY_CORE")
        exit_signal = self.decide(
            m15=exit_window, book=exit_book, now_ms=exit_now,
            indicator_values=(exit_m15_indicators, exit_h1_indicators),
        )
        self.assertEqual(exit_signal["action"], "CLOSE", exit_signal)
        self.assertEqual(exit_signal["reason"], "TAKE_PROFIT", exit_signal)
        self.assertEqual(exit_signal["intent"]["targetPositionBase"], "0")
        exit_order = self.core.submit(
            exit_signal["intent"], exit_book, exit_now, strategy_event="EXIT"
        )
        self.assertEqual(exit_order["status"], "FILLED", exit_order)
        self.assertEqual(self.core.snapshot()["positionBase"], "0")
        self.assertEqual(self.core.snapshot()["averageEntryPrice"], "0")
        self.assertFalse(self.core.strategy_state()["dcaUsed"])

        # Reconcile realized PnL, all three execution fees, and final equity.
        risk_after_exit = read_account_risk_snapshot(self.path, now_ms=exit_now)
        self.assertTrue(risk_after_exit["riskReady"], risk_after_exit)
        self.assertEqual(
            risk_after_exit["positions"]["STRATEGY_CORE"]["unrealizedPnlQuote"],
            "0",
        )
        with sqlite3.connect(self.path) as connection:
            realized_raw, fees_raw, funding_raw = connection.execute(
                """SELECT realized_pnl_quote,fees_quote,funding_quote
                   FROM paper_strategy_ledgers
                   WHERE account_id=1 AND strategy_id='STRATEGY_CORE'"""
            ).fetchone()
        realized, fees, funding = map(Decimal, (realized_raw, fees_raw, funding_raw))
        with localcontext() as context:
            context.prec = 80
            expected_fees = sum(
                (Decimal(order["feeQuote"]) for order in (entry, dca, exit_order)),
                Decimal("0"),
            )
        self.assertGreater(realized, Decimal("0"))
        self.assertEqual(fees, expected_fees)
        self.assertEqual(funding, Decimal("0"))
        with localcontext() as context:
            context.prec = 80
            expected_equity = Decimal("100") + realized - fees - funding
            self.assertEqual(Decimal(risk_after_exit["accountEquityQuote"]), expected_equity)

        # Latch the shared Kill Switch only after the position is flat; it must
        # survive the EXIT and reject a fresh Core ENTRY without new exposure.
        kill_at = exit_now + 1
        self.core.set_killed(True, kill_at, "CORE_EXIT_LIFECYCLE_COMPLETE")
        killed_snapshot = self.core.snapshot()
        self.assertTrue(killed_snapshot["riskControl"]["killed"])
        next_entry_intent = dict(entry_signal["intent"])
        next_entry_intent.update({
            "intentId": "core-entry-after-exit-kill",
            "decisionAtMs": kill_at + 1,
            "validUntilMs": kill_at + 30_001,
            "inputSnapshotId": "fixture:entry-after-exit-kill",
        })
        next_book = {
            "source": "hummingbot", "connector": "binance_perpetual",
            "symbol": "BTCUSDT", "observedAtMs": kill_at + 1,
            "bids": [{"price": str(mark_price - Decimal("0.01")), "quantity": "1"}],
            "asks": [{"price": str(mark_price), "quantity": "1"}],
        }
        blocked = self.core.submit(
            next_entry_intent, next_book, kill_at + 1, strategy_event="ENTRY"
        )
        self.assertEqual(blocked["status"], "REJECTED", blocked)
        self.assertEqual(blocked["reason"], "KILL_SWITCH", blocked)
        self.assertEqual(self.core.snapshot()["positionBase"], "0")
        self.assertEqual(self.ai.snapshot()["positionBase"], "0")

    def test_kill_switch_rejects_core_entry_without_creating_exposure(self):
        signal = self.decide()
        self.assertEqual(signal["action"], "BUY", signal)
        self.core.set_killed(True, self.now, "CORE_FIRST_KILL_SWITCH_TEST")

        order = self.core.submit(
            signal["intent"], self.book, self.now, strategy_event="ENTRY"
        )
        self.assertEqual(order["status"], "REJECTED", order)
        self.assertEqual(order["reason"], "KILL_SWITCH")
        self.assertEqual(self.core.snapshot()["positionBase"], "0")
        self.assertEqual(self.ai.snapshot()["positionBase"], "0")


    def test_concurrent_core_intents_share_one_net_position_and_kill_switch(self):
        signal = self.decide()
        self.assertEqual(signal["action"], "BUY", signal)
        first_intent = dict(signal["intent"])
        second_intent = dict(signal["intent"])
        second_intent.update({
            "intentId": "core-concurrent-competing-intent",
            "inputSnapshotId": "fixture:core-concurrent-competing-intent",
        })

        competing_core = PaperLedger(
            self.path, max_position_base="1", fee_rate="0.001",
            strategy_id="STRATEGY_CORE", source_sha="c" * 40,
            risk_limits={
                "maxDrawdownPct": "50",
                "maxDailyLossUsdt": "50",
                "maxExposureUsdt": "1000",
            },
            require_risk_limits=True, apply_migrations=False,
        )
        gate = Barrier(2)

        def submit(ledger_instance, intent):
            gate.wait(timeout=5)
            return ledger_instance.submit(
                intent, dict(self.book), self.now, strategy_event="ENTRY"
            )

        with ThreadPoolExecutor(max_workers=2) as pool:
            first_future = pool.submit(submit, self.core, first_intent)
            second_future = pool.submit(submit, competing_core, second_intent)
            orders = [first_future.result(timeout=15), second_future.result(timeout=15)]

        target = Decimal(first_intent["targetPositionBase"])
        self.assertEqual(self.core.snapshot()["positionBase"], str(target))
        self.assertEqual(self.ai.snapshot()["positionBase"], "0")
        self.assertEqual(sum((Decimal(order["filledBase"]) for order in orders), Decimal("0")), target)
        self.assertEqual(sum(1 for order in orders if Decimal(order["filledBase"]) > 0), 1)

        with sqlite3.connect(self.path) as connection:
            persisted = connection.execute(
                """SELECT intent_id,status,document,reservation_id
                   FROM paper_orders
                   WHERE intent_id IN (?,?)
                   ORDER BY intent_id""",
                (first_intent["intentId"], second_intent["intentId"]),
            ).fetchall()
            fill_events = connection.execute(
                """SELECT COUNT(*) FROM paper_account_event_journal
                   WHERE account_id=1 AND strategy_id='STRATEGY_CORE'
                     AND event_type='FILL'"""
            ).fetchone()[0]
            reservations = connection.execute(
                """SELECT COUNT(*) FROM paper_risk_reservations
                   WHERE account_id=1 AND strategy_id='STRATEGY_CORE'
                     AND intent_id IN (?,?)""",
                (first_intent["intentId"], second_intent["intentId"]),
            ).fetchone()[0]
            ai_orders = connection.execute(
                "SELECT COUNT(*) FROM paper_orders WHERE strategy_id='AI_FREQAI'"
            ).fetchone()[0]

        self.assertEqual(len(persisted), 2)
        self.assertEqual(fill_events, 1)
        self.assertEqual(reservations, 1)
        self.assertEqual(ai_orders, 0)
        for intent_id, status, document, reservation_id in persisted:
            order_document = json.loads(document)
            self.assertEqual(order_document["intentId"], intent_id)
            if Decimal(order_document["filledBase"]) > 0:
                self.assertEqual(status, "FILLED")
                self.assertIsNotNone(reservation_id)
            else:
                self.assertEqual(status, "FILLED")
                self.assertIsNone(reservation_id)

        kill_at = self.now + 1
        self.core.set_killed(True, kill_at, "CORE_CONCURRENT_ADMISSION_TEST")
        blocked_intent = dict(first_intent)
        blocked_intent.update({
            "intentId": "core-entry-after-concurrent-kill",
            "targetPositionBase": str(target + Decimal("0.01")),
            "decisionAtMs": kill_at + 1,
            "validUntilMs": kill_at + 30_001,
            "inputSnapshotId": "fixture:core-entry-after-concurrent-kill",
        })
        blocked_book = dict(self.book)
        blocked_book["observedAtMs"] = kill_at + 1
        blocked = self.core.submit(
            blocked_intent, blocked_book, kill_at + 1, strategy_event="DCA"
        )
        self.assertEqual(blocked["status"], "REJECTED", blocked)
        self.assertEqual(blocked["reason"], "KILL_SWITCH")
        self.assertEqual(self.core.snapshot()["positionBase"], str(target))
        self.assertTrue(self.core.snapshot()["riskControl"]["killed"])



    def test_multiprocess_core_entry_contention_serializes_all_clients(self):
        signal = self.decide()
        self.assertEqual(signal["action"], "BUY", signal)
        base_intent = dict(signal["intent"])
        target = Decimal(base_intent["targetPositionBase"])
        stress_path = Path(self.temp.name) / "core-multiprocess-contention.sqlite3"
        with sqlite3.connect(self.path) as source, sqlite3.connect(stress_path) as target_db:
            source.backup(target_db)

        context = multiprocessing.get_context("spawn")
        client_count = 6
        barrier = context.Barrier(client_count)
        result_queue = context.Queue()
        processes = []
        for index in range(client_count):
            intent = dict(base_intent)
            intent.update({
                "intentId": f"core-multiprocess-{index}",
                "decisionAtMs": self.now,
                "validUntilMs": self.now + 30_000,
                "inputSnapshotId": f"fixture:core-multiprocess-{index}",
            })
            process = context.Process(
                target=_multiprocess_core_entry_worker,
                args=(str(stress_path), intent, dict(self.book), self.now, barrier, result_queue),
            )
            processes.append(process)

        try:
            for process in processes:
                process.start()
            results = [result_queue.get(timeout=45) for _ in processes]
            for process in processes:
                process.join(timeout=15)
                self.assertFalse(process.is_alive(), f"process {process.pid} did not exit")
                self.assertEqual(process.exitcode, 0)
        finally:
            for process in processes:
                if process.is_alive():
                    process.terminate()
                    process.join(timeout=5)
            result_queue.close()

        self.assertTrue(all(result["ok"] for result in results), results)
        orders = [result["order"] for result in results]
        fills = [order for order in orders if Decimal(order["filledBase"]) > 0]
        self.assertEqual(len(fills), 1, orders)
        self.assertEqual(
            sum((Decimal(order["filledBase"]) for order in orders), Decimal("0")),
            target,
        )
        self.assertTrue(all(order["status"] == "FILLED" for order in orders), orders)

        with sqlite3.connect(stress_path) as connection:
            self.assertEqual(
                connection.execute("PRAGMA integrity_check").fetchone()[0], "ok"
            )
            order_count = connection.execute(
                """SELECT COUNT(*) FROM paper_orders
                   WHERE account_id=1 AND strategy_id='STRATEGY_CORE'"""
            ).fetchone()[0]
            fill_count = connection.execute(
                """SELECT COUNT(*) FROM paper_account_event_journal
                   WHERE account_id=1 AND strategy_id='STRATEGY_CORE'
                     AND event_type='FILL'"""
            ).fetchone()[0]
            reservation_count = connection.execute(
                """SELECT COUNT(*) FROM paper_risk_reservations
                   WHERE account_id=1 AND strategy_id='STRATEGY_CORE'"""
            ).fetchone()[0]
            ai_order_count = connection.execute(
                "SELECT COUNT(*) FROM paper_orders WHERE strategy_id='AI_FREQAI'"
            ).fetchone()[0]
        self.assertEqual(order_count, client_count)
        self.assertEqual(fill_count, 1)
        self.assertEqual(reservation_count, 1)
        self.assertEqual(ai_order_count, 0)
        self.assertEqual(
            PaperLedger(
                stress_path, max_position_base="1", fee_rate="0.001",
                strategy_id="STRATEGY_CORE", source_sha="c" * 40,
                risk_limits={
                    "maxDrawdownPct": "50",
                    "maxDailyLossUsdt": "50",
                    "maxExposureUsdt": "1000",
                },
                require_risk_limits=True, apply_migrations=False,
            ).snapshot()["positionBase"],
            str(target),
        )


    def test_sqlite_lock_timeout_fails_closed_then_retry_succeeds(self):
        lock_path = Path(self.temp.name) / "core-lock-timeout.sqlite3"
        with sqlite3.connect(self.path) as source, sqlite3.connect(lock_path) as target_db:
            source.backup(target_db)
        with sqlite3.connect(lock_path) as connection:
            connection.execute(
                "CREATE TABLE process_crash_probe (marker TEXT NOT NULL)"
            )

        signal = self.decide()
        intent = dict(signal["intent"])
        intent.update({
            "intentId": "core-lock-timeout-retry",
            "decisionAtMs": self.now,
            "validUntilMs": self.now + 60_000,
            "inputSnapshotId": "fixture:core-lock-timeout-retry",
        })
        context = multiprocessing.get_context("spawn")
        acquired = context.Event()
        release = context.Event()
        holder = context.Process(
            target=_hold_sqlite_write_lock_until_released,
            args=(str(lock_path), acquired, release),
        )
        holder.start()
        try:
            self.assertTrue(acquired.wait(timeout=20), "writer never acquired SQLite lock")
            ledger = PaperLedger(
                lock_path, max_position_base="1", fee_rate="0.001",
                strategy_id="STRATEGY_CORE", source_sha="c" * 40,
                risk_limits={
                    "maxDrawdownPct": "50",
                    "maxDailyLossUsdt": "50",
                    "maxExposureUsdt": "1000",
                },
                require_risk_limits=True, apply_migrations=False,
            )
            started = __import__("time").monotonic()
            with self.assertRaisesRegex(sqlite3.OperationalError, "locked"):
                ledger.submit(
                    intent, dict(self.book), self.now, strategy_event="ENTRY"
                )
            elapsed = __import__("time").monotonic() - started
            self.assertGreaterEqual(elapsed, 9.0, f"lock timeout fired too early: {elapsed:.3f}s")
        finally:
            release.set()
            holder.join(timeout=10)
            if holder.is_alive():
                holder.terminate()
                holder.join(timeout=5)

        self.assertEqual(holder.exitcode, 0)
        with sqlite3.connect(lock_path, timeout=10) as connection:
            self.assertEqual(
                connection.execute("PRAGMA integrity_check").fetchone()[0], "ok"
            )
            self.assertEqual(
                connection.execute(
                    "SELECT COUNT(*) FROM process_crash_probe"
                ).fetchone()[0],
                0,
            )
            self.assertEqual(
                connection.execute(
                    """SELECT COUNT(*) FROM paper_orders
                       WHERE account_id=1 AND strategy_id='STRATEGY_CORE'"""
                ).fetchone()[0],
                0,
            )
            self.assertEqual(
                connection.execute(
                    """SELECT COUNT(*) FROM paper_risk_reservations
                       WHERE account_id=1 AND strategy_id='STRATEGY_CORE'"""
                ).fetchone()[0],
                0,
            )
            self.assertEqual(
                connection.execute(
                    """SELECT COUNT(*) FROM paper_account_event_journal
                       WHERE account_id=1 AND strategy_id='STRATEGY_CORE'
                         AND event_type='FILL'"""
                ).fetchone()[0],
                0,
            )

        retry_order = ledger.submit(
            intent, dict(self.book), self.now, strategy_event="ENTRY"
        )
        self.assertGreater(Decimal(retry_order["filledBase"]), Decimal("0"))
        self.assertEqual(ledger.snapshot()["positionBase"], intent["targetPositionBase"])
        with sqlite3.connect(lock_path) as connection:
            self.assertEqual(
                connection.execute("PRAGMA integrity_check").fetchone()[0], "ok"
            )
            self.assertEqual(
                connection.execute(
                    """SELECT COUNT(*) FROM paper_orders
                       WHERE account_id=1 AND strategy_id='STRATEGY_CORE'"""
                ).fetchone()[0],
                1,
            )
            self.assertEqual(
                connection.execute(
                    """SELECT COUNT(*) FROM paper_risk_reservations
                       WHERE account_id=1 AND strategy_id='STRATEGY_CORE'"""
                ).fetchone()[0],
                1,
            )


    def test_interrupted_sqlite_writer_rolls_back_and_database_recovers(self):
        recovery_path = Path(self.temp.name) / "core-interrupted-writer.sqlite3"
        with sqlite3.connect(self.path) as source, sqlite3.connect(recovery_path) as target_db:
            source.backup(target_db)
        with sqlite3.connect(recovery_path) as connection:
            connection.execute(
                "CREATE TABLE process_crash_probe (marker TEXT NOT NULL)"
            )

        context = multiprocessing.get_context("spawn")
        acquired = context.Event()
        process = context.Process(
            target=_hold_sqlite_write_transaction,
            args=(str(recovery_path), acquired),
        )
        process.start()
        try:
            self.assertTrue(acquired.wait(timeout=20), "writer never acquired BEGIN IMMEDIATE")
            process.terminate()
            process.join(timeout=10)
            self.assertFalse(process.is_alive())
        finally:
            if process.is_alive():
                process.kill()
                process.join(timeout=5)

        with sqlite3.connect(recovery_path, timeout=10) as connection:
            self.assertEqual(
                connection.execute("PRAGMA integrity_check").fetchone()[0], "ok"
            )
            self.assertEqual(
                connection.execute(
                    "SELECT COUNT(*) FROM process_crash_probe WHERE marker='uncommitted'"
                ).fetchone()[0],
                0,
            )

        signal = self.decide()
        recovered_ledger = PaperLedger(
            recovery_path, max_position_base="1", fee_rate="0.001",
            strategy_id="STRATEGY_CORE", source_sha="c" * 40,
            risk_limits={
                "maxDrawdownPct": "50",
                "maxDailyLossUsdt": "50",
                "maxExposureUsdt": "1000",
            },
            require_risk_limits=True, apply_migrations=False,
        )
        recovered_order = recovered_ledger.submit(
            signal["intent"], dict(self.book), self.now, strategy_event="ENTRY"
        )
        self.assertGreater(Decimal(recovered_order["filledBase"]), Decimal("0"))
        self.assertEqual(recovered_ledger.snapshot()["positionBase"], signal["intent"]["targetPositionBase"])
        with sqlite3.connect(recovery_path) as connection:
            self.assertEqual(
                connection.execute("PRAGMA integrity_check").fetchone()[0], "ok"
            )


    def test_repeated_multi_client_entry_stress_has_no_duplicate_or_orphan_reservations(self):
        signal = self.decide()
        self.assertEqual(signal["action"], "BUY", signal)
        base_intent = dict(signal["intent"])
        target = Decimal(base_intent["targetPositionBase"])

        for round_index in range(3):
            with self.subTest(round=round_index):
                stress_path = Path(self.temp.name) / f"core-stress-{round_index}.sqlite3"
                with sqlite3.connect(self.path) as source, sqlite3.connect(stress_path) as target_db:
                    source.backup(target_db)

                client_count = 8
                clients = [
                    PaperLedger(
                        stress_path, max_position_base="1", fee_rate="0.001",
                        strategy_id="STRATEGY_CORE", source_sha="c" * 40,
                        risk_limits={
                            "maxDrawdownPct": "50",
                            "maxDailyLossUsdt": "50",
                            "maxExposureUsdt": "1000",
                        },
                        require_risk_limits=True, apply_migrations=False,
                    )
                    for _ in range(client_count)
                ]
                gate = Barrier(client_count)
                intents = []
                for client_index in range(client_count):
                    intent = dict(base_intent)
                    intent.update({
                        "intentId": f"core-stress-{round_index}-{client_index}",
                        "decisionAtMs": self.now,
                        "validUntilMs": self.now + 30_000,
                        "inputSnapshotId": f"fixture:core-stress-{round_index}-{client_index}",
                    })
                    intents.append(intent)

                def submit(index):
                    gate.wait(timeout=10)
                    return clients[index].submit(
                        intents[index], dict(self.book), self.now,
                        strategy_event="ENTRY",
                    )

                with ThreadPoolExecutor(max_workers=client_count) as pool:
                    futures = [pool.submit(submit, index) for index in range(client_count)]
                    orders = [future.result(timeout=30) for future in futures]

                fills = [order for order in orders if Decimal(order["filledBase"]) > 0]
                self.assertEqual(len(fills), 1, orders)
                self.assertEqual(
                    sum((Decimal(order["filledBase"]) for order in orders), Decimal("0")),
                    target,
                )
                self.assertTrue(
                    all(order["status"] == "FILLED" for order in orders), orders
                )
                self.assertEqual(clients[0].snapshot()["positionBase"], str(target))

                with sqlite3.connect(stress_path) as connection:
                    persisted = connection.execute(
                        """SELECT intent_id,status,reservation_id,document
                           FROM paper_orders WHERE account_id=1
                             AND strategy_id='STRATEGY_CORE'
                           ORDER BY intent_id"""
                    ).fetchall()
                    fill_events = connection.execute(
                        """SELECT COUNT(*) FROM paper_account_event_journal
                           WHERE account_id=1 AND strategy_id='STRATEGY_CORE'
                             AND event_type='FILL'"""
                    ).fetchone()[0]
                    reservations = connection.execute(
                        """SELECT reservation_id,intent_id,status,
                                  reserved_margin_quote,remaining_margin_quote
                           FROM paper_risk_reservations
                           WHERE account_id=1 AND strategy_id='STRATEGY_CORE'"""
                    ).fetchall()
                    duplicate_intents = connection.execute(
                        """SELECT COUNT(*) FROM (
                               SELECT intent_id,COUNT(*) AS n
                               FROM paper_orders
                               WHERE account_id=1 AND strategy_id='STRATEGY_CORE'
                               GROUP BY intent_id HAVING n > 1
                           )"""
                    ).fetchone()[0]
                    orphan_reservations = connection.execute(
                        """SELECT COUNT(*) FROM paper_risk_reservations r
                           LEFT JOIN paper_orders o
                             ON o.account_id=r.account_id
                            AND o.strategy_id=r.strategy_id
                            AND o.reservation_id=r.reservation_id
                           WHERE r.account_id=1 AND r.strategy_id='STRATEGY_CORE'
                             AND o.reservation_id IS NULL"""
                    ).fetchone()[0]
                    ai_orders = connection.execute(
                        "SELECT COUNT(*) FROM paper_orders WHERE strategy_id='AI_FREQAI'"
                    ).fetchone()[0]

                self.assertEqual(len(persisted), client_count)
                self.assertEqual(fill_events, 1)
                self.assertEqual(len(reservations), 1)
                self.assertEqual(duplicate_intents, 0)
                self.assertEqual(orphan_reservations, 0)
                self.assertEqual(ai_orders, 0)
                self.assertEqual(
                    sum(1 for row in persisted if row[2] is not None), 1
                )
                for _, _, _, reserved_margin, _ in reservations:
                    self.assertLessEqual(
                        Decimal(reserved_margin), Decimal("1")
                    )


    def test_concurrent_mixed_core_entry_dca_preserves_account_risk_budget(self):
        signal = self.decide()
        self.assertEqual(signal["action"], "BUY", signal)
        entry_intent = dict(signal["intent"])
        entry_intent.update({
            "intentId": "core-mixed-race-entry",
            "decisionAtMs": self.now,
            "validUntilMs": self.now + 30_000,
            "inputSnapshotId": "fixture:core-mixed-race-entry",
        })
        entry_target = Decimal(entry_intent["targetPositionBase"])
        dca_target = entry_target * Decimal("1.1")
        dca_at = self.now + 1
        dca_intent = dict(entry_intent)
        dca_intent.update({
            "intentId": "core-mixed-race-dca",
            "targetPositionBase": str(dca_target),
            "decisionAtMs": dca_at,
            "validUntilMs": dca_at + 30_000,
            "inputSnapshotId": "fixture:core-mixed-race-dca",
        })
        dca_book = dict(self.book)
        dca_book["observedAtMs"] = dca_at

        second_core = PaperLedger(
            self.path, max_position_base="1", fee_rate="0.001",
            strategy_id="STRATEGY_CORE", source_sha="c" * 40,
            risk_limits={
                "maxDrawdownPct": "50",
                "maxDailyLossUsdt": "50",
                "maxExposureUsdt": "1000",
            },
            require_risk_limits=True, apply_migrations=False,
        )
        gate = Barrier(2)

        def submit(ledger_instance, intent, book, event, at_ms):
            gate.wait(timeout=5)
            return ledger_instance.submit(
                intent, book, at_ms, strategy_event=event
            )

        with ThreadPoolExecutor(max_workers=2) as pool:
            entry_future = pool.submit(
                submit, self.core, entry_intent, dict(self.book), "ENTRY", self.now
            )
            dca_future = pool.submit(
                submit, second_core, dca_intent, dca_book, "DCA", dca_at
            )
            entry_order = entry_future.result(timeout=15)
            dca_order = dca_future.result(timeout=15)

        self.assertEqual(entry_order["status"], "FILLED", entry_order)
        self.assertIn(dca_order["status"], ("FILLED", "REJECTED"), dca_order)
        if dca_order["status"] == "REJECTED":
            self.assertEqual(
                dca_order["reason"], "DCA_REQUIRES_EXISTING_POSITION", dca_order
            )
            expected_position = entry_target
        else:
            self.assertEqual(dca_order["reason"], "VISIBLE_DEPTH_SIMULATION")
            expected_position = dca_target

        snapshot = self.core.snapshot()
        self.assertEqual(snapshot["positionBase"], str(expected_position))
        self.assertEqual(self.ai.snapshot()["positionBase"], "0")

        with sqlite3.connect(self.path) as connection:
            reservations = connection.execute(
                """SELECT intent_id,status,reserved_margin_quote,
                          remaining_margin_quote,reserved_notional_quote,
                          remaining_notional_quote,equity_basis_quote
                   FROM paper_risk_reservations
                   WHERE account_id=1 AND strategy_id='STRATEGY_CORE'
                     AND intent_id IN (?,?) ORDER BY intent_id""",
                (entry_intent["intentId"], dca_intent["intentId"]),
            ).fetchall()
            pending_count = connection.execute(
                """SELECT COUNT(*) FROM paper_orders
                   WHERE account_id=1 AND strategy_id='STRATEGY_CORE'
                     AND status IN ('OPEN','PARTIALLY_FILLED')"""
            ).fetchone()[0]
            account_positions = connection.execute(
                """SELECT position_base,average_entry_price
                   FROM paper_strategy_ledgers WHERE account_id=1"""
            ).fetchall()
            active_reservations = connection.execute(
                """SELECT remaining_notional_quote FROM paper_risk_reservations
                   WHERE account_id=1 AND status IN ('ACTIVE','PARTIAL')"""
            ).fetchall()
            ai_orders = connection.execute(
                "SELECT COUNT(*) FROM paper_orders WHERE strategy_id='AI_FREQAI'"
            ).fetchone()[0]

        self.assertEqual(len(reservations), 1 if dca_order["status"] == "REJECTED" else 2)
        self.assertLessEqual(pending_count, 1)
        self.assertEqual(ai_orders, 0)
        with localcontext() as context:
            context.prec = 80
            for _, _, reserved_margin, _, _, _, equity_basis in reservations:
                self.assertLessEqual(
                    Decimal(reserved_margin),
                    Decimal(equity_basis) * Decimal("0.01"),
                )

        with localcontext() as context:
            context.prec = 80
            gross_exposure = sum(
                (
                    abs(Decimal(quantity)) * Decimal(average)
                    for quantity, average in account_positions
                    if Decimal(quantity) != 0
                ),
                Decimal("0"),
            )
            active_notional = sum(
                (Decimal(item[0]) for item in active_reservations),
                Decimal("0"),
            )
            self.assertLessEqual(gross_exposure + active_notional, Decimal("1000"))


    def _race_core_admission_against_kill_switch(self, intent, book, event, expected_position):
        gate = Barrier(2)

        def submit():
            gate.wait(timeout=5)
            return self.core.submit(
                intent, book, intent["decisionAtMs"], strategy_event=event
            )

        def kill():
            gate.wait(timeout=5)
            return self.core.set_killed(
                True, intent["decisionAtMs"], "CONCURRENT_KILL_SWITCH_TEST"
            )

        with ThreadPoolExecutor(max_workers=2) as pool:
            submit_future = pool.submit(submit)
            kill_future = pool.submit(kill)
            order = submit_future.result(timeout=15)
            kill_future.result(timeout=15)

        snapshot = self.core.snapshot()
        self.assertTrue(snapshot["riskControl"]["killed"])
        self.assertIn(order["status"], ("FILLED", "REJECTED"), order)
        if order["status"] == "REJECTED":
            self.assertEqual(order["reason"], "KILL_SWITCH", order)
            self.assertEqual(snapshot["positionBase"], expected_position)
        else:
            self.assertEqual(order["status"], "FILLED", order)
            self.assertEqual(snapshot["positionBase"], str(intent["targetPositionBase"]))
        self.assertEqual(self.ai.snapshot()["positionBase"], "0")
        return order

    def test_kill_switch_race_linearizes_core_entry(self):
        signal = self.decide()
        self.assertEqual(signal["action"], "BUY", signal)
        intent = dict(signal["intent"])
        intent.update({
            "intentId": "core-entry-vs-kill-race",
            "decisionAtMs": self.now + 1,
            "validUntilMs": self.now + 30_001,
            "inputSnapshotId": "fixture:core-entry-vs-kill-race",
        })
        book = dict(self.book)
        book["observedAtMs"] = self.now + 1

        order = self._race_core_admission_against_kill_switch(
            intent, book, "ENTRY", "0"
        )
        self.assertIn(order["reason"], ("VISIBLE_DEPTH_SIMULATION", "KILL_SWITCH"))

    def test_kill_switch_race_linearizes_core_dca(self):
        entry_signal = self.decide()
        self.assertEqual(entry_signal["action"], "BUY", entry_signal)
        entry_intent = dict(entry_signal["intent"])
        entry_intent.update({
            "intentId": "core-dca-race-seed-entry",
            "decisionAtMs": self.now,
            "validUntilMs": self.now + 30_000,
            "inputSnapshotId": "fixture:core-dca-race-seed",
        })
        entry = self.core.submit(
            entry_intent, self.book, self.now, strategy_event="ENTRY"
        )
        self.assertEqual(entry["status"], "FILLED", entry)
        current = Decimal(self.core.snapshot()["positionBase"])
        target = current + current / Decimal("10")
        dca_at = self.now + 1
        dca_intent = dict(entry_intent)
        dca_intent.update({
            "intentId": "core-dca-vs-kill-race",
            "targetPositionBase": str(target),
            "decisionAtMs": dca_at,
            "validUntilMs": dca_at + 30_000,
            "inputSnapshotId": "fixture:core-dca-vs-kill-race",
        })
        dca_book = dict(self.book)
        dca_book["observedAtMs"] = dca_at

        order = self._race_core_admission_against_kill_switch(
            dca_intent, dca_book, "DCA", str(current)
        )
        self.assertIn(order["reason"], ("VISIBLE_DEPTH_SIMULATION", "KILL_SWITCH"))


    def test_mixed_writer_contention_serializes_timeout_retry_exposure_and_kill_switch(self):
        stress_path = Path(self.temp.name) / "core-mixed-writer-stress.sqlite3"
        with sqlite3.connect(self.path) as source, sqlite3.connect(stress_path) as target_db:
            source.backup(target_db)
        with sqlite3.connect(stress_path) as connection:
            connection.execute("CREATE TABLE process_crash_probe (marker TEXT NOT NULL)")

        signal = self.decide()
        entry_intent = dict(signal["intent"])
        entry_intent.update({
            "intentId": "core-mixed-writer-short-lock-entry",
            "decisionAtMs": self.now,
            "validUntilMs": self.now + 60_000,
            "inputSnapshotId": "fixture:core-mixed-writer-short-lock-entry",
        })
        context = multiprocessing.get_context("spawn")

        acquired = context.Event()
        release = context.Event()
        holder = context.Process(
            target=_hold_sqlite_write_lock_until_released,
            args=(str(stress_path), acquired, release),
        )
        holder.start()
        self.assertTrue(acquired.wait(timeout=20), "short-lock writer did not acquire lock")
        ledger = PaperLedger(
            stress_path, max_position_base="1", fee_rate="0.001",
            strategy_id="STRATEGY_CORE", source_sha="c" * 40,
            risk_limits={
                "maxDrawdownPct": "50",
                "maxDailyLossUsdt": "50",
                "maxExposureUsdt": "1000",
            },
            require_risk_limits=True, apply_migrations=False,
        )
        attempted = __import__("threading").Event()
        outcome = {}

        def submit_after_short_lock():
            attempted.set()
            outcome["entry"] = ledger.submit(
                entry_intent, dict(self.book), self.now, strategy_event="ENTRY"
            )

        worker = __import__("threading").Thread(target=submit_after_short_lock)
        worker.start()
        try:
            self.assertTrue(attempted.wait(timeout=5))
            __import__("time").sleep(0.25)
        finally:
            release.set()
            holder.join(timeout=10)
            if holder.is_alive():
                holder.terminate()
                holder.join(timeout=5)
        worker.join(timeout=15)
        self.assertFalse(worker.is_alive(), "short-lock admission did not finish")
        self.assertEqual(holder.exitcode, 0)
        entry_order = outcome["entry"]
        self.assertEqual(entry_order["status"], "FILLED", entry_order)
        self.assertGreater(Decimal(entry_order["filledBase"]), Decimal("0"))

        current = Decimal(ledger.snapshot()["positionBase"])
        dca_at = self.now + 1
        dca_intent = dict(entry_intent)
        dca_intent.update({
            "intentId": "core-mixed-writer-timeout-dca",
            "targetPositionBase": str(current * Decimal("1.1")),
            "decisionAtMs": dca_at,
            "validUntilMs": dca_at + 60_000,
            "inputSnapshotId": "fixture:core-mixed-writer-timeout-dca",
        })
        dca_book = dict(self.book)
        dca_book["observedAtMs"] = dca_at
        acquired_long = context.Event()
        release_long = context.Event()
        long_holder = context.Process(
            target=_hold_sqlite_write_lock_until_released,
            args=(str(stress_path), acquired_long, release_long),
        )
        long_holder.start()
        try:
            self.assertTrue(acquired_long.wait(timeout=20), "long-lock writer did not acquire lock")
            started = __import__("time").monotonic()
            with self.assertRaisesRegex(sqlite3.OperationalError, "locked"):
                ledger.submit(dca_intent, dca_book, dca_at, strategy_event="DCA")
            elapsed = __import__("time").monotonic() - started
            self.assertGreaterEqual(elapsed, 9.0, f"timeout fired too early: {elapsed:.3f}s")
        finally:
            release_long.set()
            long_holder.join(timeout=10)
            if long_holder.is_alive():
                long_holder.terminate()
                long_holder.join(timeout=5)
        self.assertEqual(long_holder.exitcode, 0)

        with sqlite3.connect(stress_path) as connection:
            self.assertEqual(connection.execute("PRAGMA integrity_check").fetchone()[0], "ok")
            self.assertEqual(connection.execute(
                "SELECT COUNT(*) FROM paper_orders WHERE strategy_id='STRATEGY_CORE'"
            ).fetchone()[0], 1)
            self.assertEqual(connection.execute(
                "SELECT COUNT(*) FROM paper_risk_reservations WHERE strategy_id='STRATEGY_CORE'"
            ).fetchone()[0], 1)
            self.assertEqual(connection.execute(
                "SELECT COUNT(*) FROM paper_account_event_journal WHERE strategy_id='STRATEGY_CORE' AND event_type='FILL'"
            ).fetchone()[0], 1)
            self.assertEqual(connection.execute(
                "SELECT COUNT(*) FROM paper_orders WHERE strategy_id='AI_FREQAI'"
            ).fetchone()[0], 0)

        dca_order = ledger.submit(dca_intent, dca_book, dca_at, strategy_event="DCA")
        self.assertEqual(dca_order["status"], "FILLED", dca_order)
        self.assertGreater(Decimal(dca_order["filledBase"]), Decimal("0"))

        snapshot = ledger.snapshot()
        post_dca = Decimal(snapshot["positionBase"])
        self.assertLess(post_dca, Decimal("1"))
        with localcontext() as decimal_context:
            decimal_context.prec = 80
            account_exposure = abs(post_dca) * Decimal(snapshot["averageEntryPrice"])
            self.assertLessEqual(account_exposure, Decimal("1000"))

        # Use a separate flat-account fixture so the Kill Switch check reaches
        # the risk gate before the one-DCA-per-position guard.
        kill_path = Path(self.temp.name) / "core-mixed-writer-kill-switch.sqlite3"
        with sqlite3.connect(self.path) as source, sqlite3.connect(kill_path) as target_db:
            source.backup(target_db)
        kill_ledger = PaperLedger(
            kill_path, max_position_base="1", fee_rate="0.001",
            strategy_id="STRATEGY_CORE", source_sha="d" * 40,
            risk_limits={
                "maxDrawdownPct": "50",
                "maxDailyLossUsdt": "50",
                "maxExposureUsdt": "1000",
            },
            require_risk_limits=True, apply_migrations=False,
        )
        kill_entry_intent = dict(entry_intent)
        kill_entry_intent.update({
            "intentId": "core-mixed-writer-kill-entry",
            "decisionAtMs": self.now,
            "validUntilMs": self.now + 60_000,
            "inputSnapshotId": "fixture:core-mixed-writer-kill-entry",
        })
        kill_entry = kill_ledger.submit(
            kill_entry_intent, dict(self.book), self.now, strategy_event="ENTRY"
        )
        self.assertEqual(kill_entry["status"], "FILLED", kill_entry)
        kill_position = Decimal(kill_ledger.snapshot()["positionBase"])
        kill_at = self.now + 2
        kill_ledger.set_killed(True, kill_at, "MIXED_WRITER_STRESS_KILL_SWITCH")
        blocked_intent = dict(kill_entry_intent)
        blocked_intent.update({
            "intentId": "core-mixed-writer-killed-dca",
            "targetPositionBase": str(kill_position * Decimal("1.05")),
            "decisionAtMs": kill_at,
            "validUntilMs": kill_at + 30_000,
            "inputSnapshotId": "fixture:core-mixed-writer-killed-dca",
        })
        blocked_book = dict(self.book)
        blocked_book["observedAtMs"] = kill_at
        blocked = kill_ledger.submit(
            blocked_intent, blocked_book, kill_at, strategy_event="DCA"
        )
        self.assertEqual(blocked["status"], "REJECTED", blocked)
        self.assertEqual(blocked["reason"], "KILL_SWITCH", blocked)
        kill_snapshot = kill_ledger.snapshot()
        self.assertTrue(kill_snapshot["riskControl"]["killed"])
        self.assertEqual(kill_snapshot["positionBase"], str(kill_position))

        with sqlite3.connect(kill_path) as connection:
            self.assertEqual(connection.execute("PRAGMA integrity_check").fetchone()[0], "ok")
            kill_orders = connection.execute(
                "SELECT order_id,intent_id,status,document FROM paper_orders ORDER BY intent_id"
            ).fetchall()
            self.assertEqual(len(kill_orders), 2, kill_orders)
            orders_by_intent = {row[1]: (row[2], __import__("json").loads(row[3])) for row in kill_orders}
            self.assertEqual(orders_by_intent["core-mixed-writer-kill-entry"][0], "FILLED")
            rejected_status, rejected_document = orders_by_intent["core-mixed-writer-killed-dca"]
            self.assertEqual(rejected_status, "REJECTED")
            self.assertEqual(rejected_document["reason"], "KILL_SWITCH")
            self.assertIsNone(rejected_document["reservationId"])
            self.assertEqual(Decimal(rejected_document["filledBase"]), Decimal("0"))
            kill_reservations = connection.execute(
                "SELECT reservation_id,intent_id,status,reserved_margin_quote,remaining_notional_quote FROM paper_risk_reservations WHERE strategy_id='STRATEGY_CORE' ORDER BY intent_id"
            ).fetchall()
            self.assertEqual(len(kill_reservations), 1, kill_reservations)
            self.assertEqual(kill_reservations[0][1], "core-mixed-writer-kill-entry")
            self.assertEqual(connection.execute(
                "SELECT COUNT(*) FROM paper_account_event_journal WHERE strategy_id='STRATEGY_CORE' AND event_type='FILL'"
            ).fetchone()[0], 1)
            self.assertEqual(connection.execute(
                "SELECT COUNT(*) FROM paper_orders WHERE strategy_id='AI_FREQAI'"
            ).fetchone()[0], 0)

        with sqlite3.connect(stress_path) as connection:
            self.assertEqual(connection.execute("PRAGMA integrity_check").fetchone()[0], "ok")
            orders = connection.execute(
                "SELECT intent_id,status FROM paper_orders WHERE account_id=1 AND strategy_id='STRATEGY_CORE' ORDER BY intent_id"
            ).fetchall()
            fills = connection.execute(
                "SELECT COUNT(*) FROM paper_account_event_journal WHERE account_id=1 AND strategy_id='STRATEGY_CORE' AND event_type='FILL'"
            ).fetchone()[0]
            reservations = connection.execute(
                "SELECT intent_id,reserved_margin_quote,equity_basis_quote FROM paper_risk_reservations WHERE account_id=1 AND strategy_id='STRATEGY_CORE'"
            ).fetchall()
            orphan_reservations = connection.execute(
                """SELECT COUNT(*) FROM paper_risk_reservations r
                   LEFT JOIN paper_orders o ON o.account_id=r.account_id
                    AND o.strategy_id=r.strategy_id AND o.reservation_id=r.reservation_id
                   WHERE r.account_id=1 AND r.strategy_id='STRATEGY_CORE'
                    AND o.reservation_id IS NULL"""
            ).fetchone()[0]
            ai_orders = connection.execute(
                "SELECT COUNT(*) FROM paper_orders WHERE strategy_id='AI_FREQAI'"
            ).fetchone()[0]
        self.assertEqual(len(orders), 2, orders)
        self.assertEqual(fills, 2)
        self.assertEqual(len(reservations), 2)
        self.assertEqual(orphan_reservations, 0)
        self.assertEqual(ai_orders, 0)
        with localcontext() as decimal_context:
            decimal_context.prec = 80
            for _, reserved_margin, equity_basis in reservations:
                self.assertLessEqual(
                    Decimal(reserved_margin), Decimal(equity_basis) * Decimal("0.01")
                )
            account_exposure = abs(Decimal(snapshot["positionBase"])) * Decimal(snapshot["averageEntryPrice"])
            self.assertLessEqual(account_exposure, Decimal("1000"))


    def test_repeated_mixed_writer_rounds_preserve_idempotency_exposure_and_kill_switch(self):
        context = multiprocessing.get_context("spawn")
        aggregate_fills = 0
        aggregate_reservations = 0
        aggregate_orders = 0

        for round_number in range(2):
            stress_path = Path(self.temp.name) / f"core-repeated-mixed-writer-{round_number}.sqlite3"
            with sqlite3.connect(self.path) as source, sqlite3.connect(stress_path) as target_db:
                source.backup(target_db)

            signal = self.decide()
            entry_intent = dict(signal["intent"])
            entry_intent.update({
                "intentId": f"core-repeated-mixed-entry-{round_number}",
                "decisionAtMs": self.now,
                "validUntilMs": self.now + 60_000,
                "inputSnapshotId": f"fixture:core-repeated-mixed-entry-{round_number}",
            })
            ledger = PaperLedger(
                stress_path, max_position_base="1", fee_rate="0.001",
                strategy_id="STRATEGY_CORE", source_sha="e" * 40,
                risk_limits={
                    "maxDrawdownPct": "50",
                    "maxDailyLossUsdt": "50",
                    "maxExposureUsdt": "1000",
                },
                require_risk_limits=True, apply_migrations=False,
            )

            short_acquired = context.Event()
            short_release = context.Event()
            short_holder = context.Process(
                target=_hold_sqlite_write_lock_until_released,
                args=(str(stress_path), short_acquired, short_release),
            )
            short_holder.start()
            self.assertTrue(short_acquired.wait(timeout=20), "short writer failed to acquire lock")
            attempted = __import__("threading").Event()
            outcome = {}

            def submit_entry():
                attempted.set()
                outcome["entry"] = ledger.submit(
                    entry_intent, dict(self.book), self.now, strategy_event="ENTRY"
                )

            worker = __import__("threading").Thread(target=submit_entry)
            worker.start()
            try:
                self.assertTrue(attempted.wait(timeout=5))
                __import__("time").sleep(0.2)
            finally:
                short_release.set()
                short_holder.join(timeout=10)
                if short_holder.is_alive():
                    short_holder.terminate()
                    short_holder.join(timeout=5)
            worker.join(timeout=15)
            self.assertFalse(worker.is_alive(), "short-lock ENTRY did not finish")
            self.assertEqual(short_holder.exitcode, 0)
            self.assertEqual(outcome["entry"]["status"], "FILLED", outcome["entry"])

            position = Decimal(ledger.snapshot()["positionBase"])
            dca_at = self.now + 10 + round_number
            dca_intent = dict(entry_intent)
            dca_intent.update({
                "intentId": f"core-repeated-mixed-dca-{round_number}",
                "targetPositionBase": str(position * Decimal("1.05")),
                "decisionAtMs": dca_at,
                "validUntilMs": dca_at + 60_000,
                "inputSnapshotId": f"fixture:core-repeated-mixed-dca-{round_number}",
            })
            dca_book = dict(self.book)
            dca_book["observedAtMs"] = dca_at
            long_acquired = context.Event()
            long_release = context.Event()
            long_holder = context.Process(
                target=_hold_sqlite_write_lock_until_released,
                args=(str(stress_path), long_acquired, long_release),
            )
            long_holder.start()
            try:
                self.assertTrue(long_acquired.wait(timeout=20), "long writer failed to acquire lock")
                started = __import__("time").monotonic()
                with self.assertRaisesRegex(sqlite3.OperationalError, "locked"):
                    ledger.submit(dca_intent, dca_book, dca_at, strategy_event="DCA")
                elapsed = __import__("time").monotonic() - started
                self.assertGreaterEqual(elapsed, 9.0, f"lock timeout fired too early: {elapsed:.3f}s")
            finally:
                long_release.set()
                long_holder.join(timeout=10)
                if long_holder.is_alive():
                    long_holder.terminate()
                    long_holder.join(timeout=5)
            self.assertEqual(long_holder.exitcode, 0)

            dca_order = ledger.submit(dca_intent, dca_book, dca_at, strategy_event="DCA")
            self.assertEqual(dca_order["status"], "FILLED", dca_order)
            replayed = ledger.submit(dca_intent, dca_book, dca_at, strategy_event="DCA")
            self.assertEqual(replayed["order_id"], dca_order["order_id"])
            self.assertEqual(replayed["status"], "FILLED")

            snapshot = ledger.snapshot()
            exposure = abs(Decimal(snapshot["positionBase"])) * Decimal(snapshot["averageEntryPrice"])
            self.assertLessEqual(exposure, Decimal("1000"))
            with sqlite3.connect(stress_path) as connection:
                self.assertEqual(connection.execute("PRAGMA integrity_check").fetchone()[0], "ok")
                orders = connection.execute(
                    "SELECT intent_id,status FROM paper_orders WHERE strategy_id='STRATEGY_CORE'"
                ).fetchall()
                fills = connection.execute(
                    "SELECT COUNT(*) FROM paper_account_event_journal WHERE strategy_id='STRATEGY_CORE' AND event_type='FILL'"
                ).fetchone()[0]
                reservations = connection.execute(
                    "SELECT intent_id,reserved_margin_quote,equity_basis_quote FROM paper_risk_reservations WHERE strategy_id='STRATEGY_CORE'"
                ).fetchall()
                orphan_count = connection.execute(
                    """SELECT COUNT(*) FROM paper_risk_reservations r
                       LEFT JOIN paper_orders o ON o.account_id=r.account_id
                        AND o.strategy_id=r.strategy_id AND o.reservation_id=r.reservation_id
                       WHERE r.strategy_id='STRATEGY_CORE' AND o.reservation_id IS NULL"""
                ).fetchone()[0]
                ai_orders = connection.execute(
                    "SELECT COUNT(*) FROM paper_orders WHERE strategy_id='AI_FREQAI'"
                ).fetchone()[0]
            self.assertEqual(len(orders), 2, orders)
            self.assertEqual(fills, 2)
            self.assertEqual(len(reservations), 2)
            self.assertEqual(orphan_count, 0)
            self.assertEqual(ai_orders, 0)
            with localcontext() as decimal_context:
                decimal_context.prec = 80
                for _, reserved_margin, equity_basis in reservations:
                    self.assertLessEqual(
                        Decimal(reserved_margin), Decimal(equity_basis) * Decimal("0.01")
                    )
            aggregate_orders += len(orders)
            aggregate_fills += fills
            aggregate_reservations += len(reservations)

        self.assertEqual(aggregate_orders, 4)
        self.assertEqual(aggregate_fills, 4)
        self.assertEqual(aggregate_reservations, 4)

        # Verify the global Kill Switch after all contention/retry rounds using
        # a clean independent fixture so the first DCA reaches the kill gate.
        kill_path = Path(self.temp.name) / "core-repeated-mixed-kill.sqlite3"
        with sqlite3.connect(self.path) as source, sqlite3.connect(kill_path) as target_db:
            source.backup(target_db)
        kill_ledger = PaperLedger(
            kill_path, max_position_base="1", fee_rate="0.001",
            strategy_id="STRATEGY_CORE", source_sha="f" * 40,
            risk_limits={
                "maxDrawdownPct": "50",
                "maxDailyLossUsdt": "50",
                "maxExposureUsdt": "1000",
            },
            require_risk_limits=True, apply_migrations=False,
        )
        kill_entry = dict(self.decide()["intent"])
        kill_entry.update({
            "intentId": "core-repeated-mixed-kill-entry",
            "decisionAtMs": self.now,
            "validUntilMs": self.now + 60_000,
            "inputSnapshotId": "fixture:core-repeated-mixed-kill-entry",
        })
        filled = kill_ledger.submit(kill_entry, dict(self.book), self.now, strategy_event="ENTRY")
        self.assertEqual(filled["status"], "FILLED", filled)
        before = kill_ledger.snapshot()
        kill_at = self.now + 100
        kill_ledger.set_killed(True, kill_at, "REPEATED_MIXED_WRITER_FINAL_KILL")
        blocked_intent = dict(kill_entry)
        blocked_intent.update({
            "intentId": "core-repeated-mixed-killed-dca",
            "targetPositionBase": str(Decimal(before["positionBase"]) * Decimal("1.05")),
            "decisionAtMs": kill_at,
            "validUntilMs": kill_at + 30_000,
            "inputSnapshotId": "fixture:core-repeated-mixed-killed-dca",
        })
        blocked_book = dict(self.book)
        blocked_book["observedAtMs"] = kill_at
        rejected = kill_ledger.submit(
            blocked_intent, blocked_book, kill_at, strategy_event="DCA"
        )
        self.assertEqual(rejected["status"], "REJECTED", rejected)
        self.assertEqual(rejected["reason"], "KILL_SWITCH")
        after = kill_ledger.snapshot()
        self.assertTrue(after["riskControl"]["killed"])
        self.assertEqual(after["positionBase"], before["positionBase"])
        with sqlite3.connect(kill_path) as connection:
            self.assertEqual(connection.execute("PRAGMA integrity_check").fetchone()[0], "ok")
            self.assertEqual(connection.execute(
                "SELECT COUNT(*) FROM paper_account_event_journal WHERE strategy_id='STRATEGY_CORE' AND event_type='FILL'"
            ).fetchone()[0], 1)
            self.assertEqual(connection.execute(
                "SELECT COUNT(*) FROM paper_risk_reservations WHERE strategy_id='STRATEGY_CORE'"
            ).fetchone()[0], 1)
            self.assertEqual(connection.execute(
                "SELECT COUNT(*) FROM paper_orders WHERE strategy_id='AI_FREQAI'"
            ).fetchone()[0], 0)


if __name__ == "__main__":
    unittest.main()
