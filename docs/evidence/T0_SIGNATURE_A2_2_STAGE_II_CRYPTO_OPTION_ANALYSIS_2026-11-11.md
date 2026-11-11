# A2.2 Stage II — cryptographic option analysis

**Status: DRAFT / NON-NORMATIVE / OWNER DECISION REQUIRED / NO IMPLEMENTATION AUTHORITY**  
**Date:** 2026-11-11  
**Branch:** `feature/t0-centralized-data-feeder-p1-20261101`  
**Purpose:** Compare bounded options for a future real signature-verification adapter. This document does not amend A2.2 or authorize implementation.

## 1. Decision boundary

Stage I remains synthetic-only and its CI gate PASS does not provide production cryptographic assurance. This assessment covers only a candidate Stage II verification adapter and its algorithm, wire-format and library choices.

The adapter must receive the exact message bytes defined by the governing A2.2 contract. It must not parse and reserialize an object, invent a new digest input, or silently hash again. Before a contract is approved, the exact signed byte sequence must be reconciled against A2.2 §§19–20 and the Signature Envelope definition.

Keep these outcomes distinct:

1. byte-level parsing and object/digest binding;
2. cryptographic signature validity;
3. signer identity and trust-root resolution;
4. Trust Policy authorization;
5. Monotonic Anchor, replay and sequence checks;
6. accepted-state/custody transition.

A successful signature verification MUST NOT itself establish items 3–6 or mutate durable state.

## 2. Candidate algorithm comparison

| Candidate | Strengths | Costs / risks | Assessment |
|---|---|---|---|
| Ed25519 (PureEdDSA, RFC 8032) | Deterministic signatures; compact fixed-size public key (32 octets) and signature (64 octets); simple verification interface; no per-signature nonce supplied by caller | Interoperability requires exact variant/profile; Ed25519 is not interchangeable with Ed25519ph/Ed25519ctx; some constrained/FIPS-validated environments may impose provider/module requirements | **Preferred candidate for a narrow, new, software-only verifier**, subject to owner decision and environment constraints |
| ECDSA P-256 with SHA-256 | Broad ecosystem and hardware/provider support; NIST FIPS 186-5 includes ECDSA | Requires exact hash/curve/profile; signature encoding choice (DER vs fixed-width) and canonicality rules; nonce-generation concerns for signers; more format/parameter surface | Viable alternative if interoperability or a validated provider is a hard requirement |
| RSA-PSS with SHA-256 | Mature, widely supported; explicit standardized padding and digest parameters | Larger keys/signatures and higher bandwidth/storage; exact modulus size, salt length and encoding must be fixed | Viable compatibility option, not preferred for a compact evidence envelope |

NIST FIPS 186-5 specifies RSA, ECDSA and EdDSA for digital signatures. RFC 8032 defines Ed25519 and its verification parsing/range checks. These standards establish candidate legitimacy, not suitability for this system by themselves.

## 3. Candidate key and signature representations

### Option A — Ed25519 raw fixed-width
- Public key: exactly 32 raw octets.
- Signature: exactly 64 octets.
- Profile: one explicit identifier for **PureEd25519 only**; explicitly reject Ed25519ph, Ed25519ctx and unknown variants.
- Reject wrong lengths and malformed/non-canonical encodings before reporting a valid signature.
- Advantages: minimal format ambiguity and compact deterministic fixtures.
- Trade-off: raw key bytes do not carry a self-describing algorithm OID; profile identifier must be bound unambiguously by the envelope and policy.

### Option B — Ed25519 SubjectPublicKeyInfo (SPKI) DER
- Public key: DER-encoded SPKI with the Ed25519 algorithm identifier; strict parser and exact accepted encoding rules.
- Signature: exactly 64 raw octets.
- Advantages: algorithm is carried in a standard public-key container; easier integration with certificate/key tooling.
- Trade-off: parser surface and DER canonicality/algorithm-parameter rules must be specified. Do not accept multiple equivalent encodings by accident.

### Option C — ECDSA/RSA encodings
- ECDSA: explicitly select DER ASN.1 or fixed-width P1363; do not accept both implicitly. Define low-S policy if required by the chosen protocol.
- RSA-PSS: define modulus size, MGF1 digest, message digest, salt length and signature length exactly.
- These options have materially more parameters than Ed25519 and should be selected only for a demonstrated compatibility requirement.

**Preliminary recommendation:** if no external interoperability or validated-module requirement overrides it, use Ed25519 with one fixed profile and one public-key encoding. Prefer SPKI DER if the envelope needs self-describing key material; prefer raw 32-byte keys only if algorithm/profile is already unambiguously bound by the envelope and signer-key registry. Owner decision required.

