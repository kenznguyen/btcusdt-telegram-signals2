# Stage C.10 — TEST-06 Lifecycle-Specific Provenance Contract

Date: 2026-11-10
Repository: kenznguyen/btcusdt-telegram-signals2
Branch: feature/t0-centralized-data-feeder-p1-20261101
Work type: documentation-only contract; TEST-06 only.
Predecessors: Stage C.4 prerequisite closure plan; C.5 TEST-01 runner; C.6 TEST-02 synthetic adapters; C.7 TEST-03 isolation; C.8 TEST-04 independent oracle; C.9 TEST-05 deterministic concurrency.
Source baseline: Stage C.9 report blob 4f6f193b3aaadb553ac1a6959a189b54e2fd73d9; handoff blob d318c300beecaacd67086fd9f1c9f2bf28061cb4.

## 1. Purpose and authority boundary

Define the lifecycle-specific provenance contract needed to establish where each lifecycle test result and evidence item came from, which immutable inputs and actors it is bound to, how events relate causally, and whether the evidence is complete, authentic, independently observed and reproducible.

The required chain is:

source/specification/vector definition → approved run manifest → actor/principal → logical operation and attempt → synthetic namespace/resource/version → lifecycle event and independent observation → oracle assertion/verdict → evidence artifact and append-only publication record.

Every link must be explicit and verifiable. A missing link is not inferred from filenames, timestamps, executor logs or naming conventions.

This is a future contract, not an implementation or proof that existing Sigstore, attestation, event-signature or evidence-archive machinery satisfies lifecycle-specific provenance. Stage C approval authorizes bounded documentary work only. It does not authorize code/schema/adapter/runner/workflow changes, tests, compilation, dry-run, fault injection, Actions dispatch, secrets or permission access, runtime/VPS/database/provider/network probes, provisioning or data mutation. TEST-08 remains a separate exact-scope owner authorization gate before execution.

Option C remains active. No deletion, archive, cleanup, expiry, compaction, vacuum, backup/replica removal, export mutation or irreversible transition. Protected assets remain T0 canonical data and recovery copies, CORE_LEDGER, AI_LEDGER, required T3 reconstruction/audit records, governance history/evidence while needed, and unknown/unclassified/orphaned objects. All future test resources must be synthetic and isolated.

## 2. Provenance properties and non-equivalences

The evaluator must assess these properties separately; one does not imply another:

- **Completeness:** every required chain link and expected event/observation is present, with declared coverage boundaries and no unexplained gaps.
- **Integrity:** bytes and canonical representations have not changed relative to their bound digests or append-only sequence.
- **Authenticity:** the claimed actor/process/source actually produced or endorsed the record under a verifiable identity/trust policy.
- **Attribution:** the record is bound to a specific principal, role, process/job and operation/attempt, not merely a display name.
- **Causal consistency:** event ordering and parent/child references satisfy declared happens-before constraints; wall-clock order alone is insufficient.
- **Independence:** executor cannot author, alter, suppress or self-validate required observer, oracle, verdict or publisher evidence.
- **Reproducibility:** frozen inputs and a specified verifier reproduce the same provenance validation and verdict without re-executing lifecycle operations.

A cryptographic hash establishes a content comparison only when the expected digest is trusted; by itself it does not establish origin, identity, completeness, time, authorization or independence. A valid signature establishes a cryptographic relationship to a key, not that the key was correctly attributed or that the signed claim is true. A workflow attestation is not automatically proof of a lifecycle operation or a complete evidence chain.

## 3. Identity and immutable identifier model

Every record must use stable, globally unambiguous identifiers within the declared contract scope. Minimum identifier classes:

