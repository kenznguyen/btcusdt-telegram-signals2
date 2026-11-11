import copy
import unittest
from pipeline.lifecycle_disposition import evaluate_disposition


def record(**changes):
    value = {
        "identity_verified": True, "object_id": "synthetic-1", "version_id": "v1",
        "namespace": "run-1", "data_class": "T4_DETERMINISTIC_CACHE",
        "steward": "owner-1", "policy_id": "RET-01", "policy_version": "B",
        "integrity": {"algorithm": "sha256", "digest": "a"*64, "byte_length": 12},
        "lineage": {"complete": True, "source_object_id": "s1", "source_version_id": "v1", "transform_id": "t1"},
        "dependencies": {"complete": True, "items": []},
        "holds": {"complete": True, "items": []}, "copies": {"complete": True, "items": []},
        "process_state": "INACTIVE", "rebuildability": {"required": True, "proven": True, "evidence_ref": "proof-1"},
        "material_decision_use": "NO", "evidence_revision": "r1",
        "review_group": "T4_DETERMINISTIC_CACHE", "storage_pressure": True,
        "consumer_ack": True, "heartbeat_lost": True,
    }
    value.update(changes)
    if "sensitivity" not in changes:
        kind = value["data_class"]
        minimums = {
            "T0_CANONICAL": "RESTRICTED",
            "CORE_LEDGER": "RESTRICTED",
            "AI_LEDGER": "RESTRICTED",
            "T3_PROTECTED_EVIDENCE": "RESTRICTED",
            "GOVERNANCE_EVIDENCE": "RESTRICTED",
            "T4_DETERMINISTIC_CACHE": "INTERNAL",
            "T2_EPHEMERAL_INFERENCE_OUTPUT": "CONFIDENTIAL",
            "T1_RAW_OBSERVATION": "CONFIDENTIAL",
            "NONCANONICAL_COPY": "CONFIDENTIAL",
        }
        label = minimums.get(kind, "PUBLIC")
        sensitivity = {
            "state": "CLASSIFIED", "label": label,
            "evidence_ref": "synthetic-sensitivity-evidence",
            "evidence_revision": "sensitivity-r1",
        }
        if kind == "NONCANONICAL_COPY":
            sensitivity["inherited_labels"] = ["CONFIDENTIAL"]
        value["sensitivity"] = sensitivity
    return value


