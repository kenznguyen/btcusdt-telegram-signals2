# T0 Simplification — SQLite Runtime Configuration Ownership Audit

- Date: 2026-11-10
- Repository: `kenznguyen/btcusdt-telegram-signals2`
- Branch: `feature/t0-centralized-data-feeder-p1-20261101`
- Exact inspected branch HEAD: `0393024d11a9b31b41d5b35e45030b4a203e4b41`
- Operation class: READ-ONLY STATIC SOURCE/TEST REVIEW
- Scope: map environment/configuration ownership across Feeder startup, storage selection, SQLite initialization and the read-only Candle API; identify behavior-preserving simplification candidates.
- No source, tests, package, workflow, schema, runtime, VPS, database, provider, secret, permission or data changes. No tests or Actions were run.

## 1. Result

**PARTIAL — configuration ownership is understandable; no sufficiently safe simplification is proven.**

The runtime has three intentional boundaries:
1. Feeder process composition and validation in `market_data.feeder_service`.
2. Backend/store construction in `market_data.storage`.
3. Read-only API process configuration and request authentication in `market_data.api`.

A small repeated backend selection read exists between the Feeder composition and storage factory. This is not enough evidence to justify a new configuration abstraction or refactor. The API's preflight configuration checks also preserve a distinct `UNCONFIGURED` response before store access; removing them without a contract-preserving replacement could change externally visible behavior.

## 2. Exact source and test evidence

| Path | Blob SHA | Observed responsibility |
|---|---|---|
| `market_data/feeder_service.py` | `bdcecf6bc98a2ff070f83098d2c50154a160c99c` | Reads environment, validates backend-specific lease/DSN constraints, constructs FeederConfig and composes runtime |
| `market_data/feeder.py` | `935d295ef42c94482a48ce6ccdc927ebfa4c7e22` | Defines validated FeederConfig and runtime/scheduler/lease lifecycle |
| `market_data/storage.py` | `13fe1ae01ebb5318b69e69eef3e512d207f74c49` | Owns SQLite/PostgreSQL store factory and fail-closed backend selection |
| `market_data/api.py` | `81733c9b6de811cbebb2f5d472d41f37f337990c` | Owns API token check, read-only request contract, API store creation and development server port |
| `market_data/initialize_sqlite.py` | `58bd2deba66cc667bad8d6446c5ff54e7f5dd240` | Explicit empty-only canonical SQLite initialization |
| `market_data/write_gateway.py` | `b2029d9db15fe39dcbe575acfeb6df1b16e16acd` | Same-database lease fencing and SQLite WAL lifecycle support |
| `market_data/store.py` | `4e1b0c54bd56455abe5be0e5c7d0807e63e0bc78` | Canonical Candle schema, validation and SQLite read/write primitives |
| `market_data/test_storage.py` | `b2635f575323187f936360d033b4fc630d8138e0` | Store factory, no-fallback and side-effect-free read contracts |
| `market_data/test_api.py` | `49df7e0bec12908adae67f18a4aa19063e461093` | API authentication, unconfigured response, backend fail-closed and read-only contract |
| `market_data/test_postgres_feeder_runtime.py` | `dba7b3a61b3963984c58309e7d334b61c0889256` | PostgreSQL runtime composition, same-DSN fencing and verified TLS contracts |
| `market_data/test_initialize_sqlite.py` | `9823f42fa1b346c7c5b96786eec7e996484b692d` | Empty-only initialization and preservation of pre-existing files |
| `market_data/test_feeder_lifecycle.py` | `5797d51e3165721863ceacb1fac76f44055f18a7` | Lease/recovery/readiness/shutdown ordering contracts |
| `market_data/test_feeder_health_api.py` | `a3d11257a0c914835a86a8a6b5502bcf93c800a2` | Liveness/readiness/data-freshness contract |

## 3. Configuration ownership map

