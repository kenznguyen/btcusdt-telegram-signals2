"""Prospective fixed 30d OOS replay, NO FreqAI training and NO real orders.

Strict 26-fold report approval, original Git SHA seal, exact closed OKX
15m/1h/5m holdout and prehistory. Frozen last-fold LightGBM is the ONLY AI
model. All modes share existing CORE rules and shared-risk portfolio engine.
Does not claim funding/exchange fill or OOS certification automatically.
"""
from __future__ import annotations
import argparse
import copy
import csv
import json
import math
from datetime import datetime,timezone
from pathlib import Path

import numpy as np
import pandas as pd

from quant_system.phase13b_matrix import matrix_digest
from quant_system.phase14_fitted_preprocessing import verify_model_bundle_seal
from quant_system.phase15_fit_time_audit import rebuilt_features
from quant_system.paper_backtest import closed_context
from quant_system.paper_portfolio import (
    PortfolioConfig,replay_portfolio,EVENT_FIELDS,TRADE_FIELDS)
from freqtrade_parity.dataset_io import read_closed_csv

START=1793750400000  # 2026-11-04T00:00:00Z
END=1796342400000    # 2026-12-04T00:00:00Z
M15=900000
H1=3600000
FIVE=300000
MODEL_SHA="sha256:918dc4737ee432df8f7f9d2c3e561ac3983aaf56d8791a731a55624ab836b81f"
SOURCE_SHA="082edc082996425f61f48c952be41fb037564103"
MODES=("CORE_ONLY","AI_ONLY","DUAL")

class OOSContractError(ValueError):
    pass

def require(value,reason):
    if not value:
        raise OOSContractError(reason)

def verify_shared_risk_protocol(p):
    policy=p["frozen_model_policy"]
    e=p["evaluation"]
    require(policy.get("retrain_inside_holdout") is False and
            policy.get("tune_parameters_using_holdout") is False and
            policy.get("change_strategy_or_features_after_seal") is False and
            e.get("no_real_orders") is True,
            "OOS_TRAINING_OR_ORDER_ENABLED")
    require(e.get("modes")==list(MODES) and
            e.get("initial_equity_usdt")==100 and
            e.get("futures_leverage")==13 and
            e.get("entry_margin_fraction_of_equity")==.1 and
            e.get("max_total_margin_fraction_of_equity")==.6 and
            e.get("max_positions")==3 and
            e.get("max_ai_origin_positions_in_dual")==2 and
            e.get("max_dca_per_position")==1 and
            e.get("fee_per_side_fraction")==.0005,
            "OOS_SHARED_RISK_CHANGED")
    return True

def verify_oos_schedule(protocol,now=None):
    now=now or datetime.now(timezone.utc)
    require(now.tzinfo is not None and now.utcoffset() is not None,
            "OOS_INVALID_CLOCK")
    require(protocol.get("protocol")=="PHASE13B_PROSPECTIVE_FROZEN_MODEL_OOS" and
            protocol.get("holdout_start_utc")=="2026-11-04T00:00:00Z" and
            protocol.get("holdout_end_utc")=="2026-12-04T00:00:00Z" and
            protocol.get("holdout_days")==30 and
            protocol.get("model_identifier")=="chart-pro-okx-shadow-v1" and
            protocol.get("holdout_data_already_used_for_model_selection") is False,
            "OOS_PROTOCOL_CHANGED")
    require(verify_shared_risk_protocol(protocol),
            "OOS_SHARED_RISK_CHANGED")
    require(now.timestamp()*1000>=END,
            "OOS_WINDOW_NOT_COMPLETE")
    return START,END

def verify_exact_closed_timebase(rows,*,start,end,step):
    require(type(start) is int and type(end) is int and
            type(step) is int and step>0 and end>start and
            len(rows)==(end-start)//step and
            end-start==len(rows)*step,
            "OOS_EXACT_CANDLE_COUNT_MISMATCH")
    for i,bar in enumerate(rows):
        require(bar.get("closed") is True and
                bar.get("open_time")==start+i*step and
                all(math.isfinite(float(bar[k]))
                    for k in ("open","high","low","close","volume")) and
                float(bar["low"])>0 and
                float(bar["high"])>=max(float(bar["open"]),
                                        float(bar["close"])) and
                float(bar["low"])<=min(float(bar["open"]),
                                       float(bar["close"])) and
                float(bar["volume"])>=0,
                "OOS_GAP_OR_OPEN_CANDLE")
    return len(rows)

