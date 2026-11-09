# Stage L.0–L.7 — Contract Profile Specification Draft
Date: 2026-11-10
Repository: kenznguyen/btcusdt-telegram-signals2
Branch: feature/t0-centralized-data-feeder-p1-20261101
Contract ID: `H5-LIFECYCLE-TECHNICAL-CONTRACT`
Base contract: `1.0.0-draft`
Companion profile: `1.1.0-profile-draft` (DOCUMENTARY ONLY; NOT FROZEN)
Work type: documentary specification; no executable schema or implementation.
Status: PROFILE DRAFT COMPLETE; NORMATIVE OPEN ITEMS PRESERVED; NOT FREEZE-READY.

## L.0 — Authority, source baseline and limits

This stage follows the owner's standing approval to continue subsequent stages automatically. The approval is applied to documentary specification only.

Sources fetched on the existing branch:
- Stage I contract: `docs/evidence/p1-8/STAGE_I0_I5_VERSIONED_TECHNICAL_CONTRACT_2026-11-10.md`, blob `ec964176cec4ae9ead00e34e3fbd36d36d437616`.
- Stage J reconciliation: `docs/evidence/p1-8/STAGE_J0_J6_CONTRACT_RECONCILIATION_FREEZE_READINESS_REVIEW_2026-11-10.md`, blob `3bbc5a51783871280b2bf799d9ebfcea6b4f9570`.
- Stage K adjudication package: `docs/evidence/p1-8/STAGE_K0_K6_OWNER_ADJUDICATION_DECISION_PACKAGE_2026-11-10.md`, blob `25ddd64e1a3aab4fa5d3e58971d88fb7e6189676`.
- Stage C.13 logical field map: `docs/evidence/p1-8/STAGE_C13_INTEGRATED_SCHEMA_FIELD_AND_EVIDENCE_DESTINATION_MAP_2026-11-10.md`, blob `c43c8bfbccaf698d6670f33fab66ee12d2072a7f`.
- Stage C.14 traceability matrix: `docs/evidence/p1-8/STAGE_C14_87_VECTOR_TEST01_07_APPLICABILITY_TRACEABILITY_MATRIX_2026-11-10.md`, blob `12bba6c475fc2ad8c4e2246e75034ede22d3bc20`.
- Project handoff at start of Stage L: blob `f76f743e65a7fc2e289ecda17435e3e4197307ff`.

This document is a companion draft, not a replacement of Stage I, C.13 or the source test contracts. It does not create JSON Schema, protobuf, database DDL, migrations, code, adapters, runners, workflows, credentials, provider accounts or permissions. It does not freeze any OPEN value.

## L.1 — Profile status and normative vocabulary

The companion profile records candidate structure while preserving uncertainty.

- **MUST / MUST NOT**: requirement for a future implementation claiming conformance, subject to final freeze.
- **SHOULD / SHOULD NOT**: recommended behavior; exceptions require explicit rationale and owner acceptance.
- **OPEN**: no value may be inferred or silently defaulted.
- **TBD-OWNER**: requires explicit owner policy decision.
- **TBD-TECH**: requires technical specification or conformance evidence.
- **TBD-EVIDENCE**: requires effective read-only or implementation evidence.
- **BLOCKED**: fail-closed; no success, permission or absence may be inferred.
- **NOT RUN**: no execution evidence exists.

No field marked OPEN/TBD may be treated as having an implementation default.

## L.2 — Candidate serialization and digest profile

### L.2.1 Approved direction retained

- Canonical record representation: UTF-8 JSON compatible with RFC 8785 JCS.
- Canonical payload digest direction: SHA-256 over JCS-emitted UTF-8 bytes.
- Source-byte digest: separate SHA-256 over exact original bytes when source-byte provenance is required.
- Canonical and source-byte digests are semantically distinct and MUST NOT be substituted.
- Domain-separated identifiers are required in principle; the construction in Stage I remains a candidate pending exact registry/profile.

### L.2.2 Explicit unresolved parameters

| Parameter | Candidate requirement | Status |
|---|---|---|
| JCS implementation/library and exact version | One pinned implementation with reproducible output | TBD-TECH |
| Parser strictness and duplicate-key rejection | Reject duplicate members before canonicalization | Requirement stated; conformance TBD-TECH |
| UTF-8 handling | Reject invalid UTF-8; no implicit Unicode normalization | Requirement stated; vectors TBD-TECH |
| Numeric profile | Reject non-finite/unsupported values; no binary float as authoritative money | Exact integer bounds and decimal grammar TBD-OWNER/TECH |
| Negative zero and exponent handling | Deterministic acceptance/rejection rules | TBD-TECH |
| Financial quantities | Typed integer base units or explicit decimal string | Unit/scale/rounding TBD-OWNER |
| Digest envelope/self-exclusion | Digest field excluded from its own canonical input | Exact envelope/field names TBD-TECH |
| Domain labels and ID encoding | Domain-separated identifiers | Registry, encoding, truncation and collision handling TBD-TECH |
| Golden vectors | Positive and negative cross-implementation fixtures | Not created or run; TBD-TECH |

