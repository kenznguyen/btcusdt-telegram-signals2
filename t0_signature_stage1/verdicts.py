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
    ("B0", "statement.purpose", "T0_CHECKPOINT_OWNER_ATTESTATION", "UNTRUSTED", "PURPOSE_NOT_SUPPORTED_BY_PROFILE", "Purpose/profile authorization UNTRUSTED"),
    ("B0", "policy.allowed_purposes", [], "BLOCKED", "POLICY_PURPOSE_NOT_EXPLICIT", "Policy purpose authorization BLOCKED"),
    ("B0", "verification_request.subject_fixture", "A1_HISTORICAL", "INVALID", "PROFILE_VERSION_MISMATCH", "Historical object/profile binding INVALID"),
    ("B0-PF", "verification_request.allow_automatic_fallback", True, "BLOCKED", "PROFILE_DOWNGRADE_FORBIDDEN", "Profile downgrade BLOCKED"),
    ("B0", "verification_request.profile_id", "UNKNOWN-PROFILE", "BLOCKED", "PROFILE_UNKNOWN", "Profile selection BLOCKED"),
    ("B0", "verification_request.profile_version", 3, "BLOCKED", "PROFILE_NOT_ENABLED", "Profile selection BLOCKED"),
    ("B0", "envelope.profile_id", "SUBSTITUTED-PROFILE", "INVALID", "PROFILE_BINDING_MISMATCH", "Envelope/profile binding INVALID"),
    ("B0", "policy.profile_version", 3, "INVALID", "PROFILE_BINDING_MISMATCH", "Policy/profile binding INVALID"),
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
    ("B-A", "bootstrap.profile_binding", "SUBSTITUTED-PROFILE-VERSION", "INVALID", "ROOT_BOOTSTRAP_PROFILE_MISMATCH", "Profile binding INVALID"),
    ("B-A", "bootstrap.sequence_predecessor", "SUBSTITUTED-SEQUENCE-PREDECESSOR", "INVALID", "ROOT_BOOTSTRAP_SEQUENCE_MISMATCH", "Sequence binding INVALID"),
    ("B-A", "bootstrap.recovery_policy_digest", "0" * 64, "INVALID", "ROOT_BOOTSTRAP_RECOVERY_POLICY_MISMATCH", "Recovery binding INVALID"),
    ("B-A", "bootstrap.verifier_readback_bytes", "ALTERED-READBACK", "INVALID", "ROOT_BOOTSTRAP_READBACK_MISMATCH", "Readback integrity INVALID"),
    ("B-A", "bootstrap.verifier_readback_availability", "UNAVAILABLE", "UNKNOWN", "ROOT_BOOTSTRAP_READBACK_UNAVAILABLE", "Readback availability UNKNOWN"),
    ("B-A", "bootstrap.authorization.issuer", "NEW_ROOT_ONLY", "BLOCKED", "ROOT_BOOTSTRAP_SELF_AUTHORIZATION_FORBIDDEN", "Self-authorization BLOCKED"),
    ("B-A", "bootstrap.owner_pin.source", "PRODUCER_SUPPLIED", "BLOCKED", "ROOT_BOOTSTRAP_PRODUCER_INPUT_UNTRUSTED", "Trust-source BLOCKED"),
    ("B-A", "bootstrap.path_evidence", ["PATH_A", "PATH_B"], "BLOCKED", "ROOT_BOOTSTRAP_PATH_MIXING_FORBIDDEN", "Path mixing BLOCKED"),
)


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


