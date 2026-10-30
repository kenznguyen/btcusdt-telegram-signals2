"""Phase 3: strict, paper-only atomic binding of dual signals to PaperLedger.

One SQLite database owns reservations, attempt markers, paper account state and
orders. Durable attempt markers prevent silent retries after a crash. Binding
and simulated order publication commit in ONE transaction; no exchange API.
"""
from contextlib import closing
from dataclasses import dataclass
from decimal import Decimal, ROUND_DOWN, InvalidOperation, localcontext
import json
from pathlib import Path
import sqlite3

from freqtrade_parity.rules import StrategyRules
from paper_execution.ledger import PaperLedger, book_value, stored_state, intent_value, text
from pipeline.decision import _canonical
from pipeline.values import identity, stamp
from quant_system.dual_strategy import (
    Origin, Side, ReservationLedger, RiskSnapshot, RouteResult,
    _select, admit, ai_signal, core_signal,
)


@dataclass(frozen=True)
class PaperBridgeResult:
    action: str
    reason: str
    intent: dict | None = None
    order: dict | None = None


class DualPaperBridge:
    """Only simulated fills; native Freqtrade entry remains disabled.

    An explicit audited RiskSnapshot and a verified flat PaperLedger are
    required for every submission. Cross-DB submissions are prohibited.
    """

    def __init__(self, reservations: ReservationLedger, paper: PaperLedger,
                 *, initial_capital_usdt="100"):
        if not isinstance(reservations, ReservationLedger) or not isinstance(paper, PaperLedger):
            raise ValueError("Both persistent ledgers are required")
        if reservations.path.resolve() != paper.path.resolve():
            raise ValueError("Dual reservations and paper orders must share one SQLite database")
        self.reservations, self.paper = reservations, paper
        self.path = paper.path.resolve()
        try:
            self.capital = Decimal(str(initial_capital_usdt))
        except (InvalidOperation, TypeError) as error:
            raise ValueError("Invalid initial paper capital") from error
        if not self.capital.is_finite() or not Decimal("0") < self.capital <= Decimal("100000000"):
            raise ValueError("Invalid initial paper capital")
        with closing(sqlite3.connect(self.path, timeout=15)) as db, db:
            db.execute("BEGIN IMMEDIATE")
            db.execute("""CREATE TABLE IF NOT EXISTS dual_paper_config (
                id INTEGER PRIMARY KEY CHECK(id=1), initial_capital TEXT NOT NULL)""")
            saved = db.execute("SELECT initial_capital FROM dual_paper_config WHERE id=1").fetchone()
            if saved is None:
                db.execute("INSERT INTO dual_paper_config VALUES (1,?)", (text(self.capital),))
            elif Decimal(saved[0]) != self.capital:
                raise ValueError("Paper capital cannot change across restarts")
            db.execute("""CREATE TABLE IF NOT EXISTS dual_paper_attempts (
                signal_id TEXT PRIMARY KEY, attempted_at_ms INTEGER NOT NULL,
                FOREIGN KEY(signal_id) REFERENCES paper_reservations(signal_id))""")

    def _connection(self):
        db = sqlite3.connect(self.path, timeout=15, isolation_level=None)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA synchronous=FULL")
        return db

    @staticmethod
    def _reservation(db, signal_id):
        return db.execute("SELECT * FROM paper_reservations WHERE signal_id=?", (signal_id,)).fetchone()

    @staticmethod
    def _pending(db):
        return db.execute(
            "SELECT 1 FROM paper_orders WHERE status IN ('OPEN','PARTIALLY_FILLED') LIMIT 1"
        ).fetchone() is not None

    def _position_gate(self, db, risk, signal):
        admission = admit(signal, risk)
        if not admission.accepted:
            return admission.reason
        position, _average, realized, fees, paused = stored_state(db)
        if paused:
            return "PAPER_PAUSED"
        if position != 0:
            return "PAPER_POSITION_OPEN"
        if self._pending(db):
            return "PAPER_PENDING_ORDER"
        with localcontext() as ctx:
            ctx.prec = 60
            equity = self.capital + realized - fees
            if equity <= 0:
                return "PAPER_EQUITY_EXHAUSTED"
            required = equity * Decimal(str(StrategyRules().p.entry_margin_pct))
            try:
                observed_required = Decimal(str(risk.required_margin))
                available = Decimal(str(risk.available_margin))
            except (InvalidOperation, TypeError):
                return "INVALID_RISK_SNAPSHOT"
            if not observed_required.is_finite() or observed_required != required:
                return "RISK_MARGIN_MISMATCH"
            if not available.is_finite() or available > equity:
                return "RISK_BALANCE_MISMATCH"
        return None

    def execute(self, route: RouteResult, row, canonical_window, prediction,
                risk: RiskSnapshot, book, now_ms):
        """Perform one authorized paper simulation, never a native/exchange order.

        A previous attempt marker, even without an order, blocks any automatic
        retry after an interrupted submission. Operator reconciliation is required.
        """
        if not isinstance(route, RouteResult) or route.action != "PAPER_RESERVED" or route.selected is None:
            return PaperBridgeResult("WAIT", "NOT_RESERVED")
        try:
            now = stamp(now_ms)
            latest = _canonical(canonical_window, now)
            if not isinstance(row, dict) or row.get("closed") is not True or (
                type(row.get("open_time")) is not int or row["open_time"] != latest["openTimeMs"]
            ):
                return PaperBridgeResult("WAIT", "INVALID_CANONICAL_ROW")
            for key in ("open", "high", "low", "close", "volume"):
                left, right = Decimal(str(row[key])), Decimal(latest[key])
                if not left.is_finite() or left != right:
                    return PaperBridgeResult("WAIT", "INVALID_CANONICAL_ROW")
            expected = _select(
                core_signal(row), ai_signal(prediction, canonical_window, latest, now),
                latest["closeTimeMs"],
            )
            if (expected.action != "SELECTED" or expected.selected != route.selected or
                    expected.sources != route.sources):
                return PaperBridgeResult("WAIT", "SIGNAL_REVALIDATION_FAILED")
            if latest["closeTimeMs"] != route.selected.candle_close_ms:
                return PaperBridgeResult("WAIT", "SIGNAL_CANDLE_MISMATCH")
            sides, price_id = None, None
            bids, asks, spread, price_id = book_value(book, now)
            if spread > self.paper.spread:
                return PaperBridgeResult("WAIT", "SPREAD_LIMIT")
            side = route.selected.side
            quote = asks[0][0] if side == Side.LONG else bids[0][0]
            if quote <= 0:
                return PaperBridgeResult("WAIT", "INVALID_BOOK")
            admission = admit(route.selected, risk)
            if not admission.accepted:
                return PaperBridgeResult("WAIT", admission.reason)
        except (ValueError, TypeError, KeyError, OverflowError, InvalidOperation):
            return PaperBridgeResult("WAIT", "INVALID_CANONICAL_ROW_OR_BOOK")

        with closing(self._connection()) as db:
            # Transaction A: irreversibly record an attempt BEFORE any submission.
            # If the process exits after this commit, recovery refuses to retry.
            db.execute("BEGIN IMMEDIATE")
            try:
                reserved = self._reservation(db, route.selected.signal_id)
                if (reserved is None or reserved["status"] != "RESERVED" or
                    reserved["origin"] != route.selected.origin.value or
                    reserved["side"] != route.selected.side.value or
                    reserved["candle_close_ms"] != route.selected.candle_close_ms):
                    db.rollback()
                    return PaperBridgeResult("WAIT", "RESERVATION_NOT_READY")
                if db.execute("SELECT 1 FROM dual_paper_attempts WHERE signal_id=?",
                              (route.selected.signal_id,)).fetchone():
                    db.rollback()
                    return PaperBridgeResult("WAIT", "ALREADY_ATTEMPTED")
                blocked = self._position_gate(db, risk, route.selected)
                if blocked:
                    db.rollback()
                    return PaperBridgeResult("WAIT", blocked)
                if db.execute("SELECT 1 FROM paper_books WHERE book_id=?",
                              (price_id,)).fetchone():
                    db.rollback()
                    return PaperBridgeResult("WAIT", "SNAPSHOT_ALREADY_USED")
                with localcontext() as ctx:
                    ctx.prec = 60
                    position, _average, realized, fees, _paused = stored_state(db)
                    equity = self.capital + realized - fees
                    stake = equity * Decimal(str(StrategyRules().p.entry_margin_pct))
                    leverage = Decimal(str(StrategyRules().p.leverage))
                    amount = (stake * leverage / quote).quantize(Decimal("0.00000001"), rounding=ROUND_DOWN)
                    if amount <= 0 or amount > self.paper.maximum:
                        db.rollback()
                        return PaperBridgeResult("WAIT", "PAPER_POSITION_LIMIT")
                    target = amount if side == Side.LONG else -amount
                if route.selected.origin == Origin.CORE:
                    strategy_version, model_version = "core-rsi-adx-smart-dca-v1", "not-applicable-core"
                else:
                    strategy_version, model_version = prediction["strategyVersion"], prediction["modelVersion"]
                intent = {
                    "intentId": identity("dual-paper:", {
                        "signalId": route.selected.signal_id,
                        "bookId": price_id, "datasetVersion": canonical_window["datasetVersion"],
                        "side": side.value, "target": text(target),
                    }),
                    "symbol": "BTCUSDT", "exchange": "binance", "marketType": "USDT_PERPETUAL",
                    "strategyVersion": strategy_version, "modelVersion": model_version,
                    "datasetVersion": canonical_window["datasetVersion"],
                    "targetPositionBase": text(target), "limitPrice": text(quote),
                    "decisionAtMs": now, "validUntilMs": now + 30_000,
                    "inputSnapshotId": price_id, "mode": "PAPER",
                }
                intent = intent_value(intent)
                db.execute("INSERT INTO dual_paper_attempts VALUES (?,?)",
                           (route.selected.signal_id, now))
                db.commit()
            except Exception:
                db.rollback()
                raise

            # Transaction B: binding and paper order become durable TOGETHER.
            # If an exception/crash interrupts this block, both roll back, but
            # the attempt marker remains so the caller MUST NOT auto-retry.
            db.execute("BEGIN IMMEDIATE")
            try:
                reserved = self._reservation(db, route.selected.signal_id)
                if reserved is None or reserved["status"] != "RESERVED":
                    db.rollback()
                    return PaperBridgeResult("WAIT", "RESERVATION_CHANGED")
                blocked = self._position_gate(db, risk, route.selected)
                if blocked:
                    db.rollback()
                    return PaperBridgeResult("WAIT", blocked)
                db.execute("""UPDATE paper_reservations
                    SET status='BOUND',intent_id=? WHERE signal_id=? AND status='RESERVED'""",
                           (intent["intentId"], route.selected.signal_id))
                # No network calls. This method shares the caller transaction.
                order = self.paper.submit(intent, book, now, connection=db)
                db.commit()
                return PaperBridgeResult(
                    "PAPER_FILLED" if order["status"] == "FILLED" else "PAPER_RECORDED",
                    order["status"], intent, order,
                )
            except Exception:
                db.rollback()
                raise

    def recover(self, signal_id):
        """Read-only cross-ledger recovery. Never implicitly reissue a paper order."""
        with closing(self._connection()) as db:
            db.execute("BEGIN")
            row = self._reservation(db, signal_id)
            if row is None:
                return {"reason": "UNKNOWN_RESERVATION", "order": None}
            attempted = db.execute("SELECT 1 FROM dual_paper_attempts WHERE signal_id=?",
                                   (signal_id,)).fetchone() is not None
            order_row = None
            if row["intent_id"] is not None:
                order_row = db.execute(
                    "SELECT document FROM paper_orders WHERE intent_id=?", (row["intent_id"],)
                ).fetchone()
            order = json.loads(order_row["document"]) if order_row else None
            if row["status"] == "RESERVED":
                reason = "ATTEMPTED_NO_PAPER_ORDER" if attempted else "UNBOUND_NO_PAPER_ORDER"
            elif row["status"] == "BOUND":
                reason = "BOUND_PAPER_ORDER_FOUND" if order is not None else "BOUND_NO_PAPER_ORDER"
            else:
                reason = "RESOLVED"
            return {"reason": reason, "status": row["status"],
                    "attempted": attempted, "order": order, "intent_id": row["intent_id"]}

    def operator_cancel_unfilled(self, signal_id, evidence):
        """Manual-only reconciliation; rejects any filled or active paper order.

        The operator is responsible for independently verifying absence of
        external work before declaring a stranded attempt canceled.
        """
        if not isinstance(evidence, str) or not 1 <= len(evidence.strip()) <= 2000:
            raise ValueError("Nonempty operator reconciliation evidence required")
        with closing(self._connection()) as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                row = self._reservation(db, signal_id)
                if row is None or row["status"] not in ("RESERVED", "BOUND"):
                    raise ValueError("Reservation not cancelable")
                if row["intent_id"]:
                    found = db.execute("SELECT document FROM paper_orders WHERE intent_id=?",
                                       (row["intent_id"],)).fetchone()
                    if found:
                        order = json.loads(found["document"])
                        if order["status"] not in ("REJECTED", "CANCELED") or (
                            Decimal(order["filledBase"]) != 0
                        ):
                            raise ValueError("Paper order still active or has fills")
                    else:
                        raise ValueError("Bound intent without paper order requires forensic review")
                if self._pending(db):
                    raise ValueError("Another paper order is pending")
                db.execute("""UPDATE paper_reservations SET status='CANCELLED', evidence=?
                    WHERE signal_id=? AND status IN ('RESERVED','BOUND')""",
                           (evidence.strip(), signal_id))
                db.commit()
            except Exception:
                db.rollback()
                raise
