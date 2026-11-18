"""Pure deterministic fixture verdict routing; not a production verifier."""

from __future__ import annotations

from dataclasses import dataclass
import copy
import hashlib
from typing import Mapping

from .primitives import canonicalize, parse_canonical_json, evidence_object_digest


PROFILE_ID = "T0-CHECKPOINT-ISSUER-SIGNATURE-PROFILE-V2"
PROFILE_VERSION = 2
LEGACY_PROFILE_ID = "T0-CHECKPOINT-ISSUER-SIGNATURE-PROFILE-LEGACY"
A1_PROFILE_ID = "T0-CHECKPOINT-ISSUER-SIGNATURE-PROFILE-A1"
FIXTURE_SCHEMA_VERSION = "A2.2-STAGE-I-FIXTURE-V1"
_REQUIRED_DIMENSIONS = ("parsing_canonicalization", "object_binding", "profile", "purpose", "signature", "policy_authorization", "bootstrap_authorization", "custody_readback")
_FORBIDDEN_TRANSITIONS = ("root_enrollment", "policy_head_advance", "anchor_head_advance", "checkpoint_acceptance", "sequence_reservation", "durable_trust_state_write")
MOCK_LABEL = "MOCK / NOT CRYPTOGRAPHIC"
MOCK_ACCEPTED = "MOCK_ACCEPTED"
MOCK_REJECTED = "MOCK_REJECTED"


@dataclass(frozen=True)
class StageStateSnapshot:
    trust_roots: tuple[str, ...]
    policy_head: str
    anchor_head: tuple[int, str]
    checkpoint_head: tuple[str, str]
    bootstrap_sequence: int


@dataclass(frozen=True)
class FixtureResult:
    verdict: str
    reason_code: str
    dimension_result: str
    state_advanced: bool = False
    dimension_results: Mapping[str, str] | None = None
    state_s0: StageStateSnapshot | None = None
    state_s1: StageStateSnapshot | None = None
    forbidden_transitions: Mapping[str, bool] | None = None


@dataclass(frozen=True)
class FixtureSpec:
    case_id: str
    baseline: str
    mutations: tuple[str, ...]
    expected_verdict: str
    expected_reason: str
    dimension_result: str
    single_mutation: bool = True
    state_unchanged: bool = True
    baseline_digest: str = ""
    mutation_path: str = ""
    mutation_value: object = None
    schema_version: str = FIXTURE_SCHEMA_VERSION
    dimension_results: Mapping[str, str] | None = None


# The profile/purpose cases precede the A2.2 §17 bootstrap first-match table.
_PROFILE_RULES = (
    ("profile_downgrade_forbidden", "BLOCKED", "PROFILE_DOWNGRADE_FORBIDDEN", "Profile downgrade BLOCKED"),
    ("profile_unknown", "BLOCKED", "PROFILE_UNKNOWN", "Profile selection BLOCKED"),
    ("profile_not_enabled", "BLOCKED", "PROFILE_NOT_ENABLED", "Profile selection BLOCKED"),
    ("profile_binding_mismatch", "INVALID", "PROFILE_BINDING_MISMATCH", "Profile binding INVALID"),
    ("profile_version_mismatch", "INVALID", "PROFILE_VERSION_MISMATCH", "Profile version INVALID"),
    ("profile_retired", "UNTRUSTED", "PROFILE_RETIRED", "Profile lifecycle UNTRUSTED"),
    ("purpose_not_supported", "UNTRUSTED", "PURPOSE_NOT_SUPPORTED_BY_PROFILE", "Purpose/profile authorization UNTRUSTED"),
    ("policy_purpose_not_explicit", "BLOCKED", "POLICY_PURPOSE_NOT_EXPLICIT", "Policy purpose authorization BLOCKED"),
)

