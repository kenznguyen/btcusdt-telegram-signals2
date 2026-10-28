"""Closed and open-position equity tests; no Freqtrade dependency."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from equity_reconstruction import equity_rows


def candle(time_ms, close):
    return {"timestamp_ms": time_ms, "close": close}


class EquityReconstructionTest(unittest.TestCase):
    def test_long_open_equity_deducts_entry_fees(self):
        t = {"open_timestamp": 0, "close_timestamp": 600000, "open_date": "2026-01-01T00:00:00+00:00",
             "close_date": "2026-01-01T00:10:00+00:00", "is_short": False,
             "fee_open": 0.001, "profit_abs": 9.79,
             "orders": [{"order_filled_timestamp": 0, "amount": 1, "safe_price": 100, "ft_is_entry": True},
                        {"order_filled_timestamp": 600000, "amount": 1, "safe_price": 110, "ft_is_entry": False}]}
        rows = list(equity_rows([candle(0, 105), candle(300000, 110)], [t], 100, 109.79))
        self.assertAlmostEqual(rows[0]["equity_usdt"], 104.9)
        self.assertAlmostEqual(rows[1]["equity_usdt"], 109.79)
        self.assertEqual(rows[1]["open_positions"], 0)

    def test_short_dca_and_reconcile(self):
        t = {"open_timestamp": 0, "close_timestamp": 900000, "open_date": "2026-01-01T00:00:00+00:00",
             "close_date": "2026-01-01T00:15:00+00:00", "is_short": True,
             "fee_open": 0.001, "profit_abs": 9.5,
             "orders": [{"order_filled_timestamp": 0, "amount": 1, "safe_price": 100, "ft_is_entry": True},
                        {"order_filled_timestamp": 300000, "amount": 1, "safe_price": 110, "ft_is_entry": True},
                        {"order_filled_timestamp": 900000, "amount": 2, "safe_price": 100, "ft_is_entry": False}]}
        rows = list(equity_rows([candle(0, 110), candle(300000, 100), candle(600000, 100)], [t], 100, 109.5))
        self.assertAlmostEqual(rows[0]["equity_usdt"], 99.79)
        self.assertAlmostEqual(rows[1]["equity_usdt"], 109.79)
        self.assertAlmostEqual(rows[2]["equity_usdt"], 109.5)

    def test_refuses_uncovered_exit(self):
        t = {"open_timestamp": 0, "close_timestamp": 600000, "open_date": "2026-01-01T00:00:00+00:00",
             "close_date": "2026-01-01T00:10:00+00:00", "is_short": False,
             "fee_open": 0, "profit_abs": 0, "orders": [
                {"order_filled_timestamp": 0, "amount": 1, "safe_price": 100, "ft_is_entry": True}]}
        with self.assertRaises(ValueError):
            list(equity_rows([candle(0, 100)], [t], 100, 100))


if __name__ == "__main__":
    unittest.main()
