# T0 Simplification — Dependency and Retirement Gate Review (Second Pass)

- Date: 2026-11-10
- Repository: `kenznguyen/btcusdt-telegram-signals2`
- Branch: `feature/t0-centralized-data-feeder-p1-20261101`
- Inspected branch HEAD: `d584a31c936d8c1d50370a3c74d4c737c853c881`
- Method: read-only exact-branch source, test, requirements and selected workflow inspection.
- Scope: classify T0 components previously proposed as PARK / CONDITIONAL / SUPPORT; determine whether simplification can safely remove or isolate them.
- No tests, workflow dispatch, runtime/VPS/database/provider access, code change, configuration change, permission change or destructive operation.

## 1. Decision summary

**Do not delete or disable any inspected T0 component in this increment.** The prior scope-minimization classification remains directionally correct, but the second pass narrows the retirement decision:

- The active SQLite path is not a small independent set of files: the Feeder composition, recovery, sync callback, lease fencing, atomic write gateway, WAL keeper, storage facade, Candle store and read API form one connected operational path.
- PostgreSQL is optional at runtime but is not fully isolated at import/dependency level. The SQLite default does not prove that PostgreSQL source or its package dependency can be removed safely.
- Kraken Spot is a separate research domain, not canonical T0 data. Its code/tests are isolated by design; preserve it outside the active T0 acceptance denominator rather than merge or delete it.
- The Binance connectivity probe is an explicitly invoked diagnostic, not part of Feeder ingestion. Keep it as a separate support tool; do not count it as a runtime dependency.
- Evidence Object / checkpoint G0–G3 is an assurance workstream, not an ingestion prerequisite. Preserve its records and existing gates, but freeze feature expansion and do not fold TSA/WORM/Root A/Root B into minimum T0.
- No source-level retirement candidate is proven safe by this pass.

## 2. Active SQLite dependency chain

Observed source composition:

```text
market_data.feeder_service
  -> build_production_runtime
  -> create_store_from_env (SQLite default)
  -> build_runtime
      -> FeederRuntime / FeederScheduler / RecoveryCoordinator
      -> LeaseStore
      -> sync_window
          -> Binance USD-M CCXT public market data
          -> SQLiteWriteGateway
              -> same SQLite DB lease + candle transaction
      -> SQLiteWalKeeper
  -> market_data.api
      -> create_store_from_env
      -> bounded authenticated read-only Candle API
  -> T2 FreqAI bridge
      -> CandleHttpClient -> /v1/candles
```

The SQLite writer and lease must share one DB path. The gateway checks the current owner/generation inside the same `BEGIN IMMEDIATE` transaction as candle insertion and checks again before commit. Startup recovery is itself a writer and uses guarded lease heartbeat before each recovery attempt. These are correctness and fencing boundaries, not accidental abstraction to remove for cosmetic simplicity.

### Active components — KEEP

| Component | Evidence-based disposition | Reason |
|---|---|---|
| `market_data.feeder.py` | KEEP | Scheduler, retry, lease, recovery and runtime state machine |
| `market_data.feeder_service.py` | KEEP | Production composition, backend selection and guarded startup recovery |
| `market_data.store.py` | KEEP | Canonical Candle contract, validation, SQLite schema/read behavior |
| `market_data.sync.py` | KEEP | Shared ingestion function used by runtime composition and explicit CLI |
| `market_data.write_gateway.SQLiteWriteGateway` | KEEP | Atomic same-DB lease fencing and canonical writes |
| `market_data.write_gateway.SQLiteWalKeeper` | KEEP for SQLite runtime | WAL lifecycle support for concurrent read-only API access |
| `market_data.storage.SQLiteCandleStore` | KEEP | Explicit SQLite facade; no implicit DB creation on reads |
| `market_data.api.py` | KEEP | Bounded authenticated read-only data boundary |
| `market_data.initialize_sqlite.py`, migrations | KEEP | Explicit, empty-only initialization and controlled schema lifecycle |
| T0 regression tests | KEEP | Preserve the existing behavioral denominator; no test deletion to create apparent simplicity |

