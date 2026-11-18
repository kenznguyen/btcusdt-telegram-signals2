import unittest

import numpy as np
import pandas as pd

import bot


class StrategyRuleTests(unittest.TestCase):
    def test_wilder_rma_uses_sma_seed_then_recursive_average(self):
        result = bot.rma(pd.Series([1.0, 2.0, 3.0, 4.0]), 3)
        self.assertAlmostEqual(result.iloc[2], 2.0)
        self.assertAlmostEqual(result.iloc[3], 8.0 / 3.0)

    def test_indicator_pipeline_emits_rsi_and_adx_columns(self):
        close = np.linspace(100.0, 120.0, 80) + np.sin(np.arange(80))
        frame = pd.DataFrame({
            "open": close - 0.2,
            "high": close + 1.0,
            "low": close - 1.0,
            "close": close,
        })
        result = bot.add_indicators(frame)
        self.assertIn("rsi", result.columns)
        self.assertIn("adx", result.columns)
        self.assertTrue(result["rsi"].notna().any())
        self.assertTrue(result["adx"].notna().any())

    def test_entry_signal_requires_h1_direction_and_adx(self):
        self.assertEqual(
            bot.entry_signals(29.0, 31.0, 30.0, 10.0, 25.0),
            (True, False),
        )
        self.assertEqual(
            bot.entry_signals(71.0, 69.0, 10.0, 30.0, 25.0),
            (False, True),
        )
        self.assertEqual(
            bot.entry_signals(29.0, 31.0, 30.0, 10.0, 10.0),
            (False, False),
        )

    def test_take_profit_requires_rsi_and_minimum_roe(self):
        self.assertTrue(bot.take_profit_signal("LONG", 77.0, 5.0))
        self.assertFalse(bot.take_profit_signal("LONG", 77.0, 4.99))
        self.assertTrue(bot.take_profit_signal("SHORT", 23.0, 5.0))

    def test_smart_dca_requires_drawdown_trend_strength_and_rsi_recovery(self):
        self.assertTrue(bot.dca_signal("LONG", -21.0, 46.0, 21.0, 20.0))
        self.assertFalse(bot.dca_signal("LONG", -19.0, 46.0, 21.0, 20.0))
        self.assertFalse(bot.dca_signal("LONG", -21.0, 44.0, 21.0, 20.0))
        self.assertTrue(bot.dca_signal("SHORT", -21.0, 46.0, 79.0, 80.0))

    def test_emergency_stop_uses_side_specific_intrabar_extreme(self):
        threshold = bot.threshold_price("LONG", 100.0, abs(bot.EMERGENCY_SL_ROE))
        self.assertTrue(bot.emergency_stop_triggered("LONG", threshold - 0.01, 101.0, 100.0))
        self.assertFalse(bot.emergency_stop_triggered("LONG", threshold + 0.01, 101.0, 100.0))

    def test_soft_stop_requires_threshold_reversal_and_two_candle_confirmation(self):
        self.assertTrue(bot.soft_stop_triggered(
            "LONG", 97.0, 101.0, 100.0, 99.0, 101.0, 100.0,
            10.0, 20.0, 40.0, 100.0,
        ))
        self.assertFalse(bot.soft_stop_triggered(
            "LONG", 97.0, 101.0, 100.0, 99.0, 101.0, 100.0,
            20.0, 10.0, 40.0, 100.0,
        ))

    def test_stop_fill_is_conservative_for_gap_through(self):
        long_fill = bot.stop_fill_price("LONG", 95.0, 90.0)
        short_fill = bot.stop_fill_price("SHORT", 105.0, 110.0)
        self.assertLess(long_fill, 90.0)
        self.assertGreater(short_fill, 110.0)

    def test_strategy_module_has_no_telegram_or_runtime_entrypoints(self):
        self.assertFalse(hasattr(bot, "telegram_send"))
        self.assertFalse(hasattr(bot, "main"))
        self.assertFalse(hasattr(bot, "load_state"))
        self.assertFalse(hasattr(bot, "get_klines"))


if __name__ == "__main__":
    unittest.main()
