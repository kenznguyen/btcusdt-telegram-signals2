# SIMULATED_CAPITAL_V1 — PaperLedger Semantics Audit and Runtime Design

Date: 2026-11-14 (Asia/Ho_Chi_Minh)
Branch: `feature/core-operational-proof-20261112`
Audit source HEAD: `c36e0cc8db830119444e22f581ec3e200e86a6b2`
Scope: read-only source audit and design. No runtime or database operation.

## 1. Result

**Audit: PASS WITHIN SOURCE-REVIEW SCOPE. Runtime integration: NOT IMPLEMENTED. PAPER Ledger readiness: BLOCKED / NOT VERIFIED.**

The existing dual-ledger path already has useful shared-risk primitives, but it is not a safe drop-in implementation of SIMULATED_CAPITAL_V1. It is built around a legacy/account funding cutover and funding-provenance readiness model. Its account migration intentionally leaves risk state not ready until equity and funding are reconciled. Simulated capital must be represented as an explicit synthetic capital origin, not fabricated as exchange funding or an account deposit.

No implementation should bypass the current risk-ready/funding checks by merely injecting a fake funding coverage row, cutover, or owner attestation.

## 2. Source inventory and exact blobs reviewed

| File | Blob SHA | Review |
|---|---|---|
| `paper_execution/ledger.py` | `03c76bcd3bab370c49d898fc1ba995073be995b1` | Dual account, migration, order admission and reservation flow |
| `paper_execution/risk_control.py` | `2309e1b31872cbbbc99ee2aade79d4f73ea42ace` | Persistent shared pause/kill latch |
| `paper_execution/bootstrap.py` | `2a75724d0071ecc340617bfc52f4198c09926c92` | Existing funding/equity/bootstrap evidence requirements |
| `paper_execution/daily_baseline.py` | `747808d9a68a70e9c2aa6f71f00aeeffb6682145` | Immutable UTC daily baseline and audit/replay |
| `paper_execution/simulated_capital.py` | `b3d23a212ba8c75cb49b7967654dfe6a67167cb6` | Approved v1 config validator only |
| `paper_execution/test_risk_limits.py` | `22645c481eea3f807fc72d659cdd05989f5673c5` | Existing shared-risk tests |
| `paper_execution/test_risk_control.py` | `5e1fdf60f9c2988d8e44e2019aa12de11c0dde9d` | Persistent kill/pause tests |
| `risk_policy.py` | `823d04748105b2996a28f2b09e3ce77bea073dce` | 1% order-margin constant and Core leverage policy |

## 3. Existing behavior mapped to approved limits

### 3.1 Shared account and exposure

- The dual-ledger schema stores `STRATEGY_CORE`, `AI_FREQAI` and `LEGACY_UNATTRIBUTED` under account ID 1.
- `_submit_scoped` executes inside SQLite `BEGIN IMMEDIATE`, so competing Core/AI order admissions serialize on the same database transaction.
- Gross exposure is calculated across all strategy-ledger positions and active reservation notionals, then the proposed increase is added. The check is account-wide, not strategy-local.
- This can support the approved shared 10 USDT cap once the account is a valid simulated-capital account and the risk inputs are accepted.

### 3.2 Drawdown and daily loss

- Admission recomputes equity from initial account capital, realized PnL, unrealized PnL at the accepted mark, fees, funding and legacy adjustments.
- Drawdown is measured against the persisted high-water mark; daily loss is measured against the persisted daily baseline.
- Daily baseline uses UTC day boundaries (`now_ms // 86_400_000 * 86_400_000`), not local Vietnam midnight.
- Breach at or above configured threshold latches the shared Kill Switch. Risk-reducing orders are allowed through the latch; exposure-increasing orders and DCA are blocked.
- Existing daily-baseline records are immutable and require replay/audit reconciliation. A simulated account needs its own truthful baseline-creation provenance; do not forge a funding cutover to satisfy the legacy baseline validator.

