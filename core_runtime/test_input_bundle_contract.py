"""RED contract tests for the frozen Core Decision Input Bundle v1.

The implementation module is intentionally absent in this RED increment.
"""

import copy
import hashlib
import unittest

import rfc8785


def contract_api():
    from core_runtime.input_bundle import (
        BundleValidationError,
        compute_bundle_id,
        validate_bundle,
    )
    return BundleValidationError, compute_bundle_id, validate_bundle


def _window(timeframe, now_ms):
    interval = 900_000 if timeframe == "15m" else 3_600_000
    end = now_ms // interval * interval - (interval if timeframe == "1h" else 0)
    candles = []
    for index in range(100):
        opened = end - (100 - index) * interval
        candles.append({
            "openTimeMs": opened,
            "closeTimeMs": opened + interval,
            "open": "50000",
            "high": "50100",
            "low": "49900",
            "close": "50010",
            "volume": "1.25",
            "isClosed": True,
            "availableAtMs": opened + interval,
            "availabilityKind": "FIRST_OBSERVED",
            "quality": "VALIDATED",
            "source": "ccxt.binanceusdm",
        })
    return {
        "contractVersion": "1.0.0",
        "schemaVersion": 1,
        "exchange": "binance",
        "marketType": "USDT_PERPETUAL",
        "symbol": "BTCUSDT",
        "timeframe": timeframe,
        "volumeUnit": "BTC_BASE_ASSET",
        "startMs": candles[0]["openTimeMs"],
        "endMs": end,
        "asOfMs": None,
        "generatedAtMs": now_ms,
        "datasetVersion": "sha256:" + ("a" if timeframe == "15m" else "b") * 64,
        "candles": candles,
        "coverage": {
            "expected": 100,
            "returned": 100,
            "complete": True,
            "gaps": [],
        },
        "freshness": {
            "latestExpectedOpenTimeMs": candles[-1]["openTimeMs"],
            "latestReturnedOpenTimeMs": candles[-1]["openTimeMs"],
            "latestCloseTimeMs": candles[-1]["closeTimeMs"],
            "latestAvailableAtMs": candles[-1]["availableAtMs"],
            "observationAgeMs": now_ms - candles[-1]["availableAtMs"],
            "closeLagMs": now_ms - candles[-1]["closeTimeMs"],
            "evaluable": True,
        },
    }


def valid_bundle():
    now = 1_800_000_000_000
    m15 = _window("15m", now)
    h1 = _window("1h", now)
    # H1 ends exactly at the start of the current M15 hour bucket.
    risk = {
        "mode": "PAPER",
        "liveTradingSupported": False,
        "available": True,
        "riskReady": True,
        "unavailableReason": None,
        "accountEquityQuote": "100",
        "grossExposureQuote": "0",
        "filledExposureQuote": "0",
        "reservedNotionalQuote": "0",
        "reservedMarginQuote": "0",
        "maxDrawdownUsdt": "0",
        "maxDrawdownPct": "0",
        "dailyPnlUsdt": "0",
        "dailyLossUsdt": "0",
        "highWaterMarkQuote": "100",
        "dailyBaselineUtcDayMs": now // 86_400_000 * 86_400_000,
        "markPrice": "50000",
        "markObservedAtMs": now,
        "datasetVersion": "risk-dataset-1",
        "killSwitch": {"enabled": False},
        "positions": {},
        "updatedAtMs": now,
    }
    bundle = {
        "contract": "CORE_DECISION_INPUT_BUNDLE",
        "contractVersion": "1.0.0",
        "schemaVersion": 1,
        "bundleId": "sha256:" + "0" * 64,
        "createdAtMs": now,
        "decisionAtMs": now,
        "mode": "PAPER",
        "aiExecutionEnabled": False,
        "strategyId": "STRATEGY_CORE",
        "market": {
            "exchange": "binance",
            "marketType": "USDT_PERPETUAL",
            "symbol": "BTCUSDT",
            "decisionTimeframe": "15m",
        },
        "marketData": {
            "sourceContract": "T0_READ_ONLY_CANDLE_V1",
            "m15": m15,
            "h1": h1,
        },
        "orderBook": {
            "source": "hummingbot",
            "connector": "binance_perpetual",
            "symbol": "BTCUSDT",
            "observedAtMs": now - 1_000,
            "bids": [{"price": "49999", "quantity": "1"}],
            "asks": [{"price": "50001", "quantity": "1"}],
        },
        "paperState": {
            "positionBase": "0",
            "averageEntryPrice": "0",
            "strategyState": {
                "owner": None,
                "dcaUsed": False,
                "strategyId": "STRATEGY_CORE",
            },
        },
        "accountRisk": {
            "snapshotDigest": "sha256:" + hashlib.sha256(rfc8785.dumps(risk)).hexdigest(),
            "snapshot": risk,
        },
    }
    digest_input = dict(bundle)
    digest_input.pop("bundleId")
    bundle["bundleId"] = "sha256:" + hashlib.sha256(rfc8785.dumps(digest_input)).hexdigest()
    return bundle


