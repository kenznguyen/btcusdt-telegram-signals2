"""Common API must consume canonical T0 candles only through Candle HTTP V1."""

import os
import unittest
from unittest.mock import patch

from pipeline import api


class FakeCandleHttpClient:
    instances = []

    def __init__(self, config):
        self.config = config
        self.calls = []
        type(self).instances.append(self)

    def fetch(self, *, start_ms, end_ms, as_of_ms, timeframe):
        self.calls.append((start_ms, end_ms, as_of_ms, timeframe))
        return {
            "symbol": "BTCUSDT",
            "timeframe": timeframe,
            "startMs": start_ms,
            "endMs": end_ms,
            "asOfMs": as_of_ms,
            "candles": [],
            "coverage": {"expected": 1, "returned": 0, "complete": False, "gaps": []},
            "datasetVersion": "sha256:" + "e" * 64,
        }


class CommonApiT0HttpBoundaryTest(unittest.TestCase):
    def setUp(self):
        FakeCandleHttpClient.instances.clear()
        self.config = {
            "T0_CANDLE_API_BASE_URL": "https://t0.example.invalid",
            "T0_CANDLE_API_TOKEN": "t0-read-only-test-token",
            "T0_CANDLE_MAX_LAG_MS": "120000",
            # Deliberately no MARKET_DATA_DB: Common API must not need local T0 storage.
        }

    def test_market_window_uses_authenticated_t0_http_client_without_local_store(self):
        with patch.dict(os.environ, self.config, clear=True), \
             patch("freqai_bridge.http_candles.CandleHttpClient", FakeCandleHttpClient), \
             patch.object(api, "create_store_from_env", side_effect=AssertionError("local T0 store used"), create=True):
            with patch.object(api, "now_ms", return_value=1_800_000_000_000):
                result = api.market_window(
                    "BTCUSDT", "15m", 1_799_998_200_000, 1_800_000_000_000,
                )

        self.assertEqual(result["datasetVersion"], "sha256:" + "e" * 64)
        client = FakeCandleHttpClient.instances[-1]
        self.assertEqual(client.config.base_url, "https://t0.example.invalid")
        self.assertEqual(client.config.token, "t0-read-only-test-token")
        self.assertEqual(client.config.max_lag_ms, 120000)
        self.assertEqual(client.calls, [(
            1_799_998_200_000, 1_800_000_000_000, None, "15m",
        )])

    def test_missing_t0_http_configuration_fails_closed_without_local_fallback(self):
        with patch.dict(os.environ, {}, clear=True), \
             patch.object(api, "create_store_from_env", side_effect=AssertionError("local T0 fallback"), create=True):
            with self.assertRaisesRegex(OSError, "T0_CANDLE_HTTP_UNAVAILABLE"):
                api.market_window("BTCUSDT", "15m", 1_799_998_200_000, 1_800_000_000_000)

    def test_invalid_t0_http_configuration_fails_closed(self):
        invalid = dict(self.config, T0_CANDLE_MAX_LAG_MS="120001")
        with patch.dict(os.environ, invalid, clear=True):
            with self.assertRaisesRegex(OSError, "T0_CANDLE_HTTP_UNAVAILABLE"):
                api.market_window("BTCUSDT", "15m", 1_799_998_200_000, 1_800_000_000_000)


if __name__ == "__main__":
    unittest.main()
