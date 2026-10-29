# BTCUSDT Chart Pro (Android)

Standalone Android chart and signal monitor using public Binance USDⓈ-M Futures data. Charts and the scanner support multiple USDT perpetual symbols; the persisted position simulation, in-app backtest and five-layer paper system remain BTCUSDT-specific and are labeled accordingly. The app never places exchange orders or requests exchange trading API keys.

## Strategy rules ported from bot.py/backtest.py

- M15 entry + last fully closed H1 trend filter; RSI(14), DMI/ADX(14), H1 ADX entry threshold 20.
- LONG: H1 +DI > -DI and ADX > 20; M15 RSI crosses upward through 30.
- SHORT: H1 -DI > +DI and ADX > 20; M15 RSI crosses downward through 70.
- TP: LONG RSI >= 76 or SHORT RSI <= 24, and estimated ROE >= +5%.
- DCA: estimated ROE <= -20%, M15 ADX > 45; LONG RSI > 20 and rising; SHORT RSI < 80 and falling; one DCA maximum.
- Soft SL: estimated ROE threshold -35% touched, H1 direction reverses with ADX > 35, and two consecutive candles confirm reversal. Because the second candle must close first, the simulated fill uses that close plus adverse slippage, never an earlier threshold price from the same candle.
- Emergency SL: -90% ROE price threshold; checked before Soft SL and TP.
- Leverage 13x, default initial margin 50% of simulated balance, DCA margin 100% of initial order margin, estimated taker fee 0.05% per side, adverse slippage 5 bps.
- DCA is skipped if the simulated wallet balance cannot cover the additional reserved margin, matching the conservative backtest behavior.
- Simulated state, position, processed candle timestamp, balance, and recent events are persisted locally. Chart alert history stores up to 100 recent events and shows local counts for today, chart alerts, and strategy events. Standalone RSI M15 threshold notifications have been removed; RSI remains part of the trading-strategy calculations. First launch warms up indicators and evaluates only the newest closed M15 candle instead of replaying old historical alerts.
- A foreground data-sync service performs monitoring while Android allows it to run. Battery settings, force-stop, manufacturer restrictions, and Android foreground-service limits may still interrupt monitoring.

## Validation and build on Codemagic

GitHub stores source and PRs; Codemagic runs all build/test jobs. Active configuration is [`codemagic.yaml`](../codemagic.yaml); historical GitHub Actions YAML is archived outside `.github/workflows`.

Use [`docs/CODEMAGIC_SETUP.md`](../docs/CODEMAGIC_SETUP.md) for the full setup. Start `android-chart-pro-debug` on `feature/android-five-layer-control` for both the regular and parallel-install APKs. Its push trigger also accepts that branch when the repository webhook is connected. It uses JDK 17, checksum-verified Gradle 8.9, SDK 35 and Build Tools 34.0.0, runs Hummingbot gateway/artifact checks and both Android unit-test suites, then assembles both variants. The artifact gate checks actual package IDs, launcher activity, labels, versions and APK signatures. Artifacts include the APKs, JUnit XML/HTML, `android-source-sha.txt` and `android-apks.json` with source SHA, APK hashes and certificate fingerprints.

### Install alongside the existing app

Download **`BTC-5-Tang-Paper-<source SHA>.apk`** from the successful Codemagic build. It installs as **BTC 5 Tầng Paper**, with an amber icon and package `com.kenznguyen.btclivealerts.paper`; it opens the five-layer tab. The regular APK retains package `com.kenznguyen.btclivealerts`, so installing Paper does not replace it. Preferences, app storage, permissions and notifications are separate on Android. Both apps still access the **same server paper ledger** when configured with the same common API; use a separate test server/database for a separate server ledger.

The parallel variant is a debug-signed testing APK, built alongside the regular debug APK. Updating an installed Paper APK requires the same signing certificate; a fresh CI debug keystore may require reinstalling only the Paper app. Compare `android-apks.json` fingerprints before an update. This does not change the existing release signing identity.

For a signed APK, manually start `android-chart-pro-release` after configuring the `android_release` secret group with the **existing** keystore and `btc-chart-release` alias. The workflow runs tests, assembles release, verifies the APK certificate against the supplied keystore and cleans up the temporary key. It does not publish to Play Store. Certificate and install-over-existing-app verification remain required before claiming release compatibility.

Local build, when JDK 17, Gradle 8.9 and SDK 35 are installed:

```bash
gradle :app:testDebugUnitTest :app:testParallelUnitTest :app:assembleDebug :app:assembleParallel --no-daemon
```

The repository has no Gradle wrapper. The regular application ID and release signing configuration are unchanged. A YAML change alone does not prove the APK has built or run on a device.

## Live chart and in-app backtest

### Hệ thống 5 tầng · BTCUSDT PAPER

