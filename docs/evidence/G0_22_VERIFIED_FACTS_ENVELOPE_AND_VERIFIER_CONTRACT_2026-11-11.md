# G0.22 — Verified-Facts Envelope and Evidence Verifier Contract

Date: 2026-11-11 (Asia/Ho_Chi_Minh)  
Branch: `feature/t0-centralized-data-feeder-p1-20261101`  
Baseline: `80e2e7fe9718c008716c50e7905f5523ed1870c7` (G0.21 completion HEAD)  
Scope: documentation-only contract design. No implementation, schema file, registry, adapter, test fixture, CI workflow, key operation or runtime access.

## 1. Executive disposition

**G0.22: DESIGN PASS — target trust boundary and required contract are specified; cryptographic profile, operational trust configuration and evidence authenticity remain NOT ESTABLISHED.**

The future lifecycle pipeline must not pass caller-authored mappings or caller-controlled booleans directly into the lifecycle evaluator as trusted facts. A distinct verifier boundary must authenticate the issuer and scoped authority, resolve exact evidence bytes and immutable versions, recompute integrity digests, validate an approved authenticity proof, reconcile inventory scope/completeness, verify policy and sensitivity lineage, and enforce freshness/revocation rules before it can materialize verified facts.

The evaluator remains a pure deterministic classifier. It receives only a verifier-produced, bounded, versioned, immutable verified-facts value. It does not retrieve evidence, parse untrusted serialized input, verify cryptography, consult registries, make owner authorization decisions or execute lifecycle actions.

This contract intentionally does **not** select a signature algorithm, hash/canonicalization profile, trust root, key hierarchy, revocation protocol, freshness duration, physical serialization, registry, API, database or executor.

## 2. Authority and scope

G0.22 is limited to the following design deliverables:
- Define the logical contents and invariants of a future verified-facts envelope.
- Define verifier responsibilities, trust inputs, verification order and fail-closed outcomes.
- Define the separation between untrusted claims, verified facts, pure disposition, owner authorization and any future executor.
- Record unresolved owner/security decisions required before implementation.

Not included or authorized:
- Any source, test, fixture, schema, API, registry, adapter, runner, oracle or workflow changes.
- Signature/key generation, key custody, trust-root installation, rotation or revocation.
- TEST-01–07 / 87-vector harness or G0.23 synthetic verifier tests.
- Runtime/VPS/data inventory, secret scanning, provider/network/database access.
- T0 canonical data access or mutation; T1 activation; PostgreSQL/TimescaleDB activation.
- Archive, quarantine, cleanup, expiry, compaction, VACUUM, deletion or other destructive operation.
- Owner authorization for any object or lifecycle action.

## 3. Required trust pipeline

1. **Untrusted claimant and source adapters** collect claims and references. All values are untrusted, including identity, provenance, completeness, sensitivity, steward, policy and rebuildability assertions.
2. **Evidence verifier** authenticates the issuer and authority; resolves evidence by immutable identity/version; reads exact bytes; recomputes digests; validates the selected authenticity proof; binds claims to the object, producer, source revision, policy and purpose; checks inventory closure and freshness/revocation.
3. **Verified-facts materializer** constructs a bounded immutable value only from successful verifier results. It must not copy through caller-supplied `*_verified` booleans as proof.
4. **Pure lifecycle evaluator** consumes only this verified-facts value and returns a disposition/reason set. It remains incapable of I/O or mutation.
5. **Separate owner authorization** approves or rejects an exact object/version, exact action, scope and expiry/conditions. Reviewability is not approval.
6. **Separate guarded executor** may be designed only under a later explicit approval. It must independently revalidate authorization and target identity immediately before action. G0.22 grants no executor authority.

## 4. Logical envelope contract

The following is a **logical contract**, not a committed JSON schema, Python class, wire format or database design. Exact field names and encoding remain subject to a later schema decision.

