# T2 Session Handoff — 2026-11-08

## Repository state

- Repository: `kenznguyen/btcusdt-telegram-signals2`.
- Active branch: `feature/dual-strategy-phase22-preholdout-attestation-20261031`.
- Latest verified code/test SHA: `7d2b73bfbe6d588c57257e93193806f7d942dbb9`.
- Latest GREEN evidence commit before this handoff update: `99951a4d863938909ea2d682d63911ba0ddb4625`.
- PR #95: OPEN / DRAFT / NOT MERGED.
- PR base: `feature/dual-strategy-phase22-frozen-reproducibility-20261031` at `b8f120fa0975225e5b7ff6243bd374cbde80b158`.
- No new branch or PR was created.
- Canonical `docs/PROJECT_SESSION_HANDOFF.md` was read on the default branch. It is absent from this active feature branch; this T2 handoff supplements it without rebasing unrelated branch history.

## Changed files

- `quant_system/dual_ledger.py` — independent ledgers, atomic shared reservations, gross exposure, cancellation/reconciliation, reduction accounting.
- `quant_system/dual_signal_coordinator.py` — independent CORE/AI ENTRY/DCA intent routing through the shared risk reservations; paper-only, no exchange orders.
- `quant_system/test_dual_signal_coordinator.py` — 11 coordinator contract tests, including independent candidate generation.
- `.github/workflows/t2-dual-signal-coordinator.yml` — offline coordinator, dual-ledger and legacy regression gate.
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
- Each entry/DCA admission calculates margin as 1% of combined portfolio equity (CORE ledger equity + AI ledger equity). The separate ledgers retain independent equity/PnL accounting; combined equity is used only for shared-risk admission. Caller-supplied equity must match the authoritative sum, otherwise admission fails closed with `ACCOUNT_EQUITY_MISMATCH`.
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

## Combined portfolio equity decision

The user selected combined portfolio equity as the 1% margin basis. The implementation reads both ledger balances and recalculates the total at every admission. A realized PnL/fee update in either ledger therefore affects the next shared-risk admission without merging the two ledger books.

## Exact verification

### Combined portfolio equity RED → GREEN

- RED run: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42455448910 — run ID `42455448910`, source SHA `d2c651927fc1e11ac1667309b87e147437513ddc`, expected failure; 23 tests ran and 5 failures exposed incorrect single-ledger equity assumptions.
- GREEN run: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42455568974 — run ID `42455568974`, exact source SHA `9492b8bc5a2d3da45a3662dc4eba7ece28fe7c7c`, SUCCESS; 23/23 tests PASS.
- Legacy regression run: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42455568882 — same exact source SHA, SUCCESS; 20 + 11 + 18 = 49 tests PASS.
- No artifacts produced by these push workflows.

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

## Dual-Strategy coordinator increment

- Coordinator contract RED run: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42455777252 — run ID `42455777252`, source SHA `c0c793689b06abe3f7261f618652b0e7e535d54b`; expected import failure because module did not exist. Only the unittest loader error ran; no behavioral methods executed.
- Implementation commit: `78bf5b8b8b620dde7bd6f093ad197db4a9b22219`.
- Final exact tested code/test SHA and PR head: `7d2b73bfbe6d588c57257e93193806f7d942dbb9`.
- GREEN run: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42455858929 — run ID `42455858929`, push event, SUCCESS; job `128654599899`.
- Tests on exact source: coordinator 11/11, dual-ledger 23/23, legacy Phase 2 20/20, Phase 3 11/11, PaperLedger 18/18; **83/83 total PASS**.
- T0 → Freqtrade adapter regression: 10/10 PASS.
- Direct-push workflow run `42456099914`: SUCCESS, exact SHA `7d2b73bfbe6d588c57257e93193806f7d942dbb9`.
- PR coordinator run `42456177935`: SUCCESS, exact PR code head `7d2b73bfbe6d588c57257e93193806f7d942dbb9`, 83 tests PASS.
- PR dual-ledger run `42456178029`: SUCCESS, 23/23.
- PR legacy regression run `42456177941`: SUCCESS, 49/49.
- PR T0 adapter run `42456177970`: SUCCESS, 10/10.
- A later documentation-only PR head (`bddf1ce751502640d0676683e3018de26afb8e5c`) triggered R22.2; that verification was IN_PROGRESS at handoff capture.
- Offline preflight: `AI_EXECUTION_ENABLED=false`; database targets and Binance/OKX credentials empty. No artifact produced.
- `generate_signals()` reuses the existing closed-candle `core_signal()` RSI/ADX/H1 logic and validated `ai_signal()` FreqAI provenance checks, but returns both candidates independently. Tests prove opposing CORE LONG / AI SHORT are both preserved, AI can signal when CORE is silent, and invalid AI provenance does not suppress a valid CORE signal.
- Opposing CORE LONG and AI SHORT intents are admitted independently when shared risk permits; each position is persisted to its own ledger. ENTRY/DCA use combined portfolio equity and 1% shared reservations. DCA side mismatch is rejected. Kill Switch blocks increases while reductions remain available.
- This is an offline coordinator slice only. It does not yet call `core_signal` / `ai_signal` itself or connect to the legacy `paper_bridge.py` / Freqtrade runtime.

