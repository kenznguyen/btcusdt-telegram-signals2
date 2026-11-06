"""Fail-closed source, workflow and fixture-byte provenance for synthetic CI evidence."""
import hashlib
import json
import re
from pathlib import Path

_SHA40 = re.compile(r"^[0-9a-f]{40}$")
_SHA64 = re.compile(r"^[0-9a-f]{64}$")


def _required(name, value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"missing or invalid {name}")
    return value.strip()


def _read_descriptor(label, path, expected_source_sha=None):
    try:
        raw = Path(path).read_bytes()
        value = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"fixture {label} descriptor unavailable or invalid") from exc
    if not isinstance(value, dict):
        raise ValueError(f"fixture {label} descriptor must be an object")
    observed = value.get("generator_source_sha")
    if expected_source_sha is not None and observed != expected_source_sha:
        raise ValueError(f"fixture {label} source SHA mismatch")
    return {"source_sha": observed, "descriptor_sha256": hashlib.sha256(raw).hexdigest()}


def build_provenance(*, source_sha, run_id, run_attempt, repository, ref,
                     workflow_ref, workflow_file, descriptor_a, descriptor_b):
    source_sha = _required("source_sha", source_sha)
    if not _SHA40.fullmatch(source_sha):
        raise ValueError("invalid source_sha")
    run_id = _required("run_id", str(run_id))
    run_attempt = _required("run_attempt", str(run_attempt))
    if not run_id.isdigit() or int(run_id) <= 0:
        raise ValueError("invalid run_id")
    if not run_attempt.isdigit() or int(run_attempt) <= 0:
        raise ValueError("invalid run_attempt")
    workflow_sha = hashlib.sha256(Path(workflow_file).read_bytes()).hexdigest()
    descriptors = {
        "A": _read_descriptor("A", descriptor_a, source_sha),
        "B": _read_descriptor("B", descriptor_b, source_sha),
    }
    return {
        "schema": "p1.8.synthetic-provenance.v2",
        "source_sha": source_sha,
        "run_id": int(run_id),
        "run_attempt": int(run_attempt),
        "repository": _required("repository", repository),
        "ref": _required("ref", ref),
        "workflow_ref": _required("workflow_ref", workflow_ref),
        "workflow_sha256": workflow_sha,
        "fixture_descriptors": descriptors,
        "artifact_id": "NOT_AVAILABLE_AT_BUILD_TIME",
        "artifact_payload_digest": "NOT_AVAILABLE_AT_BUILD_TIME",
    }


def verify_provenance(data, *, expected_source_sha, expected_run_id,
                      expected_workflow_sha256, descriptor_a, descriptor_b):
    required = ("schema", "source_sha", "run_id", "run_attempt", "repository", "ref",
                "workflow_ref", "workflow_sha256", "fixture_descriptors")
    if not isinstance(data, dict) or any(key not in data for key in required):
        raise ValueError("missing required provenance fields")
    if data["schema"] != "p1.8.synthetic-provenance.v2":
        raise ValueError("unsupported provenance schema")
    if (not isinstance(expected_source_sha, str)
            or data["source_sha"] != expected_source_sha
            or not _SHA40.fullmatch(str(data["source_sha"]))):
        raise ValueError("source_sha mismatch")
    if type(data["run_id"]) is not int or data["run_id"] != expected_run_id:
        raise ValueError("run_id mismatch")
    if type(data["run_attempt"]) is not int or data["run_attempt"] <= 0:
        raise ValueError("invalid run_attempt")
    if (not isinstance(data["workflow_sha256"], str)
            or not _SHA64.fullmatch(data["workflow_sha256"])
            or data["workflow_sha256"] != expected_workflow_sha256):
        raise ValueError("workflow_sha256 mismatch")
    descriptors = data["fixture_descriptors"]
    if not isinstance(descriptors, dict):
        raise ValueError("missing or invalid fixture_descriptors")
    for label, path in (("A", descriptor_a), ("B", descriptor_b)):
        recorded = descriptors.get(label)
        if not isinstance(recorded, dict):
            raise ValueError(f"fixture {label} provenance missing")
        actual = _read_descriptor(label, path, expected_source_sha)
        recorded_digest = recorded.get("descriptor_sha256")
        if not isinstance(recorded_digest, str) or not _SHA64.fullmatch(recorded_digest):
            raise ValueError(f"descriptor {label} digest invalid")
        if recorded_digest != actual["descriptor_sha256"]:
            raise ValueError(f"descriptor {label} SHA-256 mismatch")
        if recorded.get("source_sha") != actual["source_sha"]:
            raise ValueError(f"fixture {label} source SHA mismatch")
    for key in ("repository", "ref", "workflow_ref"):
        _required(key, data[key])
    return True


def main():
    import argparse
    import os

    parser = argparse.ArgumentParser()
    parser.add_argument("--workflow-file", required=True)
    parser.add_argument("--descriptor-a", required=True)
    parser.add_argument("--descriptor-b", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    source_sha = os.environ.get("GITHUB_SHA", "")
    workflow_digest = hashlib.sha256(Path(args.workflow_file).read_bytes()).hexdigest()
    data = build_provenance(
        source_sha=source_sha,
        run_id=os.environ.get("GITHUB_RUN_ID", ""),
        run_attempt=os.environ.get("GITHUB_RUN_ATTEMPT", ""),
        repository=os.environ.get("GITHUB_REPOSITORY", ""),
        ref=os.environ.get("GITHUB_REF", ""),
        workflow_ref=os.environ.get("GITHUB_WORKFLOW_REF", ""),
        workflow_file=args.workflow_file,
        descriptor_a=args.descriptor_a,
        descriptor_b=args.descriptor_b,
    )
    verify_provenance(
        data, expected_source_sha=source_sha,
        expected_run_id=int(os.environ.get("GITHUB_RUN_ID", "0")),
        expected_workflow_sha256=workflow_digest,
        descriptor_a=args.descriptor_a, descriptor_b=args.descriptor_b,
    )
    Path(args.output).write_text(
        json.dumps(data, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
