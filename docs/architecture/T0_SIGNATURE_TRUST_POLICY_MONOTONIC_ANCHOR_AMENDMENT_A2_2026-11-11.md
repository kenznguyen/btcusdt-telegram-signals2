# T0 Signature / Trust Policy / Monotonic Anchor — Contract Correction A2

Date: 2026-11-11  
Repository: `kenznguyen/btcusdt-telegram-signals2`  
Branch: `feature/t0-centralized-data-feeder-p1-20261101`  
Base: Checkpoint Contract v1, as formally amended by its owner-approved bounded VPS + GitHub custody addendum  
Corrects: A1 `docs/architecture/T0_SIGNATURE_TRUST_POLICY_MONOTONIC_ANCHOR_AMENDMENT_A1_2026-11-11.md`  
Status: **DRAFT A2 — DOCUMENTATION ONLY — NOT APPROVED FOR IMPLEMENTATION**

## 1. Authority, precedence and preservation

1. A2 is a contract-correction candidate responding to self-review findings SR-01 through SR-08 in `T0_SIGNATURE_CONTRACT_SELF_REVIEW_2026-11-11.md`.
2. A1 remains preserved unchanged as historical design evidence. A2 supersedes A1 only where A2 explicitly replaces or supplements a rule below. All other A1 and Checkpoint Contract v1 requirements remain in force.
3. The reviewed A1 snapshot and its source blobs are immutable review inputs. A2 is a new candidate; it does not retroactively change the frozen A1 snapshot or its review result.
4. This document defines contract semantics and test expectations only. It does not authorize code, schema migration, keys, signatures, trust-root installation, policy or anchor instances, provider/TSA use, VPS/SSH/runtime access, T0 database access, custody mutation or destructive operations.
5. A2 does not satisfy independent review. It requires a new review against its own exact frozen commit and separate implementation authorization.
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

A2 does not define or authorize an owner key, delegation ceremony or owner-approval product. Until such a separate contract and bootstrap exist, the only permitted claim is issuer attestation.

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

The implementation MUST identify one durable state authority and prove that its compare-and-advance operation is atomic across process restart. The journal and state authority are implementation choices still requiring a separate design/approval; this A2 does not select a database, filesystem, provider or runtime.

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

The selected signature profile MUST additionally define accepted public-key encoding and signature-byte format. A2 does not select the production signature algorithm.

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
- **Implementation-approved:** a separate explicit owner authorization after qualifying independent review, with exact scope and source snapshot.

A2 is a **DRAFT CONTRACT / BYTE-FROZEN ONLY WHEN A SPECIFIC REVIEW SNAPSHOT IS DECLARED**. It is not implementation-approved. The prior A1 snapshot remains byte-frozen as historical review input. A same-session self-review MUST NOT be called independent review, external review or G3.

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
1. Freeze A2 exact source commit/blob set.
2. Perform a fresh adversarial self-review of that frozen A2 candidate.
3. Obtain a qualifying independent review of the exact A2 blobs, including the revised field schema, state machine, byte vectors and test matrix.
4. Resolve all blocking findings and owner/security decisions.
5. Obtain a separate explicit owner implementation approval for a narrowly scoped synthetic-only implementation plan.
6. Implement only after approval, with TDD, independent vector oracle, offline tests, exact-SHA CI evidence and rollback plan.
7. Any VPS, provider, TSA, key custody, production trust-root or canonical T0 integration requires separate explicit approval.

No code, test, workflow, CI configuration, key, signature, trust root, policy instance, anchor instance, provider/TSA, VPS/SSH/runtime, SQLite database, canonical T0 data, retention policy or destructive operation is changed or exercised by this contract draft. Paper-only posture and `AI_EXECUTION_ENABLED=false` remain unchanged.

**A2 disposition: DRAFT CORRECTION CANDIDATE — SR-01 THROUGH SR-08 ADDRESSED AT CONTRACT-DESIGN LEVEL — NOT INDEPENDENTLY REVIEWED — NOT IMPLEMENTATION-APPROVED.**