| Identifier | Meaning | Required binding |
|---|---|---|
| source_commit_id | Exact repository source revision | Full immutable commit SHA and repository identity |
| contract_id/version | Applicable contract and version | Canonical bytes/digest |
| vector_id | Lifecycle negative vector | Exact catalog version and source location/reference |
| spec_id/version | Approved expected-state specification | Digest and approval record |
| run_id | One logical test run | Manifest digest and unique run namespace |
| namespace_id | Synthetic isolation boundary | Run binding and exact resource allowlist |
| principal_id | Effective actor identity | Identity issuer/authority and role/capability snapshot |
| process_id/job_id | Concrete executor/observer/evaluator instance | Run, principal and toolchain/runtime identity |
| operation_id | Logical lifecycle operation | Vector, actor, resource and canonical input digest |
| attempt_id | One execution/delivery attempt | Parent operation ID and monotonic attempt ordinal |
| resource_id/version_id | Exact synthetic object and immutable version | Namespace, content/metadata digest and lineage |
| event_id | One immutable lifecycle event | Producer, operation/attempt, sequence and payload digest |
| observation_id | Independent observation | Observer identity, target version, cursor/sequence and payload digest |
| assertion_id/verdict_id | Oracle assertion and result | Expected-state package and observation references |
| artifact_id | Evidence artifact | Exact bytes/digest, media/schema version and provenance chain |
| publication_id | Append-only evidence publication | Publisher identity, destination scope and predecessor reference |

Identifiers are never silently reused for a different semantic object. Mutable aliases such as branch names, latest tags, paths, job display names or current object pointers may be recorded as descriptive metadata but cannot replace immutable identity/version bindings.

A run manifest must freeze the identifier namespace and uniqueness rules before execution. Duplicate, colliding, malformed, unknown or cross-run identifiers block the affected run. A retry creates a new attempt_id while retaining the same operation_id only when it is genuinely the same logical operation and canonical payload; changed semantics require a new operation ID.

## 4. Provenance envelope and canonical schema

Each provenance-bearing record must have a versioned envelope with, at minimum:

- schema identifier and version; record type; immutable record ID;
- repository, full source commit SHA, applicable contract/spec/vector IDs and their digests;
- run ID, namespace ID and manifest digest;
- producer principal, role, process/job identity, identity issuer and effective capability snapshot reference;
- operation ID, attempt ID, parent/causal references and exact resource/version IDs where applicable;
- event/observation sequence or cursor, declared ordering scope and completeness boundary;
- payload media type, canonicalization profile, byte length and cryptographic digest;
- creation/recording time with explicit clock source, timezone, precision and uncertainty where time is used;
- previous-record/chain reference and explicit correction/supersession references;
- signature/attestation reference and trust-policy version, if used;
- validation status and typed error details, without secret values.

The contract requires canonicalization to be specified and versioned, including character encoding, key ordering, numeric representation, timestamp normalization, null-versus-absent semantics, byte encoding and collection ordering. The contract does not select a serialization format, digest algorithm, signature algorithm, attestation profile, timestamp authority or trust-root technology. Those choices require a separate technical design and evidence; no provider or trust anchor is implicitly approved here.

Unknown mandatory fields, unsupported schema versions, duplicate keys, ambiguous canonicalization, unrecognized critical extensions or digest mismatch fail closed. Optional fields cannot be used to smuggle unreviewed semantics into a verdict.

## 5. Required provenance chain and binding rules

### 5.1 Source and contract binding

The run binds the exact repository identity and full source commit SHA; runner, adapter, oracle and verifier source/configuration digests; vector catalog/version; TEST-01–06 contract versions; expected-state package digest; and toolchain/dependency identities. A branch name or workflow filename alone is not a source identity.

Any changed source, contract, fixture, verifier or policy creates a new immutable run/evaluation binding. Historical records remain linked to the original versions; they are not rewritten to appear as though they used the new version.

### 5.2 Authorization and principal binding

The manifest binds owner approval and exact authorized scope, controller, executor, observer, oracle evaluator and evidence publisher identities. Effective principals and capabilities must be evidenced, not inferred from configured role labels.

The executor cannot issue authoritative observer, oracle or publisher records; alter the expected-state package; or use publisher credentials. The observer is read-only against exact synthetic resources and independently records observations. The evaluator consumes frozen expectations and observations. The publisher appends the completed evidence package without changing its verdict.

Role separation must be evaluated against effective identities, credentials and write capabilities. Separate modules, processes or job names under the same unrestricted principal do not establish independence. If effective separation cannot be proven, provenance/independence is NOT ESTABLISHED.

### 5.3 Operation, attempt and resource binding

