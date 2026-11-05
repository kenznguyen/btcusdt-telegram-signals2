# Five-layer repository: remove BTC Chart Pro components — 2026-11-05

## Decision and scope

User direction: prioritize removing BTC Chart Pro components from the five-layer system. Do not require byte-for-byte parity or migration into the separate Chart Pro repository. The separate Chart Pro repository is not a dependency or acceptance gate.

Implementation branch: `cleanup/remove-chart-pro-from-five-layer-20261105`.
Base branch: `feature/android-five-layer-control`.
Base SHA: `2a4b914f5e1f133544494278f3bf5117ff815418`.
Implementation source SHA before this report: `767c6c8ef2550cb18686ae67336bd3a59fd38213`.

## Removed from five-layer Android

Deleted 18 Chart Pro-only Kotlin production files:
- AlertDelivery.kt, AlertHistoryStore.kt, AlertPolicy.kt
- BacktestPanel.kt
- BinanceRestGate.kt
- ChartAnalytics.kt, ChartMarketSession.kt, CompleteDashboard.kt, MarketEngine.kt
- MultiStreamSignalEngine.kt, MultiSymbolScanner.kt, ScannerMarketFeed.kt, SnapshotRetryGate.kt
- OrderBookEngine.kt, OrderBookPanel.kt, OrderBookSequence.kt
- StrategyEngine.kt, StrategyMonitorService.kt

Deleted 10 Chart Pro-specific Android tests:
- AlertHistoryCodecTest.kt, AlertPolicyTest.kt, BinanceRestGateTest.kt
- ChartAnalyticsTest.kt, ChartMarketSessionTest.kt
- MultiStreamSignalEngineTest.kt, MultiSymbolScannerTest.kt
- OrderBookSequenceTest.kt, SnapshotRetryGateTest.kt, StrategyEngineTest.kt

Removed the obsolete parallel-install resource set and legacy Chart Pro CI tooling:
- `android-app/app/src/parallel/res/**`
- `ci/test_android_apks.py`
- `ci/verify-android-apks.py`
- `ci/release-android.sh`

## Five-layer Android identity and runtime

- MainActivity now mounts only FiveLayerStandaloneDashboard.
- Gradle now builds one application variant, retaining the former five-layer parallel applicationId `com.kenznguyen.btclivealerts.paper` so Android can update the existing five-layer install; the parallel build type and Chart Pro release signing configuration are removed.
- AndroidManifest retains INTERNET permission and launcher Activity only. StrategyMonitorService and foreground-service, notification and vibration permissions are removed.
- The five-layer SharedPreferences namespace `strategy_state_v1` is retained so the previously saved API URL remains available after upgrade.
- Default app label/icon are now the five-layer Paper identity.
- Android README and Codemagic setup describe a single five-layer Paper APK, no Chart Pro tabs and no Chart Pro release workflow.
- Codemagic Android workflow renamed to `five-layer-android`; it runs boundary tests, APK verifier tests, Android unit tests, one debug build and APK identity/payload verification.
- Added `ci/verify-five-layer-android-apk.py`, `ci/test_five_layer_android_apk.py` and `ci/test_five_layer_android_boundary.py`.

## T2 ownership and preserved contracts

- Renamed FreqAI strategy `ChartProFreqaiResearch` to `FiveLayerFreqaiResearch`; updated smoke test, README and research config identifier.
- Kept Python Strategy Core at `pipeline/core_strategy.py` and its regression tests. Its RSI/DMI/ADX, entry, TP, DCA and stop defaults were not modified.
- Preserved Android five-layer UI/API/canonical candles/presentation, paper history, Hummingbot snapshot parser and OrderBookAnalytics.
- Preserved T0–T4 source, Shared Risk Engine, Kill Switch, paper execution ledger, React control dashboard, data/evidence assets.
- No T0 source, DB, Feeder, lease, exchange ingestion, paper ledger, live execution or order endpoint was changed.
- No files were copied to or reconciled with the separate Chart Pro repository.

