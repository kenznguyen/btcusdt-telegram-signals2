"""Contract tests for the common API's authoritative Bundle-v1 Core facade."""

import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pipeline.api as common_api

from core_runtime.api_facade import (
    CoreApiFacadeError,
    evaluate_core,
    preview_core,
)


NOW = 1_800_000_000_000
SOURCE_SHA = "a" * 40


class FakeRunner:
    config_path = "/paper/config.json"

    def __init__(self, events, process_result=None):
        self.events = events
        self.process_result = process_result or {
            "cycleKey": "cycle-1",
            "status": "PAPER_ACCEPTED",
            "result": {
                "runStatus": "PAPER_ACCEPTED",
                "signal": {"action": "BUY", "reason": "RSI_ADX_ENTRY"},
                "paperLedgerReference": {"orderId": "paper-order-1"},
            },
        }

    def recover_incomplete(self, *, now_ms):
        self.events.append(("recover", now_ms))
        return []

    def process_bundle(self, bundle_path, *, now_ms):
        self.events.append(("process", bundle_path, now_ms))
        return self.process_result


class FakePreviewProvider:
    def __init__(self, events):
        self.events = events

    def __call__(self, candle_open, *, persist=True):
        self.events.append(("provide", candle_open, persist))
        if persist:
            return "/bundles/core.json"
        return {"bundleId": "preview-bundle", "mode": "PAPER"}


class FakeRuntime:
    def __init__(self, events, process_result=None):
        self.runner = FakeRunner(events, process_result)
        self.bundle_provider = lambda candle_open: (
            events.append(("provide", candle_open)) or "/bundles/core.json"
        )


