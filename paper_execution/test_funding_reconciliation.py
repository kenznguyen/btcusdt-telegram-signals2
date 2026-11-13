"""D07 bounded expected-population reconciliation contract tests."""

import unittest

from paper_execution.funding_reconciliation import reconcile_funding_population


def event(event_id, at_ms, amount, digest):
    return {
        "eventId": event_id,
        "eventAtMs": at_ms,
        "amountQuote": amount,
        "payloadHash": "sha256:" + digest * 64,
    }


def population(kind, definition_id, snapshot_id, events):
    return {
        "schemaVersion": 1,
        "populationType": kind,
        "populationDefinitionId": definition_id,
        "snapshotId": snapshot_id,
        "source": snapshot_id + "-source",
        "startAtMs": 100,
        "endAtMs": 200,
        "currency": "USDT",
        "events": events,
    }


class FundingPopulationReconciliationTest(unittest.TestCase):
    def setUp(self):
        self.expected = population(
            "EXPECTED_FUNDING_EVENTS", "independent-statement-v1", "statement-001",
            [event("f-1", 120, "0.25", "a"), event("f-2", 180, "-0.10", "b")],
        )
        self.observed = population(
            "OBSERVED_FUNDING_EVENTS", "ledger-export-v1", "ledger-export-001",
            [event("f-1", 120, "0.25", "a"), event("f-2", 180, "-0.10", "b")],
        )

    def test_exact_population_match_is_complete_only_within_declared_scope(self):
        result = reconcile_funding_population(self.expected, self.observed)

        self.assertEqual(result["reconciliationStatus"], "COMPLETE_WITHIN_DECLARED_POPULATION")
        self.assertEqual(result["counts"], {
            "expected": 2, "observed": 2, "matched": 2,
            "missing": 0, "unexpected": 0, "duplicate": 0,
        })
        self.assertEqual(result["globalCompleteness"], "NOT_VERIFIED")
        self.assertEqual(result["independence"], "DECLARED_NOT_VERIFIED")
        self.assertEqual(result["freshness"], "NOT_VERIFIED")
        self.assertEqual(result["issuerAuthenticity"], "NOT_VERIFIED")

    def test_missing_expected_event_blocks_complete(self):
        self.observed["events"].pop()
        result = reconcile_funding_population(self.expected, self.observed)

        self.assertEqual(result["reconciliationStatus"], "BLOCKED")
        self.assertEqual(result["missing"], ["f-2"])

    def test_unexpected_observed_event_blocks_complete(self):
        self.observed["events"].append(event("f-3", 190, "0.01", "c"))
        result = reconcile_funding_population(self.expected, self.observed)

        self.assertEqual(result["reconciliationStatus"], "BLOCKED")
        self.assertEqual(result["unexpected"], ["f-3"])

    def test_duplicate_ids_in_expected_population_block_complete(self):
        self.expected["events"].append(event("f-1", 130, "0.5", "d"))
        result = reconcile_funding_population(self.expected, self.observed)

        self.assertEqual(result["reconciliationStatus"], "BLOCKED")
        self.assertIn("f-1", result["duplicate"])

    def test_duplicate_payload_hash_in_observed_population_blocks_complete(self):
        self.observed["events"].append(event("f-3", 190, "0.01", "a"))
        result = reconcile_funding_population(self.expected, self.observed)

        self.assertEqual(result["reconciliationStatus"], "BLOCKED")
        self.assertIn("f-3", result["duplicate"])

    def test_same_event_id_with_different_content_is_not_matched(self):
        self.observed["events"][0] = event("f-1", 120, "9.99", "c")
        result = reconcile_funding_population(self.expected, self.observed)

        self.assertEqual(result["reconciliationStatus"], "BLOCKED")
        self.assertIn("f-1", result["missing"])
        self.assertIn("f-1", result["unexpected"])

    def test_same_population_definition_cannot_claim_independent_enumeration(self):
        self.observed["populationDefinitionId"] = self.expected["populationDefinitionId"]
        with self.assertRaisesRegex(ValueError, "FUNDING_POPULATION_DEFINITION_NOT_INDEPENDENT"):
            reconcile_funding_population(self.expected, self.observed)

    def test_wrong_population_type_is_rejected(self):
        self.observed["populationType"] = "EXPECTED_FUNDING_EVENTS"
        with self.assertRaisesRegex(ValueError, "FUNDING_POPULATION_TYPE_INVALID"):
            reconcile_funding_population(self.expected, self.observed)

    def test_events_outside_half_open_scope_are_rejected(self):
        self.expected["events"].append(event("f-outside", 200, "1", "c"))
        with self.assertRaisesRegex(ValueError, "FUNDING_EVENT_OUTSIDE_SCOPE"):
            reconcile_funding_population(self.expected, self.observed)

    def test_float_amount_is_rejected_to_avoid_binary_float_money_input(self):
        self.expected["events"][0]["amountQuote"] = 0.1
        with self.assertRaisesRegex(ValueError, "FUNDING_EVENT_AMOUNT_INVALID"):
            reconcile_funding_population(self.expected, self.observed)

    def test_unknown_fields_are_rejected(self):
        self.expected["untrusted"] = True
        with self.assertRaisesRegex(ValueError, "FUNDING_POPULATION_FIELDS_INVALID"):
            reconcile_funding_population(self.expected, self.observed)

    def test_zero_event_scope_can_be_reconciled_but_not_globalized(self):
        self.expected["events"] = []
        self.observed["events"] = []
        result = reconcile_funding_population(self.expected, self.observed)

        self.assertEqual(result["reconciliationStatus"], "COMPLETE_WITHIN_DECLARED_POPULATION")
        self.assertEqual(result["globalCompleteness"], "NOT_VERIFIED")


if __name__ == "__main__":
    unittest.main()
