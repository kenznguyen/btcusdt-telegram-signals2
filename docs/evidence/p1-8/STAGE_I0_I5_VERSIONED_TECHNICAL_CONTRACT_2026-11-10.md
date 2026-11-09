# Stage I.0–I.5 — Versioned Technical Contract (Documentary Baseline)
Date: 2026-11-10
Contract ID: `H5-LIFECYCLE-TECHNICAL-CONTRACT`
Contract version: `1.0.0-draft`
Branch: `feature/t0-centralized-data-feeder-p1-20261101`
Status: DOCUMENTARY BASELINE; NOT IMPLEMENTED; NOT EXECUTABLE.

## I.0 — Authority, source baseline and contract status

The owner approved automatic execution of Stage I as the next documentary step after Stage H. This document translates approved architecture directions into a versioned, provider-neutral contract. It is not a production specification, executable schema, implementation authorization, test authorization, evidence-provider selection or lifecycle authorization.

Approved Stage H directions:
- G-DEC-01: RFC 8785 JCS + SHA-256.
- G-DEC-02: layered per-run synthetic isolation.
- G-DEC-03: distinct least-privilege principals.
- G-DEC-04: provider-neutral hybrid Git index plus separately versioned evidence payload destination.
- G-DEC-05: independent exact-version verifier.
- G-DEC-06: governance requirements approved; operational retention/recovery values remain OPEN.

Canonical source fetched for this stage:
- Stage H report: `docs/evidence/p1-8/STAGE_H0_H5_OWNER_DECISION_RESOLUTION_2026-11-10.md`, blob `12ca1aba795bd0d448d2c2b5f28734820204d93b`.
- Stage C.14 matrix: `docs/evidence/p1-8/STAGE_C14_87_VECTOR_TEST01_07_APPLICABILITY_TRACEABILITY_MATRIX_2026-11-10.md`, blob `12bba6c475fc2ad8c4e2246e75034ede22d3bc20`.
- Project handoff at start: `docs/PROJECT_SESSION_HANDOFF.md`, blob `a25eff3baf2b85c62f5dfde651bd95f79d18cb85`.

The Stage C.13 integrated schema/evidence map is referenced by the prior project record as blob `c43c8bfbccaf698d6670f33fab66ee12d2072a7f`. The expected filename/path was not resolved by the current GitHub file lookup (404), so this stage does not claim a line-by-line reconciliation against C.13. That reconciliation is OPEN and must use the exact canonical path/blob before any contract can be declared fully reconciled.

### Normative language

- **MUST / MUST NOT**: required for any future implementation claiming conformance.
- **SHOULD / SHOULD NOT**: recommended unless a documented owner-approved exception exists.
- **OPEN**: no value or mechanism may be inferred.
- **NOT VERIFIED**: a requirement exists but no effective technical evidence establishes it.
- **BLOCKED**: fail-closed disposition; no success or permission may be inferred.

This is a draft contract baseline. It does not close technical gates.

## I.1 — Canonical serialization, digest and identifier profile

### 1.1 Data model

Future manifests and evidence envelopes MUST be represented as UTF-8 JSON data compatible with RFC 8785 JCS. The parser MUST reject duplicate object member names before canonicalization. Inputs containing invalid UTF-8, non-finite numbers, unsupported numeric forms or values outside the selected interoperable data model MUST be rejected.

Canonicalization MUST NOT silently normalize Unicode strings. Strings are preserved as supplied, subject to valid Unicode and the JCS profile. Any domain-specific normalization, if later required, must be a separately versioned transformation before the canonicalization boundary.

Financial and other precision-sensitive quantities SHOULD use typed integer base units or a separately specified decimal-string representation. Binary floating-point MUST NOT be used as an implicit authoritative financial representation. Integer bounds and decimal grammar remain OPEN.

### 1.2 Digest profile

- Canonical-record digest: SHA-256 over the UTF-8 bytes emitted by the approved JCS implementation.
- Source-byte digest: SHA-256 over the exact original bytes when byte-level provenance is required.
- Canonical and source-byte digests are distinct fields and MUST NOT be substituted for one another.
- The digest algorithm and canonicalization profile MUST be explicit in the envelope.
- A record MUST exclude its own digest field from the canonical digest input; the exact envelope construction and field names remain OPEN pending golden-vector review.

