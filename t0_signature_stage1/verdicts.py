"""Pure deterministic fixture verdict routing; not a production verifier."""

from __future__ import annotations

from dataclasses import dataclass
import copy
import hashlib
from typing import Mapping

from .primitives import canonicalize


PROFILE_ID = "T0-CHECKPOINT-ISSUER-SIGNATURE-PROFILE-V2"
PROFILE_VERSION = 2
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
    fact_key: str = ""
    mutation_value: object = None


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
    ("B0", "purpose_not_supported", "UNTRUSTED", "PURPOSE_NOT_SUPPORTED_BY_PROFILE", "Purpose/profile authorization UNTRUSTED"),
    ("B0", "policy_purpose_not_explicit", "BLOCKED", "POLICY_PURPOSE_NOT_EXPLICIT", "Policy purpose authorization BLOCKED"),
    ("B0", "profile_version_mismatch", "INVALID", "PROFILE_VERSION_MISMATCH", "Historical object/profile binding INVALID"),
    ("B0-PF", "profile_downgrade_forbidden", "BLOCKED", "PROFILE_DOWNGRADE_FORBIDDEN", "Profile downgrade BLOCKED"),
    ("B0", "profile_unknown", "BLOCKED", "PROFILE_UNKNOWN", "Profile selection BLOCKED"),
    ("B0", "profile_not_enabled", "BLOCKED", "PROFILE_NOT_ENABLED", "Profile selection BLOCKED"),
    ("B0", "profile_binding_mismatch", "INVALID", "PROFILE_BINDING_MISMATCH", "Envelope/profile binding INVALID"),
    ("B0", "profile_binding_mismatch", "INVALID", "PROFILE_BINDING_MISMATCH", "Policy/profile binding INVALID"),
    ("B0", "profile_retired", "UNTRUSTED", "PROFILE_RETIRED", "Profile lifecycle UNTRUSTED"),
    ("B0", "path_not_enabled", "BLOCKED", "ROOT_BOOTSTRAP_PATH_NOT_ENABLED", "Path configuration BLOCKED"),
    ("B0", "path_not_enabled", "BLOCKED", "ROOT_BOOTSTRAP_PATH_NOT_ENABLED", "Path configuration BLOCKED"),
    ("B-A", "evidence_missing", "BLOCKED", "ROOT_BOOTSTRAP_EVIDENCE_MISSING", "Evidence presence BLOCKED"),
    ("B-A", "trust_boundary_unavailable", "UNKNOWN", "ROOT_BOOTSTRAP_TRUST_BOUNDARY_UNAVAILABLE", "Trust-boundary availability UNKNOWN"),
    ("B-A", "authorization_invalid", "INVALID", "ROOT_BOOTSTRAP_AUTHORIZATION_INVALID", "Authorization signature INVALID"),
    ("B-A", "digest_mismatch", "INVALID", "ROOT_BOOTSTRAP_DIGEST_MISMATCH", "Subject binding INVALID"),
    ("B-A", "namespace_mismatch", "INVALID", "ROOT_BOOTSTRAP_NAMESPACE_MISMATCH", "Namespace binding INVALID"),
    ("B-A", "audience_mismatch", "INVALID", "ROOT_BOOTSTRAP_AUDIENCE_MISMATCH", "Audience binding INVALID"),
    ("B-A", "root_fingerprint_mismatch", "INVALID", "ROOT_BOOTSTRAP_ROOT_FINGERPRINT_MISMATCH", "Root binding INVALID"),
    ("B-A", "root_role_mismatch", "INVALID", "ROOT_BOOTSTRAP_ROLE_MISMATCH", "Role binding INVALID"),
    ("B-A", "bootstrap_profile_mismatch", "INVALID", "ROOT_BOOTSTRAP_PROFILE_MISMATCH", "Profile binding INVALID"),
    ("B-A", "sequence_mismatch", "INVALID", "ROOT_BOOTSTRAP_SEQUENCE_MISMATCH", "Sequence binding INVALID"),
    ("B-A", "recovery_policy_mismatch", "INVALID", "ROOT_BOOTSTRAP_RECOVERY_POLICY_MISMATCH", "Recovery binding INVALID"),
    ("B-A", "readback_mismatch", "INVALID", "ROOT_BOOTSTRAP_READBACK_MISMATCH", "Readback integrity INVALID"),
    ("B-A", "readback_unavailable", "UNKNOWN", "ROOT_BOOTSTRAP_READBACK_UNAVAILABLE", "Readback availability UNKNOWN"),
    ("B-A", "self_authorization", "BLOCKED", "ROOT_BOOTSTRAP_SELF_AUTHORIZATION_FORBIDDEN", "Self-authorization BLOCKED"),
    ("B-A", "producer_input_untrusted", "BLOCKED", "ROOT_BOOTSTRAP_PRODUCER_INPUT_UNTRUSTED", "Trust-source BLOCKED"),
    ("B-A", "path_mixing", "BLOCKED", "ROOT_BOOTSTRAP_PATH_MIXING_FORBIDDEN", "Path mixing BLOCKED"),
)


