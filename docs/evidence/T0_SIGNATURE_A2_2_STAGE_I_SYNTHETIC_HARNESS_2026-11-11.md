# T0 Signature A2.2 Stage I — Synthetic Harness Increment

Date: 2026-11-11  
Repository: `kenznguyen/btcusdt-telegram-signals2`  
Branch: `feature/t0-centralized-data-feeder-p1-20261101`  
Governing A2.2 blob: `41d41cd23f73a6e552b9ceca5ebbb39c46934e7d`  
Owner Stage I approval blob: `04c6deb7b04c6cef10a8e696c9bd63af69264c2a`

## Scope implemented

Added an isolated `t0_signature_stage1/` package and tests, separate from `synthetic_evidence/`.

- Strict UTF-8 JSON parsing, duplicate-key rejection, BOM rejection, canonical byte comparison and UTF-16 code-unit key ordering.
- Canonical unsigned decimal U64 parsing and U64BE encoding.
- Canonical unpadded base64url encode/decode with round-trip rejection of noncanonical pad bits.
- Evidence Object domain-separated SHA-256 helper.
- Immutable profile ID/version binding across descriptor, statement, envelope, policy and verifier request.
- Deterministic Stage I profile/bootstrap reason routing, 27 A2.2 negative fixture records, exact named baseline digest, one mutation path/value, exact expected verdict/reason and unchanged in-memory state assertions.
- Test-only verifier routing stub explicitly labelled `MOCK / NOT CRYPTOGRAPHIC`; it emits only `MOCK_ACCEPTED` / `MOCK_REJECTED`.

## Source commits and blobs

All seven package/test files were read back from the active branch. Local Git blob-header SHA-1 calculations match the GitHub blob SHAs.

| File | Commit | Blob SHA |
|---|---|---|
| `t0_signature_stage1/__init__.py` | `bca516482c52063967e293b84526362dd514e648` | `de3841295124c36cd366a4ff138c42ada303b688` |
| `t0_signature_stage1/README.md` | `ef780085be57f2e0acd3bd64d7327e6acdec7370` | `883f1adcd866b769c3e094e1c0b5167f278733a5` |
| `t0_signature_stage1/primitives.py` | `655df14f39f5cccc9c9c3487871e2505c5cb9697` | `a8ff4b274bd516aa26782ee44d0344d50321a883` |
| `t0_signature_stage1/verdicts.py` | `b72d8fc610a5361f78c24cf1f1a09cb06d9f0444` | `600c49865279e03ef28466f267a6bf0b57176aa1` |
| `t0_signature_stage1/tests/__init__.py` | `75eb3431441959f02d1b7481c957d5fc33bc4e55` | `4beea581f1e3cd514e6a085290f7f4dffb47aea9` |
| `t0_signature_stage1/tests/test_primitives.py` | `e2837323f959f7a3e3fdc7634963bfe57ae4dab0` | `025e601ed6cace778b18d5a7e5f923d7d6fa8964` |
| `t0_signature_stage1/tests/test_verdicts.py` | `40b338336fcad59f058fac320bffe6182b4485f8` | `d37ab48b0455d788bd5c87398281420a7aa121d8` |

Branch HEAD after source/test commits: `40b338336fcad59f058fac320bffe6182b4485f8`.

## TDD and local verification

Initial RED: before implementation modules existed, both focused test modules failed import with `ModuleNotFoundError`.  
GREEN after implementation and final source synchronization:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s t0_signature_stage1/tests -p 'test_*.py' -v
```

Result: **32 tests PASS**, 0 failures, 0 errors, 0 skipped.

Compile check:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m compileall -q t0_signature_stage1
```

Result: **PASS**.

Local runtime used Python **3.13.5** in an isolated temporary working directory containing byte-for-byte source matching the committed Git blobs. Python 3.12 parity is **NOT VERIFIED**; Python 3.12 was not installed in the local environment.

## Contract blockers discovered — fail closed

The source documents do not use one unambiguous byte spelling for domain separators:

- A1 Evidence Object digest uses `T0-EVIDENCE-OBJECT-V1\0` (single backslash before zero).
- A1 Trust Policy body digest uses `T0-TRUST-POLICY-BODY-V1\\0` (two backslashes before zero in the source document).
- A1 Monotonic Anchor object digest uses `T0-MONOTONIC-ANCHOR-OBJECT-V1\\0`.
- A2.2 Signature Envelope object digest uses `T0-SIGNATURE-ENVELOPE-OBJECT-V1\\0`.

Interpreting the latter three as NUL escapes or literal backslash-plus-zero changes the digest preimage. Stage I does not guess. The three corresponding helpers currently raise `DOMAIN_SEPARATOR_ENCODING_UNRESOLVED`.

Additional parser limit: JSON floating-point tokens are rejected and JSON integer tokens are restricted to the IEEE-754 safe-integer range. Logical U64 values use decimal strings per contract. Broader T0-JCS-1 numeric-domain conformance is **NOT VERIFIED**.

Consequently this increment is **PARTIAL PASS / STAGE I ACCEPTANCE BLOCKED**, not full Stage I PASS. The passing 32-test result proves only the implemented synthetic subset and explicit fail-closed behavior.

## Self-review

- Correctness: primitive vectors and fixture result/reason assertions pass; no cryptographic validity is claimed.
- Architecture: isolated package, standard library only, no imports for network/database/process integration.
- Security: no keys, credentials, external network, production filesystem, VPS, SQLite or canonical T0 access.
- State: fixture evaluator returns the same frozen in-memory state snapshot; no state writer exists.
- Residual: domain-separator byte spelling and broader JCS numeric subset require contract clarification.
- Review type: same-session self-review only. Independent review remains waived/not performed; G3 is not established.

## CI / workflow status

- Dedicated workflow: `.github/workflows/t0-signature-a2-2-stage-i.yml`, blob `90560d0257ca6cf52e6626616769a0abab8ce10b`.
- Workflow dispatch: **NOT RUN**; the owner approval of Stage I implementation and workflow authoring does not itself authorize workflow execution.
- Workflow run / job IDs / artifacts: **NONE**.
- YAML lint / GitHub Actions validation: **NOT RUN**.

## Unchanged boundaries

No production cryptography, real key generation/import, signing/verification, trust-root enrollment, Path A/B activation, durable Trust Policy/Anchor state, VPS, SSH, systemd, Feeder, API, SQLite, canonical T0, custody publication, CI secrets, deployment, trading strategy, ledger, Shared Risk Engine, Kill Switch, order execution or destructive operation was changed or exercised. Paper-only posture and `AI_EXECUTION_ENABLED=false` remain unchanged.

## Next step

Obtain an explicit owner-approved contract correction defining the exact domain-separator byte sequences and resolving the T0-JCS-1 numeric subset. Then implement the three blocked digest helpers and expand canonicalization vectors. Do not dispatch the workflow until this blocker is resolved and workflow execution is separately authorized.
