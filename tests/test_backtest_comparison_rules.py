"""Unit tests for the 180-day A/B backtest rule definitions.

These tests intentionally test signal semantics, not market performance. They do not
claim that a historical backtest has been run.
"""
import unittest


def b_signals(previous_pb, current_pb):
    """Signal rules copied from the supplied Pine source."""
    long_entry = previous_pb < 0.2 and current_pb > 0.2
    short_entry = previous_pb > 0.8 and current_pb < 0.8
    exit_signal = (
        (previous_pb > 0.2 and current_pb < 0.2)
        or (previous_pb < 0.8 and current_pb > 0.8)
    )
    return long_entry, short_entry, exit_signal


def a_entry_signals(previous_rsi, current_rsi, h1_plus_di, h1_minus_di,
                    h1_adx, adx_min=20, long_level=30, short_level=70):
    """Current bot.py entry rule: closed H1 directional ADX filter + M15 RSI cross."""
    h1_bull = h1_plus_di > h1_minus_di and h1_adx > adx_min
    h1_bear = h1_minus_di > h1_plus_di and h1_adx > adx_min
    long_entry = h1_bull and previous_rsi <= long_level and current_rsi > long_level
    short_entry = h1_bear and previous_rsi >= short_level and current_rsi < short_level
    return long_entry, short_entry


def h1_is_closed_for_m15(m15_open, h1_open):
    """The bot uses only an H1 candle whose open precedes the current M15 hour bucket."""
    return h1_open < m15_open.floor("h")


class TestStrategyBSignals(unittest.TestCase):
    def test_long_cross_is_strict(self):
        self.assertEqual(b_signals(0.19, 0.21), (True, False, False))
        self.assertFalse(b_signals(0.20, 0.21)[0])
        self.assertFalse(b_signals(0.19, 0.20)[0])

    def test_short_cross_is_strict(self):
        self.assertEqual(b_signals(0.81, 0.79), (False, True, False))
        self.assertFalse(b_signals(0.80, 0.79)[1])
        self.assertFalse(b_signals(0.81, 0.80)[1])

    def test_exit_crosses_are_strict(self):
        self.assertTrue(b_signals(0.21, 0.19)[2])
        self.assertTrue(b_signals(0.79, 0.81)[2])
        self.assertFalse(b_signals(0.20, 0.19)[2])
        self.assertFalse(b_signals(0.80, 0.81)[2])

    def test_flat_or_nan_like_values_do_not_signal(self):
        self.assertEqual(b_signals(float("nan"), 0.5), (False, False, False))


class TestStrategyAEntry(unittest.TestCase):
    def test_long_requires_rsi_cross_and_bullish_h1(self):
        self.assertEqual(a_entry_signals(29, 31, 25, 20, 24), (True, False))
        self.assertEqual(a_entry_signals(31, 32, 25, 20, 24), (False, False))
        self.assertEqual(a_entry_signals(29, 31, 20, 25, 24), (False, False))
        self.assertEqual(a_entry_signals(29, 31, 25, 20, 20), (False, False))

    def test_short_requires_rsi_cross_and_bearish_h1(self):
        self.assertEqual(a_entry_signals(71, 69, 20, 25, 24), (False, True))
        self.assertEqual(a_entry_signals(69, 68, 20, 25, 24), (False, False))
        self.assertEqual(a_entry_signals(71, 69, 25, 20, 24), (False, False))


if __name__ == "__main__":
    unittest.main()
