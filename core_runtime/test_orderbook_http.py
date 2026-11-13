"""Deterministic tests for the one-shot T1 Order Book HTTP reader."""

import json
import unittest

import requests

from core_runtime.orderbook_http import (
    OrderBookHttpClient,
    OrderBookHttpConfig,
    OrderBookHttpError,
)


NOW = 1_800_000_000_000


def valid_snapshot():
    return {
        "contractVersion": "T1_T2_ORDERBOOK_V1",
        "symbol": "BTCUSDT",
        "market": "BINANCE_USDM_PERPETUAL",
        "bids": [[str(50_000 - index), "0.012500"] for index in range(20)],
        "asks": [[str(50_001 + index), "0.015000"] for index in range(20)],
        "snapshotLastUpdateId": 100,
        "firstAppliedU": 101,
        "lastAppliedU": 101,
        "sourceTimestampMs": NOW - 100,
        "observedAtMs": NOW - 90,
        "decisionWatermark": 101,
        "generation": 1,
        "snapshotId": "sha256:" + "a" * 64,
        "continuity": "VERIFIED",
        "freshness": "FRESH",
        "depth": {"bids": 20, "asks": 20},
        "complete": True,
    }


class FakeResponse:
    def __init__(self, body, *, status=200, headers=None, chunk_size=4096):
        self.body = body if isinstance(body, bytes) else body.encode("utf-8")
        self.status_code = status
        self.headers = headers or {
            "Content-Type": "application/json",
            "Content-Length": str(len(self.body)),
        }
        self.chunk_size = chunk_size
        self.closed = False

    def iter_content(self, chunk_size=8192):
        for offset in range(0, len(self.body), min(chunk_size, self.chunk_size)):
            yield self.body[offset:offset + min(chunk_size, self.chunk_size)]

    def close(self):
        self.closed = True


