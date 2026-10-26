import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from android_indicators import IndicatorConfig, indicator_series, rma


class AndroidIndicatorsTests(unittest.TestCase):
    def test_rma_seeds_from_first_n_non_null_values(self):
        self.assertEqual([None, None, None, 2.0, 3.0],
                         rma([None, 1.0, 3.0, 2.0, 5.0], 3))

    def test_rma_carries_forward_missing_values(self):
        self.assertEqual([None, 2.0, 2.0, 4.0],
                         rma([2.0, 2.0, None, 6.0], 2))

    def test_rsi_constant_close_is_fifty(self):
        candles = [{"high": 101.0, "low": 99.0, "close": 100.0}] * 30
        result = indicator_series(candles)
        self.assertIsNone(result[13]["rsi"])
        self.assertEqual(50.0, result[14]["rsi"])
        self.assertIsNone(result[-1]["adx"])

    def test_rsi_rising_close_is_hundred(self):
        candles = [{"high": i + 2.0, "low": i, "close": i + 1.0} for i in range(40)]
        result = indicator_series(candles)
        self.assertEqual(100.0, result[14]["rsi"])
        self.assertAlmostEqual(50.0, result[-1]["plus_di"])
        self.assertEqual(0.0, result[-1]["minus_di"])
        self.assertAlmostEqual(100.0, result[-1]["adx"])

    def test_short_series_does_not_invent_indicators(self):
        candles = [{"high": 102.0, "low": 98.0, "close": 100.0}] * 5
        self.assertIsNone(indicator_series(candles)[-1]["rsi"])

    def test_invalid_rma_length_is_rejected(self):
        with self.assertRaises(ValueError):
            rma([1.0], 0)


if __name__ == "__main__":
    unittest.main()