Each operation record binds vector ID, run/namespace, actor, logical operation ID, attempt ID, canonical input digest, precondition, exact resource/version and declared expected effect. Attempt records capture start, completion, rejection, timeout, cancellation or indeterminate acknowledgement without changing the logical operation identity.

Resource creation/version records bind immutable object identity, exact bytes and metadata digests, parent/source lineage, namespace and the operation that produced the version. A path or mutable object name is insufficient. Cross-namespace or protected-root references are scope violations and trigger abort.

### 5.4 Event and observation binding

Every event binds event ID, producer principal/process, operation/attempt, resource/version, event type, canonical payload digest, sequence/cursor and causal parent references. Events must distinguish attempted, accepted, committed, rejected and observed states; an API response or executor log is not proof of durable commit.

Every observation binds observer identity, read-only interface/version, exact target identity/version, observation plan, cursor/sequence range, completeness/freshness classification, raw payload digest and the event/resource references observed. Missing event ranges, pagination gaps, stale reads, failed reads and observed absence are distinct states.

### 5.5 Oracle and verdict binding

Each assertion verdict binds the frozen expected-state assertion, vector/case IDs, complete observation IDs, evaluator source/config digest, canonical comparison policy and typed outcome. Run-level aggregation references every selected vector and assertion, including BLOCKED and NOT RUN outcomes. No result is omitted from the denominator.

Executor summaries, scheduler traces and self-reported PASS values may be retained as diagnostic inputs, but cannot be the sole source of truth for an assertion or verdict.

### 5.6 Artifact and publication binding

Each evidence artifact binds exact bytes, digest, schema/media type, producer and source chain. The publication record binds artifact IDs/digests, run/verdict IDs, publisher principal, destination identity, append sequence and predecessor record. Publication success does not imply correctness of artifact contents; verification must independently validate the artifact and all required links.

## 6. Causal order, replay and append-only correction

Causality is represented by explicit parent/event references, monotonic sequence numbers within a declared scope, operation/attempt relations and declared happens-before edges. Wall-clock timestamps are supporting metadata, not a substitute for causal order. If timestamps are required, the clock source, precision, skew/uncertainty and boundary semantics must be frozen; ambiguous ordering yields INDETERMINATE.

The verifier must detect:
- missing, duplicate, orphaned or unreferenced records;
- broken parent links, cycles, impossible causal edges or sequence regression;
- replayed records, reused IDs, cross-run/namespace substitution or conflicting payloads under one identity;
- event forks, gaps, truncation, incomplete pagination or reordered append sequences;
- mismatched source/spec/vector/manifest/resource/observation/verdict/artifact digests;
- stale or revoked identity/trust status under the applicable frozen policy;
- corrections that overwrite or conceal the original record.

Corrections, retractions and supersession are append-only new records. They identify the original record, reason, authorizing principal, time/sequence and replacement/superseding record. Original bytes and verdicts remain preserved. No correction may retroactively make an earlier run appear to have used a later policy or source version.

Replay is read-only: it validates preserved evidence and recomputes provenance/verdicts without re-executing lifecycle operations, refreshing resources or contacting external systems. Same frozen evidence plus same verifier/policy version must produce the same result. A changed verifier/policy creates a linked new evaluation.

## 7. Trust, signatures and time claims

If cryptographic signatures or attestations are used, validation must bind the exact signed bytes and immutable verification context, including the relevant source/spec/run/artifact identities. Trust policy must define issuer/key identity, allowed purpose, validity interval, revocation semantics, rotation/cutover, trust-root provenance and verifier version.

A signature is not accepted merely because it verifies mathematically: identity attribution, authorization, key custody/issuer trust and applicable validity/revocation policy must also be established. A timestamp token, if later selected, can support only the precise temporal claim warranted by its verified imprint and trusted-time semantics; it must not be described as proving exact signature creation time or signer intent.

No signing key, OIDC identity, TSA, attestation provider, trust root, algorithm, key lifecycle policy or permission is selected or authorized by this contract. No live signature, attestation or timestamp operation is performed here. Existing repository workflow permissions such as id-token:write or attestations:write are not evidence that a lifecycle run is correctly authenticated or independently verified.

