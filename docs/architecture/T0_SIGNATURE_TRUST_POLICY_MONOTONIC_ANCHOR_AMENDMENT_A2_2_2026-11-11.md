# T0 Signature / Trust Policy / Monotonic Anchor — Contract Correction A2.2

Date: 2026-11-11  
Repository: `kenznguyen/btcusdt-telegram-signals2`  
Branch: `feature/t0-centralized-data-feeder-p1-20261101`  
Base: Checkpoint Contract v1, as formally amended by its owner-approved bounded VPS + GitHub custody addendum  
Corrects: A1 `docs/architecture/T0_SIGNATURE_TRUST_POLICY_MONOTONIC_ANCHOR_AMENDMENT_A1_2026-11-11.md`  
Status: **DRAFT A2.2 — OWNER-APPROVED STAGE I SYNTHETIC IMPLEMENTATION ONLY — NO PRODUCTION IMPLEMENTATION AUTHORITY**

## 1. Authority, precedence and preservation

1. A2.2 is a contract-correction candidate responding to A2.1 second self-review findings A2.1-R2-01 through A2.1-R2-05. It preserves A2 and A2.1 as historical inputs and applies the explicit overrides in §§14–18 and the owner-approved byte-level clarification in §20 below.
2. A1 remains preserved unchanged as historical design evidence. A2.2 supersedes A2.1, A2 and A1 only where this candidate explicitly replaces or supplements a rule below; all earlier versions remain historical inputs. All other A1 and Checkpoint Contract v1 requirements remain in force.
3. The reviewed A1 snapshot and its source blobs are immutable review inputs. A2.2 is the current new candidate; A2 and A2.1 remain historical candidates and review inputs. This revision does not retroactively change any prior frozen snapshot or review result.
4. This document defines contract semantics and test expectations only. It does not authorize code, schema migration, keys, signatures, trust-root installation, policy or anchor instances, provider/TSA use, VPS/SSH/runtime access, T0 database access, custody mutation or destructive operations.
5. A2.2 is subject to exact-blob self-review and the owner-controlled review/approval decisions recorded in separate evidence. Independent review is not a mandatory gate following the owner's waiver; implementation still requires separate explicit owner authorization.
6. The accepted custody boundary remains the owner-approved bounded VPS + GitHub arrangement. Joint rollback of both locations to the same older valid chain remains undetectable. No WORM, third failure domain, global latestness or absolute anti-rollback claim is made.
7. The initial G1 A proof-of-existence evidence product remains unsigned. A2 governs only a separate future signature/trust extension; it does not retroactively add signer authenticity to G1 A.

Normative terms MUST, MUST NOT, SHOULD, SHOULD NOT and MAY have their usual contract meaning.

## 2. SR-01 — Correct purpose semantics and owner-intent boundary

### 2.1 Replace owner-attestation purpose

A1 §4.2's v1 purpose value `T0_CHECKPOINT_OWNER_ATTESTATION` is superseded for this design by:

- `T0_CHECKPOINT_ISSUER_ATTESTATION`: the authorized checkpoint signer attests only that the exact statement identifies the exact checkpoint object and that the signer performed the cryptographic signing act under the declared policy authorization.

This purpose MUST NOT be described as proof of owner intent, owner approval, exchange truth, source correctness, completeness, durable commit or custody.

The signer role is `CHECKPOINT_SIGNER`. A Trust Policy entry authorizes a key to perform the issuer-signing role; that authorization alone does not make the signer the owner or the owner's delegate.

### 2.2 Separate owner authorization if an owner claim is later required

A future purpose such as `T0_CHECKPOINT_OWNER_APPROVAL` MUST NOT be introduced by relabeling the issuer signature. It requires a distinct Owner Authorization object with at least:

- immutable `authorization_id`, schema/type and exact canonical bytes;
- owner principal/authority identifier and authenticated owner public-key fingerprint or equivalent independently provisioned identity;
- exact subject object ID, type, schema, digest algorithm, digest and byte length;
- explicit action/claim authorized, including whether the authorization covers signing, publication, custody or a named operational decision;
- exact audience/namespace and checkpoint stream;
- scope limitations, validity interval only where trusted-time semantics exist, and revocation/supersession rules;
- owner authorization signature and its own trust/bootstrap chain;
- a detached descriptor with exact object digest and byte length.

The Signature Statement MUST bind the Owner Authorization object's exact ID and digest when such authorization is claimed. The verifier MUST check subject, scope, audience, role, status and authorization chain. Missing, mismatched or untrusted authorization MUST produce `UNTRUSTED` or `BLOCKED`, never owner approval by inference.

A2.1 does not define or authorize an owner key, delegation ceremony or owner-approval product. Until such a separate contract and bootstrap exist, the only permitted claim is issuer attestation.

## 3. SR-02 — Complete Signature Statement and envelope field mapping

### 3.1 Mandatory Signature Statement fields

The A1 Signature Statement remains canonical T0-JCS-1 and retains all A1 fields. It is supplemented with this mandatory mapping. Field names below are normative; all IDs are immutable within their namespace.

| Field | Type / encoding | Binding and verification |
|---|---|---|
| `signature_envelope_id` | Non-empty immutable identifier string | Chosen before signing; included in signed statement and envelope; unique within the signature namespace. Reuse with different statement or signature is `SIGNATURE_ENVELOPE_ID_REUSE`. |
| `signing_software_id` | Stable software product identifier | Signed; resolves to the declared software identity record. |
| `signing_software_version` | Version string | Signed; exact version, no floating alias such as `latest`. |
| `signing_build_digest_algorithm` | Registered digest identifier | Signed; must match policy-approved provenance profile. |
| `signing_build_digest` | Lowercase hex digest | Signed; commits to exact build artifact or reproducible build statement. |
| `signing_request_id` | Immutable request identifier | Signed; unique in request namespace. |
| `signing_decision_id` | Immutable decision identifier | Signed; identifies the authorization decision that allowed this signing operation. |
| `signing_decision_digest` | Digest descriptor | Signed; exact canonical decision-evidence object digest and length. |
| `signer_authority_evidence_id` | Immutable object ID | Signed; exact signer authorization/delegation evidence object. |
| `signer_authority_evidence_digest` | Digest descriptor | Signed; exact digest algorithm, digest and byte length of the authorization evidence object. |
| `signer_custody_evidence_id` | Immutable object ID or explicit `NOT_APPLICABLE` enum | Signed; identifies key-custody authorization evidence. `NOT_APPLICABLE` is permitted only if the selected signature profile/policy explicitly allows it. |
| `signer_custody_evidence_digest` | Digest descriptor or explicit `NOT_APPLICABLE` | Signed; must agree with the preceding field. |
| `owner_authorization_id` | Immutable object ID or explicit `NOT_CLAIMED` enum | Signed; only present as a claim when separately authorized under §2.2. |
| `owner_authorization_digest` | Digest descriptor or explicit `NOT_CLAIMED` | Signed; exact subject authorization evidence. |

The existing fields for statement type, purpose, audience, exact Evidence Object descriptor, checkpoint identity/sequence/predecessor, signer fingerprint/role, Trust Policy identity/sequence/digest and profile/algorithm remain mandatory. The purpose MUST use `T0_CHECKPOINT_ISSUER_ATTESTATION` unless a separately approved future contract defines another purpose.

### 3.2 Referenced evidence object contract

Every non-null evidence reference in §3.1 MUST resolve to an immutable descriptor containing:

- object ID, type, schema version and namespace;
- canonicalization profile;
- digest algorithm, exact digest and exact byte length;
- issuer identity and role;
- authorization scope and audience;
- signature statement/envelope reference where the evidence object is signed.

The verifier MUST retrieve the exact bytes from the supplied frozen verification input set, recompute digest and length, validate the evidence object's own trust chain and verify that its scope authorizes the statement field that references it. A producer-supplied label, URL or mutable metadata is not proof.

If an evidence reference is required but absent, unresolved, digest-mismatched or outside its authorized scope, verification MUST fail closed with a stable reason code.

### 3.3 Envelope identity and circularity

`signature_envelope_id` is assigned before signing and is included in the signed Signature Statement. It is not computed from the completed envelope bytes. The completed envelope digest is a separate post-signing digest:

```
signature_envelope_digest =
  SHA256(
    UTF8("T0-SIGNATURE-ENVELOPE-OBJECT-V1\\0")
    || U64BE(byte_length(canonical_envelope_bytes))
    || canonical_envelope_bytes
  )
```

The canonical envelope contains the exact canonical statement bytes, signature algorithm/profile repeated for consistency, signature bytes and the signed `signature_envelope_id`. Mutable transport metadata MUST be excluded from canonical envelope bytes. The verifier recomputes the envelope digest; it MUST NOT trust a producer-supplied digest.

