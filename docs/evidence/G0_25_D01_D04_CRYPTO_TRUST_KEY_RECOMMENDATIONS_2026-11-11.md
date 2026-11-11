# G0.25 — Technical Assessment and Recommendations for D01–D04

Date: 2026-11-11 (Asia/Ho_Chi_Minh)  
Branch: `feature/t0-centralized-data-feeder-p1-20261101`  
Baseline HEAD: `dc75ab5ce6a4f5cc5db82fa9ebe48ff0a2825509`  
Input: G0.24 Owner/Security Decision Package  
Scope: documentation-only technical assessment. Recommendations are not owner ratification.

## 1. Executive result

**G0.25: TECHNICAL ASSESSMENT PASS — recommended direction documented; D01–D04 remain OPEN pending explicit owner decisions.**

Recommended direction for a small, personal, paper-only system:

| Decision | Recommended direction | Confidence / condition |
|---|---|---|
| D01 | DSSE envelope; Ed25519 signature; SHA-256 for content/evidence digests | Suitable baseline, subject to exact signed payload and algorithm policy |
| D02 | UTF-8 JSON payload canonicalized with RFC 8785 JCS | Suitable if schema restricts numeric/time semantics and parser rejects ambiguity |
| D03 | Owner-controlled offline root; narrowly delegated issuer identities by claim class/domain | Strong separation; registry and delegation format still need design |
| D04 | Keep root key offline; issuer signing key hardware-backed or managed signing boundary; never raw key in VPS/CI | Preferred security posture; actual custody option remains owner choice |

No cryptographic profile, trust root, issuer, key, credential or operational signing process is created or approved here. This is an assessment only.

## 2. Scope and limits

Included:
- Compare practical options for D01–D04.
- Recommend a coherent, minimal profile and identify conditions/risks.
- Define decisions that must remain open until the owner explicitly ratifies them.

Not included:
- No source, test, fixture, schema, API, registry, adapter or workflow changes.
- No key generation/import/signing/rotation/revocation or secret handling.
- No runtime/VPS/provider/database/T0 access or inventory.
- No lifecycle mutation, archive, quarantine, cleanup, expiry, compaction, VACUUM or deletion.
- No authorization for verifier implementation or evidence-source integration.

## 3. D01 — Cryptographic integrity and authenticity

### Options assessed

**A. Raw digest plus bespoke detached-signature statement**
- Flexible and easy to prototype.
- Requires the project to define its own statement framing, signature input, key selection, multi-signature behavior and parsing rules.
- Increases risk of inconsistent implementations and subtle domain/field-binding omissions.

**B. DSSE envelope with a defined payload type**
- Uses a standard signing protocol and pre-authentication encoding (PAE) to bind payload type and exact payload bytes before signing.
- Keeps payload semantics separate from the signature envelope.
- Supports multiple signatures over one payload.
- Still requires the project to choose payload encoding, signature algorithm, trusted key policy and issuer authorization. A DSSE `keyid` is only a key-selection hint, not proof that the key is trusted.

**C. Custom or alternative attestation protocol**
- Not recommended unless a concrete interoperability requirement cannot be met by DSSE or another maintained standard.

### Recommendation

Adopt **DSSE as the envelope/signing protocol**, with:
- **Ed25519** as the initial signature algorithm.
- **SHA-256** as the content/evidence digest algorithm.
- A versioned, fixed payload type identifying this lifecycle verified-evidence statement.
- Signature verification against a separately configured trusted-key/issuer policy; never trust a key merely because its `keyid` appears in the envelope.
- Signature coverage of the exact payload bytes; payload semantics must bind issuer/principal, subject namespace/object/immutable version, evidence digest and byte length, evidence revision, claim purpose, policy revision, issuance time and expiry where applicable.
- Explicit algorithm allowlist and no fallback/downgrade. Unsupported algorithms fail closed.

**Important distinction:** DSSE signs the PAE of payload type and payload bytes. It does not by itself define the payload's canonical serialization or establish trust in the signer. D02 and D03 are mandatory dependencies.