## 8. Completeness, integrity and provenance verification

A verifier must evaluate chain completeness against the frozen manifest and vector denominator, not merely validate records that happen to be present. It must account for every selected vector, operation, attempt, expected event, required observation, assertion, verdict and artifact. Missing expected records are explicit failures/indeterminate outcomes, not silently excluded items.

Minimum validation sequence:
1. Validate schema versions, canonicalization and identifier uniqueness.
2. Verify source, contract, vector, manifest and expected-state digests.
3. Verify approval and exact scope binding, without treating approval as technical proof.
4. Validate principal/process identity and effective role/capability evidence.
5. Reconstruct operation/attempt/resource lineage and exact namespace membership.
6. Validate event identity, causal graph, sequence continuity and declared completeness.
7. Validate independent observations, freshness, read-only scope and exact target versions.
8. Validate signatures/attestations/trust policy if present; otherwise report authenticity limits explicitly.
9. Recompute assertion and run verdicts using the frozen oracle policy.
10. Validate artifact bytes, publication chain, append-only continuity and full denominator.
11. Emit a new immutable verification record containing verifier identity/version, inputs, findings and result.

A successful digest check alone cannot produce PASS. All applicable properties and dependencies must be evidenced.

## 9. Failure classes and verdict semantics

Typed provenance errors should include at least:

| Error | Meaning |
|---|---|
| PROV_SCHEMA_INVALID | Unsupported or malformed provenance envelope |
| PROV_ID_DUPLICATE | Identifier collision or semantic reuse |
| PROV_LINK_MISSING | Required chain edge or record absent |
| PROV_LINK_ORPHAN | Record has no valid parent/run/manifest binding |
| PROV_DIGEST_MISMATCH | Content does not match bound digest |
| PROV_SOURCE_MISMATCH | Source/contract/spec/vector binding differs |
| PROV_SCOPE_MISMATCH | Wrong run, namespace, resource or protected-root reference |
| PROV_PRINCIPAL_UNVERIFIED | Actor/process identity cannot be established |
| PROV_AUTHORITY_UNPROVEN | Approval/capability/authorization evidence insufficient |
| PROV_ROLE_COLLISION | Executor/observer/evaluator/publisher separation not established |
| PROV_CAUSAL_GAP | Missing, forked, reordered or impossible causal sequence |
| PROV_REPLAY_OR_REUSE | Replayed record or reused immutable identity |
| PROV_OBSERVATION_INCOMPLETE | Missing range, stale read or incomplete pagination |
| PROV_TRUST_INVALID | Signature/attestation issuer, key or trust policy invalid/unresolved |
| PROV_TIME_UNCERTAIN | Required temporal ordering cannot be established |
| PROV_ARTIFACT_SUBSTITUTION | Published artifact differs from bound evidence |
| PROV_POLICY_DRIFT | Verifier/canonicalization/trust policy differs from frozen version |

Verdicts retain TEST-01/04 semantics:
- **PASS:** every required chain link is present and valid; source/spec/vector/run/actor/operation/resource/event/observation/oracle/artifact bindings match; completeness, integrity, authenticity and independence are established to the declared claim; causal order and append-only history validate; all prerequisite gates pass.
- **FAIL:** complete trustworthy evidence proves a specific prohibited mutation, substitution, unauthorized actor, forged or invalid record, broken integrity, or other explicit invariant violation.
- **INDETERMINATE:** evidence is incomplete, stale, ambiguous, conflicting or insufficient to establish correctness/authenticity/independence; do not turn missing proof into PASS or assert an unproven violation as FAIL.
- **BLOCKED:** authorization or prerequisite gates prevent valid execution/verification.
- **NOT RUN:** no lifecycle execution was attempted.

Run aggregation is deterministic: FAIL if any required vector has a proven failure; otherwise INDETERMINATE if any required evidence/property is indeterminate or incomplete; PASS only when every selected vector and run-level gate passes; BLOCKED if prohibited before a valid run; NOT RUN if no run was attempted. BLOCKED and NOT RUN never count as coverage or successful outcomes.

## 10. Required evidence package