### 3.3 Order margin and leverage

- `risk_policy.py` defines `ORDER_MARGIN_BUDGET_PCT = 0.01`.
- Current dual-ledger admission calculates `admission_margin = equity * ORDER_MARGIN_BUDGET_PCT`, then `admission_notional = admission_margin * self.leverage`; it rejects when requested incremental notional exceeds that value.
- Core leverage is constrained to 1x. AI leverage is constrained to 1x–3x by `PaperLedger.__init__`.
- The approved contract includes `maxOrderMarginPct=1`, but the scoped admission currently reads the global constant rather than the contract field. This is a parity/integration gap: the runtime must load the validated contract and prove the effective percentage is exactly 1%.
- This is a per-order admission ceiling. It is not a separate aggregate cap on the sum of all open-order margins. Existing reservations do aggregate notional for the shared exposure cap. Whether a portfolio-wide aggregate margin ceiling is desired is not specified by SIMULATED_CAPITAL_V1 and must not be silently invented.

### 3.4 DCA

- ENTRY and DCA increases share the same exposure and order-margin admission path.
- DCA therefore consumes the same 1% per-order margin calculation and shared 10 USDT exposure budget.
- Existing dual-ledger state also has a `dca_used` boolean and rejects a second DCA for that strategy. This is a current implementation limitation, not a complete multi-step Smart DCA policy. Do not claim Smart DCA parity until the intended DCA lifecycle is reconciled with that flag and reservation/fill behavior.

### 3.5 Kill Switch

- `paper_risk_control` is persisted in the same SQLite database and is shared by Core and AI.
- Kill reset requires explicit acknowledgement and readiness. Generic resume cannot clear the latch.
- This is a suitable primitive to retain, but simulated-capital breach evaluation must update the same latch within the atomic admission transaction.

## 4. Blocking compatibility gap

The existing dual-ledger migration:
1. obtains initial capital from the legacy `paper_account_config`;
2. creates the dual-ledger account and strategy rows;
3. initializes risk state with `risk_ready=0` and reason `LEGACY_CUTOVER_REQUIRES_EQUITY_AND_FUNDING_RECONCILIATION`;
4. requires a valid account-equity cutover and funding provenance before risk admission becomes ready.

The current bootstrap manifest also requires funding evidence, funding population, equity cutover, and owner-attestation fields. Those represent the current real-account evidence workflow and must not be falsified to represent synthetic 100 USDT.

**Decision:** implement a separate, explicitly tagged simulated-capital origin and initialization path. Preserve legacy funding/cutover validation for accounts that use that origin. Do not modify existing databases or run migrations as part of this audit.

## 5. Proposed implementation boundary

Implement in a later, separately scoped code increment:

