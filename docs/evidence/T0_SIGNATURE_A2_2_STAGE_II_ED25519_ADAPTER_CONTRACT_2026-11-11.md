# A2.2 Stage II — Ed25519 verification adapter contract

**Status: DRAFT / OWNER-DECISIONS RECORDED / CONTRACT-ONLY / NOT FROZEN / NO IMPLEMENTATION AUTHORITY**  
**Date:** 2026-11-11  
**Branch:** `feature/t0-centralized-data-feeder-p1-20261101`  
**Governing references:** A2.2 amendment §20; A1 §§3–4, 13.2–13.4; Stage II crypto option analysis.

## 1. Authority and scope

This document records the owner-approved Stage II cryptographic choices and specifies a narrow, stateless signature-verification adapter. It is a contract draft only. It does not amend A1/A2.2, freeze the complete trust architecture, or authorize implementation.

Stage II is limited to answering one question: does the supplied Ed25519 public key mathematically verify the supplied signature over the exact contract-defined preimage bytes?

The adapter MUST NOT decide signer identity, key trust, role, purpose, audience, Trust Policy authorization, revocation status, historical trust-at-time, Monotonic Anchor freshness, custody, or acceptance. Those are separate layers and remain governed by A1 and subsequent approved contracts.

## 2. Owner decisions recorded

| Decision | Approved value |
|---|---|
| Signature algorithm | Ed25519 PureEdDSA as defined by RFC 8032 |
| Profile | Ed25519 only; Ed25519ph and Ed25519ctx are not accepted |
| Python library candidate | PyCA `cryptography`; exact version and wheel hashes remain a later supply-chain/build gate |
| Public-key representation | DER SubjectPublicKeyInfo (SPKI), strict canonical DER |
| Signature representation | Exactly 64 raw octets |
| FIPS requirement | A FIPS-validated cryptographic module is not a mandatory project requirement |
| Runtime posture | Offline verification; no network fetch; no VPS/runtime integration authorized |
| Key posture | Public key input only; no private key, key generation, signing, import ceremony, or trust-root bootstrap |

The FIPS decision is a project requirement decision only. It MUST NOT be represented as FIPS certification, validation, or approved-mode operation.

## 3. Governing signed bytes — no new message format

A1 §4.3 defines the checkpoint Signature Statement preimage. Let `S` be the exact canonical T0-JCS-1 bytes of the Signature Statement:

```
signature_preimage =
    UTF8("T0-SIGNATURE-STATEMENT-V1\0")
    || U64BE(byte_length(S))
    || S
```

The adapter MUST receive the already-constructed `signature_preimage` byte string and MUST pass those exact bytes to the Ed25519 verification primitive.

Requirements:

1. No JSON parsing or reserialization occurs inside the cryptographic adapter.
2. No implicit SHA-256 or other pre-hash is applied by the adapter. Ed25519 PureEdDSA verifies the supplied message bytes directly.
3. No newline conversion, Unicode normalization, whitespace trimming, encoding conversion, or domain-separator reconstruction occurs inside the adapter.
4. The caller MUST construct and validate the preimage according to A1 §4.3 and the governing T0-JCS-1/A2.2 rules before calling the adapter.
5. Producer-supplied preimage digests are not accepted as a substitute for the exact bytes.
6. The adapter MUST NOT accept a caller-selected algorithm fallback or infer an algorithm from signature length.

The same adapter primitive MAY be called by higher-level policy/anchor verifiers with their separately specified A1 preimages, but each caller remains responsible for supplying the exact bytes for the corresponding domain and object type. This contract does not authorize policy, anchor, root-bootstrap, or stateful verification implementation.

## 4. Key and signature encoding

### 4.1 Public key

Input public-key bytes MUST be one DER-encoded SubjectPublicKeyInfo object for Ed25519.

