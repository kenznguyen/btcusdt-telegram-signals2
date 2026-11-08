# T2 Dual Ledger GREEN Evidence — 2026-11-08

## Scope

Implement the first paper-only Dual-Strategy accounting and shared-admission slices:

- Separate CORE and AI ledger namespaces in one durable SQLite file.
- Independent positions, DCA count, equity, and realized PnL.
- Shared gross margin and gross notional exposure are calculated across CORE + AI without netting opposing LONG/SHORT positions.
- Each admitted entry/DCA calculates required margin as 1% of supplied account equity.
- No fixed position-count cap.
- Atomic shared reservation serializes concurrent CORE/AI admission through SQLite `BEGIN IMMEDIATE`.
- Pending reservations count against available collateral and gross exposure until consumed.
- Ledger entry/DCA writes consume one reservation atomically and cannot exceed the reserved notional exposure.
- Stale data, unreconciled state, Kill Switch, and insufficient collateral fail closed.
- Kill Switch blocks increases but a validated reduction intent remains admissible.
- No exchange order submission.

## Source changes

Branch: `feature/dual-strategy-phase22-preholdout-attestation-20261031`

PR #95:
- State: OPEN / DRAFT / NOT MERGED.
- Head SHA at evidence capture: `1d3359cbcadaa9b7d2b7872ff349b32c5be98390`.
- Base branch: `feature/dual-strategy-phase22-frozen-reproducibility-20261031`.
- Base SHA: `b8f120fa0975225e5b7ff6243bd374cbde80b158`.

Implementation/test commits in this increment:
- Initial ledger/risk implementation: `d4e5d05070e18478f9bfc7927d881e3658f7affe`.
- Atomic reservation implementation: `a217dc28d758abfa738c60138fbb145f864cb99a`.
- Restore-only API separation: `383fd7e5b5cc4051a1f0a816fd94099dc5f6b025`.
- Gross notional exposure implementation: `2b1e6597858673b3eef91007b0cb60e0348a526e`.
- Reserved exposure consumption fix: `3739c8272ad3885d27ae8b46b98f44826b56d9fc`.
- Exposure enforcement tests: `fab6b3fb33ff63b1259f40984d6961ddf6203269`.
- Pending exposure aggregation assertion: `1d3359cbcadaa9b7d2b7872ff349b32c5be98390`.

Files:
- `quant_system/dual_ledger.py`
- `quant_system/test_dual_ledger_contract.py`
- Existing T2 contract workflow unchanged.
- No T0/T1 schema, source, strategy rules, FreqAI model, or runtime settings changed.

## RED → GREEN evidence

### Atomic reservation RED

- Run: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42454340727
- Run ID: `42454340727`, event `push`, source SHA `f8d4d4a31b146ea3bdf28a5fd46aac7a596d4e64`.
- Result: FAILURE as expected; 15 tests ran, 4 reservation-contract errors because persistent reservation APIs did not exist.
- This is the RED proof for the atomic reservation slice.

### Latest T2 direct push — exact head

- Run: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42454705548
- Run ID: `42454705548`, event `push`, conclusion SUCCESS.
- PR/code source SHA: `1d3359cbcadaa9b7d2b7872ff349b32c5be98390`.
- Job ID: `128651142263`.
- Checked-out source is the direct push SHA; job summary: **17 tests, OK**.
- Artifact: none produced by this workflow.

### Latest T2 pull-request merge-context run

- Run: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42454708246
- Run ID: `42454708246`, event `pull_request`, conclusion SUCCESS.
- PR head SHA: `1d3359cbcadaa9b7d2b7872ff349b32c5be98390`.
- Base SHA: `b8f120fa0975225e5b7ff6243bd374cbde80b158`.
- Checked-out synthetic merge SHA: `4fdcafafa008f1f2bfcae29134c7b56e512fde1a`.
- Job ID: `128651150310`.
- Test summary: **17 tests, OK**.
- This is merge-context verification, not a direct-head checkout. Exact-head proof is the push run above.

### T0 adapter regression at exact PR head

- Run: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42454708185
- Run ID: `42454708185`, event `pull_request`, conclusion SUCCESS.
- PR head and checked-out SHA: `1d3359cbcadaa9b7d2b7872ff349b32c5be98390`.
- Base SHA: `b8f120fa0975225e5b7ff6243bd374cbde80b158`.
- Test summary: **10 tests, OK**.
- Artifact ID: `13607446120`.
- Artifact name: `f1-t0-freqtrade-adapter-4fdcafafa008f1f2bfcae29134c7b56e512fde1a`.
- Size: 943 bytes; not expired at metadata inspection.
- GitHub upload SHA-256 digest: `d665868f664994c9d53085f047a84e14090df3e1f38ae07645295cc7a7941c33`.
- Artifact payload bytes have not been downloaded and independently re-hashed.