## Verification status

- Git tree inspection: PASS; only five-layer Android sources/tests/resources remain under the Android module.
- Static boundary tests added: NOT RUN locally.
- APK verifier contract tests added: NOT RUN locally.
- Android Gradle unit tests: NOT RUN.
- Android APK build and DEX/manifest inspection: NOT VERIFIED.
- Codemagic workflow run/artifact: NOT VERIFIED (no run result has been retrieved in this session).
- Python Strategy Core source/defaults and regression-test files inspected: PASS at source review level; test suite NOT RUN.
- PR #65 and PR #134 were not modified or merged.

## Next gates

1. Verify Codemagic `five-layer-android` on the exact resulting branch HEAD; require boundary tests, APK verifier tests, Android unit tests and APK build to pass.
2. Inspect artifact `android-apk.json` and APK SHA; confirm package `com.kenznguyen.fivelayerpaper`, DEX excludes Chart Pro classes and manifest contains no Chart Pro service/permissions.
3. Run Python Core strategy regressions and relevant T0–T4 regression suite on the same candidate source SHA.
4. Review the diff and update handoff with exact workflow run/artifact. Keep PR draft/unmerged until explicit approval.

No claim of a successful APK build or device installation is made by this report.


## Follow-up: preserve the existing five-layer Android installation

After reviewing upgrade compatibility, the initial package/settings rename was corrected:
- The single APK now retains the previous five-layer parallel variant application ID `com.kenznguyen.btclivealerts.paper`; removing the parallel build type does not change the installed five-layer package identity.
- `FiveLayerPanel` retains the original `strategy_state_v1` SharedPreferences namespace, preserving the previously saved API URL.
- Boundary tests now assert both compatibility contracts; the APK verifier expects the preserved package ID.
- This avoids the known package-ID and preference-key migration break. APK signer continuity still requires verification against the previously installed APK certificate.

Latest source checkpoint for this follow-up: `907c5d254d3f832f7d5062ac22b3c529305a6c20`.
Build/tests and Codemagic artifact remain NOT VERIFIED.

## Follow-up: ensure cleanup branch runs the full five-layer CI gates

Static review found that the cleanup branch was included in the Android workflow but omitted from the Codemagic branch filters for `canonical-market-data` and `five-layer-dashboard`. This would have left T0/T1/Core Strategy/paper integration and React dashboard regression gates untriggered on this branch.
- Added `cleanup/remove-chart-pro-from-five-layer-20261105` to the branch patterns of `canonical-market-data` and `five-layer-dashboard`.
- Added a boundary test asserting the cleanup branch is configured for all three workflows: `five-layer-android`, `canonical-market-data`, and `five-layer-dashboard`.
- Verified by reading the exact Codemagic YAML on the branch: all three workflows contain the cleanup branch pattern and a changeset gate. This is static configuration verification only; Codemagic execution is NOT VERIFIED.
- Fixed the boundary test's workflow-block extraction to match top-level YAML sections rather than indentation prefixes.

Source checkpoint before this evidence update: `ed9fc45248b25669a849f98a5844977ed2deccb0`.

## Follow-up: compare protected strategy and paper-risk files by blob SHA

Compared the PR base branch `feature/android-five-layer-control` with the cleanup branch. All six protected files have identical Git blob SHA values:
- `pipeline/core_strategy.py`: `b4266fc05ea41355ba9dcf6f15cb7b5a6d3800b0`
- `pipeline/test_core_strategy.py`: `bff8e2c0a21abce99ae4e6f46c911fe88a4925b5`
- `pipeline/core_signal.py`: `df5fbb59611bdd4fbb8224665f79655dd4433455`
- `pipeline/test_core_signal.py`: `a946716604e2e1a74b0e32f0aae5d07b820f2cbf`
- `paper_execution/risk_control.py`: `3c76e462b0b4d924c2418842d95ed74285e2315d`
- `paper_execution/ledger.py`: `68209ce48a6e5e9a995f93167684133e41cc7f55`

