"""Pure, execution-free signal resolution. No exchange or Freqtrade dependencies.

Neither CORE nor AI may submit orders here. RiskGate defaults to paper-only.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Candidate:
    origin: str
    direction: str
    valid: bool = True

    def __post_init__(self):
        if self.origin not in ("CORE", "AI_NATIVE"):
            raise ValueError("invalid origin")
        if self.direction not in ("LONG", "SHORT"):
            raise ValueError("invalid direction")


@dataclass(frozen=True)
class Intent:
    origin: str
    direction: Optional[str]
    status: str
    ai_valid: bool = True


@dataclass(frozen=True)
class RiskPolicy:
    execution_mode: str = "PAPER"
    position_open: bool = False
    allow_ai_native: bool = False


@dataclass(frozen=True)
class Decision:
    approved: bool
    reason: str


def resolve(core: Optional[Candidate], ai: Optional[Candidate]) -> Intent:
    if core is not None and core.origin != "CORE":
        raise ValueError("core channel must be CORE")
    if ai is not None and ai.origin != "AI_NATIVE":
        raise ValueError("ai channel must be AI_NATIVE")
    if core and ai:
        if core.direction != ai.direction:
            return Intent("CONFLICT", None, "CONFLICT", ai.valid)
        return Intent("CONFIRMED", core.direction, "CANDIDATE", ai.valid)
    if core:
        return Intent("CORE", core.direction, "CANDIDATE")
    if ai:
        return Intent("AI_NATIVE", ai.direction, "CANDIDATE", ai.valid)
    return Intent("NONE", None, "NO_SIGNAL")


def approve(intent: Intent, policy: RiskPolicy) -> Decision:
    if policy.execution_mode != "PAPER":
        return Decision(False, "PAPER_ONLY")
    if policy.position_open:
        return Decision(False, "POSITION_OPEN")
    if intent.status != "CANDIDATE":
        return Decision(False, intent.status)
    if intent.origin in ("AI_NATIVE", "CONFIRMED") and not intent.ai_valid:
        return Decision(False, "INVALID_AI_PREDICTION")
    if intent.origin == "AI_NATIVE" and not policy.allow_ai_native:
        return Decision(False, "AI_SHADOW_MODE")
    return Decision(True, "PAPER_APPROVED")
