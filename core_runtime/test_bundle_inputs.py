"""Contract tests for normalizing T0/T1 inputs into Core Bundle v1."""

import copy
import unittest

from core_runtime.bundle_inputs import (
    BundleInputError,
    build_core_bundle,
    normalize_candle_window,
    normalize_orderbook_snapshot,
)
from core_runtime.input_bundle import validate_bundle
from core_runtime.test_input_bundle_contract import valid_bundle


class CoreBundleInputsTest(unittest.TestCase):
    def setUp(self):
        self.bundle = valid_bundle()

    def api_window(self, timeframe):
        window = copy.deepcopy(self.bundle["marketData"][timeframe])
        window["source"] = "ccxt.binanceusdm"
        for candle in window["candles"]:
            candle.update({
                "exchange": "binance",
                "marketType": "USDT_PERPETUAL",
                "symbol": "BTCUSDT",
                "timeframe": timeframe,
            })
        return window

    def test_normalizes_t0_envelope_without_rewriting_dataset_version_or_candles(self):
        source = self.api_window("m15")
        normalized = normalize_candle_window(source, timeframe="15m")
        self.assertEqual(normalized["datasetVersion"], source["datasetVersion"])
        self.assertEqual(normalized["candles"][0]["openTimeMs"],
                         source["candles"][0]["openTimeMs"])
        self.assertEqual(set(normalized), {
            "contractVersion", "schemaVersion", "exchange", "marketType",
            "symbol", "timeframe", "volumeUnit", "startMs", "endMs",
            "asOfMs", "generatedAtMs", "datasetVersion", "candles",
            "coverage", "freshness",
        })
        self.assertEqual(set(normalized["candles"][0]), {
            "openTimeMs", "closeTimeMs", "open", "high", "low", "close",
            "volume", "isClosed", "availableAtMs", "availabilityKind",
            "quality", "source",
        })

    def test_rejects_wrong_t0_timeframe_and_missing_provenance(self):
        source = self.api_window("m15")
        source["timeframe"] = "1h"
        with self.assertRaises(BundleInputError):
            normalize_candle_window(source, timeframe="15m")
        source = self.api_window("m15")
        del source["datasetVersion"]
        with self.assertRaises(BundleInputError):
            normalize_candle_window(source, timeframe="15m")

    def test_normalizes_validated_t1_snapshot_to_bundle_wire_shape(self):
        book = self.bundle["orderBook"]
        snapshot = {
            "contractVersion": book["t1Evidence"]["contractVersion"],
            "symbol": book["symbol"],
            "market": book["t1Evidence"]["market"],
            "bids": [[row["price"], row["quantity"]] for row in book["bids"]],
            "asks": [[row["price"], row["quantity"]] for row in book["asks"]],
            **book["t1Evidence"],
        }
        normalized = normalize_orderbook_snapshot(snapshot)
        self.assertEqual(normalized["source"], "t1")
        self.assertEqual(normalized["connector"], "binance_usdm_perpetual")
        self.assertEqual(normalized["t1Evidence"]["snapshotId"],
                         book["t1Evidence"]["snapshotId"])
        self.assertEqual(normalized["bids"][0], book["bids"][0])

    def test_builds_bundle_accepted_by_frozen_v1_validator(self):
        risk = copy.deepcopy(self.bundle["accountRisk"]["snapshot"])
        paper = {
            "positionBase": "0",
            "averageEntryPrice": "0",
            "strategyState": {
                "owner": None,
                "dcaUsed": False,
                "strategyId": "STRATEGY_CORE",
            },
        }
        book = {
            "contractVersion": self.bundle["orderBook"]["t1Evidence"]["contractVersion"],
            "symbol": "BTCUSDT",
            "market": self.bundle["orderBook"]["t1Evidence"]["market"],
            "bids": [[row["price"], row["quantity"]]
                     for row in self.bundle["orderBook"]["bids"]],
            "asks": [[row["price"], row["quantity"]]
                     for row in self.bundle["orderBook"]["asks"]],
            **self.bundle["orderBook"]["t1Evidence"],
        }
        result = build_core_bundle(
            decision_at_ms=self.bundle["decisionAtMs"],
            m15_payload=self.api_window("m15"),
            h1_payload=self.api_window("h1"),
            orderbook_snapshot=book,
            paper_snapshot=paper,
            account_risk_snapshot=risk,
        )
        verdict = validate_bundle(result, max_book_age_ms=5_000)
        self.assertEqual(verdict["status"], "BUNDLE_VALID")
        self.assertEqual(result["aiExecutionEnabled"], False)
        self.assertEqual(result["strategyId"], "STRATEGY_CORE")

    def test_native_readonly_paper_risk_control_shape_is_preserved(self):
        risk = copy.deepcopy(self.bundle["accountRisk"]["snapshot"])
        risk["killSwitch"] = {
            "paused": False, "killed": False, "reason": None,
            "updatedAtMs": self.bundle["decisionAtMs"],
            "mode": "PAPER", "liveTradingSupported": False,
        }
        paper = {
            "positionBase": "0", "averageEntryPrice": "0",
            "strategyState": {
                "owner": None, "dcaUsed": False,
                "strategyId": "STRATEGY_CORE",
            },
        }
        book = self.bundle["orderBook"]
        native_book = {
            "contractVersion": book["t1Evidence"]["contractVersion"],
            "symbol": book["symbol"],
            "market": book["t1Evidence"]["market"],
            "bids": [[row["price"], row["quantity"]] for row in book["bids"]],
            "asks": [[row["price"], row["quantity"]] for row in book["asks"]],
            **book["t1Evidence"],
        }
        result = build_core_bundle(
            decision_at_ms=self.bundle["decisionAtMs"],
            m15_payload=self.api_window("m15"),
            h1_payload=self.api_window("h1"),
            orderbook_snapshot=native_book,
            paper_snapshot=paper,
            account_risk_snapshot=risk,
        )
        self.assertEqual(result["accountRisk"]["snapshot"], risk)

    def test_risk_unready_snapshot_is_rejected_before_bundle_creation(self):
        risk = copy.deepcopy(self.bundle["accountRisk"]["snapshot"])
        risk["riskReady"] = False
        with self.assertRaises(BundleInputError):
            build_core_bundle(
                decision_at_ms=self.bundle["decisionAtMs"],
                m15_payload=self.api_window("m15"),
                h1_payload=self.api_window("h1"),
                orderbook_snapshot=self.bundle["orderBook"],
                paper_snapshot=self.bundle["paperState"],
                account_risk_snapshot=risk,
            )


if __name__ == "__main__":
    unittest.main()
