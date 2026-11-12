"""Isolated T1 -> T2 Order Book v1 contract tests; synthetic fixtures only."""

import copy
import threading
import unittest
from decimal import Decimal

from core_runtime.orderbook_contract import (
    OrderBookContractError,
    SnapshotSlot,
    parse_decimal,
    reanchor,
    run_after_book_validation,
    validate_snapshot,
)


NOW = 1_800_000_000_000


def levels(start, count=20, step="1"):
    return [[str(50_000 - i), step] for i in range(count)] if start == "bids" else [
        [str(50_001 + i), step] for i in range(count)
    ]


def rest_snapshot(anchor=100):
    return {
        "lastUpdateId": anchor,
        "bids": levels("bids"),
        "asks": levels("asks"),
        "sourceTimestampMs": NOW - 100,
        "observedAtMs": NOW - 90,
    }


def event(first, final, previous, *, bids=None, asks=None, observed=NOW - 20):
    return {
        "U": first, "u": final, "pu": previous,
        "b": bids or [], "a": asks or [],
        "E": NOW - 30, "observedAtMs": observed,
    }


def valid_candidate(generation=1):
    # Rebuild a complete 20x20 book from an anchor and one bridging event.
    return reanchor(
        rest_snapshot(),
        [event(101, 101, 100)],
        generation=generation,
        decision_at_ms=NOW,
    )


class DecimalContractTests(unittest.TestCase):
    def test_decimal_precision_is_preserved_without_binary_float(self):
        value = "50000.00000000000000000000000000000001"
        self.assertEqual(parse_decimal(value, positive=True), Decimal(value))
        self.assertEqual(str(parse_decimal(value, positive=True)), value)

    def test_json_number_is_rejected(self):
        for value in (50000, 50000.0):
            with self.subTest(value=value), self.assertRaises(OrderBookContractError):
                parse_decimal(value, positive=True)

    def test_noncanonical_or_nonfinite_decimal_is_rejected(self):
        for value in ("05.0", "NaN", "Infinity", "1e-8", "+1", " 1", "1."):
            with self.subTest(value=value), self.assertRaises(OrderBookContractError):
                parse_decimal(value, positive=True)

    def test_zero_quantity_is_allowed_only_for_delta_removal(self):
        self.assertEqual(parse_decimal("0", nonnegative=True), Decimal("0"))
        with self.assertRaises(OrderBookContractError):
            parse_decimal("0", positive=True)

    def test_negative_and_unbounded_decimal_are_rejected(self):
        for value in ("-1", "9" * 300):
            with self.subTest(value=value), self.assertRaises(OrderBookContractError):
                parse_decimal(value, positive=True)


class SequenceAndReanchorTests(unittest.TestCase):
    def test_anchor_bridge_and_contiguous_pu_chain_verify(self):
        events = [
            event(100, 100, 99),  # old event discarded
            event(101, 102, 100),
            event(103, 104, 102),
        ]
        result = reanchor(rest_snapshot(), events, generation=1, decision_at_ms=NOW)
        self.assertEqual(result["continuity"], "VERIFIED")
        self.assertEqual(result["snapshotLastUpdateId"], 100)
        self.assertEqual(result["firstAppliedU"], 101)
        self.assertEqual(result["lastAppliedU"], 104)
        self.assertEqual(result["decisionWatermark"], 104)

    def test_first_event_must_bridge_anchor_plus_one(self):
        with self.assertRaisesRegex(OrderBookContractError, "ANCHOR_BRIDGE_INVALID"):
            reanchor(rest_snapshot(), [event(102, 103, 100)], generation=1, decision_at_ms=NOW)

    def test_subsequent_pu_must_equal_previous_u(self):
        with self.assertRaisesRegex(OrderBookContractError, "SEQUENCE_GAP"):
            reanchor(rest_snapshot(), [
                event(101, 101, 100), event(102, 102, 99)
            ], generation=1, decision_at_ms=NOW)

    def test_old_and_duplicate_events_do_not_regress_watermark(self):
        result = reanchor(rest_snapshot(), [
            event(101, 101, 100), event(101, 101, 100),
            event(100, 100, 99), event(102, 102, 101),
        ], generation=1, decision_at_ms=NOW)
        self.assertEqual(result["lastAppliedU"], 102)

    def test_missing_bridge_fails_closed(self):
        with self.assertRaisesRegex(OrderBookContractError, "ANCHOR_BRIDGE_MISSING"):
            reanchor(rest_snapshot(), [], generation=1, decision_at_ms=NOW)

    def test_delta_updates_replace_insert_and_remove_exact_levels(self):
        result = reanchor(rest_snapshot(), [event(
            101, 101, 100,
            bids=[["50000", "0"], ["49999.5", "0.12500000000000000001"]],
            asks=[["50001.5", "2.00000000000000000001"]],
        )], generation=1, decision_at_ms=NOW)
        bid_map = dict(result["bids"])
        ask_map = dict(result["asks"])
        self.assertNotIn("50000", bid_map)
        self.assertEqual(bid_map["49999.5"], "0.12500000000000000001")
        self.assertEqual(ask_map["50001.5"], "2.00000000000000000001")

    def test_malformed_delta_discards_candidate(self):
        with self.assertRaises(OrderBookContractError):
            reanchor(rest_snapshot(), [event(101, 101, 100, bids=[[50000, "1"]])],
                     generation=1, decision_at_ms=NOW)


