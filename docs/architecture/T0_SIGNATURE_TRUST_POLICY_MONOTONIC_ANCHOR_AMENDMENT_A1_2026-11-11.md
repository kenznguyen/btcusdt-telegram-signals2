# T0 Signature / Trust Policy / Monotonic Anchor Contract Amendment A1

Date: 2026-11-11  
Repository: `kenznguyen/btcusdt-telegram-signals2`  
Branch: `feature/t0-centralized-data-feeder-p1-20261101`  
Base contract: `docs/architecture/T0_EVIDENCE_OBJECT_CHECKPOINT_CONTRACT_V1.md`  
Status: **DRAFT A1 — CONTRACT-ONLY — NOT APPROVED FOR IMPLEMENTATION**  
Scope: Resolve the signature, trust bootstrap, replay/rollback and custody-boundary gaps identified by the 2026-11-11 architecture review.

## 1. Authority, precedence and non-goals

This amendment is a normative extension to Checkpoint Contract v1. It does not silently rewrite historical records.

1. Where this amendment explicitly says it **supersedes** or **narrows** a v1 clause, this amendment governs the signature/trust/anchor design only.
2. All v1 requirements not expressly amended remain in force.
3. This document defines data structures, byte encodings, verification order, state transitions and negative-test expectations. It does not authorize implementation, key generation, signing, trust-root installation, anchor publication, TSA use, provider selection, VPS access, T0 database access or destructive operations.
4. The production signature algorithm/profile, root enrollment ceremony, anchor authority identity, key provider and any trusted-time service remain owner/security decisions. No production algorithm or provider is selected here.
5. No live trading or order execution is in scope. T0 remains an independent canonical data asset.

Normative terms MUST, MUST NOT, SHOULD, SHOULD NOT and MAY have their usual contract meaning.

## 2. Security claims and explicit limits

The system MUST keep these claims separate:

- **Content integrity:** exact object bytes match their recomputed digest.
- **Signer authenticity:** a signature verifies under a key authorized by an authenticated Trust Policy for the stated purpose and audience.
- **Policy authenticity:** the Trust Policy is rooted in an owner-approved bootstrap and its signed transition chain is valid.
- **Freshness / anti-replay:** an authenticated anchor identifies the accepted checkpoint head within the limits stated below.
- **Historical trust-at-time:** the signer was authorized at the claimed signing time; this requires trusted time and authenticated key-status/revocation history.
- **Custody / availability:** required copies can be read back from the approved custody locations. This is not implied by a valid signature or anchor.

A signature MUST NOT be interpreted as proof of source truth, data completeness, durable commit, custody, latestness or historical trust-at-time.

### 2.1 Accepted custody boundary and supersession of conflicting v1 language

The owner-accepted custody scope for this workstream is **VPS + GitHub only**. No external backup, third-party WORM service or independent external anchor is assumed.

Accordingly, for signature/anchor design, any v1 wording that makes storage outside both VPS and GitHub an unconditional prerequisite is **superseded by this bounded design scope**. This is not a claim that VPS + GitHub provide independent custody or WORM protection.

Required limits:

1. The current anchor record and its signed predecessor chain SHOULD be retained/readable at both the approved VPS custody location and the GitHub evidence location, using exact-byte copies.
2. A verifier MUST compare the available copies and MUST report a conflict if their anchor sequence, digest or predecessor linkage differs.
3. If either required copy is unavailable, incomplete or cannot be authenticated, freshness/custody MUST be UNKNOWN or BLOCKED according to the failed dimension; the verifier MUST NOT silently accept the remaining copy as proof of latestness.
4. Even if both copies agree, this arrangement cannot prove that both have not been jointly rolled back, deleted or replaced. It therefore supports **cross-copy consistency and retained-chain verification**, not absolute anti-rollback against simultaneous compromise/loss of both custody domains.
5. Any claim requiring an independently protected monotonic anchor outside both VPS and GitHub remains **NOT ESTABLISHED / NOT VERIFIED** until the owner separately approves and qualifies such a mechanism.
6. No WORM, immutable-storage, independent-backup, disaster-recovery or guaranteed-availability claim is made.

