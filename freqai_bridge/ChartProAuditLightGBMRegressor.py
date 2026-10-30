"""Instrument actual FreqAI LightGBM train()/predict(), PAPER-ONLY.

Delegates all model fitting and predictions to pinned upstream LightGBMRegressor.
Hashes the fitted in-memory Booster and captures conservative available-label
cutoff; this does NOT attest the actual train/test split or purging.
"""
from __future__ import annotations
import csv
import os
from pathlib import Path
from freqtrade.freqai.prediction_models.LightGBMRegressor import LightGBMRegressor
from quant_system.phase8_model_evidence import FIELDS,booster_sha256,EvidenceError

M15_MS=900000

def _ms(value):
    if getattr(value,'tzinfo',None) is None:
        raise EvidenceError('NAIVE_FREQAI_MODEL_TIMESTAMP')
    return int(value.timestamp()*1000)

class ChartProAuditLightGBMRegressor(LightGBMRegressor):
    def train(self,unfiltered_df,pair,dk,**kwargs):
        if not os.environ.get('PHASE8_LINEAGE_CSV'):
            return super().train(unfiltered_df,pair,dk,**kwargs)
        if pair!='BTC/USDT:USDT':
            raise EvidenceError('INVALID_PHASE8_PAIR')
        horizon=self.freqai_info['feature_parameters']['label_period_candles']
        if type(horizon) is not int or not 1<=horizon<=48:
            raise EvidenceError('INVALID_PHASE8_LABEL_HORIZON')
        if '&-future_return' not in unfiltered_df or 'date' not in unfiltered_df:
            raise EvidenceError('MISSING_REAL_FREQAI_TRAINING_LABELS')
        valid=unfiltered_df.loc[unfiltered_df['&-future_return'].notna(),'date']
        if valid.empty:
            raise EvidenceError('NO_OBSERVED_TRAINING_LABELS')
        trainend=int(self.training_timerange.stopts)*1000
        featureend=_ms(valid.max())
        labelend=featureend+horizon*M15_MS
        if labelend>=trainend:
            raise EvidenceError('PHASE8_TRAINING_LABEL_LOOKAHEAD')
        self._phase8_train_meta=dict(
            training_end_ms=trainend,latest_train_feature_ms=featureend,
            latest_observed_label_end_ms=labelend,
            configured_label_horizon_candles=horizon,
            fold_model_name=dk.model_filename,
            model_identifier=self.freqai_info['identifier'])
        return super().train(unfiltered_df,pair,dk,**kwargs)

    def predict(self,unfiltered_df,dk,**kwargs):
        predictions,flags=super().predict(unfiltered_df,dk,**kwargs)
        destination=os.environ.get('PHASE8_LINEAGE_CSV')
        if not destination:
            return predictions,flags
        meta=getattr(self,'_phase8_train_meta',None)
        if meta is None or dk.model_filename!=meta['fold_model_name']:
            raise EvidenceError('MISSING_ACTUAL_MODEL_TRAINING_METADATA')
        if len(unfiltered_df)!=len(flags):
            raise EvidenceError('MISMATCHED_NATIVE_PREDICTION_FLAGS')
        path=Path(destination)
        if not path.is_absolute() or path.suffix!='.csv' or path.is_symlink():
            raise EvidenceError('INVALID_PHASE8_TRACE_PATH')
        model_sha=booster_sha256(self.model)
        rows=[]
        for moment,flag in zip(unfiltered_df['date'],flags):
            candle=_ms(moment)
            if candle<meta['training_end_ms'] or candle%M15_MS:
                raise EvidenceError('MODEL_PREDICTION_BEFORE_TRAIN_END')
            value=int(flag)
            if value not in (1,0,-1,-2):
                raise EvidenceError('INVALID_NATIVE_MODEL_PREDICT_FLAG')
            rows.append(dict(open_time=candle,model_sha256=model_sha,
                             do_predict=value,**meta))
        path.parent.mkdir(parents=True,exist_ok=True)
        exists=path.exists()
        with path.open('a' if exists else 'w',newline='',encoding='utf8') as stream:
            writer=csv.DictWriter(stream,fieldnames=FIELDS)
            if not exists: writer.writeheader()
            writer.writerows(rows)
            stream.flush();os.fsync(stream.fileno())
        return predictions,flags
