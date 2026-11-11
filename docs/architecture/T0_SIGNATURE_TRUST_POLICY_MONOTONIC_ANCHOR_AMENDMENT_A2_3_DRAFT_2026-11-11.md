# T0 Signature / Trust Policy / Monotonic Anchor — Contract Amendment A2.3 (Draft)

**Date:** 2026-11-11  
**Branch:** `feature/t0-centralized-data-feeder-p1-20261101`  
**Status:** **DRAFT / B + E2 OWNER-APPROVED ARCHITECTURE / NORMATIVE TEXT PROPOSED / NOT BYTE-FROZEN / NOT IMPLEMENTATION-AUTHORIZED**  
**Supersedes:** A2.2 §§3.1, 3.2, 3.3, 15 (only where explicitly stated), and the A2.2-NV-31..34 mappings below. All other A1/A2.2 requirements remain in force unless explicitly amended here.

## 1. Authority, purpose and precedence

1. This is a bounded successor proposal to resolve the two known conflicts between the owner-approved B + E2 architecture and A2.2.
2. The owner approved B + E2 as the target architecture and approved continued Stage II work. That does not make this draft frozen or authorize production key/trust/runtime operations.
3. A1 remains historical and normative except where A2.2/A2.3 explicitly supersede it. A2.3, once separately approved and frozen, supersedes A2.2 only for the exact clauses listed above.
4. This amendment does not enable root bootstrap. A2.2 §§16–17 remain in force: Path A and Path B are NOT_ENABLED, and initial bootstrap is BLOCKED.
5. This amendment does not claim owner intent, owner approval, exchange truth, data correctness, checkpoint completeness, custody or global latestness.
6. Normative terms MUST, MUST NOT, SHOULD, SHOULD NOT and MAY have their usual contract meaning.

## 2. Chosen architecture and object graph

The selected architecture is:
- **B:** a separately signed Authorization Evidence Object (AEO) carries the signing provenance and authority/custody evidence for the main checkpoint signature. The main Signature Statement binds the exact AEO package through a descriptor.
- **E2:** the completed signature envelope is identified by a detached descriptor created only after the complete envelope bytes exist. The descriptor ID is independent of both envelope bytes and descriptor serialization.

The required dependency graph is:

```
AEO body (exact canonical bytes)
  └─ AEO Signature Statement + independent issuer signature
       └─ AEO signature envelope
            └─ detached AEO package descriptor
                 └─ bound by main checkpoint Signature Statement

Main checkpoint Signature Statement + Ed25519 signature
  └─ completed main signature envelope
       └─ detached main envelope descriptor
            └─ append-only Verification Records reference exact descriptor + digest
```

A descriptor or ID is not itself proof of authority. All object bytes, digests, lengths, signatures, profiles, policy bindings and scope must be verified.

## 3. AEO body schema — normative proposal

### 3.1 Identity and canonicalization

- `object_type`: exact string `T0-AUTHORIZATION-EVIDENCE-V1`.
- `authorization_evidence_id`: immutable opaque identifier in the AEO namespace.
- `schema_version`: exact integer discriminator `1`.
- `canonicalization_profile`: exact identifier `T0-JCS-1`.
- AEO body bytes are the exact canonical T0-JCS-1 UTF-8 serialization.
- The body MUST NOT contain its own content digest, signature, signature envelope digest, or detached package descriptor. Its body digest MUST use the A2.2 §20.1 Evidence Object domain bytes, U64BE exact canonical body byte length, and exact canonical body bytes.
- Logical IDs and U64 values follow A1 §14.2 and A2.2 §20.2. Schema-version discriminators are fixed schema-defined integer tokens only where explicitly stated.

### 3.2 Required fields

