"""Deterministic synthetic evidence fixtures. Standard-library only; no external I/O."""
from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import platform
import re
import uuid
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

SPEC_VERSION = "synthetic-evidence-fixture/1"
EVENT_HASH_DOMAIN = b"BTCUSDT-PAPER-EVENT-V1\n"
MANIFEST_HASH_DOMAIN = b"BTCUSDT-PAPER-MANIFEST-V1\n"
PRF_PREFIX = b"SYNTH-EVIDENCE-PRF-V1\n"
GENESIS = "GENESIS"
MAX_SAFE_INTEGER = (2**53) - 1
MAX_U64 = (2**64) - 1
MAX_OUTPUT_BYTES = 16 * 1024 * 1024
TARGET_CLASS_WEIGHTS = {"intent_signal": 6, "risk_decision": 8, "reservation": 8, "order_lifecycle": 12, "position_transition": 14, "fee_adjustment": 8, "funding": 8, "mark_valuation": 10, "config": 6, "baseline_risk": 8, "recovery_audit": 6}
STREAM_RE = re.compile(r"^[A-Z0-9-]{1,64}$", re.ASCII)
SHA_RE = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$", re.ASCII)

STREAMS = (
    ("SYNTH-CORE-001", "CORE_LEDGER", "SYNTH_CORE_STRATEGY"),
    ("SYNTH-AI-001", "AI_LEDGER", "SYNTH_AI_STRATEGY"),
    ("SYNTH-LEGACY-001", "LEGACY_UNATTRIBUTED", "SYNTH_LEGACY_DOMAIN"),
)
CORE_SCENARIO = (
    ("STRATEGY_CONFIG_ACTIVATED", "config"),
    ("SIGNAL_CREATED", "intent_signal"),
    ("RISK_ADMITTED", "risk_decision"),
    ("KILL_SWITCH_CHANGED", "risk_decision"),
    ("RESERVATION_CREATED", "reservation"),
    ("ORDER_ACCEPTED", "order_lifecycle"),
    ("ORDER_PARTIAL", "order_lifecycle"),
    ("ORDER_FILLED", "order_lifecycle"),
    ("RESERVATION_CONSUMED", "reservation"),
    ("RESERVATION_RELEASED", "reservation"),
    ("POSITION_OPENED", "position_transition"),
    ("DCA_APPLIED", "position_transition"),
    ("POSITION_REDUCED", "position_transition"),
    ("POSITION_CLOSED", "position_transition"),
    ("FEE_ACCRUED", "fee_adjustment"),
    ("FUNDING_ACCRUED", "funding"),
    ("FUNDING_CORRECTION", "funding"),
    ("MARK_OBSERVED", "mark_valuation"),
    ("VALUATION_COMPUTED", "mark_valuation"),
    ("DAILY_BASELINE_ESTABLISHED", "baseline_risk"),
    ("DAILY_BASELINE_ADVANCED", "baseline_risk"),
    ("HWM_UPDATED", "baseline_risk"),
    ("CHECKPOINT_SEALED", "recovery_audit"),
    ("REPLAY_COMPLETED", "recovery_audit"),
)
LEGACY_SCENARIO = (
    ("LEGACY_ADJUSTMENT", "fee_adjustment"),
    ("MARK_OBSERVED", "mark_valuation"),
    ("VALUATION_COMPUTED", "mark_valuation"),
    ("DAILY_BASELINE_ESTABLISHED", "baseline_risk"),
    ("DAILY_BASELINE_ADVANCED", "baseline_risk"),
    ("HWM_UPDATED", "baseline_risk"),
    ("CHECKPOINT_SEALED", "recovery_audit"),
    ("REPLAY_COMPLETED", "recovery_audit"),
)
SCENARIOS = {
    "CORE_LEDGER": CORE_SCENARIO,
    "AI_LEDGER": CORE_SCENARIO,
    "LEGACY_UNATTRIBUTED": LEGACY_SCENARIO,
}
ALL_SCENARIO_TYPES = {event_type: event_class for scenario in SCENARIOS.values() for event_type, event_class in scenario}