An envelope ID collision with different canonical envelope bytes is `SIGNATURE_ENVELOPE_ID_REUSE`. An exact duplicate read of identical bytes is idempotent.

## 4. SR-03 — Crash-consistent anchor advancement and two-copy publication

### 4.1 Required durable authority

Anchor advancement MUST be serialized by one authorized anchor authority using a durable transition journal. A process-local mutex, memory-only sequence counter or read-then-write sequence is insufficient.

The implementation MUST identify one durable state authority and prove that its compare-and-advance operation is atomic across process restart. The journal and state authority are implementation choices still requiring a separate design/approval; this A2.1 does not select a database, filesystem, provider or runtime.

The durable authority MUST record at least:
- stream/audience and current accepted anchor sequence/digest;
- candidate sequence/digest and exact predecessor;
- transition ID and deterministic idempotency key;
- state and state-transition evidence;
- exact publication/readback receipts for VPS and GitHub;
- failure/recovery reason and operator authorization, where applicable.

### 4.2 Normative transition state machine

Each proposed successor MUST follow this state machine in order:

1. `CANDIDATE_CREATED`: exact anchor statement/envelope candidate bytes and predecessor are fixed. No sequence is accepted.
2. `AUTHORIZATION_VERIFIED`: signer role, policy, signature and checkpoint descriptor have passed. Candidate bytes cannot be mutated after this point.
3. `TRANSITION_RESERVED`: durable atomic compare-and-reserve confirms that the predecessor is the current accepted head and reserves exactly predecessor sequence + 1 for this transition ID. A competing writer MUST receive `ANCHOR_ADVANCE_CONFLICT`.
4. `VPS_PUBLISHED`: exact candidate bytes are written to the designated VPS custody location and read back independently with matching digest.
5. `GITHUB_PUBLISHED`: exact candidate bytes are written to the designated GitHub evidence location and read back independently with matching digest.
6. `BOTH_COPIES_VERIFIED`: both exact copies, descriptors, predecessor chain and custody receipts are verified. A missing/mismatched copy blocks progress.
7. `HEAD_COMMITTED`: the durable authority atomically commits the candidate as accepted head, conditional on the same reserved predecessor and transition ID. **This is the sole linearization point at which the candidate becomes the accepted head.**
8. `COMPLETE`: durable completion record is appended. The transition is closed; historical records are not overwritten.

Before `HEAD_COMMITTED`, the candidate is pending and MUST NOT be presented as the accepted current head. After `HEAD_COMMITTED`, the anchor is the accepted head even if a later completion-notification step fails; recovery MUST finish the same transition, not create a new sequence.

### 4.3 Crash and partial-publication recovery

- Crash before `TRANSITION_RESERVED`: candidate may be discarded; accepted head is unchanged.
- Crash after reservation but before both verified copies: transition remains pending; no sequence N+1 may be reserved. Recovery MUST resume the exact same immutable candidate and transition ID, or enter an explicitly authorized blocked/aborted recovery state. It MUST NOT silently skip the sequence.
- Only VPS published: verifier reports pending/incomplete custody; retry publishes the same exact bytes to GitHub. It MUST NOT create a different candidate for the reserved sequence.
- Only GitHub published: same rule; retry publishes the same exact bytes to VPS.
- Both published but one readback unavailable/mismatched: transition remains pending/BLOCKED. Do not commit head.
- Both readbacks pass but process crashes before `HEAD_COMMITTED`: recovery re-verifies both copies and commits the same reserved transition using compare-and-advance.
- Crash after `HEAD_COMMITTED`: the accepted head remains committed. Recovery appends/repairs only the completion record and readback evidence for the same transition; it MUST NOT advance sequence again.
- A reserved transition cannot be abandoned and its sequence reused without a durable, authenticated abort record. Abort does not delete or rewrite any historical anchor; a replacement requires a new authorized transition and explicit reason.

### 4.4 Two-copy assurance boundary

The above protocol enforces consistency and recovery within the approved VPS + GitHub boundary. It does not make the two locations independent failure domains, prevent a malicious authority from jointly rolling both back, or establish global latestness. A verifier with conflicting, missing or inaccessible required copies MUST return BLOCKED/UNKNOWN. Both locations unavailable means no availability/recovery claim.

## 5. SR-04 and SR-06 — Deterministic negative-verification suite

### 5.1 Test assertion contract

Every negative case MUST define:
- a clean baseline fixture and one isolated mutation;
- exact expected per-dimension result;
- exactly one aggregate verdict;
- exactly one stable primary reason code;
- expected anchor/policy/object state before and after;
- whether any state transition is forbidden.

A test MUST NOT pass by accepting alternative verdicts. Compound attacks MUST be split into independent fixtures. Secondary diagnostic codes MAY be emitted, but the primary reason code and aggregate result are fixed below.

### 5.2 Deterministic negative cases

| ID | Isolated mutation / condition | Dimension result | Aggregate | Primary reason code |
|---|---|---|---|---|
| A2-NV-01 | Flip one signature bit | Signature INVALID | INVALID | `SIGNATURE_MISMATCH` |
| A2-NV-02 | Signature verified against a different key while trusted signer is known | Signature INVALID | INVALID | `SIGNATURE_MISMATCH` |
| A2-NV-03 | Mutate one manifest byte, retain original descriptor/signature | Object INVALID | INVALID | `EVIDENCE_DIGEST_MISMATCH` |
| A2-NV-04 | Alter signed byte length only | Object INVALID | INVALID | `EVIDENCE_LENGTH_MISMATCH` |
| A2-NV-05 | Substitute another valid checkpoint digest | Binding INVALID | INVALID | `CHECKPOINT_DESCRIPTOR_MISMATCH` |
| A2-NV-06 | Reuse evidence object ID with changed descriptor | Identity INVALID | INVALID | `OBJECT_ID_REUSE` |
| A2-NV-07 | Change object type/schema/canonicalization profile | Binding INVALID | INVALID | `OBJECT_PROFILE_MISMATCH` |
| A2-NV-08 | Change purpose after signing | Statement INVALID | INVALID | `SIGNED_CONTEXT_MISMATCH` |
| A2-NV-09 | Change audience after signing | Statement INVALID | INVALID | `SIGNED_CONTEXT_MISMATCH` |
| A2-NV-10 | Alter signer fingerprint/role/policy digest/algorithm after signing | Statement INVALID | INVALID | `SIGNED_AUTHORIZATION_CONTEXT_MISMATCH` |
| A2-NV-11 | Use unknown or policy-disabled algorithm | Policy UNTRUSTED | UNTRUSTED | `ALGORITHM_NOT_AUTHORIZED` |
| A2-NV-12 | Use known key with wrong role/object/purpose authorization | Signer UNTRUSTED | UNTRUSTED | `SIGNER_SCOPE_UNAUTHORIZED` |
| A2-NV-13 | Omit policy signature | Policy BLOCKED | BLOCKED | `POLICY_SIGNATURE_MISSING` |
| A2-NV-14 | Same policy sequence with different digest | Policy BLOCKED | BLOCKED | `POLICY_EQUIVOCATION` |
| A2-NV-15 | Use revoked key for a new signature | Signer UNTRUSTED | UNTRUSTED | `SIGNER_KEY_REVOKED` |
| A2-NV-16 | Present valid old checkpoint after accepted head advanced | Freshness STALE_REPLAY | STALE_REPLAY | `CHECKPOINT_STALE_REPLAY` |
| A2-NV-17 | Same anchor sequence with different digest | Anchor BLOCKED | BLOCKED | `ANCHOR_EQUIVOCATION` |
| A2-NV-18 | Anchor signature bit flip | Anchor INVALID | INVALID | `ANCHOR_SIGNATURE_MISMATCH` |
| A2-NV-19 | One required anchor copy inaccessible | Custody UNKNOWN | UNKNOWN | `ANCHOR_COPY_UNAVAILABLE` |
| A2-NV-20 | Backdate local clock to claim pre-revocation signing | Historical trust UNKNOWN | UNKNOWN | `TRUSTED_TIME_UNAVAILABLE` |
| A2-NV-21 | Alter pinned bootstrap fingerprint in untrusted producer input | Bootstrap BLOCKED | BLOCKED | `BOOTSTRAP_PIN_MISMATCH` |
| A2-NV-22 | Duplicate JSON keys or noncanonical statement bytes | Parsing INVALID | INVALID | `NONCANONICAL_STATEMENT` |
| A2-NV-23 | Signature valid but checkpoint completeness is UNKNOWN | Completeness UNKNOWN | BLOCKED | `CHECKPOINT_COMPLETENESS_UNKNOWN` |
| A2-NV-24 | Offline verifier lacks required pinned root bytes | Bootstrap BLOCKED | BLOCKED | `TRUST_ROOT_MATERIAL_MISSING` |
| A2-NV-25 | Exact duplicate anchor bytes and sequence | Idempotent read | PASS for idempotent-read assertion | `ANCHOR_DUPLICATE_IDEMPOTENT` |
| A2-NV-26 | Attempt to overwrite prior Verification Record | Record INVALID | INVALID | `VERIFICATION_RECORD_OVERWRITE` |
| A2-NV-27 | VPS and GitHub copies contain different anchor digests | Custody BLOCKED | BLOCKED | `CUSTODY_CONFLICT` |
| A2-NV-28 | Both copies contain same older valid chain; verifier has no independent newer fact | Global freshness NOT ESTABLISHED | UNKNOWN | `GLOBAL_FRESHNESS_UNPROVABLE` |
| A2-NV-29 | Two writers reserve the same next sequence concurrently | Losing transition BLOCKED; accepted head unchanged by loser | BLOCKED | `ANCHOR_ADVANCE_CONFLICT` |
| A2-NV-30 | Valid key is not authorized for declared audience/stream | Signer UNTRUSTED | UNTRUSTED | `SIGNER_AUDIENCE_UNAUTHORIZED` |
| A2-NV-31 | Missing or altered signing build identity/digest | Provenance INVALID | INVALID | `SIGNING_BUILD_PROVENANCE_INVALID` |
| A2-NV-32 | Missing signing request or decision reference | Authorization BLOCKED | BLOCKED | `SIGNING_DECISION_MISSING` |
| A2-NV-33 | Required signer authority evidence is missing | Authorization BLOCKED | BLOCKED | `SIGNER_AUTHORITY_EVIDENCE_MISSING` |
| A2-NV-34 | Signature envelope ID reused with different bytes | Envelope identity INVALID | INVALID | `SIGNATURE_ENVELOPE_ID_REUSE` |
| A2-NV-35 | Owner-approval claim made without a separately trusted Owner Authorization object | Owner claim UNTRUSTED | UNTRUSTED | `OWNER_AUTHORIZATION_MISSING` |
| A2-NV-36 | U64 decimal has a leading zero, sign or non-decimal character | Wire parse INVALID | INVALID | `U64_NONCANONICAL` |
| A2-NV-37 | U64 value exceeds 2^64-1 | Wire parse INVALID | INVALID | `U64_OVERFLOW` |
| A2-NV-38 | Base64url uses padding, standard alphabet or whitespace | Wire parse INVALID | INVALID | `BASE64URL_NONCANONICAL` |
| A2-NV-39 | Crash after VPS publication but before GitHub publication | Anchor transition pending; accepted head unchanged | BLOCKED | `ANCHOR_PUBLICATION_INCOMPLETE` |
| A2-NV-40 | Crash after both readbacks but before head commit | Before recovery: transition pending and accepted head unchanged. After recovery: same reserved transition commits; no N+1 or duplicate sequence | Before recovery BLOCKED; after recovery PASS | `ANCHOR_COMMIT_PENDING` before recovery; `ANCHOR_RECOVERY_COMMITTED` after recovery |
| A2-NV-41 | Missing or invalid root bootstrap owner authorization | Bootstrap BLOCKED | BLOCKED | `ROOT_BOOTSTRAP_UNAUTHORIZED` |
| A2-NV-42 | Missing owner delegation for an explicit owner-approval purpose | Owner authorization UNTRUSTED | UNTRUSTED | `OWNER_DELEGATION_INVALID` |
| A2-NV-43 | Signer authority evidence is present but its digest does not match exact bytes | Authorization INVALID | INVALID | `SIGNER_AUTHORITY_DIGEST_MISMATCH` |

