"""Fail-closed, read-only preflight for the Core paper runtime.

This first CLI increment validates configuration and existing account risk state.
It deliberately does not run a strategy cycle or construct a writable ledger.
"""

import argparse
import json
import os
from pathlib import Path
import sys
import time

from paper_execution.ledger import read_account_risk_snapshot


_ALLOWED_CONFIG_KEYS = {"mode", "ai_execution_enabled", "ledger_path"}
_CREDENTIAL_ENV_KEYS = (
    "BINANCE_API_KEY",
    "BINANCE_API_SECRET",
    "OKX_API_KEY",
    "OKX_API_SECRET",
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
    if not isinstance(config, dict) or set(config) != _ALLOWED_CONFIG_KEYS:
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


def _preflight(config_path):
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

    risk = read_account_risk_snapshot(
        ledger_path, now_ms=time.time_ns() // 1_000_000
    )
    if risk.get("mode") != "PAPER" or risk.get("liveTradingSupported") is not False:
        raise PreflightError("PAPER_LEDGER_REQUIRED")
    if risk.get("riskReady") is not True:
        raise PreflightError("RISK_STATE_BLOCKED")

    return {
        "status": "PREFLIGHT_PASS",
        "mode": "PAPER",
        "decisionCycle": "NOT_RUN",
        "ledgerPath": str(ledger_path),
        "riskReady": True,
        "aiExecutionEnabled": False,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, help="Explicit paper-only JSON config")
    args = parser.parse_args(argv)
    try:
        result = _preflight(args.config)
    except PreflightError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except Exception:
        print("PREFLIGHT_FAILED", file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True, separators=(",", ":"), allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