## 3. Parked / conditional components — dependency findings

### T0-SM2 — PostgreSQL adapter and migration set

Files include `market_data/postgres.py`, `market_data/migrations.py`, migration SQL, PostgreSQL integration tests, and the optional branch in `feeder_service.py`.

- Runtime default remains SQLite; PostgreSQL requires explicit backend and DSN.
- PostgreSQL is nevertheless directly imported by `storage.py` and `feeder_service.py`, and PostgreSQL store/lease/write-gateway composition is present in the production builder.
- `requirements-market-data.txt` installs `psycopg[binary]` unconditionally alongside CCXT.
- Therefore PostgreSQL is **optional in runtime selection, not isolated from import/dependency packaging**.
- Safe simplification opportunity: a future design-only proposal may consider lazy/optional imports and a SQLite-only install extra, but only after checking every test/workflow/install path and preserving an explicit opt-in PostgreSQL qualification path.
- Disposition: PARK; NOT A RETIREMENT CANDIDATE. Do not remove adapter, migrations, tests or psycopg dependency in this pass.

### T0-SM3 — Kraken Spot research domain

Files include `kraken_spot.py`, `kraken_spot_store.py`, `kraken_spot_api.py`, and dedicated tests.

- Separate instrument identity: Kraken / SPOT / BTC-USDT; separate SQLite store and API.
- Source documentation explicitly says it does not write to Binance canonical storage, provide failover, or feed Futures strategy/paper execution.
- Dedicated tests exercise market identity, source provenance, isolated persistence and read-only API.
- This is not an active canonical T0 dependency. It is also not proven disposable: it has its own code and test contract and may represent retained research work.
- Disposition: SEPARATE RESEARCH DOMAIN / PARK. Exclude from active T0 readiness denominator; do not merge into canonical store or delete without owner decision and complete workflow/evidence mapping.

### T0-SM4 — Binance connectivity probe

- `market_data.binance_connectivity_probe.py` declares explicit `--confirm-network`, no T0 store/Feeder import and no persistence.
- It is a manual network diagnostic, not a continuous ingestion dependency or a production acceptance substitute.
- Disposition: KEEP AS OPTIONAL SUPPORT TOOL; exclude from always-on runtime and core ingestion dependency graph. Do not invoke it during this audit.

### T0-SM5 — Explicit sync CLI / ShadowWriteGateway

- `sync_window()` is shared by the Feeder's canonical sync callback and the explicit one-shot sync CLI.
- `ShadowWriteGateway` is a no-persistence sink for manual shadow inspection; it is not the canonical production writer.
- The module mixes a core shared ingestion function with a CLI/shadow utility. Splitting it may improve module boundaries but is not necessary to simplify the active runtime and could accidentally fork ingestion semantics.
- Disposition: KEEP shared function; PARK any file split until full import, test and CLI compatibility mapping is complete.

### T0-SM6 — Evidence Object / Checkpoint G0–G3

- The checkpoint contract and synthetic-only reference tests/workflow are separate from the Feeder's canonical candle write/read path.
- G2 exact committed-SHA / GitHub Actions result remains NOT VERIFIED; G3 independent review remains PENDING.
- L4-Minimum acceptance remains BLOCKED / NOT VERIFIED.
- These assurance gates must not be represented as required for basic SQLite ingestion/API operation; nor may their incomplete status be hidden by removing them from their own assurance claim.
- Disposition: PRESERVE RECORDS; FREEZE feature expansion; track separately from minimum active T0 runtime.

## 4. Workflow and package implications

