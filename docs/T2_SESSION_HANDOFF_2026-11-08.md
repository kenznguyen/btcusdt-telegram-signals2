# T2 Session Handoff — 2026-11-08

## Repository state

- Repository: `kenznguyen/btcusdt-telegram-signals2`.
- Active branch: `feature/dual-strategy-phase22-preholdout-attestation-20261031`.
- Latest verified code/test SHA: `afa44c4bbab5a86040aadbeed219df7fe10a87cb`.
- Latest GREEN evidence commit before this handoff update: `24346c29f4186a0ac3fb1f79e506f55ff9c8649a`.
- PR #95: OPEN / DRAFT / NOT MERGED.
- PR base: `feature/dual-strategy-phase22-frozen-reproducibility-20261031` at `b8f120fa0975225e5b7ff6243bd374cbde80b158`.
- No new branch or PR was created.
- Canonical `docs/PROJECT_SESSION_HANDOFF.md` was read on the default branch. It is absent from this active feature branch; this T2 handoff supplements it without rebasing unrelated branch history.

## Changed files

- `quant_system/dual_ledger.py` — independent ledgers, atomic shared reservations, gross exposure, cancellation/reconciliation, reduction accounting.
- `quant_system/test_dual_ledger_contract.py` — 21 focused tests.
- `.github/workflows/t2-dual-ledger-contract.yml` — T2 dual-ledger gate.
- `.github/workflows/t2-legacy-paper-regression.yml` — legacy Phase 2/3 and PaperLedger regression gate.
- `quant_system/DUAL_LEDGER_RED_EVIDENCE_2026-11-08.md` — RED evidence.
- `quant_system/DUAL_LEDGER_GREEN_EVIDENCE_2026-11-08.md` — latest GREEN evidence and limits.
- `docs/T2_SESSION_HANDOFF_2026-11-08.md` — this handoff.

Working-tree status: NOT VERIFIED; GitHub Contents API commits were used and no local checkout status was inspected.

## Completed implementation

- CORE and AI have independent persisted position, DCA, equity and realized-PnL state.
- Both ledgers can share one SQLite file; writes are transactional.
- Each entry/DCA admission calculates margin as 1% of supplied account equity.
- No fixed position-count cap; shared collateral uses gross margin.
- Gross notional exposure sums both strategies without netting opposing LONG/SHORT positions.
- SQLite `BEGIN IMMEDIATE` serializes concurrent shared reservations.
- Pending reservations count against shared margin and gross exposure.
- Entry/DCA ledger updates consume a matching reservation once and cannot exceed reserved notional.
- Duplicate reservation IDs are rejected.
- Unresolved reservations can be cancelled only with explicit reconciliation evidence; cancelled IDs cannot be reused.
- Partial/full reductions atomically reduce quantity, release proportional margin, and book realized PnL/fees.
- Kill Switch blocks increases; validated reductions remain admissible.
- No exchange order path was added.

## Exact verification

### RED for reservation recovery/reduction

- Run: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42454847720
- Run ID: `42454847720`, event `push`, source SHA `1ca8aeb716b95c30f49e1a0f8aad5f4255067c6c`.
- Expected FAILURE: 21 tests ran; 4 errors because `cancel_reservation` and `record_reduction` were not implemented.

### T2 direct push — exact source SHA

- Run: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42454885138
- Run ID: `42454885138`, event `push`, conclusion SUCCESS.
- Source and checked-out SHA: `afa44c4bbab5a86040aadbeed219df7fe10a87cb`.
- Job ID: `128651680137`.
- Result: **21 tests, OK**.
- Artifact: none.

### T2 PR merge-context run

- Run: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42454888637
- Run ID: `42454888637`, event `pull_request`, conclusion SUCCESS.
- PR head SHA: `afa44c4bbab5a86040aadbeed219df7fe10a87cb`.
- Base SHA: `b8f120fa0975225e5b7ff6243bd374cbde80b158`.
- Checked-out synthetic merge SHA: `b8312df971472df2f6118641aac3b186c00f916b`.
- Job ID: `128651689985`.
- Result: **21 tests, OK**.
- This is merge-context verification; direct-head proof is the push run above.

### T0 adapter regression at exact PR head

- Run: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42454888690
- Run ID: `42454888690`, event `pull_request`, conclusion SUCCESS.
- PR head and checked-out SHA: `afa44c4bbab5a86040aadbeed219df7fe10a87cb`.
- Base SHA: `b8f120fa0975225e5b7ff6243bd374cbde80b158`.
- Result: **10 tests, OK**.
- Artifact ID: `13606719354`, name `f1-t0-freqtrade-adapter-b8312df971472df2f6118641aac3b186c00f916b`, size 942 bytes, not expired at inspection.
- GitHub upload digest: `caeb66ffe65f92fd5e1ddfe8159d8f92f5770911ffd4104db77b579344e9e914`.
- Artifact payload has not been independently downloaded and re-hashed.

