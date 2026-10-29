# Repository maintenance and release safety

## Protected product surfaces
- Telegram webhook and commands, Python backtest and dashboard.
- Android BTCUSDT Chart Pro: M15/H1, H1 overlay, Multi-Symbol Scanner and chart symbol switching, MFI & %B, DMI/ADX, Order Book, alerts and Strategy Monitor.
- Paper trading only; do not introduce live order placement.
- Release APK must use the existing signing keystore and alias, and must update the installed app without uninstalling.

## Branches
- `main`: stable release and Telegram production; do not merge experimental work without tests.
- `feature/android-btcusdt-live-alerts`: current Android integration branch until a verified migration is completed.
- `feature/*`, `fix/*`: temporary development branches; close/merge reviewed PRs before cleanup.
- `backup/*`, `restore/*`: recovery branches; do not delete without verified archived tags and a tested restore procedure.
- `feature/driver-hotspot-android`: separate Android product; keep isolated, consider separate repository later.

## Release gate
1. Review changed files and feature parity; verify scanner, symbol switcher, M15/H1, indicator charts and notifications.
2. Run `gradle :app:testDebugUnitTest --no-daemon` and `gradle :app:assembleDebug --no-daemon` on the selected Android source branch.
3. Run Codemagic `android-chart-pro-release` manually on the reviewed source branch, using the existing release keystore from the `android_release` secret group.
4. Confirm `assembleRelease`, signature alias, applicationId/versionCode compatibility, artifact and successful install-over-existing-app.
5. Only then promote the tested source into `main`.

## Cleanup candidates — review only, not approved for deletion
- `feature/android-btcusdt-5m-forecast` and `feature/dmi-adx-5m-backtest`: deprecated UP/DOWN 5-minute experiments. Preserve history and close related PRs after confirming no shared code dependencies.
- `fix/mfib-highlight-alerts-20261024`: merged PR #49; verify branch has no unique unmerged changes before deletion.
- Older chart/scanner branches and stacked PRs (#42, #43, #44, #47): do not delete before verifying their feature code is present in the integrated Android branch.

## Documentation parity
GitHub stores source and PRs only. All runner workflows are defined in `codemagic.yaml`; old GitHub Actions YAML is archived under `ci/archive/github-actions`. The Codemagic scanner remains manual-only, requires an explicit state snapshot, and has no automatic schedule. Follow `docs/CODEMAGIC_SETUP.md` when switching the Render bridge and secret groups.

## Do not do
- Never delete backup/restore branches or keystore/secrets during routine cleanup.
- Never build a release from `main` by default if it lacks current Android features.
- Never claim tests, builds or APK signatures are verified without CI results.


