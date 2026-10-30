"""Regression tests for the Phase13 feature prefix-intervention gate.

Runs in the pinned Codemagic FreqAI Python venv; pandas is required.
"""
from __future__ import annotations
import csv
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from quant_system.phase13_feature_causality import inspect_features, prefix_cut_points

class SafeStrategy:
    def feature_engineering_expand_all(self, df, period, metadata, **kwargs):
        df["%-relative-price"] = df["close"] / df["close"].rolling(period).mean() - 1
        df["%-relative-volume"] = df["volume"] / df["volume"].rolling(period).mean()
        return df

    def feature_engineering_expand_basic(self, df, metadata, **kwargs):
        df["%-pct-change"] = df["close"].pct_change()
        df["%-raw-volume"] = df["volume"]
        return df

    def feature_engineering_standard(self, df, metadata, **kwargs):
        df["%-day-of-week"] = df["date"].dt.dayofweek
        df["%-hour-of-day"] = df["date"].dt.hour
        return df

class LookaheadStrategy(SafeStrategy):
    def feature_engineering_expand_basic(self, df, metadata, **kwargs):
        df = SafeStrategy.feature_engineering_expand_basic(self, df, metadata, **kwargs)
        df["%-pct-change"] = df["close"].shift(-1).ffill()
        return df

class AdditionalFeatureStrategy(SafeStrategy):
    def feature_engineering_expand_basic(self, df, metadata, **kwargs):
        df = SafeStrategy.feature_engineering_expand_basic(self, df, metadata, **kwargs)
        df["%-future-hint"] = df["close"].shift(-2)
        return df

def fixture(root):
    csv_path = root / "15m.csv"
    # A full 1,200-row closed-candle series.
    with csv_path.open("w", newline="", encoding="utf8") as f:
        writer = csv.DictWriter(f, fieldnames=(
            "open_time", "open", "high", "low", "close", "volume", "closed"))
        writer.writeheader()
        for i in range(1200):
            price = 30_000.0 + 1.5 * i + (i % 9) * 0.13
            writer.writerow(dict(open_time=1_780_000_200_000 + i * 900000,
                open=price, high=price + 4, low=price - 5,
                close=price + 1, volume=20.0 + (i % 13), closed=1))
    config_path = root / "config.json"
    config = {
        "dry_run": True, "force_entry_enable": False,
        "timeframe": "15m", "exchange": {"name": "okx"},
        "freqai": {
            "feature_parameters": {
                "indicator_periods_candles": [14, 28],
                "include_shifted_candles": 2,
                "include_timeframes": ["15m"],
                "include_corr_pairlist": [],
                "label_period_candles": 4
            },
            "data_split_parameters": {"test_size": 0.2, "shuffle": False}
        }
    }
    config_path.write_text(json.dumps(config), encoding="utf8")
    return csv_path, config_path

class Phase13FeatureTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.csv, self.config = fixture(self.root)

    def tearDown(self):
        self.temp.cleanup()

    def test_prefix_cuts_cover_small_and_full_historical_datasets(self):
        # Regression for Codemagic: 1,200 candles yielded only ~6 cuts,
        # while 20 features require >=400 real invariance comparisons.
        for candles in (1000, 1200, 17280, 34560):
            with self.subTest(candles=candles):
                cuts = prefix_cut_points(candles)
                self.assertGreaterEqual(len(cuts), 20)
                self.assertLessEqual(len(cuts), 40)
                self.assertEqual(cuts, sorted(set(cuts)))
                self.assertGreater(min(cuts), 64)
                self.assertLess(max(cuts), candles)
                self.assertIn(candles - 3, cuts)
                self.assertIn(candles - 28, cuts)
                # 20 expected feature columns * at least 20 prefixes.
                self.assertGreaterEqual(20 * len(cuts), 400)

    def test_safe_features_obey_all_prefix_interventions(self):
        result = inspect_features(self.csv, self.config, SafeStrategy)
        self.assertEqual(result["errors"], [])
        self.assertTrue(result["feature_source_prefix_invariance_verified"])
        self.assertEqual(result["audited_feature_column_count"], 20)
        self.assertGreaterEqual(result["prefix_intervention_comparisons"], 400)
        self.assertFalse(result["full_model_pipeline_causality_verified"])
        self.assertFalse(result["independent_oos_verified"])

    def test_future_shift_cannot_pass(self):
        result = inspect_features(self.csv, self.config, LookaheadStrategy)
        self.assertFalse(result["feature_source_prefix_invariance_verified"])
        self.assertTrue(result["errors"])
        self.assertTrue(any("FUTURE_DEPENDENT_FEATURE" in error or
                            "INVALID_FINITE_MODEL_FEATURE" in error
                            for error in result["errors"]))

    def test_unreviewed_extra_feature_fails_closed(self):
        result = inspect_features(self.csv, self.config, AdditionalFeatureStrategy)
        self.assertFalse(result["feature_inventory_verified"])
        self.assertIn("PHASE13_UNKNOWN_GENERIC_FEATURE", result["errors"])

    def test_unapproved_config_and_market_gap_denied(self):
        cfg = json.loads(self.config.read_text())
        cfg["freqai"]["feature_parameters"]["include_shifted_candles"] = 0
        self.config.write_text(json.dumps(cfg))
        bad_config = inspect_features(self.csv, self.config, SafeStrategy)
        self.assertIn("PHASE13_UNAPPROVED_FEATURE_CONFIG", bad_config["errors"])
        cfg["freqai"]["feature_parameters"]["include_shifted_candles"] = 2
        self.config.write_text(json.dumps(cfg))
        lines = self.csv.read_text().splitlines()
        self.csv.write_text("\n".join(lines[:10] + lines[11:]) + "\n")
        gap = inspect_features(self.csv, self.config, SafeStrategy)
        self.assertIn("PHASE13_GAPPED_OR_DUPLICATE_CANDLES", gap["errors"])

if __name__ == "__main__":
    unittest.main()
