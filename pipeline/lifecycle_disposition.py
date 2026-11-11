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
SENSITIVITY_ORDER = {
    "PUBLIC": 0,
    "INTERNAL": 1,
    "CONFIDENTIAL": 2,
    "RESTRICTED": 3,
}
# Explicit mapping only for identifiers already accepted by this evaluator.
# Values are the exact G0.17 semantic-domain minimums.
SENSITIVITY_MINIMUMS = {
    "T0_CANONICAL": "RESTRICTED",
    "CORE_LEDGER": "RESTRICTED",
    "AI_LEDGER": "RESTRICTED",
    "T3_PROTECTED_EVIDENCE": "RESTRICTED",
    "GOVERNANCE_EVIDENCE": "RESTRICTED",
    "T4_DETERMINISTIC_CACHE": "INTERNAL",
    "T2_EPHEMERAL_INFERENCE_OUTPUT": "CONFIDENTIAL",
    "T1_RAW_OBSERVATION": "CONFIDENTIAL",
}
SENSITIVITY_STATES = {
    "CLASSIFIED", "UNCLASSIFIED", "CONFLICTED", "PENDING_OWNER_DECISION",
}

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
    policy_id, policy_version = record.get("policy_id"), record.get("policy_version")
    if not isinstance(policy_id, str) or not isinstance(policy_version, str) or (policy_id, policy_version) not in POLICIES:
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



def _sensitivity_unknowns(record, kind, codes):
    sensitivity = record.get("sensitivity")
    if not isinstance(sensitivity, Mapping):
        codes.add("UNK_SENSITIVITY_METADATA")
        return

    state = sensitivity.get("state")
    label = sensitivity.get("label")
    if not isinstance(state, str) or state not in SENSITIVITY_STATES:
        codes.add("UNK_SENSITIVITY_STATE")
    elif state != "CLASSIFIED":
        codes.add("UNK_SENSITIVITY_STATE")
        if label is not None:
            codes.add("UNK_SENSITIVITY_LABEL")
    elif not isinstance(label, str) or label not in SENSITIVITY_ORDER:
        codes.add("UNK_SENSITIVITY_LABEL")

    if (not _text(sensitivity.get("evidence_ref"))
            or not _text(sensitivity.get("evidence_revision"))):
        codes.add("UNK_SENSITIVITY_EVIDENCE")

    if not isinstance(state, str) or state != "CLASSIFIED":
        return
    if not isinstance(label, str) or label not in SENSITIVITY_ORDER:
        return

    if kind == "NONCANONICAL_COPY":
        inherited = sensitivity.get("inherited_labels")
        if (not isinstance(inherited, list) or not inherited
                or any(not isinstance(item, str) or item not in SENSITIVITY_ORDER
                       for item in inherited)):
            codes.add("UNK_SENSITIVITY_INHERITANCE")
            return
        minimum_rank = max(SENSITIVITY_ORDER[item] for item in inherited)
        if SENSITIVITY_ORDER[label] < minimum_rank:
            codes.add("UNK_SENSITIVITY_BELOW_INHERITED")
        return

    minimum = SENSITIVITY_MINIMUMS.get(kind) if isinstance(kind, str) else None
    if minimum is None:
        codes.add("UNK_SENSITIVITY_CLASS_MAPPING")
    elif SENSITIVITY_ORDER[label] < SENSITIVITY_ORDER[minimum]:
        codes.add("UNK_SENSITIVITY_BELOW_CLASS_MINIMUM")


