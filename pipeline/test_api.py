import csv
from datetime import datetime, timezone
import io
import json
import multiprocessing
import os
import socket
import sqlite3
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from futures_intelligence.import_collector import build_snapshot
from market_data.store import Candle, CandleStore, read_window
from market_data.test_support import seed_candles
from pipeline import api
from paper_execution import kill_reset_service


def _run_kill_reset_service_for_test(socket_path, key_path, control_token, ready_event):
    kill_reset_service.KILL_RESET_SIGNING_KEY_PATH = Path(key_path)
    os.environ["KILL_RESET_CONTROL_TOKEN"] = control_token
    kill_reset_service._serve_socket(
        socket_path, control_token, os.geteuid(), ready_event=ready_event
    )


class FixtureT0CandleHttpClient:
    db_path = None
    calls = []

    def __init__(self, config):
        self.config = config

    def fetch(self, *, start_ms, end_ms, as_of_ms, timeframe):
        from freqai_bridge.http_candles import CandleHttpError
        type(self).calls.append((timeframe, start_ms, end_ms, as_of_ms))
        try:
            return read_window(
                type(self).db_path, "BTCUSDT", timeframe, start_ms, end_ms, as_of_ms,
            )
        except (ValueError, OSError, sqlite3.Error):
            raise CandleHttpError("CANDLE_INVALID") from None


class FiveLayerApiTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.end = 1_800_001_800_000
        self.now = self.end + 5000
        self.db = self.root / "market-data.sqlite3"
        self.paper_db = self.root / "paper.sqlite3"
        self.paper_db.touch()
        self.signing_key_path = self.root / "kill-reset-signing.key"
        self.signing_key_path.write_bytes(b"test-only-kill-reset-signing-key-32-bytes")
        self.signing_key_path.chmod(0o600)
        self.signing_key_patch = patch.object(
            kill_reset_service, "KILL_RESET_SIGNING_KEY_PATH",
            self.root / "missing-service-signing-key",
        )
        self.signing_key_patch.start()
        self.addCleanup(self.signing_key_patch.stop)
        self.control_socket = self.root / "kill-reset-control.sock"
        self.control_token = "test-control-token-" + "x" * 48
        CandleStore(self.db)
        seed_candles(self.db, [
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
        FixtureT0CandleHttpClient.db_path = self.db
        FixtureT0CandleHttpClient.calls.clear()
        self.t0_http_client = patch(
            "freqai_bridge.http_candles.CandleHttpClient", FixtureT0CandleHttpClient,
        )
        self.t0_http_client.start()
        self.addCleanup(self.t0_http_client.stop)
        self.config = {"MARKET_DATA_DB": str(self.db), "PAPER_DB": str(self.paper_db),
                       "T0_CANDLE_API_BASE_URL": "https://t0.test.invalid",
                       "T0_CANDLE_API_TOKEN": "read-only-test-token",
                       "T0_CANDLE_MAX_LAG_MS": "120000", "MARKET_DATA_TOKEN": "read-token",
                       "CONTROL_TOKEN": "paper-control-token",
                       "KILL_RESET_CONTROL_SOCKET": str(self.control_socket),
                       "KILL_RESET_CONTROL_TOKEN": self.control_token,
                       "INTELLIGENCE_REPORT_PATH": str(self.intel_path),
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

    def test_kill_reset_signing_key_loader_rejects_path_swap_to_symlink(self):
        key_path = self.root / "race-signing.key"
        target_path = self.root / "attacker-signing.key"
        key_path.write_bytes(b"trusted-signing-key-material-32-bytes")
        target_path.write_bytes(b"attacker-signing-key-material-32-bytes")
        key_path.chmod(0o600)
        target_path.chmod(0o600)
        real_open = os.open

        def replace_path_before_open(path, flags, *args, **kwargs):
            Path(path).unlink()
            Path(path).symlink_to(target_path)
            return real_open(path, flags, *args, **kwargs)

        with patch.object(
            kill_reset_service, "KILL_RESET_SIGNING_KEY_PATH", key_path
        ), patch.object(
            kill_reset_service.os, "open", side_effect=replace_path_before_open
        ):
            with self.assertRaisesRegex(
                ValueError, "KILL_RESET_SIGNING_KEY_UNAVAILABLE"
            ):
                kill_reset_service._load_signing_key()

    def test_kill_reset_signing_key_loader_rejects_existing_symlink(self):
        target_path = self.root / "target-signing.key"
        link_path = self.root / "linked-signing.key"
        target_path.write_bytes(b"attacker-signing-key-material-32-bytes")
        target_path.chmod(0o600)
        link_path.symlink_to(target_path)
        with patch.object(
            kill_reset_service, "KILL_RESET_SIGNING_KEY_PATH", link_path
        ):
            with self.assertRaisesRegex(
                ValueError, "KILL_RESET_SIGNING_KEY_UNAVAILABLE"
            ):
                kill_reset_service._load_signing_key()

    def test_kill_reset_signing_key_loader_rejects_group_readable_file(self):
        key_path = self.root / "group-readable-signing.key"
        key_path.write_bytes(b"test-only-kill-reset-signing-key-32-bytes")
        key_path.chmod(0o640)
        with patch.object(
            kill_reset_service, "KILL_RESET_SIGNING_KEY_PATH", key_path
        ):
            with self.assertRaisesRegex(
                ValueError, "KILL_RESET_SIGNING_KEY_PERMISSIONS_INVALID"
            ):
                kill_reset_service._load_signing_key()

    def test_kill_reset_control_service_rejects_untrusted_peer_uid(self):
        service_socket, client_socket = socket.socketpair()
        self.addCleanup(service_socket.close)
        self.addCleanup(client_socket.close)

        class UnauthorizedPeerServer:
            allowed_api_uid = os.geteuid() + 1
            control_token = self.control_token

        client_socket.sendall(json.dumps({
            "acknowledge": True, "token": self.control_token,
        }).encode("utf-8") + b"\\n")
        client_socket.shutdown(socket.SHUT_WR)
        kill_reset_service._KillResetHandler(
            service_socket, ("local", 0), UnauthorizedPeerServer()
        )
        response = json.loads(client_socket.recv(4096))
        self.assertEqual(response["status"], 401)
        self.assertEqual(response["body"]["error"], "CONTROL_SERVICE_UNAUTHORIZED")

    def start_kill_reset_service(self):
        ready = multiprocessing.Event()
        process = multiprocessing.Process(
            target=_run_kill_reset_service_for_test,
            args=(str(self.control_socket), str(self.signing_key_path),
                  self.control_token, ready),
            daemon=True,
        )
        process.start()
        self.addCleanup(process.join, 5)
        self.addCleanup(process.terminate)
        if not ready.wait(5):
            process.terminate()
            process.join(5)
            self.fail("isolated Kill Reset Control Service did not start")
        return process

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

    def valid_ai_decision(self):
        """Isolate paper risk/ledger tests from the unavailable production admission provider."""
        return {"source": "AI_FREQAI", "action": "BUY", "reason": "ALIGNED_PAPER_SIGNAL",
                "intent": {
                    "intentId": f"api-test-ai-{self.prediction['availableAtMs']}",
                    "symbol": "BTCUSDT", "exchange": "binance",
                    "marketType": "USDT_PERPETUAL", "strategyVersion": "fixture-strategy",
                    "modelVersion": "fixture-model", "datasetVersion": self.window["datasetVersion"],
                    "targetPositionBase": "0.001", "limitPrice": "100.02",
                    "decisionAtMs": self.now-1000, "validUntilMs": self.now+20_000,
                    "inputSnapshotId": "sha256:"+"d"*64, "mode": "PAPER",
                }}

    def test_missing_trusted_calibration_context_blocks_ai_paper_execution(self):
        code, intelligence = self.request("/v1/intelligence")
        self.assertEqual(code, 200, intelligence)
        self.assertEqual(intelligence["netTakerQuote"], "100")
        self.assertEqual(intelligence["collectorCommit"], "bc4f0ef633fbeee4a49defd72827f17162693805")
        self.assertEqual(len(intelligence["inputFiles"]["trades"][0]["sha256"]), 64)
        code, result = self.request("/v1/paper/evaluate", "POST", {})
        self.assertEqual(code, 200, result)
        self.assertEqual(result["decision"]["action"], "WAIT")
        self.assertEqual(result["decision"]["reason"], "AI_CALIBRATION_ADMISSION_CONTEXT_UNAVAILABLE")
        self.assertIsNone(result["decision"]["intent"])
        self.assertIsNone(result["order"])
        _, state = self.request("/v1/paper")
        self.assertEqual(state["positionBase"], "0")
        self.assertFalse(state["liveTradingSupported"])
        self.assertEqual(float(state["feesQuote"]), 0)

    def test_retries_do_not_duplicate_positions_or_fees(self):
        with patch.object(api, "decide", return_value=self.valid_ai_decision()):
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
        with patch.object(api, "decide", return_value=self.valid_ai_decision()):
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
        self.paper_db.touch(exist_ok=True)
        for _ in range(30):
            self.assertTrue(api.control_permit(self.now))
        self.assertFalse(api.control_permit(self.now))
        self.assertEqual(self.request("/v1/paper/pause", "POST", {"paused": True})[0], 429)
        self.assertTrue(api.control_permit(self.now+60_000))

    def test_missing_t0_http_config_does_not_create_a_fake_fresh_paper_account_on_write(self):
        with patch.dict(os.environ, {"T0_CANDLE_API_BASE_URL": ""}):
            self.assertEqual(self.request("/v1/paper/evaluate", "POST", {})[0], 503)

    def test_read_only_paper_does_not_create_missing_or_uninitialized_account(self):
        self.paper_db.unlink(missing_ok=True)
        self.assertEqual(self.request("/v1/paper")[0], 503)
        missing_paper = self.root / "absent-paper.sqlite3"
        with patch.dict(os.environ, {"PAPER_DB": str(missing_paper)}):
            self.assertEqual(self.request("/v1/paper")[0], 503)
            self.assertFalse(missing_paper.exists())

    def test_empty_intelligence_snapshot_does_not_become_ready(self):
        missing = build_snapshot(self.now-300_000, self.now-1000, self.now-500)
        self.intel_path.write_text(json.dumps(missing))
        _, system = self.request("/v1/system")
        self.assertEqual(system["layers"][1]["status"], "WAIT")

    def test_corrupt_stored_candles_and_paper_state_are_service_errors(self):
        self.request("/v1/paper/pause", "POST", {"paused": False})
        with sqlite3.connect(self.paper_db) as connection:
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
        core_order = {"status": "FILLED", "orderId": "core-test-order"}
        with patch.object(api, "core_runtime_preview", return_value=core), \
             patch.object(api, "core_runtime_evaluate", return_value={"decision": core, "order": core_order}):
            code, signals = self.request("/v1/signals")
            self.assertEqual(code, 200)
            self.assertEqual(signals["strategyCore"]["action"], "BUY")
            self.assertEqual(signals["aiStrategy"]["action"], "WAIT")
            self.assertEqual(signals["aiStrategy"]["reason"], "AI_CALIBRATION_ADMISSION_CONTEXT_UNAVAILABLE")
            self.assertIsNone(signals["aiStrategy"]["intent"])
            self.assertEqual(signals["strategyCore"]["source"], "STRATEGY_CORE")
            self.assertEqual(signals["aiStrategy"]["source"], "AI_FREQAI")
            code, result = self.request("/v1/paper/evaluate", "POST", {"source": "CORE"})
        self.assertEqual(code, 200, result)
        self.assertEqual(result["decision"]["source"], "STRATEGY_CORE")
        self.assertEqual(result["order"]["status"], "FILLED")
        self.assertEqual(self.request("/v1/paper/evaluate", "POST", {"source": "UNKNOWN"})[0], 400)

    def test_equity_endpoint_persists_history_and_returns_drawdown_daily_metrics(self):
        code, result = self.request("/v1/equity")
        self.assertEqual(code,200, result)
        self.assertTrue(result["available"])
        self.assertEqual(result["initialCapital"],"100")
        self.assertEqual(result["latest"]["equity"],"100")
        self.assertEqual(result["dailyLossUsdt"],"0")
        with sqlite3.connect(self.paper_db) as connection:
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM paper_equity_history").fetchone()[0],1)
            self.assertIsNone(connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='paper_schema_migrations'"
            ).fetchone())

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

    def test_quality_reports_feed_level_freshness_provenance_and_unknown_continuity(self):
        code, quality = self.request("/v1/quality")
        self.assertEqual(code, 200)
        intelligence = next(row for row in quality["streams"] if row["name"] == "Futures Intelligence")
        feeds = {row["name"]: row for row in intelligence["feeds"]}
        self.assertEqual(feeds["trades"]["freshness"], "FRESH")
        self.assertEqual(feeds["trades"]["continuityStatus"], "UNVERIFIED")
        self.assertEqual(feeds["trades"]["connectionStatus"], "UNVERIFIABLE")
        self.assertEqual(feeds["trades"]["integrityStatus"], "OK")
        self.assertEqual(feeds["trades"]["duplicateRows"], 0)
        self.assertGreaterEqual(feeds["trades"]["ageMs"], 0)
        self.assertEqual(feeds["funding"]["freshness"], "MISSING")
        self.assertEqual(feeds["openInterest"]["freshness"], "MISSING")
        self.assertEqual(feeds["liquidations"]["freshness"], "MISSING")
        self.assertEqual(intelligence["collectorCommit"], "bc4f0ef633fbeee4a49defd72827f17162693805")
        self.assertGreater(intelligence["inputFileCount"], 0)

    def test_quality_marks_old_trade_capture_stale_without_refreshing_it(self):
        trade_path = self.root / "old-trades.csv"
        headers = "exchange,market,datatype,timestamp_ms,datetime_utc,symbol,trade_id,side,price,quantity,is_buyer_maker,first_update_id,last_update_id".split(",")
        with trade_path.open("w", newline="") as output:
            writer = csv.writer(output)
            writer.writerow(headers)
            instant = self.now-180_000
            utc = datetime.fromtimestamp(instant/1000, timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")
            writer.writerow(["binance", "futures", "trades", instant, utc, "btcusdt", 99, "buy", "100", "1", 0, 99, 99])
        old = build_snapshot(self.now-300_000, self.now-120_000, self.now-100_000, trades=trade_path)
        self.intel_path.write_text(json.dumps(old))
        _, quality = self.request("/v1/quality")
        intelligence = next(row for row in quality["streams"] if row["name"] == "Futures Intelligence")
        trades = next(row for row in intelligence["feeds"] if row["name"] == "trades")
        self.assertEqual(trades["freshness"], "STALE")
        self.assertEqual(intelligence["status"], "DEGRADED")

    def test_risk_limit_breach_auto_kills_new_paper_intents(self):
        self.request("/v1/equity")
        with sqlite3.connect(self.paper_db) as connection:
            connection.execute("UPDATE paper_state SET realized='-25' WHERE id=1")
        with patch.dict(os.environ,{"PAPER_MAX_DRAWDOWN_PCT":"20","PAPER_MAX_DAILY_LOSS_USDT":"10","PAPER_MAX_EXPOSURE_USDT":"1000"}):
            with patch.object(api, "decide", return_value=self.valid_ai_decision()):
                code, result = self.request("/v1/paper/evaluate","POST",{})
        self.assertEqual(code,200)
        self.assertEqual(result["order"]["reason"],"MAX_DRAWDOWN_LIMIT")
        self.assertTrue(self.request("/v1/paper")[1]["riskControl"]["killed"])

    def test_unconfigured_risk_limits_fail_closed(self):
        with patch.dict(os.environ,{"PAPER_MAX_DRAWDOWN_PCT":"","PAPER_MAX_DAILY_LOSS_USDT":"","PAPER_MAX_EXPOSURE_USDT":""}):
            with patch.object(api, "decide", return_value=self.valid_ai_decision()):
                _, result = self.request("/v1/paper/evaluate","POST",{})
        self.assertEqual(result["order"]["reason"],"RISK_LIMITS_UNCONFIGURED")

    def test_core_producer_waits_on_incomplete_history_without_suppressing_ai(self):
        preview = {"source": "STRATEGY_CORE", "action": "WAIT",
                   "reason": "CORE_CANDLE_WINDOW_INCOMPLETE", "indicators": None}
        with patch.object(api, "core_runtime_preview", return_value=preview):
            _, signals = self.request("/v1/signals")
        self.assertEqual(signals["strategyCore"]["action"], "WAIT")
        self.assertEqual(signals["strategyCore"]["reason"], "CORE_CANDLE_WINDOW_INCOMPLETE")
        self.assertEqual(signals["aiStrategy"]["action"], "WAIT")
        self.assertEqual(signals["aiStrategy"]["reason"], "AI_CALIBRATION_ADMISSION_CONTEXT_UNAVAILABLE")
        self.assertIsNone(signals["aiStrategy"]["intent"])

    def test_api_kill_switch_requires_control_token_and_blocks_paper_evaluation(self):
        self.assertEqual(self.request("/v1/paper/kill", "POST", {"enabled": True}, token="read-token")[0], 401)
        code, state = self.request("/v1/paper/kill", "POST", {"enabled": True})
        self.assertEqual(code, 200)
        self.assertTrue(state["riskControl"]["killed"])
        with patch.object(api, "decide", return_value=self.valid_ai_decision()):
            _, result = self.request("/v1/paper/evaluate", "POST", {})
        self.assertEqual(result["order"]["status"], "REJECTED")
        self.assertEqual(result["order"]["reason"], "KILL_SWITCH")
        self.start_kill_reset_service()
        self.assertEqual(self.request("/v1/paper/reset-kill", "POST",
                                      {"acknowledge": True})[0], 200)
        # A rejected intent remains idempotently rejected. A fresh prediction
        # timestamp creates a new signal identity after the operator reset.
        self.prediction["availableAtMs"] = self.now-500
        self.pred_path.write_text(json.dumps(self.prediction))
        with patch.object(api, "decide", return_value=self.valid_ai_decision()):
            _, result = self.request("/v1/paper/evaluate", "POST", {})
        self.assertEqual(result["order"]["status"], "FILLED")

    def test_kill_reset_rejects_stale_or_unissued_readiness_capability(self):
        self.request("/v1/paper/kill", "POST", {"enabled": True})
        checks = {
            "closedCandles": True, "orderBook": True,
            "noPendingPaperOrders": True, "accountRiskReady": True,
        }
        stale = {
            "ready": True, "checks": checks,
            "evidence": {"token": "x"*43, "checkedAtMs": self.now-6_000},
        }
        with patch.object(api, "control_readiness", return_value=stale):
            self.start_kill_reset_service()
            code, result = self.request("/v1/paper/reset-kill", "POST", {"acknowledge": True})
        self.assertEqual(code, 409)
        self.assertEqual(result["error"], "SYSTEM_NOT_READY")
        self.assertTrue(self.request("/v1/paper")[1]["riskControl"]["killed"])

    def test_production_control_service_requires_a_distinct_non_root_api_user(self):
        with patch.object(
            kill_reset_service, "KILL_RESET_SIGNING_KEY_PATH", self.signing_key_path
        ), patch.dict(os.environ, {
            "KILL_RESET_CONTROL_TOKEN": self.control_token,
            "KILL_RESET_CONTROL_SOCKET": str(self.control_socket),
            "KILL_RESET_API_UID": str(os.geteuid()),
        }, clear=True):
            with self.assertRaisesRegex(RuntimeError, "different non-root OS users"):
                kill_reset_service.serve()

    def test_kill_reset_fails_closed_when_isolated_service_is_unavailable(self):
        self.request("/v1/paper/kill", "POST", {"enabled": True})
        socket_path = str(self.root / "missing-kill-reset-control.sock")
        with patch.dict(os.environ, {"KILL_RESET_CONTROL_SOCKET": socket_path}):
            code, result = self.request(
                "/v1/paper/reset-kill", "POST", {"acknowledge": True}
            )
        self.assertEqual(code, 503)
        self.assertEqual(result["error"], "KILL_RESET_CONTROL_UNAVAILABLE")
        self.assertTrue(self.request("/v1/paper")[1]["riskControl"]["killed"])

    def test_arbitrary_api_process_cannot_mint_fabricated_reset_evidence(self):
        self.request("/v1/paper/kill", "POST", {"enabled": True})
        with self.assertRaisesRegex(ValueError, "KILL_RESET_SIGNING_KEY_UNAVAILABLE"):
            kill_reset_service._issue_kill_reset_evidence(
                checked_at_ms=self.now,
                checks={"closedCandles": True, "orderBook": True,
                        "noPendingPaperOrders": True, "accountRiskReady": True},
                candle_evidence={"datasetVersion": "sha256:"+"a"*64,
                                 "closeTimeMs": self.now-900_000,
                                 "availableAtMs": self.now-1_000},
                book_evidence={"snapshotDigest": "sha256:"+"b"*64,
                               "observedAtMs": self.now-100},
            )
        forged = {"token": "x"*43, "checkedAtMs": self.now, "signature": "0"*64}
        with self.assertRaisesRegex(ValueError, "server-issued readiness evidence"):
            api.ledger().reset_kill(True, forged, self.now)
        self.assertTrue(self.request("/v1/paper")[1]["riskControl"]["killed"])

    def test_kill_reset_requires_server_side_readiness(self):
        self.request("/v1/paper/kill", "POST", {"enabled": True})
        with patch.object(api, "book_snapshot", return_value=None):
            self.start_kill_reset_service()
            code, result = self.request("/v1/paper/reset-kill", "POST", {"acknowledge": True})
        self.assertEqual(code, 409)
        self.assertEqual(result["error"], "SYSTEM_NOT_READY")
        self.assertTrue(self.request("/v1/paper")[1]["riskControl"]["killed"])

    def test_kill_switch_cannot_be_cleared_by_generic_resume_or_malformed_reset(self):
        self.request("/v1/paper/kill", "POST", {"enabled": True})
        self.request("/v1/paper/pause", "POST", {"paused": False})
        with patch.object(api, "decide", return_value=self.valid_ai_decision()):
            _, result = self.request("/v1/paper/evaluate", "POST", {})
        self.assertEqual(result["order"]["reason"], "KILL_SWITCH")
        self.assertEqual(self.request("/v1/paper/reset-kill", "POST",
                                      {"acknowledge": True, "ready": False})[0], 400)


    def test_market_data_reads_use_t0_http_client_while_paper_ledger_stays_separate(self):
        query = (f"symbol=BTCUSDT&timeframe=15m&startMs={self.end-1_800_000}"
                 f"&endMs={self.end}")
        code, _ = self.request("/v1/candles", query=query)
        self.assertEqual(code, 200)

        code, quality = self.request("/v1/quality")
        self.assertEqual(code, 200)
        self.assertEqual(quality["mode"], "PAPER")

        timeframes = {call[0] for call in FixtureT0CandleHttpClient.calls}
        self.assertIn("15m", timeframes)
        self.assertIn("1h", timeframes)

        api.ledger()
        before_paper_read = len(FixtureT0CandleHttpClient.calls)
        code, paper = self.request("/v1/paper")
        self.assertEqual(code, 200)
        self.assertFalse(paper["liveTradingSupported"])
        self.assertEqual(len(FixtureT0CandleHttpClient.calls), before_paper_read)


if __name__ == "__main__":
    unittest.main()