This clause reconciles the design with the accepted custody boundary without promoting L4 custody or freshness controls to PASS.

## 3. Canonical byte and digest rules

### 3.1 Canonicalization

All structured objects defined by this amendment MUST use the existing restricted `T0-JCS-1` canonicalization profile unless a later versioned profile explicitly supersedes it.

- Input MUST be strict UTF-8 without BOM.
- Duplicate object keys MUST be rejected before canonicalization.
- Non-finite numbers, unsupported numeric forms, invalid Unicode and noncanonical encodings MUST be rejected.
- The verifier MUST canonicalize independently and MUST compare the resulting bytes to the received canonical bytes where canonical wire bytes are required.
- Unknown critical fields MUST be rejected. Unknown noncritical fields may be accepted only if the relevant schema explicitly permits extension and the fields remain included in the signed canonical bytes.

### 3.2 Evidence Object digest

For the exact canonical Checkpoint Manifest Evidence Object bytes (M):

```
object_digest =
  SHA256(
    UTF8("T0-EVIDENCE-OBJECT-V1\0")
    || U64BE(byte_length(M))
    || M
  )
```

`byte_length` is the number of octets, not Unicode characters. Digest text is lowercase hexadecimal with exactly 64 characters for SHA-256.

The primary signed subject is the exact serialized `T0_CHECKPOINT_MANIFEST` Evidence Object. It is not a mutable database row, API response, Git commit, ZIP archive, display representation or bare `content_root`.

The external descriptor MUST bind this tuple immutably:

`(evidence_object_id, object_type, object_schema_version, canonicalization_profile, digest_algorithm, content_digest, byte_length)`.

An `evidence_object_id` MUST map to exactly one such tuple for its lifetime. Any change to bytes, type, schema, profile, algorithm, digest or length under the same ID is `OBJECT_ID_REUSE` and MUST be rejected. A changed object receives a new ID.

Every separately stored segment or sidecar MUST be bound by exact object ID, media type, schema/profile where applicable, byte length and digest in the manifest/descriptor. A Merkle root over logical rows MUST NOT be treated as a digest of independently transported segment bytes.

## 4. Signature Statement v1

### 4.1 Purpose

A Signature Statement is a canonical, detached statement that binds a signer’s cryptographic act to one exact Evidence Object and its authorization context. The statement is signed; the signature envelope carries the statement and signature bytes.

The statement MUST NOT be embedded in the manifest it signs. The signature envelope MUST NOT be included in the manifest digest. This avoids circular hashing.

### 4.2 Required logical fields

The schema identifier is `T0-SIGNATURE-STATEMENT-V1`. The following fields are mandatory unless explicitly marked optional:

| Field | Rule |
|---|---|
| `statement_type` | Exact constant `T0-SIGNATURE-STATEMENT-V1` |
| `signature_profile_id` | Versioned profile identifier fixed by Trust Policy |
| `signature_algorithm_id` | Exact algorithm identifier; no producer-selected fallback |
| `purpose` | Registered enum; v1 checkpoint purpose is `T0_CHECKPOINT_OWNER_ATTESTATION` |
| `audience` | Exact configured system identifier; v1 target is `BTCUSDT-QUANT-T0` |
| `evidence_object_id` | Exact immutable object ID |
| `object_type` | Exact object type |
| `object_schema_version` | Exact schema version |
| `canonicalization_profile` | Exact profile used for manifest bytes |
| `digest_algorithm` | Exact digest algorithm |
| `content_digest` | Recomputed manifest Evidence Object digest |
| `byte_length` | Exact manifest byte length |
| `checkpoint_id` | Exact checkpoint identity |
| `checkpoint_sequence` | Unsigned, monotonically increasing sequence within the declared checkpoint stream |
| `predecessor_checkpoint_digest` | Previous checkpoint digest or explicit genesis null |
| `signer_key_fingerprint` | SHA-256 fingerprint of the exact DER SubjectPublicKeyInfo bytes |
| `signer_role` | Role identifier authorized by Trust Policy |
| `trust_policy_id` | Exact policy identity |
| `trust_policy_sequence` | Exact policy sequence used for authorization |
| `trust_policy_digest` | Digest of exact canonical policy body bytes |
| `signing_time_observed_ms` | Optional local observation only; MUST be labeled untrusted and MUST NOT establish historical validity |

