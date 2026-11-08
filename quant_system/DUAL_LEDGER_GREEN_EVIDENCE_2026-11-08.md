# T2 Dual Ledger GREEN Evidence — 2026-11-08

## Scope

Paper-only Dual-Strategy accounting and shared-risk slices implemented:

- Independent CORE/AI position, DCA, equity and realized-PnL ledgers.
- Shared gross margin and gross notional exposure across both strategies; opposing LONG/SHORT positions are summed, never netted.
- 1% account-equity margin for each admitted entry/DCA.
- No fixed position-count cap.
- Atomic shared reservations using SQLite `BEGIN IMMEDIATE`; pending reservations count against collateral and gross exposure.
- Reservation ID uniqueness and exactly-once consumption by the matching strategy ledger.
- Ledger consumption rejects actual notional greater than the reserved notional.
- Evidence-backed cancellation of unresolved reservations; cancellation releases collateral and cannot be repeated or reused.
- Partial/full reductions atomically reduce quantity, release proportional margin, and book realized PnL/fees.
- Stale data, unreconciled state, Kill Switch, and insufficient collateral fail closed.
- No exchange order submission.

## Source and PR identity

- Repository: `kenznguyen/btcusdt-telegram-signals2`.
- Branch: `feature/dual-strategy-phase22-preholdout-attestation-20261031`.
- PR #95: OPEN / DRAFT / NOT MERGED.
- Current code/test head at evidence capture: `afa44c4bbab5a86040aadbeed219df7fe10a87cb`.
- Base branch: `feature/dual-strategy-phase22-frozen-reproducibility-20261031`.
- Base SHA: `b8f120fa0975225e5b7ff6243bd374cbde80b158`.

Key commits:
- Initial ledger/risk implementation: `d4e5d05070e18478f9bfc7927d881e3658f7affe`.
- Atomic shared reservation: `a217dc28d758abfa738c60138fbb145f864cb99a`.
- Gross notional exposure: `2b1e6597858673b3eef91007b0cb60e0348a526e`.
- Reservation/reduction RED tests: `1ca8aeb716b95c30f49e1a0f8aad5f4255067c6c`.
- Reservation cancellation + reduction implementation: `afa44c4bbab5a86040aadbeed219df7fe10a87cb`.

Files changed:
- `quant_system/dual_ledger.py`
- `quant_system/test_dual_ledger_contract.py`
- `quant_system/DUAL_LEDGER_RED_EVIDENCE_2026-11-08.md`
- `quant_system/DUAL_LEDGER_GREEN_EVIDENCE_2026-11-08.md`
- `docs/T2_SESSION_HANDOFF_2026-11-08.md`
- Existing GitHub Actions workflow retained; no CI platform migration.

## RED → GREEN evidence

### Reservation/reduction RED

- Run: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42454847720
- Run ID: `42454847720`, event `push`, source SHA `1ca8aeb716b95c30f49e1a0f8aad5f4255067c6c`.
- Result: expected FAILURE; 21 tests ran, 4 errors because `cancel_reservation` and `record_reduction` did not exist.

### T2 direct push — exact head

- Run: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42454885138
- Run ID: `42454885138`, event `push`, conclusion SUCCESS.
- Source SHA and checked-out SHA: `afa44c4bbab5a86040aadbeed219df7fe10a87cb`.
- Job ID: `128651680137`.
- Result: **21 tests, OK**.
- Artifact: none.

### T2 pull-request merge-context run

- Run: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42454888637
- Run ID: `42454888637`, event `pull_request`, conclusion SUCCESS.
- PR head SHA: `afa44c4bbab5a86040aadbeed219df7fe10a87cb`.
- Base SHA: `b8f120fa0975225e5b7ff6243bd374cbde80b158`.
- Checked-out synthetic merge SHA: `b8312df971472df2f6118641aac3b186c00f916b`.
- Job ID: `128651689985`.
- Result: **21 tests, OK**.
- This is merge-context verification; direct-head evidence is the push run above.

### T0 adapter regression at exact PR head

- Run: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42454888690
- Run ID: `42454888690`, event `pull_request`, conclusion SUCCESS.
- PR head and checked-out SHA: `afa44c4bbab5a86040aadbeed219df7fe10a87cb`.
- Base SHA: `b8f120fa0975225e5b7ff6243bd374cbde80b158`.
- Result: **10 tests, OK**.
- Artifact ID: `13606719354`.
- Artifact name: `f1-t0-freqtrade-adapter-b8312df971472df2f6118641aac3b186c00f916b`.
- Size: 942 bytes; not expired at metadata inspection.
- GitHub upload SHA-256 digest: `caeb66ffe65f92fd5e1ddfe8159d8f92f5770911ffd4104db77b579344e9e914`.
- Artifact payload bytes have not been independently downloaded and re-hashed.

### R22.2 isolated Phase 22 verification

- Latest run for code SHA `afa44c4bbab5a86040aadbeed219df7fe10a87cb`: run ID `42454888603`.
- URL: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42454888603
- At evidence capture: IN_PROGRESS; no conclusion or artifact asserted.
- Earlier R22.2 PASS on older source SHA does not certify the latest reservation/reduction implementation.

