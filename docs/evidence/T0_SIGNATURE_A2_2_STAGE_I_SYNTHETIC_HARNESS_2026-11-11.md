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

Contract-only correction proposal is now recorded at `docs/evidence/T0_SIGNATURE_A2_2_STAGE_I_CONTRACT_AMBIGUITY_PROPOSAL_2026-11-11.md` (blob `37bff74053ddc1034e09f40d9cc3bf558588e897`, commit `d5695ed7ac752d8e5570354a1389ef9c8403033c`). The proposal is NOT OWNER-APPROVED and does not amend A2.2. Obtain explicit owner approval or rejection of its exact domain bytes and T0-JCS-1 numeric grammar before changing the three blocked digest helpers. Do not dispatch the workflow until this blocker is resolved and workflow execution is separately authorized.


---

## Post-approval contract clarification and implementation delta (2026-11-11)

This section supersedes the earlier "Next step" disposition above. The proposal was subsequently owner-approved, and the governing A2.2 contract plus isolated Stage I code/tests were updated.

### Owner decision and governing contract
- Approved proposal blob: `37bff74053ddc1034e09f40d9cc3bf558588e897`.
- Normative amendment: A2.2 §20 in `docs/architecture/T0_SIGNATURE_TRUST_POLICY_MONOTONIC_ANCHOR_AMENDMENT_A2_2_2026-11-11.md`.
- Amendment commit: `e1cb154755f127587e5a868c3ac9423ecf9bf15f`; blob: `3f4cb1fc36a58bc6ccaa26872360b8ee2961270b`.
- The amendment specifies four exact ASCII-plus-NUL domain byte strings as hex and a restricted T0-JCS-1 numeric grammar. It preserves A1 §14.2's stricter decimal-string encoding for logical integer fields; A2.2's fixed profile-version discriminator remains integer `2`.

### TDD implementation delta
- RED test-first commit: `f1bc86d25b7ca773848c0ff5093e887e389f9a88`; test blob: `8e47af0bb98cae6e8501c609c97259ebc5e0c78f`.
- GREEN implementation commit: `8af2aeca99ddcab6d93133c5a689276582e4b358`; `primitives.py` blob: `91496d70a67d12525b8399b46aeb1318693b17ee`.
- The three former fail-closed digest helpers now use the exact approved domain constants. The Evidence Object helper was also normalized to the same explicit hex constant.
- Primitive tests now contain 23 test methods; fixture/verdict tests contain 11; expected total is **34 tests**.
- New test coverage includes four independent fixed SHA-256 vectors, four exact domain-hex assertions, cross-domain separation, safe-integer boundaries, overflow, negative-zero, fractional and exponent-form rejection.
- A separate Python smoke check of the four fixed digest vectors and numeric-token cases passed: 4/4 digest vectors, 4 distinct domains, 2 safe-integer boundaries accepted and 6 invalid numeric forms rejected. This is a spot-check, not execution of the repository test suite.

### Verification status after the change
- Repository unittest suite: **NOT RUN**. A fresh local clone was attempted but GitHub DNS resolution failed; no claim of a full local test result is made.
- `compileall`: **NOT RUN** after the latest source changes.
- GitHub Actions workflow: **NOT DISPATCHED**. The workflow is manual-only and dispatch remains outside the approved scope.
- Workflow run/job IDs and artifacts: **NONE**.
- Python 3.12 parity: **NOT VERIFIED**.
- Current disposition: **CONTRACT CLARIFICATION APPLIED / IMPLEMENTATION COMMITTED / TEST EXECUTION NOT VERIFIED**. Do not promote Stage I acceptance to PASS until the exact 34-test suite and compile check run successfully on the committed source, preferably through the dedicated workflow after separate dispatch authorization.

### Scope and boundaries
No production cryptography, real keys, trust-root enrollment, Path A/B activation, durable policy/anchor state, VPS/SSH/runtime, canonical T0, custody publication, CI secrets, deployment, trading or destructive operation was changed. Independent review remains waived/not performed; G3 is not established.
