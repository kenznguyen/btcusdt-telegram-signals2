# Stage C.11 — TEST-07 Synthetic-Only Cleanup Containment Contract

Date: 2026-11-10
Repository: kenznguyen/btcusdt-telegram-signals2
Branch: feature/t0-centralized-data-feeder-p1-20261101
Work type: documentation-only contract; TEST-07 only.
Predecessors: Stage C.4 prerequisite closure plan; C.5 TEST-01 runner; C.6 TEST-02 synthetic adapters; C.7 TEST-03 isolation; C.8 TEST-04 independent oracle; C.9 TEST-05 deterministic concurrency; C.10 TEST-06 lifecycle-specific provenance.
Source baseline: Stage C.10 report blob 3621ee7039c13b3accf887a3a22bc6a0400c9ba4; handoff branch HEAD 2bd3907034a0386806a5add1f068224f7a64a760.

## 1. Purpose and strict authority boundary

Define how a future lifecycle test system may prove that any cleanup operation is confined to an explicitly authorized, uniquely identified, disposable synthetic namespace and cannot address protected, unknown, shared, production or out-of-scope data.

This is a containment contract, not permission to delete anything. It defines prerequisites, authorization binding, target enumeration, independent checks, negative cases and evidence required before a future cleanup implementation could even be considered.

**Current authority remains Option C — No Destructive Authority.** No archive, cleanup, deletion, expiry, compaction, vacuum, truncation, overwrite, backup/replica removal, export mutation or irreversible transition is authorized by this document or by general Stage C documentary approval. No cleanup code, capability, adapter method, workflow permission, dry-run, test, dispatch or actual cleanup is introduced or executed. Any future destructive action requires a separate explicit owner approval for the exact run, target set, operation, limits and abort conditions.

Protected assets include T0 canonical market data and all required recovery copies; CORE_LEDGER; AI_LEDGER; required T3 paper-trading reconstruction/audit records; governance decisions/manifests/evidence while needed; backups, replicas, snapshots, exports and recipient/provider copies; and all unknown, unclassified, orphaned or incompletely inventoried objects.

## 2. Core safety principles

1. **No implicit cleanup:** cleanup is never an automatic consequence of test completion, failure, timeout, cancellation, runner shutdown or resource expiry.
2. **Synthetic-only:** a target must be proven to belong to one immutable run-bound synthetic namespace; a synthetic label alone is insufficient.
3. **Exact target enumeration:** wildcard, prefix-only, recursive discovery, mutable aliases and "delete everything created by this job" are prohibited as authorization.
4. **Default deny:** unknown identity, incomplete inventory, ambiguous path, missing lineage, unresolved alias, capability uncertainty or oracle disagreement means no cleanup.
5. **No protected-root access:** protected roots are outside the cleanup interface and must be independently shown unreachable, not merely omitted from a manifest.
6. **Separation of duties:** executor cannot authorize, enumerate, approve or independently attest its own cleanup targets.
7. **Two-phase control:** any future cleanup requires a separately approved immutable plan followed by a distinct execution authorization; plan generation is not execution permission.
8. **Evidence first:** capture and verify required evidence before any future cleanup; cleanup must not erase the evidence needed to establish what occurred.
9. **Abort preserves state:** on any uncertainty, stop and preserve the namespace and evidence for owner disposition; never broaden cleanup to recover from a partial cleanup.
10. **No false assurance:** a synthetic cleanup-containment result does not prove production data deletion, provider-side deletion, legal erasure, backup expiry or global copy removal.

## 3. Resource classification and eligibility

Every resource must be classified before it can enter a cleanup candidate set.

| Classification | Examples | Cleanup eligibility under a future separately approved scope |
|---|---|---|
| Protected canonical | T0 canonical candles, CORE_LEDGER, AI_LEDGER | NEVER |
| Protected reconstruction/evidence | Required T3 records, governance history, audit/provenance evidence still needed | NEVER while protected/required |
| Recovery/copy asset | Backup, WAL, snapshot, replica, export, archive, provider copy | NEVER under this contract |
| Unknown/unclassified/orphan | Missing owner, incomplete lineage/inventory, unresolved path or identity | NEVER; quarantine/escalate, no cleanup |
| Shared/non-exclusive | Shared cache, shared bucket/database/schema, common workspace | INELIGIBLE |
| Synthetic run-owned | Immutable run-bound fixture/object created in disposable isolated namespace | Candidate only after all gates and separate exact authorization |
| Evidence artifact | Manifest, observation, verdict, attestation, logs, audit records | Retain; not a cleanup candidate under this contract |

Eligibility is conjunctive: exact immutable identity, exclusive synthetic ownership, complete lineage, namespace proof, no shared references, no protected dependency, independent inventory, retention/hold resolution, and exact owner authorization must all be established. Failure of any condition makes the object ineligible.

