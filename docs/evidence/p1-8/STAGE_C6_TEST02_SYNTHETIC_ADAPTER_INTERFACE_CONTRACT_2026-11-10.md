# Stage C.6 — TEST-02 Synthetic Adapter Interface Contract

Date: 2026-11-10  
Repository: kenznguyen/btcusdt-telegram-signals2  
Branch: feature/t0-centralized-data-feeder-p1-20261101  
Work type: documentation-only interface contract  
Predecessors: Stage C.4 prerequisite closure plan; Stage C.5 TEST-01 lifecycle runner contract  
Scope: TEST-02 only; no implementation or execution

## 1. Purpose and authority boundary

Define a technology-neutral, synthetic-only adapter boundary for a future lifecycle negative-vector harness. The contract specifies interfaces, identity, capability, error, idempotency, transaction and evidence semantics. It does not select a language, framework, database, object-store product, workflow, container image or implementation.

Stage C approval covers this bounded documentary work. It does not authorize code changes, adapter implementation, tests, compile, dry-run, fault injection, GitHub Actions dispatch, secrets or permission access, runtime/VPS/database/provider/network probes, or data mutation. TEST-08 remains a separate exact-scope authorization gate.

Option C remains active. No deletion, archive, cleanup, expiry, compaction, vacuum, backup/replica removal, export mutation or irreversible transition is authorized. T0 canonical data and recovery copies, CORE_LEDGER, AI_LEDGER, required T3 reconstruction/audit evidence, governance history and unknown/unclassified objects remain protected.

## 2. Contract principles

1. **Synthetic-only by construction:** every adapter instance is bound to one immutable run namespace and run ID.
2. **Explicit capability:** an adapter exposes only named operations; no generic execute, arbitrary path, raw connection, delete or cleanup method is part of this contract.
3. **No backend discovery or fallback:** backend selection is explicit and allowlisted in the frozen manifest. Unknown, missing or production-like backends fail before opening a resource.
4. **Exact identity:** object identity includes namespace, logical key, immutable version and content digest. A mutable key alone is never sufficient.
5. **Fail closed:** ambiguity, stale identity, missing inventory, conflicting metadata, unknown state or partial commit returns a typed non-success result.
6. **Independent evidence:** adapter audit events are append-only from the adapter's perspective; the independent oracle does not trust executor-supplied state as its sole truth.
7. **No ambient authority:** no secrets, network, production credentials, host paths, mounts, environment-based connection discovery or implicit cloud identity.
8. **No destructive capability:** TEST-02 adapters do not expose delete, expire, purge, compact, vacuum, overwrite, restore-over-existing or cleanup operations. TEST-07 is a separate design gate.

## 3. Common type and identity model

The following are conceptual, language-neutral types. An implementation must freeze a strict schema and canonical serialization before execution.

| Type | Required semantics |
|---|---|
| RunIdentity | Immutable run_id, namespace_id, manifest_digest and source_commit |
| NamespaceIdentity | Unique synthetic namespace bound to exactly one RunIdentity; never inferred from a path prefix alone |
| ObjectIdentity | namespace_id, logical_key, immutable version_id, content_digest, byte_length and media/type declaration |
| RegistryRecord | ObjectIdentity plus record_schema_version, creation event reference and declared lifecycle state |
| HoldIdentity | hold_id, subject ObjectIdentity or explicitly defined scope, policy_version and immutable authorization reference |
| CopyIdentity | copy_id, source ObjectIdentity, destination ObjectIdentity, lineage event and verification state |
| CheckpointIdentity | checkpoint_id, manifest_digest, watermark and immutable seal/commit evidence references |
| EventIdentity | event_id, aggregate identity, monotonic sequence, event_type, canonical payload digest and prior-event linkage where required |
| CapabilitySet | Explicit operation names and resource namespace; no wildcard or implicit escalation |
| Result | Typed success or typed failure; never ambiguous null/boolean-only success |

All IDs must be non-empty, canonical and validated. Cross-run references, namespace mismatch, version substitution, digest mismatch, duplicate immutable IDs or non-canonical serialization are rejected. No adapter may resolve an ObjectIdentity by silently selecting “latest”.

