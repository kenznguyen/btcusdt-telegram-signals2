"""Phase 1: independent signals and shared fail-closed risk admission.

This module is deliberately independent of the existing strategy implementation.
No exchange execution is performed here.
"""
from dataclasses import dataclass
from enum import Enum
from typing import Optional


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
    confidence: Optional[float] = None


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


def admit(signal: Signal, risk: RiskSnapshot) -> Decision:
    """Admit an independent CORE or AI signal only with explicit safe state."""
    if not risk.data_fresh:
        return Decision(False, "STALE_DATA")
    if not risk.state_reconciled or risk.has_unresolved_reservation:
        return Decision(False, "UNRECONCILED_STATE")
    if signal.candle_close_ms <= 0 or not signal.signal_id:
        return Decision(False, "INVALID_SIGNAL")
    if signal.origin == Origin.AI:
        if not risk.ai_model_validated:
            return Decision(False, "AI_NOT_VALIDATED")
        if signal.confidence is None or not 0 <= signal.confidence <= 1:
            return Decision(False, "INVALID_AI_CONFIDENCE")
    if risk.max_positions <= 0 or risk.active_positions < 0 or risk.active_positions >= risk.max_positions:
        return Decision(False, "POSITION_LIMIT")
    if risk.required_margin <= 0 or risk.available_margin < risk.required_margin:
        return Decision(False, "INSUFFICIENT_MARGIN")
    return Decision(True, "ADMITTED_FOR_PAPER_EVALUATION", signal)
