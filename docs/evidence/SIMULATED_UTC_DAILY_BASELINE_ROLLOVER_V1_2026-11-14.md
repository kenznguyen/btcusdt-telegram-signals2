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
- RED execution evidence: **OBSERVED** in GitHub Actions; the initial rollover tests exposed a bool/dict contract mismatch.
- GREEN / integration test execution: **PASS WITHIN CI TEST SCOPE** at final source SHA `88ff9d51b845ca674a547bf27d479358a380bdcb`.
- Paper Ledger T1 Compatibility run [43606676090](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43606676090), job `132482704667`: **SUCCESS**, 140/140 tests, exact checkout SHA `88ff9d51b845ca674a547bf27d479358a380bdcb`.
- Simulated Capital V1 Contract run [43606676141](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43606676141), job `132482704933`: **SUCCESS**, 28/28 tests, exact checkout SHA `88ff9d51b845ca674a547bf27d479358a380bdcb`.
- The 140-test Paper Ledger suite includes 13 Dual Ledger Bootstrap contract tests; these are disposable test contracts, not Bootstrap activation or runtime evidence.
- Earlier failing runs were retained: `43605410402`, `43606530035`, `43606568914`, and `43606634971`; each exposed a distinct issue that was corrected before the final passing runs.
- Artifacts: **NONE** for both final runs.
- Funded-account Bootstrap/funding/cutover compatibility: **PASS WITHIN THE 140-TEST SUITE ONLY**; no operational/funded DB or Bootstrap runtime was accessed.
- Overall PAPER Ledger readiness: **BLOCKED / NOT VERIFIED** because the complete runtime Shared Risk Engine admission, including contract-bound 1% per-order margin enforcement, remains unimplemented/unverified.
- Bootstrap activation, Runner, VPS, operational DB, exchange access and real trading: **NOT AUTHORIZED**.

The six new tests are committed but are not claimed as passing. CI must check out the exact implementation source HEAD above before any PASS status is assigned.

## Safety boundaries

All intended test coverage is for disposable temporary SQLite databases. No operational database, VPS, T0, exchange credentials, deployment, Bootstrap runtime, Runner, AI execution, live order or real trade was used or authorized.

## Next step

Obtain and inspect a GitHub Actions run for the exact implementation HEAD `d27c8dbf7497c49cf7c14a45248dfbe8bb2a7b61`; fix failures test-first; then verify funded-account compatibility and document exact workflow/job/artifact evidence. Do not activate Bootstrap or Runner.

 
## 2026-11-14 — CI failure analysis and final verification

- CI was queried through the repository Actions API, including push-triggered runs, resolving the earlier limitation of the PR-only commit-run wrapper.
- Initial exact-source run 43605410402 checked out 9365d3669a0a2a7c52295b58b1a472fe1972d8d0 and failed 7 tests because verify_simulated_equity_origin() returns a boolean while rollover code indexed it as a mapping.
- The origin anchor is now read from the persisted, already-validated paper_simulated_equity_origin row. A second issue was exposed: the immutable origin validator assumed the current risk baseline must remain at initial 100 USDT. It now validates a contiguous later risk day against the existence of the corresponding rollover event, while the dedicated daily-baseline verifier remains responsible for validating the event hash chain and exact baseline value.
- A further test exposed validator ordering: tampered event content was being reported as generic equity risk-state corruption before the dedicated provenance verifier could report SIMULATED_DAILY_BASELINE_PROVENANCE_INVALID. The generic origin validator now leaves event-content integrity to the dedicated provenance verifier.
- Relevant intermediate failing runs: 43605410402, 43606530035, 43606568914, 43606634971. Failures were not hidden or marked as passes.
- Final tested source HEAD: 88ff9d51b845ca674a547bf27d479358a380bdcb.
- Final source blobs: paper_execution/simulated_daily_baseline.py bf3a0bb56d8e12e26f529b258d430dd35c7f88c3; paper_execution/simulated_equity.py 1219723ffca0de4237032061de4b46d0bacf7a08; paper_execution/account_equity.py 701bcc25e8c5850fdb9052fd7481996debb2e019; paper_execution/ledger.py a9839b979f863b06ba056c4c7aa3cca2d86a9cc2; paper_execution/test_simulated_equity.py e2aacddc899102a89f8aee19337ecaf35465513a.
- Workflow blobs: .github/workflows/paper-ledger-t1-compatibility.yml aa071bd626c289befff8a484a4efc99ef5db5672; .github/workflows/simulated-capital-v1-contract.yml d2d5edb43c41e946d7a2e168a724e17f1c9037de. The Simulated Capital workflow now includes the rollover module in its trigger and compile list.
- Paper Ledger T1 Compatibility run 43606676090, job 132482704667: SUCCESS, 140/140 tests, exact source SHA 88ff9d51b845ca674a547bf27d479358a380bdcb, no artifact.
- Simulated Capital V1 Contract run 43606676141, job 132482704933: SUCCESS, 28/28 tests, exact source SHA 88ff9d51b845ca674a547bf27d479358a380bdcb, no artifact.
- The 140-test suite includes 13 Dual Ledger Bootstrap contract tests and risk-control tests. This establishes compatibility within disposable CI fixtures only; it does not authorize or establish operational Bootstrap readiness.
- Status: rollover implementation and dedicated integration tests **PASS WITHIN CI TEST SCOPE**; funded Bootstrap contract compatibility **PASS WITHIN THE SAME TEST SCOPE**; runtime Shared Risk Engine enforcement and contract-bound 1% per-order margin admission **NOT VERIFIED / NOT IMPLEMENTED**; overall PAPER Ledger readiness **BLOCKED / NOT VERIFIED**.
- No operational DB, VPS, T0, exchange credentials, deployment, Bootstrap runtime, Runner, AI execution, live order or real trading was used or authorized.