def _utf8(value: str, field: str) -> bytes:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be a string")
    try:
        return value.encode("utf-8", errors="strict")
    except UnicodeEncodeError as exc:
        raise ValueError(f"{field} contains invalid Unicode") from exc


def _validate_json_value(value: Any) -> Any:
    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, int):
        if abs(value) > MAX_SAFE_INTEGER:
            raise ValueError("JSON integers must remain within the interoperable safe range")
        return value
    if isinstance(value, float):
        raise ValueError("floating-point JSON values are forbidden; use exact decimal strings")
    if isinstance(value, str):
        _utf8(value, "JSON string")
        return value
    if isinstance(value, list):
        return [_validate_json_value(item) for item in value]
    if isinstance(value, dict):
        normalized = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValueError("JSON object keys must be strings")
            _utf8(key, "JSON object key")
            normalized[key] = _validate_json_value(item)
        return {key: normalized[key] for key in sorted(normalized, key=lambda k: _utf8(k, "JSON key").decode("utf-8").encode("utf-16-be"))}
    raise ValueError(f"unsupported JSON value type: {type(value).__name__}")


def canonical_json(value: Any) -> bytes:
    """Serialize the supported JCS subset: UTF-8, UTF-16 key ordering, no floats."""
    normalized = _validate_json_value(value)
    return json.dumps(normalized, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")


def parse_json_strict(source: str | bytes) -> Any:
    """Parse JSON while rejecting duplicate keys, floats, constants and invalid Unicode."""
    if isinstance(source, bytes):
        try:
            source = source.decode("utf-8", errors="strict")
        except UnicodeDecodeError as exc:
            raise ValueError("invalid UTF-8 JSON input") from exc

    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    def reject_float(_value):
        raise ValueError("floating-point JSON values are forbidden")

    def reject_constant(_value):
        raise ValueError("non-finite JSON values are forbidden")

    try:
        parsed = json.loads(source, object_pairs_hook=pairs, parse_float=reject_float, parse_constant=reject_constant)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ValueError("invalid JSON input") from exc
    _validate_json_value(parsed)
    return parsed


def _u16(value: bytes, field: str) -> bytes:
    if len(value) > 0xFFFF:
        raise ValueError(f"{field} exceeds uint16 byte length")
    return len(value).to_bytes(2, "big")


def hmac_stream(seed_hex: str, domain: str, stream_id: str, sequence: int, field_path: str, sample_index: int, length: int) -> bytes:
    """Derive deterministic bytes from the P1.7 domain-separated HMAC-SHA-256 PRF."""
    if not isinstance(seed_hex, str) or not re.fullmatch(r"[0-9a-f]{64}", seed_hex):
        raise ValueError("seed must be exactly 64 lowercase hexadecimal characters")
    if not isinstance(stream_id, str) or not STREAM_RE.fullmatch(stream_id):
        raise ValueError("stream_id must match [A-Z0-9-]{1,64}")
    if not isinstance(sequence, int) or isinstance(sequence, bool) or not 1 <= sequence <= MAX_U64:
        raise ValueError("sequence must be an unsigned 64-bit integer starting at 1")
    if not isinstance(sample_index, int) or isinstance(sample_index, bool) or not 0 <= sample_index <= 0xFFFFFFFF:
        raise ValueError("sample_index must fit uint32")
    if not isinstance(length, int) or isinstance(length, bool) or not 0 <= length <= MAX_OUTPUT_BYTES:
        raise ValueError("length must be between 0 and 16 MiB")
    domain_b, stream_b, path_b = _utf8(domain, "domain"), _utf8(stream_id, "stream_id"), _utf8(field_path, "field_path")
    message = (PRF_PREFIX + _u16(domain_b, "domain") + domain_b + _u16(stream_b, "stream_id") + stream_b
               + sequence.to_bytes(8, "big") + _u16(path_b, "field_path") + path_b + sample_index.to_bytes(4, "big"))
    key, output, block_index = bytes.fromhex(seed_hex), bytearray(), 0
    while len(output) < length:
        if block_index > 0xFFFFFFFF:
            raise ValueError("PRF block counter exhausted")
        output.extend(hmac.new(key, message + block_index.to_bytes(4, "big"), hashlib.sha256).digest())
        block_index += 1
    return bytes(output[:length])


def _parse_base_time(value: str) -> datetime:
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z", value):
        raise ValueError("base_time_utc must use YYYY-MM-DDTHH:mm:ss.sssZ")
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)
    except ValueError as exc:
        raise ValueError("base_time_utc is not a valid UTC timestamp") from exc


