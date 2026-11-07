"""R22.6: replay native FreqAI feature construction on sealed historical candles.

Only the canonical M15 CSV is read from the verified Phase14 ZIP. The joblib
member is never opened, extracted, loaded, or unpickled.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import tempfile
import zipfile
from pathlib import Path, PurePosixPath

import numpy as np
import pandas as pd

EXPECTED_ARCHIVE_SHA256 = "b64f39bd70c27c8d6abed1795ee06504c108eed42ebdab98ce375a6449b5b035"
EXPECTED_ARCHIVE_GIT_BLOB_SHA1 = "17ec47fcbab047a540b1b1d2faad6a73182b5ab5"
EXPECTED_SOURCE_COMMIT = "082edc082996425f61f48c952be41fb037564103"
EXPECTED_CONFIG_SHA256 = "c253091852b704c00fa33bd6fceb69fb4d480630da1645e3e35ebea13888bb72"
EXPECTED_FREQAI_CONFIG_SHA256 = "a716c80fbb78b8d4bc8b436136912e93e6988a8cdf8d7d1945e8f512bcd6d852"
EXPECTED_BUNDLE_SHA256 = "918dc4737ee432df8f7f9d2c3e561ac3983aaf56d8791a731a55624ab836b81f"
PAIR = "BTC/USDT:USDT"


class FeatureReplayError(ValueError):
    pass


def require(condition: bool, code: str) -> None:
    if not condition:
        raise FeatureReplayError(code)


def normalize_registered_sha256(value: str) -> str:
    """Normalize metadata SHA-256 values with or without the sha256: prefix."""
    if not isinstance(value, str):
        raise FeatureReplayError("INVALID_REGISTERED_SHA256")
    digest = value[7:] if value.startswith("sha256:") else value
    if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
        raise FeatureReplayError("INVALID_REGISTERED_SHA256")
    return digest


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git_blob_sha1(path: Path) -> str:
    digest = hashlib.sha1()
    digest.update(f"blob {path.stat().st_size}\0".encode("ascii"))
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_runtime_feature_matrix(
    config: dict,
    strategy,
    candles: pd.DataFrame,
    pair: str,
) -> pd.DataFrame:
    """Execute Freqtrade 2026.9 DataKitchen on the supplied closed candles."""
    from freqtrade.freqai.data_kitchen import FreqaiDataKitchen

    required = ["date", "open", "high", "low", "close", "volume"]
    require(set(required).issubset(candles.columns), "INVALID_FEATURE_INPUT_COLUMNS")
    kitchen = object.__new__(FreqaiDataKitchen)
    kitchen.config = config
    kitchen.freqai_config = config["freqai"]
    base_dataframes = {config["timeframe"]: candles[required].copy()}
    populated = kitchen.populate_features(
        candles[required].copy(),
        pair,
        strategy,
        corr_dataframes={},
        base_dataframes=base_dataframes,
    )
    populated = strategy.feature_engineering_standard(
        populated.copy(),
        metadata={"pair": pair},
    )
    populated = kitchen.remove_special_chars_from_feature_names(populated)
    columns = [column for column in populated.columns if column.startswith("%")]
    require(len(columns) == 20 and len(set(columns)) == 20,
            "NATIVE_DATAKITCHEN_FEATURE_INVENTORY_MISMATCH")
    return populated.loc[:, columns].reset_index(drop=True)


def build_manual_feature_matrix(
    candles: pd.DataFrame,
    strategy_class,
    pair: str,
) -> pd.DataFrame:
    """Rebuild the original Phase13/15 strategy-only feature matrix."""
    from quant_system.phase13_feature_causality import feature_matrix

    manual = feature_matrix(candles.copy(), strategy_class)
    suffix = pair.replace(":", "") + "_15m"
    manual = manual.rename(columns={
        column: column if column in ("%-day-of-week", "%-hour-of-day")
        else column + "_" + suffix
        for column in manual.columns
    })
    return manual.reset_index(drop=True)


def compare_feature_matrices(
    actual: pd.DataFrame,
    manual: pd.DataFrame,
    expected_columns: list[str],
) -> dict:
    if list(actual.columns) != list(expected_columns):
        raise FeatureReplayError("NATIVE_FEATURE_COLUMN_ORDER_MISMATCH")
    if list(manual.columns) != list(expected_columns):
        raise FeatureReplayError("MANUAL_FEATURE_COLUMN_ORDER_MISMATCH")
    if len(actual) != len(manual):
        raise FeatureReplayError("FEATURE_MATRIX_ROW_COUNT_MISMATCH")

    left = actual.to_numpy(dtype=np.float64)
    right = manual.to_numpy(dtype=np.float64)
    left_nan = np.isnan(left)
    right_nan = np.isnan(right)
    if not np.array_equal(left_nan, right_nan):
        raise FeatureReplayError("FEATURE_MATRIX_NAN_MASK_MISMATCH")
    finite = ~left_nan
    if not np.isfinite(left[finite]).all() or not np.isfinite(right[finite]).all():
        raise FeatureReplayError("FEATURE_MATRIX_NONFINITE_VALUE")
    if not np.allclose(left[finite], right[finite], rtol=1e-11, atol=1e-11):
        difference = np.abs(left[finite] - right[finite])
        raise FeatureReplayError(
            "FEATURE_MATRIX_VALUE_MISMATCH:max_abs_diff=" + format(float(difference.max()), ".12g")
        )
    return {
        "all_values_match": True,
        "row_count": len(actual),
        "feature_count": len(expected_columns),
        "finite_value_comparisons": int(finite.sum()),
        "max_abs_difference": float(np.max(np.abs(left[finite] - right[finite]))) if finite.any() else 0.0,
    }


def verify_prefix_invariance(
    config: dict,
    strategy,
    candles: pd.DataFrame,
    pair: str,
    *,
    cut_points: list[int],
) -> dict:
    full = build_runtime_feature_matrix(config, strategy, candles, pair)
    comparisons = 0
    for length in cut_points:
        require(64 < length < len(candles), "INVALID_PREFIX_CUT")
        prefix = build_runtime_feature_matrix(
            config, strategy, candles.iloc[:length].copy(), pair
        )
        require(len(prefix) == length and len(full) == len(candles),
                "PREFIX_FEATURE_ROW_ALIGNMENT_MISMATCH")
        left = prefix.iloc[-1].to_numpy(dtype=np.float64)
        right = full.iloc[length - 1].to_numpy(dtype=np.float64)
        if not np.array_equal(np.isnan(left), np.isnan(right)):
            raise FeatureReplayError("FUTURE_SUFFIX_CHANGED_FEATURE_NAN_MASK")
        finite = np.isfinite(left) & np.isfinite(right)
        require(bool(np.isfinite(left[finite]).all()) and
                bool(np.isfinite(right[finite]).all()),
                "PREFIX_FEATURE_NONFINITE_VALUE")
        if not np.allclose(left[finite], right[finite], rtol=1e-11, atol=1e-11):
            raise FeatureReplayError("FUTURE_SUFFIX_CHANGED_HISTORICAL_FEATURE")
        comparisons += len(full.columns)
    return {
        "prefix_invariance_verified": True,
        "prefix_cut_count": len(cut_points),
        "feature_comparisons": comparisons,
    }


def _load_canonical_from_archive(archive_path: Path):
    from quant_system.phase13_feature_causality import canonical_frame

    archive_sha = _sha256_file(archive_path)
    require(archive_sha == EXPECTED_ARCHIVE_SHA256, "PHASE14_ARCHIVE_SHA256_MISMATCH")
    require(_git_blob_sha1(archive_path) == EXPECTED_ARCHIVE_GIT_BLOB_SHA1,
            "PHASE14_ARCHIVE_GIT_BLOB_SHA1_MISMATCH")

    with zipfile.ZipFile(archive_path, "r") as archive:
        matches = [
            info for info in archive.infolist()
            if not info.is_dir()
            and PurePosixPath(info.filename).parts[-2:] == ("canonical", "15m.csv")
        ]
        require(len(matches) == 1, "CANONICAL_M15_ARCHIVE_MEMBER_MISSING_OR_AMBIGUOUS")
        member = matches[0]
        require(member.file_size <= 64 * 1024 * 1024, "CANONICAL_M15_MEMBER_TOO_LARGE")
        with tempfile.NamedTemporaryFile(prefix="r22-6-canonical-", suffix=".csv", delete=False) as temp:
            temp_path = Path(temp.name)
            with archive.open(member, "r") as source:
                shutil.copyfileobj(source, temp)
    try:
        frame = canonical_frame(temp_path)
        canonical_sha = _sha256_file(temp_path)
    finally:
        temp_path.unlink(missing_ok=True)
    return frame, member.filename, canonical_sha, archive_sha


def _load_safe_freqai_config(config_path: Path) -> tuple[dict, dict]:
    from freqtrade.configuration import Configuration
    from quant_system.phase22_runtime_probe import (
        apply_freqtrade_schema_defaults,
        build_runtime_config,
        canonical_sha,
        runtime_config_snapshot,
    )

    raw = json.loads(config_path.read_text(encoding="utf8"))
    with tempfile.TemporaryDirectory(prefix="r22-6-userdata-") as temp:
        user_data = Path(temp) / "user_data"
        user_data.mkdir()
        safe_config_path = Path(temp) / "config.json"
        safe_config_path.write_text(
            json.dumps(build_runtime_config(raw, str(user_data))),
            encoding="utf8",
        )
        loaded = Configuration.from_files([str(safe_config_path)])
        loaded = apply_freqtrade_schema_defaults(loaded)
    snapshot = runtime_config_snapshot(loaded)
    require(canonical_sha(snapshot) == EXPECTED_CONFIG_SHA256,
            "R22_6_EFFECTIVE_CONFIG_HASH_MISMATCH")
    require(canonical_sha(snapshot["freqai"]) == EXPECTED_FREQAI_CONFIG_SHA256,
            "R22_6_FREQAI_CONFIG_HASH_MISMATCH")
    return loaded, {
        "effective_config_sha256": canonical_sha(snapshot),
        "freqai_config_sha256": canonical_sha(snapshot["freqai"]),
    }


def inspect_historical_features(
    archive_path: str | Path,
    config_path: str | Path,
    metadata_path: str | Path,
    output_path: str | Path,
) -> dict:
    from freqai_bridge.ChartProFreqaiResearch import ChartProFreqaiResearch
    from quant_system.phase13_feature_causality import prefix_cut_points

    result = {
        "schemaVersion": 1,
        "audit": "R22_6_NATIVE_FREQAI_DATKITCHEN_HISTORICAL_FEATURE_REPLAY",
        "native_datakitchen_feature_values_reconciled": False,
        "feature_source_prefix_invariance_verified": False,
        "full_model_pipeline_causality_verified": False,
        "independent_oos_verified": False,
        "oos_certified": False,
        "live_orders_enabled": False,
        "strategy_started": False,
        "backtest_started": False,
        "training_started": False,
        "retraining_started": False,
        "exchange_network_calls": 0,
        "joblib_loaded": False,
        "errors": [],
    }
    try:
        archive_path = Path(archive_path)
        config_path = Path(config_path)
        metadata_path = Path(metadata_path)
        metadata = json.loads(metadata_path.read_text(encoding="utf8"))
        require(metadata.get("source_commit_sha") == EXPECTED_SOURCE_COMMIT,
                "FROZEN_SOURCE_COMMIT_MISMATCH")
        candidate_sha = normalize_registered_sha256(metadata.get("candidate_sha256"))
        require(candidate_sha == EXPECTED_BUNDLE_SHA256,
                "FROZEN_CANDIDATE_SHA_MISMATCH")
        expected_columns = metadata.get("ordered_feature_columns")
        require(isinstance(expected_columns, list) and len(expected_columns) == 20,
                "FROZEN_FEATURE_SCHEMA_INVALID")

        frame, member_path, canonical_sha, archive_sha = _load_canonical_from_archive(
            archive_path
        )
        config, config_hashes = _load_safe_freqai_config(config_path)
        candles = frame[["date", "open", "high", "low", "close", "volume"]].copy()
        strategy = object.__new__(ChartProFreqaiResearch)

        actual = build_runtime_feature_matrix(config, strategy, candles, PAIR)
        manual = build_manual_feature_matrix(candles, ChartProFreqaiResearch, PAIR)
        comparison = compare_feature_matrices(actual, manual, expected_columns)
        cuts = prefix_cut_points(len(candles))
        prefix = verify_prefix_invariance(
            config, strategy, candles, PAIR, cut_points=cuts
        )

        result.update({
            "native_datakitchen_feature_values_reconciled": True,
            "feature_source_prefix_invariance_verified": True,
            "canonical_archive_member": member_path,
            "canonical_m15_sha256": canonical_sha,
            "canonical_m15_rows": len(candles),
            "first_candle_open_utc": frame["date"].iloc[0].isoformat(),
            "last_candle_open_utc": frame["date"].iloc[-1].isoformat(),
            "archive_sha256": archive_sha,
            "source_commit_sha": metadata["source_commit_sha"],
            "candidate_sha256": candidate_sha,
            **config_hashes,
            **comparison,
            **prefix,
            "feature_schema_source": "FreqaiDataKitchen.populate_features+ChartProFreqaiResearch+Freqtrade.remove_special_chars_from_feature_names",
            "oos_candles_read": False,
            "archive_extracted": False,
            "canonical_csv_temp_file_used": True,
        })
    except Exception as exc:
        result["errors"].append(
            str(exc) if isinstance(exc, FeatureReplayError) else
            "R22_6_HISTORICAL_FEATURE_REPLAY_FAILED:" + type(exc).__name__
        )

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf8",
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", required=True)
    parser.add_argument("--config", required=True)
    parser.add_argument("--metadata", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    result = inspect_historical_features(
        args.archive, args.config, args.metadata, args.out
    )
    print(json.dumps({
        "native_datakitchen_feature_values_reconciled":
            result["native_datakitchen_feature_values_reconciled"],
        "feature_source_prefix_invariance_verified":
            result["feature_source_prefix_invariance_verified"],
        "canonical_m15_rows": result.get("canonical_m15_rows"),
        "prefix_cut_count": result.get("prefix_cut_count"),
        "errors": result["errors"],
        "full_model_pipeline_causality_verified":
            result["full_model_pipeline_causality_verified"],
    }, sort_keys=True))
    return 0 if (
        result["native_datakitchen_feature_values_reconciled"]
        and result["feature_source_prefix_invariance_verified"]
        and not result["errors"]
    ) else 2


if __name__ == "__main__":
    raise SystemExit(main())
