"""Contract tests for the GitHub-only L4 artifact inventory and SHA-256 manifest."""
import io
import stat
import unittest
import urllib.request
import warnings
import zipfile
from datetime import datetime, timezone

from ci.t0_l4_artifact_manifest import (
    ArtifactManifestError,
    _StripAuthorizationRedirectHandler,
    build_manifest,
    validate_allowlist,
)

SOURCE_SHA = "27aea002a3f404792d4c1a3dc56eff77c2163840"
COLLECTOR_SHA = "d6550315521c3d0660a57afbe1c2e4bbdd3dff65"
NOW = datetime(2026, 11, 10, 14, 20, tzinfo=timezone.utc)
MEMBERS = {
    "l4-source-sha.txt": (SOURCE_SHA + "\n").encode(),
    "l4-validation-scope.txt": b"T0_L4_MINIMUM_LINEAGE=GITHUB_HOSTED_READ_ONLY\n",
    "l4-lineage-contract-tests.log": b"Ran 11 tests in 0.004s\n\nOK\n",
    "l4-lineage-contract-verdict.txt": b"L4_MINIMUM_LINEAGE_CONTRACT=PASS\n",
}
EXPECTED = {
    "repository": "kenznguyen/btcusdt-telegram-signals2",
    "run_id": 42831240089,
    "artifact_id": 13771662067,
    "branch": "feature/t0-centralized-data-feeder-p1-20261101",
    "source_sha": SOURCE_SHA,
    "collector_source_sha": COLLECTOR_SHA,
    "workflow_path": ".github/workflows/t0-l4-minimum-validation.yml",
    "artifact_name": "t0-l4-minimum-lineage-42831240089",
    "evidence_class": "L4_LINEAGE_CONTRACT_CI",
    "expected_members": list(MEMBERS),
    "lineage_contract": True,
}