class LifecycleDispositionTests(unittest.TestCase):
    def test_reviewable_noncanonical_requires_complete_positive_evidence(self):
        out = evaluate_disposition(record())
        self.assertEqual(out["disposition"], "REVIEWABLE_NONCANONICAL")
        self.assertIn("REV_REBUILDABILITY_PROVEN", out["reason_codes"])

    def test_protected_classes_win_over_unrelated_missing_metadata(self):
        cases = {"T0_CANONICAL":"PROT_CLASS_T0_CANONICAL",
                 "CORE_LEDGER":"PROT_CLASS_CORE_LEDGER", "AI_LEDGER":"PROT_CLASS_AI_LEDGER",
                 "T3_PROTECTED_EVIDENCE":"PROT_CLASS_T3_EVIDENCE",
                 "GOVERNANCE_EVIDENCE":"PROT_CLASS_GOVERNANCE_EVIDENCE"}
        for kind, code in cases.items():
            with self.subTest(kind=kind):
                out = evaluate_disposition(record(data_class=kind, steward=None, integrity=None))
                self.assertEqual(out["disposition"], "PROTECTED")
                self.assertIn(code, out["reason_codes"])

    def test_binding_preservation_hold_is_protected(self):
        out = evaluate_disposition(record(holds={"complete":True,"items":[{
            "hold_id":"h1","owner":"owner","status":"ACTIVE","binding":True}]}))
        self.assertEqual(out["disposition"], "PROTECTED")
        self.assertIn("PROT_BINDING_HOLD_ACTIVE", out["reason_codes"])

    def test_unverifiable_hold_blocks(self):
        out = evaluate_disposition(record(holds={"complete":False,"items":[]}))
        self.assertEqual(out["disposition"], "BLOCKED_UNKNOWN")
        self.assertIn("UNK_HOLD_STATE", out["reason_codes"])

    def test_unknown_identity_class_owner_policy_and_integrity_block(self):
        changes = [
            ({"identity_verified":False}, "UNK_OBJECT_IDENTITY"),
            ({"data_class":"UNKNOWN"}, "UNK_CLASSIFICATION"),
            ({"steward":None}, "UNK_STEWARD_OWNER"),
            ({"policy_id":"UNKNOWN"}, "UNK_POLICY_REFERENCE"),
            ({"integrity":None}, "UNK_INTEGRITY_METADATA"),
            ({"integrity":{"algorithm":"sha256","digest":"bad","byte_length":-1}}, "UNK_INTEGRITY_MISMATCH"),
        ]
        for values, code in changes:
            with self.subTest(code=code):
                out = evaluate_disposition(record(**values))
                self.assertEqual(out["disposition"], "BLOCKED_UNKNOWN")
                self.assertIn(code, out["reason_codes"])

    def test_incomplete_lineage_registry_or_copy_inventory_blocks(self):
        changes = [
            ({"lineage":{"complete":False}}, "UNK_SOURCE_LINEAGE"),
            ({"dependencies":{"complete":False,"items":[]}}, "UNK_DEPENDENCY_REGISTRY"),
            ({"copies":{"complete":True,"items":[{"copy_id":"x"}]}}, "UNK_COPY_LINEAGE"),
        ]
        for values, code in changes:
            with self.subTest(code=code):
                out = evaluate_disposition(record(**values))
                self.assertEqual(out["disposition"], "BLOCKED_UNKNOWN")
                self.assertIn(code, out["reason_codes"])

    def test_known_open_dependency_retains_and_unknown_registry_blocks(self):
        out = evaluate_disposition(record(dependencies={"complete":True,"items":[{
            "dependency_id":"c1","state":"ACTIVE","obligation_type":"CONSUMER"}]}))
        self.assertEqual(out["disposition"], "RETAIN_UNTIL_OBLIGATIONS_CLOSE")
        self.assertIn("RET_DEPENDENCY_ACTIVE", out["reason_codes"])

    def test_open_special_obligations_retain(self):
        for kind, code in (("REPLAY_RECOVERY","RET_REPLAY_RECOVERY_OPEN"),
                           ("MODEL_REPRODUCTION","RET_MODEL_REPRODUCTION_OPEN"),
                           ("VALIDATION_REPROCESS","RET_VALIDATION_REPROCESS_OPEN")):
            out = evaluate_disposition(record(dependencies={"complete":True,"items":[{
                "dependency_id":"o1","state":"OPEN","obligation_type":kind}]}))
            self.assertEqual(out["disposition"], "RETAIN_UNTIL_OBLIGATIONS_CLOSE")
            self.assertIn(code, out["reason_codes"])

    def test_active_or_unknown_process_is_never_reviewable(self):
        active = evaluate_disposition(record(process_state="ACTIVE"))
        unknown = evaluate_disposition(record(process_state="UNKNOWN"))
        self.assertEqual(active["disposition"], "RETAIN_UNTIL_OBLIGATIONS_CLOSE")
        self.assertEqual(unknown["disposition"], "BLOCKED_UNKNOWN")

    def test_missing_rebuildability_proof_blocks(self):
        out = evaluate_disposition(record(rebuildability={"required":True,"proven":False}))
        self.assertEqual(out["disposition"], "BLOCKED_UNKNOWN")
        self.assertIn("UNK_REBUILDABILITY_PROOF", out["reason_codes"])

    def test_t2_material_use_retains_and_unknown_use_blocks(self):
        base = {"data_class":"T2_EPHEMERAL_INFERENCE_OUTPUT","review_group":"T2_EPHEMERAL_INFERENCE_OUTPUT"}
        yes = evaluate_disposition(record(**base, material_decision_use="YES"))
        unknown = evaluate_disposition(record(**base, material_decision_use="UNKNOWN"))
        no = evaluate_disposition(record(**base))
        self.assertEqual(yes["disposition"], "RETAIN_UNTIL_OBLIGATIONS_CLOSE")
        self.assertEqual(unknown["disposition"], "BLOCKED_UNKNOWN")
        self.assertEqual(no["disposition"], "REVIEWABLE_NONCANONICAL")
        self.assertIn("REV_NON_MATERIAL_USE_PROVEN", no["reason_codes"])

    def test_exact_copy_is_scoped_and_requires_full_lineage(self):
        base = {"data_class":"NONCANONICAL_COPY","review_group":"NONCANONICAL_COPY","object_kind":"COPY"}
        base["object_id"] = "c1"
        good = evaluate_disposition(record(**base, copy_lineage={"complete":True,"copy_id":"c1",
            "source_object_id":"s1","source_version_id":"v1"},
            copies={"complete":True,"items":[{"copy_id":"c1","version_id":"v1",
                "kind":"NONCANONICAL_COPY","state":"PRESENT"}]}))
        bad = evaluate_disposition(record(**base, copy_lineage={"complete":False}))
        self.assertEqual(good["disposition"], "COPY_SPECIFIC_REVIEW")
        self.assertEqual(bad["disposition"], "BLOCKED_UNKNOWN")

    def test_t1_is_not_reviewable_without_rebuildability_proof(self):
        out = evaluate_disposition(record(data_class="T1_RAW_OBSERVATION",
            review_group="T1_RAW_OBSERVATION",
            rebuildability={"required":True,"proven":False}))
        self.assertEqual(out["disposition"], "BLOCKED_UNKNOWN")

    def test_t1_cannot_disable_rebuildability_or_omit_producer_provenance(self):
        base = {"data_class":"T1_RAW_OBSERVATION","review_group":"T1_RAW_OBSERVATION",
                "rebuildability":{"required":False,"proven":False}}
        missing_provenance = evaluate_disposition(record(**base))
        verified_values = dict(base)
        verified_values.update(rebuildability={"required":True,"proven":True,"evidence_ref":"rebuild-proof"},
                               producer_provenance_verified=True)
        verified = evaluate_disposition(record(**verified_values))
        self.assertEqual(missing_provenance["disposition"], "BLOCKED_UNKNOWN")
        self.assertIn("UNK_SOURCE_LINEAGE", missing_provenance["reason_codes"])
        self.assertEqual(verified["disposition"], "REVIEWABLE_NONCANONICAL")

    def test_ack_heartbeat_and_storage_pressure_do_not_change_disposition(self):
        a = evaluate_disposition(record())
        b = evaluate_disposition(record(storage_pressure=False, consumer_ack=False, heartbeat_lost=False))
        self.assertEqual(a, b)

    def test_input_immutable_and_output_has_no_execution_authority(self):
        source = record()
        before = copy.deepcopy(source)
        out = evaluate_disposition(source)
        self.assertEqual(source, before)
        self.assertIs(out["mutation_performed"], False)
        self.assertIs(out["execution_authorized"], False)
        self.assertNotIn("command", out)
        self.assertNotIn("path", out)

    def test_repeated_evaluation_is_deterministic_and_codes_sorted(self):
        source = record(steward=None, policy_version=None)
        a, b = evaluate_disposition(source), evaluate_disposition(source)
        self.assertEqual(a, b)
        self.assertEqual(a["reason_codes"], sorted(a["reason_codes"]))

    def test_unhashable_or_wrong_type_enum_values_fail_closed(self):
        cases = [
            ({"data_class": []}, "UNK_CLASSIFICATION"),
            ({"policy_id": []}, "UNK_POLICY_REFERENCE"),
            ({"process_state": []}, "UNK_PROCESS_STATE"),
            ({"material_decision_use": []}, "UNK_MATERIAL_USE_STATUS"),
            ({"review_group": []}, "UNK_CLASSIFICATION"),
            ({"dependencies": {"complete": True, "items": [
                {"dependency_id": "d1", "state": [], "obligation_type": "CONSUMER"}]}},
             "UNK_DEPENDENCY_REGISTRY"),
        ]
        for changes, code in cases:
            with self.subTest(code=code):
                out = evaluate_disposition(record(**changes))
                self.assertEqual(out["disposition"], "BLOCKED_UNKNOWN")
                self.assertIn(code, out["reason_codes"])

    def test_malformed_obligation_type_is_retained_conservatively(self):
        out = evaluate_disposition(record(dependencies={"complete": True, "items": [
            {"dependency_id": "d1", "state": "ACTIVE", "obligation_type": []}
        ]}))
        self.assertEqual(out["disposition"], "RETAIN_UNTIL_OBLIGATIONS_CLOSE")
        self.assertIn("RET_DEPENDENCY_ACTIVE", out["reason_codes"])

    def test_copy_inventory_unhashable_state_fails_closed(self):
        base = {"data_class":"NONCANONICAL_COPY", "review_group":"NONCANONICAL_COPY",
                "object_kind":"COPY", "object_id":"copy-1",
                "copy_lineage":{"complete":True,"copy_id":"copy-1",
                    "source_object_id":"s1","source_version_id":"v1"},
                "copies":{"complete":True,"items":[{"copy_id":"copy-1",
                    "version_id":"v1","kind":"NONCANONICAL_COPY","state":[]} ]}}
        out = evaluate_disposition(record(**base))
        self.assertEqual(out["disposition"], "BLOCKED_UNKNOWN")
        self.assertIn("UNK_COPY_LINEAGE", out["reason_codes"])

    def test_copy_review_requires_one_exact_inventory_match(self):
        base = {"data_class":"NONCANONICAL_COPY", "review_group":"NONCANONICAL_COPY",
                "object_kind":"COPY", "object_id":"copy-1",
                "copy_lineage":{"complete":True,"copy_id":"copy-1",
                    "source_object_id":"s1","source_version_id":"v1"}}
        exact = {"complete":True,"items":[{"copy_id":"copy-1","version_id":"v1",
            "kind":"NONCANONICAL_COPY","state":"PRESENT"}]}
        cases = [
            ({"complete":True,"items":[]}),
            ({"complete":True,"items":[{"copy_id":"copy-1","version_id":"v2",
                "kind":"NONCANONICAL_COPY","state":"PRESENT"}]}),
            ({"complete":True,"items":[exact["items"][0], exact["items"][0]]}),
        ]
        self.assertEqual(evaluate_disposition(record(**base, copies=exact))["disposition"],
                         "COPY_SPECIFIC_REVIEW")
        for inventory in cases:
            with self.subTest(inventory=inventory):
                out = evaluate_disposition(record(**base, copies=inventory))
                self.assertEqual(out["disposition"], "BLOCKED_UNKNOWN")
                self.assertIn("UNK_COPY_LINEAGE", out["reason_codes"])

    def test_protected_precedence_still_reports_all_unknown_metadata(self):
        out = evaluate_disposition(record(data_class="T0_CANONICAL", holds=None,
            lineage=None, dependencies=None, copies=None, process_state=None))
        self.assertEqual(out["disposition"], "PROTECTED")
        for code in ("PROT_CLASS_T0_CANONICAL", "UNK_HOLD_STATE", "UNK_SOURCE_LINEAGE",
                     "UNK_DEPENDENCY_REGISTRY", "UNK_COPY_LINEAGE", "UNK_PROCESS_STATE"):
            self.assertIn(code, out["reason_codes"])

    def test_unratified_group_and_malformed_input_block(self):
        out = evaluate_disposition(record(review_group="UNRATIFIED"))
        self.assertEqual(out["disposition"], "BLOCKED_UNKNOWN")
        for value in (None, [], "invalid", {}):
            self.assertEqual(evaluate_disposition(value)["disposition"], "BLOCKED_UNKNOWN")



    def test_sensitivity_labels_validate_against_ratified_class_minimums(self):
        cases = [
            ("T0_CANONICAL", "RESTRICTED", "PROTECTED"),
            ("CORE_LEDGER", "RESTRICTED", "PROTECTED"),
            ("AI_LEDGER", "RESTRICTED", "PROTECTED"),
            ("T3_PROTECTED_EVIDENCE", "RESTRICTED", "PROTECTED"),
            ("GOVERNANCE_EVIDENCE", "RESTRICTED", "PROTECTED"),
            ("T4_DETERMINISTIC_CACHE", "INTERNAL", "REVIEWABLE_NONCANONICAL"),
            ("T2_EPHEMERAL_INFERENCE_OUTPUT", "CONFIDENTIAL", "REVIEWABLE_NONCANONICAL"),
            ("T1_RAW_OBSERVATION", "CONFIDENTIAL", "REVIEWABLE_NONCANONICAL"),
        ]
        for kind, minimum, expected in cases:
            with self.subTest(kind=kind):
                out = evaluate_disposition(record(data_class=kind, review_group=kind,
                    producer_provenance_verified=True))
                self.assertEqual(out["disposition"], expected)
                self.assertNotIn("UNK_SENSITIVITY_BELOW_CLASS_MINIMUM", out["reason_codes"])

    def test_sensitivity_below_class_minimum_blocks_nonprotected_object(self):
        sensitivity = {"state":"CLASSIFIED", "label":"PUBLIC",
            "evidence_ref":"synthetic-ref", "evidence_revision":"r1"}
        out = evaluate_disposition(record(sensitivity=sensitivity))
        self.assertEqual(out["disposition"], "BLOCKED_UNKNOWN")
        self.assertIn("UNK_SENSITIVITY_BELOW_CLASS_MINIMUM", out["reason_codes"])

    def test_unknown_conflicted_and_pending_sensitivity_states_fail_closed(self):
        for state in ("UNCLASSIFIED", "CONFLICTED", "PENDING_OWNER_DECISION"):
            with self.subTest(state=state):
                sensitivity = {"state":state, "label":None,
                    "evidence_ref":"synthetic-ref", "evidence_revision":"r1"}
                out = evaluate_disposition(record(sensitivity=sensitivity))
                self.assertEqual(out["disposition"], "BLOCKED_UNKNOWN")
                self.assertIn("UNK_SENSITIVITY_STATE", out["reason_codes"])

    def test_malformed_sensitivity_metadata_fails_closed(self):
        cases = [
            (None, "UNK_SENSITIVITY_METADATA"),
            ([], "UNK_SENSITIVITY_METADATA"),
            ({"state":"CLASSIFIED", "label":"UNKNOWN", "evidence_ref":"x", "evidence_revision":"r1"},
             "UNK_SENSITIVITY_LABEL"),
            ({"state":"UNKNOWN", "label":"INTERNAL", "evidence_ref":"x", "evidence_revision":"r1"},
             "UNK_SENSITIVITY_STATE"),
            ({"state":"CLASSIFIED", "label":"INTERNAL", "evidence_ref":"", "evidence_revision":"r1"},
             "UNK_SENSITIVITY_EVIDENCE"),
            ({"state":"CLASSIFIED", "label":None, "evidence_ref":"x", "evidence_revision":"r1"},
             "UNK_SENSITIVITY_LABEL"),
        ]
        for sensitivity, code in cases:
            with self.subTest(sensitivity=sensitivity):
                out = evaluate_disposition(record(sensitivity=sensitivity))
                self.assertEqual(out["disposition"], "BLOCKED_UNKNOWN")
                self.assertIn(code, out["reason_codes"])

    def test_protected_object_remains_protected_when_sensitivity_is_unknown(self):
        out = evaluate_disposition(record(data_class="T0_CANONICAL", sensitivity={
            "state":"CONFLICTED", "label":None,
            "evidence_ref":"synthetic-ref", "evidence_revision":"r1"}))
        self.assertEqual(out["disposition"], "PROTECTED")
        self.assertIn("PROT_CLASS_T0_CANONICAL", out["reason_codes"])
        self.assertIn("UNK_SENSITIVITY_STATE", out["reason_codes"])

    def test_noncanonical_copy_must_inherit_source_sensitivity(self):
        base = {"data_class":"NONCANONICAL_COPY", "review_group":"NONCANONICAL_COPY",
                "object_kind":"COPY", "object_id":"copy-1"}
        lineage = {"complete":True, "copy_id":"copy-1",
                   "source_object_id":"source-1", "source_version_id":"v1"}
        inventory = {"complete":True, "items":[{"copy_id":"copy-1", "version_id":"v1",
                    "kind":"NONCANONICAL_COPY", "state":"PRESENT"}]}
        too_low = {"state":"CLASSIFIED", "label":"INTERNAL",
                   "inherited_labels":["CONFIDENTIAL"], "evidence_ref":"synthetic-ref",
                   "evidence_revision":"r1"}
        valid = dict(too_low, label="RESTRICTED")
        malformed_inheritance = dict(valid, inherited_labels="CONFIDENTIAL")
        for sensitivity, expected, code in (
            (too_low, "BLOCKED_UNKNOWN", "UNK_SENSITIVITY_BELOW_INHERITED"),
            (valid, "COPY_SPECIFIC_REVIEW", None),
            (dict(valid, inherited_labels=[]), "BLOCKED_UNKNOWN", "UNK_SENSITIVITY_INHERITANCE"),
            (malformed_inheritance, "BLOCKED_UNKNOWN", "UNK_SENSITIVITY_INHERITANCE"),
        ):
            out = evaluate_disposition(record(**base, copy_lineage=lineage,
                copies=inventory, sensitivity=sensitivity))
            self.assertEqual(out["disposition"], expected)
            if code:
                self.assertIn(code, out["reason_codes"])

    def test_sensitivity_never_grants_mutation_or_execution_authority(self):
        out = evaluate_disposition(record())
        self.assertIs(out["mutation_performed"], False)
        self.assertIs(out["execution_authorized"], False)

if __name__ == "__main__":
    unittest.main()
