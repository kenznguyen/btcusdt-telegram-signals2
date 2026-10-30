"""BTCUSDT Dual-Strategy Phase 2: paper-only signal routing and reservation.

The CORE source calls the existing Kotlin-derived StrategyRules unchanged.
The AI source consumes *validated real FreqAI artifacts*, not synthetic indicators.
No exchange orders or Freqtrade native entry flags are emitted by this module.
"""
from contextlib import closing
from dataclasses import dataclass, replace
from decimal import Decimal, InvalidOperation
from enum import Enum
import hashlib
import json
import math
from pathlib import Path
import sqlite3
import time
from typing import Optional

from freqtrade_parity.rules import StrategyRules

CANDLE_MS = 900_000
HOUR_MS = 3_600_000
SYMBOL = "BTCUSDT"


class Side(str, Enum):
    LONG = "LONG"
    SHORT = "SHORT"


class Origin(str, Enum):
    CORE = "CORE"
    AI = "AI"


@dataclass(frozen=True)
class Signal:
    origin: Origin
    side: Side
    candle_close_ms: int
    signal_id: str
    confidence: Optional[float] = None  # None means not calibrated; never infer from predictedReturn.


@dataclass(frozen=True)
class RiskSnapshot:
    data_fresh: bool
    state_reconciled: bool
    has_unresolved_reservation: bool
    active_positions: int
    max_positions: int
    available_margin: float
    required_margin: float
    ai_model_validated: bool = False


@dataclass(frozen=True)
class Decision:
    accepted: bool
    reason: str
    signal: Optional[Signal] = None


@dataclass(frozen=True)
class RouteResult:
    action: str
    reason: str
    selected: Optional[Signal] = None
    core: Optional[Signal] = None
    ai: Optional[Signal] = None
    sources: tuple = ()


def _number(value):
    if isinstance(value, bool):
        raise ValueError("booleans are not numeric market data")
    numeric = float(value)
    if not math.isfinite(numeric):
        raise ValueError("non-finite market data")
    return numeric


def admit(signal, risk):
    """Risk admission is required even when a caller bypasses the coordinator."""
    if not isinstance(signal, Signal) or type(signal.candle_close_ms) is not int or (
        signal.candle_close_ms <= 0 or signal.candle_close_ms > (2**63 - 1) or
        signal.candle_close_ms % CANDLE_MS != 0
    ) or not isinstance(signal.signal_id, str) or not 1 <= len(signal.signal_id) <= 256 or (
        not isinstance(signal.origin, Origin) or not isinstance(signal.side, Side)
    ):
        return Decision(False, "INVALID_SIGNAL")
    if not isinstance(risk, RiskSnapshot) or not all(type(getattr(risk, field)) is bool for field in (
        "data_fresh", "state_reconciled", "has_unresolved_reservation", "ai_model_validated"
    )):
        return Decision(False, "INVALID_RISK_SNAPSHOT")
    if not risk.data_fresh:
        return Decision(False, "STALE_DATA")
    if not risk.state_reconciled or risk.has_unresolved_reservation:
        return Decision(False, "UNRECONCILED_STATE")
    if type(risk.active_positions) is not int or type(risk.max_positions) is not int or (
        risk.max_positions <= 0 or risk.active_positions < 0
    ):
        return Decision(False, "INVALID_RISK_SNAPSHOT")
    try:
        available, required = _number(risk.available_margin), _number(risk.required_margin)
    except (TypeError, ValueError, OverflowError):
        return Decision(False, "INVALID_RISK_SNAPSHOT")
    if required <= 0 or available < 0:
        return Decision(False, "INVALID_RISK_SNAPSHOT")
    if risk.active_positions >= risk.max_positions:
        return Decision(False, "POSITION_LIMIT")
    if available < required:
        return Decision(False, "INSUFFICIENT_MARGIN")
    if signal.origin == Origin.AI:
        if not risk.ai_model_validated:
            return Decision(False, "AI_NOT_VALIDATED")
        if signal.confidence is not None:
            try:
                score = _number(signal.confidence)
            except (TypeError, ValueError, OverflowError):
                return Decision(False, "INVALID_AI_CONFIDENCE")
            if not 0 <= score <= 1:
                return Decision(False, "INVALID_AI_CONFIDENCE")
    return Decision(True, "RISK_ADMITTED", signal)


def admit_adjustment(signal, risk, *, position_side, dca_count):
    """Shared-risk gate for ONE DCA on an already verified single position.

    Reuse admit() for every data, provenance, margin and consistency gate.
    The position slot is temporarily available *only after* confirming the
    one existing position is the same direction and has no prior DCA.
    This does NOT alter default admit() behavior or the CORE DCA thresholds.
    """
    if (not isinstance(signal, Signal) or not isinstance(risk, RiskSnapshot)
        or type(risk.active_positions) is not int
        or type(risk.max_positions) is not int
        or risk.active_positions != 1 or risk.max_positions != 1):
        return Decision(False, "INVALID_ADJUSTMENT_POSITION")
    if (not isinstance(position_side, Side) or signal.side != position_side
        or type(dca_count) is not int or dca_count != 0):
        return Decision(False, "DCA_ALREADY_USED_OR_WRONG_SIDE")
    base = admit(signal, replace(risk, active_positions=0))
    return Decision(base.accepted,
                    "RISK_ADMITTED_EXISTING_POSITION_DCA" if base.accepted
                    else base.reason, base.signal if base.accepted else None)


