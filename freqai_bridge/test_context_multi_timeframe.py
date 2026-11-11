"""Context window selection tests for M15/H1 fixtures."""

import unittest

from freqai_bridge.context import canonical_context


NOW = 1_800_000_900_123
INTERVAL = {"15m": 900_000, "1h": 3_600_000}


class CaptureClient:
    def __init__(self):
        self.calls = []

    def fetch(self, **kwargs):
        self.calls.append(kwargs)
        return {"datasetVersion": "fixture"}


class T2ContextTimeframeTest(unittest.TestCase):
    def test_h1_context_uses_hour_alignment_and_explicit_timeframe(self):
        client = CaptureClient()
        result = canonical_context(now_ms=NOW, bars=3, timeframe="1h", client=client)
        end = NOW // INTERVAL["1h"] * INTERVAL["1h"]
        self.assertEqual(client.calls, [{
            "start_ms": end - 3 * INTERVAL["1h"],
            "end_ms": end,
            "as_of_ms": NOW,
            "timeframe": "1h",
        }])
        self.assertEqual(result["datasetVersion"], "fixture")

    def test_h1_context_accepts_windows_larger_than_single_http_page(self):
        client = CaptureClient()
        canonical_context(now_ms=NOW, bars=65, timeframe="1h", client=client)
        self.assertEqual(client.calls[0]["timeframe"], "1h")
        self.assertEqual(client.calls[0]["end_ms"] - client.calls[0]["start_ms"], 65 * INTERVAL["1h"])

    def test_unsupported_timeframe_fails_before_client_access(self):
        client = CaptureClient()
        with self.assertRaises(ValueError):
            canonical_context(now_ms=NOW, bars=1, timeframe="4h", client=client)
        self.assertEqual(client.calls, [])


if __name__ == "__main__":
    unittest.main()
