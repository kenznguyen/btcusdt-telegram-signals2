"""RED-only architecture and behavior contracts for the T2 HTTP candle consumer.

The HTTP behavior tests define the consumer-facing adapter seam before any
production adapter exists. They must remain failing until a separately
authorized GREEN implementation is supplied.
"""
import ast
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
BRIDGE = ROOT / "freqai_bridge"
STEP = 900_000
START = 1_800_000_000_000
END = START + STEP
AS_OF = END + 60_000
GENERATED = AS_OF
AVAILABLE = END + 30_000


class FakeResponse:
    def __init__(self, status=200, payload=None, body=None, content_type="application/json; charset=utf-8"):
        self.status_code = status
        self.headers = {"Content-Type": content_type}
        self.body = body if body is not None else json.dumps(payload, separators=(",", ":")).encode()
        self.closed = False

    def iter_content(self, chunk_size=8192):
        for offset in range(0, len(self.body), chunk_size):
            yield self.body[offset:offset + chunk_size]

    def close(self):
        self.closed = True


class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        response = self.responses.pop(0)
        if isinstance(response, BaseException):
            raise response
        return response


def response_envelope(**changes):
    candle = {
        "exchange": "binance",
        "marketType": "USDT_PERPETUAL",
        "symbol": "BTCUSDT",
        "timeframe": "15m",
        "openTimeMs": START,
        "closeTimeMs": END,
        "open": "100.00",
        "high": "102",
        "low": "99",
        "close": "101.25",
        "volume": "3.5",
        "isClosed": True,
        "availableAtMs": AVAILABLE,
        "availabilityKind": "FIRST_OBSERVED",
        "quality": "VALIDATED",
        "source": "ccxt.binanceusdm",
    }
    envelope = {
        "contractVersion": "1.0.0",
        "schemaVersion": 1,
        "exchange": "binance",
        "marketType": "USDT_PERPETUAL",
        "symbol": "BTCUSDT",
        "timeframe": "15m",
        "startMs": START,
        "endMs": END,
        "asOfMs": AS_OF,
        "candles": [candle],
        "datasetVersion": "sha256:" + "a" * 64,
        "coverage": {"expected": 1, "returned": 1, "complete": True, "gaps": []},
        "volumeUnit": "BTC_BASE_ASSET",
        "source": "ccxt.binanceusdm",
        "generatedAtMs": GENERATED,
        "freshness": {
            "latestExpectedOpenTimeMs": START,
            "latestReturnedOpenTimeMs": START,
            "latestCloseTimeMs": END,
            "latestAvailableAtMs": AVAILABLE,
            "observationAgeMs": GENERATED - AVAILABLE,
            "closeLagMs": GENERATED - END,
            "evaluable": True,
        },
    }
    envelope.update(changes)
    return envelope


