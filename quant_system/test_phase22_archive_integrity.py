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
    }
    if include_candidate:
        members["artifacts/phase3/native/phase13b-unsealed-model-candidate.joblib"] = b"opaque candidate bytes"
    if duplicate_candidate:
        members["duplicate/phase13b-unsealed-model-candidate.joblib"] = b"second candidate"
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_STORED) as archive:
        for name, payload in members.items():
            archive.writestr(name, payload)
    return members


def make_protocol(path: Path) -> bytes:
    payload = b'{"protocol":"frozen"}'
    path.write_bytes(payload)
    return payload


class Phase22ArchiveIntegrityTests(unittest.TestCase):
    def test_valid_archive_hashes_members_and_separate_protocol_and_reports_bad_copy(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive = root / "original.zip"
            current = root / "repo-copy.joblib"
            protocol = root / "phase13b-oos-protocol.json"
            members = make_archive(archive)
            protocol_bytes = make_protocol(protocol)
            current.write_bytes(b"wrong repo copy")
            result = audit_archive(
                archive,
                current,
                protocol,
                expected_archive_sha256=sha256_bytes(archive.read_bytes()),
                expected_bundle_sha256=sha256_bytes(
                    members["artifacts/phase3/native/phase13b-unsealed-model-candidate.joblib"]
                ),
                expected_metadata_sha256=sha256_bytes(
                    members["artifacts/phase3/native/phase13b-unsealed-model-candidate.json"]
                ),
                expected_protocol_sha256=sha256_bytes(protocol_bytes),
            )
            self.assertTrue(result["archive_integrity_verified"])
            self.assertTrue(result["protocol_sha256_match"])
            self.assertFalse(result["current_repo_bundle_matches_registered"])
            self.assertFalse(result["unpickle_performed"])
            self.assertEqual(result["candidate_member_path"],
                             "artifacts/phase3/native/phase13b-unsealed-model-candidate.joblib")

    def test_archive_digest_mismatch_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive = root / "original.zip"
            current = root / "repo-copy.joblib"
            protocol = root / "phase13b-oos-protocol.json"
            members = make_archive(archive)
            protocol_bytes = make_protocol(protocol)
            current.write_bytes(b"wrong")
            with self.assertRaisesRegex(ArchiveIntegrityError, "ARCHIVE_SHA256_MISMATCH"):
                audit_archive(
                    archive,
                    current,
                    protocol,
                    expected_archive_sha256="0" * 64,
                    expected_bundle_sha256=sha256_bytes(
                        members["artifacts/phase3/native/phase13b-unsealed-model-candidate.joblib"]
                    ),
                    expected_metadata_sha256=sha256_bytes(
                        members["artifacts/phase3/native/phase13b-unsealed-model-candidate.json"]
                    ),
                    expected_protocol_sha256=sha256_bytes(protocol_bytes),
                )

    def test_missing_candidate_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive = root / "original.zip"
            current = root / "repo-copy.joblib"
            protocol = root / "phase13b-oos-protocol.json"
            make_archive(archive, include_candidate=False)
            protocol_bytes = make_protocol(protocol)
            current.write_bytes(b"wrong")
            with self.assertRaisesRegex(ArchiveIntegrityError, "CANDIDATE_MEMBER_MISSING"):
                audit_archive(
                    archive, current, protocol,
                    expected_archive_sha256=sha256_bytes(archive.read_bytes()),
                    expected_bundle_sha256="0" * 64,
                    expected_metadata_sha256="0" * 64,
                    expected_protocol_sha256=sha256_bytes(protocol_bytes),
                )

    def test_duplicate_candidate_members_fail_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive = root / "original.zip"
            current = root / "repo-copy.joblib"
            protocol = root / "phase13b-oos-protocol.json"
            make_archive(archive, duplicate_candidate=True)
            protocol_bytes = make_protocol(protocol)
            current.write_bytes(b"wrong")
            with self.assertRaisesRegex(ArchiveIntegrityError, "CANDIDATE_MEMBER_AMBIGUOUS"):
                audit_archive(
                    archive, current, protocol,
                    expected_archive_sha256=sha256_bytes(archive.read_bytes()),
                    expected_bundle_sha256="0" * 64,
                    expected_metadata_sha256="0" * 64,
                    expected_protocol_sha256=sha256_bytes(protocol_bytes),
                )

    def test_unsafe_archive_path_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive = root / "original.zip"
            current = root / "repo-copy.joblib"
            protocol = root / "phase13b-oos-protocol.json"
            with zipfile.ZipFile(archive, "w") as z:
                z.writestr("../escape.joblib", b"no extraction")
            protocol_bytes = make_protocol(protocol)
            current.write_bytes(b"wrong")
            with self.assertRaisesRegex(ArchiveIntegrityError, "UNSAFE_ARCHIVE_MEMBER_PATH"):
                audit_archive(
                    archive, current, protocol,
                    expected_archive_sha256=sha256_bytes(archive.read_bytes()),
                    expected_bundle_sha256="0" * 64,
                    expected_metadata_sha256="0" * 64,
                    expected_protocol_sha256=sha256_bytes(protocol_bytes),
                )

    def test_protocol_file_is_verified_separately_from_archive(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive = root / "original.zip"
            current = root / "repo-copy.joblib"
            protocol = root / "phase13b-oos-protocol.json"
            members = make_archive(archive)
            make_protocol(protocol)
            current.write_bytes(b"wrong")
            with self.assertRaisesRegex(ArchiveIntegrityError, "PROTOCOL_SHA256_MISMATCH"):
                audit_archive(
                    archive, current, protocol,
                    expected_archive_sha256=sha256_bytes(archive.read_bytes()),
                    expected_bundle_sha256=sha256_bytes(
                        members["artifacts/phase3/native/phase13b-unsealed-model-candidate.joblib"]
                    ),
                    expected_metadata_sha256=sha256_bytes(
                        members["artifacts/phase3/native/phase13b-unsealed-model-candidate.json"]
                    ),
                    expected_protocol_sha256="0" * 64,
                )


if __name__ == "__main__":
    unittest.main()
