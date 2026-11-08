# T2 Session Handoff — 2026-11-08

## Repository state

- Repository: `kenznguyen/btcusdt-telegram-signals2`.
- Active branch: `feature/dual-strategy-phase22-preholdout-attestation-20261031`.
- Latest verified code/test SHA: `afa44c4bbab5a86040aadbeed219df7fe10a87cb`.
- Latest GREEN evidence commit before this handoff update: `743fcf1ac8f32e0e04abcf70f1fac83d6daac515`.
- PR #95: OPEN / DRAFT / NOT MERGED.
- PR base: `feature/dual-strategy-phase22-frozen-reproducibility-20261031` at `b8f120fa0975225e5b7ff6243bd374cbde80b158`.
- No new branch or PR was created.
- Canonical `docs/PROJECT_SESSION_HANDOFF.md` was read on the default branch. It is absent from this active feature branch; this T2 handoff supplements it without rebasing unrelated branch history.

## Changed files

- `quant_system/dual_ledger.py` — independent ledgers, atomic shared reservations, gross exposure, cancellation/reconciliation, reduction accounting.
- `quant_system/test_dual_ledger_contract.py` — 21 focused tests.
- `.github/workflows/t2-dual-ledger-contract.yml` — existing GitHub Actions gate.
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

- Latest run for code SHA `afa44c4bbab5a86040aadbeed219df7fe10a87cb`: run ID `42454888603`.
- URL: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42454888603
- At handoff capture: IN_PROGRESS / NOT VERIFIED.
- Earlier R22.2 PASS on an older source SHA does not certify the latest reservation/reduction implementation.

## Current verdict

- Independent CORE/AI ledger accounting: PASS (21/21).
- Atomic shared margin reservation and exactly-once consumption: PASS.
- Gross margin and gross notional aggregation without directional netting: PASS.
- Reservation cancellation/reconciliation: PASS in focused tests.
- Partial/full reduction accounting: PASS in focused tests.
- Exact-head T2 CI: PASS (21/21).
- Exact-head T0 adapter regression: PASS (10/10).
- Latest R22.2: IN_PROGRESS / NOT VERIFIED.
- Gross exposure ceiling: NOT DEFINED.
- Signal coordinator integration: NOT IMPLEMENTED.
- Combined CORE + AI paper replay: NOT RUN.
- T0/T1 runtime integration: NOT RUN.
- Production readiness: NOT CERTIFIED.

## Remaining required work before combined paper use

1. Define the gross notional exposure ceiling. The engine calculates gross exposure but does not invent a threshold.
2. Confirm the portfolio margin budget. Current collateral logic prevents committed margin from exceeding supplied account equity (100% collateral guard).
3. Integrate CORE and AI signal routes through persistent `reserve_entry`/`reserve_dca` and matching reserved ledger writes.
4. Connect Kill Switch to an authoritative runtime state source.
5. Run isolated strategy backtests, then combined portfolio backtest, before paper runtime.

## Constraints

- Keep `ai_execution_enabled=false`.
- Paper/research only; no real orders.
- Do not create/open canonical T0 DB, start Feeder, connect to exchange, or sync market data.
- Do not change T0/T1 schemas or interfaces.
- Do not merge PR #95 or any other PR without explicit user approval.
- Do not rebase or retarget PR #95 without explicit approval.

## Next step

Implement the Dual-Strategy signal coordinator and route both Core and AI signals through the persistent shared-risk reservation API. Obtain the gross-exposure ceiling and confirm the margin budget before combined paper replay.
