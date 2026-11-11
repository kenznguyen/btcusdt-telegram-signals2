# G0.18 — Sensitivity Field Integration Plan for Pure Lifecycle Evaluator (2026-11-11)

Date: 2026-11-11 (Asia/Ho_Chi_Minh)  
Work type: documentation-only implementation plan  
Branch: `feature/t0-centralized-data-feeder-p1-20261101`  
Starting handoff blob: `1b3acea07bba2154dbf0fa14d68cb1418690c623`  
Current evaluator blob: `6f083a6b9b7107f3b6e3c7af3b32da34b5dafb5e`  
Current focused-test blob: `2ba03eb0deac67e1b82afb60ca24a6c15a2a56ce`  
Controlling owner policy: G0.17, blob `60263b93fead38206430557eefa830e94e319ba9`

## 1. Objective and bounded scope

Prepare a precise, reviewable plan to integrate the owner-ratified sensitivity policy into the existing pure lifecycle disposition evaluator and its in-memory synthetic unit tests, closing the remaining implementation portion of G0.15 R4.

The planned implementation is limited to:
- `pipeline/lifecycle_disposition.py`
- `pipeline/test_lifecycle_disposition.py`

No new module, schema, registry, API, adapter, fixture file, runner, oracle, workflow, scheduler, service, permission, credential, database, storage, VPS or runtime component is in scope. No CI dispatch is authorized by this plan.

## 2. Controlling policy and invariants

G0.17 owner-ratified:
- Ordered sensitivity labels: `PUBLIC < INTERNAL < CONFIDENTIAL < RESTRICTED`.
- Non-label classification states: `UNCLASSIFIED`, `CONFLICTED`, `PENDING_OWNER_DECISION`.
- Unknown, stale, contradictory or unauthenticated classification fails closed and receives protective handling as RESTRICTED pending resolution.
- Effective sensitivity is the most restrictive applicable class default, source/parent, embedded-content, policy/hold and recipient/export-context requirement.
- Copies, backups, replicas, caches, features, reports and exports inherit the highest sensitivity of their inputs; no automatic downgrade.
- Credentials, private keys, tokens, signing material and trust-root secrets are always RESTRICTED. Secret values must not enter ordinary evidence or CI artifacts.
- Sensitivity is separate from lifecycle disposition, retention eligibility and execution authority.

The five lifecycle dispositions and their precedence remain unchanged:
`PROTECTED`, `BLOCKED_UNKNOWN`, `RETAIN_UNTIL_OBLIGATIONS_CLOSE`, `COPY_SPECIFIC_REVIEW`, `REVIEWABLE_NONCANONICAL`.

Every evaluator result must continue to set `mutation_performed=false` and `execution_authorized=false`. A sensitivity label must never grant reviewability, retention-floor completion, archive/deletion approval or execution authority. RET-01 B / RET-02 B remain controlling; T0 remains protected and independent.

## 3. Proposed in-memory input contract

Add one required top-level mapping named `sensitivity` to each evaluator record. The implementation plan proposes these exact fields:

| Field | Type | Accepted values / rule |
|---|---|---|
| `state` | string | Exactly one of `CLASSIFIED`, `UNCLASSIFIED`, `CONFLICTED`, `PENDING_OWNER_DECISION` |
| `label` | string or null | Exactly one of `PUBLIC`, `INTERNAL`, `CONFIDENTIAL`, `RESTRICTED`; must be null unless state is `CLASSIFIED` |
| `evidence_ref` | non-empty string | Opaque synthetic evidence reference; no secret values or production identifiers |
| `evidence_revision` | non-empty string | Revision identifier for deterministic test input |

Missing mapping, wrong container/type, unknown state, label/state mismatch, missing evidence reference/revision or malformed values must fail closed. No fallback to PUBLIC or INTERNAL is permitted.

The pure evaluator must not read files, resolve references, inspect payload bytes, query registries, verify signatures, access a clock, or authenticate the asserted evidence. The input remains caller-supplied metadata. This plan does not claim to solve external fact authentication.

## 4. Class minimums and effective-label validation

Implement the exact G0.17 minimum mapping, without adding or weakening entries:

| `data_class` | Minimum label |
|---|---|
| `T0_CANONICAL` | `RESTRICTED` |
| `T0_LEASE_FENCING_RECOVERY` | `RESTRICTED` |
| `T1_RAW_OBSERVATION` | `CONFIDENTIAL` |
| `T1_SIDECAR_SESSION_INTEGRITY` | `RESTRICTED` |
| `T2_CANONICAL_INPUT_FEATURES_LABELS_DATASETS` | `CONFIDENTIAL` |
| `T2_MODEL_ARTIFACTS_EVALUATION_PROVENANCE` | `CONFIDENTIAL` |
| `T2_EPHEMERAL_INFERENCE_OUTPUT` | `CONFIDENTIAL` |
| `T3_CORE_LEDGER_AI_LEDGER_ACCOUNT_EQUITY_RISK` | `RESTRICTED` |
| `T3_SIGNALS_DECISIONS_PAPER_AUDIT` | `RESTRICTED` |
| `T4_DETERMINISTIC_CACHE_READ_MODEL` | `INTERNAL` |
| `GOVERNANCE_CUSTODY_TRUST_LIFECYCLE_EVIDENCE` | `RESTRICTED` |
| `SYNTHETIC_FIXTURE_CI_REPORT` | `INTERNAL`, only when wholly synthetic and secret-free |
| `NONCANONICAL_COPY_BACKUP_REPLICA_EXPORT` | Inherit source sensitivity; no lower default |
| Unknown/unmapped class | Fail closed; treat as RESTRICTED pending resolution |

