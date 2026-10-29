"""Run a bounded legacy task on Codemagic; no GitHub Actions API is used."""

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time
from decimal import Decimal, InvalidOperation

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
COMMANDS = {"help", "status", "position", "signal", "backtest", "btstatus", "btresult"}


def backtest_environment(env):
    try:
        days = int(env.get("BACKTEST_DAYS", "360"))
        capital = Decimal(env.get("BACKTEST_INITIAL_CAPITAL", "100"))
        entry = Decimal(env.get("ENTRY_MARGIN_PCT", "50"))
        dca = Decimal(env.get("DCA_MARGIN_RATIO", "100"))
    except (ValueError, InvalidOperation) as error:
        raise ValueError("Invalid backtest parameters") from error
    if not 1 <= days <= 365 or not all(v.is_finite() for v in (capital, entry, dca)):
        raise ValueError("Invalid backtest parameters")
    if not 1 <= capital <= 100_000_000 or not 1 <= entry <= 100 or not 0 <= dca <= 500:
        raise ValueError("Backtest parameters outside allowed limits")
    # Codemagic/API inputs are percentages; engine env also accepts fractions.
    # Convert explicitly so 1% entry and 5% DCA do not become 100%/500%.
    return {"BACKTEST_DAYS": str(days), "BACKTEST_INITIAL_CAPITAL": str(capital),
            "ENTRY_MARGIN_PCT": str(entry / 100), "DCA_MARGIN_RATIO": str(dca / 100)}


def restore_state(env, directory, required=False):
    supplied = env.get("LEGACY_STATE_JSON", "")
    if not supplied:
        if required:
            raise ValueError("Scanner requires an explicit prior LEGACY_STATE_JSON snapshot; state is not a CI cache")
        return
    if len(supplied.encode()) > 1_048_576:
        raise ValueError("State snapshot is too large")
    state = json.loads(supplied)
    required_fields = {"side", "qty", "avg_entry", "account_balance"}
    if not isinstance(state, dict) or not required_fields <= state.keys() or state.get("side") not in (None, "LONG", "SHORT"):
        raise ValueError("Invalid paper state snapshot")
    try:
        amounts = [state[name] for name in ("qty", "avg_entry", "account_balance")]
        if any(type(value) not in (int, float) or not math.isfinite(value) or value < 0 for value in amounts):
            raise ValueError("Invalid paper position numbers")
    except OverflowError as error:
        raise ValueError("Invalid paper position numbers") from error
    quantity, entry, _ = amounts
    if state.get("side") is not None and (quantity <= 0 or entry <= 0):
        raise ValueError("An open paper position needs quantity and entry price")
    if state.get("side") is None and quantity != 0:
        raise ValueError("Flat paper state cannot contain a position quantity")
    # Reject non-JSON numeric constants without logging sensitive state contents.
    data = json.dumps(state, allow_nan=False, sort_keys=True).encode()
    directory.joinpath("state.json").write_bytes(data)
    directory.joinpath("state-provenance.json").write_text(json.dumps({
        "mode": "MANUAL_SNAPSHOT", "inputSha256": hashlib.sha256(data).hexdigest(),
        "buildId": env.get("CM_BUILD_ID"), "restoredAtMs": time.time_ns() // 1_000_000,
    }))


def run_task(mode, env=None, directory=ROOT):
    env = dict(os.environ if env is None else env)
    directory = Path(directory)
    env["BACKTEST_RUN_ID"] = env.get("CM_BUILD_ID") or env.get("BACKTEST_RUN_ID") or f"manual-{time.time_ns()}"
    if mode == "scanner":
        restore_state(env, directory, required=True)
        command = [sys.executable, str(ROOT / "bot.py")]
    elif mode == "dashboard":
        env.update(backtest_environment(env))
        command = [sys.executable, str(ROOT / "backtest.py")]
    elif mode == "telegram":
        selected = env.get("TELEGRAM_COMMAND", "help")
        if selected not in COMMANDS:
            raise ValueError("Unsupported Telegram command")
        if selected == "backtest":
            env.update(backtest_environment(env))
        if selected in {"status", "position"}:
            restore_state(env, directory)
        if selected in {"btstatus", "btresult"}:
            from integrations.codemagic_client import latest_report
            report = latest_report("telegram-command")
            for name in ("backtest_last_result.json", "backtest_status.json"):
                value = report.get("files", {}).get(name)
                if value is not None:
                    data = json.loads(value)
                    if not isinstance(data, dict):
                        raise ValueError("Invalid backtest report")
                    directory.joinpath(name).write_text(json.dumps(data, allow_nan=False))
        command = [sys.executable, str(ROOT / "telegram_commands.py"), selected]
    else:
        raise ValueError("Unsupported Codemagic task")
    subprocess.run(command, cwd=directory, env=env, check=True)
    if mode == "dashboard" or (mode == "telegram" and selected == "backtest"):
        # The legacy Telegram handler catches engine errors. A zero exit alone
        # cannot certify success; require this build's completed status file.
        status_path = directory / env.get("BACKTEST_STATUS_FILE", "backtest_status.json")
        try:
            status = json.loads(status_path.read_text())
        except (OSError, ValueError) as error:
            raise RuntimeError("Backtest did not produce a valid status") from error
        if not isinstance(status, dict) or status.get("status") != "completed" or status.get("run_id") != env["BACKTEST_RUN_ID"]:
            raise RuntimeError("Backtest did not complete for this build")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("telegram", "dashboard", "scanner"))
    args = parser.parse_args()
    try:
        run_task(args.mode)
    except (ValueError, OSError, RuntimeError, subprocess.CalledProcessError) as error:
        # Deliberately do not print command env, state JSON or credentials.
        parser.exit(1, f"Codemagic task failed ({type(error).__name__}); inspect the task step logs.\n")
