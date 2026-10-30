"""Execute guarded native Freqtrade and FreqAI research on one pinned dataset.

This is NOT a trade-parity certificate: both native strategies intentionally
block native orders. Exported model research can only be used as candidate AI
artifacts after an independent provenance and out-of-sample validation gate.
"""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import sys

from quant_system.intrabar_audit import audit_history
from quant_system.native_dataset import training_window


def research_commands(*, days, detail_minutes, dataset_dir, native_datadir, out_dir, userdir,
                      config_path=None, exchange="binance"):
    if type(days) is not int or days not in (180, 360):
        raise ValueError("Only 180/360-day research is supported")
    if detail_minutes not in (1, 5):
        raise ValueError("Invalid native detail timeframe")
    if type(exchange) is not str or exchange not in ("okx", "binance"):
        raise ValueError("UNSUPPORTED_RESEARCH_VENUE")
    files = [Path(dataset_dir) / "15m.csv", Path(dataset_dir) / "1h.csv",
             Path(dataset_dir) / f"{detail_minutes}m.csv"]
    verified = audit_history(
        *files, days=days, detail_minutes=detail_minutes,
    )
    training_window(files[0], files[1], days=days, warmup_days=35)
    if not verified["ohlcv_verified"]:
        raise ValueError("Missing or invalid shared OHLCV data")
    root = Path(__file__).resolve().parents[1]
    config_file = (root / "freqai_bridge/config.research.json").resolve() if config_path is None else Path(config_path).resolve()
    approved_configs = {
        (root / "freqai_bridge/config.research.json").resolve(),
        (root / "freqai_bridge/config.okx-research.json").resolve(),
    }
    if config_file not in approved_configs:
        raise ValueError("UNAPPROVED_RESEARCH_CONFIG")
    config = json.loads(config_file.read_text())
    provenance_path = Path(dataset_dir) / "native-export-report.json"
    if not provenance_path.is_file():
        raise ValueError("MISSING_VENUE_DATASET_PROVENANCE")
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    if (provenance.get("exchange") != exchange or
        provenance.get("symbol") != "BTC/USDT:USDT" or
        provenance.get("marketType") != "USDT_PERPETUAL" or
        provenance.get("dataset_sha256") != verified.get("dataset_sha256") or
        provenance.get("ohlcv_verified") is not True):
        raise ValueError("VENUE_MISMATCH_OR_UNVERIFIED_DATASET")
    if (config.get("dry_run") is not True or config.get("trading_mode") != "futures"
        or config.get("exchange", {}).get("name") != exchange
        or config.get("freqai", {}).get("enabled") is not True
        or config.get("force_entry_enable") is not False):
        raise ValueError("Native Freqtrade research config not fail-closed")
    for file in ("freqai_bridge/ChartProFreqaiResearch.py",
                 "freqtrade_parity/ChartProParityDryRun.py"):
        source = (root / file).read_text(encoding="utf-8")
        if ('dataframe["enter_long"] = 0' not in source and
            'dataframe["enter_long"]=0' not in source):
            raise ValueError("Native entry unexpectedly enabled")
        if ('dataframe["enter_short"] = 0' not in source and
            'dataframe["enter_short"]=0' not in source):
            raise ValueError("Native short unexpectedly enabled")
        if "return False" not in source:
            raise ValueError("Native confirm_trade_entry protection missing")
    beginning, ending = verified["start_ms"], verified["end_ms"]
    if beginning % 60_000 or ending % 60_000 or beginning >= ending:
        raise ValueError("INVALID_NATIVE_TIMERANGE")
    timerange = (
        datetime.fromtimestamp(beginning / 1000, tz=timezone.utc).strftime("%Y%m%dT%H%M")
        + "-" +
        datetime.fromtimestamp(ending / 1000, tz=timezone.utc).strftime("%Y%m%dT%H%M")
    )
    target = Path(out_dir).resolve()
    target.mkdir(parents=True, exist_ok=True)
    user_dir = Path(userdir).resolve()
    # Freqtrade CLI requires a pre-created user-data root. Never rely on
    # the implicit checkout ./user_data or create a new one mid-backtest.
    if not user_dir.is_dir() or not (user_dir / "strategies").is_dir():
        raise ValueError("MISSING_INITIALIZED_FREQTRADE_USERDIR")
    common = [
        sys.executable, "-m", "freqtrade", "backtesting",
        "--config", str(config_file),
        "--datadir", str(Path(native_datadir).resolve()),
        "--userdir", str(user_dir),
        "--timeframe", "15m", "--timeframe-detail", f"{detail_minutes}m",
        "--timerange", timerange,
        "--dry-run-wallet", "100", "--fee", "0.0005", "--cache", "none",
        "--export", "signals",
    ]
    core = common + [
        "--strategy-path", str(root / "freqtrade_parity"),
        "--strategy", "ChartProParityDryRun",
    ]
    freqai = common + [
        "--strategy-path", str(root / "freqai_bridge"),
        "--strategy", "ChartProFreqaiResearch",
        "--freqaimodel", "LightGBMRegressor",
    ]
    return verified, [("core", core), ("freqai", freqai)]