| Field | Type | Requirement |
|---|---|---|
| `authorization_evidence_id` | string | Unique immutable ID in the AEO namespace |
| `object_type` | string | Exact `T0-AUTHORIZATION-EVIDENCE-V1` |
| `schema_version` | integer | Exact `1` |
| `canonicalization_profile` | string | Exact `T0-JCS-1` |
| `authorization_purpose` | enum | Exact `T0_CHECKPOINT_SIGNING_PROVENANCE` |
| `audience` | string | Exact verifier namespace |
| `subject_signer_spki_fingerprint` | lowercase hex string | SHA-256 over exact DER SPKI bytes used by the main checkpoint signature |
| `subject_signer_role` | string | Exact role asserted for the main checkpoint signer |
| `subject_signature_profile_id` | string | Exact profile ID used by the main checkpoint Signature Statement |
| `subject_signature_profile_version` | integer | Exact profile version |
| `signing_software` | object | Stable software ID, exact version, build digest algorithm and build digest |
| `signing_request` | object | Immutable request ID and exact request evidence descriptor |
| `signing_decision` | object | Immutable decision ID, exact decision evidence descriptor and affirmative outcome |
| `signer_authority_evidence` | non-empty array | Exact authority/delegation evidence descriptors and explicit scope |
| `signer_custody_evidence` | array or policy-approved NOT_APPLICABLE | Exact custody evidence descriptors; empty only where Trust Policy explicitly permits and gives a reason |
| `scope` | object | Exact action, audience, object type, checkpoint stream and constraints |
| `issued_for_checkpoint_id` | string | Exact checkpoint ID for which the AEO is issued |
| `issued_for_checkpoint_sequence` | canonical U64 decimal string | Exact checkpoint sequence |
| `issuer_id` | string | Identity reference of the AEO issuer |
| `issuer_policy_id` | string | Exact Trust Policy identity authorizing the AEO issuer |
| `issuer_policy_sequence` | canonical U64 decimal string | Exact policy sequence |
| `issuer_policy_digest` | lowercase hex string | Digest of exact canonical Trust Policy body |
| `issued_at_observed_ms` | canonical U64 decimal string or null | Untrusted local observation only; no historical validity inference |
| `extensions` | object | Empty in v1; future extensions require registered schema/profile |

The nested `signing_software` object contains `software_id`, `software_version`, `build_digest_algorithm`, and `build_digest`. Floating aliases such as `latest` are forbidden.

The nested request/decision descriptors MUST bind object ID, type, schema version, canonicalization profile, digest algorithm, exact digest and byte length. The decision outcome MUST be exactly `APPROVED_FOR_THIS_SIGNATURE`; any other value cannot authorize the signature.

The `scope` object MUST include exact `actions`, `audience`, `object_types`, `checkpoint_stream_ids`, and a versioned `constraints` object. Wildcards are forbidden in v1.

### 3.3 Non-self-authentication and issuer independence

1. The AEO subject signer is the key used for the main checkpoint signature. The AEO issuer is the principal/key that independently attests the subject's software/build, request/decision and authority/custody evidence.
2. The AEO issuer MUST be authorized by the Trust Policy under role `AUTHORIZATION_EVIDENCE_ISSUER` for the exact audience, purpose, checkpoint stream and object type.
3. The AEO issuer principal and SPKI fingerprint MUST be distinct from the subject checkpoint signer principal and SPKI fingerprint. Equality MUST fail with `AUTHORIZATION_EVIDENCE_SELF_ISSUED`.
4. The AEO issuer MUST NOT establish its own authority by assertions inside the AEO. Its role and key authorization come only from the already accepted Trust Policy chain.
5. AEO issuer authorization is not owner authorization and MUST NOT be represented as owner approval. A2.2 §2.2 remains unchanged.
6. AEO signature verification does not recursively require another AEO. The narrowly scoped exception is that the AEO issuer's own Signature Statement is authorized directly by the accepted Trust Policy role `AUTHORIZATION_EVIDENCE_ISSUER`; it MUST NOT be used as a checkpoint issuer statement. This exception MUST be explicit in the verifier's statement-purpose dispatch.

