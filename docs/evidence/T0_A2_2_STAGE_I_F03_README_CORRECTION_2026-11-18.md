# T0 A2.2 Stage I — F-03 README Digest Helper Correction

Date: 2026-11-18
Repository: kenznguyen/btcusdt-telegram-signals2
Branch: feature/core-operational-proof-20261112

## Authorization and scope

Owner explicitly approved the F-03 documentation-only correction. Only `t0_signature_stage1/README.md` was changed. No source, tests, workflow, runtime, T0 data, VPS, credentials, exchange or trading files were changed.

## Contract/source comparison

- README previous blob: `883f1adcd866b769c3e094e1c0b5167f278733a5`.
- A2.2 normative specification §20.1 blob: `d9f93bf390d107381b7135c3073aeca0d14894d4`.
- Source `t0_signature_stage1/primitives.py` blob: `91496d70a67d12525b8399b46aeb1318693b17ee`.
- Test `t0_signature_stage1/tests/test_primitives.py` blob: `8e47af0bb98cae6e8501c609c97259ebc5e0c78f`.

§20.1 defines all four domain separators as exact ASCII domain bytes followed by one NUL octet, and supplies normative hex encodings. The source defines all four corresponding constants from those exact hex bytes and implements:
- `evidence_object_digest`
- `trust_policy_body_digest`
- `anchor_object_digest`
- `signature_envelope_digest`

The primitive tests compare all four functions with independent SHA-256 vectors and assert the exact domain bytes. Therefore the prior README statement that three helpers fail closed with `DOMAIN_SEPARATOR_ENCODING_UNRESOLVED` was stale and incorrect.

## README correction

- Lists all four implemented digest helpers.
- Documents the four normative §20.1 hex domain encodings and exactly one NUL octet.
- Documents `domain_bytes || U64BE(byte_length(payload)) || payload`.
- States that fixed digest vectors and exact-byte tests cover all four.
- Removes the obsolete BLOCKED claim.
- Explicitly limits the claim to helper-level digest behavior; it does not imply authenticity, authorization, custody, operational validity, or production cryptography.
- Retains mock-verifier, signature verification and custody/readback limitations as NOT VERIFIED.

## Exact Git evidence

- Documentation commit: `205ecc4c8a8d313cc6f837847a6e322a3fc3b4d7`.
- Updated README blob: `7a36943b9dbfb36a665f93ceea0caf961dac0b74`.
- Compare from pre-change HEAD `11180fdc4eedff5b193fc2e3c9b2e69f242a3c44`: exactly one changed path, `t0_signature_stage1/README.md`; 1 commit ahead, 0 behind.
- Digest helper source and test blobs are unchanged from the previously verified source.
- No tests were rerun because this increment changes documentation only. Existing exact-source test evidence remains: source SHA `64b859e6b5fbbb45e4f764cfc7af22c1e0d57667`, focused tests 28/28 and Stage I package tests 51/51 PASS in an isolated ephemeral Python sandbox. This is not a GitHub Actions run; no workflow run or artifact exists.

## Disposition

| Item | Status |
|---|---|
| F-03 README consistency | PASS |
| Documentation scope isolation | PASS |
| Source/test regression rerun for docs-only change | NOT RUN / NOT REQUIRED |
| Stage I full contract conformance | PARTIAL / NOT VERIFIED |
| Signature cryptographic verification | NOT VERIFIED |
| Custody/readback | NOT VERIFIED |
| Workflow dispatch / CI | NOT RUN / NOT AUTHORIZED |
| Stages II–V | BLOCKED / NOT APPROVED |
| Merge / deployment / trading | NOT AUTHORIZED |

## Next step

Conduct a fresh read-only review of the Stage I package and evidence after the R1–R5 and F-03 corrections. Do not dispatch the manual workflow or proceed to Stages II–V without separate explicit authorization.
