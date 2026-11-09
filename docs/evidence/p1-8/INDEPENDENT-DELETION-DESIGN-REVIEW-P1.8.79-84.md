# Independent Deletion-Design Review — P1.8.79–P1.8.84

Date: 2026-11-09
Review type: Read-only documentary architecture and safety review
Review scope: P1.8.79–P1.8.84 and governing lifecycle contracts
Verdict: **PARTIAL — DESIGN COHERENT AT PRINCIPLE LEVEL; MATERIAL CLOSURE GAPS REMAIN**
Execution authority: **NONE — NOT IMPLEMENTED / NOT ACTIVE / NOT AUTHORIZED**

## 1. Review method and evidence boundary

The review read the following documents from branch `feature/t0-centralized-data-feeder-p1-20261101`:

| Document | Blob SHA |
|---|---|
| `docs/architecture/DATA_DELETION_SAFETY_CONTRACT.md` | `e055d88308d8576c5c6826e12280b847f5ec5717` |
| `docs/architecture/CENTRAL_DATA_LIFECYCLE_POLICY.md` | `9fd46c029cff643ccc35492fd09620581f6eff35` |
| `docs/architecture/DATASET_CONSUMER_CONTRACT.md` | `31d958360315eb24716a7656cef8b430187c82b1` |
| `docs/architecture/DATA_COPY_BACKUP_REPLICA_LIFECYCLE_CONTRACT.md` | `4112c68eceef7d9047117efc5027750ae2edf2d8` |
| `docs/architecture/SHARED_DATA_FOUNDATION.md` | `18f8566723b95c4b38586e3848bde5305295a4dc` |
| `docs/evidence/p1-8/P1.8.79-deletion-mechanism-gap-assessment.md` | `4942433048d1e052e989a9a9bca9a1a2ce3433ab` |
| `docs/evidence/p1-8/P1.8.80-retention-and-eligibility-policy.md` | `a38710c9d01e5409ce989cc73f791c94bc73773f` |
| `docs/evidence/p1-8/P1.8.81-dependency-and-consumer-governance-contract.md` | `f1423d16e0327f47e2b974ae13e622174c5a0cb6` |
| `docs/evidence/p1-8/P1.8.82-deletion-authorization-and-execution-contract.md` | `99f7e5a4cdcdf3edf88c424dde30e8306ad78aae` |
| `docs/evidence/p1-8/P1.8.83-copy-and-evidence-lifecycle-closure.md` | `3020dbeb47d54b41fa6b7608ddf2721f83b5b47e` |
| `docs/evidence/p1-8/P1.8.84-deletion-acceptance-and-negative-case-matrix.md` | `99b2e688075b0b39e84fc1a07673ebd2a7e69a62` |

Review was documentary and read-only. No source, schema, workflow, service, database, VPS, runtime, copy inventory or storage object was inspected or changed. No test, workflow, dry-run, restore, fault injection or destructive operation was run. This is not a production security certification or independent runtime verification.

## 2. Executive conclusion

The design has a strong and internally consistent safety direction:

- eligibility, approval, execution authorization, execution and independent verification are separate gates;
- consumer ACK is not dependency release, and dependency release is not deletion authority;
- unknown/stale/unavailable dependency, hold, copy, recovery or evidence state is protective;
- source, consumer dependency, copy, request/execution and evidence lifecycles are separate;
- exact immutable scope, no cascade, idempotency and no blind retry are explicit;
- T0 canonical data and T3 CORE_LEDGER/AI_LEDGER boundaries are protected;
- archive and deletion are distinct operations;
- no numeric retention or grace values were invented.

No direct contradiction was found that authorizes an unsafe action or weakens T0 protection. However, the contracts do not yet form a fully closed, implementable control specification. Several key authorities, concurrency semantics, state mappings, storage outcome semantics and test oracles remain unresolved.

**Verdict: PARTIAL.** The design may proceed to bounded gap closure and further documentary review. It must not proceed to implementation, staging, runtime inventory, deletion tests against real storage, archive or deletion execution.

## 3. Findings

### DR-01 — MAJOR: Hold lifecycle and propagation contract is incomplete

