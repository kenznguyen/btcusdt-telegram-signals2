# Stage II — Authorization Evidence Object and Detached Envelope Descriptor Schema Draft

**Date:** 2026-11-11 (Asia/Ho_Chi_Minh)  
**Branch:** `feature/t0-centralized-data-feeder-p1-20261101`  
**Status: OWNER-APPROVED ARCHITECTURE DIRECTION / DETAILED SCHEMA PROPOSAL / NON-NORMATIVE / NOT FROZEN / NO IMPLEMENTATION AUTHORITY**

## 1. Authority and scope

This draft implements the documentation task authorized by the owner's approval of Option B + E2:
- Option B: carry signing provenance and authorization references in a separately signed Authorization Evidence Object (AEO), bound by the main Signature Statement.
- Option E2: identify the completed signature envelope using a detached descriptor whose identifier is independent of the descriptor bytes.

This document proposes bounded logical schemas, object relationships, validation rules, and lifecycle ordering. It does not amend A1/A2.2, freeze wire formats, select a new signature domain, resolve trust bootstrap, or authorize implementation.

The approved Stage II Ed25519 primitive remains unchanged: it verifies the exact preimage bytes supplied by its caller, using Ed25519 PureEdDSA, SPKI DER and a 64-octet signature. The primitive does not parse these proposed objects or make trust/authorization decisions.

## 2. Normative source review and known conflicts

The draft was compared with:
- Checkpoint Contract v1, blob `a6825270d59bde274bfe765d5f942144b66a84de`;
- A1, blob `00fdad293e129562145ab930507a4e6b9c2bf23d`;
- A2.2, blob `d9f93bf390d107381b7135c3073aeca0d14894d4`;
- Stage II Ed25519 adapter contract before this draft, blob `e1b12fc1fc4b463fc82ff8b6b5f0b2701af5888b`.

Important reconciliation findings:

1. A1 §14.4 explicitly permits the three provenance/authorization items either inside the signed Signature Statement or in a separately signed authorization-evidence object whose exact ID/digest is bound by the statement. B is compatible with this alternative.
2. A1 §4.4 states envelope ID/digest is computed only after signature creation and MUST NOT be included in its own signed statement. This aligns with detached E2.
3. A2.2 §3.1 currently places software/build, request/decision and signer authority/custody fields directly in the main Signature Statement. This conflicts with selected Option B unless A2.2 is explicitly amended.
4. A2.2 §3.1 and §3.3 currently require `signature_envelope_id` to be assigned before signing and included in the signed statement. This conflicts with detached E2 and A1 §4.4.
5. A2.2 §5.2 includes negative cases tied to direct provenance fields and envelope-ID reuse. These cases need remapping to AEO/descriptor semantics, not silent deletion.

Therefore this draft is a target schema proposal, not a claim that A1/A2.2 are already consistent. A bounded normative correction (expected A2.3 or an explicitly versioned successor) and a renewed exact-blob consistency review are required before freeze.

## 3. Object graph

The proposed graph is:

```
Authorization Evidence Object bytes
        |
        +-- Authorization Evidence Statement (signed independently)
        |
        +-- Authorization Evidence Descriptor (exact ID/type/schema/digest/length)
                         |
                         v
Main Signature Statement -- binds AEO descriptor
        |
        +-- Ed25519 signature over A1-defined exact statement preimage
        |
        v
Completed Signature Envelope bytes
        |
        +-- Detached Envelope Descriptor (external ID + exact digest/length)
                         |
                         v
Append-only Verification Records reference descriptor ID + envelope digest
```

No object may establish its own trust merely by asserting a role, authority, issuer or key fingerprint in its own bytes. All signer/issuer claims require validation against the separately provisioned Trust Policy/bootstrap path.

## 4. Authorization Evidence Object (AEO) — proposed schema

### 4.1 Object identity and canonical bytes

Proposed type: `T0_AUTHORIZATION_EVIDENCE`  
Proposed schema identifier: `T0-AUTHORIZATION-EVIDENCE-V1`  
Canonicalization: T0-JCS-1, subject to final A1/A2.2 consistency review.

The canonical AEO body MUST NOT contain its own content digest or detached descriptor. Its exact canonical bytes are hashed externally using the governing Evidence Object digest rule. An ID MUST NOT be reused for changed bytes.

### 4.2 Proposed body fields

