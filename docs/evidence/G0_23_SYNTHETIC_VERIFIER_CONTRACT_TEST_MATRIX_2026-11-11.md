# G0.23 — Synthetic Verifier Contract Test Matrix

Date: 2026-11-11 (Asia/Ho_Chi_Minh)  
Branch: `feature/t0-centralized-data-feeder-p1-20261101`  
Baseline: `be802d46efd7399b84212c9724f70aadb49fa0a2` (G0.22 completion HEAD)  
Scope: synthetic-only verifier contract test design and abstract fixture catalog. Documentation-only; no verifier implementation or executable fixtures.

## 1. Executive disposition

**G0.23: TEST-DESIGN PASS — synthetic negative/positive contract cases and expected outcomes are specified. EXECUTABLE TESTS NOT RUN; verifier implementation and canonical envelope schema do not exist.**

This gate translates G0.22 into a deterministic test oracle and a set of wholly synthetic fixture scenarios. It defines what a future verifier must accept, block or reject without selecting cryptographic primitives or trusting caller assertions.

Because G0.22 deliberately left the physical envelope encoding, schema, signature profile, trust root, revocation source and verifier interface unresolved, creating executable payload fixtures now would prematurely freeze those choices. Accordingly, this report defines logical fixture records and expected outcomes only. It does not create JSON/YAML fixture files, test modules, mocks that pretend to perform cryptography, or a runnable verifier.

## 2. Exact scope and authority

Approved:
- Define synthetic test categories, logical fixture inputs and expected verifier outcomes.
- Specify fail-closed invariants and test-oracle rules.
- Identify which cases are contract-ready and which require owner/security decisions first.
- Record exact implementation prerequisites for a future executable suite.

Not approved or performed:
- Verifier, parser, envelope class/schema, cryptographic implementation or evaluator adapter.
- Executable tests, test fixtures on disk, fake production trust roots, generated keys or signatures.
- Changes to `pipeline/lifecycle_disposition.py` or its existing tests.
- CI workflow, workflow permissions, workflow dispatch, secrets, dependencies or artifact upload.
- Production evidence, credentials, real identities, actual keys, provider/network/database/VPS/runtime access.
- TEST-01–07 / 87-vector harness.
- Owner authorization or any lifecycle executor.
- Archive, quarantine, cleanup, expiry, compaction, VACUUM, deletion or other mutation.

## 3. Synthetic fixture rules

All future fixtures in this suite must:
- Use clearly synthetic identifiers with a reserved prefix such as `syn-` (for example `syn-object-001`, `syn-issuer-001`, `syn-evidence-001`).
- Use fabricated payload bytes and deterministic digests computed from those bytes under the eventually ratified profile.
- Use synthetic namespaces, object versions, policy revisions, inventory snapshots, timestamps and lineage.
- Never copy real user, account, market, ledger, model, T0/T1/T2, VPS, provider or production evidence.
- Never include credentials, tokens, private keys, trust-root secrets or actual personal data.
- State the single intended mutation from a valid baseline for each negative case, so the failure reason is isolated.
- Keep expected verifier outcome separate from the lifecycle evaluator disposition and from owner action authorization.

No actual fixture bytes or serialized envelope are committed in G0.23. The names and values below are logical fixture descriptors, not a wire-format schema.

## 4. Test oracle

The verifier has three conceptual outcomes from G0.22:
- `VERIFIED`: all mandatory checks pass for the declared purpose and exact scope; only then may a verified-facts value be materialized.
- `BLOCKED`: required evidence or trust state is unavailable, incomplete, stale, revoked, contradictory, unsupported or fails a verification prerequisite.
- `REJECTED`: the submitted envelope is malformed, ambiguous, oversized, uses an unsupported critical contract version/field, or violates a non-recoverable structural invariant.

