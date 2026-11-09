# Stage C.9 — TEST-05 Deterministic Concurrency Contract

Date: 2026-11-10
Repository: kenznguyen/btcusdt-telegram-signals2
Branch: feature/t0-centralized-data-feeder-p1-20261101
Work type: documentation-only contract; TEST-05 only.
Predecessors: Stage C.4 prerequisite plan; C.5 TEST-01 runner; C.6 TEST-02 adapters; C.7 TEST-03 isolation; C.8 TEST-04 independent oracle.

## 1. Purpose and authority boundary

Define requirements for deterministic testing of concurrent lifecycle operations and their safety properties. The contract covers race conditions, event ordering, fencing, idempotency, duplicate delivery, retry ambiguity, conflicting writes, crash/restart boundaries and reproducibility.

This document specifies a future test contract. It does not select a concurrency-control algorithm, assert that current T0/T1/T2/T3 implementations satisfy these properties, implement a scheduler/harness, or establish runtime behavior.

Stage C automatic approval authorizes bounded documentary work only. It does not authorize code/schema/adapter/runner/workflow changes, compilation, tests, dry-run, fault injection, GitHub Actions dispatch, secrets/permission access, runtime/VPS/database/provider/network probes, provisioning or data mutation. TEST-08 remains a separate exact-scope owner authorization gate before execution.

Option C remains active: no deletion, archive, cleanup, expiry, compaction, vacuum, backup/replica removal, export mutation or irreversible transition. All concurrency scenarios must use isolated synthetic resources only. Protected roots include T0 canonical data and recovery copies, CORE_LEDGER, AI_LEDGER, required T3 reconstruction/audit evidence, governance history/evidence while needed, and unknown/unclassified objects.

## 2. Concurrency model and terminology

Every future scenario must declare its concurrency model rather than relying on implicit database or storage semantics.

- **Operation:** one logical lifecycle action, with a stable operation ID and declared precondition/effect.
- **Attempt:** one delivery/execution attempt for an operation; retries retain the logical operation identity.
- **Actor:** a synthetic executor identity participating in the schedule.
- **Epoch/fencing token:** monotonically ordered authority generation used to distinguish current ownership from stale actors where the design uses fencing.
- **Linearization point:** the single logical instant at which an operation takes effect, but only for operations whose contract promises linearizability.
- **Happens-before:** declared causal ordering; concurrent operations without a causal edge are not assigned an invented total order.
- **Idempotency key:** stable key identifying one logical request across duplicate/retry attempts.
- **Schedule:** deterministic partial order and controlled interleaving of operation steps, barriers and failure points.
- **Observable state:** state collected independently under TEST-04, not an executor's internal claim.

The contract does not impose global serializability or linearizability on every subsystem. Each vector/specification must state whether it requires linearizable, serializable, per-key ordered, monotonic, at-least-once/idempotent, or another explicit consistency model. An unstated model is a specification defect and blocks the test.

## 3. Required schedule manifest

Each concurrency run is bound to an immutable manifest, frozen before execution, containing:

- run ID, synthetic namespace ID, spec ID/version/digest and exact source commit;
- selected vector IDs and one-to-one mapping to scenario, operation and assertion IDs;
- actor identities and their allowed capabilities;
- operation IDs, idempotency keys, inputs, preconditions and expected effects;
- declared consistency model and allowed partial-order constraints;
- deterministic scheduler/version and exact schedule representation;
- explicit barriers, release conditions, injected failure points and restart boundaries;
- random seed only if a seeded generator is used, plus generator version and fully materialized resulting schedule;
- maximum actors, steps, interleavings, retries and execution bounds;
- expected final/intermediate states and allowed outcome set;
- oracle, observer and evidence configuration digests per TEST-04;
- abort conditions and exact synthetic resource allowlist.

Execution must consume the materialized schedule, not regenerate a potentially different schedule during replay. Duplicate IDs, unknown operations, cycles in required happens-before constraints, missing preconditions, unbounded loops, unspecified consistency semantics or schedule digest mismatch reject the manifest before execution.

