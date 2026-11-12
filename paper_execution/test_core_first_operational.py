import os
import sqlite3
import tempfile
from decimal import Decimal
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

    def decide(self, *, m15=None, book=None, adx=30.0):
        with patch.dict(os.environ, {
            "MARKET_DATA_DB": str(self.path),
            "PAPER_MAX_POSITION_BASE": "1",
            "AI_EXECUTION_ENABLED": "false",
        }, clear=False), patch(
            "pipeline.api.market_window", side_effect=[m15 or self.m15, self.h1]
        ), patch(
            "pipeline.core_strategy.indicators", side_effect=self.core_indicators(adx)
        ):
            return core_decide(self.now, book or self.book)

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
            self.assertLessEqual(Decimal(margin), Decimal(basis) * Decimal("0.01"))
            self.assertGreater(Decimal(margin), Decimal(basis) * Decimal("0.0099"))
            self.assertEqual(Decimal(notional), Decimal(margin) * Decimal("13"))
            self.assertEqual(status, "CONSUMED")

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


if __name__ == "__main__":
    unittest.main()
