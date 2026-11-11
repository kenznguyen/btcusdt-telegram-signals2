# G0.47 — D06 Minimal Issuer Authority Owner Decision Record

Date: 2026-11-11 (Asia/Ho_Chi_Minh)
Repository: `kenznguyen/btcusdt-telegram-signals2`
Branch: `feature/t0-centralized-data-feeder-p1-20261101`
Baseline: `0e7a62ec565fff003edc5ab48956e6e7d2f282e4`
Related decisions: G0.26, G0.46
Type: documentation-only owner decision record and next-decision package
Disposition: **OWNER SELECTIONS D01–D04 RECORDED; D06 INITIAL-PHASE MANUAL OWNER ATTESTATION SELECTED; AUTONOMOUS ISSUER AUTHENTICITY DEFERRED; S2 IMPLEMENTATION NOT AUTHORIZED**

## 1. Purpose and boundary

This record captures the owner's selections supplied after G0.46 and prepares the next narrow owner decision on D06 (evidence authorities and issuer scope). It does not implement a verifier, create a trust policy instance, or authorize signing.

The controlling G0.26 rule remains: use the minimum mechanism required by the exact claim. Byte integrity, issuer authenticity, owner authorization, freshness/anti-replay, and evidence truth/completeness/custody are distinct claims.

## 2. Owner selections recorded from explicit instruction

The following selections are recorded as the owner's chosen direction:

| Decision | Owner selection | Recorded interpretation |
|---|---|---|
| D01 — signature/digest | Conditional | SHA-256 over exact bytes is the default integrity mechanism. Consider DSSE + Ed25519 + SHA-256 only for an exact evidence class whose claim requires issuer authenticity and only after its authority and verifier contract are approved. |
| D02 — canonicalization | Conditional | Opaque artifacts are hashed/verified as exact contract-defined bytes. UTF-8 JSON + RFC 8785 JCS is considered only for a structured signed statement where deterministic serialization is required and its schema/test vectors are separately fixed. |
| D03 — key topology | Single | Keep a single-owner trust topology: one Owner Root role and at most one initially scoped Issuer Key role. Do not introduce multiple delegated issuer keys or a multi-issuer PKI by default. Owner authorization remains logically distinct from issuer attestation and trust administration. |
| D04 — custody | Defer | No real key generation, import, custody enrollment, signing, rotation, revocation, KMS/HSM setup, or provider operation now. Paper-only posture remains. A custody mechanism must be decided before any real key operation. |

**Decision status:** owner-selected direction recorded. Conditional cryptographic details and operational parameters remain subject to the exact claim, threat model, and later bounded approval. These selections do not authorize implementation or key operations.

## 3. Reconciliation with G0.26

The selections are consistent with G0.26:

1. SHA-256 over exact bytes establishes integrity relative to a reference digest; it does not establish producer identity, owner approval, freshness, factual correctness, completeness, or custody.
2. A detached DSSE/Ed25519 statement is considered only where an identified issuer-authenticity claim requires it. A valid signature authenticates the signed statement under an approved trust policy; it does not prove the statement is true.
3. JCS is not applied to opaque bytes or retroactively to G1 A. It is conditional on a future structured signed statement.
4. A single topology minimizes operational complexity but must preserve separate logical authority for Owner Root administration, issuer attestation, and owner authorization. A single key must not silently perform every role.
5. G1 A remains unsigned under T0 Checkpoint Contract v1. A1 remains a separate extension. No retroactive signature requirement is introduced.

## 4. D06 — Minimal issuer-authenticity candidate scope

D06 asks which exact evidence classes and issuer principals may make authoritative claims. The following three claim classes are in scope for the initial manual Owner-attestation process. This is not an autonomous issuer allowlist and does not assert that an attestation proves the underlying facts.

| Candidate evidence class | Claim that may require issuer authenticity | Minimum supporting checks beyond signature | Proposed treatment |
|---|---|---|---|
| Producer/source provenance attestation | A named producer asserts that an exact dataset/artifact was produced by a specified source and process | Bind exact subject/version/digest/byte length; reconcile producer identity and source records | Initial phase: manual Owner attestation only; no autonomous producer signature or issuer key |
| Inventory closure/completeness attestation | An authorized inventory authority asserts that a defined evidence set is complete for a bounded scope and snapshot | Independently enumerate expected scope; reconcile omissions, pagination and immutable references | Initial phase: manual Owner attestation only; independently enumerate expected scope because attestation alone never proves completeness |
| Recovery/readback/custody event attestation | An authorized custodian asserts a specific readback, restore, transfer or custody event occurred | Exact object/digest, source/destination, operation result, time/sequence evidence and independent readback where applicable | Initial phase: manual Owner attestation only; retain independent readback/custody evidence where applicable |

The following are **not** issuer-signature requirements by default:

