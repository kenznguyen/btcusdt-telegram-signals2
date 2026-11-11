"""Deterministic, in-memory S1 synthetic preflight runner.

This module defines a frozen synthetic recipe and preflight checks only.
It has no CLI, persistence, environment, clock, network, provider, database,
or runtime integration. Calling prepare_preflight is reserved to focused
unit tests in the G0.40-A scope; actual G0.41 measurement needs new approval.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping

from tools import s1_measurement_harness as harness

CASE_IDS = ("SYN-01", "SYN-29", "SYN-30", "SYN-31", "SYN-32")
EXPECTED_FIXTURE_COUNT = 22
CORPUS_REVISION = "S1-SYNTHETIC-PREFLIGHT-RECIPE-V1"
EXPECTED_CASE_COUNTS = {
    "SYN-01": 11,
    "SYN-29": 3,
    "SYN-30": 2,
    "SYN-31": 3,
    "SYN-32": 3,
}
_SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")
_COMMIT_RE = re.compile(r"[0-9a-f]{40,64}\Z")


def _fixture_value(fixture_id: str, case_id: str, fixture_type: str) -> dict:
    return {
        "schema_version": harness.SCHEMA_VERSION,
        "fixture_id": fixture_id,
        "case_id": case_id,
        "fixture_type": fixture_type,
        "subject": {
            "object_id": "syn-object-001",
            "version_id": "syn-version-001",
            "namespace": "syn-namespace-001",
        },
        "purpose": harness.PURPOSE,
        "claims": {},
    }


def _encode(value: dict) -> bytes:
    return json.dumps(value, ensure_ascii=True, separators=(",", ":")).encode("utf-8")


def _positive_bytes(fixture_id: str, fixture_type: str) -> bytes:
    return _encode(_fixture_value(fixture_id, "SYN-01", fixture_type))


def _negative_fixture(case_id: str, fixture_id: str, fixture_type: str, variant: int):
    value = _fixture_value(fixture_id, case_id, fixture_type)
    if case_id == "SYN-29":
        raw = _encode(value)
        if variant == 0:
            needle = b'"fixture_id":"' + fixture_id.encode("ascii") + b'"'
            return raw.replace(needle, needle + needle, 1), "PARSE_DUPLICATE_KEY"
        if variant == 1:
            return b'{"outer":{"duplicate":1,"duplicate":2}}', "PARSE_DUPLICATE_KEY"
        return b'{"unterminated":', "PARSE_INVALID_JSON"
    if case_id == "SYN-30":
        if variant == 0:
            value["schema_version"] = "synthetic-contract-fixture/v999"
            return _encode(value), "SCHEMA_VERSION_UNSUPPORTED"
        value["purpose"] = "UNSUPPORTED_SYNTHETIC_PURPOSE"
        return _encode(value), "SCHEMA_PURPOSE_UNSUPPORTED"
    if case_id == "SYN-31":
        if variant == 0:
            value["probe_unknown_field"] = {
                "nested_object": {
                    "level_two": [
                        {"level_three": ["syn-value-" + ("x" * 48), 7, True, None]}
                    ]
                }
            }
        elif variant == 1:
            value["probe_unknown_field"] = [
                {"array_member": "syn-array-value"},
                ["syn-inner-array", 11, False],
            ]
        else:
            value["probe_unknown_field"] = {
                "long_key_probe_01": "syn-" + ("v" * 96),
                "second_member": 23,
                "third_member": ["syn-a", "syn-b", "syn-c"],
            }
        return _encode(value), "SCHEMA_FIELD_UNKNOWN"
    if case_id == "SYN-32":
        if variant == 0:
            value.pop("purpose")
            return _encode(value), "SCHEMA_FIELD_MISSING"
        if variant == 1:
            value["claims"] = []
            return _encode(value), "SCHEMA_TYPE_MISMATCH"
        value["unknown_top_level"] = "syn-extra"
        return _encode(value), "SCHEMA_FIELD_UNKNOWN"
    raise ValueError("unsupported frozen case")


def build_recipe() -> dict:
    """Build a fresh deterministic recipe; never persists or contacts services."""
    ordered_ids = [f"syn-fixture-{index:03d}" for index in range(1, EXPECTED_FIXTURE_COUNT + 1)]
    fixture_types = sorted(harness.D10_TYPES)
    parser_inputs = {}
    oracle_records = {}
    manifest = {}

    for index, fixture_type in enumerate(fixture_types):
        fixture_id = ordered_ids[index]
        parser_inputs[fixture_id] = _positive_bytes(fixture_id, fixture_type)
        oracle_records[fixture_id] = {"expected_reason_code": None}
        manifest[fixture_id] = {"case_id": "SYN-01", "fixture_type": fixture_type}

    negative_plan = (
        ("SYN-29", 0), ("SYN-29", 1), ("SYN-29", 2),
        ("SYN-30", 0), ("SYN-30", 1),
        ("SYN-31", 0), ("SYN-31", 1), ("SYN-31", 2),
        ("SYN-32", 0), ("SYN-32", 1), ("SYN-32", 2),
    )
    for offset, (case_id, variant) in enumerate(negative_plan, start=len(fixture_types)):
        fixture_id = ordered_ids[offset]
        fixture_type = fixture_types[(offset - len(fixture_types)) % len(fixture_types)]
        raw, expected_reason = _negative_fixture(case_id, fixture_id, fixture_type, variant)
        parser_inputs[fixture_id] = raw
        oracle_records[fixture_id] = {"expected_reason_code": expected_reason}
        manifest[fixture_id] = {"case_id": case_id, "fixture_type": fixture_type}

    return {
        "parser_inputs": parser_inputs,
        "oracle_records": oracle_records,
        "manifest": manifest,
        "ordered_ids": ordered_ids,
        "expected_fixture_ids": list(ordered_ids),
        "expected_case_ids": list(CASE_IDS),
        "expected_fixture_types": list(fixture_types),
        "claims_schemas": {},
    }


def validate_recipe(recipe) -> bool:
    if not isinstance(recipe, Mapping):
        return False
    required = {
        "parser_inputs", "oracle_records", "manifest", "ordered_ids",
        "expected_fixture_ids", "expected_case_ids", "expected_fixture_types",
        "claims_schemas",
    }
    if set(recipe) != required:
        return False
    ordered_ids = recipe["ordered_ids"]
    if type(ordered_ids) is not list or len(ordered_ids) != EXPECTED_FIXTURE_COUNT:
        return False
    if ordered_ids != [f"syn-fixture-{index:03d}" for index in range(1, EXPECTED_FIXTURE_COUNT + 1)]:
        return False
    if recipe["expected_fixture_ids"] != ordered_ids:
        return False
    if recipe["expected_case_ids"] != list(CASE_IDS):
        return False
    if recipe["expected_fixture_types"] != sorted(harness.D10_TYPES):
        return False
    if not isinstance(recipe["claims_schemas"], Mapping) or recipe["claims_schemas"]:
        return False
    if not harness.validate_manifest(
        recipe["parser_inputs"], recipe["oracle_records"], recipe["manifest"],
        ordered_ids, recipe["expected_case_ids"], recipe["expected_fixture_types"],
    ):
        return False
    if not harness.validate_d05_corpus(
        recipe["parser_inputs"], recipe["oracle_records"], recipe["claims_schemas"]
    ):
        return False
    counts = {case_id: 0 for case_id in CASE_IDS}
    for fixture_id in ordered_ids:
        record = recipe["manifest"][fixture_id]
        if record["case_id"] not in counts:
            return False
        counts[record["case_id"]] += 1
    if counts != EXPECTED_CASE_COUNTS:
        return False
    positives = [
        recipe["manifest"][fid]["fixture_type"] for fid in ordered_ids
        if recipe["manifest"][fid]["case_id"] == "SYN-01"
    ]
    return len(positives) == len(harness.D10_TYPES) and set(positives) == set(harness.D10_TYPES)


def validate_empty_execution_trace(trace) -> bool:
    return harness.validate_execution_trace(trace)


def validate_runner_source(source_bytes: bytes, frozen_sha256: str) -> bool:
    if type(source_bytes) is not bytes or type(frozen_sha256) is not str:
        return False
    if not _SHA256_RE.fullmatch(frozen_sha256):
        return False
    if hashlib.sha256(source_bytes).hexdigest() != frozen_sha256:
        return False
    return (
        harness.validate_capability_boundary(source_bytes, "persistence")
        and harness.validate_capability_boundary(source_bytes, "external")
    )


def prepare_preflight(
    *,
    harness_source_bytes: bytes,
    frozen_harness_sha256: str,
    runner_source_bytes: bytes,
    frozen_runner_sha256: str,
    source_commit: str,
    command: str,
) -> dict:
    """Build in-memory evidence for focused tests; no file/network/runtime access."""
    if type(source_commit) is not str or not _COMMIT_RE.fullmatch(source_commit):
        raise ValueError("invalid exact source commit")
    if type(command) is not str or not command.strip():
        raise ValueError("exact command is required")
    if not validate_runner_source(runner_source_bytes, frozen_runner_sha256):
        raise ValueError("runner source digest or capability boundary failed")
    if type(harness_source_bytes) is not bytes:
        raise ValueError("harness source bytes are required")
    if not harness.validate_provenance(
        {
            "corpus_revision": CORPUS_REVISION,
            "source_commit": source_commit,
            "source_blob_sha256": frozen_harness_sha256,
            "command": command,
            "python_version": "preflight-test-runtime",
            "platform": "preflight-test-platform",
            "measurement_definition_revision": harness.MEASUREMENT_DEFINITION_REVISION,
        },
        harness_source_bytes,
        frozen_harness_sha256,
    ):
        raise ValueError("harness source provenance failed")
    if not harness.validate_capability_boundary(harness_source_bytes, "persistence"):
        raise ValueError("harness persistence capability check failed")
    if not harness.validate_capability_boundary(harness_source_bytes, "external"):
        raise ValueError("harness external capability check failed")

    recipe_first = build_recipe()
    recipe_second = build_recipe()
    if not validate_recipe(recipe_first) or not validate_recipe(recipe_second):
        raise ValueError("frozen recipe validation failed")
    if recipe_first != recipe_second:
        raise ValueError("independent recipe construction is non-deterministic")

    measurement_first = harness.measure_corpus(
        recipe_first["parser_inputs"], recipe_first["ordered_ids"]
    )
    measurement_second = harness.measure_corpus(
        recipe_second["parser_inputs"], recipe_second["ordered_ids"]
    )
    if measurement_first != measurement_second:
        raise ValueError("independent measurement passes differ")

    provenance = harness.runtime_provenance(
        CORPUS_REVISION, source_commit, frozen_harness_sha256, command
    )
    trace = {"payload_persistence_events": [], "external_access_events": []}
    provisional_assertions = {f"A-{index:02d}": True for index in range(1, 14)}
    report_bytes = harness.build_report(
        CORPUS_REVISION, measurement_first, provisional_assertions, provenance
    )
    evidence = {
        **recipe_first,
        "measurement": measurement_first,
        "measurement_pass_1": measurement_first,
        "measurement_pass_2": measurement_second,
        "provenance": provenance,
        "harness_source_bytes": harness_source_bytes,
        "frozen_source_sha256": frozen_harness_sha256,
        "report_bytes": report_bytes,
        "execution_trace": trace,
    }
    assertions = harness.evaluate_assertions(evidence)
    if set(assertions) != {f"A-{index:02d}" for index in range(1, 14)}:
        raise ValueError("assertion registry is incomplete")
    if not all(value is True for value in assertions.values()):
        raise ValueError("one or more executable harness assertions failed")
    if not harness.validate_report_readback(report_bytes):
        raise ValueError("serialized report readback failed")

    return {
        "corpus_revision": CORPUS_REVISION,
        "fixture_count": len(recipe_first["ordered_ids"]),
        "case_counts": dict(EXPECTED_CASE_COUNTS),
        "parser_input_digest": measurement_first["corpus_sha256"],
        "measurement_pass_1": measurement_first,
        "measurement_pass_2": measurement_second,
        "assertions": assertions,
        "report_readback_valid": True,
        "runner_source_sha256": frozen_runner_sha256,
        "harness_source_sha256": frozen_harness_sha256,
        "execution_trace": trace,
    }
