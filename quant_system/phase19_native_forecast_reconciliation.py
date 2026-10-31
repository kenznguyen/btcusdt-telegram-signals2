"""Phase19: original native LAST-FOLD FreqAI forecast reconstruction.

Check all original SHA-pinned native LightGBM PREDICT X matrices, flags and
the native captured predicted-return trace against the fixed fitted model.
Historical only, no fit, retrain, OOS holdout access, orders or promotion.
"""
from __future__ import annotations
import argparse
import csv
import json
import math
from pathlib import Path

M15=900000
OOS_START=1793750400000
ORIGINAL_SOURCE_SHA="082edc082996425f61f48c952be41fb037564103"
ORIGINAL_BUNDLE_SHA="sha256:918dc4737ee432df8f7f9d2c3e561ac3983aaf56d8791a731a55624ab836b81f"
MODEL_ID="chart-pro-okx-shadow-v1"

class NativeForecastMismatch(ValueError):
    pass

def require(condition,code):
    if not condition:
        raise NativeForecastMismatch(code)

def numbers(values):
    try:
        output=[float(x) for x in values]
    except (ValueError,TypeError,OverflowError) as exc:
        raise NativeForecastMismatch("PHASE19_NATIVE_X_MISMATCH") from exc
    require(bool(output) and all(math.isfinite(x) for x in output),
            "PHASE19_NATIVE_X_MISMATCH")
    return output

def validate_native_timestamps(times,cutoff,holdout_start=OOS_START):
    require(type(cutoff) is int and type(holdout_start) is int and
            isinstance(times,list) and len(times)>0 and
            all(type(t) is int and t>0 and t%M15==0 for t in times),
            "PHASE19_INVALID_NATIVE_TIME")
    require(all(cutoff<=t<holdout_start for t in times),
            "PHASE19_HOLDOUT_OR_TRAINING_OVERLAP")
    require(all(b>a for a,b in zip(times,times[1:])),
            "PHASE19_DUPLICATE_OR_REVERSED_TIME")
    return len(times)

def check_original_prediction_map(times,rows):
    """Require EXACT one captured original-native row per model matrix time."""
    lookup={}
    wanted=set(times)
    for record in rows:
        try:
            raw=record["open_time"]
            time=int(raw)
            require(str(time)==str(raw),"PHASE19_INVALID_NATIVE_TIME")
            require(time in wanted,"PHASE19_UNEXPECTED_NATIVE_PREDICTION")
            require(time not in lookup,"PHASE19_DUPLICATE_NATIVE_PREDICTION")
            lookup[time]=record
        except (TypeError,ValueError,KeyError,OverflowError) as exc:
            if isinstance(exc,NativeForecastMismatch):
                raise
            raise NativeForecastMismatch("PHASE19_INVALID_NATIVE_TIME") from exc
    require(set(lookup)==wanted,"PHASE19_MISSING_NATIVE_PREDICTION")
    return lookup

def verify_native_row(recomputed,native):
    """Compare reconstructed LightGBM input, accepted flag and inverse label."""
    require(isinstance(recomputed,dict) and isinstance(native,dict),
            "PHASE19_INVALID_ROW")
    require(native.get("source")=="freqai-native-backtest" and
            native.get("pair")=="BTC/USDT:USDT" and
            native.get("model_identifier")==MODEL_ID,
            "PHASE19_WRONG_NATIVE_PROVENANCE")
    expected=numbers(recomputed.get("x"))
    original=numbers(native.get("x"))
    require(len(expected)==len(original) and
            all(math.isclose(a,b,rel_tol=1e-9,abs_tol=1e-10)
                for a,b in zip(expected,original)),
            "PHASE19_NATIVE_X_MISMATCH")
    flag=recomputed.get("flag")
    require(type(flag) is int and flag in (-2,-1,0,1) and
            type(native.get("flag")) is int and native["flag"]==flag,
            "PHASE19_NATIVE_DO_PREDICT_MISMATCH")
    actual=recomputed.get("prediction")
    observed=native.get("predicted_return")
    if flag!=1:
        require(actual is None and observed in (None,""),
                "PHASE19_REJECTED_NATIVE_FORECAST_PRESENT")
    else:
        try:
            expected_y=float(actual)
            native_y=float(observed)
        except (TypeError,ValueError,OverflowError) as exc:
            raise NativeForecastMismatch("PHASE19_NATIVE_FORECAST_MISMATCH") from exc
        require(math.isfinite(expected_y) and math.isfinite(native_y) and
                math.isclose(expected_y,native_y,rel_tol=1e-7,abs_tol=1e-9),
                "PHASE19_NATIVE_FORECAST_MISMATCH")
    return True

