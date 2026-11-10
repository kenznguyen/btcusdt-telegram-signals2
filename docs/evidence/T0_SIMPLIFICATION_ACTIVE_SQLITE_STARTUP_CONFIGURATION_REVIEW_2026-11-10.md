# T0 Simplification — Active SQLite Startup/Configuration Review

- Date: 2026-11-10
- Repository: `kenznguyen/btcusdt-telegram-signals2`
- Branch: `feature/t0-centralized-data-feeder-p1-20261101`
- Exact documentation baseline after L4-Minimum administrative closure: `c66c34ab709d6677530c0a745d37791034331651`
- Operation class: READ-ONLY SOURCE REVIEW + DOCUMENTATION RECORD
- Scope: inspect ownership of active SQLite feeder configuration and startup composition; identify only evidenced duplication candidates.
- No source, test, package, workflow, runtime, VPS, database, provider, secret, permission, network or data changes.

## 1. Decision

**KEEP the current startup/lifecycle boundaries. Do not refactor in this increment.**

One narrow candidate for a future behavior-preserving simplification was identified: the production builder and storage factory independently parse `MARKET_DATA_BACKEND`. This is a configuration-source duplication, but it is not yet approved for implementation because builder-specific regression coverage and the complete caller/workflow denominator have not been established.

No evidence supports merging lifecycle, scheduler, recovery, storage, lease or writer responsibilities.

## 2. Exact source inventory

| File | Blob SHA | Reviewed responsibility |
|---|---|---|
| `market_data/feeder.py` | `935d295ef42c94482a48ce6ccdc927ebfa4c7e22` | Validated `FeederConfig`; retry/scheduler/recovery/runtime lifecycle; heartbeat and drain |
| `market_data/feeder_service.py` | `bdcecf6bc98a2ff070f83098d2c50154a160c99c` | Environment parsing; backend/lease selection; runtime composition; systemd notify and process signals |
| `market_data/api.py` | `81733c9b6de811cbebb2f5d472d41f37f337990c` | Read API preflight and store-factory call |
| `market_data/storage.py` | `13fe1ae01ebb5318b69e69eef3e512d207f74c49` | Side-effect-free SQLite/PostgreSQL store factory and environment backend selection |
| `market_data/test_storage.py` | `b2635f575323187f936360d033b4fc630d8138e0` | Store factory, SQLite default, invalid backend, no implicit DB creation and storage contract |
| `market_data/test_api.py` | `49df7e0bec12908adae67f18a4aa19063e461093` | API auth, SQLite configuration, missing store, explicit PostgreSQL-without-DSN and HTTP error semantics |
| `market_data/test_postgres_feeder_runtime.py` | `dba7b3a61b3963984c58309e7d334b61c0889256` | Production builder PostgreSQL TLS, host, lease identity, forbidden SQLite lease DB and per-process owner ID contracts |
| `market_data/test_feeder_lifecycle.py` | `5797d51e3165721863ceacb1fac76f44055f18a7` | Runtime lifecycle, lease fencing, recovery, startup and shutdown behavior |
| `market_data/test_feeder_process_restart.py` | `607228708c174bfa3af437b8a4d419f30a7030c3` | Isolated temporary-SQLite process crash/restart and generation fencing |
| `market_data/test_feeder_scheduler.py` | `695c53548c58763cffecc86626171f6a691e75fd` | Scheduler defaults and poll/close-boundary behavior |
| `market_data/test_controlled_ingestion_acceptance.py` | `92c76fea839858f128ed228ac25b36b6bb8ec375` | Controlled ingestion acceptance fixture |
| `market_data/README.md` | `d90f84f8135c8ab9da1b57863e145d86565bf179` | Operator-facing canonical data and API contract |

The above are exact GitHub blob identities read from the active branch. This is a bounded inventory, not a claim that every repository caller or workflow has been enumerated.

## 3. Configuration ownership map

1. `FeederConfig` is the validated runtime configuration object. It owns poll interval, close grace, retry limits, lease TTL/heartbeat and timeframe tuple.
2. `build_production_runtime()` translates environment values into concrete dependencies and `FeederConfig`; it generates a per-process owner ID and passes the recovery lookback separately.
3. `create_store_from_env()` owns store construction and independently normalizes `MARKET_DATA_BACKEND`; constructors remain side-effect free.
4. `build_runtime()` composes the selected store, lease authority, one fenced writer gateway, recovery coordinators and scheduler. SQLite keeps the same-database candle/lease invariant.
5. `FeederRuntime` owns lease acquisition, WAL keeper lifecycle, recovery-before-readiness, scheduler start, heartbeat, lease-loss response and graceful drain.
6. `run_service()/main()` own process-level SIGINT/SIGTERM handling and systemd READY/STOPPING notification. Readiness is emitted only after `runtime.start()` succeeds.

