"""Contract tests for the exact-commit L4 GitHub repository-file inventory."""
import hashlib
import json
import pathlib
import subprocess
import tempfile
import unittest

from ci.t0_l4_repository_file_inventory import (
    RepositoryInventoryError,
    build_inventory,
    validate_config,
)

BRANCH = "feature/t0-centralized-data-feeder-p1-20261101"


def git(root, *args, input_bytes=None):
    return subprocess.run(
        ["git", *args], cwd=root, input=input_bytes,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
    ).stdout


class RepositoryFileInventoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.temp.name)
        git(self.root, "init", "-q")
        git(self.root, "config", "user.email", "l4-test@example.invalid")
        git(self.root, "config", "user.name", "L4 Inventory Test")
        (self.root / "docs").mkdir()
        (self.root / "docs" / "matrix.md").write_bytes(b"matrix\n")
        (self.root / "docs" / "decision.md").write_bytes(b"decision\x00bytes")
        git(self.root, "add", ".")
        git(self.root, "commit", "-qm", "fixture")
        self.commit = git(self.root, "rev-parse", "HEAD").decode().strip()
        self.matrix_blob = git(self.root, "rev-parse", "HEAD:docs/matrix.md").decode().strip()
        self.decision_blob = git(self.root, "rev-parse", "HEAD:docs/decision.md").decode().strip()
        self.config = {
            "schema_version": "T0_L4_REPOSITORY_FILE_INVENTORY_V1",
            "source_branch": BRANCH,
            "files": [
                {"path": "docs/matrix.md", "git_blob_sha1": self.matrix_blob},
                {"path": "docs/decision.md", "git_blob_sha1": self.decision_blob},
            ],
        }

    def tearDown(self):
        self.temp.cleanup()

    def test_builds_exact_commit_inventory_with_git_blob_and_content_sha256(self):
        result = build_inventory(self.root, self.config, self.commit, BRANCH)
        self.assertEqual(self.commit, result["source_commit"])
        self.assertEqual(BRANCH, result["branch"])
        self.assertEqual(
            ["docs/decision.md", "docs/matrix.md"],
            [item["path"] for item in result["files"]],
        )
        for item in result["files"]:
            content = git(self.root, "cat-file", "blob", item["git_blob_sha1"])
            self.assertEqual(hashlib.sha256(content).hexdigest(), item["sha256"])
            self.assertEqual(len(content), item["size_bytes"])

    def test_rejects_missing_path(self):
        bad = json.loads(json.dumps(self.config))
        bad["files"][0]["path"] = "docs/missing.md"
        with self.assertRaisesRegex(RepositoryInventoryError, "FILE_PATH_MISSING"):
            build_inventory(self.root, bad, self.commit, BRANCH)

    def test_rejects_stale_expected_blob_sha(self):
        bad = json.loads(json.dumps(self.config))
        bad["files"][0]["git_blob_sha1"] = "0" * 40
        with self.assertRaisesRegex(RepositoryInventoryError, "GIT_BLOB_SHA_MISMATCH"):
            build_inventory(self.root, bad, self.commit, BRANCH)

    def test_rejects_duplicate_paths(self):
        bad = json.loads(json.dumps(self.config))
        bad["files"].append(dict(bad["files"][0]))
        with self.assertRaisesRegex(RepositoryInventoryError, "DUPLICATE_FILE_PATH"):
            validate_config(bad, BRANCH)

    def test_rejects_path_traversal_and_absolute_paths(self):
        for path in ("../secret", "/etc/passwd", "docs/../secret", "docs\\secret"):
            bad = json.loads(json.dumps(self.config))
            bad["files"][0]["path"] = path
            with self.subTest(path=path):
                with self.assertRaises(RepositoryInventoryError):
                    validate_config(bad, BRANCH)

    def test_rejects_unsupported_schema(self):
        bad = json.loads(json.dumps(self.config))
        bad["schema_version"] = "UNKNOWN"
        with self.assertRaisesRegex(RepositoryInventoryError, "SCHEMA_UNSUPPORTED"):
            validate_config(bad, BRANCH)

    def test_rejects_branch_mismatch(self):
        with self.assertRaisesRegex(RepositoryInventoryError, "BRANCH_MISMATCH"):
            build_inventory(self.root, self.config, self.commit, "main")

    def test_rejects_commit_mismatch(self):
        with self.assertRaisesRegex(RepositoryInventoryError, "COMMIT_MISMATCH"):
            build_inventory(self.root, self.config, "0" * 40, BRANCH)

    def test_rejects_symlink_instead_of_regular_blob(self):
        (self.root / "docs" / "link.md").symlink_to("matrix.md")
        git(self.root, "add", "docs/link.md")
        git(self.root, "commit", "-qm", "symlink")
        new_commit = git(self.root, "rev-parse", "HEAD").decode().strip()
        blob = git(self.root, "rev-parse", "HEAD:docs/link.md").decode().strip()
        bad = {
            "schema_version": "T0_L4_REPOSITORY_FILE_INVENTORY_V1",
            "source_branch": BRANCH,
            "files": [{"path": "docs/link.md", "git_blob_sha1": blob}],
        }
        with self.assertRaisesRegex(RepositoryInventoryError, "FILE_NOT_REGULAR"):
            build_inventory(self.root, bad, new_commit, BRANCH)

    def test_manifest_is_deterministic_for_same_commit(self):
        first = build_inventory(self.root, self.config, self.commit, BRANCH)
        second = build_inventory(self.root, self.config, self.commit, BRANCH)
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