A2-NV-40 is a stateful recovery test with two ordered assertions: pending before recovery, then successful commit of the same reserved transition after recovery. A2-NV-33 and A2-NV-43 are separate single-fault fixtures; no fixture may combine missing evidence with a digest mismatch.

### 5.3 Known undetectable boundary assertion (not a detection test)

The common-mode rollback case is an assurance-boundary assertion, not a detected attack:
- Given two byte-identical VPS and GitHub copies of the same older valid chain, and no independent newer anchor fact;
- the verifier MUST report `UNKNOWN` with `GLOBAL_FRESHNESS_UNPROVABLE`;
- it MAY report `CONSISTENT_WITH_RETAINED_ANCHOR_HEAD` only as a separate bounded consistency dimension;
- it MUST NOT claim global latestness, absolute anti-rollback or detection of the joint rollback.

This assertion is retained for traceability as the former A1 NV-28 boundary but is not counted among the negative detection cases.

### 5.4 State assertions

- Any failed policy, signature or descriptor check MUST leave accepted policy/anchor head unchanged.
- A failed anchor writer MUST NOT advance sequence, overwrite predecessor records or permit a successor to skip the pending sequence.
- Exact duplicate publication MUST be idempotent and MUST NOT advance sequence.
- All Verification Records are append-only. Re-verification appends a new record; it does not mutate the prior record.
- Positive tests MUST use independently implemented byte-vector oracles, not the same producer helper as verifier.

## 6. SR-05 — Canonical integer and binary wire primitives

### 6.1 U64 logical integer

Every logical integer serialized under A1/A2 as a decimal string MUST conform to the unsigned 64-bit range:

`0 <= value <= 18446744073709551615`.

Canonical wire grammar:
- ASCII decimal digits only;
- exactly `0` for zero;
- no leading zero for nonzero values;
- no plus/minus sign, exponent, decimal point, whitespace or separators;
- reject overflow before conversion;
- JSON numeric tokens are forbidden for fields declared as logical integers.

`U64BE(value)` is exactly 8 octets, big-endian, of the decoded logical integer value. It is not the UTF-8 encoding or byte length of the decimal string.

Required vectors:
- 0 → `0000000000000000`
- 1 → `0000000000000001`
- 18446744073709551615 → `ffffffffffffffff`
- 18446744073709551616 → reject `U64_OVERFLOW`
- `00`, `01`, `+1`, `-1`, `1.0`, `1e0`, whitespace and empty string → reject `U64_NONCANONICAL`

Schema-specific narrower limits (for example a timestamp or version bound) MUST be declared by that field's schema in addition to the U64 primitive. A field cannot silently accept values outside its semantic range merely because they fit U64.

### 6.2 Base64url

All binary values in canonical JSON envelopes use unpadded RFC 4648 base64url:
- alphabet is `A-Z a-z 0-9 - _`;
- `=` padding, standard Base64 `+` and `/`, whitespace and all other characters are forbidden;
- decoder MUST reject noncanonical pad bits and any value that does not round-trip exactly through canonical decode/re-encode;
- empty bytes encode as empty string only where the field schema explicitly permits empty bytes.

Required vectors:
- empty bytes → `""` only for fields explicitly allowing empty;
- byte `00` → `AA`;
- byte `FF` → `_w`;
- byte `FB` → `-w`;
- padded, standard-alphabet, whitespace and malformed encodings → reject `BASE64URL_NONCANONICAL`.

The selected signature profile MUST additionally define accepted public-key encoding and signature-byte format. A2.1 does not select the production signature algorithm.

## 7. SR-08 — Owner-pinned Trust Bootstrap Record

### 7.1 Bootstrap record schema

Define `T0-TRUST-BOOTSTRAP-RECORD-V1`. Its canonical record MUST contain:

- exact record type and schema version;
- stable trust namespace and audience;
- bootstrap sequence and explicit genesis marker;
- root key type and exact accepted public-key encoding identifier;
- exact root public-key bytes in canonical unpadded base64url;
- lowercase SHA-256 fingerprint over the exact decoded DER SubjectPublicKeyInfo octets;
- root role and permitted policy-signature profile/algorithm identifiers;
- bootstrap version and verifier minimum version;
- owner authorization evidence ID and digest;
- recovery/rotation policy identifier and predecessor reference;
- explicit statement that the record is provisioned out-of-band from the checkpoint producer.

The verifier MUST decode the public-key bytes, recompute the SPKI fingerprint and compare it to the independently pinned fingerprint. A fingerprint without a trusted source of the corresponding public-key bytes is insufficient to verify signatures. A producer-supplied key, record or URL MUST NOT establish or replace the pin.

### 7.2 Pinning and recovery

The verifier's trust pin MUST be provisioned through an owner-controlled channel independent of the checkpoint producer and ordinary evidence publication. The exact channel, custody, operator ceremony and recovery procedure remain implementation/owner decisions and MUST be documented before implementation approval.

Root rotation MUST be authorized by the currently pinned root and bind the exact successor bootstrap record digest, namespace, audience, sequence and predecessor. If the current root is compromised/unavailable, recovery requires a separately owner-approved recovery authority/ceremony. No automatic TOFU, network fetch, Git branch-head substitution or producer-supplied fallback is allowed.

