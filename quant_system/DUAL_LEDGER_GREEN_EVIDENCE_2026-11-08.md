# T2 Dual Ledger GREEN Evidence — 2026-11-08

## Scope

Paper-only Dual-Strategy accounting and shared-risk slices implemented. The approved margin basis is now **combined portfolio equity = CORE ledger equity + AI ledger equity**. Each entry/DCA reserves 1% of that combined value at admission; independent ledger equity/PnL accounting remains separate.

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
- Current code/test head at evidence capture: `9492b8bc5a2d3da45a3662dc4eba7ece28fe7c7c`.
- Portfolio-equity policy implementation commit: `9d3ef163868c99a2438bfaa4b9c98e3a9954ef4c`.
- Final focused-test correction commit: `9492b8bc5a2d3da45a3662dc4eba7ece28fe7c7c`.
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

## Combined portfolio equity decision and verification

The user selected **combined portfolio equity** as the 1% margin basis.

Implementation contract:
- `portfolio_equity = CORE.snapshot().equity + AI.snapshot().equity`.
- Every admitted entry/DCA requires margin = `portfolio_equity * 0.01`.
- Independent CORE and AI equity/PnL ledgers remain separate; only the shared risk budget uses their sum.
- Stateless admission rejects a caller-supplied equity value that differs from the sum of the two snapshots with `ACCOUNT_EQUITY_MISMATCH`.
- Persistent reservation reads both stored strategy account balances inside the same `BEGIN IMMEDIATE` transaction and rejects a caller-supplied mismatch. The authoritative combined value determines required margin.
- The combined equity is recalculated at every admission, so realized PnL in either ledger changes subsequent admission sizing.

### RED → GREEN

- RED test commit: `d2c651927fc1e11ac1667309b87e147437513ddc`.
- RED run: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42455448910
- Run ID `42455448910`, source SHA `d2c651927fc1e11ac1667309b87e147437513ddc`, expected FAILURE: 23 tests ran; 5 failures exposed caller-supplied single-ledger equity and stale 1% sizing.
- GREEN code commit: `9d3ef163868c99a2438bfaa4b9c98e3a9954ef4c`.
- Final GREEN source SHA: `9492b8bc5a2d3da45a3662dc4eba7ece28fe7c7c`.
- T2 run: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42455568974
- Run ID `42455568974`, event `push`, exact source SHA `9492b8bc5a2d3da45a3662dc4eba7ece28fe7c7c`, SUCCESS; 23 tests PASS.
- Legacy regression run: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42455568882
- Run ID `42455568882`, same exact source SHA, SUCCESS; Phase 2 20/20, Phase 3 11/11, PaperLedger 18/18 (49/49 total).
- No artifacts produced by these two push workflows.

## Test coverage — 23/23

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

## Dual-Strategy coordinator RED → GREEN

- Contract tests: `quant_system/test_dual_signal_coordinator.py` (8 tests).
- RED test commit: `a4596369ff98f836745e115b6ce44360d84301a2`.
- RED workflow run: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42455777252
- RED run ID `42455777252`, source SHA `c0c793689b06abe3f7261f618652b0e7e535d54b`, expected failure because `quant_system.dual_signal_coordinator` did not exist. The loader ran one failed import test; the eight behavioral methods did not execute.
- Coordinator implementation commit: `78bf5b8b8b620dde7bd6f093ad197db4a9b22219`.
- Final coordinator workflow commit: `34c6b41246b5eb580f7d6085c62e25b7a35c3160`.
- Exact source SHA and PR head for the final verification: `34c6b41246b5eb580f7d6085c62e25b7a35c3160`.
- GREEN workflow: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42455858929
- Run ID `42455858929`, event `push`, conclusion SUCCESS; job `128654599899`.
- Focused coordinator: 8/8 PASS.
- Shared ledger contract: 23/23 PASS.
- Legacy Phase 2: 20/20 PASS; Phase 3: 11/11 PASS; PaperLedger: 18/18 PASS.
- Total: **70 tests PASS** on the exact source SHA.
- Offline boundary passed: `AI_EXECUTION_ENABLED=false`; DB targets and Binance/OKX credentials empty.
- No artifact produced.
- Coordinator accepts separately produced CORE and AI intents, preserves opposing directions, uses combined portfolio equity for each 1% admission, persists each entry/DCA reservation, and writes only to its matching ledger. It does not submit exchange orders.

