# T0 Simplification — PostgreSQL Dependency and Install-Path Inventory

- Date: 2026-11-10
- Repository: `kenznguyen/btcusdt-telegram-signals2`
- Branch: `feature/t0-centralized-data-feeder-p1-20261101`
- Current branch HEAD observed: `92ab5e937ed8eba5e5ce1f1f4b19dcdc85b235d8`
- Previous packaging review baseline: `27d22fe1c3103732eaa9da8a36e22d77b19d4688`
- Comparison: current HEAD is 8 commits ahead, 0 behind; GitHub compare reports only README, handoff, scope-index and evidence-document changes. No source or workflow files changed between the prior baseline and current HEAD.
- Repository tree: 662 blobs; `.github/workflows/`: 14 YAML files.
- Method: read-only branch/tree inspection, fetch of all 14 workflow definitions, relevant requirements/source/test/setup/docs files, and exact blob SHA recording. No source checkout or branch-wide shell grep was available through this inspection path.
- Operation class: READ-ONLY STATIC INVENTORY. No source, test, package, workflow, runtime, VPS, database, provider, secret, permission or data changes. No tests or workflows executed.

## 1. Result

**PARTIAL — dependency/install paths and PostgreSQL qualification consumers identified; repository-wide textual exhaustiveness NOT VERIFIED.**

The evidence confirms a low-risk packaging simplification candidate: separate the SQLite/CCXT base dependency set from the optional PostgreSQL qualification driver. It does not justify removing PostgreSQL adapter code, migrations, SQL, tests or qualification jobs.

## 2. Requirements file and installation consumers

### Shared dependency file

`requirements-market-data.txt` (blob `0c1b47046bc264be48fa9e11360ce3488046530d`):
- `ccxt>=4.4.0,<5`
- `psycopg[binary]>=3.2,<4`

### Confirmed GitHub Actions consumers on the active branch

1. `.github/workflows/t0-manual-validation.yml` (blob `395ae93274a9202f14ab63d528be5cd582c30149`)
   - pip install combines `requirements-market-data.txt`, `requirements.txt`, `requirements-web.txt`, and `requirements-ci.txt`.
   - The same job offers SQLite/component/Kraken gates and a separately selected TimescaleDB integration gate. Consequently, the current install is over-inclusive for non-PostgreSQL manual gates.
2. `.github/workflows/p5-3-11-g2-integration-green.yml` (blob `3b75fdbf34768a315e5ed025b2ba0015ce138b17`)
   - Installs market-data, CI and base requirements. Preserve the complete G2 test scope; do not infer that this entire workflow is PostgreSQL qualification.
3. `.github/workflows/t0-single-writer-gateway-red.yml` (blob `2d836c6c835f414efa62137abf7b97b7bcd6d5ec`)
   - Two isolated TimescaleDB jobs install `requirements-market-data.txt`: restricted provider bootstrap and read-only/atomic-writer/Feeder/role qualification.
   - The SQLite/T0 core job installs `requirements-web.txt`, not the market-data shared file.
4. `.github/workflows/t0-postgres16-grantor-repro.yml` (blob `c7bc589ca8240edb25a9c33cce5b9a76e6193271`)
   - Installs `psycopg[binary]>=3.2,<4` directly for a disposable PostgreSQL 16 grantor reproduction; does not install the shared requirements file.

Other inspected GitHub Actions workflows do not install `requirements-market-data.txt`. Their source YAMLs were individually fetched from the exact active branch. No workflow was dispatched.

### Legacy / non-canonical installation consumers

- `codemagic.yaml` (blob `c8626f8b6b55fa7d76cd885a63beb60413d6fd77`) passes the shared requirements file to:
  - `canonical-market-data` job with base/web/CI requirements;
  - `market-data-timescaledb` job with CI requirements;
  - `freqai-strategy-smoke` alongside FreqAI requirements;
  - three separate Kraken adapter/SQLite/read-API jobs with CI requirements.
- Codemagic remains PARKED/legacy under owner-approved D-01/D-02. Do not alter, disable or delete it as part of this inventory. If a future requirements split is implemented, these references must be dispositioned explicitly even though Codemagic is not the canonical runner.
- `ci/setup-python.sh` (blob `d7df05135595e7a5dc251901cb059c2d6b246af8`) accepts an arbitrary list of requirements files and installs each in an isolated venv. It is a generic installer, not itself a fixed dependency consumer.
- `ci/test-timescaledb.sh` (blob `f0af703349457e8ff7fbe45260bc3fae5acd8f88`) explicitly imports `psycopg` before running the PostgreSQL/TimescaleDB suites. Its caller must provide the optional driver.
- `market_data/README.md` (blob `19485ce933e15433c412a54ab15d9cbc1860dfd7`) instructs the SQLite sync user to install `requirements-market-data.txt`; that currently installs psycopg even for the documented SQLite path.

## 3. PostgreSQL driver and adapter import map

### Runtime/source

