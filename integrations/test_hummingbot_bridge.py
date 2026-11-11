import io
import http.client
import json
import unittest
from unittest.mock import patch

from integrations import hummingbot_bridge as bridge


class HummingbotBridgeTest(unittest.TestCase):
    def setUp(self):
        self.now_ms = 1_800_000_000_000
        self.snapshot = {
            "trading_pair": "BTC-USDT",
            "timestamp": self.now_ms / 1000,
            "bids": [{"price": 99900, "amount": 2}],
            "asks": [{"price": 100100, "amount": 3}],
        }
        self.config = {
            "HB_API_URL": "http://localhost:8000",
            "HB_API_USER": "api-user",
            "HB_API_PASSWORD": "upstream-secret",
            "HB_BRIDGE_TOKEN": "phone-token",
            "HB_SYMBOLS": "BTCUSDT,ETHUSDT",
        }

    def request(self, query="symbol=BTCUSDT", token="phone-token", path="/v1/order-book", method="GET"):
        status = []
        environ = {"REQUEST_METHOD": method, "PATH_INFO": path, "QUERY_STRING": query,
                   "HTTP_AUTHORIZATION": "Bearer " + token}
        body = b"".join(bridge.application(environ, lambda s, h: status.append((s, h))))
        return int(status[0][0].split()[0]), json.loads(body)

    def test_snapshot_preserves_upstream_observation_time(self):
        result = bridge.normalize_snapshot(self.snapshot, "BTCUSDT", self.now_ms + 1000)
        self.assertEqual(result["observedAtMs"], self.now_ms)
        self.assertEqual(result["bids"], [{"price": 99900.0, "quantity": 2.0}])
        self.assertEqual(result["source"], "hummingbot")

    def test_rejects_stale_future_wrong_pair_crossed_and_nonfinite(self):
        invalid = [
            {"timestamp": (self.now_ms - 30001) / 1000},
            {"timestamp": (self.now_ms + 5001) / 1000},
            {"trading_pair": "ETH-USDT"},
            {"asks": [{"price": 99000, "amount": 1}]},
            {"bids": [{"price": float("nan"), "amount": 1}]},
            {"bids": [{"price": 99900, "amount": -1}]},
            {"bids": []},
            {"timestamp": True},
        ]
        for values in invalid:
            with self.subTest(values=values), self.assertRaises(ValueError):
                bridge.normalize_snapshot({**self.snapshot, **values}, "BTCUSDT", self.now_ms)

    def test_auth_and_allowlist_stop_requests_before_upstream(self):
        with patch.dict("os.environ", self.config, clear=True), patch.object(bridge, "fetch_snapshot") as fetch:
            self.assertEqual(self.request(token="wrong")[0], 401)
            self.assertEqual(self.request(query="symbol=SOLUSDT")[0], 400)
            self.assertEqual(self.request(query="symbol=BTCUSDT&symbol=ETHUSDT")[0], 400)
            self.assertEqual(self.request(method="POST")[0], 405)
            fetch.assert_not_called()

    def test_unconfigured_token_never_exposes_data(self):
        with patch.dict("os.environ", {**self.config, "HB_BRIDGE_TOKEN": ""}, clear=True):
            self.assertEqual(self.request()[0], 503)

    def test_success_and_upstream_errors_do_not_leak_credentials(self):
        with patch.dict("os.environ", self.config, clear=True), patch.object(bridge.time, "time", return_value=self.now_ms / 1000):
            with patch.object(bridge, "fetch_snapshot", return_value=self.snapshot):
                code, result = self.request()
                self.assertEqual(code, 200)
                self.assertEqual(result["symbol"], "BTCUSDT")
            with patch.object(bridge, "fetch_snapshot", side_effect=OSError("upstream-secret")):
                code, result = self.request()
                self.assertEqual(code, 502)
                self.assertNotIn("upstream-secret", json.dumps(result))

    def test_uses_real_api_contract_and_limits_response(self):
        class Response(io.BytesIO):
            def __enter__(self):
                return self

            def __exit__(self, *args):
                self.close()

        with patch.dict("os.environ", self.config, clear=True), patch.object(bridge.OPENER, "open", return_value=Response(json.dumps(self.snapshot).encode())) as call:
            result = bridge.fetch_snapshot("BTCUSDT")
            self.assertEqual(result, self.snapshot)
            request = call.call_args.args[0]
            self.assertEqual(request.full_url, "http://localhost:8000/market-data/order-book")
            self.assertEqual(json.loads(request.data), {"connector_name": "binance_perpetual", "trading_pair": "BTC-USDT", "depth": 20})
            self.assertTrue(request.get_header("Authorization").startswith("Basic "))
        with patch.dict("os.environ", self.config, clear=True), patch.object(bridge.OPENER, "open", return_value=Response(b" " * (bridge.MAX_BYTES + 1))):
            with self.assertRaises(ValueError):
                bridge.fetch_snapshot("BTCUSDT")

    def test_truncated_upstream_response_becomes_sanitized_gateway_error(self):
        error = http.client.IncompleteRead(b"upstream-secret", 20)
        with patch.dict("os.environ", self.config, clear=True), patch.object(bridge, "fetch_snapshot", side_effect=error):
            code, result = self.request()
            self.assertEqual(code, 502)
            self.assertEqual(result, {"error": "UPSTREAM_UNAVAILABLE"})


if __name__ == "__main__":
    unittest.main()