# Exact first-match order from A2.2 §17. A true predicate wins over later ones.
_BOOTSTRAP_RULES = (
    ("path_not_configured", "BLOCKED", "ROOT_BOOTSTRAP_PATH_NOT_CONFIGURED", "Bootstrap not configured"),
    ("path_not_enabled", "BLOCKED", "ROOT_BOOTSTRAP_PATH_NOT_ENABLED", "Path unavailable"),
    ("evidence_missing", "BLOCKED", "ROOT_BOOTSTRAP_EVIDENCE_MISSING", "Evidence missing"),
    ("trust_boundary_unavailable", "UNKNOWN", "ROOT_BOOTSTRAP_TRUST_BOUNDARY_UNAVAILABLE", "Trust boundary unavailable"),
    ("self_authorization", "BLOCKED", "ROOT_BOOTSTRAP_SELF_AUTHORIZATION_FORBIDDEN", "Self-authorization forbidden"),
    ("producer_input_untrusted", "BLOCKED", "ROOT_BOOTSTRAP_PRODUCER_INPUT_UNTRUSTED", "Producer input untrusted"),
    ("path_mixing", "BLOCKED", "ROOT_BOOTSTRAP_PATH_MIXING_FORBIDDEN", "Path mixing forbidden"),
    ("authorization_invalid", "INVALID", "ROOT_BOOTSTRAP_AUTHORIZATION_INVALID", "Authorization invalid"),
    ("digest_mismatch", "INVALID", "ROOT_BOOTSTRAP_DIGEST_MISMATCH", "Subject binding invalid"),
    ("namespace_mismatch", "INVALID", "ROOT_BOOTSTRAP_NAMESPACE_MISMATCH", "Namespace binding invalid"),
    ("audience_mismatch", "INVALID", "ROOT_BOOTSTRAP_AUDIENCE_MISMATCH", "Audience binding invalid"),
    ("root_fingerprint_mismatch", "INVALID", "ROOT_BOOTSTRAP_ROOT_FINGERPRINT_MISMATCH", "Root binding invalid"),
    ("root_role_mismatch", "INVALID", "ROOT_BOOTSTRAP_ROLE_MISMATCH", "Role binding invalid"),
    ("bootstrap_profile_mismatch", "INVALID", "ROOT_BOOTSTRAP_PROFILE_MISMATCH", "Profile binding invalid"),
    ("sequence_mismatch", "INVALID", "ROOT_BOOTSTRAP_SEQUENCE_MISMATCH", "Sequence binding invalid"),
    ("recovery_policy_mismatch", "INVALID", "ROOT_BOOTSTRAP_RECOVERY_POLICY_MISMATCH", "Recovery binding invalid"),
    ("readback_mismatch", "INVALID", "ROOT_BOOTSTRAP_READBACK_MISMATCH", "Readback integrity invalid"),
    ("readback_unavailable", "UNKNOWN", "ROOT_BOOTSTRAP_READBACK_UNAVAILABLE", "Readback unavailable"),
)


