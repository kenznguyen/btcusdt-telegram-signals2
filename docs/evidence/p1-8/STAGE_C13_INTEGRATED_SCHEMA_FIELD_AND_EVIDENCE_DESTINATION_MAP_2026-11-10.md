# Stage C.13 — Integrated TEST-01–07 Schema/Field and Evidence-Destination Contract Map

Date: 2026-11-10
Repository: kenznguyen/btcusdt-telegram-signals2
Branch: feature/t0-centralized-data-feeder-p1-20261101
Work type: documentation-only logical schema/field mapping; no schema or implementation changes.
Predecessors: Stage C.4 prerequisite plan; Stage C.5–C.11 contracts; Stage C.12 cross-contract review.
C.12 input: report blob 2205caf4c177fa036eafd26ec65569a3c40e0aaf; C.12-F01 and C.12-F03.

## 1. Purpose and authority boundary

Resolve the documentary integration gaps concerning:
- one shared logical field map across the runner manifest, adapters, schedule, independent oracle, provenance and cleanup-containment plan;
- immutable evidence-destination identity, trust boundary, append-only publication and retention semantics.

This document defines a technology-neutral logical contract map. It does not create executable schemas, migrations, code, adapters, workflow configuration, storage, credentials, provider accounts or permissions. It does not select JSON/CBOR/Protobuf/Avro or another serialization; digest/signature algorithm; object store/database; attestation provider; timestamp authority; key-management system; or retention product.

No tests, compile, dry-run, Actions dispatch, runtime/provider probe, provisioning, data mutation or destructive operation is authorized or performed. TEST-08 remains NOT GRANTED. Option C remains active; evidence is not eligible for cleanup under this contract.

## 2. Logical contract profile

Proposed documentation profile name: `LIFECYCLE_EVIDENCE_CHAIN_V1`.

This is a logical field registry, not an implemented schema version. The profile has four rules:
1. One immutable run manifest is the root binding for a run.
2. Every downstream record references the root run/namespace and the exact upstream immutable IDs/digests it consumes.
3. A record may add facts but cannot rewrite or silently replace an upstream record.
4. Missing, ambiguous, mismatched or unsupported required fields fail closed; unknown records do not disappear from the denominator.

### 2.1 Common envelope

Every persisted provenance/evidence record uses the following conceptual common envelope:

| Field | Logical type | Required | Semantics |
|---|---|---:|---|
| schema_id | immutable identifier | yes | Logical record schema name |
| schema_version | version identifier | yes | Exact supported version |
| record_type | enumerated identifier | yes | Manifest, operation, event, observation, verdict, artifact, publication, correction or verification |
| record_id | immutable identifier | yes | Unique within declared global/run scope |
| repository_id | immutable identifier | yes | Canonical repository identity, not display text |
| source_commit_sha | full commit SHA | yes | Immutable source revision |
| run_id | immutable identifier | yes | Root run identity |
| namespace_id | immutable identifier | yes | Exact synthetic isolation boundary |
| manifest_digest | digest reference | yes | Canonical frozen manifest bytes |
| created_sequence | monotonic sequence | yes | Append order within declared record stream |
| recorded_time | structured time claim | conditional | Only with explicit clock source, precision and uncertainty |
| payload_digest | digest reference | yes | Digest of canonical payload bytes |
| previous_record_ref | immutable reference | conditional | Prior record in a defined append chain |
| correction_refs | immutable reference list | no | Append-only supersession/retraction references |
| producer_principal_ref | immutable reference | yes | Effective identity record |
| producer_process_ref | immutable reference | yes | Process/job identity record |
| validation_profile_ref | immutable reference | yes | Applicable verifier/policy profile |

A digest reference is logically an algorithm identifier plus digest bytes; the actual algorithm and encoding remain unselected. Canonicalization must distinguish absent from null, preserve exact numeric semantics, define text/byte encoding, key order, timestamp representation and collection order. A schema cannot be accepted until its canonicalization profile is versioned.

## 3. Root manifest field map (TEST-01)

