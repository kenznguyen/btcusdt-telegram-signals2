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

    def test_profile_binding_requires_all_five_locations_to_match(self):
        from t0_signature_stage1.verdicts import PROFILE_ID, PROFILE_VERSION, validate_profile_bindings
        bindings = {
            name: {"profile_id": PROFILE_ID, "profile_version": PROFILE_VERSION}
            for name in ("descriptor", "statement", "envelope", "policy", "request")
        }
        result = validate_profile_bindings(bindings)
        self.assertEqual((result.verdict, result.reason_code), ("PASS", "PROFILE_BINDING_MATCH"))
        bindings["envelope"]["profile_id"] = "untrusted-substitution"
        result = validate_profile_bindings(bindings)
        self.assertEqual((result.verdict, result.reason_code), ("INVALID", "PROFILE_BINDING_MISMATCH"))
        bindings["envelope"]["profile_id"] = PROFILE_ID
        bindings["policy"]["profile_version"] = "2"
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
