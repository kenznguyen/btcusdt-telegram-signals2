"""Dual-Strategy Phase 2: real-core predicates, FreqAI provenance, shared ledger."""
from dataclasses import replace
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import tempfile
import unittest

from market_data.store import Candle, CandleStore, read_window
from freqtrade_parity.rules import StrategyParameters, StrategyRules
from quant_system.dual_strategy import (
    Origin, Side, Signal, RiskSnapshot, PaperSignalCoordinator, ReservationLedger,
    admit, core_signal, ai_signal,
)


class DualStrategyPhase2Test(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.path = Path(temp.name)
        self.ledger = ReservationLedger(self.path / "reservations.sqlite3")
        self.opened = 1_800_000_000_000
        self.now = self.opened + 900_000 + 5_000
        data = self.path / "ohlcv.sqlite3"
        CandleStore(data).insert([Candle("15m", self.opened, "100", "102", "99", "101", "3",
                                         self.opened + 901_000)])
        self.window = read_window(data, "BTCUSDT", "15m", self.opened, self.opened + 900_000)
        self.row = {
            "closed": True, "open_time": self.opened, "open": 100.0,
            "high": 102.0, "low": 99.0, "close": 101.0, "volume": 3.0,
            "rsi": 31.0, "previous_rsi": 29.0, "h1_plus": 26.0,
            "h1_minus": 12.0, "h1_adx": 22.0,
            "h1_source_open_time": self.opened - 3_600_000,
        }
        self.prediction = {
            "schemaVersion": 1, "exchange": "binance", "marketType": "USDT_PERPETUAL",
            "symbol": "BTCUSDT", "timeframe": "15m", "candleOpenTimeMs": self.opened,
            "candleCloseTimeMs": self.opened + 900_000, "availableAtMs": self.now - 2_000,
            "trainedThroughMs": self.opened, "trainingCompletedAtMs": self.opened + 1_000,
            "modelVersion": "model-1", "strategyVersion": "strategy-1",
            "trainingDatasetVersion": "sha256:" + "a" * 64, "predictedReturn": "0.004",
            "doPredict": 1, "datasetVersion": self.window["datasetVersion"],
        }
        self.safe = RiskSnapshot(
            data_fresh=True, state_reconciled=True, has_unresolved_reservation=False,
            active_positions=0, max_positions=1, available_margin=100.0,
            required_margin=50.0, ai_model_validated=True,
        )
        self.coordinator = PaperSignalCoordinator()

    def decide(self, *, row=None, prediction="default", risk=None, ledger=None, window=None):
        if prediction == "default":
            prediction = self.prediction
        return self.coordinator.evaluate(
            self.row if row is None else row,
            self.window if window is None else window,
            prediction, self.now, self.safe if risk is None else risk,
            self.ledger if ledger is None else ledger,
        )

    def test_core_entry_uses_existing_kotlin_derived_parameters(self):
        p = StrategyParameters()
        self.assertEqual((p.leverage, p.dca_roe, p.dca_adx, p.tp_roe,
                          p.soft_sl_roe, p.emergency_sl_roe, p.dca_margin_ratio),
                         (13.0, -20.0, 45.0, 5.0, -35.0, -90.0, 1.0))
        result = core_signal(self.row, StrategyRules())
        self.assertEqual((result.origin, result.side), (Origin.CORE, Side.LONG))

    def test_core_only_without_ai_is_reserved_for_paper_binding(self):
        result = self.decide(prediction=None)
        self.assertEqual((result.action, result.reason), ("PAPER_RESERVED", "RESERVED_FOR_PAPER_BINDING"))
        self.assertEqual(result.selected.origin, Origin.CORE)
        self.assertIsNone(result.ai)

    def test_ai_long_without_core_signal(self):
        row = {**self.row, "rsi": 40.0, "previous_rsi": 39.0}
        result = self.decide(row=row)
        self.assertEqual(result.action, "PAPER_RESERVED")
        self.assertEqual((result.selected.origin, result.selected.side), (Origin.AI, Side.LONG))
        self.assertIsNone(result.core)

    def test_ai_short_without_core_signal(self):
        row = {**self.row, "rsi": 40.0, "previous_rsi": 39.0}
        result = self.decide(row=row, prediction={**self.prediction, "predictedReturn": "-0.004"})
        self.assertEqual(result.action, "PAPER_RESERVED")
        self.assertEqual((result.selected.origin, result.selected.side), (Origin.AI, Side.SHORT))

    def test_opposing_signals_are_blocked_without_reservation(self):
        result = self.decide(prediction={**self.prediction, "predictedReturn": "-0.004"})
        self.assertEqual((result.action, result.reason), ("WAIT", "SOURCE_CONFLICT"))
        self.assertEqual(self.ledger.entries(), [])

    def test_same_direction_issues_only_one_reservation_core_preferred(self):
        result = self.decide()
        self.assertEqual(result.action, "PAPER_RESERVED")
        self.assertEqual(result.selected.origin, Origin.CORE)
        self.assertEqual(result.sources, ("CORE", "AI"))
        self.assertEqual(len(self.ledger.entries()), 1)

    def test_model_flag_and_provenance_rejection_does_not_block_valid_core(self):
        for mutation in ({"doPredict": 0}, {"trainedThroughMs": self.opened + 1},
                         {"datasetVersion": "sha256:" + "0" * 64},
                         {"availableAtMs": self.now - 31_000},
                         {"predictedReturn": "NaN"}):
            with self.subTest(mutation=mutation):
                ledger = ReservationLedger(self.path / ("a" + str(len(str(mutation))) + str(abs(hash(str(mutation)))) + ".sqlite3"))
                result = self.decide(ledger=ledger, prediction={**self.prediction, **mutation})
                self.assertEqual(result.action, "PAPER_RESERVED")
                self.assertIsNone(result.ai)

    def test_invalid_ai_cannot_trade_when_core_is_silent(self):
        row = {**self.row, "rsi": 40.0, "previous_rsi": 39.0}
        for p in (None, {**self.prediction, "doPredict": 0},
                  {**self.prediction, "predictedReturn": "0.001"}):
            with self.subTest(p=p):
                result = self.decide(row=row, prediction=p)
                self.assertEqual((result.action, result.reason), ("WAIT", "NO_SIGNAL"))

    def test_unvalidated_ai_and_common_risk_refusals(self):
        row = {**self.row, "rsi": 40.0, "previous_rsi": 39.0}
        for risk, reason in (
            (replace(self.safe, ai_model_validated=False), "AI_NOT_VALIDATED"),
            (replace(self.safe, active_positions=1), "POSITION_LIMIT"),
            (replace(self.safe, available_margin=0), "INSUFFICIENT_MARGIN"),
            (replace(self.safe, data_fresh=False), "STALE_DATA"),
            (replace(self.safe, has_unresolved_reservation=True), "UNRECONCILED_STATE"),
        ):
            with self.subTest(reason=reason):
                result = self.decide(row=row, risk=risk)
                self.assertEqual((result.action, result.reason), ("WAIT", reason))
                self.assertEqual(self.ledger.entries(), [])

    def test_wrong_market_row_and_unclosed_candle_are_blocked(self):
        self.assertEqual(self.decide(row={**self.row, "closed": False}).reason, "UNVERIFIED_CANDLE")
        self.assertEqual(self.decide(row={**self.row, "close": 101.25}).reason, "CANONICAL_ROW_MISMATCH")
        self.assertEqual(self.decide(window={**self.window, "datasetVersion": "sha256:"+"0"*64}).reason,
                         "INVALID_CANONICAL_WINDOW")

    def test_h1_current_or_future_hour_is_not_read(self):
        row = {**self.row, "h1_source_open_time": self.opened}
        self.assertIsNone(core_signal(row))
        # AI stays independent of H1 when canonical M15 data is validated.
        result = self.decide(row=row)
        self.assertEqual(result.selected.origin, Origin.AI)

    def test_duplicate_on_restart_never_reissues_paper_reservation(self):
        first = self.decide()
        again = self.decide(ledger=ReservationLedger(self.ledger.path))
        self.assertEqual(first.action, "PAPER_RESERVED")
        self.assertEqual((again.action, again.reason), ("WAIT", "DUPLICATE_CANDLE"))

    def test_crash_after_reservation_before_binding_stays_unresolved(self):
        first = self.decide()
        recovered = ReservationLedger(self.ledger.path)
        self.assertEqual(recovered.entries()[0]["status"], "RESERVED")
        second = self.decide(ledger=recovered)
        self.assertEqual(second.reason, "DUPLICATE_CANDLE")
        # No auto-binding or auto retry is permitted.
        self.assertIsNone(recovered.entries()[0]["intent_id"])
        self.assertEqual(first.selected.signal_id, recovered.entries()[0]["signal_id"])

    def test_pending_reservation_blocks_other_candles_until_manual_resolution(self):
        first = self.decide(prediction=None)
        second = Signal(Origin.CORE, Side.SHORT, self.opened + 2*900_000, "different-candle")
        self.assertEqual(self.ledger.reserve(second, self.safe).reason, "PENDING_RESERVATION")
        self.ledger.bind(first.selected.signal_id, "paper-intent-1")
        self.assertEqual(self.ledger.entries()[0]["status"], "BOUND")
        self.assertEqual(self.ledger.reserve(second, self.safe).reason, "PENDING_RESERVATION")
        self.ledger.resolve(first.selected.signal_id, "CLOSED", "manual-paper-reconciliation")
        self.assertEqual(self.ledger.reserve(second, self.safe).reason, "RESERVED_FOR_PAPER_BINDING")
        self.assertEqual(self.decide(prediction=None).reason, "DUPLICATE_CANDLE")

    def test_bind_requires_existing_reservation_and_stable_intent_id(self):
        first = self.decide(prediction=None)
        self.ledger.bind(first.selected.signal_id, "paper-intent-1")
        self.ledger.bind(first.selected.signal_id, "paper-intent-1")
        with self.assertRaises(ValueError):
            self.ledger.bind(first.selected.signal_id, "paper-intent-2")
        with self.assertRaises(ValueError):
            self.ledger.resolve(first.selected.signal_id, "CLOSED", "")

    def test_concurrent_reservations_issue_at_most_one(self):
        a = Signal(Origin.CORE, Side.LONG, self.opened + 900_000, "core-concurrent")
        b = Signal(Origin.AI, Side.LONG, self.opened + 900_000, "ai-concurrent")
        with ThreadPoolExecutor(max_workers=2) as pool:
            outcomes = list(pool.map(lambda s: ReservationLedger(self.ledger.path).reserve(s, self.safe), (a, b)))
        self.assertEqual(sum(x.accepted for x in outcomes), 1)
        self.assertEqual(len(self.ledger.entries()), 1)

    def test_emergency_dca_rules_are_not_mutated(self):
        r = StrategyRules()
        self.assertTrue(r.dca("LONG", -21, 46, 23, 22))
        self.assertFalse(r.dca("LONG", -21, 45, 23, 22))
        self.assertEqual(r.exit_priority(True, True, True), "EMERGENCY SL")


if __name__ == "__main__":
    unittest.main()
