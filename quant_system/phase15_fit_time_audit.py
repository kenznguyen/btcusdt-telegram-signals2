"""Phase15: independently re-FIT native preprocessing on ORIGINAL sealed model TRAIN rows.

Use Phase12 original raw sample timestamps and labels, Phase13B native LightGBM
X/y/w, and the exact original candidate's SHA-sealed pipeline. No new
LightGBM training, no OOS access or automatic promotion.
"""
from __future__ import annotations
import argparse
import copy
import csv
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
from quant_system.phase13b_matrix import matrix_digest, read_matrix
from quant_system.phase14_fitted_preprocessing import verify_model_bundle_seal
from quant_system.phase13_feature_causality import canonical_frame, feature_matrix

M15 = 900000

class FitCausalityError(ValueError):
    pass

def require(ok, code):
    if not ok:
        raise FitCausalityError(code)

def eligible_rows(train_rows, test_rows, cutoff, horizon=4):
    """Time/order and target purge must already hold BEFORE scaler fit."""
    require(horizon == 4 and type(cutoff) is int, "PHASE15_INVALID_CUTOFF")
    require(len(train_rows) >= 8 and len(test_rows) > 0,
            "PHASE15_MISSING_FIT_SAMPLE")
    tr = [int(r["feature_open_ms"]) for r in train_rows]
    te = [int(r["feature_open_ms"]) for r in test_rows]
    require(all(t > 0 and t % M15 == 0 for t in tr + te) and
            all(b > a for xs in (tr, te) for a,b in zip(xs,xs[1:])) and
            tr[-1] + horizon*M15 < te[0] and
            te[-1] + horizon*M15 < cutoff,
            "PHASE15_FIT_LABEL_PURGE_OR_TEMPORAL_LEAK")
    for r in train_rows + test_rows:
        t=int(r["feature_open_ms"])
        label_end=int(r["label_end_ms"])
        label=float(r["observed_raw_label"])
        expected=float(r["expected_recomputed_label"])
        require(int(r["training_end_ms"]) == cutoff and
                label_end == t+horizon*M15 and label_end < cutoff and
                math.isfinite(label) and math.isfinite(expected) and
                math.isclose(label,expected,rel_tol=1e-11,abs_tol=1e-12),
                "PHASE15_UNTRUSTED_FIT_ROW_PROVENANCE")
    return tr, te

def numeric_frame(x,columns):
    require(isinstance(x,pd.DataFrame) and list(x.columns)==list(columns),
            "PHASE15_FITTED_SCHEMA_MISMATCH")
    a=x.to_numpy(dtype=np.float64)
    require(a.ndim==2 and a.shape[1]==len(columns) and
            np.isfinite(a).all(),"PHASE15_NONFINITE_FITTED_FEATURE")
    return a

def verify_fitted_outputs(actual,features,labels,weights,timestamps):
    """Read FULL native LightGBM.fit/eval X, y, weights and row order."""
    x=numeric_frame(features,actual["columns"])
    y=np.asarray(labels,dtype=np.float64).reshape(-1)
    w=np.asarray(weights,dtype=np.float64).reshape(-1)
    n=len(actual["timestamps"])
    require(x.shape==actual["values"].shape and len(y)==len(w)==n and
            timestamps==actual["timestamps"] and np.isfinite(y).all() and
            np.isfinite(w).all(),
            "PHASE15_REPLAY_FIT_SHAPE_OR_ORDER_MISMATCH")
    require(np.allclose(x,actual["values"],rtol=1e-9,atol=1e-10) and
            np.allclose(y,actual["labels"],rtol=1e-9,atol=1e-10) and
            np.allclose(w,actual["weights"],rtol=1e-10,atol=1e-12),
            "PHASE15_REPLAYED_FIT_NOT_NATIVE_LIGHTGBM_X_Y_W")
    return n

def rebuilt_features(raw, names):
    from freqai_bridge.ChartProFreqaiResearch import ChartProFreqaiResearch
    base=feature_matrix(raw,ChartProFreqaiResearch)
    base=base.rename(columns={name:(
        name if name in ("%-day-of-week","%-hour-of-day")
        else name+"_BTC/USDTUSDT_15m") for name in base.columns})
    require(set(base.columns)==set(names) and len(names)==20,
            "PHASE15_UNAPPROVED_FEATURE_SCHEMA")
    return base.loc[:,names]