**Evidence**
- Central lifecycle policy defines a hold owner and scoped hold review.
- Copy lifecycle contract requires source-hold protection to apply to known copies and keeps unknown lineage protected.
- P1.8.84 blocks active, unknown or disputed holds.

**Gap**
The documents do not define one complete hold lifecycle: creation authority, immutable scope identity, owner/delegate rules, propagation/acknowledgement across copy inventory, renewal, expiry semantics, revocation, concurrent hold creation during authorization/execution, and authoritative proof that a hold change has reached every relevant decision/executor boundary.

**Risk**
A hold may be validly created or changed while a request is approved or multi-object execution is underway, without a precise serialization/fencing contract proving whether the hold takes effect before each mutation.

**Required closure**
Define a hold contract with explicit states and transitions, exact source/copy scope, authority, event ordering, propagation evidence, and race behavior. A review date or nominal expiry must never silently remove protection. Until closed, unresolved hold state blocks all affected disposition.

### DR-02 — MAJOR: No single canonical state-machine mapping across contracts

**Evidence**
- Data Deletion Safety Contract defines the fuller request lifecycle, including eligibility review, eligible for approval, approved, awaiting execution authorization, execution authorized, executing, reconciliation and verified complete, plus cancelled/rejected/expired.
- P1.8.82 presents a compressed logical sequence: REQUESTED → REVIEWED_ELIGIBLE → APPROVED → FINAL_RECHECK → AUTHORIZED → EXECUTING → RECONCILIATION_REQUIRED → VERIFIED_COMPLETE.
- P1.8.84 defines ordered gates G0–G14 and additional outcome vocabulary.

**Gap**
The documents do not provide a canonical crosswalk for state names, transition guards, terminality, retries, re-entry after invalidation, and the relationship between request state, authorization state, per-object execution state, copy state and dataset state.

**Risk**
Different future components could interpret the same event differently, especially cancellation, expiry, approval invalidation, partial execution and reconciliation.

**Required closure**
Publish one normative state-transition table or model that maps each domain separately and defines allowed transitions, guards, event ordering, terminal states and recovery/re-entry. Do not collapse dataset, dependency, copy, request, authorization, per-object execution and evidence states into one enum.

### DR-03 — MAJOR: Hold/registry decision barrier is not fenced through the full mutation window

**Evidence**
- P1.8.81 requires an authoritative registry decision barrier and revision.
- P1.8.82 requires final rechecks and executor validation before each destructive mutation.
- P1.8.84 requires cancellation races to serialize and unknown ordering to reconcile.

**Gap**
No complete protocol specifies how a dependency/hold/policy change occurring after final authorization but between objects in a multi-object manifest is ordered against each mutation. A preflight snapshot alone is insufficient unless the system can prove that no protective state changed or can atomically fence the operation.

**Risk**
An operation may continue on later objects after a newly registered dependency or hold should have blocked further progress.

**Required closure**
Define a decision-barrier/fencing protocol: authoritative revision, authorization binding, per-object compare-and-act preconditions or an equivalent serialized transaction, revocation/hold propagation guarantees, and exact stop/reconcile behavior. If the backend cannot enforce this, it must not support destructive multi-object execution.

### DR-04 — MAJOR: Storage disposition semantics are not normalized

**Evidence**
- Contracts distinguish archive, deletion, access revocation, encryption-key destruction, copy disposition and evidence disposition.
- Adapter sections require backend-specific identity and verification.
- P1.8.82 expects exact objects to match the requested operation and independent verification.

**Gap**
There is no common operation/result vocabulary defining logical unlink, row deletion, partition drop, object-version purge, delete marker, cryptographic erasure, overwrite, inaccessible-but-retained data, replica propagation and residual metadata. “Removed” and “deleted” can have different meanings across SQLite, PostgreSQL, object storage, backups and external recipients.

**Risk**
A backend may report success for logical invisibility while recoverable payload, replicas, WAL, snapshots, recipient copies or provider lifecycle remnants remain. A verifier could incorrectly report global deletion.

