"""Check an actual installed Freqtrade runtime without conflating it with parity.

Usage:
    python runtime_probe.py --output freqtrade-runtime-status.json

The adapter currently disables all signals. Do not call a successful runtime
probe 'Android <-> Freqtrade strategy parity'.
"""
import argparse
import json
import re
import shutil
import subprocess
from pathlib import Path


def probe(executable="freqtrade"):
    report = {
        "schema_version": 1,
        "engine": "freqtrade",
        "actual_runtime_invoked": False,
        "runtime_available": False,
        "strategy_entry_exit_ported": False,
        "backtesting_executed": False,
        "same_ohlcv_data_compared": False,
        "event_parity_verified": False,
        "verified": False,
        "checks": {},
    }
    path = shutil.which(executable)
    if path is None:
        report["checks"]["runtime"] = "executable_not_found"
        return report
    try:
        version = subprocess.run([path, "--version"], capture_output=True,
                                 text=True, timeout=60, check=False)
        report["actual_runtime_invoked"] = True
        report["checks"]["version_exit_code"] = version.returncode
        report["checks"]["version_output"] = (version.stdout + version.stderr).strip()[:1000]
        report["runtime_available"] = version.returncode == 0 and "freqtrade" in (
            version.stdout + version.stderr).lower()
    except (OSError, subprocess.TimeoutExpired) as exc:
        report["checks"]["runtime"] = type(exc).__name__
    if report["runtime_available"]:
        try:
            root = Path(__file__).resolve().parent
            cmd = [path, "list-strategies", "--strategy-path",
                   str(root / "strategies"), "--one-column"]
            result = subprocess.run(cmd, capture_output=True, text=True,
                                    timeout=120, check=False)
            output = result.stdout + result.stderr
            report["checks"]["strategy_discovery_exit_code"] = result.returncode
            report["checks"]["strategy_discovered"] = bool(
                re.search(r"(?m)^BtcM15H1ParityGate\s*$", result.stdout))
            report["checks"]["strategy_discovery_tail"] = output[-1500:]
        except (OSError, subprocess.TimeoutExpired) as exc:
            report["checks"]["strategy_discovery_error"] = type(exc).__name__
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--require-runtime", action="store_true")
    args = parser.parse_args()
    report = probe()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n",
                           encoding="utf-8")
    print(json.dumps(report, indent=2))
    if args.require_runtime and not report["runtime_available"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