## 4. Adapter interfaces

### 4.1 Synthetic object-store adapter

**Purpose:** model immutable synthetic object versions and controlled reads/writes without touching a real object store.

Allowed operations:

- `put_new(namespace, logical_key, expected_digest, bytes, idempotency_key) -> ObjectIdentity`
- `get_exact(ObjectIdentity) -> ObjectBytes + observed_digest`
- `head_exact(ObjectIdentity) -> ObjectMetadata`
- `list_namespace(namespace, continuation_token) -> bounded page of ObjectIdentity`

Requirements:

- `put_new` is create-only; an existing key/version conflict is a typed conflict, never overwrite.
- The adapter computes the digest itself and compares it with the declared digest before acknowledging.
- `get_exact` and `head_exact` require the complete immutable identity; no latest-version lookup.
- Listing is namespace-scoped, bounded, deterministic and snapshot-consistent or explicitly marked non-snapshot with a consistency token.
- No delete, overwrite, lifecycle expiry, retention shortening, restore-overwrite or arbitrary bucket/path operation exists.
- An interrupted write returns UNKNOWN/INDETERMINATE unless a subsequent exact read proves the committed immutable identity and digest.

### 4.2 Metadata registry adapter

**Purpose:** maintain synthetic object metadata, exact version binding and lifecycle-state projections.

Allowed operations:

- `register_created(ObjectIdentity, creation_event) -> RegistryRecord`
- `get_exact(ObjectIdentity) -> RegistryRecord`
- `compare_and_transition(ObjectIdentity, expected_state, expected_revision, new_state, event_id) -> RegistryRecord`
- `list_by_namespace(namespace, bounded_filter, continuation_token) -> page`

Requirements:

- Registry identity is keyed by namespace + logical key + immutable version, not logical key alone.
- State transitions use compare-and-swap semantics with a monotonically increasing revision.
- Duplicate event IDs are idempotent only when canonical payload digests match; same ID with different payload is a hard conflict.
- The registry is not authoritative for object bytes; byte integrity must be verified through the object-store adapter or independent oracle.
- No unversioned update, blind upsert, delete or cross-namespace query is allowed.
- Projection lag or inconsistent state is surfaced explicitly; it cannot be interpreted as absence or permission.

### 4.3 Hold and authorization-resolution adapter

**Purpose:** resolve whether a precisely identified synthetic object is subject to a hold and whether a separately recorded policy decision permits a specified non-destructive operation.

Allowed operations:

- `resolve_holds(ObjectIdentity, policy_version, as_of_profile) -> HoldResolution`
- `resolve_authorization(ObjectIdentity, operation, principal, authorization_ref) -> AuthorizationDecision`

Requirements:

- Hold resolution returns the complete matching hold set, policy version, evidence references and a deterministic decision: HELD, NOT_HELD or INDETERMINATE.
- Missing, stale, conflicting or untrusted hold inputs yield INDETERMINATE and deny the requested operation.
- Authorization is operation-specific, principal-specific, namespace-specific and version-specific; broad “admin” or wildcard authorization is invalid.
- The adapter cannot create, release or modify holds or grant authority. It only resolves preloaded synthetic policy fixtures.
- A NOT_HELD result is not itself authorization. Hold state and operation authorization are separate predicates.
- No production policy, legal hold system, identity provider or external authority is queried.

### 4.4 Copy-inventory and lineage adapter

**Purpose:** enumerate synthetic copies and prove their source/destination lineage.

Allowed operations:

- `record_copy(source_identity, destination_identity, copy_event, idempotency_key) -> CopyIdentity`
- `get_copy_exact(copy_id) -> CopyRecord`
- `enumerate_lineage(ObjectIdentity, bounded_depth, continuation_token) -> LineagePage`

Requirements:

- Every copy record binds exact source and destination versions and their content digests.
- A copy is not VERIFIED merely because a destination record exists; verification requires destination byte digest evidence.
- Missing, cyclic, ambiguous or cross-namespace lineage is surfaced as incomplete/invalid and blocks any completeness claim.
- Enumeration reports pagination completeness, observed revision/watermark and any gaps.
- No real backup, replica, recipient, export, cache, provider or restore destination is discovered or contacted.
- The adapter has no copy, move, replication, export or deletion side effect; it records synthetic fixture facts only.

