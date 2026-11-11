# T0 Signature A2.2 — Stage I Harness

Synthetic-only, offline contract harness for the owner-approved A2.2 Stage I scope.

## Included

- Strict UTF-8 JSON parsing, duplicate-key rejection, canonical byte comparison and UTF-16 code-unit object-key ordering.
- Canonical U64 decimal parsing and 8-byte big-endian encoding.
- Canonical unpadded base64url encoding/decoding, including pad-bit round-trip rejection.
- Domain-separated SHA-256 helper for the Evidence Object domain, whose NUL escape is unambiguous in the source contract.
- Trust Policy body, Monotonic Anchor envelope and A2.2 signature envelope digest helpers currently fail closed with `DOMAIN_SEPARATOR_ENCODING_UNRESOLVED`; the source documents use `\\0` for these domains, which is ambiguous against the single-backslash `\0` form used by the Evidence Object domain.
- Immutable signature profile ID/version binding across descriptor, statement, envelope, policy and verifier request fixtures.
- Deterministic profile/bootstrap fixture verdict routing and 27 A2.2 negative fixture records.
- Immutable in-memory state snapshots and a `MOCK / NOT CRYPTOGRAPHIC` verifier routing stub.

## Important limits

This package is not a production verifier or signer. It does not select or implement a signature algorithm, generate/import keys, enroll roots, activate Path A/B, instantiate durable Trust Policy or Anchor state, or access network, credentials, VPS, SQLite or canonical T0.

The current parser deliberately rejects JSON floating-point tokens and restricts JSON integer tokens to the IEEE-754 safe-integer range. The A2.2 Stage I schemas represent logical U64 values as canonical decimal strings. Full numeric-domain coverage beyond these scoped fields is **NOT VERIFIED** and must not be inferred from this harness. The three ambiguous digest domains are **BLOCKED** pending an exact-byte contract correction; no NUL-versus-literal-backslash interpretation is assumed.

The mock verifier returns only `MOCK_ACCEPTED` or `MOCK_REJECTED`; it never emits `VALID_SIGNATURE` and provides no cryptographic assurance.

## Run locally

```bash
PYTHONDONTWRITEBYTECODE=1 python -m compileall -q t0_signature_stage1
PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s t0_signature_stage1/tests -p 'test_*.py' -v
```

The dedicated GitHub Actions workflow is manual-only. Its execution requires separate explicit authorization after package review.
