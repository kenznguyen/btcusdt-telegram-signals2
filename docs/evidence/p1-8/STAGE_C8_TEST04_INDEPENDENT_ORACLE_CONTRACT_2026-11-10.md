# Stage C.8 — TEST-04 Independent Oracle Contract

Date: 2026-11-10
Repository: kenznguyen/btcusdt-telegram-signals2
Branch: feature/t0-centralized-data-feeder-p1-20261101
Work type: documentation-only contract; TEST-04 only.
Predecessors: Stage C.4 prerequisite plan; C.5 TEST-01 runner; C.6 TEST-02 adapters; C.7 TEST-03 isolation.

## 1. Purpose and authority

Specify an independent oracle that evaluates synthetic lifecycle outcomes without trusting executor self-reports. It compares an immutable expected-state specification, frozen before execution, with independently collected actual-state observations and emits deterministic, evidence-backed verdicts.

This is a design contract, not an implementation or proof that any existing oracle is independent. Stage C approval authorizes this documentary work only. It does not authorize code/schema/adapter/runner/workflow changes, tests, compilation, dry-run, fault injection, Actions dispatch, secrets or permission access, runtime/VPS/database/provider/network probes, provisioning or data mutation. TEST-08 remains a separate exact-scope owner authorization gate before execution.

Option C remains active. No deletion, archive, cleanup, expiry, compaction, vacuum, backup/replica removal, export mutation or irreversible transition. Protected assets: T0 canonical data and recovery copies; CORE_LEDGER; AI_LEDGER; required T3 reconstruction/audit evidence; governance history/evidence while needed; unknown, unclassified or incompletely inventoried objects.

## 2. Independence definition and threat model

An oracle is independent only if the executor cannot control, alter, suppress, bias or forge: (a) expected-state specification; (b) oracle implementation and policy; (c) observation channel and raw observations; (d) verdict calculation; or (e) final evidence and provenance. Independence depends on effective principals, trust boundaries, data flow and permissions—not module names or self-attestation.

Threats include executor self-asserted PASS; expected-state mutation; shared writable storage; forged adapter responses; observer substitution or omission; stale/replayed evidence; event reordering; incomplete pagination; clock manipulation; configuration drift; artifact substitution; shared credentials; compromised runner; and circular verification where expected state is derived from executor output.

Explicit trust assumptions must identify controller, immutable specification source, observer, evaluator, runtime substrate, cryptographic primitives and evidence destination. No claim is made against compromise of host kernel, GitHub control plane, hypervisor, provider or hardware root of trust.

## 3. Roles and separation of duties

| Role | Responsibility | Prohibited capability |
|---|---|---|
| Owner/approver | Approves lifecycle semantics and exact run scope | Silent mutation of frozen run evidence |
| Specification authority | Publishes immutable expected-state package | Derive expectations from executor output |
| Run controller | Binds manifest, source, fixtures, namespace and oracle version | Change expected state after executor starts |
| Lifecycle executor | Performs selected synthetic operations | Write specification, observations, verdict or protected evidence |
| Independent observer | Reads actual synthetic state and events | Mutate lifecycle resources or trust executor summary as ground truth |
| Oracle evaluator | Compares frozen expectations and observations | Change specification, suppress observations or self-assign PASS |
| Evidence publisher | Appends run evidence to approved destination | Change verdict or expose write credentials to executor |

Roles may be separate services/processes, but distinct effective identities and non-overlapping write capabilities must be evidenced. Shared mutable state or principal means independence is NOT ESTABLISHED unless a specific independently verified control proves separation.

## 4. Frozen expected-state package

Expected state is authored and approved before execution, bound immutably to the run manifest, and never derived from executor observations. The package contains:

- Immutable spec ID/version, canonical serialization and complete package digest.
- Selected lifecycle vector IDs and one-to-one vector/case/assertion mapping.
- Preconditions, exact synthetic namespace/resource identities and ordered permitted transitions.
- Expected object bytes or canonical content digest; immutable object/version identity; metadata fields and revision.
- Expected copy inventory and lineage; hold/authorization state; checkpoint, manifest, cursor and watermark semantics.
- Expected audit/event types, required fields, sequence/causal relationships and append-only invariants.
- Protected-root invariants and explicit absence assertions for forbidden objects, copies, transitions and side effects.
- Comparison/canonicalization policy, permitted nondeterministic fields and explicit tolerances (default: none).
- Stop conditions, expected error classes, author/approver identity and approval evidence.

