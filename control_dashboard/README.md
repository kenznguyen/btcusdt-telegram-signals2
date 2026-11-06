# Chart Pro control dashboard

React frontend for the paper-only five-layer API in `pipeline/CONTRACTS.md`.
It contains no demo market values, exchange credentials, trading SDK, or live-order
path. Read and control bearer tokens stay in React memory and are cleared on
disconnect/reload; they are never put in localStorage, sessionStorage, cookies or
URLs. The browser talks to the common backend directly, without third-party fonts,
charts, analytics or API proxies.

## Build and serve

Use Node 24 and npm 11.9.0 (the declared manager). From this directory:

```bash
npm ci --ignore-scripts
npm test
npm run build
npm audit --audit-level=high
```

Serve `dist` through the common API at `/control/`. Vite's base is `/control/`.
The initial API address is the current origin, so the production reverse proxy can
serve the UI and `/v1/*` together without CORS. For local UI development, start the
common backend on `127.0.0.1:8789`, run `npm run dev`, and leave the API address
blank. Vite proxies `/v1/*` to that fixed local backend, keeping browser requests
on the same origin. No server CORS change is needed. Remote API addresses require HTTPS. HTTP is accepted
only for localhost/127.0.0.1/IPv6 loopback development.

The server uses `MARKET_DATA_TOKEN` for GETs and a separate `CONTROL_TOKEN` for
paper operations. The latter only enables the UI when the server confirms
`mode=PAPER`, `liveTradingSupported=false` and a paper ledger is available.
Controls wait for server responses and never optimistically claim a fill or
automatically retry a timed-out POST. Polling runs every five seconds while the
page is visible, cancels replaced requests, and clears each failed data source.

## Dependency provenance and verification limits

The authoritative npm lock was reduced from the already inspected Capture Desk
lock at `waynemason1/binance-futures-collector` commit
`bc4f0ef633fbeee4a49defd72827f17162693805`, retaining exact npm versions, integrity
hashes and transitive dependency metadata, then normalized successfully by
`npm install --package-lock-only --offline --ignore-scripts`. This project uses
only React 18.3.1, React DOM 18.3.1 and Vite 8.1.3; no Capture Desk application code
or unused UI libraries are included. `.npmrc` disables dependency scripts;
the optional macOS `fsevents` install script remains disabled.

The execution sandbox blocks the npm registry and the package tarballs are not
cached, so a clean dependency installation, Vite build, npm audit and full browser
render were **not verified here**. The node:test checks exercise URL/token
handling, closed-candle query windows, JSON/error contracts and response limits
without requiring dependencies. Codemagic must complete the frozen install,
build and audit before the dashboard can be considered verified.
