# BTC Chart Pro separation audit — 2026-11-05

## Objective

Remove BTCUSDT Chart Pro product code and product-specific operational configuration from the independent five-layer system while preserving five-layer data, strategy, risk, paper-ledger and control-plane capabilities. This is an inventory and dependency-boundary audit only; no source or workflow files were deleted or modified.

## Repository and source identities inspected

- Five-layer repository: kenznguyen/btcusdt-telegram-signals2.
- Documentation/evidence branch: main, HEAD before this report: e8d075d2b4e743630da10f4d33ebc359a34e1ba8.
- Current T0 implementation PR #134: OPEN / DRAFT / NOT MERGED; head branch feature/t0-atomic-write-fencing-20261105, head SHA d0f503ee3ba987784daa36e904588829c44e93b6; base branch feature/t0-centralized-data-feeder-p1-20261101, base SHA 8b196d2720eab804728df7c0227c606c094b16ad.
- Five-layer PR #134 head tree: 234 paths; contains android-app/, control_dashboard/, market_data/, futures_intelligence/, freqai_bridge/, paper_execution/, pipeline/, integrations/, quant_system/, and other components.
- Separate Chart Pro repository exists: https://github.com/kenznguyen/btcusdt-chart-pro-android, private, default branch main. Its tree contains the standalone Chart Pro Android app and Chart Pro-specific screens/engines. This is the intended home for Chart Pro-only Android product code.
- The default branch main of the five-layer repository is currently a legacy Telegram Signal Bot snapshot (42 paths) and is not the same source line as PR #134 / the five-layer T0 branch. Do not treat default-branch contents as a complete representation of the active five-layer source.

## Confirmed contamination / boundary conflicts

| Area | Evidence | Classification | Disposition |
|---|---|---|---|
| Root README | At PR #134 head, title is “BTCUSDT Chart Pro và hệ thống phân tích futures”; lists Android BTCUSDT Chart Pro, Chart Pro Android workflows and product-specific runtime instructions alongside five-layer components. | MIXED / OUTDATED | Rewrite as five-layer-only project README; retain references to Chart Pro only as a separate repository link where useful. |
| Android module identity | android-app/README.md identifies the module as “BTCUSDT Chart Pro (Android)” and describes chart tabs, multi-symbol chart/scanner, alert history, backtest, 13x leverage and Chart Pro release signing. | CHART PRO PRODUCT DOC | Move/retire from five-layer docs after five-layer Android ownership is explicitly defined. |
| Android app entrypoint | MainActivity.kt mounts CompleteDashboard and starts StrategyMonitorService for the regular variant; parallel variant mounts FiveLayerStandaloneDashboard. | MIXED APP SHELL | The five-layer Paper variant is already isolated at runtime, but shares the same Gradle module/source tree with Chart Pro. Separate build/module boundary is required before removing Chart Pro classes. |
| Android chart screens/engine | CompleteDashboard.kt, MarketEngine.kt, ChartAnalytics.kt, ChartMarketSession.kt, BacktestPanel.kt, chart alert/history classes and StrategyMonitorService.kt are part of the Chart Pro product path. | CHART PRO CANDIDATE | Remove from the five-layer app only after compile/runtime dependency tracing confirms no imports from the five-layer variant. Canonical source exists in the separate Chart Pro repo. |
| Multi-symbol scanner | MultiSymbolScanner.kt, ScannerMarketFeed.kt, and scanner-specific UI are multi-symbol chart/scanner functionality. The five-layer paper runbook and decision flow are BTCUSDT-centric. | CHART PRO-ONLY CANDIDATE | Exclude from the five-layer APK; preserve in Chart Pro repo. Do not confuse this with T1 futures intelligence feeds. |
| Chart Pro build/release | android-app/app/build.gradle.kts uses package com.kenznguyen.btclivealerts, with a parallel applicationId suffix and release signing environment variables. Android docs describe Chart Pro release alias btc-chart-release. | CHART PRO BUILD COUPLING | Replace with a five-layer-owned app identity/build configuration before deleting Chart Pro variant. Do not copy Chart Pro signing keys or release identity into the five-layer app. |
| CI and runner docs | At PR #134 head, root README and Android README still describe Codemagic as the runner and list android-chart-pro-debug/release; this conflicts with the current handoff policy that GitHub Actions is default and Codemagic is fallback-only. | STALE CI / PRODUCT CONFIG | Reconcile docs and workflows in a separate controlled increment; keep active T0 GitHub Actions workflow intact. |
| Architecture docs | docs/FIVE_LAYER_ARCHITECTURE.md describes the APK as “Chart Pro” client; docs/FIVE_LAYER_PAPER_RUNBOOK.md references ChartProFreqaiResearch and Codemagic Android workflows. | MIXED / STALE NAMING | Rename/rewrite to five-layer-owned client and remove Chart Pro product assumptions; retain FreqAI research implementation where still used. |
| Legacy Telegram/dashboard | Root main README and files app.py, bot.py, telegram_commands.py, dashboard/ describe legacy Telegram bot and backtest dashboard. | LEGACY / NOT AUTOMATICALLY CHART PRO | Do not delete as part of Chart Pro cleanup without confirming ownership, active usage, secrets, deployment and migration evidence. |