- The decoded key type MUST be Ed25519.
- The SPKI AlgorithmIdentifier MUST identify Ed25519 with parameters absent, consistent with the applicable encoding standard.
- The subjectPublicKey BIT STRING MUST contain exactly 32 public-key octets.
- BER, PEM, raw-key, certificate, alternate algorithm, unexpected parameters, trailing bytes, truncated DER, and noncanonical encodings MUST be rejected.
- The parser MUST consume the complete input.
- A parse/serialize round trip MUST reproduce the exact accepted DER bytes; otherwise reject.
- The signer fingerprint used by A1 is lowercase hexadecimal SHA-256 over these exact DER SPKI octets.

The cryptographic adapter receives SPKI bytes only. It does not resolve a fingerprint to a trusted registry entry or decide whether that key is authorized.

### 4.2 Signature

- Signature input MUST be exactly 64 octets.
- The signature is raw Ed25519 output; it is not ASN.1 DER, base64 text, or a digest.
- Any other length or malformed value MUST fail closed.
- Where carried in a canonical JSON envelope, binary-to-text encoding MUST follow A1 §14.3: unpadded base64url with strict canonical decoding. Envelope decoding is outside this adapter boundary.

## 5. Adapter interface

Conceptual interface:

```python
verify_ed25519(
    *,
    signature_preimage: bytes,
    public_key_spki_der: bytes,
    signature: bytes,
) -> VerificationResult
```

The interface MUST be deterministic and side-effect-free. Inputs are immutable byte strings. No filesystem, database, environment-variable, network, clock, subprocess, key-discovery, or mutable global-state access is permitted.

### 5.1 Result model

The adapter MUST return exactly one typed outcome:

- `VALID`
- `INVALID_SIGNATURE`
- `MALFORMED_PUBLIC_KEY`
- `MALFORMED_SIGNATURE`
- `UNSUPPORTED_KEY_TYPE`
- `BACKEND_UNAVAILABLE`
- `INTERNAL_ERROR`

The adapter MUST NOT collapse backend unavailability or unexpected internal errors into `INVALID_SIGNATURE`, and MUST NEVER convert an exception or unknown result into `VALID`.

Input-size/resource-limit rejection may be represented by a separately agreed `INPUT_LIMIT_EXCEEDED` result once limits are frozen; until then resource ceilings remain an implementation-approval blocker and MUST NOT be guessed by an implementation.

### 5.2 Error semantics

- A mathematically incorrect signature for a well-formed Ed25519 key and message returns `INVALID_SIGNATURE`.
- Invalid or noncanonical SPKI returns `MALFORMED_PUBLIC_KEY`.
- Signature length other than 64 octets returns `MALFORMED_SIGNATURE`.
- A valid SPKI object for a different key type returns `UNSUPPORTED_KEY_TYPE`.
- Missing/unloadable cryptographic backend returns `BACKEND_UNAVAILABLE`.
- Unexpected errors return `INTERNAL_ERROR`; diagnostics MUST be sanitized and MUST NOT expose key material or sensitive input bytes.
- No failure result may trigger fallback to another algorithm, profile, key encoding, library, or online provider.

## 6. Security and isolation invariants

The implementation, when separately authorized, MUST satisfy all of the following:

1. Verify only Ed25519 PureEdDSA; reject Ed25519ph, Ed25519ctx, ECDSA, RSA and unknown profiles.
2. Verify exactly the supplied preimage bytes; never silently hash or canonicalize them.
3. Accept only the single SPKI DER representation specified in §4.1 and a 64-octet signature.
4. Perform no network access and no runtime package/key/trust-root retrieval.
5. Perform no writes or state transitions.
6. Make no trust, identity, authorization, freshness, custody, or historical-time claims.
7. Fail closed on malformed input, unsupported profiles, backend failure, and unexpected exceptions.
8. Keep private keys entirely outside this component and its fixtures.
9. Do not log raw public-key bytes, signature bytes, or message contents by default.
10. Preserve `AI_EXECUTION_ENABLED=false`; no trading or order path may consume this adapter as execution authorization.

## 7. Required verification tests

A future implementation test suite MUST include:

