# Core-First Readiness Plan — Strategy Core and Shared Risk

- Plan date: 2026-11-12
- Repository: `kenznguyen/btcusdt-telegram-signals2`
- Branch: `feature/t0-centralized-data-feeder-p1-20261101`
- Inspected source HEAD: `c7748adca424ea9d56004bcdb9669dd8db88d570`
- Inspected tree SHA: `8572ebe397506a9c1b7c94101c44b131c3ff4d8e` (recursive tree, not truncated)
- Plan status: **READY FOR OWNER REVIEW**
- Execution status: **NOT STARTED**

## 1. Objective

Establish a minimal, evidence-led readiness path for the existing Strategy Core (RSI + ADX + Smart DCA) and its existing Shared Risk / paper-ledger controls. The Core remains the only strategy in the paper decision path under the approved Core-First architecture.

This plan does not claim that the strategy is profitable, statistically validated, runtime-ready or authorized for live trading.

## 2. Read-only source inventory

Inspected files and exact Git blob SHAs at the source HEAD above:

| Component | Path | Blob SHA | Inventory finding |
|---|---|---|---|
| Core producer | `pipeline/core_strategy.py` | `c14e76f2cecb9f8aca54db263ded1ff17881cb24` | Native RSI/ADX/Smart-DCA producer; closed/complete candle checks; H1 filter; sizing; book validation; provenance-bound intent |
| Core producer tests | `pipeline/test_core_strategy.py` | `a0d5b46845d3fde006ed817fe21bdd8b6546c1d1` | 6 named tests covering indicators, incomplete windows, missing book, entry, DCA and exit priority |
| Core signal adapter | `pipeline/core_signal.py` | `df5fbb59611bdd4fbb8224665f79655dd4433455` | Validates source, market, direction, provenance and signal expiry |
| Core adapter tests | `pipeline/test_core_signal.py` | `a946716604e2e1a74b0e32f0aae5d07b820f2cbf` | 6 named tests covering LONG/SHORT/FLAT/WAIT, stale and invalid artifacts |
| Risk latch | `paper_execution/risk_control.py` | `3c76e462b0b4d924c2418842d95ed74285e2315d` | Persistent pause/kill latch; explicit acknowledged reset |
| Risk latch tests | `paper_execution/test_risk_control.py` | `69c9177a249369f52d0c81e442c9c4583c9f5b77` | 4 named tests for default state, persistence, priority and reset behavior |
| Paper ledger | `paper_execution/ledger.py` | `37c0aeb9dd28514dd19b87667b762c5592baf61f` | Atomic paper ledger; local/no-network module; risk and reservation checks |
| Ledger tests | `paper_execution/test_ledger.py` | `0c05ae1ed0d9526978f8a90c983957dbd7baed5a` | 19 named tests covering fills, idempotency, concurrency, stale books, corrupt state, Kill Switch and risk reductions |

The test fixtures generate deterministic candle/book data. Their passing would demonstrate software behavior against those fixtures, not historical market performance or real-world execution quality.

## 3. Existing CI entry points

1. `.github/workflows/p5-3-11-g2-integration-green.yml` (blob `3b75fdbf34768a315e5ed025b2ba0015ce138b17`) already compiles pipeline modules and runs `pipeline.test_core_signal` and `pipeline.test_core_strategy`. It sets `AI_EXECUTION_ENABLED=false`, blanks database and exchange credential environment variables, and explicitly excludes canonical runtime/exchange connectivity.
2. `.github/workflows/dual-ledger-red.yml` (blob `8b1620482dabd59d46e6f3f4e7ad66c178e520e8`) runs focused Core/API contracts and the full `paper_execution` unittest discovery, including risk-control and ledger regressions. It blanks database/exchange credentials and records exact source SHA.
3. Workflow definitions were inspected only. No workflow was triggered in this increment; no run ID or artifact is claimed.

## 4. Minimal readiness sequence

### R0 — Freeze scope and source baseline

- Keep the current branch and exact source baseline.
- No source edits or dependency changes in the inventory stage.
- Preserve Core thresholds and behavior; any threshold change requires a separate evidence-backed decision.
- Acceptance: exact SHA, tree and source blob inventory recorded. **Inventory PASS**.

### R1 — T0 data availability decision (separate gate)

- Determine whether a recoverable owner-held dataset exists; previous GitHub inventory did not find the canonical historical OOS payload.
- If no dataset exists, prepare a separate bounded T0 reacquisition decision covering period, M15/H1 requirements, collection method, retention, integrity, gap handling and immutable research export.
- Do not start T0, provision a VPS, connect to Binance, export candles or create a dataset under this plan.
- Acceptance: an explicit owner-approved data source and collection scope, followed by separately approved runtime/collection steps. **Current status: BLOCKED pending separate owner decision**.

### R2 — Deterministic Core contract CI