No library, numeric bound, decimal scale, rounding mode, Unicode normalization rule, digest envelope or domain-label value is selected here.

### L.2.3 Candidate digest reference shape (logical, not executable)

| Member | Logical type | Requiredness | Status |
|---|---|---|---|
| algorithm | enum/string | required | Candidate `SHA-256`; wire spelling TBD-TECH |
| digest_encoding | enum | required | TBD-TECH |
| digest_value | byte string / encoded string | required | Encoding TBD-TECH |
| canonicalization_profile | immutable profile ref | required for canonical digest | JCS direction approved; profile version TBD-TECH |
| source_byte_digest | digest ref | conditional | Required only when exact source bytes are retained |
| digest_domain | immutable registry ref | conditional | Registry TBD-TECH |

## L.3 — Candidate common evidence envelope

The following is a logical field registry consolidated from C.13 and Stage I. It is not a machine schema.

| Field | Candidate type | Requiredness | Constraint / unresolved item |
|---|---|---|---|
| schema_id | immutable identifier | MUST | Registry and URI/URN form TBD-TECH |
| schema_version | version string | MUST | Version grammar and compatibility matrix TBD-TECH |
| record_type | enum | MUST | Controlled vocabulary TBD-TECH |
| record_id | immutable identifier | MUST | Scope, entropy and encoding TBD-TECH |
| repository_id | canonical repository identity | MUST | Canonical identity syntax TBD-TECH |
| source_commit_sha | full Git commit SHA | MUST | Hash algorithm/length validation profile TBD-TECH |
| run_id | immutable identifier | MUST | Generation and uniqueness guarantee TBD-TECH |
| namespace_id | immutable identifier | MUST | Isolation binding TBD-TECH |
| manifest_digest | digest reference | MUST | Exact digest envelope TBD-TECH |
| created_sequence | non-negative integer | MUST | Stream scope, allocation and overflow bound TBD-OWNER/TECH |
| recorded_time | structured time claim | CONDITIONAL | Clock authority, precision, uncertainty and encoding TBD-OWNER/TECH |
| payload_digest | digest reference | MUST | Canonical payload digest; self-exclusion rules TBD-TECH |
| previous_record_ref | immutable reference | CONDITIONAL | Chain scope and genesis rules TBD-TECH |
| correction_refs | immutable reference list | OPTIONAL | Correction and supersession semantics TBD-TECH |
| producer_principal_ref | immutable principal reference | MUST | Issuer/subject identity schema TBD-TECH |
| producer_process_ref | immutable process reference | MUST | Build/toolchain/process schema TBD-TECH |
| validation_profile_ref | immutable policy/profile reference | MUST | Exact verifier policy binding TBD-TECH |

Rules:
1. Each record binds to exactly one run and namespace, unless a separately versioned record type explicitly defines otherwise.
2. Required references resolve to exact immutable identities, not branch names, mutable tags, display labels or `latest` aliases.
3. Missing, duplicate, ambiguous, mismatched or unsupported required values fail closed.
4. Absent and null are distinct; their field-specific semantics must be declared.
5. A record is append-only. Corrections create new records referencing the prior record; they do not rewrite history.
6. Exact cardinalities and reference-closure constraints remain subject to machine-readable schema design.

## L.4 — Candidate record families and relationships