def select_samples(features,candles,rows,names):
    source={int(t):i for i,t in enumerate(candles["open_time"])}
    times=[int(r["feature_open_ms"]) for r in rows]
    require(all(t in source for t in times),"PHASE15_SOURCE_CANDLE_MISSING")
    x=features.iloc[[source[t] for t in times]].loc[:,names].reset_index(drop=True)
    y=pd.DataFrame({"&-future_return":[float(r["observed_raw_label"]) for r in rows]})
    w=np.ones(len(rows),dtype=np.float64)
    require(np.isfinite(x.to_numpy(dtype=float)).all() and
            np.isfinite(y.to_numpy(dtype=float)).all(),
            "PHASE15_INVALID_PREFIT_SOURCE")
    for row,time in zip(rows,times):
        k=source[time]
        require(k+4<len(candles) and
                int(candles["open_time"].iloc[k+4])==time+4*M15,
                "PHASE15_SOURCE_LABEL_HORIZON_MISSING")
        actual=float(candles["close"].iloc[k+4])/float(candles["close"].iloc[k])-1.
        require(math.isclose(actual,float(row["observed_raw_label"]),
                             rel_tol=1e-9,abs_tol=1e-10),
                "PHASE15_LABEL_NOT_FROM_CLOSED_MARKET")
    return x,y,w

def refit_original_preprocessor(train_x,train_y,train_w,
                                test_x,test_y,test_w,config):
    """Create UNFITTED pinned DataSieve factories, fit solely on TRAIN."""
    from freqtrade.freqai.freqai_interface import IFreqaiModel
    from types import SimpleNamespace
    owner=SimpleNamespace(freqai_info=config["freqai"])
    fx=IFreqaiModel.define_data_pipeline(owner,threads=1)
    ly=IFreqaiModel.define_label_pipeline(owner,threads=1)
    require([name for name,_ in fx.steps]==["const","scaler","di"] and
            [name for name,_ in ly.steps]==["scaler"],
            "PHASE15_UNAPPROVED_PREFIT_TRANSFORMS")
    x,y,w=fx.fit_transform(train_x.copy(),train_y.copy(),train_w.copy())
    y,_,_=ly.fit_transform(y)
    test_x,test_y,test_w=fx.transform(
        test_x.copy(),test_y.copy(),test_w.copy())
    test_y,_,_=ly.transform(test_y)
    return fx,ly,(x,y,w),(test_x,test_y,test_w)