class SnapshotAcceptanceTests(unittest.TestCase):
    def test_reanchor_publishes_complete_immutable_contract(self):
        result = valid_candidate()
        accepted = validate_snapshot(result, decision_at_ms=NOW)
        self.assertEqual(accepted["depth"], {"bids": 20, "asks": 20})
        self.assertTrue(accepted["complete"])
        self.assertEqual(accepted["freshness"], "FRESH")

    def test_depth_below_twenty_on_either_side_is_rejected(self):
        result = valid_candidate()
        result["bids"] = result["bids"][:-1]
        result["depth"]["bids"] = 19
        with self.assertRaisesRegex(OrderBookContractError, "DEPTH_INVALID"):
            validate_snapshot(result, decision_at_ms=NOW)

    def test_crossed_or_locked_book_is_rejected(self):
        result = valid_candidate()
        result["asks"][0] = ["50000", "1"]
        with self.assertRaisesRegex(OrderBookContractError, "SPREAD_INVALID"):
            validate_snapshot(result, decision_at_ms=NOW)

    def test_source_and_observation_freshness_are_both_enforced(self):
        result = valid_candidate()
        result["sourceTimestampMs"] = NOW - 2_001
        with self.assertRaisesRegex(OrderBookContractError, "SOURCE_STALE"):
            validate_snapshot(result, decision_at_ms=NOW)
        result = valid_candidate()
        result["observedAtMs"] = NOW - 2_001
        with self.assertRaisesRegex(OrderBookContractError, "OBSERVATION_STALE"):
            validate_snapshot(result, decision_at_ms=NOW)

    def test_future_skew_over_250ms_is_rejected(self):
        result = valid_candidate()
        result["sourceTimestampMs"] = NOW + 251
        with self.assertRaisesRegex(OrderBookContractError, "TIMESTAMP_FUTURE"):
            validate_snapshot(result, decision_at_ms=NOW)

    def test_watermark_and_generation_identity_are_mandatory(self):
        result = valid_candidate()
        result["decisionWatermark"] += 1
        with self.assertRaisesRegex(OrderBookContractError, "WATERMARK_MISMATCH"):
            validate_snapshot(result, decision_at_ms=NOW)
        result = valid_candidate()
        result["generation"] = 0
        with self.assertRaises(OrderBookContractError):
            validate_snapshot(result, decision_at_ms=NOW)

    def test_unknown_partial_or_wrong_market_contract_is_rejected(self):
        for mutate in (
            lambda x: x.update(complete=False),
            lambda x: x.update(continuity="BROKEN"),
            lambda x: x.update(contractVersion="T1_T2_ORDERBOOK_V2"),
            lambda x: x.update(symbol="ETHUSDT"),
        ):
            result = valid_candidate()
            mutate(result)
            with self.assertRaises(OrderBookContractError):
                validate_snapshot(result, decision_at_ms=NOW)


