# T2 Dual Ledger GREEN Evidence — 2026-11-08

## Scope

Implement the first paper-only accounting slice for Dual-Strategy Intelligence:

- Separate CORE and AI ledger namespaces in one durable SQLite file.
- Independent positions, DCA count, equity, and realized PnL.
- Shared Risk Engine reads both ledgers and sums gross margin without offsetting opposite directions.
- Each accepted entry/DCA calculates required margin as 1% of supplied account equity.
- No fixed position-count cap.
- Fail-closed gates for stale data, unreconciled state, Kill Switch, and insufficient collateral.
- Reductions remain admissible under Kill Switch when the target position and quantity are valid.
- No exchange order submission.

## Source changes

Branch: `feature/dual-strategy-phase22-preholdout-attestation-20261031`

PR #95:
- State: OPEN / DRAFT / NOT MERGED.
- Head SHA: `d4e04a701ae229c585d4598e93632831791c74d3`.
- Base branch: `feature/dual-strategy-phase22-frozen-reproducibility-20261031`.
- Base SHA: `b8f120fa0975225e5b7ff6243bd374cbde80b158`.

Commits in this increment:
- Implementation: `d4e5d05070e18478f9bfc7927d881e3658f7affe` — `quant_system/dual_ledger.py`.
- Expanded tests: `d4e04a701ae229c585d4598e93632831791c74d3` — `quant_system/test_dual_ledger_contract.py`.

The RED workflow and original RED evidence were retained. No T0/T1 files, strategy rules, FreqAI artifacts, or runtime settings were changed.

## Verification

### T2 direct push — exact head SHA

- Workflow: T2 Dual Ledger Contract.
- Run ID: `42454140520`.
- URL: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42454140520
- Event: `push`.
- PR head / workflow head SHA: `d4e04a701ae229c585d4598e93632831791c74d3`.
- Job ID: `128649446306`.
- Checked-out SHA from job log: `d4e04a701ae229c585d4598e93632831791c74d3`.
- Job conclusion: SUCCESS.
- Test summary: **11 tests, OK**.
- Artifact: none produced by this workflow.

### T2 pull-request merge-context run

- Workflow run: `42454144922`.
- URL: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42454144922
- Event: `pull_request`.
- PR head SHA: `d4e04a701ae229c585d4598e93632831791c74d3`.
- Base SHA: `b8f120fa0975225e5b7ff6243bd374cbde80b158`.
- Synthetic merge/check-out SHA: `41a059bdc40c74c5c5b028ef78de3d7e8068935e`.
- Job conclusion: SUCCESS.
- Test summary: **11 tests, OK**.
- This is merge-context verification, not a direct-head checkout. The direct-head evidence is the push run above.

### T0 adapter regression at exact PR head

- Workflow run: `42454144881`.
- URL: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42454144881
- Event: `pull_request`.
- PR head SHA: `d4e04a701ae229c585d4598e93632831791c74d3`.
- Checked-out SHA from workflow log: `d4e04a701ae229c585d4598e93632831791c74d3`.
- Base SHA: `b8f120fa0975225e5b7ff6243bd374cbde80b158`.
- Job conclusion: SUCCESS.
- Test summary: **10 tests, OK**.
- Artifact ID: `13606424039`.
- Artifact name: `f1-t0-freqtrade-adapter-41a059bdc40c74c5c5b028ef78de3d7e8068935e`.
- Artifact size: 943 bytes; not expired at metadata inspection.
- GitHub upload SHA-256 digest from job log: `7cff01c719d5a6f87396da40bb6ce6fd8cd6ff255d5b27289f15e61146707711`.
- Artifact payload has not been downloaded and independently re-hashed; payload checksum verification remains NOT VERIFIED.

### R22.2 isolated Phase 22 runtime verification

- Run ID: `42454144968`.
- URL: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42454144968
- At evidence capture: IN_PROGRESS; no conclusion or artifact asserted.
- This run is not required to claim the 11-test T2 contract result. Update this evidence if/when the run completes.

## Test coverage — 11/11

1. CORE/AI position isolation in one persistent store.
2. DCA state isolation.
3. DCA rejects missing or ambiguous position identity.
4. One-percent margin calculation for entry and DCA.
5. Independent equity and realized PnL.
6. Kill Switch blocks entry/DCA and permits validated reduction.
7. Restart persistence without cross-contamination.
8. No fixed position-count cap in the tested shared-collateral range (12 positions).
9. Gross margin sums opposite LONG/SHORT positions without netting.
10. Insufficient collateral blocks admission if gross margin leaves less than 1% for the next increase.
11. Stale data and unreconciled state fail closed.

## Review findings and boundaries

The 11 tests PASS, but this is **not full Dual-Strategy execution certification**.

Required next work before wiring both signal streams into paper execution:

1. **Atomic shared admission is not implemented.** `admit_entry` and `admit_dca` are read-only checks; they do not persist a shared reservation. Concurrent CORE and AI admissions could evaluate the same pre-admission snapshots. Implement a transactional shared reservation/fencing boundary before combined portfolio use.
2. **Ledger writes are not bound to a RiskDecision.** `record_entry` and `record_dca` can be called directly. The next coordinator must enforce that every increase has a current accepted risk decision and consumes its reservation exactly once.
3. **Collateral policy is provisional.** Available collateral is currently calculated as supplied account equity minus gross recorded margin, effectively preventing recorded margin from exceeding 100% of that equity. This is a collateral guard, not an explicitly approved total-risk/exposure ceiling. Confirm the portfolio margin budget before combined paper testing.
4. **Reduction mutation is not implemented here.** The module validates a reduction intent but does not yet update/close the ledger position. Implement the accounting transition with tests before paper replay.

## Status

- Independent ledger persistence contract: **PASS (11/11)**.
- Shared gross-margin calculation and admission gates: **PASS (11/11)**.
- Exact-head GitHub Actions verification: **PASS**.
- Full atomic shared-risk enforcement: **BLOCKED / NOT IMPLEMENTED**.
- Combined CORE + AI paper replay: **NOT RUN**.
- T0/T1 runtime integration: **NOT RUN**.
- Live execution: **DISABLED**.

## Restrictions

- Keep `ai_execution_enabled=false`.
- Paper/research only; no real orders.
- Do not create/open canonical T0 DB, start Feeder, connect to exchange, or sync market data.
- Do not modify T0/T1 schemas or interfaces.
- Do not merge PR #95 or any other PR without explicit user approval.

## Next step

Write RED tests for atomic shared risk reservation, duplicate reservation prevention, exactly-once consumption by CORE/AI ledger writes, and reduction accounting. Then implement the smallest transactional coordinator and rerun the exact-head GitHub Actions gates.