| Logical field | TEST-01 source | Downstream consumers | Cardinality / rule |
|---|---|---|---|
| run_id | manifest | every record | Exactly one immutable value per run |
| namespace_id | manifest | adapters, observations, cleanup plan | Exactly one; bound to run_id |
| source_commit_sha | manifest | runner, adapter build, oracle, verifier, artifacts | Exactly one full SHA |
| catalogue_digest | manifest | vector map, per-vector results, aggregation | One frozen catalogue version/digest |
| selected_vector_ids | manifest | test-case map, schedule, oracle, coverage report | Unique explicit subset; denominator preserved |
| test_case_map | manifest | runner, assertion records | Exactly one case/version per selected vector |
| spec_refs/digests | manifest | expected-state package, oracle, provenance | Exact immutable versions and digests |
| fixture_digest | manifest | adapter/resource lineage, evidence | Frozen before execution |
| runner_identity | manifest | executor/process provenance | Exact build/toolchain identity |
| adapter_set | manifest | operation/resource records | Explicit allowlist and versions |
| oracle_identity | manifest | observation/verdict provenance | Exact evaluator/observer profile |
| deterministic_seed | manifest | schedule trace | Conditional; seed plus generator identity |
| schedule_ref/digest | manifest | TEST-05 operations/events | Required for concurrency vectors |
| time_profile_ref | manifest | event ordering and observations | Fixed synthetic clock profile; uncertainty explicit |
| artifact_destination_ref | manifest | publication records | Immutable destination identity; no arbitrary URL/path |
| network_policy_ref | manifest | isolation evidence | Initial harness DENY_ALL |
| approval_ref | manifest | run controller and verifier | Exact scope approval; does not replace TEST-08 |

The manifest is immutable after run start. A changed field creates a new manifest/run binding; it does not mutate the historical run.

## 4. Cross-contract entity and relationship map

### 4.1 Source, specification and vector entities

| Entity | Required fields | Relationship |
|---|---|---|
| SourceRevision | repository_id, source_commit_sha | Root input to run manifest |
| ContractVersion | contract_id, version, content_digest | Manifest references each applicable TEST contract |
| VectorDefinition | catalogue_version, vector_id, definition_digest | One selected vector maps to exactly one test case |
| ExpectedStatePackage | spec_id, version, digest, approver_ref | Frozen before executor start; oracle consumes read-only |
| TestCaseBinding | vector_id, test_case_id, test_case_version, assertion_ids | One-to-one vector/case mapping; may contain multiple assertions |

No branch name, mutable tag, path or display name substitutes for immutable source/spec/vector identity.

### 4.2 Principal and process entities

| Entity | Required fields | Relationship |
|---|---|---|
| PrincipalRecord | principal_id, issuer_ref, subject_ref, role, capability_snapshot_ref | Referenced by every producer/observer/evaluator/publisher record |
| ProcessRecord | process_id, principal_id, job_id, build_digest, toolchain_ref | Binds a concrete execution process to its effective principal |
| AuthorizationRecord | approval_id, approver_principal_ref, scope_digest, decision, validity | Binds exact permitted run/operation; no inferred authority |
| CapabilitySnapshot | principal_id, resource_scope, operation_allowlist, observed_at/profile | Evidence of effective, not merely configured, capabilities |

A role label does not prove separation. Shared unrestricted principals or shared writable trust boundaries leave independence NOT ESTABLISHED.

### 4.3 Operation and attempt entities (TEST-02/05)

| Entity | Required fields | Relationship |
|---|---|---|
| OperationRecord | operation_id, vector_id, run_id, namespace_id, actor_ref, input_digest, precondition_ref, expected_effect_ref | One logical lifecycle action |
| AttemptRecord | attempt_id, operation_id, ordinal, outcome, start/end sequence, receipt_ref | One or more attempts per operation; attempts never overwrite |
| ScheduleStep | schedule_id, step_id, operation_id, attempt_id, barrier_ref, partial_order_refs | TEST-05 materialized deterministic execution order |
| ResourceVersion | resource_id, version_id, namespace_id, content_digest, metadata_digest, parent_refs, creator_operation_ref | Immutable synthetic resource version |
| AdapterEvent | event_id, event_type, producer_ref, operation_ref, attempt_ref, resource_version_ref, sequence, causal_refs, payload_digest | Append-only lifecycle event; attempt/commit/observe states distinguished |

An operation retry retains operation_id only for the same logical request and canonical payload; each attempt receives a new attempt_id. Changed payload or semantics require a new operation_id. Exact object version is mandatory; no latest alias.

### 4.4 Observation and oracle entities (TEST-04)

| Entity | Required fields | Relationship |
|---|---|---|
| ObservationPlan | plan_id, observer_ref, run_id, namespace_id, target_allowlist, cursor/completeness rules | Frozen before execution |
| ObservationRecord | observation_id, observer_ref, target_version_ref, source_interface_ref, cursor/sequence_range, freshness, completeness, payload_digest | Independently collected, read-only observation |
| AssertionRecord | assertion_id, vector_id, expected_state_ref, observation_refs, comparison_policy_ref, outcome | Evaluates one expected invariant |
| VerdictRecord | verdict_id, run_id, selected_vector_ids, assertion_refs, evaluator_ref, aggregate_status, reason_refs | Deterministic run/vector aggregation |

A failed read is not observed absence. Incomplete pagination is not an empty inventory. Executor logs do not replace independent observations. BLOCKED/NOT RUN are never PASS.

### 4.5 Provenance and artifact entities (TEST-06)