No field that changes object interpretation, signer authorization, purpose, audience, algorithm or policy context may remain unsigned.

### 4.3 Exact preimage

Let `S` be the canonical T0-JCS-1 bytes of the Signature Statement:

```
statement_bytes = T0_JCS_1(statement)

signature_preimage =
    UTF8("T0-SIGNATURE-STATEMENT-V1\0")
    || U64BE(byte_length(statement_bytes))
    || statement_bytes

signature = Sign(private_key_for_authorized_profile, signature_preimage)
```

The domain separator and length prefix are mandatory. The signature implementation MUST use exactly the algorithm/profile authorized by the authenticated Trust Policy. This amendment does not select that production algorithm.

The verifier MUST reconstruct the preimage from the received canonical statement and verify the signature over those exact bytes. It MUST NOT trust a producer-supplied preimage digest or a separately supplied “signed bytes” field.

### 4.4 Detached envelope

The detached envelope schema is `T0-SIGNATURE-ENVELOPE-V1` and contains:

- envelope schema/type;
- the exact canonical statement bytes (or a lossless representation whose canonical bytes are unambiguous);
- signature algorithm/profile identifiers repeated for transport convenience, which MUST exactly match the signed statement and policy;
- signature bytes;
- optional transport metadata explicitly classified as unsigned/non-authoritative.

The verifier MUST reject any mismatch between duplicated envelope fields and signed statement fields. Envelope ID/digest is computed only after the signature exists and MUST NOT be included in its own signed statement. Transport/display metadata MUST NOT affect authorization.

## 5. Trust Policy v1

### 5.1 Policy object and chain

The policy body schema is `T0-TRUST-POLICY-V1`. It MUST include:

- `policy_id`, schema version and policy sequence;
- predecessor policy digest, or explicit genesis marker;
- digest algorithm and digest of the exact canonical policy body;
- root/rotation authority fingerprint and role reference;
- allowed signature profile and algorithm identifiers;
- signer key entries;
- minimum verifier version and critical-feature requirements;
- policy effective/retirement metadata, with timestamps marked trusted or untrusted as appropriate.

The policy digest is computed over the exact canonical policy body using a domain-separated, length-prefixed digest profile defined for the policy object. The policy signature MUST be detached and MUST bind the policy ID, sequence, predecessor digest, exact policy digest/length, audience, signer fingerprint/role and signature profile. The policy body MUST NOT contain its own signature.

### 5.2 Root bootstrap

An offline verifier MUST begin with an owner-approved, pre-pinned root public-key fingerprint or an equivalent authenticated bootstrap record provisioned independently of the checkpoint producer.

- A root fingerprint or policy file supplied only by the checkpoint producer is untrusted.
- The verifier MUST NOT auto-fetch, auto-enroll or trust a replacement root because the current root is missing or verification fails.
- The bootstrap record MUST identify the root fingerprint, accepted key encoding, root role, policy namespace/audience, bootstrap version and the owner authorization evidence reference.
- Root replacement MUST be an explicit, authenticated transition authorized by the currently trusted root or by a separately owner-approved recovery ceremony. If the prior root is unavailable/compromised and no authenticated recovery path exists, verification is BLOCKED.
- The storage/distribution location and owner ceremony for this pinned bootstrap remain an owner decision. VPS + GitHub copies alone do not create an external trust root or prove resistance to joint rollback.

### 5.3 Signer entries and authorization

Each signer entry MUST be keyed by the SHA-256 fingerprint of the exact DER SubjectPublicKeyInfo bytes. The fingerprint procedure and accepted key encoding MUST be fixed by the selected profile; display names, email addresses and mutable key IDs are not identity.

Each entry MUST define:

- key fingerprint and key type;
- role;
- permitted object types, purposes and audiences;
- permitted signature profiles/algorithms;
- status and validity metadata;
- activation and retirement policy;
- revocation/compromise event references and effective-time semantics.

