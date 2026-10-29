import copy
from email.message import Message
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit
from urllib.request import HTTPHandler, ProxyHandler, build_opener as real_build_opener

from data_lake.client import DataLakeClient, DataLakeError, MAX_RESPONSE_BYTES, _NoRedirect
from market_data.api import application
from market_data.store import Candle, CandleStore, INTERVAL_MS, read_window


class Response(io.BytesIO):
    def __init__(self, body, status=200, headers=None, url="http://127.0.0.1/v1/candles"):
        raw = body if isinstance(body, bytes) else json.dumps(body).encode()
        super().__init__(raw)
        self.status = self.code = status
        self.msg, self.url = "response", url
        self.headers = Message()
        for key, value in (headers or {"Content-Type": "application/json", "Content-Length": str(len(raw))}).items():
            self.headers[key] = value

    def info(self):
        return self.headers


class ApiTransport:
    """Replace only urllib's socket boundary; run the real API and SQLite store."""

    def __init__(self, database, token="consumer-test-token"):
        self.database, self.token, self.requests = database, token, []

    def open(self, request, timeout):
        self.requests.append((request, timeout))
        url, status = urlsplit(request.full_url), []
        environ = {"REQUEST_METHOD": request.get_method(), "PATH_INFO": url.path,
                   "QUERY_STRING": url.query, "HTTP_AUTHORIZATION": request.get_header("Authorization", "")}
        with patch.dict(os.environ, {"MARKET_DATA_DB": str(self.database), "MARKET_DATA_TOKEN": self.token}, clear=True):
            raw = b"".join(application(environ, lambda code, headers: status.append((code, headers))))
        return Response(raw, int(status[0][0].split()[0]), dict(status[0][1]), request.full_url)


class ClientTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.db = Path(self.temp.name)/"candles.sqlite3"
        self.step = INTERVAL_MS["15m"]
        self.start = 1_700_000_000_000//self.step*self.step
        self.end = self.start+2*self.step
        self.cutoff = self.end+100
        CandleStore(self.db).insert([
            Candle("15m", self.start+i*self.step, "100.00000000000000000001", "101", "99", "100.5", "2.5",
                   self.start+(i+1)*self.step+7) for i in range(2)])
        self.report = read_window(self.db, "BTCUSDT", "15m", self.start, self.end, self.cutoff)
        self.transport = ApiTransport(self.db)
        self.client = DataLakeClient("http://127.0.0.1:8788", self.transport.token)
        self.client._opener = self.transport

    def read(self):
        return self.client.read_candles("15m", self.start, self.end, self.cutoff)

    def test_real_api_and_sqlite_preserve_precision_query_auth_and_as_of(self):
        report = self.read()
        self.assertEqual(report["datasetVersion"], self.report["datasetVersion"])
        self.assertEqual(report["candles"][0]["open"], "100.00000000000000000001")
        request, timeout = self.transport.requests[0]
        self.assertEqual(timeout, 15)
        self.assertEqual(request.get_header("Authorization"), "Bearer "+self.transport.token)
        self.assertNotIn(self.transport.token, request.full_url)
        self.assertEqual(parse_qs(urlsplit(request.full_url).query), {
            "symbol": ["BTCUSDT"], "timeframe": ["15m"], "startMs": [str(self.start)],
            "endMs": [str(self.end)], "asOfMs": [str(self.cutoff)]})
        past = self.client.read_candles("15m", self.start, self.end, self.start+self.step)
        self.assertFalse(past["coverage"]["complete"])
        self.assertEqual(past["candles"], [])
        self.assertEqual(past["coverage"]["gaps"], [{"startMs": self.start, "endMs": self.end}])

    @unittest.skipUnless(importlib.util.find_spec("fastapi") and importlib.util.find_spec("httpx"),
                         "FastAPI/httpx unavailable; installed by data-lake CI")
    def test_real_fastapi_sqlite_response_passes_consumer_validation(self):
        from data_lake.api import create_app
        from data_lake.test_api import asgi_request

        app = create_app(str(self.db), self.transport.token)

        class AsgiTransport:
            def open(transport, request, timeout):
                url = urlsplit(request.full_url)
                response = asgi_request(app, request.get_method(), url.path+"?"+url.query,
                                        headers={"Authorization": request.get_header("Authorization")})
                return Response(response.content, response.status_code, dict(response.headers))

        self.client._opener = AsgiTransport()
        report = self.read()
        self.assertEqual(report["datasetVersion"], self.report["datasetVersion"])
        self.assertTrue(report["coverage"]["complete"])
        self.assertEqual(report["candles"][0]["open"], "100.00000000000000000001")

    def test_invalid_origins_tokens_and_windows_never_make_a_request(self):
        for url in ("http://example.com", "http://localhost", "http://127.1", "http://2130706433",
                    "https://user:secret@example.com", "https://example.com?token=secret",
                    "https://example.com/#secret", "https://example.com/prefix", "https://example.com\\@evil.com",
                    "https://example.com\n", "https://[::1%25eth0]", "ftp://example.com", "https://example.com:99999"):
            with self.subTest(url=url), self.assertRaises(DataLakeError):
                DataLakeClient(url, "safe")
        for token in ("", "bad\nheader", "bad token", "é", "x"*4097, None):
            with self.subTest(token_length=len(token) if token else 0), self.assertRaises(DataLakeError):
                DataLakeClient("https://data.example.com", token)
        self.assertEqual(DataLakeClient("http://[::1]:8788/", "safe").base_url, "http://[::1]:8788")
        for args in (("1d", self.start, self.end), ("15m", True, self.end),
                     ("15m", self.start+1, self.end), ("15m", self.start, self.start+2001*self.step)):
            with self.subTest(args=args), self.assertRaises(DataLakeError):
                self.client.read_candles(*args)
        with self.assertRaises(DataLakeError):
            self.client.read_candles("15m", self.start, self.end, 2**63-1)
        self.assertEqual(self.transport.requests, [])

    def test_only_literal_loopback_bypasses_inherited_proxies_without_enabling_redirects(self):
        proxy_environment = {"http_proxy": "http://proxy.invalid:8888",
                             "https_proxy": "http://proxy.invalid:8888"}
        with patch.dict(os.environ, proxy_environment, clear=True):
            for base_url in ("http://127.0.0.1:8788", "https://127.0.0.1:8788", "http://[::1]:8788"):
                with self.subTest(base_url=base_url), patch("data_lake.client.build_opener", wraps=real_build_opener) as build:
                    DataLakeClient(base_url, "safe")
                    handlers = build.call_args.args
                    proxies = [handler for handler in handlers if isinstance(handler, ProxyHandler)]
                    self.assertEqual(len(proxies), 1)
                    self.assertEqual(proxies[0].proxies, {})
                    self.assertTrue(any(isinstance(handler, _NoRedirect) for handler in handlers))
            remote = DataLakeClient("https://data.example.com", "safe")
            proxies = [handler.proxies for handler in remote._opener.handlers if isinstance(handler, ProxyHandler)]
            self.assertEqual(proxies, [{"http": "http://proxy.invalid:8888", "https": "http://proxy.invalid:8888"}])
            self.assertEqual(dict(os.environ), proxy_environment)

    def test_redirect_is_rejected_before_sending_bearer_to_second_origin(self):
        calls = []

        class RedirectTransport(HTTPHandler):
            def http_open(self, request):
                calls.append(request)
                return Response(b"", 302, {"Location": "https://attacker.invalid/stolen", "Content-Length": "0"}, request.full_url)

        self.client._opener = real_build_opener(_NoRedirect(), RedirectTransport())
        with self.assertRaises(DataLakeError) as failure:
            self.read()
        self.assertEqual(len(calls), 1)
        self.assertNotIn(self.transport.token, str(failure.exception))
        self.assertNotIn("attacker", str(failure.exception))

    def test_hash_market_source_closedness_order_and_coverage_are_verified(self):
        mutations = (
            lambda r: r.update(symbol="ETHUSDT"),
            lambda r: r.update(startMs=self.start+self.step),
            lambda r: r.update(asOfMs=None),
            lambda r: r.update(datasetVersion="sha256:"+"a"*64),
            lambda r: r["candles"][0].update(close="100.6"),
            lambda r: r["candles"][0].update(source="fabricated"),
            lambda r: r["candles"][0].update(isClosed=1),
            lambda r: r["candles"][0].update(availableAtMs=self.cutoff+1),
            lambda r: r["candles"][0].update(open="100.000"),
            lambda r: r["candles"].reverse(),
            lambda r: r["coverage"].update(returned=True),
            lambda r: r["coverage"].update(gaps=[{"startMs": self.start, "endMs": self.end}]),
        )
        for mutation in mutations:
            body = copy.deepcopy(self.report)
            mutation(body)
            with self.subTest(body=body), patch.object(self.transport, "open", return_value=Response(body)), self.assertRaises(DataLakeError):
                self.read()

    def test_bounded_malformed_and_transport_failures_do_not_expose_credentials(self):
        responses = (Response(b"{}", 401), Response(b"not json"), Response(b'{"x":1,"x":2}'),
                     Response(b'{"x":NaN}'), Response(b"x"*(MAX_RESPONSE_BYTES+1), headers={"Content-Type": "application/json"}),
                     Response(b"{}", headers={"Content-Type": "text/html"}),
                     Response(b"{}", headers={"Content-Type": "application/json", "Content-Length": "200"}),
                     Response(b"{}", headers={"Content-Type": "application/json", "Content-Encoding": "gzip"}))
        for response in responses:
            with patch.object(self.transport, "open", return_value=response), self.assertRaises(DataLakeError) as failure:
                self.read()
            self.assertNotIn(self.transport.token, str(failure.exception))
        with patch.object(self.transport, "open", side_effect=OSError(self.transport.token)), self.assertRaises(DataLakeError) as failure:
            self.read()
        self.assertNotIn(self.transport.token, str(failure.exception))


if __name__ == "__main__":
    unittest.main()