## 4. Candidate library/provider

**Candidate: PyCA `cryptography`**, using its high-level Ed25519 verification API.

Reasons:
- Python-native API with explicit `verify(signature, data)` semantics and an `InvalidSignature` failure.
- Supports raw and DER/SPKI public-key serialization/parsing.
- Current project CI uses CPython 3.12; PyCA's current installation documentation lists Python 3.9+ support and tested Ubuntu releases including 26.04.
- Wheels bundle cryptographic dependencies on common Linux platforms, which can support a pinned, offline CI build when the exact wheel and hashes are vendored/allowlisted.

Limits:
- No package version is selected here. A future contract must pin an exact release and dependency hashes, record wheel provenance, and test the exact CPython/platform matrix.
- A Python package using OpenSSL does **not** by itself prove FIPS 140 validation or that the runtime is operating in an approved validated mode. If FIPS validation is a requirement, obtain a separately validated provider/module and verify its exact operational configuration.
- Verification must not fetch packages, keys, trust roots, CRLs or network metadata at runtime.
- No package installation on the VPS or project runtime is authorized.

## 5. Proposed narrow adapter contract (for later specification)

Input:
- explicit immutable profile identifier/version;
- exact message byte string, already produced by the contract-defined canonical/digest layer;
- bounded public-key bytes in one selected representation;
- bounded signature bytes in one selected representation.

Output:
- `VALID` or a typed failure reason such as `INVALID_SIGNATURE`, `MALFORMED_KEY`, `MALFORMED_SIGNATURE`, `UNSUPPORTED_PROFILE`, `BACKEND_UNAVAILABLE`, or `INTERNAL_ERROR`;
- no identity/trust/policy verdict;
- no writes, state transitions, fallback, network access or key discovery.

The public adapter should fail closed. Unexpected backend errors must not be converted into `VALID`; they must remain distinguishable from an ordinary invalid signature. The caller must not advance Trust Policy, Monotonic Anchor, accepted checkpoint or custody state for any failure.

## 6. Minimum test/evidence requirements

- Independently sourced RFC/NIST known-answer vectors for the selected profile.
- Valid signature over the exact approved bytes.
- One-bit mutation of message and signature; wrong key.
- Wrong profile/version and attempted Ed25519 variant downgrade.
- Empty, truncated, overlong and malformed key/signature encodings.
- Unsupported key type/algorithm parameters.
- Exact-byte binding tests: no JSON reserialization, implicit hashing, newline normalization or Unicode normalization.
- Backend unavailable/error and deterministic typed reason mapping.
- State-immutability assertion for every rejected/error case.
- Offline CI with dependency lock, hashes, no network fetch, bounded input sizes and reproducible artifact evidence.
- Independent security review; explicitly revisit the existing G3 waiver rather than treating Stage I self-review as independent assurance.

## 7. Recommendation and unresolved owner decisions

1. **Algorithm candidate:** Ed25519 PureEdDSA.
2. **Library candidate:** PyCA `cryptography`, exact version to be pinned only after the supported runtime and provenance review.
3. **Public-key representation:** choose one of raw 32-byte or SPKI DER. SPKI is the more self-describing candidate; raw is simpler only where the envelope/profile registry already fixes the algorithm unambiguously.
4. **Signature representation:** fixed 64-byte Ed25519 signature.
5. **Verification input:** must be copied verbatim from the normative A2.2 definition; this document intentionally does not infer whether the signed message is the serialized envelope, a domain-separated object digest, or another byte sequence.
6. **FIPS/validated-module requirement:** currently unknown and must be answered before locking the algorithm/provider.
7. **Trust/key lifecycle:** out of scope for this adapter and requires separately specified/approved trust and bootstrap stages.

**Decision requested:** approve/reject the Ed25519 + PyCA candidate for a contract-only Stage II specification, and decide whether SPKI DER or raw public-key bytes are required. This decision would still not authorize implementation, real key generation/import, private-key use, trust-root bootstrap, durable trust/anchor state, runtime/VPS integration, workflow dispatch or trading.

## 8. References

- NIST FIPS 186-5, Digital Signature Standard: https://csrc.nist.gov/pubs/fips/186-5/final
- RFC 8032, EdDSA: Ed25519 and Ed448: https://www.rfc-editor.org/rfc/rfc8032.html
- PyCA cryptography Ed25519 API: https://cryptography.io/en/latest/hazmat/primitives/asymmetric/ed25519/
- PyCA cryptography installation/platform support: https://cryptography.io/en/latest/installation/

**Current disposition: DRAFT / NON-NORMATIVE / NOT OWNER-APPROVED / NO IMPLEMENTATION AUTHORITY.**