class FakeSession:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.calls = []

    def get(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        if self.error is not None:
            raise self.error
        return self.response


def make_client(response=None, *, error=None, max_response_bytes=65_536):
    session = FakeSession(response=response, error=error)
    config = OrderBookHttpConfig(
        base_url="http://127.0.0.1:8787",
        token="local-test-token",
        max_response_bytes=max_response_bytes,
    )
    return OrderBookHttpClient(config, session=session), session


def response_for(payload, **kwargs):
    return FakeResponse(json.dumps(payload, separators=(",", ":")), **kwargs)


class OrderBookHttpConfigTests(unittest.TestCase):
    def test_only_loopback_http_origin_is_accepted(self):
        for url in (
            "http://example.com:8787",
            "https://example.com",
            "http://127.0.0.1:8787/private",
            "http://user:pass@127.0.0.1:8787",
            "http://127.0.0.1:8787?token=secret",
        ):
            with self.subTest(url=url), self.assertRaises(OrderBookHttpError):
                OrderBookHttpConfig(url, "local-test-token", max_response_bytes=65_536)

    def test_empty_token_and_unbounded_limits_are_rejected(self):
        with self.assertRaises(OrderBookHttpError):
            OrderBookHttpConfig("http://127.0.0.1:8787", "", max_response_bytes=65_536)
        with self.assertRaises(OrderBookHttpError):
            OrderBookHttpConfig("http://127.0.0.1:8787", "token", max_response_bytes=0)


class OneShotOrderBookHttpTests(unittest.TestCase):
    def test_valid_snapshot_is_returned_after_strict_validation_and_exactly_one_get(self):
        snapshot = valid_snapshot()
        response = response_for(snapshot)
        client, session = make_client(response)

        result = client.fetch(decision_at_ms=NOW)

        self.assertEqual(result, snapshot)
        self.assertEqual(len(session.calls), 1)
        args, kwargs = session.calls[0]
        self.assertEqual(args[0], "http://127.0.0.1:8787/internal/v1/orderbook/btcusdt")
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer local-test-token")
        self.assertEqual(kwargs["headers"]["Accept"], "application/json")
        self.assertEqual(kwargs["headers"]["Cache-Control"], "no-store")
        self.assertEqual(kwargs["timeout"], (0.25, 0.5))
        self.assertTrue(kwargs["stream"])
        self.assertFalse(kwargs["allow_redirects"])
        self.assertTrue(response.closed)

    def test_non_200_status_is_rejected_without_retry(self):
        for status in (301, 302, 400, 404, 429, 500, 503):
            with self.subTest(status=status):
                client, session = make_client(FakeResponse("{}", status=status))
                with self.assertRaises(OrderBookHttpError):
                    client.fetch(decision_at_ms=NOW)
                self.assertEqual(len(session.calls), 1)

    def test_unauthorized_response_has_stable_auth_error(self):
        client, session = make_client(FakeResponse("{}", status=401))
        with self.assertRaisesRegex(OrderBookHttpError, "AUTH_REJECTED"):
            client.fetch(decision_at_ms=NOW)
        self.assertEqual(len(session.calls), 1)

    def test_timeout_is_rejected_without_retry(self):
        client, session = make_client(error=requests.exceptions.ReadTimeout())
        with self.assertRaisesRegex(OrderBookHttpError, "HTTP_TIMEOUT"):
            client.fetch(decision_at_ms=NOW)
        self.assertEqual(len(session.calls), 1)

    def test_connection_refusal_is_rejected_without_retry(self):
        client, session = make_client(error=requests.exceptions.ConnectionError())
        with self.assertRaisesRegex(OrderBookHttpError, "HTTP_UNAVAILABLE"):
            client.fetch(decision_at_ms=NOW)
        self.assertEqual(len(session.calls), 1)

    def test_malformed_json_and_duplicate_keys_are_rejected(self):
        for body in (
            b'{"contractVersion":',
            b'{"a":1,"a":2}',
            b'{"contractVersion":"T1_T2_ORDERBOOK_V1","complete":NaN}',
        ):
            with self.subTest(body=body):
                client, session = make_client(FakeResponse(body))
                with self.assertRaises(OrderBookHttpError):
                    client.fetch(decision_at_ms=NOW)
                self.assertEqual(len(session.calls), 1)

    def test_wrong_content_type_and_compressed_response_are_rejected(self):
        for headers in (
            {"Content-Type": "text/plain", "Content-Length": "2"},
            {"Content-Type": "application/json", "Content-Encoding": "gzip"},
        ):
            with self.subTest(headers=headers):
                client, session = make_client(FakeResponse("{}", headers=headers))
                with self.assertRaises(OrderBookHttpError):
                    client.fetch(decision_at_ms=NOW)
                self.assertEqual(len(session.calls), 1)

    def test_declared_oversize_response_is_rejected_before_body_read(self):
        response = FakeResponse(
            b"{}",
            headers={"Content-Type": "application/json", "Content-Length": "999"},
        )
        client, session = make_client(response, max_response_bytes=128)
        with self.assertRaisesRegex(OrderBookHttpError, "RESPONSE_TOO_LARGE"):
            client.fetch(decision_at_ms=NOW)
        self.assertEqual(len(session.calls), 1)
        self.assertTrue(response.closed)

    def test_streamed_oversize_response_is_rejected_without_content_length(self):
        response = FakeResponse(
            b"x" * 256,
            headers={"Content-Type": "application/json"},
            chunk_size=32,
        )
        client, session = make_client(response, max_response_bytes=128)
        with self.assertRaisesRegex(OrderBookHttpError, "RESPONSE_TOO_LARGE"):
            client.fetch(decision_at_ms=NOW)
        self.assertEqual(len(session.calls), 1)
        self.assertTrue(response.closed)

    def test_unknown_missing_or_wrong_identity_fields_fail_closed(self):
        cases = []
        unknown = valid_snapshot()
        unknown["unexpected"] = True
        cases.append(unknown)
        missing = valid_snapshot()
        missing.pop("generation")
        cases.append(missing)
        wrong_symbol = valid_snapshot()
        wrong_symbol["symbol"] = "ETHUSDT"
        cases.append(wrong_symbol)
        wrong_version = valid_snapshot()
        wrong_version["contractVersion"] = "T1_BTCUSDT_ORDERBOOK_V1"
        cases.append(wrong_version)

        for payload in cases:
            with self.subTest(payload=payload):
                client, session = make_client(response_for(payload))
                with self.assertRaises(OrderBookHttpError):
                    client.fetch(decision_at_ms=NOW)
                self.assertEqual(len(session.calls), 1)

    def test_stale_future_and_incomplete_books_fail_closed(self):
        stale = valid_snapshot()
        stale["sourceTimestampMs"] = NOW - 2_001
        future = valid_snapshot()
        future["observedAtMs"] = NOW + 251
        incomplete = valid_snapshot()
        incomplete["complete"] = False
        depth = valid_snapshot()
        depth["bids"] = depth["bids"][:-1]
        depth["depth"]["bids"] = 19

        for payload in (stale, future, incomplete, depth):
            with self.subTest(payload=payload):
                client, session = make_client(response_for(payload))
                with self.assertRaises(OrderBookHttpError):
                    client.fetch(decision_at_ms=NOW)
                self.assertEqual(len(session.calls), 1)

    def test_invalid_decision_timestamp_fails_before_network_call(self):
        client, session = make_client(response_for(valid_snapshot()))
        for value in (True, -1, 1.5, "1800000000000"):
            with self.subTest(value=value), self.assertRaises(OrderBookHttpError):
                client.fetch(decision_at_ms=value)
        self.assertEqual(session.calls, [])


if __name__ == "__main__":
    unittest.main()
