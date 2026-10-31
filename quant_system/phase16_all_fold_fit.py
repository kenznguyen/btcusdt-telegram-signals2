"""Phase16: re-fit preprocessing ONLY on original TRAIN for ALL 26 historical folds.

Independent of future OOS, does not train LightGBM or replace sealed model.
Uses SHA-witnessed actual original LightGBM.fit X/y/w and source-row dates.
"""
from __future__ import annotations
import argparse
import csv
import json
import math
from collections import defaultdict
from pathlib import Path

import numpy as np
from quant_system.phase13b_matrix import read_matrix,matrix_digest
from quant_system.phase15_fit_time_audit import (
    eligible_rows,rebuilt_features,select_samples,
    refit_original_preprocessor,verify_fitted_outputs,FitCausalityError)
from quant_system.phase13_feature_causality import canonical_frame
from quant_system.phase14_fitted_preprocessing import verify_model_bundle_seal

EXPECTED_FOLDS=26
EXPECTED_TRAIN_ROWS=59696
EXPECTED_VALIDATION_ROWS=14825
M15=900000

class FoldEvidenceError(ValueError):
    pass

def require(condition,code):
    if not condition:
        raise FoldEvidenceError(code)

def index_folds(events,rows,*,expected_fold_count=EXPECTED_FOLDS):
    """Zero inference from PR names: every fold must have 3 native stages."""
    require(isinstance(events,list) and isinstance(rows,list) and
            type(expected_fold_count) is int and expected_fold_count>0,
            "PHASE16_INVALID_FOLD_INVENTORY")
    groups=defaultdict(dict)
    for event in events:
        try:
            name=event["fold_model_name"]
            stage=event["stage"]
            require(isinstance(name,str) and name.startswith("cb_btc_") and
                    stage in ("FIT_TRAIN","FIT_TEST","PREDICT"),
                    "PHASE16_UNEXPECTED_FOLD_IDENTITY")
            require(stage not in groups[name],"PHASE16_DUPLICATE_FIT_STAGE")
            groups[name][stage]=event
        except (KeyError,TypeError) as exc:
            raise FoldEvidenceError("PHASE16_MALFORMED_NATIVE_EVENT") from exc
    require(len(groups)==expected_fold_count,"PHASE16_FOLD_COUNT_MISMATCH")
    row_groups=defaultdict(list)
    for row in rows:
        require(row.get("fold_model_name") in groups,
                "PHASE16_UNKNOWN_SOURCE_FOLD")
        row_groups[row["fold_model_name"]].append(row)
    result=[]
    used_cutoffs=set()
    for name,stages in sorted(groups.items(),
                              key=lambda x:int(x[1]["FIT_TRAIN"]["training_end_ms"])
                                   if "FIT_TRAIN" in x[1] else -1):
        require(set(stages)=={"FIT_TRAIN","FIT_TEST","PREDICT"},
                "PHASE16_INCOMPLETE_ORIGINAL_FOLD")
        tr,te,pr=(stages[k] for k in ("FIT_TRAIN","FIT_TEST","PREDICT"))
        cutoff=tr.get("training_end_ms")
        sha=tr.get("model_sha256")
        columns=tr.get("columns")
        require(type(cutoff) is int and cutoff>0 and cutoff%M15==0 and
                cutoff not in used_cutoffs and isinstance(sha,str) and
                sha.startswith("sha256:") and len(sha)==71 and
                isinstance(columns,list) and len(columns)==20 and
                len(set(columns))==20 and
                all(e.get("training_end_ms")==cutoff and
                    e.get("model_sha256")==sha and
                    e.get("columns")==columns and
                    e.get("n_features")==20 and
                    e.get("label_horizon_candles")==4
                    for e in (tr,te,pr)),
                "PHASE16_FOLD_NATIVE_IDENTITY_MISMATCH")
        used_cutoffs.add(cutoff)
        group=row_groups[name]
        train=[r for r in group if r.get("row_kind")=="TRAIN"]
        test=[r for r in group if r.get("row_kind")=="TEST"]
        require(len(group)==len(train)+len(test) and
                len(train)==tr.get("n_rows") and
                len(test)==te.get("n_rows"),
                "PHASE16_NATIVE_SOURCE_ROW_COUNT_MISMATCH")
        require(all(r.get("model_sha256")==sha and
                    r.get("model_identifier")=="chart-pro-okx-shadow-v1" and
                    int(r["training_end_ms"])==cutoff and
                    int(r["horizon_candles"])==4 for r in group),
                "PHASE16_FOLD_SOURCE_IDENTITY_MISMATCH")
        try:
            eligible_rows(train,test,cutoff)
        except (FitCausalityError,TypeError,ValueError,KeyError) as exc:
            raise FoldEvidenceError(
                "PHASE16_FOLD_TEMPORAL_PROVENANCE_FAILED:"+name) from exc
        result.append((name,cutoff,sha,columns,train,test,stages))
    return result

