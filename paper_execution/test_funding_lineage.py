"""Offline contract tests for Binance/Tardis funding observation comparison."""

import unittest

from paper_execution.funding_lineage import compare_funding_observations


def observation(*, venue, funding_time_ms=1000, funding_rate="0.001", **overrides):
    row = {
        "venue": venue,
        "instrument": "BTCUSDT",
        "market_type": "USD_M_FUTURES",
        "contract_type": "PERPETUAL",
        "margin_asset": "USDT",
        "settlement_asset": "USDT",
        "funding_time_ms": funding_time_ms,
        "funding_rate": funding_rate,
    }
    row.update(overrides)
    return row


class FundingLineageComparisonTest(unittest.TestCase):
    def test_equal_observations_corroborate_only_the_exact_overlap(self):
        result = compare_funding_observations(
            [observation(venue="BINANCE")],
            [observation(venue="BINANCE", exchange_timestamp_ms=999, local_timestamp_ms=1001)],
        )

        self.assertEqual(result["observationCorroboration"], "PASS_WITHIN_OVERLAP")
        self.assertEqual(result["matchedCount"], 1)
        self.assertEqual(result["unmatchedBinanceCount"], 0)
        self.assertEqual(result["unmatchedTardisCount"], 0)
        self.assertEqual(result["issuerIndependence"], "NOT_VERIFIED_SAME_ISSUER")
        self.assertEqual(result["collectorIndependence"], "NOT_VERIFIED")

    def test_rate_mismatch_blocks_observation_corroboration(self):
        result = compare_funding_observations(
            [observation(venue="BINANCE", funding_rate="0.001")],
            [observation(venue="BINANCE", funding_rate="0.0011")],
        )

        self.assertEqual(result["observationCorroboration"], "MISMATCH")
        self.assertEqual(result["mismatchCount"], 1)

    def test_partial_overlap_is_not_population_completeness(self):
        result = compare_funding_observations(
            [observation(venue="BINANCE", funding_time_ms=1000),
             observation(venue="BINANCE", funding_time_ms=2000)],
            [observation(venue="BINANCE", funding_time_ms=1000)],
        )

        self.assertEqual(result["observationCorroboration"], "PASS_WITHIN_OVERLAP")
        self.assertEqual(result["unmatchedBinanceCount"], 1)
        self.assertEqual(result["enumerationCompleteness"], "NOT_VERIFIED")
        self.assertEqual(result["globalCompleteness"], "NOT_VERIFIED")

    def test_no_overlap_is_not_verified(self):
        result = compare_funding_observations(
            [observation(venue="BINANCE", funding_time_ms=1000)],
            [observation(venue="BINANCE", funding_time_ms=2000)],
        )

        self.assertEqual(result["observationCorroboration"], "NOT_VERIFIED_NO_OVERLAP")

    def test_different_venue_is_rejected_not_substituted(self):
        with self.assertRaisesRegex(ValueError, "FUNDING_VENUE_MISMATCH"):
            compare_funding_observations(
                [observation(venue="BINANCE")],
                [observation(venue="BYBIT")],
            )

    def test_different_contract_identity_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "FUNDING_INSTRUMENT_MISMATCH"):
            compare_funding_observations(
                [observation(venue="BINANCE")],
                [observation(venue="BINANCE", market_type="COIN_M_FUTURES")],
            )

    def test_duplicate_settlement_key_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "FUNDING_OBSERVATION_DUPLICATE"):
            compare_funding_observations(
                [observation(venue="BINANCE"), observation(venue="BINANCE")],
                [observation(venue="BINANCE")],
            )

    def test_invalid_decimal_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "FUNDING_RATE_INVALID"):
            compare_funding_observations(
                [observation(venue="BINANCE", funding_rate="NaN")],
                [observation(venue="BINANCE")],
            )

    def test_shared_collector_lineage_is_explicitly_blocked(self):
        result = compare_funding_observations(
            [observation(venue="BINANCE")],
            [observation(venue="BINANCE")],
            shared_collector_lineage=True,
        )

        self.assertEqual(result["collectorIndependence"], "BLOCKED_SHARED_COLLECTOR_LINEAGE")
        self.assertEqual(result["observationCorroboration"], "PASS_WITHIN_OVERLAP")

    def test_empty_inputs_do_not_claim_corroboration(self):
        result = compare_funding_observations([], [])

        self.assertEqual(result["observationCorroboration"], "NOT_VERIFIED_NO_OVERLAP")
        self.assertEqual(result["issuerIndependence"], "NOT_VERIFIED_SAME_ISSUER")


if __name__ == "__main__":
    unittest.main()
