# A2.3 Draft — Static Consistency and Adversarial Self-Review

**Date:** 2026-11-11  
**Branch:** `feature/t0-centralized-data-feeder-p1-20261101`  
**Review type:** Same-session author self-review; documentation/static inspection only  
**Disposition:** **PARTIAL PASS WITH BLOCKERS / NOT INDEPENDENT REVIEW / NOT FROZEN / NO IMPLEMENTATION AUTHORITY**

## 1. Exact review inputs

| Input | Exact blob |
|---|---|
| Checkpoint Contract v1 | `a6825270d59bde274bfe765d5f942144b66a84de` |
| A1 | `00fdad293e129562145ab930507a4e6b9c2bf23d` |
| A2.2 | `d9f93bf390d107381b7135c3073aeca0d14894d4` |
| Stage II Ed25519 adapter contract | `e1b12fc1fc4b463fc82ff8b6b5f0b2701af5888b` |
| B + E2 schema draft | `6a47509fc902cfe40188f890d06f20af23cffeec` |
| A2.3 review candidate | `14fd2bcce2f4c466d2c448863403fba9971131df` |

The review candidate is the A2.3 document blob, not a frozen or owner-approved normative contract.

## 2. Checks performed

### 2.1 Option B against A1 §14.4

**PARTIAL PASS.** A1 §14.4 explicitly allows provenance/authorization evidence either in the signed Signature Statement or in a separately signed authorization-evidence object whose exact ID/digest is bound by the statement. A2.3 follows the latter alternative and binds both the exact AEO body descriptor and its independently verifiable signature-envelope descriptor.

The main statement's provenance fields are explicitly superseded rather than silently removed. Required software/build, request/decision, authority and custody facts remain in the AEO dependency closure.

### 2.2 Option E2 against A1 §4.4 and A2.2 §3.3

**PASS AT DESIGN LEVEL.** A1 §4.4 requires envelope identity/digest to be computed after signature creation and not included in its own signed statement. A2.3 creates the completed envelope first, computes exact digest/length, and then assigns a detached descriptor ID. A2.2 §3.3's signed preassigned `signature_envelope_id` is explicitly superseded in full.

UUIDv4 descriptor IDs are independent of descriptor/envelope bytes. Same-ID/different-bytes is a hard conflict; exact duplicate bytes are idempotent; uncertain writes require readback before retry.

### 2.3 Signature primitive and exact bytes

**PASS AT INTERFACE LEVEL.** A2.3 preserves the stateless adapter boundary: exact preimage bytes, strict Ed25519 SPKI DER and a 64-octet raw signature. The main checkpoint statement continues to use A1 §4.3. The AEO signature statement has a distinct purpose-specific type/domain so it cannot be interpreted as a checkpoint statement and does not fabricate checkpoint fields.

The AEO domain hex was independently checked against the literal ASCII domain plus one NUL octet. A fixed SHA-256 domain KAT is included. This is not an independent Ed25519 implementation or external review.

### 2.4 Profile and algorithm alignment

**PARTIAL PASS.** A2.3 records the already owner-approved Ed25519 PureEdDSA choice and defines a purpose-specific AEO profile proposal. Both profiles use strict DER SPKI, parameters absent, 32-byte Ed25519 public key and 64-byte raw signature. A2.2's legacy statement that production algorithm was unselected is explicitly addressed by the new §5.1 profile amendment.

Still required: exact Trust Policy allowlist schema/entries for the AEO issuer role/profile/purpose, final profile registry freeze and exact dependency/build provenance. No trust policy instance or root is created.

### 2.5 AEO non-self-authentication

**PARTIAL PASS / OWNER DECISION REQUIRED.** A2.3 requires the AEO issuer to be authorized by an already accepted Trust Policy and distinct from the subject checkpoint signer principal/key. This prevents the subject signer from issuing its own provenance authorization. This is a substantive security constraint introduced by the draft; the owner approved Option B, but has not yet separately approved this distinct-issuer rule. Keep it proposed until explicit contract freeze.

