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

    def test_context_uses_real_http_adapter_against_loopback_contract_server(self):
        import hashlib
        import json
        import threading
        import time
        from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
        from urllib.parse import parse_qs, urlsplit

        captured = {}

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                query = parse_qs(urlsplit(self.path).query)
                start = int(query["startMs"][0])
                end = int(query["endMs"][0])
                as_of = int(query["asOfMs"][0])
                generated = time.time_ns() // 1_000_000
                available = end + 1_000
                candle = {
                    "exchange": "binance", "marketType": "USDT_PERPETUAL", "symbol": "BTCUSDT",
                    "timeframe": "15m", "openTimeMs": start, "closeTimeMs": end,
                    "open": "100", "high": "102", "low": "99", "close": "101", "volume": "3",
                    "isClosed": True, "availableAtMs": available,
                    "availabilityKind": "FIRST_OBSERVED", "quality": "VALIDATED",
                    "source": "ccxt.binanceusdm",
                }
                payload = {
                    "exchange": "binance", "marketType": "USDT_PERPETUAL", "symbol": "BTCUSDT",
                    "timeframe": "15m", "startMs": start, "endMs": end, "asOfMs": as_of,
                    "candles": [candle],
                }
                version = hashlib.sha256(
                    json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
                ).hexdigest()
                body = {
                    "contractVersion": "1.0.0", "schemaVersion": 1,
                    **payload, "datasetVersion": "sha256:" + version,
                    "coverage": {"expected": 1, "returned": 1, "complete": True, "gaps": []},
                    "volumeUnit": "BTC_BASE_ASSET", "source": "ccxt.binanceusdm",
                    "generatedAtMs": generated,
                    "freshness": {
                        "latestExpectedOpenTimeMs": start,
                        "latestReturnedOpenTimeMs": start,
                        "latestCloseTimeMs": end,
                        "latestAvailableAtMs": available,
                        "observationAgeMs": generated - available,
                        "closeLagMs": generated - end,
                        "evaluable": True,
                    },
                }
                captured["authorization"] = self.headers.get("Authorization")
                captured["path"] = urlsplit(self.path).path
                encoded = json.dumps(body, separators=(",", ":")).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(encoded)))
                self.end_headers()
                self.wfile.write(encoded)

            def log_message(self, *args):
                return

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        self.addCleanup(thread.join, 2)

        observation = time.time_ns() // 1_000_000 - 60_000
        env = {
            "T0_CANDLE_API_BASE_URL": f"http://127.0.0.1:{server.server_port}",
            "T0_CANDLE_API_TOKEN": "loopback-test-token",
            "T0_CANDLE_MAX_LAG_MS": "120000",
        }
        with patch.dict(os.environ, env, clear=True):
            result = canonical_context(now_ms=observation, bars=1)

        self.assertEqual(captured["authorization"], "Bearer loopback-test-token")
        self.assertEqual(captured["path"], "/v1/candles")
        self.assertEqual(result["asOfMs"], observation)
        self.assertEqual(len(result["candles"]), 1)
        self.assertEqual(result["datasetVersion"][:7], "sha256:")

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