## 4. Deterministic scheduling requirements

A future harness must control interleavings at explicit operation boundaries. Wall-clock sleeps, best-effort timing, external load, host scheduling luck or uncontrolled network delays must not be the sole mechanism for producing a race.

Required properties:
1. Every scheduling decision is explicit, recorded and reproducible.
2. Barriers and rendezvous points have bounded waits and deterministic release rules.
3. A schedule declares which actions may overlap and which must happen-before others.
4. The scheduler records attempted, started, completed, rejected and aborted operation steps.
5. A timeout is a typed test outcome, not silently treated as a successful ordering.
6. The harness cannot expand scope or invent extra actors/operations at runtime.
7. Replaying a frozen schedule uses the same operation identities and order constraints.
8. If real asynchronous components cannot be controlled deterministically, the affected assertion remains NOT ESTABLISHED; a timing-based pass is insufficient.

Schedule exploration may use bounded interleavings and deterministic seeds, but must record the explored set and its limits. Sampling is not exhaustive proof. A finite run cannot claim all possible schedules are covered unless the state space and exhaustive enumeration are demonstrated.

## 5. Required concurrency scenario families

Each applicable family must map to explicit lifecycle vectors and assertions. Not every family applies to every vector; omitted families require a documented applicability rationale.

### 5.1 Competing writers and conflicting updates

Two or more actors attempt updates to the same synthetic object or metadata revision. Assert the declared conflict policy: compare-and-swap/version precondition, serialization, conflict rejection or another specified rule. No silent lost update, last-writer-wins assumption or partial hybrid state is accepted unless explicitly specified and approved.

### 5.2 Duplicate delivery and idempotency

Deliver the same logical operation more than once, sequentially and concurrently, with the same idempotency key. Verify one logical effect and deterministic response semantics. Reuse of a key with a different payload must be rejected or handled exactly as the frozen specification states; it must not be silently treated as a valid duplicate.

### 5.3 Retry and ambiguous acknowledgement

Exercise the boundary where an operation may have committed but its acknowledgement is lost or delayed. Retry must use the original operation identity/key. Verify no duplicate logical side effect, no false success, and a query/reconciliation path that distinguishes committed, not committed and indeterminate states.

### 5.4 Lease expiry, owner change and stale actor fencing

Where leases/ownership are part of the contract, schedule owner A, expiry or revocation, acquisition by owner B with a newer epoch/token, then a delayed write attempt from A. A stale actor must not commit after losing authority. Verify the authoritative epoch/token at the mutation boundary, not merely at initial request validation. A stale actor's response must not be mistaken for a successful mutation.

### 5.5 Ordering, causal dependencies and event append

Concurrent operations may produce a partial order. Verify all required happens-before edges, sequence uniqueness and declared per-key/global ordering guarantees. Do not require an arbitrary total order for truly concurrent events unless the specification defines one. Detect missing, duplicate, reordered, forked or causally impossible events.

### 5.6 Checkpoint, cursor and recovery races

Race checkpoint/watermark advancement against writes, delayed events, retries and reader snapshots. Verify that a checkpoint never claims coverage beyond committed/observable data under the declared consistency model; no gap is silently skipped; replay/recovery is idempotent; and a cursor cannot regress or fork unless the contract explicitly allows a versioned reset.

### 5.7 Reader/writer visibility

Schedule readers before, during and after writes. Verify declared snapshot/read-committed/monotonic visibility semantics and prevent partial object or metadata visibility. Distinguish stale-but-allowed reads from forbidden stale reads using explicit version and freshness rules.

### 5.8 Crash/restart and partial completion

Inject synthetic process interruption only at declared operation boundaries in a future authorized test. Verify durable state, recovery decisions, idempotent continuation and evidence preservation. No actual VPS, production process, canonical database, provider or backup is in scope.

