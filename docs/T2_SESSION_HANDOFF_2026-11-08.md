# T2 Session Handoff — 2026-11-08

## Repository state

- Repository: `kenznguyen/btcusdt-telegram-signals2`.
- Active branch: `feature/dual-strategy-phase22-preholdout-attestation-20261031`.
- Latest verified code/test SHA: `1d3359cbcadaa9b7d2b7872ff349b32c5be98390`.
- Latest evidence-document commit before this handoff update: `a895dcdeb9725f12e7d194106d212e1bf5afe792`.
- PR #95: OPEN / DRAFT / NOT MERGED.
- PR head at code verification: `1d3359cbcadaa9b7d2b7872ff349b32c5be98390`.
- PR base: `feature/dual-strategy-phase22-frozen-reproducibility-20261031` at `b8f120fa0975225e5b7ff6243bd374cbde80b158`.
- No new branch or PR was created.
- Canonical `docs/PROJECT_SESSION_HANDOFF.md` was read on the default branch. It is absent from this active feature branch; this T2-specific handoff supplements it without rebasing unrelated branch history.

## Changed files

- `quant_system/dual_ledger.py` — isolated ledgers, persistent shared reservations, gross margin and gross notional exposure.
- `quant_system/test_dual_ledger_contract.py` — 17 focused contract tests.
- `.github/workflows/t2-dual-ledger-contract.yml` — existing GitHub Actions gate.
- `quant_system/DUAL_LEDGER_RED_EVIDENCE_2026-11-08.md` — RED evidence.
- `quant_system/DUAL_LEDGER_GREEN_EVIDENCE_2026-11-08.md` — current GREEN evidence and limitations.
- `docs/T2_SESSION_HANDOFF_2026-11-08.md` — this handoff.

Working-tree status: NOT VERIFIED; changes were committed through GitHub Contents API and no local checkout status was inspected.

## Completed implementation

- CORE and AI have separate persisted position, DCA, equity and realized-PnL state.
- Both ledgers can share a SQLite file; writes use transactions.
- Each accepted entry/DCA calculates margin as 1% of supplied account equity.
- No fixed position-count cap; margin collateral is checked against shared gross margin.
- Gross notional exposure sums absolute position notionals across both strategies; opposing LONG/SHORT positions do not net.
- Atomic persistent reservation serializes competing CORE/AI admissions with SQLite `BEGIN IMMEDIATE`.
- Pending reservation margin and notional exposure are counted before consumption.
- Entry/DCA ledger updates consume a matching reservation exactly once and reject actual notional above the reserved amount.
- Direct low-level state restoration is explicitly named `restore_position` / `restore_dca`; new strategy increases use reserved-write APIs.
- Stale data, unreconciled state, Kill Switch and insufficient collateral fail closed.
- No exchange execution path was added.

## Exact verification

### T2 direct push — exact source SHA

- Run: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42454705548
- Run ID: `42454705548`, event `push`, conclusion SUCCESS.
- Source SHA and checked-out SHA: `1d3359cbcadaa9b7d2b7872ff349b32c5be98390`.
- Job ID: `128651142263`.
- Result: **17 tests, OK**.
- Artifact: none.

### T2 pull-request merge-context run

- Run: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42454708246
- Run ID: `42454708246`, event `pull_request`, conclusion SUCCESS.
- PR head SHA: `1d3359cbcadaa9b7d2b7872ff349b32c5be98390`.
- Base SHA: `b8f120fa0975225e5b7ff6243bd374cbde80b158`.
- Checked-out synthetic merge SHA: `4fdcafafa008f1f2bfcae29134c7b56e512fde1a`.
- Job ID: `128651150310`.
- Result: **17 tests, OK**.
- This is merge-context verification, not exact-head checkout; the direct push run above proves the exact source SHA.

### T0 adapter regression at exact PR head

- Run: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42454708185
- Run ID: `42454708185`, event `pull_request`, conclusion SUCCESS.
- PR head and checked-out SHA: `1d3359cbcadaa9b7d2b7872ff349b32c5be98390`.
- Base SHA: `b8f120fa0975225e5b7ff6243bd374cbde80b158`.
- Result: **10 tests, OK**.
- Artifact ID: `13607446120`, name `f1-t0-freqtrade-adapter-4fdcafafa008f1f2bfcae29134c7b56e512fde1a`, 943 bytes, not expired at inspection.
- GitHub upload digest: `d665868f664994c9d53085f047a84e14090df3e1f38ae07645295cc7a7941c33`.
- Artifact payload has not been independently downloaded and re-hashed.

### R22.2

- Latest run for current code SHA: `42454708188`.
- URL: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42454708188
- At handoff capture: PENDING / NOT VERIFIED.
- Earlier R22.2 PASS on SHA `d4e04a701ae229c585d4598e93632831791c74d3` does not certify subsequent atomic reservation and gross exposure changes.

## Current verdict

- Ledger isolation and persistence: PASS (focused tests).
- Atomic reservation and exactly-once consumption: PASS (concurrency tests).
- Gross margin and gross notional aggregation without directional netting: PASS (focused tests).
- T2 exact-head CI: PASS (17/17).
- T0 adapter regression exact-head: PASS (10/10).
- R22.2 latest code: PENDING / NOT VERIFIED.
- Combined CORE + AI signal coordinator: NOT IMPLEMENTED.
- Combined paper replay: NOT RUN.
- T0/T1 live data integration: NOT RUN.
- Production readiness: NOT CERTIFIED.

## Remaining required work before combined paper use

1. Gross exposure ceiling has not been defined. Engine reports gross notional exposure but does not invent a maximum. Confirm the intended exposure limit.
2. Available collateral currently uses account equity minus gross recorded/pending margin, effectively capping committed margin at 100% of supplied equity. Confirm this portfolio margin budget before combined paper use.
3. Add evidence-backed cancellation/reconciliation for interrupted reservations. Until then, unresolved reservations remain fail-closed and continue holding collateral.
4. Implement atomic reduction/close accounting: reduce quantity, release proportional margin, and book realized PnL/fees.
5. Integrate CORE and AI signal routes through persistent `reserve_entry`/`reserve_dca` and the reserved ledger-write methods. No signal route has been wired yet.

## Constraints

- Keep `ai_execution_enabled=false`.
- Paper/research only; no real orders.
- Do not create/open canonical T0 DB, start Feeder, connect to exchange, or sync market data.
- Do not change T0/T1 schemas or interfaces.
- Do not merge PR #95 or any other PR without explicit user approval.
- Do not rebase or retarget PR #95 without explicit approval.

## Next step

Continue T2 with RED tests for reservation cancellation/reconciliation and reduction/close accounting. Implement those transactions, then wire both signal streams through the persistent shared-risk coordinator. Do not begin combined paper replay until the gross exposure ceiling and collateral budget are explicitly defined.