class CoreApiFacadeTest(unittest.TestCase):
    def setUp(self):
        self.environ = {
            "CORE_RUNTIME_CONFIG_PATH": "/paper/config.json",
            "CORE_RUNTIME_JOURNAL_PATH": "/paper/runtime.sqlite3",
            "CORE_RUNTIME_BUNDLE_STORE_DIR": "/paper/bundles",
            "CORE_RUNTIME_SOURCE_SHA": SOURCE_SHA,
            "T0_CANDLE_API_BASE_URL": "https://t0.example.test",
            "T0_CANDLE_API_TOKEN": "t0-token",
            "T0_CANDLE_MAX_LAG_MS": "120000",
            "T1_ORDERBOOK_API_BASE_URL": "http://127.0.0.1:8787",
            "T1_ORDERBOOK_API_TOKEN": "t1-token",
        }
        self.events = []
        self.runtime = FakeRuntime(self.events)

    def test_preview_uses_non_persistent_bundle_and_one_shot_without_submitting(self):
        provider = FakePreviewProvider(self.events)
        captured = {}

        def inspect_preview(config_path, bundle_path, *, now_ms, submit):
            captured["path"] = Path(bundle_path)
            self.assertTrue(captured["path"].is_file())
            self.assertEqual(
                json.loads(captured["path"].read_text(encoding="utf-8")),
                {"bundleId": "preview-bundle", "mode": "PAPER"},
            )
            return {
                "runStatus": "SIGNAL_READY",
                "signal": {"action": "BUY", "reason": "RSI_ADX_ENTRY"},
                "riskDecision": {"decision": "NOT_EVALUATED"},
            }

        with (
            patch("core_runtime.api_facade.build_core_bundle_provider",
                  return_value=provider) as build_provider,
            patch("core_runtime.api_facade.build_continuous_runtime") as build_runtime,
            patch("core_runtime.api_facade.latest_eligible_m15_open_ms",
                  return_value=NOW - 900_000),
            patch("core_runtime.one_shot.run_once", side_effect=inspect_preview) as run_once,
        ):
            result = preview_core(now_ms=NOW, environ=self.environ)

        self.assertEqual(result["runStatus"], "SIGNAL_READY")
        build_provider.assert_called_once()
        build_runtime.assert_not_called()
        self.assertEqual(run_once.call_args.args[0], "/paper/config.json")
        self.assertEqual(run_once.call_args.kwargs, {"now_ms": NOW, "submit": False})
        self.assertFalse(captured["path"].exists())
        self.assertEqual(self.events, [("provide", NOW - 900_000, False)])

    def test_evaluation_recovers_then_processes_bundle_through_continuous_runner(self):
        with (
            patch("core_runtime.api_facade.build_continuous_runtime",
                  return_value=self.runtime),
            patch("core_runtime.api_facade.latest_eligible_m15_open_ms",
                  return_value=NOW - 900_000),
        ):
            result = evaluate_core(now_ms=NOW, environ=self.environ)

        self.assertEqual(result["status"], "PAPER_ACCEPTED")
        self.assertEqual(self.events, [
            ("recover", NOW),
            ("provide", NOW - 900_000),
            ("process", "/bundles/core.json", NOW),
        ])

    def test_missing_runtime_configuration_fails_closed_before_factory(self):
        invalid = dict(self.environ)
        invalid.pop("T1_ORDERBOOK_API_TOKEN")
        with patch("core_runtime.api_facade.build_core_bundle_provider") as build:
            with self.assertRaises(CoreApiFacadeError):
                preview_core(now_ms=NOW, environ=invalid)
        build.assert_not_called()

    def test_common_signals_projection_uses_bundle_preview_for_core(self):
        preview = {
            "source": "STRATEGY_CORE",
            "action": "BUY",
            "reason": "RSI_ADX_ENTRY",
            "intent": {"source": "STRATEGY_CORE"},
        }
        with (
            patch.object(common_api, "context", return_value={}),
            patch.object(common_api, "decide", return_value={"action": "WAIT"}),
            patch.object(common_api, "core_runtime_preview", return_value=preview) as core_preview,
        ):
            result = common_api.signal_snapshot(NOW)

        self.assertIs(result["strategyCore"], preview)
        core_preview.assert_called_once_with(NOW)
        self.assertFalse(hasattr(common_api, "core_decide"))

    def test_common_api_preserves_preview_risk_decision_for_signal_display(self):
        preview = {
            "runStatus": "SIGNAL_READY",
            "signal": {
                "action": "BUY",
                "reason": "RSI_ADX_ENTRY",
                "intent": {"mode": "PAPER"},
            },
            "riskDecision": {
                "decision": "NOT_EVALUATED",
                "reason": "PREVIEW_ONLY",
            },
        }
        with patch("core_runtime.api_facade.preview_core", return_value=preview):
            result = common_api.core_runtime_preview(NOW)

        self.assertEqual(result["action"], "BUY")
        self.assertEqual(result["riskDecision"], preview["riskDecision"])

    def test_quality_projection_uses_bundle_preview_and_t1_book_evidence(self):
        window = {
            "coverage": {"complete": True},
            "candles": [{} for _ in range(500)],
            "datasetVersion": "dataset-v1",
        }
        preview = {
            "action": "WAIT",
            "reason": "CORE_NO_ENTRY",
            "indicators": {
                "rsiM15": "45", "adxM15": "20",
                "plusDiH1": "22", "minusDiH1": "18", "adxH1": "25",
            },
            "sourceEvidence": {"t1SnapshotId": "sha256:" + "b" * 64},
        }
        with (
            patch.object(common_api, "context", return_value={
                "intelligence": None, "book": None, "prediction": None, "errors": {},
            }),
            patch.object(common_api, "market_window", return_value=window),
            patch.object(common_api, "core_runtime_preview", return_value=preview) as core_preview,
        ):
            result = common_api.quality_snapshot(NOW)

        streams = {item["name"]: item for item in result["streams"]}
        self.assertEqual(streams["Strategy Core producer"]["status"], "READY")
        self.assertEqual(streams["T1 Order Book V1"]["status"], "READY")
        self.assertEqual(
            streams["T1 Order Book V1"]["snapshotId"],
            preview["sourceEvidence"]["t1SnapshotId"],
        )
        core_preview.assert_called_once_with(NOW)

    def test_core_evaluate_route_never_uses_legacy_local_decision_or_hummingbot_path(self):
        with tempfile.TemporaryDirectory() as directory:
            db_path = Path(directory) / "paper.sqlite3"
            db_path.touch()
            body = json.dumps({"source": "CORE"}).encode()
            environ = {
                "REQUEST_METHOD": "POST",
                "PATH_INFO": "/v1/paper/evaluate",
                "CONTENT_LENGTH": str(len(body)),
                "wsgi.input": io.BytesIO(body),
                "HTTP_AUTHORIZATION": "Bearer control-secret",
            }
            response_meta = {}
            def start_response(status, headers):
                response_meta["status"] = status
                response_meta["headers"] = headers

            expected = {
                "decision": {
                    "source": "STRATEGY_CORE",
                    "action": "WAIT",
                    "reason": "CORE_NO_ENTRY",
                    "intent": None,
                },
                "order": None,
            }
            with (
                patch.dict(os.environ, {
                    "CONTROL_TOKEN": "control-secret",
                    "MARKET_DATA_TOKEN": "read-secret",
                    "MARKET_DATA_DB": str(db_path),
                }, clear=False),
                patch.object(common_api, "now_ms", return_value=NOW),
                patch.object(common_api, "control_permit", return_value=True),
                patch.object(common_api, "core_runtime_evaluate", return_value=expected) as evaluate,
                patch.object(common_api, "market_window", side_effect=AssertionError("legacy T0 read")),
                patch.object(common_api, "book_snapshot", side_effect=AssertionError("legacy Hummingbot read")),
                patch.object(common_api, "context", side_effect=AssertionError("legacy context")),
                patch.object(common_api, "ledger", side_effect=AssertionError("legacy ledger writer")),
            ):
                payload = b"".join(common_api.application(environ, start_response))

        self.assertEqual(response_meta["status"], "200 OK")
        self.assertEqual(json.loads(payload), expected)
        evaluate.assert_called_once_with(NOW)
        self.assertFalse(hasattr(common_api, "core_decide"))

    def test_invalid_pinned_source_sha_fails_closed_before_factory(self):
        invalid = dict(self.environ)
        invalid["CORE_RUNTIME_SOURCE_SHA"] = "not-a-commit"
        with patch("core_runtime.api_facade.build_continuous_runtime") as build:
            with self.assertRaises(CoreApiFacadeError):
                evaluate_core(now_ms=NOW, environ=invalid)
        build.assert_not_called()


if __name__ == "__main__":
    unittest.main()
