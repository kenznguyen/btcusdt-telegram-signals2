# Main Core Runtime Dependency Inventory and Integration Test Plan — 2026-11-18

## Scope and provenance

- Repository: `kenznguyen/btcusdt-telegram-signals2`
- Inventory target: `main`
- Exact main source SHA: `9490b64b232258604418257ef5f69bd17f4b9a3f`
- Main tree: 49 tracked blobs; recursive tree was not truncated.
- Core First source branch: `feature/core-operational-proof-20261112`
- Exact current Core First branch SHA inspected: `e6606e28a696374f31cd6db1ec0a1372d942d64d`
- Latest successful Core First operational workflow inspected: run [44272495963](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/44272495963), event `workflow_dispatch`, exact tested source SHA `ea8dc9159782a3da83cab2b84409698922bd281d`, conclusion SUCCESS.
- Workflow artifact: [ID 14413755795](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/44272495963/artifacts/14413755795), name `core-first-code-operational-proof-44272495963`, SHA-256 `86370ed99fb0895e560d60469334fd5f765c40c10c2ac764912041002e2e09d6`.
- Audit type: read-only Git tree/source/dependency inspection plus test-plan design. No source or runtime change.

## 1. Main inventory

The exact `main` tree has 49 tracked files. The following implementation packages required by the Common API/Core path are absent or materially incomplete:

| Package/path | Present on main | Missing implementation / consequence |
|---|---|---|
| `core_runtime/` | `test_api_facade.py` only | Missing `api_facade.py`, `runtime_factory.py`, `bundle_provider.py`, bundle validators, Continuous Runner, journal, cadence, preflight and order-book HTTP client. The facade test cannot import the production Core facade. |
| `pipeline/` | `api.py` only | Missing `values.py`, `decision.py`, `core_strategy.py`, `core_signal.py`, and the API/Core contract tests. |
| `paper_execution/` | Absent | Missing `ledger.py`, `equity.py`, risk control, simulated-account and paper execution dependencies. |
| `freqai_bridge/` | Absent | Missing `http_candles.py`, the strict T0 Candle Contract v1 HTTP consumer used by Core Bundle construction. |
| `risk_policy.py` | Absent | Missing shared Core risk policy constants imported by the API/ledger path. |
| `futures_intelligence/` | Absent | Missing T1 futures-intelligence import/validation consumer. |
| `integrations/` | Absent | Missing optional Hummingbot order-book bridge imported by the Common API. |
| `market_data/` | `test_write_gateway.py` only | Missing `api.py`, `storage.py`, `postgres.py`, store and other T0 implementation modules imported by the current main Common API. |

### Direct import blockers in main

At the inspected main SHA, `pipeline/api.py` imports these missing internal modules at module import time:

- `market_data.api.candle_query`
- `market_data.postgres.StoreUnavailable`
- `market_data.storage.create_store_from_env`
- `pipeline.values.stamp`

Additional runtime paths lazily import missing modules, including:

- `pipeline.decision.evaluate`
- `core_runtime.api_facade` (`preview_core` and `evaluate_core`)
- `paper_execution.ledger.PaperLedger` and dual-ledger/readiness functions
- `paper_execution.equity.parse_limits`
- `risk_policy.CORE_LEVERAGE`
- `futures_intelligence.import_collector`
- `integrations.hummingbot_bridge`

The focused test `ci/test_core_api_quality_snapshot.py` deliberately stubs import-time adapter symbols to isolate one already-fixed projection defect. Those stubs are valid for that narrow regression only; they are not a replacement dependency graph and must not be reused as proof of full API/Core integration.

## 2. Official source and dependency classification

### Core Runtime source

No separately published Core Runtime Python package or standalone Core Runtime repository was found in the accessible GitHub repositories. The project's active Core First implementation source is the existing branch:

- Repository: `kenznguyen/btcusdt-telegram-signals2`
- Branch: `feature/core-operational-proof-20261112`
- Current inspected branch SHA: `e6606e28a696374f31cd6db1ec0a1372d942d64d`

