# G0.12 — Lifecycle Disposition Decision Table and Reason-Code Catalogue

Date: 2026-11-11  
Status: **DOCUMENTARY POLICY SPECIFICATION — NOT IMPLEMENTED / NOT EXECUTED / NOT ACTIVE**

## 1. Purpose and boundary

G0.12 freezes the logical precedence, field interpretation and stable reason-code vocabulary required before a pure G0.10 disposition evaluator can be implemented.

Inputs are already materialized synthetic facts. This document does not define a production inventory reader, physical schema, database, filesystem adapter, registry, scheduler, storage provider, approval service or executor. It does not grant eligibility or destructive authority.

Controlling inputs:
- G0.10 five-disposition dry-run contract and SYN-DRY-001–026;
- G0.11 pure evaluator boundary and separation from the broader TEST-01–07 assurance harness;
- RET-01 B / RET-02 B ratification and G0.9 storage governance;
- Stage C.13 logical field map and Stage C.14 87-vector design traceability.

T0 remains independent and protected. Paper-only remains mandatory; `AI_EXECUTION_ENABLED=false`.

## 2. Frozen disposition meanings

| Disposition | Exact meaning | What it does not mean |
|---|---|---|
| `PROTECTED` | A verified protected class or an active binding preservation hold prohibits ordinary lifecycle review | It does not assert every other field is valid; it does not authorize any operation |
| `RETAIN_UNTIL_OBLIGATIONS_CLOSE` | A known, attributable dependency or operational/reproducibility obligation remains open | It is not a time-based retention period and does not auto-release when a timer expires |
| `BLOCKED_UNKNOWN` | Required identity, classification, provenance, policy, integrity, lineage, dependency or process facts are absent, stale, contradictory or unverifiable | It is not evidence that the object is disposable or that no dependency exists |
| `COPY_SPECIFIC_REVIEW` | One exact, independently identified noncanonical copy has complete copy-specific evidence and may enter a separate review | It does not include its source, sibling copies, replicas or derived objects; it is not deletion approval |
| `REVIEWABLE_NONCANONICAL` | One exact noncanonical object is in an owner-ratified review group and every required eligibility predicate is positively established | It is not an instruction, authorization, candidate execution manifest or deletion approval |

No other output disposition is valid. In particular, the evaluator must never emit `ELIGIBLE_FOR_DELETION`, `AUTHORIZED`, `ARCHIVED`, `DELETED`, `EXECUTING` or equivalent action states.

## 3. Deterministic precedence and tie-break rules

The evaluator applies the following ordered rules to one exact object/version. The first matching rule determines the disposition. It must not use majority voting, risk scoring, recency heuristics or permissive fallback.

| Priority | Condition | Result | Tie-break rationale |
|---:|---|---|---|
| 1 | Exact identity and positive evidence establish a protected class: T0 canonical; CORE_LEDGER; AI_LEDGER; protected T3 reconstruction/reconciliation/audit evidence; governance approvals/history/tombstones | `PROTECTED` | A known protection invariant cannot be weakened by unrelated missing metadata or a completed consumer job |
| 2 | Exact identity and positive evidence establish an active binding legal, security, incident or owner-imposed preservation hold | `PROTECTED` | Binding preservation hold takes precedence over ordinary operational dependencies |
| 3 | No verified protected fact, but any required identity/classification/steward/policy/version/integrity/lineage/registry/copy/process fact is missing, stale, contradictory, unsupported or unverifiable | `BLOCKED_UNKNOWN` | Unknown is not absence and cannot be treated as a release |
| 4 | Required facts are known, but one or more exact consumer dependencies, replay/recovery, audit, model/research, validation, correction/reprocessing or other declared obligations remain open | `RETAIN_UNTIL_OBLIGATIONS_CLOSE` | A known open obligation is distinguishable from unknown evidence |
| 5 | Exact copy identity and complete copy lineage, holds, dependencies, recovery chain, integrity and policy evidence are verified; copy is independently classified as noncanonical and in a ratified review group | `COPY_SPECIFIC_REVIEW` | Copy review is narrower than source or dataset-family review |
| 6 | Exact object is in a ratified noncanonical review group; all required evidence is complete; no protected invariant, hold, unknown fact or open obligation remains; rebuildability/non-material-use predicates are proven where required | `REVIEWABLE_NONCANONICAL` | Reviewability is the least permissive positive outcome and still grants no action authority |
| 7 | No rule above conclusively applies | `BLOCKED_UNKNOWN` | Default-deny |

