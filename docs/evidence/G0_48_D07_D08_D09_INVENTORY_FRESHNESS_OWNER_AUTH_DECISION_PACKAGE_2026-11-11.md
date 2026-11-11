# G0.48 — D07/D08/D09 Inventory, Freshness and Owner Authentication Decision Package

Date: 2026-11-11 (Asia/Ho_Chi_Minh)
Repository: kenznguyen/btcusdt-telegram-signals2
Branch: feature/t0-centralized-data-feeder-p1-20261101
Baseline: eeaeec02b38d428cb535a5dffc7ded4dec3bfe85
Related records: G0.26, G0.46, G0.47
Type: documentation-only owner decision package
Disposition: **PACKAGE PREPARED — D07/D08/D09 OPEN / NOT RATIFIED; S2 IMPLEMENTATION NOT AUTHORIZED**

## 1. Purpose and current owner decisions

This package prepares the next owner decisions after G0.47. The owner has selected:

- D01: SHA-256 exact-byte integrity by default; signature conditional on a specific claim.
- D02: exact opaque bytes by default; JCS only if a future structured signed statement requires it.
- D03: single topology preference; this does not authorize an Issuer Key.
- D04: defer real key custody and all real key operations.
- D06: manual Owner attestation only in the initial phase; autonomous issuer authenticity is deferred.

G0.26 remains controlling: byte integrity, issuer authenticity, Owner authorization, freshness/anti-replay, and evidence truth/completeness/custody are separate claims. G1 A remains unsigned; A1 remains a separate extension.

This package offers candidate policies for D07, D08 and D09. It does not ratify them and does not authorize implementation.

## 2. D07 — Inventory closure and omission detection

### Problem

An inventory is not complete merely because a producer supplies a manifest, a page counter reaches its last page, or an Owner attests that it was reviewed. Completeness requires a defined expected scope and evidence that every expected item was accounted for.

### Candidate minimum contract

1. **Declare scope before enumeration:** identify inventory domain, source/system, object classes, selection filters, snapshot/cut boundary, and the exact question the inventory claims to answer.
2. **Define expected population:** identify the authoritative enumeration mechanism and its limits. If no authoritative expected population exists, label the result SCOPE_UNBOUNDED or equivalent; do not claim completeness.
3. **Enumerate deterministically:** capture stable object identifiers and immutable version/reference where available. Preserve pagination/cursor evidence and the terminal condition.
4. **Reconcile expected and observed:** classify each expected item as observed, explicitly absent/not applicable with evidence, inaccessible, ambiguous, or unresolved. Duplicate identifiers, cursor discontinuity, unreadable pages, source errors, and unexplained count mismatches prevent closure.
5. **Bind evidence:** record exact manifest bytes/digest, scope definition/version, source identity/reference, snapshot/cut identifier, enumeration procedure/version, and reconciliation result.
6. **Fail closed:** unknown scope, incomplete pagination, unavailable source, conflicting counts, missing page, unresolved item, or ambiguous identity means INCOMPLETE/NOT VERIFIED, never implicit complete.
7. **Keep attestation separate:** manual Owner attestation records that the Owner reviewed the bounded inventory evidence; it cannot create completeness where independent enumeration/reconciliation is missing.

### Owner decision options

- **D07-A (recommended):** require declared scope + independently defined expected population + complete enumeration + expected/observed reconciliation; any unresolved item means not closed.
- D07-B: permit scoped partial inventories, but require an explicit partial-coverage label and prohibit any completeness claim.
- D07-C: permit source-provided manifest-only closure. Not recommended because it cannot independently detect omissions.

Recommendation: adopt D07-A as the default closure rule, while allowing D07-B only when the claim explicitly says partial. Reject D07-C for any claim of completeness.

### Questions to ratify

- Is D07-A the default rule for any claim that an evidence inventory is complete?
- May D07-B be used for explicitly partial inventories, with no completeness claim?
- Should all unresolved/inaccessible/ambiguous items block closure? Recommended: yes.

No corpus size, pagination maximum, retry count, byte ceiling, or time limit is proposed here. Numeric limits require measurement and a separate owner decision.

## 3. D08 — Freshness, expiry, revocation, replay and rollback

### Problem

A valid digest or a manual Owner attestation does not establish that evidence is current. Local timestamps may be wrong or manipulated. Without a trusted comparison point, the system cannot reliably claim latest, not replayed or not rolled back.

### Candidate minimum claim model

Classify each decision/evidence use into one of these claim levels:

