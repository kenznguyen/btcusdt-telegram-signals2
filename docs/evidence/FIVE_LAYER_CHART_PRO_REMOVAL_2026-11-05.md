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