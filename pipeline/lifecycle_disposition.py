"""Pure lifecycle disposition evaluator; no I/O or execution capabilities."""
from collections.abc import Mapping
import re

PROTECTED = {
    "T0_CANONICAL": "PROT_CLASS_T0_CANONICAL",
    "CORE_LEDGER": "PROT_CLASS_CORE_LEDGER",
    "AI_LEDGER": "PROT_CLASS_AI_LEDGER",
    "T3_PROTECTED_EVIDENCE": "PROT_CLASS_T3_EVIDENCE",
    "GOVERNANCE_EVIDENCE": "PROT_CLASS_GOVERNANCE_EVIDENCE",
}
REVIEW = {"T4_DETERMINISTIC_CACHE", "T2_EPHEMERAL_INFERENCE_OUTPUT",
          "T1_RAW_OBSERVATION", "NONCANONICAL_COPY"}
POLICIES = {("RET-01", "B"), ("RET-02", "B")}
OBLIGATIONS = {"REPLAY_RECOVERY": "RET_REPLAY_RECOVERY_OPEN",
               "MODEL_REPRODUCTION": "RET_MODEL_REPRODUCTION_OPEN",
               "VALIDATION_REPROCESS": "RET_VALIDATION_REPROCESS_OPEN"}


def _text(value):
    return isinstance(value, str) and bool(value.strip())


def _result(state, codes):
    return {"disposition": state, "reason_codes": sorted(set(codes) or {"UNK_UNSUPPORTED_VALUE"}),
            "mutation_performed": False, "execution_authorized": False}


def _unknowns(record, codes):
    if not _text(record.get("steward")):
        codes.add("UNK_STEWARD_OWNER")
    if (record.get("policy_id"), record.get("policy_version")) not in POLICIES:
        codes.add("UNK_POLICY_REFERENCE")
    integrity = record.get("integrity")
    if not isinstance(integrity, Mapping):
        codes.add("UNK_INTEGRITY_METADATA")
    elif (integrity.get("algorithm") != "sha256"
          or not isinstance(integrity.get("digest"), str)
          or re.fullmatch(r"[0-9a-f]{64}", integrity.get("digest", "")) is None
          or type(integrity.get("byte_length")) is not int
          or integrity.get("byte_length", -1) < 0):
        codes.add("UNK_INTEGRITY_MISMATCH")
    if not _text(record.get("evidence_revision")):
        codes.add("UNK_EVIDENCE_REVISION")