### 3.1 Protected versus unknown

- If a trusted, exact object record positively identifies a protected class, return `PROTECTED` even if unrelated metadata is missing. Missing fields must still be included as reason codes.
- If object identity itself is ambiguous and there is no trustworthy exact link to a protected object, return `BLOCKED_UNKNOWN`.
- If conflicting class claims include a positively evidenced protected classification, choose `PROTECTED`; record the conflicting classification reason as well.
- If classification is merely unknown or conflicting without positive protected evidence, choose `BLOCKED_UNKNOWN`.
- A protected disposition is a conservative classification, not a claim that the full record is valid.

### 3.2 Protected hold versus ordinary obligation

- A verified binding legal/security/incident preservation hold maps to `PROTECTED`.
- A known operational dependency, replay/recovery requirement, training/evaluation reproducibility obligation, validation/reprocessing obligation, or unresolved consumer dependency maps to `RETAIN_UNTIL_OBLIGATIONS_CLOSE`.
- A hold whose existence, scope, owner or status cannot be verified maps to `BLOCKED_UNKNOWN`, unless another verified protected rule already applies.
- No expiry timestamp automatically releases a hold. Release requires the authorized hold owner/governance process defined outside this evaluator.

### 3.3 Known obligation versus unknown registry

- Complete registry with an active dependency: `RETAIN_UNTIL_OBLIGATIONS_CLOSE`.
- Missing, stale, inaccessible, partial or contradictory registry: `BLOCKED_UNKNOWN`.
- Complete registry showing no dependencies is necessary but not sufficient for reviewability; holds, lineage, copies, process state and policy predicates must also be complete.
- Consumer ACK, successful job, elapsed time, missed heartbeat or absence of recent reads never substitutes for a dependency release or a complete registry.

### 3.4 Copy-specific review versus general review

- An exact copy may return `COPY_SPECIFIC_REVIEW` only when its immutable identity and complete lineage are known and the copy itself is independently in a ratified review group.
- Any unknown source, replica, backup, export, recovery-chain member, shared storage boundary or sibling relationship blocks the copy result as `BLOCKED_UNKNOWN`.
- A known open dependency/hold on the copy produces `PROTECTED` or `RETAIN_UNTIL_OBLIGATIONS_CLOSE` under the precedence above.
- No copy disposition propagates to the source or other copies.

### 3.5 Reviewable noncanonical

Only these four owner-ratified groups may be considered, and only per exact object/version:
1. T4 deterministic caches, read models and materializations, after exact rebuildability and dependency closure are proven.
2. T2 ephemeral inference outputs, after proving they did not underpin material decisions, claims, signals, risk decisions or retained evidence.
3. T1 raw observations, only after exact dependent outputs are reproducible from retained authoritative inputs and all obligations close. Current T1 evidence remains blocked; this rule does not change its status.
4. Individually identified noncanonical copies, subject to the separate copy-specific rule.

No other class is implicitly admitted. A directory or filename containing “cache”, “scratch”, “temporary”, “old” or “log” is not classification evidence.

## 4. Field-level input semantics

The evaluator consumes an immutable, already-materialized record. It does not fetch or verify external facts.

