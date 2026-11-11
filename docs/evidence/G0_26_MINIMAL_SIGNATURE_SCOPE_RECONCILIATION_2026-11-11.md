# G0.26 — Minimal Signature Scope Reconciliation

Date: 2026-11-11 (Asia/Ho_Chi_Minh)
Repository: `kenznguyen/btcusdt-telegram-signals2`
Branch: `feature/t0-centralized-data-feeder-p1-20261101`
Baseline handoff blob: `d3fa7ab5d92517456832f08f072ec21b6a7767a6`
Type: documentation-only reconciliation
Disposition: **ANALYSIS PASS — MINIMALITY PRINCIPLES IDENTIFIED; D01–D04 NOT RATIFIED; IMPLEMENTATION NOT AUTHORIZED**

## 1. Purpose

Reconcile G0.25's recommended cryptographic profile against the existing T0 Checkpoint Contract v1, Signature/Trust Policy Amendment A1 and the G0.21–G0.24 verified-facts design. The objective is to avoid imposing a full signing/trust stack on claims that require only byte integrity, while preserving explicit authentication requirements wherever a claim relies on signer authority.

This report is a design analysis, not an owner decision. It does not ratify DSSE, Ed25519, SHA-256, JCS, delegation, key custody or any other D01–D14 option.

## 2. Controlling distinctions

The following claims are different and MUST NOT be collapsed:

1. **Byte integrity:** recomputing a digest over exact bytes proves whether those bytes match the referenced digest. It does not authenticate who produced or approved them.
2. **Signer authenticity:** a valid signature, together with an authenticated trust policy and scoped authorization, establishes that an authorized key signed the exact statement. It does not establish factual truth.
3. **Owner authorization:** a separate authenticated owner decision authorizes a specific action or disposition. A signer identity or valid signature does not itself grant deletion, execution or policy-change authority.
4. **Freshness / anti-replay:** requires a trusted comparison point or authenticated sequence/anchor. A signature alone does not establish latestness.
5. **Evidence truth/completeness/custody:** require independent evidence resolution, inventory closure and readback. Neither digest nor signature proves these properties.

The T0 Checkpoint Contract v1 explicitly states that G1 A is an unsigned proof-of-existence product and makes no signer-authenticity claim. A1 is a separate signature/trust extension. Do not retroactively impose A1 signing on G1 A.

## 3. Minimality decision framework (proposed, not ratified)

| Claim being made | Minimum mechanism indicated | Explicit non-claims |
|---|---|---|
| Exact bytes match a known digest | SHA-256 (or separately approved digest profile) over the exact canonical/defined bytes | No signer identity, owner approval, freshness, truth or custody |
| A trusted principal attested to an exact object for a defined purpose | Detached signature over a minimal, domain-separated statement binding exact object identity/version, digest, purpose and audience; verifier checks signer authorization against trusted policy | No factual truth, completeness, durable commit, custody or latestness |
| A specific owner approved a policy/action | Separately authenticated owner authorization bound to exact action, target, scope and policy version | A generic object signature is not owner authorization |
| Object is the accepted latest checkpoint | Separate authenticated freshness/anchor mechanism and rollback/equivocation checks | Signature sequence field alone is insufficient |
| Lifecycle disposition is safe | Verified-facts evidence plus pure evaluator and separate exact-object owner authorization | Successful use/ACK/signature is not deletion permission |

A claim must not receive a stronger mechanism merely because the implementation already supports it. Conversely, a weaker mechanism must not be used to make a stronger claim.

## 4. Candidate minimal signed statement

If and only if signer authenticity is required for a particular claim, the signed statement should carry only fields necessary to make the signature unambiguous and non-transferable:

- statement schema/type and version;
- exact purpose and audience/domain;
- immutable subject identifier and subject type/version;
- digest algorithm, digest and exact byte length;
- canonicalization/profile identifier where structured bytes are canonicalized;
- policy/profile reference or version needed to resolve signer authority.

The signer key identifier/fingerprint may be carried in the detached envelope or resolved through the verifier's trusted policy, but it MUST NOT be trusted merely because the producer supplied it. Avoid duplicating the same identity and policy metadata in multiple layers unless a concrete verification rule requires the duplication.

The following should remain outside the minimal signed payload unless a claim-specific requirement proves otherwise:

- full public-key certificate/delegation chains;
- revocation lists or complete trust-policy documents;
- custody receipts and readback records;
- producer logs, CI metadata and environment diagnostics;
- local wall-clock timestamps presented as if trusted;
- inventory manifests unrelated to the exact signed subject;
- operational retry/transport metadata.

These external records must still be authenticated and bound by exact references/digests when they are required for verification. Moving a field outside the payload does not make it trustworthy by itself.

## 5. G0.25 recommendation assessment