_BASELINES = {
    "B0": {
        "fixture": "A2.2-SYNTHETIC-BASELINE-B0",
        "profile_id": PROFILE_ID,
        "profile_version": PROFILE_VERSION,
        "purpose": "T0_CHECKPOINT_ISSUER_ATTESTATION",
        "policy_explicit_purpose": True,
        "bootstrap_path_a": "NOT_ENABLED",
        "bootstrap_path_b": "NOT_ENABLED",
        "accepted_state": "S0",
    },
    "B0-PF": {
        "fixture": "A2.2-SYNTHETIC-BASELINE-B0-PF",
        "statement_profile_id": "T0-CHECKPOINT-ISSUER-SIGNATURE-PROFILE-LEGACY",
        "descriptor_profile_id": PROFILE_ID,
        "envelope_profile_id": PROFILE_ID,
        "policy_profile_id": PROFILE_ID,
        "request_profile_id": PROFILE_ID,
        "accepted_state": "S0",
    },
    "B-A": {
        "fixture": "A2.2-SYNTHETIC-HYPOTHETICAL-BASELINE-B-A-NOT-OPERATIONAL",
        "path": "A",
        "path_configured": True,
        "path_enabled_in_hypothetical_fixture_only": True,
        "owner_pin": "synthetic-only",
        "owner_authorization": "synthetic-only",
        "accepted_state": "S0",
        "operational_bootstrap_enabled": False,
    },
}

_MUTATION_DEFINITIONS = (
    ("statement.purpose", "T0_CHECKPOINT_OWNER_ATTESTATION"),
    ("policy.allowed_purposes", []),
    ("verification_request.profile_id", PROFILE_ID),
    ("verification_request.allow_automatic_fallback", True),
    ("verification_request.profile_id", "UNKNOWN-PROFILE"),
    ("verification_request.profile_version", 3),
    ("envelope.profile_id", "SUBSTITUTED-PROFILE"),
    ("policy.profile_version", 3),
    ("profile.lifecycle", "RETIRED"),
    ("verification_request.bootstrap_path", "A"),
    ("verification_request.bootstrap_path", "B"),
    ("bootstrap.owner_authorization", None),
    ("bootstrap.owner_pin_availability", "UNAVAILABLE"),
    ("bootstrap.authorization.signature", "INVALID-SYNTHETIC-BYTES"),
    ("bootstrap.authorization.subject_digest", "0" * 64),
    ("bootstrap.namespace", "SUBSTITUTED-NAMESPACE"),
    ("bootstrap.audience", "SUBSTITUTED-AUDIENCE"),
    ("bootstrap.root_spki_fingerprint", "0" * 64),
    ("bootstrap.root_role", "UNAUTHORIZED-ROLE"),
    ("bootstrap.profile_id_version", "SUBSTITUTED-PROFILE-VERSION"),
    ("bootstrap.sequence_predecessor", "SUBSTITUTED-SEQUENCE-PREDECESSOR"),
    ("bootstrap.recovery_policy_digest", "0" * 64),
    ("bootstrap.verifier_readback_bytes", "ALTERED-READBACK"),
    ("bootstrap.verifier_readback_availability", "UNAVAILABLE"),
    ("bootstrap.authorization.issuer", "NEW-ROOT-ONLY"),
    ("bootstrap.owner_pin.source", "PRODUCER-SUPPLIED"),
    ("bootstrap.path_evidence", "PATH-A-PLUS-PATH-B"),
)