## Review findings and remaining boundaries

This is a passing ledger/risk-accounting slice, **not full Dual-Strategy execution certification**.

1. **Gross exposure ceiling is not defined.** Engine calculates and reports gross notional exposure but does not invent a maximum. Set the intended gross exposure limit before combined paper use.
2. **Equity basis is confirmed; portfolio budget remains conservative.** The 1% margin basis is combined portfolio equity (CORE + AI). Available collateral is combined equity minus gross recorded/pending margin, so committed margin cannot exceed 100% of combined equity. A separate gross-notional exposure ceiling is still undefined.
3. **AI sizing/leverage is not defined.** The new risk API receives an explicit notional exposure from its caller, but no AI position-sizing/leverage policy has been approved. Do not infer AI leverage from the legacy Core 13x setting.
4. **Coordinator exists as an offline integration slice; live paper bridge wiring is not implemented.** `quant_system/dual_signal_coordinator.py` accepts independent CORE/AI ENTRY and DCA intents, routes each through persistent shared reservations, and writes only to the originating ledger. It does not yet call the signal producers itself or connect to `paper_bridge.py` / the Freqtrade runtime. The `restore_position`/`restore_dca` methods remain for reconciled restore only.
5. **Legacy signal/paper route is incompatible and remains unchanged.** `quant_system/dual_strategy.py` still routes through `RiskSnapshot.max_positions`, and `_select` arbitrates CORE/AI into one selected signal (opposing directions are blocked). `quant_system/paper_bridge.py` still calculates stake from the legacy `StrategyRules().p.entry_margin_pct` and uses `PaperLedger`'s single signed net position. These do not implement independent CORE_LEDGER/AI_LEDGER with 1% margin and no fixed position-count cap. Do not treat the legacy `PaperSignalCoordinator` / `DualPaperBridge` path as integrated with the new `dual_ledger.py` module.
6. **Signal coordinator and runtime Kill Switch wiring are not implemented.** The new risk API accepts a boolean Kill Switch state; the coordinator must supply an authoritative source.
7. **Legacy Phase 2/Phase 3 regression tests PASS but preserve legacy semantics.** Workflow run `42455156480` at SHA `8849ea2c6c9f28ac60067a7e6339eb7260a27b6b` passed 20 Phase 2 tests, 11 Phase 3 paper bridge tests, and 18 PaperLedger tests. These prove no regression in the old path; they do NOT certify compatibility with the new 1% margin, no-fixed-position-cap, independent-ledger rules.
8. **Combined CORE + AI replay and T0/T1 runtime integration have not run.**

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

- Independent CORE/AI ledger accounting and combined-equity risk sizing: **PASS (23/23 focused tests)**.
- Atomic shared margin reservation and exactly-once consumption: **PASS; 1% basis is combined CORE + AI equity**.
- Gross margin and gross notional aggregation without directional netting: **PASS**.
- Reservation cancellation/reconciliation: **PASS (focused test)**.
- Partial/full reduction accounting: **PASS (focused tests)**.
- Exact-head T2 GitHub Actions: **PASS**.
- Exact-head T0 adapter regression: **PASS**.
- R22.2 isolated offline verification for code SHA `afa44c4bbab5a86040aadbeed219df7fe10a87cb`: **PASS (8/8)**.
- Gross exposure policy threshold: **NOT DEFINED**.
- New offline Dual-Strategy coordinator: **PASS (8/8)**; paper bridge/runtime wiring: **NOT IMPLEMENTED**.
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

Wire the offline coordinator to the independently validated CORE/AI signal producers and a paper-only execution adapter without reusing legacy `_select` arbitration or `PaperLedger` netting. Before combined paper replay, define the gross-notional exposure ceiling, AI sizing/leverage, and authoritative Kill Switch source.