class T2HttpConsumerRedTest(unittest.TestCase):
    def _adapter(self):
        from freqai_bridge.http_candles import CandleHttpClient, CandleHttpConfig, CandleHttpError
        return CandleHttpClient, CandleHttpConfig, CandleHttpError

    def _client(self, responses=None, envelope=None, **config_changes):
        Client, Config, _ = self._adapter()
        session = FakeSession(responses or [FakeResponse(payload=envelope or response_envelope())])
        values = {
            "base_url": "https://t0.example.invalid",
            "token": "test-secret-token",
            "max_lag_ms": 120_000,
        }
        values.update(config_changes)
        config = Config(**values)
        return Client(config, session=session, sleep=lambda _: None, clock_ms=lambda: GENERATED), session

    def _fetch(self, client):
        return client.fetch(start_ms=START, end_ms=END, as_of_ms=AS_OF)

    def test_http_adapter_module_exists(self):
        self.assertTrue((BRIDGE / "http_candles.py").is_file(), "T2 HTTP adapter is not implemented")

    def test_context_does_not_import_t0_store(self):
        tree = ast.parse((BRIDGE / "context.py").read_text(encoding="utf-8"))
        imports = [n for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module == "market_data.store"]
        self.assertEqual(imports, [], "T2 context still imports market_data.store")

    def test_context_does_not_call_t0_read_window(self):
        tree = ast.parse((BRIDGE / "context.py").read_text(encoding="utf-8"))
        calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "read_window"]
        self.assertEqual(calls, [], "T2 context still calls direct SQLite read_window")

    def test_strategy_does_not_accept_canonical_db_path(self):
        source = (BRIDGE / "ChartProFreqaiResearch.py").read_text(encoding="utf-8")
        self.assertNotIn("canonical_db_path", source)

    def test_strategy_does_not_pass_database_to_canonical_context(self):
        tree = ast.parse((BRIDGE / "ChartProFreqaiResearch.py").read_text(encoding="utf-8"))
        calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "canonical_context"]
        self.assertEqual(calls, [])

    def test_approved_freshness_formula_is_present_in_contract_plan(self):
        plan = (ROOT / "docs/architecture/T2_HTTP_CANDLE_CONSUMER_CONTRACT_AND_TEST_PLAN_2026-11-08.md").read_text(encoding="utf-8")
        self.assertIn("latestAvailableAtMs - latestCloseTimeMs", plan)
        self.assertIn("closeLagMs - observationAgeMs", plan)
        self.assertIn("120000 ms", plan)

    def test_transport_limits_are_recorded_in_contract_plan(self):
        plan = (ROOT / "docs/architecture/T2_HTTP_CANDLE_CONSUMER_CONTRACT_AND_TEST_PLAN_2026-11-08.md").read_text(encoding="utf-8")
        for value in ("connect timeout 3 s", "read timeout 5 s", "3 total attempts", "250 ms then 500 ms", "256 KiB", "do not automatically follow redirects"):
            with self.subTest(value=value):
                self.assertIn(value, plan)

    def test_valid_response_is_accepted_and_dataset_version_is_preserved(self):
        client, _ = self._client()
        result = self._fetch(client)
        self.assertEqual(result["datasetVersion"], "sha256:" + "a" * 64)
        self.assertEqual(result["candles"][0]["open"], "100.00")

    def test_request_uses_exact_market_range_and_as_of_parameters(self):
        client, session = self._client()
        self._fetch(client)
        url, kwargs = session.calls[0]
        self.assertEqual(url, "https://t0.example.invalid/v1/candles")
        self.assertEqual(kwargs["params"], {"symbol": "BTCUSDT", "timeframe": "15m", "startMs": START, "endMs": END, "asOfMs": AS_OF})

    def test_request_sends_bearer_header_and_no_token_in_url(self):
        client, session = self._client()
        self._fetch(client)
        url, kwargs = session.calls[0]
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer test-secret-token")
        self.assertNotIn("test-secret-token", url)
        self.assertNotIn("token", kwargs["params"])

    def test_request_enforces_transport_and_resource_limits(self):
        client, session = self._client()
        self._fetch(client)
        _, kwargs = session.calls[0]
        self.assertEqual(kwargs["timeout"], (3, 5))
        self.assertTrue(kwargs["stream"])
        self.assertFalse(kwargs["allow_redirects"])
        self.assertIs(kwargs["verify"], True)
        self.assertEqual(kwargs["headers"]["Accept-Encoding"], "identity")
        self.assertEqual(kwargs["headers"]["Cache-Control"], "no-store")

    def test_missing_or_blank_base_url_is_rejected(self):
        _, Config, Error = self._adapter()
        for value in ("", "   "):
            with self.subTest(value=value), self.assertRaises(Error):
                Config(base_url=value, token="secret", max_lag_ms=120_000)

    def test_missing_or_blank_token_is_rejected(self):
        _, Config, Error = self._adapter()
        for value in ("", "   "):
            with self.subTest(value=value), self.assertRaises(Error):
                Config(base_url="https://t0.example.invalid", token=value, max_lag_ms=120_000)

    def test_missing_or_invalid_freshness_threshold_fails_closed(self):
        _, Config, Error = self._adapter()
        for value in (None, 0, -1, True, "120000"):
            with self.subTest(value=value), self.assertRaises((Error, TypeError)):
                Config(base_url="https://t0.example.invalid", token="secret", max_lag_ms=value)

    def test_remote_plain_http_endpoint_is_rejected(self):
        _, Config, Error = self._adapter()
        with self.assertRaises(Error):
            Config(base_url="http://remote.example.invalid", token="secret", max_lag_ms=120_000)

    def test_requested_window_must_be_aligned_and_contain_one_to_32_bars(self):
        client, session = self._client()
        for start, end in ((START, START), (START, START + 33 * STEP), (START + 1, END)):
            with self.subTest(start=start, end=end), self.assertRaises(Exception):
                client.fetch(start_ms=start, end_ms=end, as_of_ms=AS_OF)
        self.assertEqual(session.calls, [])

    def test_contract_version_and_schema_version_must_match_exactly(self):
        _, _, Error = self._adapter()
        for changes in ({"contractVersion": "2.0.0"}, {"schemaVersion": 2}):
            client, _ = self._client(envelope=response_envelope(**changes))
            with self.subTest(changes=changes), self.assertRaises(Error):
                self._fetch(client)

    def test_market_identity_and_request_echo_must_match(self):
        _, _, Error = self._adapter()
        for changes in ({"exchange": "okx"}, {"marketType": "SPOT"}, {"symbol": "ETHUSDT"}, {"timeframe": "1h"}, {"startMs": START - STEP}, {"endMs": END + STEP}, {"asOfMs": AS_OF + 1}, {"volumeUnit": "QUOTE_ASSET"}, {"source": "other"}):
            client, _ = self._client(envelope=response_envelope(**changes))
            with self.subTest(changes=changes), self.assertRaises(Error):
                self._fetch(client)

    def test_dataset_version_must_be_sha256_formatted(self):
        _, _, Error = self._adapter()
        client, _ = self._client(envelope=response_envelope(datasetVersion="sha256:bad"))
        with self.assertRaises(Error):
            self._fetch(client)

    def test_incomplete_or_gapped_coverage_is_rejected(self):
        _, _, Error = self._adapter()
        bad_coverage = {"expected": 1, "returned": 1, "complete": False, "gaps": [{"startMs": START, "endMs": END}]}
        client, _ = self._client(envelope=response_envelope(coverage=bad_coverage))
        with self.assertRaises(Error):
            self._fetch(client)

    def test_duplicate_or_off_grid_candle_timestamp_is_rejected(self):
        _, _, Error = self._adapter()
        candle = response_envelope()["candles"][0].copy()
        candle["openTimeMs"] = START + 1
        client, _ = self._client(envelope=response_envelope(candles=[candle]))
        with self.assertRaises(Error):
            self._fetch(client)

    def test_open_or_invalid_close_boundary_candle_is_rejected(self):
        _, _, Error = self._adapter()
        for changes in ({"isClosed": False}, {"closeTimeMs": END - 1}):
            candle = response_envelope()["candles"][0] | changes
            client, _ = self._client(envelope=response_envelope(candles=[candle]))
            with self.subTest(changes=changes), self.assertRaises(Error):
                self._fetch(client)

    def test_invalid_decimal_or_ohlc_relationship_is_rejected(self):
        _, _, Error = self._adapter()
        for changes in ({"open": 100.0}, {"high": "NaN"}, {"low": "103"}, {"volume": "-1"}):
            candle = response_envelope()["candles"][0] | changes
            client, _ = self._client(envelope=response_envelope(candles=[candle]))
            with self.subTest(changes=changes), self.assertRaises(Error):
                self._fetch(client)

    def test_availability_after_as_of_cutoff_is_rejected(self):
        _, _, Error = self._adapter()
        candle = response_envelope()["candles"][0] | {"availableAtMs": AS_OF + 1}
        client, _ = self._client(envelope=response_envelope(candles=[candle]))
        with self.assertRaises(Error):
            self._fetch(client)

    def test_ingestion_delay_exactly_120000_ms_is_accepted(self):
        candle = response_envelope()["candles"][0] | {"availableAtMs": END + 120_000}
        generated = END + 180_000
        freshness = response_envelope()["freshness"] | {
            "latestAvailableAtMs": END + 120_000,
            "observationAgeMs": generated - (END + 120_000),
            "closeLagMs": generated - END,
        }
        client, _ = self._client(envelope=response_envelope(candles=[candle], generatedAtMs=generated, freshness=freshness))
        self._fetch(client)

    def test_ingestion_delay_120001_ms_is_rejected(self):
        _, _, Error = self._adapter()
        candle = response_envelope()["candles"][0] | {"availableAtMs": END + 120_001}
        generated = END + 180_001
        freshness = response_envelope()["freshness"] | {
            "latestAvailableAtMs": END + 120_001,
            "observationAgeMs": generated - (END + 120_001),
            "closeLagMs": generated - END,
        }
        client, _ = self._client(envelope=response_envelope(candles=[candle], generatedAtMs=generated, freshness=freshness))
        with self.assertRaises(Error):
            self._fetch(client)

    def test_large_normal_m15_close_lag_and_observation_age_do_not_cause_false_stale_rejection(self):
        candle = response_envelope()["candles"][0] | {"availableAtMs": END + 30_000}
        generated = END + 800_000
        freshness = response_envelope()["freshness"] | {
            "latestAvailableAtMs": END + 30_000,
            "observationAgeMs": generated - (END + 30_000),
            "closeLagMs": generated - END,
            "latestExpectedOpenTimeMs": END,
        }
        client, _ = self._client(envelope=response_envelope(candles=[candle], generatedAtMs=generated, freshness=freshness))
        self._fetch(client)

    def test_server_global_expected_slot_may_be_outside_request_window(self):
        freshness = response_envelope()["freshness"] | {"latestExpectedOpenTimeMs": END}
        client, _ = self._client(envelope=response_envelope(freshness=freshness))
        self._fetch(client)

    def test_unauthorized_response_is_not_retried(self):
        _, _, Error = self._adapter()
        client, session = self._client(responses=[FakeResponse(status=401, payload={"error": "UNAUTHORIZED"})])
        with self.assertRaises(Error):
            self._fetch(client)
        self.assertEqual(len(session.calls), 1)

    def test_client_and_server_errors_400_404_405_are_not_retried(self):
        _, _, Error = self._adapter()
        for status in (400, 404, 405):
            client, session = self._client(responses=[FakeResponse(status=status, payload={"error": "rejected"})])
            with self.subTest(status=status), self.assertRaises(Error):
                self._fetch(client)
            self.assertEqual(len(session.calls), 1)

    def test_http_503_uses_at_most_three_attempts_and_fixed_backoff(self):
        Client, Config, _ = self._adapter()
        session = FakeSession([FakeResponse(status=503), FakeResponse(status=503), FakeResponse(status=503)])
        delays = []
        client = Client(Config(base_url="https://t0.example.invalid", token="secret", max_lag_ms=120_000), session=session, sleep=delays.append, clock_ms=lambda: GENERATED)
        with self.assertRaises(Exception):
            self._fetch(client)
        self.assertEqual(len(session.calls), 3)
        self.assertEqual(delays, [0.25, 0.5])

    def test_transient_connection_timeout_uses_bounded_retry_policy(self):
        import requests
        Client, Config, _ = self._adapter()
        session = FakeSession([requests.exceptions.ConnectTimeout(), requests.exceptions.ReadTimeout(), FakeResponse(payload=response_envelope())])
        delays = []
        client = Client(Config(base_url="https://t0.example.invalid", token="secret", max_lag_ms=120_000), session=session, sleep=delays.append, clock_ms=lambda: GENERATED)
        self._fetch(client)
        self.assertEqual(len(session.calls), 3)
        self.assertEqual(delays, [0.25, 0.5])

    def test_response_body_over_256_kib_is_rejected(self):
        _, _, Error = self._adapter()
        response = FakeResponse(body=b" " * (256 * 1024 + 1))
        client, _ = self._client(responses=[response])
        with self.assertRaises(Error):
            self._fetch(client)

    def test_wrong_content_type_or_malformed_json_is_rejected(self):
        _, _, Error = self._adapter()
        responses = [
            FakeResponse(body=b"{}", content_type="text/plain"),
            FakeResponse(body=b"{not-json", content_type="application/json"),
        ]
        for response in responses:
            client, _ = self._client(responses=[response])
            with self.subTest(content_type=response.headers["Content-Type"]), self.assertRaises(Error):
                self._fetch(client)

    def test_secret_is_not_exposed_in_error_text(self):
        _, _, Error = self._adapter()
        client, _ = self._client(responses=[FakeResponse(status=401, payload={"error": "UNAUTHORIZED"})])
        with self.assertRaises(Error) as caught:
            self._fetch(client)
        self.assertNotIn("test-secret-token", str(caught.exception))

    def test_http_unavailable_has_no_sqlite_cache_or_venue_fallback(self):
        source = (BRIDGE / "context.py").read_text(encoding="utf-8")
        strategy = (BRIDGE / "ChartProFreqaiResearch.py").read_text(encoding="utf-8")
        self.assertNotIn("market_data.store", source)
        self.assertNotIn("canonical_db_path", strategy)
        self.assertNotIn("sqlite", source.lower())

    def test_native_order_signals_remain_disabled(self):
        source = (BRIDGE / "ChartProFreqaiResearch.py").read_text(encoding="utf-8")
        self.assertIn('dataframe["enter_long"] = 0', source)
        self.assertIn('dataframe["enter_short"] = 0', source)
        self.assertIn("return False", source)


if __name__ == "__main__":
    unittest.main()