Global assertions for every test:
1. Only `VERIFIED` may produce a verified-facts value.
2. `BLOCKED` and `REJECTED` produce no trusted facts and cannot be passed to the pure evaluator.
3. No verifier outcome grants owner authorization or execution authority.
4. No test may cause source mutation or a lifecycle action.
5. Caller-supplied booleans, labels, steward strings, inventory counts or `complete=true` claims are never accepted as proof without the corresponding authenticated evidence.
6. Unknown, missing, stale, contradictory or unavailable trust state must never be coerced to success.
7. Test output contains only synthetic identifiers and safe reason codes; no secret values.

## 5. Synthetic contract case matrix

### A. Positive control and issuer authority

| ID | Synthetic fixture mutation / condition | Expected | Purpose |
|---|---|---|---|
| SYN-01 | Fully consistent synthetic evidence; authenticated issuer has exact scoped authority; exact object/version, integrity, policy, inventory, sensitivity and freshness checks all pass | VERIFIED | Positive control for the complete path |
| SYN-02 | Claim sets `identity_verified=true`, but issuer identity proof is absent | BLOCKED | Caller boolean is not identity proof |
| SYN-03 | Issuer is unknown to the approved trust configuration | BLOCKED | Unknown issuer fails closed |
| SYN-04 | Issuer is authenticated but lacks authority for this data domain or claim category | BLOCKED | Authentication does not imply authorization |
| SYN-05 | Issuer authority is outside its valid time/scope | BLOCKED | Enforce scoped authority |
| SYN-06 | Steward field contains a plausible owner name, but no authenticated owner decision/authority evidence exists | BLOCKED | A name string is not owner approval |

### B. Exact subject binding and integrity

| ID | Synthetic fixture mutation / condition | Expected | Purpose |
|---|---|---|---|
| SYN-07 | Attestation subject object ID differs from the requested object ID | BLOCKED | Bind evidence to exact object |
| SYN-08 | Attestation version differs from the immutable requested object version | BLOCKED | Prevent version substitution |
| SYN-09 | Evidence reference resolves only to a mutable alias/path, not an immutable version | BLOCKED | Reject ambiguous subject resolution |
| SYN-10 | Payload bytes are changed while the claimed digest remains unchanged | BLOCKED | Recompute digest over exact bytes |
| SYN-11 | Digest and byte length do not match the resolved payload | BLOCKED | Verify content identity and length |
| SYN-12 | Authenticity proof is invalid under the eventually approved profile | BLOCKED | Reject invalid attestation/signature |
| SYN-13 | Proof is valid cryptographically but does not bind purpose, revision, subject version or policy context | BLOCKED | Prevent cross-purpose or cross-version replay |

### C. Provenance and inventory completeness

| ID | Synthetic fixture mutation / condition | Expected | Purpose |
|---|---|---|---|
| SYN-14 | Producer attestation references a different source/build/artifact revision | BLOCKED | Exact producer provenance |
| SYN-15 | One required parent/input lineage edge is missing | BLOCKED | No incomplete lineage |
| SYN-16 | Inventory claimant says `complete=true`, but an authoritative partition/cursor is absent | BLOCKED | Caller completeness boolean is insufficient |
| SYN-17 | Enumerated inventory count conflicts with authoritative snapshot count | BLOCKED | Detect truncated/inconsistent inventory |
| SYN-18 | A synthetic hold/dependency/copy/consumer exists in an authoritative source but is omitted from the submitted list | BLOCKED | Detect omitted obligations |
| SYN-19 | Inventory source is unavailable or pagination cannot reach a verified terminal cursor | BLOCKED | Inaccessible/partial inventory is unknown |

### D. Sensitivity and policy binding