- `market_data/postgres.py` (blob `2fe27fe2d066dda0c192a381b72d27404487b800`): the only runtime `import psycopg` is inside `connection()`; the driver is lazy with respect to importing this module.
- `market_data/storage.py` (blob `13fe1ae01ebb5318b69e69eef3e512d207f74c49`): imports `PostgresCandleStore` and the PostgreSQL read function at module import.
- `market_data/feeder_service.py` (blob `bdcecf6bc98a2ff070f83098d2c50154a160c99c`): imports PostgreSQL store/lease/write-gateway classes at module import.
- `market_data/migrations.py` (blob `b4574f2a867b0dae7818cd39249cfd95fe0ce1f0`): imports the adapter's `connection`; it is a PostgreSQL migration entry point, not a SQLite runtime dependency.
- `market_data/postgres.py` contains adapter, lease and write-gateway implementation. It must remain preserved while PostgreSQL is PARKED.

### Direct driver imports in test/qualification code

- `market_data/test_timescaledb.py` (blob `59f8ca223b1cd7e580afed18e0be0d0fb0e72ea4`): imports psycopg in integration `setUpClass`; six read-only/migration/API integration tests.
- `market_data/test_postgres_write_gateway.py` (blob `443eaa5ffe0167d0c775bb0d6d8a3cd299e7d069`): imports psycopg in PostgreSQL integration setup and interrupted-migration contract.
- `market_data/test_postgres_role_privileges.py` (blob `f26f8ec7a782fd1ca0d339a1d8eb5ef613cda13f`): imports psycopg in class setup; role, lease, read/write privilege and migration-safety integration.
- `market_data/test_postgres_provider_bootstrap.py` (blob `ac8cccbd4fe1930627153de57ac113faba281110`): imports psycopg in its disposable-cluster bootstrap test.
- `market_data/test_postgres_feeder_runtime.py` (blob `dba7b3a61b3963984c58309e7d334b61c0889256`): imports PostgreSQL adapter types and tests composition/lease/runtime contracts; no direct psycopg import was found in the inspected file.
- `market_data/test_postgres_feeder_runtime_lifecycle.py` (blob `ff8458fd6250fca264799810d78b2566ebcfda10`): imports adapter types and exercises PostgreSQL runtime lifecycle/connection contracts; no direct psycopg import was found in the inspected file.

### Inline workflow driver use

- `.github/workflows/t0-postgres16-grantor-repro.yml` installs and imports psycopg in an inline script. This direct install must remain explicit and isolated from SQLite requirements.

## 4. PostgreSQL qualification denominator to preserve

The exact branch's T0 workflow invokes these PostgreSQL/TimescaleDB modules:
- `market_data.test_postgres_provider_bootstrap` — isolated fresh-cluster restricted bootstrap.
- `market_data.test_postgres_write_gateway` — lease-fenced writer and migration contracts.
- `market_data.test_postgres_feeder_runtime` — runtime composition/lease contracts and integration.
- `market_data.test_postgres_feeder_runtime_lifecycle` — lifecycle/heartbeat/restart/timeout contracts.
- `market_data.test_postgres_role_privileges` — least-privilege role and migration contracts.
- `market_data.test_timescaledb` — read-only adapter, migration, precision, gaps and API contracts.

Keep all six modules, their compile/test commands, disposable TimescaleDB service setup, preflight checks, artifact paths, and grantor reproduction workflow. No test count, module, job, trigger or path filter is authorized for removal or reduction.

## 5. Dependency separation implications

A future proposal may define:
- SQLite/base market-data requirements: CCXT plus dependencies proven necessary for the selected SQLite path.
- PostgreSQL qualification requirements: base requirements plus `psycopg[binary]`.
- Explicit PostgreSQL test install in any isolated job that requires the driver.
- Clean-environment SQLite import tests for `market_data.storage`, `market_data.api`, and `market_data.feeder_service`, with psycopg absent and no exchange connection/runtime start.
- PostgreSQL integration tests run in an environment with the optional driver installed and all existing disposable-target guards retained.

Do not implement until every installation reference is exhaustively verified and the dependency split is independently reviewed. Lazy adapter imports remain a separate optional refactor and are not required for dependency separation.

## 6. Coverage limitation and status

- PASS: current branch identity, tree inventory, all 14 workflow YAML files fetched, exact relevant source/requirements/test/docs/setup files inspected, and key dependency consumers mapped.
- PARTIAL / NOT VERIFIED: exact all-repository textual occurrence count for `requirements-market-data.txt` and `psycopg`. GitHub code search indexes the default branch rather than this non-default active branch, and no branch-local shell grep/checkout was available. The list above is the set of confirmed consumers from fetched files, not a claim that no other file reference exists.
- NOT RUN: clean SQLite-only import test, all test suites, dependency installation matrix, or compile checks.
- NOT DISPATCHED: GitHub Actions.
- NOT PERFORMED: independent review.
- G2 NOT VERIFIED; G3 PENDING; L4-Minimum BLOCKED / NOT VERIFIED.
- No source/test/workflow/package/config/runtime/VPS/database/provider/secret/permission/data changes; no PR or merge.

## 7. Next gate

1. Obtain a branch-local exact text search (or equivalent exhaustive repository-content scan) for `requirements-market-data.txt`, `psycopg`, PostgreSQL test module names, migration/CLI entry points and pip install commands.
2. Reconcile any additional matches with the confirmed inventory above.
3. Prepare a dependency split design with an explicit per-job/per-entry-point install matrix and unchanged PostgreSQL test denominator.
4. Obtain independent review before any requirements/workflow/test edits.
