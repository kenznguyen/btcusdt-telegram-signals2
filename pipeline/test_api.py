import csv
from datetime import datetime, timezone
import io
import json
import os
import sqlite3
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from futures_intelligence.import_collector import build_snapshot
from market_data.store import Candle, CandleStore, read_window
from pipeline import api


class FiveLayerApiTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.end = 1_800_001_800_000
        self.now = self.end + 5000
        self.db = self.root / "system.sqlite3"
        CandleStore(self.db).insert([
            Candle("15m", self.end-1_800_000, "100", "102", "99", "101", "3", self.end-899_000),
            Candle("15m", self.end-900_000, "101", "102", "99", "100", "2", self.end+1000)])
        self.window = read_window(self.db, "BTCUSDT", "15m", self.end-1_800_000, self.end)
        trade_path = self.root / "trades.csv"
        headers = "exchange,market,datatype,timestamp_ms,datetime_utc,symbol,trade_id,side,price,quantity,is_buyer_maker,first_update_id,last_update_id".split(",")
        with trade_path.open("w", newline="") as output:
            writer = csv.writer(output)
            writer.writerow(headers)
            for offset, trade_id, side, qty, maker in ((297000, 42, "buy", "2", 0), (298000, 43, "sell", "1", 1)):
                instant = self.now-300_000+offset
                utc = datetime.fromtimestamp(instant/1000, timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")
                writer.writerow(["binance", "futures", "trades", instant, utc, "btcusdt", trade_id, side, "100", qty, maker, 100, 101])
        intelligence = build_snapshot(self.now-300_000, self.now-1000, self.now-500, trades=trade_path)
        self.intel_path = self.root / "intelligence.json"
        self.intel_path.write_text(json.dumps(intelligence))
        self.pred_path = self.root / "prediction.json"
        self.prediction = {"schemaVersion": 1, "exchange": "binance", "marketType": "USDT_PERPETUAL",
            "symbol": "BTCUSDT", "timeframe": "15m", "candleOpenTimeMs": self.end-900_000,
            "candleCloseTimeMs": self.end, "availableAtMs": self.end+3000, "trainedThroughMs": self.end-900_000,
            "modelVersion": "fixture-model", "strategyVersion": "fixture-strategy", "predictedReturn": "0.004",
            "doPredict": 1, "datasetVersion": self.window["datasetVersion"],
            "trainingCompletedAtMs": self.end-900_000, "trainingDatasetVersion": "sha256:"+"a"*64}
        self.pred_path.write_text(json.dumps(self.prediction))
        self.book = {"source": "hummingbot", "connector": "binance_perpetual", "symbol": "BTCUSDT",
                     "observedAtMs": self.now-100, "bids": [{"price": "100", "quantity": "1"}],
                     "asks": [{"price": "100.02", "quantity": "1"}]}
        self.config = {"MARKET_DATA_DB": str(self.db), "MARKET_DATA_TOKEN": "read-token",
                       "CONTROL_TOKEN": "paper-control-token", "INTELLIGENCE_REPORT_PATH": str(self.intel_path),
                       "FREQAI_REPORT_PATH": str(self.pred_path)}
        self.env = patch.dict(os.environ, self.config, clear=True)
        self.env.start()
        self.addCleanup(self.env.stop)
        self.clock = patch.object(api, "now_ms", return_value=self.now)
        self.clock.start()
        self.addCleanup(self.clock.stop)
        self.books = patch.object(api, "book_snapshot", return_value=self.book)
        self.books.start()
        self.addCleanup(self.books.stop)

    def request(self, path, method="GET", body=None, token=None, query=""):
        raw = b"" if body is None else json.dumps(body).encode()
        token = token if token is not None else "paper-control-token" if method == "POST" else "read-token"
        env = {"PATH_INFO": path, "REQUEST_METHOD": method, "QUERY_STRING": query,
               "HTTP_AUTHORIZATION": "Bearer "+token, "CONTENT_LENGTH": str(len(raw)), "wsgi.input": io.BytesIO(raw)}
        statuses = []
        data = b"".join(api.application(env, lambda status, headers: statuses.append((status, headers))))
        status, headers = statuses[0]
        self.assertIn(("X-Content-Type-Options", "nosniff"), headers)
        return int(status.split()[0]), json.loads(data)

    def test_collector_to_canonical_prediction_to_paper_and_read_api(self):
        code, intelligence = self.request("/v1/intelligence")
        self.assertEqual(code, 200)
        self.assertEqual(intelligence["netTakerQuote"], "100")
        code, result = self.request("/v1/paper/evaluate", "POST", {})
        self.assertEqual(code, 200)
        self.assertEqual(result["decision"]["action"], "BUY")
        self.assertEqual(result["order"]["status"], "FILLED")
        self.assertEqual(result["order"]["filledBase"], "0.001")
        _, state = self.request("/v1/paper")
        self.assertEqual(state["positionBase"], "0.001")
        self.assertFalse(state["liveTradingSupported"])
        self.assertGreater(float(state["feesQuote"]), 0)

    def test_shared_candle_source_is_separate_from_local_paper_state(self):
        shared = self.root / "lake.sqlite3"
        CandleStore(shared).insert([Candle("15m", self.end-900_000, "200", "202", "199", "201", "4", self.end+1000)])
        os.environ["DATA_LAKE_DATABASE_URL"] = str(shared)
        query = f"symbol=BTCUSDT&timeframe=15m&startMs={self.end-900_000}&endMs={self.end}"
        code, window = self.request("/v1/candles", query=query)
        self.assertEqual(code, 200)
        self.assertEqual(window["candles"][0]["close"], "201")
        code, state = self.request("/v1/paper/pause", "POST", {"paused": True})
        self.assertEqual(code, 200)
        self.assertTrue(state["paused"])
        with sqlite3.connect(shared) as connection:
            tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        self.assertEqual(tables, {"candles"})
        with sqlite3.connect(self.db) as connection:
            self.assertEqual(connection.execute("SELECT paused FROM paper_state WHERE id=1").fetchone()[0], 1)

    def test_retries_do_not_duplicate_positions_or_fees(self):
        _, first = self.request("/v1/paper/evaluate", "POST", {})
        _, before = self.request("/v1/paper")
        _, retry = self.request("/v1/paper/evaluate", "POST", {})
        _, after = self.request("/v1/paper")
        self.assertEqual(first["order"], retry["order"])
        self.assertEqual(before, after)

    def test_no_prediction_is_wait_with_no_order(self):
        self.pred_path.unlink()
        code, result = self.request("/v1/paper/evaluate", "POST", {})
        self.assertEqual(code, 200)
        self.assertEqual(result["decision"]["action"], "WAIT")
        self.assertEqual(result["decision"]["reason"], "PREDICTION_UNAVAILABLE")
        self.assertIsNone(result["order"])

    def test_pause_is_persistent_and_distinct_auth_is_required(self):
        self.assertEqual(self.request("/v1/paper/pause", "POST", {"paused": True}, token="read-token")[0], 401)
        code, result = self.request("/v1/paper/pause", "POST", {"paused": True})
        self.assertEqual(code, 200)
        self.assertTrue(result["paused"])
        _, result = self.request("/v1/paper/evaluate", "POST", {})
        self.assertEqual(result["order"]["status"], "REJECTED")
        self.assertEqual(result["order"]["reason"], "PAUSED")
        self.assertEqual(self.request("/v1/paper")[1]["positionBase"], "0")

    def test_controls_never_accept_user_provided_predictions_or_books(self):
        for body in ({"prediction": self.prediction}, {"book": self.book}, {"mode": "LIVE"}):
            with self.subTest(body=body):
                self.assertEqual(self.request("/v1/paper/evaluate", "POST", body)[0], 400)
        self.assertEqual(self.request("/v1/paper/pause", "POST", {"paused": "true"})[0], 400)
        self.assertEqual(self.request("/v1/paper", token="bad")[0], 401)
        self.assertEqual(self.request("/v1/orders", "POST", {})[0], 404)
        with patch.dict(os.environ, {"CONTROL_TOKEN": "read-token"}):
            self.assertEqual(self.request("/v1/paper/pause", "POST", {"paused": True}, token="read-token")[0], 503)

    def test_corrupt_artifacts_and_stale_model_do_not_generate_orders(self):
        self.prediction["availableAtMs"] = self.now-31_000
        self.pred_path.write_text(json.dumps(self.prediction))
        _, result = self.request("/v1/paper/evaluate", "POST", {})
        self.assertEqual(result["decision"]["action"], "WAIT")
        self.assertIsNone(result["order"])
        snapshot = json.loads(self.intel_path.read_text())
        snapshot["netTakerQuote"] = "99999"
        self.intel_path.write_text(json.dumps(snapshot))
        self.assertEqual(self.request("/v1/intelligence")[0], 503)
        self.assertEqual(self.request("/v1/decision")[1]["action"], "WAIT")

    def test_system_and_apk_book_contract_are_explicit_paper(self):
        code, system = self.request("/v1/system")
        self.assertEqual(code, 200)
        self.assertEqual(len(system["layers"]), 5)
        self.assertEqual(system["mode"], "PAPER")
        code, book = self.request("/v1/order-book", query="symbol=BTCUSDT")
        self.assertEqual(code, 200)
        self.assertEqual(book, self.book)
        self.assertEqual(self.request("/v1/order-book", query="symbol=ETHUSDT")[0], 400)

    def test_static_files_cannot_escape_build_directory(self):
        dist = self.root / "dist"
        dist.mkdir()
        (self.root / "secret.txt").write_text("not-public")
        with patch.dict(os.environ, {"CONTROL_DIST_PATH": str(dist)}):
            (dist / "private.json").write_text('{"secret":"not-public"}')
            self.assertEqual(self.request("/control/../secret.txt")[0], 404)
            self.assertEqual(self.request("/control/%2e%2e/secret.txt")[0], 404)
            self.assertEqual(self.request("/control/private.json")[0], 404)
            self.assertEqual(self.request("/control")[0], 404)
        with patch.dict(os.environ, {"CONTROL_DIST_PATH": ""}):
            self.assertEqual(api.control_root(), (api.ROOT / "control_dashboard/dist").resolve())

    def test_write_budget_is_shared_in_sqlite_and_resets_next_minute(self):
        for _ in range(30):
            self.assertTrue(api.control_permit(self.now))
        self.assertFalse(api.control_permit(self.now))
        self.assertEqual(self.request("/v1/paper/pause", "POST", {"paused": True})[0], 429)
        self.assertTrue(api.control_permit(self.now+60_000))

    def test_missing_store_does_not_create_a_fake_fresh_paper_account_on_write(self):
        path = self.root / "missing.sqlite3"
        with patch.dict(os.environ, {"MARKET_DATA_DB": str(path)}):
            self.assertEqual(self.request("/v1/paper/evaluate", "POST", {})[0], 503)
            self.assertFalse(path.exists())

    def test_read_only_paper_does_not_create_missing_or_uninitialized_account(self):
        self.assertEqual(self.request("/v1/paper")[0], 503)
        with patch.dict(os.environ, {"MARKET_DATA_DB": str(self.root / "absent.sqlite3")}):
            self.assertEqual(self.request("/v1/paper")[0], 503)
            self.assertFalse((self.root / "absent.sqlite3").exists())

    def test_empty_intelligence_snapshot_does_not_become_ready(self):
        missing = build_snapshot(self.now-300_000, self.now-1000, self.now-500)
        self.intel_path.write_text(json.dumps(missing))
        _, system = self.request("/v1/system")
        self.assertEqual(system["layers"][1]["status"], "WAIT")

    def test_corrupt_stored_candles_and_paper_state_are_service_errors(self):
        self.request("/v1/paper/pause", "POST", {"paused": False})
        with sqlite3.connect(self.db) as connection:
            connection.execute("UPDATE paper_state SET position='NaN'")
        self.assertEqual(self.request("/v1/paper")[0], 503)
        with sqlite3.connect(self.db) as connection:
            connection.execute("UPDATE candles SET high='0'")
        query = f"symbol=BTCUSDT&timeframe=15m&startMs={self.end-1_800_000}&endMs={self.end}"
        self.assertEqual(self.request("/v1/candles", query=query)[0], 503)


if __name__ == "__main__":
    unittest.main()
