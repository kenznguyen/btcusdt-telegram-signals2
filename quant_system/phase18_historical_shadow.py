"""Phase18 research-only historical frozen prediction shadow replay.

Only SHA-sealed, previously observed PRE-OOS market history is read.
No FreqAI fit/train, exchange I/O, holdout reads, portfolio actions or live orders.
This compares historical fixed-model inference invariance, NOT native parity/OOS.
"""
from __future__ import annotations
import argparse
import copy
import json
import math
from pathlib import Path

M15=900000
OOS_START=1793750400000
SOURCE_SHA="082edc082996425f61f48c952be41fb037564103"
BUNDLE_SHA="sha256:918dc4737ee432df8f7f9d2c3e561ac3983aaf56d8791a731a55624ab836b81f"

class HistoricalShadowError(ValueError):
    pass

def require(ok,code):
    if not ok:
        raise HistoricalShadowError(code)

def _numbers(values):
    try:
        numbers=[float(v) for v in values]
    except (ValueError,TypeError,OverflowError) as exc:
        raise HistoricalShadowError("SHADOW_INVALID_NUMERIC_WITNESS") from exc
    require(bool(numbers) and all(math.isfinite(v) for v in numbers),
            "SHADOW_INVALID_NUMERIC_WITNESS")
    return numbers

def _matching(x,y):
    a,b=_numbers(x),_numbers(y)
    return len(a)==len(b) and all(math.isclose(u,v,rel_tol=1e-9,abs_tol=1e-10)
                                  for u,v in zip(a,b))

