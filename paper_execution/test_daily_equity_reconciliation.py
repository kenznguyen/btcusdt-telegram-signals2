"""Pure daily equity replay orchestration and reconciliation contract (PAPER only)."""
import unittest

from paper_execution.replay_reconciliation import reconcile_daily_equity_replay


class DailyEquityReplayReconciliationContractTest(unittest.TestCase):
    def setUp(self):
        self.boundary = 1_700_006_400_000
        self.snapshot_at = 1_700_000_000_000
        self.cutover = {
            "initial_capital_quote": "1000",
            "account_equity_quote": "1000",
            "mark_price": "100",
            "mark_candle_close_ms": self.snapshot_at,
            "reconciled_realized_pnl_quote": "0",
            "reconciled_fees_quote": "0",
            "reconciled_funding_quote": "0",
            "expected_account_equity_quote": "1000",
        }
        empty_snapshot = {
            "position_base": "0",
            "average_entry_price": "0",
            "realized_pnl_quote": "0",
            "fees_quote": "0",
            "funding_quote": "0",
            "snapshot_at_ms": self.snapshot_at,
        }
        self.inputs = {
            "utc_day_ms": self.boundary,
            "cutover_id": "cutover-1",
            "cutover_snapshot_at_ms": self.snapshot_at,
            "cutover": dict(self.cutover),
            "ledgers": {
                "STRATEGY_CORE": {
                    "snapshot": dict(empty_snapshot),
                    "execution_events": [{
                        "event_id": "core-buy",
                        "event_type": "FILL",
                        "event_at_ms": self.snapshot_at + 10,
                        "recorded_at_ms": self.snapshot_at + 20,
                        "quantity_delta_base": "1",
                        "fill_price": "100",
                        "fee_quote": "1",
                        "fee_currency": "USDT",
                    }],
                    "funding_events": [{
                        "funding_event_id": "core-funding",
                        "event_at_ms": self.snapshot_at + 30,
                        "recorded_at_ms": self.snapshot_at + 40,
                        "amount_quote": "2",
                    }],
                    "coverage_watermark_at_ms": self.boundary + 1000,
                },
                "AI_FREQAI": {
                    "snapshot": dict(empty_snapshot),
                    "execution_events": [],
                    "funding_events": [],
                    "coverage_watermark_at_ms": self.boundary + 1000,
                },
                "LEGACY_UNATTRIBUTED": {
                    "snapshot": dict(empty_snapshot),
                    "execution_events": [],
                    "funding_events": [],
                    "coverage_watermark_at_ms": self.boundary + 1000,
                },
            },
            "market_mark": {
                "mark_id": "boundary-mark",
                "effective_at_ms": self.boundary,
                "candle_close_ms": self.boundary,
                "mark_price": "110",
                "quality_status": "VERIFIED",
            },
        }

    def test_replays_each_ledger_and_reconciles_cutover_and_boundary_equity(self):
        result = reconcile_daily_equity_replay(self.inputs)
        self.assertEqual(result["boundary_ms"], self.boundary)
        self.assertEqual(result["cutover_id"], "cutover-1")
        self.assertEqual(result["ledgers"]["STRATEGY_CORE"]["position_base"], "1")
        self.assertEqual(result["ledgers"]["STRATEGY_CORE"]["realized_pnl_quote"], "0")
        self.assertEqual(result["ledgers"]["STRATEGY_CORE"]["unrealized_pnl_quote"], "10")
        self.assertEqual(result["ledgers"]["STRATEGY_CORE"]["fees_quote"], "1")
        self.assertEqual(result["ledgers"]["STRATEGY_CORE"]["funding_quote"], "2")
        self.assertEqual(result["equity_quote"], "1007")
        self.assertEqual(result["realized_pnl_quote"], "0")
        self.assertEqual(result["unrealized_pnl_quote"], "10")
        self.assertEqual(result["fees_quote"], "1")
        self.assertEqual(result["funding_quote"], "2")

    def test_rejects_cutover_equity_that_does_not_reconcile_to_ledger_snapshots(self):
        self.inputs["cutover"]["account_equity_quote"] = "999"
        with self.assertRaisesRegex(ValueError, "ACCOUNT_EQUITY_CUTOVER_RECONCILIATION_MISMATCH"):
            reconcile_daily_equity_replay(self.inputs)

    def test_rejects_cutover_aggregate_totals_that_do_not_match_ledgers(self):
        self.inputs["cutover"]["reconciled_fees_quote"] = "0.01"
        with self.assertRaisesRegex(ValueError, "ACCOUNT_EQUITY_CUTOVER_RECONCILIATION_MISMATCH"):
            reconcile_daily_equity_replay(self.inputs)

    def test_rejects_missing_or_extra_ledger(self):
        del self.inputs["ledgers"]["LEGACY_UNATTRIBUTED"]
        with self.assertRaisesRegex(ValueError, "ACCOUNT_HISTORY_CUTOVER_LEDGER_SET_INVALID"):
            reconcile_daily_equity_replay(self.inputs)

    def test_rejects_boundary_mark_not_at_exact_utc_boundary(self):
        self.inputs["market_mark"]["effective_at_ms"] -= 1
        with self.assertRaisesRegex(ValueError, "ACCOUNT_HISTORY_BOUNDARY_MARK_INVALID"):
            reconcile_daily_equity_replay(self.inputs)

    def test_rejects_non_verified_boundary_mark(self):
        self.inputs["market_mark"]["quality_status"] = "UNKNOWN"
        with self.assertRaisesRegex(ValueError, "ACCOUNT_HISTORY_BOUNDARY_MARK_INVALID"):
            reconcile_daily_equity_replay(self.inputs)

    def test_rejects_unknown_legacy_fee_instead_of_assuming_zero(self):
        self.inputs["ledgers"]["LEGACY_UNATTRIBUTED"]["execution_events"] = [{
            "event_id": "legacy-unknown-fee",
            "event_type": "FILL",
            "event_at_ms": self.snapshot_at + 10,
            "recorded_at_ms": self.snapshot_at + 20,
            "quantity_delta_base": "1",
            "fill_price": "100",
            "fee_quote": "0",
            "fee_currency": None,
        }]
        with self.assertRaisesRegex(ValueError, "ACCOUNT_HISTORY_FEE_PROVENANCE_UNKNOWN"):
            reconcile_daily_equity_replay(self.inputs)

    def test_does_not_mutate_loader_input(self):
        import copy
        original = copy.deepcopy(self.inputs)
        reconcile_daily_equity_replay(self.inputs)
        self.assertEqual(self.inputs, original)


if __name__ == "__main__":
    unittest.main()