### 4.1 Envelope identity and version
The envelope must identify:
- Contract/schema identifier and major/minor version.
- Unique verification result identifier.
- Verification outcome and verifier implementation/version identity.
- Verification time and the evidence snapshot's own source time/revision, kept distinct.
- A stable binding to the exact subject object, immutable object version and namespace/domain.
- The intended verification purpose and policy context.

Unknown major versions, unsupported critical extensions, duplicate logical fields, ambiguous encodings, or unsupported required semantics must be rejected. No silent coercion, defaulting or downgrade is allowed.

### 4.2 Subject binding
The subject binding must be exact and unambiguous:
- Object identifier, namespace/data domain and immutable version or generation.
- Object type/data class from an explicitly supported vocabulary.
- Producer identity and exact producer source revision/build/artifact provenance where applicable.
- Parent/source object-version references for copies and derived objects.
- Expected content identity, length and digest after the verifier has read the exact bytes.

A mutable path, display name, tag, branch name or caller-provided URI alone is not an immutable object identity. Resolution must end at an exact versioned object or fail closed. Path-to-object binding and storage-specific race protections belong to the future adapter/executor design, not this document.

### 4.3 Issuer identity and scoped authority
The verifier must establish:
- Authenticated issuer/principal identity, not a string or boolean supplied in the claim.
- Issuer authority for the specific data domain, claim type, object scope and time interval.
- The authenticated binding between issuer, attestation and exact claim payload.
- Whether the issuer is permitted to assert producer provenance, inventory completeness, sensitivity classification, steward/policy status or rebuildability.

Authentication and authorization are separate checks. A valid identity without the required scoped authority is insufficient. Repository write access, CI success, a non-empty steward field or a claimant's own assertion does not establish owner authority. Owner-only assertions remain pending until backed by an explicitly approved owner-authentication and custody process.

### 4.4 Evidence manifest and integrity
Every evidence item needed for a material claim must be referenced by:
- Immutable evidence identifier and revision/version.
- Exact subject/object binding and claim purpose.
- Expected byte length and digest metadata.
- Issuer/producer and source revision where applicable.
- Authenticity-proof reference and verification result.
- Sensitivity classification and inherited source context.

The verifier must retrieve the exact version, enforce configured size bounds, recompute the digest over the exact bytes, compare it with the authenticated expected digest, and validate the authenticity proof over a precisely defined statement binding at minimum the issuer, subject, version, digest, length, evidence revision, purpose and policy context.

A syntactically valid digest is not verification. A digest without authenticated binding is not proof of issuer or integrity. A signature that does not cover the relevant binding fields is insufficient. The exact hash algorithm, signature scheme, canonical byte representation, domain separation, trust root and key lifecycle are **OPEN OWNER/SECURITY DECISIONS** and must not be guessed in implementation.

Secrets, private keys, tokens and trust-root material must never be copied into ordinary envelope fields, logs, test output or CI artifacts. The envelope may carry non-secret key identifiers and verification outcomes only where the eventual approved profile permits.

### 4.5 Provenance and transformation lineage
For each producer or transformation claim, the verifier must bind:
- Producer identity and authorized role.
- Exact source commit, build, artifact or immutable deployment identity as applicable.
- Exact input object versions and their digests.
- Transformation/configuration identity and version.
- Output object version and recomputed digest.
- Parent-child lineage edges, with no unresolved parent references.

A source commit alone does not prove which bytes ran; a build label alone does not prove source; an artifact name alone does not prove artifact identity. Missing or contradictory provenance is unverified and blocks positive eligibility.

### 4.6 Inventory scope and completeness
Completeness is not a free-standing boolean. The verifier must validate an inventory statement that defines:
- Inventory authority and the exact namespace/domain/object scope.
- Snapshot/revision identifier and source generation or cursor.
- Included inventory classes (holds, dependencies, consumers, copies, replicas, backups, lineage parents/children and other applicable obligations).
- Expected partitions, pagination/cursors, counts or closure markers appropriate to the authoritative source.
- Snapshot consistency and evidence that enumeration reached a terminal, complete state.
- Reconciliation across authoritative sources where a single registry cannot establish closure.

