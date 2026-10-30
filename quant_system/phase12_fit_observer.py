"""Preserve the already fitted FreqAI booster when research-only logging fails.

Never certify missing observation data. All observer failures are persisted and
cause native research and the independent Phase12 gate to fail closed.
The observer is executed only AFTER upstream LightGBM.fit has succeeded.
"""
from __future__ import annotations
import json
import os
from pathlib import Path


def read_observer_errors(path):
    path=Path(path)
    if not path.exists():
        return []
    out=[]
    with path.open('r',encoding='utf8') as f:
        for line in f:
            if not line.strip():
                raise ValueError('INVALID_PHASE12_OBSERVER_ERROR_ROW')
            try:
                row=json.loads(line)
            except (ValueError,TypeError) as e:
                raise ValueError('INVALID_PHASE12_OBSERVER_ERROR_ROW') from e
            if (not isinstance(row,dict) or
                    not isinstance(row.get('fold_model_name'),str) or
                    not row['fold_model_name'] or
                    not isinstance(row.get('error_code'),str) or
                    not row['error_code'] or
                    not isinstance(row.get('error_type'),str) or
                    not row['error_type']):
                raise ValueError('INVALID_PHASE12_OBSERVER_ERROR_ROW')
            out.append(row)
    return out


def observe_post_fit(fitted_model, observer, diagnostics_path, fold_model_name):
    """Return exact fitted booster regardless of an OBSERVER failure.

    This preserves the original research prediction path without treating
    missing or broken Phase12 evidence as an audit success. OSError when
    persisting an observation error deliberately propagates (fail closed).
    """
    if not callable(observer):
        raise ValueError('INVALID_PHASE12_OBSERVER')
    if not isinstance(fold_model_name,str) or not fold_model_name:
        raise ValueError('INVALID_PHASE12_FOLD_ID')
    path=Path(diagnostics_path)
    if not path.is_absolute() or path.suffix!='.jsonl' or path.is_symlink():
        raise ValueError('INVALID_PHASE12_DIAGNOSTICS_PATH')
    try:
        observer()
    except Exception as exc:
        error_code=str(exc)[:180] or 'UNSPECIFIED_PHASE12_OBSERVATION_FAILURE'
        row=dict(fold_model_name=fold_model_name,error_type=type(exc).__name__,
                 error_code=error_code)
        path.parent.mkdir(parents=True,exist_ok=True)
        with path.open('a',encoding='utf8') as f:
            f.write(json.dumps(row,sort_keys=True,allow_nan=False)+'\n')
            f.flush()
            os.fsync(f.fileno())
    return fitted_model
