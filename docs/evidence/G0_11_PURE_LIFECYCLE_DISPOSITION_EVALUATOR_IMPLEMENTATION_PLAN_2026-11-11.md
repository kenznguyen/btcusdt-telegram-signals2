# G0.11 — Pure Lifecycle Disposition Evaluator Implementation Plan

Date: 2026-11-11  
Status: **DOCUMENTARY IMPLEMENTATION PLAN — NOT IMPLEMENTED / NOT EXECUTED / NOT ACTIVE**

## 1. Purpose

G0.11 converts the G0.10 synthetic-only disposition contract into a bounded implementation plan while reconciling it with the repository's earlier lifecycle assurance work:

- Stage C.5–C.11: TEST-01–07 runner, adapter, isolation, independent oracle, deterministic concurrency, provenance and synthetic cleanup-containment contracts;
- Stage C.12: cross-contract static consistency review;
- Stage C.13: integrated logical schema/field and evidence-destination map;
- Stage C.14: 87-vector source-to-assertion applicability matrix;
- G0.9: VPS data lifecycle/storage governance;
- G0.10: five-disposition pure dry-run contract and 26 synthetic acceptance cases.

This report is a planning document only. It does not implement code, fixtures, tests, schemas, adapters, runner, oracle, CI workflow, storage interface, registry, scheduler, attestation, cleanup controller or executor.

## 2. Critical scope reconciliation

There are two related but distinct workstreams. They must not be conflated.

### Workstream A — G0.10 disposition evaluator

A pure function that receives already-constructed synthetic metadata records and returns one of five non-executable dispositions:

- `PROTECTED`
- `RETAIN_UNTIL_OBLIGATIONS_CLOSE`
- `REVIEWABLE_NONCANONICAL`
- `COPY_SPECIFIC_REVIEW`
- `BLOCKED_UNKNOWN`

It does not read paths, enumerate storage, access databases, resolve providers, inspect process handles, move files, delete objects or authorize an operation. This is the only evaluator contemplated by the G0.10/G0.11 narrow implementation path.

### Workstream B — Stage C lifecycle assurance harness

TEST-01–07 and the 87-vector catalogue address a much broader future assurance system: runner manifests, synthetic adapters, effective isolation, independent oracle, deterministic concurrency, lifecycle provenance and cleanup containment. These contracts describe future capabilities and prerequisites. They are not implemented merely because their contracts or traceability matrix exist.

G0.11 does not implement Workstream B and does not treat the G0.10 evaluator as closure of TEST-01–07, LDA-07 or any of the 87 lifecycle vectors.

## 3. Existing repository evidence and reuse

| Existing evidence | What it establishes | What it does not establish |
|---|---|---|
| Stage C.5 TEST-01 runner contract | Logical run manifest, deterministic selection, result and exit semantics | Runner implementation or execution |
| Stage C.6 TEST-02 synthetic adapter contract | Required adapter boundary and deny-by-default semantics | Any implemented adapter |
| Stage C.7 TEST-03 isolation contract | Required filesystem/network/identity isolation proof | Effective isolation |
| Stage C.8 TEST-04 oracle contract | Independent read-only oracle requirements | Independent oracle implementation |
| Stage C.9 TEST-05 concurrency contract | Deterministic schedules, barriers and causal traces | Executed deterministic schedules |
| Stage C.10 TEST-06 provenance contract | Lifecycle-specific provenance requirements | Complete cryptographic binding or verification |
| Stage C.11 TEST-07 containment contract | Exact synthetic namespace and containment requirements | Cleanup implementation or authorization |
| Stage C.12 review | Static consistency review and integration findings | Technical closure |
| Stage C.13 field map | Logical field/cardinality/relationship and destination identity map; C12-F01/F03 resolved at documentary level | Physical schema, canonicalization, provider, effective permissions or destination proof |
| Stage C.14 matrix | 87/87 source definitions and TEST-01–07 assertion mappings at design level | Executable test binding or lifecycle coverage |
| G0.10 | Five output dispositions and 26 synthetic acceptance specifications | Implemented evaluator or executed tests |

