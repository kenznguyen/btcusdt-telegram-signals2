"""Test Freqtrade-compatible ENTRY diagnostics against the common Android fixture."""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
try:
    import pandas as pd
    from entry_frame import entry_diagnostics
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

from android_ohlc_replay import replay_ohlc

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "android_python_entry_ohlc_v1.json"


@unittest.skipUnless(PANDAS_AVAILABLE, "pandas unavailable; install for Freqtrade frame tests")
class EntryFrameTest(unittest.TestCase):
    def setUp(self):
        self.fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def frame(self, candles):
        return pd.DataFrame([
            {
                "date": pd.to_datetime(c["timestamp_ms"], unit="ms", utc=True),
                "open": c["open"], "high": c["high"], "low": c["low"],
                "close": c["close"], "volume": c["volume"],
            } for c in candles
        ])

    def test_same_entry_as_python_replay(self):
        m15 = self.fixture["candles_m15"]
        h1 = self.fixture["candles_h1"]
        frame = entry_diagnostics(self.frame(m15), self.frame(h1))
        _, events = replay_ohlc(m15, h1, symbol="BTCUSDT")
        replay_entry_times = [event["timestamp_ms"] for event in events
                              if event["kind"] == "ENTRY" and event["side"] == "LONG"]
        frame_entry_times = [
            candle["timestamp_ms"] for candle, flag in zip(m15, frame["android_entry_long"])
            if flag == 1
        ]
        self.assertTrue(frame_entry_times)
        # Frame predicates can show candidate entries while a position is already open.
        self.assertEqual(frame_entry_times[0], replay_entry_times[0])

    def test_h1_is_invisible_until_candle_closes(self):
        m15 = self.fixture["candles_m15"]
        h1 = self.fixture["candles_h1"]
        frame = entry_diagnostics(self.frame(m15), self.frame(h1))
        first_ms = m15[0]["timestamp_ms"]
        index = next(i for i, c in enumerate(m15) if c["timestamp_ms"] == first_ms)
        # The H1 bar with exactly the current hour open is not visible until +1h.
        # With existing older H1 candles this verifies the diagnostic has a value only from prior hour.
        self.assertEqual(float(frame.iloc[index]["android_h1_adx"]),
                         float(frame.iloc[index]["android_h1_adx"]))
        restricted_h1 = [c for c in h1 if c["timestamp_ms"] >= first_ms]
        restricted = entry_diagnostics(self.frame(m15), self.frame(restricted_h1))
        self.assertTrue(pd.isna(restricted.iloc[0]["android_h1_adx"]))

    def test_missing_m15_interval_rejected(self):
        m15 = self.fixture["candles_m15"]
        with self.assertRaisesRegex(ValueError, "Missing M15 candle"):
            entry_diagnostics(self.frame(m15[:9] + m15[10:]), self.frame(self.fixture["candles_h1"]))

    def test_duplicate_h1_timestamp_rejected(self):
        h1 = self.fixture["candles_h1"]
        with self.assertRaisesRegex(ValueError, "duplicate"):
            entry_diagnostics(self.frame(self.fixture["candles_m15"]), self.frame(h1 + [h1[-1]]))


if __name__ == "__main__":
    unittest.main()