## Components that must be preserved pending dependency proof

- T0 canonical market-data store, API, Feeder, scheduler, retry/recovery, lease/fencing and health/readiness.
- T1 futures intelligence, source provenance, coverage and quality indicators.
- T2 Freqtrade/FreqAI research, CORE + independent AI signal generation and model lineage.
- Shared Risk Engine, Kill Switch, reservation/admission rules and paper-only safety.
- T3 Hummingbot read-only/order-book snapshot integration and paper execution ledger; no live order path.
- T4 React control_dashboard/ and pipeline/api.py control plane.
- Android five-layer-specific FiveLayerStandaloneDashboard.kt, FiveLayerPanel.kt, FiveLayerApi.kt, FiveLayerCandlesCard.kt, FiveLayerPresentation.kt, and related tests.
- Shared candidates StrategyEngine.kt, OrderBookEngine.kt, OrderBookSequence.kt, OrderBookAnalytics.kt, HummingbotOrderBook.kt, and paper-order/history contracts. These may be reused by Chart Pro but are not safe to classify as removable until imports, build variants and runtime responsibilities are traced.

## Safe cleanup sequence

1. Freeze boundaries: designate the separate Chart Pro repository as owner of chart UI, multi-symbol chart scanner, chart alerts, in-app chart backtest and Chart Pro release identity. Five-layer owns T0–T4 and its standalone Paper client.
2. Dependency map: trace imports and source-set inclusion from the five-layer APK entrypoint. Produce an explicit keep/move/remove manifest for every Android source and test file. Identify which shared strategy/order-book contracts remain necessary.
3. Build isolation: create a five-layer-specific Android module/application ID and build only its source set. Verify it has no Chart Pro screens, services, scanner or release-signing configuration. Do not remove the existing Chart Pro source until this build passes.
4. Documentation/config cleanup: rewrite five-layer README, architecture and runbook; remove Chart Pro-specific build workflow IDs from five-layer docs. Reconcile stale Codemagic instructions against GitHub Actions-default policy.
5. Test and provenance: add RED contracts proving Chart Pro classes/resources are not packaged or referenced by the five-layer app; run focused Android unit tests, full relevant Python/React regression and GitHub Actions against exact source SHA; record artifacts and package ID.
6. Remove only proven Chart Pro-only files from the five-layer source line after the isolated five-layer app passes. Preserve historical branches, PRs and evidence; no bulk branch deletion or old PR replay.

## Current status

- Repository/tree and key Android/docs files inspected: PASS (read-only inventory).
- Separate Chart Pro repository confirmed: PASS.
- Five-layer Android module fully dependency-mapped: NOT VERIFIED.
- Chart Pro source removed from five-layer repository: NOT STARTED.
- Android/Python/React tests and builds: NOT RUN for this audit.
- T0/PR #134 source, workflows, branch and PR state changed: NO.
- Production DB, Feeder, exchange data ingestion or order execution: NOT TOUCHED.

## Immediate next action

Trace the five-layer parallel variant dependency graph and package inputs, then establish a standalone five-layer Android module/build identity before deleting or moving any Chart Pro source. Keep PR #134 scoped to T0 and unmerged; do not mix this cleanup into its 34-file T0 change set.