A producer-supplied `complete=true`, a self-selected list, or a successful partial query cannot establish completeness. Missing partitions, inaccessible sources, pagination gaps, stale snapshots, conflicting counts, unknown consumers or unresolved lineage must produce a blocked result. The authoritative registries and their adapters are not selected or authorized in G0.22.

### 4.7 Policy and sensitivity binding
The verifier must bind the exact ratified policy identifier, version and content digest applicable to the claim and scope. It must authenticate the authority that issued any owner/steward decision; a policy name or version string alone is not enough.

Sensitivity must follow the G0.17 owner-ratified rules:
- Ordered labels: `PUBLIC < INTERNAL < CONFIDENTIAL < RESTRICTED`.
- Non-label states: `UNCLASSIFIED`, `CONFLICTED`, `PENDING_OWNER_DECISION`.
- Unknown, stale, conflicting or unauthenticated classification fails closed and is treated as RESTRICTED pending resolution.
- Most-restrictive-wins inheritance applies across copies, backups, replicas, exports and derived outputs; no automatic downgrade.
- Declassification requires exact-scope owner approval and evidence.

The verifier must resolve and authenticate the complete source/parent chain and calculate the effective sensitivity; it must not trust a claimant-supplied inherited-label array. Credentials, keys, tokens, signing material and trust-root secrets remain RESTRICTED and their values must not be exposed.

Sensitivity is independent of lifecycle disposition. It cannot grant reviewability, satisfy retention floors, authorize archive/deletion or enable execution.

### 4.8 Rebuildability and downstream-use claims
Where a disposition depends on rebuildability or absence of material decision use, the verifier must require evidence bound to exact retained inputs, transform/code/configuration versions and output identity. It must reconcile relevant downstream uses, including signals, risk decisions, ledgers, audit/reconstruction records and consumers.

A claimant's `proven=true` or `material_decision_use=NO` is not proof. Unknown use, incomplete downstream coverage or irreproducible output remains blocked. Known material use remains retained until all applicable obligations are closed. G0.22 does not define a replay system or authorize access to ledgers.

### 4.9 Freshness, revocation and time
The contract requires verifier-enforced freshness and revocation checks for issuer authority, evidence attestations, policy versions, inventory snapshots and owner decisions. The verifier must distinguish:
- Evidence creation/source time.
- Inventory snapshot time or revision.
- Attestation/decision time.
- Verification time.
- Any expiry or revocation effective time.

Missing, future-dated beyond permitted clock tolerance, stale, expired, revoked, superseded or temporally contradictory evidence must fail closed. Offline/unavailable revocation status must not be interpreted as “not revoked”.

**No numeric freshness window, clock-skew tolerance, expiry default, revocation source/protocol, cache lifetime or offline grace period is selected here.** These are explicit owner/security decisions before implementation.

## 5. Verified-facts output invariants

A future verifier-produced value must satisfy all of the following:
- It is materialized only by the trusted verifier boundary; callers cannot construct or mutate it through a public untrusted mapping path.
- It is immutable for the lifetime of one evaluation and contains only bounded, normalized, validated values.
- It identifies the verifier and contract version and carries references to the verification evidence needed for audit.
- Every positive fact is traceable to authenticated evidence, exact object/version and a verified issuer with scoped authority.
- No caller-controlled `identity_verified`, `producer_provenance_verified`, `complete`, `proven` or similar boolean can independently establish trust.
- Unknown, missing, stale, conflicting, malformed, unsupported or unauthenticated critical facts remain explicit and fail closed; they are never silently converted to false, empty, current or complete.
- Unsupported data classes remain unsupported until their exact mapping is separately ratified. No inferred aliases.
- Secret values are excluded.
- It cannot carry owner action approval or executor capability.