### 4.5 Checkpoint, manifest and watermark adapter

**Purpose:** model immutable inventory snapshots and checkpoint boundaries for deterministic lifecycle scenarios.

Allowed operations:

- `create_manifest(namespace, frozen_object_set, inventory_revision, manifest_digest) -> ManifestIdentity`
- `seal_checkpoint(manifest_identity, watermark, schedule_id, seal_event) -> CheckpointIdentity`
- `get_checkpoint_exact(CheckpointIdentity) -> CheckpointRecord`
- `compare_checkpoint(expected_identity, observed_state) -> ComparisonResult`

Requirements:

- The manifest freezes the exact object-version set and inventory revision; no mutable selector such as “all current objects” may be reevaluated later.
- Watermark semantics use the separately approved contract; timestamps are typed with explicit clock profile and precision.
- Sealing is immutable and idempotent by checkpoint identity plus canonical payload digest.
- A retry after an ambiguous outcome must read the exact checkpoint identity before attempting any repeat; it must never create a second checkpoint under the same identity with different content.
- Missing inventory pages, unresolved lineage, clock uncertainty or digest mismatch blocks sealing.
- The adapter cannot advance production watermarks, alter real checkpoints or mutate source data.

### 4.6 Append-only audit/event-sink adapter

**Purpose:** preserve every synthetic adapter request, decision and outcome for independent reconstruction.

Allowed operations:

- `append_event(event, idempotency_key) -> EventReceipt`
- `read_events_exact(namespace, sequence_range) -> ordered events + completeness proof`
- `head(namespace) -> sequence + chain_digest`

Requirements:

- Events have canonical serialization, stable event IDs, sequence numbers and payload digests.
- Append is idempotent only for an identical event ID and identical canonical payload; a mismatch is a conflict.
- Event ordering and gap detection are explicit. A missing sequence, broken digest chain or unavailable receipt makes evidence incomplete.
- The sink is append-only to the adapter principal; no update, truncate, delete or rewrite operation exists.
- The executor cannot alter oracle records or use the event sink to certify its own correctness.
- Audit-write failure prevents the operation from being reported as PASS, even if the simulated state change appears successful.

### 4.7 Namespace and capability resolver

**Purpose:** provide the sole binding between a run manifest, a synthetic namespace and the adapter capabilities granted to that run.

Allowed operations:

- `resolve_run(manifest_digest, run_id) -> RunIdentity`
- `resolve_namespace(RunIdentity) -> NamespaceIdentity`
- `authorize_capability(RunIdentity, adapter_id, operation, resource_identity) -> CapabilityDecision`

Requirements:

- The resolver accepts only an explicit allowlist of synthetic adapter IDs and versions from the frozen manifest.
- Namespace identity is created before fixture setup and is immutable for the run.
- Resource access must match exact namespace and adapter capability; path-prefix checks alone are insufficient.
- Unknown adapter, operation, resource type, namespace or manifest field is denied.
- No environment-variable, filesystem, DNS, URL, cloud metadata or credential-based backend discovery is permitted.
- Capability resolution is not a user/production authorization service and cannot grant TEST-08 execution authority.

## 5. Shared operation envelope and error model

Every adapter request must carry:

- RunIdentity and NamespaceIdentity;
- adapter_id and adapter_version;
- operation name and schema version;
- exact resource identity or explicitly bounded query;
- idempotency key where a mutation-like synthetic record operation exists;
- expected revision/digest where concurrency or immutability applies;
- deterministic clock/schedule context where relevant;
- correlation/event ID.

Every response must carry a typed outcome, adapter identity/version, request digest, observed revision or sequence, evidence/event references and a machine-readable reason.

Minimum error classes:

| Error | Required behavior |
|---|---|
| INVALID_INPUT / UNKNOWN_FIELD | Reject before resource access |
| UNKNOWN_ADAPTER / UNKNOWN_BACKEND | Deny; no discovery or fallback |
| NAMESPACE_MISMATCH / CROSS_RUN_REFERENCE | Deny and emit a security-relevant audit event where possible |
| NOT_FOUND | Exact identity absent; never substitute another version |
| VERSION_CONFLICT / REVISION_CONFLICT | Preserve existing state; return conflict |
| DIGEST_MISMATCH | Fail closed; mark evidence invalid |
| HOLD / AUTHORIZATION_DENIED | Deny requested operation |
| INDETERMINATE_POLICY | Deny and preserve unresolved evidence |
| INCOMPLETE_INVENTORY / LINEAGE_GAP | Block completeness or checkpoint claims |
| IDEMPOTENCY_CONFLICT | Reject same key with different payload |
| AUDIT_UNAVAILABLE | Do not report PASS |
| TIME_UNTRUSTED / SCHEDULE_MISMATCH | Block time-dependent assertion |
| ADAPTER_UNAVAILABLE / INTERNAL_ERROR | BLOCKED or INDETERMINATE, never success |

No adapter may catch an unknown error and return success, empty results, default authorization or a guessed state.

## 6. Idempotency, transaction and fencing semantics

- Every state-changing synthetic record operation has a caller-supplied idempotency key and canonical request digest.
- Repeating the same key and digest returns the original semantic result and receipt; same key with a different digest returns IDEMPOTENCY_CONFLICT.
- Object creation is immutable create-only. Registry transitions require expected revision and compare-and-swap.
- Where a logical operation spans object storage, registry and audit sink, the contract does not assume a distributed transaction. It requires an explicit operation state machine, durable intent/event evidence, reconciliation after ambiguous outcomes and no false atomicity claim.
- A partial commit is surfaced as PARTIAL/INDETERMINATE and must be reconciled by exact identities; no compensating deletion is allowed.
- Fencing tokens or monotonically increasing ownership epochs are required for concurrent writers to a namespace/aggregate. Stale epochs are rejected.
- The independent oracle observes final object bytes, registry revisions, lineage and audit chain independently; adapter self-reports alone are insufficient.
- Timeouts do not imply rollback. The caller must resolve the exact operation identity and receipt before retrying.

## 7. Synthetic namespace and resource containment

The adapter boundary must reject:

- production-like URI schemes, hostnames, account/project identifiers and known canonical paths;
- T0/T1/T2/T3/T4 resource identities, VPS paths, real ledger identifiers, backup/replica locations and external recipient references;
- symlinks, path traversal, mount escapes, aliases and namespace collisions;
- unbounded listing, wildcard resource selectors and arbitrary query expressions;
- injected credentials, ambient cloud identity and outbound network access.

A synthetic marker alone is insufficient. Containment requires the conjunction of immutable run-bound namespace identity, explicit capability allowlist, isolated resource root and independent observation. If any element is missing, the harness is BLOCKED before adapter use.

This contract defines logical boundaries only. It does not prove OS/container/network/filesystem isolation; TEST-03 remains OPEN and must establish that independently before any implementation can be exercised.

## 8. Oracle, provenance and evidence obligations

- TEST-04 must define an independent oracle outside the executor's mutable state and trust boundary. TEST-02 interfaces do not provide that proof.
- TEST-06 must bind adapter contract version, adapter implementation/build digest, manifest, source commit, fixture digest, oracle identity, run ID, per-vector outcomes and artifact digests.
- Every adapter operation emits an auditable request/outcome record or causes the scenario to become BLOCKED/INDETERMINATE.
- Evidence is append-preserving; retries and later attempts create distinct attempt records.
- The run must preserve denied operations, conflicts, partial outcomes and audit failures, not only successful calls.
- No generic attestation workflow is selected or authorized by this contract.

## 9. Adapter acceptance matrix for future TEST-02 implementation

