# BTCUSDT Chart Pro (Android)

Standalone Android chart and signal monitor using public Binance USDⓈ-M Futures data. Charts and the scanner support multiple USDT perpetual symbols; the persisted position simulation and in-app backtest remain BTCUSDT-specific and are labeled accordingly. The app never places orders or requests trading API keys.

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

## Validation

Codemagic runs JUnit tests before assembling a debug APK on Android-related pushes to `fix/chart-pro-reliability-20261027` and `main`. Each build tests the checked-out source commit. A push to the fix branch also validates the code proposed in its pull request; a separate pull-request trigger is omitted to avoid duplicate builds. GitHub Actions remains available as a manual fallback while its build quota is exhausted. Regression tests cover symbol isolation, stale callbacks, scanner reconnection/backfill, closed-candle preservation, alert history/policy, Order Book retries, and close-confirmed Soft SL pricing, alongside the existing indicator and strategy tests.

A successful build and unit tests do not prove numerical parity with TradingView or live fills. Indicator results must still be compared against the Python engine on the same candle fixture before relying on alerts. Data source is Binance Futures while the existing Python bot/backtest use OKX candles, so prices and indicator values can differ slightly. This app is a simulation/alerting tool only, not financial advice. Do not use the simulated PnL or alerts as a guarantee of future results.

## Build

Use JDK 17, Gradle 8.9 and Android SDK 35, or open this directory in Android Studio:

```bash
gradle :app:testDebugUnitTest :app:assembleDebug --no-daemon
```

The repository currently does not include a Gradle wrapper; use the pinned Gradle version above. The debug APK is at `app/build/outputs/apk/debug/app-debug.apk`.

- **Codemagic / android-chart-pro-debug** is the primary automatic test and debug build workflow; setup and manual start instructions are below.
- **Android Live Chart CI** manually runs tests and builds debug APKs. Its `source_branch` input accepts existing integration branches, including `integration/android-freqtrade-analytics-20261025`.
- **Android APK** manually builds the selected workflow branch; when the existing signing secrets are present, it also builds and verifies a release APK.
- **Android Release APK** manually builds a selected source branch using the existing release keystore secrets and `btc-chart-release` alias. It uploads an APK artifact, not a Play Store publication.
- Every workflow records the actual checked-out commit in `android-source-sha.txt` and build logs or the run summary. Check that commit when comparing artifacts: a GitHub workflow launched from `main` can intentionally build another branch.

Package: `com.kenznguyen.btclivealerts`

### Codemagic setup and first build

The repository-root [`codemagic.yaml`](../codemagic.yaml) defines `android-chart-pro-debug`. It uses a Mac mini M2 runner with JDK 17, downloads Gradle 8.9 with a pinned SHA-256 check, ensures Android SDK 35 is installed, runs unit tests, and then assembles the debug APK. The build has a 30-minute limit, caches Gradle dependencies and its verified distribution, and cancels outdated webhook builds. No signing variables or release keystore are needed for this debug workflow.

1. Open the `btcusdt-telegram-signals2` application already added to Codemagic and use its YAML configuration.
2. Select **Start new build**, branch **`fix/chart-pro-reliability-20261027`**, and workflow **`android-chart-pro-debug`**. Select `main` only after the Android changes and YAML have been merged there.
3. Start the build. On success, download **`app-debug.apk`** and **`android-source-sha.txt`** from the build artifacts. JUnit XML and the HTML unit-test report are also collected, with test results displayed in the build overview.
4. For subsequent automatic builds, ensure the application's GitHub webhook is enabled. Pushes to the two configured branches run when `android-app/` or `codemagic.yaml` changes; the first build establishes the change-tracking baseline. If the webhook is not configured, start builds manually as above.

The workflow produces debug artifacts only. A passing build is the source of truth for compilation and test results; adding the YAML alone does not verify the app. For configuration details, see the official [Codemagic YAML guide](https://docs.codemagic.io/yaml-basic-configuration/yaml-getting-started/), [automatic build triggers](https://docs.codemagic.io/yaml-running-builds/starting-builds-automatically/), and [test reports](https://docs.codemagic.io/yaml-testing/testing/).

## Live chart and in-app backtest

- The live candlestick chart displays recent candles, a price grid, and Bollinger Bands (20, 2). Initial loading, periodic reconciliation and reconnection use the selected symbol. Late callbacks from replaced connections are ignored.
- Chart alert titles, history and deduplication keys include the symbol and timeframe. The newest 100 history items are retained. Master notification settings, direction filters where applicable, quiet hours, sound and vibration share one delivery policy.
- The multi-symbol scanner reconnects with backoff and loads candle history before resuming evaluation; switching continuous scanning off and on restarts it without reopening the app.
- The BTCUSDT backtest offers 7/30/90/180/360-day history through paginated requests and processes each candle once. It shows estimated net PnL, balance, closed exits, win rate, Profit Factor, max drawdown and recent closed events.
- Closed-trade PnL and open-position unrealized PnL are displayed separately. Equity/drawdown include estimated unrealized PnL and fees; intrabar extremes are estimates from OHLC, not tick-order reconstruction. Validate the same candle fixture and fill assumptions before comparing results with another engine.