## 4. AEO signature and package binding

### 4.1 AEO-specific signature statement and domain

The AEO issuer signs a separate canonical `T0-AUTHORIZATION-EVIDENCE-SIGNATURE-STATEMENT-V1`. A1 §4.3 remains unchanged for the main checkpoint Signature Statement. The AEO-specific statement is required because the AEO is not a checkpoint and must not fabricate checkpoint ID, sequence or predecessor fields.

The exact AEO statement domain is ASCII `T0-AUTHORIZATION-EVIDENCE-SIGNATURE-STATEMENT-V1` followed by exactly one NUL octet. Normative domain hex:

```
54302d415554484f52495a4154494f4e2d45564944454e43452d5349474e41545552452d53544154454d454e542d563100
```

The exact preimage is:

```
ASCII("T0-AUTHORIZATION-EVIDENCE-SIGNATURE-STATEMENT-V1")
|| 0x00
|| U64BE(byte_length(canonical_AEO_signature_statement_bytes))
|| canonical_AEO_signature_statement_bytes
```

The AEO Signature Statement MUST bind: exact statement type/schema; profile ID/version; Ed25519 algorithm ID; purpose `T0_AUTHORIZATION_EVIDENCE_ISSUER_ATTESTATION`; audience; AEO body object ID/type/schema/canonicalization/digest algorithm/digest/byte length; issuer SPKI fingerprint and role `AUTHORIZATION_EVIDENCE_ISSUER`; Trust Policy ID/sequence/digest. All logical U64 fields remain canonical decimal strings under A1 §14.2/A2.2 §20.2.

The AEO statement MUST NOT contain checkpoint-specific fields or claim checkpoint attestation. The purpose, role, audience, profile and exact AEO subject descriptor are inside the signed canonical statement. The distinct domain prevents cross-protocol substitution with the A1 checkpoint statement. The domain is a proposed normative addition and requires independent review and exact known-answer vectors before freeze.

The AEO Signature Statement has exactly these required logical fields (the final canonical JSON schema and enum registry are part of the freeze gate):

| Field | Requirement |
|---|---|
| `statement_type` | Exact `T0-AUTHORIZATION-EVIDENCE-SIGNATURE-STATEMENT-V1` |
| `signature_profile_id` / `signature_profile_version` | Exact AEO issuer profile ID and version from §5.1 |
| `signature_algorithm_id` | Exact `Ed25519` |
| `purpose` | Exact `T0_AUTHORIZATION_EVIDENCE_ISSUER_ATTESTATION` |
| `audience` | Exact relying verifier namespace |
| `subject_object_descriptor` | Exact AEO body descriptor from §4.3 |
| `signer_key_fingerprint` | SHA-256 of exact DER SPKI octets |
| `signer_role` | Exact `AUTHORIZATION_EVIDENCE_ISSUER` |
| `trust_policy_id` / `trust_policy_sequence` / `trust_policy_digest` | Exact accepted policy snapshot authorizing this AEO issuer |
| `signing_time_observed_ms` | Optional local observation only; MUST NOT establish historical validity |

The AEO body descriptor is:

| Field | Requirement |
|---|---|
| `object_id` | Exact AEO `authorization_evidence_id` |
| `object_type` | Exact `T0-AUTHORIZATION-EVIDENCE-V1` |
| `schema_version` | Exact integer `1` |
| `canonicalization_profile` | Exact `T0-JCS-1` |
| `digest_algorithm` | Exact `SHA-256` |
| `content_digest` | SHA-256 using A2.2 §20.1 Evidence Object domain, U64BE length and exact canonical AEO body bytes |
| `byte_length` | Exact canonical AEO body byte length as canonical U64 decimal string |
| `purpose` | Exact `T0_CHECKPOINT_SIGNING_PROVENANCE` |
| `audience` | Exact verifier namespace |