def core_signal(row, rules=None):
    """Derive CORE ENTRY strictly from a closed M15 with a prior closed H1.

    DCA, TP and stop rules remain owned by freqtrade_parity.callbacks / rules.
    """
    if not isinstance(row, dict) or row.get("closed") is not True:
        return None
    opened, h1_open = row.get("open_time"), row.get("h1_source_open_time")
    if type(opened) is not int or opened <= 0 or opened % CANDLE_MS:
        return None
    if type(h1_open) is not int or h1_open < 0 or h1_open % HOUR_MS or h1_open + HOUR_MS > opened:
        return None
    try:
        previous, current, plus, minus, h1_adx = (
            _number(row[key]) for key in
            ("previous_rsi", "rsi", "h1_plus", "h1_minus", "h1_adx")
        )
        r = rules if rules is not None else StrategyRules()
        is_long = r.long_entry(previous, current, plus, minus, h1_adx)
        is_short = r.short_entry(previous, current, plus, minus, h1_adx)
    except (KeyError, TypeError, ValueError, OverflowError):
        return None
    if is_long == is_short:
        return None
    side = Side.LONG if is_long else Side.SHORT
    closed = opened + CANDLE_MS
    return Signal(Origin.CORE, side, closed, f"core:BTCUSDT:15m:{closed}:{side.value}")


def ai_signal(prediction, canonical_window, latest, now_ms, *, threshold="0.002"):
    """Accept an actual FreqAI prediction only after common provenance validation.

    The threshold is the existing pipeline.decision default (0.002), not a new
    CORE parameter. predictedReturn is NOT a calibrated confidence score.
    """
    if not isinstance(prediction, dict) or prediction.get("available") is False:
        return None
    try:
        from pipeline.decision import _prediction
        magnitude = _prediction(prediction, canonical_window, latest, now_ms)
        minimum = Decimal(str(threshold))
        if not minimum.is_finite() or minimum <= 0 or abs(magnitude) < minimum:
            return None
        side = Side.LONG if magnitude > 0 else Side.SHORT
        closed = latest["closeTimeMs"]
        payload = {field: prediction[field] for field in (
            "modelVersion", "strategyVersion", "datasetVersion", "candleCloseTimeMs",
        )}
        payload["side"] = side.value
        digest = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        return Signal(Origin.AI, side, closed, "freqai:" + digest)
    except (TypeError, ValueError, KeyError, InvalidOperation, OverflowError, AttributeError):
        return None


def _select(core, ai, candle_close_ms):
    sources = tuple(x.value for x, s in ((Origin.CORE, core), (Origin.AI, ai)) if s is not None)
    if any(s.candle_close_ms != candle_close_ms for s in (core, ai) if s is not None):
        return RouteResult("WAIT", "SIGNAL_CANDLE_MISMATCH", core=core, ai=ai, sources=sources)
    if core is not None and ai is not None and core.side != ai.side:
        return RouteResult("WAIT", "SOURCE_CONFLICT", core=core, ai=ai, sources=sources)
    selected = core if core is not None else ai
    if selected is None:
        return RouteResult("WAIT", "NO_SIGNAL")
    return RouteResult("SELECTED", "CORE_AI_AGREEMENT" if len(sources) == 2 else "SOURCE_ONLY",
                       selected=selected, core=core, ai=ai, sources=sources)


