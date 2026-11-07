"""R22.6 RED: real FreqAI DataKitchen must match the strategy feature source."""
import unittest

import pandas as pd

from freqai_bridge.ChartProFreqaiResearch import ChartProFreqaiResearch
from quant_system.phase22_historical_feature_replay import (
    FeatureReplayError,
    build_manual_feature_matrix,
    build_runtime_feature_matrix,
    compare_feature_matrices,
    verify_prefix_invariance,
)


def fixture_candles(count=256):
    close = [100.0 + i * 0.07 + (i % 11) * 0.13 for i in range(count)]
    return pd.DataFrame({
        "date": pd.date_range("2026-01-01", periods=count, freq="15min", tz="UTC"),
        "open": [x - 0.2 for x in close],
        "high": [x + 0.8 for x in close],
        "low": [x - 0.9 for x in close],
        "close": close,
        "volume": [10.0 + (i % 13) for i in range(count)],
    })


def fixture_config():
    return {
        "timeframe": "15m",
        "freqai": {
            "feature_parameters": {
                "include_timeframes": ["15m"],
                "include_corr_pairlist": [],
                "indicator_periods_candles": [14, 28],
                "include_shifted_candles": 2,
            }
        },
    }


class Phase22HistoricalDataKitchenTests(unittest.TestCase):
    def test_native_datakitchen_matches_manual_strategy_matrix(self):
        candles = fixture_candles()
        config = fixture_config()
        strategy = object.__new__(ChartProFreqaiResearch)
        actual = build_runtime_feature_matrix(
            config, strategy, candles, "BTC/USDT:USDT"
        )
        manual = build_manual_feature_matrix(
            candles, ChartProFreqaiResearch, "BTC/USDT:USDT"
        )
        result = compare_feature_matrices(actual, manual, list(manual.columns))
        self.assertTrue(result["all_values_match"])
        self.assertEqual(result["feature_count"], 20)
        self.assertEqual(result["row_count"], len(candles))

    def test_actual_datakitchen_prefix_values_ignore_future_suffix(self):
        candles = fixture_candles(512)
        config = fixture_config()
        strategy = object.__new__(ChartProFreqaiResearch)
        result = verify_prefix_invariance(
            config,
            strategy,
            candles,
            "BTC/USDT:USDT",
            cut_points=[128, 256, 384, 480],
        )
        self.assertTrue(result["prefix_invariance_verified"])
        self.assertEqual(result["prefix_cut_count"], 4)
        self.assertEqual(result["feature_comparisons"], 80)

    def test_feature_column_order_mismatch_fails_closed(self):
        candles = fixture_candles()
        config = fixture_config()
        strategy = object.__new__(ChartProFreqaiResearch)
        actual = build_runtime_feature_matrix(
            config, strategy, candles, "BTC/USDT:USDT"
        )
        manual = build_manual_feature_matrix(
            candles, ChartProFreqaiResearch, "BTC/USDT:USDT"
        )
        reordered = manual.loc[:, list(reversed(manual.columns))]
        with self.assertRaisesRegex(FeatureReplayError, "FEATURE_COLUMN_ORDER_MISMATCH"):
            compare_feature_matrices(actual, reordered, list(manual.columns))


if __name__ == "__main__":
    unittest.main()
