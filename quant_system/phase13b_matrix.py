"""Phase13B: lossless research-only X/y capture at actual LightGBM calls.

NPZ archives contain ordered float64 values, ordered names, candle timestamp
and unmodified model inputs. SHA-256 protects bytes; no pickle is loaded.
Training rows are independently mapped to Phase12 source candle identities.
Captures are evidence, not a claim of scaler/feature causality or OOS.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path

import numpy as np

M15_MS = 900000

class MatrixEvidenceError(ValueError):
    pass

def check(ok, code):
    if not ok:
        raise MatrixEvidenceError(code)

def matrix_digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()

def _numeric(value, expected, code):
    try:
        array = np.asarray(value, dtype=np.float64)
    except (TypeError, ValueError, OverflowError) as exc:
        raise MatrixEvidenceError(code) from exc
    check(array.ndim == 1 and len(array) == expected and
          bool(np.isfinite(array).all()), code)
    return array

def _timestamps(timestamps, expected):
    try:
        times = np.asarray(timestamps, dtype=np.int64)
    except (TypeError, ValueError, OverflowError) as exc:
        raise MatrixEvidenceError("MATRIX_INVALID_TIME") from exc
    check(times.ndim == 1 and len(times) == expected and
          bool((times > 0).all()) and bool((times % M15_MS == 0).all()) and
          bool((times[1:] > times[:-1]).all()),
          "MATRIX_INVALID_TIME")
    return times

def record_matrix(directory, *, stage, fold, model_sha, features, timestamps,
                  labels=None, weights=None, flags=None):
    """Fail-closed write of ONE actual ordered LightGBM call's X matrix."""
    from pandas import DataFrame
    check(stage in ("FIT_TRAIN", "FIT_TEST", "PREDICT"),
          "MATRIX_INVALID_STAGE")
    check(isinstance(fold, str) and fold and
          isinstance(model_sha, str) and len(model_sha) == 71 and
          model_sha.startswith("sha256:") and
          all(c in "0123456789abcdef" for c in model_sha[7:]),
          "MATRIX_INVALID_MODEL_ID")
    check(isinstance(features, DataFrame) and
          bool(len(features)) and bool(len(features.columns)) and
          features.columns.is_unique and
          all(isinstance(c, str) and c and not c.startswith("&")
              for c in features.columns), "MATRIX_TARGET_OR_SCHEMA")
    try:
        values = features.to_numpy(dtype=np.float64, copy=True)
    except (TypeError, ValueError, OverflowError) as exc:
        raise MatrixEvidenceError("MATRIX_INVALID_VALUES") from exc
    check(values.ndim == 2 and bool(np.isfinite(values).all()),
          "MATRIX_NONFINITE_VALUES")
    times = _timestamps(timestamps, len(values))
    if stage == "PREDICT":
        check(labels is None and weights is None and flags is not None,
              "MATRIX_PREDICT_INPUTS_INVALID")
        y = np.array([], dtype=np.float64)
        w = np.array([], dtype=np.float64)
        marks = _numeric(flags, len(values), "MATRIX_INVALID_FLAGS")
        check(all(v in (1., 0., -1., -2.) for v in marks),
              "MATRIX_INVALID_FLAGS")
    else:
        check(flags is None and labels is not None and weights is not None,
              "MATRIX_FIT_INPUTS_INVALID")
        y = _numeric(labels, len(values), "MATRIX_INVALID_LABELS")
        w = _numeric(weights, len(values), "MATRIX_INVALID_WEIGHTS")
        check(bool((w >= 0).all()), "MATRIX_INVALID_WEIGHTS")
        marks = np.array([], dtype=np.float64)
    names = list(features.columns)
    key = json.dumps([stage, fold, model_sha, times.tolist()],
                     sort_keys=True, separators=(",", ":"))
    ident = hashlib.sha256(key.encode("utf8")).hexdigest()[:24]
    name = f"{stage.lower()}-{ident}.npz"
    dest = Path(directory) / "phase13b-matrices" / name
    check(not dest.is_symlink() and not dest.exists(),
          "MATRIX_DUPLICATE_CAPTURE")
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(".partial")
    check(not tmp.exists() and not tmp.is_symlink(),
          "MATRIX_DUPLICATE_CAPTURE")
    try:
        with tmp.open("xb") as stream:
            np.savez_compressed(stream, values=values,
                columns=np.asarray(names, dtype=str),
                timestamps=times, labels=y, weights=w, flags=marks)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(tmp, dest)
    finally:
        tmp.unlink(missing_ok=True)
    path = "phase13b-matrices/" + name
    return dict(stage=stage, fold_model_name=fold, model_sha256=model_sha,
        path=path, sha256=matrix_digest(dest),
        first_open_ms=int(times[0]), last_open_ms=int(times[-1]),
        n_rows=len(times), n_features=len(names), columns=names,
        feature_schema_sha256="sha256:" + hashlib.sha256(json.dumps(
            names, separators=(",", ":")).encode("utf8")).hexdigest())

