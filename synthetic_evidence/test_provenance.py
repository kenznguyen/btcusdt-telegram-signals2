import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from synthetic_evidence.provenance import build_provenance, verify_provenance

class ProvenanceBindingTests(unittest.TestCase):
    def _inputs(self, root):
        sha = "a" * 40
        workflow = root / "workflow.yml"
        workflow.write_text("name: synthetic", encoding="utf-8")
        a, b = root / "a.json", root / "b.json"
        a.write_text(json.dumps({"generator_source_sha": sha}), encoding="utf-8")
        b.write_text(json.dumps({"generator_source_sha": sha}), encoding="utf-8")
        return dict(source_sha=sha, run_id="12345", run_attempt="1",
                    repository="owner/repo", ref="refs/heads/feature/test",
                    workflow_ref="owner/repo/.github/workflows/test.yml@refs/heads/feature/test",
                    workflow_file=workflow, descriptor_a=a, descriptor_b=b)

    def test_build_binds_both_fixtures_to_exact_source_and_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            data = build_provenance(**self._inputs(Path(tmp)))
            self.assertEqual(data["source_sha"], "a" * 40)
            self.assertEqual(data["run_id"], 12345)
            self.assertEqual(data["fixture_descriptors"]["A"]["source_sha"], "a" * 40)
            self.assertEqual(data["fixture_descriptors"]["B"]["source_sha"], "a" * 40)
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
            args = self._inputs(Path(tmp)); args["descriptor_a"].write_text('{"generator_source_sha":"' + "b"*40 + '"}')
            with self.assertRaisesRegex(ValueError, "fixture A"):
                build_provenance(**args)

    def test_rejects_fixture_b_source_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            args = self._inputs(Path(tmp)); args["descriptor_b"].write_text('{"source_sha":"' + "b"*40 + '"}')
            with self.assertRaisesRegex(ValueError, "fixture B"):
                build_provenance(**args)

    def test_verifier_fails_closed_on_missing_or_altered_binding(self):
        with tempfile.TemporaryDirectory() as tmp:
            data = build_provenance(**self._inputs(Path(tmp)))
            expected = hashlib.sha256((Path(tmp) / "workflow.yml").read_bytes()).hexdigest()
            self.assertTrue(verify_provenance(data, expected_source_sha="a"*40, expected_run_id=12345, expected_workflow_sha256=expected))
            with self.assertRaisesRegex(ValueError, "run_id"):
                verify_provenance(data, expected_source_sha="a"*40, expected_run_id=999, expected_workflow_sha256=expected)
            altered = dict(data, workflow_sha256="0"*64)
            with self.assertRaisesRegex(ValueError, "workflow_sha256"):
                verify_provenance(altered, expected_source_sha="a"*40, expected_run_id=12345, expected_workflow_sha256=expected)
            with self.assertRaisesRegex(ValueError, "missing"):
                verify_provenance({}, expected_source_sha="a"*40, expected_run_id=12345, expected_workflow_sha256=expected)

if __name__ == "__main__":
    unittest.main()