| Logical field group | Accepted semantic values | Missing/invalid treatment |
|---|---|---|
| Object identity | Exact synthetic object ID + immutable version ID + namespace/run binding | Ambiguous or duplicate identity: `BLOCKED_UNKNOWN`; if trusted identity proves protected class, retain `PROTECTED` with blocker |
| Classification | One supported functional class plus sensitivity label and policy reference | Unknown/conflicting: `BLOCKED_UNKNOWN`; positive protected evidence follows §3.1 |
| Steward/owner | One accountable, attributable synthetic owner | Missing/conflicting/unverifiable: `BLOCKED_UNKNOWN` |
| Policy | Exact supported policy ID and version; no mutable alias | Missing/unsupported/conflicting: `BLOCKED_UNKNOWN` |
| Integrity | Digest algorithm identifier, digest value and byte length; internally consistent | Missing/mismatch/unsupported encoding: `BLOCKED_UNKNOWN` |
| Source lineage | Exact source object/version and transformation references where required | Missing or inconsistent: `BLOCKED_UNKNOWN` |
| Dependencies | Complete exact-version consumer inventory and explicit state for each | Unknown/incomplete: `BLOCKED_UNKNOWN`; known active obligation: `RETAIN_UNTIL_OBLIGATIONS_CLOSE` |
| Holds | Complete scoped hold records, owner and status | Verified binding hold: `PROTECTED`; unknown/conflicting hold state: `BLOCKED_UNKNOWN` |
| Copies | Complete exact copy/replica/backup/export/derived lineage where applicable | Unknown/incomplete: `BLOCKED_UNKNOWN` |
| Process state | Explicitly observed synthetic state: inactive/closed, or active | Active known writer/job: `RETAIN_UNTIL_OBLIGATIONS_CLOSE`; unknown/stale process state: `BLOCKED_UNKNOWN` |
| Rebuildability | Exact retained input versions, transform/code/config versions and integrity-equivalence evidence | Required but absent/insufficient: `BLOCKED_UNKNOWN` |
| Material-decision use | Explicit evidence that T2 inference did not underpin a material decision/claim/evidence | Missing or ambiguous: `BLOCKED_UNKNOWN`; proven material use with open obligation: `RETAIN_UNTIL_OBLIGATIONS_CLOSE` |
| Evidence revision | Stable revision binding all supplied facts | Missing/mismatched: `BLOCKED_UNKNOWN` |

No wall-clock freshness interval is defined here. “Stale” means the record is explicitly marked stale by its supplied synthetic validity profile or fails an approved version/revision consistency check. Numeric freshness windows remain unapproved.

## 5. Stable reason-code catalogue

Reason codes are deterministic, non-secret, stable identifiers. A result may contain multiple codes. Codes are sorted lexicographically in the serialized semantic result so input order cannot change output. Codes explain the selected disposition; they do not grant authority.

