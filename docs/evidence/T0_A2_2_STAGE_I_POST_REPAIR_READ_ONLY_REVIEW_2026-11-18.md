# T0 A2.2 Stage I — Post R1–R5 / F-03 Read-only Review

Date: 2026-11-18
Repository: kenznguyen/btcusdt-telegram-signals2
Branch: feature/core-operational-proof-20261112
Reviewed HEAD: `45e2457af945d9b3ea4c9d02de054798d8b4b47f`

## Scope and method

Read-only static review of the current Stage I package, normative A2.2 specification, README, prior R1–R5 and F-03 reports, and project handoff. No source/test/workflow/runtime/T0/VPS/credential/exchange/trading changes. No tests or workflows were run.

Reviewed exact file blobs:
- `t0_signature_stage1/verdicts.py`: `6f3af6288dec3dc23f01a297b80467aa03515663`
- `t0_signature_stage1/tests/test_verdicts.py`: `2d4a44eecaccce26329c0ed98e30d2fd8a6a6812`
- `t0_signature_stage1/primitives.py`: `91496d70a67d12525b8399b46aeb1318693b17ee`
- `t0_signature_stage1/tests/test_primitives.py`: `8e47af0bb98cae6e8501c609c97259ebc5e0c78f`
- `t0_signature_stage1/README.md`: `7a36943b9dbfb36a665f93ceea0caf961dac0b74`
- A2.2 normative specification: `d9f93bf390d107381b7135c3073aeca0d14894d4`
- R1–R5 report blob: `109c83eb27f92799ec46b008d7de996591b5c974`
- F-03 report blob: `3f9d4ee03680507817953a60173036e0adc1c98f`
- Handoff blob before this report: `891522a9b27f9265cc912c7f7d46f7a93e42323b`

## Findings

### Confirmed PASS at static-review level

- R1: NV-03 models the unchanged A1 historical object and explicit V2 verifier selection; routing is not triggered by a subject label.
- R2: the modeled `signature_profile_id` / `signature_profile_version` bindings are checked across the declared profile locations. This is a fixture/model result, not production verifier assurance.
- R3: zero semantic mutation, compound mutation and state snapshot transition guards are present.
- R5: tests pin all 27 verdict/reason pairs against a hard-coded oracle.
- F-03: README now accurately lists the four implemented §20.1 digest helpers, exact domain bytes and one-NUL encoding, while retaining non-production limitations.
- Primitive implementation statically matches the documented restricted JSON/U64/Base64URL and §20.1 domain-separated digest behavior.

### R4 remains PARTIAL — two fixture assurance gaps to resolve or explicitly accept

1. **Baseline digest is generated from the same in-memory baseline under test.** `fixture_catalog()` calculates `baseline_digest = SHA256(canonicalize(_BASELINES[baseline]))` at runtime. The test checks fixture digest consistency but does not pin independently reviewed expected digests for B0, B0-PF and B-A. A baseline edit can therefore change both fixture and generated digest together. A2.2 §18.4 requires recording the complete baseline fixture digest and schema version. Current implementation records a digest but does not independently pin the baseline identity. This is a hardening gap; whether an independently pinned digest is mandatory should be confirmed against the approved Stage I acceptance criteria before changing behavior.

2. **Trust-root state terminology is ambiguous.** B0 initializes `state_snapshot.trust_roots` to `["synthetic-root-fingerprint"]`, while A2.2 §18.1/§18.4 says B0 has no enrolled bootstrap root and any synthetic checkpoint-signer trust material must be test-only and separate from bootstrap-root enrollment. The fixture does not label the value as signer-only material or explicitly model an empty bootstrap-root enrollment set. This can be misread as a root already enrolled. Clarify the state schema so signer test material and bootstrap-root enrollment are distinct, without implying any actual enrollment.

The existing R4 `signature` and `custody_readback` dimensions correctly remain `NOT_VERIFIED`; the mock verifier is not cryptographic evidence. Do not attempt to turn these into PASS using synthetic/mock assertions.

### Handoff consistency

The handoff's opening “Latest verified branch HEAD” still reports `d2edcf7706f36df2712768574269d69ac5b742a0`, while the current branch ref at review time is `45e2457af945d9b3ea4c9d02de054798d8b4b47f`. Its integration snapshot is historical and should be labelled as such rather than silently treated as current.

## Disposition

| Item | Status |
|---|---|
| R1 | PASS — static review |
| R2 | PASS — modeled bindings only |
| R3 | PASS — static review |
| R4 | PARTIAL — baseline digest not independently pinned; signer/bootstrap trust-state distinction ambiguous; signature and custody/readback NOT VERIFIED |
| R5 | PASS — oracle/test structure |
| F-03 | PASS |
| Stage I full contract conformance | PARTIAL / NOT VERIFIED |
| Tests on reviewed HEAD | NOT RUN |
| GitHub Actions / artifact | NOT RUN |
| Production crypto / bootstrap enrollment / custody | NOT VERIFIED / NOT AUTHORIZED |
| Stages II–V, workflow dispatch, merge, deployment, trading | BLOCKED / NOT AUTHORIZED |

## Recommended next action

A narrowly scoped R4 hardening proposal should first define:
- fixed, independently reviewed expected baseline digests for B0, B0-PF and B-A, if required by the approved acceptance contract;
- explicit separate fixture fields for test signer trust material and the empty bootstrap-root enrollment state.

Before modifying `verdicts.py` and `tests/test_verdicts.py`, verify that the owner's existing R1–R5 authorization covers these additional R4 changes; otherwise request separate approval. Keep all work mock-only/offline and within the two already authorized files. Do not change README, workflow, runtime, T0 data or any production trust/crypto path.

No new test evidence or workflow artifact was created by this review.
