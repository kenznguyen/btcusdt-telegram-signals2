# BTCUSDT Signal Desk — Android

Kotlin + Jetpack Compose native Android starter for the existing signal-only bot.

## Screens
- Dashboard
- Signals
- Backtest

The UI intentionally displays empty/unconnected states. It does not fabricate live prices, signals, or performance metrics.

## Build
1. Open the `android/` directory in Android Studio.
2. Use JDK 17.
3. Allow Gradle sync.
4. Run the `app` configuration on an Android emulator/device.
5. Build an APK using **Build > Build APK(s)**.

## Current data architecture
The repository currently runs the scanner and backtest in GitHub Actions. The Flask app in the root `app.py` is a Telegram webhook/command bridge, not a dashboard API. The backtest workflow uploads JSON/CSV files as workflow artifacts, but artifacts are not a stable realtime API and expire.

Next implementation phase:
- Inspect and define a sanitized read-only JSON schema for signal state and backtest summary.
- Expose data through an authenticated backend (recommended) or another controlled data store.
- Make the Android app call only that backend over HTTPS.
- Do not embed GitHub PATs, Telegram tokens, or exchange API keys in the APK.
- Keep all features read-only; no order placement.