Use the existing tests first; do not duplicate them without a demonstrated gap.

- Verify RSI/ADX/DI warm-up and deterministic output.
- Verify closed-candle, complete-window, continuity and availability-time gates.
- Verify M15/H1 alignment and H1 trend filter.
- Verify LONG/SHORT entry transitions, WAIT cases and invalid/missing inputs.
- Verify Smart DCA eligibility, one-use state and margin sizing.
- Verify TP, soft stop and emergency stop precedence.
- Verify invalid/missing execution book produces no intent.
- Run focused existing Core tests on GitHub Actions at an exact SHA and retain logs/artifacts.
- Acceptance: all relevant deterministic tests PASS; no synthetic test result is described as market OOS. **Current status: NOT RUN at inspected SHA**.

### R3 — Shared Risk and paper-ledger contract CI

Use the existing risk-control and ledger tests plus existing full `paper_execution` regression.

- Verify persistent Kill Switch and pause; generic resume must not clear kill.
- Verify explicit acknowledged reset and fail-closed behavior for missing/corrupt state.
- Verify idempotent submission and concurrent duplicate protection.
- Verify one market snapshot cannot be reused by competing intents.
- Verify stale, future, crossed, duplicate and malformed book rejection.
- Verify pending-order, position, exposure, drawdown and daily-loss limits.
- Verify the recorded 1% Account Equity order-margin budget remains enforced; do not alter its policy.
- Verify only permitted exposure reductions can proceed under applicable risk latches.
- Acceptance: focused and full paper-execution regressions PASS with isolated temporary test databases; no production DB or runtime. **Current status: NOT RUN at inspected SHA**.

### R4 — Core-to-Risk-to-Paper integration contract

Only after R1–R3 pass:

- Validate the path from a validated Core intent through the existing Shared Risk Engine to the paper ledger.
- Verify the risk engine is the final authority and that rejected intents create no reservation/fill.
- Verify Kill Switch blocks new exposure and preserves the existing permitted risk-reduction semantics.
- Verify idempotency and atomicity under concurrent requests.
- Use isolated temporary databases and deterministic fixtures in CI.
- Acceptance: exact-SHA integration tests and uploaded evidence PASS. **Current status: NOT VERIFIED**.

### R5 — Data-backed paper evaluation (separate operational approval)

- Requires real, quality-checked T0 market data and a separately approved runtime/collection plan.
- First run as offline/backtest or replay using immutable, lineage-tracked data; then consider paper runtime only under a separate approval.
- Evaluate fees, slippage, funding, drawdown, exposure, DCA contribution and regime sensitivity. Compare with a simple baseline on the same population.
- Synthetic fixtures cannot satisfy this gate.
- Acceptance: owner-reviewed evidence and explicit approval for any runtime paper observation. **Current status: BLOCKED by R1 and separate runtime approval**.

## 5. Explicit non-goals and constraints

- No AI Strategy implementation, AI admission, AI Ledger, calibration registry, trusted-time provider, key enrollment, AI leverage policy or AI execution.
- No T1 activation.
- No change to T0/T1/T2/Core/CANCEL source behavior, Core thresholds, database schema, canonical data, ledger schema, Shared Risk Engine or Kill Switch in this planning increment.
- No VPS, runtime, service start/restart, exchange connection, Binance collection, data export or bundle creation.
- No live trading or real orders. `AI_EXECUTION_ENABLED=false`.
- Do not infer readiness from code presence, test fixtures, documentation or an unexecuted workflow.

## 6. Current disposition

| Area | Status | Reason |
|---|---|---|
| Source inventory | **PASS** | Exact branch HEAD/tree and source blobs inspected |
| Core implementation presence | **PASS — static inventory only** | Producer, adapter and tests exist |
| Core deterministic CI at inspected SHA | **NOT RUN** | Workflow not triggered |
| Risk/ledger test presence | **PASS — static inventory only** | Risk latch and 19 ledger tests exist |
| Risk/ledger CI at inspected SHA | **NOT RUN** | Workflow not triggered |
| Core-to-Risk integration acceptance | **NOT VERIFIED** | No exact-SHA run/evidence in this increment |
| Real T0 dataset availability | **BLOCKED** | Historical canonical payload not found in inspected GitHub sources; T0 recollection requires separate approval |
| Data-backed performance | **NOT VERIFIED** | No recoverable historical dataset / real OOS evidence |
| Runtime paper operation | **NOT AUTHORIZED by this plan** | Requires separate explicit approval |
| Live trading | **NOT AUTHORIZED** | Outside project scope |

## 7. Next action

The smallest next technical action, after owner approval, is to dispatch the existing isolated GitHub Actions workflows at the exact current branch SHA and record their run IDs, job conclusions and artifact IDs. No code changes are required before that baseline run. T0 data reacquisition remains a separate owner decision and must not be bundled into CI approval.
