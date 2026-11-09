# T0 Simplification — Optional PostgreSQL Packaging Isolation Review

- Date: 2026-11-10
- Repository: `kenznguyen/btcusdt-telegram-signals2`
- Branch: `feature/t0-centralized-data-feeder-p1-20261101`
- Exact source baseline inspected: `27d22fe1c3103732eaa9da8a36e22d77b19d4688`
- Method: read-only inspection of exact-branch dependency, storage composition, PostgreSQL adapter and GitHub Actions workflow files.
- Scope: determine whether the selected SQLite T0 runtime unnecessarily installs optional PostgreSQL dependencies, and what must be preserved before any packaging simplification.
- No source/test/workflow/package/config/runtime/VPS/database/provider/permission/data changes. No tests or workflows executed.

## 1. Executive result

**SIMPLIFICATION OPPORTUNITY CONFIRMED — IMPLEMENTATION NOT AUTHORIZED.**

SQLite is the selected default and the canonical T0 backend. The active SQLite path requires CCXT for Binance USD-M public market data; the PostgreSQL driver is not needed for ordinary SQLite storage operations based on the inspected import path. However, the current shared requirements file installs the PostgreSQL driver unconditionally.

This supports a future packaging-only proposal to separate SQLite runtime dependencies from PostgreSQL qualification dependencies. It does **not** support deleting the PostgreSQL adapter, migrations, tests or integration workflow.

## 2. Exact source evidence

| File | Blob SHA | Observation |
|---|---|---|
| `requirements-market-data.txt` | `0c1b47046bc264be48fa9e11360ce3488046530d` | Contains both `ccxt>=4.4.0,<5` and `psycopg[binary]>=3.2,<4`; the driver is currently installed for all users of this requirements file. |
| `market_data/storage.py` | `13fe1ae01ebb5318b69e69eef3e512d207f74c49` | SQLite is the default; PostgreSQL adapter module and its read function are imported at module load. Backend selection remains explicit and fails closed for unknown/incomplete configuration. |
| `market_data/feeder_service.py` | `bdcecf6bc98a2ff070f83098d2c50154a160c99c` | Imports PostgreSQL store/lease/write-gateway classes at module load; selects PostgreSQL only when `MARKET_DATA_BACKEND=postgres`, otherwise composes SQLite. |
| `market_data/postgres.py` | `2fe27fe2d066dda0c192a381b72d27404487b800` | Driver import occurs inside the database connection function, rather than at module import. This reduces runtime driver coupling but does not remove adapter-module import coupling. |
| `market_data/test_storage.py` | `b2635f575323187f936360d033b4fc630d8138e0` | Covers SQLite default, explicit PostgreSQL selection, no fallback, side-effect-free construction, missing-file read behavior, shared SQLite write/read contract and PostgreSQL failure semantics. |
| `.github/workflows/t0-single-writer-gateway-red.yml` | Exact workflow blob is retained in the inspected branch; see branch source baseline above. | Workflow installs `requirements-market-data.txt` for both SQLite/T0 tests and disposable PostgreSQL/TimescaleDB integration jobs. These environments must be separated carefully before dependency removal from any job. |

## 3. Findings

### T0-PKG-01 — Unconditional PostgreSQL driver installation

- Severity: MEDIUM.
- Status: SOURCE-CONFIRMED.
- SQLite-only use currently installs `psycopg[binary]` because the shared requirements file includes it unconditionally.
- This is a packaging footprint issue, not evidence of a runtime correctness defect.
- Candidate simplification: define a SQLite/base requirements set containing CCXT and a distinct PostgreSQL qualification set that additionally installs psycopg.
- Do not edit requirements until all repository install commands, developer instructions, workflow jobs, container/build contexts and test entry points are mapped.

### T0-PKG-02 — Adapter modules are eagerly imported, driver is lazily imported

- Severity: LOW–MEDIUM.
- Status: SOURCE-CONFIRMED for inspected files.
- `storage.py` and `feeder_service.py` import PostgreSQL adapter classes at module scope.
- The inspected `postgres.py` imports `psycopg` inside the connection function. Therefore, importing the adapter module does not itself establish that the driver must be installed for SQLite operations.
- Candidate simplification: evaluate moving PostgreSQL adapter imports into the explicit PostgreSQL selection/composition branch. This is a code-boundary refactor, not required to solve the unconditional dependency installation.
- Do not implement until import behavior, public names, type checks, tests, and all entry points are mapped. In particular, `build_runtime()` currently distinguishes the PostgreSQL store using its concrete class.