_FIXTURE_ROWS = (
    ("B0", "statement.purpose", "T0_CHECKPOINT_OWNER_ATTESTATION", "UNTRUSTED", "PURPOSE_NOT_SUPPORTED_BY_PROFILE", "Purpose/profile authorization UNTRUSTED"),
    ("B0", "policy.allowed_purposes", [], "BLOCKED", "POLICY_PURPOSE_NOT_EXPLICIT", "Policy purpose authorization BLOCKED"),
    ("B0", "verification_request.subject_object_id", "A1-HISTORICAL-OBJECT", "INVALID", "PROFILE_VERSION_MISMATCH", "Historical object/profile binding INVALID"),
    ("B0-PF", "verification_request.allow_automatic_fallback", True, "BLOCKED", "PROFILE_DOWNGRADE_FORBIDDEN", "Profile downgrade BLOCKED"),
    ("B0", "verification_request.signature_profile_id", "UNKNOWN-PROFILE", "BLOCKED", "PROFILE_UNKNOWN", "Profile selection BLOCKED"),
    ("B0", "verification_request.signature_profile_version", 3, "BLOCKED", "PROFILE_NOT_ENABLED", "Profile selection BLOCKED"),
    ("B0", "envelope.signature_profile_id", "SUBSTITUTED-PROFILE", "INVALID", "PROFILE_BINDING_MISMATCH", "Envelope/profile binding INVALID"),
    ("B0", "policy_profile_authorization.signature_profile_version", 3, "INVALID", "PROFILE_BINDING_MISMATCH", "Policy/profile binding INVALID"),
    ("B0", "profile.lifecycle", "RETIRED", "UNTRUSTED", "PROFILE_RETIRED", "Profile lifecycle UNTRUSTED"),
    ("B0", "verification_request.bootstrap_path", "A", "BLOCKED", "ROOT_BOOTSTRAP_PATH_NOT_ENABLED", "Path configuration BLOCKED"),
    ("B0", "verification_request.bootstrap_path", "B", "BLOCKED", "ROOT_BOOTSTRAP_PATH_NOT_ENABLED", "Path configuration BLOCKED"),
    ("B-A", "bootstrap.owner_authorization", None, "BLOCKED", "ROOT_BOOTSTRAP_EVIDENCE_MISSING", "Evidence presence BLOCKED"),
    ("B-A", "bootstrap.owner_pin.availability", "UNAVAILABLE", "UNKNOWN", "ROOT_BOOTSTRAP_TRUST_BOUNDARY_UNAVAILABLE", "Trust-boundary availability UNKNOWN"),
    ("B-A", "bootstrap.authorization.signature", "INVALID-SYNTHETIC-BYTES", "INVALID", "ROOT_BOOTSTRAP_AUTHORIZATION_INVALID", "Authorization signature INVALID"),
    ("B-A", "bootstrap.authorization.subject_digest", "0" * 64, "INVALID", "ROOT_BOOTSTRAP_DIGEST_MISMATCH", "Subject binding INVALID"),
    ("B-A", "bootstrap.namespace", "SUBSTITUTED-NAMESPACE", "INVALID", "ROOT_BOOTSTRAP_NAMESPACE_MISMATCH", "Namespace binding INVALID"),
    ("B-A", "bootstrap.audience", "SUBSTITUTED-AUDIENCE", "INVALID", "ROOT_BOOTSTRAP_AUDIENCE_MISMATCH", "Audience binding INVALID"),
    ("B-A", "bootstrap.root_spki_fingerprint", "0" * 64, "INVALID", "ROOT_BOOTSTRAP_ROOT_FINGERPRINT_MISMATCH", "Root binding INVALID"),
    ("B-A", "bootstrap.root_role", "UNAUTHORIZED-ROLE", "INVALID", "ROOT_BOOTSTRAP_ROLE_MISMATCH", "Role binding INVALID"),
    ("B-A", "bootstrap_record.signature_profile_id", "SUBSTITUTED-PROFILE", "INVALID", "ROOT_BOOTSTRAP_PROFILE_MISMATCH", "Profile binding INVALID"),
    ("B-A", "bootstrap.sequence_predecessor", "SUBSTITUTED-SEQUENCE-PREDECESSOR", "INVALID", "ROOT_BOOTSTRAP_SEQUENCE_MISMATCH", "Sequence binding INVALID"),
    ("B-A", "bootstrap.recovery_policy_digest", "0" * 64, "INVALID", "ROOT_BOOTSTRAP_RECOVERY_POLICY_MISMATCH", "Recovery binding INVALID"),
    ("B-A", "bootstrap.verifier_readback_bytes", "ALTERED-READBACK", "INVALID", "ROOT_BOOTSTRAP_READBACK_MISMATCH", "Readback integrity INVALID"),
    ("B-A", "bootstrap.verifier_readback_availability", "UNAVAILABLE", "UNKNOWN", "ROOT_BOOTSTRAP_READBACK_UNAVAILABLE", "Readback availability UNKNOWN"),
    ("B-A", "bootstrap.authorization.issuer", "NEW_ROOT_ONLY", "BLOCKED", "ROOT_BOOTSTRAP_SELF_AUTHORIZATION_FORBIDDEN", "Self-authorization BLOCKED"),
    ("B-A", "bootstrap.owner_pin.source", "PRODUCER_SUPPLIED", "BLOCKED", "ROOT_BOOTSTRAP_PRODUCER_INPUT_UNTRUSTED", "Trust-source BLOCKED"),
    ("B-A", "bootstrap.path_evidence", ["PATH_A", "PATH_B"], "BLOCKED", "ROOT_BOOTSTRAP_PATH_MIXING_FORBIDDEN", "Path mixing BLOCKED"),
)


def _profile_binding() -> dict[str, object]:
    return {"signature_profile_id": PROFILE_ID, "signature_profile_version": PROFILE_VERSION}


