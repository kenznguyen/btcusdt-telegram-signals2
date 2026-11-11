# G0.46 — S2 Minimal Trust and Key Owner Decision Package

Date: 2026-11-11 (Asia/Ho_Chi_Minh)
Repository: `kenznguyen/btcusdt-telegram-signals2`
Branch: `feature/t0-centralized-data-feeder-p1-20261101`
Baseline: `799d8dfc273a690c16279ee40c1ca6fa02aa0f59`
Type: documentation-only owner decision package
Authorization: owner approved preparation of G0.46 docs-only on the existing branch
Disposition: **PACKAGE PREPARED — OWNER DECISIONS D01–D04 REMAIN OPEN; S2 IMPLEMENTATION NOT AUTHORIZED**

## 1. Purpose and decision boundary

G0.45 completed the bounded S1 synthetic parser. S2 is the next trust-verification stage, but the current records do not ratify a production signature profile, key topology, canonicalization profile, custody mechanism, issuer authority, freshness/revocation policy or verifier implementation.

This package applies the G0.26 minimality principle: select a mechanism only for the exact claim being made. It does not presume that every evidence object needs a signature, and it does not weaken authentication where a claim depends on an issuer's authority.

This package records recommendations and decision prompts only. It does not itself ratify D01–D04 or authorize S2.

## 2. Controlling invariants

1. **G1 A remains unsigned.** T0 Checkpoint Contract v1 defines G1 A as an unsigned proof-of-existence product. A1 remains a separate signature/trust extension. Do not retroactively impose A1 signing on G1 A.
2. **Digest is not identity.** A matching digest establishes byte integrity relative to the referenced digest; it does not establish who produced, approved, or custody-held the bytes.
3. **Signature is not truth.** A valid signature can authenticate an attestation by a trusted signer, but does not independently prove completeness, factual correctness, readback, custody, or latestness.
4. **Owner authorization is distinct.** An issuer signature must not be treated as owner approval for deletion, policy changes, execution, key rotation, or any other privileged action.
5. **Freshness is distinct.** Signature validity alone does not prove that an object is current or prevent rollback/equivocation.
6. **S1 parser boundary remains unchanged.** The parser accepts only the ratified synthetic fixture contract and emits no trusted facts or authority. No production evidence is to be passed through it as though it were a trust verifier.
7. T0 remains independent/protected; CORE_LEDGER and AI_LEDGER remain separate; paper-only and `AI_EXECUTION_ENABLED=false` remain unchanged.

## 3. Claim-to-mechanism classification

| Claim / evidence use | Minimum mechanism indicated | Signature status |
|---|---|---|
| Exact immutable bytes match a recorded digest | Recompute SHA-256 over the exact bytes; bind digest to immutable object/version and byte length in the inventory | Not required merely for byte integrity |
| Source-code identity / exact Git object | Git commit and blob identity, plus independent hash/readback where the evidence policy requires it | No extra detached signature inferred |
| S1 synthetic parser fixture validity | G0.45 parser contract and its bounded tests | No production key or signature |
| CI test outcome | Resolve exact workflow run, repository, event, branch, checked-out SHA, job/test result and artifact; authenticate the platform/source records according to a separately approved evidence policy | Do not invent a producer signature; issuer authority remains a D06 decision |
| A producer/service asserts provenance, completeness, inventory closure, recovery, or a custody event | Authenticated issuer identity and scoped authority, exact subject/version/digest binding, plus corroborating inventory/readback evidence | Signature likely required if this attestation is relied upon as an authoritative claim; exact classes remain owner decision |
| Owner approves a privileged action or disposition | Separately authenticated owner decision bound to exact action, target, scope, policy version and expiry/nonce as later ratified | Separate owner authorization; generic issuer signature is insufficient |
| Object is the accepted latest checkpoint / anti-replay state | Authenticated monotonic anchor or trusted sequence/freshness source, with rollback/equivocation checks | Separate freshness mechanism; not supplied by signature alone |
| Evidence truth, completeness or custody | Source reconciliation, complete inventory, readback, custody records and independent corroboration appropriate to the claim | Signature alone is insufficient |

The table is a classification framework, not a final D06 evidence-class allowlist. No evidence class is promoted to authenticated solely by appearing here.

## 4. D01 — Signature and digest profile

