# AI Strategy Contract and TDD RED Preparation — 2026-11-11

## Scope and owner approval

The owner approved recording the independent AI Strategy contract and preparing test-only RED work. This increment is limited to design documentation and tests. It does not include production implementation.

Reviewed source baseline: `6ef0d7456b2791fae73bfea8855ee30482774673`.

## Changes

1. Added `docs/architecture/AI_STRATEGY_CONTRACT.md`.
   - Independent AI signal producer; Core remains RSI + ADX + Smart DCA.
   - Calibrated confidence plus model/calibration/dataset provenance.
   - AI leverage mapping in [1x, 3x], based on required versioned `C_min`.
   - AI ENTRY/DCA sizing from reconciled Account Equity, 1% margin budget, admitted leverage, execution limit price and lot-step floor.
   - AI ledger isolation and common Shared Risk Engine/Kill Switch authority.
   - Explicit approval boundary: no GREEN implementation, numerical `C_min`, calibration training, migration, backtest acceptance, runtime, VPS, deployment or live trading.

2. Added `pipeline/test_ai_strategy_contract_red.py` with five focused test methods in `pipeline/test_ai_strategy_contract_red.py` covering:
   - Missing calibrated confidence.
   - Confidence bounds and non-finite values.
   - Missing calibration provenance.
   - AI ledger leverage supplied as an admitted policy snapshot, independent of generic `LEVERAGE`.
   - Equity-based sizing and fail-closed missing/non-positive equity.

## Exact Git evidence

- Contract documentation commit: `2f498b33953cb3ecf2c66c242000e9e0de2048ce`.
- Initial test-only commit: `e9b39ad8d2492f8e27c1ad0ecf54e168cbbd8bd7`.
- Follow-up test refinement commit: `d0f1b014463e6ad1eff36425a18411233c484ba2`.
- E2E RED test commit: `550a529c2a726f82911602aee207f0df32c78eb9`.
- Latest known source/test SHA for this increment: `550a529c2a726f82911602aee207f0df32c78eb9`.
- Branch: `feature/t0-centralized-data-feeder-p1-20261101`.
- GitHub commit status query for initial test commit returned no status checks. No workflow run or artifact has been verified for the final test SHA.

## Verification and disposition

- Contract recorded: **PASS — documentation only**.
- Test source committed: **PASS — test authoring only**.
- RED execution: **NOT VERIFIED**. The execution environment could not resolve `github.com` for a shallow clone; no local checkout was available. No test result is claimed.
- Syntax/runtime test status: **NOT VERIFIED**.
- AI implementation: **NOT AUTHORIZED / NOT STARTED**.
- Calibration artifact, numerical `C_min`, OOS evidence and minimum calibration sample/period thresholds: **NOT DEFINED / NOT VERIFIED**.
- E2E AI BUY while Core WAIT → AI ledger only → Shared Risk Engine rejection test: added to `paper_execution/test_dual_strategy_api_red.py` at exact SHA `550a529c2a726f82911602aee207f0df32c78eb9`. It asserts the AI order is rejected while account risk is unready and neither Core state nor Core orders change.
- No production source, Core strategy behavior, DB/schema, T0, T1, T2 runtime, VPS, credentials, deployment or exchange state changed.

## Next step

Run the focused RED test file in the repository's GitHub Actions test environment against exact SHA `d0f1b014463e6ad1eff36425a18411233c484ba2`. Inspect failures and correct test fixtures/specification only. Then add the missing E2E ownership/risk-denial RED test. Do not implement GREEN behavior until a separate owner approval is recorded.
