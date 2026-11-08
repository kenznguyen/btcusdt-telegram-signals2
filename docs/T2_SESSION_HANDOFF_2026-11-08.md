# T2 Session Handoff — 2026-11-08

## Repository state

- Repository: `kenznguyen/btcusdt-telegram-signals2`.
- Active branch: `feature/dual-strategy-phase22-preholdout-attestation-20261031`.
- Latest branch HEAD at handoff publication: `581fc72d6bab1441bf052e526f4b59793f61c441` (R22.2 evidence update).
- Latest implementation/test source SHA: `d4e04a701ae229c585d4598e93632831791c74d3`.
- Implementation source commit: `d4e5d05070e18478f9bfc7927d881e3658f7affe`.
- PR #95: OPEN / DRAFT / NOT MERGED.
- PR base: `feature/dual-strategy-phase22-frozen-reproducibility-20261031` at `b8f120fa0975225e5b7ff6243bd374cbde80b158`.
- No new branch or PR was created.
- The canonical `docs/PROJECT_SESSION_HANDOFF.md` exists on the repository default branch but was not present on this active feature branch. This T2-specific handoff supplements it without rebasing or merging unrelated branch history.

## Changed files in this workstream

- `quant_system/test_dual_ledger_contract.py` — 11 contract tests.
- `.github/workflows/t2-dual-ledger-contract.yml` — GitHub Actions gate, unchanged in GREEN increment.
- `quant_system/dual_ledger.py` — initial independent ledger and shared risk admission implementation.
- `quant_system/DUAL_LEDGER_RED_EVIDENCE_2026-11-08.md` — original RED evidence.
- `quant_system/DUAL_LEDGER_GREEN_EVIDENCE_2026-11-08.md` — GREEN evidence, test and review boundaries; updated after R22.2 completed SUCCESS.
- `docs/T2_SESSION_HANDOFF_2026-11-08.md` — this handoff.

Working-tree status: GitHub contents API commits were used; local working-tree status was not inspected and is therefore NOT VERIFIED.

## Completed work and exact evidence

### T2 Dual Ledger Contract

- Direct push run: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42454140520
  - Run ID: `42454140520`, event `push`, conclusion SUCCESS.
  - PR/code source SHA and checked-out SHA: `d4e04a701ae229c585d4598e93632831791c74d3`.
  - Job ID: `128649446306`.
  - Tests: 11/11 PASS.
  - Artifact: none.
- PR run: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42454144922
  - Run ID: `42454144922`, event `pull_request`, conclusion SUCCESS.
  - PR head SHA: `d4e04a701ae229c585d4598e93632831791c74d3`.
  - Base SHA: `b8f120fa0975225e5b7ff6243bd374cbde80b158`.
  - Checked-out synthetic merge SHA: `41a059bdc40c74c5c5b028ef78de3d7e8068935e`.
  - Job ID: `128649460255`.
  - Tests: 11/11 PASS.
  - This is merge-context verification, not exact-head checkout; exact-head proof is the direct push run above.

### T0 adapter regression

- Run: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42454144881
- Run ID: `42454144881`, event `pull_request`, conclusion SUCCESS.
- PR head and checked-out SHA: `d4e04a701ae229c585d4598e93632831791c74d3`.
- Base SHA: `b8f120fa0975225e5b7ff6243bd374cbde80b158`.
- Tests: 10/10 PASS.
- Artifact ID: `13606424039`, name `f1-t0-freqtrade-adapter-41a059bdc40c74c5c5b028ef78de3d7e8068935e`, size 943 bytes, not expired at inspection.
- GitHub upload digest: `7cff01c719d5a6f87396da40bb6ce6fd8cd6ff255d5b27289f15e61146707711`.
- Artifact payload bytes have not been independently downloaded and re-hashed.

### R22.2 isolated Phase 22 verification

- Run: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42454144968
- Run ID: `42454144968`, event `pull_request`, conclusion SUCCESS.
- PR head SHA: `d4e04a701ae229c585d4598e93632831791c74d3`.
- Base SHA: `b8f120fa0975225e5b7ff6243bd374cbde80b158`.
- Checked-out synthetic merge SHA: `41a059bdc40c74c5c5b028ef78de3d7e8068935e`.
- Job ID: `128649460777`.
- Offline runtime probe: 8 tests PASS.
- Paper-only boundary passed; OKX API key/secret environment values were empty; no exchange execution.
- Artifact ID: `13607047149`, name `r22-2-phase22-runtime-41a059bdc40c74c5c5b028ef78de3d7e8068935e`, size 7,026 bytes, not expired at inspection.
- GitHub upload SHA-256 digest: `efcf2bade58264d6e257509998962b13b17f35bc45a6ebab76058740772f170b`.
- Artifact payload bytes have not been independently downloaded and re-hashed.

## Current technical verdict

- Independent CORE/AI ledger storage contract: PASS (11/11).
- Per-ledger position, DCA, equity and realized-PnL isolation: PASS in focused tests.
- Shared gross-margin sum and 1% admission calculation: PASS in focused tests.
- Kill Switch entry/DCA rejection and reduction-intent acceptance: PASS in focused tests.
- Exact-head direct-push T2 verification: PASS.
- T0 adapter regression at exact PR head: PASS.
- R22.2 isolated offline probe: PASS.
- Full atomic shared-risk admission: BLOCKED / NOT IMPLEMENTED.
- Combined CORE + AI portfolio replay: NOT RUN.
- T0/T1 live data integration: NOT RUN.
- Production readiness: NOT CERTIFIED.

## Code-review findings — must address before combined paper use

1. SharedRiskEngine admission methods are read-only. They do not atomically reserve collateral. Concurrent CORE and AI admissions can inspect the same snapshots. Add a shared transactional reservation/fencing boundary.
2. Ledger `record_entry` and `record_dca` accept writes without consuming a current accepted RiskDecision. The coordinator must bind every increase to a valid, single-use reservation.
3. Current available-collateral calculation is supplied account equity minus gross recorded margin, effectively preventing recorded margin from exceeding 100% of that equity. This is provisional collateral behavior, not an approved total-risk ceiling. Confirm the intended portfolio margin budget before combined paper testing.
4. Reduction admission is implemented, but reduction/close ledger accounting transitions are not yet implemented.

## Constraints

- `ai_execution_enabled=false`.
- Paper/research only. No real orders.
- Do not create/open canonical T0 database, start Feeder, connect to exchange, or sync market data.
- Do not change T0/T1 schema or interfaces.
- Do not merge PR #95 or any other PR without explicit user approval.
- Do not rebase or retarget PR #95 without explicit scope approval.

## Next step

Start T2 GREEN 2 using TDD:
1. Write RED tests for concurrent CORE/AI admissions against one shared collateral budget.
2. Test duplicate reservation rejection and exactly-once reservation consumption.
3. Test that ledger entry/DCA writes cannot bypass the risk reservation.
4. Add reduction/close accounting tests.
5. Implement the smallest transactional shared coordinator and rerun exact-head GitHub Actions plus existing regressions.

Do not start combined paper replay until the atomicity and policy-budget questions above are resolved.
