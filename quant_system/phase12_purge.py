"""Phase 12: mandatory, causal four-M15-candle label purge before fit().

Intercepts the actual chronological FreqAI train/test split, not a copy made
after LightGBM has already learned overlapping future targets. The original
CORE strategy, independent AI inference thresholds, risk router, leverage,
portfolio slots and native no-order protections are untouched.
"""
from __future__ import annotations
from datetime import timezone

M15=900000

class PurgeError(ValueError):
    pass

def require(ok,reason):
    if not ok:raise PurgeError(reason)

def stamp(value):
    require(getattr(value,'tzinfo',None) is not None and
            value.utcoffset() is not None,
            'PHASE12_NAIVE_SPLIT_TIMESTAMP')
    n=int(value.timestamp()*1000)
    require(n>0 and n%M15==0,'PHASE12_INVALID_SPLIT_TIMESTAMP')
    return n

def purge_train_test_split(dk,data_dictionary,*,horizon):
    """Drop TRAIN suffix with label_end >= first TEST opening.

    Called immediately after pinned FreqAI 2026.9
    dk.make_train_test_datasets() and BEFORE label/scaler fitting.
    Keeps 20% TEST untouched; preserves original trained row identities on
    dk for independent Phase12 fit and canonical OHLCV verification.
    """
    require(type(horizon) is int and horizon==4,
            'PHASE12_UNAPPROVED_LABEL_HORIZON')
    dd=data_dictionary
    keys=('train_features','train_labels','train_weights',
          'test_features','test_labels','test_weights')
    require(isinstance(dd,dict) and all(k in dd for k in keys),
            'PHASE12_MISSING_PREPURGE_DATA_DICTIONARY')
    train=dd['train_features']
    labels=dd['train_labels']
    test=dd['test_features']
    test_labels=dd['test_labels']
    train_ids=list(train.index)
    test_ids=list(test.index)
    filtered_ids=list(dk.train_dates.index)
    require(len(train_ids)>=12 and len(test_ids)>=1 and
            len(train_ids)==len(labels)==len(dd['train_weights']) and
            len(test_ids)==len(test_labels)==len(dd['test_weights']) and
            train_ids==list(labels.index) and
            test_ids==list(test_labels.index) and
            len(filtered_ids)==len(train_ids)+len(test_ids) and
            filtered_ids==train_ids+test_ids and
            len(set(filtered_ids))==len(filtered_ids),
            'PHASE12_PREPURGE_SPLIT_IDENTITY_INVALID')
    times=[stamp(dk.train_dates.loc[index]) for index in filtered_ids]
    require(all(b>a for a,b in zip(times,times[1:])),
            'PHASE12_NONCHRONOLOGICAL_SPLIT')
    test_open=times[len(train_ids)]
    keep=sum(t+horizon*M15<test_open for t in times[:len(train_ids)])
    require(keep>=8 and
            all(t+horizon*M15<test_open for t in times[:keep]) and
            all(t+horizon*M15>=test_open for t in times[keep:len(train_ids)]),
            'PHASE12_INVALID_PURGE_BOUNDARY')
    # The test set stays exactly as FreqAI's chronological 20% split.
    # Only the end of TRAIN is removed, in all three fitted arrays.
    dd['train_features']=train.iloc[:keep].copy()
    dd['train_labels']=labels.iloc[:keep].copy()
    dd['train_weights']=dd['train_weights'][:keep]
    require(len(dd['train_features'])==len(dd['train_labels'])==
            len(dd['train_weights'])==keep and
            list(dd['train_features'].index)==train_ids[:keep] and
            list(dd['train_labels'].index)==train_ids[:keep],
            'PHASE12_POSTPURGE_ROW_MISMATCH')
    dk._phase12_purged_train_source_indices=list(train_ids[:keep])
    dk._phase12_purge_meta=dict(
        horizon_candles=horizon,
        original_train_rows=len(train_ids),
        fitted_train_rows=keep,
        removed_train_rows=len(train_ids)-keep,
        first_test_feature_open_ms=test_open,
        last_train_label_end_ms=times[keep-1]+horizon*M15,
    )
    return dd