| Field | Proposed type | Required meaning / validation |
|---|---|---|
| `authorization_evidence_id` | opaque identifier string | Unique within the AEO namespace; not a mutable URL or display name |
| `object_type` | exact enum | `T0_AUTHORIZATION_EVIDENCE` |
| `schema_version` | canonical schema-version value | Exact schema discriminator |
| `canonicalization_profile` | registered identifier | `T0-JCS-1` for this draft |
| `authorization_purpose` | registered enum | Exact purpose for which this evidence is issued; no generic wildcard |
| `audience` | immutable namespace identifier | Exact relying system/namespace |
| `subject_signer_fingerprint` | lowercase SHA-256 hex | Fingerprint of exact DER SPKI bytes of the signer whose authority is evidenced |
| `subject_signer_role` | registered role identifier | Role granted/evidenced; must be checked against Trust Policy |
| `signing_software` | object | Exact software product ID, version, build digest algorithm and build digest |
| `signing_request` | object | Immutable request ID and request digest descriptor |
| `signing_decision` | object | Immutable decision ID, decision digest descriptor and explicit outcome |
| `authority_evidence_refs` | non-empty ordered array | Exact references to delegation/authority evidence supporting the subject role |
| `custody_evidence_refs` | ordered array | Exact references to key-custody evidence; empty only when policy explicitly allows and records why |
| `scope` | object | Exact permitted action, object types, stream/audience and any limits |
| `issuer_identity_ref` | immutable reference | Identity record for AEO issuer; not self-authenticating |
| `issued_at_observed_ms` | canonical unsigned decimal string or explicit null | Local observation only; never proves trusted historical time |
| `validity` | object or explicit `NOT_ASSERTED` | Time-bounded validity only if trusted-time semantics and status history are defined |
| `status_evidence_refs` | ordered array | Revocation/supersession/status evidence references, or explicit `NOT_ESTABLISHED` |
| `extensions` | object | MUST be empty in v1 unless a registered extension namespace/schema is approved |

The following subobjects are proposed:

**`signing_software`**
- `software_id`: stable product identifier;
- `software_version`: exact version string, no floating alias;
- `build_digest_algorithm`: registered digest identifier;
- `build_digest`: digest of exact build artifact or independently verifiable reproducible-build statement.

**`signing_request`**
- `request_id`: immutable ID in a declared namespace;
- `request_digest`: descriptor with object ID, object type, schema, digest algorithm, digest and exact byte length.

**`signing_decision`**
- `decision_id`: immutable ID;
- `decision_digest`: descriptor of exact decision evidence;
- `outcome`: explicit enum; only an affirmative, in-scope decision can support signing authorization.

**`scope`**
- `actions`: non-empty registered action list;
- `audience`: exact audience identifier;
- `object_types`: explicit allowlist;
- `stream_ids`: explicit checkpoint stream allowlist;
- `constraints`: versioned constraints object; no implicit wildcard.

No untrusted local timestamp may be used to establish expiry, historical signer authority or revocation ordering. If the relying verifier cannot establish a required time/status fact, the result is UNKNOWN/BLOCKED, not authorized by inference.

### 4.3 AEO detached descriptor

Proposed descriptor type: `T0_AUTHORIZATION_EVIDENCE_DESCRIPTOR`.

| Field | Proposed rule |
|---|---|
| `object_id` | Exact `authorization_evidence_id` |
| `object_type` | `T0_AUTHORIZATION_EVIDENCE` |
| `schema_version` | Exact AEO schema version |
| `canonicalization_profile` | Exact canonicalization identifier |
| `digest_algorithm` | Fixed registered digest; SHA-256 under current v1 profile |
| `content_digest` | Digest recomputed over exact canonical AEO bytes |
| `byte_length` | Exact byte length of canonical AEO bytes |
| `purpose` | Exact purpose matching the AEO body |
| `audience` | Exact audience matching the AEO body |

The descriptor is carried in the main Signature Statement. The descriptor's ID is not derived from its own serialized bytes. The digest and length MUST be recomputed from the exact AEO bytes supplied in the frozen verification input set. A mutable locator may be used only as a retrieval hint and MUST NOT participate in identity or authorization.

### 4.4 AEO signature statement — unresolved normative profile

The AEO MUST be signed independently from the main Signature Envelope. The signature statement for the AEO MUST bind:
- AEO object ID, type, schema, canonicalization, digest algorithm, digest and byte length;
- purpose and audience;
- signer SPKI fingerprint and role;
- Trust Policy identity, sequence and exact policy-body digest;
- exact signature profile and algorithm.

**Open decision:** A1 currently defines the exact preimage domain for `T0-SIGNATURE-STATEMENT-V1`. A separate AEO signature statement needs a distinct domain/type binding to prevent cross-object substitution. This draft does not invent or activate that domain separator. A2.3 must specify the AEO statement type, exact domain bytes, length-prefix rule, field schema and trust-policy binding, and prove no collision or cross-purpose confusion with A1 §4.3 and A2.2 §20.

The selected Ed25519 primitive may verify the eventual exact preimage bytes, but the caller-specific AEO preimage contract must be approved before implementation.

## 5. Main Signature Statement mapping under B