def fixture_catalog() -> tuple[FixtureSpec, ...]:
    fixtures = []
    for index, (baseline, fact_key, verdict, reason, dimension) in enumerate(_FIXTURE_ROWS, start=1):
        mutation_path, mutation_value = _MUTATION_DEFINITIONS[index - 1]
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
            fact_key=fact_key,
            mutation_value=mutation_value,
        ))
    return tuple(fixtures)


def build_fixture(case_id: str) -> tuple[dict[str, object], dict[str, object], FixtureSpec]:
    """Return a fresh baseline and a clone with exactly one declared mutation."""
    fixture = next((item for item in fixture_catalog() if item.case_id == case_id), None)
    if fixture is None:
        raise KeyError(case_id)
    baseline = copy.deepcopy(_BASELINES[fixture.baseline])
    mutated = copy.deepcopy(baseline)
    cursor = mutated
    parts = fixture.mutation_path.split(".")
    for part in parts[:-1]:
        child = cursor.get(part)
        if not isinstance(child, dict):
            child = {}
            cursor[part] = child
        cursor = child
    cursor[parts[-1]] = copy.deepcopy(fixture.mutation_value)
    return baseline, mutated, fixture


def evaluate_stage1_facts(facts: Mapping[str, bool]) -> FixtureResult:
    """Evaluate synthetic facts in deterministic profile then bootstrap order."""
    for key, verdict, reason, dimension in _PROFILE_RULES:
        if facts.get(key, False) is True:
            return FixtureResult(verdict, reason, dimension)
    for key, verdict, reason, dimension in _BOOTSTRAP_RULES:
        if facts.get(key, False) is True:
            return FixtureResult(verdict, reason, dimension)
    # The governing A2.2 draft has no enabled bootstrap path. No success path
    # is implemented or implied by this Stage I harness.
    return FixtureResult("BLOCKED", "ROOT_BOOTSTRAP_PATH_NOT_ENABLED", "Path unavailable")


def evaluate_stage1_fixture(case_id: str, state: StageStateSnapshot) -> tuple[StageStateSnapshot, FixtureResult]:
    fixture = next((item for item in fixture_catalog() if item.case_id == case_id), None)
    if fixture is None:
        raise KeyError(case_id)
    result = evaluate_stage1_facts({fixture.fact_key: True})
    # Return the identical immutable snapshot: this harness has no state writer.
    return state, result


class MockSignatureVerifier:
    """A routing stub only. Never represents cryptographic verification."""

    classification = MOCK_LABEL

    def verify(self, _message: bytes, mock_result: bytes) -> str:
        return MOCK_ACCEPTED if mock_result == b"mock-ok" else MOCK_REJECTED


def validate_profile_bindings(bindings: Mapping[str, Mapping[str, object]]) -> FixtureResult:
    """Check immutable profile ID/version across five contract locations.

    Required locations: descriptor, statement, envelope, policy and request.
    This validates only field equality; it does not establish signature trust.
    """
    required = ("descriptor", "statement", "envelope", "policy", "request")
    if any(location not in bindings for location in required):
        return FixtureResult("INVALID", "PROFILE_BINDING_MISMATCH", "Profile binding INVALID")
    values = []
    for location in required:
        item = bindings[location]
        if not isinstance(item, Mapping) or "profile_id" not in item or "profile_version" not in item:
            return FixtureResult("INVALID", "PROFILE_BINDING_MISMATCH", "Profile binding INVALID")
        profile_id = item["profile_id"]
        profile_version = item["profile_version"]
        if type(profile_id) is not str or type(profile_version) is not int:
            return FixtureResult("INVALID", "PROFILE_BINDING_MISMATCH", "Profile binding INVALID")
        values.append((profile_id, profile_version))
    if any(value != (PROFILE_ID, PROFILE_VERSION) for value in values):
        return FixtureResult("INVALID", "PROFILE_BINDING_MISMATCH", "Profile binding INVALID")
    return FixtureResult("PASS", "PROFILE_BINDING_MATCH", "Profile binding PASS")