If bootstrap record, owner authorization, root bytes, pin, role, profile or recovery evidence is missing or contradictory, verifier returns BLOCKED/UNKNOWN. No trust root is generated, installed or selected by this A2 document.

## 8. SR-07 — Snapshot and draft status terminology

The following terms MUST be used consistently:
- **Byte-frozen review candidate:** exact source blobs/commit are fixed so a reviewer can reproduce the reviewed input. This does not mean the contract is approved.
- **Draft contract:** normative proposal remains open to findings and owner/security decisions.
- **Owner-approved contract decision:** only the specifically recorded owner-approved scope is approved; this does not imply implementation authority.
- **Implementation-approved:** a separate explicit owner authorization with exact source snapshot, bounded scope, permitted environment and prohibited operations. Independent review is not a prerequisite under the owner waiver.

A2.2 is a **DRAFT CONTRACT / BYTE-FROZEN ONLY WHEN A SPECIFIC REVIEW SNAPSHOT IS DECLARED**. It is not implementation-approved. The prior A1, A2 and A2.1 snapshots remain historical review inputs. A same-session self-review MUST NOT be called independent review, external review or G3.

## 9. Updated owner/security decisions and implementation blockers

The following remain unresolved and block implementation:
1. Production signature algorithm and exact profile/version.
2. Owner-controlled bootstrap provisioning, root custody, rotation and recovery ceremony.
3. Actual checkpoint signer identity, role enrollment and signer key custody.
4. Actual anchor authority identity, durable journal technology and concurrency mechanism.
5. Whether trusted-time/TSA evidence is required for any historical trust-at-time claim.
6. Exact policy/anchor/evidence retention and recovery requirements.
7. Any future Owner Authorization/delegation contract if owner-intent claims are required.
8. Independent second implementation and byte-vector conformance.
9. Concrete field-to-source evidence mapping and verifier behavior for every mandatory provenance reference.

The owner-approved VPS + GitHub bounded custody decision remains resolved only for that bounded claim. No external monotonic anchor is authorized.

## 10. Acceptance gates and unchanged boundaries

Before implementation can be considered:
1. Freeze the exact A2.2 source blob and all dependency blob pins.
2. Perform a fresh adversarial self-review of that exact A2.2 candidate.
3. Record the owner's review-gate decision against the exact A2.2 blob set. Independent review may be commissioned voluntarily, but is not mandatory under the owner waiver.
4. Resolve all blocking findings and owner/security decisions.
5. Obtain a separate explicit owner implementation approval for a narrowly scoped synthetic-only implementation plan.
6. Implement only after approval, with TDD, independent vector oracle, offline tests, exact-SHA CI evidence and rollback plan.
7. Any VPS, provider, TSA, key custody, production trust-root or canonical T0 integration requires separate explicit approval.

No code, test, workflow, CI configuration, key, signature, trust root, policy instance, anchor instance, provider/TSA, VPS/SSH/runtime, SQLite database, canonical T0 data, retention policy or destructive operation is changed or exercised by this contract draft. Paper-only posture and `AI_EXECUTION_ENABLED=false` remain unchanged.

**A2.1 disposition: DRAFT CORRECTION CANDIDATE — A2-SR-01/02 ADDRESSED AT CONTRACT-DESIGN LEVEL — NOT INDEPENDENTLY REVIEWED — NOT IMPLEMENTATION-APPROVED.**


## 11. A2-SR-01 — Explicit rejection of legacy purpose in the A2.2 profile

This section is normative and overrides any inconsistent implication in §§1–10 or inherited A1 text.

1. For every object verified under the A2.1 profile, the only permitted checkpoint-signature purpose is `T0_CHECKPOINT_ISSUER_ATTESTATION`.
2. The A2.2 Trust Policy schema and every policy entry authorizing this checkpoint-signature flow MUST enumerate `T0_CHECKPOINT_ISSUER_ATTESTATION` explicitly. An omitted purpose, wildcard purpose, inherited default, or legacy-purpose fallback MUST NOT authorize the operation.
3. An A2.2 verifier MUST reject `T0_CHECKPOINT_OWNER_ATTESTATION` when presented for an A2.2 object, regardless of whether the signature is cryptographically valid or an A1-era key/policy would otherwise accept it. The deterministic aggregate verdict is `UNTRUSTED`; primary reason code is `PURPOSE_NOT_SUPPORTED_BY_PROFILE`. No policy head, anchor head or accepted checkpoint state may advance.
4. A historical A1 object MAY be evaluated only by an explicitly selected A1 historical-verification profile and its pinned historical Trust Policy. The verifier MUST retain the object's A1 version/type and original purpose. It MUST NOT relabel, upgrade, reinterpret or re-issue the historical object as A2/A2.1. A1 historical acceptance MUST NOT authorize an A2.1 object.
5. An A2.1 verifier MUST NOT silently downgrade to A1 when an A2.1 purpose or policy check fails. Profile selection is explicit and bound to the verification request and signed object descriptor.
6. Add mandatory negative cases:
   - **A2.1-NV-01:** A2.1 object carries legacy `T0_CHECKPOINT_OWNER_ATTESTATION` with an otherwise valid signature → `UNTRUSTED`, `PURPOSE_NOT_SUPPORTED_BY_PROFILE`; accepted state unchanged.
   - **A2.1-NV-02:** A2.1 policy omits issuer purpose or uses wildcard/implicit fallback → `BLOCKED`, `POLICY_PURPOSE_NOT_EXPLICIT`; accepted state unchanged.
   - **A2.1-NV-03:** A1 historical object is relabeled as A2.1 or silently verified through A2.1 profile → `INVALID`, `PROFILE_VERSION_MISMATCH`; accepted state unchanged.
   - **A2.1-NV-04:** A2.1 purpose check fails and verifier attempts automatic A1 fallback → `BLOCKED`, `PROFILE_DOWNGRADE_FORBIDDEN`; accepted state unchanged.

## 12. A2-SR-02 — Independent bootstrap authorization and non-circular root enrollment

This section is normative and overrides any inconsistent or incomplete implication in §7.

### 12.1 Bootstrap authorization object

Define `T0-TRUST-BOOTSTRAP-AUTHORIZATION-V1`. The authorization MUST be independently verifiable and MUST bind all of the following exact values:

- authorization object ID, type, schema version and canonicalization profile;
- exact bootstrap record digest algorithm, digest and byte length;
- trust namespace and audience;
- root key type, exact SPKI fingerprint and permitted root role;
- permitted policy-signature profile/algorithm identifiers;
- bootstrap sequence and explicit genesis/predecessor state;
- recovery/rotation policy identifier and digest;
- explicit authorization action: initial enrollment of this root for this namespace/audience and the stated scope;
- issuer authority identity, role, validity/revocation semantics where trusted time is available, and exact signature descriptor if signed.

The verifier MUST recompute the bootstrap record digest from the exact canonical record bytes and compare every bound field. An authorization that binds only a root fingerprint but not the exact bootstrap record and its namespace, audience, role, profile, sequence and recovery policy is insufficient.

### 12.2 Exactly one approved independent verification path

Bootstrap MUST use exactly one of the following documented paths. The selected path and its verifier configuration MUST be explicit; mixing partial evidence from both paths is not permitted.

**Path A — separately pre-pinned owner authority**
- The owner-authority public key/fingerprint is provisioned to the verifier through an out-of-band channel independent of the checkpoint producer, newly enrolled root and ordinary VPS/GitHub evidence publication.
- The bootstrap authorization object is signed by that owner authority using a separately approved authorization-signature profile.
- The verifier validates the authorization signature against the pre-pinned owner authority and verifies all §12.1 bindings before accepting the root bootstrap record.
- The newly enrolled root MUST NOT sign, countersign, attest or otherwise be the sole authority validating its own initial enrollment.

**Path B — owner-controlled provisioning ceremony**
- A documented owner-controlled ceremony provisions the exact canonical bootstrap record digest directly into the verifier's trusted configuration through an independent channel.
- The ceremony record MUST identify the owner-authorized operator/authority, verifier identity and configuration target, exact bootstrap digest, namespace, audience, root SPKI fingerprint, role, profile, sequence, recovery policy, date/time as an untrusted operational annotation, and the authorization and readback results.
- The verifier MUST receive/pin the exact digest independently of the checkpoint producer and normal evidence stores. A copy of the ceremony record placed only beside the bootstrap record is not independent evidence.
- The enrolled root MUST NOT be used as the sole authority to authenticate the ceremony or its own initial enrollment.

