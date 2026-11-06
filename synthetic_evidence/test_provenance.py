import hashlib
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from synthetic_evidence.provenance import (
    build_provenance, verify_artifact_archive, verify_provenance,
)


class ProvenanceBindingTests(unittest.TestCase):
    def _inputs(self, root):
        sha = "a" * 40
        workflow = root / "workflow.yml"
        workflow.write_text("name: synthetic", encoding="utf-8")
        a, b = root / "a.json", root / "b.json"
        a.write_text(json.dumps({"generator_source_sha": sha, "fixture": "A"}), encoding="utf-8")
        b.write_text(json.dumps({"generator_source_sha": sha, "fixture": "B"}), encoding="utf-8")
        return dict(source_sha=sha, run_id="12345", run_attempt="1",
                    repository="owner/repo", ref="refs/heads/feature/test",
                    workflow_ref="owner/repo/.github/workflows/test.yml@refs/heads/feature/test",
                    workflow_file=workflow, descriptor_a=a, descriptor_b=b)

    def test_build_binds_both_fixtures_to_exact_source_and_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            args = self._inputs(Path(tmp))
            data = build_provenance(**args)
            self.assertEqual(data["source_sha"], "a" * 40)
            self.assertEqual(data["run_id"], 12345)
            self.assertEqual(data["fixture_descriptors"]["A"]["source_sha"], "a" * 40)
            self.assertEqual(data["fixture_descriptors"]["B"]["source_sha"], "a" * 40)
            self.assertEqual(len(data["fixture_descriptors"]["A"]["descriptor_sha256"]), 64)
            self.assertEqual(len(data["workflow_sha256"]), 64)

    def test_rejects_missing_run_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            args = self._inputs(Path(tmp)); args["run_id"] = ""
            with self.assertRaisesRegex(ValueError, "run_id"):
                build_provenance(**args)

    def test_rejects_malformed_source_sha(self):
        with tempfile.TemporaryDirectory() as tmp:
            args = self._inputs(Path(tmp)); args["source_sha"] = "invalid"
            with self.assertRaisesRegex(ValueError, "source_sha"):
                build_provenance(**args)

    def test_rejects_fixture_a_source_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            args = self._inputs(Path(tmp))
            args["descriptor_a"].write_text(json.dumps({"generator_source_sha": "b" * 40}))
            with self.assertRaisesRegex(ValueError, "fixture A"):
                build_provenance(**args)

    def test_rejects_fixture_b_source_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            args = self._inputs(Path(tmp))
            args["descriptor_b"].write_text(json.dumps({"generator_source_sha": "b" * 40}))
            with self.assertRaisesRegex(ValueError, "fixture B"):
                build_provenance(**args)

    def test_verifier_fails_closed_on_missing_or_altered_binding(self):
        with tempfile.TemporaryDirectory() as tmp:
            args = self._inputs(Path(tmp))
            data = build_provenance(**args)
            expected = hashlib.sha256(args["workflow_file"].read_bytes()).hexdigest()
            verify_provenance(data, expected_source_sha="a"*40, expected_run_id=12345,
                              expected_workflow_sha256=expected,
                              descriptor_a=args["descriptor_a"], descriptor_b=args["descriptor_b"])
            with self.assertRaisesRegex(ValueError, "run_id"):
                verify_provenance(data, expected_source_sha="a"*40, expected_run_id=999,
                                  expected_workflow_sha256=expected,
                                  descriptor_a=args["descriptor_a"], descriptor_b=args["descriptor_b"])
            altered = dict(data, workflow_sha256="0"*64)
            with self.assertRaisesRegex(ValueError, "workflow_sha256"):
                verify_provenance(altered, expected_source_sha="a"*40, expected_run_id=12345,
                                  expected_workflow_sha256=expected,
                                  descriptor_a=args["descriptor_a"], descriptor_b=args["descriptor_b"])
            with self.assertRaisesRegex(ValueError, "missing"):
                verify_provenance({}, expected_source_sha="a"*40, expected_run_id=12345,
                                  expected_workflow_sha256=expected,
                                  descriptor_a=args["descriptor_a"], descriptor_b=args["descriptor_b"])

    def test_rejects_fixture_descriptor_substitution_even_when_source_sha_matches(self):
        with tempfile.TemporaryDirectory() as tmp:
            args = self._inputs(Path(tmp))
            data = build_provenance(**args)
            expected = hashlib.sha256(args["workflow_file"].read_bytes()).hexdigest()
            original_a, original_b = args["descriptor_a"].read_bytes(), args["descriptor_b"].read_bytes()
            args["descriptor_a"].write_bytes(original_b)
            args["descriptor_b"].write_bytes(original_a)
            with self.assertRaisesRegex(ValueError, "descriptor A"):
                verify_provenance(data, expected_source_sha="a"*40, expected_run_id=12345,
                                  expected_workflow_sha256=expected,
                                  descriptor_a=args["descriptor_a"], descriptor_b=args["descriptor_b"])

    def test_rejects_tampered_fixture_descriptor_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            args = self._inputs(Path(tmp))
            data = build_provenance(**args)
            expected = hashlib.sha256(args["workflow_file"].read_bytes()).hexdigest()
            args["descriptor_a"].write_text(json.dumps({"generator_source_sha": "a"*40, "fixture": "tampered"}))
            with self.assertRaisesRegex(ValueError, "descriptor A"):
                verify_provenance(data, expected_source_sha="a"*40, expected_run_id=12345,
                                  expected_workflow_sha256=expected,
                                  descriptor_a=args["descriptor_a"], descriptor_b=args["descriptor_b"])

    def test_rejects_tampered_provenance_descriptor_digest(self):
        with tempfile.TemporaryDirectory() as tmp:
            args = self._inputs(Path(tmp))
            data = build_provenance(**args)
            expected = hashlib.sha256(args["workflow_file"].read_bytes()).hexdigest()
            data["fixture_descriptors"]["B"]["descriptor_sha256"] = "0"*64
            with self.assertRaisesRegex(ValueError, "descriptor B"):
                verify_provenance(data, expected_source_sha="a"*40, expected_run_id=12345,
                                  expected_workflow_sha256=expected,
                                  descriptor_a=args["descriptor_a"], descriptor_b=args["descriptor_b"])

    def test_rejects_source_sha_mismatch_during_replay(self):
        with tempfile.TemporaryDirectory() as tmp:
            args = self._inputs(Path(tmp))
            data = build_provenance(**args)
            expected = hashlib.sha256(args["workflow_file"].read_bytes()).hexdigest()
            with self.assertRaisesRegex(ValueError, "source_sha"):
                verify_provenance(data, expected_source_sha="b"*40, expected_run_id=12345,
                                  expected_workflow_sha256=expected,
                                  descriptor_a=args["descriptor_a"], descriptor_b=args["descriptor_b"])

    def test_accepts_exact_artifact_archive_digest_and_valid_zip(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "evidence.zip"
            with zipfile.ZipFile(archive, "w") as z:
                z.writestr("provenance.json", '{"schema":"p1.8.synthetic-provenance.v2"}')
            digest = hashlib.sha256(archive.read_bytes()).hexdigest()
            self.assertTrue(verify_artifact_archive(archive, expected_sha256=digest))

    def test_rejects_substituted_artifact_archive(self):
        with tempfile.TemporaryDirectory() as tmp:
            expected_archive = Path(tmp) / "expected.zip"
            substituted_archive = Path(tmp) / "substituted.zip"
            with zipfile.ZipFile(expected_archive, "w") as z:
                z.writestr("evidence.json", "expected")
            with zipfile.ZipFile(substituted_archive, "w") as z:
                z.writestr("evidence.json", "substituted")
            expected = hashlib.sha256(expected_archive.read_bytes()).hexdigest()
            with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
                verify_artifact_archive(substituted_archive, expected_sha256=expected)

    def test_rejects_corrupt_artifact_archive(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "corrupt.zip"
            archive.write_bytes(b"not a zip archive")
            digest = hashlib.sha256(archive.read_bytes()).hexdigest()
            with self.assertRaisesRegex(ValueError, "valid ZIP"):
                verify_artifact_archive(archive, expected_sha256=digest)


if __name__ == "__main__":
    unittest.main()