### R22.2 isolated Phase 22 runtime verification

- Latest run for source SHA `1d3359cbcadaa9b7d2b7872ff349b32c5be98390`: run ID `42454708188`.
- URL: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42454708188
- At evidence capture: PENDING; no conclusion or artifact asserted.
- Earlier R22.2 run `42454144968` passed 8 tests on source head `d4e04a701ae229c585d4598e93632831791c74d3`, but it does not certify the later gross-exposure/reservation changes.

## Test coverage — 17/17

1. CORE/AI position isolation in one persistent store.
2. DCA state isolation.
3. DCA rejects missing or ambiguous position identity.
4. One-percent margin calculation for entry and DCA.
5. Independent equity and realized PnL.
6. Kill Switch blocks entry/DCA and permits validated reduction intent.
7. Restart persistence without cross-contamination.
8. No fixed position-count cap in the tested shared-collateral range (12 positions).
9. Gross margin sums opposing LONG/SHORT positions without netting.
10. Gross notional exposure sums opposing LONG/SHORT positions without netting.
11. Insufficient collateral blocks admission if gross margin leaves less than 1% for the next increase.
12. Stale data and unreconciled state fail closed.
13. Concurrent CORE/AI reservations serialize against one shared collateral budget.
14. Duplicate reservation ID cannot be reused across strategies.
15. Reserved entry is consumed exactly once by the matching ledger.
16. Reserved DCA is consumed exactly once and updates only the target ledger.
17. Entry/DCA ledger mutations cannot exceed the notional exposure reserved.

## Review findings and remaining boundaries

This is a passing ledger/reservation slice, **not full Dual-Strategy execution certification**.

1. **Gross exposure ceiling is not defined.** The engine calculates and reports gross notional exposure, including pending reservations, but no maximum gross exposure threshold was invented. A portfolio exposure limit must be explicitly set before combined paper use.
2. **Collateral ceiling is provisional.** Available collateral currently uses supplied account equity minus gross recorded/pending margin, effectively preventing committed margin from exceeding 100% of that equity. This is a collateral guard, not an approved total-risk ceiling. Confirm the intended portfolio margin budget before combined paper testing.
3. **Reservation recovery is incomplete.** Unconsumed RESERVED rows fail closed and continue holding collateral. There is not yet an evidence-backed cancellation/reconciliation API for orphaned reservations after an interrupted process.
4. **Reduction accounting is incomplete.** The module validates a reduction intent, but does not yet atomically reduce/close position quantity, release margin, and book realized PnL/fees.
5. **Signal coordinator integration is not implemented.** The future CORE and AI signal routes must use persistent `reserve_entry`/`reserve_dca` and consume reservations through `record_reserved_entry`/`record_reserved_dca`. The `restore_position`/`restore_dca` methods are for reconciled restore only, not new strategy intents.
6. Stateless `admit_entry`/`admit_dca` remain suitable for deterministic offline analysis; they do not create persistent reservations.

## Status

- Independent CORE/AI ledger accounting: **PASS (17/17 focused tests)**.
- Atomic shared collateral reservations: **PASS (concurrency and exactly-once tests)**.
- Gross notional exposure aggregation/no directional netting: **PASS (focused tests)**.
- Exact-head GitHub Actions T2: **PASS**.
- Exact-head T0 adapter regression: **PASS**.
- Latest R22.2 for current SHA: **PENDING / NOT VERIFIED**.
- Gross exposure policy threshold: **NOT DEFINED**.
- Reservation orphan recovery: **NOT IMPLEMENTED**.
- Reduction accounting: **NOT IMPLEMENTED**.
- Signal coordinator / combined CORE + AI replay: **NOT RUN**.
- T0/T1 live data integration: **NOT RUN**.
- Production readiness: **NOT CERTIFIED**.

## Restrictions

- Keep `ai_execution_enabled=false`.
- Paper/research only; no real orders.
- Do not create/open canonical T0 DB, start Feeder, connect to exchange, or sync market data.
- Do not change T0/T1 schemas or interfaces.
- Do not merge PR #95 or any other PR without explicit user approval.

## Next step

Continue T2 in this order:
1. Add evidence-backed cancellation/reconciliation for interrupted reservations.
2. Add transactional reduction/close accounting, including margin release and realized PnL/fees.
3. Integrate Strategy Core and AI signal routes with the persistent reservation API.
4. Confirm gross exposure ceiling and portfolio margin budget before combined paper replay.