def _bootstrap_baseline(*, path_a_enabled: bool, path_b_enabled: bool) -> dict[str, object]:
    return {
        "path_a_enabled": path_a_enabled,
        "path_b_enabled": path_b_enabled,
        "record_digest": "a" * 64,
        "owner_authorization": "SYNTHETIC-OWNER-AUTHORIZATION",
        "owner_pin": {"availability": "AVAILABLE", "source": "INDEPENDENT"},
        "authorization": {
            "signature": "SYNTHETIC-VALID",
            "subject_digest": "a" * 64,
            "namespace": "T0",
            "audience": "BTCUSDT",
            "root_spki_fingerprint": "b" * 64,
            "root_role": "T0_BOOTSTRAP_ROOT",
            "profile_binding": f"{PROFILE_ID}:v{PROFILE_VERSION}",
            "sequence_predecessor": "1:GENESIS",
            "recovery_policy_digest": "c" * 64,
            "issuer": "OWNER_AUTHORITY",
        },
        "namespace": "T0",
        "audience": "BTCUSDT",
        "root_spki_fingerprint": "b" * 64,
        "root_role": "T0_BOOTSTRAP_ROOT",
        "profile_binding": f"{PROFILE_ID}:v{PROFILE_VERSION}",
        "sequence_predecessor": "1:GENESIS",
        "recovery_policy_digest": "c" * 64,
        "verifier_readback_bytes": "CANONICAL-SYNTHETIC-CONFIG",
        "expected_readback_bytes": "CANONICAL-SYNTHETIC-CONFIG",
        "verifier_readback_availability": "AVAILABLE",
        "path_evidence": ["PATH_A"],
    }


def _make_baseline(name: str, *, legacy_statement: bool = False, path_a_enabled: bool = False) -> dict[str, object]:
    binding = _profile_binding()
    statement_binding = dict(binding)
    if legacy_statement:
        statement_binding["signature_profile_id"] = LEGACY_PROFILE_ID
    policy_authorization = dict(
        binding,
        profile_namespace="T0",
        profile_purpose="T0_CHECKPOINT_ISSUER_ATTESTATION",
        signer_id="SYNTHETIC-TEST-SIGNER",
        signer_role="T0_CHECKPOINT_ISSUER",
        namespace="T0",
        audience="BTCUSDT",
        allowed_purposes=["T0_CHECKPOINT_ISSUER_ATTESTATION"],
    )
    policy_signed_binding = dict(
        binding,
        signed_statement_digest="d" * 64,
        policy_body_digest="e" * 64,
        statement_binding="SYNTHETIC-TEST-ONLY-NOT-CRYPTOGRAPHIC",
    )
    bootstrap = _bootstrap_baseline(path_a_enabled=path_a_enabled, path_b_enabled=False)
    bootstrap_record = dict(binding, namespace="T0", audience="BTCUSDT", root_spki_fingerprint="b" * 64)
    bootstrap_authorization = dict(binding, sequence_predecessor="1:GENESIS", recovery_policy_digest="c" * 64)
    return {
        "fixture": name,
        "schema_version": FIXTURE_SCHEMA_VERSION,
        "evidence_object": {
            "object_id": "A2_2_CURRENT_OBJECT",
            "object_type": "T0_CHECKPOINT",
            "schema_version": "T0-CHECKPOINT-V1",
            "canonical_bytes": '{"checkpoint":"synthetic","sequence":"0"}',
            "byte_length": 41,
            "digest": evidence_object_digest(b'{"checkpoint":"synthetic","sequence":"0"}'),
        },
        "descriptor": dict(binding, object_id="A2_2_CURRENT_OBJECT"),
        "statement": dict(statement_binding, object_id="A2_2_CURRENT_OBJECT", purpose="T0_CHECKPOINT_ISSUER_ATTESTATION",
                          signer_id="SYNTHETIC-TEST-SIGNER", signer_role="T0_CHECKPOINT_ISSUER"),
        "envelope": dict(binding, object_id="A2_2_CURRENT_OBJECT", signature_bytes="MOCK-NOT-CRYPTOGRAPHIC", envelope_digest="f" * 64),
        "test_signer": {"signer_id": "SYNTHETIC-TEST-SIGNER", "role": "T0_CHECKPOINT_ISSUER",
                        "classification": MOCK_LABEL},
        "policy": {"allowed_purposes": ["T0_CHECKPOINT_ISSUER_ATTESTATION"]},
        "policy_profile_authorization": policy_authorization,
        "policy_signed_binding": policy_signed_binding,
        "verification_request": dict(binding, allow_automatic_fallback=False, bootstrap_path=("A" if path_a_enabled else None),
                                     subject_object_id="A2_2_CURRENT_OBJECT"),
        "verifier_allowed_profile": dict(binding, locally_enabled=True),
        "profile": {"lifecycle": "ACTIVE"},
        "bootstrap": bootstrap,
        "bootstrap_record": bootstrap_record,
        "bootstrap_authorization": bootstrap_authorization,
        "historical_fixture": {
            "object_id": "A1-HISTORICAL-OBJECT",
            "signature_profile_id": A1_PROFILE_ID,
            "signature_profile_version": 1,
            "immutable": True,
        },
        "state_snapshot": {
            "trust_roots": ["synthetic-root-fingerprint"],
            "policy_head": "policy-digest-0",
            "anchor_head": [0, "anchor-digest-0"],
            "checkpoint_head": ["checkpoint-0", "object-digest-0"],
            "bootstrap_sequence": 0,
        },
        "accepted_state": "S0",
    }