Stage C.13 exact path: `docs/evidence/p1-8/STAGE_C13_INTEGRATED_SCHEMA_FIELD_AND_EVIDENCE_DESTINATION_MAP_2026-11-10.md`, blob `c43c8bfbccaf698d6670f33fab66ee12d2072a7f`.

Stage C.14 exact path: `docs/evidence/p1-8/STAGE_C14_87_VECTOR_TEST01_07_APPLICABILITY_TRACEABILITY_MATRIX_2026-11-10.md`, blob `12bba6c475fc2ad8c4e2246e75034ede22d3bc20`.

G0.11 reuses these as documentary inputs. It does not duplicate their schemas or claim their technical gates are closed.

## 4. Proposed pure evaluator boundary

### 4.1 Functional interface

Logical interface only:

`evaluate_disposition(record, policy_profile) -> DispositionResult`

The evaluator must be a deterministic, side-effect-free transformation over supplied values. It must not accept a filesystem path, URI, database connection, network client, storage adapter, process handle, clock, secret, credential, shell command or executor object.

No input loader or storage discovery layer is included in this scope.

### 4.2 Input boundary

The caller supplies a fully materialized immutable synthetic record. Required logical groups are:

- exact synthetic object and version identity;
- data class and steward;
- governing policy identifier/version;
- source and copy lineage references;
- content digest and byte length;
- dependency and obligation states;
- hold state;
- process/writer/job state as pre-supplied synthetic facts;
- rebuildability evidence references where applicable;
- evidence revision.

The evaluator validates shape, identity uniqueness within the supplied record set, supported enumerations and cross-field consistency. It does not independently prove the truth of supplied facts. Missing or unverifiable facts produce a protective disposition.

### 4.3 Output boundary

The result contains only:

- input record identity;
- applied policy version;
- one of the five G0.10 dispositions;
- stable blocker/reason codes;
- references to supplied synthetic evidence;
- deterministic input digest reference (only after a canonicalization profile is separately approved);
- evaluator version;
- `mutation_performed=false`;
- `execution_authorized=false`.

The result must not contain executable paths, shell commands, SQL, provider locators, deletion manifests, authorization tokens or an action-ready target list.

### 4.4 Capability restrictions

The evaluator has no API for:
- listing or opening directories/files;
- reading/writing databases or object stores;
- HTTP/network access;
- archive, move, rename, truncate, overwrite or compression;
- delete, expiry, vacuum, compaction or provider lifecycle operations;
- process execution, scheduling or background work;
- creating approvals or promoting a disposition to authorization.

No destructive executor or cleanup-capable mock is part of the evaluator package.

## 5. Deterministic decision precedence

The implementation proposal must encode explicit precedence rather than permissive heuristics:

1. **Protected class/policy invariant** wins: return `PROTECTED`.
2. **Unknown, missing, contradictory, stale or unsupported required facts** return `BLOCKED_UNKNOWN`.
3. **Known open dependency, obligation, hold or active process/job** returns `RETAIN_UNTIL_OBLIGATIONS_CLOSE` or `PROTECTED` according to the controlling policy; it can never be reviewable.
4. **Individually identified copy** can return `COPY_SPECIFIC_REVIEW` only after exact copy lineage, holds, dependencies and recovery-chain evidence are complete.
5. **Ratified noncanonical review class** can return `REVIEWABLE_NONCANONICAL` only when every required evidence predicate is satisfied.
6. All other conditions fail closed.

The exact tie-break rules between `PROTECTED`, `RETAIN_UNTIL_OBLIGATIONS_CLOSE` and `BLOCKED_UNKNOWN` must be frozen in a versioned decision table before implementation. No inferred TTL, age, access time, consumer ACK, training completion, heartbeat loss, storage pressure or disk threshold can promote eligibility.

## 6. Mapping G0.10 acceptance cases to existing assurance contracts

