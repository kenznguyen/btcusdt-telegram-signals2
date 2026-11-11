# G0.39-B — Exact-source verification results

Date: 2026-11-11  
Repository: `kenznguyen/btcusdt-telegram-signals2`  
Branch: `feature/t0-centralized-data-feeder-p1-20261101`  
Owner authorization: explicit approval of Cách 2 — isolated GitHub Actions exact-source verification  
Verdict: **PASS — exact approved source checkout, 24/24 focused tests, compile check, and artifact upload succeeded**

## 1. Scope

This gate verifies only the already-approved G0.39-A implementation:
- checkout exact commit `30fa54e6a24e95a275c4fbfd27170371e1d56d78`;
- assert exact harness and test blob identities;
- run `python -m unittest tools.test_s1_measurement_harness -v`;
- run `python -m py_compile tools/s1_measurement_harness.py tools/test_s1_measurement_harness.py`;
- upload identity and command logs as a GitHub Actions artifact.

No corpus generation/measurement, numeric D11 ceiling selection, parser/verifier production implementation, dependency change, runtime/VPS/database/network-to-provider access, T0/T1/T2 modification, ledger change or destructive operation was performed.

## 2. Workflow source

- Workflow: `.github/workflows/g039-b-exact-source-verification.yml`
- Workflow blob SHA: `1e6241911845762c8770f7e59e23e21d4d51b0a8`
- Workflow commit: `bae7430ca68fd0ab35806dd7f00d133166c53699`
- Workflow is triggered by a push that changes only this workflow path on the existing project branch.
- It uses read-only repository permissions, pinned checkout/upload-artifact action revisions, disables persisted checkout credentials, and has a five-minute job timeout.
- It always checks out the frozen target SHA rather than the workflow-triggering commit.

## 3. Exact-source identity

All immutable identity assertions passed:
- Checkout commit: `30fa54e6a24e95a275c4fbfd27170371e1d56d78`
- Harness blob: `0f713a1cc87f4c0c355d4488f1cf6af4d8f08d98`
- Test blob: `ff5e3c9d584e13948fc4265f9ca261e697fa9da6`
- Python: `3.14.4`

## 4. GitHub Actions execution

- Workflow run ID: `43046949518`
- Run URL: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43046949518
- Triggering workflow commit / run head SHA: `bae7430ca68fd0ab35806dd7f00d133166c53699`
- Event: `push`
- Job ID: `130613317796`
- Job conclusion: `success`
- Checkout step: SUCCESS
- Immutable source identity step: SUCCESS
- Focused unit test step: SUCCESS
- Focused compile step: SUCCESS
- Artifact upload step: SUCCESS

### Test output

`Ran 24 tests in 0.124s`  
`OK`

The compile command exited successfully. GitHub Actions step status is SUCCESS.

## 5. Artifact

- Artifact name: `g039-b-exact-source-verification`
- Artifact ID: `13867028275`
- Size: 1,338 bytes
- SHA-256: `554a0bb3afdb00f8f2319471873a128676f7c64549c1c8f9f382170496853d62`
- Expiry reported by GitHub: 2026-11-18T15:17:56Z
- Contents: verification identity, focused unit-test log, compile log. No corpus or raw fixture payloads.

## 6. Reconciliation with earlier G0.39-A evidence

This run resolves the previous exact-source attribution gap. The 24/24 test and compile results now apply to the exact GitHub commit and exact source/test blobs identified above, not merely to the earlier isolated authoring workspace.

G0.39-A implementation verification is therefore **PASS for its authorized implementation + focused test/compile scope**. This does not mean the S1 corpus measurement has been run or that D11 numeric limits have been ratified.

The earlier DNS-blocked checkout attempt remains historically accurate but is superseded by this successful GitHub Actions verification.

## 7. Final disposition

| Item | Status |
|---|---|
| G0.39-A narrow implementation scope | PASS |
| Exact commit/blob checkout assertions | PASS |
| Focused tests | 24/24 PASS |
| Focused compile | PASS |
| Workflow job | SUCCESS |
| Artifact upload | PASS |
| G0.39-B | **PASS** |
| G0.40 corpus generation/measurement | NOT AUTHORIZED |
| Numeric D11 ceilings | OPEN / NOT RATIFIED |
| Parser/verifier production implementation | NOT AUTHORIZED |
| CI beyond this isolated workflow | NOT AUTHORIZED |
| Runtime/VPS/T0/T1/T2/ledger/destructive actions | NOT AUTHORIZED |

Next gate: prepare a separate G0.40 owner decision package. No corpus generation or measurement is permitted until that distinct scope is explicitly approved.

T0 remains independent/protected. CORE_LEDGER and AI_LEDGER remain separate. Paper-only posture and `AI_EXECUTION_ENABLED=false` remain unchanged.