### Risks and controls

| Risk | Required control |
|---|---|
| Trusted-looking but attacker-selected key ID | Resolve key ID only within an independently trusted issuer/key registry |
| Valid signature for wrong object or purpose | Include exact subject/version/purpose/policy binding inside signed payload |
| Same payload interpreted under another protocol | Fixed payload type and DSSE PAE verification |
| Digest proves integrity but not origin | Verify issuer signature and authority separately |
| Algorithm downgrade | Versioned allowlist; reject unknown algorithms and ambiguous negotiation |
| Key compromise | Revocation and issuer validity checks from D03/D04/D08 |

### D01 recommendation status

**RECOMMEND: DSSE + Ed25519 + SHA-256. NOT RATIFIED.**

Ed25519 is a practical 128-bit-class signature choice with published test vectors. The project must still select maintained libraries and define strict key/algorithm identifiers. SHA-256 should be used for object-content digests; it is not a substitute for signature verification.

## 4. D02 — Canonical representation and signed bytes

### Options assessed

**A. RFC 8785 JCS**
- Deterministic JSON representation with recursive property sorting and UTF-8 output.
- Constrains inputs to I-JSON and rejects duplicate property names.
- Human-readable payloads are easier to inspect and debug.
- JSON number semantics are based on IEEE-754 binary64; large integers and precision-sensitive values require string representation.
- Unicode strings must be preserved as-is; JCS does not apply Unicode normalization.

**B. Deterministic CBOR**
- Compact typed encoding and supports a broader data model.
- Requires a strict deterministic-encoding profile and disciplined tooling; less immediately inspectable.
- Would require a deliberate decision on CBOR profile, tags, map ordering and cross-language implementation.

### Recommendation

For this personal system's small metadata envelopes, use **UTF-8 JSON payloads canonicalized with RFC 8785 JCS**, conditional on the following schema/parser rules:
1. Reject duplicate JSON object keys before constructing a trusted object.
2. Reject invalid UTF-8, invalid Unicode/lone surrogates, non-I-JSON values and ambiguous encodings.
3. Preserve Unicode code points exactly; do not silently normalize strings.
4. Represent identifiers, hashes, byte lengths, sequence numbers and any integer that may exceed exact binary64 range as strings with explicit lexical validation.
5. Use a single strict timestamp format: UTC RFC 3339 with a defined precision and explicit `Z`; reject ambiguous/local timestamps and invalid calendar values.
6. Do not use floating-point values for security-sensitive quantities.
7. Define required fields, null-versus-omitted behavior and extension policy in a separately ratified schema.
8. Generate canonical bytes once, sign those exact bytes through DSSE, and verify by independently canonicalizing/rejecting nonconforming input according to the eventual wire contract.
9. Commit cross-language canonicalization and negative test vectors before production evidence is accepted.

Do not mix JCS and CBOR in the first version. Any future migration requires a new payload type/schema version and explicit compatibility policy, not runtime negotiation.

### D02 recommendation status

**RECOMMEND: RFC 8785 JCS over UTF-8 JSON. NOT RATIFIED.**

This choice is based on the envelope being small, metadata-oriented and likely to need human inspection. If payloads later become large, binary-heavy or require richer typed values, reassess CBOR in a new version rather than extending this contract implicitly.

## 5. D03 — Trust roots, issuer identity and delegation

### Recommended trust model

Use a three-level logical separation:

1. **Owner trust root**
   - Establishes the initial trust policy and authorizes issuer keys.
   - Kept offline; not present in application runtime, VPS, repository, or CI.
   - Used rarely for issuer onboarding, rotation/revocation and policy-root changes.

2. **Delegated issuer keys**
   - Distinct keys and identities for bounded claim domains, such as producer/build provenance, inventory closure, policy/sensitivity evidence and owner decisions.
   - Each delegation binds issuer identity, public-key fingerprint, allowed claim types, data domain/namespace, subject scope, validity interval and policy revision.
   - No issuer can delegate authority unless its own delegation explicitly permits it.
   - Separate producer attestations from inventory completeness and owner authorization; a producer must not certify its own global inventory closure or approve deletion of its own outputs.

