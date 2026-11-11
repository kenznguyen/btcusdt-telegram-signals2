# G0.47 — D06 Minimal Issuer Authority Owner Decision Record

Date: 2026-11-11 (Asia/Ho_Chi_Minh)
Repository: `kenznguyen/btcusdt-telegram-signals2`
Branch: `feature/t0-centralized-data-feeder-p1-20261101`
Baseline: `0e7a62ec565fff003edc5ab48956e6e7d2f282e4`
Related decisions: G0.26, G0.46
Type: documentation-only owner decision record and next-decision package
Disposition: **OWNER SELECTIONS D01–D04 RECORDED; D06 CANDIDATE SCOPE PREPARED FOR OWNER CONFIRMATION; S2 IMPLEMENTATION NOT AUTHORIZED**

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

D06 asks which exact evidence classes and issuer principals may make authoritative claims. The following is a deliberately narrow candidate set for owner confirmation, not an approved production allowlist.

| Candidate evidence class | Claim that may require issuer authenticity | Minimum supporting checks beyond signature | Proposed treatment |
|---|---|---|---|
| Producer/source provenance attestation | A named producer asserts that an exact dataset/artifact was produced by a specified source and process | Bind exact subject/version/digest/byte length; reconcile producer identity and source records | Consider issuer signature only if the claim is relied upon as authoritative |
| Inventory closure/completeness attestation | An authorized inventory authority asserts that a defined evidence set is complete for a bounded scope and snapshot | Independently enumerate expected scope; reconcile omissions, pagination and immutable references | Consider issuer signature for the authority's assertion; signature alone never proves completeness |
| Recovery/readback/custody event attestation | An authorized custodian asserts a specific readback, restore, transfer or custody event occurred | Exact object/digest, source/destination, operation result, time/sequence evidence and independent readback where applicable | Consider issuer signature only when custody/event authority is relied upon |

The following are **not** issuer-signature requirements by default:

- Git commit/blob identity, SHA-256 manifests and exact artifact-byte integrity checks where the claim is only byte identity.
- Synthetic fixture/parser results and test-only reports.
- G1 A unsigned proof-of-existence.
- Owner approval of a privileged action; this requires a separate owner-authentication and authorization mechanism.
- Freshness, anti-replay, rollback protection, factual truth or completeness; these require their own evidence and verification rules.

### D06 proposed issuer boundary

If the owner confirms any candidate class above:

- issuer identity and authority must be resolved from verifier-controlled trust policy, not trusted from producer-supplied labels alone;
- authority must be scoped to named evidence classes, claim types, subject types and purpose/audience;
- the signed statement must bind the exact immutable subject/version and digest;
- the verifier must reject unknown, expired, revoked, out-of-scope or ambiguous issuer authority;
- signature validity must not promote unsupported claims about truth, completeness, custody or latestness.

No issuer principal, key identifier, trust anchor, signature payload schema, revocation mechanism or freshness policy is selected by this record.

## 5. D06 owner confirmation still required

The owner must confirm whether the candidate set is correct and whether each row is in scope. In particular:

1. Should producer/source provenance attestation require issuer authenticity?
2. Should inventory closure/completeness attestation require issuer authenticity?
3. Should recovery/readback/custody event attestation require issuer authenticity?
4. Is a manual owner-attestation process sufficient initially for any of these claims, such that an autonomous Issuer Key can be deferred entirely?

No answer is inferred from the word “minimal”. If a class is not approved for issuer authenticity, the system must state the weaker claim level explicitly and must not label it issuer-authenticated.

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

**G0.47 disposition: D01–D04 OWNER SELECTIONS RECORDED AS CONDITIONAL DIRECTION. D06 CANDIDATE EVIDENCE CLASSES PREPARED — OWNER CONFIRMATION REQUIRED. S2 IMPLEMENTATION NOT AUTHORIZED.**

Next: owner confirms the exact D06 candidate classes and whether manual owner attestation is sufficient initially. Only then prepare the next bounded decision record for the remaining dependent controls.
