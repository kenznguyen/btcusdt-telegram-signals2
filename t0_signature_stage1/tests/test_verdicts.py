import unittest

from t0_signature_stage1.verdicts import (
    MOCK_LABEL,
    MOCK_REJECTED,
    MOCK_ACCEPTED,
    MockSignatureVerifier,
    StageStateSnapshot,
    evaluate_stage1_fixture,
    fixture_catalog,
)


def _test_state():
    return StageStateSnapshot(
        trust_roots=("synthetic-root-fingerprint",),
        policy_head="policy-digest-0",
        anchor_head=(0, "anchor-digest-0"),
        checkpoint_head=("checkpoint-0", "object-digest-0"),
        bootstrap_sequence=0,
    )


class FixtureMatrixTests(unittest.TestCase):
    def test_exactly_27_a22_fixtures_are_registered(self):
        fixtures = fixture_catalog()
        self.assertEqual(len(fixtures), 27)
        self.assertEqual([item.case_id for item in fixtures], [f"A2.2-NV-{i:02d}" for i in range(1, 28)])

    def test_every_fixture_has_one_mutation_and_fixed_verdict_reason(self):
        for fixture in fixture_catalog():
            with self.subTest(case_id=fixture.case_id):
                self.assertTrue(fixture.baseline in {"B0", "B-A", "B0-PF"})
                self.assertTrue(fixture.single_mutation)
                self.assertEqual(len(fixture.mutations), 1)
                self.assertTrue(fixture.expected_verdict)
                self.assertTrue(fixture.expected_reason)
                self.assertTrue(fixture.state_unchanged)

    def test_each_fixture_produces_exact_expected_verdict_and_reason(self):
        for fixture in fixture_catalog():
            with self.subTest(case_id=fixture.case_id):
                before = StageStateSnapshot(
                    trust_roots=("synthetic-root-fingerprint",),
                    policy_head="policy-digest-0",
                    anchor_head=(0, "anchor-digest-0"),
                    checkpoint_head=("checkpoint-0", "object-digest-0"),
                    bootstrap_sequence=0,
                )
                after, result = evaluate_stage1_fixture(fixture.case_id, before)
                self.assertEqual(result.verdict, fixture.expected_verdict)
                self.assertEqual(result.reason_code, fixture.expected_reason)
                self.assertEqual(after, before)
                self.assertFalse(result.state_advanced)


    def test_every_declared_mutation_targets_an_existing_baseline_field(self):
        from t0_signature_stage1.verdicts import _BASELINES, _get_existing_path
        for fixture in fixture_catalog():
            with self.subTest(case_id=fixture.case_id):
                _get_existing_path(_BASELINES[fixture.baseline], fixture.mutation_path)

    def test_fixture_builder_fails_closed_for_missing_mutation_path(self):
        from t0_signature_stage1.verdicts import _set_existing_path
        baseline = {"nested": {"present": "value"}}
        with self.assertRaises(KeyError):
            _set_existing_path(baseline, "nested.missing.leaf", "mutated")

    def test_each_fixture_mutates_an_existing_leaf_without_adding_fields(self):
        from t0_signature_stage1.verdicts import build_fixture
        def leaves(value, prefix=""):
            if isinstance(value, dict):
                result = {}
                for key, child in value.items():
                    result.update(leaves(child, f"{prefix}.{key}" if prefix else key))
                return result
            return {prefix: value}
        for fixture in fixture_catalog():
            with self.subTest(case_id=fixture.case_id):
                baseline, mutated, spec = build_fixture(fixture.case_id)
                before, after = leaves(baseline), leaves(mutated)
                self.assertIn(spec.mutation_path, before)
                self.assertIn(spec.mutation_path, after)
                self.assertEqual(set(before), set(after))
                changed = {key for key in before if before[key] != after[key]}
                self.assertEqual(changed, {spec.mutation_path})

    def test_fixture_verdict_is_derived_from_mutated_content_not_catalog_fact_key(self):
        from t0_signature_stage1.verdicts import build_fixture, evaluate_fixture_content
        baseline, mutated, _spec = build_fixture("A2.2-NV-01")
        before = StageStateSnapshot(
            trust_roots=("synthetic-root-fingerprint",),
            policy_head="policy-digest-0",
            anchor_head=(0, "anchor-digest-0"),
            checkpoint_head=("checkpoint-0", "object-digest-0"),
            bootstrap_sequence=0,
        )
        after, result = evaluate_fixture_content(baseline, mutated, before)
        self.assertEqual((result.verdict, result.reason_code),
                         ("UNTRUSTED", "PURPOSE_NOT_SUPPORTED_BY_PROFILE"))
        self.assertEqual(after, before)
        # Restore the mutated semantic field: the same evaluator must no longer
        # emit the purpose failure, regardless of the catalog's expected fact key.
        restored = dict(mutated)
        restored["statement"] = dict(mutated["statement"])
        restored["statement"]["purpose"] = baseline["statement"]["purpose"]
        _same_state, restored_result = evaluate_fixture_content(baseline, restored, before)
        self.assertNotEqual(restored_result.reason_code, "PURPOSE_NOT_SUPPORTED_BY_PROFILE")


    def test_fixture_evaluator_rejects_compound_mutations(self):
        import copy
        from t0_signature_stage1.verdicts import build_fixture, evaluate_fixture_content
        baseline, mutated, _spec = build_fixture("A2.2-NV-01")
        compound = copy.deepcopy(mutated)
        compound["policy_profile_authorization"]["signature_profile_version"] = 3
        state = StageStateSnapshot(
            trust_roots=("synthetic-root-fingerprint",),
            policy_head="policy-digest-0",
            anchor_head=(0, "anchor-digest-0"),
            checkpoint_head=("checkpoint-0", "object-digest-0"),
            bootstrap_sequence=0,
        )
        after, result = evaluate_fixture_content(baseline, compound, state)
        self.assertEqual((result.verdict, result.reason_code),
                         ("INVALID", "FIXTURE_SINGLE_MUTATION_VIOLATION"))
        self.assertEqual(after, state)


    def test_mutable_catalog_values_are_defensively_copied(self):
        from t0_signature_stage1.verdicts import build_fixture
        first = fixture_catalog()[-1]
        first.mutation_value.append("UNEXPECTED")
        _baseline, mutated, _spec = build_fixture("A2.2-NV-27")
        self.assertEqual(mutated["bootstrap"]["path_evidence"], ["PATH_A", "PATH_B"])


    def test_nv03_uses_unchanged_a1_object_and_v2_request_not_a_label_trigger(self):
        from t0_signature_stage1.verdicts import PROFILE_ID, PROFILE_VERSION, build_fixture, evaluate_fixture_content
        baseline, mutated, _spec = build_fixture("A2.2-NV-03")
        self.assertEqual(mutated["historical_fixture"], baseline["historical_fixture"])
        self.assertEqual(mutated["historical_fixture"]["signature_profile_id"], "T0-CHECKPOINT-ISSUER-SIGNATURE-PROFILE-A1")
        self.assertEqual(mutated["verification_request"]["signature_profile_id"], PROFILE_ID)
        self.assertEqual(mutated["verification_request"]["signature_profile_version"], PROFILE_VERSION)
        self.assertNotIn("subject_fixture", mutated["verification_request"])
        state = _test_state()
        after, result = evaluate_fixture_content(baseline, mutated, state)
        self.assertEqual((result.verdict, result.reason_code), ("INVALID", "PROFILE_VERSION_MISMATCH"))
        self.assertEqual(after, state)

    def test_nv04_b0pf_has_only_normative_statement_profile_mismatch(self):
        from t0_signature_stage1.verdicts import PROFILE_ID, PROFILE_VERSION, build_fixture
        baseline, mutated, _spec = build_fixture("A2.2-NV-04")
        self.assertEqual(baseline["statement"]["signature_profile_id"], "T0-CHECKPOINT-ISSUER-SIGNATURE-PROFILE-LEGACY")
        self.assertEqual(baseline["statement"]["signature_profile_version"], PROFILE_VERSION)
        for section in ("descriptor", "envelope", "policy_profile_authorization", "policy_signed_binding", "verification_request", "verifier_allowed_profile"):
            self.assertEqual(mutated[section]["signature_profile_id"], PROFILE_ID)
            self.assertEqual(mutated[section]["signature_profile_version"], PROFILE_VERSION)
        self.assertTrue(mutated["verification_request"]["allow_automatic_fallback"])
        self.assertEqual(baseline["bootstrap"], mutated["bootstrap"])


    def test_baselines_have_complete_canonical_evidence_and_policy_authorization_metadata(self):
        from t0_signature_stage1.verdicts import _BASELINES
        from t0_signature_stage1.primitives import evidence_object_digest, parse_canonical_json
        for name, baseline in _BASELINES.items():
            with self.subTest(baseline=name):
                evidence = baseline["evidence_object"]
                raw = evidence["canonical_bytes"].encode("utf-8")
                self.assertEqual(len(raw), evidence["byte_length"])
                self.assertEqual(evidence_object_digest(raw), evidence["digest"])
                self.assertEqual(parse_canonical_json(raw)["checkpoint"], "synthetic")
                policy = baseline["policy_profile_authorization"]
                self.assertEqual(policy["signer_id"], baseline["test_signer"]["signer_id"])
                self.assertEqual(policy["signer_role"], baseline["test_signer"]["role"])
                self.assertEqual(policy["namespace"], "T0")
                self.assertEqual(policy["audience"], "BTCUSDT")
                self.assertEqual(policy["allowed_purposes"], baseline["policy"]["allowed_purposes"])

    def test_evaluator_rejects_invalid_canonical_evidence_object(self):
        import copy
        from t0_signature_stage1.verdicts import build_fixture, evaluate_fixture_content
        baseline, mutated, _spec = build_fixture("A2.2-NV-01")
        corrupted_baseline = copy.deepcopy(baseline)
        corrupted_baseline["evidence_object"]["digest"] = "0" * 64
        corrupted = copy.deepcopy(mutated)
        corrupted["evidence_object"]["digest"] = "0" * 64
        after, result = evaluate_fixture_content(corrupted_baseline, corrupted, _test_state())
        self.assertEqual((result.verdict, result.reason_code), ("INVALID", "FIXTURE_CONTENT_INVALID"))
        self.assertEqual(after, _test_state())


    def test_evaluator_rejects_zero_semantic_mutations(self):
        from t0_signature_stage1.verdicts import build_fixture, evaluate_fixture_content
        baseline, _mutated, _spec = build_fixture("A2.2-NV-01")
        state = _test_state()
        after, result = evaluate_fixture_content(baseline, baseline, state)
        self.assertEqual((result.verdict, result.reason_code), ("INVALID", "FIXTURE_SINGLE_MUTATION_VIOLATION"))
        self.assertEqual(after, state)

    def test_profile_bindings_cover_all_normative_locations(self):
        from t0_signature_stage1.verdicts import PROFILE_ID, PROFILE_VERSION, validate_profile_bindings
        locations = ("descriptor", "statement", "envelope", "policy_profile_authorization",
                     "policy_signed_binding", "bootstrap_record", "bootstrap_authorization",
                     "verifier_request", "verifier_allowed_profile")
        bindings = {name: {"signature_profile_id": PROFILE_ID, "signature_profile_version": PROFILE_VERSION}
                    for name in locations}
        self.assertEqual((validate_profile_bindings(bindings).verdict, validate_profile_bindings(bindings).reason_code),
                         ("PASS", "PROFILE_BINDING_MATCH"))
        del bindings["policy_signed_binding"]
        result = validate_profile_bindings(bindings)
        self.assertEqual((result.verdict, result.reason_code), ("INVALID", "PROFILE_BINDING_MISMATCH"))

    def test_each_fixture_records_schema_dimensions_state_and_forbidden_transitions(self):
        from t0_signature_stage1.verdicts import build_fixture, evaluate_fixture_content
        required = {"parsing_canonicalization", "object_binding", "profile", "purpose",
                    "signature", "policy_authorization", "bootstrap_authorization", "custody_readback"}
        for fixture in fixture_catalog():
            with self.subTest(case_id=fixture.case_id):
                baseline, mutated, spec = build_fixture(fixture.case_id)
                self.assertEqual(spec.schema_version, "A2.2-STAGE-I-FIXTURE-V1")
                self.assertEqual(baseline["schema_version"], spec.schema_version)
                self.assertEqual(set(spec.dimension_results), required)
                state = _test_state()
                after, result = evaluate_fixture_content(baseline, mutated, state)
                self.assertEqual(after, state)
                self.assertEqual(result.state_s0, state)
                self.assertEqual(result.state_s1, state)
                self.assertEqual(set(result.dimension_results), required)
                self.assertEqual(result.dimension_results, spec.dimension_results)
                self.assertEqual(result.dimension_results["signature"], "NOT_VERIFIED")
                self.assertEqual(result.dimension_results["custody_readback"], "NOT_VERIFIED")
                self.assertTrue(result.forbidden_transitions)
                self.assertTrue(all(result.forbidden_transitions.values()))


