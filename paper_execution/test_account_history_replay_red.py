"""RED contract for deterministic per-ledger event replay (PAPER only)."""
import unittest

from paper_execution.account_history import replay_ledger_events


class DeterministicLedgerReplayContractTest(unittest.TestCase):
    def setUp(self):
        self.snapshot = {
            "position_base": "0",
            "average_entry_price": "0",
            "realized_pnl_quote": "0",
            "fees_quote": "0",
            "funding_quote": "0",
        }

    def event(self, event_id, at, quantity, price, fee):
        return {
            "event_id": event_id,
            "event_type": "FILL",
            "event_at_ms": at,
            "quantity_delta_base": quantity,
            "fill_price": price,
            "fee_quote": fee,
            "fee_currency": "USDT",
        }

    def test_replay_sorts_by_event_time_and_handles_partial_fills_reduction_and_reversal(self):
        # Deliberately pass rows out of insertion/time order.
        events = [
            self.event("sell-reverse", 40, "-2", "90", "0.20"),
            self.event("buy-second", 20, "1", "110", "0.10"),
            self.event("sell-reduce", 30, "-0.5", "120", "0.05"),
            self.event("buy-first", 10, "1", "100", "0.10"),
        ]
        result = replay_ledger_events(
            self.snapshot, events, [], boundary_ms=50
        )
        self.assertEqual(result["position_base"], "-0.5")
        self.assertEqual(result["average_entry_price"], "90")
        self.assertEqual(result["realized_pnl_quote"], "-22.5")
        self.assertEqual(result["fees_quote"], "0.45")
        self.assertEqual(
            result["included_event_ids"],
            ["buy-first", "buy-second", "sell-reduce", "sell-reverse"],
        )

    def test_funding_event_exactly_at_utc_boundary_belongs_to_new_day(self):
        funding = [
            {"funding_event_id": "before-boundary", "event_at_ms": 99,
             "amount_quote": "0.25"},
            {"funding_event_id": "at-boundary", "event_at_ms": 100,
             "amount_quote": "9.00"},
        ]
        result = replay_ledger_events(
            self.snapshot, [], funding, boundary_ms=100
        )
        self.assertEqual(result["funding_quote"], "0.25")
        self.assertEqual(result["included_funding_event_ids"], ["before-boundary"])

    def test_unknown_historical_fee_currency_fails_closed(self):
        event = self.event("unknown-fee", 10, "1", "100", "0")
        event["fee_currency"] = None
        with self.assertRaisesRegex(ValueError, "ACCOUNT_HISTORY_FEE_PROVENANCE_UNKNOWN"):
            replay_ledger_events(self.snapshot, [event], [], boundary_ms=20)

    def test_same_timestamp_events_have_stable_event_id_order(self):
        events = [
            self.event("z-buy", 10, "1", "100", "0"),
            self.event("a-buy", 10, "1", "110", "0"),
        ]
        result = replay_ledger_events(
            self.snapshot, events, [], boundary_ms=20
        )
        self.assertEqual(result["included_event_ids"], ["a-buy", "z-buy"])
        self.assertEqual(result["average_entry_price"], "105")