- Git commit/blob identity, SHA-256 manifests and exact artifact-byte integrity checks where the claim is only byte identity.
- Synthetic fixture/parser results and test-only reports.
- G1 A unsigned proof-of-existence.
- Owner approval of a privileged action; this requires a separate owner-authentication and authorization mechanism.
- Freshness, anti-replay, rollback protection, factual truth or completeness; these require their own evidence and verification rules.

### D06 owner decision — initial phase

The owner explicitly selected **manual Owner attestation only for the initial phase**. Therefore:

- No autonomous Issuer Key is required or authorized in the initial phase.
- No producer/service-generated signature is required for the three candidate claim classes in Section 4.
- The Owner manually attests only to an exact, bounded statement identifying the claim, subject/version, digest or evidence references, scope and decision purpose. The exact attestation format and authentication controls remain for D09 and the later implementation package.
- The attestation proves only that the Owner made that bounded assertion/decision. It does not independently prove source provenance, inventory completeness, successful recovery, readback correctness, custody continuity or factual truth.
- Underlying facts still require independently resolvable evidence, inventory reconciliation and readback where relevant. Missing/conflicting evidence remains unresolved/fail-closed.
- Any later move to autonomous issuer attestation, an Issuer Key or signature-based issuer authenticity requires a new exact owner decision and bounded approval. It is not implied by the single-topology preference in D03.

**D06 initial-phase policy: OWNER-DECIDED — MANUAL OWNER ATTESTATION ONLY; AUTONOMOUS ISSUER AUTHENTICITY DEFERRED.** D09 remains open for owner authentication and exact-scope authorization mechanics. This policy decision does not authorize implementation.

## 5. Decision boundary and remaining owner decisions

The initial-phase choice resolves whether an autonomous issuer is needed now: it is not. It does not close the remaining evidence-governance questions:

1. D07 must define inventory closure and omission detection independently of an Owner assertion.
2. D08 must define freshness, expiry, revocation, replay and rollback controls where applicable.
3. D09 must define how a manual Owner attestation is authenticated and bound to an exact action, target, scope and policy version.
4. D12 must define audit, custody, readback and recovery records.
5. D13 must bind verified facts to exact subject/source/version/digest/policy scope.
6. D14 must define exact S2 paths, commands, synthetic-only tests, network/dependency restrictions, source pinning and stop conditions.

If any class is not backed by adequate underlying evidence, the system must state the weaker claim level explicitly and fail closed rather than treating the manual attestation as proof of truth or completeness.

## 6. Dependencies and later decisions

D06 does not close the other trust dependencies:

- D07: inventory closure and omission detection.
- D08: freshness, expiry, revocation, replay and rollback.
- D09: owner authentication and exact-scope authorization.
- D12: audit, custody, readback and recovery records.
- D13: verified-facts binding to exact subject/source/version/digest/policy scope.
- D14: exact S2 paths, commands, synthetic-only tests, network/dependency restrictions, source pinning and stop conditions.

A separate exact S2 implementation package and explicit approval remain required after the applicable owner decisions are closed.

## 7. Explicit non-authorizations

This record authorizes documentation only. It does not authorize:

- S2 verifier/parser/source/test/fixture/schema/API/adapter/registry/workflow/CI changes;
- dependency installation, network access, external-provider access or VPS/T0 access;
- generation, import, use, export, signing, verification, rotation or revocation of any test or real key;
- creation or installation of trust roots, trust policies, issuer registries, certificates, anchors or provider accounts;
- production evidence authentication or promotion of any evidence class to trusted;
- lifecycle cleanup, archive, expiry, compaction, VACUUM, deletion or other destructive operation;
- changes to T0/T1/T2, CORE_LEDGER, AI_LEDGER, Shared Risk Engine, Kill Switch or trading runtime;
- deployment, exchange connection, live trading or real orders.

T0 remains independent and protected. CORE_LEDGER and AI_LEDGER remain separate. Paper-only and `AI_EXECUTION_ENABLED=false` remain unchanged. The VPS remains absent; no runtime state is inferred.

## 8. Verification and disposition

- Scope: documentation-only.
- Tests/compile/CI: not run; no executable code changed.
- Runtime/VPS/database/provider/key operations: not performed.
- Independent reviewer sign-off: waived as a mandatory gate by prior owner decision; no independent assurance claim is made.

**G0.47 disposition: D01–D04 OWNER SELECTIONS RECORDED AS CONDITIONAL DIRECTION. D06 INITIAL-PHASE POLICY OWNER-DECIDED — MANUAL OWNER ATTESTATION ONLY; AUTONOMOUS ISSUER AUTHENTICITY DEFERRED. D07–D09 AND D12–D14 REMAIN OPEN. S2 IMPLEMENTATION NOT AUTHORIZED.**

Next: prepare the next bounded owner decision record for the remaining dependent controls, starting with D07/D08/D09. No autonomous issuer key or cryptographic operation is authorized.