def evaluate_disposition(record):
    """Evaluate one supplied metadata record; never reads external state."""
    if not isinstance(record, Mapping):
        return _result("BLOCKED_UNKNOWN", {"UNK_OBJECT_IDENTITY"})
    codes = set()
    identity_ok = (record.get("identity_verified") is True and
                   all(_text(record.get(k)) for k in ("object_id", "version_id", "namespace")))
    kind = record.get("data_class")
    if identity_ok and kind in PROTECTED:
        codes.add(PROTECTED[kind])

    holds = record.get("holds")
    hold_unknown = not isinstance(holds, Mapping) or holds.get("complete") is not True or not isinstance(holds.get("items"), list)
    binding_hold = False
    if isinstance(holds, Mapping) and isinstance(holds.get("items"), list):
        for item in holds["items"]:
            if not isinstance(item, Mapping):
                hold_unknown = True
            elif item.get("status") == "ACTIVE" and item.get("binding") is True and _text(item.get("hold_id")) and _text(item.get("owner")):
                binding_hold = True
            elif item.get("status") not in {"ACTIVE", "RELEASED", "CLOSED"} or item.get("binding") not in {True, False} or not _text(item.get("hold_id")):
                hold_unknown = True
    if binding_hold and identity_ok:
        codes.add("PROT_BINDING_HOLD_ACTIVE")
    if codes:
        _unknowns(record, codes)
        return _result("PROTECTED", codes)

    if not identity_ok:
        codes.add("UNK_OBJECT_IDENTITY")
    if kind not in PROTECTED and kind not in REVIEW:
        codes.add("UNK_CLASSIFICATION")
    _unknowns(record, codes)

    lineage = record.get("lineage")
    if not isinstance(lineage, Mapping) or lineage.get("complete") is not True or not all(
        _text(lineage.get(k)) for k in ("source_object_id", "source_version_id", "transform_id")
    ):
        codes.add("UNK_SOURCE_LINEAGE")

    deps = record.get("dependencies")
    active = []
    if not isinstance(deps, Mapping) or deps.get("complete") is not True or not isinstance(deps.get("items"), list):
        codes.add("UNK_DEPENDENCY_REGISTRY")
    else:
        for item in deps["items"]:
            if not isinstance(item, Mapping) or not _text(item.get("dependency_id")):
                codes.add("UNK_DEPENDENCY_REGISTRY")
            elif item.get("state") in {"ACTIVE", "OPEN"}:
                active.append(item.get("obligation_type"))
            elif item.get("state") != "CLOSED":
                codes.add("UNK_DEPENDENCY_REGISTRY")
    if hold_unknown:
        codes.add("UNK_HOLD_STATE")

    copies = record.get("copies")
    if not isinstance(copies, Mapping) or copies.get("complete") is not True or not isinstance(copies.get("items"), list):
        codes.add("UNK_COPY_LINEAGE")
    else:
        for item in copies["items"]:
            if not isinstance(item, Mapping) or not all(_text(item.get(k)) for k in ("copy_id", "version_id", "kind", "state")) or item.get("state") not in {"PRESENT", "RETIRED"}:
                codes.add("UNK_COPY_LINEAGE")

    process = record.get("process_state")
    if process not in {"ACTIVE", "INACTIVE"}:
        codes.add("UNK_PROCESS_STATE")
    rebuild = record.get("rebuildability")
    if not isinstance(rebuild, Mapping) or type(rebuild.get("required")) is not bool or (
        rebuild.get("required") and (rebuild.get("proven") is not True or not _text(rebuild.get("evidence_ref")))
    ) or rebuild.get("proven") not in {True, False}:
        codes.add("UNK_REBUILDABILITY_PROOF")
    material = record.get("material_decision_use")
    if material not in {"YES", "NO"}:
        codes.add("UNK_MATERIAL_USE_STATUS")

    if codes:
        return _result("BLOCKED_UNKNOWN", codes)

    retained = set()
    if process == "ACTIVE":
        retained.add("RET_PROCESS_ACTIVE")
    for obligation in active:
        retained.add(OBLIGATIONS.get(obligation, "RET_DEPENDENCY_ACTIVE"))
    if material == "YES":
        retained.add("RET_MATERIAL_DECISION_USE")
    if retained:
        return _result("RETAIN_UNTIL_OBLIGATIONS_CLOSE", retained)

    group = record.get("review_group")
    if group not in REVIEW or group != kind:
        return _result("BLOCKED_UNKNOWN", {"UNK_CLASSIFICATION"})
    if group == "NONCANONICAL_COPY":
        copy = record.get("copy_lineage")
        if (record.get("object_kind") != "COPY" or not isinstance(copy, Mapping)
            or copy.get("complete") is not True
            or not all(_text(copy.get(k)) for k in ("copy_id", "source_object_id", "source_version_id"))):
            return _result("BLOCKED_UNKNOWN", {"UNK_COPY_LINEAGE"})
        return _result("COPY_SPECIFIC_REVIEW", {"COPY_EXACT_VERSION_REVIEW", "COPY_SOURCE_CHAIN_VERIFIED"})

    required = {"REV_RATIFIED_NONCANONICAL_CLASS", "REV_DEPENDENCIES_CLOSED",
                "REV_HOLDS_CLEAR", "REV_LINEAGE_COMPLETE", "REV_PROCESS_CLOSED"}
    if rebuild["required"]:
        required.add("REV_REBUILDABILITY_PROVEN")
    if group == "T2_EPHEMERAL_INFERENCE_OUTPUT":
        if material != "NO":
            return _result("BLOCKED_UNKNOWN", {"UNK_MATERIAL_USE_STATUS"})
        required.add("REV_NON_MATERIAL_USE_PROVEN")
    return _result("REVIEWABLE_NONCANONICAL", required)