def _rehash(bundle):
    digest_input = dict(bundle)
    digest_input.pop("bundleId")
    bundle["bundleId"] = "sha256:" + hashlib.sha256(rfc8785.dumps(digest_input)).hexdigest()


class CoreDecisionInputBundleContractTest(unittest.TestCase):
    def test_valid_paper_bundle_passes_with_explicit_book_age_policy(self):
        _, _, validate = contract_api()
        result = validate(valid_bundle(), max_book_age_ms=5_000)
        self.assertEqual(result["status"], "BUNDLE_VALID")
        self.assertEqual(result["strategyId"], "STRATEGY_CORE")

    def test_missing_or_nonpositive_book_age_policy_fails_closed(self):
        Error, _, validate = contract_api()
        for policy in (None, 0, -1, True, "5000"):
            with self.subTest(policy=policy):
                with self.assertRaises(Error):
                    validate(valid_bundle(), max_book_age_ms=policy)

    def test_stale_or_future_order_book_is_rejected(self):
        Error, _, validate = contract_api()
        stale = valid_bundle()
        stale["orderBook"]["observedAtMs"] -= 5_001
        _rehash(stale)
        with self.assertRaisesRegex(Error, "ORDER_BOOK_STALE"):
            validate(stale, max_book_age_ms=5_000)
        future = valid_bundle()
        future["orderBook"]["observedAtMs"] += 1
        _rehash(future)
        with self.assertRaisesRegex(Error, "ORDER_BOOK_TIMESTAMP_INVALID"):
            validate(future, max_book_age_ms=5_000)

    def test_non_paper_or_ai_enabled_bundle_is_rejected(self):
        Error, _, validate = contract_api()
        for field, value in (("mode", "LIVE"), ("aiExecutionEnabled", True)):
            bundle = valid_bundle()
            bundle[field] = value
            with self.subTest(field=field):
                with self.assertRaises(Error):
                    validate(bundle, max_book_age_ms=5_000)

    def test_incomplete_or_mutated_candle_window_is_rejected(self):
        Error, _, validate = contract_api()
        bundle = valid_bundle()
        bundle["marketData"]["m15"]["coverage"]["complete"] = False
        with self.assertRaisesRegex(Error, "CANDLE_COVERAGE_INVALID"):
            validate(bundle, max_book_age_ms=5_000)
        bundle = valid_bundle()
        bundle["marketData"]["h1"]["candles"][10]["close"] = 50000.0
        with self.assertRaisesRegex(Error, "JSON_FLOAT_NOT_ALLOWED"):
            validate(bundle, max_book_age_ms=5_000)

    def test_order_book_requires_positive_ordered_decimal_levels_and_valid_spread(self):
        Error, _, validate = contract_api()
        bundle = valid_bundle()
        bundle["orderBook"]["bids"][0]["price"] = "NaN"
        with self.assertRaisesRegex(Error, "ORDER_BOOK_LEVEL_INVALID"):
            validate(bundle, max_book_age_ms=5_000)
        bundle = valid_bundle()
        bundle["orderBook"]["asks"][0]["price"] = "49998"
        with self.assertRaisesRegex(Error, "ORDER_BOOK_SPREAD_INVALID"):
            validate(bundle, max_book_age_ms=5_000)

    def test_core_state_and_account_risk_snapshot_are_not_caller_overridable(self):
        Error, _, validate = contract_api()
        bundle = valid_bundle()
        bundle["paperState"]["strategyState"]["strategyId"] = "AI_FREQAI"
        with self.assertRaisesRegex(Error, "CORE_STATE_INVALID"):
            validate(bundle, max_book_age_ms=5_000)
        bundle = valid_bundle()
        bundle["accountRisk"]["snapshot"]["available"] = False
        with self.assertRaisesRegex(Error, "RISK_SNAPSHOT_UNAVAILABLE"):
            validate(bundle, max_book_age_ms=5_000)

    def test_bundle_digest_uses_rfc8785_excludes_bundle_id_and_is_key_order_independent(self):
        _, digest, _ = contract_api()
        bundle = valid_bundle()
        first = digest(bundle)
        reordered = dict(reversed(list(bundle.items())))
        reordered["bundleId"] = "sha256:" + "f" * 64
        self.assertEqual(first, digest(reordered))
        self.assertRegex(first, r"^sha256:[0-9a-f]{64}$")

    def test_bundle_digest_rejects_floats_and_unsafe_integer_values(self):
        Error, digest, _ = contract_api()
        bundle = valid_bundle()
        bundle["orderBook"]["bids"][0]["price"] = 50000.0
        with self.assertRaises(Error):
            digest(bundle)
        bundle = valid_bundle()
        bundle["decisionAtMs"] = 2**53
        with self.assertRaises(Error):
            digest(bundle)

    def test_digest_preserves_array_order_and_decimal_string_precision(self):
        _, digest, _ = contract_api()
        bundle = valid_bundle()
        first = digest(bundle)
        reordered_levels = copy.deepcopy(bundle)
        reordered_levels["orderBook"]["bids"].append(
            {"price": "49998", "quantity": "1"}
        )
        self.assertNotEqual(first, digest(reordered_levels))
        precision_change = copy.deepcopy(bundle)
        precision_change["orderBook"]["bids"][0]["price"] = "49999.0"
        self.assertNotEqual(first, digest(precision_change))

    def test_unknown_fields_and_invalid_bundle_timestamps_are_rejected(self):
        Error, _, validate = contract_api()
        bundle = valid_bundle()
        bundle["unexpected"] = "not-v1"
        with self.assertRaisesRegex(Error, "BUNDLE_FIELDS_INVALID"):
            validate(bundle, max_book_age_ms=5_000)
        bundle = valid_bundle()
        bundle["createdAtMs"] = bundle["decisionAtMs"] + 1
        with self.assertRaisesRegex(Error, "BUNDLE_TIMESTAMP_INVALID"):
            validate(bundle, max_book_age_ms=5_000)

    def test_candle_gap_unclosed_candle_and_ineligible_h1_are_rejected(self):
        Error, _, validate = contract_api()
        bundle = valid_bundle()
        bundle["marketData"]["m15"]["candles"][50]["openTimeMs"] += 900_000
        with self.assertRaisesRegex(Error, "CANDLE_SEQUENCE_INVALID"):
            validate(bundle, max_book_age_ms=5_000)
        bundle = valid_bundle()
        bundle["marketData"]["m15"]["candles"][-1]["isClosed"] = False
        with self.assertRaisesRegex(Error, "CANDLE_PROVENANCE_INVALID"):
            validate(bundle, max_book_age_ms=5_000)
        bundle = valid_bundle()
        bundle["marketData"]["h1"]["candles"][-1]["openTimeMs"] += 3_600_000
        with self.assertRaises(Error):
            validate(bundle, max_book_age_ms=5_000)

    def test_book_level_order_and_duplicate_prices_are_rejected(self):
        Error, _, validate = contract_api()
        bundle = valid_bundle()
        bundle["orderBook"]["bids"].append({"price": "50000", "quantity": "1"})
        with self.assertRaisesRegex(Error, "ORDER_BOOK_LEVEL_INVALID"):
            validate(bundle, max_book_age_ms=5_000)
        bundle = valid_bundle()
        bundle["orderBook"]["bids"].append({"price": "49999", "quantity": "2"})
        with self.assertRaisesRegex(Error, "ORDER_BOOK_LEVEL_INVALID"):
            validate(bundle, max_book_age_ms=5_000)

    def test_inconsistent_core_position_and_risk_digest_mismatch_are_rejected(self):
        Error, _, validate = contract_api()
        bundle = valid_bundle()
        bundle["paperState"]["positionBase"] = "1"
        with self.assertRaisesRegex(Error, "CORE_STATE_INVALID"):
            validate(bundle, max_book_age_ms=5_000)
        bundle = valid_bundle()
        bundle["accountRisk"]["snapshot"]["riskReady"] = False
        with self.assertRaisesRegex(Error, "RISK_SNAPSHOT_DIGEST_MISMATCH"):
            validate(bundle, max_book_age_ms=5_000)

    def test_bundle_id_mismatch_and_noncanonical_decimal_text_are_rejected(self):
        Error, _, validate = contract_api()
        bundle = valid_bundle()
        bundle["bundleId"] = "sha256:" + "f" * 64
        with self.assertRaisesRegex(Error, "BUNDLE_ID_MISMATCH"):
            validate(bundle, max_book_age_ms=5_000)
        bundle = valid_bundle()
        bundle["orderBook"]["bids"][0]["price"] = "05.000"
        with self.assertRaisesRegex(Error, "ORDER_BOOK_LEVEL_INVALID"):
            validate(bundle, max_book_age_ms=5_000
            )


if __name__ == "__main__":
    unittest.main()
