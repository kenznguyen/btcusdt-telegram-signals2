# BTCUSDT Live Alerts (Android)

Standalone Android signal-only monitor for BTCUSDT perpetual. The app uses public Binance USDⓈ-M Futures data and never places orders or requests trading API keys.

## Strategy rules ported from bot.py/backtest.py

- M15 entry + last fully closed H1 trend filter; RSI(14), DMI/ADX(14), H1 ADX entry threshold 20.
- LONG: H1 +DI > -DI and ADX > 20; M15 RSI crosses upward through 30.
- SHORT: H1 -DI > +DI and ADX > 20; M15 RSI crosses downward through 70.
- TP: LONG RSI >= 76 or SHORT RSI <= 24, and estimated ROE >= +5%.
- DCA: estimated ROE <= -20%, M15 ADX > 45; LONG RSI > 20 and rising; SHORT RSI < 80 and falling; one DCA maximum.
- Soft SL: estimated ROE threshold -35% touched, H1 direction reverses with ADX > 35, and two consecutive candles confirm reversal.
- Emergency SL: -90% ROE price threshold; checked before Soft SL and TP.
- Leverage 13x, default initial margin 50% of simulated balance, DCA margin 100% of initial order margin, estimated taker fee 0.05% per side, adverse slippage 5 bps.
- DCA is skipped if the simulated wallet balance cannot cover the additional reserved margin, matching the conservative backtest behavior.
- Simulated state, position, processed candle timestamp, balance, and recent events are persisted locally. First launch warms up indicators and evaluates only the newest closed M15 candle instead of replaying old historical alerts.
- A foreground data-sync service performs monitoring while Android allows it to run. Battery settings, force-stop, manufacturer restrictions, and Android foreground-service limits may still interrupt monitoring.

## Validation

GitHub Actions runs JUnit strategy unit tests and assembles a debug APK. Tests cover entry filters/crosses, DCA rules, TP conditions, stop conditions, gap/slippage pricing, ROE thresholds, indicator warmup, and persisted state.

A successful build and unit tests do not prove numerical parity with TradingView or live fills. Indicator results must still be compared against the Python engine on the same candle fixture before relying on alerts. Data source is Binance Futures while the existing Python bot/backtest use OKX candles, so prices and indicator values can differ slightly. This app is a simulation/alerting tool only, not financial advice.

## Build

Open this directory in Android Studio or use the Android APK GitHub Actions workflow. The downloadable artifact is a debug APK; it is not a signed Play Store release.

Package: `com.kenznguyen.btclivealerts`
