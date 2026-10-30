"""Execute guarded native Freqtrade and FreqAI research on one pinned dataset.

This is NOT a trade-parity certificate: both native strategies intentionally
block native orders. Exported model research can only be used as candidate AI
artifacts after an independent provenance and out-of-sample validation gate.
"""
import argparse
from collections import deque
import csv
import hashlib
import json
import os
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
    warmup_start, warmup_end = training_window(files[0], files[1], days=days, warmup_days=35)
    if (warmup_start != verified.get("start_ms") or
        warmup_end != verified.get("end_ms")):
        raise ValueError("NATIVE_TRAINING_WINDOW_MISMATCH")
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
    trusted_fields = {
        "exchange": exchange, "symbol": "BTC/USDT:USDT",
        "marketType": "USDT_PERPETUAL",
        "dataset_sha256": verified.get("dataset_sha256"),
        "detail_sha256": verified.get("detail_sha256"),
    }
    trusted_digest = "sha256:" + hashlib.sha256(json.dumps(
        trusted_fields, sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")).hexdigest()
    if (provenance.get("ohlcv_verified") is not True or
        any(provenance.get(k) != v or not isinstance(v, str)
            for k, v in trusted_fields.items()) or
        provenance.get("provenance_sha256") != trusted_digest):
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
    # CORE's signals are RSI/ADX/Smart DCA only. It must NOT initialize
    # FreqAI just because the separate AI research configuration enables it.
    # Freqtrade 2026.9 rejects an enabled FreqAI config without --freqaimodel:
    # "No freqaimodel set". Passing an AI model to CORE would conflate the
    # independent strategy sources, so derive an isolated fail-closed config.
    core_config = json.loads(json.dumps(config))
    core_config["freqai"]["enabled"] = False
    if (core_config["exchange"]["name"] != exchange or
        core_config.get("dry_run") is not True or
        core_config.get("force_entry_enable") is not False):
        raise ValueError("UNSAFE_CORE_RESEARCH_CONFIG")
    core_config_file = target / f"core-research-config-{days}.json"
    core_config_file.write_text(
        json.dumps(core_config, sort_keys=True, indent=2), encoding="utf-8",
    )
    core = common.copy()
    core[core.index("--config") + 1] = str(core_config_file.resolve())
    core += [
        "--strategy-path", str(root / "freqtrade_parity"),
        "--strategy", "ChartProParityDryRun",
    ]
    phase8 = os.environ.get("PHASE8_CAPTURE_MODEL_LINEAGE", "0")
    if phase8 not in ("0", "1"):
        raise ValueError("INVALID_PHASE8_CAPTURE_SWITCH")
    if phase8 == "1" and (days != 180 or exchange != "okx"):
        raise ValueError("PHASE8_REQUIRES_180D_OKX_RESEARCH")
    freqai = common + [
        "--strategy-path", str(root / "freqai_bridge"),
        "--strategy", "ChartProFreqaiResearch",
        "--freqaimodel",
        "ChartProAuditLightGBMRegressor" if phase8 == "1" else "LightGBMRegressor",
    ]
    return verified, [("core", core), ("freqai", freqai)]


def native_failure_excerpt(path, max_lines=60):
    """Return a bounded excerpt from a persisted native failure log.

    The original full log remains a Codemagic artifact. No success is inferred
    from an error excerpt; empty or absent logs remain explicit.
    """
    if not isinstance(max_lines, int) or not 1 <= max_lines <= 100:
        raise ValueError("INVALID_LOG_TAIL_LIMIT")
    source = Path(path)
    if not source.is_file():
        return "[NO_NATIVE_LOG_FILE]"
    try:
        with source.open("r", encoding="utf-8", errors="replace") as handle:
            excerpt = "".join(deque(handle, maxlen=max_lines))
        return excerpt[-10000:] if excerpt else "[EMPTY_NATIVE_LOG_FILE]"
    except OSError:
        return "[NATIVE_LOG_UNREADABLE]"


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
        "prediction_capture_verified": False,
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
        prediction_path = target / "freqai-native-predictions.csv"
        prediction_path.unlink(missing_ok=True)  # Reject cached forecasts from a prior model run.
        phase8_enabled = os.environ.get("PHASE8_CAPTURE_MODEL_LINEAGE") == "1"
        lineage_path = target / "freqai-native-model-lineage.csv"
        lineage_path.unlink(missing_ok=True)
        if phase8_enabled:
            report["phase8_model_trace_requested"] = True
        for label, command in commands:
            # AI must originate in the real FreqAI backtesting dataframe; no
            # fabricated predictions or entry flags from the offline simulator.
            environment = os.environ.copy()
            environment.pop("PHASE3_PREDICTIONS_CSV", None)
            environment.pop("PHASE8_LINEAGE_CSV", None)
            if label == "freqai" and days == 180 and exchange == "okx":
                environment["PHASE3_PREDICTIONS_CSV"] = str(prediction_path.resolve())
                if phase8_enabled:
                    environment["PHASE8_LINEAGE_CSV"] = str(lineage_path.resolve())
            log = target / f"{label}-native-{days}.log"
            with log.open("w", encoding="utf-8") as handle:
                completed = subprocess.run(
                    command, stdout=handle, stderr=subprocess.STDOUT,
                    cwd=Path(__file__).resolve().parents[1], check=False, timeout=3600,
                    env=environment,
                )
            report[f"{label}_native_runtime_succeeded"] = completed.returncode == 0
            report[f"{label}_native_exit_code"] = completed.returncode
            if completed.returncode:
                excerpt = native_failure_excerpt(log)
                report["failure_source"] = label
                report["failure_log_path"] = str(log)
                report["failure_log_tail"] = excerpt
                # Make the cause visible directly in the failed Codemagic
                # build step, not just in a downloadable ZIP artifact.
                print(
                    f"NATIVE_{label.upper()}_FAILURE_EXIT_CODE={completed.returncode}"
                    f" LOG={log}",
                    flush=True,
                )
                print("--- Native failure log (last lines) ---", flush=True)
                print(excerpt, flush=True)
                print("--- End native failure log ---", flush=True)
                raise RuntimeError(f"{label.upper()}_NATIVE_BACKTEST_FAILED")
            if label == "freqai" and days == 180 and exchange == "okx":
                if not prediction_path.is_file() or prediction_path.stat().st_size == 0:
                    raise RuntimeError("NO_NATIVE_FREQAI_PREDICTIONS")
                from quant_system.native_prediction_capture import FIELDS
                with prediction_path.open(newline="", encoding="utf-8") as source:
                    rows = csv.DictReader(source)
                    if not set(FIELDS).issubset(rows.fieldnames or []):
                        raise RuntimeError("INVALID_NATIVE_PREDICTION_COLUMNS")
                    total = accepted = 0
                    for row in rows:
                        total += 1
                        if row.get("source") != "freqai-native-backtest" or (
                            row.get("pair") != "BTC/USDT:USDT"
                        ):
                            raise RuntimeError("WRONG_NATIVE_PREDICTION_SOURCE")
                        if row.get("do_predict") == "1":
                            accepted += 1
                if not accepted:
                    raise RuntimeError("NO_ACCEPTED_NATIVE_FREQAI_FORECASTS")
                report["prediction_capture_sha256"] = (
                    "sha256:" + hashlib.sha256(prediction_path.read_bytes()).hexdigest()
                )
                report["prediction_capture_path"] = str(prediction_path)
                report["prediction_capture_rows"] = total
                report["prediction_capture_accepted"] = accepted
                native_config = json.loads(Path(config_path).read_text(encoding="utf-8"))
                report["prediction_model_identifier"] = native_config["freqai"]["identifier"]
                report["prediction_capture_verified"] = True
        if phase8_enabled:
            if not lineage_path.is_file() or lineage_path.stat().st_size <= 0:
                raise RuntimeError("MISSING_NATIVE_PHASE8_MODEL_FINGERPRINTS")
            report["phase8_model_lineage_sha256"] = (
                "sha256:" + hashlib.sha256(lineage_path.read_bytes()).hexdigest()
            )
            report["phase8_model_lineage_bytes"] = lineage_path.stat().st_size
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
    valid_capture = (report["prediction_capture_verified"] if args.days == 180 else True)
    return 0 if (report["core_native_runtime_succeeded"] and
                 report["freqai_native_runtime_succeeded"] and valid_capture) else 1


if __name__ == "__main__":
    raise SystemExit(main())
