"""Read back one explicitly allowlisted GitHub Actions artifact and emit a SHA-256 manifest."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import sys
import urllib.error
import urllib.request
import zipfile
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path, PurePosixPath

MAX_ARCHIVE_BYTES = 8 * 1024 * 1024
MAX_MEMBER_BYTES = 1024 * 1024
MAX_TOTAL_UNCOMPRESSED_BYTES = 4 * 1024 * 1024
MAX_API_RESPONSE_BYTES = 1024 * 1024
EXPECTED_MEMBERS = frozenset({
    "l4-source-sha.txt",
    "l4-validation-scope.txt",
    "l4-lineage-contract-tests.log",
    "l4-lineage-contract-verdict.txt",
})
SCOPE_MARKER = b"T0_L4_MINIMUM_LINEAGE=GITHUB_HOSTED_READ_ONLY"
PASS_MARKER = b"L4_MINIMUM_LINEAGE_CONTRACT=PASS"


class ArtifactManifestError(ValueError):
    """Raised when artifact identity, provenance, retention, or bytes fail closed."""


def _fail(code):
    raise ArtifactManifestError(code)


def _parse_timestamp(value, field):
    if not isinstance(value, str) or not value:
        _fail("INVALID_" + field.upper())
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        _fail("INVALID_" + field.upper())
    if parsed.tzinfo is None:
        _fail("TIMEZONE_MISSING_" + field.upper())
    return parsed.astimezone(timezone.utc)


def _safe_zip_members(archive_bytes):
    if not isinstance(archive_bytes, bytes) or not archive_bytes:
        _fail("ARCHIVE_EMPTY")
    if len(archive_bytes) > MAX_ARCHIVE_BYTES:
        _fail("ARCHIVE_TOO_LARGE")
    try:
        archive = zipfile.ZipFile(BytesIO(archive_bytes), "r")
    except (zipfile.BadZipFile, OSError):
        _fail("ARCHIVE_NOT_VALID_ZIP")

    with archive:
        infos = archive.infolist()
        names = [info.filename for info in infos]
        if len(infos) > len(EXPECTED_MEMBERS):
            _fail("ARCHIVE_MEMBER_COUNT_EXCEEDED")
        if len(names) != len(set(names)):
            _fail("ARCHIVE_DUPLICATE_MEMBER")
        total_size = 0
        members = {}
        for info in infos:
            name = info.filename
            path = PurePosixPath(name)
            if (
                not name
                or path.is_absolute()
                or "\\" in name
                or ":" in name
                or any(part in ("", ".", "..") for part in path.parts)
                or info.is_dir()
            ):
                _fail("ARCHIVE_UNSAFE_MEMBER_PATH")
            if info.flag_bits & 0x1:
                _fail("ARCHIVE_ENCRYPTED_MEMBER")
            mode = (info.external_attr >> 16) & 0xFFFF
            file_type = stat.S_IFMT(mode)
            if file_type not in (0, stat.S_IFREG):
                _fail("ARCHIVE_NON_REGULAR_MEMBER")
            if info.file_size > MAX_MEMBER_BYTES:
                _fail("ARCHIVE_MEMBER_TOO_LARGE")
            total_size += info.file_size
            if total_size > MAX_TOTAL_UNCOMPRESSED_BYTES:
                _fail("ARCHIVE_TOTAL_SIZE_EXCEEDED")
            try:
                content = archive.read(info)
            except (zipfile.BadZipFile, RuntimeError, OSError):
                _fail("ARCHIVE_MEMBER_READ_FAILED")
            if len(content) != info.file_size:
                _fail("ARCHIVE_MEMBER_SIZE_MISMATCH")
            members[name] = content
    if set(members) != EXPECTED_MEMBERS:
        _fail("ARCHIVE_MEMBER_SET_MISMATCH")
    return members


def build_manifest(run_metadata, artifact_metadata, archive_bytes, expected, now=None):
    """Validate exact run/artifact binding and return a deterministic manifest object."""
    required = (
        "repository", "run_id", "artifact_id", "branch", "source_sha",
        "collector_source_sha", "workflow_path", "artifact_name",
    )
    if not isinstance(expected, dict) or any(not expected.get(key) for key in required):
        _fail("EXPECTED_IDENTITY_INCOMPLETE")
    for key in ("source_sha", "collector_source_sha"):
        if not re.fullmatch(r"[0-9a-f]{40}", str(expected[key])):
            _fail("EXPECTED_" + key.upper() + "_INVALID")
    if not isinstance(run_metadata, dict):
        _fail("RUN_METADATA_INVALID")
    if run_metadata.get("id") != expected["run_id"]:
        _fail("RUN_ID_MISMATCH")
    if run_metadata.get("head_branch") != expected["branch"]:
        _fail("RUN_BRANCH_MISMATCH")
    if run_metadata.get("head_sha") != expected["source_sha"]:
        _fail("RUN_SOURCE_SHA_MISMATCH")
    if run_metadata.get("path") != expected["workflow_path"]:
        _fail("RUN_WORKFLOW_PATH_MISMATCH")
    if run_metadata.get("status") != "completed" or run_metadata.get("conclusion") != "success":
        _fail("SOURCE_RUN_NOT_SUCCESSFUL")

    if not isinstance(artifact_metadata, list):
        _fail("ARTIFACT_LIST_INVALID")
    matching = [item for item in artifact_metadata if isinstance(item, dict) and item.get("name") == expected["artifact_name"]]
    if len(matching) != 1:
        _fail("ALLOWLISTED_ARTIFACT_NOT_UNIQUE")
    artifact = matching[0]
    artifact_id = artifact.get("id")
    if not isinstance(artifact_id, int) or isinstance(artifact_id, bool) or artifact_id != expected["artifact_id"]:
        _fail("ARTIFACT_ID_MISMATCH")
    if artifact.get("expired") is not False:
        _fail("ARTIFACT_EXPIRED_OR_UNKNOWN")
    created_at = _parse_timestamp(artifact.get("created_at"), "created_at")
    expires_at = _parse_timestamp(artifact.get("expires_at"), "expires_at")
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        _fail("NOW_TIMEZONE_MISSING")
    now = now.astimezone(timezone.utc)
    if expires_at <= now:
        _fail("ARTIFACT_RETENTION_EXPIRED")
    if created_at > now:
        _fail("ARTIFACT_CREATED_IN_FUTURE")
    size = artifact.get("size_in_bytes")
    if not isinstance(size, int) or size <= 0 or size != len(archive_bytes):
        _fail("ARTIFACT_SIZE_MISMATCH")

    members = _safe_zip_members(archive_bytes)
    if members["l4-source-sha.txt"].strip() != expected["source_sha"].encode("ascii"):
        _fail("ARTIFACT_SOURCE_MARKER_MISMATCH")
    if members["l4-validation-scope.txt"].strip() != SCOPE_MARKER:
        _fail("ARTIFACT_SCOPE_MARKER_MISMATCH")
    if members["l4-lineage-contract-verdict.txt"].strip() != PASS_MARKER:
        _fail("ARTIFACT_LINEAGE_VERDICT_NOT_PASS")
    test_log = members["l4-lineage-contract-tests.log"]
    if not re.search(rb"Ran [1-9][0-9]* tests? in [0-9.]+s", test_log) or not re.search(rb"(?m)^OK$", test_log):
        _fail("ARTIFACT_TEST_LOG_NOT_PASS")

    member_entries = [
        {"path": name, "size_bytes": len(content), "sha256": hashlib.sha256(content).hexdigest()}
        for name, content in sorted(members.items())
    ]
    return {
        "schema_version": "T0_L4_GITHUB_ARTIFACT_MANIFEST_V1",
        "repository": expected["repository"],
        "branch": expected["branch"],
        "workflow_path": expected["workflow_path"],
        "source_run_id": expected["run_id"],
        "source_run_url": run_metadata.get("html_url"),
        "source_sha": expected["source_sha"],
        "collector_source_sha": expected["collector_source_sha"],
        "artifacts": [{
            "artifact_id": artifact_id,
            "artifact_name": artifact["name"],
            "created_at": created_at.isoformat().replace("+00:00", "Z"),
            "expires_at": expires_at.isoformat().replace("+00:00", "Z"),
            "size_bytes": size,
            "archive": {
                "sha256": hashlib.sha256(archive_bytes).hexdigest(),
                "size_bytes": len(archive_bytes),
                "members": member_entries,
            },
        }],
    }


class _StripAuthorizationRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Never forward the GitHub bearer token to the signed artifact-storage host."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        redirected = super().redirect_request(req, fp, code, msg, headers, newurl)
        if redirected is not None:
            redirected.remove_header("Authorization")
            redirected.remove_header("Accept")
        return redirected


def _open_github(url, token, limit):
    request = urllib.request.Request(
        url,
        headers={
            "Authorization": "Bearer " + token,
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "t0-l4-artifact-manifest",
        },
    )
    opener = urllib.request.build_opener(_StripAuthorizationRedirectHandler())
    try:
        with opener.open(request, timeout=15) as response:
            body = response.read(limit + 1)
    except urllib.error.HTTPError as exc:
        _fail("GITHUB_HTTP_" + str(exc.code))
    except (urllib.error.URLError, TimeoutError, OSError):
        _fail("GITHUB_TRANSPORT_ERROR")
    if len(body) > limit:
        _fail("GITHUB_RESPONSE_TOO_LARGE")
    return body


def collect_allowlisted_artifact(repository, allowlist, collector_source_sha, current_branch, token):
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        _fail("REPOSITORY_ID_INVALID")
    if not token:
        _fail("GITHUB_TOKEN_MISSING")
    required = ("schema_version", "source_run_id", "source_artifact_id", "source_branch", "source_sha", "source_artifact_name", "workflow_path")
    if not isinstance(allowlist, dict) or any(not allowlist.get(key) for key in required):
        _fail("ALLOWLIST_INVALID")
    if allowlist["schema_version"] != "T0_L4_ARTIFACT_ALLOWLIST_V1":
        _fail("ALLOWLIST_SCHEMA_UNSUPPORTED")
    if allowlist["source_branch"] != current_branch:
        _fail("ALLOWLIST_BRANCH_MISMATCH")
    if not isinstance(allowlist["source_run_id"], int) or isinstance(allowlist["source_run_id"], bool) or allowlist["source_run_id"] <= 0:
        _fail("ALLOWLIST_RUN_ID_INVALID")
    if not isinstance(allowlist["source_artifact_id"], int) or isinstance(allowlist["source_artifact_id"], bool) or allowlist["source_artifact_id"] <= 0:
        _fail("ALLOWLIST_ARTIFACT_ID_INVALID")
    if not re.fullmatch(r"[0-9a-f]{40}", str(allowlist["source_sha"])):
        _fail("ALLOWLIST_SOURCE_SHA_INVALID")
    if allowlist["workflow_path"] != ".github/workflows/t0-l4-minimum-validation.yml":
        _fail("ALLOWLIST_WORKFLOW_PATH_INVALID")
    if allowlist["source_artifact_name"] != "t0-l4-minimum-lineage-" + str(allowlist["source_run_id"]):
        _fail("ALLOWLIST_ARTIFACT_NAME_INVALID")
    expected = {
        "repository": repository,
        "run_id": allowlist["source_run_id"],
        "artifact_id": allowlist["source_artifact_id"],
        "branch": allowlist["source_branch"],
        "source_sha": allowlist["source_sha"],
        "collector_source_sha": collector_source_sha,
        "workflow_path": allowlist["workflow_path"],
        "artifact_name": allowlist["source_artifact_name"],
    }
    if not re.fullmatch(r"[0-9a-f]{40}", str(collector_source_sha)):
        _fail("COLLECTOR_SOURCE_SHA_INVALID")

    base = "https://api.github.com/repos/" + repository
    try:
        run_metadata = json.loads(_open_github(f"{base}/actions/runs/{expected['run_id']}", token, MAX_API_RESPONSE_BYTES))
        listing = json.loads(_open_github(f"{base}/actions/runs/{expected['run_id']}/artifacts?per_page=100", token, MAX_API_RESPONSE_BYTES))
        compare = json.loads(_open_github(f"{base}/compare/{expected['source_sha']}...{collector_source_sha}", token, MAX_API_RESPONSE_BYTES))
    except (json.JSONDecodeError, UnicodeDecodeError):
        _fail("GITHUB_JSON_INVALID")
    if not isinstance(listing, dict) or not isinstance(listing.get("artifacts"), list):
        _fail("GITHUB_ARTIFACT_LIST_INVALID")
    if listing.get("total_count") != len(listing["artifacts"]):
        _fail("GITHUB_ARTIFACT_LIST_TRUNCATED")
    if not isinstance(compare, dict) or compare.get("status") not in ("ahead", "identical") or compare.get("behind_by") != 0:
        _fail("ALLOWLISTED_SOURCE_NOT_ANCESTOR")
    matching = [item for item in listing["artifacts"] if isinstance(item, dict) and item.get("name") == expected["artifact_name"]]
    if len(matching) != 1 or matching[0].get("id") != expected["artifact_id"]:
        _fail("ALLOWLISTED_ARTIFACT_ID_OR_NAME_MISMATCH")
    archive_url = f"{base}/actions/artifacts/{expected['artifact_id']}/zip"
    archive_bytes = _open_github(archive_url, token, MAX_ARCHIVE_BYTES)
    return build_manifest(run_metadata, listing["artifacts"], archive_bytes, expected)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--allowlist", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args(argv)
    try:
        repository = os.environ["GITHUB_REPOSITORY"]
        collector_source_sha = os.environ["GITHUB_SHA"]
        current_branch = os.environ["GITHUB_REF_NAME"]
        token = os.environ["GITHUB_TOKEN"]
        allowlist = json.loads(Path(args.allowlist).read_text(encoding="utf-8"))
        manifest = collect_allowlisted_artifact(repository, allowlist, collector_source_sha, current_branch, token)
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        manifest_bytes = (json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
        manifest_path = output_dir / "l4-artifact-manifest.json"
        digest_path = output_dir / "l4-artifact-manifest.sha256"
        manifest_path.write_bytes(manifest_bytes)
        digest_path.write_text(hashlib.sha256(manifest_bytes).hexdigest() + "  l4-artifact-manifest.json\n", encoding="ascii")
    except ArtifactManifestError as exc:
        print("L4_ARTIFACT_MANIFEST=BLOCKED " + str(exc), file=sys.stderr)
        return 1
    except (KeyError, ValueError, OSError):
        print("L4_ARTIFACT_MANIFEST=BLOCKED CONFIGURATION_INVALID", file=sys.stderr)
        return 1
    print("L4_ARTIFACT_MANIFEST=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