| ID | Synthetic fixture mutation / condition | Expected | Purpose |
|---|---|---|---|
| SYN-20 | Derived copy claims PUBLIC while authenticated parent lineage is RESTRICTED | BLOCKED | Most-restrictive inheritance |
| SYN-21 | Sensitivity state is UNCLASSIFIED, CONFLICTED or PENDING_OWNER_DECISION | BLOCKED | Apply G0.17 fail-closed handling |
| SYN-22 | Parent/source sensitivity evidence is missing or unauthenticated | BLOCKED | Do not trust inherited-label arrays |
| SYN-23 | Policy identifier/version is stale, superseded or not the ratified policy for this scope | BLOCKED | Bind exact policy revision |
| SYN-24 | Declassification claim lacks authenticated exact-scope owner approval | BLOCKED | No automatic downgrade |

### E. Freshness, revocation and availability

| ID | Synthetic fixture mutation / condition | Expected | Purpose |
|---|---|---|---|
| SYN-25 | Evidence or inventory snapshot exceeds the owner-approved freshness window | BLOCKED | Stale evidence cannot pass |
| SYN-26 | Issuer key/attestation is revoked under the approved revocation source | BLOCKED | Enforce revocation |
| SYN-27 | Revocation status cannot be determined because the trust service is unavailable | BLOCKED | Unknown revocation is not “not revoked” |
| SYN-28 | Attestation, inventory and policy timestamps are contradictory or invalid under approved clock rules | BLOCKED | Enforce temporal consistency |

### F. Envelope structure and resource limits

| ID | Synthetic fixture mutation / condition | Expected | Purpose |
|---|---|---|---|
| SYN-29 | Malformed encoding, duplicate critical field or ambiguous duplicate key | REJECTED | Deterministic parsing |
| SYN-30 | Unsupported major contract version or unknown critical extension | REJECTED | No unsafe version fallback |
| SYN-31 | Envelope exceeds an owner-approved byte/depth/item limit | REJECTED | Bounded parser/resource use |
| SYN-32 | Required field has wrong type or violates a non-recoverable structural invariant | REJECTED | Reject malformed contract data |
| SYN-33 | Unknown non-critical extension appears | OPEN | Expected behavior depends on a ratified extension policy; do not assume ignore or reject |

### G. Downstream-use and output isolation

| ID | Synthetic fixture mutation / condition | Expected | Purpose |
|---|---|---|---|
| SYN-34 | Claim says no material decision use, but synthetic downstream-use reconciliation is incomplete | BLOCKED | Absence of evidence is not evidence of non-use |
| SYN-35 | Rebuildability assertion is true but exact inputs/transform/output binding is missing | BLOCKED | Caller assertion is not reproducibility proof |
| SYN-36 | Verifier returns BLOCKED or REJECTED while caller attempts to supply a positive facts object | REJECTED / no facts | Prevent caller bypass of verifier |
| SYN-37 | VERIFIED facts are altered after materialization | REJECTED by immutable-value boundary | Preserve immutability; exact enforcement mechanism remains open |
| SYN-38 | Any test attempts to interpret VERIFIED or REVIEWABLE as deletion permission | No authorization; action denied | Maintain authorization/execution separation |

## 6. Decision dependencies and test readiness

### Contract-ready behavioral expectations

The following expectations are already defined by G0.22 and can be used as logical test oracles without selecting cryptographic algorithms:
- Caller booleans do not authenticate claims.
- Authenticated identity without scoped authority is insufficient.
- Exact object/version and purpose binding are mandatory.
- Digest mismatch, incomplete lineage or inventory, sensitivity conflict, stale/revoked/unknown trust status and unavailable mandatory trust services fail closed.
- Malformed, ambiguous, unsupported-critical or over-limit envelopes are rejected.
- BLOCKED/REJECTED outcomes never produce trusted facts.
- No verifier result grants owner authorization or execution capability.

### Blocked pending owner/security decisions

Executable tests for these areas must wait until the relevant profile is ratified:
- Actual digest/signature verification and canonical byte representation.
- Trust-root, issuer/key registry, authority delegation and revocation source.
- Freshness duration, clock-skew tolerance, expiry and offline behavior.
- Physical schema, duplicate-key handling, extension policy and resource limits.
- Authoritative evidence stores, immutable-version resolvers and inventory registries.
- Verifier API/type and immutable verified-facts materialization.

