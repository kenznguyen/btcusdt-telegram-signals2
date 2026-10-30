"""Restore FreqAI fit-row dates after the pinned DataSieve pipeline resets indices.

Research instrumentation only. Uses actual dk.train_dates (post feature/label
filter), pinned chronological sklearn train_test_split, and the approved
feature pipeline. Proves that inverse-transformed fitted model labels match
their original OHLCV target in chronological partition order. Any ambiguity
or sample-count mismatch fails closed.
"""
from __future__ import annotations
import math

class RowIdentityError(ValueError):
    pass

def require(value,reason):
    if not value:
        raise RowIdentityError(reason)

def _label_vector(frame):
    values=[]
    for i in range(len(frame)):
        value=frame.iloc[i]
        if hasattr(value,'iloc'):
            value=value.iloc[0]
        elif isinstance(value,(tuple,list)):
            require(len(value)==1,'PHASE12_INVALID_INVERSE_LABEL_ROW')
            value=value[0]
        try:
            value=float(value)
        except (ValueError,TypeError,OverflowError) as exc:
            raise RowIdentityError('PHASE12_INVALID_INVERSE_LABEL_ROW') from exc
        require(math.isfinite(value),'PHASE12_INVALID_INVERSE_LABEL_ROW')
        values.append(value)
    return values

def resolve_fit_row_ids(dk,data_dictionary,raw_labels,*,split_fraction):
    """Return source indices for actual model TRAIN and TEST samples.

    DataSieve's _convert_back_to_df() creates new RangeIndex DataFrames,
    independently of the raw candle indices. Comparing postfit RangeIndex
    with dk.train_dates.index is wrong. Instead reconstruct the *approved*
    FreqAI chronological split, use DI's actual validation mask to locate
    any dropped validation rows, and verify 1:1 inverse label values at fit.

    Reject new/preprocessing transforms until independently audited.
    """
    require(type(split_fraction) is float and
            math.isclose(split_fraction,.2,rel_tol=0,abs_tol=1e-12),
            'PHASE12_UNAPPROVED_SPLIT_FRACTION')
    dates=dk.train_dates
    idx=list(dates.index)
    require(len(idx)>=10 and len(set(idx))==len(idx),
            'PHASE12_INVALID_FILTERED_DATES')
    require(set(idx).issubset(raw_labels.keys()),'PHASE12_UNKNOWN_SOURCE_INDEX')
    pipeline=dk.feature_pipeline
    steps=[step[0] for step in pipeline.steps]
    require(steps==['const','scaler','di'],
            'PHASE12_UNAPPROVED_FEATURE_PIPELINE')
    ntest=math.ceil(len(idx)*split_fraction)
    train_source=idx[:-ntest]
    test_source=idx[-ntest:]
    xtrain=data_dictionary['train_features']
    xtest=data_dictionary['test_features']
    ytrain=data_dictionary['train_labels']
    ytest=data_dictionary['test_labels']
    require(len(train_source)==len(xtrain)==len(ytrain) and
            len(xtest)==len(ytest) and
            len(data_dictionary['train_weights'])==len(xtrain) and
            len(data_dictionary['test_weights'])==len(xtest),
            'PHASE12_FIT_SAMPLE_COUNT_MISMATCH')
    di=pipeline['di']
    require(di is not None and hasattr(di,'di_values') and
            hasattr(di,'di_threshold') and
            len(di.di_values)==ntest,
            'PHASE12_DI_MASK_IDENTITY_UNVERIFIED')
    test_mask=[]
    for value in di.di_values:
        try:
            val=float(value)
        except (TypeError,ValueError,OverflowError) as exc:
            raise RowIdentityError('PHASE12_DI_MASK_IDENTITY_UNVERIFIED') from exc
        require(math.isfinite(val),'PHASE12_DI_MASK_IDENTITY_UNVERIFIED')
        test_mask.append(val<float(di.di_threshold))
    test_fitted=[index for index,keep in zip(test_source,test_mask) if keep]
    require(len(xtest)==len(test_fitted),
            'PHASE12_DI_MASK_IDENTITY_UNVERIFIED')
    # The pinned label transform is a one-column MinMaxScaler.
    # Verify model's actual transformed y, not just the pre-split labels.
    label_steps=[item[0] for item in dk.label_pipeline.steps]
    require(label_steps==['scaler'], 'PHASE12_UNAPPROVED_LABEL_PIPELINE')
    for source_ids,labels in ((train_source,ytrain),(test_fitted,ytest)):
        restored=dk.label_pipeline.inverse_transform(labels)[0]
        observed=_label_vector(restored)
        require(len(observed)==len(source_ids),
                'PHASE12_FIT_INVERSE_LABEL_COUNT_MISMATCH')
        for index,value in zip(source_ids,observed):
            expected=float(raw_labels[index])
            require(math.isfinite(expected) and math.isclose(
                    value,expected,rel_tol=1e-8,abs_tol=1e-10),
                    'PHASE12_FIT_LABEL_ORDER_MISMATCH')
    return list(train_source),list(test_fitted)