| Code | Meaning | Normally associated disposition |
|---|---|---|
| `PROT_CLASS_T0_CANONICAL` | Exact object is T0 canonical data | PROTECTED |
| `PROT_CLASS_CORE_LEDGER` | Exact object belongs to CORE_LEDGER | PROTECTED |
| `PROT_CLASS_AI_LEDGER` | Exact object belongs to AI_LEDGER | PROTECTED |
| `PROT_CLASS_T3_EVIDENCE` | Exact object is protected T3 reconstruction/reconciliation/audit evidence | PROTECTED |
| `PROT_CLASS_GOVERNANCE_EVIDENCE` | Approval, policy history, tombstone or governance evidence | PROTECTED |
| `PROT_BINDING_HOLD_ACTIVE` | Verified binding preservation hold is active | PROTECTED |
| `UNK_OBJECT_IDENTITY` | Object/version identity missing, duplicate or ambiguous | BLOCKED_UNKNOWN |
| `UNK_CLASSIFICATION` | Classification missing, unsupported or conflicting without positive protected proof | BLOCKED_UNKNOWN |
| `UNK_STEWARD_OWNER` | Steward/owner missing or conflicting | BLOCKED_UNKNOWN |
| `UNK_POLICY_REFERENCE` | Policy ID/version missing, unsupported or conflicting | BLOCKED_UNKNOWN |
| `UNK_INTEGRITY_METADATA` | Digest/byte length absent or invalid | BLOCKED_UNKNOWN |
| `UNK_INTEGRITY_MISMATCH` | Supplied digest, size or manifest facts conflict | BLOCKED_UNKNOWN |
| `UNK_SOURCE_LINEAGE` | Required source/version/transform lineage incomplete | BLOCKED_UNKNOWN |
| `UNK_DEPENDENCY_REGISTRY` | Dependency inventory incomplete, stale or unavailable | BLOCKED_UNKNOWN |
| `UNK_HOLD_STATE` | Hold state/scope/owner cannot be verified | BLOCKED_UNKNOWN |
| `UNK_COPY_LINEAGE` | Copy/replica/backup/export chain incomplete | BLOCKED_UNKNOWN |
| `UNK_PROCESS_STATE` | Writer/job/lock/process state unknown or stale | BLOCKED_UNKNOWN |
| `UNK_REBUILDABILITY_PROOF` | Required deterministic rebuild proof absent/incomplete | BLOCKED_UNKNOWN |
| `UNK_MATERIAL_USE_STATUS` | Required proof of non-use in material decisions is absent/ambiguous | BLOCKED_UNKNOWN |
| `UNK_EVIDENCE_REVISION` | Evidence revision or cross-record binding inconsistent | BLOCKED_UNKNOWN |
| `UNK_UNSUPPORTED_VALUE` | Unsupported enum/value/schema version | BLOCKED_UNKNOWN |
| `RET_DEPENDENCY_ACTIVE` | Exact consumer dependency remains active | RETAIN_UNTIL_OBLIGATIONS_CLOSE |
| `RET_REPLAY_RECOVERY_OPEN` | Replay, recovery or restoration obligation remains open | RETAIN_UNTIL_OBLIGATIONS_CLOSE |
| `RET_MODEL_REPRODUCTION_OPEN` | Training/evaluation/model explanation obligation remains open | RETAIN_UNTIL_OBLIGATIONS_CLOSE |
| `RET_VALIDATION_REPROCESS_OPEN` | Validation, correction or reprocessing obligation remains open | RETAIN_UNTIL_OBLIGATIONS_CLOSE |
| `RET_PROCESS_ACTIVE` | Known writer/job/process remains active | RETAIN_UNTIL_OBLIGATIONS_CLOSE |
| `RET_MATERIAL_DECISION_USE` | T2 inference output underpins a material decision/claim/evidence obligation | RETAIN_UNTIL_OBLIGATIONS_CLOSE |
| `COPY_EXACT_VERSION_REVIEW` | Exact noncanonical copy satisfies copy-specific review predicates | COPY_SPECIFIC_REVIEW |
| `COPY_SOURCE_CHAIN_VERIFIED` | Copy source and recovery lineage are complete | COPY_SPECIFIC_REVIEW |
| `REV_RATIFIED_NONCANONICAL_CLASS` | Exact object belongs to one of four ratified review groups | REVIEWABLE_NONCANONICAL |
| `REV_DEPENDENCIES_CLOSED` | Complete dependency evidence shows no open dependency | REVIEWABLE_NONCANONICAL |
| `REV_HOLDS_CLEAR` | Complete evidence shows no active hold | REVIEWABLE_NONCANONICAL |
| `REV_LINEAGE_COMPLETE` | Required lineage and copy inventory are complete | REVIEWABLE_NONCANONICAL |
| `REV_REBUILDABILITY_PROVEN` | Required exact rebuildability proof is complete | REVIEWABLE_NONCANONICAL |
| `REV_NON_MATERIAL_USE_PROVEN` | Required non-material-use proof is complete | REVIEWABLE_NONCANONICAL |
| `REV_PROCESS_CLOSED` | Required process/writer state is verified closed | REVIEWABLE_NONCANONICAL |
| `INFO_STORAGE_PRESSURE_IGNORED` | Storage-pressure input was ignored for disposition | Any; informational only |
| `INFO_CONSUMER_ACK_NONAUTHORITATIVE` | ACK was not treated as eligibility or authorization | Any; informational only |
| `INFO_HEARTBEAT_NONAUTHORITATIVE` | Missing heartbeat was not treated as release evidence | Any; informational only |