Important compatibility issue: the current evaluator's `PROTECTED` and `REVIEW` class identifiers are narrower than G0.17's data-domain mapping. Implementation must not silently rename, merge or remap existing identifiers. Before coding, define an explicit, reviewed mapping from each existing identifier to its G0.17 domain default. If an existing class cannot be mapped unambiguously, it must remain fail-closed until an owner-approved mapping is recorded; do not invent a class equivalence.

For a classified object, the supplied effective `label` must be at least as restrictive as the applicable class minimum. If parent/source or context labels are supplied by the input contract in a later separately reviewed extension, effective sensitivity must be the maximum (most restrictive) of all applicable labels. G0.18 implementation should not pretend to discover absent parent/context labels.

## 5. Evaluator behavior

1. Validate sensitivity metadata before any review disposition can be returned.
2. Preserve existing positive protected-class and active binding-hold precedence. A protected result remains `PROTECTED` even if sensitivity metadata is unknown; append the applicable sensitivity unknown reason code.
3. For non-protected records, missing, malformed, unknown, stale-as-asserted, conflicted, pending or below-minimum sensitivity must produce `BLOCKED_UNKNOWN`.
4. Valid sensitivity metadata does not change existing dependency, hold, process, lineage, copy, rebuildability or material-use checks.
5. Sensitivity does not change a valid disposition into a less restrictive one and does not grant any new review group.
6. Keep deterministic sorted reason codes and immutable input behavior.
7. Preserve the exact output shape and fixed false mutation/authority flags.

Reason-code additions should be stable and narrow, for example `UNK_SENSITIVITY_METADATA`, `UNK_SENSITIVITY_STATE`, `UNK_SENSITIVITY_LABEL`, `UNK_SENSITIVITY_EVIDENCE`, and `UNK_SENSITIVITY_BELOW_CLASS_MINIMUM`. Final names must be frozen in the implementation diff and covered by tests; no reason code is itself an authorization.

## 6. Required in-memory synthetic test matrix

Extend the existing tests with deterministic wholly synthetic cases covering:
- Each four ordered labels and valid classified state.
- Every G0.17 class minimum, including unmapped/ambiguous class fail-closed behavior.
- Missing sensitivity mapping; wrong mapping type; missing/empty evidence reference or revision.
- Every non-label state with null label; non-label state incorrectly paired with a label.
- Unknown label/state, wrong value types and unhashable values.
- Below-minimum label rejection and higher-label acceptance.
- T0/protected class remains PROTECTED while reporting sensitivity unknowns.
- Active binding hold remains PROTECTED with sensitivity validation findings retained.
- Valid sensitivity does not bypass open dependency, active process, material-use, copy-lineage or rebuildability gates.
- Sensitivity does not alter five-disposition precedence or authorize mutation/execution.
- Input immutability and deterministic reason-code ordering.
- Synthetic credential/trust-secret markers are represented only as non-secret classification metadata; no actual secret fixtures or values.

Test data must remain in-memory literals. No filesystem fixtures, production IDs, real market data, credentials, provider/network/database/VPS access or external evidence resolution.

## 7. TDD and verification sequence for a separately approved implementation

If implementation is separately approved:
1. Add failing tests first for the required contract and precedence.
2. Implement the smallest pure validation helper and explicit class-minimum mapping.
3. Run `python -m unittest pipeline.test_lifecycle_disposition -v`.
4. Run `python -m py_compile pipeline/lifecycle_disposition.py pipeline/test_lifecycle_disposition.py`.
5. Review the diff for pure-function boundary, compatibility, no secret leakage, deterministic output and unchanged false authority flags.
6. Record exact source SHA, test output, commit and any separately approved workflow result in a new evidence report and handoff update.

This plan does not authorize any of these implementation or verification actions. Repository-wide tests, GitHub Actions dispatch, TEST-01–07 harness, external evidence authentication and runtime inventory remain separate gates.

## 8. Explicit non-actions and restrictions

No source/test changes, fixture creation, schema/registry/API/adapter changes, workflow edits or dispatch, runner/oracle, scheduler/service/permission/credential changes, database/storage/VPS access, market-data/model/ledger/runtime changes, inventory, file/secret scan, network/provider access, archive, quarantine, cleanup, expiry, compaction, vacuum or deletion.

No numeric retention, TTL, grace period, evidence-freshness window or review cadence is set. No destructive executor is proposed. T0 remains independent and protected; CORE_LEDGER and AI_LEDGER remain separate; paper-only and `AI_EXECUTION_ENABLED=false` remain unchanged.

## 9. Status

- G0.17 policy ratification: PASS (owner-ratified, documentary).
- G0.18 integration plan: PASS (documentation-only, pending GitHub readback).
- Existing evaluator sensitivity integration: NOT IMPLEMENTED.
- Implementation approval: NOT GRANTED by this plan.
- Tests for sensitivity integration: NOT RUN.
- GitHub Actions: NOT DISPATCHED; no run/artifact.
- Evidence authentication and external lineage verification: NOT ESTABLISHED.
- TEST-01–07: no status promotion; 0/87 executed remains.
- Runtime inventory/classification: NOT PERFORMED / NOT VERIFIED.
- Destructive authority: NOT GRANTED.

## 10. Next gate

Owner approval must explicitly bound implementation to `pipeline/lifecycle_disposition.py` and `pipeline/test_lifecycle_disposition.py`, the in-memory synthetic tests in §6, and the local commands in §7. Any expansion to schemas, registries, CI/workflows, external evidence authentication, TEST-01–07, runtime inventory or destructive operations requires a separate approval.
