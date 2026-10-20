# BTC 5m Forecast (Android)

Standalone Android application dedicated to experimental BTC/USDT five-minute direction forecasts. It is separate from the BTCUSDT Chart Pro app module and does not place orders.

## Data source and limits

- Uses the public Binance Spot REST endpoint `https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1m&limit=1000`.
- Labels itself **Binance Spot proxy**. This is not Chainlink BTC/USDT Top of Book Data Streams and is not guaranteed to match any third-party market's official settlement source.
- Forecasts are created only from closed one-minute candles at a five-minute boundary. The target is five minutes after the reference time, and the target candle must have closed before evaluation.
- Missing/gapped/stale data is rejected rather than silently treated as consecutive.
- Stores pending forecasts and up to 1,000 settled paper results locally on the device.
- No exchange keys, trading permissions, or order placement are used.

## Model status

The current model is a transparent historical-frequency baseline. Its class probabilities are descriptive historical frequencies, not calibrated probabilities and not evidence of a tradable edge. Accuracy and Brier score are diagnostic only; keep the app in paper mode while collecting out-of-sample results.

## Build

Open this directory as an Android Gradle project with JDK 17 and Android SDK 35, or use the repository workflow **BTC 5m Forecast Android CI**. The workflow runs `gradle :app:testDebugUnitTest` and `gradle :app:assembleDebug`, then uploads `btc-5m-forecast-debug-apk` when both succeed.

Package: `com.kenznguyen.btc5mforecast`
