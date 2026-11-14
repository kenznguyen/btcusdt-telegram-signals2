"""Immutable contract validation for the SIMULATED_CAPITAL_V1 PAPER account.

This module validates configuration only. It does not create a ledger, bootstrap an
account, execute orders, or claim that runtime risk enforcement is active.
"""
from decimal import Decimal, DecimalException


DEFAULT_SIMULATED_CAPITAL_CONTRACT = {
    "schemaVersion": 1,
    "contractId": "SIMULATED_CAPITAL_V1",
    "capitalMode": "SIMULATED",
    "tradingMode": "PAPER",
    "initialCapitalQuote": "100",
    "quoteCurrency": "USDT",
    "resetOnRestart": False,
    "autoTopUp": False,
    "liveTradingSupported": False,
    "aiExecutionEnabled": False,
    "riskLimits": {
        "maxDrawdownPct": "10",
        "maxDailyLossUsdt": "2",
        "maxExposureUsdt": "10",
        "maxOrderMarginPct": "1",
    },
    "riskScope": "SHARED_PORTFOLIO_CORE_AND_AI",
    "dcaConsumesOrderMarginBudget": True,
}

_CONTRACT_FIELDS = frozenset(DEFAULT_SIMULATED_CAPITAL_CONTRACT)
_RISK_FIELDS = frozenset(DEFAULT_SIMULATED_CAPITAL_CONTRACT["riskLimits"])


def _decimal(value, code):
    if isinstance(value, bool):
        raise ValueError(code)
    try:
        number = Decimal(str(value))
    except (DecimalException, TypeError, ValueError):
        raise ValueError(code) from None
    if not number.is_finite():
        raise ValueError(code)
    return number


def validate_simulated_capital_contract(contract):
    """Validate the approved v1 values and return a normalized copy."""
    if not isinstance(contract, dict) or set(contract) != _CONTRACT_FIELDS:
        raise ValueError("SIMULATED_CAPITAL_FIELDS_INVALID")
    if contract["schemaVersion"] != 1 or type(contract["schemaVersion"]) is not int:
        raise ValueError("SIMULATED_CAPITAL_VERSION_UNSUPPORTED")
    if (contract["contractId"] != "SIMULATED_CAPITAL_V1"
            or contract["capitalMode"] != "SIMULATED"
            or contract["tradingMode"] != "PAPER"
            or contract["quoteCurrency"] != "USDT"):
        raise ValueError("SIMULATED_CAPITAL_IDENTITY_INVALID")
    if _decimal(contract["initialCapitalQuote"], "SIMULATED_CAPITAL_AMOUNT_INVALID") != Decimal("100"):
        raise ValueError("SIMULATED_CAPITAL_AMOUNT_INVALID")
    if (contract["resetOnRestart"] is not False or contract["autoTopUp"] is not False):
        raise ValueError("SIMULATED_CAPITAL_CAPITAL_MUTATION_FORBIDDEN")
    if (contract["liveTradingSupported"] is not False
            or contract["aiExecutionEnabled"] is not False):
        raise ValueError("SIMULATED_CAPITAL_EXECUTION_BOUNDARY")
    if contract["riskScope"] != "SHARED_PORTFOLIO_CORE_AND_AI":
        raise ValueError("SIMULATED_CAPITAL_RISK_SCOPE_INVALID")
    if contract["dcaConsumesOrderMarginBudget"] is not True:
        raise ValueError("SIMULATED_CAPITAL_DCA_BUDGET_INVALID")

    limits = contract["riskLimits"]
    if not isinstance(limits, dict) or set(limits) != _RISK_FIELDS:
        raise ValueError("SIMULATED_CAPITAL_RISK_LIMITS_INVALID")
    expected = {
        "maxDrawdownPct": Decimal("10"),
        "maxDailyLossUsdt": Decimal("2"),
        "maxExposureUsdt": Decimal("10"),
        "maxOrderMarginPct": Decimal("1"),
    }
    normalized = {}
    for field, approved in expected.items():
        value = _decimal(limits[field], "SIMULATED_CAPITAL_RISK_LIMITS_INVALID")
        if value != approved:
            raise ValueError("SIMULATED_CAPITAL_RISK_LIMITS_INVALID")
        normalized[field] = format(value.normalize(), "f")

    result = dict(contract)
    result["initialCapitalQuote"] = "100"
    result["riskLimits"] = normalized
    return result