**Path A qualification:** The owner-authority authorization format is not fully specified by this amendment. Path A MUST NOT be implemented or accepted until a separate owner-approved contract defines its canonical authorization-object schema, exact signed preimage/envelope, algorithm/profile, issuer-key identity and revocation/recovery rules. The owner-authority pin itself must already be provisioned independently; the authorization object or newly enrolled root cannot establish that pin. Until those prerequisites exist, Path A is unavailable and bootstrap remains BLOCKED unless Path B is fully evidenced.

**Path B evidence mapping:** When Path B is selected, the bootstrap record's `owner_authorization_evidence_id` and `owner_authorization_evidence_digest` MUST identify the exact canonical provisioning-ceremony record and its digest/byte length. The verifier's independently pinned bootstrap digest and the ceremony record's readback MUST agree byte-for-byte with the canonical bootstrap record. The ceremony record is evidence of the owner-controlled provisioning action, not a self-authenticating signature; its authority comes from the independent verifier provisioning channel and recorded operator authorization.

### 12.3 Fail-closed and recovery rules

1. If neither Path A nor Path B is fully evidenced and configured, initial bootstrap verdict is `BLOCKED` with primary reason `ROOT_BOOTSTRAP_AUTHORIZATION_UNVERIFIED`.
2. If an authorization object is present but its signature, issuer authority, exact bootstrap digest, namespace, audience, root fingerprint, role, profile, sequence or recovery-policy binding is invalid, verdict is `INVALID` with primary reason `ROOT_BOOTSTRAP_AUTHORIZATION_MISMATCH`.
3. If the owner authority/pin, ceremony evidence, verifier identity/configuration, or independent channel readback is unavailable, verdict is `UNKNOWN` with primary reason `ROOT_BOOTSTRAP_INDEPENDENCE_UNVERIFIED`.
4. The newly enrolled root MUST NOT authenticate its own bootstrap authorization, establish the owner-authority pin, or substitute for a missing independent owner authority/ceremony.
5. Root rotation and emergency recovery MUST follow the currently pinned owner authority or a separately pre-authorized recovery authority. The newly rotated root cannot authorize its own predecessor replacement.
6. No TOFU, producer-supplied key/pin, Git branch-head substitution, VPS/GitHub co-publication alone, or implicit network retrieval is permitted as initial bootstrap authorization.

### 12.4 Required bootstrap negative cases

- **A2.1-NV-05:** No independently verified owner authorization/ceremony → `BLOCKED`, `ROOT_BOOTSTRAP_AUTHORIZATION_UNVERIFIED`.
- **A2.1-NV-06:** Authorization binds another bootstrap digest or any mismatched namespace/audience/root/role/profile/sequence/recovery policy → `INVALID`, `ROOT_BOOTSTRAP_AUTHORIZATION_MISMATCH`.
- **A2.1-NV-07:** Only the newly enrolled root signs or attests its own enrollment → `BLOCKED`, `ROOT_BOOTSTRAP_SELF_AUTHORIZATION_FORBIDDEN`.
- **A2.1-NV-08:** Independent owner pin/ceremony readback cannot be obtained → `UNKNOWN`, `ROOT_BOOTSTRAP_INDEPENDENCE_UNVERIFIED`.
- **A2.1-NV-09:** A producer-supplied key, record, URL or ordinary VPS/GitHub copy is offered as the independent owner pin → `BLOCKED`, `ROOT_BOOTSTRAP_PRODUCER_INPUT_UNTRUSTED`.

## 13. A2.1 disposition and unchanged gates

A2.2 is a documentation-only correction candidate. The original A2 blob remains preserved as historical review input. These additions address only A2-SR-01 and A2-SR-02 at contract-design level; they do not close implementation blockers listed in §9.

The A2.2 source blob and each review disposition MUST be recorded in separate exact-blob evidence reports. Independent review is waived as a mandatory gate by the owner decision; this document does not encode mutable gate status. Implementation still requires a separate explicit owner approval. No algorithm, key, owner authority, bootstrap ceremony, trust root, policy/anchor instance, verifier, workflow, CI, VPS/runtime or canonical T0 operation is selected or exercised here.

**A2.2 disposition: DRAFT CORRECTION CANDIDATE — R2-01..R2-05 CORRECTIONS PROPOSED — REVIEW-GATE STATUS RECORDED IN SEPARATE EXACT-BLOB EVIDENCE — NOT IMPLEMENTATION-APPROVED.**


## 14. A2.1-R2-01 — Revision identity, status and review-gate precedence

This section is normative and overrides inconsistent revision/status language in §§1–13.

1. The current candidate defined by this document is **A2.2**. A2.1 (blob `73ba6fd9f6bb862121842f7a1347fffc06738451`) and A2 (blob `e15a90b779bd86b39729208db938e9de9471ef26`) are historical candidate/review inputs, not the current candidate.
2. A2.1's prior self-review report and second self-review report remain separate historical records. The second review disposition for A2.1 is REQUEST CHANGES. Neither report is a review of A2.2.
3. A2.2 review state is tracked only against its exact source blob and pinned dependency blobs. Drafting, static source checks, self-review, optional independent review and implementation approval are distinct records; none implies a later gate.
4. The status vocabulary is exact:
   - `DRAFT`: proposed normative text, not owner-approved.
   - `BYTE_FROZEN`: exact source blob set is recorded; no claim of approval.
   - `SELF_REVIEW_PASS`: same-session adversarial review completed with no blocking findings for the declared scope; not independent assurance.
   - `INDEPENDENT_REVIEW_PASS`: qualifying reviewer independent of authors/editors and relevant T0/signing/trust/anchor/custody operators has reviewed the exact blob set and recorded findings/disposition.
   - `IMPLEMENTATION_APPROVED`: separate explicit owner authorization naming exact source blobs, bounded implementation scope, permitted environment and prohibited operations.
5. A2.2 is `DRAFT` and documentation-only. Byte-freeze, self-review, independent-review and implementation-approval states are external evidence records bound to exact source blobs; they MUST be read from the latest Handoff and corresponding exact-blob evidence reports, not inferred from this static document label.
6. Historical A1/A2/A2.1 text may be quoted or superseded only by an explicit normative rule. A historical status line MUST NOT be interpreted as the status of A2.2.
7. No text in this section promotes A2.1's earlier self-review disposition. The later A2.1 second review REQUEST CHANGES supersedes its earlier "ready for independent review" recommendation for the A2.1 candidate.

## 15. A2.1-R2-05 — Immutable machine-readable signature profile identity

This section is normative and overrides any document-label-only interpretation of "A2.2 profile" or inherited generic profile references.

### 15.1 Profile identity

The checkpoint issuer-signature profile proposed by this contract has the following immutable protocol identity:

- `signature_profile_id`: `T0-CHECKPOINT-ISSUER-SIGNATURE-PROFILE-V2`
- `signature_profile_version`: `2`
- `profile_namespace`: `T0`
- `profile_purpose`: `T0_CHECKPOINT_ISSUER_ATTESTATION`

The identifier/version pair is a protocol value, not the document revision number. A2.2, A2.3 or later editorial revisions MUST NOT silently change its semantics. A semantic profile change requires a new profile ID or explicitly versioned profile, a separate policy authorization and a migration/retirement rule. The production cryptographic algorithm remains unselected.

### 15.2 Mandatory binding locations

The exact `signature_profile_id` and `signature_profile_version` MUST appear and agree in:
1. signed Evidence Object descriptor / checkpoint signature descriptor;
2. canonical Signature Statement, inside the signed preimage;
3. detached signature envelope descriptor;
4. Trust Policy profile authorization entry;
5. Trust Policy signed statement/digest binding;
6. bootstrap record and bootstrap authorization, once a bootstrap path has separately been approved;
7. verifier request and verifier's locally selected allowed-profile configuration.

No location may infer the profile from a filename, document title, branch name, algorithm, key type, producer metadata or another location's omission. The verifier MUST compare exact values across all applicable locations before cryptographic acceptance or state transition.

### 15.3 Profile selection and lifecycle

- The verification request MUST explicitly select exactly one `signature_profile_id` and `signature_profile_version`.
- Unknown ID/version → `BLOCKED`, `PROFILE_UNKNOWN`.
- Known but not enabled by the verifier's pinned local configuration → `BLOCKED`, `PROFILE_NOT_ENABLED`.
- Retired profile presented for a new signature → `UNTRUSTED`, `PROFILE_RETIRED`; historical verification is allowed only under an explicitly selected historical profile and its pinned policy.
- Any mismatch among request, descriptor, statement, envelope, policy or bootstrap binding → `INVALID`, `PROFILE_BINDING_MISMATCH`.
- Attempted implicit fallback to an older profile after any failure → `BLOCKED`, `PROFILE_DOWNGRADE_FORBIDDEN`.
- The verifier MUST NOT accept a profile solely because a producer supplied its definition or key material.
- Profile checks are preconditions; failure MUST leave trust root, policy head, anchor head and accepted checkpoint state unchanged.