| Configuration | Owner | Use | Assessment |
|---|---|---|---|
| `MARKET_DATA_BACKEND` | Feeder composition + storage factory; API preflight + storage factory | Selects SQLite or explicit PostgreSQL | Repeated selection read, but each boundary enforces its own composition or response contract |
| `MARKET_DATA_DB` | Storage factory; Feeder lease composition; API preflight | Canonical SQLite path and same-DB lease default | Same logical setting crosses process boundaries; not safe to collapse without a shared immutable process config contract |
| `MARKET_DATA_POSTGRES_DSN` | Storage factory + Feeder PostgreSQL TLS/lease composition | Optional backend connection and lease/write authority | Separate validation is intentional; keep fail-closed |
| `T0_FEEDER_LEASE_DB` | Feeder composition | Explicit SQLite lease path; PostgreSQL rejects it | KEEP |
| `T0_FEEDER_LEASE_NAME` | Feeder composition | PostgreSQL canonical lease identity | KEEP |
| `T0_FEEDER_OWNER_ID` | Feeder composition | Explicitly rejected; owner capability is generated per process | KEEP security rejection |
| `T0_FEEDER_*SECONDS / RETRY_ATTEMPTS` | Feeder composition -> FeederConfig | Scheduler/retry/lease timing | Single conversion/validation boundary; dataclass validates values |
| `T0_FEEDER_RECOVERY_CANDLES` | Feeder composition -> RecoveryAdapter | Recovery lookback bound | Separate from FeederConfig because it configures the recovery adapter |
| `MARKET_DATA_TOKEN` | API process | Bearer authentication | API-specific; do not pass through feeder config |
| `PORT` | API development entry point | Local WSGI server bind port | Development process setting, not canonical data config |
| `NOTIFY_SOCKET` | Feeder process | systemd readiness notification | Host lifecycle integration; keep separate |

## 4. Candidate analysis

### C-01 — backend selection read twice in Feeder composition and storage factory

- Observation: `build_production_runtime()` reads and normalizes `MARKET_DATA_BACKEND`, then `create_store_from_env(values)` reads and normalizes the same setting again.
- Potential simplification: have composition select the backend once and pass the normalized selection into the factory, or return a typed backend configuration.
- Risk: changing factory call shape may affect direct callers/tests; typed configuration adds a new abstraction; PostgreSQL TLS/DSN/lease checks must remain in the correct owner.
- Verdict: **PARK — cosmetic reduction only; no demonstrated net complexity reduction.**

### C-02 — API preflight backend/path checks overlap with storage factory validation

- Observation: API returns `UNCONFIGURED` for missing token or SQLite path before auth/store read, then the factory validates backend selection.
- Potential simplification: rely entirely on factory exceptions.
- Risk: externally observable HTTP error changes, authentication ordering changes and unclear classification between unconfigured and unavailable store.
- Verdict: **KEEP — preserve explicit API response semantics.**

### C-03 — FeederConfig defaults vs environment defaults

- Observation: `FeederConfig` provides validated defaults while `build_production_runtime()` explicitly supplies selected environment values and hard-coded canonical timeframes.
- Verdict: **KEEP — these are constructor defaults and production policy, not proven duplicated configuration.** Moving defaults or timeframes could silently change direct/test construction or canonical scope.

### C-04 — API and Feeder share store factory but are separate processes

- Observation: both processes select a store from their process environment; the API is read-only and Feeder owns ingestion/lease/writes.
- Verdict: **KEEP — process-level configuration separation is intentional; do not introduce shared mutable config or cross-process coupling.**

### C-05 — explicit SQLite initialization vs runtime startup

- Observation: initializer creates only an empty new database; runtime composition explicitly avoids provisioning canonical storage.
- Verdict: **KEEP — the separation prevents accidental creation/replacement at Feeder startup.**

## 5. Safety invariants that must remain

- SQLite candle store and lease must resolve to the same database path.
- Writer generation/lease checks remain in the same atomic transaction as canonical candle writes.
- Startup recovery must be lease-guarded and fail closed.
- SQLite WAL keeper remains part of the concurrent read-only API/runtime arrangement.
- Store construction and API reads must not implicitly create a missing canonical database.
- API remains bounded, authenticated and read-only; preserve error classification and no-store behavior.
- PostgreSQL remains opt-in and must retain same-DSN lease/writer binding and verified TLS checks.
- Explicit initialization must not overwrite existing files.
- Do not reduce regression tests or workflow denominators to make the implementation appear smaller.

## 6. Verdict and limitations

- Configuration ownership map: **PASS for inspected files**.
- Backend selection duplication: **FOUND; low-value refactor candidate only**.
- Safe refactor candidate: **NONE ESTABLISHED**.
- Full repository-wide environment-variable/call-site inventory: **NOT VERIFIED**.
- Process manager/deployed environment parity: **NOT VERIFIED**.
- Tests / GitHub Actions: **NOT RUN / NOT DISPATCHED**.
- No independent review was performed.
- T0 operational acceptance and L4-Minimum remain unchanged: **BLOCKED / NOT VERIFIED**.
- Option C — No Destructive Authority — remains active. No data lifecycle mutation is authorized.

## 7. Next safe increment

Continue static responsibility mapping of the canonical SQLite path across startup, API and health reporting. Specifically establish whether health endpoints share one truthful state model or report distinct process/data/API properties. Do not merge health endpoints or alter response semantics without exact route/caller/test mapping.
