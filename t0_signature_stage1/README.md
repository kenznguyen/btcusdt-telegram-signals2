# T0 Signature A2.2 — Stage I Harness

Synthetic-only, offline contract harness for the owner-approved A2.2 Stage I scope.

## Included

- Strict UTF-8 JSON parsing, duplicate-key rejection, canonical byte comparison and UTF-16 code-unit object-key ordering.
- Canonical U64 decimal parsing and 8-byte big-endian encoding.
- Canonical unpadded base64url encoding/decoding, including pad-bit round-trip rejection.
- Domain-separated SHA-256 helpers for all four A2.2 object domains:
  - Evidence Object: `evidence_object_digest`
  - Trust Policy body: `trust_policy_body_digest`
  - Monotonic Anchor object: `anchor_object_digest`
  - Signature Envelope object: `signature_envelope_digest`
- Exact domain-separator bytes are defined by A2.2 §20.1. Each domain is the listed ASCII domain name followed by exactly one NUL octet (`0x00`). The normative hex encodings are:
  - Evidence Object: `54302d45564944454e43452d4f424a4543542d563100`
  - Trust Policy body: `54302d54525553542d504f4c4943592d424f44592d563100`
  - Monotonic Anchor object: `54302d4d4f4e4f544f4e49432d414e43484f522d4f424a4543542d563100`
  - Signature Envelope object: `54302d5349474e41545552452d454e56454c4f50452d4f424a4543542d563100`
- Each helper hashes `domain_bytes || U64BE(byte_length(payload)) || payload`; payload bytes are consumed as supplied and are not reserialized by the digest helper.
- Fixed digest vectors and exact-domain-byte tests cover all four helpers against independent SHA-256 oracles.
- Immutable signature profile ID/version binding across descriptor, statement, envelope, policy and verifier request fixtures.
- Deterministic profile/bootstrap fixture verdict routing and 27 A2.2 negative fixture records.
- Immutable in-memory state snapshots and a `MOCK / NOT CRYPTOGRAPHIC` verifier routing stub.

## Important limits

This package is not a production verifier or signer. It does not select or implement a production signature algorithm, generate/import keys, enroll roots, activate Path A/B, instantiate durable Trust Policy or Anchor state, or access network, credentials, VPS, SQLite or canonical T0.

The current parser deliberately rejects JSON floating-point tokens and restricts JSON integer tokens to the IEEE-754 safe-integer range. The A2.2 Stage I schemas represent logical U64 values as canonical decimal strings. Full numeric-domain coverage beyond these scoped fields is **NOT VERIFIED** and must not be inferred from this harness.

The four digest helpers and their byte encodings are implemented and covered by deterministic test vectors. This establishes helper-level byte/digest behavior only; it does not establish the authenticity, authorization, custody, or operational validity of any object being hashed.

The mock verifier returns only `MOCK_ACCEPTED` or `MOCK_REJECTED`; it never emits `VALID_SIGNATURE` and provides no cryptographic assurance. Signature verification and custody/readback remain **NOT VERIFIED**.

## Run locally

```bash
PYTHONDONTWRITEBYTECODE=1 python -m compileall -q t0_signature_stage1
PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s t0_signature_stage1/tests -p 'test_*.py' -v
```

The dedicated GitHub Actions workflow is manual-only. Its execution requires separate explicit authorization after package review.
