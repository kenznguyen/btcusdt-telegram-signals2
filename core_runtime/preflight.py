"""Read-only PAPER Core runtime preflight shared by CLI and one-shot runner."""

import json
import os
from pathlib import Path
import time

from paper_execution.ledger import read_account_risk_snapshot


_BASE_CONFIG_KEYS = {"mode", "ai_execution_enabled", "ledger_path"}
_RUNNER_CONFIG_KEYS = _BASE_CONFIG_KEYS | {
    "risk_limits", "max_book_age_ms", "max_position_base",
}
_CREDENTIAL_ENV_KEYS = (
    "BINANCE_API_KEY", "BINANCE_API_SECRET", "OKX_API_KEY", "OKX_API_SECRET",
)


class PreflightError(Exception):
    """Stable, user-safe preflight rejection."""


def _load_config(config_path):
    path = Path(config_path)
    if not path.is_file():
        raise PreflightError("CONFIG_NOT_FOUND")
    try:
        config = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        raise PreflightError("CONFIG_INVALID") from None
    if not isinstance(config, dict) or set(config) not in (
        _BASE_CONFIG_KEYS, _RUNNER_CONFIG_KEYS,
    ):
        raise PreflightError("CONFIG_SCHEMA_INVALID")
    if config.get("mode") != "PAPER":
        raise PreflightError("PAPER_MODE_REQUIRED")
    if config.get("ai_execution_enabled") is not False:
        raise PreflightError("AI_EXECUTION_MUST_BE_DISABLED")
    ledger_value = config.get("ledger_path")
    if not isinstance(ledger_value, str) or not ledger_value.strip():
        raise PreflightError("LEDGER_PATH_REQUIRED")
    ledger_path = Path(ledger_value)
    if not ledger_path.is_absolute():
        ledger_path = path.resolve().parent / ledger_path
    return config, ledger_path.resolve()


def _preflight(config_path, *, now_ms=None, allow_risk_unready=False):
    config, ledger_path = _load_config(config_path)
    if any(os.environ.get(key) for key in _CREDENTIAL_ENV_KEYS):
        raise PreflightError("EXCHANGE_CREDENTIALS_FORBIDDEN")
    if os.environ.get("AI_EXECUTION_ENABLED", "false").strip().lower() != "false":
        raise PreflightError("AI_EXECUTION_MUST_BE_DISABLED")
    market_data_db = os.environ.get("MARKET_DATA_DB")
    if market_data_db:
        try:
            if ledger_path == Path(market_data_db).resolve():
                raise PreflightError("T0_LEDGER_PATH_FORBIDDEN")
        except OSError:
            raise PreflightError("LEDGER_PATH_INVALID") from None
    if not ledger_path.is_file():
        raise PreflightError("LEDGER_FILE_REQUIRED")
    observed_now = time.time_ns() // 1_000_000 if now_ms is None else now_ms
    risk = read_account_risk_snapshot(ledger_path, now_ms=observed_now)
    if risk.get("mode") != "PAPER" or risk.get("liveTradingSupported") is not False:
        raise PreflightError("PAPER_LEDGER_REQUIRED")
    risk_ready = risk.get("riskReady") is True
    if not risk_ready and allow_risk_unready is not True:
        raise PreflightError("RISK_STATE_BLOCKED")
    return {
        "status": "PREFLIGHT_PASS" if risk_ready else "PREFLIGHT_RISK_UNREADY",
        "mode": "PAPER", "decisionCycle": "NOT_RUN",
        "ledgerPath": str(ledger_path), "riskReady": risk_ready,
        "aiExecutionEnabled": False,
    }
