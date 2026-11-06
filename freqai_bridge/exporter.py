"""Bind actual FreqAI dataframe outputs to the canonical candle window."""

import json
from numbers import Integral
import os
import re
from pathlib import Path
import tempfile

from pipeline.decision import _canonical, _prediction
from pipeline.values import number, stamp

TARGET = "&-future_return"


def make_prediction(dataframe, canonical_window, provenance, available_at_ms):
    """Validate a real predicted frame and trainer-provided provenance.

    trainedThroughMs includes the last future label used during training, not
    merely the last feature row. It must be supplied by the training process;
    neither the current clock nor the FreqAI identifier is a training cutoff.
    """
    now = stamp(available_at_ms)
    latest = _canonical(canonical_window, now)
    if not isinstance(provenance, dict):
        raise ValueError("Training provenance is unavailable")
    training_dataset = provenance.get("trainingDatasetVersion")
    if not isinstance(training_dataset, str) or not re.fullmatch(r"sha256:[0-9a-f]{64}", training_dataset):
        raise ValueError("Missing training dataset provenance")
    # Training lineage is static; the current inference-window hash is derived
    # below from actual matching OHLCV rather than copied from model metadata.
    if "datasetVersion" in provenance and provenance["datasetVersion"] != canonical_window["datasetVersion"]:
        raise ValueError("Explicit inference dataset binding differs from canonical data")
    trained, completed = stamp(provenance["trainedThroughMs"]), stamp(provenance["trainingCompletedAtMs"])
    if not trained <= completed <= now:
        raise ValueError("Invalid training completion time")
    rows = canonical_window["candles"]
    if len(dataframe) < len(rows) or not {"date", "open", "high", "low", "close", "volume", TARGET, "do_predict"} <= set(dataframe.columns):
        raise ValueError("Missing FreqAI output or candle columns")
    selected = dataframe.tail(len(rows))
    for (_, actual), expected in zip(selected.iterrows(), rows):
        date = actual["date"]
        if getattr(date, "tzinfo", None) is None:
            raise ValueError("Freqtrade dates must be timezone-aware")
        timestamp = int(date.timestamp() * 1000)
        if timestamp != expected["openTimeMs"]:
            raise ValueError("FreqAI and canonical candle times differ")
        for field in ("open", "high", "low", "close", "volume"):
            if number(str(actual[field])) != number(expected[field]):
                raise ValueError("FreqAI and canonical OHLCV differ")
    predicted = selected.iloc[-1]
    accepted = predicted["do_predict"]
    if isinstance(accepted, bool) or not isinstance(accepted, Integral) or int(accepted) != 1:
        raise ValueError("FreqAI did not accept this prediction")
    result = {"schemaVersion": 1, "exchange": "binance", "marketType": "USDT_PERPETUAL", "symbol": "BTCUSDT",
              "timeframe": "15m", "candleOpenTimeMs": latest["openTimeMs"], "candleCloseTimeMs": latest["closeTimeMs"],
              "availableAtMs": now, "trainedThroughMs": trained, "modelVersion": provenance["modelVersion"],
              "strategyVersion": provenance["strategyVersion"], "predictedReturn": str(number(str(predicted[TARGET]), signed=True)),
              "doPredict": 1, "datasetVersion": canonical_window["datasetVersion"],
              "trainingDatasetVersion": training_dataset, "trainingCompletedAtMs": completed}
    _prediction(result, canonical_window, latest, now)
    return result


def read_context(path):
    with open(path, "rb") as source:
        data = source.read(2_097_153)
    if len(data) > 2_097_152:
        raise ValueError("Context file exceeds supported size")
    value = json.loads(data)
    if not isinstance(value, dict):
        raise ValueError("Invalid context object")
    return value


def write_artifact(path, artifact):
    """Replace only the configured JSON output atomically, with no model loading."""
    target = Path(path)
    if target.suffix != ".json":
        raise ValueError("Prediction output must be a JSON file")
    data = json.dumps(artifact, allow_nan=False, sort_keys=True, separators=(",", ":")).encode()
    if len(data) > 65_536:
        raise ValueError("Prediction artifact is too large")
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=target.parent, prefix=".freqai-", suffix=".json", delete=False) as output:
            temporary = Path(output.name)
            output.write(data)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, target)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