class ReservationLedger:
    """Atomic, durable, fail-closed single-symbol paper reservation.

    RESERVED is intentionally not retried after a crash; an operator must
    reconcile it before a new candle can reserve. No order submission here.
    """

    def __init__(self, path):
        if not path:
            raise ValueError("Persistent ledger path is required")
        self.path = Path(path)
        if str(self.path) == ":memory:":
            raise ValueError("In-memory ledger cannot survive restart")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(self.path, timeout=15)) as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.execute("PRAGMA synchronous=FULL")
            db.execute("""CREATE TABLE IF NOT EXISTS paper_reservations(
                signal_id TEXT PRIMARY KEY, symbol TEXT NOT NULL,
                candle_close_ms INTEGER NOT NULL, origin TEXT NOT NULL,
                side TEXT NOT NULL, status TEXT NOT NULL,
                intent_id TEXT, evidence TEXT,
                UNIQUE(symbol, candle_close_ms))""")
            db.execute("""CREATE UNIQUE INDEX IF NOT EXISTS paper_active_symbol
                ON paper_reservations(symbol) WHERE status IN ('RESERVED', 'BOUND')""")
            db.commit()

    def _connect(self):
        db = sqlite3.connect(self.path, timeout=15, isolation_level=None)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA synchronous=FULL")
        return db

    def entries(self):
        with closing(self._connect()) as db:
            return [dict(row) for row in db.execute(
                "SELECT * FROM paper_reservations ORDER BY candle_close_ms, signal_id").fetchall()]

    def reserve(self, signal, risk):
        decision = admit(signal, risk)
        if not decision.accepted:
            return decision
        with closing(self._connect()) as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                duplicate = db.execute("""SELECT 1 FROM paper_reservations
                    WHERE symbol=? AND candle_close_ms=?""", (SYMBOL, signal.candle_close_ms)).fetchone()
                active = db.execute("""SELECT 1 FROM paper_reservations
                    WHERE symbol=? AND status IN ('RESERVED', 'BOUND')""", (SYMBOL,)).fetchone()
                if duplicate:
                    result = Decision(False, "DUPLICATE_CANDLE")
                elif active:
                    result = Decision(False, "PENDING_RESERVATION")
                else:
                    db.execute("""INSERT INTO paper_reservations
                        (signal_id, symbol, candle_close_ms, origin, side, status)
                        VALUES (?, ?, ?, ?, ?, 'RESERVED')""", (
                        signal.signal_id, SYMBOL, signal.candle_close_ms,
                        signal.origin.value, signal.side.value,
                    ))
                    result = Decision(True, "RESERVED_FOR_PAPER_BINDING", signal)
                db.commit()
                return result
            except Exception:
                db.rollback()
                raise

    def bind(self, signal_id, paper_intent_id):
        if not isinstance(paper_intent_id, str) or not paper_intent_id.strip():
            raise ValueError("An explicit paper intent ID is required")
        with closing(self._connect()) as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                row = db.execute("SELECT status, intent_id FROM paper_reservations WHERE signal_id=?",
                                 (signal_id,)).fetchone()
                if row is None or (row["status"] == "BOUND" and row["intent_id"] != paper_intent_id) or (
                    row["status"] not in ("RESERVED", "BOUND")
                ):
                    raise ValueError("Unknown or conflicting reservation binding")
                if row["status"] == "RESERVED":
                    db.execute("""UPDATE paper_reservations SET status='BOUND', intent_id=?
                        WHERE signal_id=?""", (paper_intent_id, signal_id))
                db.commit()
            except Exception:
                db.rollback()
                raise

    def resolve(self, signal_id, status, evidence):
        if status not in ("CANCELLED", "CLOSED") or not isinstance(evidence, str) or not evidence.strip():
            raise ValueError("Explicit terminal state and reconciliation evidence are required")
        with closing(self._connect()) as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                row = db.execute("SELECT status FROM paper_reservations WHERE signal_id=?",
                                 (signal_id,)).fetchone()
                if row is None or row["status"] not in ("RESERVED", "BOUND") or (
                    status == "CLOSED" and row["status"] != "BOUND"
                ):
                    raise ValueError("Unverified terminal transition")
                db.execute("""UPDATE paper_reservations SET status=?, evidence=?
                    WHERE signal_id=?""", (status, evidence, signal_id))
                db.commit()
            except Exception:
                db.rollback()
                raise


class PaperSignalCoordinator:
    """Single-paper-signal gate that connects Freqtrade CORE and FreqAI artifacts."""

    def evaluate(self, row, canonical_window, prediction, now_ms, risk, ledger):
        if not isinstance(row, dict) or row.get("closed") is not True:
            return RouteResult("WAIT", "UNVERIFIED_CANDLE")
        try:
            from pipeline.decision import _canonical
            latest = _canonical(canonical_window, now_ms)
        except (KeyError, TypeError, ValueError, OverflowError, AttributeError):
            return RouteResult("WAIT", "INVALID_CANONICAL_WINDOW")
        try:
            if type(row.get("open_time")) is not int or row["open_time"] != latest["openTimeMs"]:
                raise ValueError("Mismatched candle")
            for field in ("open", "high", "low", "close", "volume"):
                a, b = Decimal(str(row[field])), Decimal(latest[field])
                if not a.is_finite() or a != b:
                    raise ValueError("Mismatched price")
        except (TypeError, ValueError, KeyError, InvalidOperation):
            return RouteResult("WAIT", "CANONICAL_ROW_MISMATCH")
        core = core_signal(row)
        ai = ai_signal(prediction, canonical_window, latest, now_ms)
        selected = _select(core, ai, latest["closeTimeMs"])
        if selected.action == "WAIT":
            return selected
        if not isinstance(ledger, ReservationLedger):
            return RouteResult("WAIT", "MISSING_PERSISTENT_LEDGER",
                               core=core, ai=ai, sources=selected.sources)
        admission = ledger.reserve(selected.selected, risk)
        if not admission.accepted:
            return RouteResult("WAIT", admission.reason, core=core, ai=ai, sources=selected.sources)
        return RouteResult("PAPER_RESERVED", admission.reason, selected.selected, core, ai, selected.sources)