def _near(a,b):
    return math.isclose(a,b,rel_tol=5e-8,abs_tol=1e-8)

def verify_candle_aggregation(big,small,ratio):
    require(len(small)==len(big)*ratio,
            "OOS_TIMEFRAME_AGGREGATION_GAP")
    for i,bar in enumerate(big):
        chunk=small[i*ratio:(i+1)*ratio]
        require(bar["open_time"]==chunk[0]["open_time"] and
                _near(bar["open"],chunk[0]["open"]) and
                _near(bar["close"],chunk[-1]["close"]) and
                _near(bar["high"],max(x["high"] for x in chunk)) and
                _near(bar["low"],min(x["low"] for x in chunk)),
                "OOS_TIMEFRAME_OHLCV_INCONSISTENT")
    return True

def _load_bars(holdout,prehistory):
    h,p=Path(holdout),Path(prehistory)
    m15=read_closed_csv(h/"15m.csv",M15)
    h1=read_closed_csv(h/"1h.csv",H1)
    fine=read_closed_csv(h/"5m.csv",FIVE)
    warm15=read_closed_csv(p/"15m.csv",M15)
    warm1h=read_closed_csv(p/"1h.csv",H1)
    verify_exact_closed_timebase(m15,start=START,end=END,step=M15)
    verify_exact_closed_timebase(h1,start=START,end=END,step=H1)
    verify_exact_closed_timebase(fine,start=START,end=END,step=FIVE)
    verify_exact_closed_timebase(warm15,
        start=START-128*M15,end=START,step=M15)
    verify_exact_closed_timebase(warm1h,
        start=START-100*H1,end=START,step=H1)
    verify_candle_aggregation(m15,fine,3)
    verify_candle_aggregation(h1,m15,4)
    return warm15+m15,warm1h+h1,m15,fine

def _predict_frozen(history,holdout,model_bundle,meta):
    """One candle/prefix at a time; never call fit or retrain any model."""
    import joblib
    from quant_system.phase8_model_evidence import booster_sha256
    from freqai_bridge.ChartProFreqaiResearch import ChartProFreqaiResearch
    # The caller verified SHA against an independently registered Git seal.
    data=joblib.load(model_bundle)
    require(data.get("source_commit_sha")==SOURCE_SHA and
            data.get("model_sha256")==meta["model_sha256"] and
            data.get("ordered_features")==meta["ordered_feature_columns"] and
            booster_sha256(data["model"])==meta["model_sha256"],
            "OOS_FROZEN_MODEL_WITNESS_MISMATCH")
    feature_pipe=copy.deepcopy(data["feature_pipeline"])
    label_pipe=copy.deepcopy(data["label_pipeline"])
    names=meta["ordered_feature_columns"]
    frame=pd.DataFrame(history)
    frame["date"]=pd.to_datetime(frame["open_time"],unit="ms",utc=True)
    lookup={bar["open_time"]:bar for bar in holdout}
    forecasts=[]
    for index in range(len(history)-len(holdout),len(history)):
        # A 160-candle prefix suffices for 28-candle rolling features and
        # 2 positive shifts, without ever exposing a subsequent OOS candle.
        prefix=frame.iloc[max(0,index-159):index+1].copy()
        features=rebuilt_features(prefix,names).iloc[[-1]].reset_index(drop=True)
        require(bool(np.isfinite(features.to_numpy(dtype=float)).all()),
                "OOS_NONFINITE_CAUSAL_PREFIX_FEATURE")
        transformed=feature_pipe.transform(features,outlier_check=True)
        require(isinstance(transformed,tuple) and len(transformed)==3,
                "OOS_FROZEN_PIPELINE_INVALID_RETURN")
        x,flags,_=transformed
        require(list(x.columns)==names and len(x)==1 and len(flags)==1,
                "OOS_FROZEN_FEATURE_SCHEMA_MISMATCH")
        flag=int(flags[0])
        require(flag in (1,0,-1,-2),"OOS_INVALID_FROZEN_DI_FLAG")
        predicted=""
        if flag==1:
            normal=np.asarray(data["model"].predict(x),dtype=float).reshape(-1)
            require(len(normal)==1 and np.isfinite(normal).all(),
                    "OOS_FROZEN_MODEL_INVALID_OUTPUT")
            label=label_pipe.inverse_transform(
                pd.DataFrame({"&-future_return":[float(normal[0])]})
            )
            require(isinstance(label,tuple) and len(label)==3,
                    "OOS_FROZEN_LABEL_SCALER_INVALID")
            predicted=float(label[0].iloc[0,0])
            require(math.isfinite(predicted) and abs(predicted)<=10,
                    "OOS_FROZEN_FORECAST_OUT_OF_RANGE")
        t=int(frame["open_time"].iloc[index])
        bar=lookup[t]
        forecasts.append(dict(open_time=t,
            **{k:bar[k] for k in ("open","high","low","close","volume")},
            predicted_return=predicted,do_predict=flag,
            source="freqai-frozen-oos",pair="BTC/USDT:USDT",
            model_identifier=meta["model_identifier"],
            model_sha256=meta["model_sha256"]))
    require(len(forecasts)==2880,"OOS_FROZEN_FORECAST_GAP")
    return forecasts

