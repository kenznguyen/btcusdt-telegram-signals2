"""R22.5: verify the pre-holdout Phase14 ZIP without unpickling binaries."""
import hashlib
import tempfile
import unittest
import zipfile
from pathlib import Path

from quant_system.phase22_archive_integrity import (
    ArchiveIntegrityError,
    audit_archive,
)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def make_archive(path: Path, *, include_candidate=True, duplicate_candidate=False):
    members = {
        "artifacts/phase3/native/phase13b-unsealed-model-candidate.json": b'{"model":"metadata"}',
        "artifacts/phase3/native/phase13b-oos-protocol.json": b'{"protocol":"frozen"}',
    }
    if include_candidate:
        members["artifacts/phase3/native/phase13b-unsealed-model-candidate.joblib"] = b"opaque candidate bytes"
    if duplicate_candidate:
        members["duplicate/phase13b-unsealed-model-candidate.joblib"] = b"second candidate"
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_STORED) as archive:
        for name, payload in members.items():
            archive.writestr(name, payload)
    return members


class Phase22ArchiveIntegrityTests(unittest.TestCase):
    def test_valid_archive_hashes_members_and_reports_bad_repo_copy_separately(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive = root / "original.zip"
            current = root / "repo-copy.joblib"
            members = make_archive(archive)
            current.write_bytes(b"wrong repo copy")
            result = audit_archive(
                archive,
                current,
                expected_archive_sha256=sha256_bytes(archive.read_bytes()),
                expected_bundle_sha256=sha256_bytes(
                    members["artifacts/phase3/native/phase13b-unsealed-model-candidate.joblib"]
                ),
                expected_metadata_sha256=sha256_bytes(
                    members["artifacts/phase3/native/phase13b-unsealed-model-candidate.json"]
                ),
                expected_protocol_sha256=sha256_bytes(
                    members["artifacts/phase3/native/phase13b-oos-protocol.json"]
                ),
            )
            self.assertTrue(result["archive_integrity_verified"])
            self.assertFalse(result["current_repo_bundle_matches_registered"])
            self.assertFalse(result["unpickle_performed"])
            self.assertEqual(result["candidate_member_path"],
                             "artifacts/phase3/native/phase13b-unsealed-model-candidate.joblib")

    def test_archive_digest_mismatch_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive = root / "original.zip"
            current = root / "repo-copy.joblib"
            members = make_archive(archive)
            current.write_bytes(b"wrong")
            with self.assertRaisesRegex(ArchiveIntegrityError, "ARCHIVE_SHA256_MISMATCH"):
                audit_archive(
                    archive,
                    current,
                    expected_archive_sha256="0" * 64,
                    expected_bundle_sha256=sha256_bytes(
                        members["artifacts/phase3/native/phase13b-unsealed-model-candidate.joblib"]
                    ),
                    expected_metadata_sha256=sha256_bytes(
                        members["artifacts/phase3/native/phase13b-unsealed-model-candidate.json"]
                    ),
                    expected_protocol_sha256=sha256_bytes(
                        members["artifacts/phase3/native/phase13b-oos-protocol.json"]
                    ),
                )

    def test_missing_candidate_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive = root / "original.zip"
            current = root / "repo-copy.joblib"
            make_archive(archive, include_candidate=False)
            current.write_bytes(b"wrong")
            with self.assertRaisesRegex(ArchiveIntegrityError, "CANDIDATE_MEMBER_MISSING"):
                audit_archive(
                    archive, current,
                    expected_archive_sha256=sha256_bytes(archive.read_bytes()),
                    expected_bundle_sha256="0" * 64,
                    expected_metadata_sha256="0" * 64,
                    expected_protocol_sha256="0" * 64,
                )

    def test_duplicate_candidate_members_fail_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive = root / "original.zip"
            current = root / "repo-copy.joblib"
            make_archive(archive, duplicate_candidate=True)
            current.write_bytes(b"wrong")
            with self.assertRaisesRegex(ArchiveIntegrityError, "CANDIDATE_MEMBER_AMBIGUOUS"):
                audit_archive(
                    archive, current,
                    expected_archive_sha256=sha256_bytes(archive.read_bytes()),
                    expected_bundle_sha256="0" * 64,
                    expected_metadata_sha256="0" * 64,
                    expected_protocol_sha256="0" * 64,
                )

    def test_unsafe_archive_path_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive = root / "original.zip"
            current = root / "repo-copy.joblib"
            with zipfile.ZipFile(archive, "w") as z:
                z.writestr("../escape.joblib", b"no extraction")
            current.write_bytes(b"wrong")
            with self.assertRaisesRegex(ArchiveIntegrityError, "UNSAFE_ARCHIVE_MEMBER_PATH"):
                audit_archive(
                    archive, current,
                    expected_archive_sha256=sha256_bytes(archive.read_bytes()),
                    expected_bundle_sha256="0" * 64,
                    expected_metadata_sha256="0" * 64,
                    expected_protocol_sha256="0" * 64,
                )


if __name__ == "__main__":
    unittest.main()
