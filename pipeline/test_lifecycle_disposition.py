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
        good = evaluate_disposition(record(**base, copy_lineage={"complete":True,"copy_id":"c1",
            "source_object_id":"s1","source_version_id":"v1"}))
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

    def test_unratified_group_and_malformed_input_block(self):
        out = evaluate_disposition(record(review_group="UNRATIFIED"))
        self.assertEqual(out["disposition"], "BLOCKED_UNKNOWN")
        for value in (None, [], "invalid", {}):
            self.assertEqual(evaluate_disposition(value)["disposition"], "BLOCKED_UNKNOWN")


if __name__ == "__main__":
    unittest.main()
