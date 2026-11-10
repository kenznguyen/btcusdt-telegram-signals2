"""G4 read-only runtime acceptance probe contracts; uses disposable SQLite fixtures only."""
import hashlib
import pathlib
import sqlite3
import tempfile
import unittest

from ci.t0_runtime_acceptance import inspect_sqlite_read_only
import json
from urllib.parse import parse_qs, urlsplit

from ci.t0_runtime_acceptance import ProbeError, probe_candle_api, probe_feeder_health

from app import app as feeder_health_app
from market_data.api import application as candle_api_application
from wsgiref.util import setup_testing_defaults

NOW = 1_800_000_000_000
LEASE_NAME = "binance-btcusdt-canonical"


def create_fixture(path, *, include_lease=True, lease_expiry=NOW + 60_000):
    connection = sqlite3.connect(path)
    connection.execute("""CREATE TABLE candles (
        exchange TEXT NOT NULL, market_type TEXT NOT NULL, symbol TEXT NOT NULL,
        timeframe TEXT NOT NULL, open_time_ms INTEGER NOT NULL,
        open TEXT NOT NULL, high TEXT NOT NULL, low TEXT NOT NULL,
        close TEXT NOT NULL, volume TEXT NOT NULL, available_at_ms INTEGER NOT NULL,
        PRIMARY KEY (exchange, market_type, symbol, timeframe, open_time_ms)
    )""")
    if include_lease:
        connection.execute("""CREATE TABLE feeder_leases (
            lease_name TEXT PRIMARY KEY, owner TEXT, generation INTEGER NOT NULL,
            expires_at_ms INTEGER NOT NULL
        )""")
        connection.execute(
            "INSERT INTO feeder_leases VALUES (?, ?, ?, ?)",
            (LEASE_NAME, "fixture-owner-secret", 7, lease_expiry),
        )
    for timeframe, interval in (("15m", 900_000), ("1h", 3_600_000)):
        open_time = (NOW // interval) * interval - interval
        connection.execute(
            "INSERT INTO candles VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            ("binance", "USDT_PERPETUAL", "BTCUSDT", timeframe, open_time,
             "100", "101", "99", "100", "1", open_time + interval + 100),
        )
    connection.commit()
    connection.close()



class FakeResponse:
    def __init__(self, payload, status=200):
        self.payload = json.dumps(payload).encode()
        self.status = status
        self.headers = {"Content-Type": "application/json"}

    def read(self, limit=-1):
        return self.payload if limit < 0 else self.payload[:limit]

    def getcode(self):
        return self.status

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


class FakeOpener:
    def __init__(self, responder):
        self.responder = responder
        self.requests = []

    def open(self, request, timeout):
        self.requests.append((request, timeout))
        return self.responder(request)


