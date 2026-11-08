"""T2 context must consume the T0 read-only HTTP contract only."""

import os
import unittest
from unittest.mock import patch

from freqai_bridge.context import canonical_context
from freqai_bridge.http_candles import CandleHttpError


NOW = 1_800_000_900_123
STEP = 900_000


class FakeClient:
    def __init__(self, result=None):
        self.calls = []
        self.result = result if result is not None else {"datasetVersion": "sha256:" + "a" * 64}

    def fetch(self, *, start_ms, end_ms, as_of_ms):
        self.calls.append((start_ms, end_ms, as_of_ms))
        return self.result


class T2HttpContextTest(unittest.TestCase):
    def test_context_requests_exact_closed_window_and_observation_cutoff(self):
        client = FakeClient()
        result = canonical_context(now_ms=NOW, bars=2, client=client)
        end = NOW // STEP * STEP
        self.assertEqual(client.calls, [(end - 2 * STEP, end, NOW)])
        self.assertIs(result, client.result)

    def test_context_rejects_invalid_bar_count_before_http_request(self):
        client = FakeClient()
        for bars in (0, 33, True, 1.5):
            with self.subTest(bars=bars), self.assertRaises(ValueError):
                canonical_context(now_ms=NOW, bars=bars, client=client)
        self.assertEqual(client.calls, [])

    def test_missing_http_configuration_fails_closed_without_local_fallback(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(CandleHttpError):
                canonical_context(now_ms=NOW, bars=2)

    def test_http_client_uses_explicit_environment_contract_configuration(self):
        captured = {}

        class CapturingClient:
            def __init__(self, config):
                captured["config"] = config

            def fetch(self, **kwargs):
                captured["request"] = kwargs
                return {"datasetVersion": "sha256:" + "b" * 64}

        env = {
            "T0_CANDLE_API_BASE_URL": "https://t0.example.invalid",
            "T0_CANDLE_API_TOKEN": "opaque-token",
            "T0_CANDLE_MAX_LAG_MS": "120000",
        }
        with patch.dict(os.environ, env, clear=True), patch(
            "freqai_bridge.context.CandleHttpClient", CapturingClient
        ):
            result = canonical_context(now_ms=NOW, bars=1)

        self.assertEqual(captured["config"].base_url, env["T0_CANDLE_API_BASE_URL"])
        self.assertEqual(captured["config"].token, env["T0_CANDLE_API_TOKEN"])
        self.assertEqual(captured["config"].max_lag_ms, 120_000)
        self.assertEqual(captured["request"]["as_of_ms"], NOW)
        self.assertEqual(result["datasetVersion"], "sha256:" + "b" * 64)

    def test_invalid_or_missing_freshness_configuration_fails_closed(self):
        base = {
            "T0_CANDLE_API_BASE_URL": "https://t0.example.invalid",
            "T0_CANDLE_API_TOKEN": "opaque-token",
        }
        for value in (None, "", "0", "120001", "not-an-integer", "120000.0"):
            env = dict(base)
            if value is not None:
                env["T0_CANDLE_MAX_LAG_MS"] = value
            with self.subTest(value=value), patch.dict(os.environ, env, clear=True):
                with self.assertRaises(CandleHttpError):
                    canonical_context(now_ms=NOW, bars=1)


if __name__ == "__main__":
    unittest.main()