### 1.3 Domain-separated identifiers

Identifiers derived from content MUST use domain separation so that identical bytes in different object classes do not silently share semantic identity. The logical construction is:

`SHA-256(UTF8(domain_label) || 0x00 || canonical_bytes)`

The domain-label registry, identifier encoding (hex/base64url), truncation policy (if any), collision handling and version namespace remain OPEN. No shortened digest is permitted unless a future profile explicitly specifies it.

### 1.4 Schema evolution

- Every serialized object MUST declare a schema identifier and major version.
- Major versions are immutable; incompatible changes require a new major version.
- Additive optional fields are allowed only under a documented compatibility rule.
- Unknown major versions, unknown critical fields, missing required fields, duplicate keys and digest mismatches MUST fail closed.
- Readers MUST NOT silently discard unknown critical fields.
- Schema migrations MUST preserve source identity and provide an explicit source/target version relation.

### 1.5 Conformance fixtures required before freeze

A future conformance suite must cover object-key ordering, escaping, Unicode edge cases, integer limits, decimal encoding, duplicate keys, invalid UTF-8, negative zero/number edge cases, non-finite values, unknown fields/versions, digest self-exclusion, source-byte versus canonical digest, domain separation and tamper detection.

No library/version, integer range, decimal grammar, digest envelope, domain registry or golden vector is selected in Stage I. These are OPEN. No tests are run or authorized.

## I.2 — Synthetic resource and namespace contract

### 2.1 Identity and scope

Every future run MUST have:
- globally unique `run_id`;
- unique `namespace_id`;
- immutable frozen manifest identifier and digest;
- explicit contract/schema version;
- start/terminal state and causal event references.

Every fixture, resource, operation, observation, verdict and artifact MUST carry the same run and namespace binding. Missing, mismatched, reused or cross-run identifiers MUST fail closed.

Exact ID format, entropy source, uniqueness guarantee and run lifecycle states remain OPEN.

### 2.2 Resource classification

Every discovered resource MUST be classified as exactly one of:
- `SYNTHETIC`: positive evidence proves creation/ownership inside the exact run namespace;
- `PROTECTED`: explicitly protected by policy or owner boundary;
- `UNKNOWN`: identity, ownership or scope cannot be established;
- `UNCLASSIFIED`: inventory is incomplete or classification has not completed.

Only positively proven `SYNTHETIC` resources may be eligible for a future synthetic lifecycle manifest. `PROTECTED`, `UNKNOWN` and `UNCLASSIFIED` MUST be excluded. A missing inventory entry is not evidence that a resource does not exist.

### 2.3 Layered isolation requirements

Future implementation MUST provide and independently evidence all applicable layers:
1. Per-run namespace and resource ownership.
2. Synthetic-only storage/database scope.
3. Distinct least-privilege identity and credentials.
4. Filesystem/mount allowlists; no writable path outside the designated synthetic root.
5. Default-deny network egress with explicit dependency allowlist.
6. Explicit resource API/operation allowlist.
7. Independent observation of effective—not merely declared—boundaries.

The concrete container/VM/database/filesystem/network technology and policy values remain OPEN. A configuration file or workflow declaration alone is insufficient proof. Cross-run access, protected-root reachability, unknown target, ambiguous acknowledgement or incomplete inventory MUST result in BLOCKED/NOT VERIFIED.

### 2.4 Lifecycle authority boundary

This contract defines containment only. It grants no delete, archive, expiry, overwrite, compaction, vacuum, cleanup or other destructive capability. Option C — No Destructive Authority remains ACTIVE. Even a non-mutating dry-run requires its own separately scoped authorization.

## I.3 — Principal and capability contract

### 3.1 Principal roles

| Principal | Required capability | Forbidden capability |
|---|---|---|
| Owner/controller | Approve exact scope; inspect evidence | Be treated as executor or independent verifier |
| Executor | Invoke frozen operations through bounded adapter | Access protected resources; author authoritative oracle/verifier evidence |
| Adapter | Enforce resource namespace and operation allowlist | Expand target scope or bypass policy |
| Observer | Read-only capture of actual state/events | Mutate resources or trust executor assertions as observations |
| Oracle/evaluator | Compare frozen expected state with observer output | Mutate target state or accept executor-authored expected results |
| Evidence publisher | Publish run-bound evidence and return exact version identity | Alter prior versions or issue correctness verdict |
| Independent verifier | Read exact versions and independently validate evidence | Modify source evidence or rely solely on executor self-attestation |

