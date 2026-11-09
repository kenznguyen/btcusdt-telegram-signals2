# Stage B.2 — V07 Trusted Time and Revocation Contract

Date: 2026-11-10  
Type: documentary technical contract; no implementation or qualification

## 1. Purpose and authority

Define the minimum interface and fail-closed semantics for trusted-time evidence, signing-key trust and revocation decisions consumed by lifecycle authorization. Requirements only: no TSA, clock provider, trust root, cryptographic profile, key, protocol, numeric freshness bound or clock tolerance is selected.

Controlling directions: independently verifiable trusted-time proof; proof bound to exact signature bytes and immutable verification context; distinct trusted-time, received-time and revocation semantics; quarantine/fail-closed when trust or revocation cannot be established; audited quarantine release. The timestamp claim is limited to existence no later than asserted generation time, not exact signature-creation instant.

## 2. Evidence object contract

A future V07 evidence object MUST bind:
- schema/version and canonical serialization profile;
- exact subject object ID, generation/version and digest;
- exact signature algorithm and signature bytes, or unambiguous digest over those exact bytes;
- immutable verification context: signer/key identity and version, purpose, policy ID/revision, trust-profile ID/revision and relevant object metadata;
- timestamp token/proof bytes, asserted generation time, time scale, precision and uncertainty representation;
- issuer/TSA identity, policy identifier and trust-chain references;
- local received time and verification observation time, each with provenance;
- revocation evidence identity, status, effective-time semantics, revision and observation time;
- verifier identity/version, deterministic result and reason codes;
- evidence digest and provenance chain.

A payload-only or unsigned-envelope-only imprint does not satisfy exact-signature binding. Canonicalization and imprint construction require a future versioned profile before implementation.

## 3. Time semantics

The contract distinguishes asserted trusted time, local received time, verification observation time, revocation effective time and monotonic elapsed-time source. Each timestamp carries explicit time scale, precision, uncertainty interval or UNKNOWN, source identity, source health and provenance. Comparisons use intervals and policy-defined boundary semantics; uncertainty must not be collapsed into a point value.

Wall-clock rollback, monotonic reset, source disagreement, leap/scale ambiguity and unavailable time evidence are explicit failure conditions. Freshness is a versioned predicate over evidence age, uncertainty, source health, revocation revision and policy revision. Numeric thresholds remain UNSET pending authoritative owner input and an approved profile.

## 4. Trust and revocation state model

Required states: UNASSESSED, TRUSTED_CURRENT, TRUSTED_HISTORICAL, REVOKED, EXPIRED, UNKNOWN, CONFLICT and QUARANTINED.

A transition requires a new immutable evidence/revision record. A stale cache cannot overwrite a newer revocation revision. Missing authority, invalid signature/token, untrusted chain, unknown key, unsupported profile, expired trust material, conflicting status, stale revocation view or uncertain time MUST produce UNKNOWN, CONFLICT or QUARANTINED, never implicit trust.

Historical validity requires a versioned policy defining trusted timestamp proof, revocation effective-time boundary, equality behavior and required evidence. Until those semantics and parameters are approved, no historical acceptance decision is qualified.

## 5. Fail-closed outcomes

| Condition | Required result |
|---|---|
| Exact signature/context imprint mismatch | REJECT / QUARANTINE |
| Invalid timestamp token or trust chain | REJECT / QUARANTINE |
| Unknown signer/key or unsupported profile | BLOCK |
| Revocation authority unavailable or evidence stale | UNKNOWN / QUARANTINE |
| Revocation conflict or rollback | CONFLICT / QUARANTINE |
| Time source unavailable, uncertain beyond policy or contradictory | UNKNOWN / QUARANTINE |
| Trust material expired or validity unprovable | BLOCK |
| Object/key/policy/revocation revision changed during evaluation | RESTART on exact new revisions; otherwise BLOCK |
| Verifier cannot reproduce deterministic result | NOT_VERIFIED / QUARANTINE |
| Required evidence absent or provenance incomplete | BLOCK |

Client timestamps, HTTP response order, local file modification time and cached status cannot substitute for authoritative proof.

## 6. Revision binding and vectors

Every decision binds exact object generation/digest, signature bytes, key identity/version, trust-profile revision, revocation evidence revision, policy revision, verifier version and trusted-time evidence identity. A revision change invalidates the decision. Cache keys include every relevant immutable revision; cache freshness cannot extend authority validity.

Future positive/negative vectors cover exact signature imprint, valid proof under an approved profile, deterministic replay, payload-only imprint, altered signature/context, invalid/expired token, unknown/revoked key, stale/unavailable/conflicting revocation, wall-clock rollback, monotonic reset, uncertainty, stale cache, policy race, verifier disagreement and incomplete provenance. Each vector requires exact fixture bytes, profile revision, expected state, verifier build, independent oracle and artifact provenance. Vectors are specified, not implemented or run.

## 7. Dependencies and status

RET-06 consumes freshness, trusted clock, authorization lifetime and revocation semantics; its substantive values remain OPEN / NOT PROVIDED. RET-10 supplies deterministic verification and technical separation. RET-05/LDA-05 binds the V07 decision revision at the mutation boundary. V08 and Restore consume trusted ordering and provenance.

**Status: DOCUMENTARY CONTRACT COMPLETE; V07 BLOCKED / NOT QUALIFIED / NOT VERIFIED.** Provider/profile/key/trust-root and numeric parameters remain OPEN. No key operation, provider contact, implementation, test, Actions run or runtime probe is authorized.
