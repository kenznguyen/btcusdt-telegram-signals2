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

## Validation and build on Codemagic

GitHub stores source and PRs; Codemagic runs all build/test jobs. Active configuration is [`codemagic.yaml`](../codemagic.yaml); historical GitHub Actions YAML is archived outside `.github/workflows`.

Use [`docs/CODEMAGIC_SETUP.md`](../docs/CODEMAGIC_SETUP.md) for the full setup. Start `android-chart-pro-debug` on `feature/canonical-market-data` for the current integrated source. It uses JDK 17, checksum-verified Gradle 8.9, SDK 35 and Build Tools 34.0.0, runs Hummingbot gateway tests and Android unit tests, then assembles the debug APK. Artifacts include the APK, JUnit XML/HTML and actual source SHA.

For a signed APK, manually start `android-chart-pro-release` after configuring the `android_release` secret group with the **existing** keystore and `btc-chart-release` alias. The workflow runs tests, assembles release, verifies the APK certificate against the supplied keystore and cleans up the temporary key. It does not publish to Play Store. Certificate and install-over-existing-app verification remain required before claiming release compatibility.

Local build, when JDK 17, Gradle 8.9 and SDK 35 are installed:

```bash
gradle :app:testDebugUnitTest :app:assembleDebug --no-daemon
```

The repository has no Gradle wrapper. Package: `com.kenznguyen.btclivealerts`. No application ID or signing configuration change is part of the runner migration. A YAML change alone does not prove the APK has built or run on a device.

## Live chart and in-app backtest

### Hummingbot Order Book

The **Order Book** tab supports Binance direct data and Hummingbot snapshots for the selected USDT perpetual symbol. It displays best bid/ask, spread in basis points, depth over 20 price levels, and plain/distance-weighted liquidity imbalance. Hummingbot also shows its five nearest levels on each side. Snapshots remain separate from the scanner and strategy confirmation stream: the API timestamp is retrieval time, not an exchange event time or proof of sequence synchronization.

Run the read-only gateway using [integrations/README.md](../integrations/README.md), then enter its HTTPS base URL and dedicated access token in the Hummingbot source settings. The token stays in screen memory; only the URL and source selection are saved. Hummingbot Basic credentials remain on the server. The app polls every five seconds while the panel is visible and the activity is started, cancels requests when switching symbols/sources, clears results on fetch failure, and hides expired snapshots. It never silently substitutes Binance results for Hummingbot.

Focused regression tests: `gradle :app:testDebugUnitTest --tests '*HummingbotOrderBookTest' --no-daemon`. Full validation remains the test/build command above. Codemagic accepts `feature/hummingbot-order-book` and runs the bridge tests before Android tests/build. Start `android-chart-pro-debug` on that branch if its GitHub webhook is unavailable. This source change does not include a signed release artifact.

- The live candlestick chart displays recent candles, a price grid, and Bollinger Bands (20, 2). Initial loading, periodic reconciliation and reconnection use the selected symbol. Late callbacks from replaced connections are ignored.
- Chart alert titles, history and deduplication keys include the symbol and timeframe. The newest 100 history items are retained. Master notification settings, direction filters where applicable, quiet hours, sound and vibration share one delivery policy.
- The multi-symbol scanner reconnects with backoff and loads candle history before resuming evaluation; switching continuous scanning off and on restarts it without reopening the app.
- The BTCUSDT backtest offers 7/30/90/180/360-day history through paginated requests and processes each candle once. It shows estimated net PnL, balance, closed exits, win rate, Profit Factor, max drawdown and recent closed events.
- Closed-trade PnL and open-position unrealized PnL are displayed separately. Equity/drawdown include estimated unrealized PnL and fees; intrabar extremes are estimates from OHLC, not tick-order reconstruction. Validate the same candle fixture and fill assumptions before comparing results with another engine.


