# Stage C.4 — TEST-01–07 Prerequisite Closure Plan

Date: 2026-11-10  
Repository: kenznguyen/btcusdt-telegram-signals2  
Branch: feature/t0-centralized-data-feeder-p1-20261101  
Work type: documentation-only planning; no implementation or execution  
Baseline: Stage C.3 mapping register blob 9d26ba7e71bcee565d16610be60712eba86db8ab

## 1. Purpose and boundary

Translate TEST-01–07 into evidence-bearing entry gates for a future isolated lifecycle negative-vector harness. This plan does not implement a runner, adapters, fixtures, scheduler, oracle, signing workflow or cleanup mechanism. It does not authorize test execution, Actions dispatch, repository permission changes, access to secrets, external/provider/runtime/VPS/database probes, or any production/staging mutation.

Stage C approval is interpreted only for bounded documentary analysis. TEST-08 remains a separate exact-scope authorization gate. Option C remains active: no archive, deletion, cleanup, expiry, compaction, vacuum, backup/replica removal, export mutation or irreversible transition. T0 canonical data, availability/recovery copies, CORE_LEDGER, AI_LEDGER and T3 reconstruction/audit evidence remain protected.

## 2. Prerequisite closure matrix

| ID | Required contract/evidence before implementation | Minimum acceptance evidence | Current state | Closure owner/gate |
|---|---|---|---|---|
| TEST-01 Runner | Framework/version, entrypoint, deterministic discovery, test ID ↔ vector ID mapping, timeout/exit semantics, repeatability and environment declaration | Frozen runner contract; deterministic manifest; repeat-run equivalence; no production import/config path | OPEN / NOT ESTABLISHED | Documentary contract first; implementation requires separate scope |
| TEST-02 Synthetic adapters | Explicit interfaces for object store, metadata/registry, hold/authorization, copy inventory, checkpoint/manifest and audit sink; synthetic-only namespace | Adapter contract; deny-by-default backend selection; tests proving unknown backend and production URI are rejected | OPEN / NOT ESTABLISHED | Contract + isolated implementation proposal |
| TEST-03 Isolation | Process/container/runner boundary; filesystem allowlist; network deny policy; credential absence; synthetic DB/object-store namespaces; no mount/route to canonical data | Negative isolation proof: production paths absent/unreachable; outbound network denied; no secrets injected; disposable namespace identity and ownership | OPEN / NOT ESTABLISHED | Must be independently evidenced before any run |
| TEST-04 Independent oracle | Separate principal/process and immutable expected-state source; observe executor effects without sharing its mutable state/trust boundary | Oracle identity separation; read-only observation interface; pre/post digest and event comparison; oracle tamper/compromise negative test | OPEN / NOT ESTABLISHED | Separate verifier contract and proof |
| TEST-05 Deterministic concurrency | Explicit barriers, scheduler-controlled interleavings, named fault points, deterministic clock and event ordering | Frozen schedule per race vector; reproducible traces; bounded retries; no sleep-based race assumptions; replayable event log | OPEN / NOT ESTABLISHED | Contract and fixture-level reproducibility evidence |
| TEST-06 Provenance | Bind exact source commit, spec/catalogue hashes, vector manifest, runner image/toolchain, fixture digest, oracle version, run ID and result digest; attest only after run | Verifiable attestation and independent verification; all fields cryptographically bound; no claim based solely on existing generic Sigstore workflow | PARTIAL / NOT ESTABLISHED | Reuse only after lifecycle-specific binding is designed and verified |
| TEST-07 Cleanup containment | Cleanup confined to uniquely identified synthetic namespace; enumerate all created objects; refuse unknown/out-of-scope paths; prove protected roots unchanged | Dry-run plan; allowlist/namespace proof; before/after protected-root digests; injected path traversal/alias/symlink/unknown-object negative cases; cleanup audit | OPEN / NOT ESTABLISHED | Separate cleanup contract and explicit authorization; no real cleanup now |

TEST-08 is not one of TEST-01–07 and is not satisfied by this plan. It requires separate owner approval naming the exact vectors, runner/workflow, synthetic resources, permitted network/filesystem scope, artifact destination, cleanup scope, run count and abort conditions.

## 3. Cross-cutting harness invariants