3. **Verifier trust policy**
   - Read-only, versioned configuration of trusted roots, issuer delegations, allowed algorithms, scope and revocation status.
   - Not supplied or overridden by an untrusted envelope.
   - Unknown issuer, out-of-scope claim, expired delegation or unavailable required trust state fails closed.

### Principal identity

Do not equate a key ID, username, GitHub account, repository permission or display name with owner authority. The trust policy must bind a stable principal identifier to a public key and explicit claim permissions. Owner approval remains a separate authorization record under D09.

### Delegation format

Prefer a signed, versioned delegation statement using the D01/D02 profile. It should bind:
- Parent authority and delegated principal.
- Public-key fingerprint and key purpose.
- Allowed claim types and data domains.
- Exact scope constraints.
- Not-before/expiry and policy revision.
- Delegation depth and whether further delegation is prohibited.
- Revocation handle/identifier.

Default to **no further delegation**. Keep owner approvals and lifecycle action authorization out of ordinary producer issuer permissions.

### Recommendation status

**RECOMMEND: offline owner root + narrowly scoped delegated issuer keys + verifier-owned trust policy. NOT RATIFIED.**

The concrete issuer registry, identity proofing, delegation encoding, revocation source and recovery procedure remain OPEN under D03/D06/D08/D09.

## 6. D04 — Key lifecycle and signing operations

### Recommended separation

| Key class | Purpose | Placement recommendation |
|---|---|---|
| Owner root key | Authorize issuer keys and trust-policy changes | Offline hardware-backed or otherwise strongly isolated custody; never online |
| Issuer signing key | Sign one bounded class of evidence | Hardware-backed signing device or managed signing service with narrow access and audit |
| Verifier public keys | Verify attestations | Public keys only in versioned trust configuration; no private material |
| Synthetic test keys | G0.23 test vectors and CI | Generated only inside isolated tests; never trusted outside test fixtures |

### Operational rules

- Generate keys only after D03 trust architecture, custody and entropy requirements are ratified.
- Never place private keys in Git, ordinary files, environment variables, container images, CI secrets, workflow artifacts, logs or the VPS filesystem.
- Do not mount the owner root key into any application or CI job.
- Prefer signing operations that do not export private key material. Record principal, key ID, payload digest, purpose, time and outcome without recording secrets.
- Restrict signing permission by claim type and data domain; signing access must not imply owner approval or executor permission.
- Define rotation triggers and overlap semantics before use. At minimum, rotate on suspected compromise, unauthorized access, role change, cryptographic deprecation or loss of custody assurance.
- Revocation must invalidate future verification according to an authoritative, authenticated status source; an unavailable revocation source must not be treated as “not revoked”.
- Recovery must restore trust policy without silently reactivating a revoked or superseded key.
- Synthetic test keys must use a separate namespace/trust root and be rejected by any non-test verifier configuration.

### Custody options

**Option A — Hardware-backed owner and issuer keys**
- Strong separation and avoids exporting private keys.
- Requires compatible hardware, operational discipline and tested recovery.

**Option B — Managed KMS/HSM signing boundary**
- Good for unattended signing and access audit.
- Adds provider dependency, cost and configuration complexity; must validate key non-exportability, IAM scope, audit coverage and revocation behavior.

**Option C — Plain private-key file on VPS/CI**
- **Reject.** It places signing authority alongside the system being attested or in an automation environment and increases exposure to host compromise, credential leakage and accidental copying.

### Practical staged posture

For the current project stage, the safest low-cost action is **no real key operation**:
1. Keep D04 unresolved while the verifier and evidence authorities are still design-only.
2. Use synthetic ephemeral test keys only inside a future separately approved test harness.
3. Before any production trust is needed, compare owner-held hardware-backed signing against managed KMS/HSM based on whether signing is manual or unattended.
4. Do not provision a VPS or signing service merely to complete this design gate.

