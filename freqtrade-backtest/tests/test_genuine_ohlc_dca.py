"""Find deterministic OHLC sequence with actual warmed-up RSI/ADX DCA.

Synthetic price series only; no indicator mocks, market data or trading.
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
            "high": float(price + 1), "low": float(price - 1),
            "close": float(price), "volume": 10.0, "closed": True}


class GenuineOhlcDcaTests(unittest.TestCase):
    def test_emergency_stop_preempts_late_dca_candidate(self):
        # Repeated strong downswings and modest rebounds can lift RSI
        # while keeping ADX elevated; a seeded LONG remains underwater.
        prices = [100.0]
        for i in range(1, 130):
            phase = i % 6
            prices.append(prices[-1] + (0.65 if phase == 5 else -0.45))
        candles = [bar(i, price) for i, price in enumerate(prices)]
        points = indicator_series(candles)
        initial = entry_position(100.0, "LONG", 100.0, 0)
        candidates = [
            i for i in range(1, len(candles))
            if points[i]["rsi"] is not None and points[i-1]["rsi"] is not None
            and points[i]["adx"] is not None
            and dca_signal("LONG",
                           roe_for("LONG", initial["avg_entry"], candles[i]["close"]),
                           points[i]["adx"], points[i]["rsi"], points[i-1]["rsi"])
        ]
        self.assertTrue(candidates, "Fixture must exercise a genuine DCA predicate")
        # A late technical DCA candidate cannot override an earlier stop.
        end = candidates[0] + 1
        state, events = replay_ohlc(candles[:end], [], ReplayState(100.0, initial))
        self.assertEqual(1, len(events))
        self.assertEqual("EMERGENCY_SL", events[0]["kind"])
        self.assertIsNone(state.position)
        self.assertAlmostEqual(100.0 + events[0]["net_pnl"], state.balance)
        self.assertGreater(events[0]["fees"], 0.0)


if __name__ == "__main__":
    unittest.main()
