"""R22.2 isolated, non-executing Freqtrade/FreqAI runtime compatibility probe."""
from __future__ import annotations

import hashlib
import importlib.metadata
import json
import tempfile
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "freqai_bridge" / "config.okx-research.json"
METADATA_PATH = ROOT / "research_evidence/frozen-model/phase13b-20261104/model-candidate-metadata.json"
EXPECTED_FREQTRADE = "2026.9"
EXPECTED_FEATURES = [
    "%-relative-price_14_BTC/USDTUSDT_15m",
    "%-relative-volume_14_BTC/USDTUSDT_15m",
    "%-relative-price_28_BTC/USDTUSDT_15m",
    "%-relative-volume_28_BTC/USDTUSDT_15m",
    "%-pct-change_gen_BTC/USDTUSDT_15m",
    "%-raw-volume_gen_BTC/USDTUSDT_15m",
    "%-relative-price_14_shift-1_BTC/USDTUSDT_15m",
    "%-relative-volume_14_shift-1_BTC/USDTUSDT_15m",
    "%-relative-price_28_shift-1_BTC/USDTUSDT_15m",
    "%-relative-volume_28_shift-1_BTC/USDTUSDT_15m",
    "%-pct-change_gen_shift-1_BTC/USDTUSDT_15m",
    "%-raw-volume_gen_shift-1_BTC/USDTUSDT_15m",
    "%-relative-price_14_shift-2_BTC/USDTUSDT_15m",
    "%-relative-volume_14_shift-2_BTC/USDTUSDT_15m",
    "%-relative-price_28_shift-2_BTC/USDTUSDT_15m",
    "%-relative-volume_28_shift-2_BTC/USDTUSDT_15m",
    "%-pct-change_gen_shift-2_BTC/USDTUSDT_15m",
    "%-raw-volume_gen_shift-2_BTC/USDTUSDT_15m",
    "%-day-of-week",
    "%-hour-of-day",
]


def canonical_sha(value: dict) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return "sha256:" + hashlib.sha256(raw.encode("utf8")).hexdigest()


def runtime_config_snapshot(config: dict) -> dict:
    """Match ChartProAuditLightGBMRegressor's historical freeze snapshot."""
    return {
        "freqai": config["freqai"],
        "exchange": {"name": config["exchange"]["name"]},
        "timeframe": config["timeframe"],
        "dry_run": config["dry_run"],
        "force_entry_enable": config["force_entry_enable"],
    }


def expected_expanded_features(pair: str, timeframe: str, periods: list[int],
                               shifts: int) -> list[str]:
    normalized_pair = pair.replace(":", "")
    base = []
    for period in periods:
        base.extend([
            f"%-relative-price_{period}_{normalized_pair}_{timeframe}",
            f"%-relative-volume_{period}_{normalized_pair}_{timeframe}",
        ])
    base.extend([
        f"%-pct-change_gen_{normalized_pair}_{timeframe}",
        f"%-raw-volume_gen_{normalized_pair}_{timeframe}",
    ])
    expanded = list(base)
    for shift in range(1, shifts + 1):
        expanded.extend(name.replace(f"_{normalized_pair}_{timeframe}",
                                     f"_shift-{shift}_{normalized_pair}_{timeframe}")
                        for name in base)
    expanded.extend(["%-day-of-week", "%-hour-of-day"])
    return expanded


def build_runtime_config(raw: dict) -> dict:
    """Remove startup/retraining controls; probe only the configuration loader."""
    safe = json.loads(json.dumps(raw))
    safe["initial_state"] = "stopped"
    # Preserve all fields included in the historical config hash. Loading a
    # stopped configuration does not start the bot or its FreqAI retraining.
    return safe