### T0-PKG-03 — Existing PostgreSQL qualification jobs depend on the shared requirements file

- Severity: HIGH for careless dependency removal.
- Status: SOURCE-CONFIRMED for the inspected workflow.
- The workflow contains disposable TimescaleDB provider-bootstrap and read-only integration jobs; they install `requirements-market-data.txt` and execute PostgreSQL/TimescaleDB tests.
- Removing psycopg from the shared file without changing those job install commands would break those qualification jobs.
- The optional backend must remain independently testable even though it is not part of active SQLite runtime acceptance.

### T0-PKG-04 — No basis to retire PostgreSQL source or test coverage

- Severity: HIGH.
- Status: DECISION.
- PostgreSQL remains a preserved optional backend with explicit adapter, migration, writer/lease and integration contracts.
- Its current packaging coupling is not proof that the adapter is unused or disposable.
- Keep PostgreSQL adapter, migrations, SQL, tests, and isolated disposable integration coverage. Do not count PostgreSQL qualification as proof of active SQLite production readiness.

## 4. Simplification options and risk

| Option | Expected benefit | Risk | Current disposition |
|---|---|---|---|
| A. Split SQLite/base and PostgreSQL qualification requirements | Removes unnecessary driver installation from SQLite-only environments | Medium: all install paths and CI jobs must be updated coherently | RECOMMEND FOR DESIGN; NOT IMPLEMENTED |
| B. Lazy-import PostgreSQL adapter classes | Reduces module-level coupling and clarifies backend boundary | Medium: concrete type checks, composition and import tests may change | DEFER |
| C. Remove PostgreSQL adapter/migrations/tests | Smaller source tree | High; destroys preserved optional capability and evidence | REJECT |
| D. Remove PostgreSQL integration jobs from workflow | Shorter workflow | High; reduces test denominator and optional-backend qualification | REJECT |

## 5. Required mapping before any implementation proposal

1. Search every reference to `requirements-market-data.txt`, `psycopg`, PostgreSQL test modules and PostgreSQL CLI entry points.
2. Inventory all GitHub Actions jobs and local setup/deployment instructions that install the shared requirements file.
3. Define the exact dependency contract:
   - SQLite/T0 runtime: CCXT and only dependencies required by the selected SQLite path.
   - PostgreSQL qualification: SQLite/base requirements plus the pinned/compatible PostgreSQL driver and any test-only dependencies.
4. Preserve the existing PostgreSQL disposable-cluster preflight and all PostgreSQL/TimescaleDB test commands.
5. Specify clean-environment import tests proving SQLite storage/API/Feeder startup composition does not require the PostgreSQL driver, without connecting to an exchange or starting a runtime.
6. Preserve exact test counts and workflow evidence; no test/job may be dropped to achieve a smaller dependency set.
7. Require independent review before changing package or workflow files.

## 6. Disposition

- SQLite canonical runtime: KEEP ACTIVE.
- PostgreSQL adapter, migrations and tests: PARK / PRESERVE.
- Unconditional psycopg installation: CONFIRMED SIMPLIFICATION CANDIDATE.
- Lazy adapter imports: OPTIONAL FOLLOW-UP; not yet justified as necessary.
- PostgreSQL workflow jobs: PRESERVE as optional-backend qualification; keep outside the active SQLite runtime acceptance claim.
- No source-level retirement candidate established.

## 7. Status and boundaries

- Static source/dependency observations: PASS for inspected files.
- Complete repository-wide install-path inventory: NOT VERIFIED.
- All workflow consumers/install commands: PARTIAL; complete workflow matrix not independently reviewed in this increment.
- Clean SQLite-only environment import test: NOT RUN.
- Tests: NOT RUN.
- GitHub Actions: NOT DISPATCHED.
- Independent review: NOT PERFORMED.
- G2 exact-SHA: NOT VERIFIED; G3 independent review: PENDING / NOT VERIFIED.
- T0 L4-Minimum operational acceptance: BLOCKED / NOT VERIFIED.
- Option C — No Destructive Authority — unchanged. No TTL, deletion-after-use, cleanup, archive, compaction, vacuum, backup expiry or replica removal.
- `AI_EXECUTION_ENABLED=false`; paper-only; no live orders.

No implementation is authorized by this review. The next safe increment is a read-only repository-wide inventory of requirements-file consumers and PostgreSQL test/workflow references, followed by a dependency split design. Any package/workflow edit requires separate implementation authorization.
