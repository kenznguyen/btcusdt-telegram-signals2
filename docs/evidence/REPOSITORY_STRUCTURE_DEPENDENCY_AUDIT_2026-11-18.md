# Repository Structure and Dependency Audit — 2026-11-18

- Repository: `kenznguyen/btcusdt-telegram-signals2`
- Branch: `feature/core-operational-proof-20261112`
- Inspected source HEAD: `fa48bb56a9b353256fa967ee780bee90455e794d`
- Audit type: read-only Git tree inventory and targeted source/document inspection.
- Verdict: **PARTIAL PASS — structural classifications grounded; full repository-wide caller/import graph NOT VERIFIED.**
- Changes during audit: none to application source, workflows, runtime, T0 data or credentials. This report and handoff update are documentation-only records.

## 1. Scope and method

Inspected the recursive Git tree at the exact source HEAD above (1,105 tracked files; 251 Python files outside docs; 37 workflow/CI YAML files). Directly read:
- `app.py`, `risk_policy.py`, `backtest_rsi_percent_b_h1_adx.py`, `dashboard/index.html`, `README.md`, `requirements*.txt`
- `pipeline/api.py`, `.github/workflows/core-live-data-operational-proof.yml`
- `market_data/README.md`, `docs/FIVE_LAYER_ARCHITECTURE.md`, `docs/FIVE_LAYER_PAPER_RUNBOOK.md`
- `d07_9_lineage/README.md`, `t0_signature_stage1/README.md`, `integrations/README.md`, `futures_intelligence/README.md`, `freqai_bridge/README.md`
- `docs/evidence/FIVE_LAYER_SCOPE_EXCLUSION_ANDROID_PYTHON_2026-11-10.md`

The GitHub code-search endpoint available to this audit searches the repository default branch, not the specified feature branch. Its results were therefore not treated as proof of callers on the inspected branch. No full checkout/import graph, static analyzer, test suite or workflow run was executed.

## 2. Root-level files

| Path | Observed role / dependency | Disposition |
|---|---|---|
| `risk_policy.py` | Shared policy constants; `pipeline/api.py` imports `CORE_LEVERAGE`; Core workflow path filter includes this file | **KEEP at root for now**. Moving it requires coordinated import, tests and workflow path updates. |
| `app.py` | Flask WSGI app; serves `dashboard/index.html` at `/dashboard` and exposes feeder health endpoints via `HealthEvaluator` | **REVIEW**. Keep until its deployment/start-command callers and health-check ownership are established. Do not merge into `market_data/api.py` based on naming alone. |
| `backtest_rsi_percent_b_h1_adx.py` | Explicitly described in README as independent research backtest, outside T0–T4; root requirements include its scientific/data dependencies | **KEEP / MOVE LATER** to a research namespace only after exact-branch workflow, docs and caller tracing. |
| `requirements.txt` | Shared/root dependency set; README states it remains for the standalone research script | **KEEP**. No dependency split justified by this audit. |
| `dashboard/index.html` | Manual JSON/CSV report viewer; page states it does not run backtests, dispatch workflows or call external APIs | **KEEP SEPARATE** from React control plane; consider a research/backtest-viewer location only after entrypoint checks. |
| `README.md` | Explicitly documents scope exclusions and distinction between manual backtest viewer and five-layer React dashboard | **KEEP** as top-level project boundary. |

### Important root boundary

The root README and architecture/runbook documents explicitly distinguish:
- `dashboard/index.html`: legacy/manual backtest report viewer, not the React control plane.
- `control_dashboard/`: React dashboard and T4 control plane.
- `backtest_rsi_percent_b_h1_adx.py`: independent research script, not a Core First runtime component.

Do not merge these surfaces or count them as duplicate implementations.

## 3. Special-purpose packages

