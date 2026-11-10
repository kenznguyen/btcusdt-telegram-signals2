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
| `market_data/storage.py` | `13fe1ae01ebb5318b69e69eef3e512d207f74c49` | Side-effect-free SQLite/PostgreSQL store factory and environment backend selection |
| `market_data/test_storage.py` | `b2635f575323187f936360d033b4fc630d8138e0` | Store factory, SQLite default, invalid backend, no implicit DB creation and storage contract |
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

### C-01 — duplicate backend environment parsing

- `feeder_service.build_production_runtime()` reads and normalizes `MARKET_DATA_BACKEND` to choose TLS validation and lease construction.
- It then calls `storage.create_store_from_env(values)`, which reads and normalizes the same environment key again to choose the store.
- This is a genuine duplicated selection decision across two modules.
- Possible future simplification: construct the store once and branch on the resulting concrete store type for the matching lease/TLS path, or introduce one explicit immutable backend selection result. The smallest option must be chosen only after reviewing the full builder contract.
- Risks to preserve: unknown backend must fail closed; PostgreSQL must require verified TLS and the fixed canonical lease identity; PostgreSQL must reject a separate SQLite lease DB; SQLite must preserve same-file candle/lease semantics; no implicit DB/schema provisioning; owner ID remains per-process and unconfigurable.
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

A future change must first map every caller and test path for `build_production_runtime`, `create_store_from_env`, `create_store`, and environment parsing, including the active GitHub Actions jobs.

Minimum regression cases to preserve:
- missing backend defaults to SQLite;
- explicit SQLite backend and configured database path;
- unknown backend fails closed;
- PostgreSQL without DSN fails closed;
- PostgreSQL without `sslmode=verify-full` or remote hostname fails closed;
- PostgreSQL canonical lease identity is fixed;
- PostgreSQL rejects `T0_FEEDER_LEASE_DB`;
- SQLite requires canonical DB or explicit lease DB and preserves the same-file invariant;
- configured owner ID is rejected and generated owner identity remains per-process;
- recovery lookback and all validated config bounds remain unchanged;
- constructing the runtime does not provision canonical SQLite storage or run migrations;
- readiness remains after recovery and scheduler startup only.

Current reviewed tests cover several lower-level factory and lifecycle contracts, but a focused production-builder contract suite was not identified in this bounded inspection. Full branch-wide caller/workflow coverage is **NOT VERIFIED**.

## 6. Status and limits

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

## 7. Next safe step

Complete a read-only branch-local caller and workflow inventory for the production builder and store factory, then define a focused regression matrix for C-01. Only after that review should a separate implementation approval be considered. Do not change the shared requirements file, PostgreSQL adapter, canonical SQLite path, workflow filters, or test denominator as part of this candidate.
