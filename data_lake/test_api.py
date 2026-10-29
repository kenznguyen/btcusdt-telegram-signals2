import asyncio
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

import httpx

from data_lake.api import create_app
from market_data.store import Candle, CandleStore


def asgi_request(app, method, path, headers=None):
    async def run():
        # Keep worker callbacks responsive on executors with restricted self-pipe wakeups.
        async def heartbeat():
            while True:
                await asyncio.sleep(0.01)

        tick = asyncio.create_task(heartbeat())
        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                return await asyncio.wait_for(client.request(method, path, headers=headers), timeout=5)
        finally:
            tick.cancel()
            try:
                await tick
            except asyncio.CancelledError:
                pass

    return asyncio.run(run())


class DataLakeApiTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.database = Path(self.temp.name) / "lake.sqlite3"
        self.now, self.step = 1_800_000_000_000, 900_000
        self.start = self.now - 2 * self.step
        CandleStore(self.database).insert([Candle("15m", self.start, "100.01", "101", "99", "100.5", "2.50",
                                                   self.start + self.step + 7)])
        self.app = create_app(str(self.database), "read-token")

    def request(self, path="/v1/candles", query=None, token="read-token", method="GET"):
        query = query if query is not None else f"symbol=BTCUSDT&timeframe=15m&startMs={self.start}&endMs={self.now}"
        with patch("data_lake.api.now_ms", return_value=self.now):
            response = asgi_request(self.app, method, path + "?" + query, headers={"Authorization": "Bearer " + token})
        self.assertEqual("no-store", response.headers["cache-control"])
        self.assertEqual("nosniff", response.headers["x-content-type-options"])
        return response

    def test_exact_canonical_candles_and_gap_metadata_are_preserved(self):
        response = self.request()
        self.assertEqual(200, response.status_code)
        result = response.json()
        self.assertEqual("100.01", result["candles"][0]["open"])
        self.assertEqual("2.5", result["candles"][0]["volume"])
        self.assertEqual(self.now, result["generatedAtMs"])
        self.assertEqual({"expected": 2, "returned": 1, "complete": False,
                          "gaps": [{"startMs": self.start + self.step, "endMs": self.now}]}, result["coverage"])

    def test_auth_precedes_query_and_reads_never_create_a_missing_store(self):
        for path in ("/v1/candles", "/v1/features", "/v1/cross-analysis"):
            response = self.request(path, query="invalid", token="wrong-token")
            self.assertEqual(401, response.status_code)
            self.assertEqual({"error": "UNAUTHORIZED"}, response.json())
        missing = Path(self.temp.name) / "missing.sqlite3"
        app = create_app(str(missing), "read-token")
        with patch("data_lake.api.now_ms", return_value=self.now):
            for endpoint in ("/v1/candles", "/v1/features", "/v1/cross-analysis"):
                response = asgi_request(app, "GET", f"{endpoint}?symbol=BTCUSDT&timeframe=15m&startMs={self.start}&endMs={self.now}",
                                        headers={"Authorization": "Bearer read-token"})
                self.assertEqual(503, response.status_code)
                self.assertFalse(missing.exists())
                self.assertNotIn(str(missing), response.text)

    def test_invalid_duplicate_unbounded_and_future_queries_are_rejected(self):
        base = f"symbol=BTCUSDT&timeframe=15m&startMs={self.start}&endMs={self.now}"
        queries = (base + "&symbol=ETHUSDT", base + "&token=secret", base.replace("15m", "1d"),
                   base.replace(str(self.now), str(self.now + self.step)), base + f"&asOfMs={self.now+1}",
                   base.replace(str(self.start), str(self.now - 2001 * self.step)), "x=" + "a" * 2048)
        for query in queries:
            with self.subTest(query=query[:80]):
                self.assertEqual(400, self.request(query=query).status_code)

    def test_as_of_excludes_later_observation_and_corrupt_future_rows_fail_closed(self):
        response = self.request(query=f"symbol=BTCUSDT&timeframe=15m&startMs={self.start}&endMs={self.now}"
                                      f"&asOfMs={self.start+self.step}")
        self.assertEqual([], response.json()["candles"])
        with sqlite3.connect(self.database) as connection:
            connection.execute("UPDATE candles SET available_at_ms=?", (self.now + 1,))
        response = self.request()
        self.assertEqual(503, response.status_code)
        self.assertEqual({"error": "STORE_UNAVAILABLE"}, response.json())

    def test_health_is_public_docs_disabled_and_methods_read_only(self):
        response = self.request("/health", token="")
        self.assertEqual(200, response.status_code)
        self.assertFalse(response.json()["liveTradingSupported"])
        self.assertEqual(405, self.request(method="POST").status_code)
        for path in ("/docs", "/openapi.json", "/v1/orders"):
            self.assertEqual(404, self.request(path).status_code)
        app = create_app(str(self.database), "")
        self.assertEqual(503, asgi_request(app, "GET", "/v1/candles").status_code)

    def test_connection_failure_never_exposes_database_credentials(self):
        secret = "postgresql://operator:private-password@db/lake"
        with patch("data_lake.api.read_window", side_effect=OSError(secret)):
            response = self.request()
        self.assertEqual(503, response.status_code)
        self.assertNotIn(secret, response.text)
        self.assertNotIn("private-password", response.text)

    def test_features_and_cross_analysis_use_real_canonical_and_archived_data(self):
        from futures_intelligence.import_collector import build_snapshot
        from market_data.archive import archive_snapshot, init_archive

        init_archive(self.database)
        closed = self.start + self.step
        snapshots = [build_snapshot(closed - 30_000, closed - 20_000, closed - 10_000),
                     build_snapshot(closed - 10_000, closed + 10_000, closed + 20_000),
                     build_snapshot(closed + 60_000, closed + 70_000, closed + 80_000)]
        for snapshot in snapshots:
            archive_snapshot(self.database, snapshot, self.now + 1)
        features = self.request("/v1/features")
        self.assertEqual(200, features.status_code)
        self.assertEqual(1, len(features.json()["rows"]))
        self.assertIsNone(features.json()["rows"][0]["return1"])
        self.assertEqual("causal-v2", features.json()["featureVersion"])
        from data_lake.analytics import build_cross_analysis
        with patch("data_lake.analytics.build_cross_analysis", wraps=build_cross_analysis) as analyze:
            response = self.request("/v1/cross-analysis",
                                    query=f"symbol=BTCUSDT&timeframe=15m&startMs={self.start}&endMs={closed}")
        self.assertEqual(200, response.status_code)
        self.assertTrue(response.json()["descriptiveOnly"])
        self.assertEqual(self.now, analyze.call_args.kwargs["as_of_ms"])
        self.assertEqual([row["snapshotId"] for row in snapshots[:2]],
                         [row["snapshotId"] for row in analyze.call_args.args[1]])
        self.assertEqual(closed + 60_000, response.json()["rows"][0]["analysisAtMs"])
        self.assertEqual(snapshots[1]["snapshotId"], response.json()["rows"][0]["snapshotId"])
        self.assertIsNone(response.json()["correlations"]["return1VsNetTakerQuote"]["value"])
        self.assertEqual(0, response.json()["correlations"]["return1VsNetTakerQuote"]["sampleCount"])
        with patch("data_lake.analytics.build_cross_analysis", wraps=build_cross_analysis) as analyze:
            pending = self.request("/v1/cross-analysis",
                                   query=f"symbol=BTCUSDT&timeframe=15m&startMs={self.start}&endMs={closed}&asOfMs={closed+15_000}")
        self.assertEqual([snapshots[0]["snapshotId"]], [row["snapshotId"] for row in analyze.call_args.args[1]])
        self.assertEqual("ANALYSIS_TIME_NOT_REACHED", pending.json()["rows"][0]["analysisReason"])
        with sqlite3.connect(self.database) as connection:
            connection.execute("UPDATE candles SET available_at_ms=?", (closed + 60_001,))
        late = self.request("/v1/cross-analysis",
                            query=f"symbol=BTCUSDT&timeframe=15m&startMs={self.start}&endMs={closed}")
        self.assertFalse(late.json()["rows"][0]["pointInTimeEligible"])
        self.assertEqual("FEATURE_NOT_AVAILABLE_AT_ANALYSIS_TIME", late.json()["rows"][0]["analysisReason"])


if __name__ == "__main__":
    unittest.main()