The evaluator should eventually accept a distinct verified-facts type rather than arbitrary `Mapping`. The exact type and migration path are not defined or approved in G0.22.

## 6. Verifier decision outcomes

The verifier should return a small closed outcome set, conceptually:
- **VERIFIED:** all required evidence, identity, authority, binding, completeness, policy, sensitivity and freshness checks passed for the declared purpose and scope.
- **BLOCKED:** required evidence is unavailable, incomplete, stale, revoked, contradictory, unsupported, out of scope or fails a verification check.
- **REJECTED:** the envelope is malformed, ambiguous, oversized, uses an unsupported critical version/field, or violates a non-recoverable contract invariant.

These are verifier outcomes, not lifecycle dispositions. A VERIFIED envelope does not imply `REVIEWABLE_NONCANONICAL`, owner approval, retention-floor completion or permission to mutate. The evaluator still applies its existing precedence and fail-closed rules. A BLOCKED or REJECTED result must never be coerced into an evaluator input.

## 7. Required verifier processing sequence

1. Enforce transport/input byte limits before parsing; reject malformed encoding and duplicate/ambiguous fields.
2. Parse only the supported envelope version; reject unsupported critical fields and schema ambiguity.
3. Authenticate issuer identity and validate scoped authority for every asserted claim category.
4. Resolve exact subject and evidence versions; reject mutable or ambiguous references.
5. Read bounded exact evidence bytes and recompute content digests.
6. Validate the approved signature/attestation profile and all subject, issuer, purpose, revision and policy bindings.
7. Verify producer/build/input/output lineage and exact provenance.
8. Obtain authoritative inventory snapshots and prove scope/partition/cursor closure and reconciliation.
9. Resolve policy and sensitivity inheritance through authenticated lineage; apply G0.17 fail-closed semantics.
10. Verify rebuildability and downstream-use evidence when required by the lifecycle class.
11. Check freshness, expiry, revocation and temporal consistency using an approved policy.
12. Materialize an immutable verified-facts value, or return BLOCKED/REJECTED with safe reason codes and no trusted facts.

The exact order may be optimized only if no untrusted claim can bypass a prerequisite. No partial verification may be represented as VERIFIED.

## 8. Failure behavior and information handling

- Fail closed on unavailable trust services, unknown issuer, insufficient authority, missing evidence, digest mismatch, invalid signature, unknown key status, unresolved revocation, incomplete inventory, stale policy, lineage gaps, sensitivity conflicts or downstream-use uncertainty.
- Do not downgrade a failure to a warning to preserve availability.
- Do not emit raw secret values, key material, credentials, RESTRICTED payloads or unrestricted evidence excerpts in logs or CI artifacts.
- Expose stable, non-sensitive reason codes and correlation identifiers; avoid leaking sensitive object contents through error text.
- Do not let callers choose the verifier's trust roots, policy snapshot, allowed issuer set or freshness rules through the submitted envelope.
- No fail-open cache or stale-verification reuse. Any future cache semantics require explicit owner/security policy and must be bound to exact evidence and revocation state.
- Verifier failure must not mutate source objects or trigger cleanup.

## 9. Open decisions before implementation

These decisions are deliberately unresolved and require a separate owner/security decision package:
1. Cryptographic integrity/authenticity profile: hash algorithm/version, signature or attestation format, signed statement fields, canonical serialization, domain separation and algorithm agility.
2. Trust architecture: root(s), issuer identity source, delegated authority model, key custody, hardware/software protection, rotation, compromise response and revocation.
3. Canonical envelope encoding and exact schema/versioning rules, including duplicate keys, extension handling and compatibility.
4. Authoritative evidence stores and exact immutable-version resolution for each data class.
5. Authoritative registries and closure proofs for holds, dependencies, consumers, copies, backups, replicas and lineage.
6. Freshness windows, clock-skew tolerance, expiry, revocation source/protocol, outage behavior and cache policy.
7. Owner/steward authentication and exact-scope approval evidence.
8. Exact supported data-class vocabulary and mapping to G0.17 semantic domains.
9. Resource limits: maximum envelope/evidence bytes, item counts, nesting/depth, pagination, verifier timeouts and bounded retries.
10. Audit record custody, retention, tamper evidence and safe CI/report redaction.
11. Whether and how verified-facts values are bound to a single evaluation, process boundary and verifier instance.
12. Independent review and implementation/testing gates, including G0.23 synthetic tests and G0.24 adapter assessment.