def read_matrix(directory, event):
    """Independent replay of full ordered data; np.load never unpickles."""
    check(isinstance(event, dict), "MATRIX_INVALID_MANIFEST")
    relative = event.get("path")
    check(isinstance(relative, str) and
          relative.startswith("phase13b-matrices/") and
          relative.endswith(".npz") and
          "/" not in relative[len("phase13b-matrices/"):] and
          ".." not in relative, "MATRIX_UNSAFE_PATH")
    path = Path(directory) / relative
    check(path.is_file() and not path.is_symlink(), "MATRIX_MISSING_ARCHIVE")
    check(matrix_digest(path) == event.get("sha256"), "MATRIX_SHA_MISMATCH")
    try:
        with np.load(path, allow_pickle=False) as data:
            check(set(data.files) == {
                "values", "columns", "timestamps", "labels", "weights", "flags"},
                "MATRIX_ARCHIVE_SCHEMA_INVALID")
            values = np.array(data["values"], dtype=np.float64)
            columns = [str(x) for x in data["columns"].tolist()]
            times = np.array(data["timestamps"], dtype=np.int64)
            labels = np.array(data["labels"], dtype=np.float64)
            weights = np.array(data["weights"], dtype=np.float64)
            flags = np.array(data["flags"], dtype=np.float64)
    except (OSError, TypeError, ValueError, KeyError) as exc:
        raise MatrixEvidenceError("MATRIX_ARCHIVE_INVALID") from exc
    check(values.ndim == 2 and values.shape == (
          event.get("n_rows"), event.get("n_features")) and
          bool(np.isfinite(values).all()) and columns == event.get("columns") and
          len(set(columns)) == len(columns) and
          all(c and not c.startswith("&") for c in columns) and
          "sha256:" + hashlib.sha256(json.dumps(
              columns, separators=(",", ":")).encode("utf8")).hexdigest() ==
          event.get("feature_schema_sha256"),
          "MATRIX_SCHEMA_MISMATCH")
    _timestamps(times, len(values))
    check(int(times[0]) == event.get("first_open_ms") and
          int(times[-1]) == event.get("last_open_ms"),
          "MATRIX_TIMESTAMP_MISMATCH")
    stage = event.get("stage")
    if stage == "PREDICT":
        check(len(labels) == len(weights) == 0 and
              len(flags) == len(times) and
              all(f in (1., 0., -1., -2.) for f in flags),
              "MATRIX_PREDICT_ROW_MISMATCH")
    else:
        check(stage in ("FIT_TRAIN", "FIT_TEST") and
              len(flags) == 0 and len(labels) == len(weights) == len(times)
              and bool(np.isfinite(labels).all()) and
              bool(np.isfinite(weights).all()) and
              bool((weights >= 0).all()),
              "MATRIX_FIT_ROW_MISMATCH")
    return dict(values=values, columns=columns, timestamps=times.tolist(),
                labels=labels.tolist(), weights=weights.tolist(),
                flags=flags.tolist())

def append_event(path, event):
    path = Path(path)
    check(path.is_absolute() and path.suffix == ".jsonl" and
          not path.is_symlink(), "MATRIX_INVALID_EVENT_PATH")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf8") as f:
        f.write(json.dumps(event, sort_keys=True, allow_nan=False) + "\n")
        f.flush()
        os.fsync(f.fileno())