def run(*,holdout_dir,prehistory_dir,config_path,
        model_bundle,model_metadata,protocol_path,seal_path,
        fold_audit_path,release_gate_path,output_dir):
    report=dict(schemaVersion=1,phase="PHASE16_FROZEN_OOS_PRE_REGISTERED",
        all_26_folds_fitting_time_verified=False,
        frozen_model_prospective_replay_verified=False,
        three_mode_shared_risk_paper_replayed=False,
        independent_oos_verified=False,oos_certified=False,
        ai_promotion_eligible=False,ready_for_360=False,
        live_orders_enabled=False,funding_mark_full_coverage_verified=False,
        exchange_fills_verified=False,liquidation_verified=False,
        errors=[],blockers=[
            "FUNDING_MARK_AND_LIQUIDATION_NOT_CERTIFIED",
            "EXCHANGE_FILLS_AND_REAL_EXECUTION_NOT_VERIFIED",
            "INDEPENDENT_OOS_REQUIRES_SEPARATE_REVIEW"])
    try:
        p=json.loads(Path(protocol_path).read_text(encoding="utf8"))
        verify_oos_schedule(p)
        require(verify_model_bundle_seal(model_bundle,model_metadata,
            protocol_path,seal_path,require_registered=True),
            "OOS_PREHOLDOUT_GIT_SEAL_REJECTED")
        meta=json.loads(Path(model_metadata).read_text(encoding="utf8"))
        require(meta["candidate_sha256"]==MODEL_SHA and
                meta["source_commit_sha"]==SOURCE_SHA,
                "OOS_CANDIDATE_NOT_FROZEN")
        cfg=json.loads(Path(config_path).read_text(encoding="utf8"))
        from quant_system.phase13b_freeze import _canonical_sha
        snapshot={"freqai":cfg["freqai"],
                  "exchange":{"name":cfg["exchange"]["name"]},
                  "timeframe":cfg["timeframe"],
                  "dry_run":cfg["dry_run"],
                  "force_entry_enable":cfg["force_entry_enable"]}
        require(_canonical_sha(snapshot)==meta["config_sha256"] and
                _canonical_sha(cfg["freqai"])==meta["freqai_config_sha256"],
                "OOS_ORIGINAL_FREQAI_CONFIG_SHA_MISMATCH")
        require(cfg["dry_run"] is True and
                cfg["force_entry_enable"] is False and
                cfg["exchange"]["name"]=="okx" and
                cfg["freqai"]["feature_parameters"]["label_period_candles"]==4,
                "OOS_UNAPPROVED_RESEARCH_CONFIG")
        allfold=json.loads(Path(fold_audit_path).read_text(encoding="utf8"))
        approval=json.loads(Path(release_gate_path).read_text(encoding="utf8"))
        require(allfold.get("all_26_folds_fitting_time_verified") is True and
                allfold.get("folds_verified")==26 and
                allfold.get("errors")==[] and
                allfold.get("original_bundle_sha256")==MODEL_SHA and
                allfold.get("source_commit_sha")==SOURCE_SHA and
                approval.get("approved_phase16_report_sha256")==
                    matrix_digest(fold_audit_path) and
                approval.get("original_seal_commit")==
                    "888efb11b613b42a2badb3bc8adfa19ff090f2bb" and
                approval.get("oos_no_retraining") is True and
                approval.get("no_real_orders") is True,
                "OOS_ALL_26_FOLD_RELEASE_GATE_NOT_SIGNED")
        report["all_26_folds_fitting_time_verified"]=True
        history_m15,history_h1,m15,fine=_load_bars(holdout_dir,prehistory_dir)
        candles=closed_context(history_m15,history_h1)[-2880:]
        require(len(candles)==2880,"OOS_CORE_CONTEXT_INCOMPLETE")
        forecasts=_predict_frozen(history_m15,m15,model_bundle,meta)
        results={}
        for mode in MODES:
            paper=replay_portfolio(candles,fine,forecasts,mode=mode,
                dataset_sha256=matrix_digest(Path(holdout_dir)/"15m.csv"),
                detail_sha256=matrix_digest(Path(holdout_dir)/"5m.csv"),
                model_identifier=meta["model_identifier"],
                starting_balance=100.,config=PortfolioConfig(),
                prediction_source="freqai-frozen-oos")
            results[mode]=paper
        out=Path(output_dir);out.mkdir(parents=True,exist_ok=True)
        with (out/"frozen-30d-predictions.csv").open(
                "w",newline="",encoding="utf8") as stream:
            writer=csv.DictWriter(stream,fieldnames=tuple(forecasts[0]))
            writer.writeheader()
            writer.writerows(forecasts)
        for mode in MODES:
            rec=results[mode];name=mode.lower()
            for suffix,fields,rows in (
                ("events",EVENT_FIELDS,rec["events"]),
                ("trades",TRADE_FIELDS,rec["trades"]),
                ("equity",tuple(rec["equity_curve"][0]),rec["equity_curve"])):
                with (out/(name+"-"+suffix+".csv")).open(
                        "w",newline="",encoding="utf8") as stream:
                    writer=csv.DictWriter(stream,fieldnames=fields)
                    writer.writeheader();writer.writerows(rows)
        report.update(frozen_model_prospective_replay_verified=True,
            three_mode_shared_risk_paper_replayed=True,
            original_bundle_sha256=MODEL_SHA,
            original_source_commit_sha=SOURCE_SHA,
            holdout_start_utc=p["holdout_start_utc"],
            holdout_end_utc=p["holdout_end_utc"],
            holdout_m15_count=len(m15),holdout_5m_count=len(fine),
            holdout_m15_sha256=matrix_digest(Path(holdout_dir)/"15m.csv"),
            frozen_predictions_sha256=matrix_digest(out/"frozen-30d-predictions.csv"),
            frozen_forecast_accepted=sum(x["do_predict"]==1 for x in forecasts),
            **{m:results[m]["report"] for m in MODES})
    except OOSContractError as exc:
        report["errors"].append(str(exc))
    except Exception as exc:
        report["errors"].append("OOS_FROZEN_REPLAY_FAILED")
        report["error_type"]=type(exc).__name__
        report["error_detail"]=str(exc)[:200]
    target=Path(output_dir)/"frozen-30d-oos-paper-report.json"
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(report,sort_keys=True,indent=2,
                                  allow_nan=False)+"\n",encoding="utf8")
    return report

def main():
    parser=argparse.ArgumentParser()
    for field in ("holdout-dir","prehistory-dir","config","bundle",
                  "metadata","protocol","seal","fold-audit",
                  "release-gate","out-dir"):
        parser.add_argument("--"+field,required=True)
    a=parser.parse_args()
    r=run(holdout_dir=a.holdout_dir,prehistory_dir=a.prehistory_dir,
        config_path=a.config,model_bundle=a.bundle,
        model_metadata=a.metadata,protocol_path=a.protocol,
        seal_path=a.seal,fold_audit_path=a.fold_audit,
        release_gate_path=a.release_gate,output_dir=a.out_dir)
    print(json.dumps({k:r[k] for k in
        ("three_mode_shared_risk_paper_replayed",
         "independent_oos_verified","errors")},sort_keys=True))
    return 0 if r["three_mode_shared_risk_paper_replayed"] else 2

if __name__=="__main__":
    raise SystemExit(main())