Unknown fields, duplicate vector IDs, missing expectations, ambiguous identities, mutable references, unapproved tolerances or digest mismatch reject the package before execution. No wildcard expectation may silently accept unknown objects/events. Specification is read-only to executor, observer and publisher. Corrections require a new version and new run binding; never overwrite the version used by an existing run.

## 5. Independent observation contract

Observer obtains actual state through read-only interfaces separate from executor write capabilities. An observation plan is frozen before execution and identifies exact resources, versions, checkpoints and completeness criteria.

Observations cover, as applicable:
1. Object existence, immutable identity/version, byte length and content digest.
2. Metadata state/revision, hold and authorization attributes.
3. Copy inventory and source-to-copy lineage.
4. Checkpoint, manifest, watermark and recovery-relevant state.
5. Append-only event/audit sequence, event identity, causal order and required provenance.
6. Protected-root identity, reachability and before/after integrity observations.
7. Explicit absence of forbidden objects, copies, transitions or side effects.
8. Operation response/error evidence collected independently of executor summary.

Observer distinguishes observed absence from failed read; empty result from incomplete pagination; immutable identity from mutable path/name; exact version from latest alias; no event from event-stream gap; and fresh observation from cache/stale response.

Each observation binds run ID, namespace ID, vector ID, observation ID, target identity/version, source/interface identity, logical checkpoint or time, sequence/cursor, result classification, canonical payload digest, completeness marker and provenance. No secret values. Incomplete, stale, mis-scoped or non-independent observation is INDETERMINATE, never PASS.

## 6. Read-only capabilities and scope

Oracle and observer receive read-only capabilities limited to the exact synthetic run and enumerated immutable object versions. They have no create/update/overwrite/delete/unlink/truncate/copy/restore, retention/hold/expiry change, compaction, vacuum or cleanup capability. They cannot write executor workspace, expected-state package, runner configuration or lifecycle adapters; access production credentials, canonical T0 stores, trading ledgers, provider accounts or real backups/replicas; discover backends; use default credential chains; or accept arbitrary paths/accounts/projects/buckets/databases/hosts supplied by executor.

All reads bind exact run/namespace and immutable target versions. Read errors, scope mismatch, ambiguous authorization and unknown resource type fail closed. Observer may write only its own isolated observation output; evaluator may append only a new verdict record. Neither mutates lifecycle resources or specification. These are future requirements, not claims about current permissions.

## 7. Deterministic comparison and verdict semantics

Evaluator compares frozen expected state with complete independent observations. Executor exit code, logs, summary or claimed PASS are never sufficient.

**PASS** only if specification is approved, immutable and run-bound; all required observations are complete, fresh, scoped and independent; all positive and negative assertions match; protected-root invariants are confirmed; no unknown object/event/transition/gap/duplicate/side effect exists; and evaluator/evidence provenance verifies.

**FAIL** when complete trustworthy observations establish a violation of an explicit expected or forbidden condition. Identify exact assertion and supporting observations. Do not downgrade an adverse verified result to INDETERMINATE.

**INDETERMINATE** when correctness cannot be established: incomplete/stale observations, unavailable source, pagination gap, ambiguous identity, missing provenance, digest mismatch, oracle disagreement, observer independence failure, unexpected configuration or unresolved event ordering.

**BLOCKED** means prerequisites/safety gates prevent execution or evaluation. **NOT RUN** means no execution was performed. Neither is a successful vector verdict. Unknown verdict values or partial result objects are rejected.

Run aggregation is deterministic: FAIL if any required vector FAIL; else INDETERMINATE if any required vector is INDETERMINATE or evidence incomplete; PASS only if every selected vector PASS and every run-level gate passes; BLOCKED if prohibited before a valid run; NOT RUN if no run was attempted. A blocked/not-run run must never appear as PASS with zero failures.

## 8. Determinism, replay and reproducibility

Reproducible evidence bundle binds exact source commit; runner/toolchain identity; specification bytes/digest and approval; run manifest and vector list; fixture/resource identity digests; adapter contract/version; observation plan and raw observations; evaluator source/config digest; canonicalization/comparison policy; event sequence and integrity metadata.