1. **Fail closed:** missing config, unknown backend, ambiguous identity, missing oracle, invalid manifest, stale/untrusted time or incomplete inventory means no execution or no PASS.
2. **Synthetic namespace only:** every fixture and generated object carries an immutable run namespace and synthetic marker; no implicit fallback to T0/T1/T2/T3/T4 resources.
3. **No secrets:** the harness receives no production credential, GitHub secret, exchange key, VPS credential, cloud credential or external recipient token.
4. **No network by default:** deny outbound traffic; any future exception must be enumerated, justified and separately approved.
5. **Protected-root invariance:** T0 canonical data and recovery copies, CORE_LEDGER, AI_LEDGER and required T3 evidence are outside all adapter and cleanup capabilities.
6. **Independent observation:** executor cannot alter oracle expectations or erase oracle evidence.
7. **Reproducibility:** freeze source/spec/fixture/scheduler/toolchain and record deterministic event traces.
8. **No false coverage:** a vector is covered only by a dedicated executable test with explicit vector ID, expected outcome, oracle assertion and recorded run evidence.
9. **No false assurance:** synthetic PASS does not establish runtime, provider, legal, production or environment-equivalence claims.
10. **Abort on uncertainty:** unexpected path, identity, object, network route, permission, digest mismatch or non-deterministic schedule halts the run and preserves evidence.

## 4. Vector-family dependency order

The 87-vector register contains adapter/backend, ambiguous outcome, authorization/identity, availability, copy lineage, evidence/verifier, hold, idempotency, inventory, manifest, observer, policy/privacy, race, recovery, registry, state-machine, T0 protection, T3 ledger separation and trusted-time families.

Recommended dependency order for a future harness design:

- **Foundation:** TEST-01 runner contract and TEST-02 synthetic adapter interfaces.
- **Containment:** TEST-03 isolation and TEST-07 cleanup containment design, reviewed before executable cleanup exists.
- **Truth source:** TEST-04 independent oracle.
- **Race determinism:** TEST-05 scheduler/barriers/clock/fault points.
- **Evidence binding:** TEST-06 source/spec/run/artifact provenance.
- **Only after all prerequisites:** prepare a TEST-08 exact execution authorization request. No automatic transition from this plan to implementation or dispatch.

This order is a dependency proposal, not a declaration that any prerequisite is complete.

## 5. Evidence package required per vector

Each future vector result must include:
- immutable vector ID and source catalogue version/hash;
- test case identifier and exact expected invariant;
- frozen source commit and runner/toolchain identity;
- fixture and synthetic namespace identifiers/digests;
- deterministic schedule and fault-point trace where applicable;
- executor result and independent-oracle result;
- before/after object and protected-root digests;
- complete audit events, including denied attempts;
- provenance/attestation and independent verification result;
- cleanup disposition limited to the synthetic namespace;
- explicit PASS / FAIL / BLOCKED / NOT RUN with reason.

A test report without independent oracle evidence, or a green process exit without per-vector assertions, is not a PASS.

## 6. Abort and stop conditions

Stop before execution if any of the following is unresolved:
- runner or adapter can resolve a production path/backend;
- filesystem/network isolation is not proven;
- any real secret or credential is present;
- oracle shares executor's mutable trust boundary;
- race schedule is nondeterministic or not replayable;
- source/spec/fixture/run/artifact binding is incomplete;
- cleanup can address anything outside the unique synthetic namespace;
- protected-root invariance cannot be demonstrated;
- workflow permissions or artifact destinations are broader than the approved scope;
- TEST-08 exact authorization is absent.

On abort, do not attempt automatic cleanup outside the synthetic namespace. Preserve the failed-run evidence and escalate for owner disposition.

## 7. Current disposition

| Item | Status |
|---|---|
| TEST-01 | OPEN / NOT ESTABLISHED |
| TEST-02 | OPEN / NOT ESTABLISHED |
| TEST-03 | OPEN / NOT ESTABLISHED |
| TEST-04 | OPEN / NOT ESTABLISHED |
| TEST-05 | OPEN / NOT ESTABLISHED |
| TEST-06 | PARTIAL / NOT ESTABLISHED |
| TEST-07 | OPEN / NOT ESTABLISHED |
| TEST-08 | NOT GRANTED — separate exact-scope approval required |
| LDA-07 | NOT RUN; 87/87 remain NOT RUN |
| LDA-06 | PARTIAL / NOT VERIFIED |
| LDA-08 | HOLD / NOT VERIFIED |

No test, compile, dry-run, fault injection or GitHub Actions workflow was run/dispatched for this increment. No secret values were read. No runtime/VPS/database/provider/recipient/backup/replica probes were performed. No source, schema, adapter, workflow, runner, permission, runtime or data changes were made. No destructive operation was performed.

**STAGE C.4 DOCUMENTARY PLAN COMPLETE — PREREQUISITES NOT CLOSED — NO IMPLEMENTATION OR EXECUTION AUTHORITY.**