def run_probe() -> dict:
    version = importlib.metadata.version("freqtrade")
    if version != EXPECTED_FREQTRADE:
        raise AssertionError(f"FREQTRADE_VERSION_MISMATCH:{version}")

    raw = json.loads(CONFIG_PATH.read_text(encoding="utf8"))
    metadata = json.loads(METADATA_PATH.read_text(encoding="utf8"))

    # Resolve the same config object that Freqtrade exposes as self.config.
    # The loader parses a stopped copy only; no bot, strategy, exchange, or
    # retraining lifecycle is started. Keep FreqAI settings intact because
    # they are part of the historical snapshot hash.
    from freqtrade.configuration import Configuration
    with tempfile.TemporaryDirectory(prefix="r22-config-") as temp:
        safe_path = Path(temp) / "config.json"
        safe_path.write_text(json.dumps(build_runtime_config(raw)), encoding="utf8")
        loaded = Configuration.from_files(["--config", str(safe_path)])
        loaded_config = loaded.get_config()
        if loaded_config.get("dry_run") is not True:
            raise AssertionError("PHASE22_RUNTIME_CONFIG_NOT_DRY_RUN")
        if loaded_config.get("force_entry_enable") is not False:
            raise AssertionError("PHASE22_RUNTIME_ENTRY_OVERRIDE_ENABLED")

    # Historical ChartProAuditLightGBMRegressor._capture_phase13b_predict()
    # hashes this exact five-field snapshot derived from self.config.
    snapshot = runtime_config_snapshot(loaded_config)
    config_sha = canonical_sha(snapshot)
    freqai_sha = canonical_sha(snapshot["freqai"])
    if config_sha != metadata["config_sha256"] or freqai_sha != metadata["freqai_config_sha256"]:
        raise AssertionError("PHASE22_EFFECTIVE_CONFIG_HASH_MISMATCH")

    # Import the actual strategy against the pinned Freqtrade runtime and
    # execute only its pure feature-engineering methods on synthetic candles.
    from freqai_bridge.ChartProFreqaiResearch import ChartProFreqaiResearch
    strategy = object.__new__(ChartProFreqaiResearch)
    frame = pd.DataFrame({
        "date": pd.date_range("2026-01-01", periods=96, freq="15min", tz="UTC"),
        "close": [100.0 + i for i in range(96)],
        "volume": [10.0 + (i % 7) for i in range(96)],
    })
    for period in raw["freqai"]["feature_parameters"]["indicator_periods_candles"]:
        frame = strategy.feature_engineering_expand_all(frame, period, {})
    frame = strategy.feature_engineering_expand_basic(frame, {})
    frame = strategy.feature_engineering_standard(frame, {})
    base_columns = [c for c in frame.columns if c.startswith("%-")]
    required_base = {
        "%-relative-price", "%-relative-volume", "%-pct-change",
        "%-raw-volume", "%-day-of-week", "%-hour-of-day",
    }
    if not required_base.issubset(base_columns):
        raise AssertionError("PHASE22_STRATEGY_FEATURE_METHODS_MISMATCH")

    fp = raw["freqai"]["feature_parameters"]
    expanded = expected_expanded_features(
        "BTC/USDT:USDT", raw["timeframe"],
        fp["indicator_periods_candles"], fp["include_shifted_candles"])
    frozen = metadata["ordered_feature_columns"]
    if expanded != frozen or len(set(expanded)) != 20:
        raise AssertionError("PHASE22_ORDERED_FEATURE_SCHEMA_MISMATCH")

    return {
        "status": "PASS",
        "freqtrade_version": version,
        "effective_config_sha256": config_sha,
        "freqai_config_sha256": freqai_sha,
        "feature_count": len(expanded),
        "feature_schema_match": True,
        "runtime_config_loader": "PASS",
        "strategy_feature_methods": "PASS_SYNTHETIC_ONLY",
        "exchange_network_calls": 0,
        "strategy_started": False,
        "backtest_started": False,
        "training_started": False,
        "retraining_started": False,
        "live_orders_enabled": False,
        "oos_certified": False,
    }


if __name__ == "__main__":
    print(json.dumps(run_probe(), sort_keys=True, indent=2))