This is the project-authoritative Core First development source according to that branch's current Session Handoff. It is not an independently versioned external package and must not be installed from PyPI or silently copied into main. The branch is divergent from main; current GitHub compare reports 4,667 commits ahead and 101 behind (compare file listing is capped at 300). No open PR for this branch was found. Merge/reconciliation remains BLOCKED pending a separate complete review and approval.

The latest full Core-First operational proof is run #44272495963 at source SHA `ea8dc9159782a3da83cab2b84409698922bd281d`. The current branch is 86 commits ahead of that tested SHA. The bounded compare lists only documentation, T0 Stage-I, README and T0 manual-workflow changes. A direct tree/blob comparison confirmed the following Core implementation/test/workflow files are byte-identical between the tested SHA and current branch SHA:

- `core_runtime/api_facade.py` — `98dfc38008480a5bc686e9f03e4e09041b5ad54e`
- `core_runtime/runtime_factory.py` — `b2dbd2efe0076ad5e831682caea0bd5e4a4f8bd6`
- `core_runtime/bundle_provider.py` — `9d67f1600d4177e6f9756e366af6ef9319b27c19`
- `core_runtime/continuous_runner.py` — `a654d03bc2332eb14c0c2498a80882691920825c`
- `core_runtime/test_api_facade.py` — `f860d32c4047374dec4f574605a1c1b21ba1a58b`
- `pipeline/api.py` — `bb89b0bdf196f64b3ab9d9ac15b6597f333c583e`
- `pipeline/test_api.py` — `706a091b9f93587dce4ad61167dec1202bb1c59d`
- `freqai_bridge/http_candles.py` — `1f430c6d3a762deab9342e42072824661df3bf96`
- `paper_execution/ledger.py` — `6ff1dd23295b931aad39f2416e81c1736fdc57d1`
- `paper_execution/equity.py` — `40d6566294355c646839614c92f8fba6116b582c`
- `risk_policy.py` — `823d04748105b2996a28f2b09e3ce77bea073dce`
- `.github/workflows/core-live-data-operational-proof.yml` — `0c2d86d76d4d3281e3d7ffb9904a820cf30df547`

This establishes unchanged selected Core files since the tested SHA; it does not turn the historical run into a run against the current branch HEAD.

### T0 dependency

T0 remains an independent data asset. Core Bundle v1 consumes canonical candles through the read-only T0 Candle Contract v1 HTTP interface using `freqai_bridge.http_candles.CandleHttpClient` and environment configuration `T0_CANDLE_API_BASE_URL`, `T0_CANDLE_API_TOKEN`, and `T0_CANDLE_MAX_LAG_MS`. The client requests `GET /v1/candles`, validates identity, schema, coverage, freshness, availability timestamps and dataset version, and fails closed on contract/transport errors.

The T0 implementation package (`market_data/`) is present in the Core First source tree but absent from main. It must not be copied into Core as a workaround or coupled to Core's Paper database. The Core bundle path is designed around the HTTP contract; the independent T0 service's canonical database and Feeder remain outside this test plan.

### T1 dependency

Core consumes T1 Order Book V1 through `core_runtime.orderbook_http.OrderBookHttpClient`, configured by `T1_ORDERBOOK_API_BASE_URL` and `T1_ORDERBOOK_API_TOKEN`, using route `/internal/v1/orderbook/btcusdt`. It validates the T1 snapshot contract and uses loopback-only HTTP configuration.

The separate repository `kenznguyen/binance-futures-collector` exists (default branch `main`, inspected HEAD `d43a673451f7347e16a214612165c63da1b4339c`) and contains order-book collection code/documentation. However, the exact server-side provider implementing Core's `/internal/v1/orderbook/btcusdt` route was not found in that repository's inspected default-branch paths or the accessible repository code-search results. Therefore the T1 collector source is identified, but the exact HTTP service/provider source binding remains **NOT VERIFIED**. Do not assume the collector repository alone supplies the required API route.