## 16. A2.1-R2-02 — Bootstrap trust-path availability and Path B exclusion

This section is normative and replaces A2.1 §12.2's presentation of Path A and Path B as two selectable alternatives.

### 16.1 Bootstrap state for this draft

**No bootstrap path is currently enabled or implementation-ready.** The only future candidate path is Path A, and it remains unavailable until a separate owner-approved contract defines the owner-authority authorization format, exact signed preimage/envelope, cryptographic profile, issuer identity, revocation, rotation and recovery. Therefore an implementation conforming to this draft MUST currently return `BLOCKED` for initial trust bootstrap; it MUST NOT enroll a root.

### 16.2 Path A — separately pre-pinned owner authority (deferred)

Path A may be considered only after a separate contract specifies all of the following:
- owner-authority public key and exact fingerprint provisioned to the verifier before bootstrap through an independently authenticated owner-controlled provisioning process;
- canonical authorization-object schema, exact bytes, digest/length and signed preimage/envelope;
- fixed authorization-signature algorithm/profile and key encoding;
- issuer principal, role, delegation scope, validity/revocation and compromise handling;
- exact binding to bootstrap record digest, namespace, audience, root SPKI fingerprint, role, profile ID/version, sequence and recovery policy;
- verifier pin provenance, provisioning operator authentication, configuration readback and recovery/rotation procedure;
- deterministic failure semantics and negative test vectors.

The owner-authority pin MUST NOT be established by the new root, checkpoint producer, ordinary VPS/GitHub co-publication or the authorization object itself. Until that separate contract is owner-approved and its independent pin/readback evidence exists, Path A state is `NOT_ENABLED`.

### 16.3 Path B — explicitly unavailable, not an alternate bootstrap mechanism

Path B's owner-controlled provisioning ceremony is **not a currently permitted verification path**. The earlier A2.1 description did not establish a complete authenticated trust boundary for the verifier's privileged configuration channel or prove that the operator was owner-authorized.

Path B MUST remain disabled unless a separate owner-approved Verifier Provisioning Authority Contract defines:
- the verifier's pre-existing administrative trust anchor and how it is provisioned independently before this bootstrap;
- authenticated verifier identity and configuration target;
- operator identity proof, owner delegation/authorization, scope and revocation;
- mutually authenticated provisioning channel and integrity/confidentiality requirements;
- exact authorized configuration operation and transaction semantics;
- canonical ceremony record, event ordering, anti-replay identifier and audit evidence;
- independent readback of the exact resulting configuration and bootstrap digest;
- compromise, interruption, rollback and recovery behavior;
- deterministic negative fixtures and reason codes.

A ceremony record alone is not authority. A log entry, VPS/GitHub copy, SSH session assertion, producer-supplied credential or newly enrolled root signature MUST NOT establish the provisioning authority. Until the separate contract is approved and its pre-existing trust anchor, operator authorization and authenticated channel are independently verified, Path B is `NOT_ENABLED`.

Path A and Path B MUST NOT be mixed to repair missing evidence. The newly enrolled root MUST NOT authenticate either path or bootstrap its own enrollment.

## 17. A2.1-R2-03 — Deterministic bootstrap verdict decision table

This section is normative and replaces A2.1 §12.3. The verifier evaluates conditions in the exact order below and emits exactly one aggregate verdict and one primary reason code. First matching row wins. No failure row may advance or mutate trust root, policy head, anchor head, accepted checkpoint head or bootstrap sequence.

| Priority | Path/state predicate | Dimension result | Aggregate | Primary reason |
|---:|---|---|---|---|
| 1 | No path selected in verifier's pinned local configuration | Bootstrap not configured | BLOCKED | `ROOT_BOOTSTRAP_PATH_NOT_CONFIGURED` |
| 2 | Selected path is Path A or B but that path is not enabled by its separately approved contract/configuration | Path unavailable | BLOCKED | `ROOT_BOOTSTRAP_PATH_NOT_ENABLED` |
| 3 | Required evidence is absent and the configured source was successfully read | Evidence missing | BLOCKED | `ROOT_BOOTSTRAP_EVIDENCE_MISSING` |
| 4 | Required trusted configuration, owner pin or authenticated channel cannot be reached/read, so absence cannot be established | Trust boundary unavailable | UNKNOWN | `ROOT_BOOTSTRAP_TRUST_BOUNDARY_UNAVAILABLE` |
| 5 | Newly enrolled root is sole authority for initial enrollment | Self-authorization forbidden | BLOCKED | `ROOT_BOOTSTRAP_SELF_AUTHORIZATION_FORBIDDEN` |
| 6 | Producer-supplied key, URL, record or co-published VPS/GitHub evidence is offered as independent trust anchor | Untrusted bootstrap input | BLOCKED | `ROOT_BOOTSTRAP_PRODUCER_INPUT_UNTRUSTED` |
| 7 | Evidence from Path A and Path B is combined, or path identity changes mid-verification | Path substitution | BLOCKED | `ROOT_BOOTSTRAP_PATH_MIXING_FORBIDDEN` |
| 8 | Authorization object is present but fails its approved signature/issuer/delegation validation, excluding the self-authorization case in priority 5 | Authorization invalid | INVALID | `ROOT_BOOTSTRAP_AUTHORIZATION_INVALID` |
| 9 | Exact bootstrap record digest/length differs from the independently authorized subject | Subject binding invalid | INVALID | `ROOT_BOOTSTRAP_DIGEST_MISMATCH` |
| 10 | Namespace differs | Namespace binding invalid | INVALID | `ROOT_BOOTSTRAP_NAMESPACE_MISMATCH` |
| 11 | Audience differs | Audience binding invalid | INVALID | `ROOT_BOOTSTRAP_AUDIENCE_MISMATCH` |
| 12 | Root SPKI fingerprint differs | Root binding invalid | INVALID | `ROOT_BOOTSTRAP_ROOT_FINGERPRINT_MISMATCH` |
| 13 | Root role differs | Role binding invalid | INVALID | `ROOT_BOOTSTRAP_ROLE_MISMATCH` |
| 14 | Profile ID/version differs | Profile binding invalid | INVALID | `ROOT_BOOTSTRAP_PROFILE_MISMATCH` |
| 15 | Bootstrap sequence/genesis/predecessor differs | Sequence binding invalid | INVALID | `ROOT_BOOTSTRAP_SEQUENCE_MISMATCH` |
| 16 | Recovery/rotation policy ID or digest differs | Recovery binding invalid | INVALID | `ROOT_BOOTSTRAP_RECOVERY_POLICY_MISMATCH` |
| 17 | Readback source is reachable but bytes/digest differ from the authorized exact configuration | Readback integrity invalid | INVALID | `ROOT_BOOTSTRAP_READBACK_MISMATCH` |
| 18 | Readback is required but temporarily/unexpectedly inaccessible after authorization and configuration | Readback unavailable | UNKNOWN | `ROOT_BOOTSTRAP_READBACK_UNAVAILABLE` |

### 17.1 Precedence and state invariants

1. Local path configuration is evaluated before evidence content. An unconfigured/disabled path is BLOCKED, not UNKNOWN.
2. UNKNOWN is reserved for a previously configured trust boundary or required readback that is inaccessible such that its state cannot be determined. A successfully read source that confirms missing evidence is BLOCKED.
3. INVALID is reserved for present, readable evidence/configuration that cryptographically fails or contradicts an exact authorized binding.
4. If multiple invalid fields are mutated, the fixture is invalid because it violates the single-mutation rule; production verifier primary-reason precedence follows the table's order.
5. On every non-PASS bootstrap verdict: bootstrap remains unaccepted; no root is enrolled; trust root, policy head, anchor head, accepted checkpoint head and sequence remain byte-for-byte/logically unchanged. No partial trust transition is allowed.
6. A bootstrap PASS is impossible under this draft alone because neither path is enabled. A future separately approved path contract may define the positive acceptance transition and must preserve all invariants here.

## 18. A2.1-R2-04 — Complete deterministic negative fixtures for A2.2 overrides

This section supplements A2 §5.1 and replaces the abbreviated A2.1-NV-01..09 cases. Every case below uses a fully specified clean or explicitly named precondition baseline and changes exactly one field or condition.

### 18.1 Shared clean baseline fixture B0

