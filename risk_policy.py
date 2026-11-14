"""Shared paper risk policy constants. These values are contract inputs, not runtime knobs."""
from decimal import Decimal

CORE_LEVERAGE = Decimal("1")  # Conservative Core baseline; new-order margin remains capped at 1% equity.
ORDER_MARGIN_BUDGET_PCT = Decimal("0.01")