## 4. Synthetic namespace contract

A cleanup candidate namespace must have:
- globally unique immutable namespace ID and run ID;
- exact source commit, manifest/spec digest and lifecycle vector set;
- immutable owner/principal and creation provenance;
- explicit backend/resource-root identity and isolated storage boundary;
- complete allowlisted object/version inventory, including children and derived objects;
- explicit lineage to creator operation and run;
- no alias, mount, symlink, hard link, shared volume, shared database/schema, cross-run reference or external recipient;
- independent proof that no protected root or recovery asset is reachable through the namespace;
- a frozen end-of-run state and evidence checkpoint before any proposed cleanup.

Namespace identity must not be inferred from branch, job name, timestamp, path prefix, tag, bucket prefix or a user-supplied string. If the backend cannot enforce immutable namespace ownership and exact resource identity, cleanup is BLOCKED.

## 5. Exact target manifest and immutable cleanup plan

A future cleanup plan must be a separate immutable artifact containing:
- plan ID/version/digest; run and namespace IDs; source/spec/vector references;
- exact owner approval reference and permitted cleanup operation;
- exact target resource IDs and immutable versions, with parent/child lineage;
- resource type, backend identity, account/project/database/bucket/workspace scope where applicable;
- pre-cleanup byte/content/metadata digest and independent inventory observation;
- creation provenance proving the object is synthetic and run-owned;
- explicit exclusion list for protected, shared, unknown, evidence and recovery assets;
- dependency graph and ordering constraints, including objects that must be retained;
- maximum target count, bytes, operation count, concurrency and time window;
- hold/retention/authorization decision and evidence;
- expected postcondition for each exact target and independent verification method;
- abort conditions, partial-failure handling and immutable audit destination;
- TEST-08 execution authorization binding, if a lifecycle test is ever executed.

The target list must be fully materialized and digest-bound before any action. No wildcard, recursive selector, prefix expansion, query expression, "latest" alias or runtime-discovered target can expand the approved set. If any target changes identity/version or digest after plan approval, the plan is invalid and must be reviewed as a new plan.

## 6. Authorization and separation of duties

The following roles must be independently identifiable through effective principals and capabilities:

| Role | Permitted responsibility | Prohibited authority |
|---|---|---|
| Owner/approver | Approve exact target manifest, operation and limits | Implicit approval of newly discovered targets |
| Inventory observer | Read-only enumeration and lineage evidence | Mutate targets or approve own observations |
| Policy/eligibility evaluator | Decide whether each exact target meets eligibility rules | Execute cleanup or suppress unknown objects |
| Plan publisher | Publish immutable plan and digest | Expand target set after approval |
| Cleanup executor | Future narrowly scoped operation only after separate approval | Change plan, discover targets, access protected roots or alter evidence |
| Independent verifier | Verify postconditions and protected-root invariance | Mutate target set or perform cleanup |
| Evidence publisher | Append plan, action and verification evidence | Rewrite history or decide cleanup eligibility |

Distinct labels or job names do not prove separation. Effective identity, credential, process and write-capability evidence is required. The executor must not possess authority to modify the approval, inventory, oracle, evidence store or protected-root state.

No role or permission is granted by this document. No repository, cloud, database, storage or workflow permission is changed.

## 7. Two-phase authorization protocol

A future destructive cleanup requires two independent gates:

**Phase A — plan authorization**
- freeze exact target manifest and exclusion set;
- verify namespace, lineage, exclusive ownership, hold/retention and inventory completeness;
- capture required pre-action evidence and independent protected-root baseline;
- obtain owner approval naming exact operation, targets, limits, time window and abort conditions;
- publish immutable plan and approval references.

**Phase B — execution authorization**
- revalidate plan digest, current target identities/versions/digests and approval validity;
- confirm TEST-03 isolation, TEST-04 independent oracle, TEST-06 provenance and applicable inventory/hold controls;
- confirm TEST-08 exact execution authorization where a lifecycle test is involved;
- obtain a separate explicit owner authorization for the actual destructive operation;
- execute only the exact approved target set, under bounded limits, with no target discovery or scope expansion.

Passing Phase A does not authorize Phase B. General approval to continue Stage C does not satisfy either destructive gate. Any change to target set, namespace, operation, tool, identity, workflow or limits invalidates the authorization.

## 8. Execution and failure semantics for future implementation

