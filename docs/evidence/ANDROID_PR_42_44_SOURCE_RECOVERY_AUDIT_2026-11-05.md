# Android PR #42–44 Source Recovery Audit — 2026-11-05

## Scope
Audit closed, unmerged Android PRs #42, #43 and #44 against the current `feature/android-btcusdt-live-alerts` branch. Read-only source inspection only. No branch deletion, cherry-pick, source modification, workflow execution or PR state change.

Repository: `kenznguyen/btcusdt-telegram-signals2`

## Exact references
- PR #42 head: `2c380d31adef96d4f7b38442318b796e5d7a813e`; base: `4f736e6df2a907cf1c423cca58d98948f6642713`.
- PR #43 head: `1655a92ddf9a111c1e895e6853a0bc2a54177018`; base: PR #42 head.
- PR #44 head: `32d60728c42aebe9a7c02bcf92f75e4fa8e4d53c`; base: PR #43 head.
- Current Android branch ref observed in PR comparisons: `feature/android-btcusdt-live-alerts`, SHA `4bb768ad55a89e9ad1e4a65b32bdd7ebd7ef48d4`.
- Current fetched source blob SHAs: `OrderBookEngine.kt` `ecc252ae36e990c5ada6e9de78f104314e436122`; `StrategyEngine.kt` `e77902cae14870ecff937d5dbb4c099dd1cd3b09`; `MarketEngine.kt` `b54e16e381dd46b57fe3cd6eb397f80ee37d01b2`; `CompleteDashboard.kt` `6c16d898a234b5dca2a1e71b1cfa652e5048c35b`; `StrategyEngineTest.kt` `eaddae3b7bdf2e4886bb46be41f5b89133e8f47b`.

## Findings

### PR #42 — Order Book snapshot sequence validation
- Historical head contains `OrderBookSequence.kt` (blob SHA `ae8ea9263a1c3728664b69216033c49aea0de48a`) and the associated `OrderBookSequenceTest.kt`.
- The helper source was not found at the same paths on the current Android branch.
- Current `OrderBookEngine.kt` was inspected; no separate `OrderBookSequence` helper or corresponding sequence-validation abstraction was found by source marker inspection.
- Classification: **MISSING from current branch (source-level)**. Whether equivalent inline behavior exists elsewhere is **NOT VERIFIED**. Do not restore blindly; first assess current snapshot bridge and `pu` continuity implementation and add tests.

### PR #43 — Signal-frequency diagnostics
- Historical head contains diagnostic logic in `StrategyEngine.kt` (blob SHA `6aef0c0364f0f86bf72df66c00f37d2cba513f75`) and technical-candidate diagnostic references in `StrategyMonitorService.kt` (blob SHA `a48e82971ca760d47676b13949d8947c6fdb2b29`).
- Current `StrategyEngine.kt` (blob SHA `e77902cae14870ecff937d5dbb4c099dd1cd3b09`) does not contain the inspected diagnostic/rsi-cross markers. Current dashboard and monitor source do not expose the diagnostic counters identified in the PR scope.
- Classification: **MISSING from current branch (source-level)**. Diagnostic counters were not demonstrated as preserved or replaced.

### PR #44 — Multi-Symbol Signal Scanner
- Historical head contains `MultiSymbolScanner.kt` (blob SHA `5eaa81ba8ff2641780e6135f8c737b9056e0ea7b`), `BinanceRestGate.kt` (blob SHA `266d6099a453fa69118378dc686898b26ed9c00d`), and `OrderBookSequence.kt`.
- These three files were not found at their historical paths on the current Android branch.
- Current `MarketEngine.kt` and `CompleteDashboard.kt` were inspected; no `MultiSymbol` scanner markers were found. PR #45 is merged but its changed-file list covers workflow, dashboard, MarketEngine and StrategyMonitorService; it does not establish that the dedicated PR #44 scanner implementation was integrated.
- Classification: **MISSING from current branch (source-level)**. PR #45 is not sufficient evidence that PR #44's independent multi-symbol scanner, per-symbol Order Book, multiplexed WebSocket and REST 418/429 gate were preserved or replaced.

## PR state and history caveat
- GitHub reports #42, #43 and #44 closed with `merged=false`. #43/#44 records contain merge_commit_sha fields, but those fields alone do not prove that their PRs were merged into the current Android branch.
- PR #45 is merged and was inspected as the purported restoration path; its changed-file list does not include the dedicated scanner/helper files above.
- No branch deletion or cherry-pick is authorized by this audit.

## Result
- PR #42: **MISSING / EQUIVALENCE NOT VERIFIED**.
- PR #43: **MISSING / EQUIVALENCE NOT VERIFIED**.
- PR #44: **MISSING / REPLACEMENT NOT VERIFIED**.
- Build/tests: **NOT RUN**. This was a GitHub source-level audit only.
- Current Android branch SHA used for comparison: `4bb768ad55a89e9ad1e4a65b32bdd7ebd7ef48d4`.
- No source code or CI configuration changed; no workflow run or artifact exists for this audit.

## Recommended next step
Perform a focused current-source behavior audit of `OrderBookEngine.kt` and the dashboard/monitor pipeline. Then prepare a test-first recovery plan for the missing sequence helper, diagnostic counters, and observe-only multi-symbol scanner. Preserve existing strategy thresholds and paper/analysis-only safety boundaries. Do not delete historical branches or merge/replay PRs until the recovery plan identifies non-duplicative changes and CI validates them.