_BASELINES = {
    "B0": _make_baseline("A2.2-SYNTHETIC-BASELINE-B0"),
    "B0-PF": _make_baseline("A2.2-SYNTHETIC-BASELINE-B0-PF", legacy_statement=True),
    "B-A": _make_baseline("A2.2-SYNTHETIC-HYPOTHETICAL-BASELINE-B-A-NOT-OPERATIONAL", path_a_enabled=True),
}


def _get_existing_path(value: Mapping[str, object], dotted_path: str) -> object:
    cursor: object = value
    for part in dotted_path.split("."):
        if not isinstance(cursor, Mapping) or part not in cursor:
            raise KeyError(dotted_path)
        cursor = cursor[part]
    return cursor


def _set_existing_path(value: dict[str, object], dotted_path: str, new_value: object) -> None:
    _get_existing_path(value, dotted_path)
    parts = dotted_path.split(".")
    cursor: dict[str, object] = value
    for part in parts[:-1]:
        child = cursor[part]
        if not isinstance(child, dict):
            raise KeyError(dotted_path)
        cursor = child
    cursor[parts[-1]] = copy.deepcopy(new_value)


def _leaf_values(value: object, prefix: str = "") -> dict[str, object]:
    if isinstance(value, Mapping):
        leaves: dict[str, object] = {}
        for key, child in value.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            leaves.update(_leaf_values(child, path))
        return leaves
    return {prefix: value}


def fixture_catalog() -> tuple[FixtureSpec, ...]:
    fixtures = []
    for index, (baseline, mutation_path, mutation_value, verdict, reason, dimension) in enumerate(_FIXTURE_ROWS, start=1):
        baseline_bytes = canonicalize(_BASELINES[baseline])
        fixtures.append(FixtureSpec(
            case_id=f"A2.2-NV-{index:02d}",
            baseline=baseline,
            mutations=(mutation_path,),
            expected_verdict=verdict,
            expected_reason=reason,
            dimension_result=dimension,
            baseline_digest=hashlib.sha256(baseline_bytes).hexdigest(),
            mutation_path=mutation_path,
            mutation_value=copy.deepcopy(mutation_value),
            schema_version=FIXTURE_SCHEMA_VERSION,
            dimension_results=_expected_dimensions(mutation_path, verdict),
        ))
    return tuple(fixtures)


def build_fixture(case_id: str) -> tuple[dict[str, object], dict[str, object], FixtureSpec]:
    fixture = next((item for item in fixture_catalog() if item.case_id == case_id), None)
    if fixture is None:
        raise KeyError(case_id)
    baseline = copy.deepcopy(_BASELINES[fixture.baseline])
    mutated = copy.deepcopy(baseline)
    _set_existing_path(mutated, fixture.mutation_path, fixture.mutation_value)
    before, after = _leaf_values(baseline), _leaf_values(mutated)
    changed = {key for key in before if before[key] != after[key]}
    if set(before) != set(after) or changed != {fixture.mutation_path}:
        raise ValueError(f"{case_id}: fixture must change exactly its declared existing leaf")
    return baseline, mutated, fixture


def _expected_dimensions(mutation_path: str, verdict: str) -> dict[str, str]:
    dimensions = {key: "NOT_APPLICABLE" for key in _REQUIRED_DIMENSIONS}
    dimensions.update({"parsing_canonicalization": "PASS", "object_binding": "PASS",
                       "signature": "NOT_VERIFIED", "custody_readback": "NOT_VERIFIED"})
    if mutation_path.startswith("statement.purpose"):
        dimensions["purpose"] = verdict
    elif mutation_path == "verification_request.bootstrap_path":
        dimensions["bootstrap_authorization"] = verdict
    elif mutation_path.startswith("policy."):
        dimensions["policy_authorization"] = verdict
    elif mutation_path.startswith(("verification_request.", "descriptor.", "envelope.", "policy_profile_authorization.", "profile.")):
        dimensions["profile"] = verdict
    elif mutation_path.startswith(("bootstrap.", "bootstrap_record.", "bootstrap_authorization.")):
        dimensions["bootstrap_authorization"] = verdict
        dimensions["custody_readback"] = "NOT_VERIFIED"
    return dimensions