## Current verdict

- Independent CORE/AI ledger accounting and combined-equity sizing: PASS (23/23).
- Atomic shared margin reservation and exactly-once consumption: PASS; 1% basis is combined portfolio equity.
- Gross margin and gross notional aggregation without directional netting: PASS.
- Reservation cancellation/reconciliation: PASS in focused tests.
- Partial/full reduction accounting: PASS in focused tests.
- Exact-head T2 CI: PASS (21/21).
- Exact-head T0 adapter regression: PASS (10/10).
- R22.2 isolated offline runtime probe: PASS (8/8).
- Gross exposure ceiling: NOT DEFINED.
- Offline independent signal coordinator and dual-source candidate generation: PASS (11/11); runtime/paper-bridge integration: NOT IMPLEMENTED.
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

1. Connect the coordinator to `core_signal` and validated `ai_signal` producers while preserving provenance; do not reuse `_select` conflict arbitration.
2. Add a paper-only adapter that feeds explicit order sizing into the coordinator and persists matching ledger writes; do not use legacy `PaperLedger` netting.
3. Replace the legacy fixed-position / 50%-margin gate in the paper path; preserve Strategy Core RSI/ADX/Smart DCA signal rules and separate execution sizing from strategy predicates.
4. Combined portfolio equity is CONFIRMED as the 1% margin basis; preserve independent ledger equity accounting.
5. Define the gross notional exposure ceiling and confirm the portfolio margin budget (current collateral logic uses a 100% account-equity collateral guard).
6. Define AI leverage/position sizing; do not assume Core's legacy 13x leverage applies to AI.
7. Connect Kill Switch to an authoritative runtime state source.
8. Run legacy regression tests, isolated strategy backtests, and combined portfolio backtest before paper runtime.

## Constraints

- Keep `ai_execution_enabled=false`.
- Paper/research only; no real orders.
- Do not create/open canonical T0 DB, start Feeder, connect to exchange, or sync market data.
- Do not change T0/T1 schemas or interfaces.
- Do not merge PR #95 or any other PR without explicit user approval.
- Do not rebase or retarget PR #95 without explicit approval.

## Next step

Define AI sizing/leverage, gross-notional exposure ceiling, and authoritative Kill Switch source. Then connect generated candidates to a paper-only execution adapter that accepts explicit sizing, preserves independent ledgers, and never uses legacy `_select` or `PaperLedger` netting. Follow with isolated CORE/AI backtests and combined portfolio replay. No paper runtime yet.


## AI dynamic leverage decision — 2026-11-08

User decision:

- AI leverage is dynamic and must vary according to the model's calibrated confidence.
- AI leverage must have explicit configured `min_leverage` and `max_leverage` bounds.
- AI leverage requires a separate validation/acceptance gate; Strategy Core leverage or Core validation evidence must not be reused as a substitute.
- AI leverage is independent of the legacy Core 13x setting. No Core leverage default may leak into the AI path.
- Any missing/invalid bounds, unvalidated calibration artifact, invalid/out-of-domain confidence, or calculated leverage outside the configured interval must fail closed and reject AI ENTRY/DCA.
- A leverage decision may only affect AI order sizing/gross exposure. Every resulting intent remains subject to the shared risk engine, combined-equity 1% margin reservation, gross exposure accounting, Kill Switch and reconciliation gates.
- `AI_EXECUTION_ENABLED=false`; this decision does not authorize live execution or paper-runtime activation.

Not yet specified by the user and therefore deliberately NOT defaulted:

1. Numeric `min_leverage` and `max_leverage` values.
2. The confidence-to-leverage mapping function (for example, linear interpolation versus a calibrated lookup/policy curve).
3. Calibration acceptance thresholds and minimum validation sample size (e.g. ECE/Brier limits, coverage, regime slices).
4. Whether leverage is recalculated only on new signal admission or also on subsequent DCA admissions; any recalculation must not retroactively change existing position leverage.

Implementation gate: build a sizing-agnostic AI leverage policy contract with explicit required configuration and fail-closed validation only after mapping and calibration acceptance criteria are specified. Do not infer numerical limits or claim calibration validity from model confidence alone.

