# BTCUSDT Live Alerts (Android)

Standalone Android app prototype for viewing Binance USDⓈ-M BTCUSDT perpetual market data and receiving local strategy alerts. It does **not** place orders and must never contain trading API keys.

## Current scaffold
- Kotlin + Jetpack Compose
- Public Binance Futures REST klines and mark price (no API key)
- M15 chart with timeframe selector for M15/H1
- Local RSI/ADX calculation and notification permission request
- Separate Android project so existing Python bot/dashboard are not changed

## Important limitations
This is the initial scaffold, not a validated port of the existing Python strategy. DCA/TP/Soft SL/Emergency SL and persistent position simulation must not be considered production-ready until ported and compared against Python fixtures. Live monitoring in background is not yet implemented; Android may suspend polling when the app is backgrounded.

## Build
Open this directory in Android Studio (Jellyfish or newer), let Gradle sync, then Build > Build APK(s). Or use the repository workflow to build a debug APK.

Package: `com.kenznguyen.btclivealerts`