def select_historical_witnesses(times,training_end_ms,*,max_count=24):
    """Choose only post-training historical candles, with 3 future controls."""
    require(type(training_end_ms) is int and training_end_ms>0 and
            training_end_ms % M15==0 and training_end_ms<OOS_START and
            type(max_count) is int and 16<=max_count<=64 and
            isinstance(times,list) and len(times)>=340 and
            all(type(t) is int and t>0 and t % M15==0 for t in times) and
            all(y-x==M15 for x,y in zip(times,times[1:])),
            "SHADOW_INVALID_HISTORICAL_TIMEBASE")
    require(times[-1]+M15<=OOS_START,"SHADOW_HOLDOUT_DATA_FORBIDDEN")
    candidates=[i for i in range(320,len(times)-3)
                if times[i]>=training_end_ms]
    require(len(candidates)>=16,
            "SHADOW_NOT_ENOUGH_POST_TRAIN_WITNESSES")
    count=min(max_count,len(candidates))
    selected=[candidates[(len(candidates)-1)*k//(count-1)]
              for k in range(count)]
    require(len(set(selected))==count,"SHADOW_DUPLICATE_WITNESS")
    return selected

def compare_shadow_predictions(short,long,full,future_changed,
                               positive_raw_feature_changed):
    """Four equivalent current-candle observations must yield same forecast."""
    records=(short,long,full,future_changed)
    require(all(isinstance(r,dict) for r in records),
            "SHADOW_INVALID_WITNESS")
    for row in records:
        require(type(row.get("flag")) is int and
                row["flag"] in (-2,-1,0,1),
                "SHADOW_INVALID_REJECTION_OR_FORECAST")
        prediction=row.get("prediction")
        require((prediction is None if row["flag"]!=1 else
                 type(prediction) in (float,int) and
                 math.isfinite(float(prediction)) and
                 abs(float(prediction))<=10),
                "SHADOW_INVALID_REJECTION_OR_FORECAST")
    require(_matching(short["features"],long["features"]) and
            _matching(short["features"],full["features"]) and
            _matching(short["features"],future_changed["features"]),
            "SHADOW_FUTURE_DEPENDENT_RAW_FEATURES")
    require(all(_matching(short["x"],r["x"]) and
                short["flag"]==r["flag"] for r in records[1:]),
            "SHADOW_FROZEN_X_OR_FLAG_DRIFT")
    if short["flag"]==1:
        require(all(math.isclose(float(short["prediction"]),
                 float(r["prediction"]),rel_tol=1e-9,abs_tol=1e-10)
                 for r in records[1:]),
                "SHADOW_FROZEN_PREDICTION_DRIFT")
    require(positive_raw_feature_changed is True,
            "SHADOW_INEFFECTIVE_CURRENT_CANDLE_CONTROL")
    return True

def _feature_at(raw,names,idx):
    import numpy as np
    from quant_system.phase15_fit_time_audit import rebuilt_features
    features=rebuilt_features(raw,names).iloc[[idx]].reset_index(drop=True)
    require(len(features)==1 and list(features.columns)==names and
            bool(np.isfinite(features.to_numpy(dtype=float)).all()),
            "SHADOW_INVALID_CAUSAL_FEATURE")
    return features

def _forecast_feature(row,feature_pipeline,label_pipeline,model,names):
    import numpy as np
    import pandas as pd
    transformed=copy.deepcopy(feature_pipeline).transform(
        row.copy(deep=True),outlier_check=True)
    require(isinstance(transformed,tuple) and len(transformed)==3,
            "SHADOW_INVALID_FITTED_DATASIEVE")
    x,flags,_=transformed
    require(isinstance(x,pd.DataFrame) and len(x)==1 and
            list(x.columns)==names and len(flags)==1 and
            bool(np.isfinite(x.to_numpy(dtype=float)).all()),
            "SHADOW_INVALID_FITTED_DATASIEVE")
    flag=int(flags[0])
    require(flag in (-2,-1,0,1) and float(flags[0])==flag,
            "SHADOW_INVALID_REJECTION_OR_FORECAST")
    forecast=None
    if flag==1:
        prediction=np.asarray(model.predict(x),dtype=float).reshape(-1)
        require(len(prediction)==1 and bool(np.isfinite(prediction).all()),
                "SHADOW_INVALID_FROZEN_MODEL_OUTPUT")
        inverse=copy.deepcopy(label_pipeline).inverse_transform(
            pd.DataFrame({"&-future_return":[float(prediction[0])]}))
        require(isinstance(inverse,tuple) and len(inverse)==3 and
                isinstance(inverse[0],pd.DataFrame) and
                inverse[0].shape==(1,1),
                "SHADOW_INVALID_FROZEN_LABEL_SCALER")
        forecast=float(inverse[0].iloc[0,0])
        require(math.isfinite(forecast) and abs(forecast)<=10,
                "SHADOW_INVALID_FROZEN_LABEL_SCALER")
    return dict(features=row.iloc[0].astype(float).tolist(),
                x=x.iloc[0].astype(float).tolist(),flag=flag,
                prediction=forecast)

def inspect(*,original_root,bundle,metadata,protocol,seal,output):
    """Actual historical audit, no held-out timestamps and no retraining."""
    report=dict(schemaVersion=1,audit="PHASE18_PREHOLDOUT_FROZEN_SHADOW",
                historical_frozen_prefix_invariance_verified=False,
                native_last_fold_prediction_reconciled=False,
                full_model_pipeline_causality_verified=False,
                independent_oos_verified=False,oos_certified=False,
                ai_promotion_eligible=False,ready_for_360=False,
                live_orders_enabled=False,
                errors=[],blockers=[
                    "HISTORICAL_SHADOW_IS_NOT_NATIVE_OR_INDEPENDENT_OOS_PARITY",
                    "FUNDING_MARK_LIQUIDATION_NOT_VERIFIED",
                    "NO_EXCHANGE_EXECUTION_CERTIFICATION"])
    try:
        import numpy as np
        import pandas as pd
        import joblib
        from quant_system.phase14_fitted_preprocessing import verify_model_bundle_seal
        from quant_system.phase13_feature_causality import canonical_frame
        from quant_system.phase13b_matrix import matrix_digest
        from quant_system.phase8_model_evidence import booster_sha256
        root=Path(original_root)
        meta=json.loads(Path(metadata).read_text(encoding="utf8"))
        require(verify_model_bundle_seal(bundle,metadata,protocol,seal,
                require_registered=True),"SHADOW_ORIGINAL_SEAL_MISMATCH")
        require(meta.get("candidate_sha256")==BUNDLE_SHA and
                meta.get("source_commit_sha")==SOURCE_SHA and
                meta.get("model_identifier")=="chart-pro-okx-shadow-v1" and
                type(meta.get("training_end_ms")) is int and
                meta["training_end_ms"]<OOS_START and
                (root/"artifacts/phase3/native/phase13b-unsealed-model-candidate.json").read_bytes()==
                Path(metadata).read_bytes(),
                "SHADOW_UNAPPROVED_FROZEN_CANDIDATE")
        payload=joblib.load(bundle) # ONLY after exact independent SHA seal.
        names=meta["ordered_feature_columns"]
        require(isinstance(payload,dict) and
                payload.get("ordered_features")==names and
                payload.get("model_identifier")==meta["model_identifier"] and
                payload.get("model_sha256")==meta["model_sha256"] and
                payload.get("source_commit_sha")==SOURCE_SHA and
                payload.get("training_end_ms")==meta["training_end_ms"] and
                booster_sha256(payload["model"])==meta["model_sha256"],
                "SHADOW_ORIGINAL_FROZEN_BOOSTER_MISMATCH")
        require([key for key,_ in payload["feature_pipeline"].steps]==
                ["const","scaler","di"] and
                [key for key,_ in payload["label_pipeline"].steps]==["scaler"],
                "SHADOW_FITTED_PREPROCESSOR_CHANGED")
        data_file=root/"artifacts/phase3/canonical/15m.csv"
        history=canonical_frame(data_file)
        times=history["open_time"].astype(int).tolist()
        selected=select_historical_witnesses(times,meta["training_end_ms"])
        # The full original research data may contain later historical
        # candles: use them only to PROVE they cannot change a past forecast.
        rows=[]
        for i in selected:
            short=history.iloc[i-159:i+1].copy()
            long=history.iloc[i-319:i+1].copy()
            extended=history.iloc[:i+4].copy()
            changed=extended.copy(deep=True)
            changed.loc[changed.index[-3:],["open","high","low","close","volume"]]*=3.17
            s=_feature_at(short,names,len(short)-1)
            l=_feature_at(long,names,len(long)-1)
            f=_feature_at(extended,names,i)
            m=_feature_at(changed,names,i)
            positive=short.copy(deep=True)
            positive.loc[positive.index[-1],"volume"]*=3.17
            pc=_feature_at(positive,names,len(positive)-1)
            effective=not np.allclose(s.to_numpy(dtype=float),
                    pc.to_numpy(dtype=float),rtol=1e-11,atol=1e-11)
            observations=[
                _forecast_feature(v,payload["feature_pipeline"],
                    payload["label_pipeline"],payload["model"],names)
                for v in (s,l,f,m)
            ]
            compare_shadow_predictions(*observations,effective)
            rows.append(dict(open_time_ms=int(times[i]),
                             do_predict=int(observations[0]["flag"]),
                             predicted_return=observations[0]["prediction"]))
        require(any(r["do_predict"]==1 for r in rows),
                "SHADOW_NO_ACCEPTED_HISTORICAL_FORECAST")
        report.update(historical_frozen_prefix_invariance_verified=True,
            inspected_historical_witnesses=len(rows),
            accepted_historical_forecasts=sum(r["do_predict"]==1 for r in rows),
            historical_canonical_m15_sha256=matrix_digest(data_file),
            frozen_bundle_sha256=BUNDLE_SHA,
            source_commit_sha=SOURCE_SHA,
            first_witness_open_ms=rows[0]["open_time_ms"],
            last_witness_open_ms=rows[-1]["open_time_ms"],
            witnesses=rows)
    except HistoricalShadowError as exc:
        report["errors"].append(str(exc))
    except Exception as exc:
        report["errors"].append("SHADOW_NATIVE_HISTORICAL_SMOKE_FAILED")
        report["error_type"]=type(exc).__name__
        report["error_detail"]=str(exc)[:180]
    dest=Path(output)
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(report,indent=2,sort_keys=True,
                               allow_nan=False)+"\n",encoding="utf8")
    return report

def main():
    p=argparse.ArgumentParser()
    for arg in ("original-root","bundle","metadata","protocol","seal","out"):
        p.add_argument("--"+arg,required=True)
    a=p.parse_args()
    report=inspect(original_root=a.original_root,bundle=a.bundle,
                   metadata=a.metadata,protocol=a.protocol,seal=a.seal,
                   output=a.out)
    print(json.dumps({k:report[k] for k in
          ("historical_frozen_prefix_invariance_verified","errors")},
          sort_keys=True))
    return 0 if report["historical_frozen_prefix_invariance_verified"] else 2

if __name__=="__main__":
    raise SystemExit(main())
