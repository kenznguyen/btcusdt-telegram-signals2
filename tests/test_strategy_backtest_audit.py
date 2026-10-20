"""Evidence-first audit tests for Python bot/backtest execution parity.

Known execution-model gaps are marked expectedFailure on purpose. They should be
converted to ordinary passing assertions only after the implementation is fixed
and the cross-platform behavior is verified. No strategy thresholds are changed.
"""
import re
import unittest
from pathlib import Path

import bot

ROOT = Path(__file__).resolve().parents[1]
BACKTEST_SOURCE = (ROOT / "backtest.py").read_text(encoding="utf-8")
BOT_SOURCE = (ROOT / "bot.py").read_text(encoding="utf-8")


class StrategyRuleTests(unittest.TestCase):
    def test_entry_cross_and_h1_filter_boundaries(self):
        self.assertEqual(bot.entry_signals(30.0, 30.01, 25.0, 20.0, 20.01), (True, False))
        self.assertEqual(bot.entry_signals(30.01, 31.0, 25.0, 20.0, 25.0), (False, False))
        self.assertEqual(bot.entry_signals(29.0, 31.0, 25.0, 20.0, 20.0), (False, False))
        self.assertEqual(bot.entry_signals(70.0, 69.99, 20.0, 25.0, 20.01), (False, True))

    def test_dca_threshold_is_inclusive_but_adx_is_strict(self):
        self.assertTrue(bot.dca_signal("LONG", -20.0, 45.01, 25.0, 24.0))
        self.assertFalse(bot.dca_signal("LONG", -19.99, 50.0, 25.0, 24.0))
        self.assertFalse(bot.dca_signal("LONG", -20.0, 45.0, 25.0, 24.0))
        self.assertTrue(bot.dca_signal("SHORT", -20.0, 46.0, 79.0, 80.0))

    def test_tp_requires_rsi_and_roe(self):
        self.assertTrue(bot.take_profit_signal("LONG", 76.0, 5.0))
        self.assertFalse(bot.take_profit_signal("LONG", 76.0, 4.99))
        self.assertTrue(bot.take_profit_signal("SHORT", 24.0, 5.0))
        self.assertFalse(bot.take_profit_signal("SHORT", 24.01, 9.0))

    def test_stop_gap_and_slippage_are_adverse(self):
        self.assertLess(bot.stop_fill_price("LONG", 97.0, 95.0), 95.0)
        self.assertGreater(bot.stop_fill_price("SHORT", 103.0, 105.0), 105.0)
        self.assertLess(bot.execution_fill_price(100.0, "SELL"), 100.0)
        self.assertGreater(bot.execution_fill_price(100.0, "BUY"), 100.0)

    def test_python_fee_and_slippage_defaults_are_explicit(self):
        self.assertAlmostEqual(bot.FEE_RATE, 0.0005)
        self.assertAlmostEqual(bot.SLIPPAGE_BPS, 5.0)


class KnownParityGapTests(unittest.TestCase):
    @unittest.expectedFailure
    def test_backtest_entry_uses_same_adverse_slippage_as_android_and_bot_model(self):
        # Android applies executionFillPrice at entry. Python backtest currently
        # sizes qty from raw close and stores avg=close, so this should fail today.
        self.assertRegex(
            BACKTEST_SOURCE,
            r"fill_price\s*=\s*bot\.execution_fill_price\(close,\s*action\)",
        )

    @unittest.expectedFailure
    def test_backtest_dca_uses_same_adverse_slippage_as_android_and_bot_model(self):
        # Android applies adverse slippage to DCA; Python backtest currently uses close.
        dca_section = BACKTEST_SOURCE[BACKTEST_SOURCE.find("if not pos[\"dca\"]"):BACKTEST_SOURCE.find("if pos:\n            row = m15.iloc[-1]")]
        self.assertRegex(dca_section, r"fill_price\s*=\s*bot\.execution_fill_price\(close,\s*action\)")

    @unittest.expectedFailure
    def test_h1_filter_selects_latest_candle_closed_by_m15_close_time(self):
        # At an M15 candle opening 00:45, its close is 01:00. The H1 candle
        # opening 00:00 is closed at 01:00 and is then available without lookahead.
        # Current code selects by M15 OPEN hour bucket, which keeps the 23:00 H1 bar.
        self.assertIn('h1["close_time"] <= row["close_time"]', BACKTEST_SOURCE)

    @unittest.expectedFailure
    def test_python_bot_and_backtest_do_not_skip_emergency_stop_when_indicators_are_nan(self):
        # Both implementations currently skip candle processing before the emergency
        # stop check when RSI or ADX is NaN. Protective exits must not depend on indicators.
        self.assertNotRegex(
            BOT_SOURCE,
            r'if pd\\.isna\\(row\\["rsi"\\]\\) or pd\\.isna\\(row\\["adx"\\]\\):\\s*state\\["last_processed_open"\\].*?continue',
        )
        self.assertNotRegex(
            BACKTEST_SOURCE,
            r'if i == 0 or pd\\.isna\\(row\\["rsi"\\]\\) or pd\\.isna\\(row\\["adx"\\]\\):\\s*continue',
        )

    @unittest.expectedFailure
    def test_end_of_test_exit_applies_adverse_slippage(self):
        # End-of-window close currently uses the raw last close in the backtest.
        tail = BACKTEST_SOURCE[BACKTEST_SOURCE.find('if pos:\n            row = m15.iloc[-1]'):BACKTEST_SOURCE.find("# KPI definitions")]
        self.assertRegex(tail, r"bot\.execution_fill_price\(exit_price,\s*\"SELL\"")

if __name__ == "__main__":
    unittest.main(verbosity=2)