- **INTEGRITY_ONLY:** exact bytes match a known digest. No freshness/latestness claim.
- **AS_OF_SNAPSHOT:** evidence is valid only relative to a named immutable snapshot/cut or checkpoint. It does not claim to be globally latest.
- **FRESHNESS_VERIFIED:** a separately approved trusted time/sequence/anchor and anti-rollback comparison establish freshness within an explicitly approved policy.
- **FRESHNESS_UNKNOWN:** no trusted comparison point or required evidence exists. Fail closed for actions that require freshness.

### Candidate controls

1. Do not trust producer/local wall-clock timestamps as authoritative freshness evidence by themselves.
2. Bind each attestation/evidence record to exact subject, digest/references, scope, purpose, policy version and a unique decision/record identifier.
3. For snapshot-relative claims, identify the exact snapshot/cut and state that the claim is only AS_OF_SNAPSHOT.
4. For latestness/anti-replay claims, require a separately approved monotonic sequence or trusted anchor and compare against the accepted prior state. A sequence field without a trusted comparison point is insufficient.
5. A superseding/revoking Owner decision must identify the exact prior record and reason/scope. The verifier must resolve the current accepted decision state; a stale copied record must not silently override a newer one.
6. If current state, trusted time, sequence continuity, revocation status or rollback comparison cannot be established, return FRESHNESS_UNKNOWN and do not use the evidence for a freshness-dependent action.
7. Do not introduce a universal TTL. Different evidence classes and claims may have different validity needs. Any TTL/expiry duration requires a named use case, measurement/rationale and explicit owner ratification.
8. D06 means no autonomous issuer key or issuer-signature revocation mechanism is required initially. Manual Owner supersession/revocation remains a policy decision; its authenticated representation is subject to D09.

### Owner decision options

- **D08-A (recommended initial posture):** make no global freshness/latestness claim. Use INTEGRITY_ONLY or AS_OF_SNAPSHOT where appropriate; freshness-dependent decisions fail closed until a trusted comparison/anchor is separately approved.
- D08-B: introduce per-class expiry windows immediately. Not recommended before evidence-class usage and time-source requirements are known.
- D08-C: use local timestamps as freshness authority. Reject; this overstates what local time proves.

Recommendation: adopt D08-A for the initial manual-attestation phase. Do not ratify TTL values, trusted time source, monotonic anchor technology, revocation transport or replay window in this package.

### Questions to ratify

- Is D08-A the initial policy: no global latestness claim; only integrity or named-snapshot claims unless a trusted anchor is separately approved?
- Must evidence used by freshness-dependent actions fail closed whenever freshness is unknown? Recommended: yes.
- Should TTLs and numeric freshness windows remain unratified until a specific evidence class/use case is presented? Recommended: yes.

## 4. D09 — Manual Owner authentication and exact-scope authorization

### Problem

A text field saying approved=true, an unverified username, a Git author string, or a commit SHA alone does not prove that the Owner personally authenticated or approved an exact action. Manual attestation must not become a generic approval token.

### Candidate manual-attestation record

A future Owner attestation record should bind, at minimum:

- record schema/type and version;
- Owner identity reference and the authentication context used to establish it;
- decision purpose and audience/domain;
- exact subject identifier/type/version;
- exact artifact digest and byte length, or immutable evidence references;
- claim being attested and its explicit limitations/non-claims;
- exact action/disposition being approved, if any;
- scope, policy/profile identifier and version;
- decision identifier and relationship to any superseded/revoked decision;
- decision time as metadata, with an explicit statement whether the time source is trusted;
- status and evidence references supporting the Owner's review.

The record must distinguish:
- **review attestation:** Owner states that specified evidence was reviewed;
- **authorization:** Owner approves a specific action on a specific target and scope;
- **trust administration:** Owner changes trusted identities/policy/recovery state.

These are separate actions and must not be collapsed into a generic attestation.

### Authentication options

| Option | What it establishes | Limitations |
|---|---|---|
| D09-A: authenticated owner-controlled GitHub action/commit with exact record | Platform-attributed action under the repository account, plus immutable repository commit/blob evidence | Does not by itself prove cryptographic commit signature, session assurance level, or that the account was uncompromised |
| D09-B: detached owner signature over the exact decision record | Cryptographic control of the signing key over exact bytes | Requires key generation/custody, trust anchor, verification and recovery; conflicts with current defer-key posture until separately approved |
| D09-C: external/manual approval record without verifiable account/session binding | Human-readable evidence of a decision | Weak identity assurance; cannot be promoted to authenticated Owner authorization |

### Recommendation

