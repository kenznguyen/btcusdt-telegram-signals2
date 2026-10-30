"""Strict parity verdict. Missing or unequal traces never count as verified."""
from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class ParityVerdict:
    parity_verified: bool
    reason: str
    compared_events: int


def compare_traces(kotlin: Sequence[dict] | None, python: Sequence[dict] | None) -> ParityVerdict:
    if not kotlin or not python:
        return ParityVerdict(False, "MISSING_OR_EMPTY_TRACE", 0)
    keys = ("symbol", "trade_id", "event", "candle_close_ms", "direction",
            "expected_fill_price", "actual_fill_price", "fill_difference")
    if len(kotlin) != len(python):
        return ParityVerdict(False, "EVENT_COUNT_MISMATCH", 0)
    for index, (a, b) in enumerate(zip(kotlin, python)):
        if not isinstance(a, dict) or not isinstance(b, dict):
            return ParityVerdict(False, f"INVALID_EVENT:{index}", index)
        if any(key not in a or key not in b or a[key] is None or b[key] is None for key in keys):
            return ParityVerdict(False, f"MISSING_FIELD:{index}", index)
        if any(a[k] != b[k] for k in keys):
            return ParityVerdict(False, f"EVENT_MISMATCH:{index}", index)
    return ParityVerdict(True, "MATCH", len(kotlin))