These boundaries have distinct responsibilities and should remain separate.

## 4. Candidate and non-candidates

### C-01 — backend environment selection is repeated across API, feeder builder and store factory

- `market_data/api.py` independently normalizes `MARKET_DATA_BACKEND` for the SQLite-path preflight, then calls `create_store_from_env()` which normalizes the same key again. The preflight currently occurs before bearer authorization/query processing; changing its location/order may change externally visible HTTP status behavior.
- `feeder_service.build_production_runtime()` independently normalizes `MARKET_DATA_BACKEND` to choose PostgreSQL TLS validation and lease construction, then calls `create_store_from_env(values)` which normalizes it again to choose the store.
- `storage.create_store_from_env()` is therefore not the only owner of the backend decision. The API and production builder each perform a preliminary decision for their own distinct guards.
- This is a repeated configuration decision, but not yet proven to be safely collapsible into one helper: API preflight/status ordering and PostgreSQL TLS/lease gates are behavior contracts that must remain intact.
- Possible future simplification: define one side-effect-free backend resolution result (backend enum/type plus validated required fields) consumed by API, feeder builder and store construction, only if it preserves pre-auth API behavior, fail-closed invalid-backend handling, and PostgreSQL TLS/lease restrictions. Do not move store construction earlier in the API request without proving status/auth ordering remains identical.
- Risks to preserve: unknown backend must fail closed; SQLite missing DB remains UNCONFIGURED; PostgreSQL requires verified TLS and fixed canonical lease identity; PostgreSQL rejects a separate SQLite lease DB; SQLite preserves same-file candle/lease semantics; no implicit DB/schema provisioning; owner ID remains per-process and unconfigurable.
- Disposition: **CANDIDATE — NOT IMPLEMENTED / NOT APPROVED**.

### N-01 — timeframe duplication

- `FeederConfig` defaults to `("15m", "1h")`; production builder explicitly supplies the same canonical tuple.
- This is not yet proven harmful: `FeederConfig` is also a testable/general runtime value, while production selection intentionally fixes canonical T0 frames.
- Disposition: **KEEP pending evidence of drift or maintenance defect**.

### N-02 — retry defaults repeated

- `FeederConfig` supplies retry values to `FeederRuntime`, which constructs `RetryPolicy`; `RetryPolicy` also has standalone defaults.
- The runtime path explicitly passes config values, so the duplicate defaults do not demonstrate two active authorities.
- Disposition: **KEEP**.

### N-03 — close-grace passed to scheduler and recovery

- The same validated `FeederConfig.close_grace_seconds` is consumed by scheduler and startup recovery to preserve one closed-candle boundary policy.
- This is intentional policy reuse, not duplicate configuration ownership.
- Disposition: **KEEP**.

### N-04 — process readiness and runtime readiness

- `FeederRuntime` establishes internal readiness only after lease acquisition, WAL keeper setup, recovery and scheduler startup. `run_service()` then publishes systemd READY.
- These are separate internal and supervisor-facing contracts, not duplicate lifecycle owners.
- Disposition: **KEEP**.

## 5. Regression and evidence gaps before any C-01 implementation

A future change must preserve both the store-selection contract and the distinct API/feeder guards.

**Existing coverage found (static inspection only; tests were not run):**
- `test_storage.py`: default SQLite factory, explicit PostgreSQL DSN fail-closed, unknown backend rejection, side-effect-free factory, no DB creation on missing SQLite read, SQLite factory/write/read contract.
- `test_api.py`: bearer authorization, missing SQLite path returns `UNCONFIGURED`, missing DB returns `STORE_UNAVAILABLE`, PostgreSQL without DSN returns `STORE_UNAVAILABLE`, read-only and response-contract behavior.
- `test_postgres_feeder_runtime.py`: production builder PostgreSQL selection, verified-TLS requirement, remote hostname requirement, accepted DSN forms, per-process owner generation, fixed canonical lease name and rejection of a separate SQLite lease DB.
- `test_feeder_lifecycle.py` and `test_feeder_process_restart.py`: runtime lease/recovery/readiness/drain and isolated SQLite crash/restart behavior. These do not establish that the production builder's SQLite branch is covered.
- The systemd/API integration script composes `FeederRuntime` and `run_service` directly; it does not call `build_production_runtime()`.

