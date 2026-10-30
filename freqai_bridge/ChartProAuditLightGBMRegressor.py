"""Instrument actual FreqAI LightGBM train()/predict(), PAPER-ONLY.

Delegates all model fitting and predictions to pinned upstream LightGBMRegressor.
Hashes the fitted in-memory Booster and captures conservative available-label
cutoff; this does NOT attest the actual train/test split or purging.
"""
from __future__ import annotations
import csv
import os
import math
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
        # Phase 12 captures the actual post-split feature/label row IDs
        # *inside fit()*; this unfiltered frame is only an index/date/target
        # reference, not an independently certified train selection.
        phase12 = os.environ.get('PHASE12_SAMPLES_CSV')
        if phase12:
            if not os.environ.get('PHASE8_LINEAGE_CSV'):
                raise EvidenceError('PHASE12_REQUIRES_PHASE8_MODEL_LINEAGE')
            if self.freqai_info.get('data_split_parameters',{}).get('shuffle',False) is not False or (
                self.freqai_info.get('feature_parameters',{}).get('shuffle_after_split',False)
            ) is not False or (
                self.freqai_info.get('feature_parameters',{}).get('reverse_train_test_order',False)
            ) is not False:
                raise EvidenceError('PHASE12_REQUIRES_CHRONOLOGICAL_SPLIT')
            self._phase12_unfiltered=unfiltered_df[['date','close','&-future_return']].copy()
            if not self._phase12_unfiltered.index.is_unique:
                raise EvidenceError('PHASE12_NONUNIQUE_RAW_INDEX')
        try:
            return super().train(unfiltered_df,pair,dk,**kwargs)
        finally:
            if hasattr(self,'_phase12_unfiltered'):
                del self._phase12_unfiltered

    def fit(self,data_dictionary,dk,**kwargs):
        """Observe actual LightGBM X/y + validation set at the model.fit boundary."""
        fitted=super().fit(data_dictionary,dk,**kwargs)
        destination=os.environ.get('PHASE12_SAMPLES_CSV')
        if not destination:
            return fitted
        raw=getattr(self,'_phase12_unfiltered',None)
        meta=getattr(self,'_phase8_train_meta',None)
        if raw is None or meta is None or dk.model_filename!=meta['fold_model_name']:
            raise EvidenceError('PHASE12_MISSING_FIT_DATA_PROVENANCE')
        horizon=meta['configured_label_horizon_candles']
        date_index=dk.train_dates
        if not date_index.index.is_unique:
            raise EvidenceError('PHASE12_NONUNIQUE_FILTERED_TRAIN_DATES')
        train=data_dictionary['train_features']
        test=data_dictionary['test_features']
        train_labels=data_dictionary['train_labels']
        test_labels=data_dictionary['test_labels']
        if not train.index.is_unique or not test.index.is_unique or (
            not train.index.equals(train_labels.index)
        ) or not test.index.equals(test_labels.index) or (
            len(train)==0 or len(test)==0
        ) or not train.index.isin(date_index.index).all() or (
            not test.index.isin(date_index.index).all()
        ) or not train.index.isin(raw.index).all() or (
            not test.index.isin(raw.index).all()
        ):
            raise EvidenceError('PHASE12_FIT_INDEX_IDENTITY_UNVERIFIED')
        if len(set(train.index)&set(test.index)):
            raise EvidenceError('PHASE12_OVERLAPPING_TRAIN_TEST_INDICES')
        path=Path(destination)
        if not path.is_absolute() or path.suffix!='.csv' or path.is_symlink():
            raise EvidenceError('INVALID_PHASE12_SAMPLES_PATH')
        from quant_system.phase12_training_audit import ROWS
        model_hash=booster_sha256(fitted)
        rows=[]
        expected_future=raw['close'].shift(-horizon)
        for kind,features in (('TRAIN',train),('TEST',test)):
            for index in features.index:
                moment=date_index.loc[index]
                source=raw.loc[index]
                if _ms(moment)!=_ms(source['date']):
                    raise EvidenceError('PHASE12_FILTERED_DATE_MISMATCH')
                stamp=_ms(moment)
                close=float(source['close'])
                future=float(expected_future.loc[index])
                label=float(source['&-future_return'])
                recomputed=future/close-1
                if not all(math.isfinite(v) for v in (close,future,label,recomputed)) or (
                    close<=0 or future<=0 or not math.isclose(
                        label,recomputed,rel_tol=1e-10,abs_tol=1e-10
                    )
                ):
                    raise EvidenceError('PHASE12_RAW_LABEL_MISMATCH')
                label_end=stamp+horizon*M15_MS
                if label_end>=meta['training_end_ms']:
                    raise EvidenceError('PHASE12_TRAINING_WINDOW_LABEL_LOOKAHEAD')
                rows.append(dict(fold_model_name=meta['fold_model_name'],
                    model_identifier=meta['model_identifier'],model_sha256=model_hash,
                    row_kind=kind,feature_open_ms=stamp,label_end_ms=label_end,
                    observed_raw_label=format(label,'.17g'),
                    expected_recomputed_label=format(recomputed,'.17g'),
                    feature_close=format(close,'.17g'),future_close=format(future,'.17g'),
                    training_end_ms=meta['training_end_ms'],horizon_candles=horizon))
        path.parent.mkdir(parents=True,exist_ok=True)
        exists=path.exists()
        with path.open('a' if exists else 'w',newline='',encoding='utf8') as stream:
            writer=csv.DictWriter(stream,fieldnames=ROWS)
            if not exists:writer.writeheader()
            writer.writerows(rows)
            stream.flush()
            os.fsync(stream.fileno())
        return fitted

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
