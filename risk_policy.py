"""Shared paper risk policy constants. These values are contract inputs, not runtime knobs."""
from decimal import Decimal

CORE_LEVERAGE = Decimal("1")  # Execution baseline; Core new-order margin remains capped at 1% equity.
CORE_ROE_SIGNAL_MULTIPLIER = Decimal("13")  # Legacy signal-threshold scale only; never used for order sizing or margin.
ORDER_MARGIN_BUDGET_PCT = Decimal("0.01")
