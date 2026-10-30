"""Phase12 pre-download smoke: exercise the pinned native FreqAI split with real pandas rows.

This does NOT certify actual historical folds, OOS performance or trading.
It proves the pinned upstream split leaks four-candle labels at the boundary
without a purge, and that the Phase12 hook removes exactly those TRAIN rows.
"""
from __future__ import annotations

import json
import math

import numpy as np
import pandas as pd
from freqtrade.freqai.data_kitchen import FreqaiDataKitchen

from quant_system.phase12_purge import purge_train_test_split


class SplitHarness:
    """Use the REAL FreqAI 2026.9 splitter without exchange/strategy startup."""

    def __init__(self, dates):
        split = {"test_size": 0.2, "shuffle": False}
        features = {"weight_factor": 0, "shuffle_after_split": False,
                    "reverse_train_test_order": False}
        self.freqai_config = {"data_split_parameters": split,
                              "feature_parameters": features}
        self.config = {"freqai": self.freqai_config}
        self.train_dates = dates

    def make_train_test_datasets(self, filtered_dataframe, labels):
        return FreqaiDataKitchen.make_train_test_datasets(
            self, filtered_dataframe, labels
        )

    def build_data_dictionary(self, train_features, test_features,
                              train_labels, test_labels,
                              train_weights, test_weights):
        return {
            "train_features": train_features,
            "test_features": test_features,
            "train_labels": train_labels,
            "test_labels": test_labels,
            "train_weights": train_weights,
            "test_weights": test_weights,
            "train_dates": self.train_dates,
        }


def check(condition, code):
    if not condition:
        raise AssertionError(code)


def run_smoke():
    # 120 candles, of which the final four have no future return label.
    candle_count = 120
    closes = [30000.0 + i * 2.0 + math.sin(i / 5.0)
              for i in range(candle_count)]
    valid = candle_count - 4
    source_ids = pd.RangeIndex(3000, 3000 + valid)
    dates = pd.Series(pd.date_range(
        "2026-09-01T00:00:00Z", periods=valid, freq="15min"
    ), index=source_ids)
    x = pd.DataFrame({"%-close": closes[:valid]}, index=source_ids)
    y = pd.DataFrame({"&-future_return": [
        closes[i + 4] / closes[i] - 1.0 for i in range(valid)
    ]}, index=source_ids)
    kitchen = SplitHarness(dates)

    # RED: the native chronological 80/20 split itself has no label purge.
    raw = kitchen.make_train_test_datasets(x, y)
    first_test = dates.loc[raw["test_features"].index[0]]
    last_raw_train = dates.loc[raw["train_features"].index[-1]]
    check(last_raw_train + pd.Timedelta(minutes=60) >= first_test,
          "PHASE12_SMOKE_UPSTREAM_BASELINE_UNEXPECTEDLY_PURGED")
    original_train_count = len(raw["train_features"])
    original_test_ids = list(raw["test_features"].index)
    original_test_labels = raw["test_labels"].copy(deep=True)
    original_test_weights = np.asarray(raw["test_weights"]).copy()

    # GREEN: emulate the per-fold, locally scoped production hook.
    original_split = kitchen.make_train_test_datasets
    def wrapped_split(features, labels):
        return purge_train_test_split(
            kitchen, original_split(features, labels), horizon=4
        )
    kitchen.make_train_test_datasets = wrapped_split
    try:
        fitted = kitchen.make_train_test_datasets(x, y)
    finally:
        del kitchen.make_train_test_datasets

    meta = kitchen._phase12_purge_meta
    actual_train_ids = list(fitted["train_features"].index)
    check(meta["removed_train_rows"] == 4
          and meta["original_train_rows"] == original_train_count
          and meta["fitted_train_rows"] == len(actual_train_ids)
          and len(actual_train_ids) == original_train_count - 4,
          "PHASE12_SMOKE_INCORRECT_PURGE_COUNT")
    check(actual_train_ids == list(raw["train_features"].index[:-4])
          and list(fitted["train_labels"].index) == actual_train_ids
          and len(fitted["train_weights"]) == len(actual_train_ids),
          "PHASE12_SMOKE_TRAIN_ALIGNMENT_FAILURE")
    check(list(fitted["test_features"].index) == original_test_ids
          and fitted["test_labels"].equals(original_test_labels)
          and np.array_equal(fitted["test_weights"], original_test_weights),
          "PHASE12_SMOKE_VALIDATION_CHANGED")
    check(dates.loc[actual_train_ids[-1]] + pd.Timedelta(minutes=60)
          < first_test,
          "PHASE12_SMOKE_TRAIN_TEST_LABEL_OVERLAP")
    check("make_train_test_datasets" not in vars(kitchen),
          "PHASE12_SMOKE_SPLITTER_NOT_RESTORED")

    return {
        "phase12_pinned_native_split_smoke_verified": True,
        "original_train_rows": original_train_count,
        "purged_train_rows": meta["removed_train_rows"],
        "fitted_train_rows": len(actual_train_ids),
        "validation_rows_unchanged": len(original_test_ids),
        "label_horizon_candles": 4,
        "oos_certified": False,
        "ready_for_360": False,
        "live_orders_enabled": False,
    }


if __name__ == "__main__":
    print(json.dumps(run_smoke(), sort_keys=True))