def candle_payload(timeframe, now_ms):
    interval = {"15m": 900_000, "1h": 3_600_000}[timeframe]
    end_ms = (now_ms // interval) * interval
    start_ms = end_ms - 2 * interval
    candles = []
    for open_time in (start_ms, start_ms + interval):
        candles.append({
            "exchange": "binance", "marketType": "USDT_PERPETUAL",
            "symbol": "BTCUSDT", "timeframe": timeframe,
            "openTimeMs": open_time, "closeTimeMs": open_time + interval,
            "open": "100", "high": "101", "low": "99", "close": "100",
            "volume": "1", "isClosed": True,
            "availableAtMs": open_time + interval + 100,
            "availabilityKind": "FIRST_OBSERVED", "quality": "VALIDATED",
            "source": "ccxt.binanceusdm",
        })
    return {
        "exchange": "binance", "marketType": "USDT_PERPETUAL",
        "symbol": "BTCUSDT", "timeframe": timeframe,
        "startMs": start_ms, "endMs": end_ms, "asOfMs": now_ms,
        "datasetVersion": "sha256:" + "a" * 64,
        "coverage": {"expected": 2, "returned": 2, "complete": True, "gaps": []},
        "contractVersion": "1.0.0", "schemaVersion": 1,
        "volumeUnit": "BTC_BASE_ASSET", "source": "ccxt.binanceusdm",
        "generatedAtMs": now_ms,
        "freshness": {
            "latestExpectedOpenTimeMs": end_ms - interval,
            "latestReturnedOpenTimeMs": end_ms - interval,
            "latestCloseTimeMs": end_ms,
            "latestAvailableAtMs": end_ms + 100,
            "observationAgeMs": now_ms - (end_ms + 100),
            "closeLagMs": now_ms - end_ms,
            "evaluable": True,
        },
        "candles": candles,
    }


class ReadOnlySQLiteAcceptanceTests(unittest.TestCase):
    def test_reads_integrity_lease_and_both_timeframe_watermarks(self):
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / "canonical.sqlite3"
            create_fixture(path)
            result = inspect_sqlite_read_only(str(path), now_ms=NOW + 5_000)

        self.assertEqual(result["integrity"], "ok")
        self.assertTrue(result["lease"]["valid"])
        self.assertEqual(result["lease"]["generation"], 7)
        self.assertNotIn("fixture-owner-secret", str(result))
        self.assertEqual(set(result["timeframes"]), {"15m", "1h"})
        self.assertIsNotNone(result["timeframes"]["15m"]["latest_open_time_ms"])
        self.assertIsNotNone(result["timeframes"]["1h"]["latest_open_time_ms"])

    def test_owner_identity_is_fingerprinted_not_disclosed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / "canonical.sqlite3"
            create_fixture(path)
            result = inspect_sqlite_read_only(str(path), now_ms=NOW)
        expected = hashlib.sha256(b"fixture-owner-secret").hexdigest()[:16]
        self.assertEqual(result["lease"]["owner_fingerprint"], expected)
        self.assertNotIn("owner", result["lease"])

    def test_expired_lease_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / "canonical.sqlite3"
            create_fixture(path, lease_expiry=NOW - 1)
            result = inspect_sqlite_read_only(str(path), now_ms=NOW)
        self.assertFalse(result["lease"]["valid"])
        self.assertEqual(result["lease"]["state"], "EXPIRED")

    def test_missing_lease_table_fails_closed_without_schema_creation(self):
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / "canonical.sqlite3"
            create_fixture(path, include_lease=False)
            with self.assertRaisesRegex(RuntimeError, "feeder_leases"):
                inspect_sqlite_read_only(str(path), now_ms=NOW)
            connection = sqlite3.connect(path)
            tables = {row[0] for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )}
            connection.close()
        self.assertNotIn("feeder_leases", tables)

    def test_missing_database_is_not_created(self):
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / "missing.sqlite3"
            with self.assertRaises(FileNotFoundError):
                inspect_sqlite_read_only(str(path), now_ms=NOW)
            self.assertFalse(path.exists())

    def test_snapshot_does_not_change_database_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / "canonical.sqlite3"
            create_fixture(path)
            before = hashlib.sha256(path.read_bytes()).hexdigest()
            inspect_sqlite_read_only(str(path), now_ms=NOW)
            after = hashlib.sha256(path.read_bytes()).hexdigest()
        self.assertEqual(after, before)



    def test_detailed_feeder_health_and_candle_api_are_separate_applications(self):
        self.assertIn("/health/data", {
            rule.rule for rule in feeder_health_app.url_map.iter_rules()
        })
        environ = {}
        setup_testing_defaults(environ)
        environ.update({"REQUEST_METHOD": "GET", "PATH_INFO": "/health/data"})
        response = {}

        def start_response(status, headers):
            response["status"] = status

        body = b"".join(candle_api_application(environ, start_response))
        self.assertTrue(response["status"].startswith("404"))
        self.assertIn(b"NOT_FOUND", body)

        environ["PATH_INFO"] = "/health"
        body = b"".join(candle_api_application(environ, start_response))
        self.assertTrue(response["status"].startswith("200"))
        self.assertIn(b"canonical-market-data", body)
        self.assertNotIn(b"timeframes", body)

    def test_watermarks_report_close_lag_without_claiming_health(self):
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / "canonical.sqlite3"
            create_fixture(path)
            result = inspect_sqlite_read_only(str(path), now_ms=NOW + 5_000)
        for timeframe, interval in (("15m", 900_000), ("1h", 3_600_000)):
            item = result["timeframes"][timeframe]
            self.assertEqual(
                item["close_lag_ms"],
                NOW + 5_000 - item["latest_close_time_ms"],
            )
            self.assertEqual(item["latest_close_time_ms"],
                           item["latest_open_time_ms"] + interval)


    def test_candle_api_probe_checks_both_timeframes_with_bearer_header_only(self):
        now_ms = NOW + 5_000
        fake = FakeOpener(lambda request: (
            FakeResponse({"ok": True, "service": "canonical-market-data"})
            if urlsplit(request.full_url).path == "/health"
            else FakeResponse(candle_payload(
                parse_qs(urlsplit(request.full_url).query)["timeframe"][0], now_ms
            ))
        ))
        result = probe_candle_api(
            "http://127.0.0.1:8788", "fixture-token-secret",
            now_ms=now_ms, opener_factory=lambda: fake,
        )
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(set(result["timeframes"]), {"15m", "1h"})
        for request, timeout in fake.requests:
            self.assertLessEqual(timeout, 5)
            self.assertNotIn("fixture-token-secret", request.full_url)
            if urlsplit(request.full_url).path == "/v1/candles":
                self.assertEqual(request.get_header("Authorization"),
                                 "Bearer fixture-token-secret")

    def test_candle_api_probe_rejects_non_loopback_and_missing_token(self):
        with self.assertRaises(ProbeError):
            probe_candle_api("https://example.com", "token", now_ms=NOW)
        with self.assertRaises(ProbeError):
            probe_candle_api("http://127.0.0.1:8788", "", now_ms=NOW)

    def test_candle_api_probe_fails_closed_on_incomplete_coverage(self):
        now_ms = NOW + 5_000
        def respond(request):
            if urlsplit(request.full_url).path == "/health":
                return FakeResponse({"ok": True, "service": "canonical-market-data"})
            payload = candle_payload(
                parse_qs(urlsplit(request.full_url).query)["timeframe"][0], now_ms
            )
            payload["coverage"]["complete"] = False
            payload["coverage"]["gaps"] = [{"startMs": 1, "endMs": 2}]
            return FakeResponse(payload)
        with self.assertRaises(ProbeError):
            probe_candle_api(
                "http://127.0.0.1:8788", "token", now_ms=now_ms,
                opener_factory=lambda: FakeOpener(respond),
            )

    def test_candle_api_probe_fails_closed_on_stale_watermark(self):
        now_ms = NOW + 5_000
        def respond(request):
            if urlsplit(request.full_url).path == "/health":
                return FakeResponse({"ok": True, "service": "canonical-market-data"})
            timeframe = parse_qs(urlsplit(request.full_url).query)["timeframe"][0]
            payload = candle_payload(timeframe, now_ms)
            payload["freshness"]["closeLagMs"] = 2 * {"15m": 900_000, "1h": 3_600_000}[timeframe]
            return FakeResponse(payload)
        with self.assertRaises(ProbeError):
            probe_candle_api(
                "http://127.0.0.1:8788", "token", now_ms=now_ms,
                opener_factory=lambda: FakeOpener(respond),
            )

    def test_detailed_health_probe_never_guesses_missing_flask_listener(self):
        result = probe_feeder_health(None, now_ms=NOW)
        self.assertEqual(result["status"], "NOT_VERIFIED")
        self.assertEqual(result["reason"], "LISTENER_NOT_CONFIGURED")

    def test_detailed_health_probe_requires_both_timeframes_healthy(self):
        payload = {
            "state": "HEALTHY", "live": True, "ready": True,
            "timeframes": {
                "15m": {"state": "HEALTHY", "unresolved_gap_count": 0, "sync_error": None},
                "1h": {"state": "HEALTHY", "unresolved_gap_count": 0, "sync_error": None},
            },
        }
        fake = FakeOpener(lambda _request: FakeResponse(payload))
        result = probe_feeder_health(
            "http://127.0.0.1:8790", now_ms=NOW,
            opener_factory=lambda: fake,
        )
        self.assertEqual(result["status"], "PASS")
        payload["timeframes"]["1h"]["state"] = "STALE"
        with self.assertRaises(ProbeError):
            probe_feeder_health(
                "http://127.0.0.1:8790", now_ms=NOW,
                opener_factory=lambda: FakeOpener(lambda _request: FakeResponse(payload)),
            )


    def test_http_transport_is_bounded_loopback_only_and_rejects_redirects(self):
        from ci import t0_runtime_acceptance as probe
        import inspect
        transport_source = inspect.getsource(probe._default_opener) + inspect.getsource(probe._request_json)
        self.assertIn("ProxyHandler({})", transport_source)
        self.assertIn("_RejectRedirects", transport_source)
        self.assertIn("MAX_HTTP_BODY_BYTES + 1", transport_source)
        self.assertEqual(probe.MAX_HTTP_BODY_BYTES, 1_048_576)
        for unsafe_url in (
            "http://user:pass@127.0.0.1:8788",
            "http://127.0.0.1:8788/prefix",
            "http://127.0.0.1:8788?token=secret",
            "http://192.0.2.1:8788",
        ):
            with self.subTest(url=unsafe_url), self.assertRaises(ProbeError):
                probe._loopback_base_url(unsafe_url)

    def test_candle_api_probe_rejects_non_200_health_response(self):
        fake = FakeOpener(lambda _request: FakeResponse({"ok": False}, status=302))
        with self.assertRaises(ProbeError):
            probe_candle_api(
                "http://127.0.0.1:8788", "token", now_ms=NOW,
                opener_factory=lambda: fake,
            )

if __name__ == "__main__":
    unittest.main()