Canonical serialization defines key ordering, numeric representation, timestamp/timezone handling, byte encoding, null-versus-absent distinction and collection ordering. No implicit locale, timezone, floating tolerance, current-time default or unordered semantics influence verdicts.

Replay consumes preserved evidence only. It must not re-execute lifecycle operations, refresh/mutate resources or contact external systems. Same bundle plus same evaluator version yields same verdict. A changed evaluator/policy creates a linked new evaluation record; original evidence is never overwritten.

## 9. Evidence integrity and provenance

Expected package, observation and verdict are content-addressed and explicitly linked. Run manifest binds run/namespace/vector IDs; source/workflow/job/runner identity if applicable; spec digest/approval; observer/evaluator identity and version; observation IDs and cursor/sequence ranges; completeness; assertion-level verdicts; run status/abort reason; creation sequence/time; and prior evidence-chain reference.

Evidence is append-only from executor/evaluator perspective. Corrections are new records with explicit supersession/retraction links, never silent rewrite/deletion. Hashes alone do not prove origin, completeness, independence or trustworthy time; provenance binds actor/process and inputs. Any signing/attestation scheme and trust root require separate design/authorization; this contract selects none. Publisher credentials must not be exposed to executor.

## 10. Disagreement, missing data and error handling

Fail closed on unapproved/unavailable specification; observer read failure, stale cache or partial pagination; conflicting observations for same immutable identity/checkpoint; identity/version mismatch; event gap/duplicate/fork/invalid causal order; unknown metadata/event/transition/resource; incomplete protected-root observation; digest/provenance/manifest mismatch; oracle drift; executor-supplied expected values; or unproven read-only/role separation.

Observer disagreement is not resolved by majority vote or choosing the favorable result. Preserve both observations and mark affected assertions INDETERMINATE pending owner disposition or separately specified adjudication. Adjudication never rewrites original evidence.

Stable error classes should include SPEC_INVALID, SCOPE_MISMATCH, OBSERVATION_INCOMPLETE, OBSERVATION_STALE, IDENTITY_AMBIGUOUS, VERSION_MISMATCH, EVENT_GAP, PROVENANCE_INVALID, ORACLE_DIVERGENCE and CAPABILITY_UNPROVEN. Unknown errors map to BLOCKED/INDETERMINATE, never PASS.

## 11. Protected-root invariance

Protected assets include T0 canonical market data and required recovery copies; CORE_LEDGER and AI_LEDGER; required T3 paper-trading reconstruction/audit records; governance decisions/manifests/evidence while needed; and unknown, unclassified, orphaned or incompletely inventoried objects.

Future synthetic tests must not use protected assets as fixtures or oracle inputs. Oracle may verify non-involvement only through authorized, non-invasive evidence. This contract does not authorize probing production paths/stores. Absence from a synthetic inventory does not prove protected roots were unreachable. TEST-03 isolation proof is a prerequisite for PASS assertions relying on non-access.

## 12. Required oracle evidence package

| Evidence ID | Required evidence | Acceptance condition |
|---|---|---|
| ORA-01 | Frozen expected-state package | Approved, immutable, digest-bound before run |
| ORA-02 | Vector/case/assertion mapping | One-to-one and complete; no unknown/duplicate IDs |
| ORA-03 | Role/principal/capability matrix | Executor cannot write spec, observations, oracle or evidence |
| ORA-04 | Observer read plan | Exact synthetic namespace and immutable target versions |
| ORA-05 | Raw observation bundle | Complete, independently collected, provenance-bound |
| ORA-06 | Completeness/freshness proof | Pagination, cursor, sequence and staleness checks pass |
| ORA-07 | Deterministic comparison policy | Canonicalization/tolerances frozen; default none |
| ORA-08 | Per-vector verdict records | PASS/FAIL/INDETERMINATE with assertion references |
| ORA-09 | Run-level aggregation | Deterministic; BLOCKED/NOT RUN never PASS |
| ORA-10 | Evaluator provenance | Exact evaluator source/config/toolchain identity |
| ORA-11 | Evidence integrity chain | Append-only linkage, digests and actor provenance |
| ORA-12 | Protected-root invariance | Authorized independent evidence; no production probing |
| ORA-13 | Replay/reproducibility | Same frozen bundle yields same verdict without re-execution |
| ORA-14 | Disagreement/abort records | Conflicts preserved; no favorable-result selection |
| ORA-15 | Approval/authority binding | Exact run scope and TEST-08 authorization before execution |