- `requirements-market-data.txt` includes both CCXT and psycopg, so a SQLite-only deployment currently installs the PostgreSQL driver too.
- `.github/workflows/t0-single-writer-gateway-red.yml` covers `market_data/**`, `freqai_bridge/**`, `futures_intelligence/**`, `pipeline/**`, and `requirements-web.txt`; it runs isolated static and feeder/gateway regression contracts. Its broad `market_data/**` path means even research-domain changes can trigger the T0 contract workflow.
- `.github/workflows/t0-evidence-contract-g2.yml` has a narrow path filter for the synthetic checkpoint reference, tests and its own workflow. It is a separate assurance validation lane.
- Workflow presence and trigger configuration do not prove current branch protection, workflow execution or artifacts.
- No workflow or package configuration should be narrowed until the exact full job commands, all imported tests and branch protection requirements have been mapped.

## 5. Simplification opportunities ranked by safety

1. **Documentation-only separation (LOW RISK):** label SQLite canonical runtime, optional PostgreSQL, Kraken research, connectivity support and checkpoint assurance as distinct tracks in the active T0 index/README. Preserve historical statements and avoid rewriting old evidence.
2. **Packaging proposal (MEDIUM RISK):** assess optional PostgreSQL extra/lazy imports to avoid forcing psycopg on SQLite-only use. No code or dependency change until CI and import compatibility matrix is approved.
3. **Workflow scope proposal (MEDIUM RISK):** evaluate whether Kraken research tests should have a separate workflow while retaining a T0 workflow trigger for all canonical dependencies. Do not narrow the current path filter before a complete dependency matrix and branch-protection check.
4. **Module extraction proposal (MEDIUM RISK):** consider separating manual CLI/shadow tooling from the shared sync function only if the resulting dependency graph remains single-source and behavior-equivalent.
5. **Retirement (NOT RECOMMENDED):** no deletion candidate is supported by current evidence.

## 6. Findings

- T0-SM2 / MEDIUM: PostgreSQL is optional at runtime but eagerly imported and its driver is installed unconditionally; optional-backend isolation is incomplete.
- T0-SM3 / LOW: Kraken Spot is a separate research domain and should be excluded from active canonical T0 scope, not deleted.
- T0-SM4 / LOW: connectivity probe is support-only and outside Feeder runtime.
- T0-SM5 / MEDIUM: sync module combines shared core ingestion with one-shot CLI/shadow utility; splitting is optional and not yet justified.
- T0-SM6 / HIGH: checkpoint assurance work can inflate minimum T0 scope if mixed with ingestion acceptance; preserve separate G0–G3 status and blockers.
- T0-SM7 / HIGH: broad `market_data/**` workflow path couples isolated research changes to core T0 workflow; any decoupling needs exact workflow/branch-protection and test-denominator review.

## 7. Status and limitations

- Selected exact-branch source and workflow blobs read back: PASS.
- Active SQLite runtime dependency chain: PASS for inspected source composition.
- PostgreSQL optionality and import/package coupling: PASS for inspected source.
- Kraken Spot separation: PASS for inspected module/test contracts.
- Connectivity probe support-only classification: PASS for inspected module contract.
- Full repository call graph, all workflow jobs, branch protection, deployed environment/package contents, live consumers and runtime state: NOT VERIFIED.
- Tests / GitHub Actions: NOT RUN / NOT DISPATCHED.
- Independent review: NOT PERFORMED; this is a static source review.
- L4-Minimum: BLOCKED / NOT VERIFIED; G2 exact-SHA CI: NOT VERIFIED; G3 independent review: PENDING.
- No source, test, workflow, package, schema, runtime, VPS, database, provider, key, permission or data changes.
- Option C — No Destructive Authority — unchanged. No TTL, deletion-after-use, archive, cleanup, vacuum, compaction, backup expiry or replica removal.
- `AI_EXECUTION_ENABLED=false`; paper-only; no live orders.

## 8. Next safe increment

Prepare a documentation-only **T0 Active Scope Index** that distinguishes:
- canonical SQLite ingestion/API runtime (active);
- PostgreSQL optional backend (parked);
- Kraken Spot research (separate);
- connectivity probe (support-only);
- checkpoint evidence G0–G3 (separate assurance track).

Do not remove code or narrow workflow triggers. Reconcile the README/index only after checking all current cross-references; retain historical evidence and exact status labels.