A key is authorized only when all of the following match: authenticated policy chain, exact fingerprint, active status, role, object type, purpose, audience, profile/algorithm and policy version. Possession of a public key in an envelope does not establish trust.

### 5.4 Key status and historical validity

Recognized statuses are `ACTIVE`, `REVOKED`, `COMPROMISED`, `EXPIRED`, `RETIRED` and `UNKNOWN`.

- Missing or conflicting status evidence MUST produce UNKNOWN/BLOCKED, not ACTIVE by default.
- A currently revoked/compromised key MUST NOT be used for new signatures.
- Whether a signature made before a revocation remains historically valid depends on trusted signing-time evidence and authenticated revocation chronology.
- Local wall-clock time, file timestamps, Git commit timestamps and unsigned envelope timestamps MUST NOT establish historical trust-at-time.
- If trusted time and authenticated key-status history are unavailable, historical validity MUST be UNKNOWN even if the mathematical signature verifies.
- Revocation MUST specify event ID, affected fingerprint, reason class, effective time if trusted, and retroactive-compromise semantics. An absent/ambiguous effective time cannot be inferred.

### 5.5 Policy transitions and downgrade protection

A policy transition MUST advance the policy sequence and bind the exact predecessor policy digest. It MUST be authorized by the currently trusted root or an explicitly authorized rotation authority.

- Lower sequence than the verifier’s accepted policy state is `POLICY_ROLLBACK`.
- Same sequence with a different digest is `POLICY_EQUIVOCATION`.
- Same sequence and exact same digest is an idempotent read only.
- Unknown, disabled, retired or weaker profiles MUST be rejected; there is no fallback or downgrade negotiation.
- The envelope cannot override policy algorithm/profile requirements.
- If verifier version is below the policy minimum or lacks a mandatory critical feature, verification is BLOCKED.

## 6. Monotonic Anchor v1

### 6.1 Purpose and separation

The Monotonic Anchor is a separately signed latest-head record. It is not part of the checkpoint manifest or its signature envelope. It establishes the accepted head only within the authenticated anchor history and custody limitations.

The anchor signer/authority MUST be distinct from the checkpoint signer and T0 writer. Anchor administration MUST NOT be granted through Feeder ingestion credentials.

### 6.2 Required fields

Schema: `T0-MONOTONIC-ANCHOR-V1`.

| Field | Rule |
|---|---|
| `anchor_type` | Exact constant `T0-MONOTONIC-ANCHOR-V1` |
| `anchor_stream_id` | Stable identifier for the checkpoint stream/audience |
| `audience` | Exact system identifier |
| `anchor_sequence` | Unsigned strictly increasing sequence |
| `checkpoint_id` | Exact checkpoint identity |
| `evidence_object_id` | Exact checkpoint manifest object ID |
| `checkpoint_digest` | Exact Evidence Object digest |
| `checkpoint_sequence` | Exact checkpoint sequence |
| `predecessor_anchor_digest` | Previous anchor digest or explicit genesis null |
| `predecessor_checkpoint_digest` | Previous checkpoint digest or explicit genesis null |
| `trust_policy_id` | Exact policy identity |
| `trust_policy_sequence` | Exact accepted policy sequence |
| `trust_policy_digest` | Exact canonical policy digest |
| `anchor_signer_fingerprint` | Exact DER-SPKI SHA-256 fingerprint |
| `anchor_signer_role` | Dedicated anchor role |
| `anchor_profile_id` / `anchor_algorithm_id` | Fixed by Trust Policy |
| `observed_at_ms` | Optional local observation only; not trusted time |

The anchor signature MUST bind every field above using a separate domain separator and canonical preimage:

```
anchor_statement_bytes = T0_JCS_1(anchor_statement)

anchor_preimage =
    UTF8("T0-MONOTONIC-ANCHOR-V1\0")
    || U64BE(byte_length(anchor_statement_bytes))
    || anchor_statement_bytes

anchor_signature = Sign(anchor_private_key, anchor_preimage)
```