def run_research(*, days, detail_minutes, dataset_dir, native_datadir, out_dir, userdir,
                 config_path=None, exchange="binance"):
    target = Path(out_dir).resolve()
    target.mkdir(parents=True, exist_ok=True)
    report = {
        "days": days, "detail_timeframe": f"{detail_minutes}m",
        "exchange": exchange,
        "funding_mark_full_coverage_verified": False,
        "core_native_runtime_succeeded": False,
        "freqai_native_runtime_succeeded": False,
        "freqai_oos_verified": False,
        "core_trade_parity_verified": False,
        "native_trade_parity_verified": False,
        "full_core_parity_certified": False,
        "native_orders_enabled": False,
    }
    output = target / f"native-research-{days}.json"
    try:
        verified, commands = research_commands(
            days=days, detail_minutes=detail_minutes, dataset_dir=dataset_dir,
            native_datadir=native_datadir, out_dir=out_dir, userdir=userdir,
            config_path=config_path, exchange=exchange,
        )
        report.update(dataset_sha256=verified["dataset_sha256"],
                      detail_sha256=verified["detail_sha256"],
                      ohlcv_verified=True)
        for label, command in commands:
            # Only known executable and hardcoded args. Data paths are operator input.
            log = target / f"{label}-native-{days}.log"
            with log.open("w", encoding="utf-8") as handle:
                completed = subprocess.run(
                    command, stdout=handle, stderr=subprocess.STDOUT,
                    cwd=Path(__file__).resolve().parents[1], check=False, timeout=3600,
                )
            report[f"{label}_native_runtime_succeeded"] = completed.returncode == 0
            report[f"{label}_native_exit_code"] = completed.returncode
            if completed.returncode:
                raise RuntimeError(f"{label.upper()}_NATIVE_BACKTEST_FAILED")
        report["reason"] = "NATIVE_RESEARCH_COMPLETED_TRADE_PARITY_NOT_VERIFIED"
    except (ValueError, OSError, RuntimeError, subprocess.TimeoutExpired) as error:
        report["reason"] = str(error)[:180]
    finally:
        output.write_text(json.dumps(report, sort_keys=True, indent=2), encoding="utf-8")
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, choices=(180, 360), required=True)
    parser.add_argument("--detail-minutes", type=int, choices=(1, 5), default=5)
    parser.add_argument("--dataset-dir", required=True)
    parser.add_argument("--native-datadir", required=True)
    parser.add_argument("--userdir", required=True)
    parser.add_argument("--exchange", choices=("binance", "okx"), required=True)
    parser.add_argument("--config-path", required=True)
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args()
    report = run_research(
        days=args.days, detail_minutes=args.detail_minutes,
        dataset_dir=args.dataset_dir, native_datadir=args.native_datadir,
        out_dir=args.out_dir, userdir=args.userdir,
        config_path=args.config_path, exchange=args.exchange,
    )
    print(json.dumps(report, sort_keys=True))
    return 0 if report["core_native_runtime_succeeded"] and report["freqai_native_runtime_succeeded"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
