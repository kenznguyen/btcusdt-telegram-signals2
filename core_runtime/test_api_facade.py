"""Contract tests for the common API's authoritative Bundle-v1 Core facade."""

import unittest
from unittest.mock import patch

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

    def test_preview_uses_bundle_provider_and_one_shot_without_submitting(self):
        with (
            patch("core_runtime.api_facade.build_continuous_runtime",
                  return_value=self.runtime) as build,
            patch("core_runtime.api_facade.latest_eligible_m15_open_ms",
                  return_value=NOW - 900_000),
            patch("core_runtime.one_shot.run_once", return_value={
                "runStatus": "SIGNAL_READY",
                "signal": {"action": "BUY", "reason": "RSI_ADX_ENTRY"},
            }) as run_once,
        ):
            result = preview_core(now_ms=NOW, environ=self.environ)

        self.assertEqual(result["runStatus"], "SIGNAL_READY")
        build.assert_called_once()
        run_once.assert_called_once_with(
            "/paper/config.json", "/bundles/core.json",
            now_ms=NOW, submit=False,
        )
        self.assertEqual(self.events, [("provide", NOW - 900_000)])

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
        with patch("core_runtime.api_facade.build_continuous_runtime") as build:
            with self.assertRaises(CoreApiFacadeError):
                preview_core(now_ms=NOW, environ=invalid)
        build.assert_not_called()

    def test_invalid_pinned_source_sha_fails_closed_before_factory(self):
        invalid = dict(self.environ)
        invalid["CORE_RUNTIME_SOURCE_SHA"] = "not-a-commit"
        with patch("core_runtime.api_facade.build_continuous_runtime") as build:
            with self.assertRaises(CoreApiFacadeError):
                evaluate_core(now_ms=NOW, environ=invalid)
        build.assert_not_called()


if __name__ == "__main__":
    unittest.main()
