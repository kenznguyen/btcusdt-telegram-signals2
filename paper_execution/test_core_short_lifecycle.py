import os
import sqlite3
import unittest
from decimal import Decimal, localcontext
from unittest.mock import patch

from paper_execution.test_core_first_operational import CoreFirstOperationalProofTest
from paper_execution.ledger import PaperLedger, read_account_risk_snapshot


class CoreShortLifecycleTest(unittest.TestCase):
    def test_short_entry_dca_mark_to_market_exit_fees_equity_and_kill_switch(self):
        fixture = CoreFirstOperationalProofTest()
        fixture.setUp()
        try:
            bearish_h1 = [
                {"plus_di": 10.0, "minus_di": 40.0, "adx": 30.0}
                for _ in fixture.h1_rows
            ]
            entry_m15 = [
                {"rsi": 60.0, "adx": 25.0}
                for _ in fixture.m15_rows
            ]
            entry_m15[-2] = {"rsi": 75.0, "adx": 25.0}
            entry_m15[-1] = {"rsi": 65.0, "adx": 30.0}
            entry_signal = fixture.decide(
                indicator_values=(entry_m15, bearish_h1)
            )
            self.assertEqual(entry_signal["action"], "SELL", entry_signal)
            self.assertEqual(entry_signal["reason"], "RSI_ADX_ENTRY", entry_signal)
            self.assertLess(Decimal(entry_signal["intent"]["targetPositionBase"]), 0)

            entry = fixture.core.submit(
                entry_signal["intent"], fixture.book, fixture.now,
                strategy_event="ENTRY",
            )
            self.assertEqual(entry["status"], "FILLED", entry)
            self.assertLess(Decimal(fixture.core.snapshot()["positionBase"]), 0)
            self.assertEqual(fixture.ai.snapshot()["positionBase"], "0")

            # Price rises against the short; bearish RSI/ADX conditions permit
            # the actual Strategy Core Smart DCA path.
            dca_rows = [dict(row) for row in fixture.m15_rows]
            dca_close = fixture.close * 1.03
            dca_rows[-1].update(
                open=str(fixture.close * 1.025),
                high=str(fixture.close * 1.04),
                low=str(fixture.close * 1.02),
                close=str(dca_close),
            )
            dca_window = fixture.window(dca_rows, "15m") if hasattr(fixture, "window") else {
                "timeframe": "15m", "candles": dca_rows,
                "coverage": {"expected": len(dca_rows), "returned": len(dca_rows), "complete": True},
                "datasetVersion": "sha256:" + "f" * 64,
            }
            dca_window["datasetVersion"] = "sha256:" + "f" * 64
            dca_book = {
                "source": "hummingbot", "connector": "binance_perpetual",
                "symbol": "BTCUSDT", "observedAtMs": fixture.now,
                "bids": [{"price": str(dca_close - 0.01), "quantity": "1"}],
                "asks": [{"price": str(dca_close + 0.01), "quantity": "1"}],
            }
            dca_m15 = [{"rsi": 60.0, "adx": 50.0} for _ in fixture.m15_rows]
            dca_m15[-2] = {"rsi": 65.0, "adx": 50.0}
            dca_m15[-1] = {"rsi": 60.0, "adx": 50.0}
            dca_signal = fixture.decide(
                m15=dca_window, book=dca_book, indicator_values=(dca_m15, bearish_h1)
            )
            self.assertEqual(dca_signal["action"], "SELL", dca_signal)
            self.assertEqual(dca_signal["reason"], "DCA", dca_signal)
            self.assertLess(
                Decimal(dca_signal["intent"]["targetPositionBase"]),
                Decimal(fixture.core.snapshot()["positionBase"]),
            )
            dca = fixture.core.submit(
                dca_signal["intent"], dca_book, fixture.now, strategy_event="DCA"
            )
            self.assertEqual(dca["status"], "FILLED", dca)
            self.assertTrue(fixture.core.strategy_state()["dcaUsed"])

            with sqlite3.connect(fixture.path) as connection:
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
                    self.assertEqual(Decimal(notional), Decimal(margin) * Decimal("1"))
                self.assertEqual(status, "CONSUMED")

            # Mark below weighted short entry to reconcile positive unrealized PnL.
            average = Decimal(fixture.core.snapshot()["averageEntryPrice"])
            mark_price = (average * Decimal("0.95")).quantize(Decimal("0.000000000001"))
            account_ledger = PaperLedger(
                fixture.path, max_position_base="1", fee_rate="0.001",
                source_sha="c" * 40,
            )
            account_ledger.record_account_mark(
                str(mark_price), fixture.now - 60_000, fixture.now,
                "sha256:" + "9" * 64, "100",
            )
            risk_before_exit = read_account_risk_snapshot(fixture.path, now_ms=fixture.now)
            self.assertTrue(risk_before_exit["riskReady"], risk_before_exit)
            self.assertGreater(
                Decimal(risk_before_exit["positions"]["STRATEGY_CORE"]["unrealizedPnlQuote"]),
                Decimal("0"),
            )
            self.assertGreater(Decimal(risk_before_exit["accountEquityQuote"]), Decimal("100"))

            # RSI reaches the short take-profit threshold while the short ROE
            # is positive; Core must emit CLOSE and the ledger must flatten.
            exit_rows = [dict(row) for row in fixture.m15_rows]
            exit_rows[-1].update(
                open=str(mark_price * Decimal("1.001")),
                high=str(mark_price * Decimal("1.002")),
                low=str(mark_price * Decimal("0.999")),
                close=str(mark_price),
            )
            exit_window = {
                "timeframe": "15m", "candles": exit_rows,
                "coverage": {"expected": len(exit_rows), "returned": len(exit_rows), "complete": True},
                "datasetVersion": "sha256:" + "8" * 64,
            }
            exit_m15 = [{"rsi": 30.0, "adx": 25.0} for _ in fixture.m15_rows]
            exit_m15[-2] = {"rsi": 25.0, "adx": 25.0}
            exit_m15[-1] = {"rsi": 20.0, "adx": 25.0}
            exit_book = {
                "source": "hummingbot", "connector": "binance_perpetual",
                "symbol": "BTCUSDT", "observedAtMs": fixture.now,
                "bids": [{"price": str(mark_price - Decimal("0.01")), "quantity": "1"}],
                "asks": [{"price": str(mark_price), "quantity": "1"}],
            }
            exit_signal = fixture.decide(
                m15=exit_window, book=exit_book,
                indicator_values=(exit_m15, bearish_h1),
            )
            self.assertEqual(exit_signal["action"], "CLOSE", exit_signal)
            self.assertEqual(exit_signal["reason"], "TAKE_PROFIT", exit_signal)
            self.assertEqual(exit_signal["intent"]["targetPositionBase"], "0")
            exit_order = fixture.core.submit(
                exit_signal["intent"], exit_book, fixture.now, strategy_event="EXIT"
            )
            self.assertEqual(exit_order["status"], "FILLED", exit_order)
            self.assertEqual(fixture.core.snapshot()["positionBase"], "0")
            self.assertEqual(fixture.core.snapshot()["averageEntryPrice"], "0")
            self.assertFalse(fixture.core.strategy_state()["dcaUsed"])

            risk_after_exit = read_account_risk_snapshot(fixture.path, now_ms=fixture.now)
            self.assertTrue(risk_after_exit["riskReady"], risk_after_exit)
            self.assertEqual(
                risk_after_exit["positions"]["STRATEGY_CORE"]["unrealizedPnlQuote"], "0"
            )
            with sqlite3.connect(fixture.path) as connection:
                realized_raw, fees_raw, funding_raw = connection.execute(
                    """SELECT realized_pnl_quote,fees_quote,funding_quote
                       FROM paper_strategy_ledgers
                       WHERE account_id=1 AND strategy_id='STRATEGY_CORE'"""
                ).fetchone()
            realized, fees, funding = map(
                Decimal, (realized_raw, fees_raw, funding_raw)
            )
            with localcontext() as context:
                context.prec = 80
                expected_fees = sum(
                    (Decimal(order["feeQuote"]) for order in (entry, dca, exit_order)),
                    Decimal("0"),
                )
                expected_equity = Decimal("100") + realized - fees - funding
                self.assertEqual(fees, expected_fees)
                self.assertEqual(Decimal(risk_after_exit["accountEquityQuote"]), expected_equity)
            self.assertGreater(realized, Decimal("0"))
            self.assertEqual(funding, Decimal("0"))

            kill_at = fixture.now + 1
            fixture.core.set_killed(True, kill_at, "CORE_SHORT_EXIT_LIFECYCLE_COMPLETE")
            next_entry = dict(entry_signal["intent"])
            next_entry.update({
                "intentId": "core-short-entry-after-exit-kill",
                "decisionAtMs": kill_at + 1,
                "validUntilMs": kill_at + 30_001,
                "inputSnapshotId": "fixture:short-entry-after-exit-kill",
            })
            next_book = {
                "source": "hummingbot", "connector": "binance_perpetual",
                "symbol": "BTCUSDT", "observedAtMs": kill_at + 1,
                "bids": [{"price": str(mark_price - Decimal("0.01")), "quantity": "1"}],
                "asks": [{"price": str(mark_price), "quantity": "1"}],
            }
            blocked = fixture.core.submit(
                next_entry, next_book, kill_at + 1, strategy_event="ENTRY"
            )
            self.assertEqual(blocked["status"], "REJECTED", blocked)
            self.assertEqual(blocked["reason"], "KILL_SWITCH")
            self.assertEqual(fixture.core.snapshot()["positionBase"], "0")
            self.assertEqual(fixture.ai.snapshot()["positionBase"], "0")
        finally:
            fixture.doCleanups()


if __name__ == "__main__":
    unittest.main()