If separately authorized in a future phase, the executor must:
- verify the complete plan and all target identities immediately before each operation;
- use exact immutable resource/version references, never path or alias resolution alone;
- recheck namespace and authorization at the mutation boundary;
- record each attempted, accepted, completed, rejected or indeterminate action;
- stop on first scope, identity, digest, permission, lineage, inventory or oracle discrepancy;
- never retry an ambiguous destructive action blindly;
- never broaden the target set or perform compensating deletion;
- preserve immutable audit and evidence records outside the target namespace.

A timeout or lost acknowledgement is an indeterminate outcome until independently reconciled. A partial cleanup is not rolled back by deleting more objects. Remaining objects are preserved and escalated. Cleanup must not remove evidence needed for reconciliation or proof.

This section describes future requirements only; no cleanup execution semantics are currently implemented or verified.

## 9. Independent pre/post observation

Before any future authorized action, the independent observer must record:
- exact namespace and target inventory, object/version IDs and lineage;
- content/metadata digests and object counts/byte totals;
- all shared, protected, unknown and excluded references;
- holds, retention and authorization state;
- evidence checkpoint and immutable plan digest;
- protected-root integrity/reachability baseline through an authorized non-invasive method.

After any future authorized action, the observer must independently establish:
- each approved target's exact expected postcondition;
- no unapproved target changed or disappeared;
- protected roots, recovery copies and retained evidence remain unchanged;
- no alias, child, replica, export or external copy was silently omitted from the declared scope;
- action receipts, audit sequence and provenance are complete;
- unresolved/ambiguous outcomes remain INDETERMINATE.

Absence from one namespace listing is not proof of global deletion. This contract makes no claim about provider replicas, backups, caches, downstream recipients or legal erasure.

## 10. Mandatory negative scenarios

Future synthetic tests must prove denial or safe blocking for:
- path traversal, prefix collision, symlink, hard-link, mount alias and namespace escape;
- mutable alias or "latest" reference substituted after approval;
- target object version or digest changed after plan freeze;
- unknown, unclassified, orphaned or incomplete-lineage object;
- shared resource or cross-run/cross-namespace object;
- T0/T1/T2/T3/T4, ledger, backup, replica, WAL, snapshot, export or evidence reference;
- protected root reachable through indirect path, mount, credential or backend fallback;
- wildcard, recursive listing, unbounded selector or runtime-discovered target;
- missing, expired, ambiguous or mismatched owner approval;
- executor attempts to alter plan, inventory, oracle, audit or evidence;
- inventory pagination gap, stale observation or disagreement;
- hold/retention/authorization state unknown or conflicting;
- duplicate/replayed cleanup request or ambiguous acknowledgement;
- partial action followed by retry or runner crash;
- target count/bytes/concurrency/time bound exceeded;
- evidence destination inside the target namespace;
- abort path that attempts automatic cleanup or erases evidence.

Negative fixtures must be frozen independently and later run only in a separately authorized synthetic environment. A documented denial scenario is not executed coverage.

## 11. Evidence package

| Evidence ID | Required evidence | Acceptance condition |
|---|---|---|
| CLN-01 | Resource classification registry | Every object classified; unknown defaults ineligible |
| CLN-02 | Immutable namespace identity | Run-bound isolated root and exclusive ownership |
| CLN-03 | Complete inventory and lineage | No gaps, aliases, orphan or unbounded enumeration |
| CLN-04 | Protected/excluded root registry | T0, ledgers, T3 evidence, backups and unknowns excluded |
| CLN-05 | Effective isolation evidence | TEST-03 proof; no route or capability to protected roots |
| CLN-06 | Hold/retention/authorization evidence | Exact policy result for each candidate |
| CLN-07 | Exact target manifest | Immutable resource/version list and digest |
| CLN-08 | Owner plan approval | Exact operation, targets, limits and expiry |
| CLN-09 | Independent pre-action observations | Target and protected-root baseline |
| CLN-10 | Effective principal/capability map | Role separation and executor least privilege |
| CLN-11 | Execution authorization | Separate explicit approval and TEST-08 binding where applicable |
| CLN-12 | Per-target action ledger | Exact attempt/result and immutable references |
| CLN-13 | Independent post-action observations | Approved postconditions and unchanged exclusions |
| CLN-14 | Append-only audit/provenance chain | Source, plan, actor, target, action and artifact links |
| CLN-15 | Abort/partial-failure record | State preserved; no automatic scope expansion or cleanup |
| CLN-16 | Reconciliation and residual inventory | All unresolved targets accounted for; no global deletion claim |

## 12. Future TEST-07 acceptance assertions