The AEO issuer's own statement is authorized directly by the accepted Trust Policy role and does not recursively require another AEO. This narrowly scoped exemption must remain isolated to AEO issuance and must not authorize checkpoint signing.

### 2.6 Bootstrap, Trust Policy and state boundaries

**PASS WITH LIMITATION.** A2.2 §§16–17 remain unchanged: Path A and Path B are NOT_ENABLED; initial trust bootstrap remains BLOCKED. A2.3 does not create or mutate Trust Policy, signer registry, Monotonic Anchor, Verification Records or accepted checkpoint state. The proposed AEO chain can be exercised only with isolated synthetic test policy/key material once separately approved.

### 2.7 Resource limits and result model

**PARTIAL PASS.** Bounded limits are proposed, including 1 MiB object/statement bodies, 1 MiB + 64 octets for the fully prefixed preimage, 4 KiB SPKI DER, 64-octet signatures, 64 dependency descriptors, bounded JSON depth/member/array/string sizes. These are not frozen. The Stage II adapter result model still needs to add `INPUT_LIMIT_EXCEEDED` and align the exact limit values before implementation.

### 2.8 Negative-test migration

**PARTIAL PASS.** A2.2 NV-31..34 are explicitly superseded by A2.3-NV-01..04 and expanded by A2.3-NV-05..12. The draft retains all original failure dimensions and adds AEO binding, signature, issuer authorization, self-issuance, scope, detached descriptor self-reference and negative decision outcomes.

Before freeze, each fixture needs exact canonical bytes, one isolated mutation, one aggregate verdict, one primary reason code, S0/S1 state assertions and independently generated Ed25519 known-answer material. No fixture suite has been implemented or run.

## 3. Blocking findings

| ID | Finding | Required closure |
|---|---|---|
| A23-SR-01 | AEO issuer distinct-principal/key requirement is a new owner-level security constraint | Explicit owner decision in the exact contract freeze record |
| A23-SR-02 | Trust Policy schema does not yet contain a frozen AEO issuer role/profile/purpose allowlist mapping | Normative field mapping and policy negative cases |
| A23-SR-03 | AEO issuer profile and new domain are proposed but not independently security-reviewed | Independent review of exact A2.3 blob and KATs |
| A23-SR-04 | AEO/request/decision/authority/custody descriptor schemas and namespace/cardinality rules are not all fully frozen | Complete schema appendix and dependency-closure review |
| A23-SR-05 | Resource ceilings are proposed; adapter result model has not yet been updated | Owner freeze and adapter contract amendment |
| A23-SR-06 | PyCA version, dependency hashes, wheel provenance and offline build matrix are unresolved | Supply-chain/build decision and evidence |
| A23-SR-07 | No implementation, RFC-vector test suite or CI result exists for Stage II | After contract freeze and qualifying review, separate bounded implementation authorization and TDD |

## 4. Adversarial questions retained

1. Can a compromised AEO issuer attest false build/request/authority facts despite a mathematically valid signature? Yes; this is a residual issuer-trust risk. Trust Policy authorization, issuer separation and independently auditable evidence reduce but do not eliminate it.
2. Can the same descriptor ID be rebound to a new envelope? It must be rejected as a hard conflict; the append-only namespace/readback implementation is not yet specified.
3. Can a valid AEO be replayed for a different checkpoint? The exact checkpoint ID/sequence, signer, stream, action, audience and object type are bound in AEO scope and must be compared to the main statement. Test coverage must prove each dimension separately.
4. Can the AEO signature be mistaken for a checkpoint signature? The separate statement type, purpose, role, profile and domain prevent this if the verifier dispatches strictly and forbids fallback.
5. Can an offline verifier accept an AEO whose authority evidence dependency is missing? No; required dependency absence must be BLOCKED/UNKNOWN, never inferred from a URL or label.
6. Does this design enable real signer trust? No. Bootstrap remains disabled and no Trust Policy instance/root is installed.

## 5. Scope and evidence disposition