## 6. Fencing and ownership invariants

Where fencing is required, the following invariants apply:

- Authority generations are strictly ordered and bound to an exact resource/lease scope.
- Every mutating operation carries the authority token/epoch used for authorization.
- The authoritative write boundary rejects stale generations even if a stale actor continues running.
- A new owner cannot be overwritten by a delayed request from an older owner.
- Lease expiry alone is not proof that all prior writes have stopped; fencing must protect the resource itself.
- Token reuse, rollback, missing token, ambiguous owner or generation regression fails closed.
- Renewal, reacquisition and recovery behavior are explicit; no implicit owner fallback.
- Observations prove committed state and accepted/rejected writes independently of actor logs.

This contract does not assert a particular fencing implementation is present or correct. If the target resource cannot enforce fencing at the mutation boundary, fencing-dependent assertions remain BLOCKED/NOT ESTABLISHED.

## 7. Idempotency and retry invariants

Each logical operation has a stable identity independent of delivery attempt. For an idempotent operation:

- repeated attempts with the same key and same canonical payload produce one logical effect;
- same key with conflicting payload is rejected or follows a frozen explicit policy;
- result replay is bound to the original operation and resource/version scope;
- acknowledgement loss cannot cause duplicate irreversible side effects;
- deduplication state has explicit durability and retention semantics sufficient for the declared retry window;
- expired/unknown deduplication state does not silently authorize unsafe replay;
- concurrent duplicate requests converge to one declared result;
- errors distinguish definite rejection, definite commit and indeterminate commit outcome.

Exactly-once delivery is not assumed. A claim of exactly-once effect requires proof of durable deduplication/transactional coupling across the complete side-effect boundary. Otherwise specify at-least-once delivery plus idempotent effect, or another honest guarantee.

## 8. Event order, checkpoints and recovery invariants

Events and checkpoints are compared using the TEST-04 independent oracle. The specification must define event identity, causal edges, sequence scope, cursor semantics, snapshot boundary and permissible visibility lag.

Minimum safety assertions:
- no duplicate event identity where uniqueness is required;
- no missing required event within a declared complete cursor/sequence range;
- no cursor advance over an uncommitted or unobserved gap;
- no checkpoint that claims a state later than its captured consistent snapshot;
- no silent sequence regression, fork or reordering violating declared causal constraints;
- recovery/replay does not duplicate logical effects;
- conflicting checkpoint writers follow a defined compare-and-swap or serialization rule;
- a failed or interrupted checkpoint remains distinguishable from a committed checkpoint.

Wall-clock timestamps alone are not a reliable causal order. Prefer monotonic sequence/version and explicit causal references. If time is used, clock source, precision, skew bounds and uncertainty must be specified; ambiguity yields INDETERMINATE.

## 9. Independent oracle and evidence binding

TEST-05 uses the TEST-04 oracle contract. The oracle must independently observe final and required intermediate states, object/version identities, event sequences, checkpoint/cursor values, fencing epochs, idempotency outcomes and protected-root invariants.

Executor logs and scheduler traces explain the attempted schedule but do not prove committed state. Oracle evidence must establish which effects occurred, their immutable identities, ordering constraints, and whether forbidden effects occurred.

Every result binds run/namespace/vector IDs; source commit; schedule manifest and digest; actor/operation identities; scheduler version; seed and materialized schedule; oracle/evaluator version; observation IDs; assertion verdicts; and evidence provenance. Evidence is append-only. On disagreement, preserve all traces/observations and return INDETERMINATE; never choose the favorable result.

## 10. Verdict and abort semantics

Per-scenario verdicts:

- **PASS:** every required schedule step and observation is complete; declared concurrency invariants hold; independent oracle confirms all positive and negative assertions; provenance and isolation gates pass.
- **FAIL:** complete trustworthy evidence demonstrates a violation such as stale-owner commit, duplicate logical effect, lost update, invalid ordering, cursor gap, partial visibility or protected-root mutation.
- **INDETERMINATE:** evidence is incomplete, conflicting, stale or ambiguous; schedule did not reach a required observation; oracle independence/provenance is unproven; or commit outcome cannot be resolved.
- **BLOCKED:** prerequisites, safety scope or authorization prevent a valid scenario run.
- **NOT RUN:** scenario was not executed.

