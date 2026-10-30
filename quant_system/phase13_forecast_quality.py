"""Phase13: real FreqAI four-M15 return forecast quality (retrospective only).

Bind each accepted prediction to its observed Phase8 native model fingerprint,
check its training label cutoff, then compare to canonical future close.
No label/forecast at the final history edge is invented. This is NOT a
statistically independent holdout: historic reports have been inspected.
"""
from __future__ import annotations
import argparse
import csv
import json
import math
import statistics
from pathlib import Path

from quant_system.phase13_oos_stability import (
    WINDOW, M15_MS, Phase13Error, load_json, read_equity, require, sha
)

def csv_rows(path, required):
    with Path(path).open(newline="", encoding="utf8") as f:
        rows = csv.DictReader(f)
        require(rows.fieldnames is not None and
                set(required).issubset(rows.fieldnames),
                "PHASE13_FORECAST_CSV_COLUMNS_MISSING")
        for row in rows:
            require(None not in row and all(v is not None for v in row.values()),
                    "PHASE13_FORECAST_CSV_MALFORMED")
            yield row

def timestamp(value):
    try:
        v = int(value)
        require(v > 0 and v % M15_MS == 0 and str(v) == str(value),
                "PHASE13_INVALID_FORECAST_TIMESTAMP")
        return v
    except (TypeError, ValueError, OverflowError) as exc:
        raise Phase13Error("PHASE13_INVALID_FORECAST_TIMESTAMP") from exc

def finite(value):
    try:
        f = float(value)
        require(math.isfinite(f), "PHASE13_FORECAST_NONFINITE")
        return f
    except (TypeError, ValueError, OverflowError) as exc:
        raise Phase13Error("PHASE13_FORECAST_NONFINITE") from exc

def segment_metrics(rows, segment):
    size = len(rows)
    require(size >= 100, "PHASE13_TOO_FEW_FORECASTS_IN_SEGMENT")
    predictions = [p for p, _ in rows]
    labels = [r for _, r in rows]
    accuracy = sum((p > 0) == (r > 0) for p, r in rows) / size
    try:
        ic = statistics.correlation(predictions, labels)
        if not math.isfinite(ic):
            ic = None
    except statistics.StatisticsError:
        ic = None
    return dict(segment=segment, compared_forecasts=size,
        direction_accuracy_pct=round(100 * accuracy, 6),
        mae_return=round(sum(abs(p - r) for p, r in rows)/size, 10),
        rmse_return=round(math.sqrt(
            sum((p-r)**2 for p, r in rows)/size), 10),
        prediction_actual_pearson=round(ic, 6) if ic is not None else None,
        realized_up_fraction_pct=round(
            100 * sum(r > 0 for r in labels)/size, 6),
    )