class FencingAndAtomicPublicationTests(unittest.TestCase):
    def test_reconnect_invalidates_old_generation_and_requires_next_generation(self):
        slot = SnapshotSlot()
        first = valid_candidate(generation=1)
        slot.publish(first, decision_at_ms=NOW)
        slot.invalidate("RECONNECT")
        self.assertIsNone(slot.read())
        with self.assertRaisesRegex(OrderBookContractError, "GENERATION_FENCED"):
            slot.publish(first, decision_at_ms=NOW)
        second = valid_candidate(generation=2)
        slot.publish(second, decision_at_ms=NOW)
        self.assertEqual(slot.read()["generation"], 2)

    def test_generation_must_increase_monotonically(self):
        slot = SnapshotSlot()
        slot.publish(valid_candidate(generation=1), decision_at_ms=NOW)
        with self.assertRaisesRegex(OrderBookContractError, "GENERATION_FENCED"):
            slot.publish(valid_candidate(generation=1), decision_at_ms=NOW)

    def test_readers_observe_only_whole_old_or_new_snapshot(self):
        slot = SnapshotSlot()
        slot.publish(valid_candidate(generation=1), decision_at_ms=NOW)
        seen = []
        barrier = threading.Barrier(2)

        def reader():
            barrier.wait()
            for _ in range(500):
                value = slot.read()
                if value is not None:
                    seen.append((value["generation"], value["decisionWatermark"],
                                 len(value["bids"]), len(value["asks"])))

        thread = threading.Thread(target=reader)
        thread.start()
        barrier.wait()
        slot.publish(valid_candidate(generation=2), decision_at_ms=NOW)
        thread.join()
        self.assertTrue(seen)
        self.assertTrue(all(row in ((1, 101, 20, 20), (2, 101, 20, 20)) for row in seen))

    def test_failed_reanchor_never_publishes_a_partial_candidate(self):
        slot = SnapshotSlot()
        slot.publish(valid_candidate(generation=1), decision_at_ms=NOW)
        slot.invalidate("SEQUENCE_GAP")
        with self.assertRaises(OrderBookContractError):
            reanchor(rest_snapshot(), [event(102, 103, 100)],
                     generation=2, decision_at_ms=NOW)
        self.assertIsNone(slot.read())


class FailClosedSideEffectTests(unittest.TestCase):
    def test_invalid_snapshot_cannot_invoke_producer_ledger_or_risk_admission(self):
        calls = {"producer": 0, "ledger": 0, "risk": 0}

        def callback(name):
            def invoke(*args, **kwargs):
                calls[name] += 1
                return name
            return invoke

        invalid = valid_candidate()
        invalid["continuity"] = "BROKEN"
        with self.assertRaises(OrderBookContractError):
            run_after_book_validation(
                invalid, decision_at_ms=NOW,
                producer=callback("producer"),
                paper_ledger=callback("ledger"),
                shared_risk_engine=callback("risk"),
            )
        self.assertEqual(calls, {"producer": 0, "ledger": 0, "risk": 0})

    def test_stale_snapshot_cannot_invoke_any_downstream_callback(self):
        calls = []
        stale = valid_candidate()
        stale["observedAtMs"] = NOW - 2_001
        callback = lambda *_: calls.append("called")
        with self.assertRaises(OrderBookContractError):
            run_after_book_validation(stale, decision_at_ms=NOW,
                producer=callback, paper_ledger=callback, shared_risk_engine=callback)
        self.assertEqual(calls, [])

    def test_valid_snapshot_crosses_validation_gate_once_in_order(self):
        calls = []
        def producer(book):
            calls.append("producer")
            return {"intent": "paper-only"}
        def ledger(intent, book):
            calls.append("ledger")
            return "PAPER_SUBMITTED"
        def risk(result):
            calls.append("risk")
            return "RISK_ADMISSION_CHECKED"
        result = run_after_book_validation(valid_candidate(), decision_at_ms=NOW,
            producer=producer, paper_ledger=ledger, shared_risk_engine=risk)
        self.assertEqual(result, "RISK_ADMISSION_CHECKED")
        self.assertEqual(calls, ["producer", "ledger", "risk"])


if __name__ == "__main__":
    unittest.main()