def derive_stage1_facts(fixture: Mapping[str, object]) -> dict[str, bool]:
    """Derive routing facts from normative profile fields and actual fixture bindings."""
    request = fixture.get("verification_request", {})
    statement = fixture.get("statement", {})
    descriptor = fixture.get("descriptor", {})
    envelope = fixture.get("envelope", {})
    policy = fixture.get("policy", {})
    policy_auth = fixture.get("policy_profile_authorization", {})
    policy_signed = fixture.get("policy_signed_binding", {})
    allowed = fixture.get("verifier_allowed_profile", {})
    profile = fixture.get("profile", {})
    bootstrap = fixture.get("bootstrap", {})
    historical = fixture.get("historical_fixture", {})
    if not all(isinstance(item, Mapping) for item in (
        request, statement, descriptor, envelope, policy, policy_auth,
        policy_signed, allowed, profile, bootstrap, historical
    )):
        raise ValueError("fixture contract objects must be mappings")

    selected_id = request.get("signature_profile_id")
    selected_version = request.get("signature_profile_version")
    profile_locations = (descriptor, statement, envelope, policy_auth, policy_signed, allowed)
    binding_mismatch = any(
        item.get("signature_profile_id") != selected_id
        or item.get("signature_profile_version") != selected_version
        for item in profile_locations
    )
    bootstrap_profile_mismatch = False
    if request.get("bootstrap_path") is not None:
        for item in (fixture.get("bootstrap_record", {}), fixture.get("bootstrap_authorization", {})):
            if not isinstance(item, Mapping):
                raise ValueError("bootstrap profile binding must be a mapping")
            bootstrap_profile_mismatch = bootstrap_profile_mismatch or (
                item.get("signature_profile_id") != selected_id
                or item.get("signature_profile_version") != selected_version
            )

    subject_is_historical = request.get("subject_object_id") == historical.get("object_id")
    historical_profile_mismatch = (
        subject_is_historical
        and (selected_id != historical.get("signature_profile_id")
             or selected_version != historical.get("signature_profile_version"))
    )
    statement_profile_mismatch = (
        statement.get("signature_profile_id") != selected_id
        or statement.get("signature_profile_version") != selected_version
    )
    facts = {
        "object_binding_mismatch": (
            fixture.get("evidence_object", {}).get("object_id") != descriptor.get("object_id")
            or descriptor.get("object_id") != statement.get("object_id")
            or descriptor.get("object_id") != envelope.get("object_id")
        ),
        "profile_downgrade_forbidden": request.get("allow_automatic_fallback") is True
            and (binding_mismatch or statement_profile_mismatch),
        "profile_unknown": selected_id not in {PROFILE_ID, A1_PROFILE_ID, LEGACY_PROFILE_ID},
        "profile_not_enabled": selected_id == PROFILE_ID and (
            selected_version != PROFILE_VERSION or allowed.get("locally_enabled") is not True
        ),
        "profile_binding_mismatch": binding_mismatch,
        "profile_version_mismatch": historical_profile_mismatch,
        "profile_retired": profile.get("lifecycle") == "RETIRED",
        "purpose_not_supported": statement.get("purpose") != "T0_CHECKPOINT_ISSUER_ATTESTATION",
        "policy_purpose_not_explicit": "T0_CHECKPOINT_ISSUER_ATTESTATION" not in policy.get("allowed_purposes", []),
    }

    selected_path = request.get("bootstrap_path")
    if selected_path is None:
        facts["path_not_configured"] = True
        return facts
    path_enabled = (
        bootstrap.get("path_a_enabled") is True if selected_path == "A"
        else bootstrap.get("path_b_enabled") is True if selected_path == "B"
        else False
    )
    facts["path_not_configured"] = False
    facts["path_not_enabled"] = not path_enabled
    if not path_enabled:
        return facts

    authorization = bootstrap.get("authorization", {})
    owner_pin = bootstrap.get("owner_pin", {})
    if not isinstance(authorization, Mapping) or not isinstance(owner_pin, Mapping):
        raise ValueError("bootstrap authorization and owner pin must be mappings")
    facts.update({
        "evidence_missing": bootstrap.get("owner_authorization") is None,
        "trust_boundary_unavailable": owner_pin.get("availability") != "AVAILABLE",
        "self_authorization": authorization.get("issuer") == "NEW_ROOT_ONLY",
        "producer_input_untrusted": owner_pin.get("source") == "PRODUCER_SUPPLIED",
        "path_mixing": not isinstance(bootstrap.get("path_evidence"), list)
            or bootstrap.get("path_evidence") != [f"PATH_{selected_path}"],
        "authorization_invalid": authorization.get("signature") != "SYNTHETIC-VALID",
        "digest_mismatch": authorization.get("subject_digest") != bootstrap.get("record_digest"),
        "namespace_mismatch": authorization.get("namespace") != bootstrap.get("namespace"),
        "audience_mismatch": authorization.get("audience") != bootstrap.get("audience"),
        "root_fingerprint_mismatch": authorization.get("root_spki_fingerprint") != bootstrap.get("root_spki_fingerprint"),
        "root_role_mismatch": authorization.get("root_role") != bootstrap.get("root_role"),
        "bootstrap_profile_mismatch": (
            bootstrap_profile_mismatch
            or authorization.get("profile_binding") != bootstrap.get("profile_binding")
        ),
        "sequence_mismatch": authorization.get("sequence_predecessor") != bootstrap.get("sequence_predecessor"),
        "recovery_policy_mismatch": authorization.get("recovery_policy_digest") != bootstrap.get("recovery_policy_digest"),
        "readback_mismatch": bootstrap.get("verifier_readback_bytes") != bootstrap.get("expected_readback_bytes"),
        "readback_unavailable": bootstrap.get("verifier_readback_availability") != "AVAILABLE",
    })
    return facts