Status: POLICY DIRECTION CONFIRMED; NUMERIC BOUNDS / MAPPING / CALIBRATION ACCEPTANCE CRITERIA BLOCKED ON USER SPECIFICATION. No code, runtime, T0 or T1 behavior changed in this increment.


## AI Dynamic Leverage Contract — implementation increment (2026-11-08)

User-approved policy:
- `min_leverage=1x`, `max_leverage=3x`, `mapping=linear`.
- AI does not inherit Strategy Core's legacy leverage.
- Confidence-domain endpoints are required configuration and are intentionally not defaulted from the unapproved 0.60/0.90 proposal.
- AI calibration acceptance metrics and minimum sample-size criteria remain unspecified; do not claim a real model calibration has passed.

Implementation:
- `quant_system/ai_dynamic_leverage.py`: standalone Decimal-based policy contract; fixed 1x–3x bounds; linear mapping; explicit confidence domain; calibration attestation identity/provenance/time checks; fail-closed rejection.
- `quant_system/test_ai_dynamic_leverage.py`: independent tests for mapping boundaries, invalid confidence, invalid bounds, calibration rejection, OOS/leakage flags, provenance hash/type and identity mismatch, future/expired evidence, and no Core leverage fallback.
- `.github/workflows/t2-dual-signal-coordinator.yml`: runs the independent AI leverage contract suite before existing coordinator/ledger/legacy regressions.
- `quant_system/AI_DYNAMIC_LEVERAGE_CONTRACT_2026-11-08.md`: scope and evidence limits.

TDD evidence:
- RED run `42457533430`, source SHA `004eaf3c0870f11692174c27669c5bd4021275b9`: leverage suite failed as expected on a dataset-provenance mismatch (13 passed, 1 failed).
- GREEN run `42457536254`, source SHA `685abd9cf214566e2c653af4b04171e1c42241b5`: 14/14 AI leverage tests PASS; coordinator, dual-ledger and legacy regression steps PASS; no artifacts.
- Fixed-bound run `42457578245`, source SHA `617ceea8e9669b701dbeae36acae16666b769970`: workflow SUCCESS.
- Additional hardening rejects non-string provenance fingerprints safely. Latest code/test source SHA: `6bb1ecd899e9857dfef80635c4d53a745f7c2662`; exact-source workflow run is pending at handoff capture. Do not promote the latest SHA to PASS until run/job logs confirm it.
- Latest documentation commit before this handoff update: `fb1d439bbd3520bc025a593bc5724e42faf435f3`.

Current status:
- Linear leverage contract and 1x–3x bounds: IMPLEMENTED.
- Confidence floor/ceiling: CONFIGURATION REQUIRED; no production defaults.
- Calibration evaluator, acceptance metrics and minimum OOS sample size: BLOCKED / NOT IMPLEMENTED.
- Calibration artifact authenticity and actual model quality: NOT VERIFIED.
- Coordinator/paper runtime integration: NOT IMPLEMENTED; `AI_EXECUTION_ENABLED=false`.
- Gross notional exposure ceiling: still undefined.
- No T0/T1, database, Feeder, exchange, market data, or live-order behavior changed.
- PR #95 remains OPEN / DRAFT / NOT MERGED. No merge or rebase authorized.

Next step: verify exact-source CI for `6bb1ecd899e9857dfef80635c4d53a745f7c2662`, then continue with an independent calibration-evidence evaluator only after acceptance thresholds and sample-size rules are specified. Keep runtime disabled.


### Final exact-head CI update — AI Dynamic Leverage

The pending verification recorded above is now resolved:
- Exact code/test source SHA: `6bb1ecd899e9857dfef80635c4d53a745f7c2662`.
- GitHub Actions run: [42457596650](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42457596650), push event, conclusion SUCCESS.
- Job: `128659833226`, conclusion SUCCESS.
- Exact-source test results from job logs: AI dynamic leverage 14/14; coordinator 11/11; dual-ledger 23/23; legacy Phase 2 20/20; Phase 3 11/11; PaperLedger 18/18. Total: 97/97 test invocations PASS.
- Preflight: `AI_EXECUTION_ENABLED=false`; database targets empty; Binance and OKX credentials empty.
- Artifacts: none.
- Documentation evidence update commit: `7ea94d96ad812cf923a59662264d54c775037872`.
- Current active branch head after this handoff update will be the resulting documentation commit; code/test evidence remains tied to the exact SHA above.

Status correction:
- AI dynamic leverage contract and the final exact-source contract/regression CI: PASS.
- This is not evidence that a real calibration has passed. Confidence-domain endpoints, calibration metrics/acceptance thresholds, minimum OOS sample size, calibration artifact authenticity and directional/regime coverage remain BLOCKED / NOT VERIFIED.
- No coordinator or paper runtime integration occurred. No paper or live orders were enabled.
