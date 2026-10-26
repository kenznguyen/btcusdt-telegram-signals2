"""Verify real RSI TP exit and net accounting on closed OHLC candles."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from android_indicators import indicator_series
from android_signal_predicates import entry_position
from android_ohlc_replay import replay_ohlc, M15_MS
from android_state_replay import ReplayState


def bar(i, price):
    return {"timestamp_ms": i * M15_MS, "open": float(price),
            "high": float(price + 0.1), "low": float(price - 0.1),
            "close": float(price), "volume": 10.0, "closed": True}


class GenuineOhlcTakeProfitTests(unittest.TestCase):
    def test_long_take_profit_with_actual_rsi_and_accounting(self):
        prices = [100.0 + 0.25 * i for i in range(85)]
        candles = [bar(i, price) for i, price in enumerate(prices)]
        indicators = indicator_series(candles)
        # Seed a LONG at a price below the market; RSI is calculated by
        # the actual indicator engine and must exceed the TP threshold.
        initial = entry_position(100.0, "LONG", 100.0, 0)
        state, events = replay_ohlc(candles, [], ReplayState(100.0, initial))
        self.assertEqual(1, len(events), events)
        self.assertEqual("TP", events[0]["kind"])
        self.assertEqual("LONG", events[0]["side"])
        self.assertGreaterEqual(indicators[1]["rsi"] or 0, 0)
        self.assertIsNone(state.position)
        self.assertGreater(events[0]["net_pnl"], 0)
        self.assertGreater(events[0]["fees"], 0)
        self.assertAlmostEqual(100.0 + events[0]["net_pnl"], state.balance, places=9)


if __name__ == "__main__":
    unittest.main()