def evaluate_disposition(record):
    """Evaluate one supplied metadata record; never reads external state."""
    if not isinstance(record, Mapping):
        return _result("BLOCKED_UNKNOWN", {"UNK_OBJECT_IDENTITY"})
    codes = set()
    identity_ok = (record.get("identity_verified") is True and
                   all(_text(record.get(k)) for k in ("object_id", "version_id", "namespace")))
    kind = record.get("data_class")
    if identity_ok and isinstance(kind, str) and kind in PROTECTED:
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
            elif (not isinstance(item.get("status"), str)
                  or item.get("status") not in {"ACTIVE", "RELEASED", "CLOSED"}
                  or type(item.get("binding")) is not bool or not _text(item.get("hold_id"))):
                hold_unknown = True
    if binding_hold and identity_ok:
        codes.add("PROT_BINDING_HOLD_ACTIVE")
    protected = bool(codes)

    if not identity_ok:
        codes.add("UNK_OBJECT_IDENTITY")
    if not isinstance(kind, str) or (kind not in PROTECTED and kind not in REVIEW):
        codes.add("UNK_CLASSIFICATION")
    _unknowns(record, codes)
    _sensitivity_unknowns(record, kind, codes)

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
            elif not isinstance(item.get("state"), str):
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
            if not isinstance(item, Mapping):
                codes.add("UNK_COPY_LINEAGE")
                continue
            state = item.get("state")
            if (not all(_text(item.get(k)) for k in ("copy_id", "version_id", "kind"))
                or not isinstance(state, str) or state not in {"PRESENT", "RETIRED"}):
                codes.add("UNK_COPY_LINEAGE")

    process = record.get("process_state")
    if not isinstance(process, str) or process not in {"ACTIVE", "INACTIVE"}:
        codes.add("UNK_PROCESS_STATE")
    rebuild = record.get("rebuildability")
    mandatory_rebuild = isinstance(kind, str) and kind in {"T1_RAW_OBSERVATION", "T4_DETERMINISTIC_CACHE"}
    if (not isinstance(rebuild, Mapping)
        or type(rebuild.get("required")) is not bool
        or type(rebuild.get("proven")) is not bool
        or (mandatory_rebuild and rebuild.get("required") is not True)
        or ((rebuild.get("required") or mandatory_rebuild)
            and (rebuild.get("proven") is not True or not _text(rebuild.get("evidence_ref"))))):
        codes.add("UNK_REBUILDABILITY_PROOF")
    if kind == "T1_RAW_OBSERVATION" and record.get("producer_provenance_verified") is not True:
        codes.add("UNK_SOURCE_LINEAGE")
    material = record.get("material_decision_use")
    if not isinstance(material, str) or material not in {"YES", "NO"}:
        codes.add("UNK_MATERIAL_USE_STATUS")

    if protected:
        return _result("PROTECTED", codes)
    if codes:
        return _result("BLOCKED_UNKNOWN", codes)

    retained = set()
    if process == "ACTIVE":
        retained.add("RET_PROCESS_ACTIVE")
    for obligation in active:
        code = OBLIGATIONS.get(obligation, "RET_DEPENDENCY_ACTIVE") if isinstance(obligation, str) else "RET_DEPENDENCY_ACTIVE"
        retained.add(code)
    if material == "YES":
        retained.add("RET_MATERIAL_DECISION_USE")
    if retained:
        return _result("RETAIN_UNTIL_OBLIGATIONS_CLOSE", retained)

    group = record.get("review_group")
    if not isinstance(group, str) or group not in REVIEW or group != kind:
        return _result("BLOCKED_UNKNOWN", {"UNK_CLASSIFICATION"})
    if group == "NONCANONICAL_COPY":
        copy = record.get("copy_lineage")
        if (record.get("object_kind") != "COPY" or not isinstance(copy, Mapping)
            or copy.get("complete") is not True
            or not all(_text(copy.get(k)) for k in ("copy_id", "source_object_id", "source_version_id"))
            or copy.get("copy_id") != record.get("object_id")):
            return _result("BLOCKED_UNKNOWN", {"UNK_COPY_LINEAGE"})
        inventory = record.get("copies")
        exact_matches = []
        if isinstance(inventory, Mapping) and inventory.get("complete") is True and isinstance(inventory.get("items"), list):
            exact_matches = [item for item in inventory["items"]
                if isinstance(item, Mapping)
                and item.get("copy_id") == copy.get("copy_id")
                and item.get("version_id") == record.get("version_id")
                and item.get("kind") == "NONCANONICAL_COPY"
                and isinstance(item.get("state"), str)
                and item.get("state") in {"PRESENT", "RETIRED"}]
        if len(exact_matches) != 1:
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
