"""R22.2 isolated, non-executing Freqtrade/FreqAI runtime compatibility probe."""
from __future__ import annotations

import hashlib
import importlib.metadata
import json
import tempfile
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def ensure_repository_root_on_sys_path() -> str:
    """Make repository packages importable when this file is run as a script."""
    root = str(ROOT)
    if root not in sys.path:
        sys.path.insert(0, root)
    return root


ensure_repository_root_on_sys_path()

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


def _diff_paths(left, right, prefix="") -> list[str]:
    """Return deterministic paths whose values differ, without exposing values."""
    if isinstance(left, dict) and isinstance(right, dict):
        paths = []
        for key in sorted(set(left) | set(right)):
            path = f"{prefix}.{key}" if prefix else str(key)
            if key not in left or key not in right:
                paths.append(path)
            else:
                paths.extend(_diff_paths(left[key], right[key], path))
        return paths
    if isinstance(left, list) and isinstance(right, list):
        return [] if left == right else [prefix or "$"]
    return [] if type(left) is type(right) and left == right else [prefix or "$"]


def config_hash_diagnostics(
    snapshot: dict,
    raw_snapshot: dict,
    *,
    expected_config_sha256: str,
    expected_freqai_sha256: str,
) -> dict:
    """Summarize hash provenance and raw-to-resolved changes without values."""
    return {
        "expected_config_sha256": expected_config_sha256,
        "actual_config_sha256": canonical_sha(snapshot),
        "expected_freqai_config_sha256": expected_freqai_sha256,
        "actual_freqai_config_sha256": canonical_sha(snapshot["freqai"]),
        "raw_freqai_config_sha256": canonical_sha(raw_snapshot["freqai"]),
        "runtime_vs_raw_diff_paths": _diff_paths(raw_snapshot, snapshot),
    }


def build_runtime_feature_columns(
    config: dict,
    strategy,
    candles: pd.DataFrame,
    pair: str,
) -> list[str]:
    """Run pinned FreqAI DataKitchen expansion on local synthetic candles only."""
    from freqtrade.freqai.data_kitchen import FreqaiDataKitchen

    kitchen = object.__new__(FreqaiDataKitchen)
    kitchen.config = config
    kitchen.freqai_config = config["freqai"]
    base_dataframes = {config["timeframe"]: candles.copy()}
    populated = kitchen.populate_features(
        candles.copy(),
        pair,
        strategy,
        corr_dataframes={},
        base_dataframes=base_dataframes,
    )
    populated = strategy.feature_engineering_standard(
        populated.copy(),
        metadata={"pair": pair},
    )
    return [column for column in populated.columns if column.startswith("%")]


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


def apply_freqtrade_schema_defaults(config: dict) -> dict:
    """Apply the pinned Freqtrade config-schema defaults without starting a bot.

    Configuration.from_files() loads and normalizes files but does not execute
    validate_config_schema(). FreqtradeBot reaches that validator through
    validate_config_consistency() after strategy resolution. The validator
    recursively inserts declared defaults into nested FreqAI configuration,
    which is part of the historical post-validation config snapshot.
    """
    from freqtrade.configuration.config_validation import validate_config_schema

    validate_config_schema(config)
    return config


def build_runtime_config(raw: dict, user_data_dir: str) -> dict:
    """Prevent bot startup while preserving the frozen FreqAI configuration."""
    safe = json.loads(json.dumps(raw))
    safe["initial_state"] = "stopped"
    safe["user_data_dir"] = user_data_dir
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
        isolated_user_data = Path(temp) / "user_data"
        isolated_user_data.mkdir()
        safe_path.write_text(
            json.dumps(build_runtime_config(raw, str(isolated_user_data))), encoding="utf8"
        )
        loaded_config = Configuration.from_files([str(safe_path)])
        loaded_config = apply_freqtrade_schema_defaults(loaded_config)
        if loaded_config.get("dry_run") is not True:
            raise AssertionError("PHASE22_RUNTIME_CONFIG_NOT_DRY_RUN")
        if loaded_config.get("force_entry_enable") is not False:
            raise AssertionError("PHASE22_RUNTIME_ENTRY_OVERRIDE_ENABLED")

    # Historical ChartProAuditLightGBMRegressor._capture_phase13b_predict()
    # hashes this exact five-field snapshot derived from self.config.
    snapshot = runtime_config_snapshot(loaded_config)
    diagnostics = config_hash_diagnostics(
        snapshot,
        runtime_config_snapshot(raw),
        expected_config_sha256=metadata["config_sha256"],
        expected_freqai_sha256=metadata["freqai_config_sha256"],
    )
    if (
        diagnostics["actual_config_sha256"] != diagnostics["expected_config_sha256"]
        or diagnostics["actual_freqai_config_sha256"]
        != diagnostics["expected_freqai_config_sha256"]
    ):
        print(
            "PHASE22_CONFIG_HASH_DIAGNOSTICS="
            + json.dumps(diagnostics, sort_keys=True),
            file=sys.stderr,
        )
        raise AssertionError("PHASE22_EFFECTIVE_CONFIG_HASH_MISMATCH")
    config_sha = diagnostics["actual_config_sha256"]
    freqai_sha = diagnostics["actual_freqai_config_sha256"]

    # Import the actual strategy against the pinned Freqtrade runtime and
    # execute only its pure feature-engineering methods on synthetic candles.
    from freqai_bridge.ChartProFreqaiResearch import ChartProFreqaiResearch
    strategy = object.__new__(ChartProFreqaiResearch)
    candles = pd.DataFrame({
        "date": pd.date_range("2026-01-01", periods=96, freq="15min", tz="UTC"),
        "open": [99.5 + i for i in range(96)],
        "high": [101.0 + i for i in range(96)],
        "low": [99.0 + i for i in range(96)],
        "close": [100.0 + i for i in range(96)],
        "volume": [10.0 + (i % 7) for i in range(96)],
    })
    base_features = candles.copy()
    for period in raw["freqai"]["feature_parameters"]["indicator_periods_candles"]:
        base_features = strategy.feature_engineering_expand_all(base_features, period, {})
    base_features = strategy.feature_engineering_expand_basic(base_features, {})
    base_features = strategy.feature_engineering_standard(base_features, {})
    base_columns = [c for c in base_features.columns if c.startswith("%-")]
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
    runtime_features = build_runtime_feature_columns(
        loaded_config, strategy, candles, "BTC/USDT:USDT"
    )
    frozen = metadata["ordered_feature_columns"]
    if (
        runtime_features != expanded
        or expanded != frozen
        or len(set(runtime_features)) != 20
    ):
        raise AssertionError("PHASE22_ORDERED_FEATURE_SCHEMA_MISMATCH")

    return {
        "status": "PASS",
        "freqtrade_version": version,
        "effective_config_sha256": config_sha,
        "freqai_config_sha256": freqai_sha,
        "feature_count": len(runtime_features),
        "feature_schema_match": True,
        "feature_schema_source": "FreqaiDataKitchen.populate_features+strategy.feature_engineering_standard",
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
