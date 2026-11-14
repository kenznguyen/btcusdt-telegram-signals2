# SIMULATED_CAPITAL_V1 — Atomic SIMULATED Equity Initialization

Date: 2026-11-14 (Asia/Ho_Chi_Minh)  
Repository: `kenznguyen/btcusdt-telegram-signals2`  
Branch: `feature/core-operational-proof-20261112`  
Implementation source baseline: `e999343a4b9097a42a0b8adadd24b06b90a2c0d7`  
Latest source/test commit at report preparation: `15a3e8b61f388a54b094f8bf3cb35c03b0f5d694`  
Disposition: **IMPLEMENTATION PRESENT — TEST/CI NOT VERIFIED; RUNTIME BLOCKED**

## 1. Owner authorization

On 2026-11-14 the Owner explicitly approved the SIMULATED-only Equity Initialization V1 design after the prior atomic-composability audit.

Approved scope:
- SIMULATED/PAPER account with initial capital 100 USDT.
- Immutable simulated capital origin and a separate immutable seed event; the seed is never a funding/deposit event.
- Initial HWM = 100 USDT and UTC daily baseline = 100 USDT.
- Account migration, origin, seed, equity-origin record and risk-state baseline must share one `BEGIN IMMEDIATE` transaction.
- Restart is idempotent and must not reset the original timestamp or evolved risk state.
- Contract mismatch, funded/non-empty identity, or partial/corrupt provenance fails closed.
- Existing funded-account Bootstrap/cutover behavior remains unchanged.
- Tests use disposable SQLite databases only.

Not authorized: operational database migration, VPS/SSH, Runner, service startup, T0/T1/T2 data mutation, exchange connectivity, AI execution, live trading or real orders.

## 2. Implementation

### New module — `paper_execution/simulated_equity.py`

- Requires an active caller-owned transaction and uses a savepoint; it never commits the caller's transaction.
- Requires an existing dual-ledger PAPER account with capital exactly 100 USDT.
- Requires all strategy ledgers to be flat/zero and no orders, account adjustments, funding events, funding coverage or equity cutover rows.
- Persists `paper_simulated_equity_origin` with exact contract SHA-256, initial equity, HWM, UTC day, baseline, timestamp, source and canonical record digest.
- Adds immutable UPDATE/DELETE triggers.
- Calls the existing immutable origin/seed primitive; seed remains separate from `paper_funding_events`.
- Writes HWM and UTC daily baseline into `paper_account_risk_state`.
- Deliberately keeps `risk_ready=0` with `SIMULATED_INITIAL_MARK_REQUIRED`; an initial market mark and the existing risk readiness checks are still required before order admission.
- On restart, verifies exact origin/contract binding and does not reset the live risk state or its version.

### Ledger transaction seam — `paper_execution/ledger.py`

- Adds optional `simulated_contract_bytes` and `simulated_initialized_at_ms` constructor inputs.
- Only `STRATEGY_CORE` with migrations enabled can request this path.
- Rejects conversion of an already-existing dual-ledger account unless the immutable simulated-origin row already exists (idempotent restart only).
- Acquires `BEGIN IMMEDIATE` before account migration when simulated initialization is requested; account creation by `migrate_dual_ledger`, origin, seed, equity origin and HWM/baseline writes remain inside the same connection transaction.
- The existing funded-account cutover helpers were not changed or called by this path.

### Tests — `paper_execution/test_simulated_equity.py`

Test specifications cover:
1. Initial 100 USDT equity/HWM/UTC baseline and distinct seed/funding ledgers.
2. Restart idempotence and preservation of the original origin.
3. No conversion of funded/non-empty accounts.
4. Exact contract mismatch fail-closed behavior.
5. Rollback of origin/seed/equity-origin on injected failure.
6. Immutable equity-origin rows.
7. Restart does not reset evolved HWM/baseline/version.

### CI workflow

`.github/workflows/simulated-capital-v1-contract.yml` now includes the new module, tests and ledger source in its compile/test commands and path filters.

## 3. Source identity

| File | Git blob SHA |
|---|---|
| `paper_execution/simulated_equity.py` | `4c3128875b900a0a632dfa83dfb1ad6b61443830` |
| `paper_execution/test_simulated_equity.py` | `11003b6053482237af9a06578f1456d8b62b09b1` |
| `paper_execution/ledger.py` | `81695a592e35559e3a542fc11aa5a1d43558d88d` |
| `paper_execution/simulated_origin.py` | `6c5dd0452021b42a01189ecb09b0a2f8043dd7ef` |
| `.github/workflows/simulated-capital-v1-contract.yml` | `40cd3d3e3b0d0c5ee7e4137eabd31a970f956f6a` |

## 4. Verification

- Test specification was committed before the implementation module: test commit `4cf4ba11f01ee1c98c9635ccd1cbfe755e626707`; implementation module commit `67c419ee6dfb0bb9c880a9b8250c466d57d3d100`.
- The repository's available workflow-run lookup exposes PR-triggered runs only; no matching PR run was returned for these push commits. Combined commit status for latest source commit `5c55ef98f3cd48203acb78328d69c2a624926d0c` returned no status checks.
- No local Python execution environment connected to this repository was available in this work session.
- Therefore the RED failure was **NOT CAPTURED**, compile/tests are **NOT RUN / NOT VERIFIED**, GitHub Actions result is **NOT VERIFIED**, and no artifact is recorded.
- No runtime, VPS or database operation was performed.

## 5. Disposition and next gate

- Design authorization: **PASS — OWNER APPROVED**.
- Code and test specification committed: **PRESENT**.
- Atomic transaction structure: **IMPLEMENTED BY SOURCE INSPECTION; NOT TEST VERIFIED**.
- Funded-account regression preservation: **NOT VERIFIED BY TEST**.
- Test suite/compile/CI: **NOT VERIFIED**.
- PAPER Ledger readiness/order admission: **BLOCKED** until tests pass and initial market mark/risk readiness is independently established.
- Runtime/VPS/operational database: **NOT AUTHORIZED**.

Next: obtain a verifiable GitHub Actions run on the exact latest branch SHA, fix any failures with test-first evidence, then add a funded-account regression test. Do not perform runtime initialization or enable order admission as part of this increment.