| Path | Evidence from package documentation | Disposition |
|---|---|---|
| `d07_9_lineage/` | Offline/synthetic D07.9 validator and D07.11 evidence resolver; dedicated schemas, requirements and tests | **KEEP INDEPENDENT**. Not a generic subfolder of T0 or synthetic evidence. |
| `t0_signature_stage1/` | Manual-only A2.2 Stage I synthetic harness; explicitly not a production signer/verifier and no canonical T0 access | **KEEP INDEPENDENT**. Its separate trust-policy status and manual approval gate must remain visible. |
| `synthetic_evidence/` | Separate cross-cutting synthetic verification package | **KEEP**. Do not absorb D07.9 or signature Stage I merely because all contain tests/fixtures. |
| `futures_intelligence/` | T1 CSV import/snapshot consumer with its own data contract | **KEEP** as independent T1 adapter/package. |
| `freqai_bridge/` | Prediction-only FreqAI bridge; consumes T0 via authenticated read-only HTTP | **KEEP** separate from Core runtime and paper execution. |
| `integrations/` | Optional read-only Hummingbot order-book bridge | **KEEP** separate from canonical T0 storage and order execution. |

## 4. Confirmed architecture boundaries

- `pipeline/api.py` imports `CORE_LEVERAGE` from root `risk_policy.py`; the latter is not an orphan based on the inspected source.
- `market_data/README.md` documents `market_data.api:application` as the T0 Candle API entrypoint.
- `dashboard/index.html` and `control_dashboard/` have distinct documented roles.
- `docs/FIVE_LAYER_ARCHITECTURE.md` explicitly states that the old `dashboard/index.html` is not the React Dashboard/control plane.
- The five-layer paper runbook identifies `control_dashboard/` and `pipeline/api.py` as T4.
- D07.9 and T0 Signature Stage I have separate execution instructions and explicit limitations.

## 5. Unresolved questions / next audit items

1. Find exact-branch deployment/start-command references for `app:app`; determine whether it is an active health facade, a legacy WSGI entrypoint, or both.
2. Trace every exact-branch reference to `backtest_rsi_percent_b_h1_adx.py`, `dashboard/index.html`, and root `requirements.txt` through workflows, docs and scripts.
3. Trace all imports of `risk_policy.py` and its test/CI coverage before proposing any package move.
4. Confirm whether `dashboard/` is accessed only via `app.py` or also through a static hosting workflow.
5. Build a complete import/caller graph from a local checkout at the pinned SHA before any source relocation.

## 6. Explicit non-actions

- No source files moved, renamed, deleted or edited.
- No workflows or dependency manifests changed.
- No tests or CI workflows run; no PASS is claimed for runtime behavior.
- No branch created; no merge, rebase, reset or force-push.
- No T0 canonical database, VPS, runtime, exchange or credential access.
- No AI execution, live trading or real order.

## 7. Verdict

**PARTIAL PASS — READ-ONLY STRUCTURE AUDIT.**

The current package boundaries are mostly defensible. The largest obvious maintenance issue is documentation/evidence discoverability, not proof of excessive runtime modularity. Keep source packages stable; prioritize a documentation index and exact-branch dependency graph before moving any code.

Next safe step: complete the exact-branch caller/entrypoint trace for `app.py`, the research backtest and the two dashboard surfaces.

## 8. Exact-branch entrypoint and caller trace (second pass)

Source examined at the current branch tree after the initial audit; findings below are based on direct reads of the named files. This is a targeted trace, not a complete static call graph.

### `app.py` and T0 health facade