| ID | Assertion | Minimum evidence |
|---|---|---|
| CLN-T01 | Unknown/unclassified objects are never eligible | Inventory negative fixture and deny verdict |
| CLN-T02 | Only exact run-owned synthetic namespace is eligible | Immutable namespace and ownership proof |
| CLN-T03 | Target list is exact and immutable | Frozen manifest digest and no wildcard selectors |
| CLN-T04 | Shared/cross-run resources are rejected | Lineage and namespace isolation evidence |
| CLN-T05 | Protected roots and recovery assets are unreachable/ineligible | TEST-03 isolation plus protected-root registry |
| CLN-T06 | Holds/retention/authorization are fail-closed | Per-target decision and negative cases |
| CLN-T07 | Plan and execution approvals are separate | Distinct approvals bound to exact plan/action |
| CLN-T08 | Executor cannot change plan or evidence | Effective principal/capability and denied-write evidence |
| CLN-T09 | Pre-action inventory is complete and independently observed | Cursor/pagination/lineage completeness proof |
| CLN-T10 | Changed identity/version/digest invalidates the plan | Revalidation and rejection evidence |
| CLN-T11 | Runtime target discovery cannot expand scope | Bounded selector and adapter capability proof |
| CLN-T12 | Partial/ambiguous action stops without unsafe retry | Reconciliation record and preserved state |
| CLN-T13 | Evidence survives and remains outside target namespace | Independent artifact/provenance validation |
| CLN-T14 | Post-action protected/excluded assets remain unchanged | Independent before/after observations |
| CLN-T15 | Abort never triggers automatic cleanup | Abort trace and unchanged resource evidence |
| CLN-T16 | No unsupported global deletion/erasure claim is made | Scope-limited report and residual inventory |

These are proposed assertions only. They are not executed tests and provide no coverage credit for any of the 87 lifecycle vectors.

## 13. Dependencies and closure conditions

TEST-07 cannot close until:
1. TEST-01 runner has immutable run/namespace binding and no implicit cleanup path.
2. TEST-02 adapters expose no destructive capability to ordinary executor/observer roles and cannot resolve production backends.
3. TEST-03 effective isolation, filesystem/mount/network/credential boundaries and protected-root non-reachability are technically proven.
4. TEST-04 independent oracle can observe exact resource state and protected-root invariants.
5. TEST-05 concurrency/retry semantics prevent duplicate or ambiguous destructive effects.
6. TEST-06 provenance binds approval, plan, actor, target, action, observation and artifact end-to-end.
7. Complete inventory, lineage, classification and retention/hold decisions are proven.
8. Exact plan and target set are immutable; unknown/shared/protected objects fail closed.
9. Pre/post evidence is independent, append-only and retained outside the candidate namespace.
10. A separate owner approval authorizes any actual destructive implementation or execution; TEST-08 remains mandatory for lifecycle runs.
11. No protected data, backups, replicas, governance history or required evidence is made eligible by inference.

This contract deliberately does not add cleanup to the TEST-02 adapter interface or runner. A future implementation proposal must first demonstrate that ordinary test execution has no delete capability and that any exceptional cleanup controller is separately isolated, explicitly authorized and independently verifiable.

## 14. Current disposition

| Item | Status |
|---|---|
| TEST-01 | CONTRACT DOCUMENTED / IMPLEMENTATION NOT ESTABLISHED |
| TEST-02 | CONTRACT DOCUMENTED / IMPLEMENTATION NOT ESTABLISHED |
| TEST-03 | CONTRACT DOCUMENTED / EFFECTIVE ISOLATION NOT VERIFIED |
| TEST-04 | CONTRACT DOCUMENTED / INDEPENDENT ORACLE NOT ESTABLISHED |
| TEST-05 | CONTRACT DOCUMENTED / DETERMINISTIC CONCURRENCY NOT ESTABLISHED |
| TEST-06 | CONTRACT DOCUMENTED / LIFECYCLE-SPECIFIC PROVENANCE NOT ESTABLISHED |
| TEST-07 | CONTRACT DOCUMENTED / CLEANUP CONTAINMENT NOT ESTABLISHED |
| TEST-08 | NOT GRANTED — separate exact-scope authorization required |
| LDA-07 | NOT RUN; 87/87 lifecycle vectors remain NOT RUN |
| LDA-06 | PARTIAL / NOT VERIFIED |
| LDA-08 | HOLD / NOT VERIFIED |

No tests, compile, dry-run, fault injection, provisioning or GitHub Actions dispatch were performed. No cleanup, deletion, archive, expiry, compaction, vacuum or other destructive operation was performed. No secrets or permission values were accessed. No runtime/VPS/database/provider/recipient/backup/replica probes were performed. No source, schema, adapter, workflow, runner, permission, runtime or data changes were made.

**STAGE C.11 DOCUMENTARY CONTRACT COMPLETE — TEST-07 NOT CLOSED — CLEANUP CONTAINMENT NOT ESTABLISHED — OPTION C UNCHANGED — NO DESTRUCTIVE AUTHORITY.**