### 5.1 Reason-code validity

- Every disposition must include at least one reason code.
- `PROTECTED` must include at least one `PROT_*` code.
- `BLOCKED_UNKNOWN` must include at least one `UNK_*` code unless a higher-precedence verified protected rule selected PROTECTED.
- `RETAIN_UNTIL_OBLIGATIONS_CLOSE` must include at least one `RET_*` code.
- `COPY_SPECIFIC_REVIEW` must include `COPY_EXACT_VERSION_REVIEW` and `COPY_SOURCE_CHAIN_VERIFIED`.
- `REVIEWABLE_NONCANONICAL` must include `REV_RATIFIED_NONCANONICAL_CLASS`, `REV_DEPENDENCIES_CLOSED`, `REV_HOLDS_CLEAR`, `REV_LINEAGE_COMPLETE`, and every applicable rebuildability/non-material-use/process proof code.
- Informational codes never satisfy a required eligibility predicate.
- A reason code cannot be supplied by an untrusted record as proof. The evaluator derives codes from validated fields and rules.

## 6. Determinism and output invariants

For the same evaluator version, policy version and semantically identical input facts:
- disposition and reason-code set are identical;
- reason codes are emitted in canonical sorted order;
- input record ordering does not affect result;
- no current wall-clock time, filesystem metadata, environment variable, random seed or external state affects the decision;
- supplied input is not mutated;
- output contains `mutation_performed=false` and `execution_authorized=false`;
- no command, path, SQL, provider locator, deletion manifest or executor payload is emitted.

If canonical byte encoding or digest algorithm is not yet frozen, G0.12 only specifies semantic determinism. It does not authorize inventing or hardcoding a physical canonicalization/digest standard.

## 7. Mapping to the 26 G0.10 synthetic cases

| G0.10 cases | Required decision-table result / reason coverage |
|---|---|
| SYN-DRY-001 | REVIEWABLE_NONCANONICAL with complete REV_* predicate codes |
| SYN-DRY-002 | PROTECTED + PROT_CLASS_T0_CANONICAL |
| SYN-DRY-003 | PROTECTED + CORE_LEDGER or AI_LEDGER class code |
| SYN-DRY-004 | PROTECTED for protected T3 evidence, otherwise RETAIN for known open reconstruction obligation |
| SYN-DRY-005 | BLOCKED_UNKNOWN + UNK_CLASSIFICATION / UNK_STEWARD_OWNER |
| SYN-DRY-006 | BLOCKED_UNKNOWN + UNK_INTEGRITY_METADATA / UNK_INTEGRITY_MISMATCH |
| SYN-DRY-007 | BLOCKED_UNKNOWN + UNK_DEPENDENCY_REGISTRY |
| SYN-DRY-008 | RETAIN + RET_DEPENDENCY_ACTIVE |
| SYN-DRY-009 | PROTECTED for verified binding hold; BLOCKED_UNKNOWN for unverifiable hold |
| SYN-DRY-010 | BLOCKED_UNKNOWN + UNK_COPY_LINEAGE |
| SYN-DRY-011 | RETAIN for known active writer/job; BLOCKED_UNKNOWN for unknown process state |
| SYN-DRY-012 | BLOCKED_UNKNOWN + UNK_REBUILDABILITY_PROOF |
| SYN-DRY-013 | Current T1 evidence remains blocked; synthetic known open obligation RETAIN, unknown producer/lineage facts BLOCKED_UNKNOWN |
| SYN-DRY-014 | RETAIN for proven material use; BLOCKED_UNKNOWN if material-use status is unknown |
| SYN-DRY-015 | COPY_SPECIFIC_REVIEW only with exact copy and complete evidence |
| SYN-DRY-016 | BLOCKED_UNKNOWN + UNK_POLICY_REFERENCE |
| SYN-DRY-017, 025 | Identical semantic result independent of repeat/order |
| SYN-DRY-018, 020, 021 | Input immutability and no mutation capability; no disposition can authorize an action |
| SYN-DRY-019, 026 | Reject invalid test input before evaluation; no path read or secret ingestion |
| SYN-DRY-022 | Test/report sink failure is harness failure, not a permissive evaluator result |
| SYN-DRY-023 | Storage pressure is informational only; no disposition change |
| SYN-DRY-024 | ACK/heartbeat are non-authoritative; no eligibility upgrade |

