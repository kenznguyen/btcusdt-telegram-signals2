"""Real-indicator DCA regression without disabling emergency risk protection.

Seed a LONG only after constructing a fully warmed synthetic price series.
Its entry price is anchored to the first qualifying RSI/ADX rebound, so the
preceding downtrend cannot prematurely hit the LONG emergency stop.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from android_indicators import indicator_series
from android_signal_predicates import dca_signal, entry_position, roe_for
from android_ohlc_replay import replay_ohlc, M15_MS
from android_state_replay import ReplayState


def bar(i, price):
    return {"timestamp_ms": i * M15_MS, "open": float(price),
            "high": float(price + 0.1), "low": float(price - 0.1),
            "close": float(price), "volume": 10.0, "closed": True}


class GenuineOhlcDcaTests(unittest.TestCase):
    def test_warmed_indicators_trigger_dca_before_emergency_stop(self):
        # A descending market with occasional rebounds maintains high ADX.
        prices = [100.0]
        for i in range(1, 130):
            prices.append(prices[-1] + (0.65 if i % 6 == 5 else -0.45))
        candles = [bar(i, price) for i, price in enumerate(prices)]
        points = indicator_series(candles)
        candidates = [
            i for i in range(1, len(candles))
            if points[i]["rsi"] is not None and points[i-1]["rsi"] is not None
            and points[i]["adx"] is not None and points[i]["adx"] > 45
            and points[i]["rsi"] > 20
            and points[i]["rsi"] > points[i-1]["rsi"]
        ]
        self.assertTrue(candidates, "OHLC must warm up a qualifying RSI/ADX rebound")
        target = candidates[0]
        # At target, ROE is about -26%, above the -90% emergency threshold.
        # Earlier candles are at higher prices and cannot stop this seeded LONG.
        entry_reference = candles[target]["close"] / 0.98
        initial = entry_position(100.0, "LONG", entry_reference, 0)
        self.assertTrue(dca_signal(
            "LONG", roe_for("LONG", initial["avg_entry"], candles[target]["close"]),
            points[target]["adx"], points[target]["rsi"], points[target-1]["rsi"]))
        state, events = replay_ohlc(
            candles[:target + 1], [], ReplayState(100.0, initial))
        self.assertEqual(1, len(events), events)
        self.assertEqual("DCA", events[0]["kind"])
        self.assertEqual(100.0, events[0]["margin"])
        self.assertEqual(100.0, state.balance)
        self.assertTrue(state.position["dca_used"])
        self.assertGreater(state.position["qty"], initial["qty"])
        self.assertLess(state.position["avg_entry"], initial["avg_entry"])


if __name__ == "__main__":
    unittest.main()