The AEO package descriptor embedded in the main checkpoint Signature Statement contains exactly two nested descriptors: the AEO body descriptor above and the detached descriptor of the AEO signature envelope. Both nested descriptors MUST be checked independently and MUST refer to the same AEO object ID, purpose and audience.


### 4.4 AEO domain known-answer vector (contract test vector)

For the exact AEO statement domain and payload below:
- domain hex: `54302d415554484f52495a4154494f4e2d45564944454e43452d5349474e41545552452d53544154454d454e542d563100`;
- domain byte length: `49`;
- payload ASCII: `A2.3-AEO-domain-KAT-v1`;
- payload byte length: `22`;
- U64BE length: `0000000000000016`;
- expected SHA-256 of domain || U64BE(length) || payload: `64172accdaf1f2add08b201b25c8ea26b52e2c90e68674126bbef465f4e7acde`.

This fixed byte/digest vector was independently calculated from the literal domain bytes, payload bytes and standard SHA-256 construction. It is a primitive known-answer vector only; it does not replace an independent implementation/vector conformance review or a valid Ed25519 signature test.

### 4.2 Signature profile

- AEO issuer profile ID: `T0-AUTHORIZATION-EVIDENCE-ISSUER-SIGNATURE-PROFILE-V1`.
- Profile version: exact integer `1`.
- Algorithm: Ed25519 PureEdDSA only.
- Public key: strict DER SubjectPublicKeyInfo containing Ed25519 with absent parameters and 32-byte public key.
- Signature: exactly 64 raw octets.
- Library candidate: PyCA `cryptography`; exact version/hash/build provenance remains a pre-implementation gate.
- No Ed25519ph, Ed25519ctx, algorithm fallback, PEM/raw-key/certificate input or network resolution.
- Trust Policy MUST explicitly authorize the AEO profile, issuer role, purpose, audience and scope. Profile ID alone never establishes trust.

### 4.3 AEO package descriptor

The detached AEO package descriptor MUST bind both:
- the AEO body descriptor (object ID/type/schema/canonicalization/digest algorithm/digest/byte length); and
- the AEO signature envelope descriptor (descriptor ID/type/schema/digest algorithm/digest/byte length).

The AEO signature envelope itself MUST contain the exact canonical AEO Signature Statement bytes and 64-octet signature. Its own detached envelope descriptor follows §6. The main checkpoint Signature Statement binds the complete AEO package descriptor. Thus the verifier can resolve the AEO body and independently verify the AEO signature without relying on mutable URLs or unbound metadata.

## 5. Main checkpoint Signature Statement changes — B

A2.2 §3.1 is superseded as follows.

1. Retain all A1 checkpoint statement fields, A2.2 purpose/audience/profile/signer/policy fields and exact Evidence Object descriptor.
2. Remove the following direct provenance fields from the main Signature Statement: `signing_software_id`, `signing_software_version`, `signing_build_digest_algorithm`, `signing_build_digest`, `signing_request_id`, `signing_decision_id`, `signing_decision_digest`, `signer_authority_evidence_id`, `signer_authority_evidence_digest`, `signer_custody_evidence_id`, `signer_custody_evidence_digest`.
3. Replace them with exactly one mandatory `authorization_evidence_package_descriptor` object. It binds the AEO body descriptor and AEO signature-envelope descriptor as defined in §4.3.
4. A missing, unresolved, mismatched, invalidly signed, out-of-scope or untrusted AEO package MUST fail closed. The main checkpoint signature MUST NOT be considered trusted/authorized merely because its own Ed25519 signature is mathematically valid.
5. Owner authorization fields remain separate and follow A2.2 §2.2. The AEO is signer provenance/authority evidence, not an Owner Authorization object.



## 5.1 Profile and algorithm amendments — A2.2 §15

A2.2 §15 is supplemented by the following exact profile rules. The existing checkpoint profile identifier remains unchanged; its algorithm is now fixed by the owner's Stage II Ed25519 decision.

