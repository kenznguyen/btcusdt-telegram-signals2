# ADR-002 — Android Canonical Host Package with Authenticated IPC

## Status

**ACCEPTED — OWNER DECISION RECORDED.** Accepted on 2026-11-03. This is an architecture decision only; implementation and runtime activation are not authorized.

## Date

2026-11-03

## Context

The owner-selected T0 topology is Android-hosted canonical SQLite, with T0 Market Data and Paper Ledger in one shared physical database file. The Android application currently has a regular variant and a parallel `.paper` variant with distinct application IDs.

Android app-private storage is sandboxed by application identity. Two packages cannot assume that identically named files in their respective private directories are one physical SQLite database. Nor should a database path or raw database handle be exposed to another package.

P5.4.37 source trace found no implemented Android canonical database path authority, composition root or local T0/Paper persistence integration. P5.4.38 defined three packaging options and required one package/process to own the database and sole canonical writer.

## Decision

Choose **Option B — Dedicated canonical host package plus authenticated IPC client**.

1. Exactly one designated Android package/process is the canonical host and sole owner of the Android canonical SQLite file.
2. The host owns canonical path resolution, DB identity, schema/migration authority, transaction coordination, lease/fencing authority, recovery/readiness gates and all canonical write capabilities.
3. The separately installed `.paper` package is a client. It must not resolve or open the canonical DB path, receive a raw SQLite handle/file descriptor, create a local shadow canonical DB, hold writer credentials or obtain lease/fencing authority.
4. The client accesses permitted local canonical operations only through a narrowly scoped, authenticated IPC boundary hosted by the canonical package.
5. IPC authorization must enforce caller identity/package and signing-certificate trust, with explicit allowlisting and versioned typed contracts. Signature-level Android permissions should be used where supported by the selected IPC mechanism. Authentication and authorization failures fail closed.
6. IPC exposes typed domain commands and read-only projections, never arbitrary SQL, raw paths, database handles or general-purpose write access.
7. All accepted Paper intents, whether from Strategy Core or the independent AI strategy, pass through the same host-side Shared Risk Engine and Kill Switch before any paper-ledger transition. IPC cannot bypass those controls.
8. If the host is unavailable, the client reports canonical operations unavailable. It must not fall back to a second local database, an alternate writer or an unapproved remote route.
9. The PC remains a read-only research/backtest consumer and does not become a canonical writer.
10. Runtime activation remains separately gated by explicit approval after implementation and fixture/device acceptance.

## Consequences

### Positive

- Preserves the one-physical-file Android topology despite distinct app package IDs.
- Keeps database identity, migrations, writer lease and risk controls inside one security/process boundary.
- Allows the parallel `.paper` package to remain separately installable without pretending its app-private storage is shared.
- Creates a narrow, auditable interface between UI client and canonical data owner.

### Costs and constraints

- Host installation and lifecycle become prerequisites for client-side local canonical operations.
- IPC introduces caller authentication, authorization, contract versioning, process-death/reconnect and denial-of-service considerations.
- Host process death or upgrade must fail closed; the client cannot independently recover or become writer.
- Requires explicit compatibility policy for client/host version skew and a threat model for exported IPC surfaces.

## Alternatives Considered

### Option A — Same application ID for local variants

Rejected for this decision because it would give up the current separately installable package identity/side-by-side behavior that the parallel variant provides.

### Option C — Keep the `.paper` package remote-API-only

Rejected because the selected architecture needs a defined local access path to the Android-hosted canonical services for the parallel client. Remote API remains a separate capability only if explicitly designed and approved; it is not the selected canonical access boundary.

### Two independent package-private SQLite files

Rejected. They are separate physical files and would create competing state, ambiguous ownership and unsafe reconciliation.

## Open implementation decisions

This ADR does not select:
- the exact canonical host package/application ID or which current variant will become the host;
- whether IPC is implemented as a bound service, ContentProvider or another Android-supported mechanism;
- exact signature permission declaration, exported component configuration and caller allowlist representation;
- Kotlin interface names, serialization format, API version negotiation or timeout/retry policy;
- database path, filename, SQLite driver, schema/migration implementation or process model;
- backup/restore, recovery epoch, retention or production activation procedure.

These must be resolved in implementation design and security review without weakening the accepted one-host/one-writer boundary.

## Security and lifecycle invariants

- No client receives raw DB paths, file descriptors, DB connections, SQL access, lease tokens or writer credentials.
- Every mutating IPC method is a typed, idempotent domain command and is re-authorized by the host at execution time.
- Host checks readiness, current fencing generation, recovery state and Kill Switch before canonical mutation.
- Caller identity is verified by the host, not trusted from a caller-supplied package-name string.
- Client process restart/reconnect cannot create a second host or writer.
- Unknown caller, revoked signature, incompatible contract, stale fencing, host-not-ready or uncertain transaction outcome fails closed.
- Strategy Core and independent AI remain separate signal sources but share the same host-side risk and paper acceptance path.
- `AI_EXECUTION_ENABLED=false`; no live orders or real exchange execution.

## Verification and limits

P5.4.39 records the owner's explicit choice and reconciles it with P5.4.38. This ADR does not prove an IPC implementation exists or works.

**PASS** — owner decision and architecture constraints recorded.

**NOT VERIFIED** — host package identity, IPC mechanism/security configuration, implementation, process lifecycle, device behavior and integration tests.

**NOT AUTHORIZED** — code changes, dependency installation, applicationId changes, IPC component creation/export, DB creation/opening/path probing, device or instrumentation tests, Feeder startup, exchange connection, market-data sync, backup/restore or live execution.

No tests or GitHub Actions workflows were run. Documentation-only. `AI_EXECUTION_ENABLED=false`.

## Follow-up

P5.4.40 should produce an implementation-ready IPC threat model and contract specification: caller identity, signature trust, permission boundary, typed read/command surface, versioning, idempotency, host death/reconnect and fail-closed behavior. It must not implement runtime components until a separate explicit authorization.


## Owner decision addendum — P5.4.41 (2026-11-04)

The owner explicitly approved the following implementation-design decisions:

1. **IPC primitive:** Android Bound Service using explicit component binding and a narrow typed Binder/AIDL contract. Require a custom signature-level bind permission and host-side caller UID/package/installed-signer verification on every call.
2. **Canonical host variant:** the existing Android `regular` variant is the canonical host. The `.paper` variant is the separately installed IPC client and must not own/open a second canonical database.
3. **Signing relationship:** host and `.paper` client use the same controlled installed signing identity. The host must still pin the exact expected client package and approved signer/lineage; same-signer permission is not a substitute for package/operation authorization.

These decisions resolve the corresponding owner gates from P5.4.41. They do **not** establish the exact application IDs, installed certificate digest, key custody/rotation details, or prove the existing build variants actually use the approved installed signer. Those require source/release evidence before implementation.

The P5.4.42 design must retain one-host/one-writer ownership, no raw DB capability across IPC, host-side idempotency/risk/fencing enforcement, fail-closed behavior, and paper-only operation. Runtime implementation and activation remain separately unauthorized.
