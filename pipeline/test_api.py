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
        self.core_path = self.root / "core-signal.json"
        self.core_signal = {"schemaVersion": 1, "source": "STRATEGY_CORE", "exchange": "binance",
            "marketType": "USDT_PERPETUAL", "symbol": "BTCUSDT", "timeframe": "15m", "action": "LONG",
            "reason": "RSI_ADX_ENTRY", "strategyVersion": "rsi-adx-smart-dca-v1",
            "datasetVersion": "sha256:"+"c"*64, "inputSnapshotId": "sha256:"+"d"*64,
            "decisionAtMs": self.now-1000, "validUntilMs": self.now+20_000,
            "targetPositionBase": "0.001", "limitPrice": "100.02"}
        self.core_path.write_text(json.dumps(self.core_signal))
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
                       "FREQAI_REPORT_PATH": str(self.pred_path), "STRATEGY_CORE_REPORT_PATH": str(self.core_path),
                       "PAPER_MAX_DRAWDOWN_PCT":"95", "PAPER_MAX_DAILY_LOSS_USDT":"95",
                       "PAPER_MAX_EXPOSURE_USDT":"1000"}
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

    def test_core_and_ai_signals_are_independent_and_share_the_risk_gate(self):
        core_intent = {"intentId":"core-test-intent","symbol":"BTCUSDT","exchange":"binance",
            "marketType":"USDT_PERPETUAL","strategyVersion":"rsi-adx-smart-dca-v1",
            "modelVersion":"strategy-core","datasetVersion":"sha256:"+"c"*64,
            "targetPositionBase":"0.001","limitPrice":"100.02","decisionAtMs":self.now-1000,
            "validUntilMs":self.now+20_000,"inputSnapshotId":"sha256:"+"d"*64,"mode":"PAPER"}
        core = {"source":"STRATEGY_CORE","action":"BUY","reason":"RSI_ADX_ENTRY","intent":core_intent}
        with patch.object(api,"core_decide",return_value=core):
            code, signals = self.request("/v1/signals")
            self.assertEqual(code, 200)
            self.assertEqual(signals["strategyCore"]["action"], "BUY")
            self.assertEqual(signals["aiStrategy"]["action"], "BUY")
            self.assertEqual(signals["strategyCore"]["source"], "STRATEGY_CORE")
            self.assertEqual(signals["aiStrategy"]["source"], "AI_FREQAI")
            code, result = self.request("/v1/paper/evaluate", "POST", {"source": "CORE"})
        self.assertEqual(code, 200)
        self.assertEqual(result["decision"]["source"], "STRATEGY_CORE")
        self.assertEqual(result["order"]["status"], "FILLED")
        self.assertEqual(self.request("/v1/paper/evaluate", "POST", {"source": "UNKNOWN"})[0], 400)

    def test_equity_endpoint_persists_history_and_returns_drawdown_daily_metrics(self):
        code, result = self.request("/v1/equity")
        self.assertEqual(code,200)
        self.assertTrue(result["available"])
        self.assertEqual(result["initialCapital"],"100")
        self.assertEqual(result["latest"]["equity"],"100")
        self.assertEqual(result["dailyLossUsdt"],"0")
        with sqlite3.connect(self.db) as connection:
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM paper_equity_history").fetchone()[0],1)

    def test_audit_and_data_quality_endpoints_return_real_store_state(self):
        self.request("/v1/paper/pause","POST",{"paused":True})
        code, audit = self.request("/v1/audit",query="limit=10")
        self.assertEqual(code,200)
        self.assertEqual(audit["events"][0]["kind"],"PAUSE")
        code, quality = self.request("/v1/quality")
        self.assertEqual(code,200)
        self.assertEqual(quality["mode"],"PAPER")
        self.assertIs(quality["liveTradingSupported"], False)
        streams={stream["name"]:stream for stream in quality["streams"]}
        self.assertEqual(streams["M15 candles"]["status"],"DEGRADED")
        self.assertEqual(streams["H1 candles"]["status"],"DEGRADED")
        self.assertEqual(streams["Strategy Core producer"]["status"],"DEGRADED")
        self.assertEqual(streams["Shared Risk Limits"]["status"],"READY")
        self.assertEqual(streams["Shared Risk Limits"]["maxDrawdownPct"],"95")

    def test_risk_limit_breach_auto_kills_new_paper_intents(self):
        self.request("/v1/equity")
        with sqlite3.connect(self.db) as connection:
            connection.execute("UPDATE paper_state SET realized='-25' WHERE id=1")
        with patch.dict(os.environ,{"PAPER_MAX_DRAWDOWN_PCT":"20","PAPER_MAX_DAILY_LOSS_USDT":"10","PAPER_MAX_EXPOSURE_USDT":"1000"}):
            code, result = self.request("/v1/paper/evaluate","POST",{})
        self.assertEqual(code,200)
        self.assertEqual(result["order"]["reason"],"MAX_DRAWDOWN_LIMIT")
        self.assertTrue(self.request("/v1/paper")[1]["riskControl"]["killed"])

    def test_unconfigured_risk_limits_fail_closed(self):
        with patch.dict(os.environ,{"PAPER_MAX_DRAWDOWN_PCT":"","PAPER_MAX_DAILY_LOSS_USDT":"","PAPER_MAX_EXPOSURE_USDT":""}):
            _, result = self.request("/v1/paper/evaluate","POST",{})
        self.assertEqual(result["order"]["reason"],"RISK_LIMITS_UNCONFIGURED")

    def test_core_producer_waits_on_incomplete_history_without_suppressing_ai(self):
        _, signals = self.request("/v1/signals")
        self.assertEqual(signals["strategyCore"]["action"], "WAIT")
        self.assertEqual(signals["strategyCore"]["reason"], "CORE_CANDLE_WINDOW_INCOMPLETE")
        self.assertEqual(signals["aiStrategy"]["action"], "BUY")

    def test_api_kill_switch_requires_control_token_and_blocks_paper_evaluation(self):
        self.assertEqual(self.request("/v1/paper/kill", "POST", {"enabled": True}, token="read-token")[0], 401)
        code, state = self.request("/v1/paper/kill", "POST", {"enabled": True})
        self.assertEqual(code, 200)
        self.assertTrue(state["riskControl"]["killed"])
        _, result = self.request("/v1/paper/evaluate", "POST", {})
        self.assertEqual(result["order"]["status"], "REJECTED")
        self.assertEqual(result["order"]["reason"], "KILL_SWITCH")
        self.assertEqual(self.request("/v1/paper/reset-kill", "POST",
                                      {"acknowledge": True})[0], 200)
        # A rejected intent remains idempotently rejected. A fresh prediction
        # timestamp creates a new signal identity after the operator reset.
        self.prediction["availableAtMs"] = self.now-500
        self.pred_path.write_text(json.dumps(self.prediction))
        _, result = self.request("/v1/paper/evaluate", "POST", {})
        self.assertEqual(result["order"]["status"], "FILLED")

    def test_kill_reset_requires_server_side_readiness(self):
        self.request("/v1/paper/kill", "POST", {"enabled": True})
        with patch.object(api, "book_snapshot", return_value=None):
            code, result = self.request("/v1/paper/reset-kill", "POST", {"acknowledge": True})
        self.assertEqual(code, 409)
        self.assertEqual(result["error"], "SYSTEM_NOT_READY")
        self.assertTrue(self.request("/v1/paper")[1]["riskControl"]["killed"])

    def test_kill_switch_cannot_be_cleared_by_generic_resume_or_malformed_reset(self):
        self.request("/v1/paper/kill", "POST", {"enabled": True})
        self.request("/v1/paper/pause", "POST", {"paused": False})
        _, result = self.request("/v1/paper/evaluate", "POST", {})
        self.assertEqual(result["order"]["reason"], "KILL_SWITCH")
        self.assertEqual(self.request("/v1/paper/reset-kill", "POST",
                                      {"acknowledge": True, "ready": False})[0], 400)


    def test_market_data_reads_follow_factory_while_paper_ledger_stays_sqlite(self):
        calls = []

        class SelectedStore:
            def read_window(self, symbol, timeframe, start_ms, end_ms, as_of_ms=None):
                calls.append((symbol, timeframe, start_ms, end_ms, as_of_ms))
                return {
                    "candles": [],
                    "coverage": {"complete": False, "expected": 1, "returned": 0, "gaps": []},
                    "datasetVersion": "sha256:" + "e" * 64,
                }

        selected_store = SelectedStore()
        with patch.object(api, "create_store_from_env", return_value=selected_store):
            query = (f"symbol=BTCUSDT&timeframe=15m&startMs={self.end-1_800_000}"
                     f"&endMs={self.end}")
            code, _ = self.request("/v1/candles", query=query)
            self.assertEqual(code, 200)

            code, quality = self.request("/v1/quality")
            self.assertEqual(code, 200)
            self.assertEqual(quality["mode"], "PAPER")

            timeframes = {call[1] for call in calls}
            self.assertIn("15m", timeframes)
            self.assertIn("1h", timeframes)

            api.ledger()
            before_paper_read = len(calls)
            code, paper = self.request("/v1/paper")
            self.assertEqual(code, 200)
            self.assertFalse(paper["liveTradingSupported"])
            self.assertEqual(len(calls), before_paper_read)


if __name__ == "__main__":
    unittest.main()