The exact anchor object digest is computed after the signed object exists and MUST NOT be self-referential.

### 6.3 Sequence and transition rules

1. The genesis anchor has sequence 0 and an explicit genesis marker; it MUST be owner-authorized under the trusted bootstrap.
2. Every accepted successor has sequence exactly predecessor sequence + 1, and its predecessor anchor digest MUST equal the exact digest of the previously accepted anchor.
3. The checkpoint sequence and predecessor checkpoint digest MUST agree with the checkpoint stream history bound by the anchor.
4. Anchor advancement MUST be serialized by one authorized anchor authority. Concurrent writers MUST use an atomic compare-and-advance operation or an equivalent single-writer mechanism; a read-then-write race is forbidden.
5. Exact duplicate publication of the same anchor bytes/digest is idempotent and MUST NOT advance the sequence.
6. Same anchor sequence with a different digest is `ANCHOR_EQUIVOCATION` and MUST fail closed.
7. A lower sequence, broken predecessor link, skipped sequence, mismatched checkpoint digest or unexpected stream/audience is `ANCHOR_ROLLBACK_OR_SUBSTITUTION` and MUST fail closed.
8. A validly signed checkpoint whose digest is not the accepted current head is `STALE_REPLAY`; signature validity does not make it current.
9. Historical anchors MUST NOT be overwritten. A new head appends a new anchor record; corrections require a new sequence and explicit reason/reference.

### 6.4 VPS + GitHub publication and freshness verdict

Within the accepted custody boundary, the exact signed anchor bytes and predecessor records SHOULD be published to both the approved VPS custody location and GitHub evidence location. A verifier MUST:

- authenticate the anchor signature and policy authorization;
- validate the entire available predecessor chain to the pinned genesis/accepted checkpoint;
- compare exact anchor sequence and digest across both locations;
- reject conflicting copies;
- report UNKNOWN/BLOCKED if a required copy or required chain segment is missing or inaccessible.

If both locations agree, the result may be reported as `CONSISTENT_WITH_RETAINED_ANCHOR_HEAD`, not as proof against joint rollback. The verifier MUST NOT claim globally latest or absolute anti-rollback solely from agreement between VPS and GitHub. If both stores have been jointly rolled back to the same older chain, this design has no external fact with which to detect it.

A stronger global monotonicity claim requires a separately owner-approved external anchor or other independently protected monotonic authority. That is explicitly outside this amendment and remains NOT ESTABLISHED.

## 7. Verification pipeline and aggregate outcomes

The verifier MUST execute checks in deterministic order:

1. Parse strict bytes; reject invalid UTF-8, BOM, duplicate keys, unsupported schema, invalid canonical form and unknown critical fields.
2. Recompute exact manifest byte length and Evidence Object digest from received bytes.
3. Enforce object-ID uniqueness and exact type/schema/profile/digest/length binding.
4. Recompute semantic, row, partition, Merkle and completeness claims from preserved inputs under the base contract.
5. Parse and canonicalize the Signature Statement; validate every required field against the exact object descriptor and checkpoint.
6. Resolve the signer only from the authenticated Trust Policy chain rooted in the pinned bootstrap.
7. Enforce signer role, object type, purpose, audience, algorithm/profile, policy sequence and verifier minimum version.
8. Reconstruct the exact domain-separated preimage and verify signature bytes.
9. Evaluate key status and historical trust-time separately. Do not infer trusted time from local observations.
10. Verify anchor signature, role, policy, sequence, predecessor chain and current-head equality.
11. Compare the required VPS/GitHub anchor copies and state the custody/freshness limitation.
12. Emit a new immutable Verification Record with per-dimension outcomes, reason codes, verifier version and exact input digests. Earlier verification records MUST NOT be overwritten.

Per-dimension verdicts MUST remain distinct. Aggregate outcomes:

- `PASS`: all mandatory checks for the explicitly stated, bounded claim pass. This does not imply a stronger claim than the evidence supports.
- `INVALID`: malformed/noncanonical bytes, digest mismatch, signature mismatch, forbidden field binding or object-ID reuse.
- `UNTRUSTED`: unknown/unauthorized signer, role, policy, purpose, audience or algorithm/profile.
- `STALE_REPLAY`: valid old object/signature is not the accepted current head.
- `BLOCKED`: required trust, policy, anchor, custody or verifier material is missing, inaccessible or contradictory.
- `UNKNOWN`: a required fact cannot be established, including historical trust-at-time or global latestness beyond the approved custody boundary.

The verifier MUST NOT collapse these into a Boolean, apply best-effort acceptance, fetch a replacement root, downgrade algorithms, trust producer assertions or use network fallback during offline verification.

## 8. Minimum negative-verification test contract

All cases are synthetic-only. Disposable ephemeral keys may be generated only after separate implementation/test approval. No production keys, canonical T0 data, VPS, network, provider or live runtime may be used.

| ID | Attack / defect | Expected result |
|---|---|---|
| NV-01 | Flip one bit in signature bytes | INVALID |
| NV-02 | Verify using a different public key | INVALID or UNTRUSTED |
| NV-03 | Mutate one manifest byte while retaining original digest/signature | INVALID |
| NV-04 | Alter signed byte length or digest | INVALID |
| NV-05 | Substitute digest from another valid checkpoint | INVALID |
| NV-06 | Reuse object ID with changed digest/type/schema/length | INVALID — OBJECT_ID_REUSE |
| NV-07 | Change object type, schema or canonicalization profile | INVALID |
| NV-08 | Reuse valid signature for a different purpose | INVALID |
| NV-09 | Reuse valid signature for a different audience | INVALID |
| NV-10 | Alter signer fingerprint, role, policy digest or algorithm after signing | INVALID |
| NV-11 | Unknown, disabled, retired or downgraded algorithm/profile | UNTRUSTED / BLOCKED |
| NV-12 | Unknown key, wrong role or unauthorized object/purpose | UNTRUSTED |
| NV-13 | Missing/invalid policy signature or unpinned root | BLOCKED / UNKNOWN |
| NV-14 | Lower policy sequence or same-sequence different policy digest | BLOCKED — POLICY_ROLLBACK / EQUIVOCATION |
| NV-15 | Revoked/compromised/expired key | UNTRUSTED; historical status UNKNOWN without trusted chronology |
| NV-16 | Valid old checkpoint after anchor head advanced | STALE_REPLAY |
| NV-17 | Same anchor sequence with different digest | BLOCKED — ANCHOR_EQUIVOCATION |
| NV-18 | Invalid anchor signature, wrong anchor role or predecessor mismatch | INVALID / BLOCKED |
| NV-19 | Missing, stale, conflicting or inaccessible anchor copy | UNKNOWN / BLOCKED |
| NV-20 | Backdate local clock to evade revocation | UNKNOWN; local clock cannot establish historical validity |
| NV-21 | Alter trust-policy snapshot or pinned verifier root | INVALID / BLOCKED |
| NV-22 | Duplicate keys, noncanonical statement bytes or unknown critical field | INVALID |
| NV-23 | Valid signature over incomplete/UNKNOWN/INVALID checkpoint data | Signature dimension may pass; aggregate checkpoint claim BLOCKED/INVALID |
| NV-24 | Offline verifier lacks root, policy, revocation or anchor evidence | BLOCKED / UNKNOWN; no network fallback |
| NV-25 | Exact duplicate object/anchor read with same digest and sequence | Idempotent read; no sequence advancement |
| NV-26 | Attempt to overwrite earlier Verification Record | INVALID — append-only history violation |
| NV-27 | VPS and GitHub anchor copies disagree | BLOCKED — CUSTODY_CONFLICT |
| NV-28 | Both VPS and GitHub copies are consistently rolled back to an older valid chain | NOT DETECTABLE by this boundary; global freshness MUST remain NOT ESTABLISHED |
| NV-29 | Concurrent anchor writers race to publish the same next sequence | Exactly one serialized transition; conflict is BLOCKED, never last-write-wins |
| NV-30 | Valid signature uses key not authorized for the declared audience or stream | UNTRUSTED |

