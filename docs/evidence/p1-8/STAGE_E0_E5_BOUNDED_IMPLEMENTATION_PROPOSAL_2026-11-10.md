# Stage E.0–E.5 — Bounded Implementation Proposal
Date: 2026-11-10
Branch: `feature/t0-centralized-data-feeder-p1-20261101`
Scope: documentation-only; no implementation or execution authority.

## E.0 Purpose and boundary
Translate the Stage C documentary contracts and Stage D readiness findings into a bounded proposal for implementing TEST-01–07. This stage records a proposal only. It does not establish readiness, close any test gate, authorize TEST-08, or authorize destructive operations.

## E.1 Proposed implementation scope
The future implementation is limited to synthetic-only lifecycle verification and must be organized into these work packages:

| Work package | Intended boundary | Required outcome | Current status |
|---|---|---|---|
| TEST-01 Runner | Deterministic synthetic run manifest, immutable run/namespace identity, bounded scenario selection, explicit verdict lifecycle | Runner contract implemented and independently observable | NOT ESTABLISHED |
| TEST-02 Adapters | Synthetic-only resource adapters with no production credentials or protected-root reachability | Adapter capability boundary and synthetic resource lifecycle | NOT ESTABLISHED |
| TEST-03 Isolation | Effective isolation across identity, namespace, storage, network and resource references | Negative proof that protected/non-synthetic targets cannot be reached or mutated | NOT VERIFIED |
| TEST-04 Oracle | Independent observation and oracle principal, separate from executor | Deterministic expected-vs-observed verdicts; executor cannot author authoritative oracle evidence | NOT ESTABLISHED |
| TEST-05 Concurrency | Deterministic schedules/barriers, competing writers, duplicate/retry/ambiguous-ACK and fencing scenarios | Reproducible interleaving evidence and correct linearization/reconciliation | NOT ESTABLISHED |
| TEST-06 Provenance | Complete immutable source-to-result provenance chain | Verifiable completeness, integrity, attribution, causality and reproducibility | NOT ESTABLISHED |
| TEST-07 Cleanup containment | Synthetic-only candidate inventory and two-phase containment proof; no destructive capability in this proposal | Demonstrate that protected roots are excluded and no cleanup action can escape the synthetic namespace | NOT ESTABLISHED |

Implementation must consume the canonical contracts: C.4 runner contract; C.5–C.11 TEST-01–07 contracts; C.13 integrated logical schema/evidence-destination map; revised C.14 87-vector traceability matrix; C.15 closure-readiness review; and D.0–D.5 readiness/authorization proposal. Canonical records only: do not use the two identified non-canonical duplicate C.12/C.15 files.

No production T0/T1/T2/T3, database, feeder, exchange, ledger, strategy, risk engine, VPS or user data may be used as test targets. All fixtures and resources must be synthetic and isolated. No production secrets or credentials may be introduced.

## E.2 Dependency sequence
1. Reconcile and freeze the normative inputs: exact 87-vector definitions, canonical TEST-01–07 contracts, integrated logical schema, evidence-destination contract and acceptance assertions.
2. Resolve prerequisite blockers that can be resolved without execution: executable schema/canonicalization details, synthetic resource model, principal/capability model, destination identity/retention policy and verifier contract. Do not invent provider or numeric values.
3. Implement TEST-02 synthetic adapters and TEST-03 isolation boundary before exposing runner operations.
4. Implement TEST-04 independent oracle and observation path before runner verdict publication.
5. Implement TEST-06 provenance envelope/verifier and append-only evidence binding before claiming reproducible results.
6. Implement TEST-01 deterministic runner and frozen scenario manifest over the established adapters, isolation, oracle and provenance interfaces.
7. Implement TEST-05 deterministic concurrency harness and schedules against the same interfaces.
8. Implement TEST-07 synthetic-only cleanup containment as a plan/containment proof only; do not add a destructive executor or cleanup permission under Option C.
9. Perform static integration review and source-level checks after each bounded work package. Any executable lifecycle test remains blocked until the separate TEST-08 authorization and all preconditions are satisfied.
10. Map all 87 vectors to executable assertions only where exact semantics and executable bindings are demonstrated; preserve NOT RUN for all others.

This is a proposed dependency order, not an implementation plan approved for execution. Actual sequencing may be revised only through a documented owner decision; no work package can weaken another package's boundary.

## E.3 Acceptance criteria and evidence
A future work package may be considered implemented only when its code/interface and evidence meet the relevant contract. Minimum cross-cutting criteria:

