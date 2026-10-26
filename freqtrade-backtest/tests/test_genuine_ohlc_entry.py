"""Deterministic OHLC integration test: genuine RSI crossing with prior H1 trend.

No mocked indicators or exchange calls. All candles are synthetic, not
historical Binance data and not a claim of strategy profitability.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from android_indicators import indicator_series
from android_ohlc_replay import replay_ohlc, M15_MS
from android_h1_alignment import HOUR_MS, aligned_indicators
from android_signal_predicates import entry_side


def bar(timestamp, price):
    return {
        "timestamp_ms": timestamp, "open": float(price),
        "high": float(price + 1), "low": float(price - 1),
        "close": float(price), "volume": 10.0, "closed": True,
    }


class GenuineOhlcEntryTests(unittest.TestCase):
    def test_long_entry_requires_real_indicator_cross_and_prior_h1(self):
        # 65 upward H1 candles warm up Wilder ADX and establish positive DI.
        h1 = [bar(i * HOUR_MS, 100 + 2 * i) for i in range(65)]
        # Long M15 down leg pushes RSI below 30; subsequent recovery crosses 30.
        # The clock starts after H1 warmup, avoiding any look-ahead.
        prices = [250 - i for i in range(45)] + [205 + i for i in range(35)]
        start = 60 * HOUR_MS
        m15 = [bar(start + i * M15_MS, price) for i, price in enumerate(prices)]
        m15_points = indicator_series(m15)
        h1_points = indicator_series(h1)
        enriched = [{**c, **point} for c, point in zip(h1, h1_points)]
        crossings = []
        for i in range(1, len(m15)):
            point = m15_points[i]
            prev = m15_points[i - 1]
            hour = aligned_indicators(m15[i]["timestamp_ms"], enriched)
            if prev["rsi"] is None or point["rsi"] is None or point["adx"] is None:
                continue
            side = entry_side(prev["rsi"], point["rsi"],
                              hour["h1_plus_di"], hour["h1_minus_di"], hour["h1_adx"])
            if side == "LONG":
                crossings.append(i)
        self.assertTrue(crossings, "Synthetic candles must produce a genuine LONG crossover")
        state, events = replay_ohlc(m15, h1)
        self.assertTrue(any(e["kind"] == "ENTRY" and e["side"] == "LONG" for e in events))
        self.assertEqual("BTCUSDT", events[0]["symbol"])
        self.assertGreater(events[0]["quantity"], 0)
        self.assertGreater(events[0]["margin"], 0)


if __name__ == "__main__":
    unittest.main()