Run aggregation: FAIL if any required scenario fails; otherwise INDETERMINATE if any required result/evidence is indeterminate or incomplete; PASS only if every selected required scenario passes and all run-level gates pass; BLOCKED when execution is prohibited before a valid run; NOT RUN when no run was attempted. BLOCKED/NOT RUN cannot be counted as successful coverage.

Immediate abort conditions include synthetic namespace escape, protected-root reference, unexpected actor/operation, unbounded schedule, missing/ambiguous authority token, observer/evaluator write capability, secret/network access, evidence tampering, unknown side effect, or any indication that the scenario touched non-synthetic resources. Abort preserves evidence; no automatic cleanup is permitted.

## 11. Determinism and reproducibility

Reproduction requires exact source commit, immutable spec and fixtures, fully materialized schedule, scheduler version/config, actor and operation identities, adapter versions, oracle/evaluator source/config, raw observations and comparison policy.

Same frozen inputs must produce the same schedule decisions and verdicts. Any nondeterministic external dependency must be eliminated, controlled or explicitly classified; otherwise the affected assertion is NOT ESTABLISHED. Randomized exploration records seed, generator version, all generated schedules and bounds. A seed alone is insufficient if generator/runtime versions are not pinned.

Replay is read-only and consumes preserved traces/evidence. It does not re-execute operations or contact external systems. Re-evaluation with a changed policy creates a new linked record and does not overwrite the original result.

## 12. Required evidence package

| Evidence ID | Required evidence | Acceptance condition |
|---|---|---|
| CON-01 | Frozen concurrency specification | Exact consistency model and invariants per scenario |
| CON-02 | Immutable schedule manifest | Actors, operations, barriers, partial order and bounds digest-bound |
| CON-03 | Materialized schedule trace | Every scheduling decision and step outcome recorded |
| CON-04 | Actor/operation identity map | Stable logical IDs and attempt IDs; no ambiguous actor |
| CON-05 | Fencing evidence | Epoch/token progression and stale-write rejection at commit boundary |
| CON-06 | Idempotency evidence | Duplicate/retry attempts converge to one specified logical effect |
| CON-07 | Conflict evidence | Competing updates follow explicit conflict/version policy |
| CON-08 | Event/cursor/checkpoint evidence | Sequence, causal edges, gap and watermark assertions |
| CON-09 | Crash/restart boundary evidence | Durable state and recovery outcome at declared synthetic boundary |
| CON-10 | Independent oracle observations | Exact state/version and event evidence per TEST-04 |
| CON-11 | Isolation and capability evidence | TEST-03 boundaries and synthetic-only scope established |
| CON-12 | Determinism/replay record | Same frozen inputs reproduce schedule and verdict |
| CON-13 | Provenance/evidence chain | Source, spec, schedule, observer and evaluator bound |
| CON-14 | Abort/disagreement record | All evidence preserved; no automatic cleanup |
| CON-15 | Approval and authority binding | Exact test scope and TEST-08 approval before execution |

## 13. Future TEST-05 acceptance assertions