class MockVerifierTests(unittest.TestCase):
    def test_mock_verifier_is_explicitly_non_cryptographic(self):
        verifier = MockSignatureVerifier()
        self.assertEqual(verifier.classification, MOCK_LABEL)
        self.assertEqual(verifier.verify(b"synthetic", b"mock-ok"), MOCK_ACCEPTED)
        self.assertEqual(verifier.verify(b"synthetic", b"anything-else"), MOCK_REJECTED)
        self.assertNotIn("VALID_SIGNATURE", (MOCK_ACCEPTED, MOCK_REJECTED))

    def test_bootstrap_first_match_precedence_is_stable(self):
        from t0_signature_stage1.verdicts import evaluate_stage1_facts
        result = evaluate_stage1_facts({
            "path_not_configured": True,
            "path_not_enabled": True,
            "evidence_missing": True,
            "authorization_invalid": True,
        })
        self.assertEqual((result.verdict, result.reason_code), ("BLOCKED", "ROOT_BOOTSTRAP_PATH_NOT_CONFIGURED"))

    def test_bootstrap_unavailable_boundary_precedes_content_invalidity(self):
        from t0_signature_stage1.verdicts import evaluate_stage1_facts
        result = evaluate_stage1_facts({
            "trust_boundary_unavailable": True,
            "authorization_invalid": True,
        })
        self.assertEqual((result.verdict, result.reason_code), ("UNKNOWN", "ROOT_BOOTSTRAP_TRUST_BOUNDARY_UNAVAILABLE"))

    def test_no_positive_bootstrap_path_is_implemented(self):
        from t0_signature_stage1.verdicts import evaluate_stage1_facts
        result = evaluate_stage1_facts({})
        self.assertEqual((result.verdict, result.reason_code), ("BLOCKED", "ROOT_BOOTSTRAP_PATH_NOT_ENABLED"))

    def test_profile_binding_requires_all_normative_locations_to_match(self):
        from t0_signature_stage1.verdicts import PROFILE_ID, PROFILE_VERSION, validate_profile_bindings
        names = ("descriptor", "statement", "envelope", "policy_profile_authorization",
                 "policy_signed_binding", "bootstrap_record", "bootstrap_authorization",
                 "verifier_request", "verifier_allowed_profile")
        bindings = {
            name: {"signature_profile_id": PROFILE_ID, "signature_profile_version": PROFILE_VERSION}
            for name in names
        }
        result = validate_profile_bindings(bindings)
        self.assertEqual((result.verdict, result.reason_code), ("PASS", "PROFILE_BINDING_MATCH"))
        bindings["envelope"]["signature_profile_id"] = "untrusted-substitution"
        result = validate_profile_bindings(bindings)
        self.assertEqual((result.verdict, result.reason_code), ("INVALID", "PROFILE_BINDING_MISMATCH"))
        bindings["envelope"]["signature_profile_id"] = PROFILE_ID
        bindings["policy_signed_binding"]["signature_profile_version"] = "2"
        result = validate_profile_bindings(bindings)
        self.assertEqual((result.verdict, result.reason_code), ("INVALID", "PROFILE_BINDING_MISMATCH"))

    def test_fixture_catalog_binds_exact_baseline_digest_and_one_mutation_path(self):
        import hashlib
        from t0_signature_stage1.verdicts import _BASELINES
        from t0_signature_stage1.primitives import canonicalize
        for fixture in fixture_catalog():
            with self.subTest(case_id=fixture.case_id):
                expected = hashlib.sha256(canonicalize(_BASELINES[fixture.baseline])).hexdigest()
                self.assertEqual(fixture.baseline_digest, expected)
                self.assertTrue(fixture.mutation_path)
                self.assertEqual(len(fixture.mutations), 1)

    def test_each_negative_fixture_changes_exactly_one_declared_leaf(self):
        from t0_signature_stage1.verdicts import build_fixture

        def leaves(value, prefix=""):
            if isinstance(value, dict):
                result = {}
                for key, child in value.items():
                    result.update(leaves(child, f"{prefix}.{key}" if prefix else key))
                return result
            return {prefix: value}

        for fixture in fixture_catalog():
            with self.subTest(case_id=fixture.case_id):
                baseline, mutated, spec = build_fixture(fixture.case_id)
                before = leaves(baseline)
                after = leaves(mutated)
                changed = {key for key in set(before) | set(after) if before.get(key, object()) != after.get(key, object())}
                self.assertEqual(changed, {spec.mutation_path})
                self.assertEqual(len(spec.mutations), 1)

    def test_package_source_has_no_runtime_network_database_or_process_imports(self):
        import ast
        from pathlib import Path
        package_root = Path(__file__).resolve().parents[1]
        forbidden = {"socket", "ssl", "urllib", "http", "requests", "sqlite3", "subprocess"}
        for source_path in package_root.glob("*.py"):
            tree = ast.parse(source_path.read_text(encoding="utf-8"))
            imported = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imported.update(alias.name.split(".")[0] for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imported.add(node.module.split(".")[0])
            self.assertFalse(imported & forbidden, f"forbidden imports in {source_path.name}: {imported & forbidden}")