The **Hệ thống 5 tầng** tab connects to the common API described in [`pipeline/CONTRACTS.md`](../pipeline/CONTRACTS.md). Enter the server's HTTPS base URL and its `MARKET_DATA_TOKEN` as the read token. This panel always represents BTCUSDT, independently of the symbol selected for charts or the scanner. It shows layer status, observed futures flow, Hummingbot Order Book, the AI decision and server paper ledger; unavailable data remains unavailable rather than becoming zero.

The canonical candle card requests the last 20 closed M15 slots from the layer-0 store. It displays actual OHLCV strings, coverage and missing slots, and leaves gaps in the chart instead of inventing candles. It validates the returned market/window, closure, availability times, OHLC bounds and coverage; the dataset identifier is server-supplied. This preview has its own 20-slot query and is separate from the two-candle input window used by the decision engine. Older common APIs without `generatedAtMs` remain supported; the app labels its own API-read time separately from candle close time.

Each section updates independently and shows safe Vietnamese diagnostics for rejected tokens, missing endpoints, unavailable server data, timeouts and invalid responses. Known decision and paper-state reasons have Vietnamese explanations. Leaving the screen cancels requests; manual refresh and reconnect clear earlier results. These additions do not enable automatic paper orders.

To evaluate a paper intent, pause/resume the paper ledger or cancel a pending paper order, enter the separate `CONTROL_TOKEN`. Read-only use does not need that control token. The app saves only the base URL; both tokens stay in screen memory and must be entered again after leaving the panel or restarting the app. No exchange credentials belong in either field. Requests use the configured common API; a paper action never places an exchange order.

Paper history now browses the server's bounded latest 100 records, with status filters, pages of 10 and a detail dialog containing order/intent IDs, quantities, fill price, fee, reason and UTC timestamps. The dialog uses the latest valid snapshot and disables cancellation while data is unavailable. Canceled orders can retain an unfilled quantity; that value is not an active pending order.

The last action's validated server response is shown separately with received time and exact fill/fee details. Starting another action clears that prior receipt. A timeout or lost response remains an unconfirmed outcome while the app rereads the ledger; it never presents the previous response as the new result or automatically resubmits a command.

Deploy and configure the API separately using the [five-layer runbook](../docs/FIVE_LAYER_PAPER_RUNBOOK.md). Codemagic builds the APK and runs finite checks; it does not host the API, Hummingbot or model training. Source/configuration alone does not confirm a successful APK build, device run or connection to those services.

### Hummingbot Order Book

The **Order Book** tab supports Binance direct data and Hummingbot snapshots for the selected USDT perpetual symbol. It displays best bid/ask, spread in basis points, depth over 20 price levels, and plain/distance-weighted liquidity imbalance. Hummingbot also shows its five nearest levels on each side. Snapshots remain separate from the scanner and strategy confirmation stream: the API timestamp is retrieval time, not an exchange event time or proof of sequence synchronization.

Run the read-only gateway using [integrations/README.md](../integrations/README.md), then enter its HTTPS base URL and dedicated access token in the Hummingbot source settings. The token stays in screen memory; only the URL and source selection are saved. Hummingbot Basic credentials remain on the server. The app polls every five seconds while the panel is visible and the activity is started, cancels requests when switching symbols/sources, clears results on fetch failure, and hides expired snapshots. It never silently substitutes Binance results for Hummingbot.

Focused regression tests: `gradle :app:testDebugUnitTest --tests '*HummingbotOrderBookTest' --no-daemon`. Full validation remains the test/build command above. Codemagic accepts `feature/hummingbot-order-book` and runs the bridge tests before Android tests/build. Start `android-chart-pro-debug` on that branch if its GitHub webhook is unavailable. This source change does not include a signed release artifact.

- The live candlestick chart displays recent candles, a price grid, and Bollinger Bands (20, 2). Initial loading, periodic reconciliation and reconnection use the selected symbol. Late callbacks from replaced connections are ignored.
- Chart alert titles, history and deduplication keys include the symbol and timeframe. The newest 100 history items are retained. Master notification settings, direction filters where applicable, quiet hours, sound and vibration share one delivery policy.
- The multi-symbol scanner reconnects with backoff and loads candle history before resuming evaluation; switching continuous scanning off and on restarts it without reopening the app.
- The BTCUSDT backtest offers 7/30/90/180/360-day history through paginated requests and processes each candle once. It shows estimated net PnL, balance, closed exits, win rate, Profit Factor, max drawdown and recent closed events.
- Closed-trade PnL and open-position unrealized PnL are displayed separately. Equity/drawdown include estimated unrealized PnL and fees; intrabar extremes are estimates from OHLC, not tick-order reconstruction. Validate the same candle fixture and fill assumptions before comparing results with another engine.


