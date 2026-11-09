# Stage B.4 — RET-10 Adapter and Separate Verifier Qualification Contract

Date: 2026-11-10  
Type: documentary qualification contract; no implementation or qualification

## 1. Objective

Define evidence required before a lifecycle adapter can be trusted to enforce exact-object, policy, authorization, hold, time, checkpoint and mutation preconditions. Define the verifier boundary. No backend, provider, database, transaction primitive, cryptographic algorithm, credential model or deployment topology is selected.

## 2. Adapter capability declaration

A candidate adapter MUST publish a versioned declaration containing adapter name/version/build digest and source provenance; exact backend/provider/product/version and endpoint/region/failure-domain identity where applicable; supported object classes and operations; explicit read/write capabilities and default-deny forbidden operations; object identity/generation/digest semantics; transaction/isolation/linearization guarantees and limits; compare-and-set/fencing primitive and stale-writer behavior; durability/ACK and read-after-write semantics; retry, idempotency, timeout, cancellation and partial-failure semantics; cascade/archive/delete behavior; error taxonomy; required credentials/permissions; and recovery/reconciliation behavior.

Undocumented or unsupported capability is UNKNOWN, not assumed supported.

## 3. Read-only and mutation boundary

Read-only inspection and mutation capabilities are separate and explicit. Qualification of read-only behavior does not qualify mutation behavior. A mutation request binds exact object ID/class/generation/digest, policy revision, authorization, hold/dependency revision, trusted-time/revocation evidence, checkpoint/seal generation, restore epoch, idempotency identity and audit intent.

Wildcard, alias, query-time expansion, mutable predicates and implicit cascades are rejected. The adapter must not widen a frozen manifest silently.

## 4. Technical verifier separation

The verifier is technically separated from the executor/adapter path across principal and credentials, process/runtime and deployment lifecycle, writable storage path and mutation API, failure domain/control plane where feasible, evidence acquisition/readback path, and source of expected state/oracle.

The verifier is read-only, independently obtains exact object state and immutable evidence, and cannot reuse executor credentials or trust only executor logs/responses. Shared source code alone does not prove independence; distinct process labels without distinct authority/failure paths do not prove separation. Required separation dimensions and evidence must be frozen for the candidate environment before qualification.

## 5. Deterministic verification contract

Input is a closed, versioned manifest of exact objects, revisions, expected operations and evidence requirements. Output contains manifest ID/digest and policy/authorization revisions; adapter/backend identity and operation identity; per-object observed state/version/digest/evidence references; expected-versus-observed comparison; verifier identity/build and evidence-source identities; deterministic reason codes and terminal result; unresolved/unknown residuals; canonical output digest and provenance.

Repeated verification over identical frozen inputs and observations yields identical canonical output. Missing, extra, stale, conflicting or unreadable evidence yields NOT_VERIFIED, not PASS. The verifier identifies out-of-scope changes, residual references, backups/replicas/exports and unknown copies within the declared boundary.

## 6. Qualification matrix

Qualification requires separately evidenced: contract conformance/capability truth; exact object/version binding; read-only behavior and denied write attempts; transaction/concurrency ordering; idempotency/retry; crash/lost-response; partial failure/reconciliation; no-cascade/no-scope-expansion; permission/credential separation; verifier readback/independent oracle; deterministic replay/artifact provenance; restore epoch/fencing interaction.

Every result is tied to exact adapter/backend version, fixture digest, runner, environment and evidence artifact. A generic unit test or synthetic reference model does not qualify a production adapter.

## 7. Fail-closed outcomes

Unknown backend semantics, unsupported operation, stale revision, unavailable verifier, shared mutation credentials, missing independent oracle, inconsistent readback, lost fence, unknown side effect or incomplete evidence MUST stop further operations and produce BLOCKED, RECONCILIATION_REQUIRED or NOT_VERIFIED. No batch success is emitted while any object outcome is unknown.

## 8. Dependencies and status

V07 supplies time/revocation evidence; V08 supplies checkpoint/seal commit semantics; RET-05/LDA-05 uses adapter capabilities to bind mutation preconditions; Restore requires a separate read-only oracle and backend recovery semantics.

**Status: DOCUMENTARY CONTRACT COMPLETE; RET-10 OPEN / NOT QUALIFIED / NOT VERIFIED.** Technical verifier separation remains mandatory despite the owner waiver of independent human review. No adapter/backend selected, installed, configured or tested.