### Python package dependencies

- Main `requirements-web.txt` blob `bfce94528a5ae2f6e4c5bcd644177a898d5646dc` currently lists Flask, Requests and Gunicorn only.
- Core First `requirements-web.txt` includes Flask, Requests, Gunicorn, Cryptography and `rfc8785`.
- Core First `requirements-market-data.txt` contains CCXT and Psycopg for the T0 market-data service.
- The Core operational workflow installs `requirements-web.txt`; internal Python packages are supplied by the pinned repository checkout, not pip.

Do not blindly copy all T0 dependencies into Core's web/test environment. Freeze a per-workflow dependency manifest after the exact import/test scope is agreed. Add `rfc8785` only as part of a reviewed dependency-manifest reconciliation, not as an isolated guess.

## 3. Existing Core First evidence and limits

- Workflow run #44272495963: SUCCESS, exact checkout SHA `ea8dc9159782a3da83cab2b84409698922bd281d`.
- All 38 operational workflow steps completed successfully.
- Artifact ID `14413755795`; artifact SHA-256 `86370ed99fb0895e560d60469334fd5f765c40c10c2ac764912041002e2e09d6`.
- The artifact report records Core entry/DCA, long/short lifecycle, mixed-writer stress, Shared Risk/Paper Ledger, T0/Paper storage isolation, T1/T2 order-book contracts and paper-only guards as PASS within its exact test boundary.
- Safety: `AI_EXECUTION_ENABLED=false`, no exchange credentials, `REAL_ORDERS_SENT=false`, no VPS/persistent runtime, no canonical T0 mutation.
- Real-market OOS profitability, production/runtime readiness, actual T0/T1 service reachability and live-trading readiness remain NOT VERIFIED / NOT AUTHORIZED.
- AI paper execution remains deferred in Core First. Core remains the only paper-executable strategy.

## 4. Proposed integration test plan — no execution authorized by this document

All tests should run against the existing Core First source branch at a newly recorded exact SHA after the owner authorizes the run. Do not merge, cherry-pick, rebase, reset or copy source to main to run these tests.

| Gate | Test scope | Required evidence / acceptance |
|---|---|---|
| I0 — Source and dependency lock | Pin exact branch SHA, tree SHA, Python version, all internal package paths and per-workflow external requirements. Import smoke test must use real modules, not module stubs. | Every required internal import resolves from the pinned checkout; dependency install is deterministic; no untracked or cross-branch source. |
| I1 — T0/T1 transport boundaries | Run T0 Candle HTTP client and T1 Order Book HTTP client contract tests against deterministic local HTTP fixtures. Exercise auth rejection, timeout, malformed/duplicate JSON keys, wrong identity, stale/future timestamps, gaps, oversized payload, TLS/loopback restrictions and fail-closed behavior. | T0 is read-only; T1 snapshot is contract-valid; no database/file sharing or direct canonical DB access by Core. |
| I2 — Core Bundle v1 | Validate M15/H1 identity, complete coverage, closed candles, first-observed availability, datasetVersion, asOf cut-off, T1 continuity/freshness, bundle canonicalization and immutable digest. | Invalid/missing/stale source data produces no Core intent; valid fixture produces a deterministic validated bundle. |
| I3 — Core API facade | Test preview and evaluate separately. Preview must use non-persistent bundle path and `submit=False`; evaluation must use Continuous Runner, recover incomplete cycles first, and fail closed on bad config/source SHA. | Preview has no journal/ledger mutation; evaluation has one deterministic cycle per eligible M15; duplicate cycle does not create a second order. |
| I4 — Core Strategy and Shared Risk | Test RSI/ADX/DI inputs, closed-candle gates, entry, WAIT, Smart DCA one-use rule, exits, short lifecycle, book validation, Kill Switch and risk rejection. Risk limits must come exclusively from the validated account/risk contract; no second independent limit set may override it. | Every new entry and DCA is admitted by the common Shared Risk Engine; recorded margin budget remains within 1% of account equity for each admitted order/adjustment; rejection creates no reservation/fill. |
| I5 — Paper Ledger and recovery | Run disposable SQLite tests for dual-ledger ownership, idempotency, concurrent/mixed writers, partial-fill process crash, journal/ledger reconciliation, read-only account risk snapshot and permitted risk reductions. | Atomicity, no cross-strategy ownership leakage, no T0/Paper path alias, no duplicate fill after restart, fail-closed recovery. |
| I6 — API + end-to-end Core First | Run Common API, Paper storage isolation, Core facade, Bundle Provider, Continuous Runner, Core entry/DCA, long/short lifecycle, Shared Risk/Ledger and T1/T2 HTTP integration suites. | All required suites pass on one exact SHA; no stubs for internal Core/T0 modules; all fixtures disposable; evidence includes logs and artifact digest. |
| I7 — Independent review and closeout | Independent review of the exact tested SHA, test diffs, workflow, risk authority, side effects and all unresolved findings. | No unresolved critical/high finding; source SHA and workflow/artifact provenance reconciled; Core First closeout explicitly approved before any Dual-Strategy work. |