The deployment may combine observer and oracle only if the future contract proves technical independence from executor and preserves read-only access. Publisher and verifier MUST remain separate trust principals.

### 3.2 Identity binding

Each authenticated action MUST be attributable to immutable issuer/subject, principal role, process/job/build identity, run_id, namespace_id, effective resource scope, operation, authorization decision and capability snapshot. Credential source and validity interval must be recorded without exposing secret material.

Role labels are not proof of separation. If the platform cannot demonstrate effective identity and capability separation, the corresponding gate remains NOT VERIFIED.

Identity provider, token format/lifetime, policy language, credential rotation and effective permission evidence remain OPEN. No permission changes or credential probes are authorized.

## I.4 — Evidence manifest and verifier interface

### 4.1 Logical evidence envelope

A future evidence manifest MUST bind, at minimum:
- contract ID/version and schema/profile identifiers;
- source commit SHA and relevant source blob SHAs;
- vector catalogue identity/version and exact vector IDs;
- run_id, namespace_id and frozen manifest digest;
- principal, process, workflow/job and toolchain identities;
- operation/attempt identifiers and target resource identities/versions;
- causal event references and event ordering metadata;
- observer observations and oracle verdict references;
- artifact source-byte and canonical digests;
- destination identity, object key and exact immutable object-version identifier;
- verifier identity, policy/build identity, verification time source and result.

Exact field names, required/optional status, event clock semantics, timestamp authority, object-version syntax and envelope nesting remain OPEN for the canonical schema profile. No timestamp or freshness threshold may be invented.

### 4.2 Verifier interface

The logical verifier input is a frozen manifest plus exact evidence object references and the applicable trust/policy profile. The verifier MUST independently retrieve the referenced bytes and validate:
1. exact object-version identity and byte retrieval;
2. source-byte and canonical digests as applicable;
3. schema/profile and required-field validity;
4. source SHA and vector catalogue binding;
5. run/namespace consistency and no cross-run references;
6. principal/capability separation evidence;
7. causal reference closure and event ordering;
8. observer/oracle provenance and completeness;
9. artifact completeness against the frozen manifest;
10. protected/unknown resource exclusion and evidence containment.

The verifier result vocabulary is:
- `PASS`: all required assertions have independently verified evidence;
- `FAIL`: verified evidence demonstrates a contract violation;
- `INDETERMINATE`: required evidence is missing, inaccessible, conflicting or unverifiable;
- `BLOCKED`: prerequisite, authority or isolation gate prevents evaluation.

Missing evidence MUST NOT be treated as PASS or as proof of absence. Executor success or upload success MUST NOT be treated as verification success. Verifier trust roots, signature model, binary/build provenance, output schema and result-signing mechanism remain OPEN.

### 4.3 Destination boundary

GitHub remains the source of project code, decisions and evidence index/manifests. A separate versioned evidence-payload destination is the approved target direction, but provider/account/region/service is NOT SELECTED. Future selection requires separate owner decision and evidence of exact-version retrieval, append-only/versioning enforcement, ownership, trust boundary, access policy, retention/hold, inventory and recovery.

No external evidence destination has been provisioned or probed.

## I.5 — Retention/recovery governance, traceability and closure criteria

### 5.1 Retention and recovery decision fields

Before destination approval, a future owner decision must explicitly set:
- data/evidence classification and accountable owner;
- retention duration and start/stop semantics;
- legal/administrative hold authority and release procedure;
- immutable versioning/append-only enforcement;
- inventory enumeration and completeness evidence;
- backup scope, cadence and ownership;
- recovery objective and recovery procedure;
- restore verification and evidence integrity checks;
- authorized disposition procedure and separately approved destructive authority.

All numeric durations, recovery objectives, provider features, backup schedule and hold semantics remain OPEN. No defaults are inferred. If any required field or enforcement evidence is missing, destination readiness remains BLOCKED.

Option C remains ACTIVE: no deletion, expiry, archive, overwrite, compaction, vacuum or cleanup authority.

