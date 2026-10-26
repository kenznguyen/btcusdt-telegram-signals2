import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from android_ohlc_replay import replay_ohlc, M15_MS
from android_h1_alignment import HOUR_MS


def candle(timestamp, close=100.0):
    return {"timestamp_ms": timestamp, "open": close, "high": close + 1,
            "low": close - 1, "close": close, "closed": True}


class OhlcReplayTests(unittest.TestCase):
    def test_constant_market_produces_no_trades(self):
        m15 = [candle(i * M15_MS) for i in range(45)]
        h1 = [candle(i * HOUR_MS) for i in range(12)]
        state, events = replay_ohlc(m15, h1)
        self.assertEqual(100.0, state.balance)
        self.assertIsNone(state.position)
        self.assertEqual([], events)

    def test_rejects_missing_m15_candle(self):
        with self.assertRaisesRegex(ValueError, "Missing M15"):
            replay_ohlc([candle(0), candle(2 * M15_MS)], [])

    def test_rejects_unclosed_h1(self):
        hour = candle(0)
        hour["closed"] = False
        with self.assertRaisesRegex(ValueError, "Unclosed H1"):
            replay_ohlc([candle(0), candle(M15_MS)], [hour])

    def test_rejects_duplicate_h1(self):
        with self.assertRaisesRegex(ValueError, "strictly"):
            replay_ohlc([candle(0), candle(M15_MS)], [candle(0), candle(0)])

    def test_rejects_unaligned_m15(self):
        with self.assertRaisesRegex(ValueError, "Invalid M15"):
            replay_ohlc([candle(1)], [])


if __name__ == "__main__":
    unittest.main()
