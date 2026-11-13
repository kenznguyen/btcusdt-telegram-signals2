"""D07 PAPER funding-model contract tests (TDD-first)."""

import unittest

from paper_execution.funding_model import build_expected_funding_population


START = 1_800_000_000_000
SETTLEMENT = START + 10_000
END = SETTLEMENT + 1


def position(strategy, quantity, *, observed=SETTLEMENT, snapshot=None):
    return {
        "snapshotId": snapshot or f"position-{strategy}-{observed}",
        "strategyId": strategy,
        "symbol": "BTCUSDT",
        "observedAtMs": observed,
        "positionBase": quantity,
    }


def rate(*, at=SETTLEMENT, value="0.001", mark="100", event_id="rate-001"):
    return {
        "eventId": event_id,
        "symbol": "BTCUSDT",
        "fundingTimeMs": at,
        "fundingRate": value,
        "markPrice": mark,
        "sourceSnapshotId": f"public-rate-{event_id}",
    }


def positions(at=SETTLEMENT, core="1", ai="-2", legacy="0"):
    return [
        position("STRATEGY_CORE", core, observed=at),
        position("AI_FREQAI", ai, observed=at),
        position("LEGACY_UNATTRIBUTED", legacy, observed=at),
    ]


class PaperFundingModelTest(unittest.TestCase):
    def build(self, position_rows=None, rate_rows=None, **kwargs):
        return build_expected_funding_population(
            start_at_ms=START,
            end_at_ms=END,
            position_snapshots=positions() if position_rows is None else position_rows,
            funding_rate_events=[rate()] if rate_rows is None else rate_rows,
            **kwargs,
        )

    def test_long_pays_positive_rate_and_short_receives_it(self):
        result = self.build()
        events = {event["eventId"]: event for event in result["events"]}

        self.assertEqual(len(events), 2)
        amounts = sorted(event["amountQuote"] for event in events.values())
        self.assertEqual(amounts, ["-0.2", "0.1"])
        self.assertTrue(all(event["eventAtMs"] == SETTLEMENT for event in events.values()))
        self.assertTrue(all(event["payloadHash"].startswith("sha256:") for event in events.values()))

    def test_negative_funding_rate_reverses_cashflow_sign(self):
        result = self.build(rate_rows=[rate(value="-0.002")])
        self.assertEqual(
            sorted(event["amountQuote"] for event in result["events"]),
            ["-0.1", "0.4"],
        )

    def test_zero_position_does_not_create_funding_event(self):
        result = self.build(position_rows=positions(core="0", ai="0", legacy="0"))
        self.assertEqual(result["events"], [])

    def test_latest_position_snapshot_at_or_before_settlement_is_selected(self):
        rows = [
            position("STRATEGY_CORE", "1", observed=SETTLEMENT - 5_000, snapshot="core-old"),
            position("STRATEGY_CORE", "2", observed=SETTLEMENT, snapshot="core-current"),
            position("AI_FREQAI", "-1", observed=SETTLEMENT, snapshot="ai-current"),
            position("LEGACY_UNATTRIBUTED", "0", observed=SETTLEMENT, snapshot="legacy-current"),
        ]
        result = self.build(position_rows=rows)
        self.assertEqual(
            [event["amountQuote"] for event in result["events"]],
            ["0.2", "-0.1"],
        )

    def test_future_position_snapshot_is_never_used(self):
        rows = positions()
        rows[0] = position("STRATEGY_CORE", "9", observed=SETTLEMENT + 1)
        with self.assertRaisesRegex(ValueError, "FUNDING_POSITION_SNAPSHOT_MISSING"):
            self.build(position_rows=rows)

    def test_missing_strategy_position_snapshot_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "FUNDING_POSITION_SNAPSHOT_MISSING"):
            self.build(position_rows=positions()[:-1])

    def test_stale_position_snapshot_fails_closed(self):
        rows = positions(at=SETTLEMENT - 60_001)
        with self.assertRaisesRegex(ValueError, "FUNDING_POSITION_SNAPSHOT_STALE"):
            self.build(position_rows=rows)

    def test_duplicate_strategy_snapshot_at_same_time_is_rejected(self):
        rows = positions() + [position("STRATEGY_CORE", "3")]
        with self.assertRaisesRegex(ValueError, "FUNDING_POSITION_SNAPSHOT_DUPLICATE"):
            self.build(position_rows=rows)

    def test_duplicate_market_funding_event_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "FUNDING_RATE_EVENT_DUPLICATE"):
            self.build(rate_rows=[rate(), rate()])

    def test_funding_event_outside_half_open_scope_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "FUNDING_RATE_EVENT_OUTSIDE_SCOPE"):
            self.build(rate_rows=[rate(at=END)])

    def test_market_symbol_mismatch_is_rejected(self):
        row = rate()
        row["symbol"] = "ETHUSDT"
        with self.assertRaisesRegex(ValueError, "FUNDING_RATE_EVENT_SYMBOL_INVALID"):
            self.build(rate_rows=[row])

    def test_binary_float_money_and_rate_inputs_are_rejected(self):
        row = rate()
        row["fundingRate"] = 0.001
        with self.assertRaisesRegex(ValueError, "FUNDING_RATE_VALUE_INVALID"):
            self.build(rate_rows=[row])

    def test_non_finite_and_non_positive_mark_price_are_rejected(self):
        for mark in ("NaN", "Infinity", "0", "-1"):
            with self.subTest(mark=mark):
                with self.assertRaisesRegex(ValueError, "FUNDING_MARK_PRICE_INVALID"):
                    self.build(rate_rows=[rate(mark=mark)])

    def test_unknown_input_fields_are_rejected(self):
        row = position("STRATEGY_CORE", "1")
        row["untrusted"] = True
        with self.assertRaisesRegex(ValueError, "FUNDING_POSITION_SNAPSHOT_FIELDS_INVALID"):
            self.build(position_rows=[row] + positions()[1:])

    def test_output_is_deterministic_when_input_order_changes(self):
        rows = positions()
        first = self.build(position_rows=rows, rate_rows=[rate()])
        second = self.build(
            position_rows=list(reversed(rows)),
            rate_rows=[rate()],
        )
        self.assertEqual(first, second)

    def test_population_matches_d07_expected_population_contract(self):
        result = self.build()
        self.assertEqual(result["schemaVersion"], 1)
        self.assertEqual(result["populationType"], "EXPECTED_FUNDING_EVENTS")
        self.assertEqual(result["populationDefinitionId"], "paper-linear-funding-v1")
        self.assertEqual(result["startAtMs"], START)
        self.assertEqual(result["endAtMs"], END)
        self.assertEqual(result["currency"], "USDT")
        self.assertEqual(
            set(result["events"][0]),
            {"eventId", "eventAtMs", "amountQuote", "payloadHash"},
        )
        self.assertTrue(result["snapshotId"].startswith("sha256:"))
        self.assertEqual(result["source"], "paper_simulation:linear_usdt_perpetual")


if __name__ == "__main__":
    unittest.main()