**Checkpoint issuer profile**
- `signature_profile_id`: `T0-CHECKPOINT-ISSUER-SIGNATURE-PROFILE-V2`.
- `signature_profile_version`: exact integer `2`.
- `signature_algorithm_id`: exact string `Ed25519` (RFC 8032 PureEdDSA).
- Public-key encoding: strict DER SubjectPublicKeyInfo, Ed25519 AlgorithmIdentifier parameters absent, 32-byte subjectPublicKey.
- Signature encoding: exactly 64 raw octets.
- Ed25519ph and Ed25519ctx are forbidden.

**Authorization Evidence issuer profile**
- `signature_profile_id`: `T0-AUTHORIZATION-EVIDENCE-ISSUER-SIGNATURE-PROFILE-V1`.
- `signature_profile_version`: exact integer `1`.
- `signature_algorithm_id`: exact string `Ed25519` (RFC 8032 PureEdDSA).
- Public-key and signature encodings are identical to the checkpoint profile above.
- Purpose MUST be `T0_AUTHORIZATION_EVIDENCE_ISSUER_ATTESTATION`; signer role MUST be `AUTHORIZATION_EVIDENCE_ISSUER`.

Trust Policy MUST authorize each profile ID/version, algorithm, role, purpose, audience and scope explicitly. No profile may be inferred from the other. Both profiles use the same stateless Ed25519 verification primitive, but their signed statements and domain separators remain distinct. The FIPS-validated-module requirement remains NOT mandatory and MUST NOT be represented as FIPS certification or approved-mode operation.

This section records the owner's already-approved Ed25519 algorithm/key/signature choices and defines the AEO purpose-specific profile proposal. The AEO profile's exact blob remains subject to independent review and owner freeze.

## 6. Detached envelope descriptor — E2

A2.2 §3.3 is superseded in full.

### 6.1 Envelope bytes

The canonical `T0-SIGNATURE-ENVELOPE-V1` contains only:
- envelope type/schema;
- exact canonical Signature Statement bytes;
- exact signature profile/algorithm identifiers repeated for transport consistency;
- exact 64-octet signature representation.

Mutable transport metadata and detached descriptor fields MUST NOT be included in canonical envelope bytes. The envelope MUST NOT contain its own descriptor ID, envelope digest or envelope byte length.

### 6.2 Detached descriptor schema

Type: `T0-SIGNATURE-ENVELOPE-DESCRIPTOR-V1`.

| Field | Type | Rule |
|---|---|---|
| `descriptor_id` | string | Independently allocated opaque ID; not derived from descriptor/envelope bytes |
| `descriptor_type` | string | Exact type above |
| `schema_version` | integer | Exact `1` |
| `envelope_type` | string | Exact `T0-SIGNATURE-ENVELOPE-V1` |
| `envelope_schema_version` | integer | Exact envelope schema version |
| `canonicalization_profile` | string | Exact envelope canonicalization |
| `digest_algorithm` | string | Exact `SHA-256` |
| `envelope_digest` | lowercase hex string | A2.2 §20.1 Signature Envelope object digest over exact complete canonical envelope bytes |
| `envelope_byte_length` | canonical U64 decimal string | Exact byte length |
| `audience` | string | Exact verifier namespace |
| `created_at_observed_ms` | canonical U64 decimal string or null | Observation only, not trusted time |

Descriptor ID format is `urn:uuid:<lowercase-canonical-UUIDv4>`. The authorized descriptor issuer generates UUIDv4 using a cryptographically secure random generator and checks the append-only descriptor namespace before publication. A collision with identical exact descriptor bytes is idempotent; a collision with any different descriptor bytes is a hard conflict and MUST NOT overwrite. After an uncertain write, read back and compare exact bytes before retry. A retry MUST reuse the same pending descriptor bytes and ID; replacement requires an explicit immutable abort/replacement record.