**Decision required:** whether any exact evidence class needs issuer authenticity beyond byte integrity, and which profile is the smallest adequate mechanism.

| Option | Description | Assessment |
|---|---|---|
| D01-A | SHA-256 digest only over exact bytes | Minimum for integrity-only claims; cannot assert signer identity or owner approval |
| D01-B | Detached statement using DSSE envelope/PAE, Ed25519 and SHA-256 | Coherent candidate if an exact class needs signer authenticity; more machinery than digest-only claims |
| D01-C | Other profile | Requires explicit threat-model, interoperability, dependency and verification rationale |

**Recommendation (not ratified):** keep digest-only evidence digest-only. If and only if D06 identifies an issuer-authenticity claim, evaluate D01-B as the initial candidate, subject to exact payload/domain separation and verifier contract. DSSE is an envelope/PAE format, not a trust policy or key lifecycle.

Open questions:
- Which named evidence classes require issuer authenticity?
- What exact statement is signed, including subject identity/version, digest algorithm/value, byte length, purpose and audience/domain?
- Are any regulatory/FIPS or platform interoperability constraints applicable? These are currently unknown.
- Does the signed statement need canonical structured bytes, or can it bind already-defined opaque bytes?

Status: **OPEN / NOT RATIFIED.** No signature algorithm or dependency is approved for installation or implementation.

## 5. D02 — Canonicalization and signed payload

**Decision required:** the exact bytes that a verifier hashes and, where applicable, verifies as a signature.

| Payload kind | Minimum rule indicated |
|---|---|
| Opaque file/artifact bytes | Hash/sign the exact bytes as defined by the object contract; do not transform them |
| Structured JSON statement | Freeze a strict schema and deterministic byte representation before signing; RFC 8785 JCS is a candidate, not an automatic requirement |
| External policy, inventory or custody record | Keep as a separately identified object; bind by exact immutable reference and digest when a claim depends on it |

**Recommendation (not ratified):** do not introduce JCS for opaque data or G1 A. For a future structured signed statement, consider UTF-8 JSON plus RFC 8785 JCS only after schema compatibility, number/Unicode constraints and exact byte-level test vectors are ratified.

Status: **OPEN / NOT RATIFIED.** No canonicalization library, schema, serializer or signed payload is authorized.

## 6. D03 — Minimum key topology and authority separation

The design must distinguish three logical roles even if the eventual key count is minimized:

- **Issuer attestation:** a producer states a scoped fact about an exact object.
- **Owner authorization:** the owner approves an exact action or policy decision.
- **Trust-anchor administration/recovery:** controls which keys are trusted, revoked or replaced.

These roles must not collapse into a generic `is_signed` or `trusted=true` flag.

| Option | Topology | Trade-off |
|---|---|---|
| D03-A | One owner-controlled signing authority for manual owner attestations; no delegated service issuers | Smallest initial topology if manual attestation is sufficient; does not scale to independent service issuers |
| D03-B | One offline owner trust anchor plus one scoped issuer key | Separates trust administration from routine issuer signing; adds custody, enrollment and revocation obligations |
| D03-C | Offline root plus multiple delegated issuer keys | Only justified when distinct producers/principals need separate scopes, independent rotation or revocation |
| D03-D | Platform-managed identity / KMS signing | Could reduce key handling, but introduces provider, account, policy, availability and custody dependencies; not assumed compatible |

**Recommendation (not ratified):** do not create a multi-issuer PKI by default. First establish whether any producer actually needs an autonomous signing identity. If no autonomous producer attestation is needed, prefer a manual owner-attestation workflow and defer issuer delegation. If one issuer is proven necessary, consider one narrowly scoped issuer key under a separately controlled trust anchor. Keep owner authorization logically separate regardless of key topology.

The number of keys, root authority, issuer scope, recovery authority, enrollment, rotation, revocation and compromise response remain owner decisions. No key identifier supplied by an untrusted producer may establish trust by itself.

Status: **OPEN / NOT RATIFIED.** No key generation, import, enrollment, export, signing, rotation, revocation, root installation or provider setup is authorized.

## 7. D04 — Key custody and signing operation

