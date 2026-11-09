# Stage D.0–D.5 — Implementation Readiness and Execution Authorization Proposal

Date: 2026-11-10
Repository: kenznguyen/btcusdt-telegram-signals2
Branch: feature/t0-centralized-data-feeder-p1-20261101
Work type: documentation-only readiness and owner decision package.
Authority: owner approved automatic execution of Stage D steps, bounded to the previously proposed D.0–D.5 documentary scope.

## 1. Scope and authority

Stage D.0–D.5 records prerequisites, a proposed implementation sequence, least-privilege permission requirements, a future TEST-08 authorization package and the owner decision boundary.

This approval does **not** authorize implementation, test execution, compile, dry-run, fault injection, GitHub Actions dispatch, workflow or permission changes, provisioning, secrets access, VPS/T0/T1/database/provider/network probes, data mutation, or destructive operations. No implementation or execution authority is inferred from this document.

The work remains on the existing branch. No branch, PR, merge, rebase or force update is created. Option C — No Destructive Authority — remains active. TEST-08 remains NOT GRANTED. AI execution remains disabled; no live orders.

## 2. D.1 — Prerequisite assessment

The following statuses are taken from canonical Stage C.15 and its referenced C.13/C.14 records. They are not upgraded by this readiness review.

| Gate / item | Recorded status | Evidence needed before technical closure |
|---|---|---|
| TEST-01 runner | Implementation NOT ESTABLISHED | Implemented manifest-bound runner, immutable vector selection, per-vector result and fail-closed aggregation |
| TEST-02 synthetic adapters | Implementation NOT ESTABLISHED | Synthetic-only adapters with exact object/version preconditions, bounded capabilities and mapped tests |
| TEST-03 isolation | NOT VERIFIED | Effective process, filesystem/mount, network, credential and principal isolation, independently observed |
| TEST-04 independent oracle | NOT ESTABLISHED | Separate observer/evaluator principal, frozen expected state, independent read-only channel and deterministic comparison |
| TEST-05 concurrency | NOT ESTABLISHED | Deterministic materialized schedules/barriers, causal trace and independent outcome observation |
| TEST-06 provenance | NOT ESTABLISHED | Complete source/spec/vector-to-artifact provenance chain and independent verification |
| TEST-07 cleanup containment | NOT ESTABLISHED | Synthetic namespace inventory, protected-root exclusions and independently observed containment; no cleanup capability authorized |
| TEST-08 execution authorization | NOT GRANTED | Separate exact-scope owner authorization; this document is not that authorization |
| LDA-07 lifecycle suite | 87/87 NOT RUN | Executable bindings and authorized run evidence for every selected vector; denominator cannot be silently reduced |
| LDA-06 live copy/consumer inventory | PARTIAL / NOT VERIFIED | Authorized complete inventory of consumers, DB/WAL/snapshots, backups, replicas, exports, caches, recipients and restore paths |
| LDA-08 effective permissions | HOLD / NOT VERIFIED | Branch-protection read gap and effective workflow/runner/OIDC/environment/provider capabilities evidenced |

### Readiness conclusion

**BLOCKED for implementation execution and lifecycle testing.** The contracts and documentary traceability exist, but implementation, effective isolation, independent oracle, provenance, inventory and authorization prerequisites are not established. No claim of execution readiness is made.

The known branch-protection metadata read gap remains HTTP 403. No Administration permission request or change is included in this stage.

## 3. D.2 — Proposed implementation dependency order

The following is a design sequence only. It does not authorize work on these components.

1. **TEST-01 Runner foundation:** frozen run manifest, exact source/spec/vector binding, immutable namespace identity, bounded selection and result aggregation. Runner must have no cleanup capability.
2. **TEST-02 Synthetic adapters:** synthetic in-memory/file-backed resources only; exact version/precondition semantics; explicit operation allowlist; no provider or production adapters.
3. **TEST-03 Isolation:** establish and independently observe process, filesystem/mount, network, credentials and principal boundaries before any test can be considered isolated.
4. **TEST-04 Independent oracle:** freeze expected state before execution; use a distinct observer/evaluator trust boundary; incomplete observations are INDETERMINATE, never absence or PASS.
5. **TEST-05 Deterministic concurrency:** materialize bounded schedules and barriers; bind attempts/events to causal order; replay the schedule without relying on timing sleeps.
6. **TEST-06 Provenance:** bind exact source SHA, contract/catalogue digests, manifest, principal/process, operations, resources, observations, verdicts and artifact bytes into an append-only verifiable chain.
7. **TEST-07 Cleanup containment:** first prove synthetic inventory and protected-root exclusion. Cleanup remains absent from the ordinary runner/adapters. Any future destructive capability is a separate, separately authorized subsystem and is not part of this implementation sequence.

### Dependency and stop rules

- TEST-01/02 cannot establish meaningful lifecycle results without TEST-03 isolation and TEST-04 independent observation.
- TEST-05 applies to vectors whose normative scenario specifies concurrency, interleaving, replay, retry or ambiguous acknowledgement; C.14's explicit N/A decisions remain limited to vectors whose source scenario does not specify those conditions.
- TEST-06 is required for every claimed result; a workflow log or uploaded artifact alone is insufficient.
- TEST-07 must not grant deletion authority. Protected or unknown resources remain ineligible.
- Any missing identity, incomplete inventory, ambiguous outcome, unverified isolation, principal overlap, failed oracle read, provenance gap or scope mismatch causes fail-closed BLOCKED/INDETERMINATE; no fallback to PASS.

## 4. D.3 — Minimum permission and evidence-destination design

No permission change is requested or performed. The following is a future design target to validate against effective GitHub Actions and repository settings before a separate implementation approval.