- independently sourced RFC 8032 Ed25519 known-answer vectors;
- valid signature over exact expected bytes;
- one-bit mutation of the message;
- one-bit mutation of the signature;
- wrong public key;
- empty, truncated, overlong, malformed and trailing-byte SPKI inputs;
- SPKI with wrong OID, unexpected parameters, wrong BIT STRING length, or noncanonical DER;
- raw 32-byte key, PEM, certificate, and alternate key types rejected;
- signature lengths 0, 1, 63, 65 and a valid-length incorrect signature;
- Ed25519ph/Ed25519ctx and profile downgrade attempts rejected;
- exact-byte tests proving no reserialization, implicit hashing, newline or Unicode normalization;
- backend unavailable and unexpected backend exception mapping;
- no filesystem/network/database access;
- no state mutation on every success and failure path;
- independent vector/oracle comparison not implemented by reusing the same helper under test.

Test vectors MUST be sourced independently from the implementation and recorded with provenance. Test fixtures MUST use published vectors or ephemeral test-only material; no production private key may be created or stored as part of this stage.

## 8. Dependency and build provenance — deferred gate

PyCA `cryptography` is the approved library candidate, not yet a pinned dependency.

Before implementation approval, a separate build review MUST record:

- exact package version;
- exact transitive dependency resolution;
- wheel/source distribution provenance and SHA-256 hashes;
- supported CPython and OS/platform matrix;
- offline installation/build behavior;
- license and maintenance/security review;
- backend/OpenSSL runtime details needed to interpret operational claims;
- reproducible CI inputs and artifact evidence.

No package installation, lockfile change, VPS installation, CI secret, workflow dispatch, or runtime deployment is authorized by this contract draft.

## 9. Open blockers before contract freeze

The owner-approved choices above resolve the algorithm, library candidate, key encoding, signature encoding and FIPS requirement. The following are intentionally not invented:

1. Exact maximum preimage size and parser/resource ceilings.
2. Exact pinned PyCA release and dependency hashes.
3. Full mapping of every legacy v1 signature-envelope provenance field to the A1 Signature Statement schema, if not already satisfied by the controlling schema.
4. Final consistency review against the complete A1/A2.2 contract and a qualifying independent security review.
5. Stable public reason-code compatibility policy, if consumers beyond the current verifier will depend on these values.

Until these blockers are resolved and the exact contract blob is approved/frozen, implementation remains BLOCKED.

## 10. Explicit exclusions

This document does NOT authorize:

- code implementation or test/workflow changes;
- generation, import, export, storage, use, rotation, or revocation of real keys;
- private-key operations or production signing;
- root enrollment, trust bootstrap, Trust Policy instances, signer registry, or key lifecycle operations;
- Monotonic Anchor instances, publication, durable state, or custody transitions;
- TSA/trusted-time provider selection or network access;
- VPS/SSH/systemd/Feeder/API/SQLite/T0 access or modification;
- CI secrets, dependency installation, workflow dispatch, deployment, or runtime integration;
- trading integration, ledger mutation, Shared Risk Engine, Kill Switch, or orders;
- deletion, retention, compaction, or any destructive data operation.

**Disposition: OWNER DECISIONS RECORDED; CONTRACT DRAFT ONLY; NOT FROZEN; IMPLEMENTATION BLOCKED / NOT AUTHORIZED.**


## 11. Owner-approved higher-level provenance and envelope identity decisions (2026-11-11)

**Decision status: ARCHITECTURE PATTERN SELECTED / DETAILED SCHEMAS NOT FROZEN.**  
The owner approved Option B + E2 from the Stage II provenance/envelope options note. This decision authorizes documentation and contract refinement only. It does not authorize implementation, tests, dependency changes, key operations, trust-state changes, CI dispatch, or runtime integration.

### 11.1 Option B — separately signed Authorization Evidence Object

The three A1 §14.4 provenance/authorization items MUST be represented in a distinct Authorization Evidence Object rather than added as direct fields to the Signature Statement:

1. signing software/build identity;
2. signing request/decision reference;
3. signer authority/custody evidence reference.

The Signature Statement MUST bind the exact Authorization Evidence Object using an immutable descriptor. At minimum, the descriptor contract MUST define and bind:
- object ID;
- object type;
- schema version;
- canonicalization identifier;
- digest algorithm and digest over the exact canonical object bytes;
- exact byte length;
- purpose/context.

