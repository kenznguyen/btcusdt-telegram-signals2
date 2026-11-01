# Hummingbot Order Book bridge

See [the five-layer architecture](../docs/FIVE_LAYER_ARCHITECTURE.md) for the proposed collector, microstructure, FreqAI, execution and React/APK integration. That design is a roadmap; this adapter only implements read-only Hummingbot snapshots.

The first canonical BTCUSDT candle store, CCXT importer and read-only API are documented in [market_data/README.md](../market_data/README.md).

This optional server adapter exposes Hummingbot's public-market order book to
BTCUSDT Chart Pro. It uses Python's standard library and does not alter the
Telegram webhook. Exchange credentials are not required for public market data;
Hummingbot API login credentials stay on the server.

## Contract

`GET /v1/order-book?symbol=BTCUSDT` requires
`Authorization: Bearer <HB_BRIDGE_TOKEN>`. Its response is:

```json
{
  "source": "hummingbot",
  "symbol": "BTCUSDT",
  "connector": "binance_perpetual",
  "observedAtMs": 1800000000000,
  "bids": [{"price": 99900.0, "quantity": 2.0}],
  "asks": [{"price": 100100.0, "quantity": 3.0}]
}
```

The values above illustrate the schema; the bridge never serves demo data.
`observedAtMs` preserves Hummingbot's snapshot retrieval timestamp. It does **not**
establish exchange-event freshness or prove that a WebSocket tracker is synced.
The bridge rejects snapshots older than 30 seconds, over 5 seconds in the future,
for another pair, with non-finite/invalid levels, or with crossed prices. It
returns an error when Hummingbot is unavailable; it does not switch data sources.

## Run

Run Hummingbot API separately. Set these environment variables for the bridge:

| Variable | Meaning |
| --- | --- |
| `HB_API_URL` | Internal Hummingbot API base URL, e.g. `http://127.0.0.1:8000` |
| `HB_API_USER` | Hummingbot API username |
| `HB_API_PASSWORD` | Hummingbot API password |
| `HB_BRIDGE_TOKEN` | Separate strong random read-only access token for the APK |
| `HB_SYMBOLS` | Comma-separated allowed symbols; default `BTCUSDT,ETHUSDT` |
| `PORT` | Local development port; default `8787` |

Generate a bridge token with `python3 -c 'import secrets; print(secrets.token_urlsafe(32))'`.
Store credentials in the hosting environment; do not commit them. The bridge
returns HTTP 503 until all four required connection/token variables are set.

Before reading a pair, initialize its continuous tracker through the Hummingbot
API's authenticated `POST /market-data/trading-pair/add` endpoint:

```json
{"connector_name":"binance_perpetual","trading_pair":"BTC-USDT","timeout":30}
```

Repeat for every allowed symbol (`ETH-USDT`, etc.). This is operator setup; the
bridge itself only calls `POST /market-data/order-book`, with the selected pair
and `depth=20`. That endpoint may fall back to a fresh REST snapshot when the
tracker is unavailable. No order placement endpoints are called.

From the repository root, local development uses:

```bash
python3 -m integrations.hummingbot_bridge
```

For a server, install the repository's existing `requirements-web.txt` and run:

```bash
gunicorn --bind 127.0.0.1:8787 --workers 1 --threads 4 --timeout 20 integrations.hummingbot_bridge:application
```

Expose the bridge through an HTTPS reverse proxy, leaving Hummingbot API private.
In the APK, enter the bridge's HTTPS base URL and its separate bearer token.
`GET /health` is an unauthenticated process health check, not proof that upstream
market data is available. Existing app signing and application ID are unchanged.

## Verify

```bash
python3 -m unittest integrations.test_hummingbot_bridge -v
```

Tests exercise the actual WSGI handler and mock only the upstream HTTP boundary.
Live validation additionally needs a running Hummingbot API and an HTTPS bridge.

Upstream contract verified against
[`hummingbot/hummingbot-api` at `7ae108f11bf20651682dbdff639a8717068c5883`](https://github.com/hummingbot/hummingbot-api/tree/7ae108f11bf20651682dbdff639a8717068c5883):
[`routers/market_data.py`](https://github.com/hummingbot/hummingbot-api/blob/7ae108f11bf20651682dbdff639a8717068c5883/routers/market_data.py),
[`models/market_data.py`](https://github.com/hummingbot/hummingbot-api/blob/7ae108f11bf20651682dbdff639a8717068c5883/models/market_data.py),
and [`services/market_data_service.py`](https://github.com/hummingbot/hummingbot-api/blob/7ae108f11bf20651682dbdff639a8717068c5883/services/market_data_service.py).