## 13. Future TEST-04 acceptance assertions

| ID | Assertion | Minimum evidence |
|---|---|---|
| ORA-T01 | Expected state frozen before execution and not executor-derived | Approved spec digest and run binding |
| ORA-T02 | Executor cannot alter expected-state source | Principal/capability proof and denied write attempt |
| ORA-T03 | Observer independent and read-only | Separate identity and effective permission evidence |
| ORA-T04 | Exact immutable object/version observation | Complete observation records and target binding |
| ORA-T05 | Pagination/cursors/event sequence complete | Completeness/freshness proof and gap detection |
| ORA-T06 | Canonical comparisons deterministic | Frozen policy and repeat evaluation |
| ORA-T07 | PASS requires all positive and negative assertions | Assertion-level verdict mapping |
| ORA-T08 | FAIL supported by complete adverse evidence | Exact failed assertion and observation references |
| ORA-T09 | Missing/ambiguous/conflicting evidence is INDETERMINATE | Negative fixtures and verdict traces |
| ORA-T10 | Executor cannot forge/suppress observations or verdicts | Capability boundary and independent capture |
| ORA-T11 | Provenance binds source, spec, observer and evaluator | Verified evidence manifest |
| ORA-T12 | Replay read-only and reproducible | Repeated frozen-bundle evaluation; no lifecycle calls |
| ORA-T13 | Protected-root invariance independently supported | Authorized non-invasive observations plus TEST-03 proof |
| ORA-T14 | Disagreement preserves all observations | Conflict record and deterministic INDETERMINATE |
| ORA-T15 | Aggregation cannot mask partial/blocked vectors | Aggregation tests and strict schema validation |

These assertions are proposals only. They are not executed tests, provide no coverage credit for the 87 lifecycle vectors, and do not prove an existing oracle is independent.

## 14. Dependencies and closure conditions

TEST-04 closes only after: (1) TEST-01 runner implementation and exact run binding proven; (2) TEST-02 adapters enforce read-only observer and exact namespace capabilities; (3) TEST-03 isolation technically proven, including principal, filesystem, network and credential separation; (4) expected-state packages approved and frozen before execution; (5) observer independence, completeness/freshness and exact identity/version binding demonstrated; (6) evaluator deterministic, fail-closed and reproducible; (7) evidence provenance and append-only integrity proven; (8) protected-root invariance supported without unauthorized probing; (9) TEST-06 provenance requirements met; (10) TEST-08 exact-scope owner authorization obtained before execution; (11) TEST-07 remains separate and no cleanup/deletion capability is introduced.

A contract or self-attestation cannot close these gates. Missing conditions keep TEST-04 OPEN/BLOCKED/NOT VERIFIED as appropriate.

## 15. Current disposition

| Item | Status |
|---|---|
| TEST-01 | CONTRACT DOCUMENTED / IMPLEMENTATION NOT ESTABLISHED |
| TEST-02 | CONTRACT DOCUMENTED / IMPLEMENTATION NOT ESTABLISHED |
| TEST-03 | CONTRACT DOCUMENTED / EFFECTIVE ISOLATION NOT VERIFIED |
| TEST-04 | CONTRACT DOCUMENTED / INDEPENDENT ORACLE NOT ESTABLISHED |
| TEST-05 | OPEN / NOT ESTABLISHED |
| TEST-06 | PARTIAL / NOT ESTABLISHED |
| TEST-07 | OPEN / NOT ESTABLISHED |
| TEST-08 | NOT GRANTED — separate exact-scope authorization required |
| LDA-07 | NOT RUN; 87/87 lifecycle vectors remain NOT RUN |
| LDA-06 | PARTIAL / NOT VERIFIED |
| LDA-08 | HOLD / NOT VERIFIED |

No tests, compile, dry-run, fault injection, provisioning or Actions dispatch were performed. No secrets, permissions, runtime, VPS, database, provider, recipient, backup or replica were accessed. No source, schema, adapter, workflow, runner, permission, runtime or data changes were made. No destructive operation was performed.

**STAGE C.8 DOCUMENTARY CONTRACT COMPLETE — TEST-04 NOT CLOSED — INDEPENDENT ORACLE NOT ESTABLISHED — NO IMPLEMENTATION OR EXECUTION AUTHORITY.**