### D04 recommendation status

**RECOMMEND: offline root; hardware-backed or managed isolated issuer signing; prohibit plaintext private keys on VPS/CI. NOT RATIFIED.**

No key generation, import, signing, rotation, revocation, backup or destruction is authorized by this recommendation.

## 7. Cross-decision consistency requirements

D01–D04 must be ratified as one compatible profile:
- DSSE PAE signs the exact payload type and canonical payload bytes.
- JCS defines those payload bytes for the JSON payload version.
- The signed payload binds the subject, immutable version, digest, issuer, claim scope and policy.
- Trust policy—not the envelope's key ID—decides whether the signing key is trusted and authorized.
- Delegation validity and revocation are checked at verification time.
- Key custody and signing authorization are separated from verifier execution and owner action approval.
- A valid signature establishes that a trusted key signed the statement; it does not prove the statement is factually true. Evidence resolution, digest recomputation, producer authority, inventory closure and independent owner authorization remain required.

## 8. Dependencies and unresolved questions

Before D01–D04 can be marked APPROVED, the owner must explicitly decide:
- Whether to accept DSSE, Ed25519 and SHA-256 as the initial profile.
- Whether to accept RFC 8785 JCS and its numeric/Unicode constraints.
- Who holds the owner root and how that principal is authenticated.
- Whether issuer signing is manual/hardware-backed or unattended/managed KMS/HSM.
- Which issuer roles are required initially and which claim types each may sign.
- How key IDs, public-key fingerprints, delegation and revocation are represented and stored.
- What compromise/recovery process is acceptable for a personal system.

D06–D09 and D12 remain dependencies: evidence authorities, revocation source, owner authentication and audit custody are not settled. Ratifying D01–D04 alone does not make the verifier implementable or trustworthy.

## 9. Gate matrix

| Area | G0.25 result |
|---|---|
| D01 options and recommendation | ASSESSED; NOT RATIFIED |
| D02 options and recommendation | ASSESSED; NOT RATIFIED |
| D03 trust model recommendation | ASSESSED; NOT RATIFIED |
| D04 custody/lifecycle recommendation | ASSESSED; NOT RATIFIED |
| Compatibility across D01–D04 | DESIGN REVIEW PASS |
| Physical envelope/schema | OPEN |
| Trust registry and revocation source | OPEN |
| Owner authentication/approval | OPEN |
| Real key operation | NOT AUTHORIZED |
| Verifier implementation | NOT AUTHORIZED |
| Executable G0.23 tests | NOT RUN |
| Runtime/VPS/T0 access | NOT PERFORMED |
| Lifecycle mutation | NOT AUTHORIZED |

## 10. References

- DSSE protocol and PAE: https://github.com/secure-systems-lab/dsse/blob/master/protocol.md
- DSSE scope and envelope semantics: https://github.com/secure-systems-lab/dsse/blob/master/governance/02-scope.md
- RFC 8785 — JSON Canonicalization Scheme: https://www.rfc-editor.org/rfc/rfc8785.html
- RFC 8032 — EdDSA / Ed25519: https://www.rfc-editor.org/rfc/rfc8032.html

These references support technical characteristics only; they do not constitute owner approval or a complete security certification.

## 11. Final verdict and next step

**G0.25: TECHNICAL ASSESSMENT PASS — coherent recommendations for D01–D04 are documented. All four decisions remain OPEN until explicit owner ratification.**

Next gate: owner reviews the recommended profile and makes exact decisions. If any recommendation is rejected or modified, update the compatibility analysis before marking dependent decisions approved. Do not proceed to verifier implementation, real keys, trust registry, evidence-source adapters or runtime integration on the strength of this assessment.

T0 remains independent and protected. CORE_LEDGER and AI_LEDGER remain separate. Paper-only and `AI_EXECUTION_ENABLED=false` remain unchanged.
