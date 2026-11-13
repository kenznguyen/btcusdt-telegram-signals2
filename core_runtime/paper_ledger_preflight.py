"""Read-only PaperLedger readiness gate; never starts a decision cycle."""

import os
from pathlib import Path

from core_runtime.continuous_dry_run import _canonical, _overlaps
from core_runtime.preflight import (
    _CREDENTIAL_ENV_KEYS,
    _load_config,
)
from paper_execution.ledger import read_account_risk_snapshot


class PaperLedgerPreflightError(ValueError):
    """Stable, fail-closed PaperLedger preflight rejection."""


_PROTECTED_DB_ENV_KEYS = (
    "MARKET_DATA_DB", "T0_FEEDER_LEASE_DB", "PAPER_DB", "PAPER_TRADING_DB",
)


def inspect_paper_ledger_preflight(config_path, *, now_ms, environ=None):
    """Read and validate an existing PAPER ledger without writing any state."""
    env = os.environ if environ is None else environ
    try:
        _, ledger_path = _load_config(config_path)
    except Exception as exc:
        raise PaperLedgerPreflightError(str(exc) or "CONFIG_INVALID") from None

    if env.get("AI_EXECUTION_ENABLED") != "false":
        raise PaperLedgerPreflightError("AI_EXECUTION_MUST_BE_EXPLICITLY_DISABLED")
    if any(env.get(key) for key in _CREDENTIAL_ENV_KEYS):
        raise PaperLedgerPreflightError("EXCHANGE_CREDENTIALS_FORBIDDEN")

    ledger = _canonical(ledger_path)
    if not ledger.is_file():
        raise PaperLedgerPreflightError("LEDGER_FILE_REQUIRED")

    for key in _PROTECTED_DB_ENV_KEYS:
        protected_value = env.get(key)
        if protected_value and _overlaps(ledger, _canonical(protected_value)):
            if key in ("PAPER_DB", "PAPER_TRADING_DB"):
                if _canonical(protected_value) != ledger:
                    raise PaperLedgerPreflightError("LEDGER_PATH_ENV_MISMATCH")
            else:
                raise PaperLedgerPreflightError("T0_LEDGER_PATH_FORBIDDEN")

    try:
        snapshot = read_account_risk_snapshot(ledger, now_ms=now_ms)
    except Exception as exc:
        code = str(exc).strip() or type(exc).__name__
        raise PaperLedgerPreflightError("PAPER_LEDGER_UNREADABLE:" + code) from None

    if snapshot.get("mode") != "PAPER" or snapshot.get("liveTradingSupported") is not False:
        raise PaperLedgerPreflightError("PAPER_LEDGER_REQUIRED")
    if snapshot.get("riskReady") is not True:
        raise PaperLedgerPreflightError("RISK_STATE_BLOCKED")

    kill_switch = snapshot.get("killSwitch")
    if not isinstance(kill_switch, dict):
        raise PaperLedgerPreflightError("RISK_CONTROL_STATE_MISSING")
    if kill_switch.get("killed") is not False:
        raise PaperLedgerPreflightError("PAPER_KILL_SWITCH_ACTIVE")
    if kill_switch.get("paused") is not False:
        raise PaperLedgerPreflightError("PAPER_RISK_PAUSED")

    return {
        "status": "PAPER_LEDGER_READY",
        "mode": "PAPER",
        "liveTradingSupported": False,
        "riskReady": True,
        "killSwitch": {
            "killed": False,
            "paused": False,
            "updatedAtMs": kill_switch.get("updatedAtMs"),
        },
        "decisionCycle": "NOT_RUN",
        "oneShotInvoked": False,
        "aiExecutionEnabled": False,
        "exchangeCredentialsUsed": False,
        "persistentStateMutation": "NONE",
    }