def _timestamp(value: datetime) -> str:
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:23] + "Z"


def _decimal_value(seed: str, stream_id: str, sequence: int, path: str) -> str:
    raw = int.from_bytes(hmac_stream(seed, "fixture/decimal/v1", stream_id, sequence, path, 0, 8), "big")
    units = raw % 10_000_000
    return f"{units // 10000}.{units % 10000:04d}"


def _largest_remainder(total: int, weights: list[int]) -> list[int]:
    weight_sum = sum(weights)
    base = [(total * weight) // weight_sum for weight in weights]
    remainder = total - sum(base)
    order = sorted(range(len(weights)), key=lambda i: (-(total * weights[i] % weight_sum), i))
    for index in order[:remainder]:
        base[index] += 1
    return base


def _stats(values: list[int]) -> dict[str, int | str]:
    if not values:
        return {"sample_count": 0, "total": 0, "min": 0, "mean": "0", "p50": 0, "p90": 0, "p95": 0, "p99": 0, "max": 0}
    ordered = sorted(values)

    def nearest_rank(numerator: int, denominator: int) -> int:
        rank = max(1, (numerator * len(ordered) + denominator - 1) // denominator)
        return ordered[rank - 1]

    return {
        "sample_count": len(ordered), "total": sum(ordered), "min": ordered[0],
        "mean": format(Decimal(sum(ordered)) / Decimal(len(ordered)), "f"),
        "p50": nearest_rank(50, 100), "p90": nearest_rank(90, 100),
        "p95": nearest_rank(95, 100), "p99": nearest_rank(99, 100), "max": ordered[-1],
    }


def _environment_descriptor() -> dict[str, Any]:
    try:
        memory_bytes = int(os.sysconf("SC_PHYS_PAGES") * os.sysconf("SC_PAGE_SIZE"))
    except (AttributeError, OSError, ValueError):
        memory_bytes = None
    return {
        "os": platform.system(),
        "architecture": platform.machine(),
        "cpu_model": platform.processor() or "UNKNOWN",
        "cpu_count": os.cpu_count(),
        "memory_total_bytes_sysconf": memory_bytes,
        "storage_medium": "NOT_MEASURED",
        "tool_versions": {"python": platform.python_version(), "implementation": platform.python_implementation()},
    }


def _build_digest() -> str:
    digest = hashlib.sha256()
    build_files = ("__init__.py", "generator.py", "__main__.py")
    for source_path in (Path(__file__).parent / name for name in build_files):
        relative, content = source_path.name.encode("utf-8"), source_path.read_bytes()
        digest.update(len(relative).to_bytes(2, "big"))
        digest.update(relative)
        digest.update(len(content).to_bytes(8, "big"))
        digest.update(content)
    return digest.hexdigest()


def _negative_vectors(namespace_uuid: uuid.UUID) -> list[dict[str, Any]]:
    """Create isolated fault descriptions; never add them to clean event counts."""
    cases = [
        ("DUPLICATE_IDENTICAL_DELIVERY", "same event ID and identical canonical bytes", "IDEMPOTENT_ACK"),
        ("SAME_EVENT_ID_CHANGED_BYTES", "same event ID with modified payload bytes", "BLOCK_INTEGRITY_VIOLATION"),
        ("MISSING_SEQUENCE", "stream sequence skips one committed value", "BLOCK_STREAM_GAP"),
        ("WRONG_PREVIOUS_HASH", "previous-event hash does not match predecessor", "BLOCK_HASH_CHAIN"),
        ("INVALID_SIGNATURE", "synthetic invalid signature bytes; no private key involved", "REJECT_SIGNATURE"),
        ("UNKNOWN_SIGNING_KEY", "signature references an unknown synthetic key ID", "REJECT_UNKNOWN_KEY"),
        ("REVOKED_SIGNING_KEY", "signature references a revoked synthetic key ID", "REJECT_REVOKED_KEY"),
        ("LATE_PRE_BOUNDARY_EVENT", "pre-boundary event commits after the proposed boundary", "INVALIDATE_CHECKPOINT"),
        ("PARTIAL_FILL_CANCEL_REPLACE", "accepted, partial fill, cancel, replace, final fill", "REPLAY_ORDER_LIFECYCLE"),
        ("REDUCE_CLOSE_REVERSAL", "reduce and close before separately admitting reversal increase", "REDUCE_THEN_ADMIT_REVERSE"),
        ("UNKNOWN_FEE_FUNDING", "fee and funding amounts are UNKNOWN, not numeric zero", "BLOCK_REQUIRED_EQUITY"),
        ("STALE_MISSING_MARK_CLOCK", "stale/missing mark and uncertain source clock", "BLOCK_VALUATION_READINESS"),
        ("ROOT_B_DUPLICATE_ACK_CRASH", "duplicate observer acknowledgement and crash around checkpoint commit", "IDEMPOTENT_RECOVERY_OR_BLOCK"),
    ]
    return [{
        "vector_id": str(uuid.uuid5(namespace_uuid, f"negative-vector:{name}")),
        "name": name,
        "description": description,
        "expected_disposition": expected,
        "clean_volume_denominator": False,
        "signature_material": "SYNTHETIC_PLACEHOLDER_ONLY" if "SIGNATURE" in name or "KEY" in name else "NOT_APPLICABLE",
    } for name, description, expected in cases]


def generate_fixture(*, seed_hex: str, namespace: str, base_time_utc: str, event_count: int,
                     source_sha: str, segment_event_cap: int = 100, segment_byte_cap: int = 1_048_576) -> dict[str, Any]:
    """Build a deterministic clean fixture entirely in memory."""
    if not isinstance(seed_hex, str) or not re.fullmatch(r"[0-9a-f]{64}", seed_hex):
        raise ValueError("seed_hex must be 64 lowercase hexadecimal characters")
    try:
        namespace_uuid = uuid.UUID(namespace)
    except (ValueError, AttributeError) as exc:
        raise ValueError("namespace must be a UUID") from exc
    if str(namespace_uuid) != namespace:
        raise ValueError("namespace must use canonical lowercase UUID notation")
    if not isinstance(event_count, int) or isinstance(event_count, bool) or not 1 <= event_count <= 100_000:
        raise ValueError("event_count must be between 1 and 100000")
    if not isinstance(source_sha, str) or not SHA_RE.fullmatch(source_sha):
        raise ValueError("source_sha must be a full lowercase Git SHA")
    if not isinstance(segment_event_cap, int) or isinstance(segment_event_cap, bool) or not 1 <= segment_event_cap <= 5000:
        raise ValueError("segment_event_cap must be between 1 and 5000")
    if not isinstance(segment_byte_cap, int) or not 1024 <= segment_byte_cap <= 32 * 1024 * 1024:
        raise ValueError("segment_byte_cap must be between 1 KiB and 32 MiB")
    base_time = _parse_base_time(base_time_utc)

    counts = _largest_remainder(event_count, [1, 1, 1])
    config = {"event_count": event_count, "namespace": str(namespace_uuid), "seed": seed_hex,
              "segment_event_cap": segment_event_cap, "segment_byte_cap": segment_byte_cap, "source_sha": source_sha}
    config_sha = hashlib.sha256(canonical_json(config)).hexdigest()
    descriptor = {
        "fixture_spec_version": SPEC_VERSION, "generator_source_sha": source_sha,
        "generator_build_digest": _build_digest(), "seed": seed_hex, "namespace": str(namespace_uuid),
        "base_time_utc": base_time_utc, "event_mix_version": "scenario-bundle-target-mix/1",
        "event_count_requested": event_count,
        "stream_event_counts": {STREAMS[i][0]: counts[i] for i in range(len(STREAMS))},
        "payload_profile": "ROTATING-SMALL-MEDIAN-LARGE/1",
        "canonicalization_profile": "RFC8785-JCS-STRICT-SUBSET/1",
        "hash_profile": "BTCUSDT-PAPER-EVENT-V1+MANIFEST-V1",
        "hash_signature_profile": "SHA256_EVENT_AND_MANIFEST_UNSIGNED_LOCAL/1",
        "segment_policy": {"event_cap": segment_event_cap, "byte_cap": segment_byte_cap, "scope": "single-stream-contiguous"},
        "compression_profile": "NONE", "negative_vector_profile": "synthetic-fault-vectors/1",
        "environment": _environment_descriptor(),
    }

    events_by_stream: dict[str, list[dict[str, Any]]] = {}
    all_events: list[dict[str, Any]] = []
    cohort_names = ("SMALL", "MEDIAN", "LARGE")
    for stream_id, ledger, strategy in STREAMS:
        stream_count = counts[STREAMS.index((stream_id, ledger, strategy))]
        scenario = SCENARIOS[ledger]
        stream_events, previous_hash, previous_event_id = [], GENESIS, None
        for sequence in range(1, stream_count + 1):
            event_type, _event_class = scenario[(sequence - 1) % len(scenario)]
            cohort = cohort_names[(sequence - 1) % len(cohort_names)]
            scenario_index = (sequence - 1) // len(scenario)
            event_id = str(uuid.uuid5(namespace_uuid, f"{stream_id}:{sequence:020d}"))
            scenario_id = str(uuid.uuid5(namespace_uuid, f"scenario:{stream_id}:{scenario_index:012d}"))
            intent_id = str(uuid.uuid5(namespace_uuid, f"intent:{stream_id}:{scenario_index:012d}"))
            committed = _timestamp(base_time + timedelta(milliseconds=sequence - 1))
            amount = _decimal_value(seed_hex, stream_id, sequence, "payload.amount")
            payload = {
                "scenario_id": scenario_id, "intent_id": intent_id,
                "entity_id": str(uuid.uuid5(namespace_uuid, f"entity:{stream_id}:{scenario_index:012d}")),
                "event_state": event_type, "payload_cohort": cohort, "amount": amount,
                "amount_unit": "SYNTHETIC_UNIT", "sequence_in_scenario": (sequence - 1) % len(scenario) + 1,
            }
            if event_type == "SIGNAL_CREATED":
                payload["side"] = "LONG" if scenario_index % 2 == 0 else "SHORT"
            if event_type == "KILL_SWITCH_CHANGED":
                payload["kill_switch_state"] = "DISABLED"
            if event_type.startswith("RESERVATION_"):
                payload["reservation_id"] = str(uuid.uuid5(namespace_uuid, f"reservation:{stream_id}:{scenario_index:012d}"))
            if cohort == "MEDIAN":
                payload["reason"] = "synthetic deterministic scenario transition"
                payload["source_refs"] = ["SYNTH-REF-00", "SYNTH-REF-01"]
            elif cohort == "LARGE":
                payload["reason"] = "synthetic bounded provenance extension " * 24
                payload["source_refs"] = [f"SYNTH-REF-{i:02d}" for i in range(12)]
            if event_type.startswith("ORDER_"):
                payload["order_id"] = str(uuid.uuid5(namespace_uuid, f"order:{stream_id}:{scenario_index:012d}"))
            if event_type in {"POSITION_OPENED", "DCA_APPLIED", "POSITION_REDUCED", "POSITION_CLOSED"}:
                payload["position_id"] = str(uuid.uuid5(namespace_uuid, f"position:{stream_id}:{scenario_index:012d}"))
            causation = [previous_event_id] if previous_event_id else []
            core = {
                "envelope_version": "1", "event_id": event_id, "stream_id": stream_id,
                "sequence": f"{sequence:020d}", "event_type": event_type, "schema_version": "synthetic-paper-event/1",
                "producer": {"service": "synthetic-evidence-generator", "instance_id": "SYNTH-LOCAL-001",
                             "build_sha": source_sha, "config_sha256": config_sha},
                "scope": {"account_domain": "SYNTHETIC_ONLY", "ledger": ledger, "strategy_id": strategy,
                          "strategy_version": "synthetic-scenario/1"},
                "time": {"occurred_at": committed, "committed_at": committed,
                         "clock_source": "FIXED_SYNTHETIC_CLOCK", "clock_uncertainty_ms": "0"},
                "causality": {"correlation_id": scenario_id, "causation_event_ids": causation,
                              "intent_id": intent_id, "idempotency_key": f"{stream_id}:{sequence:020d}"},
                "payload": payload,
                "provenance": {"fact_class": "SYNTHETIC_FIXTURE", "source_type": "DETERMINISTIC_GENERATOR",
                               "source_snapshot_id": f"{SPEC_VERSION}:{scenario_id}", "source_sha256": config_sha},
                "previous_event_hash": previous_hash,
            }
            event_hash = hashlib.sha256(EVENT_HASH_DOMAIN + canonical_json(core)).hexdigest()
            envelope = {"event_core": core, "integrity": {"hash_algorithm": "SHA-256", "event_hash": event_hash}}
            stream_events.append(envelope)
            all_events.append(envelope)
            previous_hash, previous_event_id = event_hash, event_id
        events_by_stream[stream_id] = stream_events

    all_events.sort(key=lambda event: (event["event_core"]["time"]["committed_at"],
                                       event["event_core"]["stream_id"], event["event_core"]["sequence"]))
    events_jsonl = b"".join(canonical_json(event) + b"\n" for event in all_events)

    segments, manifest_lines, segment_index = [], [], 0
    for stream_id in sorted(events_by_stream):
        current_events, current_bytes, previous_manifest_hash = [], bytearray(), GENESIS

        def seal_segment(batch, batch_bytes):
            nonlocal segment_index, previous_manifest_hash
            if not batch:
                return
            segment_index += 1
            first_core, last_core = batch[0]["event_core"], batch[-1]["event_core"]
            segment_digest = hashlib.sha256(batch_bytes).hexdigest()
            manifest_core = {
                "manifest_schema_version": "synthetic-segment-manifest/1",
                "manifest_id": str(uuid.uuid5(namespace_uuid, f"manifest:{stream_id}:{first_core['sequence']}:{last_core['sequence']}")),
                "stream_id": stream_id, "first_sequence": first_core["sequence"], "last_sequence": last_core["sequence"],
                "event_count": len(batch), "first_event_hash": batch[0]["integrity"]["event_hash"],
                "last_event_hash": batch[-1]["integrity"]["event_hash"], "previous_manifest_hash": previous_manifest_hash,
                "segment_byte_length": len(batch_bytes), "segment_sha256": segment_digest,
                "source_build_sha": source_sha, "config_sha256": config_sha,
                "sealed_at": last_core["time"]["committed_at"], "signature_profile_id": "UNSIGNED_LOCAL_SYNTHETIC_FIXTURE",
            }
            manifest_hash = hashlib.sha256(MANIFEST_HASH_DOMAIN + canonical_json(manifest_core)).hexdigest()
            manifest = {"manifest_core": manifest_core, "integrity": {"hash_algorithm": "SHA-256", "manifest_hash": manifest_hash}}
            manifest_lines.append(canonical_json(manifest) + b"\n")
            segments.append({
                "segment_name": f"segment-{segment_index:06d}.jsonl", "stream_id": stream_id,
                "first_sequence": int(first_core["sequence"]), "last_sequence": int(last_core["sequence"]),
                "event_count": len(batch), "byte_length": len(batch_bytes), "sha256": segment_digest,
                "data": bytes(batch_bytes), "events": list(batch), "manifest": manifest,
            })
            previous_manifest_hash = manifest_hash

        for event in events_by_stream[stream_id]:
            line = canonical_json(event) + b"\n"
            if len(line) > segment_byte_cap:
                raise ValueError("single event exceeds segment byte cap")
            if current_events and (len(current_events) >= segment_event_cap or len(current_bytes) + len(line) > segment_byte_cap):
                seal_segment(current_events, bytes(current_bytes))
                current_events, current_bytes = [], bytearray()
            current_events.append(event)
            current_bytes.extend(line)
        seal_segment(current_events, bytes(current_bytes))

    class_sizes: dict[str, list[int]] = defaultdict(list)
    cohort_sizes: dict[str, list[int]] = defaultdict(list)
    overall_sizes, event_class_counts = [], Counter()
    for event in all_events:
        core = event["event_core"]
        size = len(canonical_json(core))
        overall_sizes.append(size)
        event_class = ALL_SCENARIO_TYPES[core["event_type"]]
        class_sizes[event_class].append(size)
        cohort_sizes[core["payload"]["payload_cohort"]].append(size)
        event_class_counts[event_class] += 1

    target_names = sorted(TARGET_CLASS_WEIGHTS)
    target_counts = _largest_remainder(event_count, [TARGET_CLASS_WEIGHTS[name] for name in target_names])
    measurements = {
        "statistic": "nearest-rank; rank=ceil(p*n), 1-indexed",
        "event_class_target_weights": TARGET_CLASS_WEIGHTS,
        "event_class_target_weight_sum": sum(TARGET_CLASS_WEIGHTS.values()),
        "event_class_target_counts_normalized": {name: count for name, count in zip(target_names, target_counts)},
        "event_core_bytes": {
            "overall": _stats(overall_sizes),
            "by_event_class": {key: _stats(value) for key, value in sorted(class_sizes.items())},
            "by_payload_cohort": {key: _stats(value) for key, value in sorted(cohort_sizes.items())},
        },
        "event_counts_by_class": dict(sorted(event_class_counts.items())),
        "event_class_actual_counts_are_scenario_driven": True,
        "segments": {"count": len(segments), "total_bytes": sum(segment["byte_length"] for segment in segments),
                     "max_bytes": max((segment["byte_length"] for segment in segments), default=0)},
        "manifests": {"count": len(manifest_lines), "total_bytes": sum(len(line) for line in manifest_lines)},
        "compression": "NOT_MEASURED (profile NONE)", "root_b_replay": "LOCAL_REPLAY_SIMULATION_ONLY",
    }
    return {"descriptor": descriptor, "events": all_events, "events_jsonl": events_jsonl,
            "segments": segments, "manifests_jsonl": b"".join(manifest_lines),
            "measurements": measurements, "negative_vectors": _negative_vectors(namespace_uuid)}


def verify_local_replay(events: list[dict[str, Any]]) -> dict[str, Any]:
    """Verify local event chains; this is not independent Root B evidence."""
    last_sequence, last_hash, last_event_id, last_committed_at = {}, {}, {}, {}
    seen_ids: dict[str, bytes] = {}
    duplicate_deliveries_ignored = 0
    for event in events:
        core = event["event_core"]
        event_id = core["event_id"]
        event_bytes = canonical_json(event)
        if event_id in seen_ids:
            if seen_ids[event_id] != event_bytes:
                raise ValueError("same event ID delivered with changed bytes")
            duplicate_deliveries_ignored += 1
            continue
        stream, sequence_text = core["stream_id"], core["sequence"]
        if not re.fullmatch(r"\d{20}", sequence_text):
            raise ValueError("sequence must be a 20-digit decimal string")
        sequence = int(sequence_text)
        if sequence != last_sequence.get(stream, 0) + 1:
            raise ValueError(f"sequence gap or reorder in {stream}")
        ledger = core["scope"]["ledger"]
        expected_type = SCENARIOS[ledger][(sequence - 1) % len(SCENARIOS[ledger])][0]
        if core["event_type"] != expected_type:
            raise ValueError(f"invalid scenario transition at {stream}:{sequence}")
        if core["previous_event_hash"] != last_hash.get(stream, GENESIS):
            raise ValueError(f"previous hash mismatch in {stream}")
        expected_causation = [last_event_id[stream]] if stream in last_event_id else []
        if core["causality"]["causation_event_ids"] != expected_causation:
            raise ValueError(f"causation mismatch in {stream}")
        committed_at = core["time"]["committed_at"]
        if committed_at < last_committed_at.get(stream, committed_at):
            raise ValueError(f"commit timestamp moved backwards in {stream}")
        expected_hash = hashlib.sha256(EVENT_HASH_DOMAIN + canonical_json(core)).hexdigest()
        if event["integrity"].get("event_hash") != expected_hash:
            raise ValueError("event hash mismatch")
        seen_ids[event_id] = event_bytes
        last_sequence[stream], last_hash[stream] = sequence, expected_hash
        last_event_id[stream], last_committed_at[stream] = core["event_id"], committed_at
    return {"status": "PASS", "assurance": "LOCAL_REPLAY_SIMULATION",
            "events_verified": len(events) - duplicate_deliveries_ignored,
            "deliveries_seen": len(events), "duplicate_deliveries_ignored": duplicate_deliveries_ignored,
            "streams_verified": len(last_sequence)}


def write_fixture(fixture: dict[str, Any], output_dir: Path) -> Path:
    """Write a new local directory. Existing output paths are never overwritten."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=False)
    (output_dir / "segments").mkdir()
    files: dict[str, bytes] = {
        "run_descriptor.json": canonical_json(fixture["descriptor"]) + b"\n",
        "events.jsonl": fixture["events_jsonl"],
        "manifests.jsonl": fixture["manifests_jsonl"],
        "measurements.json": canonical_json(fixture["measurements"]) + b"\n",
        "negative_vectors.json": canonical_json(fixture["negative_vectors"]) + b"\n",
    }
    for segment in fixture["segments"]:
        files[f"segments/{segment['segment_name']}"] = segment["data"]
    for relative, content in files.items():
        path = output_dir / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    digest_lines = [f"{hashlib.sha256(content).hexdigest()}  {relative}" for relative, content in sorted(files.items())]
    (output_dir / "fixture.sha256").write_text("\n".join(digest_lines) + "\n", encoding="ascii")
    return output_dir


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate deterministic synthetic evidence fixtures (local only).")
    parser.add_argument("--seed", required=True, help="64 lowercase hex characters (32 bytes)")
    parser.add_argument("--namespace", required=True, help="fixed UUID namespace for synthetic IDs")
    parser.add_argument("--base-time-utc", required=True, help="fixed UTC timestamp YYYY-MM-DDTHH:mm:ss.sssZ")
    parser.add_argument("--events", type=int, default=1000, help="number of clean synthetic events (1..100000)")
    parser.add_argument("--source-sha", required=True, help="full immutable Git source SHA")
    parser.add_argument("--out", required=True, type=Path, help="new local output directory; must not exist")
    parser.add_argument("--segment-event-cap", type=int, default=100)
    parser.add_argument("--segment-byte-cap", type=int, default=1_048_576)
    args = parser.parse_args(argv)
    fixture = generate_fixture(seed_hex=args.seed, namespace=args.namespace, base_time_utc=args.base_time_utc,
                               event_count=args.events, source_sha=args.source_sha,
                               segment_event_cap=args.segment_event_cap, segment_byte_cap=args.segment_byte_cap)
    replay = verify_local_replay(fixture["events"])
    output = write_fixture(fixture, args.out)
    print(json.dumps({"output": str(output), "source_sha": args.source_sha, "events": len(fixture["events"]),
                      "segments": len(fixture["segments"]), "negative_vectors": len(fixture["negative_vectors"]),
                      "replay": replay, "artifact_scope": "SYNTHETIC_ONLY_LOCAL"}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