| Family | Candidate records | Required relationship | Open specification |
|---|---|---|---|
| Root/selection | RunManifest, Catalogue, TestCaseBinding | One immutable root manifest binds selected vector set, source revision, contracts and fixtures | Exact field schema, cardinalities and freeze timing TBD-TECH |
| Source/specification | SourceRevision, ContractVersion, VectorDefinition, ExpectedStatePackage | Exact immutable versions referenced by manifest | Identifier grammar and compatibility TBD-TECH |
| Identity/process | PrincipalRecord, ProcessRecord, AuthorizationRecord, CapabilitySnapshot | Every producer/observer/evaluator/publisher binds effective principal and process | Identity issuer, credentials and capability proof TBD-OWNER/EVIDENCE |
| Operation/resource | OperationRecord, AttemptRecord, ScheduleStep, ResourceVersion, AdapterEvent | Attempts belong to logical operation; resource/event references are causal and run-scoped | State machine, retry/idempotency, sequence and cycle rules TBD-TECH |
| Observation/oracle | ObservationPlan, ObservationRecord, AssertionRecord, VerdictRecord | Independent observer supplies exact observations; oracle binds assertions to frozen expected state | Cursor, completeness, freshness and aggregation profile TBD-TECH |
| Provenance/artifact | ProvenanceEnvelope, ArtifactRecord, PublicationRecord, CorrectionRecord | Artifacts bind exact bytes, producer, run, source and causal references | Byte length, media/schema type, exact destination version TBD-TECH |
| Verification | VerificationRecord | Separate verifier validates exact-version bytes, digest, schema, provenance and causal closure | Trust roots, verifier build, result schema and signature TBD-OWNER/TECH |
| Resource/cleanup | ResourceClassification, CleanupCandidate, CleanupPlan, CleanupExecutionAuthorization, CleanupActionRecord, CleanupPostObservation | Synthetic-only scope, explicit authorization and independent post-observation | Documentary only; no cleanup permission; TEST-08 separately required |
| Destination/retention | EvidenceDestinationIdentity, DestinationPolicy, RetentionDecision, RecoveryRecord | Evidence destination is outside synthetic cleanup boundary and preserves exact versions | Provider, owner, append-only enforcement, duration and recovery TBD-OWNER/EVIDENCE |

### L.4.1 Operation and attempt candidate invariants

- One logical request has one operation identity; each retry has a distinct attempt identity.
- Reuse of an operation identity is permitted only for an identical canonical request under a frozen idempotency profile.
- Changed payload or semantics require a new operation identity.
- Attempt records are immutable; retries do not overwrite earlier attempts.
- Terminal-state vocabulary, retry classification, linearization point and receipt semantics remain OPEN.
- Cyclic causal references, orphan references and ambiguous terminal state must fail closed; exact detection profile remains TBD-TECH.

### L.4.2 Observation and verdict candidate invariants

- Executor output is not an independent observation.
- A failed read is not proof of absence; incomplete pagination is not an empty inventory.
- Observation records bind observer, source interface, cursor/range, freshness and completeness.
- Verdicts preserve the complete selected-vector denominator.
- PASS, FAIL, BLOCKED, INDETERMINATE and NOT RUN are distinct states; aggregation precedence and exact reason schema remain TBD-TECH.
- No lifecycle vector gains PASS status from this documentary profile.

## L.5 — Candidate resource, identity and evidence trust boundaries

### L.5.1 Resource classes

Exactly one classification per discovered resource:
- `SYNTHETIC`: positive evidence proves creation and ownership within the exact run namespace.
- `PROTECTED`: explicitly protected by policy/owner boundary.
- `UNKNOWN`: identity, ownership or scope cannot be established.
- `UNCLASSIFIED`: inventory is incomplete or classification has not completed.

Only positively proven SYNTHETIC resources could be eligible for a future separately authorized lifecycle manifest. All other classes are excluded. This eligibility statement grants no authority to act.

### L.5.2 Isolation target

Stage H approved layered per-run synthetic isolation. Candidate layers:
1. Per-run namespace and resource ownership.
2. Synthetic-only storage/database scope.
3. Distinct least-privilege identity and credentials.
4. Filesystem/mount allowlists and no writable path outside synthetic root.
5. Default-deny network egress with explicit dependency allowlist.
6. Explicit resource API/operation allowlist.
7. Independent observation of effective boundaries.

Container/VM/process topology, network policy implementation, filesystem enforcement, storage backend and negative-test evidence remain TBD-OWNER/TECH/EVIDENCE. No actual isolation is claimed.

### L.5.3 Principal separation target

Candidate roles: owner/controller, executor, adapter, observer/oracle, publisher and independent verifier.

- Role names alone do not establish separation.
- Effective principals and capabilities must be separately evidenced.
- Executor must not possess evidence-store publication, retention-policy mutation or deletion capability.
- Observer/oracle must not rely solely on executor-controlled logs.
- Publisher cannot author the independent verifier's verdict.
- Verifier must read exact immutable versions and remain read-only.
- Identity provider, credential issuance/rotation/revocation and effective permission proof remain OPEN.

### L.5.4 Evidence destination and verification

Approved architecture direction: Git index plus separately versioned evidence payload destination, provider-neutral.

Candidate destination requirements:
- immutable exact-version retrieval;
- append-only or equivalently enforced immutability;
- independently verified read-back;
- separate trust boundary from synthetic resources;
- no mutable latest alias as an evidence identity;
- destination identity, owner and version reference included in the manifest.

Provider, account, region, ownership, pricing, retention mechanism and effective permissions are not selected.

Independent verifier candidate checks:
1. exact input version and byte length;
2. source-byte and canonical digest as applicable;
3. schema/profile validity;
4. source commit and producer/process provenance;
5. run/namespace binding;
6. reference closure and causal graph integrity;
7. selected vector denominator preservation;
8. destination read-back and immutability evidence;
9. policy/build/trust-root identity.

