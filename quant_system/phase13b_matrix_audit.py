"""Independent Phase13B SHA/row/schema audit of real LightGBM fit and predict X.

This does NOT certify preprocessing fit causality, independent OOS or live orders.
"""
from __future__ import annotations
import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

from quant_system.phase13b_matrix import (
    MatrixEvidenceError, check, read_matrix, matrix_digest
)

def load_json(path):
    data=json.loads(Path(path).read_text(encoding="utf8"))
    check(isinstance(data,dict),"PHASE13B_INVALID_JSON")
    return data

def csv_rows(path,needed):
    with Path(path).open(newline="",encoding="utf8") as source:
        reader=csv.DictReader(source)
        check(reader.fieldnames is not None and
              len(reader.fieldnames)==len(set(reader.fieldnames)) and
              set(needed).issubset(reader.fieldnames),"PHASE13B_INVALID_CSV_HEADER")
        rows=list(reader)
    check(all(None not in row and all(v is not None for v in row.values())
              for row in rows),"PHASE13B_INVALID_CSV_ROW")
    return rows

def reconcile_exported_predictions(native, report, phase8, lineage):
    """Reconcile two intentionally different populations, never omit evidence.

    LightGBM.predict sees only FreqAI's inference window (model lineage).
    The downstream strategy exports more candles than LightGBM predicts:
    pre-model training/warmup rows and, at most, one next-candle boundary
    after the final native model inference. These neutral rows must have
    do_predict=0 and an empty forecast. Interior inference gaps and all
    untraced accepted forecasts are invalid.
    """
    path=native/"freqai-native-predictions.csv"
    check(matrix_digest(path)==report.get("prediction_capture_sha256"),
          "PHASE13B_EXPORTED_PREDICTION_SHA_MISMATCH")
    fields=("open_time","do_predict","predicted_return",
            "model_identifier","source","pair")
    rows=csv_rows(path,fields)
    check(len(rows)==report.get("prediction_capture_rows"),
          "PHASE13B_EXPORTED_PREDICTION_COUNT_MISMATCH")
    recorded={}
    for key,group in lineage.items():
        for time,flag in group:
            check(time not in recorded,"PHASE13B_DUPLICATE_MODEL_PREDICTION_TIME")
            recorded[time]=(int(flag),key)
    check(bool(recorded),"PHASE13B_NO_MODEL_PREDICTIONS")
    first_model_time=min(recorded)
    last_model_time=max(recorded)
    seen=set()
    unmodeled=matched=accepted=0
    warmup=trailing=0
    for row in rows:
        try:
            time=int(row["open_time"])
        except (TypeError,ValueError,OverflowError) as exc:
            raise MatrixEvidenceError("PHASE13B_INVALID_EXPORTED_TIMESTAMP") from exc
        check(time>0 and time%900000==0 and
              str(time)==row["open_time"] and time not in seen,
              "PHASE13B_DUPLICATE_OR_INVALID_EXPORTED_TIMESTAMP")
        seen.add(time)
        flag=row["do_predict"]
        check(flag in ("1","0","-1","-2") and
              row["model_identifier"]==report.get("prediction_model_identifier") and
              row["source"]=="freqai-native-backtest" and
              row["pair"]=="BTC/USDT:USDT",
              "PHASE13B_INVALID_EXPORTED_PREDICTION_SOURCE")
        evidence=recorded.get(time)
        if evidence is None:
            check(flag!="1",
                  "PHASE13B_ACCEPTED_FORECAST_WITHOUT_MODEL_MATRIX")
            check(flag=="0" and row["predicted_return"]=="",
                  "PHASE13B_NONMODEL_ROW_NOT_NEUTRAL")
            if time<first_model_time:
                warmup+=1
            elif time>last_model_time:
                # The native FreqAI dataframe can include exactly ONE
                # end-boundary candle outside the last LightGBM.predict(X)
                # window. Never extend this exemption to an arbitrary
                # trailing period or to an accepted prediction.
                check(time==last_model_time+900000 and trailing==0,
                      "PHASE13B_UNEXPLAINED_POSTMODEL_NEUTRAL_ROW")
                trailing+=1
            else:
                raise MatrixEvidenceError(
                    "PHASE13B_UNMODELED_ROW_INSIDE_INFERENCE_WINDOW")
            unmodeled+=1
            continue
        expected_flag,model_key=evidence
        check(flag==str(expected_flag),
              "PHASE13B_EXPORTED_PREDICTION_MODEL_FLAG_MISMATCH")
        if flag=="1":
            try:
                forecast=float(row["predicted_return"])
            except (ValueError,TypeError,OverflowError) as exc:
                raise MatrixEvidenceError(
                    "PHASE13B_INVALID_ACCEPTED_FORECAST_VALUE") from exc
            import math
            check(math.isfinite(forecast),
                  "PHASE13B_INVALID_ACCEPTED_FORECAST_VALUE")
            accepted+=1
        else:
            check(row["predicted_return"]=="",
                  "PHASE13B_REJECTED_MODEL_FORECAST_NOT_EMPTY")
        matched+=1
    check(matched==len(recorded) and
          len(seen)==len(rows) and
          len(rows)==matched+unmodeled,
          "PHASE13B_MISSING_OR_UNACCOUNTED_MODEL_PREDICTIONS")
    check(accepted==report.get("prediction_capture_accepted") and
          accepted==phase8.get("matched_accepted_forecasts") and
          matched==phase8.get("emitted_lineage_rows"),
          "PHASE13B_PHASE8_ACCEPTED_MODEL_COUNTS_MISMATCH")
    return dict(exported_prediction_rows=len(rows),
                modeled_prediction_rows=matched,
                unmodeled_neutral_rows=unmodeled,
                unmodeled_warmup_rows=warmup,
                unmodeled_trailing_rows=trailing,
                model_inference_first_open_ms=first_model_time,
                model_inference_last_open_ms=last_model_time,
                modeled_accepted_rows=accepted)


