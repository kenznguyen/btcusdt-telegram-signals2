# SIMULATED-only Shared Order Admission V1 — Implementation and CI Evidence

Date: 2026-11-14
Branch: `feature/core-operational-proof-20261112`
Implementation source SHA: `a65025f517affbba46756d020150b4f6ddff31bb`
Test specification commit: `ff573a71e6a2c6d9d79694b4edcba8fc4c452c1f`

## Scope

Additive writer-side support for a valid SIMULATED-only account to pass the same shared PAPER risk admission checks without fabricated funded-account cutover or funding evidence. The funded-account admission path remains unchanged.

No operational database, VPS, T0, Bootstrap runtime, Runner, exchange, AI execution, live order, or real trade was used.

## Implementation

- `PaperLedger._submit_scoped` identifies a SIMULATED account only through `verify_simulated_equity_origin`.
- It validates the current UTC daily-baseline provenance chain using `verify_simulated_daily_baseline_provenance`.
- A verified SIMULATED account may proceed without a funded cutover row or funding-coverage proof. The funded branch still requires both.
- The existing shared risk checks remain in force: risk readiness, mark freshness, account equity, drawdown, daily loss, shared exposure/reservations, per-order 1% margin ceiling, and Kill Switch.
- Core ENTRY and DCA use the same writer admission and reservation path. Existing one-DCA-per-position lifecycle behavior is not changed.
- Test risk limits now match the approved simulated contract: max drawdown 10%, max daily loss 2 USDT, max exposure 10 USDT.

Source blob:
- `paper_execution/ledger.py`: `4eca46c42a54d48afe067c3acd14fe305fc188c1`

Test blob:
- `paper_execution/test_simulated_order_admission.py`: `c20e63f095ffb0460ddbcbd4a03fadcbd452b95a`

## TDD evidence

- RED test commit: `ff573a71e6a2c6d9d79694b4edcba8fc4c452c1f`.
- RED workflow run: [43608778212](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43608778212), source SHA `ff573a71e6a2c6d9d79694b4edcba8fc4c452c1f`, 4 expected failures across Core ENTRY, DCA, and Kill Switch tests. The writer returned `RISK_INPUTS_UNAVAILABLE` because it still required funded cutover.
- GREEN implementation source SHA: `a65025f517affbba46756d020150b4f6ddff31bb`.
- Simulated Capital V1 workflow: [43608805148](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43608805148), job `132489066899`, SUCCESS; `py_compile`, JSON parse and 32/32 unit tests PASS.
- PaperLedger compatibility workflow: [43608805101](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43608805101), job `132489120079`, SUCCESS; 144/144 tests PASS, including funded dual-ledger ENTRY/DCA reservation and risk-control regression.
- No workflow artifact was uploaded for these two runs.

## Disposition

- SIMULATED Core ENTRY without funded cutover: PASS within CI test scope.
- SIMULATED Core DCA through shared admission: PASS within CI test scope.
- 1% per-order margin rejection: PASS within CI test scope.
- Shared Kill Switch rejection: PASS within CI test scope.
- Funded PaperLedger compatibility: PASS within the 144-test compatibility suite.
- Bootstrap compatibility and broader operational-proof workflow: still running at time of this report; NOT VERIFIED pending terminal run results.
- AI Trusted Admission Context / admitted leverage: NOT IMPLEMENTED / BLOCKED. AI must remain fail-closed until calibrated, provenance-bound leverage in the approved 1x–3x range is supplied.
- Runtime readiness / PAPER Ledger activation: BLOCKED / NOT VERIFIED.

## Next step

Wait for the same-source Bootstrap compatibility and operational-proof workflows to finish. Reconcile their exact checkout SHA and test results, then update this report and the session handoff. Do not activate Bootstrap or Runner.