def inspect(root_path,metadata,protocol,seal,config_file,outfile):
    result=dict(schemaVersion=1,
        audit="PHASE15_ORIGINAL_FROZEN_FIT_RECONSTRUCTION",
        original_frozen_fit_reconstruction_verified=False,
        fitted_training_time_causality_verified=False,
        full_model_pipeline_causality_verified=False,
        independent_oos_verified=False,oos_certified=False,
        ai_promotion_eligible=False,ready_for_360=False,
        full_core_parity_certified=False,live_orders_enabled=False,
        blockers=["ALL_26_FOLDS_FIT_TIME_OBSERVATION_NOT_CERTIFIED",
                  "PROSPECTIVE_OOS_NOT_EVALUATED",
                  "EXECUTION_FUNDING_AND_KOTLIN_PARITY_PENDING"],
        errors=[])
    try:
        root=Path(root_path)
        native=root/"artifacts/phase3/native"
        paper=root/"artifacts/phase3/paper"
        meta=json.loads(Path(metadata).read_text())
        require(verify_model_bundle_seal(
                    native/meta["candidate_path"],metadata,protocol,seal,
                    require_registered=True),
                "PHASE15_ORIGINAL_SEAL_NOT_VERIFIED")
        require((native/"phase13b-unsealed-model-candidate.json").read_bytes()
                ==Path(metadata).read_bytes(),
                "PHASE15_METADATA_NOT_EXACT_GIT_SNAPSHOT")
        prior=json.loads((paper/"phase13b-native-matrix-audit.json").read_text())
        report=json.loads((native/"native-research-180.json").read_text())
        require(prior["actual_fit_predict_matrices_verified"] is True and
                prior["errors"]==[] and
                matrix_digest(native/"phase13b-native-matrix-events.jsonl")==
                report["phase13b_matrix_events_sha256"] and
                matrix_digest(native/"freqai-native-training-samples.csv")==
                report["phase12_training_samples_sha256"],
                "PHASE15_ORIGINAL_NATIVE_LEDGER_TAMPERED")
        config=json.loads(Path(config_file).read_text())
        require(config["dry_run"] is True and
                config["force_entry_enable"] is False and
                config["exchange"]["name"]=="okx" and
                config["timeframe"]=="15m" and
                config["freqai"]["feature_parameters"]["DI_threshold"]==0.9 and
                config["freqai"]["data_split_parameters"]==
                    {"test_size":0.2,"shuffle":False},
                "PHASE15_UNAPPROVED_FIT_CONFIGURATION")
        rows=[]
        with (native/"freqai-native-training-samples.csv").open(newline="") as f:
            for row in csv.DictReader(f):
                if row["fold_model_name"]==meta["fold_model_name"]:
                    require(row["model_sha256"]==meta["model_sha256"] and
                            row["model_identifier"]==meta["model_identifier"],
                            "PHASE15_WRONG_ORIGINAL_BOOSTER")
                    rows.append(row)
        trrows=[r for r in rows if r["row_kind"]=="TRAIN"]
        terows=[r for r in rows if r["row_kind"]=="TEST"]
        require(len(trrows)+len(terows)==len(rows),
                "PHASE15_UNKNOWN_SOURCE_SAMPLE_KIND")
        trtimes,tetimes=eligible_rows(trrows,terows,meta["training_end_ms"])
        observed={}
        for line in (native/"phase13b-native-matrix-events.jsonl").read_text().splitlines():
            event=json.loads(line)
            if (event["fold_model_name"]==meta["fold_model_name"] and
                event["model_sha256"]==meta["model_sha256"] and
                event["stage"] in ("FIT_TRAIN","FIT_TEST")):
                require(event["stage"] not in observed,
                        "PHASE15_DUPLICATE_ORIGINAL_NATIVE_FIT")
                observed[event["stage"]]=read_matrix(native,event)
        require(set(observed)=={"FIT_TRAIN","FIT_TEST"},
                "PHASE15_MISSING_ORIGINAL_NATIVE_FIT")
        candles=canonical_frame(root/"artifacts/phase3/canonical/15m.csv")
        names=meta["ordered_feature_columns"]
        base=rebuilt_features(candles,names)
        xtr,ytr,wtr=select_samples(base,candles,trrows,names)
        xte,yte,wte=select_samples(base,candles,terows,names)
        fx,ly,tr,te=refit_original_preprocessor(
            xtr,ytr,wtr,xte,yte,wte,config)
        ntrain=verify_fitted_outputs(observed["FIT_TRAIN"],*tr,trtimes)
        ntest=verify_fitted_outputs(observed["FIT_TEST"],*te,tetimes)
        # Existing native fitted pipeline must be exactly re-creatable using
        # ONLY the original historical training rows and labels.
        import joblib
        original=joblib.load(native/meta["candidate_path"])
        require(original["model_sha256"]==meta["model_sha256"] and
                original["ordered_features"]==names,
                "PHASE15_ORIGINAL_PIPELINE_IDENTITY_MISMATCH")
        frozen_fx=copy.deepcopy(original["feature_pipeline"])
        frozen_ly=copy.deepcopy(original["label_pipeline"])
        xf,yf,wf=frozen_fx.transform(xte.copy(),yte.copy(),wte.copy())
        yf,_,_=frozen_ly.transform(yf)
        verify_fitted_outputs(observed["FIT_TEST"],xf,yf,wf,tetimes)
        # FUTURE suffix perturbation on the raw market history. Recreate
        # feature generation; no pre-cutoff source input may change.
        future=candles.copy(deep=True)
        mask=future["open_time"]>=meta["training_end_ms"]
        require(mask.any() and (~mask).any(),
                "PHASE15_FUTURE_INTERVENTION_NOT_AVAILABLE")
        for col in ("open","high","low","close","volume"):
            future.loc[mask,col]*=3.17
        changed=rebuilt_features(future,names)
        positions={int(t):i for i,t in enumerate(candles["open_time"])}
        positions=[positions[t] for t in trtimes+tetimes]
        require(np.allclose(base.iloc[positions].to_numpy(dtype=float),
                            changed.iloc[positions].to_numpy(dtype=float),
                            rtol=1e-11,atol=1e-11),
                "PHASE15_FUTURE_CANDLES_CHANGED_PREFIT_FEATURES")
        # POSITIVE CONTROLS: a genuine TRAIN feature/label mutation MUST
        # alter the fitted scaler output, or the test is not meaningful.
        damaged=xtr.copy(deep=True)
        volume="%-raw-volume_gen_BTC/USDTUSDT_15m"
        require(volume in damaged,"PHASE15_POSITIVE_CONTROL_SCHEMA")
        damaged.iloc[-1,damaged.columns.get_loc(volume)]=float(
            damaged[volume].max())*1000+1e6
        _,_,train_changed,_=refit_original_preprocessor(
            damaged,ytr,wtr,xte,yte,wte,config)
        require(not np.allclose(tr[0].to_numpy(dtype=float),
                                train_changed[0].to_numpy(dtype=float),
                                rtol=1e-8,atol=1e-9),
                "PHASE15_TRAIN_FEATURE_POSITIVE_CONTROL_FAILED")
        yy=ytr.copy(deep=True)
        yy.iloc[-1,0]=float(yy.iloc[:,0].max())+20
        _,_,label_changed,_=refit_original_preprocessor(
            xtr,yy,wtr,xte,yte,wte,config)
        require(not np.allclose(tr[1].to_numpy(dtype=float),
                                label_changed[1].to_numpy(dtype=float),
                                rtol=1e-8,atol=1e-9),
                "PHASE15_TRAIN_LABEL_POSITIVE_CONTROL_FAILED")
        result.update(original_frozen_fit_reconstruction_verified=True,
            fitted_training_time_causality_verified=True,
            frozen_candidate_sha256=meta["candidate_sha256"],
            original_source_commit_sha=meta["source_commit_sha"],
            source_fold_model_name=meta["fold_model_name"],
            original_training_end_ms=meta["training_end_ms"],
            train_rows_reconstructed=ntrain,
            validation_rows_reconstructed=ntest,
            future_market_rows_perturbed=int(mask.sum()),
            frozen_pipeline_validation_replayed=True,
            original_train_feature_mutation_detected=True,
            original_train_label_mutation_detected=True,
            recorded_source_samples_sha256=matrix_digest(
                native/"freqai-native-training-samples.csv"))
    except FitCausalityError as e:
        result["errors"].append(str(e))
    except Exception as e:
        result["errors"].append("PHASE15_ORIGINAL_PREFIT_REPLAY_RUNTIME_FAILED")
        result["error_type"]=type(e).__name__
        result["error_detail"]=str(e)[:280]
    target=Path(outfile)
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(result,indent=2,sort_keys=True,
                                 allow_nan=False)+"\n",encoding="utf8")
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--artifacts-root",required=True)
    p.add_argument("--candidate-metadata",required=True)
    p.add_argument("--protocol",required=True)
    p.add_argument("--seal",required=True)
    p.add_argument("--config",required=True)
    p.add_argument("--out",required=True)
    a=p.parse_args()
    res=inspect(a.artifacts_root,a.candidate_metadata,a.protocol,a.seal,a.config,a.out)
    print(json.dumps({k:res[k] for k in
        ("original_frozen_fit_reconstruction_verified",
         "fitted_training_time_causality_verified","errors")},sort_keys=True))
    return 0 if res["fitted_training_time_causality_verified"] else 2

if __name__=="__main__":
    raise SystemExit(main())