- Frozen inputs: source SHA, contract/document blob SHAs, vector catalogue version, manifest digest and assertion identifiers are explicit and immutable for the run.
- Synthetic identity: every run/resource/event/observation is bound to a unique run and synthetic namespace; cross-run or unknown references fail closed.
- Least privilege: executor, observer/oracle and publisher/verifier capabilities are distinct and evidenced; no production credentials or protected-root access.
- Isolation: positive and negative boundary checks prove that protected T0 canonical data/recovery copies, CORE_LEDGER, AI_LEDGER, required T3 reconstruction/audit evidence, governance history, backups, replicas, snapshots, exports and unknown/unclassified objects are not candidates or reachable mutation targets.
- Oracle: expected state is frozen independently; observed state is independently captured; PASS/FAIL/INDETERMINATE/BLOCKED/NOT RUN semantics are explicit.
- Concurrency: schedules and barriers are immutable and reproducible; duplicate delivery, retries after ambiguous acknowledgement, competing writers, lease/epoch fencing, stale-owner rejection, checkpoint/cursor races and reader visibility are asserted at the mutation boundary.
- Provenance: source/spec/vector → manifest → principal/process → operation/attempt → resource/version → event/observation → oracle/verdict → artifact/publication chain is complete, causally consistent and verifiable.
- Cleanup containment: inventory is complete for the synthetic namespace; exact target manifest and independent pre/post observations exist; protected/unknown resources are excluded; no deletion/archive/expiry/compaction/vacuum capability or execution is introduced.
- Vector coverage: each of the 87 vectors receives an exact executable assertion mapping or remains explicitly BLOCKED/NOT APPLICABLE with rationale. Family-level mapping or adjacent tests do not count as coverage.
- Reproducibility: a separate replay using the frozen inputs can independently reproduce the same verdict and evidence references.

Required evidence package per future work package: implementation/source SHA; changed-file list; contract-to-code traceability; static review/check results; test command and exact results when authorized; workflow run ID and artifact IDs only when actually produced; immutable manifest and evidence digests; principal/capability and isolation proof; unresolved findings; PASS/PARTIAL/BLOCKED/NOT VERIFIED/NOT RUN disposition. No workflow run or artifact is produced or claimed by Stage E.0.

## E.4 Risk controls and stop conditions
Stop and classify BLOCKED or INDETERMINATE if any of the following occurs:
- Any production or protected resource, credential, endpoint or data is referenced or becomes reachable.
- Synthetic namespace, inventory completeness, effective permissions, principal separation, evidence destination identity or retention/append-only behavior cannot be proven.
- A source SHA, contract version, vector definition, manifest, schedule or expected state changes during a run.
- The executor can author/alter authoritative observer, oracle or publisher evidence.
- A retry, duplicate, crash, lease loss, stale owner, race or ambiguous acknowledgement cannot be deterministically resolved.
- A test requires destructive action, cleanup permission, external provider selection, provisioning, runtime access, secrets, database/VPS probing or workflow dispatch outside its separately approved scope.
- Evidence is missing, mutable, non-causal, unbound to exact source/run/resource, or cannot be independently replayed.
- A result depends on unstated numeric/provider/clock/retention assumptions.

Mandatory controls:
- Option C — No Destructive Authority remains ACTIVE. No cleanup, deletion, archive, expiry, compaction, vacuum or other destructive lifecycle operation is authorized.
- TEST-08 remains NOT GRANTED. No lifecycle test execution, dry-run, fault injection or Actions dispatch is authorized by this proposal.
- No implementation, source/schema/adapter/runner/workflow/permission/runtime/data change is authorized by Stage E.0.
- No VPS/T0/T1/database/provider/secret/recipient/backup/replica probe, provisioning or permission change.
- `AI_EXECUTION_ENABLED=false`; paper-only; no live orders.
- Branch protection read gap LDA-08 remains HOLD / NOT VERIFIED (HTTP 403; no permission change).
- Independent Review waiver remains as previously recorded; this proposal does not claim independent assurance or technical verification.

## E.5 Owner disposition and next gate
**Stage E.0–E.5: DOCUMENTARY PROPOSAL COMPLETE. Implementation readiness: BLOCKED. Execution: NOT AUTHORIZED.**

| Gate | Disposition |
|---|---|
| TEST-01 | Implementation NOT ESTABLISHED |
| TEST-02 | Implementation NOT ESTABLISHED |
| TEST-03 | NOT VERIFIED |
| TEST-04 | NOT ESTABLISHED |
| TEST-05 | NOT ESTABLISHED |
| TEST-06 | NOT ESTABLISHED |
| TEST-07 | NOT ESTABLISHED |
| TEST-08 | NOT GRANTED |
| LDA-07 | 87/87 NOT RUN |
| LDA-06 | PARTIAL / NOT VERIFIED |
| LDA-08 | HOLD / NOT VERIFIED |

The owner's approval in this conversation authorizes only the documentary E.0–E.5 steps listed in the preceding proposal. It does not approve implementation, tests, compilation, dry-run, fault injection, workflow dispatch, permission changes, secrets access, runtime/provider/VPS/database probes, provisioning or destructive operations.

**Next gate:** owner decision on whether to authorize a separately bounded implementation proposal or to resolve specified prerequisite blockers first. Any implementation and any lifecycle execution require separate, explicit scope and authorization; TEST-08 must be granted before lifecycle test execution. Option C remains active.