def make_archive(members=None):
    payload = io.BytesIO()
    with zipfile.ZipFile(payload, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in (MEMBERS if members is None else members).items():
            archive.writestr(name, data)
    return payload.getvalue()


def make_run(**overrides):
    run = {
        "id": EXPECTED["run_id"],
        "head_branch": EXPECTED["branch"],
        "head_sha": EXPECTED["source_sha"],
        "path": EXPECTED["workflow_path"],
        "status": "completed",
        "conclusion": "success",
        "html_url": "https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42831240089",
    }
    run.update(overrides)
    return run


def make_artifact(archive_bytes, **overrides):
    artifact = {
        "id": EXPECTED["artifact_id"],
        "name": EXPECTED["artifact_name"],
        "size_in_bytes": len(archive_bytes),
        "expired": False,
        "created_at": "2026-11-10T14:09:25Z",
        "expires_at": "2026-11-17T14:09:25Z",
    }
    artifact.update(overrides)
    return artifact


class L4ArtifactManifestContractTests(unittest.TestCase):
    def build(self, archive_bytes=None, run=None, artifacts=None, expected=None, now=NOW):
        archive_bytes = make_archive() if archive_bytes is None else archive_bytes
        run = make_run() if run is None else run
        artifacts = [make_artifact(archive_bytes)] if artifacts is None else artifacts
        return build_manifest(run, artifacts, archive_bytes, EXPECTED if expected is None else expected, now=now)

    def test_builds_manifest_with_archive_and_member_sha256(self):
        archive_bytes = make_archive()
        manifest = self.build(archive_bytes=archive_bytes)
        self.assertEqual("T0_L4_GITHUB_ARTIFACT_MANIFEST_V1", manifest["schema_version"])
        self.assertEqual(EXPECTED["source_sha"], manifest["source_sha"])
        artifact = manifest["artifacts"][0]
        self.assertEqual(EXPECTED["evidence_class"], artifact["evidence_class"])
        self.assertEqual(len(archive_bytes), artifact["archive"]["size_bytes"])
        self.assertEqual(4, len(artifact["archive"]["members"]))
        self.assertEqual(64, len(artifact["archive"]["sha256"]))
        self.assertTrue(all(len(member["sha256"]) == 64 for member in artifact["archive"]["members"]))

    def test_manifest_is_deterministic_for_identical_inputs(self):
        archive_bytes = make_archive()
        self.assertEqual(self.build(archive_bytes), self.build(archive_bytes))

    def test_hashes_generic_multi_file_evidence_without_lineage_markers(self):
        generic_members = {"bundle.json": b'{"fixture":"synthetic"}', "segments/a.jsonl": b'{"n":1}\n'}
        archive_bytes = make_archive(generic_members)
        expected = dict(EXPECTED, evidence_class="P1_8_SYNTHETIC_TEST_BUNDLE", expected_members=None, lineage_contract=False)
        manifest = self.build(archive_bytes=archive_bytes, expected=expected)
        self.assertEqual(2, len(manifest["artifacts"][0]["archive"]["members"]))

    def test_rejects_source_sha_mismatch(self):
        with self.assertRaises(ArtifactManifestError):
            self.build(run=make_run(head_sha="f" * 40))

    def test_rejects_wrong_run_id_branch_or_workflow(self):
        for changes in (
            {"id": EXPECTED["run_id"] + 1},
            {"head_branch": "main"},
            {"path": ".github/workflows/other.yml"},
            {"status": "in_progress"},
            {"conclusion": "failure"},
        ):
            with self.subTest(changes=changes), self.assertRaises(ArtifactManifestError):
                self.build(run=make_run(**changes))

    def test_requires_exactly_one_allowlisted_artifact(self):
        archive_bytes = make_archive()
        artifact = make_artifact(archive_bytes)
        with self.assertRaises(ArtifactManifestError):
            self.build(artifacts=[])
        with self.assertRaises(ArtifactManifestError):
            self.build(artifacts=[artifact, dict(artifact, id=artifact["id"] + 1)])

    def test_rejects_artifact_name_or_id_mismatch(self):
        archive_bytes = make_archive()
        for changes in ({"name": "unapproved-name"}, {"id": 0}):
            with self.subTest(changes=changes), self.assertRaises(ArtifactManifestError):
                self.build(artifacts=[make_artifact(archive_bytes, **changes)])

    def test_rejects_expired_or_expiry_timestamp_in_the_past(self):
        archive_bytes = make_archive()
        with self.assertRaises(ArtifactManifestError):
            self.build(artifacts=[make_artifact(archive_bytes, expired=True)])
        with self.assertRaises(ArtifactManifestError):
            self.build(artifacts=[make_artifact(archive_bytes, expires_at="2026-11-09T00:00:00Z")])

    def test_rejects_archive_size_mismatch(self):
        archive_bytes = make_archive()
        with self.assertRaises(ArtifactManifestError):
            self.build(artifacts=[make_artifact(archive_bytes, size_in_bytes=len(archive_bytes) + 1)])

    def test_rejects_corrupt_zip(self):
        with self.assertRaises(ArtifactManifestError):
            self.build(archive_bytes=b"not-a-zip")

    def test_rejects_missing_or_unexpected_lineage_members(self):
        missing = dict(MEMBERS)
        missing.pop("l4-validation-scope.txt")
        with self.assertRaises(ArtifactManifestError):
            self.build(archive_bytes=make_archive(missing))
        extra = dict(MEMBERS, **{"unexpected.txt": b"x"})
        with self.assertRaises(ArtifactManifestError):
            self.build(archive_bytes=make_archive(extra))

    def test_rejects_unsafe_archive_member_path(self):
        unsafe = dict(MEMBERS)
        unsafe["../l4-source-sha.txt"] = unsafe.pop("l4-source-sha.txt")
        with self.assertRaises(ArtifactManifestError):
            self.build(archive_bytes=make_archive(unsafe))

    def test_rejects_duplicate_archive_member_names(self):
        payload = io.BytesIO()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            with zipfile.ZipFile(payload, "w") as archive:
                for name, data in MEMBERS.items():
                    archive.writestr(name, data)
                archive.writestr("l4-source-sha.txt", MEMBERS["l4-source-sha.txt"])
        with self.assertRaises(ArtifactManifestError):
            self.build(archive_bytes=payload.getvalue())

    def test_rejects_symlink_archive_member(self):
        payload = io.BytesIO()
        with zipfile.ZipFile(payload, "w") as archive:
            for name, data in MEMBERS.items():
                info = zipfile.ZipInfo(name)
                if name == "l4-source-sha.txt":
                    info.create_system = 3
                    info.external_attr = (stat.S_IFLNK | 0o777) << 16
                archive.writestr(info, data)
        with self.assertRaises(ArtifactManifestError):
            self.build(archive_bytes=payload.getvalue())

    def test_rejects_mismatched_source_marker_or_verdict(self):
        wrong_source = dict(MEMBERS)
        wrong_source["l4-source-sha.txt"] = ("f" * 40 + "\n").encode()
        with self.assertRaises(ArtifactManifestError):
            self.build(archive_bytes=make_archive(wrong_source))
        wrong_verdict = dict(MEMBERS)
        wrong_verdict["l4-lineage-contract-verdict.txt"] = b"FAIL\n"
        with self.assertRaises(ArtifactManifestError):
            self.build(archive_bytes=make_archive(wrong_verdict))

    def test_rejects_unhealthy_test_log(self):
        bad_log = dict(MEMBERS)
        bad_log["l4-lineage-contract-tests.log"] = b"FAILED (failures=1)\n"
        with self.assertRaises(ArtifactManifestError):
            self.build(archive_bytes=make_archive(bad_log))

    def test_redirect_handler_does_not_forward_bearer_authorization(self):
        request = urllib.request.Request(
            "https://api.github.com/repos/example/repo/actions/artifacts/1/zip",
            headers={"Authorization": "Bearer secret-value", "Accept": "application/vnd.github+json"},
        )
        redirected = _StripAuthorizationRedirectHandler().redirect_request(
            request, None, 302, "Found", {}, "https://artifact-storage.example/signed.zip"
        )
        self.assertFalse(any(key.lower() == "authorization" for key in redirected.headers))
        self.assertFalse(any(key.lower() == "authorization" for key in redirected.unredirected_hdrs))

    def test_rejects_invalid_allowlist_identity_before_network_access(self):
        allowlist = {
            "schema_version": "T0_L4_ARTIFACT_ALLOWLIST_V1",
            "artifacts": [{
                "source_run_id": "../999",
                "source_artifact_id": EXPECTED["artifact_id"],
                "source_branch": EXPECTED["branch"],
                "source_sha": SOURCE_SHA,
                "source_artifact_name": EXPECTED["artifact_name"],
                "workflow_path": EXPECTED["workflow_path"],
                "evidence_class": "L4_LINEAGE_CONTRACT_CI",
            }],
        }
        with self.assertRaises(ArtifactManifestError):
            validate_allowlist(allowlist, EXPECTED["branch"])

    def test_rejects_duplicate_artifact_ids_in_allowlist(self):
        item = {
            "source_run_id": EXPECTED["run_id"],
            "source_artifact_id": EXPECTED["artifact_id"],
            "source_branch": EXPECTED["branch"],
            "source_sha": SOURCE_SHA,
            "source_artifact_name": EXPECTED["artifact_name"],
            "workflow_path": EXPECTED["workflow_path"],
            "evidence_class": "L4_LINEAGE_CONTRACT_CI",
            "expected_members": list(MEMBERS),
            "lineage_contract": True,
        }
        allowlist = {"schema_version": "T0_L4_ARTIFACT_ALLOWLIST_V1", "artifacts": [item, dict(item)]}
        with self.assertRaises(ArtifactManifestError):
            validate_allowlist(allowlist, EXPECTED["branch"])


if __name__ == "__main__":
    unittest.main()