### R22.2

- Run: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42454888603
- Run ID: `42454888603`, event `pull_request`, conclusion SUCCESS.
- PR head SHA at run: `afa44c4bbab5a86040aadbeed219df7fe10a87cb`.
- Base SHA: `b8f120fa0975225e5b7ff6243bd374cbde80b158`.
- Checked-out synthetic merge SHA: `b8312df971472df2f6118641aac3b186c00f916b`.
- Job ID: `128651696509`.
- Offline runtime probe: **8 tests PASS**; paper-only boundary PASS; OKX API key/secret values empty.
- Artifact ID: `13607287365`, name `r22-2-phase22-runtime-b8312df971472df2f6118641aac3b186c00f916b`, 6,993 bytes, not expired at metadata inspection.
- GitHub upload digest: `7b07fa372063b022fe14c43a8152a1adce3042e01d9f2c8a78bc5642ebae5150`.
- Artifact payload bytes have not been independently downloaded and re-hashed.

## Current verdict

- Independent CORE/AI ledger accounting: PASS (21/21).
- Atomic shared margin reservation and exactly-once consumption: PASS.
- Gross margin and gross notional aggregation without directional netting: PASS.
- Reservation cancellation/reconciliation: PASS in focused tests.
- Partial/full reduction accounting: PASS in focused tests.
- Exact-head T2 CI: PASS (21/21).
- Exact-head T0 adapter regression: PASS (10/10).
- R22.2 isolated offline runtime probe: PASS (8/8).
- Gross exposure ceiling: NOT DEFINED.
- Signal coordinator integration: NOT IMPLEMENTED.
- Combined CORE + AI paper replay: NOT RUN.
- T0/T1 runtime integration: NOT RUN.
- Production readiness: NOT CERTIFIED.

## Legacy regression evidence and critical integration finding

The old Phase 2/3 path remains regression-tested, but is not compatible with the updated Dual-Strategy rules and has not been changed:

- Legacy regression run: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42455156480
- Run ID `42455156480`, exact checked-out SHA `8849ea2c6c9f28ac60067a7e6339eb7260a27b6b`, SUCCESS.
- Phase 2 tests: 20/20 PASS; Phase 3 paper bridge tests: 11/11 PASS; PaperLedger tests: 18/18 PASS; total 49/49.
- This proves no regression in the old path, not compliance with the new risk policy.

- `quant_system/dual_strategy.py` still uses `RiskSnapshot.max_positions` and `_select` to choose one signal or block opposing CORE/AI signals.
- `quant_system/paper_bridge.py` still uses the legacy `StrategyRules().p.entry_margin_pct` sizing and `PaperLedger`'s single signed net position.
- This path does not implement independent CORE_LEDGER/AI_LEDGER, 1% margin per entry/DCA, or no fixed position-count cap.
- Do not treat `PaperSignalCoordinator` or `DualPaperBridge` as wired to the new `dual_ledger.py` shared-risk API.
- The legacy tests pass, but they assert old max-position / single-net-position behavior and do not certify the new independent-ledger policy.

## Remaining required work before combined paper use

1. Build a new signal coordinator that preserves `core_signal` / `ai_signal` provenance but emits independent CORE and AI intents; do not reuse `_select` conflict arbitration.
2. Route every entry/DCA through persistent shared reservations and matching ledger writes.
3. Replace the legacy fixed-position / 50%-margin gate in the paper path; preserve the Strategy Core RSI/ADX/Smart DCA signal rules and explicitly separate execution sizing from strategy predicates.
4. Define the gross notional exposure ceiling and confirm the portfolio margin budget (current collateral logic uses a 100% account-equity guard).
5. Connect Kill Switch to an authoritative runtime state source.
6. Run legacy regression tests, isolated strategy backtests, and combined portfolio backtest before paper runtime.

## Constraints

- Keep `ai_execution_enabled=false`.
- Paper/research only; no real orders.
- Do not create/open canonical T0 DB, start Feeder, connect to exchange, or sync market data.
- Do not change T0/T1 schemas or interfaces.
- Do not merge PR #95 or any other PR without explicit user approval.
- Do not rebase or retarget PR #95 without explicit approval.

## Next step

Implement the Dual-Strategy signal coordinator and route both Core and AI signals through the persistent shared-risk reservation API. Obtain the gross-exposure ceiling and confirm the margin budget before combined paper replay.