| Entity | Required fields | Relationship |
|---|---|---|
| ProvenanceEnvelope | common envelope plus source/spec/vector/actor/operation/resource/event/observation/verdict refs | Links every lifecycle record to the root manifest |
| ArtifactRecord | artifact_id, media/schema_version, exact_byte_length, payload_digest, producer_ref, provenance_ref | Identifies immutable evidence bytes |
| PublicationRecord | publication_id, artifact_refs, destination_ref, publisher_ref, append_sequence, predecessor_ref, result | Appends artifact evidence to approved destination |
| VerificationRecord | verifier_ref, verifier_build_digest, policy_ref, input_artifact_refs, result, findings | Independently validates provenance and artifact chain |
| CorrectionRecord | correction_id, original_record_ref, reason, approver_ref, replacement_ref | Append-only; original record remains available |

An uploaded artifact is not automatically valid evidence. The verifier must validate bytes, manifest links, producer identity, completeness and publication chain.

### 4.6 Cleanup planning entities (TEST-07)

| Entity | Required fields | Relationship |
|---|---|---|
| ResourceClassification | resource_version_ref, class, owner_ref, lineage_complete, eligibility | Unknown/protected/shared/evidence/recovery classes are ineligible |
| CleanupCandidate | exact resource_version_ref, run_namespace_ref, eligibility_evidence_refs | Candidate only; not authority to act |
| CleanupPlan | plan_id, target_refs, exclusion_refs, plan_digest, limits, pre_observation_refs, approval_ref | Immutable Phase A plan |
| CleanupExecutionAuthorization | authorization_id, plan_digest, exact_operation, limits, approver_ref | Separate Phase B approval; no implied authority |
| CleanupActionRecord | action_id, target_version_ref, attempt_ref, outcome, receipt_ref | Future action evidence only if separately authorized |
| CleanupPostObservation | observation_id, target_version_ref, expected_postcondition, actual_state, protected_root_refs | Independent postcondition and protected-root verification |

TEST-07 does not add delete/cleanup to ordinary adapters or the runner. The cleanup entities are documentary future concepts only. Current Option C means no such action is authorized.

## 5. Cardinality and integrity rules

1. One run_id maps to exactly one immutable manifest digest and one namespace_id.
2. One selected vector_id maps to exactly one test_case_id/version; assertion count may be one or more but must be frozen.
3. Every operation belongs to exactly one run, namespace and vector; every attempt belongs to exactly one operation.
4. Every resource version has exactly one creator lineage or an explicit approved fixture-origin record.
5. Every event has one producer and a valid operation/attempt or an explicitly declared system-origin record.
6. Every observation has one observer, exact target version and frozen observation plan.
7. Every assertion binds one expected-state assertion and all required observations; no hidden denominator reduction.
8. Every verdict references all selected vector results and all run-level gates.
9. Every artifact has exact bytes/digest and provenance; every publication references one immutable destination and publisher.
10. Every correction references an existing original and preserves it.
11. Every cleanup candidate references a classified exact resource version; every future action requires both immutable plan and separate authorization.
12. Duplicate, orphaned, ambiguous, cross-run, cross-namespace, cyclic, missing or mismatched links fail closed.

## 6. Evidence destination contract (C12-F03)

### 6.1 Logical destination identity

A future approved evidence destination must be represented by an immutable `EvidenceDestinationIdentity` record:

| Field | Requirement |
|---|---|
| destination_id | Immutable logical identity |
| destination_class | Dedicated evidence store / repository evidence path / other explicitly approved class |
| owner_principal_ref | Responsible owner identity |
| trust_zone_id | Separate from executor's mutable workspace and all cleanup candidate namespaces |
| resource_locator_ref | Exact opaque locator reference; secrets and credentials are never embedded |
| access_policy_ref | Effective read/write principal and capability snapshot |
| append_policy_ref | Append-only/versioned publication semantics |
| retention_policy_ref | Explicit retention/hold policy and authority |
| inventory_policy_ref | Complete enumeration, pagination and version rules |
| integrity_policy_ref | Canonicalization, digest and independent verification profile |
| recovery_policy_ref | Required availability/recovery treatment for evidence |
| approval_ref | Owner approval of destination class, scope and retention |
| destination_version | Immutable destination configuration/version digest |

The locator is not an arbitrary URL/path and cannot be supplied by the executor. A branch/path may be descriptive but is not, by itself, a complete effective destination trust boundary.

### 6.2 Role capabilities

- Executor: no destination write credential and no ability to change destination configuration or publication policy.
- Observer/evaluator: read-only access to the exact approved evidence inputs; may emit their own isolated records only through separately scoped interfaces.
- Evidence publisher: append-only publication of a completed, digest-bound package; cannot change verdicts or rewrite existing artifacts.
- Independent verifier: read-only retrieval of exact published versions and verification of bytes/lineage.
- Owner/controller: approves the destination policy; does not silently rewrite prior publication records.