def _dimension_results_for(fixture: Mapping[str, object], facts: Mapping[str, bool], result: FixtureResult) -> dict[str, str]:
    dimensions = {key: "NOT_APPLICABLE" for key in _REQUIRED_DIMENSIONS}
    dimensions.update({"parsing_canonicalization": "PASS", "object_binding": "PASS",
                       "signature": "NOT_VERIFIED", "custody_readback": "NOT_VERIFIED"})
    if facts.get("object_binding_mismatch"):
        dimensions["object_binding"] = result.verdict
    if facts.get("purpose_not_supported"):
        dimensions["purpose"] = result.verdict
    elif facts.get("policy_purpose_not_explicit"):
        dimensions["policy_authorization"] = result.verdict
    elif any(facts.get(key) for key in ("profile_downgrade_forbidden", "profile_unknown",
              "profile_not_enabled", "profile_binding_mismatch", "profile_version_mismatch", "profile_retired")):
        dimensions["profile"] = result.verdict
    elif any(key.startswith(("path_", "evidence_", "trust_boundary_", "self_authorization",
              "producer_input_", "authorization_", "digest_", "namespace_", "audience_",
              "root_", "bootstrap_", "sequence_", "recovery_", "readback_")) and value
              for key, value in facts.items()):
        dimensions["bootstrap_authorization"] = result.verdict
    return dimensions


def evaluate_stage1_facts(facts: Mapping[str, bool]) -> FixtureResult:
    """Evaluate synthetic facts in deterministic profile then bootstrap order."""
    for key, verdict, reason, dimension in _PROFILE_RULES:
        if facts.get(key, False) is True:
            return FixtureResult(verdict, reason, dimension)
    for key, verdict, reason, dimension in _BOOTSTRAP_RULES:
        if facts.get(key, False) is True:
            return FixtureResult(verdict, reason, dimension)
    return FixtureResult("BLOCKED", "ROOT_BOOTSTRAP_PATH_NOT_ENABLED", "Path unavailable")


def evaluate_stage1_fixture(case_id: str, state: StageStateSnapshot) -> tuple[StageStateSnapshot, FixtureResult]:
    baseline, mutated, _fixture = build_fixture(case_id)
    return evaluate_fixture_content(baseline, mutated, state)


class MockSignatureVerifier:
    """A routing stub only. Never represents cryptographic verification."""

    classification = MOCK_LABEL

    def verify(self, _message: bytes, mock_result: bytes) -> str:
        return MOCK_ACCEPTED if mock_result == b"mock-ok" else MOCK_REJECTED