For initial documentation-only governance, use D09-A only as a platform-attributed manual decision record if the Owner confirms that the authenticated repository account and its access controls are an acceptable initial identity channel. Explicitly label it PLATFORM_ATTRIBUTED_OWNER_ACTION, not CRYPTOGRAPHICALLY_SIGNED_OWNER_ATTESTATION.

Do not treat Git author/committer metadata or a commit SHA alone as proof of identity. Record the exact decision, subject, digest, purpose, scope and policy version in the committed document. Any stronger assurance (signed commit or detached signature) requires a separate owner decision, key custody decision and exact approval; no key operation is authorized now.

A review attestation must never implicitly authorize deletion, cleanup, archive, retention change, key operation, deployment, trading, or any other privileged action. A privileged action requires a distinct exact-scope authorization.

### Questions to ratify

- Is D09-A acceptable for initial manual Owner decisions, with the explicit PLATFORM_ATTRIBUTED_OWNER_ACTION limitation?
- Must review attestation and privileged-action authorization be separate records/decisions? Recommended: yes.
- Must each authorization bind exact target, action, scope, policy version and evidence digest/references? Recommended: yes.
- Is D09-B deferred until a separate key-custody decision? Recommended: yes.

## 5. Cross-decision consistency and dependencies

- D06 remains manual Owner attestation only; no autonomous Issuer Key or producer/service signature in the initial phase.
- D07 completeness must be established by independently scoped enumeration and reconciliation, not by Owner assertion alone.
- D08 freshness is independent of digest integrity and Owner identity. The initial posture makes no global latestness claim.
- D09 Owner authentication is independent of issuer authenticity. A platform-attributed Owner action is not a producer signature and does not create a trust root.
- D12 must define durable audit/custody/readback/recovery evidence.
- D13 must bind verified facts to exact subject/source/version/digest/policy scope and preserve the distinct claim levels.
- D14 must define exact S2 implementation/test paths, commands, source pins, side-effect restrictions and stop conditions.
- D05/D10/D11 and the S1 parser contract remain synthetic-only; they do not authorize production trust or lifecycle execution.

## 6. Proposed owner selections (not ratified)

| Decision | Recommended initial selection | Status |
|---|---|---|
| D07 | A: declared scope, independent expected population, full enumeration and reconciliation; unresolved items block closure. B allowed only for explicitly partial inventory. | OPEN |
| D08 | A: integrity-only or named-snapshot claims; no global latestness; freshness-dependent actions fail closed if freshness is unknown. No TTL/anchor numeric values yet. | OPEN |
| D09 | A: platform-attributed manual Owner action only, if Owner accepts its assurance limits; separate review attestation from privileged authorization; exact-scope binding. Defer cryptographic signatures. | OPEN |

The recommendations are not decisions. No answer is inferred from prior selection of manual Owner attestation.

## 7. Explicit non-authorizations

This package authorizes documentation preparation only. It does not authorize:

- any parser/verifier/source/test/fixture/schema/API/adapter/registry/workflow/CI change;
- installation of dependencies, network access, external provider access, VPS/T0 access or inventory collection;
- generation/import/use/export/signing/verification/rotation/revocation of test or real keys;
- creation or installation of trust roots, trust policies, issuer registries, certificates, anchors, timestamp services or provider accounts;
- promotion of any production evidence to trusted or freshness-verified;
- lifecycle cleanup, archive, expiry, compaction, VACUUM, deletion or other destructive action;
- changes to T0/T1/T2, CORE_LEDGER, AI_LEDGER, Shared Risk Engine, Kill Switch or trading runtime;
- deployment, exchange connection, live trading or real orders.

T0 remains independent and protected. CORE_LEDGER and AI_LEDGER remain separate. Paper-only and AI_EXECUTION_ENABLED=false remain unchanged. VPS remains absent; no runtime state is inferred.

## 8. Verification and disposition

- Scope: documentation-only owner decision package.
- Tests/compile/CI: not run; no executable code changed.
- Runtime/VPS/database/provider/key operations: not performed.
- Independent reviewer sign-off: not mandatory under the existing owner waiver; no independent assurance claim is made.

**G0.48 disposition: PACKAGE PREPARED — D07/D08/D09 RECOMMENDATIONS READY FOR OWNER DECISION; ALL THREE REMAIN OPEN / NOT RATIFIED; S2 IMPLEMENTATION NOT AUTHORIZED.**

Next: Owner selects or amends D07, D08 and D09. Record each choice explicitly before preparing any implementation package. No automatic progression to S2 is permitted.