The main Signature Statement retains all existing A1 checkpoint, purpose, audience, object, checkpoint sequence/predecessor, signer, profile/algorithm and Trust Policy fields.

The following direct A2.2 provenance fields are proposed to be replaced by one mandatory field:

| Field | Proposed type | Rule |
|---|---|---|
| `authorization_evidence_descriptor` | descriptor object | Exactly one descriptor for v1; binds the AEO ID/type/schema/canonicalization/digest algorithm/digest/byte length/purpose/audience |

The direct fields proposed for removal from the main statement are:
- `signing_software_id`, `signing_software_version`, `signing_build_digest_algorithm`, `signing_build_digest`;
- `signing_request_id`, `signing_decision_id`, `signing_decision_digest`;
- `signer_authority_evidence_id`, `signer_authority_evidence_digest`;
- `signer_custody_evidence_id`, `signer_custody_evidence_digest`.

Those values remain mandatory in the AEO dependency closure. A field is not made optional merely by moving it: every required claim must remain bound, verifiable, purpose-limited and fail-closed.

Owner Authorization is a distinct concept under A2.2 §2.2. This B decision does not merge owner approval with signer authorization and does not create an owner key, owner authorization object, or owner-approval purpose. If an owner-authorization claim is later made, it retains its separate object and trust chain.

## 6. Detached Signature Envelope Descriptor (E2)

### 6.1 Completed envelope bytes

The completed canonical Signature Envelope contains:
- envelope schema/type;
- exact canonical Signature Statement bytes;
- signature algorithm/profile repeated for transport consistency and checked against the statement;
- raw signature bytes;
- only explicitly classified unsigned transport metadata outside the canonical signed content, where the governing envelope profile permits it.

The envelope's canonical bytes MUST NOT contain its own detached descriptor ID, envelope digest or envelope byte length.

### 6.2 Proposed detached descriptor schema

Proposed type: `T0_SIGNATURE_ENVELOPE_DESCRIPTOR`.

| Field | Proposed type | Rule |
|---|---|---|
| `descriptor_id` | opaque identifier string | Independently allocated; not derived from descriptor bytes; unique within declared namespace |
| `descriptor_type` | exact enum | `T0_SIGNATURE_ENVELOPE_DESCRIPTOR` |
| `descriptor_schema_version` | canonical schema version | Exact descriptor schema |
| `envelope_type` | exact enum | `T0-SIGNATURE-ENVELOPE-V1` |
| `envelope_schema_version` | canonical schema version | Exact envelope schema |
| `canonicalization_profile` | registered identifier | Exact envelope canonicalization |
| `digest_algorithm` | registered digest identifier | SHA-256 under current profile |
| `envelope_digest` | lowercase hex | Digest recomputed over complete canonical envelope bytes |
| `envelope_byte_length` | canonical unsigned decimal string | Exact byte length |
| `audience` | immutable namespace identifier | Exact intended verifier namespace |
| `created_at_observed_ms` | canonical unsigned decimal string or null | Local observation only; not trusted time |

The detached descriptor is external to the envelope bytes it describes. Its ID is allocated independently and is not included in the digest input. The descriptor itself may be stored as immutable evidence, but its identity/digest lifecycle must not be circular: if a descriptor digest is needed, it is computed over descriptor bytes that exclude the descriptor's own ID and digest, or through a separately specified external descriptor-of-descriptor. This draft prefers no descriptor-of-descriptor requirement.

### 6.3 ID allocation and idempotency proposal

- Namespace is scoped to the signature-envelope descriptor issuer.
- ID is an opaque, non-empty identifier allocated by the authorized descriptor issuer using a collision-resistant uniqueness mechanism.
- Exact allocation algorithm, namespace authority, collision probability target, persistence, and retry semantics remain open.
- Repeated publication of the same descriptor ID is idempotent only when descriptor bytes and bound envelope digest/length are identical.
- Same ID with any different field or envelope digest/length is a hard conflict; never overwrite.
- A retry after an uncertain write MUST read back and compare exact descriptor bytes before retrying. It MUST NOT allocate a second ID for the same pending logical publication unless a durable, authenticated abort/replacement record is defined.
- The descriptor ID alone is never proof of envelope authenticity or latestness.

### 6.4 Verification Record references

Append-only Verification Records SHOULD reference:
- descriptor ID and descriptor schema;
- exact envelope digest algorithm, digest and byte length;
- exact verification input-set identity/digest;
- verifier identity/version/build provenance;
- per-dimension outcomes and one aggregate verdict/reason code;
- local verification observation time, explicitly not trusted time.

Verification Records MUST NOT be inserted into or mutate the signed Signature Statement or completed Signature Envelope. Record schema, append-only enforcement, retention and conflict/recovery behavior remain separate contract work.

