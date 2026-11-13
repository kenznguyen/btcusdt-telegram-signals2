"""Loopback TCP integration for the T2 client against the frozen T1 V1 wire shape."""

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from threading import Thread
import unittest

from core_runtime.orderbook_http import OrderBookHttpClient, OrderBookHttpConfig
from core_runtime.test_orderbook_http import NOW, valid_snapshot


TOKEN = "integration-only-token"


class T1WireFixtureServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address, payload):
        super().__init__(address, T1WireFixtureHandler)
        self.payload = payload
        self.body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        self.requests_seen = []


class T1WireFixtureHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def do_GET(self):
        self.server.requests_seen.append({
            "path": self.path,
            "authorization": self.headers.get("Authorization"),
        })
        if self.path != "/internal/v1/orderbook/btcusdt":
            self.send_error(404)
            return
        if self.headers.get("Authorization") != "Bearer " + TOKEN:
            self.send_error(401)
            return

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(self.server.body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(self.server.body)

    def log_message(self, _format, *_args):
        return


class T1T2OrderBookHttpIntegrationTests(unittest.TestCase):
    def test_t2_reader_round_trips_one_complete_t1_v1_snapshot_over_loopback(self):
        payload = valid_snapshot()
        server = T1WireFixtureServer(("127.0.0.1", 0), payload)
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            port = server.server_address[1]
            config = OrderBookHttpConfig(
                base_url=f"http://127.0.0.1:{port}",
                token=TOKEN,
            )
            client = OrderBookHttpClient(config)

            accepted = client.fetch(decision_at_ms=NOW)

            self.assertEqual(accepted, payload)
            self.assertEqual(accepted["bids"][0], ["50000", "0.012500"])
            self.assertEqual(accepted["asks"][0], ["50001", "0.015000"])
            self.assertEqual(accepted["depth"], {"bids": 20, "asks": 20})
            self.assertEqual(server.requests_seen, [{
                "path": "/internal/v1/orderbook/btcusdt",
                "authorization": "Bearer " + TOKEN,
            }])
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