The descriptor is detached and does not contain its own digest. If descriptor integrity is needed, the containing immutable evidence record or custody system binds its exact bytes. No descriptor-of-descriptor is introduced in v1.

### 6.3 Digest and lifecycle

The envelope digest is computed only after the complete canonical envelope bytes exist, using the exact A2.2 §20.1 Signature Envelope domain bytes, U64BE byte length and exact envelope bytes. The descriptor ID is assigned independently and is not included in the envelope digest input. The detached descriptor is created after the envelope digest/length are known.

External Verification Records MUST reference descriptor ID, descriptor schema, envelope digest algorithm/digest/length, verification input-set identity/digest, verifier build identity and append-only record identity. They MUST NOT be inserted into or mutate the signed statement or envelope.

## 7. Deterministic validation order and fail-closed outcomes

The verifier MUST apply these checks in order:
1. Parse exact canonical statement/envelope/descriptor bytes under the declared profiles; reject duplicates, noncanonical bytes and resource-limit violations.
2. Recompute exact object digests and lengths for the checkpoint Evidence Object, AEO body, AEO signature envelope and main signature envelope.
3. Verify descriptor IDs/types/schema/canonicalization/purpose/audience and cross-bind every exact digest/length.
4. Verify the AEO issuer Signature Statement signature mathematically using the Ed25519 adapter.
5. Verify the AEO issuer's key, role, profile, purpose, audience and scope against the already accepted Trust Policy. Do not attempt root bootstrap; A2.2 §§16–17 remain BLOCKED.
6. Check AEO issuer and subject signer are distinct.
7. Resolve and verify every required request, decision, authority and custody evidence dependency from the frozen verification input set.
8. Verify the AEO scope covers the exact subject signer, action, checkpoint ID/sequence, stream, object type and audience.
9. Verify the main checkpoint Signature Statement signature mathematically.
10. Verify main signer key/role/profile/purpose/audience against the accepted Trust Policy and confirm the AEO authorizes that exact signer and signing operation.
11. Only after all checks pass may the higher-level verifier report signer TRUSTED / signature AUTHORIZED. This amendment does not authorize anchor or checkpoint state mutation.

A mathematically valid signature is only a cryptographic dimension. It is not signer trust, owner approval, custody or authorization.

## 8. Negative-case migration — no silent loss

A2.2 NV-31..34 are superseded by the following exact cases. Existing A2.2 identifiers remain historical references.

| New case | Single isolated mutation | Expected result | Primary reason |
|---|---|---|---|
| A2.3-NV-01 | AEO body build digest changed while descriptor is retained | INVALID | `SIGNING_BUILD_PROVENANCE_INVALID` |
| A2.3-NV-02 | Required signing request/decision evidence absent | BLOCKED | `SIGNING_DECISION_MISSING` |
| A2.3-NV-03 | Required signer authority evidence absent | BLOCKED | `SIGNER_AUTHORITY_EVIDENCE_MISSING` |
| A2.3-NV-04 | Same detached envelope descriptor ID reused with different descriptor bytes | INVALID | `SIGNATURE_ENVELOPE_DESCRIPTOR_ID_REUSE` |
| A2.3-NV-05 | AEO body digest or byte length differs from exact bytes | INVALID | `AUTHORIZATION_EVIDENCE_DIGEST_MISMATCH` |
| A2.3-NV-06 | AEO issuer signature invalid | INVALID | `AUTHORIZATION_EVIDENCE_SIGNATURE_MISMATCH` |
| A2.3-NV-07 | AEO issuer key valid but not authorized for AEO role/purpose/audience | UNTRUSTED | `AUTHORIZATION_EVIDENCE_ISSUER_UNAUTHORIZED` |
| A2.3-NV-08 | AEO issuer and subject checkpoint signer are the same principal/key | BLOCKED | `AUTHORIZATION_EVIDENCE_SELF_ISSUED` |
| A2.3-NV-09 | AEO scope omits the exact checkpoint stream or signer | UNTRUSTED | `AUTHORIZATION_EVIDENCE_SCOPE_MISMATCH` |
| A2.3-NV-10 | Main statement references a different AEO package descriptor | INVALID | `AUTHORIZATION_EVIDENCE_BINDING_MISMATCH` |
| A2.3-NV-11 | Detached envelope descriptor ID is inserted into canonical envelope bytes | INVALID | `ENVELOPE_DESCRIPTOR_SELF_REFERENCE` |
| A2.3-NV-12 | AEO decision outcome is not affirmative | UNTRUSTED | `SIGNING_DECISION_NOT_APPROVED` |

