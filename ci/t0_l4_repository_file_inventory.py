"""Build a deterministic inventory of explicitly allowlisted GitHub repository files."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath

MAX_FILE_BYTES = 2 * 1024 * 1024
MAX_TOTAL_BYTES = 16 * 1024 * 1024


class RepositoryInventoryError(ValueError):
    """Raised when exact-commit repository-file identity cannot be proven."""


def _fail(code: str) -> None:
    raise RepositoryInventoryError(code)


def validate_config(config: object, current_branch: str) -> tuple[dict, ...]:
    if not isinstance(config, dict):
        _fail("CONFIG_INVALID")
    if config.get("schema_version") != "T0_L4_REPOSITORY_FILE_INVENTORY_V1":
        _fail("SCHEMA_UNSUPPORTED")
    source_branch = config.get("source_branch")
    if not isinstance(source_branch, str) or not source_branch or source_branch != current_branch:
        _fail("BRANCH_MISMATCH")
    files = config.get("files")
    if not isinstance(files, list) or not 1 <= len(files) <= 100:
        _fail("FILE_COUNT_INVALID")
    seen = set()
    normalized = []
    for item in files:
        if not isinstance(item, dict):
            _fail("FILE_ENTRY_INVALID")
        path = item.get("path")
        blob_sha = item.get("git_blob_sha1")
        if not isinstance(path, str) or not path or len(path) > 512:
            _fail("FILE_PATH_INVALID")
        posix = PurePosixPath(path)
        if (
            path.startswith("/")
            or "\\" in path
            or ":" in path
            or any(part in ("", ".", "..", ".git") for part in path.split("/"))
            or not re.fullmatch(r"[A-Za-z0-9._/-]+", path)
            or posix.is_absolute()
        ):
            _fail("FILE_PATH_UNSAFE")
        if path in seen:
            _fail("DUPLICATE_FILE_PATH")
        seen.add(path)
        if not isinstance(blob_sha, str) or not re.fullmatch(r"[0-9a-f]{40}", blob_sha):
            _fail("GIT_BLOB_SHA_INVALID")
        normalized.append({"path": path, "git_blob_sha1": blob_sha})
    return tuple(sorted(normalized, key=lambda item: item["path"]))


def _git(repo_root: Path, *args: str, max_output_bytes: int = MAX_FILE_BYTES) -> bytes:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=repo_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        _fail("GIT_COMMAND_FAILED")
    if result.returncode != 0:
        _fail("GIT_COMMAND_FAILED")
    if len(result.stdout) > max_output_bytes:
        _fail("GIT_OBJECT_TOO_LARGE")
    return result.stdout


def _git_blob_sha1(content: bytes) -> str:
    header = b"blob " + str(len(content)).encode("ascii") + bytes([0])
    return hashlib.sha1(header + content).hexdigest()


def build_inventory(
    repo_root: Path,
    config: object,
    expected_commit: str,
    current_branch: str,
    repository: str = "",
) -> dict:
    if not isinstance(expected_commit, str) or not re.fullmatch(r"[0-9a-f]{40}", expected_commit):
        _fail("EXPECTED_COMMIT_INVALID")
    files = validate_config(config, current_branch)
    actual_commit = _git(repo_root, "rev-parse", "HEAD", max_output_bytes=128).decode("ascii").strip()
    if actual_commit != expected_commit:
        _fail("COMMIT_MISMATCH")

    entries = []
    total_bytes = 0
    for item in files:
        path = item["path"]
        tree_output = _git(
            repo_root, "ls-tree", "-z", "HEAD", "--", ":(literal)" + path,
            max_output_bytes=64 * 1024,
        )
        records = [record for record in tree_output.split(bytes([0])) if record]
        if len(records) != 1:
            _fail("FILE_PATH_MISSING_OR_AMBIGUOUS")
        try:
            metadata, returned_path = records[0].split(b"\t", 1)
            mode, object_type, actual_blob_sha = metadata.decode("ascii").split(" ")
            returned_path_text = returned_path.decode("utf-8")
        except (ValueError, UnicodeDecodeError):
            _fail("GIT_TREE_ENTRY_INVALID")
        if returned_path_text != path:
            _fail("FILE_PATH_MISMATCH")
        if object_type != "blob" or mode not in ("100644", "100755"):
            _fail("FILE_NOT_REGULAR")
        if actual_blob_sha != item["git_blob_sha1"]:
            _fail("GIT_BLOB_SHA_MISMATCH")
        content = _git(repo_root, "cat-file", "blob", actual_blob_sha, max_output_bytes=MAX_FILE_BYTES)
        if _git_blob_sha1(content) != actual_blob_sha:
            _fail("GIT_OBJECT_CONTENT_MISMATCH")
        total_bytes += len(content)
        if total_bytes > MAX_TOTAL_BYTES:
            _fail("GIT_INVENTORY_TOTAL_SIZE_EXCEEDED")
        entries.append({
            "path": path,
            "git_blob_sha1": actual_blob_sha,
            "size_bytes": len(content),
            "sha256": hashlib.sha256(content).hexdigest(),
        })

    return {
        "schema_version": "T0_L4_REPOSITORY_FILE_INVENTORY_V1",
        "repository": repository,
        "branch": current_branch,
        "source_commit": actual_commit,
        "file_count": len(entries),
        "total_size_bytes": total_bytes,
        "files": entries,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args(argv)
    try:
        repository = os.environ["GITHUB_REPOSITORY"]
        expected_commit = os.environ["GITHUB_SHA"]
        branch = os.environ["GITHUB_REF_NAME"]
        config = json.loads(Path(args.config).read_text(encoding="utf-8"))
        inventory = build_inventory(Path.cwd(), config, expected_commit, branch, repository)
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        payload = (json.dumps(inventory, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
        manifest = output_dir / "l4-repository-file-inventory.json"
        sidecar = output_dir / "l4-repository-file-inventory.sha256"
        manifest.write_bytes(payload)
        sidecar.write_text(hashlib.sha256(payload).hexdigest() + "  " + manifest.name + "\n", encoding="ascii")
    except RepositoryInventoryError as exc:
        print("L4_REPOSITORY_FILE_INVENTORY=BLOCKED " + str(exc), file=sys.stderr)
        return 1
    except (KeyError, OSError, ValueError, UnicodeError):
        print("L4_REPOSITORY_FILE_INVENTORY=BLOCKED CONFIGURATION_INVALID", file=sys.stderr)
        return 1
    print("L4_REPOSITORY_FILE_INVENTORY=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