| Option | Custody model | Assessment |
|---|---|---|
| D04-A | No real key operation in current paper-only stage | Safest current posture; leaves real signer custody unclaimed |
| D04-B | Offline owner-held key with documented manual ceremony | Low operational complexity for infrequent owner attestations; recovery and loss procedures still required |
| D04-C | Hardware-backed or isolated signing device | Stronger isolation potential; requires device procurement, enrollment, backup/recovery and physical custody evidence |
| D04-D | Managed KMS/HSM | Operationally convenient for automated signing but adds provider/account trust, IAM, audit, availability and jurisdictional dependencies |

**Recommendation (not ratified):** D04-A remains the current posture. Select a real custody method only after D01/D03 establish an actual signing requirement and the threat model, recovery authority, revocation and audit obligations are decided. Do not install or configure a key provider as part of S2 design preparation.

Status: **OPEN / NOT RATIFIED.** No real or test key material is to be created or imported under this package.

## 8. Dependencies outside D01–D04

A minimal cryptographic profile cannot compensate for unresolved trust and evidence dependencies:

- **D06 — evidence authorities:** define which issuers and exact evidence classes may make which claims.
- **D07 — inventory closure:** establish completeness and omission detection for the relevant evidence set.
- **D08 — freshness/revocation:** define expiry, revocation, replay, rollback and trusted-time/anchor requirements for claims that need them.
- **D09 — owner authentication:** define how owner decisions are authenticated and bound to exact scope.
- **D12 — audit/custody:** define durable audit, readback, recovery and custody evidence.
- **D13 — verified-facts binding:** bind verified facts to exact subject, source, version, digest and policy scope.
- **D14 — implementation boundary:** define the exact paths, commands, fixtures, CI and permitted side effects for S2.

D05/D10/D11 and the S1 parser are already bounded for the synthetic parser contract; they do not silently resolve these production trust dependencies.

Independent review is not a mandatory gate under the user's previously recorded waiver. Do not reintroduce it as a required gate unless the owner explicitly reinstates it. This waiver is not evidence of independent assurance and does not waive owner decisions, exact-source verification, fail-closed behavior or negative tests.

## 9. Proposed S2 entry criteria (not yet approved)

S2 must remain BLOCKED until the owner has explicitly resolved the required decisions and approved an exact implementation package. At minimum:

1. D06 names the precise evidence classes and issuer principals requiring authentication; all other classes retain their explicitly weaker claim level.
2. D01 fixes the signature/digest profile only for those classes.
3. D02 fixes exact signed bytes and canonicalization only where required.
4. D03 separates issuer, owner authorization and trust administration; key count is justified by actual authority boundaries.
5. D04 defines custody/recovery before any real key operation.
6. D07–D09, D12–D13 define inventory, freshness/revocation, owner authentication, audit/custody and exact verified-facts binding.
7. D14 is amended with exact S2 paths, commands, synthetic-only test scope, network/dependency restrictions, source pinning and stop conditions.
8. A separate owner approval authorizes the exact S2 implementation and verification attempt.

No item above is deemed satisfied merely by preparing or accepting this package. No automatic progression from S2 design to real-source adapters or runtime is permitted.

## 10. Explicit non-authorizations

This G0.46 approval covers documentation preparation only. It does not authorize:

- changing G1 A or the T0 Checkpoint Contract v1;
- approving A1 or any production signature/trust policy;
- ratifying D01–D04 or closing D06–D09/D12–D14;
- changing parser, tests, fixtures, schemas, APIs, adapters, registries, workflows or CI permissions;
- installing dependencies, generating/importing/using test or real keys, signing or verifying production evidence;
- creating trust roots, anchors, certificates, revocation lists or provider accounts;
- accessing VPS, T0 databases, external providers, networks, exchanges or runtime;
- changing T0/T1/T2, market/model data, CORE_LEDGER, AI_LEDGER, Shared Risk Engine or Kill Switch;
- cleanup, retention, archive, expiry, compaction, VACUUM or deletion;
- deployment, live trading or real orders.

## 11. Owner decision record

No D01–D04 choice is ratified by G0.46. The owner may accept, amend or reject each recommendation independently. If the owner wants to proceed, the next decision should name the exact evidence classes requiring issuer authenticity and whether a manual owner-attestation workflow is sufficient initially.

**Final disposition: G0.46 PACKAGE PREPARED — DOCUMENTATION ONLY. D01–D04 OPEN / NOT RATIFIED. S2 IMPLEMENTATION NOT AUTHORIZED.**