The 26 cases remain specifications until implementation and separately approved tests exist.

## 8. Relationship to Stage C.5–C.14 and lifecycle vectors

- C.13 remains a logical field/relationship map; no physical schema or canonicalization is selected here.
- C.14 remains a design-level mapping of 87 source vectors; 87/87 remain NOT RUN.
- The evaluator reason codes provide a vocabulary for G0.10 disposition outcomes; they do not replace TEST-01–07 assertion IDs or prove their coverage.
- TEST-01–07 implementation/technical closure remains NOT ESTABLISHED.
- TEST-08 remains NOT GRANTED.
- G0.12 does not create or approve fixtures, runner, adapters, oracle, isolation harness, evidence publisher, CI workflow or cleanup executor.

## 9. Explicit policy non-decisions

This decision table does not set:
- numeric TTL, retention floor, grace period, review cadence or freshness interval;
- storage-pressure threshold or automatic cleanup trigger;
- archive/quarantine duration;
- digest/signature algorithm or canonical serialization;
- physical schema, registry, evidence destination or provider;
- authorization lifetime or destructive-operation scope.

The former suggested 24-hour cache, 7-day scratch, 14–30-day logs and 80% pressure threshold remain unapproved. T1 raw data remains blocked by current evidence. T0, ledgers, protected T3 and governance evidence remain protected.

## 10. G0.12 verdict and next gate

- Five disposition semantics: **PASS — documentary specification**.
- Ordered tie-break precedence: **PASS — documentary specification**.
- Protected/unknown/retain tie-break: **PASS — conservative rules frozen**.
- Copy-specific and general noncanonical review boundary: **PASS — documentary specification**.
- Stable reason-code catalogue: **PASS — documentary specification**.
- Field semantics and G0.10 case mapping: **PASS — documentary specification**.
- Physical schema/canonicalization: **NOT ESTABLISHED**.
- Implementation paths and fixture allowlist: **NOT APPROVED**.
- Pure evaluator implementation: **NOT IMPLEMENTED**.
- Tests: **NOT RUN**.
- GitHub Actions: **NOT DISPATCHED**; no run/artifact.
- TEST-01–07 technical closure: **NOT ESTABLISHED**.
- Lifecycle vectors: **0/87 executed; 87/87 NOT RUN**.
- TEST-08: **NOT GRANTED**.
- Cleanup/archive/expiry/compaction/vacuum/deletion: **NOT AUTHORIZED / NOT PERFORMED**.

No source code, test, fixture, schema, API, registry, adapter, runner, oracle, workflow, scheduler, permission, credential, database, storage, VPS, market data, model, ledger or runtime was changed. No tests, compile, dry-run, fault injection, workflow dispatch, inventory, provider/runtime probe or destructive operation was performed.

Next gate: request a separate bounded approval for pure evaluator implementation and in-memory synthetic unit tests, specifying exact code/test paths and command. CI workflow dispatch, broader TEST-01–07 harness and every destructive operation remain separate approvals.

T0 remains independent. Paper-only and `AI_EXECUTION_ENABLED=false` remain unchanged.