Verifier trust roots, build attestation, signed result format and failure aggregation remain OPEN.

## L.6 — Time, retention and authority profile

### L.6.1 Time and causal ordering

- Sequence and explicit causal references are candidate authoritative ordering mechanisms.
- Wall-clock timestamps are descriptive claims, not sole proof of causality.
- Every time claim must identify clock source, encoding, precision and uncertainty.
- Sequence scope, allocator, monotonicity across process restart, timestamp authority and accepted uncertainty remain OPEN.
- No timestamp or lag threshold is invented in this stage.

### L.6.2 Retention and recovery

- Retention/hold/recovery governance direction from Stage H is preserved.
- No retention duration, provider, backup interval, RPO/RTO operational commitment or recovery mechanism is selected.
- While Option C remains ACTIVE, no automatic expiry, cleanup, archive-as-deletion, purge or destructive lifecycle operation is authorized.
- Protected evidence is preserved by default.
- Any future retention/recovery policy requires explicit owner values and effective provider evidence.

### L.6.3 Authorization boundaries

- TEST-08 remains NOT GRANTED.
- No cleanup, deletion, expiry, archive, restore, mutation or lifecycle operation may be inferred from this profile.
- No code/schema implementation, test, compile, dry-run, fault injection, Actions dispatch, permission change, credential provisioning or runtime/provider/VPS/database probe is authorized.
- `AI_EXECUTION_ENABLED=false`; paper-only; no live orders.

## L.7 — Open register, traceability and disposition

| ID | Topic | Profile status | Freeze blocker |
|---|---|---|---|
| L-OPEN-01 | JCS library/version and strict parser conformance | TBD-TECH | Yes |
| L-OPEN-02 | Integer bounds, decimal grammar, Unicode and numeric edge cases | TBD-OWNER/TECH | Yes |
| L-OPEN-03 | Digest envelope, domain registry, ID encoding | TBD-TECH | Yes |
| L-OPEN-04 | Schema IDs, exact types/requiredness and evolution matrix | TBD-OWNER/TECH | Yes |
| L-OPEN-05 | Clock authority, sequence scope and causal/time profile | TBD-OWNER/TECH | Yes |
| L-OPEN-06 | Retry, attempt, idempotency, correction and terminal states | TBD-TECH | Yes |
| L-OPEN-07 | Isolation topology and effective boundary proof | TBD-OWNER/TECH/EVIDENCE | Yes |
| L-OPEN-08 | Identity provider, credentials and effective capabilities | TBD-OWNER/TECH/EVIDENCE | Yes |
| L-OPEN-09 | Evidence provider/owner/version/immutability | TBD-OWNER/EVIDENCE | Yes |
| L-OPEN-10 | Verifier trust roots/build/result signature | TBD-OWNER/TECH/EVIDENCE | Yes |
| L-OPEN-11 | Retention/hold/recovery values and enforcement | TBD-OWNER/EVIDENCE | Yes |
| L-OPEN-12 | TEST-08 exact lifecycle execution authorization | NOT GRANTED | Execution blocker |
| L-OPEN-13 | LDA-06 inventory and LDA-08 effective permission evidence | PARTIAL / HOLD; NOT VERIFIED | Readiness blocker |

### Traceability preservation

- C.13 logical entity/field map: source blob `c43c8bfbccaf698d6670f33fab66ee12d2072a7f`.
- C.14 denominator: 87 unique vectors (47 + 40); 87/87 design-level mapped; 0/87 executable bindings; 87/87 NOT RUN.
- C.15 finding dispositions and Stage J crosswalk remain unchanged.
- No vector status, coverage, test result or production assurance is upgraded by Stage L.

### Final Stage L disposition

**PROFILE DRAFT COMPLETE — CONTRACT FREEZE NOT READY.**

Stage L supplies a structured candidate profile, explicit logical fields, entity families, invariants, trust boundaries and an OPEN register. It does not provide executable schemas or conformance proof. The companion profile must remain draft until owner decisions and technical evidence close all applicable blockers.

Recommended next stage: **Stage M — Profile Consistency and Test-Traceability Review**, documentary-only. Compare this companion profile against C.13, C.5–C.11, C.14, C.15 and Stages H–K; identify omissions, contradictions, ambiguous normative language and test assertion coverage gaps. Do not create executable tests or change the 87-vector denominator. Any implementation or lifecycle execution remains separately gated.

**STAGE L DOCUMENTARY PROFILE DRAFT COMPLETE — NOT FROZEN — NOT IMPLEMENTED — NOT EXECUTABLE — OPTION C ACTIVE.**