| Evidence ID | Required evidence | Acceptance condition |
|---|---|---|
| PRV-01 | Frozen source/contract/vector registry | Exact repository, commit, versions and digests |
| PRV-02 | Approved immutable run manifest | Run/namespace/vector denominator and scope frozen |
| PRV-03 | Identifier registry | Unique run-bound IDs and collision/reuse checks |
| PRV-04 | Principal and process identity map | Issuer, role, process/job and effective capability evidence |
| PRV-05 | Authorization binding | Exact owner approval and scope; no inferred authority |
| PRV-06 | Operation/attempt ledger | Stable logical IDs, attempt lineage and canonical input digests |
| PRV-07 | Synthetic resource/version lineage | Exact immutable identities, content/metadata digests and namespace |
| PRV-08 | Lifecycle event stream | Producer, causal references, sequence and append-only continuity |
| PRV-09 | Independent observation bundle | Observer identity, read-only plan, exact targets and completeness |
| PRV-10 | Oracle assertion/verdict records | Frozen expectations and complete observation references |
| PRV-11 | Artifact manifest | Exact bytes, digests, schema and complete chain links |
| PRV-12 | Trust/attestation validation record | Identity, issuer, policy and limitations; if applicable |
| PRV-13 | Causal/completeness report | Gap, duplicate, orphan, replay, fork and ordering checks |
| PRV-14 | Append-only correction/publication log | Original preserved; supersession and publisher bound |
| PRV-15 | Independent verifier record | Verifier source/config, input digests and reproducible result |
| PRV-16 | Abort and protected-root evidence | Scope violations stop; protected assets remain outside scope |
| PRV-17 | Authorization and execution gate record | TEST-08 exact authorization before any future execution |

## 11. Future TEST-06 acceptance assertions

| ID | Assertion | Minimum evidence |
|---|---|---|
| PRV-T01 | Every selected vector has complete end-to-end provenance | One-to-one vector-to-chain mapping and denominator reconciliation |
| PRV-T02 | Source, contracts and expected state are immutable and run-bound | Full commit/version/digest and frozen manifest |
| PRV-T03 | Principal and process identities are attributable | Issuer-backed identity and effective capability evidence |
| PRV-T04 | Executor cannot self-authoritative observer/oracle/publisher records | Role separation and denied capability evidence |
| PRV-T05 | Logical operation and attempt identities are unambiguous | Stable operation ID, unique attempt IDs and payload binding |
| PRV-T06 | Synthetic resource/version lineage is exact | Namespace and immutable object/version digest chain |
| PRV-T07 | Events are complete and causally consistent | Sequence/cursor continuity and parent/happens-before validation |
| PRV-T08 | Independent observations bind exact immutable targets | Observer provenance, read-only scope and freshness/completeness |
| PRV-T09 | Oracle assertions and verdicts bind all required evidence | Assertion-level references and deterministic recomputation |
| PRV-T10 | Artifacts are byte-identical to their manifest bindings | Digest, schema and publication chain validation |
| PRV-T11 | Replay, duplication, substitution and fork are detected | Negative cases and preserved original evidence |
| PRV-T12 | Corrections are append-only and non-destructive | Supersession records with original history preserved |
| PRV-T13 | Signature/attestation claims are properly scoped | Exact signed-byte/context binding and explicit trust limitations |
| PRV-T14 | Completeness and provenance properties are reported separately | No hash-only, self-attested or partial-chain PASS |
| PRV-T15 | Same frozen evidence yields reproducible verification | Read-only replay with pinned verifier/policy |
| PRV-T16 | All failure/ambiguity cases fail closed | Typed errors and deterministic INDETERMINATE/BLOCKED handling |
| PRV-T17 | Protected roots and unauthorized systems are never used | TEST-03 isolation evidence and authorized non-invasive proof |
| PRV-T18 | Approval and execution authority are exact and independently bound | TEST-08 record and run scope match |

These are proposed acceptance assertions only. They are not executed tests and provide no coverage credit for the 87 lifecycle vectors.

## 12. Negative provenance scenarios