### Test environment rules

- Use GitHub Actions as the default CI. Existing workflow: `.github/workflows/core-live-data-operational-proof.yml`.
- Use Python 3.12 as in the existing Core First workflow unless a separately reviewed compatibility change is proposed.
- Keep `AI_EXECUTION_ENABLED=false`; blank exchange credentials and persistent DB environment variables.
- Use only temporary/disposable SQLite databases and deterministic HTTP fixtures. Do not point tests at canonical T0 DB, production Paper DB, a VPS path or any persistent runtime.
- Do not start the T0 Feeder, connect to Binance/OKX, create/alter canonical storage, or send any exchange order.
- A local HTTP fixture validates the consumer contract, not actual T0/T1 service deployment. Any actual service-level acceptance needs a separate test endpoint and explicit owner approval.
- Record exact source SHA, workflow run ID/event, checkout SHA, all job conclusions, artifact ID/name/digest, test counts and independent review disposition.

## 5. Stop conditions and non-authorizations

- Do not merge or reconcile the divergent Core First branch into main as part of this inventory.
- Do not copy Core Runtime, Paper Ledger or T0 source from the feature branch into main as a CI workaround.
- Do not treat the focused main quality-snapshot test with stubs as full integration evidence.
- Do not invent or assume the T1 HTTP server/provider source; resolve its repository/path and version binding before actual service integration.
- Do not alter T0, canonical DB, Feeder, VPS, deployment, credentials, Shared Risk policy, Paper schema or Core strategy thresholds.
- Do not implement Dual-Strategy Intelligence or enable AI paper execution until Core First closeout and a separate owner approval.
- No live trading or real orders.

## 6. Disposition

| Item | Status |
|---|---|
| Main source tree inventory | PASS — read-only |
| Missing Core Runtime dependency list | PASS — direct import/path evidence |
| Core First source location | IDENTIFIED — active project branch; not a released package |
| T0 HTTP consumer contract | IDENTIFIED |
| T1 HTTP consumer contract | IDENTIFIED |
| T1 server/provider source binding | NOT VERIFIED |
| Existing Core First exact-SHA operational CI | PASS — historical exact tested SHA |
| Current Core First HEAD full workflow run | NOT RUN |
| Main full Core/API integration | BLOCKED — implementation dependencies absent |
| Proposed integration plan | COMPLETE — not executed |
| Merge/reconciliation | BLOCKED / NOT AUTHORIZED |
| Dual-Strategy expansion | DEFERRED |

Next action: resolve and pin the T1 HTTP provider source/version, then obtain owner authorization to run the existing Core First operational workflow on the exact current feature-branch HEAD. No source change is needed for this inventory increment.