No item above is resolved by this design. Do not infer a default from library conventions or existing caller fields.

## 10. Gate matrix

| Area | G0.22 disposition |
|---|---|
| Logical verified-facts envelope contract | DESIGN PASS |
| Verifier responsibilities and processing boundary | DESIGN PASS |
| Exact subject/evidence binding requirements | SPECIFIED; implementation NOT PRESENT |
| Issuer authentication and scoped authority | NOT IMPLEMENTED / NOT VERIFIED |
| Digest recomputation and cryptographic authenticity | NOT IMPLEMENTED / NOT VERIFIED |
| Provenance and inventory completeness proof | NOT ESTABLISHED |
| Policy and sensitivity lineage authentication | NOT ESTABLISHED |
| Freshness and revocation enforcement | NOT IMPLEMENTED; policy values OPEN |
| Physical schema, registry, adapter or API | NOT DEFINED / NOT AUTHORIZED |
| Cryptographic/key-management profile | OPEN OWNER/SECURITY DECISION |
| G0.23 synthetic verifier tests | NOT STARTED / SEPARATE APPROVAL |
| G0.24 evaluator adapter | NOT STARTED / SEPARATE APPROVAL |
| TEST-01–07 | 0/87; unchanged |
| Runtime/VPS inventory | NOT PERFORMED / NOT VERIFIED |
| Destructive authority | NOT GRANTED |

## 11. Next gates and explicit limits

Proposed sequence:
- **G0.23 — Synthetic verifier contract test design/fixtures:** requires separate bounded approval. Use wholly synthetic evidence and identities; test forged claims, wrong issuer/authority, digest tampering, signature/binding mismatch, stale/revoked evidence, inventory omissions, sensitivity inheritance conflict, policy mismatch, malformed/duplicate/oversized envelopes and unavailable trust services. No production credentials or evidence.
- **Owner/security decision package:** ratify the open cryptographic, trust-root, encoding, freshness/revocation, registry and resource-limit choices before implementation.
- **G0.24 — Pure evaluator adapter assessment:** separate approval, and only after the verified-facts contract and required trust decisions are ratified. No registry/runtime integration by default.
- **Implementation and CI:** each separately scoped; no implicit approval from G0.22.
- **TEST-01–07, runtime inventory and any executor:** remain independent approval gates.

No source/test/fixture/schema/API/registry/adapter/runner/oracle/workflow/scheduler/permission/credential/database/storage/market-data/model/ledger/VPS/runtime changes. No test or workflow dispatch. No network/provider/database/VPS access or inventory. No key operation, archive, quarantine, cleanup, expiry, compaction, VACUUM or deletion.

T0 remains independent and protected. CORE_LEDGER and AI_LEDGER remain separate. Paper-only and `AI_EXECUTION_ENABLED=false` remain unchanged.

## 12. Final verdict

**G0.22: DESIGN PASS — a bounded verified-facts envelope and evidence-verifier contract is specified. Trust authenticity, cryptographic profile, operational evidence sources and enforcement are NOT ESTABLISHED.**

This design does not make the current lifecycle evaluator trustworthy for external claims by itself. Until a separately approved verifier is implemented and tested against an owner-ratified trust profile, the existing caller-supplied facts remain untrusted and all positive lifecycle dispositions remain non-authorizing. No archive, cleanup, expiry, compaction, VACUUM, deletion or other mutation is permitted by this gate.