def inspect(root_path,config_path,metadata_path,protocol_path,seal_path,output):
    result=dict(schemaVersion=1,audit="PHASE16_ALL_26_ORIGINAL_FIT_TIME_REPLAY",
        total_expected_folds=EXPECTED_FOLDS,folds_verified=0,
        all_26_folds_fitting_time_verified=False,
        full_model_pipeline_causality_verified=False,
        independent_oos_verified=False,oos_certified=False,
        ai_promotion_eligible=False,ready_for_360=False,
        live_orders_enabled=False,full_core_parity_certified=False,
        errors=[],blockers=["OOS_PROSPECTIVE_DATA_NOT_YET_MATURE",
                            "NO_FUNDING_MARK_LIQUIDATION_CERTIFICATE",
                            "NOT_ALL_OF_ORIGINAL_UPSTREAM_FEATURE_CONSTRUCTION_FIT_OBSERVED"])
    failing_fold=None
    try:
        root=Path(root_path)
        native=root/"artifacts/phase3/native"
        paper=root/"artifacts/phase3/paper"
        meta=json.loads(Path(metadata_path).read_text(encoding="utf8"))
        require(verify_model_bundle_seal(
            native/meta["candidate_path"],metadata_path,protocol_path,
            seal_path,require_registered=True),
            "PHASE16_ORIGINAL_SEAL_REJECTED")
        require((native/"phase13b-unsealed-model-candidate.json").read_bytes()==
                Path(metadata_path).read_bytes(),
                "PHASE16_CANDIDATE_METADATA_NOT_GIT_SEALED")
        config=json.loads(Path(config_path).read_text(encoding="utf8"))
        require(config.get("dry_run") is True and
                config.get("force_entry_enable") is False and
                config["exchange"]["name"]=="okx" and
                config["timeframe"]=="15m" and
                config["freqai"]["feature_parameters"]==
                  {"DI_threshold":0.9,"include_corr_pairlist":[],
                   "include_shifted_candles":2,"include_timeframes":["15m"],
                   "indicator_periods_candles":[14,28],"label_period_candles":4} and
                config["freqai"]["data_split_parameters"]==
                    {"test_size":0.2,"shuffle":False},
                "PHASE16_UNAPPROVED_NATIVE_CONFIG")
        report=json.loads((native/"native-research-180.json").read_text())
        prior=json.loads((paper/"phase13b-native-matrix-audit.json").read_text())
        require(prior.get("actual_fit_predict_matrices_verified") is True and
                prior.get("errors")==[] and
                report["phase13b_candidate_sha256"]==meta["candidate_sha256"] and
                matrix_digest(native/"freqai-native-training-samples.csv")==
                    report["phase12_training_samples_sha256"] and
                matrix_digest(native/"phase13b-native-matrix-events.jsonl")==
                    report["phase13b_matrix_events_sha256"],
                "PHASE16_ORIGINAL_NATIVE_SOURCE_SHA_MISMATCH")
        events=[json.loads(line) for line in
                (native/"phase13b-native-matrix-events.jsonl").read_text(
                    encoding="utf8").splitlines()]
        with (native/"freqai-native-training-samples.csv").open(
                newline="",encoding="utf8") as stream:
            samples=list(csv.DictReader(stream))
        folds=index_folds(events,samples)
        require(sum(len(f[4]) for f in folds)==EXPECTED_TRAIN_ROWS and
                sum(len(f[5]) for f in folds)==EXPECTED_VALIDATION_ROWS and
                folds[-1][0]==meta["fold_model_name"] and
                folds[-1][2]==meta["model_sha256"] and
                folds[-1][1]==meta["training_end_ms"],
                "PHASE16_ALL_FOLD_COUNTS_OR_SEALED_LAST_FOLD_MISMATCH")
        closed=canonical_frame(root/"artifacts/phase3/canonical/15m.csv")
        names=meta["ordered_feature_columns"]
        source_features=rebuilt_features(closed,names)
        positions={int(t):i for i,t in enumerate(closed["open_time"])}
        per_fold=[]
        prev_cutoff=None
        for name,cutoff,sha,columns,trrows,terows,stages in folds:
            failing_fold=name
            require(prev_cutoff is None or cutoff>prev_cutoff,
                    "PHASE16_NONMONOTONIC_FOLD_CUTOFF")
            prev_cutoff=cutoff
            require(columns==names,"PHASE16_FOLD_FEATURE_SCHEMA_CHANGED")
            tr_native=read_matrix(native,stages["FIT_TRAIN"])
            te_native=read_matrix(native,stages["FIT_TEST"])
            train_times,test_times=eligible_rows(trrows,terows,cutoff)
            xtr,ytr,wtr=select_samples(
                source_features,closed,trrows,names)
            xte,yte,wte=select_samples(
                source_features,closed,terows,names)
            fx,ly,tr,te=refit_original_preprocessor(
                xtr,ytr,wtr,xte,yte,wte,config)
            ntrain=verify_fitted_outputs(
                tr_native,*tr,train_times)
            ntest=verify_fitted_outputs(
                te_native,*te,test_times)
            # Change ONLY future market rows after this fold's cutoff.
            # Historical fit/eval source features must remain identical.
            mutated=closed.copy(deep=True)
            mask=mutated["open_time"]>=cutoff
            require(bool(mask.any()) and bool((~mask).any()),
                    "PHASE16_FUTURE_SUFFIX_NOT_PRESENT")
            for col in ("open","high","low","close","volume"):
                mutated.loc[mask,col] *= 3.17
            future_features=rebuilt_features(mutated,names)
            indices=[positions[t] for t in train_times+test_times]
            require(np.allclose(
                    source_features.iloc[indices].to_numpy(dtype=float),
                    future_features.iloc[indices].to_numpy(dtype=float),
                    rtol=1e-11,atol=1e-11),
                    "PHASE16_FUTURE_CHANGED_HISTORICAL_PREFIT_FEATURE")
            # Refit using the FUTURE-perturbed history (historical
            # TRAIN remains identical). Its actual fitted matrices
            # MUST still equal the original LightGBM witnesses.
            altered_trrows=xtr.copy(deep=True)
            altered_terows=xte.copy(deep=True)
            altered_xtr=future_features.iloc[
                [positions[t] for t in train_times]].reset_index(drop=True)
            altered_xte=future_features.iloc[
                [positions[t] for t in test_times]].reset_index(drop=True)
            _,_,train2,test2=refit_original_preprocessor(
                altered_xtr,ytr,wtr,altered_xte,yte,wte,config)
            verify_fitted_outputs(tr_native,*train2,train_times)
            verify_fitted_outputs(te_native,*test2,test_times)
            # Positive control: changing eligible TRAIN data MUST alter
            # at least a fitted feature and the fitted label scale.
            poison_x=xtr.copy(deep=True)
            target_col="%-raw-volume_gen_BTC/USDTUSDT_15m"
            require(target_col in poison_x.columns,
                    "PHASE16_POSITIVE_FEATURE_NOT_PRESENT")
            poison_x.iloc[-1,poison_x.columns.get_loc(target_col)] = (
                float(poison_x[target_col].max())*1000.0+1e6)
            poison_y=ytr.copy(deep=True)
            poison_y.iloc[-1,0]=float(poison_y.iloc[:,0].max())+20.0
            _,_,poisoned,_=refit_original_preprocessor(
                poison_x,poison_y,wtr,xte,yte,wte,config)
            require(not np.allclose(
                    poisoned[0].to_numpy(dtype=float),
                    tr[0].to_numpy(dtype=float),
                    rtol=1e-8,atol=1e-9) and
                    not np.allclose(
                    poisoned[1].to_numpy(dtype=float),
                    tr[1].to_numpy(dtype=float),
                    rtol=1e-8,atol=1e-9),
                    "PHASE16_ELIGIBLE_TRAIN_MUTATION_NOT_DETECTED")
            per_fold.append(dict(
                fold_model_name=name,model_sha256=sha,training_end_ms=cutoff,
                train_rows=ntrain,validation_rows=ntest,
                future_source_rows_perturbed=int(mask.sum()),
                native_x_y_weights_reproduced=True,
                future_only_intervention_invariant=True,
                eligible_train_positive_control_detected=True))
            result["folds_verified"]=len(per_fold)
        result.update(all_26_folds_fitting_time_verified=True,
            fold_results=per_fold,
            source_commit_sha=meta["source_commit_sha"],
            original_bundle_sha256=meta["candidate_sha256"],
            original_matrix_events_sha256=report["phase13b_matrix_events_sha256"],
            original_samples_sha256=report["phase12_training_samples_sha256"],
            total_reproduced_train_rows=sum(x["train_rows"] for x in per_fold),
            total_reproduced_validation_rows=sum(
                x["validation_rows"] for x in per_fold))
    except (FoldEvidenceError,FitCausalityError) as exc:
        result["errors"].append(str(exc))
        if failing_fold is not None:
            result["failing_fold_model_name"]=failing_fold
    except Exception as exc:
        result["errors"].append("PHASE16_NATIVE_FIT_REPLAY_FAILED")
        result["error_type"]=type(exc).__name__
        result["error_detail"]=str(exc)[:250]
        if failing_fold is not None:
            result["failing_fold_model_name"]=failing_fold
    path=Path(output);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(result,indent=2,sort_keys=True,
                allow_nan=False)+"\n",encoding="utf8")
    return result

def main():
    arg=argparse.ArgumentParser()
    for flag in ("artifacts-root","config","metadata","protocol","seal","out"):
        arg.add_argument("--"+flag,required=True)
    a=arg.parse_args()
    r=inspect(a.artifacts_root,a.config,a.metadata,a.protocol,a.seal,a.out)
    print(json.dumps({k:r[k] for k in
        ("folds_verified","all_26_folds_fitting_time_verified","errors")},
        sort_keys=True))
    return 0 if r["all_26_folds_fitting_time_verified"] else 2

if __name__=="__main__":
    raise SystemExit(main())