## 7. Proposed validation and fail-closed rules

1. Verify canonical encoding and exact byte length before digest comparison.
2. Recompute AEO digest and envelope digest from exact bytes; do not trust producer values.
3. Check object ID/type/schema/canonicalization/purpose/audience against the descriptor and referring statement.
4. Verify the AEO signature independently under its own approved statement domain and Trust Policy authorization.
5. Verify the main Signature Statement signature independently under A1 §4.3.
6. Validate that AEO scope explicitly covers the signer, action, audience, checkpoint stream and object type being asserted.
7. Resolve every required authority/request/decision/custody dependency from the frozen verification input set; missing dependencies are BLOCKED/UNKNOWN, not silently omitted.
8. Distinguish cryptographic VALID from signer TRUSTED and policy AUTHORIZED. No signature result alone grants authority.
9. Reject duplicate IDs with different exact bytes; preserve both evidence and conflict record without overwriting.
10. Reject mutable URL, display label or producer-supplied status as a substitute for exact object bytes and trusted status evidence.
11. Do not infer historical validity, expiry, revocation order or trusted time from local observation timestamps.
12. No fallback algorithm, key encoding, signature profile, canonicalization profile or online retrieval.

## 8. Required negative cases to add or remap

A future normative A2.3 matrix should include isolated cases for:
- AEO missing, malformed, wrong type/schema/canonicalization or wrong audience/purpose;
- AEO digest/length/ID mismatch and descriptor substitution;
- AEO signature invalid, wrong key, unsupported profile or wrong domain;
- AEO signer mathematically valid but unauthorized by Trust Policy;
- AEO scope omits signer/action/stream/object type/audience;
- missing, mismatched, expired only under trusted-time rules, revoked or superseded authority evidence;
- request ID collision, decision digest mismatch, negative decision outcome;
- build identity/version/digest mismatch;
- custody evidence missing where policy requires it;
- main Signature Statement references a different AEO than the one verified;
- envelope descriptor missing, ID collision, descriptor substitution, envelope digest/length mismatch;
- detached descriptor ID accidentally included in signed statement or envelope bytes (self-reference/circularity);
- retry after uncertain descriptor publication and same-ID/different-bytes conflict;
- Verification Record overwrite or retroactive mutation;
- AEO and main statement signatures valid individually but cross-object purpose/audience/scope binding inconsistent.

Each case must have one isolated mutation, one fixed aggregate verdict, one stable primary reason code, and before/after state assertions. Existing A2.2 NV-31 through NV-34 must be remapped rather than discarded.

## 9. Open decisions before schema freeze

1. Exact AEO field names/types and namespace registration.
2. AEO signature statement type and distinct domain separator/preimage, reconciled with A1 §4.3 and A2.2 §20.
3. Whether AEO signature uses the same Ed25519 profile and Trust Policy signer roles, or a separately registered role/profile.
4. Authority/delegation evidence issuer model, dependency closure, reuse/cardinality and anti-replay scope.
5. Trusted-time, validity, revocation and supersession semantics; local timestamps remain observation-only.
6. Descriptor ID namespace authority, allocation method, uniqueness/collision target and durable retry/abort protocol.
7. Exact descriptor canonicalization and whether any descriptor-of-descriptor digest is required (draft recommendation: none).
8. Verification Record schema and append-only storage/enforcement contract.
9. Maximum object/preimage sizes, parser limits and resource ceilings.
10. Pinned PyCA version, dependency hashes, wheel provenance and build matrix.
11. A2.3 normative amendment resolving the explicit A2.2 §3.1/§3.3 conflicts and remapping negative cases.
12. A renewed exact-blob consistency review. Qualifying independent security review remains required before implementation is considered; no waiver is inferred from this draft.

## 10. Explicit non-authorizations

This draft does NOT authorize:
- implementation, code changes, tests, test fixtures containing generated keys, dependency or lockfile changes;
- key generation/import/export/storage, signing, trust-root bootstrap or owner-key ceremony;
- Trust Policy, signer registry, Monotonic Anchor or Verification Record state creation/mutation;
- CI workflow changes or dispatch;
- VPS/SSH/systemd/Feeder/API/SQLite/T0 access or modification;
- custody publication, TSA/provider selection or network access;
- trading, ledger mutation, Shared Risk Engine, Kill Switch or orders;
- retention, deletion, compaction, backup expiry or other destructive operations.

**Disposition: DETAILED SCHEMA DRAFT CREATED / OWNER-APPROVED B + E2 ARCHITECTURE RESPECTED / A1-A2.2 CONFLICTS IDENTIFIED / CONTRACT NOT FROZEN / IMPLEMENTATION BLOCKED AND NOT AUTHORIZED.**

No tests were run; this increment is documentation-only.