| ID | Required negative/positive assertion | Minimum evidence |
|---|---|---|
| ADP-01 | Unknown adapter/backend rejected before opening any resource | Denial result + proof no resource access occurred |
| ADP-02 | Production URI/path/resource identity rejected | Exact rejected identity + isolation observation |
| ADP-03 | Cross-run and cross-namespace reference rejected | Namespace/run binding evidence |
| ADP-04 | Exact object version required; no latest-version substitution | Two-version fixture and exact-read trace |
| ADP-05 | Create-only object write cannot overwrite | Existing-object digest unchanged |
| ADP-06 | Digest mismatch blocks acknowledgement | Expected/observed digest and failure event |
| ADP-07 | Registry CAS rejects stale revision | Before/after revision and conflict event |
| ADP-08 | Duplicate idempotency key with same payload is stable | Same semantic receipt and single logical event |
| ADP-09 | Duplicate idempotency key with changed payload conflicts | Conflict event; original state unchanged |
| ADP-10 | Hold uncertainty and missing authorization deny | Decision inputs and fail-closed result |
| ADP-11 | NOT_HELD does not imply operation authorization | Separate hold and authorization decisions |
| ADP-12 | Incomplete/cyclic/cross-namespace lineage blocks completeness | Lineage gap/cycle evidence |
| ADP-13 | Incomplete inventory or watermark uncertainty blocks checkpoint seal | Frozen manifest and blocked seal evidence |
| ADP-14 | Audit sink failure prevents PASS | Missing receipt and run-level blocked outcome |
| ADP-15 | Event sequence gap or chain mismatch is detected | Independent event-chain verification |
| ADP-16 | Partial multi-adapter commit is not represented as atomic success | Operation state and reconciliation trace |
| ADP-17 | Stale fencing epoch is rejected | Competing epoch trace |
| ADP-18 | Unbounded listing/arbitrary selector rejected | Bounded-query validation evidence |
| ADP-19 | Adapter has no destructive/cleanup capability | Interface/capability inspection and denied-operation evidence |
| ADP-20 | Adapter cannot reach oracle state or alter oracle evidence | Principal/process separation proof (TEST-04 dependency) |

These assertions are proposed contract requirements, not executed tests and not coverage credit for any of the 87 lifecycle vectors.

## 10. Dependency and closure conditions

TEST-02 cannot be marked CLOSED based on this document alone. Closure requires:

1. Frozen schemas and canonical serialization for all shared types.
2. Versioned interface definitions for every required adapter.
3. Explicit adapter registry and capability allowlist with no fallback.
4. Synthetic-only implementation bound to immutable run namespaces.
5. Positive and negative adapter tests mapped to exact TEST-02 assertions.
6. Independent observation of object bytes, metadata revisions, lineage and audit events.
7. Proof that destructive/cleanup operations are absent from adapter capabilities.
8. TEST-03 isolation proof before execution.
9. TEST-04 independent-oracle design and proof before claiming oracle-backed PASS.
10. TEST-06 lifecycle-specific provenance before attesting results.
11. TEST-07 separate cleanup-containment design; no cleanup capability is added here.
12. TEST-08 separate exact-scope owner authorization before any execution.

TEST-03, TEST-04, TEST-05 and TEST-07 remain independent prerequisite workstreams. TEST-02 must not weaken or absorb their gates.

## 11. Current disposition

| Item | Status |
|---|---|
| TEST-01 | CONTRACT DOCUMENTED / IMPLEMENTATION NOT ESTABLISHED |
| TEST-02 | CONTRACT DOCUMENTED / IMPLEMENTATION NOT ESTABLISHED |
| TEST-03 | OPEN / NOT ESTABLISHED |
| TEST-04 | OPEN / NOT ESTABLISHED |
| TEST-05 | OPEN / NOT ESTABLISHED |
| TEST-06 | PARTIAL / NOT ESTABLISHED |
| TEST-07 | OPEN / NOT ESTABLISHED |
| TEST-08 | NOT GRANTED — separate exact-scope authorization required |
| LDA-07 | NOT RUN; 87/87 lifecycle vectors remain NOT RUN |
| LDA-06 | PARTIAL / NOT VERIFIED |
| LDA-08 | HOLD / NOT VERIFIED |

No tests, compile, dry-run, fault injection or Actions dispatch were performed. No secrets, permissions, runtime, VPS, database, provider, recipient, backup or replica were accessed. No source, schema, adapter, workflow, runner, permission, runtime or data changes were made. No destructive operation was performed.

**STAGE C.6 DOCUMENTARY CONTRACT COMPLETE — TEST-02 NOT CLOSED — NO IMPLEMENTATION OR EXECUTION AUTHORITY.**