**Required closure**
Define operation semantics and bounded claims per adapter: what exact representation is affected, what remains, what can be recovered, propagation guarantees, residual states, verification oracle and permitted final status. Global deletion must never be claimed when unmanaged/external copies are unknown.

### DR-05 — MAJOR: Independent approval model is not operable for the current personal-project authority model

**Evidence**
- P1.8.82 requires requester and approver to be distinct.
- It allows a single human to hold multiple roles only with a separately approved compensating-control design; no such exception is approved.
- Quorum, identity provider, MFA and delegation remain OPEN.

**Gap**
No approved role/identity model exists for the personal project, including how independence is evidenced when one owner is responsible for the project and what compensating controls could be acceptable.

**Risk**
A future implementation could either deadlock permanently or weaken separation informally to make the workflow usable.

**Required closure**
Keep destructive authorization disabled until the owner explicitly chooses and approves a role model. A compensating-control proposal must be separately reviewed and must not silently treat self-approval as independent approval. No quorum or identity provider is inferred.

### DR-06 — MAJOR: Runtime inventory completeness and unknown external-copy discovery remain unproven

**Evidence**
- P1.8.83 requires per-boundary inventory outcomes and states registry absence is not proof of absence.
- P1.8.84 requires all applicable copies and external destinations to be accounted for.
- Runtime copy/consumer inventory is explicitly NOT VERIFIED.

**Gap**
Discovery authorities and methods for unmanaged local files, user downloads, third-party recipients, CI artifacts, external exports, snapshots and provider-side replicas are not selected or evidenced. There is no owner-approved rule for when a bounded inventory can support a bounded claim.

**Risk**
The system may claim that all copies have been handled when its discovery method cannot observe all destinations.

**Required closure**
Define bounded inventory claims by source boundary, discovery authority, coverage, exclusions, observation evidence and residual uncertainty. Unknown/unmanaged destinations must limit the claim to “known in-scope copies”; they must not be represented as global deletion.

### DR-07 — MAJOR: Acceptance matrix is not yet an executable, independently verifiable test specification

**Evidence**
- P1.8.84 defines 45 negative cases and a required evidence package.
- It explicitly states tests/CI were not run and no adapters, registry or verifier are implemented.

**Gap**
The matrix does not yet assign each vector a fixture, initial state, event sequence, expected transition, observable oracle, isolation proof, cleanup/containment rule, and evidence schema. Several race and adversarial cases are described but not made deterministic and independently observable.

**Missing or under-specified examples**
- registry split-brain/leadership change and stale authoritative revision;
- hold creation/revocation racing with authorization and per-object execution;
- duplicate/reordered/replayed registry events;
- wall-clock rollback, untrusted timestamp and expiry boundary behavior;
- symlink/path substitution and object-generation replacement at the mutation boundary;
- verifier compromise or shared control plane with executor;
- delayed replication, provider lifecycle jobs and residual recovery artifacts;
- evidence-store partition or tampering concurrent with execution.

**Required closure**
Turn each required vector into a versioned test case with deterministic fixture and independent oracle. Synthetic tests must remain isolated from canonical/runtime storage. Do not run them until a separate test scope and approval exist.

### DR-08 — MAJOR: Trusted time and evidence freshness are not operationally bound

**Evidence**
- Deletion safety and P1.8.82 require fresh evidence and time-bounded authorization.
- P1.8.81 leaves read-model freshness open.
- P1.8.82 leaves evidence freshness, authorization lifetime and identity assurance open.
- P1.8.84 lists stale evidence but has no authoritative time model.

**Gap**
No trusted time source, timestamp authenticity, clock rollback/skew handling, monotonic ordering or freshness evaluation mechanism is selected. This is especially important for approval expiry, revocation, hold events and evidence age.

**Risk**
Different components may disagree on whether evidence or authorization is valid, or accept stale/replayed evidence.

**Required closure**
Define a fail-closed trusted-time and event-ordering contract before implementation. Keep all numeric windows OPEN until measured and approved. If time trust cannot be established, block authorization.

### DR-09 — MINOR: Copy lifecycle contract section numbering is out of order

**Evidence**
The copy lifecycle contract places §5.6 before §5.5.