Effective principal and storage permissions must be observed independently. A configured permission declaration or GitHub workflow YAML is insufficient.

### 6.3 Retention and protection

Evidence needed for reproducibility, reconciliation, governance, legal/security review or unresolved lifecycle claims remains protected. There is no automatic TTL, expiry, lifecycle deletion, compaction or cleanup of evidence under Option C. Any future retention change or evidence deletion requires separate exact owner authorization and a separate impact review.

The destination must be outside the synthetic resource namespace subject to future cleanup. A destination sharing a mutable storage root, principal or deletion boundary with candidate resources is not acceptable unless independent evidence proves strict isolation; otherwise it is BLOCKED.

### 6.4 Destination closure evidence

Required future evidence:
- exact destination identity and immutable configuration digest;
- effective principal/capability map and read/write separation;
- append-only/version behavior and denied overwrite/delete attempts in an authorized synthetic test;
- complete artifact inventory and exact-version retrieval;
- independent byte/digest and provenance verification;
- retention/hold policy and protected evidence classification;
- evidence that cleanup candidate namespace cannot reach or delete the destination;
- recovery/availability claims limited to measured evidence.

No provider, repository feature, retention value or backup policy is selected by this map.

## 7. Canonicalization and unresolved technology choices

The logical map requires deterministic canonicalization but intentionally does not choose the implementation. Before any schema implementation, a versioned technical proposal must define:
- serialization format and strict schema evolution rules;
- canonical byte representation and digest algorithm/encoding;
- identifier syntax, uniqueness scope and normalization;
- timestamp encoding, clock source, precision and uncertainty;
- signature/attestation and identity issuer/trust policy, if used;
- artifact media types, size/count limits and pagination;
- destination implementation, effective permission proof, retention and recovery;
- compatibility and migration policy for historical records.

Until these choices are approved and frozen, the logical profile is a documentary map only. No hash algorithm is mandated here despite prior contracts using SHA-256 as an illustrative or specific catalogue digest requirement; the canonical profile must make all algorithm identifiers explicit and consistent before implementation.

## 8. Cross-contract gap disposition

| Finding | Disposition |
|---|---|
| C12-F01 Integrated schema/field registry | RESOLVED AT LOGICAL DOCUMENTARY MAP LEVEL; executable schemas and canonicalization remain OPEN |
| C12-F02 87-vector assertion traceability | OPEN; assigned to Stage C.14 |
| C12-F03 Evidence-destination identity/retention binding | RESOLVED AT LOGICAL DOCUMENTARY MAP LEVEL; provider/effective permissions/retention evidence NOT VERIFIED |
| C12-F04 PRV-T04 wording | OPEN; editorial correction assigned to Stage C.15 |

Resolution here means only that field ownership, relationship, cardinality and trust-boundary requirements are now mapped in documentation. It does not close TEST-01–07 or prove destination availability, immutability, permissions or retention.

## 9. Current disposition

| Item | Status |
|---|---|
| TEST-01 | CONTRACT DOCUMENTED / IMPLEMENTATION NOT ESTABLISHED |
| TEST-02 | CONTRACT DOCUMENTED / IMPLEMENTATION NOT ESTABLISHED |
| TEST-03 | CONTRACT DOCUMENTED / EFFECTIVE ISOLATION NOT VERIFIED |
| TEST-04 | CONTRACT DOCUMENTED / INDEPENDENT ORACLE NOT ESTABLISHED |
| TEST-05 | CONTRACT DOCUMENTED / DETERMINISTIC CONCURRENCY NOT ESTABLISHED |
| TEST-06 | CONTRACT DOCUMENTED / LIFECYCLE-SPECIFIC PROVENANCE NOT ESTABLISHED |
| TEST-07 | CONTRACT DOCUMENTED / CLEANUP CONTAINMENT NOT ESTABLISHED |
| TEST-08 | NOT GRANTED — separate exact-scope owner authorization required |
| LDA-07 | NOT RUN; 87/87 lifecycle vectors remain NOT RUN |
| LDA-06 | PARTIAL / NOT VERIFIED |
| LDA-08 | HOLD / NOT VERIFIED |

No tests, compile, dry-run, fault injection, provisioning, Actions dispatch, secrets/permission/runtime/VPS/database/provider/recipient/backup/replica probes, source/schema/adapter/workflow/runner/permission/runtime/data changes or destructive operations were performed.

**STAGE C.13 DOCUMENTARY FIELD MAP COMPLETE — C12-F01/C12-F03 RESOLVED AT LOGICAL CONTRACT LEVEL ONLY — IMPLEMENTATION AND DESTINATION VERIFICATION NOT ESTABLISHED.**