Tests MUST assert the per-dimension result, aggregate result and stable reason code. Positive tests MUST prove exact byte vectors using an independently implemented oracle, not the same helper used by the producer.

## 9. Role separation

The following authorities remain distinct:

1. T0 writer/Feeder — canonical candle write under existing lease/fencing only.
2. Checkpoint builder/issuer — read-only snapshot construction; no signing, anchor administration or custody rewrite.
3. Checkpoint signer — signs only authorized statements; no T0 write or anchor administration.
4. Trust-policy root/rotation authority — approves policy transitions and key authorization.
5. Anchor authority — advances the monotonic anchor; distinct from checkpoint signer and T0 writer.
6. Custodian — retains exact bytes and supports readback; cannot alter signed objects.
7. Verifier — independently verifies and emits append-only records; cannot alter inputs.
8. Independent reviewer — reviews frozen contract/source/evidence and cannot be the sole author/operator of the reviewed control.

No ingestion credential may confer signing or anchor authority. Private keys MUST NOT be committed to Git, Actions artifacts, T0, fixtures or logs.

## 10. Test architecture and acceptance gates

Before implementation approval, freeze this amendment and its test matrix and obtain a qualifying independent review of the exact frozen commit.

After a separate implementation approval, the planned synthetic-only gates are:

- deterministic T0-JCS-1, object digest, statement preimage and anchor preimage byte vectors;
- crypto positive/negative tests with ephemeral process-local keys;
- Trust Policy bootstrap, transition, rotation, revocation, compromise, expiry, role and downgrade tests;
- stateful anchor advancement, idempotency, replay, rollback, equivocation and concurrency tests;
- offline integration tests with network disabled and only frozen inputs;
- independent second implementation/vector comparison;
- exact-SHA GitHub Actions results and artifact digests.

A suite that uses the same producer helper to create and verify its expected preimage is insufficient. No test may weaken assertions to obtain green results.

## 11. Owner decisions still required before implementation

The following remain deliberately unresolved and MUST be decided explicitly by the owner/security review:

1. Production signature algorithm and exact profile/version.
2. Root bootstrap ceremony, pinned-root custody and recovery/rotation authority.
3. Dedicated checkpoint signer and anchor signer identities/roles.
4. Anchor authority implementation and serialization/concurrency mechanism.
5. Whether the owner accepts the bounded VPS + GitHub limitation as sufficient for the intended claim, or wants to authorize an external monotonic anchor later.
6. Whether any trusted-time/TSA evidence is required for the intended historical trust-at-time claim.
7. Exact policy/anchor object retention and recovery requirements, without inferring deletion or TTL authority.

No answer is inferred from prior provider discussions. Absence of a decision means implementation remains BLOCKED.

## 12. Disposition and unchanged boundaries

- Signature Statement exact preimage: **SPECIFIED AT DRAFT CONTRACT LEVEL**.
- Trust Policy and root bootstrap: **SPECIFIED AT DRAFT CONTRACT LEVEL; owner bootstrap ceremony unresolved**.
- Monotonic Anchor transition/replay protocol: **SPECIFIED AT DRAFT CONTRACT LEVEL; absolute anti-rollback not achievable under VPS + GitHub-only custody**.
- Custody conflict S-04: **RECONCILED AS A BOUNDED CLAIM; external independent custody/global freshness remains NOT ESTABLISHED**.
- Algorithm/profile and anchor authority: **OWNER DECISION REQUIRED**.
- Negative-verification tests: **CONTRACT MATRIX DRAFTED; NOT IMPLEMENTED / NOT RUN**.
- Independent review: **NOT PERFORMED FOR THIS AMENDMENT**.
- Implementation: **BLOCKED — separate approval required after frozen-contract independent review**.

No code, test, workflow, CI configuration, key, trust root, policy instance, anchor record, TSA/provider, VPS runtime, Feeder/API, SQLite database, canonical data, retention policy or destructive operation is changed or exercised by this amendment. No key was generated; no signature was produced; no anchor was published. Paper-only posture and `AI_EXECUTION_ENABLED=false` remain unchanged.