_BASELINES = {
    "B0": {
        "fixture": "A2.2-SYNTHETIC-BASELINE-B0",
        "descriptor": {"profile_id": PROFILE_ID, "profile_version": PROFILE_VERSION},
        "statement": {
            "profile_id": PROFILE_ID,
            "profile_version": PROFILE_VERSION,
            "purpose": "T0_CHECKPOINT_ISSUER_ATTESTATION",
        },
        "envelope": {"profile_id": PROFILE_ID, "profile_version": PROFILE_VERSION},
        "policy": {
            "profile_id": PROFILE_ID,
            "profile_version": PROFILE_VERSION,
            "allowed_purposes": ["T0_CHECKPOINT_ISSUER_ATTESTATION"],
        },
        "verification_request": {
            "profile_id": PROFILE_ID,
            "profile_version": PROFILE_VERSION,
            "allow_automatic_fallback": False,
            "bootstrap_path": None,
            "subject_fixture": "A2_2_CURRENT",
        },
        "profile": {"lifecycle": "ACTIVE"},
        "bootstrap": _bootstrap_baseline(path_a_enabled=False, path_b_enabled=False),
        "historical_fixture": {"fixture": "A1-HISTORICAL-SEPARATE", "profile_id": "A1"},
        "accepted_state": "S0",
    },
    "B0-PF": {
        "fixture": "A2.2-SYNTHETIC-BASELINE-B0-PF",
        "descriptor": {"profile_id": PROFILE_ID, "profile_version": PROFILE_VERSION},
        "statement": {
            "profile_id": "T0-CHECKPOINT-ISSUER-SIGNATURE-PROFILE-LEGACY",
            "profile_version": 1,
            "purpose": "T0_CHECKPOINT_ISSUER_ATTESTATION",
        },
        "envelope": {"profile_id": PROFILE_ID, "profile_version": PROFILE_VERSION},
        "policy": {
            "profile_id": PROFILE_ID,
            "profile_version": PROFILE_VERSION,
            "allowed_purposes": ["T0_CHECKPOINT_ISSUER_ATTESTATION"],
        },
        "verification_request": {
            "profile_id": PROFILE_ID,
            "profile_version": PROFILE_VERSION,
            "allow_automatic_fallback": False,
            "bootstrap_path": None,
            "subject_fixture": "A2_2_CURRENT",
        },
        "profile": {"lifecycle": "ACTIVE"},
        "bootstrap": _bootstrap_baseline(path_a_enabled=False, path_b_enabled=False),
        "historical_fixture": {"fixture": "A1-HISTORICAL-SEPARATE", "profile_id": "A1"},
        "accepted_state": "S0",
    },
    "B-A": {
        "fixture": "A2.2-SYNTHETIC-HYPOTHETICAL-BASELINE-B-A-NOT-OPERATIONAL",
        "descriptor": {"profile_id": PROFILE_ID, "profile_version": PROFILE_VERSION},
        "statement": {
            "profile_id": PROFILE_ID,
            "profile_version": PROFILE_VERSION,
            "purpose": "T0_CHECKPOINT_ISSUER_ATTESTATION",
        },
        "envelope": {"profile_id": PROFILE_ID, "profile_version": PROFILE_VERSION},
        "policy": {
            "profile_id": PROFILE_ID,
            "profile_version": PROFILE_VERSION,
            "allowed_purposes": ["T0_CHECKPOINT_ISSUER_ATTESTATION"],
        },
        "verification_request": {
            "profile_id": PROFILE_ID,
            "profile_version": PROFILE_VERSION,
            "allow_automatic_fallback": False,
            "bootstrap_path": "A",
            "subject_fixture": "A2_2_CURRENT",
        },
        "profile": {"lifecycle": "ACTIVE"},
        "bootstrap": _bootstrap_baseline(path_a_enabled=True, path_b_enabled=False),
        "historical_fixture": {"fixture": "A1-HISTORICAL-SEPARATE", "profile_id": "A1"},
        "accepted_state": "S0",
    },
}


def _get_existing_path(value: Mapping[str, object], dotted_path: str) -> object:
    """Read a dotted path, rejecting any missing/non-object intermediate."""
    cursor: object = value
    for part in dotted_path.split("."):
        if not isinstance(cursor, Mapping) or part not in cursor:
            raise KeyError(dotted_path)
        cursor = cursor[part]
    return cursor


def _set_existing_path(value: dict[str, object], dotted_path: str, new_value: object) -> None:
    """Replace an existing leaf only; never create a missing object or field."""
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
            mutation_value=mutation_value,
        ))
    return tuple(fixtures)


def build_fixture(case_id: str) -> tuple[dict[str, object], dict[str, object], FixtureSpec]:
    """Return a fresh schema-shaped baseline and one existing-leaf mutation."""
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