This proves these exact source/test files are byte-identical to the PR base; it does not replace executing their regression suites. T0 source path inventory remains outside the PR diff.

## Superseding follow-up: move CI execution to GitHub Actions — 2026-11-05

The project decision is GitHub Actions as the default and official CI runner. Codemagic is no longer the runner for this repository's normal workflows. This section supersedes the earlier Codemagic branch-coverage and execution instructions above; those entries remain as historical records of the previous configuration.

- Added `.github/workflows/five-layer-pr-validation.yml` with separate Android Paper, backend T0–T3/Core, and T4 Dashboard jobs.
- Triggers: pull requests targeting `feature/android-five-layer-control`, pushes to `cleanup/remove-chart-pro-from-five-layer-20261105`, and manual dispatch.
- Every job checks out the exact PR head SHA (not the synthetic merge ref), runs with `contents: read`, and does not receive production secrets or external DB/exchange credentials. `AI_EXECUTION_ENABLED=false`.
- Android job runs source boundary and APK verifier contract tests, Android unit tests, debug APK build, and APK package/label/manifest/DEX/signature verification. The APK verifier receives `CM_BUILD_DIR` only as its existing repository-root parameter; this is not a Codemagic runtime.
- Backend job runs isolated T0 Gateway/Feeder/scheduler/recovery/health/storage tests, T1 futures intelligence, T2 Core Strategy/FreqAI, T3 Paper Risk/Ledger/Hummingbot, and CI/T0 policy tests.
- Dashboard job runs frozen npm install, React tests, build and high-severity dependency audit.
- Retired `codemagic.yaml`, `docs/CODEMAGIC_SETUP.md`, and the Codemagic-only `ci/setup-android.sh`.
- Static workflow and source-boundary checks are recorded in the PR; GitHub Actions execution, APK output, signer continuity with an existing installation, and all runtime deployment properties remain NOT VERIFIED until the exact new head run completes.
- No T0 runtime/data source, Strategy Core, Paper Risk/Ledger, PR #65, PR #134, canonical DB, exchange connection, Feeder activation or live execution was changed or enabled.
- PR remains OPEN / DRAFT / NOT MERGED pending exact-SHA GitHub Actions results and review.


## GitHub Actions first execution and syntax repair — 2026-11-05

- The first active GitHub Actions workflow was triggered after the Codemagic migration. Run #42044164991 (push) was cancelled by a newer push; run #42044180900 (PR) completed with failure on source SHA `c6de7e06acfef4d6f8e7d20cec145c5a2697afdf`.
- Android boundary test and backend compile both exposed a malformed test-file edit: `ci/test_five_layer_android_boundary.py` had a duplicated method appended after `unittest.main()`, producing a Python SyntaxError. This is a real failed CI attempt, not a pass.
- Rewrote the complete boundary test file with a single correctly ordered test class and `unittest.main()` at EOF. Corrective commit/source SHA: `d7cce0172cb7b25a8a7cd0feb0a4ce4a521f1b99`.
- Replaced obsolete Codemagic CI policy tests that asserted GitHub Actions must be absent. New `ci/test_ci_policy.py` asserts the GitHub Actions trigger, exact PR-head checkout, three job boundaries, Android tests/build/APK verification, paper-only backend regression boundary, and Dashboard test/build/audit gates.
- Adjusted backend T0 command list to modules that actually exist on this PR's declared base: `market_data.test_store`, `market_data.test_sync`, `market_data.test_storage`, and `market_data.test_api`. This PR branch does not contain the newer feeder scheduler/recovery test modules; those modern T0 acceptance suites remain outside this PR's exact branch and are not claimed as run here.
- Current exact-head GitHub Actions runs on `d7cce0172cb7b25a8a7cd0feb0a4ce4a521f1b99`: PR run #42044440154 was IN_PROGRESS at evidence update; push run #42044431785 was QUEUED. These are not PASS.
- Earlier cancelled run #42044164991 showed Dashboard npm install, React tests, production build and npm audit steps completed successfully on the prior source SHA `c6de7e06acfef4d6f8e7d20cec145c5a2697afdf`; this is historical partial evidence only and does not certify the latest SHA.
- Android boundary/APK tests, Gradle unit tests/build, backend regression suites and latest Dashboard gates remain NOT VERIFIED until the current exact-head run completes. No artifact is accepted yet.
- T0 source paths remain unchanged by this PR. Core Strategy/Paper protected file blob hashes remain identical to PR base. No canonical DB, exchange, Feeder, live execution, PR #65 or PR #134 changed.