- Review was static and performed by the same assistant that authored the draft.
- No tests were run; no code was changed.
- No keys, signatures, trust roots, policy/anchor/verification state, CI dispatch, VPS/T0/runtime, trading or destructive operation was performed.
- This report is NOT an independent review and MUST NOT be labeled G3.

**Final disposition: PARTIAL PASS WITH BLOCKERS. A2.3 IS A REVIEW CANDIDATE ONLY; NOT FROZEN; STAGE II IMPLEMENTATION NOT YET AUTHORIZED.**


## 6. Follow-up review addendum — expanded A2.3 schema iteration

**Reviewed A2.3 blob:** `41d6abfc9df20047af4668b80a6ce2edb7e07117`  
**Review remains:** same-session author self-review only.

Additional checks:
- AEO body digest is explicitly bound to A2.2 §20.1 Evidence Object domain bytes, U64BE exact body length and exact canonical body bytes.
- AEO signature statement now has a distinct type and exact domain separator; the 49-octet domain hex was independently checked from the literal ASCII bytes plus one NUL. The fixed SHA-256 KAT uses payload `A2.3-AEO-domain-KAT-v1`, length 22, U64BE `0000000000000016`, expected digest `64172accdaf1f2add08b201b25c8ea26b52e2c90e68674126bbef465f4e7acde`.
- The AEO signature statement's required field set, body descriptor, package descriptor, request/decision/authority/custody descriptor shapes and Trust Policy issuer-entry mapping are now specified at draft level.
- AEO and envelope descriptor identifiers use canonical UUIDv4 URNs, generated from a CSPRNG and checked against an append-only namespace; same-ID/different-bytes remains a hard conflict.
- Resource limits now include a 16 MiB maximum frozen verification input-set size, 64 dependency descriptors and 1 MiB maximum per dependency, in addition to per-object/parser ceilings.
- Stage II adapter contract has been aligned to the AEO caller-level preimage and `INPUT_LIMIT_EXCEEDED` result. It remains stateless and does not parse AEO/descriptor content.

Updated findings:
- A23-SR-02 is reduced but not closed: the AEO Trust Policy entry is described, but the complete Trust Policy schema and issuer status/revocation semantics still require exact crosswalk to A1/A2.2.
- A23-SR-04 is reduced but not closed: logical descriptor shapes are described; exact canonical JSON schemas, namespace authority, evidence issuer model and revocation/status evidence semantics remain to be frozen.
- A23-SR-05 remains open: ceilings are now more complete but remain proposed until owner freeze and independent review.
- A23-SR-01 remains open: distinct AEO issuer principal/key is a new security constraint and has not yet received a separate explicit owner decision.
- A23-SR-03, SR-06 and SR-07 remain open: independent security review, pinned PyCA/build provenance, and post-freeze implementation/test/CI authorization.

No tests or implementation were run. The updated adapter contract blob is `1bdfc87949429cfd164892eab519971954f243eb`. This follow-up does not change the original disposition: **PARTIAL PASS WITH BLOCKERS / NOT INDEPENDENT REVIEW / NOT FROZEN / IMPLEMENTATION BLOCKED**.


## 7. Dependency candidate follow-up

A separate documentation-only dependency candidate now records `cryptography==50.0.2`, a proposed CPython 3.11+ ABI3 / manylinux_2_34 x86-64 wheel and candidate hashes:
- `docs/evidence/T0_SIGNATURE_A2_3_PYCA_DEPENDENCY_CANDIDATE_2026-11-11.md`;
- creation commit `d633b478a4f158f48ccb43e379dbd14c023d9b87`.

The wheel hash is not yet recomputed from the exact downloaded PyPI artifact in this repository. Transitive dependency closure, runner glibc, provenance-attestation verification and offline install remain unverified. The adapter contract was updated accordingly; current blob is `8ec916c152c51e75c5a3852e7977dd7f1239d8fe`.

This reduces the version-selection ambiguity but does not close the supply-chain/build gate. No package was installed and no lockfile/CI file was changed.