**Additional regression cases needed before any C-01 change:**
- production builder with absent backend selects SQLite using `MARKET_DATA_DB`;
- production builder with explicit `MARKET_DATA_BACKEND=sqlite`;
- production builder rejects unknown backend before constructing an exchange/runtime;
- SQLite missing DB and explicit `T0_FEEDER_LEASE_DB` semantics, including same-file invariant;
- store factory and API preflight resolve the same backend without changing API's current pre-auth `UNCONFIGURED` / auth `401` / store `503` ordering;
- PostgreSQL builder cases above remain unchanged;
- constructing the SQLite production runtime does not create the canonical database or run migrations;
- recovery lookback and all validated config bounds remain unchanged;
- readiness remains after lease acquisition, WAL keeper setup, recovery and scheduler startup only.

The active workflow inventory identifies the full `market_data` regression job and separate PostgreSQL qualification jobs, but no workflow run was executed in this review. Full branch-wide caller/trigger coverage remains **NOT VERIFIED**.

## 6. Workflow and caller inventory (bounded)

Direct references found in the inspected active `market_data` package:
- `build_production_runtime()` is defined in `feeder_service.py` and called by that module's `main()`.
- `create_store_from_env()` is called by `api.py` and `feeder_service.py`; it is defined in `storage.py`.
- `api.py` has its own backend preflight before calling the factory. This is a third read of the same setting, with an externally visible pre-auth response-order implication.
- The bounded scan covered the `market_data` package files listed by the active-branch directory API. It does not prove there are no references elsewhere in the repository.

Relevant workflow contracts read from the active branch:
| Workflow | Blob SHA | Relevant scope |
|---|---|---|
| `.github/workflows/t0-single-writer-gateway-red.yml` | `2d836c6c835f414efa62137abf7b97b7bcd6d5ec` | Full `market_data` regression, lifecycle, process restart, consumer parity, plus separate PostgreSQL qualification jobs |
| `.github/workflows/t0-systemd-feeder-api-integration.yml` | `64476a3dd281eb69b92d29f3783570107c4ab48e` | Compiles and invokes a CI integration script that composes `FeederRuntime` and `run_service`; inspected script does not call `build_production_runtime()` |
| `.github/workflows/t0-sqlite-readonly-sandbox.yml` | `a41e63cc7581606c6fb1bea264c1340d6448355d` | SQLite sandbox contract; source path filters include feeder/service and write-gateway modules |
| `.github/workflows/t0-manual-validation.yml` | `395ae93274a9202f14ab63d528be5cd582c30149` | Selectable manual gates; scheduler/retry/recovery/lease/health plus other T0/research gates |
| `.github/workflows/p5-3-11-g2-integration-green.yml` | `3b75fdbf34768a315e5ed025b2ba0015ce138b17` | Broad G2 denominator includes feeder lifecycle/scheduler/retry/recovery, storage and API tests |
| `.github/workflows/t2-freqtrade-2026-9-strategy-smoke.yml` | `89fe779e88c11c9a1598d2138286b7d4bfe7742b` | `market_data/**` path filter; T2 HTTP consumer regression |
| `.github/workflows/t2-http-consumer-red.yml` | `7690780e076c317345879dcef081951e78cf2c6a` | T2 HTTP consumer tests; relevant compatibility gate |

The workflow inventory is based on exact active-branch workflow blobs and inspected command/path lines. No workflow was run. The complete repository-wide caller and trigger denominator remains NOT VERIFIED.

## 7. Status and limits

- Exact reviewed source/document blobs read from active branch: **PASS**.
- Configuration ownership map for inspected path: **PASS**.
- C-01 candidate identified: **PASS — static observation only**.
- Complete repository-wide caller/import/install/workflow scan: **NOT VERIFIED**.
- Focused production-builder regression denominator: **NOT VERIFIED**.
- Tests/compile/dry-run: **NOT RUN**.
- GitHub Actions: **NOT DISPATCHED**; no run or artifact claimed.
- Independent review: **NOT PERFORMED**.
- Runtime/VPS/SSH/DB/provider access: **NOT PERFORMED**.
- No source or behavior changed.

## 8. Next safe step

Complete a read-only branch-local caller and workflow inventory for the production builder and store factory, then define a focused regression matrix for C-01. Only after that review should a separate implementation approval be considered. Do not change the shared requirements file, PostgreSQL adapter, canonical SQLite path, workflow filters, or test denominator as part of this candidate.