def audit_matrices(artifacts_root):
    out=dict(schemaVersion=1,audit="PHASE13B_ACTUAL_LIGHTGBM_X_Y_AND_PREDICT_X",
        actual_fit_predict_matrices_verified=False,
        full_model_pipeline_causality_verified=False,
        independent_oos_verified=False,oos_certified=False,
        ai_promotion_eligible=False,ready_for_360=False,
        full_core_parity_certified=False,live_orders_enabled=False,
        blockers=["TRANSFORMED_FEATURE_TEMPORAL_INTERVENTION_NOT_CERTIFIED",
                  "FROZEN_MODEL_NOT_YET_SEALED_IN_GIT_BEFORE_OOS",
                  "INDEPENDENT_OOS_HOLDOUT_NOT_YET_OBSERVED",
                  "EXCHANGE_EXECUTION_FUNDING_LIQUIDATION_NOT_CERTIFIED"],
        errors=[])
    try:
        root=Path(artifacts_root)
        native=root/"native"
        phase12=load_json(root/"paper/phase12-native-fit-label-audit.json")
        phase8=load_json(root/"paper/phase8-native-model-evidence.json")
        report=load_json(native/"native-research-180.json")
        check(phase12.get("train_test_label_purge_verified") is True and
              phase12.get("actual_fit_sample_lineage_verified") is True and
              phase12.get("errors")==[] and
              phase8.get("native_model_lineage_verified") is True and
              phase8.get("errors")==[] and
              report.get("core_native_runtime_succeeded") is True and
              report.get("freqai_native_runtime_succeeded") is True,
              "PHASE13B_PRIOR_PHASE_GATES_NOT_VERIFIED")
        events_path=native/"phase13b-native-matrix-events.jsonl"
        samples_path=native/"freqai-native-training-samples.csv"
        lineage_path=native/"freqai-native-model-lineage.csv"
        check(matrix_digest(events_path)==report.get("phase13b_matrix_events_sha256")
              and matrix_digest(samples_path)==report.get("phase12_training_samples_sha256")
              and matrix_digest(lineage_path)==report.get("phase8_model_lineage_sha256"),
              "PHASE13B_NATIVE_EVIDENCE_SHA_MISMATCH")
        samples=defaultdict(lambda:dict(TRAIN=[],TEST=[]))
        for row in csv_rows(samples_path,(
                "fold_model_name","model_sha256","row_kind","feature_open_ms")):
            key=(row["fold_model_name"],row["model_sha256"])
            kind=row["row_kind"]
            check(kind in ("TRAIN","TEST"),
                  "PHASE13B_UNKNOWN_SOURCE_SAMPLE_KIND")
            samples[key][kind].append(int(row["feature_open_ms"]))
        lineage=defaultdict(list)
        for row in csv_rows(lineage_path,(
                "fold_model_name","model_sha256","open_time","do_predict")):
            key=(row["fold_model_name"],row["model_sha256"])
            lineage[key].append((int(row["open_time"]),int(row["do_predict"])))
        check(set(samples)==set(lineage) and bool(samples),
              "PHASE13B_SAMPLE_MODEL_LINK_MISSING")
        grouped=defaultdict(lambda:dict(FIT_TRAIN=[],FIT_TEST=[],PREDICT=[]))
        used=set()
        event_count=0
        with events_path.open(encoding="utf8") as stream:
            for line in stream:
                check(bool(line.strip()),"PHASE13B_EMPTY_EVENT")
                event=json.loads(line)
                check(isinstance(event,dict),"PHASE13B_INVALID_EVENT")
                key=(event.get("fold_model_name"),event.get("model_sha256"))
                check(key in samples,"PHASE13B_UNLINKED_MODEL_FINGERPRINT")
                stage=event.get("stage")
                check(stage in ("FIT_TRAIN","FIT_TEST","PREDICT"),
                      "PHASE13B_INVALID_STAGE")
                check(event.get("label_horizon_candles")==4 and
                      isinstance(event.get("training_end_ms"),int),
                      "PHASE13B_INVALID_TRAINING_METADATA")
                check(event["path"] not in used,"PHASE13B_DUPLICATE_ARCHIVE")
                used.add(event["path"])
                data=read_matrix(native,event)
                times=data["timestamps"]
                check(all(t < event["training_end_ms"] for t in times)
                      if stage!="PREDICT" else
                      all(t >= event["training_end_ms"] for t in times),
                      "PHASE13B_NONCAUSAL_TRAIN_INFERENCE_TIME")
                grouped[key][stage].append((event,data))
                event_count+=1
        check(set(grouped)==set(samples),
              "PHASE13B_UNOBSERVED_FIT_OR_PREDICT_MODEL")
        archived={"phase13b-matrices/"+p.name
                  for p in (native/"phase13b-matrices").glob("*.npz")}
        check(archived==used,
              "PHASE13B_UNREFERENCED_OR_MISSING_MATRIX_ARCHIVES")
        train_rows=test_rows=pred_rows=0
        schemas={}
        for key,parts in grouped.items():
            check(len(parts["FIT_TRAIN"])==len(parts["FIT_TEST"])==1
                  and bool(parts["PREDICT"]),
                  "PHASE13B_MISSING_FIT_EVAL_OR_PREDICT_WITNESS")
            tr=parts["FIT_TRAIN"][0][1]
            te=parts["FIT_TEST"][0][1]
            check(tr["timestamps"]==samples[key]["TRAIN"] and
                  te["timestamps"]==samples[key]["TEST"],
                  "PHASE13B_FITTED_SOURCE_TIMESTAMPS_MISMATCH")
            schema=tr["columns"]
            check(schema==te["columns"] and len(schema)>0,
                  "PHASE13B_FIT_TEST_SCHEMA_MISMATCH")
            merged=[]
            for ev,df in parts["PREDICT"]:
                check(df["columns"]==schema,
                      "PHASE13B_FIT_PREDICT_SCHEMA_MISMATCH")
                merged.extend(zip(df["timestamps"],df["flags"]))
            expected=lineage[key]
            check(len(merged)==len(expected) and
                  all(a==b[0] and int(c)==b[1]
                      for (a,c),b in zip(merged,expected)),
                  "PHASE13B_PREDICTION_ROW_MODEL_MISMATCH")
            check(max(tr["timestamps"])+4*900000 < min(te["timestamps"]),
                  "PHASE13B_TRAIN_TEST_HORIZON_OVERLAP")
            check(max(te["timestamps"])+4*900000 <
                  parts["FIT_TEST"][0][0]["training_end_ms"],
                  "PHASE13B_TEST_TARGET_AFTER_TRAIN_CUTOFF")
            train_rows+=len(tr["timestamps"])
            test_rows+=len(te["timestamps"])
            pred_rows+=len(merged)
            schemas[key[0]]={"model_sha256":key[1],
                "n_features":len(schema),
                "feature_columns":schema}
        # Phase12 TRAIN/TEST counts are fit rows. Phase8 PREDICT counts
        # are calls to LightGBM, NOT the longer exported FreqAI warmup history.
        out["row_accounting"]=dict(
            matrix_train_rows=train_rows,matrix_validation_rows=test_rows,
            matrix_predict_rows=pred_rows,
            phase12_train_rows=phase12.get("train_rows"),
            phase12_validation_rows=phase12.get("test_rows"),
            phase8_model_lineage_rows=sum(len(v) for v in lineage.values()),
            native_exported_prediction_rows=report.get("prediction_capture_rows"),
            expected_unmodeled_neutral_rows=(
                report["prediction_capture_rows"]-pred_rows
                if type(report.get("prediction_capture_rows")) is int
                else None))
        check(train_rows==phase12.get("train_rows") and
              test_rows==phase12.get("test_rows") and
              pred_rows==sum(len(v) for v in lineage.values()),
              "PHASE13B_NATIVE_MATRIX_ROW_COUNTS_MISMATCH")
        coverage=reconcile_exported_predictions(native,report,phase8,lineage)
        out["row_accounting"].update(coverage)
        meta_path=native/"phase13b-unsealed-model-candidate.json"
        bundle_path=native/"phase13b-unsealed-model-candidate.joblib"
        check(matrix_digest(meta_path)==
              report.get("phase13b_candidate_metadata_sha256") and
              matrix_digest(bundle_path)==
              report.get("phase13b_candidate_sha256"),
              "PHASE13B_CANDIDATE_NATIVE_SHA_MISMATCH")
        candidate=load_json(meta_path)
        latest_key=max(grouped,key=lambda key:
            grouped[key]["FIT_TRAIN"][0][0]["training_end_ms"])
        last_event=grouped[latest_key]["FIT_TRAIN"][0][0]
        check(candidate.get("fold_model_name")==latest_key[0] and
              candidate.get("model_sha256")==latest_key[1] and
              candidate.get("training_end_ms")==last_event["training_end_ms"] and
              candidate.get("ordered_feature_columns")==
                  grouped[latest_key]["FIT_TRAIN"][0][1]["columns"] and
              candidate.get("candidate_sha256")==matrix_digest(bundle_path) and
              candidate.get("sealed_in_git") is False,
              "PHASE13B_CANDIDATE_NOT_LAST_VERIFIED_MODEL")
        out.update(actual_fit_predict_matrices_verified=True,
            model_fold_count=len(grouped),matrix_event_count=event_count,
            fit_train_rows=train_rows,fit_validation_rows=test_rows,
            predict_rows=pred_rows,**coverage,model_feature_schemas=schemas,
            matrix_events_sha256=matrix_digest(events_path))
    except MatrixEvidenceError as exc:
        out["errors"].append(str(exc))
    except (ValueError,TypeError,KeyError,OSError,UnicodeError,
            OverflowError,csv.Error,json.JSONDecodeError) as exc:
        out["errors"].append("PHASE13B_MISSING_OR_INVALID_EVIDENCE")
        out["error_type"]=type(exc).__name__
    return out

def main():
    cli=argparse.ArgumentParser()
    cli.add_argument("--artifacts-root",required=True)
    cli.add_argument("--out",required=True)
    args=cli.parse_args()
    result=audit_matrices(args.artifacts_root)
    dest=Path(args.out)
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(result,sort_keys=True,indent=2,
                               allow_nan=False)+"\n",encoding="utf8")
    print(json.dumps({k:result[k] for k in (
        "actual_fit_predict_matrices_verified",
        "model_fold_count","fit_train_rows","predict_rows",
        "exported_prediction_rows","unmodeled_neutral_rows","row_accounting",
        "independent_oos_verified","errors") if k in result},sort_keys=True))
    return 0 if result["actual_fit_predict_matrices_verified"] else 2

if __name__=="__main__":raise SystemExit(main())