**Risk**
Low; may confuse future references.

**Required closure**
Normalize section order and check inbound references during the next documentation-only correction. No need to alter semantics.

### DR-10 — OBSERVATION: No unsafe contradiction found in the reviewed design set

The following potentially conflicting rules were reviewed and found compatible when interpreted as separate authority domains:
- consumer ACK vs explicit dependency release;
- dependency release vs dataset eligibility;
- source hold inheritance vs copy-specific hold;
- source lifecycle vs copy lifecycle vs evidence lifecycle;
- archive authorization vs deletion authorization;
- T0 writer fencing vs deletion authority;
- executor result vs independent verification;
- design-defined negative cases vs tests actually executed.

The stricter role separation in P1.8.82 supplements, rather than weakens, the base deletion contract. The unresolved personal-project role model remains DR-05.

## 4. Coverage assessment

| Review axis | Result | Rationale |
|---|---|---|
| Correctness / internal consistency | PARTIAL | Core invariants align; canonical state mapping and hold races remain open |
| Authority and separation of duties | PARTIAL | Roles are described; operable identity/quorum/compensating-control model absent |
| Dependency and registry safety | PARTIAL | Fail-closed principles strong; mutation-window fencing not closed |
| Copy and recovery lifecycle | PARTIAL | Copy contract comprehensive at principle level; runtime inventory and adapter semantics unverified |
| Storage and security semantics | PARTIAL | Exact-scope safeguards described; trusted time, per-adapter deletion semantics and verifier independence need closure |
| Failure-mode coverage | PARTIAL | 45 cases are useful; missing deterministic race/adversarial vectors identified |
| Testability / evidence | PARTIAL | Evidence package described; no executable oracle or test evidence exists |
| T0 and ledger protection | PASS at design level | No deletion authority inferred; T0 and CORE_LEDGER/AI_LEDGER boundaries retained |
| Runtime/production readiness | NOT VERIFIED | No implementation, runtime inventory, tests, CI or independent operational evidence |

## 5. Required next work, in order

1. **P1.8.85 — Hold Lifecycle and Mutation-Window Fencing Contract**: close DR-01 and DR-03.
2. **P1.8.86 — Canonical Lifecycle State Mapping**: close DR-02 across dataset, dependency, copy, request, authorization, object execution and evidence domains.
3. **P1.8.87 — Storage Disposition Semantics and Bounded Claims**: close DR-04 per backend and copy type.
4. **P1.8.88 — Identity, Trusted Time and Approval Governance**: close DR-05 and DR-08 without inventing provider, quorum or numeric windows.
5. **P1.8.89 — Inventory Claim Boundaries and Discovery Evidence**: close DR-06 at design level; runtime inventory remains separate and unauthorized.
6. **P1.8.90 — Executable Negative-Case Specification**: close DR-07 at design level only; no test execution without separate authorization.
7. Correct the section numbering in the copy lifecycle contract as a bounded documentation-only change.
8. Conduct a second independent review of the corrected design set.

Do not begin V07/V08/Restore/TSA conflict review until the second independent deletion-design review is complete.

## 6. Final decision and restrictions

**INDEPENDENT REVIEW VERDICT: PARTIAL.**

The principles are coherent and preserve the intended safety boundaries, but material design gaps prevent declaring the deletion mechanism design closed or implementation-ready.

- No implementation is approved.
- No staging or workflow dispatch is approved.
- No runtime/VPS/database/copy inventory is authorized by this review.
- No archive, cleanup, retention timer, vacuum, compaction, restore, key destruction or deletion is authorized.
- No real-storage dry-run or destructive test is authorized.
- T0 remains an independently governed canonical data asset; this review grants no T0 deletion permission.
- CORE_LEDGER and AI_LEDGER remain separate and protected by their obligations.
- Numeric retention, grace, evidence freshness, authorization lifetime, quorum, RPO/RTO, identity provider and storage provider remain OPEN.
- V07/V08/Restore/TSA conflict review remains deferred.

Tests/CI: NOT RUN. Workflow run/artifact: NONE. Runtime evidence: NOT VERIFIED.