- `app.py` defines a Flask WSGI object named `app`; it exposes `/dashboard` (serves `dashboard/index.html`), `/health/live`, `/health/ready`, `/health/data`, and aggregate `/health`.
- It imports `HealthEvaluator` from `market_data.feeder`. Its health snapshot provider is injected through Flask config; without a provider, storage/lease checks fail closed. This file is a health/dashboard facade, not the canonical Candle API implementation.
- Exact-branch caller found: `market_data/test_feeder_health_api.py` imports `from app import app` and exercises the health routes using Flask's test client.
- GitHub Actions `.github/workflows/t0-manual-validation.yml` installs the relevant requirements, runs `market_data.test_feeder_health_api` (with the other T0 component tests) and compiles `app.py`.
- `codemagic.yaml` also imports `app`, and retains legacy T0 health workflows that run the health API tests. Codemagic is documented as legacy/fallback, not the canonical Five-Layer CI runner.
- No current README production start command or deployment manifest for `app:app` was found in the inspected files. Actual hosted deployment/WSGI use is **NOT VERIFIED**.
- Disposition: **KEEP at root for now**. The Python import in the health API test is a concrete path dependency; moving requires a compatibility/import migration and tests. Do not conflate this Flask health facade with `market_data.api:application`, the separately documented T0 Candle API entrypoint.

### `dashboard/index.html` versus `control_dashboard/`

- `app.py` serves the legacy/manual viewer at `/dashboard`.
- `dashboard/index.html` declares that it only loads user-selected JSON/CSV files. Its JavaScript uses the file input and local `File.text()`; the reviewed source contains no `fetch()`, XMLHttpRequest, workflow dispatch or API call. It is a static manual report viewer, not a live dashboard.
- The independent research backtest writes `summary.json`, `trades.csv`, and `equity_curve_m15.csv`; the viewer recognizes JSON with `net_profit_usdt`/trade fields and CSV trade/equity files. This is a manual file hand-off, not an automated runtime dependency.
- `control_dashboard/` is the React T4 control plane. `pipeline/api.py` serves its built files under `/control` from `CONTROL_DIST_PATH` or `control_dashboard/dist`, with path containment and asset allowlisting. It is not served by `app.py`.
- Disposition: **KEEP BOTH SEPARATE**. The two dashboards have different users, data paths and trust/runtime responsibilities.

### `backtest_rsi_percent_b_h1_adx.py`

- The script is self-contained as a command-line research backtest, imports NumPy/Pandas/Requests, fetches public Binance Futures klines (with public Data Vision archive fallback), and writes research outputs under `rsi_percent_b_backtest` by default.
- It has no import of the Five-Layer packages or paper ledger in the inspected source. The README explicitly calls it an independent research script outside T0–T4.
- No direct workflow invocation was found in the inspected GitHub Actions T0/Core workflows or `codemagic.yaml`. This does not prove that no external/manual invocation exists.
- `dashboard/index.html` can display the script's saved outputs after manual file selection; it does not launch the script.
- Disposition: **KEEP AS AN INDEPENDENT RESEARCH ASSET**. A future move into a `research/` namespace is optional and requires a separate source-path migration plan; there is no demonstrated need to move it now.

### Dependency manifest implications

- `requirements.txt` contains Requests, NumPy, Pandas, Flask, Gunicorn, Cryptography and RFC8785. It supports the research script's scientific/data dependencies and the Flask app's runtime/test import; it is not safe to move or delete as if it belonged only to the research script.
- `requirements-web.txt` separately includes Flask, Requests, Gunicorn, Cryptography and RFC8785 for web/API workflows.
- `requirements-market-data.txt` contains CCXT and Psycopg dependencies.
- Keep dependency manifests unchanged until a reproducible dependency-ownership matrix and workflow install audit are completed.

## 9. Second-pass verdict

- `app.py` caller trace: **PARTIAL PASS** (test and workflow references confirmed; production deployment caller NOT VERIFIED).
- Manual dashboard boundary: **PASS** for inspected source (file-only viewer; separate from React control plane).
- Research backtest boundary: **PASS** for documented scope and inspected script; exhaustive external/manual caller search NOT VERIFIED.
- React control plane serving path: **PASS** for inspected `pipeline/api.py` route.
- Full repository-wide dependency/import graph: **NOT VERIFIED**.
- No source relocation is justified by this pass. Recommended next step is a documentation navigation index, not a source move. Preserve Core First, T0 and the existing runtime boundaries.
