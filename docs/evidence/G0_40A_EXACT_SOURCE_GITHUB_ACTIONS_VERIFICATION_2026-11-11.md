# G0.40-A — Exact-Source GitHub Actions Verification

Date: 2026-11-11 (Asia/Ho_Chi_Minh)  
Repository: `kenznguyen/btcusdt-telegram-signals2`  
Branch: `feature/t0-centralized-data-feeder-p1-20261101`  
Frozen source checkout: `a68d0096f6a04b9ce25591118a47b89660c0965c`  
Workflow commit / run head: `6222102147431c25ba2796ab111240e9e1129c18`  
Verdict: **EXACT-SOURCE FOCUSED VERIFICATION PASS**

## Scope

Following the owner's instruction to run GitHub Actions, one isolated workflow was added on the existing branch:

- Workflow: `.github/workflows/g040-a-exact-source-verification.yml`
- Workflow blob: `ebb0ad4296b8656b62220d3d88be8dc0a8866596`
- Workflow commit: `6222102147431c25ba2796ab111240e9e1129c18`
- Trigger: push of this workflow file on the existing branch; no manual dispatch or unrelated workflow.
- Permissions: `contents: read`; checkout credentials not persisted.
- Checkout pinned to frozen source commit `a68d0096f6a04b9ce25591118a47b89660c0965c`.
- The workflow asserted exact runner and test Git blob IDs before executing checks.

## Exact source identity

- Checkout SHA: `a68d0096f6a04b9ce25591118a47b89660c0965c`
- Runner blob: `784d2b5381fa50007ceba468b8bc81ce045b80c2`
- Test blob: `47363d0a30cd12795fe43b22e0b5a22f934854bf`
- Python: `3.14.4`

All three identity assertions passed.

## Workflow evidence

- Run ID: `43048826022`
- Run URL: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43048826022
- Event: `push`
- Run head SHA: `6222102147431c25ba2796ab111240e9e1129c18`
- Job ID: `130620048937`
- Job: `Verify frozen G0.40-A runner source`
- Job conclusion: `success`
- Identity check: PASS.
- Focused unit tests: **18/18 PASS** (`Ran 18 tests in 0.059s`, `OK`).
- Python compile: `python -m py_compile tools/s1_measurement_runner.py tools/test_s1_measurement_runner.py` — PASS.
- Artifact: `g040-a-exact-source-verification`
- Artifact ID: `13868137683`
- Size: 1,153 bytes.
- GitHub-reported ZIP SHA-256: `fe0d2aefacd12ba6da86bd101333865732b1c652a9ef121e15c6c671495b3247`.
- Expiry: `2026-11-18T15:29:14Z`.
- Repository retention policy capped the artifact to 7 days despite the workflow's requested 14 days.
- Artifact metadata/digest is recorded; artifact payload was not independently downloaded and re-hashed, so independent payload verification is NOT VERIFIED.

## Disposition

- G0.40-A implementation/scope: PASS.
- Exact frozen-source identity: PASS.
- Focused unit tests: PASS, 18/18.
- Focused Python compile: PASS.
- Exact-source GitHub Actions execution: PASS.
- TDD RED execution: NOT VERIFIED; this workflow does not retroactively prove a pre-implementation failing test run.
- Overall G0.40-A focused implementation verification: **PASS**, with the TDD RED evidence limitation above.

No corpus generation or measurement was run as a separate operation. The focused tests exercise the approved runner test suite only. G0.41 measurement remains NOT AUTHORIZED. Numeric D11 ceilings remain OPEN / NOT RATIFIED. Parser/verifier implementation, broader CI, runtime/VPS, external/provider/database/network, T0/T1/T2, market data, model, ledgers, lifecycle and destructive operations were not touched.

T0 remains independent/protected. CORE_LEDGER and AI_LEDGER remain separate. Paper-only posture and `AI_EXECUTION_ENABLED=false` remain unchanged.