SYN-12, SYN-13, SYN-25–28, SYN-29–33 and SYN-37 therefore remain logical cases only until their corresponding decisions and implementation exist. The expected high-level behavior is fixed where stated; the mechanics and numeric parameters are not.

## 7. Future executable test organization

After the owner ratifies the open decisions and a verifier implementation exists, a separate implementation approval should:
1. Freeze a versioned envelope schema and verifier interface.
2. Create a dedicated synthetic fixture directory; do not place fixtures beside production data or reuse real records.
3. Implement deterministic tests for each applicable SYN case, with one failure mutation per case.
4. Use a test-only synthetic trust configuration that cannot be loaded by production/runtime code.
5. Use actual cryptographic libraries only after the algorithm/profile and key handling are approved; do not mock signature success as proof of cryptographic correctness.
6. Verify that no test accesses the network, external trust provider, database, filesystem outside the isolated test fixture area, VPS or real credentials.
7. Run focused tests first, then the repository's approved broader suite; record exact source SHA, workflow run, job and artifact.
8. Keep CI permissions read-only unless a later explicit approval establishes a narrowly required permission. No CI workflow is authorized by this gate.

No exact fixture path, command, workflow, permission set or artifact policy is frozen here.

## 8. Gate matrix

| Area | G0.23 disposition |
|---|---|
| Synthetic test categories and logical fixture catalog | PASS |
| Expected VERIFIED/BLOCKED/REJECTED outcomes | PASS, subject to stated open dependencies |
| Positive full-path control | SPECIFIED; not executable |
| Forged identity/issuer/authority cases | SPECIFIED; not executable |
| Digest/signature and exact binding cases | SPECIFIED; cryptographic profile OPEN |
| Inventory/provenance completeness cases | SPECIFIED; authoritative registries OPEN |
| Sensitivity/policy inheritance cases | SPECIFIED; verifier implementation NOT PRESENT |
| Freshness/revocation cases | SPECIFIED; numeric/protocol policy OPEN |
| Malformed/oversized input cases | SPECIFIED; schema/resource limits OPEN |
| Downstream-use and no-authorization cases | SPECIFIED; implementation NOT PRESENT |
| Executable fixtures/tests | NOT CREATED |
| Test execution / CI workflow | NOT RUN / NOT DISPATCHED |
| Verifier implementation | NOT PRESENT / NOT AUTHORIZED |
| G0.24 evaluator adapter | NOT STARTED / SEPARATE APPROVAL |
| TEST-01–07 | 0/87; unchanged |
| Runtime/VPS inventory | NOT PERFORMED / NOT VERIFIED |
| Destructive authority | NOT GRANTED |

## 9. Explicit non-actions

Documentation-only. No source code, test module, executable fixture, schema, API, registry, adapter, runner, oracle, workflow, scheduler, permission, credential, key, database, storage, market data, model, ledger, VPS or runtime change. No tests or workflow dispatch. No network/provider/database/VPS access, inventory or secret scan. No archive, quarantine, cleanup, expiry, compaction, VACUUM, deletion or other mutation.

T0 remains independent and protected. CORE_LEDGER and AI_LEDGER remain separate. Paper-only and `AI_EXECUTION_ENABLED=false` remain unchanged.

## 10. Final verdict

**G0.23: TEST-DESIGN PASS — 38 synthetic contract cases specified; executable verification NOT RUN because no verifier implementation or ratified physical envelope/trust profile exists.**

This gate creates a test oracle, not proof that a verifier works. The next valid step is an owner/security decision package for the unresolved trust profile and implementation prerequisites, followed by a separate approval for verifier implementation and executable synthetic tests. G0.24 adapter, TEST-01–07, runtime inventory and any destructive executor remain separate gates.
