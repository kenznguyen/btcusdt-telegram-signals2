# A2.2 Stage I — Contract Ambiguity Resolution Proposal

Date: 2026-11-11  
Status: **PROPOSAL ONLY — NOT OWNER-APPROVED — DOES NOT AMEND A2.2**  
Governing source: `docs/architecture/T0_SIGNATURE_TRUST_POLICY_MONOTONIC_ANCHOR_AMENDMENT_A2_2_2026-11-11.md`  
Governing source blob: `41d41cd23f73a6e552b9ceca5ebbb39c46934e7d`

## 1. Purpose

Resolve two byte-level implementation ambiguities discovered while implementing the already owner-approved synthetic-only Stage I harness:

1. Different source spellings for domain-separator terminators.
2. Incomplete numeric-domain definition for restricted `T0-JCS-1`.

No authoritative architecture document or implementation code is changed by this proposal. The existing Stage I implementation remains fail-closed for unresolved digest domains.

## 2. Domain-separator byte sequence proposal

### 2.1 Observed source inconsistency

The source documents currently spell the domains as follows:

| Domain | Source spelling | Issue |
|---|---|---|
| Evidence Object | `T0-EVIDENCE-OBJECT-V1\0` | Single backslash before zero |
| Trust Policy body | `T0-TRUST-POLICY-BODY-V1\\0` | Double backslash before zero |
| Monotonic Anchor object | `T0-MONOTONIC-ANCHOR-OBJECT-V1\\0` | Double backslash before zero |
| Signature Envelope object | `T0-SIGNATURE-ENVELOPE-OBJECT-V1\\0` | Double backslash before zero |

A single-backslash NUL escape and a double-backslash literal-backslash-plus-zero spelling produce different digest preimages. The implementation MUST NOT infer which byte sequence was intended.

### 2.2 Proposed normative resolution

Use ASCII domain text followed by exactly one NUL octet (`0x00`) for all four domains. Express the byte sequence normatively as hexadecimal, not only as source-language escape syntax:

| Domain | Exact bytes (hex) |
|---|---|
| Evidence Object | `54302d45564944454e43452d4f424a4543542d563100` |
| Trust Policy body | `54302d54525553542d504f4c4943592d424f44592d563100` |
| Monotonic Anchor object | `54302d4d4f4e4f544f4e49432d414e43484f522d4f424a4543542d563100` |
| Signature Envelope object | `54302d5349474e41545552452d454e56454c4f50452d4f424a4543542d563100` |

Equivalent notation for each is `ASCII(domain-name) || 0x00`.

The digest preimage remains:

```
domain_bytes || U64BE(byte_length(payload)) || exact_payload_bytes
```

The payload MUST be the exact canonical object bytes specified by the relevant contract section. No JSON reserialization, normalization or producer-supplied digest is accepted in place of exact bytes.

### 2.3 Required acceptance vectors

For each domain, add a known-answer test that independently constructs:
- the exact hex domain bytes above;
- an 8-byte big-endian payload length;
- a fixed payload byte vector;
- the expected SHA-256 digest computed by an independent oracle.

Add a cross-domain separation test proving that the same payload yields different digests under each distinct domain.

## 3. Proposed restricted T0-JCS-1 numeric profile

The current A1 contract calls T0-JCS-1 a restricted profile but does not provide a complete numeric-token grammar in the inspected source. The current Stage I parser deliberately fails closed on floats and limits JSON integer tokens to the IEEE-754 safe-integer range; that implementation choice is not yet contract-approved.

Proposed normative rules:

1. Canonical structured objects use UTF-8 without BOM.
2. Duplicate object keys, invalid UTF-8, unpaired surrogates and non-finite numeric tokens are rejected.
3. Object member names are ordered by UTF-16 code units.
4. String serialization follows the selected JCS string-escaping rules; received canonical wire bytes MUST equal the independently serialized bytes.
5. JSON numeric tokens are limited to finite integral values in the inclusive range `-(2^53-1)` through `+(2^53-1)`. Fractional and exponent-form tokens are forbidden in T0-JCS-1 objects.
6. Logical U64 values MUST be encoded as JSON strings matching canonical unsigned decimal grammar; they MUST NOT be JSON numeric tokens.
7. Financial decimal values (including OHLCV) MUST remain canonical decimal strings under their owning schema, not binary floating-point JSON numbers.
8. Negative zero is noncanonical; its canonical representation is `0`.
9. Unknown critical fields are rejected. Unknown noncritical fields are accepted only where the object schema explicitly permits extension and the fields remain covered by canonical bytes.

This proposal intentionally restricts numeric JSON tokens to safe integers. If a schema later requires a fractional JSON number, it must use a new versioned canonicalization profile or an explicit schema amendment with independent byte vectors; it must not silently broaden T0-JCS-1.

## 4. Required implementation/test changes after approval

- Replace the three fail-closed digest helper bodies with exact NUL-terminated domain bytes from §2.2.
- Add independent SHA-256 known-answer vectors for Trust Policy body, Monotonic Anchor object and Signature Envelope object.
- Preserve the existing Evidence Object vector and add cross-domain separation tests.
- Expand canonicalization tests for the approved numeric grammar, negative zero, exponent/fraction rejection and safe-integer boundaries.
- Recompute all 27 fixture baseline digests if the baseline canonical bytes change; otherwise retain exact baseline identities.
- Run the focused local suite and compile check.
- Request separate owner authorization before dispatching the manual GitHub Actions workflow.

## 5. Non-goals and unchanged boundaries

This proposal does not select a production signature algorithm, key type or library. It does not authorize real keys/signatures, root enrollment, Path A/B, durable Trust Policy/Anchor state, VPS/SSH/runtime, T0 access, custody publication, CI secrets, deployment, trading changes or destructive operations.

The verifier mock remains `MOCK / NOT CRYPTOGRAPHIC`. Independent review remains waived/not performed; no G3 assurance is claimed.

## 6. Owner decision required

The owner must explicitly approve or reject:
- the four exact NUL-terminated domain byte sequences in §2.2;
- the restricted T0-JCS-1 numeric profile in §3.

Until that decision is recorded against an exact proposal blob, the three digest helpers remain BLOCKED and Stage I acceptance remains PARTIAL / NOT PASS.
