import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from android_ohlc_replay import replay_ohlc, M15_MS
from compare_events import validate_event
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

    def test_emitted_entry_matches_canonical_android_schema(self):
        from unittest.mock import patch
        from android_state_replay import ReplayState
        candles = [candle(i * M15_MS) for i in range(3)]
        h1 = [candle(0)]
        mock_points = [
            {"rsi": 29, "adx": 30, "plus_di": 25, "minus_di": 15},
            {"rsi": 30, "adx": 30, "plus_di": 25, "minus_di": 15},
            {"rsi": 31, "adx": 30, "plus_di": 25, "minus_di": 15},
        ]
        with patch("android_ohlc_replay.indicator_series", side_effect=[
            mock_points, [{"rsi": 50, "adx": 25, "plus_di": 30, "minus_di": 10}]
        ]), patch("android_ohlc_replay.aligned_indicators", return_value={
            "h1_plus_di": 30, "h1_minus_di": 10, "h1_adx": 25
        }):
            state, events = replay_ohlc(candles, h1, symbol="BTCUSDT")
        self.assertEqual(1, len(events))
        self.assertEqual("ENTRY", events[0]["kind"])
        self.assertIsNone(events[0]["net_pnl"])
        self.assertIsNone(events[0]["fees"])
        self.assertEqual(50.0, events[0]["margin"])
        self.assertEqual(100.0, state.balance)
        validate_event(events[0])

    def test_rejects_unaligned_m15(self):
        with self.assertRaisesRegex(ValueError, "Invalid M15"):
            replay_ohlc([candle(1)], [])


if __name__ == "__main__":
    unittest.main()
