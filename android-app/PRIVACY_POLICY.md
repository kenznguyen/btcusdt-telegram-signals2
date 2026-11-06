# BTCUSDT Chart Pro — Privacy Policy

**Status:** Draft for product review. **Last updated:** 19 October 2026.

BTCUSDT Chart Pro is an informational chart, indicator, simulation and alerting application. It does not place trades and does not ask users for exchange API keys.

## Information processed by the app

- **Market data:** The app connects to Binance USDⓈ-M Futures public market-data endpoints to retrieve BTCUSDT candles and mark-price data.
- **On-device settings and history:** Chart preferences, alert preferences, simulated strategy state, simulated positions, backtest state and recent alert/event history are stored locally on the device using Android app preferences.
- **Notifications:** If enabled and permitted by Android, the app posts local notifications for supported chart alerts and strategy events.
- **Permissions:** The app requests internet access and notification/foreground-service permissions required for market monitoring and notifications.

## Sharing and advertising

The app is designed not to upload local alert history, chart preferences or simulated account state to the developer. Market-data requests go to the configured market-data provider. This draft does not make claims about data handling by that provider; consult its privacy documentation.

The current Android implementation does not require a user account or exchange credentials. Before public release, the publisher must verify the complete release build and all bundled dependencies for analytics, crash reporting, advertising SDKs or other network destinations and update this policy if any are added.

## Retention and deletion

App preferences and local history remain on the device until the user clears them or uninstalls the app. Android system backups are disabled in the app manifest. Uninstalling the app removes its private local app data under normal Android behavior.

## Children

The app is a financial-market information tool and is not designed for children.

## Financial risk

Charts, indicators, alerts and backtest results are informational simulations, not investment advice or a promise of performance. Data, calculations, fees, slippage and execution assumptions may differ from live trading conditions. Users are responsible for their own decisions.

## Contact and publication

Before publishing, replace this section with the legal name and a monitored contact address for the app publisher, and host this policy at a stable public HTTPS URL. Do not submit this draft as the final Play Store privacy-policy URL without completing that review.

