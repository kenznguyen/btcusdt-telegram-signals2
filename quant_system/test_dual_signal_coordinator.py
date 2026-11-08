"""Contracts for the independent CORE/AI signal coordinator."""

from decimal import Decimal
from pathlib import Path
import tempfile
import unittest

from quant_system.dual_ledger import SharedRiskEngine, StrategyLedger
from quant_system.dual_strategy import Origin, Side, Signal
from market_data.store import Candle, CandleStore, read_window
from quant_system.dual_signal_coordinator import (
    DualStrategySignalCoordinator,
    StrategyIntent,
)


class DualStrategySignalCoordinatorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.db = Path(self.temp.name) / "dual.sqlite3"
        self.core = StrategyLedger(self.db, strategy_id="CORE", initial_equity="10000")
        self.ai = StrategyLedger(self.db, strategy_id="AI", initial_equity="10000")
        self.risk = SharedRiskEngine(self.db)
        self.coordinator = DualStrategySignalCoordinator(
            core_ledger=self.core, ai_ledger=self.ai, risk_engine=self.risk
        )
        self.closed = 1_800_000_000_000
        self.now_ms = self.closed + 5_000
        self.market_db = Path(self.temp.name) / "market.sqlite3"
        CandleStore(self.market_db).insert([
            Candle("15m", self.closed, "100", "102", "99", "101", "3", self.closed + 901_000)
        ])
        self.window = read_window(
            self.market_db, "BTCUSDT", "15m", self.closed, self.closed + 900_000
        )
        self.row = {
            "closed": True, "open_time": self.closed, "open": 100.0,
            "high": 102.0, "low": 99.0, "close": 101.0, "volume": 3.0,
            "rsi": 31.0, "previous_rsi": 29.0, "h1_plus": 26.0,
            "h1_minus": 12.0, "h1_adx": 22.0,
            "h1_source_open_time": self.closed - 3_600_000,
        }
        self.prediction = {
            "schemaVersion": 1, "exchange": "binance", "marketType": "USDT_PERPETUAL",
            "symbol": "BTCUSDT", "timeframe": "15m", "candleOpenTimeMs": self.closed,
            "candleCloseTimeMs": self.closed + 900_000, "availableAtMs": self.now_ms - 2_000,
            "trainedThroughMs": self.closed, "trainingCompletedAtMs": self.closed + 1_000,
            "modelVersion": "model-1", "strategyVersion": "strategy-1",
            "trainingDatasetVersion": "sha256:" + "a" * 64, "predictedReturn": "0.004",
            "doPredict": 1, "datasetVersion": self.window["datasetVersion"],
        }

    def intent(self, origin, side, *, action="ENTRY", position_id=None,
               quantity="0.01", price="1000", reservation_id=None):
        signal = Signal(
            origin=origin, side=side, candle_close_ms=self.closed,
            signal_id=f"{origin.value.lower()}:{self.closed}:{side.value}",
        )
        position_id = position_id or f"{origin.value.lower()}-position"
        return StrategyIntent(
            signal=signal, action=action, position_id=position_id,
            reservation_id=reservation_id or f"reserve:{signal.signal_id}:{action}",
            quantity=quantity, price=price,
            notional_exposure=str(Decimal(quantity) * Decimal(price)),
        )

    def route(self, *intents, **overrides):
        options = {
            "data_fresh": True, "state_reconciled": True, "kill_switch": False,
        }
        options.update(overrides)
        return self.coordinator.route(intents, **options)


    def test_signal_generation_preserves_opposing_core_long_and_ai_short(self):
        candidates = self.coordinator.generate_signals(
            self.row, self.window,
            {**self.prediction, "predictedReturn": "-0.004"}, self.now_ms,
        )
        self.assertEqual(candidates.reason, "SIGNALS_GENERATED")
        self.assertEqual(candidates.core.side, Side.LONG)
        self.assertEqual(candidates.ai.side, Side.SHORT)

    def test_ai_signal_is_generated_when_core_is_silent(self):
        row = {**self.row, "rsi": 40.0, "previous_rsi": 39.0}
        candidates = self.coordinator.generate_signals(
            row, self.window, self.prediction, self.now_ms,
        )
        self.assertIsNone(candidates.core)
        self.assertEqual(candidates.ai.side, Side.LONG)

    def test_valid_core_signal_survives_invalid_ai_prediction(self):
        candidates = self.coordinator.generate_signals(
            self.row, self.window, {**self.prediction, "doPredict": 0}, self.now_ms,
        )
        self.assertEqual(candidates.core.side, Side.LONG)
        self.assertIsNone(candidates.ai)

    def test_opposing_core_and_ai_signals_are_both_admitted_to_separate_ledgers(self):
        result = self.route(
            self.intent(Origin.CORE, Side.LONG),
            self.intent(Origin.AI, Side.SHORT),
        )
        self.assertEqual(len(result.intents), 2)
        self.assertTrue(all(item.accepted for item in result.intents))
        self.assertEqual(
            [(p.side, p.position_id) for p in self.core.snapshot().positions],
            [("LONG", "core-position")],
        )
        self.assertEqual(
            [(p.side, p.position_id) for p in self.ai.snapshot().positions],
            [("SHORT", "ai-position")],
        )
        self.assertEqual(self.core.snapshot().positions[0].margin_used, Decimal("200"))
        self.assertEqual(self.ai.snapshot().positions[0].margin_used, Decimal("200"))

    def test_core_signal_routes_when_ai_has_no_signal(self):
        result = self.route(self.intent(Origin.CORE, Side.LONG))
        self.assertEqual(len(result.intents), 1)
        self.assertTrue(result.intents[0].accepted)
        self.assertEqual(len(self.core.snapshot().positions), 1)
        self.assertEqual(len(self.ai.snapshot().positions), 0)

    def test_ai_signal_routes_when_core_has_no_signal(self):
        result = self.route(self.intent(Origin.AI, Side.SHORT))
        self.assertTrue(result.intents[0].accepted)
        self.assertEqual(len(self.core.snapshot().positions), 0)
        self.assertEqual(len(self.ai.snapshot().positions), 1)

    def test_stale_or_unreconciled_market_state_fails_closed(self):
        for flags, expected in (
            ({"data_fresh": False}, "STALE_DATA"),
            ({"state_reconciled": False}, "UNRECONCILED_STATE"),
            ({"kill_switch": True}, "KILL_SWITCH_ACTIVE"),
        ):
            with self.subTest(flags=flags):
                result = self.route(self.intent(Origin.AI, Side.LONG), **flags)
                self.assertFalse(result.intents[0].accepted)
                self.assertEqual(result.intents[0].reason, expected)
                self.assertEqual(self.ai.snapshot().positions, ())

    def test_dca_is_reserved_and_written_only_to_its_origin_ledger(self):
        opened = self.route(self.intent(Origin.CORE, Side.LONG))
        self.assertTrue(opened.intents[0].accepted)
        dca = self.route(self.intent(
            Origin.CORE, Side.LONG, action="DCA", position_id="core-position",
            reservation_id="core-dca-1",
        ))
        self.assertTrue(dca.intents[0].accepted)
        core_position = self.core.snapshot().positions[0]
        self.assertEqual(core_position.dca_count, 1)
        self.assertEqual(core_position.margin_used, Decimal("400"))
        self.assertEqual(self.ai.snapshot().positions, ())

    def test_dca_side_mismatch_is_rejected_without_reservation(self):
        self.route(self.intent(Origin.CORE, Side.LONG))
        result = self.route(self.intent(
            Origin.CORE, Side.SHORT, action="DCA", position_id="core-position",
            reservation_id="wrong-side-dca",
        ))
        self.assertFalse(result.intents[0].accepted)
        self.assertEqual(result.intents[0].reason, "DCA_SIDE_MISMATCH")
        self.assertEqual(self.core.snapshot().positions[0].dca_count, 0)

    def test_duplicate_reservation_cannot_create_a_second_position(self):
        intent = self.intent(Origin.AI, Side.LONG, reservation_id="stable-id")
        first = self.route(intent)
        second = self.route(intent)
        self.assertTrue(first.intents[0].accepted)
        self.assertFalse(second.intents[0].accepted)
        self.assertEqual(second.intents[0].reason, "DUPLICATE_RESERVATION")
        self.assertEqual(len(self.ai.snapshot().positions), 1)

    def test_kill_switch_blocks_increases_but_allows_position_reduction(self):
        self.route(self.intent(Origin.AI, Side.LONG))
        blocked = self.route(self.intent(Origin.AI, Side.LONG), kill_switch=True)
        self.assertEqual(blocked.intents[0].reason, "KILL_SWITCH_ACTIVE")
        reduction = self.coordinator.reduce(
            strategy_id="AI", position_id="ai-position", quantity="0.005",
            realized_pnl="10", fees="1", kill_switch=True,
        )
        self.assertTrue(reduction.accepted)
        position = self.ai.snapshot().positions[0]
        self.assertEqual(position.quantity, Decimal("0.005"))
        self.assertEqual(position.margin_used, Decimal("100"))
        self.assertEqual(self.ai.snapshot().equity, Decimal("10009"))


if __name__ == "__main__":
    unittest.main()