### 5.2 87-vector traceability

The C.14 matrix is the current documentary traceability baseline:
- source definitions reconciled: 87/87;
- unique matrix rows: 87/87;
- design-level TEST-01–07 mapping: 87/87;
- executable bindings established: 0/87;
- executed vectors: 0/87;
- lifecycle status: 87/87 NOT RUN.

This contract does not alter the vector denominator, source definitions, expected outcomes or assertion mappings. Future contract fields must permit exact binding of each vector to a frozen fixture, expected outcome, run, observer evidence, oracle verdict and artifact set. Mapping is not executable coverage.

The exact C.13 logical map reconciliation remains OPEN because its canonical path was not resolved in the current read. C.15 and Stage D–H status is preserved; no technical gate is upgraded.

### 5.3 Documentary acceptance criteria for Stage I

Stage I is complete as a draft documentary baseline when:
- all five contract areas (I.1–I.5) are documented;
- every unresolved value is explicitly OPEN;
- authority and fail-closed boundaries are explicit;
- the 87-vector denominator and NOT RUN status are preserved;
- source references and known retrieval limitations are recorded;
- the report and handoff are committed on the existing branch and read back from GitHub.

These criteria do not constitute technical conformance, implementation readiness or lifecycle test acceptance.

### 5.4 Open decision register

| ID | Contract area | OPEN item / required future evidence |
|---|---|---|
| I-OPEN-01 | JCS | Exact library/version and conformance profile |
| I-OPEN-02 | Data model | Integer bounds, decimal grammar, Unicode/parser edge behavior |
| I-OPEN-03 | Digest | Envelope fields, domain-label registry, identifier encoding |
| I-OPEN-04 | Schema evolution | Compatibility matrix and migration rules |
| I-OPEN-05 | Isolation | Namespace technology, storage topology, filesystem/network policy and negative proof |
| I-OPEN-06 | Identity | Identity provider, credential model, effective capability evidence |
| I-OPEN-07 | Evidence destination | Provider/owner, immutable version semantics, append-only proof |
| I-OPEN-08 | Verifier | Trust roots, build provenance, output/signature contract |
| I-OPEN-09 | Retention | Duration, hold/release authority, backup/recovery values |
| I-OPEN-10 | C.13 reconciliation | Resolve exact canonical path/blob and perform explicit field-level crosswalk |
| I-OPEN-11 | Lifecycle authority | TEST-08 exact-scope authorization and any separate destructive authority |

### 5.5 Next gate

After owner review of this draft, the next permissible documentary activity is a contract reconciliation/revision that resolves source crosswalks and explicitly adjudicates OPEN fields. Implementation requires a separate explicit owner approval with exact files and acceptance criteria. TEST-08 remains a separate exact-scope authorization and is not granted by Stage I. Any lifecycle execution remains prohibited until implementation, isolation and evidence prerequisites are technically established and TEST-08 is explicitly approved.

## Final status and boundaries

- Stage I.0–I.5: DOCUMENTARY DRAFT BASELINE COMPLETE.
- Contract version: `1.0.0-draft`; not frozen, not implemented, not executable.
- C.13 field-level reconciliation: OPEN / NOT VERIFIED.
- C.14 traceability: 87/87 design-mapped; 0/87 executable; 87/87 NOT RUN.
- TEST-01/02/04/05/06/07: NOT ESTABLISHED; TEST-03: NOT VERIFIED; TEST-08: NOT GRANTED.
- LDA-06: PARTIAL / NOT VERIFIED; LDA-08: HOLD / NOT VERIFIED.
- Technical readiness: BLOCKED; implementation and execution: NOT AUTHORIZED.
- Option C — No Destructive Authority: ACTIVE.
- `AI_EXECUTION_ENABLED=false`; paper-only; no live orders.
- No code/schema/adapter/runner/workflow/permission/runtime/data changes.
- No tests, compilation, dry-run, fault injection or Actions dispatch.
- No secrets, VPS, T0/T1, database, provider, recipient, backup or replica probes.
- No provisioning, external evidence publication or destructive operation.
- No workflow run or artifact is claimed.

**STAGE I.0–I.5 COMPLETE — DOCUMENTARY DRAFT BASELINE ONLY.**