## Final GitHub Actions exact-head acceptance — 2026-11-05

- Source SHA: `5aedfe7c6f55163b3bbb5a3b6c82677da0272eb1`.
- PR workflow run #42046383582: **SUCCESS**. URL: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42046383582.
- Job IDs and conclusions:
  - Android Paper boundary, unit tests and APK verification: job `127310345192` — **SUCCESS**.
  - T0–T3, Core Strategy and Paper isolation regressions: job `127310345756` — **SUCCESS**.
  - T4 React tests, production build and dependency audit: job `127310345761` — **SUCCESS**.
- Android: 16 source-boundary/APK-verifier contract tests PASS; `:app:testDebugUnitTest` BUILD SUCCESSFUL; `:app:assembleDebug` BUILD SUCCESSFUL; verifier output: `Verified five-layer-only APK for source 5aedfe7c6f55163b3bbb5a3b6c82677da0272eb1`.
- Backend: T0 available branch storage/sync/read API tests 35 PASS; T1 futures intelligence 10 PASS; T2 Core Strategy/signal/FreqAI 56 PASS; T3 Paper risk/ledger/Hummingbot 42 PASS; GitHub Actions policy 5 PASS. Total 148 Python backend/policy tests PASS.
- Dashboard: npm install PASS; React tests PASS (6 tests); production build PASS; `npm audit --audit-level=high` reports 0 vulnerabilities.
- Artifacts, all attached to exact source SHA `5aedfe7c6f55163b3bbb5a3b6c82677da0272eb1`:
  - Android APK/report bundle ID `13424328512`, size 9,759,372 bytes, digest `sha256:22f46b3a7c193ebed72d79b98dd9a55cc429ac359eb56403ade89f7d6a70264a`.
  - Backend logs/source SHA ID `13424133997`, digest `sha256:aebf9cdd2a03de068023dabec3e6c5774d686ce88be4af4fec2473b3d528e674`.
  - Dashboard build ID `13425595458`, digest `sha256:e3887e7db1047e99e60ceab30216e5ba6b31ffbc634458cb9b735f685801d6e2`.
- The Android verifier checked the built APK's single-app identity, package/label, manifest/permissions, DEX payload and signature presence. Existing-install signing-certificate continuity with any previously installed APK remains **NOT VERIFIED**; the artifact is a CI debug APK, not a release-signed APK.
- The PR branch's T0 test scope is limited to the T0 modules available on its declared base branch. Current-main feeder scheduler/recovery acceptance is a separate workstream and is not claimed by this run.
- No T0 source/data/Feeder/lease/fencing/recovery path, canonical DB, exchange access, live execution, PR #65 or PR #134 was changed or activated.
- Status on tested SHA: GitHub Actions migration **PASS**; Chart Pro removal boundary **PASS**; Android Paper debug build and verifier **PASS**; T0–T3/Core and T4 regression jobs **PASS**; existing-install signer continuity **NOT VERIFIED**.
- PR #135 remains OPEN / DRAFT / NOT MERGED. Do not merge without explicit approval.