def evaluate_fixture_content(
    baseline: Mapping[str, object],
    mutated: Mapping[str, object],
    state: StageStateSnapshot,
) -> tuple[StageStateSnapshot, FixtureResult]:
    """Evaluate one semantic fixture mutation; never perform state transitions."""
    before, after = _leaf_values(baseline), _leaf_values(mutated)
    if set(before) != set(after):
        return state, FixtureResult("INVALID", "FIXTURE_STRUCTURE_CHANGED", "Fixture structure INVALID",
                                    dimension_results={}, state_s0=state, state_s1=state,
                                    forbidden_transitions={key: True for key in _FORBIDDEN_TRANSITIONS})
    changed = {key for key in before if before[key] != after[key]}
    if len(changed) != 1:
        return state, FixtureResult("INVALID", "FIXTURE_SINGLE_MUTATION_VIOLATION", "Fixture mutation INVALID",
                                    dimension_results={}, state_s0=state, state_s1=state,
                                    forbidden_transitions={key: True for key in _FORBIDDEN_TRANSITIONS})
    try:
        evidence = baseline.get("evidence_object", {})
        if not isinstance(evidence, Mapping):
            raise ValueError("evidence object must be a mapping")
        raw = evidence.get("canonical_bytes")
        if not isinstance(raw, str):
            raise ValueError("canonical evidence bytes missing")
        raw_bytes = raw.encode("utf-8", "strict")
        parse_canonical_json(raw_bytes)
        if evidence.get("byte_length") != len(raw_bytes):
            raise ValueError("evidence byte length mismatch")
        if evidence.get("digest") != evidence_object_digest(raw_bytes):
            raise ValueError("evidence object digest mismatch")
        if not evidence.get("object_id") or not evidence.get("object_type") or not evidence.get("schema_version"):
            raise ValueError("evidence object identity/schema incomplete")
        snapshot = baseline.get("state_snapshot", {})
        mutated_snapshot = mutated.get("state_snapshot", {})
        if mutated_snapshot != snapshot:
            return state, FixtureResult("INVALID", "FIXTURE_STATE_TRANSITION_FORBIDDEN", "Fixture state transition INVALID",
                                        dimension_results={}, state_s0=state, state_s1=state,
                                        forbidden_transitions={key: True for key in _FORBIDDEN_TRANSITIONS})
        if not isinstance(snapshot, Mapping) or (
            tuple(snapshot.get("trust_roots", ())) != state.trust_roots
            or snapshot.get("policy_head") != state.policy_head
            or tuple(snapshot.get("anchor_head", ())) != state.anchor_head
            or tuple(snapshot.get("checkpoint_head", ())) != state.checkpoint_head
            or snapshot.get("bootstrap_sequence") != state.bootstrap_sequence
        ):
            raise ValueError("fixture S0 state snapshot mismatch")
        facts = derive_stage1_facts(mutated)
        result = evaluate_stage1_facts(facts)
        if facts.get("object_binding_mismatch"):
            result = FixtureResult("INVALID", "OBJECT_BINDING_MISMATCH", "Object binding INVALID")
        dimensions = _dimension_results_for(mutated, facts, result)
        result = FixtureResult(result.verdict, result.reason_code, result.dimension_result,
                               state_advanced=False, dimension_results=dimensions,
                               state_s0=state, state_s1=state,
                               forbidden_transitions={key: True for key in _FORBIDDEN_TRANSITIONS})
    except (KeyError, TypeError, ValueError):
        result = FixtureResult("INVALID", "FIXTURE_CONTENT_INVALID", "Fixture content INVALID",
                               dimension_results={}, state_s0=state, state_s1=state,
                               forbidden_transitions={key: True for key in _FORBIDDEN_TRANSITIONS})
    return state, result


def validate_profile_bindings(bindings: Mapping[str, Mapping[str, object]]) -> FixtureResult:
    """Check exact profile ID/version across every modeled normative location."""
    required = (
        "descriptor", "statement", "envelope", "policy_profile_authorization",
        "policy_signed_binding", "bootstrap_record", "bootstrap_authorization",
        "verifier_request", "verifier_allowed_profile",
    )
    if any(location not in bindings for location in required):
        return FixtureResult("INVALID", "PROFILE_BINDING_MISMATCH", "Profile binding INVALID")
    values = []
    for location in required:
        item = bindings[location]
        if not isinstance(item, Mapping):
            return FixtureResult("INVALID", "PROFILE_BINDING_MISMATCH", "Profile binding INVALID")
        profile_id = item.get("signature_profile_id")
        profile_version = item.get("signature_profile_version")
        if type(profile_id) is not str or type(profile_version) is not int:
            return FixtureResult("INVALID", "PROFILE_BINDING_MISMATCH", "Profile binding INVALID")
        values.append((profile_id, profile_version))
    if any(value != (PROFILE_ID, PROFILE_VERSION) for value in values):
        return FixtureResult("INVALID", "PROFILE_BINDING_MISMATCH", "Profile binding INVALID")
    return FixtureResult("PASS", "PROFILE_BINDING_MATCH", "Profile binding PASS")
