# SIMULATED-only UTC Daily Baseline Rollover V1 — implementation record

Date: 2026-11-14  
Branch: `feature/core-operational-proof-20261112`  
Implementation HEAD: `9365d3669a0a2a7c52295b58b1a472fe1972d8d0`  
Base handoff HEAD: `8032ff1303e9e7ae6825149fb020b5cbdd43f208`

## Owner-approved contract

Owner accepted the rule that a new SIMULATED UTC daily baseline is the last confirmed account equity mark from the immediately preceding UTC day. Rollover is rejected if the previous UTC day has no confirmed mark or if one or more UTC days were skipped.

The implementation is additive and SIMULATED-only. It does not create funding events, funding coverage, or funded-account cutover evidence. HWM and initial simulated capital remain unchanged by rollover.

## Changes committed

- `paper_execution/simulated_daily_baseline.py`: additive migration v11, immutable append-only event table, hash-linked provenance from the immutable simulated equity-origin record, and read-time verification.
- `paper_execution/account_equity.py`: account mark path validates existing provenance, admits only a one-day contiguous rollover with a confirmed previous-day mark, records the baseline event and updates risk state inside the same `BEGIN IMMEDIATE` transaction.
- `paper_execution/ledger.py`: applies and requires migration v11; verifies the provenance chain in read-only account risk snapshots.
- `paper_execution/test_simulated_equity.py`: adds six isolated SQLite integration tests for successful rollover, skipped-day rejection, atomic rollback, tamper detection, restart/multi-day chain continuity, and missing prior-day mark rejection.

## Test-first and source history

Test specification commit (preceded implementation): `ca7e1ded65c037750682c7c9908ac5f4e7b987c7`.

Subsequent implementation/fix commits:
- `920c279d66f352d342b9bca3cf2542bc711721fa`
- `1d8a4c28942dc571e82ad7b1d9550519fdb194a4`
- `8b4568afce57592f86cb64db266f0e79a9a7a05f`
- `f052088666c50c9a13005d0ab9df298947fc4818`
- `80beedf01086611fa1aaae0ff06dc4011abbb64d`
- `e6378f8fba06b7fbecb742ae2470cef7a8498291`
- `d27c8dbf7497c49cf7c14a45248dfbe8bb2a7b61`
- `3b29a9a3cf48d0d422b4030230a25dd282718267` (removed superseded pre-rollover fail-closed test)

Exact final source blob SHAs:
- `paper_execution/simulated_daily_baseline.py`: `19cd99cb55b03aa178d09b48b7b8348bae035d1e`
- `paper_execution/account_equity.py`: `701bcc25e8c5850fdb9052fd7481996debb2e019`
- `paper_execution/ledger.py`: `a9839b979f863b06ba056c4c7aa3cca2d86a9cc2`
- `paper_execution/test_simulated_equity.py`: `e2aacddc899102a89f8aee19337ecaf35465513a`
- `.github/workflows/paper-ledger-t1-compatibility.yml`: `aa071bd626c289befff8a484a4efc99ef5db5672`

## Verification status

- Contract and code changes: **COMMITTED**.
- Test specification: **COMMITTED BEFORE IMPLEMENTATION**.
- RED execution evidence: **NOT VERIFIED**.
- GREEN / integration test execution: **NOT VERIFIED**.
- GitHub Actions workflow run ID, job ID, and artifacts: **NOT VERIFIED / NONE RECORDED**. The available workflow-run lookup did not return push-triggered runs; no run ID is inferred.
- Funded-account Bootstrap/funding/cutover regression after this change: **NOT VERIFIED**.
- Overall PAPER Ledger readiness: **BLOCKED / NOT VERIFIED**.
- Bootstrap activation, Runner, VPS, operational DB, exchange access and real trading: **NOT AUTHORIZED**.

The six new tests are committed but are not claimed as passing. CI must check out the exact implementation source HEAD above before any PASS status is assigned.

## Safety boundaries

All intended test coverage is for disposable temporary SQLite databases. No operational database, VPS, T0, exchange credentials, deployment, Bootstrap runtime, Runner, AI execution, live order or real trade was used or authorized.

## Next step

Obtain and inspect a GitHub Actions run for the exact implementation HEAD `d27c8dbf7497c49cf7c14a45248dfbe8bb2a7b61`; fix failures test-first; then verify funded-account compatibility and document exact workflow/job/artifact evidence. Do not activate Bootstrap or Runner.