def inspect(*,original_root,bundle,metadata,protocol,seal,output):
    report=dict(schemaVersion=1,
                audit="PHASE19_ORIGINAL_LAST_FOLD_NATIVE_PREDICTION_RECONCILIATION",
                original_last_fold_native_predict_x_verified=False,
                original_last_fold_native_forecasts_verified=False,
                native_last_fold_prediction_reconciled=False,
                independent_oos_verified=False,oos_certified=False,
                ai_promotion_eligible=False,ready_for_360=False,
                full_core_parity_certified=False,live_orders_enabled=False,
                errors=[],blockers=[
                  "ONLY_ORIGINAL_LAST_FOLD_HISTORICAL_NATIVE_PARITY",
                  "FUTURE_OOS_NOT_OBSERVED",
                  "REAL_FUNDING_MARK_LIQUIDATION_AND_EXCHANGE_FILLS_PENDING"])
    failing_time=None
    try:
        import numpy as np
        import pandas as pd
        import joblib
        from quant_system.phase8_model_evidence import booster_sha256
        from quant_system.phase13b_matrix import matrix_digest,read_matrix
        from quant_system.phase13_feature_causality import canonical_frame
        from quant_system.phase14_fitted_preprocessing import verify_model_bundle_seal
        from quant_system.phase15_fit_time_audit import rebuilt_features
        from quant_system.phase18_historical_shadow import _forecast_feature
        root=Path(original_root)
        meta=json.loads(Path(metadata).read_text(encoding="utf8"))
        require(verify_model_bundle_seal(bundle,metadata,protocol,seal,
                require_registered=True),"PHASE19_ORIGINAL_MODEL_SEAL_MISMATCH")
        require(meta.get("candidate_sha256")==ORIGINAL_BUNDLE_SHA and
                meta.get("source_commit_sha")==ORIGINAL_SOURCE_SHA and
                meta.get("model_identifier")==MODEL_ID and
                type(meta.get("training_end_ms")) is int and
                meta["training_end_ms"]<OOS_START and
                (root/"artifacts/phase3/native/phase13b-unsealed-model-candidate.json").read_bytes()==
                Path(metadata).read_bytes(),
                "PHASE19_UNAPPROVED_MODEL_OR_METADATA")
        native=root/"artifacts/phase3/native"
        source_report=json.loads((native/"native-research-180.json").read_text(encoding="utf8"))
        event_file=native/"phase13b-native-matrix-events.jsonl"
        predict_file=native/"freqai-native-predictions.csv"
        require(matrix_digest(event_file)==source_report.get("phase13b_matrix_events_sha256")
                and matrix_digest(predict_file)==source_report.get("prediction_capture_sha256")
                and source_report.get("phase13b_candidate_sha256")==ORIGINAL_BUNDLE_SHA,
                "PHASE19_ORIGINAL_NATIVE_TRACE_SHA_MISMATCH")
        # Reject missing PREDICT stages, orphan duplicated events and wrong
        # model identity; retained per-matrix NPZ SHA is checked in read_matrix.
        events=[json.loads(x) for x in event_file.read_text(encoding="utf8").splitlines()]
        selected=[e for e in events if e.get("stage")=="PREDICT"
                  and e.get("fold_model_name")==meta["fold_model_name"]]
        require(bool(selected) and all(
                    e.get("model_sha256")==meta["model_sha256"] and
                    e.get("training_end_ms")==meta["training_end_ms"] and
                    e.get("columns")==meta["ordered_feature_columns"]
                    for e in selected),
                "PHASE19_ORIGINAL_PREDICT_STAGE_MISMATCH")
        names=meta["ordered_feature_columns"]
        times,arrays,flags=[],[],[]
        for event in selected:
            matrix=read_matrix(native,event)
            require(matrix["columns"]==names,
                    "PHASE19_ORIGINAL_MATRIX_SCHEMA_MISMATCH")
            times.extend(int(x) for x in matrix["timestamps"])
            arrays.extend(matrix["values"].tolist())
            flags.extend(int(x) for x in matrix["flags"])
        require(len(times)>=64 and len(times)==len(arrays)==len(flags),
                "PHASE19_ORIGINAL_NATIVE_ROWS_MISSING")
        validate_native_timestamps(times,meta["training_end_ms"])
        # Avoid treating predictions of other folds as this exact model's
        # predictions; check unique timestamps across the original trace.
        captured={}
        with predict_file.open(newline="",encoding="utf8") as stream:
            reader=csv.DictReader(stream)
            require(set(("open_time","source","pair","model_identifier",
                         "predicted_return","do_predict")).issubset(reader.fieldnames or []),
                    "PHASE19_ORIGINAL_PREDICTION_SCHEMA_MISSING")
            for row in reader:
                t=int(row["open_time"])
                require(t not in captured,"PHASE19_DUPLICATE_NATIVE_PREDICTION")
                captured[t]=row
        prediction_map=check_original_prediction_map(
            times,[captured[t] for t in times if t in captured])
        original=joblib.load(bundle) # trusted only AFTER pre-registered SHA
        require(isinstance(original,dict) and
                original.get("model_sha256")==meta["model_sha256"] and
                original.get("source_commit_sha")==ORIGINAL_SOURCE_SHA and
                original.get("training_end_ms")==meta["training_end_ms"] and
                original.get("ordered_features")==names and
                booster_sha256(original["model"])==meta["model_sha256"],
                "PHASE19_ORIGINAL_LIGHTGBM_MODEL_MISMATCH")
        closed=canonical_frame(root/"artifacts/phase3/canonical/15m.csv")
        stamp_index={int(t):i for i,t in enumerate(closed["open_time"])}
        require(len(stamp_index)==len(closed) and
                int(closed["open_time"].iloc[-1])<OOS_START,
                "PHASE19_HOLDOUT_DATA_FORBIDDEN")
        accepted=rejected=0
        reconciled=[]
        for time,actual_x,original_flag in zip(times,arrays,flags):
            failing_time=time
            require(time in stamp_index and stamp_index[time]>=159,
                    "PHASE19_UNAVAILABLE_HISTORICAL_PREFIX")
            index=stamp_index[time]
            source=closed.iloc[index-159:index+1].copy()
            feature=rebuilt_features(source,names).iloc[[-1]].reset_index(drop=True)
            require(bool(np.isfinite(feature.to_numpy(dtype=float)).all()),
                    "PHASE19_NONFINITE_SOURCE_FEATURE")
            rebuilt=_forecast_feature(feature,original["feature_pipeline"],
                      original["label_pipeline"],original["model"],names)
            original_capture=prediction_map[time]
            try:
                archive_flag=int(original_capture["do_predict"])
            except (ValueError,TypeError,OverflowError) as exc:
                raise NativeForecastMismatch("PHASE19_INVALID_NATIVE_DO_PREDICT") from exc
            native_row=dict(x=actual_x,flag=original_flag,
                 predicted_return=original_capture["predicted_return"],
                 source=original_capture["source"],
                 pair=original_capture["pair"],
                 model_identifier=original_capture["model_identifier"])
            require(archive_flag==original_flag,
                    "PHASE19_NATIVE_EVENT_CAPTURE_FLAG_MISMATCH")
            verify_native_row(rebuilt,native_row)
            if original_flag==1:
                accepted+=1
            else:
                rejected+=1
            reconciled.append(dict(open_time_ms=time,do_predict=original_flag,
                                  accepted_forecast=original_flag==1))
        require(accepted>0 and accepted+rejected==len(times),
                "PHASE19_NO_ACCEPTED_NATIVE_FORECAST")
        report.update(original_last_fold_native_predict_x_verified=True,
                original_last_fold_native_forecasts_verified=True,
                native_last_fold_prediction_reconciled=True,
                original_native_predict_count=len(times),
                accepted_native_predict_count=accepted,
                rejected_native_predict_count=rejected,
                model_identifier=MODEL_ID,
                original_model_bundle_sha256=ORIGINAL_BUNDLE_SHA,
                original_native_predict_trace_sha256=matrix_digest(predict_file),
                original_native_matrix_ledger_sha256=matrix_digest(event_file),
                first_native_predict_open_ms=times[0],
                last_native_predict_open_ms=times[-1],
                rows=reconciled)
    except NativeForecastMismatch as exc:
        report["errors"].append(str(exc))
        if failing_time is not None:
            report["failing_native_open_ms"]=failing_time
    except Exception as exc:
        report["errors"].append("PHASE19_ORIGINAL_NATIVE_RECONCILIATION_FAILED")
        report["error_type"]=type(exc).__name__
        report["error_detail"]=str(exc)[:180]
        if failing_time is not None:
            report["failing_native_open_ms"]=failing_time
    dest=Path(output)
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(report,indent=2,sort_keys=True,allow_nan=False)+"\n",encoding="utf8")
    return report

def main():
    p=argparse.ArgumentParser()
    for name in ("original-root","bundle","metadata","protocol","seal","out"):
        p.add_argument("--"+name,required=True)
    a=p.parse_args()
    report=inspect(original_root=a.original_root,bundle=a.bundle,
                   metadata=a.metadata,protocol=a.protocol,seal=a.seal,
                   output=a.out)
    print(json.dumps({key:report[key] for key in
         ("native_last_fold_prediction_reconciled","errors")},sort_keys=True))
    return 0 if report["native_last_fold_prediction_reconciled"] else 2

if __name__=="__main__":
    raise SystemExit(main())