1. **Explicit account origin:** persist `capital_mode=SIMULATED`, `trading_mode=PAPER`, quote currency USDT, initial amount 100, contract ID/version and a deterministic account identity. The record must distinguish synthetic seed capital from deposits, exchange balances and funding events.
2. **One-time initialization:** use a single SQLite `BEGIN IMMEDIATE` transaction and unique singleton/account key. First initialization records an immutable seed event and starting equity baseline. Repeated initialization must return the existing matching account or fail on any mismatch; it must never reset, top up, or silently repair the balance.
3. **Restart invariance:** reopening the database must read the same account identity, initial capital, seed event, contract hash and ledger balances. Missing/corrupt/mismatched provenance fails closed.
4. **Accepted equity snapshot:** use one account-wide, validated and freshness-bounded mark/equity snapshot. Missing, stale, future-dated, non-finite, non-positive or unreconciled equity blocks all new exposure. No fallback to a caller-supplied initial capital argument.
5. **Atomic admission:** within the same `BEGIN IMMEDIATE` transaction, validate contract, account origin, accepted equity, UTC daily baseline, high-water mark, shared Core+AI filled/reserved exposure, pending reservations, Kill Switch and requested incremental margin; persist reservation/order/ledger updates atomically.
6. **Order margin:** enforce `requested_incremental_notional / effective_leverage <= equity * 0.01` using Decimal arithmetic. Load 1% from the validated contract and assert parity with the policy constant. Keep Core 1x; AI 1x–3x only if separately calibrated/approved by its policy. DCA increases use the exact same calculation.
7. **Shared exposure:** calculate gross filled exposure plus active reserved notional across Core and AI, then the proposed increase. Enforce <= 10 USDT. Do not count the same reservation twice.
8. **Loss controls:** use a persisted high-water mark and immutable UTC daily baseline; define equity as capital + realized + unrealized - fees - funding, with explicit source/mark provenance. At 10% drawdown or 2 USDT daily loss, atomically latch the shared Kill Switch and reject increases/DCA while allowing valid risk reductions.
9. **Audit and recovery:** append-only seed, baseline, contract-binding, admission and kill events; detect duplicate IDs and state divergence; add deterministic reopen/recovery tests. No automatic repair or reset.
10. **Smart DCA parity:** first specify whether multiple DCA legs are allowed and how each leg is identified, budgeted and reserved. Do not weaken the existing single-DCA guard as a shortcut.

## 6. Required TDD acceptance matrix

- Empty database: simulated account initialization occurs exactly once; initial equity is 100 USDT.
- Duplicate initializer, concurrent initializer and process-reopen: no duplicate seed and no reset/top-up.
- Same account with altered capital, contract ID/hash, currency or mode: fail closed.
- Missing/corrupt seed, account origin or contract binding: no new order.
- Missing/stale/future/invalid mark or equity: no new order or DCA.
- Core then AI, and AI then Core: combined filled + reserved exposure cannot exceed 10 USDT.
- Concurrent Core/AI admissions: serialization prevents both from independently spending the same exposure/margin budget.
- New order at exactly 1% margin boundary passes; above boundary rejects; test at 1x and AI 1x/3x.
- DCA uses the same margin and shared exposure limits; test reservation, partial fill, expiry, retry and restart.
- Daily loss exactly 2 USDT and drawdown exactly 10% latch Kill Switch; no increase after latch; valid reductions remain possible.
- UTC date rollover: baseline is created once from a valid accepted equity snapshot; replay/audit tampering fails closed.
- Full existing ledger, dual-ledger, funding, equity, risk and Kill Switch regression suite remains green.
- No test creates a real order, contacts an exchange, touches T0, VPS or production state.

## 7. Status and authorization boundary

- Approved SIMULATED_CAPITAL_V1 values: **APPROVED**.
- Existing ledger/risk semantics source audit: **PASS WITHIN SCOPE**.
- Contract/validator/synthetic CI: **PASS WITHIN PREVIOUSLY RECORDED SCOPE** (run 43601696202 at source `66cdc68e3beadce31c4f57175ef4b8b80de59e5d`, 6/6 tests).
- Runtime simulated-capital persistence: **NOT IMPLEMENTED**.
- Contract-to-order-margin wiring: **NOT IMPLEMENTED**.
- Simulated account initialization and atomic risk enforcement: **NOT IMPLEMENTED**.
- Smart DCA multi-leg parity: **NOT VERIFIED**.
- PAPER Ledger readiness: **BLOCKED / NOT VERIFIED**.
- Bootstrap and Runner: **NOT AUTHORIZED**.

No code, schema, workflow, test, database or runtime state was changed in this audit. No migration, Bootstrap, Runner, exchange access, live order, T0 operation or VPS operation was performed.

## 8. Next step

A separate implementation increment may add the simulated-origin persistence and contract-bound atomic admission path using TDD, without activating Bootstrap or Runner. Before that implementation, freeze the simulated-account origin schema and Smart DCA leg semantics; retain all fail-closed conditions above.
