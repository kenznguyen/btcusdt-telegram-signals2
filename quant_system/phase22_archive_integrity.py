"""R22.5: byte-level verification of the pre-holdout Phase14 archive.

This module hashes ZIP members as opaque bytes. It never extracts files or
loads/unpickles the frozen model.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import stat
import zipfile
from pathlib import Path, PurePosixPath

EXPECTED_ARCHIVE_SHA256 = "b64f39bd70c27c8d6abed1795ee06504c108eed42ebdab98ce375a6449b5b035"
EXPECTED_ARCHIVE_GIT_BLOB_SHA1 = "17ec47fcbab047a540b1b1d2faad6a73182b5ab5"
EXPECTED_BUNDLE_SHA256 = "918dc4737ee432df8f7f9d2c3e561ac3983aaf56d8791a731a55624ab836b81f"
EXPECTED_BUNDLE_MEMBER = "artifacts/phase3/native/phase13b-unsealed-model-candidate.joblib"
EXPECTED_METADATA_SHA256 = "07e9c1b65df7a477de8ee14c51d47325932e6bf9a0732f3ea64e3118abcac3e5"
EXPECTED_METADATA_BASENAME = "phase13b-unsealed-model-candidate.json"
EXPECTED_PROTOCOL_SHA256 = "b10d63c952a40fa70a3d4dfed2d952d676a888a0f72832734d3ff8d8c14c5b6e"
AUDITED_BAD_COPY_SHA256 = "51c8474d0bdb93140523bd127cf89a9afb69d299e143518c8da90a4487ad3874"
AUDITED_BAD_COPY_GIT_BLOB_SHA1 = "91283dde513e24b9f87a936220a09e5f78612a49"

MAX_MEMBER_BYTES = 64 * 1024 * 1024
MAX_TOTAL_UNCOMPRESSED_BYTES = 128 * 1024 * 1024


class ArchiveIntegrityError(ValueError):
    pass


def _hash_file(path: Path, algorithm: str) -> str:
    digest = hashlib.new(algorithm)
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git_blob_sha1(path: Path) -> str:
    size = path.stat().st_size
    digest = hashlib.sha1()
    digest.update(f"blob {size}\0".encode("ascii"))
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _validate_member(info: zipfile.ZipInfo) -> None:
    name = info.filename
    path = PurePosixPath(name)
    mode = info.external_attr >> 16
    if (
        not name
        or "\\" in name
        or path.is_absolute()
        or any(part in ("", ".", "..") for part in path.parts)
        or (len(path.parts) > 0 and ":" in path.parts[0])
        or stat.S_ISLNK(mode)
    ):
        raise ArchiveIntegrityError("UNSAFE_ARCHIVE_MEMBER_PATH")
    if info.file_size > MAX_MEMBER_BYTES:
        raise ArchiveIntegrityError("ARCHIVE_MEMBER_SIZE_LIMIT")
    if info.flag_bits & 0x1:
        raise ArchiveIntegrityError("ENCRYPTED_ARCHIVE_MEMBER_UNSUPPORTED")


def _unique_member(infos: list[zipfile.ZipInfo], basename: str, code: str) -> zipfile.ZipInfo:
    matches = [
        info for info in infos
        if not info.is_dir() and PurePosixPath(info.filename).name == basename
    ]
    if not matches:
        raise ArchiveIntegrityError(code + "_MISSING")
    if len(matches) != 1:
        raise ArchiveIntegrityError(code + "_AMBIGUOUS")
    return matches[0]


def _member_sha256(archive: zipfile.ZipFile, info: zipfile.ZipInfo) -> str:
    digest = hashlib.sha256()
    with archive.open(info, "r") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def audit_archive(
    archive_path: str | Path,
    current_bundle_path: str | Path,
    protocol_path: str | Path,
    *,
    expected_archive_sha256: str,
    expected_bundle_sha256: str,
    expected_metadata_sha256: str,
    expected_protocol_sha256: str,
    expected_archive_git_blob_sha1: str | None = None,
    expected_current_copy_sha256: str | None = None,
    expected_current_copy_git_blob_sha1: str | None = None,
) -> dict:
    archive_path = Path(archive_path)
    current_bundle_path = Path(current_bundle_path)
    protocol_path = Path(protocol_path)
    if not archive_path.is_file() or archive_path.is_symlink():
        raise ArchiveIntegrityError("ARCHIVE_FILE_MISSING_OR_UNSAFE")

    archive_sha = _hash_file(archive_path, "sha256")
    if archive_sha != expected_archive_sha256:
        raise ArchiveIntegrityError("ARCHIVE_SHA256_MISMATCH")

    archive_blob_sha = _git_blob_sha1(archive_path)
    if (
        expected_archive_git_blob_sha1 is not None
        and archive_blob_sha != expected_archive_git_blob_sha1
    ):
        raise ArchiveIntegrityError("ARCHIVE_GIT_BLOB_SHA1_MISMATCH")

    try:
        with zipfile.ZipFile(archive_path, "r") as archive:
            infos = archive.infolist()
            if not infos:
                raise ArchiveIntegrityError("ARCHIVE_EMPTY")
            total_size = 0
            for info in infos:
                _validate_member(info)
                if not info.is_dir():
                    total_size += info.file_size
            if total_size > MAX_TOTAL_UNCOMPRESSED_BYTES:
                raise ArchiveIntegrityError("ARCHIVE_TOTAL_SIZE_LIMIT")

            candidate = _unique_member(
                infos, PurePosixPath(EXPECTED_BUNDLE_MEMBER).name, "CANDIDATE_MEMBER"
            )
            if candidate.filename != EXPECTED_BUNDLE_MEMBER:
                raise ArchiveIntegrityError("CANDIDATE_MEMBER_PATH_MISMATCH")
            metadata = _unique_member(
                infos, EXPECTED_METADATA_BASENAME, "METADATA_MEMBER"
            )

            candidate_sha = _member_sha256(archive, candidate)
            metadata_sha = _member_sha256(archive, metadata)
    except zipfile.BadZipFile as exc:
        raise ArchiveIntegrityError("INVALID_ZIP_ARCHIVE") from exc

    if candidate_sha != expected_bundle_sha256:
        raise ArchiveIntegrityError("EMBEDDED_CANDIDATE_SHA256_MISMATCH")
    if metadata_sha != expected_metadata_sha256:
        raise ArchiveIntegrityError("EMBEDDED_METADATA_SHA256_MISMATCH")
    if not protocol_path.is_file() or protocol_path.is_symlink():
        raise ArchiveIntegrityError("PROTOCOL_FILE_MISSING_OR_UNSAFE")
    protocol_sha = _hash_file(protocol_path, "sha256")
    if protocol_sha != expected_protocol_sha256:
        raise ArchiveIntegrityError("PROTOCOL_SHA256_MISMATCH")

    current_present = current_bundle_path.is_file() and not current_bundle_path.is_symlink()
    current_sha = _hash_file(current_bundle_path, "sha256") if current_present else None
    current_blob_sha = _git_blob_sha1(current_bundle_path) if current_present else None
    current_matches_registered = current_sha == expected_bundle_sha256
    current_matches_audited_copy = (
        current_sha == expected_current_copy_sha256
        and (
            expected_current_copy_git_blob_sha1 is None
            or current_blob_sha == expected_current_copy_git_blob_sha1
        )
    ) if expected_current_copy_sha256 is not None else None

    return {
        "schemaVersion": 1,
        "audit": "R22_5_PHASE14_ORIGINAL_ARCHIVE_BYTE_INTEGRITY",
        "archive_path": str(archive_path),
        "archive_sha256": archive_sha,
        "expected_archive_sha256": expected_archive_sha256,
        "archive_git_blob_sha1": archive_blob_sha,
        "expected_archive_git_blob_sha1": expected_archive_git_blob_sha1,
        "candidate_member_path": candidate.filename,
        "candidate_sha256": candidate_sha,
        "expected_candidate_sha256": expected_bundle_sha256,
        "metadata_member_path": metadata.filename,
        "metadata_sha256": metadata_sha,
        "expected_metadata_sha256": expected_metadata_sha256,
        "protocol_path": str(protocol_path),
        "protocol_sha256": protocol_sha,
        "protocol_sha256_match": protocol_sha == expected_protocol_sha256,
        "expected_protocol_sha256": expected_protocol_sha256,
        "current_repo_bundle_path": str(current_bundle_path),
        "current_repo_bundle_present": current_present,
        "current_repo_bundle_sha256": current_sha,
        "current_repo_bundle_git_blob_sha1": current_blob_sha,
        "current_repo_bundle_matches_registered": current_matches_registered,
        "current_repo_bundle_matches_audited_copy": current_matches_audited_copy,
        "archive_integrity_verified": True,
        "restoration_required": not current_matches_registered,
        "archive_extracted": False,
        "unpickle_performed": False,
        "live_orders_enabled": False,
        "oos_certified": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", required=True)
    parser.add_argument("--current-bundle", required=True)
    parser.add_argument("--protocol-file", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    try:
        result = audit_archive(
            args.archive,
            args.current_bundle,
            args.protocol_file,
            expected_archive_sha256=EXPECTED_ARCHIVE_SHA256,
            expected_archive_git_blob_sha1=EXPECTED_ARCHIVE_GIT_BLOB_SHA1,
            expected_bundle_sha256=EXPECTED_BUNDLE_SHA256,
            expected_metadata_sha256=EXPECTED_METADATA_SHA256,
            expected_protocol_sha256=EXPECTED_PROTOCOL_SHA256,
            expected_current_copy_sha256=AUDITED_BAD_COPY_SHA256,
            expected_current_copy_git_blob_sha1=AUDITED_BAD_COPY_GIT_BLOB_SHA1,
        )
    except (OSError, ArchiveIntegrityError) as exc:
        result = {
            "schemaVersion": 1,
            "audit": "R22_5_PHASE14_ORIGINAL_ARCHIVE_BYTE_INTEGRITY",
            "archive_integrity_verified": False,
            "errors": [str(exc) if isinstance(exc, ArchiveIntegrityError) else "ARCHIVE_IO_ERROR"],
            "archive_extracted": False,
            "unpickle_performed": False,
            "live_orders_enabled": False,
            "oos_certified": False,
        }

    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf8")
    print(json.dumps({
        "archive_integrity_verified": result.get("archive_integrity_verified"),
        "candidate_sha256": result.get("candidate_sha256"),
        "current_repo_bundle_matches_registered": result.get("current_repo_bundle_matches_registered"),
        "restoration_required": result.get("restoration_required"),
        "errors": result.get("errors", []),
    }, sort_keys=True))
    return 0 if result.get("archive_integrity_verified") is True else 2


if __name__ == "__main__":
    raise SystemExit(main())