B0 is a synthetic, offline-only fixture. Its test-only signer and Trust Policy are cryptographically valid under an isolated fixture profile; this does not select a production algorithm or create a production trust root. It contains:
- one A2.2 checkpoint descriptor and one canonical Evidence Object whose bytes, ID, type, schema, digest and byte length are mutually consistent;
- Signature Statement and detached envelope with identical `T0-CHECKPOINT-ISSUER-SIGNATURE-PROFILE-V2` / version `2` values at every applicable descriptor, statement and envelope location;
- purpose `T0_CHECKPOINT_ISSUER_ATTESTATION`;
- one synthetic Trust Policy fixture explicitly authorizing that purpose/profile for the exact synthetic signer role, namespace and audience;
- a verifier request explicitly selecting the same profile ID/version;
- a synthetic A1 historical fixture stored separately and never relabeled;
- bootstrap verifier configuration explicitly marking both Path A and Path B `NOT_ENABLED`, with no enrolled bootstrap root or accepted bootstrap sequence; the synthetic checkpoint signer trust material, if needed for a dimension-specific fixture, is test-only and separate from bootstrap-root enrollment;
- state snapshot S0 containing exact trust-root set, policy-head digest, anchor-head sequence/digest, accepted checkpoint-head ID/digest and bootstrap sequence; all are recorded before each test and must remain unchanged after a failed test.

For each test, clone its named baseline (B0 or B-A; A2.2-NV-04 uses B0-PF) to a fresh isolated fixture. B0-PF is defined as a fixed pre-existing profile-check failure: the statement's `signature_profile_id` is `T0-CHECKPOINT-ISSUER-SIGNATURE-PROFILE-LEGACY`, while descriptor, envelope, Trust Policy and verifier request retain the B0 V2 ID/version. The only mutation in NV-04 is enabling automatic fallback. Apply exactly the one mutation listed. Record per-dimension outcomes, one aggregate verdict, one primary reason, S0 and post-state S1, and forbidden transitions. The expected post-state for every failing case is S1 = S0.

### 18.2 Profile and purpose fixtures

| ID | Single mutation from B0 | Per-dimension expected result | Aggregate / primary reason | State and forbidden transitions |
|---|---|---|---|---|
| A2.2-NV-01 | Change only statement purpose to legacy `T0_CHECKPOINT_OWNER_ATTESTATION`; regenerate the derived test signature so the altered statement remains cryptographically valid under the synthetic test signer | Purpose/profile authorization is UNTRUSTED; signature is cryptographically valid but purpose is unsupported | UNTRUSTED / `PURPOSE_NOT_SUPPORTED_BY_PROFILE` | S1=S0; no root enrollment, policy/anchor/checkpoint advancement |
| A2.2-NV-02 | Remove only issuer purpose from the policy allowlist and regenerate the derived policy signature so the changed policy remains cryptographically valid | Policy authorization BLOCKED; policy signature is valid but does not authorize this purpose | BLOCKED / `POLICY_PURPOSE_NOT_EXPLICIT` | S1=S0; no authorization or state advancement |
| A2.2-NV-03 | Select only the A2.2 V2 profile in the verifier request for an unchanged A1 historical object | Historical object/profile binding INVALID | INVALID / `PROFILE_VERSION_MISMATCH` | S1=S0; no historical relabel or A2.2 acceptance |
| A2.2-NV-04 | Baseline B0-PF contains one fixed A2.2 profile-check failure; change only verifier configuration to enable automatic A1 fallback | Profile downgrade BLOCKED | BLOCKED / `PROFILE_DOWNGRADE_FORBIDDEN` | S1=S0; no second-profile attempt or state advancement |
| A2.2-NV-05 | Change only verifier request profile ID to an unknown ID | Profile selection BLOCKED | BLOCKED / `PROFILE_UNKNOWN` | S1=S0; no policy lookup fallback or state advancement |
| A2.2-NV-06 | Change only verifier request profile version to synthetic registry version `3`, which is known but locally disabled in the fixture | Profile selection BLOCKED | BLOCKED / `PROFILE_NOT_ENABLED` | S1=S0; no profile substitution |
| A2.2-NV-07 | Change only envelope profile ID while statement/descriptor/policy/request remain B0 | Envelope/profile binding INVALID | INVALID / `PROFILE_BINDING_MISMATCH` | S1=S0; no signature acceptance |
| A2.2-NV-08 | Change only Trust Policy profile version | Policy/profile binding INVALID | INVALID / `PROFILE_BINDING_MISMATCH` | S1=S0; no policy-head advancement |
| A2.2-NV-09 | Mark only the selected profile retired for new signatures | Profile lifecycle UNTRUSTED | UNTRUSTED / `PROFILE_RETIRED` | S1=S0; historical profile path remains separately selected only |

### 18.3 Bootstrap path and single-binding fixtures

Each fixture starts from B0 and changes only the stated condition. Since neither path is enabled in B0, cases that test a later Path A stage use a separate synthetic sub-baseline B-A: a fully configured, independently pinned Path A fixture under a hypothetical separately approved contract. B-A is a test fixture only and does not enable a real path or select an algorithm/key.

| ID | Baseline | Single mutation | Per-dimension expected result | Aggregate / primary reason | State and forbidden transitions |
|---|---|---|---|---|---|
| A2.2-NV-10 | B0 | Select Path A while its contract/config remains NOT_ENABLED | Path configuration BLOCKED | BLOCKED / `ROOT_BOOTSTRAP_PATH_NOT_ENABLED` | S1=S0; no root enrollment |
| A2.2-NV-11 | B0 | Select Path B while its contract/config remains NOT_ENABLED | Path configuration BLOCKED | BLOCKED / `ROOT_BOOTSTRAP_PATH_NOT_ENABLED` | S1=S0; no ceremony accepted |
| A2.2-NV-12 | B-A | Remove only the required owner authorization object from an otherwise readable source | Evidence presence BLOCKED | BLOCKED / `ROOT_BOOTSTRAP_EVIDENCE_MISSING` | S1=S0; no root/policy/anchor/checkpoint advance |
| A2.2-NV-13 | B-A | Make only the pre-pinned owner authority configuration unavailable | Trust-boundary availability UNKNOWN | UNKNOWN / `ROOT_BOOTSTRAP_TRUST_BOUNDARY_UNAVAILABLE` | S1=S0; no root enrollment |
| A2.2-NV-14 | B-A | Replace only authorization signature with invalid bytes | Authorization signature INVALID | INVALID / `ROOT_BOOTSTRAP_AUTHORIZATION_INVALID` | S1=S0; no root enrollment |
| A2.2-NV-15 | B-A | Change only authorized bootstrap digest | Subject binding INVALID | INVALID / `ROOT_BOOTSTRAP_DIGEST_MISMATCH` | S1=S0; no root enrollment |
| A2.2-NV-16 | B-A | Change only namespace in bootstrap record | Namespace binding INVALID | INVALID / `ROOT_BOOTSTRAP_NAMESPACE_MISMATCH` | S1=S0; no root enrollment |
| A2.2-NV-17 | B-A | Change only audience in bootstrap record | Audience binding INVALID | INVALID / `ROOT_BOOTSTRAP_AUDIENCE_MISMATCH` | S1=S0; no root enrollment |
| A2.2-NV-18 | B-A | Change only root SPKI fingerprint in bootstrap record | Root binding INVALID | INVALID / `ROOT_BOOTSTRAP_ROOT_FINGERPRINT_MISMATCH` | S1=S0; no root enrollment |
| A2.2-NV-19 | B-A | Change only root role in bootstrap record | Role binding INVALID | INVALID / `ROOT_BOOTSTRAP_ROLE_MISMATCH` | S1=S0; no root enrollment |
| A2.2-NV-20 | B-A | Change only profile ID/version in bootstrap record | Profile binding INVALID | INVALID / `ROOT_BOOTSTRAP_PROFILE_MISMATCH` | S1=S0; no root enrollment |
| A2.2-NV-21 | B-A | Change only bootstrap sequence/predecessor | Sequence binding INVALID | INVALID / `ROOT_BOOTSTRAP_SEQUENCE_MISMATCH` | S1=S0; no sequence advance |
| A2.2-NV-22 | B-A | Change only recovery-policy digest | Recovery binding INVALID | INVALID / `ROOT_BOOTSTRAP_RECOVERY_POLICY_MISMATCH` | S1=S0; no root enrollment |
| A2.2-NV-23 | B-A | Change only readable verifier readback bytes while retaining expected digest | Readback integrity INVALID | INVALID / `ROOT_BOOTSTRAP_READBACK_MISMATCH` | S1=S0; no configuration acceptance |
| A2.2-NV-24 | B-A | Make only required verifier readback endpoint unavailable | Readback availability UNKNOWN | UNKNOWN / `ROOT_BOOTSTRAP_READBACK_UNAVAILABLE` | S1=S0; no configuration acceptance |
| A2.2-NV-25 | B-A | Set only the new root as sole bootstrap authorizer | Self-authorization BLOCKED | BLOCKED / `ROOT_BOOTSTRAP_SELF_AUTHORIZATION_FORBIDDEN` | S1=S0; no root enrollment |
| A2.2-NV-26 | B-A | Replace only the independent owner pin with producer-supplied key material | Trust-source BLOCKED | BLOCKED / `ROOT_BOOTSTRAP_PRODUCER_INPUT_UNTRUSTED` | S1=S0; no root enrollment |
| A2.2-NV-27 | B-A | Add only a Path B ceremony fragment to a Path A verification request | Path mixing BLOCKED | BLOCKED / `ROOT_BOOTSTRAP_PATH_MIXING_FORBIDDEN` | S1=S0; no path substitution |