| G0.10 case family | Existing Stage C evidence to reuse | Additional evaluator-specific assertion |
|---|---|---|
| Protected T0, ledgers, T3 | C6 adapter deny rules; C8 oracle; C14 NEG-T0 / NEG-T3 rows | Disposition always protective regardless of age/ACK |
| Unknown identity/class/policy | C5 manifest validation; C6 identity; C10 provenance | Unknown input cannot produce a reviewable disposition |
| Hash/manifest mismatch | C6 exact-version/integrity; C8 independent observation; C10 provenance | Supplied digest/size inconsistency blocks |
| Dependencies and holds | C6 registry/hold; C8 oracle; C14 applicable hold/registry rows | Any unresolved dependency/hold prevents reviewability |
| Copy lineage/recovery chain | C6 copy inventory; C8 oracle; C11 containment | Copy review is exact-object-only; no cascade |
| Process/writer/job active | C6 process/lease semantics; C9 race vectors; C14 T0 fencing rows | Active or unknown process state is never reviewable |
| Rebuildability | C6 source/transform lineage; C8 independent oracle; C10 provenance | Claim without exact reproducibility evidence blocks |
| Determinism/repeatability | C5 deterministic result; C9 schedules; C10 provenance | Identical logical input produces identical semantic result |
| Input immutability/no side effects | C7 isolation; C8 read-only observer; C11 containment | Evaluator cannot mutate supplied input and has no I/O capability |
| Storage pressure | G0.9 governance; G0.10 SYN-DRY-023 | Pressure is reporting-only and cannot change disposition |
| No implicit authorization | C5 runner boundary; C6 adapter capability; C11 containment | No output state or API can invoke an executor |

C14's 87 rows remain design-level mappings. This table does not claim any of those 87 vectors has been executed or covered by the proposed evaluator.

## 7. Proposed module and test layout (not approved file creation)

Names below are illustrative planning targets only. They do not assert existing paths and are not an implementation allowlist.

| Proposed unit | Responsibility | Must not contain |
|---|---|---|
| `lifecycle_disposition/types` | Immutable input/output value types and enums | Filesystem/storage/network types |
| `lifecycle_disposition/policy` | Versioned pure decision table | TTL scheduler or runtime config |
| `lifecycle_disposition/evaluator` | Deterministic precedence and validation | I/O, adapters, executor |
| `tests/lifecycle_disposition/` | Synthetic in-memory unit fixtures | Production database or mounted data |
| `tests/fixtures/lifecycle_dry_run/` | Optional committed synthetic fixtures, only after provenance/allowlist approval | Real candles, raw captures, ledgers, secrets, models |
| `build/test-artifacts/lifecycle-dry-run/` | Optional test report output, only after CI scope approval | Production evidence destination |

Prefer in-memory synthetic records for the first implementation. Do not create fixture files unless a later approval establishes their exact names, content provenance and allowlist.

## 8. Test strategy and acceptance criteria

The first evaluator test increment, if separately approved, should be pure unit tests with no runner, adapter, database, filesystem fixture loader, network, concurrency scheduler, oracle service or CI artifact publisher.

Minimum tests:
1. one positive synthetic noncanonical record satisfying every reviewability predicate;
2. T0 canonical, CORE_LEDGER, AI_LEDGER and protected T3 cases;
3. missing/unknown/duplicate identities and unsupported policy versions;
4. digest/size/lineage mismatch;
5. open, stale, contradictory and missing dependency/hold/copy/process facts;
6. incomplete rebuildability evidence;
7. exact-copy review versus broad source/copy cascade;
8. storage pressure cannot alter disposition;
9. consumer ACK, elapsed time and heartbeat loss cannot upgrade eligibility;
10. deterministic repeated evaluation and input immutability;
11. forbidden I/O/capability dependency is absent from the evaluator boundary;
12. all output values enforce `mutation_performed=false` and `execution_authorized=false`.

Acceptance requires all declared cases to pass, no skipped/xfail masking, a frozen policy decision table, independent review of expected outputs at the test-design level, and evidence bound to exact source SHA. Passing unit tests proves only the pure evaluator against synthetic inputs; it does not prove input truth, effective isolation, filesystem safety, deletion safety, TEST-01–07 closure or production readiness.

