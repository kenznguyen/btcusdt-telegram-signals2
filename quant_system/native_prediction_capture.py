"""Capture FreqAI *actual native backtest* forecasts into an offline trace.

Never creates a prediction, never fits a model, never submits a trade. This
artifact is not a signed training-cutoff / OOS quality certificate.
"""
from __future__ import annotations

import csv
import math
import os
from pathlib import Path

from freqai_bridge.exporter import TARGET

FIELDS=('open_time','open','high','low','close','volume','predicted_return',
        'do_predict','model_identifier','source','pair')


def capture_predictions(frame, destination, model_identifier, *, pair='BTC/USDT:USDT'):
    """Append only observed FreqAI dataframe forecasts, including abstentions.

    If called repeatedly by a native backtest, duplicate timestamps are
    rejected at paper replay unless predictions agree exactly. This protects
    against leaked training rows or mixed model windows changing a signal.
    """
    if (not isinstance(model_identifier,str) or not model_identifier.strip() or
        pair!='BTC/USDT:USDT'):
        raise ValueError('INVALID_NATIVE_MODEL_OR_PAIR')
    required={'date','open','high','low','close','volume',TARGET,'do_predict'}
    if frame is None or not required.issubset(frame.columns):
        raise ValueError('MISSING_NATIVE_FREQAI_PREDICTIONS')
    rows=[]
    for _, item in frame.iterrows():
        timestamp=item['date']
        if getattr(timestamp,'tzinfo',None) is None:
            raise ValueError('NAIVE_NATIVE_FREQAI_TIMESTAMP')
        try:
            opened=int(timestamp.timestamp()*1000)
            if opened%900_000:
                raise ValueError('UNALIGNED_NATIVE_FREQAI_CANDLE')
            raw_flag=float(item['do_predict'])
            if not math.isfinite(raw_flag) or not raw_flag.is_integer() or raw_flag>1 or raw_flag < -10:
                raise ValueError('INVALID_NATIVE_DO_PREDICT')
            flag=int(raw_flag)
            values=[float(item[name]) for name in ('open','high','low','close','volume')]
            if not all(math.isfinite(v) for v in values):
                raise ValueError('INVALID_NATIVE_PREDICTION_OHLCV')
            forecast=item[TARGET]
            if flag==1:
                forecast=float(forecast)
                if not math.isfinite(forecast):
                    raise ValueError('NONFINITE_ACCEPTED_NATIVE_FORECAST')
            else:
                # FreqAI uses -1/-2/0 for rejected predictions. Never trade.
                forecast='' 
            rows.append(dict(open_time=opened,
                **{name:format(v,'.17g') for name,v in zip(
                    ('open','high','low','close','volume'),values)},
                predicted_return=format(forecast,'.17g') if flag==1 or forecast!='' else '',
                do_predict=flag, model_identifier=model_identifier,
                source='freqai-native-backtest',pair=pair))
        except (TypeError,OverflowError,KeyError) as error:
            raise ValueError('INVALID_NATIVE_FREQAI_ROW') from error
    if not rows:
        raise ValueError('NO_NATIVE_FREQAI_CANDLES')
    dest=Path(destination)
    if not dest.is_absolute() or dest.suffix!='.csv' or dest.is_symlink():
        raise ValueError('INVALID_NATIVE_CAPTURE_PATH')
    dest.parent.mkdir(parents=True,exist_ok=True)
    existed=dest.exists()
    with dest.open('a' if existed else 'w',encoding='utf-8',newline='') as source:
        writer=csv.DictWriter(source,fieldnames=FIELDS)
        if not existed:
            writer.writeheader()
        writer.writerows(rows)
        source.flush()
        os.fsync(source.fileno())
    return len(rows)