The Authorization Evidence Object MUST have its own signed statement and signature. Its signature MUST be verified independently from the main Signature Statement. A mathematically valid signature on either object MUST NOT by itself be treated as proof of signer authority, custody, trust, or policy authorization.

The object schema, exact field names/types, signer role, signature domain/profile, trust chain, evidence issuer namespaces, cardinality, reuse scope, revocation and historical-time semantics remain open contract work. They MUST be specified consistently with A1 before schema freeze. A referenced object MUST NOT be accepted based only on a mutable URL, label, or unverified ID.

The Authorization Evidence Object signer MUST NOT be allowed to establish its own authority merely by asserting it inside the same object. The governing trust layer must validate the signer and authority evidence through an independently defined trust path.

### 11.2 Option E2 — detached descriptor identity

Envelope identity MUST use a detached descriptor. The envelope ID MUST NOT be inserted into bytes from which that same ID is derived.

The detached descriptor MUST bind the completed envelope using at least:
- a descriptor ID assigned independently of the descriptor bytes (or by a separately specified non-self-referential derivation);
- the exact envelope content digest and digest algorithm;
- exact envelope byte length;
- the envelope type/schema/profile identifiers needed to interpret the bytes.

For this draft, use an independently assigned opaque descriptor ID as the conservative baseline. The allocation authority, namespace, uniqueness scope, collision handling, and retry semantics remain to be specified before freeze. Do not derive the descriptor ID from a descriptor serialization that contains the ID itself.

The envelope digest MUST be computed only after the complete envelope bytes exist. External Verification Records MUST reference the immutable descriptor/envelope digest, not a mutable locator or descriptor ID alone. Verification Records remain post-signing append-only records and MUST NOT be inserted retroactively into the signed Signature Statement.

### 11.3 Non-circular object lifecycle

The intended higher-level lifecycle is:

1. Construct and canonicalize the Authorization Evidence Object.
2. Sign that object under its separately specified, A1-consistent signature contract.
3. Compute its exact immutable descriptor fields (digest and byte length included).
4. Include that descriptor in the main Signature Statement.
5. Canonicalize and sign the main Signature Statement using the existing A1 §4.3 preimage and Ed25519 adapter boundary.
6. Construct the completed envelope.
7. Compute the envelope digest and byte length.
8. Create the detached descriptor and assign its independent opaque ID.
9. Append Verification Records referencing the exact descriptor/envelope digest after verification.

This is a contract-level ordering model, not an implementation workflow authorization. Exact object serialization, signature domains, descriptor schemas, failure semantics, and transaction/retry behavior remain open.

### 11.4 Separation from the cryptographic primitive

The Ed25519 adapter defined in §§3–7 remains unchanged and stateless. It receives exact preimage bytes, SPKI DER, and a 64-octet signature. It does not parse Authorization Evidence Objects, resolve descriptors, establish signer authority, evaluate Trust Policy, check revocation/anchors, or mutate Verification Records.

### 11.5 Remaining blockers

The B + E2 architecture choice resolves the representation-level owner decision. It does NOT close the complete schema or implementation gates. The following remain open:
1. Exact Authorization Evidence Object schema, field names/types, cardinality and canonicalization.
2. Authorization-object signature statement, domain separator, signer role and trust-chain contract, consistent with A1.
3. Exact immutable descriptor schema and ID allocation/uniqueness/retry rules.
4. Resource ceilings, parser limits and maximum object/preimage sizes.
5. Pinned PyCA release, dependency hashes and build provenance.
6. Complete A1/A2.2 consistency review and qualifying independent security review.
7. Verification Record schema, retention and append-only enforcement contract.
8. Stable public reason-code compatibility policy, if externally consumed.

**Updated disposition: B + E2 OWNER-APPROVED AS ARCHITECTURE PATTERN; DETAILED CONTRACT DRAFT / NOT FROZEN; IMPLEMENTATION BLOCKED / NOT AUTHORIZED.**