def inspect_forecasts(artifacts_root):
    result = dict(schemaVersion=1,
        audit="PHASE13_NATIVE_FORECAST_4C_QUALITY",
        retrospective_forecast_quality_verified=False,
        temporal_training_before_prediction_verified=False,
        independent_oos_verified=False,
        oos_certified=False,
        ai_promotion_eligible=False,
        ready_for_360=False,
        live_orders_enabled=False,
        blockers=["HISTORICAL_RESEARCH_NOT_UNTOUCHED_INDEPENDENT_HOLDOUT",
                  "FEATURE_PIPELINE_CAUSALITY_NOT_YET_CERTIFIED"],
        errors=[])
    try:
        root = Path(artifacts_root)
        phase12 = load_json(root / "paper/phase12-native-fit-label-audit.json")
        native = load_json(root / "native/native-research-180.json")
        phase8 = load_json(root / "paper/phase8-native-model-evidence.json")
        require(phase8.get("native_model_lineage_verified") is True and
                phase8.get("errors") == [] and
                isinstance(phase8.get("evidence_sha256"), dict),
                "PHASE13_PHASE8_MODEL_LINK_NOT_VERIFIED")
        require(phase12.get("train_test_label_purge_verified") is True and
                phase12.get("actual_fit_sample_lineage_verified") is True and
                phase12.get("errors") == [],
                "PHASE13_PHASE12_NOT_VERIFIED")
        pred_path = root / "native/freqai-native-predictions.csv"
        lineage_path = root / "native/freqai-native-model-lineage.csv"
        candles_path = root / "canonical/15m.csv"
        require(sha(pred_path) == native.get("prediction_capture_sha256") ==
                    phase8["evidence_sha256"].get("predictions") and
                sha(lineage_path) == native.get("phase8_model_lineage_sha256") ==
                    phase8["evidence_sha256"].get("lineage") and
                sha(candles_path) == phase12.get("canonical_m15_sha256"),
                "PHASE13_FORECAST_EVIDENCE_SHA_MISMATCH")
        candles = {}
        for row in csv_rows(candles_path, ("open_time", "close", "closed")):
            t = timestamp(row["open_time"])
            require(t not in candles and row["closed"] in ("1", "True", "true"),
                    "PHASE13_CANONICAL_CANDLE_DUPLICATE_OR_OPEN")
            candles[t] = finite(row["close"])
            require(candles[t] > 0, "PHASE13_CANONICAL_PRICE_NONPOSITIVE")
        start = read_equity(root / "paper/portfolio-dual-equity.csv")[0][0] - M15_MS
        stop = start + 6 * WINDOW * M15_MS
        models = {}
        for row in csv_rows(lineage_path,
                ("open_time", "model_sha256", "training_end_ms",
                 "latest_observed_label_end_ms", "model_identifier",
                 "configured_label_horizon_candles", "do_predict")):
            t = timestamp(row["open_time"])
            require(t not in models and row["model_sha256"].startswith("sha256:")
                    and len(row["model_sha256"]) == 71,
                    "PHASE13_DUPLICATE_OR_INVALID_MODEL_FINGERPRINT")
            models[t] = row
        require(bool(models), "PHASE13_NO_NATIVE_MODEL_LINEAGE")
        groups = [[] for _ in range(6)]
        accepted = unlabeled = 0
        seen = set()
        for row in csv_rows(pred_path,
                ("open_time", "close", "predicted_return", "do_predict",
                 "model_identifier", "source", "pair")):
            t = timestamp(row["open_time"])
            require(t not in seen, "PHASE13_DUPLICATE_FORECAST")
            seen.add(t)
            require(row["source"] == "freqai-native-backtest" and
                    row["pair"] == "BTC/USDT:USDT" and
                    row["model_identifier"] == native.get("prediction_model_identifier"),
                    "PHASE13_UNVERIFIED_FORECAST_SOURCE")
            if row["do_predict"] != "1":
                require(row["do_predict"] in ("0", "-1", "-2") and
                        not row["predicted_return"],
                        "PHASE13_INVALID_ABSTENTION")
                continue
            accepted += 1
            require(t in models, "PHASE13_UNLINKED_ACCEPTED_FORECAST")
            m = models[t]
            require(m["do_predict"] == "1" and
                    m["model_identifier"] == row["model_identifier"] and
                    m["configured_label_horizon_candles"] == "4" and
                    timestamp(m["latest_observed_label_end_ms"]) <
                    timestamp(m["training_end_ms"]) <= t,
                    "PHASE13_NONCAUSAL_MODEL_TRAINING_TIME")
            require(start <= t < stop,
                    "PHASE13_ACCEPTED_FORECAST_OUTSIDE_PAPER_WINDOW")
            require(t in candles and
                    math.isclose(candles[t], finite(row["close"]),
                                 rel_tol=1e-10, abs_tol=1e-9),
                    "PHASE13_PREDICTION_PRICE_MISMATCH")
            predicted = finite(row["predicted_return"])
            require(-1 <= predicted <= 1,
                    "PHASE13_FORECAST_RETURN_OUT_OF_BOUNDS")
            future_t = t + 4 * M15_MS
            if future_t not in candles:
                # Right edge: exclude, NEVER manufacture target.
                require(future_t > max(candles),
                        "PHASE13_INTERNAL_FUTURE_CANDLE_MISSING")
                unlabeled += 1
                continue
            label = candles[future_t] / candles[t] - 1
            groups[(t-start)//(WINDOW*M15_MS)].append((predicted, label))
        require(accepted == native.get("prediction_capture_accepted"),
                "PHASE13_NATIVE_ACCEPTED_FORECAST_COUNT_MISMATCH")
        scores = [segment_metrics(g, i+1) for i, g in enumerate(groups)]
        total = sum(len(group) for group in groups)
        correct = sum(sum((p>0) == (y>0) for p,y in group) for group in groups)
        require(accepted == total+unlabeled,
                "PHASE13_FORECAST_LABEL_ACCOUNTING_MISMATCH")
        result.update(retrospective_forecast_quality_verified=True,
            temporal_training_before_prediction_verified=True,
            accepted_forecasts=accepted,
            labeled_forecasts=total,
            right_edge_unlabeled_forecasts=unlabeled,
            overall_direction_accuracy_pct=round(100*correct/total, 6),
            segments=scores,
            prediction_sha256=sha(pred_path),
            lineage_sha256=sha(lineage_path),
            canonical_sha256=sha(candles_path))
    except Phase13Error as exc:
        result["errors"].append(str(exc))
    except (OSError, ValueError, TypeError, KeyError, csv.Error,
            ZeroDivisionError, OverflowError, UnicodeError) as exc:
        result["errors"].append("PHASE13_FORECAST_EVIDENCE_INVALID")
        result["error_type"] = type(exc).__name__
    return result

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifacts-root", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    result = inspect_forecasts(args.artifacts_root)
    target = Path(args.out)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, indent=2, sort_keys=True,
                                 allow_nan=False)+"\n", encoding="utf8")
    print(json.dumps({k: result[k] for k in
        ("retrospective_forecast_quality_verified", "accepted_forecasts",
         "independent_oos_verified", "errors") if k in result}, sort_keys=True))
    return 0 if result["retrospective_forecast_quality_verified"] and not result["errors"] else 2

if __name__ == "__main__":
    raise SystemExit(main())