| Principal / component | Minimum intended capability | Explicit exclusions |
|---|---|---|
| Workflow runner / executor | Read frozen source/spec; write only run-scoped synthetic namespace and run-scoped result staging | No repository administration, secrets enumeration, production/T0/T1/DB/provider access, protected-root write, cleanup/delete, or evidence-store mutation |
| Synthetic adapter | Only declared operations on exact run/namespace/resource versions | No arbitrary path, network egress, cross-run access, provider credentials or implicit cascade |
| Independent observer | Read-only access to exact synthetic namespace and protected-root invariants | No executor credential sharing; no mutation or cleanup |
| Oracle/evaluator | Read frozen expected-state package and observer records; append verdict | No executor-controlled expected-state rewrite or resource mutation |
| Evidence publisher | Append immutable, run-bound artifacts to a dedicated approved destination | No overwrite/delete/retention-policy administration |
| Owner/controller | Approve exact scope and stop/abort; record decision | Approval cannot be inferred from workflow configuration or prior stage approval |

### Permission validation requirements

- Begin from deny-by-default; explicitly enumerate repository contents, Actions, environment, OIDC, artifact and external destination capabilities.
- Distinguish configured workflow permissions from effective token/principal capabilities at runtime.
- Do not request broad Administration, secrets, write-all, or provider access to resolve an evidence gap.
- The existing branch-protection read gap must remain visible as NOT VERIFIED until an independently approved read-only evidence route is available.
- No credential, token or secret value may be copied into the repository or evidence package.

### Evidence destination

Use the C.13 logical EvidenceDestinationIdentity contract. A concrete destination, owner, trust zone, effective access policy, append policy, retention/hold, inventory and recovery treatment remain unselected/unverified. Do not treat the current repository path or Actions artifact as an approved immutable evidence store without verifying those properties.

## 5. D.4 — Draft TEST-08 execution authorization package (NOT GRANTED)

TEST-08 requires a separate owner decision that binds, at minimum:

1. Exact source commit SHA and immutable catalogue/specification digests.
2. Exact vector IDs selected from the 87-vector denominator, with an explicit reason for every excluded vector; no silent denominator reduction.
3. Exact runner/workflow identity and immutable workflow/source revision.
4. Exact synthetic adapter set, fixture digests and resource types.
5. Exact isolated namespace and resource boundary; proof that production, T0/T1, databases, ledgers, backups, replicas, exports and external recipients are unreachable and excluded.
6. Exact network policy, filesystem/mount boundary and effective principal/capability evidence.
7. Exact independent observer/oracle identities and frozen expected-state package.
8. Exact evidence destination identity, append-only policy, retention/hold and recovery treatment.
9. Maximum run count, retry policy, concurrency schedule bounds and artifact size/resource limits.
10. Explicit abort conditions, stop authority and treatment of partial/ambiguous outcomes.
11. Explicit statement that the authorization is synthetic-only and does not grant cleanup, deletion, archive, expiry, compaction, vacuum, overwrite or any other destructive operation.

No exact vector subset, run count, runner identity, destination provider or effective isolation proof is approved by Stage D.4. The list above is the required content of a future request, not a completed authorization. TEST-08 remains **NOT GRANTED**.

### Destructive authority is separate

Even a future TEST-08 approval does not grant destructive authority. Option C remains active. Any destructive action would require a separate exact target manifest, operation, exclusions, pre/post observations, independent verification and explicit owner approval. No such action is proposed or enabled here.

## 6. D.5 — Owner decision and disposition

| Decision | Disposition |
|---|---|
| Stage D.0–D.5 documentary preparation | APPROVED and completed within scope |
| Implement TEST-01–07 | NOT AUTHORIZED |
| Execute any lifecycle test / dispatch Actions | NOT AUTHORIZED; TEST-08 NOT GRANTED |
| Change GitHub permissions or branch protection | NOT AUTHORIZED |
| Access secrets, VPS, T0/T1, DB, providers or production runtime | NOT AUTHORIZED |
| Provision external infrastructure or select provider | NOT AUTHORIZED |
| Cleanup, archive, expiry, deletion, compaction, vacuum or overwrite | NOT AUTHORIZED; Option C ACTIVE |
| Live trading / real orders | PROHIBITED; AI execution remains disabled |

### Stage D disposition

**DOCUMENTARY READINESS PACKAGE COMPLETE. IMPLEMENTATION READINESS: BLOCKED. TEST-08: NOT GRANTED. LDA-06: PARTIAL / NOT VERIFIED. LDA-08: HOLD / NOT VERIFIED. LDA-07: 87/87 NOT RUN. OPTION C: ACTIVE.**

The next permissible step is a new, separately scoped owner decision on whether to prepare a bounded implementation proposal. No technical implementation or execution begins automatically from Stage D completion.

## 7. Evidence and verification record

- Source branch at start: feature/t0-centralized-data-feeder-p1-20261101.
- Source branch HEAD at start: `d2b52e459f284dabb2e84c49a8d8b9cd14d6d059`.
- Canonical Stage C.15 report blob: `7c7e49b722d4808c764b4a262b5ec7c79dd48b13`.
- Canonical Stage C.14 matrix blob: `12bba6c475fc2ad8c4e2246e75034ede22d3bc20`.
- Canonical Stage C.13 map blob: `c43c8bfbccaf698d6670f33fab66ee12d2072a7f`.
- Verification performed: GitHub read-only fetch/read of branch reference, handoff and canonical C.13–C.15 records.
- Tests/compile/dry-run/fault injection/Actions dispatch: NOT RUN.
- Workflow run/artifact: NONE for this documentary work.
- Runtime/provider/permission/secret/VPS/database probes: NOT PERFORMED.
- Code/schema/workflow/permission/runtime/data changes: NONE.
- Destructive operations: NONE.