| ID | Assertion | Minimum evidence |
|---|---|---|
| CON-T01 | Concurrency semantics explicitly declared | Frozen spec identifies consistency model and invariants |
| CON-T02 | Schedule is deterministic and bounded | Materialized schedule and complete scheduler trace |
| CON-T03 | Competing writers cannot violate conflict policy | Version/commit observations and assertion result |
| CON-T04 | Duplicate delivery yields specified idempotent effect | Same-key concurrent/sequential duplicate evidence |
| CON-T05 | Conflicting payload under same key is safely handled | Explicit rejection/policy evidence |
| CON-T06 | Retry after ambiguous acknowledgement is safe | Commit-state reconciliation and no duplicate effect |
| CON-T07 | Stale actor cannot commit after fencing transition | New epoch plus denied stale mutation at write boundary |
| CON-T08 | Required causal order is preserved | Event identity, sequence and happens-before comparison |
| CON-T09 | Checkpoint/cursor does not skip committed work or gaps | Independent state and completeness observations |
| CON-T10 | Reader visibility matches declared isolation model | Versioned observations at controlled schedule points |
| CON-T11 | Crash/restart preserves declared durability/recovery semantics | Synthetic interruption and independent post-recovery state |
| CON-T12 | No lost update, duplicate side effect or partial state | Oracle assertion evidence across all relevant actors |
| CON-T13 | Schedule replay is deterministic | Repeated read-only replay of frozen schedule/evidence |
| CON-T14 | Abort/ambiguity fails closed and preserves evidence | Abort trace and INDETERMINATE/BLOCKED result |
| CON-T15 | Protected roots remain outside test scope | TEST-03 proof and authorized non-invasive oracle evidence |

These are proposed acceptance assertions only. They are not executed tests, do not establish coverage for any of the 87 lifecycle vectors, and do not prove current implementations are race-safe.

## 14. Dependencies and closure conditions

TEST-05 closes only when: (1) TEST-01 runner implementation and run binding are proven; (2) TEST-02 synthetic adapters enforce scoped operations; (3) TEST-03 effective isolation is proven; (4) TEST-04 independent oracle is implemented and evidenced; (5) each selected scenario has approved consistency semantics and a frozen deterministic schedule; (6) concurrency outcomes are independently observable; (7) fencing/idempotency/conflict/checkpoint assertions are applicable and evidenced or explicitly marked not applicable with rationale; (8) deterministic replay and provenance pass; (9) TEST-06 provenance requirements are met; (10) TEST-08 exact-scope authorization is granted before execution; and (11) TEST-07 remains separate with no cleanup/deletion capability.

No contract, scheduler trace, executor log or self-attestation closes TEST-05. Missing prerequisites keep it OPEN/BLOCKED/NOT VERIFIED. A bounded schedule set must not be described as exhaustive unless exhaustive state-space coverage is demonstrated.

## 15. Current disposition

| Item | Status |
|---|---|
| TEST-01 | CONTRACT DOCUMENTED / IMPLEMENTATION NOT ESTABLISHED |
| TEST-02 | CONTRACT DOCUMENTED / IMPLEMENTATION NOT ESTABLISHED |
| TEST-03 | CONTRACT DOCUMENTED / EFFECTIVE ISOLATION NOT VERIFIED |
| TEST-04 | CONTRACT DOCUMENTED / INDEPENDENT ORACLE NOT ESTABLISHED |
| TEST-05 | CONTRACT DOCUMENTED / DETERMINISTIC CONCURRENCY NOT ESTABLISHED |
| TEST-06 | PARTIAL / NOT ESTABLISHED |
| TEST-07 | OPEN / NOT ESTABLISHED |
| TEST-08 | NOT GRANTED — separate exact-scope authorization required |
| LDA-07 | NOT RUN; 87/87 lifecycle vectors remain NOT RUN |
| LDA-06 | PARTIAL / NOT VERIFIED |
| LDA-08 | HOLD / NOT VERIFIED |

No tests, compile, dry-run, fault injection, provisioning or Actions dispatch were performed. No secrets, permissions, runtime, VPS, database, provider, recipient, backup or replica were accessed. No source, schema, adapter, workflow, runner, permission, runtime or data changes were made. No destructive operation was performed.

**STAGE C.9 DOCUMENTARY CONTRACT COMPLETE — TEST-05 NOT CLOSED — DETERMINISTIC CONCURRENCY NOT ESTABLISHED — NO IMPLEMENTATION OR EXECUTION AUTHORITY.**