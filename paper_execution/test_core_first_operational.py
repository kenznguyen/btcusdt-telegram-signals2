import os
import json
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


if __name__ == "__main__":
    unittest.main()
