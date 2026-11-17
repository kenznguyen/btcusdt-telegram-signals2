"""Test-first contracts for the read-only Core Bundle Provider orchestration."""

import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from core_runtime.bundle_provider import CoreBundleProvider, BundleProviderError


NOW = 1_800_000_010_000
INTERVAL_M15 = 900_000
INTERVAL_H1 = 3_600_000


class CoreBundleProviderTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.config = self.root / "paper.json"
        self.config.write_text(json.dumps({
            "mode": "PAPER",
            "ai_execution_enabled": False,
            "ledger_path": str(self.root / "paper.sqlite3"),
        }), encoding="utf-8")
        self.candle = Mock()
        self.candle.fetch_one_page.side_effect = lambda start, end, as_of, timeframe: {
            "timeframe": timeframe, "startMs": start, "endMs": end,
            "asOfMs": as_of,
        }
        self.book = Mock()
        self.book.fetch.return_value = {"contractVersion": "T1_T2_ORDERBOOK_V1"}
        self.preflight = Mock(return_value={
            "status": "PAPER_LEDGER_READY", "riskReady": True,
            "killSwitch": {"killed": False, "paused": False},
        })
        self.risk = Mock(return_value={
            "mode": "PAPER", "liveTradingSupported": False,
            "available": True, "riskReady": True,
            "killSwitch": {
                "paused": False, "killed": False, "reason": None,
                "updatedAtMs": NOW, "mode": "PAPER",
                "liveTradingSupported": False,
            },
        })
        self.paper = Mock(return_value={
            "positionBase": "0", "averageEntryPrice": "0",
            "strategyState": {
                "owner": "STRATEGY_CORE", "dcaUsed": False,
                "strategyId": "STRATEGY_CORE", "initialMarginQuote": "0",
            },
        })
        self.builder = Mock(return_value={
            "contract": "CORE_DECISION_INPUT_BUNDLE",
            "bundleId": "sha256:" + "a" * 64,
        })
        self.provider = CoreBundleProvider(
            candle_client=self.candle,
            orderbook_client=self.book,
            config_path=self.config,
            bundle_store_dir=self.root / "bundles",
            clock_ms=lambda: NOW,
            settlement_ms=0,
            preflight_fn=self.preflight,
            risk_reader=self.risk,
            paper_reader=self.paper,
            bundle_builder=self.builder,
            environ={"AI_EXECUTION_ENABLED": "false"},
        )

    def test_fetches_aligned_closed_m15_and_h1_windows_and_reads_paper_state(self):
        candle_open = ((NOW - 1) // INTERVAL_M15) * INTERVAL_M15 - INTERVAL_M15
        output_path = self.provider(candle_open)
        self.assertTrue(Path(output_path).is_file())
        m15_start = candle_open - 99 * INTERVAL_M15
        m15_end = candle_open + INTERVAL_M15
        h1_end = (candle_open // INTERVAL_H1) * INTERVAL_H1
        h1_start = h1_end - 100 * INTERVAL_H1
        self.assertEqual(self.candle.fetch_one_page.call_args_list[0].args,
                         (m15_start, m15_end, NOW))
        self.assertEqual(self.candle.fetch_one_page.call_args_list[0].kwargs,
                         {"timeframe": "15m"})
        self.assertEqual(self.candle.fetch_one_page.call_args_list[1].args,
                         (h1_start, h1_end, NOW))
        self.assertEqual(self.candle.fetch_one_page.call_args_list[1].kwargs,
                         {"timeframe": "1h"})
        self.book.fetch.assert_called_once_with(decision_at_ms=NOW)
        self.preflight.assert_called_once()
        self.risk.assert_called_once()
        self.paper.assert_called_once()
        self.assertEqual(self.builder.call_args.kwargs["decision_at_ms"], NOW)
        self.assertEqual(self.builder.call_args.kwargs["paper_snapshot"], {
            "positionBase": "0", "averageEntryPrice": "0",
            "strategyState": {
                "owner": "STRATEGY_CORE", "dcaUsed": False,
                "strategyId": "STRATEGY_CORE",
            },
        })

    def test_preview_returns_bundle_in_memory_without_persistent_store_write(self):
        candle_open = ((NOW - 1) // INTERVAL_M15) * INTERVAL_M15 - INTERVAL_M15
        bundle = self.provider(candle_open, persist=False)

        self.assertIsInstance(bundle, dict)
        self.assertEqual(bundle["contract"], "CORE_DECISION_INPUT_BUNDLE")
        self.assertFalse((self.root / "bundles").exists())
        self.builder.assert_called_once()

    def test_persists_bundle_immutably_and_reuses_identical_content(self):
        candle_open = ((NOW - 1) // INTERVAL_M15) * INTERVAL_M15 - INTERVAL_M15
        first = Path(self.provider(candle_open))
        second = Path(self.provider(candle_open))
        self.assertEqual(first, second)
        self.assertTrue(first.is_file())
        raw = first.read_bytes()
        self.assertEqual(first.name, hashlib.sha256(raw).hexdigest() + ".json")
        self.assertEqual(json.loads(raw)["bundleId"], "sha256:" + "a" * 64)

    def test_blocks_before_network_when_paper_risk_or_kill_switch_is_not_ready(self):
        self.preflight.side_effect = BundleProviderError("PAPER_LEDGER_NOT_READY")
        candle_open = ((NOW - 1) // INTERVAL_M15) * INTERVAL_M15 - INTERVAL_M15
        with self.assertRaises(BundleProviderError):
            self.provider(candle_open)
        self.candle.fetch_one_page.assert_not_called()
        self.book.fetch.assert_not_called()
        self.risk.assert_not_called()
        self.paper.assert_not_called()

    def test_rejects_non_latest_or_unaligned_m15_open_before_io(self):
        with self.assertRaises(BundleProviderError):
            self.provider(123)
        self.candle.fetch_one_page.assert_not_called()
        self.book.fetch.assert_not_called()


class CoreBundleProviderSQLiteIntegrationTest(unittest.TestCase):
    """Exercise the provider against real read-only PAPER SQLite readers."""

    def test_builds_valid_bundle_from_disposable_sqlite_without_mutating_ledger(self):
        from core_runtime.input_bundle import validate_bundle
        from core_runtime.test_input_bundle_contract import valid_bundle
        from paper_execution.test_core_first_operational import CoreFirstOperationalProofTest

        fixture = CoreFirstOperationalProofTest(
            "test_core_signal_flows_through_shared_risk_into_paper_ledger"
        )
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        root = Path(fixture.temp.name)
        ledger_path = fixture.path
        config_path = root / "provider-paper-config.json"
        config_path.write_text(json.dumps({
            "mode": "PAPER",
            "ai_execution_enabled": False,
            "ledger_path": str(ledger_path),
        }), encoding="utf-8")

        template = valid_bundle()
        windows = {}
        for key, timeframe in (("m15", "15m"), ("h1", "1h")):
            payload = copy.deepcopy(template["marketData"][key])
            payload["source"] = "ccxt.binanceusdm"
            for candle in payload["candles"]:
                candle.update({
                    "exchange": "binance",
                    "marketType": "USDT_PERPETUAL",
                    "symbol": "BTCUSDT",
                    "timeframe": timeframe,
                })
            windows[timeframe] = payload

        class FixtureCandleClient:
            def fetch_one_page(self, start_ms, end_ms, as_of_ms, *, timeframe):
                return copy.deepcopy(windows[timeframe])

        class FixtureOrderbookClient:
            def fetch(self, *, decision_at_ms):
                return copy.deepcopy(template["orderBook"])

        env = {
            "AI_EXECUTION_ENABLED": "false",
            "MARKET_DATA_DB": "",
            "T0_FEEDER_LEASE_DB": "",
            "PAPER_DB": "",
            "PAPER_TRADING_DB": "",
            "BINANCE_API_KEY": "",
            "BINANCE_API_SECRET": "",
            "OKX_API_KEY": "",
            "OKX_API_SECRET": "",
        }
        before = hashlib.sha256(ledger_path.read_bytes()).hexdigest()
        provider = CoreBundleProvider(
            candle_client=FixtureCandleClient(),
            orderbook_client=FixtureOrderbookClient(),
            config_path=config_path,
            bundle_store_dir=root / "provider-bundles",
            clock_ms=lambda: fixture.now,
            settlement_ms=0,
            environ=env,
        )

        candle_open = fixture.now - INTERVAL_M15
        output_path = Path(provider(candle_open))
        bundle = json.loads(output_path.read_text(encoding="utf-8"))
        verdict = validate_bundle(bundle, max_book_age_ms=2_000)

        self.assertEqual(verdict["status"], "BUNDLE_VALID")
        self.assertEqual(bundle["strategyId"], "STRATEGY_CORE")
        self.assertIs(bundle["aiExecutionEnabled"], False)
        self.assertEqual(bundle["marketData"]["m15"]["datasetVersion"],
                         windows["15m"]["datasetVersion"])
        self.assertEqual(bundle["marketData"]["h1"]["datasetVersion"],
                         windows["1h"]["datasetVersion"])
        self.assertIs(bundle["accountRisk"]["snapshot"]["riskReady"], True)
        self.assertIs(bundle["accountRisk"]["snapshot"]["killSwitch"]["killed"], False)
        self.assertIs(bundle["accountRisk"]["snapshot"]["killSwitch"]["paused"], False)
        self.assertEqual(bundle["paperState"]["strategyState"]["strategyId"],
                         "STRATEGY_CORE")
        self.assertEqual(
            hashlib.sha256(ledger_path.read_bytes()).hexdigest(), before,
            "CoreBundleProvider must not mutate the PAPER SQLite ledger",
        )


if __name__ == "__main__":
    unittest.main()