def derive_stage1_facts(fixture: Mapping[str, object]) -> dict[str, bool]:
    """Derive deterministic routing facts from fixture content, not catalog metadata."""
    request = fixture.get("verification_request", {})
    statement = fixture.get("statement", {})
    descriptor = fixture.get("descriptor", {})
    envelope = fixture.get("envelope", {})
    policy = fixture.get("policy", {})
    profile = fixture.get("profile", {})
    bootstrap = fixture.get("bootstrap", {})
    if not all(isinstance(item, Mapping) for item in (request, statement, descriptor, envelope, policy, profile, bootstrap)):
        raise ValueError("fixture contract objects must be mappings")

    selected_profile = request.get("profile_id")
    selected_version = request.get("profile_version")
    statement_profile = statement.get("profile_id")
    facts = {
        "profile_downgrade_forbidden": (
            request.get("allow_automatic_fallback") is True
            and statement_profile != selected_profile
        ),
        "profile_unknown": selected_profile not in {PROFILE_ID},
        "profile_not_enabled": selected_profile == PROFILE_ID and selected_version != PROFILE_VERSION,
        "profile_binding_mismatch": (
            descriptor.get("profile_id") != statement_profile
            or descriptor.get("profile_version") != statement.get("profile_version")
            or envelope.get("profile_id") != statement_profile
            or envelope.get("profile_version") != statement.get("profile_version")
            or policy.get("profile_id") != selected_profile
            or policy.get("profile_version") != selected_version
            or descriptor.get("profile_id") != selected_profile
            or descriptor.get("profile_version") != selected_version
        ),
        "profile_version_mismatch": (
            request.get("subject_fixture") == "A1_HISTORICAL"
            and selected_profile == PROFILE_ID
            and selected_version == PROFILE_VERSION
        ),
        "profile_retired": profile.get("lifecycle") == "RETIRED",
        "purpose_not_supported": statement.get("purpose") != "T0_CHECKPOINT_ISSUER_ATTESTATION",
        "policy_purpose_not_explicit": (
            "T0_CHECKPOINT_ISSUER_ATTESTATION" not in policy.get("allowed_purposes", [])
        ),
    }

    selected_path = request.get("bootstrap_path")
    if selected_path is None:
        facts["path_not_configured"] = True
        return facts
    if selected_path == "A":
        path_enabled = bootstrap.get("path_a_enabled") is True
    elif selected_path == "B":
        path_enabled = bootstrap.get("path_b_enabled") is True
    else:
        path_enabled = False
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
        "path_mixing": (
            not isinstance(bootstrap.get("path_evidence"), list)
            or bootstrap.get("path_evidence") != [f"PATH_{selected_path}"]
        ),
        "authorization_invalid": authorization.get("signature") != "SYNTHETIC-VALID",
        "digest_mismatch": authorization.get("subject_digest") != bootstrap.get("record_digest"),
        "namespace_mismatch": authorization.get("namespace") != bootstrap.get("namespace"),
        "audience_mismatch": authorization.get("audience") != bootstrap.get("audience"),
        "root_fingerprint_mismatch": authorization.get("root_spki_fingerprint") != bootstrap.get("root_spki_fingerprint"),
        "root_role_mismatch": authorization.get("root_role") != bootstrap.get("root_role"),
        "bootstrap_profile_mismatch": authorization.get("profile_binding") != bootstrap.get("profile_binding"),
        "sequence_mismatch": authorization.get("sequence_predecessor") != bootstrap.get("sequence_predecessor"),
        "recovery_policy_mismatch": authorization.get("recovery_policy_digest") != bootstrap.get("recovery_policy_digest"),
        "readback_mismatch": bootstrap.get("verifier_readback_bytes") != bootstrap.get("expected_readback_bytes"),
        "readback_unavailable": bootstrap.get("verifier_readback_availability") != "AVAILABLE",
    })
    return facts


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


def evaluate_fixture_content(
    baseline: Mapping[str, object],
    mutated: Mapping[str, object],
    state: StageStateSnapshot,
) -> tuple[StageStateSnapshot, FixtureResult]:
    """Evaluate actual fixture content and reject structural/compound mutations."""
    before, after = _leaf_values(baseline), _leaf_values(mutated)
    if set(before) != set(after):
        return state, FixtureResult("INVALID", "FIXTURE_STRUCTURE_CHANGED", "Fixture structure INVALID")
    changed = {key for key in before if before[key] != after[key]}
    if len(changed) > 1:
        return state, FixtureResult("INVALID", "FIXTURE_SINGLE_MUTATION_VIOLATION", "Fixture mutation INVALID")
    try:
        result = evaluate_stage1_facts(derive_stage1_facts(mutated))
    except (KeyError, TypeError, ValueError):
        result = FixtureResult("INVALID", "FIXTURE_CONTENT_INVALID", "Fixture content INVALID")
    return state, result


def evaluate_stage1_fixture(case_id: str, state: StageStateSnapshot) -> tuple[StageStateSnapshot, FixtureResult]:
    baseline, mutated, _fixture = build_fixture(case_id)
    return evaluate_fixture_content(baseline, mutated, state)


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
