"""Phase 3 cross-ledger tests. Intentionally written before the implementation."""
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from market_data.store import Candle, CandleStore, read_window
from paper_execution.ledger import PaperLedger
from quant_system.dual_strategy import (
    Origin, Side, RiskSnapshot, ReservationLedger, PaperSignalCoordinator,
)
from quant_system.paper_bridge import DualPaperBridge


class Phase3PaperBridgeTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.dir = Path(self.temp.name)
        self.shared_path = self.dir / "shared-paper.sqlite3"
        self.paper = PaperLedger(self.shared_path, max_position_base="10")
        self.reservations = ReservationLedger(self.shared_path)
        self.bridge = DualPaperBridge(self.reservations, self.paper, initial_capital_usdt="100")
        self.open = 1_800_000_000_000
        self.now = self.open + 900_000 + 5000
        market_path = self.dir / "candles.sqlite3"
        CandleStore(market_path).insert([
            Candle("15m", self.open, "100", "102", "99", "101", "3", self.open + 900_500)
        ])
        self.window = read_window(market_path, "BTCUSDT", "15m", self.open, self.open + 900_000)
        self.row = {
            "closed": True, "open_time": self.open,
            "open": 100.0, "high": 102.0, "low": 99.0, "close": 101.0, "volume": 3.0,
            "rsi": 31., "previous_rsi": 29., "h1_plus": 26., "h1_minus": 12.,
            "h1_adx": 22., "h1_source_open_time": self.open - 3_600_000,
        }
        self.prediction = {
            "schemaVersion": 1, "exchange": "binance", "marketType": "USDT_PERPETUAL",
            "symbol": "BTCUSDT", "timeframe": "15m", "candleOpenTimeMs": self.open,
            "candleCloseTimeMs": self.open + 900_000, "availableAtMs": self.now - 2000,
            "trainedThroughMs": self.open, "trainingCompletedAtMs": self.open + 1000,
            "modelVersion": "model-v1", "strategyVersion": "strategy-v1",
            "trainingDatasetVersion": "sha256:" + "a" * 64, "predictedReturn": "0.004",
            "doPredict": 1, "datasetVersion": self.window["datasetVersion"],
        }
        self.book = {
            "source": "hummingbot", "connector": "binance_perpetual", "symbol": "BTCUSDT",
            "observedAtMs": self.now,
            "bids": [{"price": "100", "quantity": "10"}],
            "asks": [{"price": "100.1", "quantity": "10"}],
        }
        self.risk = RiskSnapshot(
            data_fresh=True, state_reconciled=True, has_unresolved_reservation=False,
            active_positions=0, max_positions=1, available_margin=100.,
            required_margin=50., ai_model_validated=True,
        )

    def reserve(self, row=None, prediction=None):
        return PaperSignalCoordinator().evaluate(
            row if row is not None else self.row,
            self.window, prediction, self.now, self.risk, self.reservations,
        )

    def submit(self, selected, row=None, prediction=None, risk=None, book=None):
        return self.bridge.execute(
            selected, row if row is not None else self.row,
            self.window, prediction, self.risk if risk is None else risk,
            self.book if book is None else book, self.now,
        )

    def test_core_reservation_submits_real_paper_ledger_intent_once(self):
        selected = self.reserve()
        self.assertEqual(selected.action, "PAPER_RESERVED")
        first = self.submit(selected)
        self.assertEqual(first.action, "PAPER_FILLED")
        self.assertEqual(first.order["status"], "FILLED")
        self.assertEqual(first.intent["mode"], "PAPER")
        self.assertEqual(first.intent["modelVersion"], "not-applicable-core")
        self.assertEqual(first.intent["strategyVersion"], "core-rsi-adx-smart-dca-v1")
        self.assertGreater(float(self.paper.snapshot()["positionBase"]), 0)
        self.assertEqual(self.reservations.entries()[0]["intent_id"], first.intent["intentId"])
        self.assertEqual(self.reservations.entries()[0]["status"], "BOUND")
        self.assertEqual(len(self.paper.snapshot()["orders"]), 1)
        duplicate = self.submit(selected)
        self.assertEqual((duplicate.action, duplicate.reason), ("WAIT", "RESERVATION_NOT_READY"))
        self.assertEqual(len(self.paper.snapshot()["orders"]), 1)

    def test_ai_short_can_fill_without_core_and_keeps_model_provenance(self):
        row = {**self.row, "previous_rsi": 39., "rsi": 40.}
        pred = {**self.prediction, "predictedReturn": "-0.004"}
        selected = self.reserve(row, pred)
        self.assertEqual((selected.selected.origin, selected.selected.side), (Origin.AI, Side.SHORT))
        result = self.submit(selected, row, pred)
        self.assertEqual(result.action, "PAPER_FILLED")
        self.assertLess(float(self.paper.snapshot()["positionBase"]), 0)
        self.assertEqual(result.intent["modelVersion"], "model-v1")
        self.assertEqual(result.intent["strategyVersion"], "strategy-v1")

    def test_ai_cannot_submit_with_changed_or_missing_model_artifact(self):
        row = {**self.row, "previous_rsi": 39., "rsi": 40.}
        selected = self.reserve(row, self.prediction)
        for artifact in (None, {**self.prediction, "doPredict": 0},
                         {**self.prediction, "modelVersion": "other-model"},
                         {**self.prediction, "predictedReturn": "-0.004"}):
            with self.subTest(artifact=artifact):
                result = self.submit(selected, row, artifact)
                self.assertEqual((result.action, result.reason), ("WAIT", "SIGNAL_REVALIDATION_FAILED"))
        self.assertEqual(self.reservations.entries()[0]["status"], "RESERVED")
        self.assertEqual(len(self.paper.snapshot()["orders"]), 0)

    def test_opposite_core_ai_and_unsafe_risk_never_submit(self):
        opposite = self.reserve(prediction={**self.prediction, "predictedReturn": "-0.004"})
        self.assertEqual(opposite.reason, "SOURCE_CONFLICT")
        self.assertEqual(self.submit(opposite).action, "WAIT")
        self.assertEqual(len(self.paper.snapshot()["orders"]), 0)
        valid = self.reserve()
        from dataclasses import replace
        for risk in (
            replace(self.risk, available_margin=1000.),
            replace(self.risk, required_margin=1.),
            replace(self.risk, data_fresh=False),
        ):
            with self.subTest(risk=risk):
                self.assertEqual(self.submit(valid, risk=risk).action, "WAIT")
        self.assertEqual(self.reservations.entries()[0]["status"], "RESERVED")
        self.assertEqual(len(self.paper.snapshot()["orders"]), 0)

    def test_crash_after_prebind_before_submit_never_retries(self):
        selected = self.reserve()
        self.paper.submit = Mock(side_effect=RuntimeError("simulated crash after prebind"))
        with self.assertRaises(RuntimeError):
            self.submit(selected)
        self.assertEqual(self.reservations.entries()[0]["status"], "BOUND")
        self.assertEqual(self.bridge.recover(selected.selected.signal_id)["reason"], "BOUND_NO_PAPER_ORDER")
        restarted = DualPaperBridge(
            ReservationLedger(self.shared_path),
            PaperLedger(self.shared_path, max_position_base="10"),
            initial_capital_usdt="100",
        )
        refused = restarted.execute(selected, self.row, self.window, None, self.risk, self.book, self.now)
        self.assertEqual((refused.action, refused.reason), ("WAIT", "RESERVATION_NOT_READY"))
        self.assertEqual(len(restarted.paper.snapshot()["orders"]), 0)

    def test_recovery_filled_order_does_not_claim_trade_closed(self):
        selected = self.reserve()
        result = self.submit(selected)
        recovery = self.bridge.recover(selected.selected.signal_id)
        self.assertEqual(recovery["reason"], "BOUND_PAPER_ORDER_FOUND")
        self.assertEqual(recovery["order"]["status"], "FILLED")
        with self.assertRaises(ValueError):
            self.bridge.operator_cancel_unfilled(selected.selected.signal_id, "manual review")
        self.assertEqual(self.reservations.entries()[0]["status"], "BOUND")
        self.assertEqual(result.order["status"], "FILLED")

    def test_operator_can_cancel_unbound_reservation_only_with_evidence(self):
        selected = self.reserve()
        with self.assertRaises(ValueError):
            self.bridge.operator_cancel_unfilled(selected.selected.signal_id, "")
        self.bridge.operator_cancel_unfilled(selected.selected.signal_id, "Verified no paper submission")
        self.assertEqual(self.reservations.entries()[0]["status"], "CANCELLED")
        self.assertEqual(self.submit(selected).action, "WAIT")
        self.assertEqual(len(self.paper.snapshot()["orders"]), 0)

    def test_paper_position_or_pause_and_external_pending_block_prebind(self):
        selected = self.reserve()
        self.paper.set_paused(True, self.now)
        self.assertEqual(self.submit(selected).reason, "PAPER_PAUSED")
        self.paper.set_paused(False, self.now)
        with sqlite3.connect(self.shared_path) as db:
            db.execute("UPDATE paper_state SET position='0.1',average='100' WHERE id=1")
        self.assertEqual(self.submit(selected).reason, "PAPER_POSITION_OPEN")
        self.assertEqual(self.reservations.entries()[0]["status"], "RESERVED")
        self.assertEqual(len(self.paper.snapshot()["orders"]), 0)

    def test_separate_databases_not_allowed_for_reservation_and_paper(self):
        other = PaperLedger(self.dir / "other.sqlite3")
        with self.assertRaises(ValueError):
            DualPaperBridge(self.reservations, other, initial_capital_usdt="100")

    def test_tampered_candle_or_changed_book_refused_without_binding(self):
        selected = self.reserve()
        self.assertEqual(self.submit(selected, row={**self.row, "close": 101.5}).reason, "INVALID_CANONICAL_ROW")
        stale = {**self.book, "observedAtMs": self.now - 31_000}
        self.assertEqual(self.submit(selected, book=stale).reason, "INVALID_BOOK")
        self.assertEqual(self.reservations.entries()[0]["status"], "RESERVED")

    def test_no_remote_exchange_submission_path(self):
        source = (Path(__file__).resolve().parent / "paper_bridge.py").read_text()
        self.assertNotIn("ccxt.", source)
        self.assertNotIn("create_order(", source)
        self.assertIn("paper.submit(", source)


if __name__ == "__main__":
    unittest.main()