Every negative fixture MUST start from an independently verified clean synthetic baseline, apply exactly one mutation, assert one aggregate verdict and one primary reason code, and prove all trust/policy/anchor/checkpoint state remains unchanged. No private production keys or real trust roots are permitted in fixtures.

## 9. Resource ceilings and parsing limits — proposed bounded profile

The following ceilings are proposed for Stage II offline verification and require explicit contract freeze:
- canonical signature statement bytes: maximum 1,048,576 octets (1 MiB); maximum fully prefixed signature preimage: 1,048,640 octets (1 MiB + 64 octets), covering the longest approved domain separator plus 8-byte length prefix;
- SPKI DER input: maximum 4,096 octets, with accepted Ed25519 SPKI expected to be the single canonical DER encoding;
- signature: exactly 64 octets;
- AEO canonical body: maximum 1,048,576 octets;
- canonical Signature Statement: maximum 1,048,576 octets before domain/length prefix;
- canonical envelope: maximum 1,114,112 octets (1 MiB + 64 KiB envelope overhead);
- descriptor: maximum 65,536 octets;
- nested evidence dependency count: maximum 64 descriptors per AEO package;
- JSON nesting depth: maximum 32; maximum object members 256; maximum array elements 256; maximum string UTF-8 length 16,384 octets.

Exceeding a ceiling MUST return `INPUT_LIMIT_EXCEEDED` or the owning parser's stable size-limit reason, before expensive parsing/verification. These are proposed ceilings, not frozen constants, until exact owner approval and independent review.

## 10. Relationship to Stage II Ed25519 adapter

The adapter contract remains narrow and stateless:
- exact preimage bytes in;
- strict DER SPKI bytes in;
- 64-octet raw signature in;
- typed mathematical verification outcome out.

The adapter does not parse AEOs, descriptors, JSON, Trust Policy, request/decision evidence or Verification Records. It does not perform trust, authorization, revocation, time, anchor or stateful checks. The AEO and main-statement verifiers construct the correct exact preimage and invoke the same primitive with their own explicit purpose/profile dispatch.

## 11. Remaining gates and non-authorizations

Before A2.3 can be frozen:
1. Owner approval of this exact A2.3 blob and proposed resource ceilings.
2. Exact-blob consistency review against Checkpoint Contract v1, A1, A2.2 §20 and the Stage II adapter contract.
3. Independent security review of the exact A2.3 and adapter-contract blobs. Self-review is not independent review.
4. Pin PyCA version, dependency hashes, wheel provenance, supported Python/platform matrix and offline build provenance.
5. Freeze the stable result/reason-code contract and AEO/descriptor schemas.
6. Reconcile the A2.2 Stage II adapter contract status text and handoff so that approval gates are not ambiguous.

Even after contract freeze, this amendment alone does not authorize root bootstrap, Trust Policy/Monotonic Anchor instances, durable Verification Record state, VPS/T0/runtime integration, custody publication, CI dispatch, production keys/signing, trading, or destructive operations. Adapter implementation requires an explicit exact-blob implementation authorization after the review gate.

**Disposition: A2.3 DRAFT CREATED / B + E2 CONFLICTS ADDRESSED / RESOURCE CEILINGS PROPOSED / NOT FROZEN / IMPLEMENTATION NOT YET AUTHORIZED.**
