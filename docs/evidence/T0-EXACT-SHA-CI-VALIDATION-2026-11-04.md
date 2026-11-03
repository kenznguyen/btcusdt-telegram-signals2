# T0 Exact-SHA CI Validation — 2026-11-04

## Scope
Correct the active-branch T0 CI trigger and align its policy test with the branch allowlist. Execute the T0 regression workflow and integrated P5.4.1 acceptance on the same source SHA. No production runtime or canonical storage actions.

## Source identity
- Repository: `kenznguyen/btcusdt-telegram-signals2`
- Branch: `feature/p5-4-1-post-merge-validation-20261103`
- Exact source SHA: `bb9a032705bc100311d91b1d3f6506173e0784ef`
- Parent SHA: `58aca4d59bf42baec60058fc271937ec483d06c4`
- CI workflow blob: `234d11ab48d26d85ad300e887227b71683d1257c`
- CI policy test blob: `2aba882b93b79d8ed7d510c2ab5cdbe8888d6f92`

## Changes
1. Added the active branch to `.github/workflows/t0-validation.yml` push allowlist.
2. Updated `ci/test_ci_policy.py` to assert both supported branches.
3. Changed the CI policy test step to use `set -euo pipefail`, so a failed unittest command cannot be hidden by `tee` returning success.

## Workflow evidence
### Direct T0 workflow
- Run: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/41739693635
- Conclusion: **SUCCESS**
- Exact head SHA: `bb9a032705bc100311d91b1d3f6506173e0784ef`
- Job: T0 isolated automated contracts — SUCCESS; all 19 substantive steps completed successfully.
- Evidence artifact: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/41739693635/artifacts/13280772186
- Artifact ID: `13280772186`; name: `t0-automated-evidence-41739693635`
- Downloaded ZIP SHA-256 independently recomputed: `8cf99e8c301e124d414c17d0ab63ab1ff92e03bf1f55e1489e4c699ecb99c910` (matches GitHub artifact digest).
- ZIP integrity: `unzip -t` passed.

### Integrated P5.4.1 workflow
- Run: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/41739693660
- Conclusion: **SUCCESS**
- Exact head SHA: `bb9a032705bc100311d91b1d3f6506173e0784ef`
- Jobs: 5/5 SUCCESS — exact source/environment verification; G2 writer routing and consumer regression; G1 Gateway transaction acceptance; T0 full automated regression; common-SHA/evidence publication.
- Artifacts:
  - T0: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/41739693660/artifacts/13280772186
  - G1: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/41739693660/artifacts/13280263110
  - G2: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/41739693660/artifacts/13279553639

## Verified T0 test evidence
All listed invocations returned unittest `OK` on the exact SHA:
- CI policy: 14 tests.
- Market-data core/Gateway: 55 tests.
- Feeder lease: 11 tests.
- Feeder health + health API: 20 tests.
- Feeder lifecycle regression group: 91 tests.
- Atomic fencing regression group: 100 tests.
- Runtime health API regression group: 107 tests.
- SIGKILL recovery regression group: 101 tests.
- Operational contract tests: 11 tests; static audit verdict `T0_OPERATIONAL_CONTRACT_RELEASE_GATE=PASS`.
- Data integrity/candle continuity: 12 tests.

These are overlapping test-suite invocations; **do not sum them as unique test cases**. The SIGKILL audit recorded: process A terminated by SIGKILL; SQLite quick_check=ok; uncommitted batch rows=0; lease generation advanced 1→2; M15 and H1 coverage each 4/4; replacement lease generation valid; RESULT=PASS.

## Verdict
- Active-branch T0 push routing: **PASS**.
- T0 exact-SHA automated regression: **PASS**.
- Integrated P5.4.1 workflow: **PASS (5/5 jobs)**.
- Artifact payload integrity for downloaded T0 ZIP: **PASS** (ZIP valid; locally recomputed digest matches GitHub digest).
- T0 operational source/static release gate: **PASS**.

## Explicit limits
- These are isolated GitHub Actions tests, not Windows PC runtime acceptance.
- Windows canonical SQLite path/integrity: **NOT VERIFIED**.
- Actual Feeder startup/continuous operation, live M15/H1 freshness and exchange connectivity: **NOT VERIFIED / NOT RUN**.
- No canonical DB was opened or modified; no Feeder started; no exchange connection or market-data sync occurred.
- PostgreSQL/TimescaleDB canonical writer is not certified by this run.
- No live trading or real orders. Keep `AI_EXECUTION_ENABLED=false`.

## Next step
Proceed with the separately scoped Windows PC canonical-path and SQLite integrity verification only when that environment is available and the user explicitly authorizes access. Do not start the Feeder or connect an exchange as part of that check.