B-A is strictly a synthetic test baseline describing a hypothetical future Path A contract. It does not override §16.1 and MUST NOT be used as evidence that bootstrap is enabled or implemented. The positive Path A fixture and its independent trust root are not to be generated in this documentation-only work.

### 18.4 Required assertions for every fixture

For every A2.2-NV case above, the test harness MUST:
1. record the complete B0, B-A or B0-PF baseline fixture digest and schema version;
2. record exactly one semantic mutation and prove no unrelated fixture field changed; when a signed field is intentionally changed for a policy/purpose test, regenerate the dependent test-only signature and enclosing digest artifacts so the fixture remains internally valid. For a signature-invalidity case, retain the intentionally invalid signature bytes but recompute the enclosing envelope/object digests so the verifier reaches the signature check rather than failing earlier on an outer digest;
3. record per-dimension results for parsing/canonicalization, object binding, profile, purpose, signature, policy authorization, bootstrap authorization and custody/readback as applicable;
4. emit exactly one aggregate verdict and exactly one primary reason code from the row;
5. record state snapshot S0 and S1, proving S1 equals S0 for every failed case;
6. assert no root enrollment, policy-head advancement, anchor-head advancement, checkpoint acceptance, sequence reservation or durable trust-state write occurred;
7. fail the test if an alternative verdict/reason is accepted or if any forbidden transition occurs.

## 19. A2.2 disposition and unchanged approval gates

A2.2 was initially prepared as a documentation-only candidate and is subsequently amended by the owner-approved §20 byte-level clarification. It preserves A2 and A2.1 as historical inputs and does not claim that the bootstrap trust problem is operationally solved. Both Path A and Path B remain disabled; initial bootstrap is deliberately BLOCKED until their respective separate contracts and independent trust evidence exist.

The second self-review of A2.1 is recorded as REQUEST CHANGES. A2.2 has received a fresh adversarial self-review. By the owner decision recorded in `docs/evidence/OWNER_DECISION_WAIVE_INDEPENDENT_REVIEW_A2_2_2026-11-11.md`, qualifying independent review is waived as a mandatory gate for the exact A2.2 candidate and its pinned review dependencies; this waiver does not represent that independent review occurred or establish independent assurance/G3. The owner separately approved only the bounded Stage I synthetic implementation, tied to the exact A2.2 and Stage I approval records. This approval does not authorize production cryptography, keys, signatures, root enrollment, verifier configuration, policy/anchor instances, workflow dispatch, CI secrets, VPS/runtime or canonical T0 operation.

**A2.2 disposition: DRAFT / SELF-REVIEW PASS (see exact-scope evidence) / INDEPENDENT REVIEW WAIVED (NOT PERFORMED) / STAGE I SYNTHETIC IMPLEMENTATION OWNER-APPROVED ONLY / PRODUCTION IMPLEMENTATION NOT APPROVED.**


## 20. Owner-approved byte-level clarification — domain separators and T0-JCS-1 numeric subset (2026-11-11)

**Authority:** explicit owner approval of proposal blob `37bff74053ddc1034e09f40d9cc3bf558588e897`, recorded 2026-11-11. This section is normative for A2.2 and overrides conflicting source-language escape spellings in §§3.3, 13.1, 13.3 and any inherited domain references for the four object-digest functions below. The proposal's approval does not authorize production cryptography or any scope beyond the separately approved Stage I synthetic harness.

### 20.1 Exact domain-separator octets

Each domain is the ASCII bytes shown below followed by exactly one NUL octet `0x00`. The hexadecimal column is normative and takes precedence over source-language escape notation.

| Digest function | Exact domain bytes (hex) |
|---|---|
| Evidence Object | `54302d45564944454e43452d4f424a4543542d563100` |
| Trust Policy body | `54302d54525553542d504f4c4943592d424f44592d563100` |
| Monotonic Anchor object | `54302d4d4f4e4f544f4e49432d414e43484f522d4f424a4543542d563100` |
| Signature Envelope object | `54302d5349474e41545552452d454e56454c4f50452d4f424a4543542d563100` |

Equivalent definition: `ASCII(domain-name) || 0x00`. A literal backslash followed by ASCII `0` is NOT the terminator and MUST NOT be used. Implementations MUST use the exact bytes in the table.

For exact payload bytes `P`, each digest is:

```
SHA256(domain_bytes || U64BE(byte_length(P)) || P)
```

The length is an unsigned 64-bit big-endian count of payload octets. Payload bytes MUST be the exact canonical bytes required by the owning object section; implementations MUST NOT reserialize or normalize a supplied payload inside the digest helper.

### 20.2 Restricted T0-JCS-1 numeric-token grammar

For all structured objects covered by A2.2:

1. JSON input is strict UTF-8 without BOM. Duplicate object keys, invalid UTF-8, unpaired surrogates, non-finite values and noncanonical byte encodings MUST be rejected.
2. JSON number tokens, where a schema explicitly permits a JSON number token, MUST be finite integral decimal tokens whose mathematical value is within the inclusive range `-(2^53-1)` through `+(2^53-1)`.
3. Fractional tokens and exponent notation are forbidden, including forms such as `1.0`, `0.25`, `1e0` and `-2E+3`.
4. Negative zero token `-0` is noncanonical and MUST be rejected by canonical-byte comparison; the only canonical zero number token is `0`.
5. JSON numeric tokens MUST NOT be used for logical U64 values, byte lengths, checkpoint/policy/anchor sequences, timestamps, or schema-version fields that A1 §14.2 requires to use canonical unsigned decimal strings. U64 values MUST be decimal strings matching the canonical unsigned decimal grammar and are range-checked separately against `2^64-1`.
6. A2.2's fixed `signature_profile_version` discriminator remains the exact schema-defined integer value `2`; it is not a free-form sequence or U64 field. No other field may infer permission to use a JSON number merely because its value is small.
7. Financial decimal quantities and any schema-defined decimal quantities MUST use canonical decimal strings, not JSON floating-point numbers.
8. Object member names MUST be ordered by UTF-16 code units. String escaping MUST be deterministic and conform to the restricted profile; valid Unicode scalar values are permitted, while unpaired surrogates are rejected.
9. Canonical wire bytes MUST equal the independently generated canonical UTF-8 serialization byte-for-byte. Whitespace, alternate escapes, alternate number spellings, duplicate keys or noncanonical key order MUST be rejected.
10. A schema requiring fractional or exponent-form numeric semantics MUST use a separately versioned canonicalization profile or a further explicit contract amendment. It MUST NOT silently broaden T0-JCS-1.

This §20.2 clarifies the generic numeric-token subset while preserving the more specific A1 §14.2 rule for logical integer wire fields. Where a schema forbids JSON numeric tokens for a field, that stricter field-level rule controls.

### 20.3 Required Stage I known-answer and negative vectors

The Stage I synthetic harness MUST contain:
- independent SHA-256 known-answer vectors for all four domain byte strings, including the 8-byte U64BE length prefix;
- a cross-domain separation assertion proving the same payload produces four distinct digests;
- exact hex assertions for each domain byte string;
- acceptance vectors at both safe-integer boundaries;
- rejection vectors for positive/negative overflow, fractional and exponent tokens, non-finite values and negative zero;
- preservation tests that logical U64 values remain canonical decimal strings and retain U64 overflow checks;
- byte-for-byte canonicalization tests for duplicate keys, UTF-8/BOM, Unicode validity, UTF-16 key ordering and noncanonical serialization.

The expected digest values MUST be fixed vectors derived independently from the implementation under test. A test MUST NOT compute its only expected value by calling the same production helper it is testing.

### 20.4 Implementation and approval boundary

The owner-approved Stage I implementation scope is limited to the isolated `t0_signature_stage1/` package and its synthetic tests. It does not authorize production signing/verification, production algorithm/library selection, real keys, trust-root enrollment, Path A/B activation, durable policy/anchor state, VPS/SSH/runtime, canonical T0 access, custody publication, workflow dispatch, secrets, deployment or trading changes.

The dedicated GitHub Actions workflow remains manual-only and NOT DISPATCHED. Dispatch requires separate explicit authorization after local Stage I acceptance criteria are met. Independent review remains waived/not performed; G3 is not established.