| G0.25 recommendation | Minimality assessment | Current disposition |
|---|---|---|
| D01 DSSE + Ed25519 + SHA-256 | A coherent candidate for a detached signature envelope and fixed asymmetric signature profile, but not automatically the minimum for digest-only G1 A. DSSE is an envelope/PAE format, not a trust policy or key lifecycle. | OPEN / NOT RATIFIED |
| D02 RFC 8785 JCS | Useful only where a structured JSON statement needs deterministic bytes. It is not needed for already-defined opaque byte payloads. The exact numeric/Unicode restrictions must match the schema. | OPEN / NOT RATIFIED |
| D03 offline root + delegated issuer keys | Stronger trust architecture than a single owner-held signer. Delegation is justified only if distinct principals/services genuinely need separate signing authority and revocation scopes. | OPEN / NOT RATIFIED |
| D04 hardware-backed or managed isolated signing | Good custody options for real signing, but the current paper-only stage has no approved real key operation. Hardware/KMS selection should follow an actual signing requirement and threat model. | OPEN / NOT RATIFIED |

No recommendation is rejected by this report; none is approved. The report identifies where each adds complexity and what evidence would justify it.

## 6. Cross-document reconciliation findings

1. **G1 A remains unsigned.** The initial T0 proof-of-existence product must remain digest/timestamp-oriented as its contract states. Do not add signer claims by implication.
2. **A1 remains a separate extension.** Its richer Signature Statement and Trust Policy requirements apply only to the signature/trust claims within its declared scope. They are not a universal requirement for every evidence object.
3. **G0 lifecycle verifier has a stronger trust-boundary need.** G0.21 identified caller-asserted identity, provenance, digest and completeness facts. If the lifecycle evaluator is to consume authenticated facts, a signature/authenticity mechanism may be necessary for specific evidence issuers. It still does not follow that every fact, object or internal test fixture needs a production signature.
4. **Digest and signature must remain separate verdict dimensions.** A digest-only record may be integrity-checked while signer authenticity is ABSENT/NOT REQUIRED for that claim. It must not be promoted to signer-authenticated.
5. **Owner authorization and lifecycle execution remain separate.** No signature profile gives an evaluator, issuer, CI workflow or runtime destructive authority.
6. **Freshness and monotonic anchor are optional claim dimensions, not implicit signature features.** Include them only when the system actually asserts latestness/anti-replay.
7. **Do not infer that “minimal” means omitting domain separation, subject binding or purpose/audience.** These are core protections against cross-object and cross-purpose signature reuse when signing is required.

## 7. Recommended staged posture

- Stage 0 (current): retain digest-only G1 A; no real key, signature, signer or anchor operations.
- Stage 1 (design only): identify exact G0 evidence classes whose facts require issuer authenticity; classify all other facts as digest/inventory/policy evidence with their own verification requirements.
- Stage 2 (after owner decisions): ratify only the minimum signature profile and trust model needed for those classes; resolve D05–D14 dependencies before implementation.
- Stage 3 (separate approval): synthetic-only executable verification using test-only keys and bounded fixtures.
- Stage 4 (separate approval): real evidence-source adapters or runtime integration, only after source authority, owner authentication, revocation/freshness, custody and audit requirements are closed.

No stage automatically authorizes the next.

## 8. Open owner decisions

D01–D04 remain OPEN. D05–D14 remain OPEN as recorded in G0.24. In particular, D06 evidence authorities, D07 inventory closure, D08 freshness/revocation, D09 owner authentication, D12 audit custody and D13 verified-facts binding remain dependencies. A minimal signature payload cannot compensate for unresolved issuer authority or incomplete evidence inventory.

Owner questions for a later exact decision:
- Which exact G0 evidence classes require signer authenticity, rather than digest integrity only?
- Is there more than one real signing principal/authority that justifies delegation?
- Which exact claims require latestness/anti-replay, and which do not?
- Is the initial implementation expected to support unattended signing, or is a manual owner-attestation workflow sufficient?
- Which fields are truly required by the selected verifier contract, and which can be resolved from authenticated external policy/evidence records?

No answer is inferred from “tiếp theo” or from this analysis.

## 9. Scope and verification

- Documentation-only analysis.
- No source, test, fixture, schema, API, registry, adapter, workflow, CI permission, credential, key, trust root, provider, database, storage, market-data, model, ledger, VPS or runtime changes.
- No tests or workflow dispatch.
- No key generation/import/signing/rotation/revocation; no trust-policy or anchor instance created.
- No VPS/provider/database/network access or inventory.
- No archive, quarantine, cleanup, expiry, compaction, VACUUM or deletion.
- T0 remains independent and protected; CORE_LEDGER and AI_LEDGER remain separate; paper-only and `AI_EXECUTION_ENABLED=false` unchanged.

## 10. Final verdict

**G0.26: ANALYSIS PASS — minimality framework and cross-document scope boundaries recorded. D01–D04 NOT RATIFIED; D05–D14 OPEN; signature implementation NOT AUTHORIZED; runtime and lifecycle mutation NOT AUTHORIZED.**

Next: owner may decide the exact evidence classes requiring signer authenticity and then ratify/modify/reject D01–D04. Until then, retain the current unsigned G1 A boundary and do not implement the proposed cryptographic stack.
