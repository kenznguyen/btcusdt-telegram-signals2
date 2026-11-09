# T0 Simplification — PostgreSQL Packaging Reassessment

- Date: 2026-11-10
- Repository: `kenznguyen/btcusdt-telegram-signals2`
- Branch: `feature/t0-centralized-data-feeder-p1-20261101`
- Exact source baseline: `4d3945e37d74b8ce81227db3265a80dd85f29c24`
- Baseline tree: `b344c6b09f00e6a7abd7a2c5456f3d39f6608365`
- Operation class: READ-ONLY SOURCE/WORKFLOW REVIEW + DOCUMENTATION RECORD
- Scope: reassess whether splitting the shared market-data requirements into SQLite/base and PostgreSQL-only dependency sets is a net simplification for the currently selected SQLite T0 runtime.
- No source, tests, requirements, workflow, runtime, VPS, database, provider, secret, permission or data changes.

## 1. Decision

**PARK the requirements split. Keep the current shared `requirements-market-data.txt` unchanged for now.**

The earlier install-path inventory correctly identified unnecessary installation of `psycopg[binary]` on some SQLite-oriented paths. However, the present review does not establish that adding another requirements file and conditional install branches would reduce total system complexity enough to justify the additional maintenance surface.

This is a reassessment of the earlier candidate, not a deletion or removal of PostgreSQL support.

## 2. Current exact-branch observations

| Path | Blob SHA | Observation |
|---|---|---|
| `requirements-market-data.txt` | `0c1b47046bc264be48fa9e11360ce3488046530d` | Only CCXT and psycopg are declared |
| `market_data/storage.py` | `13fe1ae01ebb5318b69e69eef3e512d207f74c49` | Imports PostgreSQL adapter symbols at module load; no direct psycopg import |
| `market_data/feeder_service.py` | `bdcecf6bc98a2ff070f83098d2c50154a160c99c` | Imports PostgreSQL adapter classes; runtime selects SQLite by default |
| `market_data/postgres.py` | `2fe27fe2d066dda0c192a381b72d27404487b800` | Imports psycopg only inside `connection()`; driver import is lazy |
| `market_data/migrations.py` | `b4574f2a867b0dae7818cd39249cfd95fe0ce1f0` | Explicit PostgreSQL migration entry point |
| `.github/workflows/t0-manual-validation.yml` | `395ae93274a9202f14ab63d528be5cd582c30149` | One manual job installs shared requirements for several selectable gates, including TimescaleDB |
| `.github/workflows/p5-3-11-g2-integration-green.yml` | `3b75fdbf34768a315e5ed025b2ba0015ce138b17` | G2 installs shared requirements and runs a broad T0/consumer denominator |
| `.github/workflows/t0-single-writer-gateway-red.yml` | `2d836c6c835f414efa62137abf7b97b7bcd6d5ec` | SQLite jobs do not install the shared market-data file; isolated PostgreSQL/TimescaleDB jobs do |
| `codemagic.yaml` | `996893437f5746ae296e8a7bda5b38e0a76b3c18` | PARKED/legacy configuration still references shared requirements in canonical, TimescaleDB, FreqAI and Kraken jobs |
| `market_data/README.md` | `19485ce933e15433c412a54ab15d9cbc1860dfd7` | Documents shared requirements for one-shot sync |

The prior inventory used an earlier source/documentation baseline. This reassessment records the current branch blobs above; the Codemagic blob in particular has changed since that inventory.

## 3. Why not split now

1. The shared file currently contains only two direct dependencies. The unnecessary dependency is identifiable, but the absolute dependency surface is already small.
2. The active T0 Gateway workflow already separates SQLite jobs from two disposable PostgreSQL/TimescaleDB jobs. The principal over-installation remains in the manual multi-gate workflow and the G2 integration workflow.
3. The manual workflow selects among multiple gates in one job. A clean split would require conditional install logic or a more granular job/environment design. That adds workflow branches and another package contract.
4. G2 deliberately preserves a broad cross-domain test denominator. Changing its install set requires import and test evidence across all invoked modules, not only the SQLite runtime.
5. Codemagic is parked/legacy but still has several references. Updating it would expand this task into legacy-runner maintenance without a current canonical execution requirement.
6. `market_data.postgres` can be imported without psycopg installed because the driver import occurs inside the connection function. Therefore, a missing psycopg package is not currently shown to prevent importing the shared storage/feeder modules. This is a static observation, not a clean-environment test result.

A possible future split would require an exhaustive reference inventory, a per-job/per-entry-point installation matrix, clean SQLite-only import tests with psycopg absent, and the unchanged PostgreSQL qualification suite with psycopg present. That evidence is not available in this pass.

## 4. Preserve — do not simplify by deletion

- Keep PostgreSQL adapter, lease/write-gateway code, migrations, SQL, tests and disposable TimescaleDB jobs.
- Keep all six PostgreSQL/TimescaleDB qualification modules identified in the previous install-path inventory.
- Keep the existing shared requirements file and all install commands unchanged.
- Keep the SQLite single-writer/lease/fencing/recovery/WAL/API path intact.
- Keep Kraken Spot as a separate preserved research domain, outside active canonical T0 acceptance.
- Keep Evidence Object / Checkpoint G0–G3 as a separate assurance workstream.
- Do not narrow workflow path filters or test denominators.
- Option C — No Destructive Authority — remains unchanged. No TTL, deletion-after-use, cleanup, archive, compaction, vacuum, backup expiry or replica removal.

## 5. Simplification assessment

| Candidate | Assessment | Decision |
|---|---|---|
| Remove PostgreSQL adapter/migrations/tests | Would destroy preserved optional qualification capability | REJECT |
| Remove psycopg from shared requirements | Would break PostgreSQL qualification consumers | REJECT |
| Add SQLite-only + PostgreSQL requirements files now | Potentially reduces one dependency but adds package/workflow branching; benefit not proven | PARK |
| Lazy-import PostgreSQL adapter classes | Not required to avoid psycopg import; additional refactor surface without proven operational benefit | PARK |
| Narrow mixed workflow path filters or G2 denominator | Governance and evidence coverage not fully mapped | NOT AUTHORIZED |
| Keep current small shared requirements contract | Lowest configuration complexity with existing test coverage retained | KEEP |

## 6. Status and limitations

- Current branch and exact source blobs read back: PASS.
- Runtime import structure and current workflow install commands: PASS for inspected files.
- Net benefit of a requirements split: NOT ESTABLISHED; PARK.
- Exhaustive branch-local repository-wide occurrence scan: NOT VERIFIED.
- Clean SQLite-only environment import test: NOT RUN.
- Unit/integration tests: NOT RUN.
- GitHub Actions: NOT DISPATCHED; no run or artifact.
- Independent review: NOT PERFORMED.
- G2 exact-SHA CI: NOT VERIFIED; G3 independent review: PENDING; L4-Minimum: BLOCKED / NOT VERIFIED.
- No source/package/workflow/test/runtime/VPS/database/provider/secret/permission/data changes.

## 7. Next safe increment

Continue read-only T0 minimization by reviewing the *operationally active SQLite path* for duplicated configuration or responsibilities only where a behavior-preserving simplification can be demonstrated. Prioritize configuration ownership and startup composition; do not split modules, change imports, or edit workflows until a specific duplicate is proven and the complete regression denominator is mapped.