## Test coverage — 21/21

1. CORE/AI position isolation in one persistent store.
2. DCA state isolation.
3. DCA rejects missing or ambiguous position identity.
4. 1% margin calculation for entry and DCA.
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
15. Reserved entry is consumed exactly once by its matching ledger.
16. Reserved DCA is consumed exactly once and updates only the target ledger.
17. Entry/DCA mutation cannot exceed reserved notional.
18. Pending gross exposure is included in subsequent admission decisions.
19. Reservation cancellation requires reconciliation evidence and releases collateral.
20. Partial reduction releases proportional margin and books realized PnL/fees.
21. Full reduction closes the position; over-reduction is rejected without mutation.

## Review findings and remaining boundaries

This is a passing ledger/risk-accounting slice, **not full Dual-Strategy execution certification**.

1. **Gross exposure ceiling is not defined.** Engine calculates and reports gross notional exposure but does not invent a maximum. Set the intended gross exposure limit before combined paper use.
2. **Collateral ceiling is provisional.** Available collateral is account equity minus gross recorded/pending margin, effectively preventing committed margin from exceeding 100% of supplied equity. Confirm this portfolio margin budget before combined paper use.
3. **Signal coordinator integration is not implemented.** CORE and AI signal routes must use persistent `reserve_entry`/`reserve_dca` and consume through `record_reserved_entry`/`record_reserved_dca`. The `restore_position`/`restore_dca` methods are for reconciled restore only.
4. **Legacy signal/paper route is incompatible and remains unchanged.** `quant_system/dual_strategy.py` still routes through `RiskSnapshot.max_positions`, and `_select` arbitrates CORE/AI into one selected signal (opposing directions are blocked). `quant_system/paper_bridge.py` still calculates stake from the legacy `StrategyRules().p.entry_margin_pct` and uses `PaperLedger`'s single signed net position. These do not implement independent CORE_LEDGER/AI_LEDGER with 1% margin and no fixed position-count cap. Do not treat the legacy `PaperSignalCoordinator` / `DualPaperBridge` path as integrated with the new `dual_ledger.py` module.
5. **Signal coordinator and runtime Kill Switch wiring are not implemented.** The new risk API accepts a boolean Kill Switch state; the coordinator must supply an authoritative source.
6. **Legacy Phase 2/Phase 3 regression tests PASS but preserve legacy semantics.** Workflow run `42455156480` at SHA `8849ea2c6c9f28ac60067a7e6339eb7260a27b6b` passed 20 Phase 2 tests, 11 Phase 3 paper bridge tests, and 18 PaperLedger tests. These prove no regression in the old path; they do NOT certify compatibility with the new 1% margin, no-fixed-position-cap, independent-ledger rules.
7. **Combined CORE + AI replay and T0/T1 runtime integration have not run.**

### Legacy paper regression gate

- Workflow: T2 Legacy Paper Regression.
- Run: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42455156480
- Run ID: `42455156480`, event `push`, conclusion SUCCESS.
- Source and checked-out SHA: `8849ea2c6c9f28ac60067a7e6339eb7260a27b6b`.
- Job ID: `128652473964`.
- `quant_system.test_dual_strategy_phase2`: 20 tests PASS.
- `quant_system.test_phase3_paper_bridge`: 11 tests PASS.
- `paper_execution.test_ledger`: 18 tests PASS.
- Total: 49 tests PASS.
- No artifact produced.
- These are regression proofs for the legacy path only; that path still conflicts with the new independent-ledger risk rules described above.

## Status

- Independent CORE/AI ledger accounting: **PASS (21/21 focused tests)**.
- Atomic shared margin reservation and exactly-once consumption: **PASS**.
- Gross margin and gross notional aggregation without directional netting: **PASS**.
- Reservation cancellation/reconciliation: **PASS (focused test)**.
- Partial/full reduction accounting: **PASS (focused tests)**.
- Exact-head T2 GitHub Actions: **PASS**.
- Exact-head T0 adapter regression: **PASS**.
- R22.2 isolated offline verification for code SHA `afa44c4bbab5a86040aadbeed219df7fe10a87cb`: **PASS (8/8)**.
- Gross exposure policy threshold: **NOT DEFINED**.
- New Dual-Strategy signal coordinator integration: **NOT IMPLEMENTED**.
- Legacy Phase 2/Phase 3 regression suite: **PASS (49 tests across 3 modules) under legacy behavior**; compatibility with updated Dual-Strategy risk policy remains BLOCKED.
- Combined paper replay: **NOT RUN**.
- Production readiness: **NOT CERTIFIED**.

## Restrictions

- Keep `ai_execution_enabled=false`.
- Paper/research only; no real orders.
- Do not create/open canonical T0 DB, start Feeder, connect to exchange, or sync market data.
- Do not change T0/T1 schemas or interfaces.
- Do not merge PR #95 or any other PR without explicit user approval.

## Next step

Implement the Dual-Strategy signal coordinator and route both Core and AI signals through the persistent reservation API. Before combined paper replay, obtain the portfolio gross-exposure ceiling and confirm the margin collateral budget.