## 9. CI proposal — not dispatched

A future CI job may run only after separate approval of exact workflow path, trigger, permissions, commands, dependency installation, artifact output and network policy.

Initial proposed constraints:
- run on GitHub-hosted ephemeral runner with no production secrets;
- no deployment, environment approval, write token, cloud credential or external network dependency;
- read-only checkout permissions unless the approved test report requires a narrowly scoped artifact mechanism;
- run only the explicitly selected pure unit test module, not repository-wide lifecycle or destructive tests;
- no service containers, database, mounted volume, provider or VPS;
- do not dispatch existing workflows that include runtime probes, integration, provisioning, cleanup or unrelated test suites;
- preserve logs and exact test result; artifact publication remains a separate destination decision under C.13.

No workflow is selected or modified by G0.11.

## 10. Dependencies and unresolved decisions

| Item | Status | Required before implementation |
|---|---|---|
| G0.10 five-disposition contract | DOCUMENTED | Freeze tie-break table and field-level input semantics |
| C.13 logical field map | DOCUMENTED | Do not claim physical schema/canonicalization is frozen |
| C.14 87-vector mapping | DESIGN MAPPED | Preserve 87/87 NOT RUN |
| RET-01 B / RET-02 B policy | RATIFIED | No change inferred |
| RET-03–RET-10 | OPEN / NOT VERIFIED | No numeric TTL/retention/alert/freshness values |
| Synthetic fixture file allowlist | NOT APPROVED | Exact files/content provenance must be approved |
| Implementation paths/command | NOT APPROVED | Exact bounded code/test scope approval |
| CI workflow and permissions | NOT APPROVED | Exact workflow scope approval |
| TEST-01–07 | DOCUMENTED; technical gates open | Must not be represented as closed by this evaluator |
| TEST-08 | NOT GRANTED | Separate exact-scope owner authorization for the broader harness |
| Destructive operations | NOT AUTHORIZED | Separate bounded approval for each concrete operation |

G0.11 does not require choosing a serialization, digest/signature implementation, provider, evidence destination or numeric retention policy.

## 11. G0.11 verdict

- Reconciliation of G0.10 with Stage C.5–C.14: **PASS — documentary mapping**.
- Separation of pure disposition evaluator from lifecycle assurance harness: **PASS — scope clarity**.
- Pure evaluator interface/capability boundary: **CONDITIONAL PASS — design proposal**.
- Decision precedence and tie-break table: **OPEN — requires a frozen policy table before code**.
- Physical schema/canonicalization: **NOT ESTABLISHED**.
- Fixtures and test paths: **NOT APPROVED / NOT CREATED**.
- Implementation: **NOT IMPLEMENTED**.
- Tests: **NOT RUN**.
- GitHub Actions: **NOT DISPATCHED**; no run/artifact.
- TEST-01–07 technical closure: **NOT ESTABLISHED**.
- 87 lifecycle vectors: **0/87 executed; 87/87 NOT RUN**.
- TEST-08: **NOT GRANTED**.
- VPS/runtime/data cleanup/deletion: **NOT AUTHORIZED / NOT PERFORMED**.

## 12. Explicit non-actions and next gate

No source code, tests, fixtures, schemas, APIs, registries, adapters, runner, oracle, workflow, scheduler, service, permission, credential, database, storage, VPS, market data, model, ledger or runtime was changed. No tests, compile, dry-run, fault injection, workflow dispatch, live inventory, provider/runtime probe, archive, quarantine, cleanup, expiry, compaction, vacuum or deletion was performed.

Next bounded documentary increment: freeze the evaluator's field-level decision table and reason-code catalogue, resolving precedence for protected, retained and unknown states without inventing retention values. After that, request a separate exact-scope approval for the pure evaluator implementation and its in-memory synthetic unit tests. CI dispatch, broader TEST-01–07 harness implementation and any destructive capability remain separate gates.

T0 remains independent. Paper-only and `AI_EXECUTION_ENABLED=false` remain unchanged.
