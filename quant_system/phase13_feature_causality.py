"""Phase13 observed strategy-feature prefix invariance on genuine closed OKX M15.

Runs the actual ChartProFreqaiResearch feature methods for both configured
periods and every positive shifted input. It does NOT equate this source-level
test with certified upstream DataSieve/model preprocessing or independent OOS.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path

PERIODS = (14, 28)
SHIFTS = (1, 2)
EXPECTED = {
    "%-relative-price_14", "%-relative-volume_14",
    "%-relative-price_28", "%-relative-volume_28",
    "%-pct-change_gen", "%-raw-volume_gen",
    "%-day-of-week", "%-hour-of-day",
}
M15 = 900000

class FeatureCausalityError(ValueError):
    pass

def require(value, code):
    if not value:
        raise FeatureCausalityError(code)

def digest(path):
    return "sha256:" + hashlib.sha256(Path(path).read_bytes()).hexdigest()

def feature_matrix(frame, strategy):
    """Re-execute precisely the configured strategy feature methods."""
    features = {}
    pair = {"pair": "BTC/USDT:USDT", "tf": "15m"}
    for period in PERIODS:
        generated = strategy.feature_engineering_expand_all(
            frame.copy(), period=period, metadata=pair
        )
        names = [col for col in generated if col.startswith("%")]
        require(set(names) == {"%-relative-price", "%-relative-volume"},
                "PHASE13_UNKNOWN_EXPANDED_FEATURE")
        for name in names:
            features[name + "_" + str(period)] = generated[name]
    generic = strategy.feature_engineering_expand_basic(frame.copy(), metadata=pair)
    names = [col for col in generic if col.startswith("%")]
    require(set(names) == {"%-pct-change", "%-raw-volume"},
            "PHASE13_UNKNOWN_GENERIC_FEATURE")
    for name in names:
        features[name + "_gen"] = generic[name]
    # FreqAI 2026.9 includes two positive-shifted feature copies for 15m.
    base = dict(features)
    for offset in SHIFTS:
        for name, series in base.items():
            features[name + "_shift-" + str(offset)] = series.shift(offset)
    standard = strategy.feature_engineering_standard(frame.copy(), metadata=pair)
    names = [col for col in standard if col.startswith("%")]
    require(set(names) == {"%-day-of-week", "%-hour-of-day"},
            "PHASE13_UNKNOWN_STANDARD_FEATURE")
    for name in names:
        features[name] = standard[name]
    actual = set(features)
    expected = EXPECTED | {
        name + "_shift-" + str(offset)
        for name in EXPECTED
        if name not in {"%-day-of-week", "%-hour-of-day"}
        for offset in SHIFTS
    }
    require(actual == expected and len(features) == 20,
            "PHASE13_FEATURE_INVENTORY_MISMATCH")
    # Build feature-only frame: no targets beginning with '&' can enter it.
    import pandas as pd
    return pd.DataFrame(features, index=frame.index)

def canonical_frame(path):
    import pandas as pd
    raw = pd.read_csv(path)
    require(set(("open_time", "open", "high", "low", "close", "volume", "closed"))
            .issubset(raw.columns) and len(raw) >= 1000,
            "PHASE13_CANONICAL_M15_INVALID")
    require(raw["closed"].isin((1, True)).all(),
            "PHASE13_OPEN_CANDLE_IN_FEATURE_SOURCE")
    ms = raw["open_time"].to_numpy()
    require(bool((ms[1:] - ms[:-1] == M15).all()) and
            bool((ms % M15 == 0).all()),
            "PHASE13_GAPPED_OR_DUPLICATE_CANDLES")
    for column in ("open", "high", "low", "close", "volume"):
        values = raw[column].to_numpy()
        require(bool(pd.notna(values).all()) and
                all(math.isfinite(float(x)) for x in values),
                "PHASE13_INVALID_PRICE_OR_VOLUME")
    require(bool((raw["close"] > 0).all()) and
            bool((raw["volume"] >= 0).all()),
            "PHASE13_INVALID_CLOSE_VOLUME")
    raw["date"] = pd.to_datetime(raw["open_time"], unit="ms", utc=True)
    return raw

def inspect_features(canonical_path, config_path, strategy_class):
    report = dict(schemaVersion=1,
        feature_source_prefix_invariance_verified=False,
        feature_inventory_verified=False,
        full_model_pipeline_causality_verified=False,
        independent_oos_verified=False,
        oos_certified=False,
        ai_promotion_eligible=False,
        ready_for_360=False,
        live_orders_enabled=False,
        errors=[],
        blockers=[
            "ACTUAL_FITTED_FEATURE_COLUMN_PROVENANCE_NOT_YET_ATTESTED",
            "DATA_PIPELINE_AND_SCALER_CAUSALITY_NOT_INDEPENDENTLY_ATTESTED",
            "INDEPENDENT_PROSPECTIVE_HOLDOUT_NOT_PROVEN",
        ],
    )
    try:
        settings = json.loads(Path(config_path).read_text(encoding="utf8"))
        feat = settings["freqai"]["feature_parameters"]
        require(settings["dry_run"] is True and
                settings["force_entry_enable"] is False and
                settings["timeframe"] == "15m" and
                settings["exchange"]["name"] == "okx" and
                feat["indicator_periods_candles"] == list(PERIODS) and
                feat["include_shifted_candles"] == len(SHIFTS) and
                feat["include_timeframes"] == ["15m"] and
                feat["include_corr_pairlist"] == [] and
                feat["label_period_candles"] == 4 and
                settings["freqai"]["data_split_parameters"] ==
                    {"test_size": 0.2, "shuffle": False},
                "PHASE13_UNAPPROVED_FEATURE_CONFIG")
        frame = canonical_frame(canonical_path)
        # Only known user-defined feature generation entrypoints may exist.
        methods = {name for name in dir(strategy_class)
                   if name.startswith("feature_engineering_")}
        require(methods == {
            "feature_engineering_expand_all",
            "feature_engineering_expand_basic",
            "feature_engineering_standard",
        }, "PHASE13_UNREVIEWED_FEATURE_METHOD")
        whole = feature_matrix(frame, strategy_class)
        require(not any(col.startswith("&") for col in whole.columns),
                "PHASE13_TARGET_IN_FEATURE_MATRIX")
        require(bool(whole.iloc[64:].notna().all().all()) and
                bool(whole.iloc[64:].apply(
                    lambda s: s.map(math.isfinite)).all().all()),
                "PHASE13_INVALID_FINITE_MODEL_FEATURE")
        # Check many interior / fold-like cut points, including late history.
        indexes = sorted(set(
            list(range(128, len(frame), 397)) +
            [len(frame) - i for i in (3, 28, 128, 2880)]
        ))
        checks = 0
        for length in indexes:
            if length <= 64 or length >= len(frame):
                continue
            prefix = feature_matrix(frame.iloc[:length].copy(), strategy_class)
            # The most recent CLOSED candle is the one that could be altered
            # by a future-dependent expression (shift(-k), centered rolling).
            for column in whole.columns:
                observed = float(prefix[column].iloc[-1])
                expected = float(whole[column].iloc[length - 1])
                require(math.isfinite(observed) and math.isfinite(expected) and
                        math.isclose(observed, expected,
                                     rel_tol=1e-11, abs_tol=1e-11),
                        "PHASE13_FUTURE_DEPENDENT_FEATURE:" + column)
                checks += 1
        require(checks >= 20 * 20,
                "PHASE13_INSUFFICIENT_PREFIX_INTERVENTIONS")
        report.update(feature_source_prefix_invariance_verified=True,
            feature_inventory_verified=True,
            audited_feature_columns=list(whole.columns),
            audited_feature_column_count=len(whole.columns),
            prefix_intervention_comparisons=checks,
            first_candle_open_ms=int(frame["open_time"].iloc[0]),
            last_candle_open_ms=int(frame["open_time"].iloc[-1]),
            canonical_m15_sha256=digest(canonical_path),
            config_sha256=digest(config_path))
    except FeatureCausalityError as exc:
        report["errors"].append(str(exc))
    except (OSError, UnicodeError, ValueError, KeyError, TypeError,
            OverflowError, ImportError, AttributeError) as exc:
        report["errors"].append("PHASE13_FEATURE_AUDIT_FAILED")
        report["error_type"] = type(exc).__name__
    return report

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--canonical", required=True)
    parser.add_argument("--config", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    from freqai_bridge.ChartProFreqaiResearch import ChartProFreqaiResearch
    report = inspect_features(args.canonical, args.config, ChartProFreqaiResearch)
    path = Path(args.out)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False)
                    + "\n", encoding="utf8")
    print(json.dumps({k: report[k] for k in
        ("feature_source_prefix_invariance_verified",
         "feature_inventory_verified", "full_model_pipeline_causality_verified",
         "errors", "ready_for_360")}, sort_keys=True))
    return 0 if report["feature_source_prefix_invariance_verified"] and not report["errors"] else 2

if __name__ == "__main__":
    raise SystemExit(main())