Future synthetic fixtures must include, where applicable:
- altered artifact bytes with unchanged manifest digest;
- valid digest but wrong source commit, spec version, vector or run;
- duplicate/reused operation, attempt, event, observation or artifact ID;
- missing parent, orphan event, causal cycle, sequence gap, fork and reordering;
- cross-run or cross-namespace object/version substitution;
- executor-created or executor-modified observer/oracle/publisher record;
- observer identity substitution, stale observation or incomplete pagination;
- signature valid under an untrusted/wrong-purpose identity, revoked/unknown key or wrong signed context;
- timestamp proof bound to payload but not exact signed bytes/context;
- replayed old attestation or evidence bundle presented as a new run;
- correction that overwrites or hides original evidence;
- missing selected vector or missing artifact omitted from the denominator;
- verifier/policy drift, canonicalization ambiguity and unsupported schema version;
- evidence publication to an unapproved destination or by an unauthorized publisher.

Fixture definitions and expected results must be frozen independently before execution. A negative fixture is not evidence of coverage until an authorized runner executes it and the independent oracle verifies its result.

## 13. Dependencies and closure conditions

TEST-06 closes only after all applicable conditions are implemented and evidenced:
1. TEST-01 runner produces a frozen, validated manifest and complete vector denominator.
2. TEST-02 adapters expose immutable synthetic identities, exact versions, event/lineage records and scoped capabilities.
3. TEST-03 effective isolation and principal/credential separation are technically proven.
4. TEST-04 independent observer/oracle collects and evaluates records without executor control.
5. TEST-05 deterministic schedules preserve operation/attempt/event causal references.
6. Source, spec, vector, run, principal, operation, resource, event, observation, verdict and artifact links validate end-to-end.
7. Completeness, integrity, authenticity, attribution, causal consistency and independence are evaluated separately.
8. Replay, duplicate, substitution, orphan, gap, fork, reordering and policy-drift cases are detected.
9. Evidence publication is append-only and independently verifiable; corrections preserve originals.
10. Trust policy, identity issuer, signing/attestation and time claims are explicit and validated if used.
11. Protected-root invariance and synthetic-only scope are established without unauthorized probes.
12. TEST-08 exact-scope owner authorization is obtained before execution.
13. TEST-07 remains a separate gate; no cleanup/deletion capability is introduced.

A contract, hash list, executor log, self-attestation, existing workflow permission or successful artifact upload cannot close TEST-06. Missing links or unproven trust/identity/independence keep it OPEN/BLOCKED/NOT VERIFIED as appropriate.

## 14. Current disposition

| Item | Status |
|---|---|
| TEST-01 | CONTRACT DOCUMENTED / IMPLEMENTATION NOT ESTABLISHED |
| TEST-02 | CONTRACT DOCUMENTED / IMPLEMENTATION NOT ESTABLISHED |
| TEST-03 | CONTRACT DOCUMENTED / EFFECTIVE ISOLATION NOT VERIFIED |
| TEST-04 | CONTRACT DOCUMENTED / INDEPENDENT ORACLE NOT ESTABLISHED |
| TEST-05 | CONTRACT DOCUMENTED / DETERMINISTIC CONCURRENCY NOT ESTABLISHED |
| TEST-06 | CONTRACT DOCUMENTED / LIFECYCLE-SPECIFIC PROVENANCE NOT ESTABLISHED |
| TEST-07 | OPEN / NOT ESTABLISHED |
| TEST-08 | NOT GRANTED — separate exact-scope authorization required |
| LDA-07 | NOT RUN; 87/87 lifecycle vectors remain NOT RUN |
| LDA-06 | PARTIAL / NOT VERIFIED |
| LDA-08 | HOLD / NOT VERIFIED |

No tests, compile, dry-run, fault injection, provisioning or GitHub Actions dispatch were performed. No secrets or permission values were accessed. No runtime/VPS/database/provider/recipient/backup/replica probes were performed. No source, schema, adapter, workflow, runner, permission, runtime or data changes were made. No destructive operation was performed.

**STAGE C.10 DOCUMENTARY CONTRACT COMPLETE — TEST-06 NOT CLOSED — LIFECYCLE-SPECIFIC PROVENANCE NOT ESTABLISHED — NO IMPLEMENTATION OR EXECUTION AUTHORITY.**
