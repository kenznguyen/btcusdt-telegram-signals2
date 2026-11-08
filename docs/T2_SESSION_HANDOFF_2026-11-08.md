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


### Evidence artifact and PR-context verification update

The workflow was hardened to include the new leverage files in both push and pull_request path filters and to upload a provenance + test-log artifact.

- Final exact-head push run: [42457686964](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42457686964), source/head/checked-out SHA `ccc182378772a25f2afb475b4070d281222d7f7f`, SUCCESS; job `128660101285` SUCCESS.
- Test logs: AI leverage 14/14; coordinator 11/11; dual ledger 23/23; Phase 2 20/20; Phase 3 11/11; PaperLedger 18/18. Total 97/97.
- Exact-head artifact: ID `13607992537`, name `t2-ai-dynamic-leverage-ccc182378772a25f2afb475b4070d281222d7f7f`, GitHub digest and independently recomputed ZIP SHA-256 both `3d2c14ea53cdf1e12633c6fbe1f2f540b052c2a6ae16bcfecae8e915f6112cce`.
- Artifact contents confirm push event, exact checked-out SHA, `AI_EXECUTION_ENABLED=false`, empty database targets and exchange credentials, and AI leverage tests 14/14 PASS.
- PR run: [42457691928](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42457691928), PR head SHA `ccc182378772a25f2afb475b4070d281222d7f7f`, synthetic merge checkout SHA `443b08f5e94c584aba75d232f6e86609a43d7ef8`, SUCCESS; same 97/97 suite totals. Do not mislabel this as direct-head evidence.
- PR-context artifact ID `13608346507`, GitHub digest `sha256:31b28ed5130b7523e25f853f02c691e32014fec857698a21472c1e5c32bf9004`.
- Latest evidence-document commit before this handoff append: `e40c66aada46859ecbc3734a514b322af80f01bf`.

Final verdict for this increment:
- Contract implementation + independent unit tests + T2 regression: PASS at exact push SHA `ccc182378772a25f2afb475b4070d281222d7f7f`.
- Exact-head artifact payload integrity: PASS (independent ZIP hash matched GitHub digest).
- PR #95: still OPEN / DRAFT / NOT MERGED. No merge or rebase.
- Working-tree status: NOT VERIFIED (no local checkout inspected).
- Real calibration quality, acceptance metrics, sample-size requirements, confidence-domain configuration, gross exposure ceiling and runtime integration remain blocked or unverified as recorded above.


## AI Calibration Evaluator — implementation increment (2026-11-08)

### Scope

Implemented a standalone offline evaluator for already-produced AI probability predictions:
- `quant_system/ai_calibration_evaluator.py`
- `quant_system/test_ai_calibration_evaluator.py`
- `quant_system/AI_CALIBRATION_EVALUATOR_2026-11-08.md`
- Updated `.github/workflows/t2-dual-signal-coordinator.yml` to compile the calibration/leverage modules and run both independent suites; upload source provenance, compile log and both test logs.

### Contract

- Equal-width ECE with explicit bin count.
- Brier score compared with a same-sample climatology/no-skill reference; strict improvement required.
- Overall metrics and separate LONG/SHORT × each explicitly declared regime.
- Every policy value is required explicitly: max ECE, minimum total samples, minimum per-group samples, bin count and regime taxonomy. No production defaults were invented.
- Fail closed for non-OOS markers, malformed labels/probabilities, unknown regimes, missing/undersized directional-regime groups, excessive ECE or Brier not better than baseline.
- Canonical ordered input rows are fingerprinted; report digest binds the input fingerprint, metrics, reasons and explicit gate policy.
- Evaluator acceptance is metric-gate acceptance only. It never issues a leverage attestation and always returns `trade_authorized=false` and `attestation_issued=false`.

### TDD and exact-source CI

RED evidence:
- Run `42457995143`, source `bd7ea4c74e9f3f0cc6ba16188a01e19b108cb22f`: expected import failure because evaluator implementation did not yet exist.
- Run `42458033277`, source `cab0d34102c7da884c820662ae5d4b5df34d1b52`: evaluator imported; first behavioral acceptance test exposed an incorrect synthetic fixture.
- Runs `42458082523` and `42458142080`: refined fixture exposed finite-sample ECE expectation mismatch; no implementation acceptance was claimed from these RED runs.

Final exact-source push:
- Run: [42458217777](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42458217777), event push, source/head/checked-out SHA `56da92b86dc75ad76e0b391854c2e672268178b1`, SUCCESS.
- Job: `128661678013`, SUCCESS.
- Logs: py_compile PASS; calibration evaluator 14/14; dynamic leverage 14/14; coordinator 11/11; dual ledger 23/23; Phase 2 20/20; Phase 3 11/11; PaperLedger 18/18 — **111/111 test invocations PASS**.
- Artifact: ID `13608870606`, name `t2-ai-intelligence-contracts-56da92b86dc75ad76e0b391854c2e672268178b1`, GitHub digest `sha256:ba6de2deb3deefdc3ab8715571a2dc167ec6b577f8d50b2c56a9ae43b16b1284`.
- Artifact ZIP downloaded; independently recomputed SHA-256 matched the GitHub digest. Payload contains source provenance, compile log, calibration evaluator log and leverage log. Calibration evaluator log confirms 14/14 PASS.
- Artifact provenance: push event, github_sha=checked_out_sha=`56da92b86dc75ad76e0b391854c2e672268178b1`, `AI_EXECUTION_ENABLED=false`, DB targets empty, exchange credentials empty.
- PR-context run: [42458221166](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42458221166), PR head SHA `56da92b86dc75ad76e0b391854c2e672268178b1`, synthetic merge checkout SHA `8033250cc6179eb23397f54ea603a38458f13a9b`, SUCCESS. This is merge-context verification, not direct-head evidence.
- Evidence report update commit: `2ba84eda4e2251a3d081bca3952da2c4d82f8d1a`.

### Limits and status

- Evaluator implementation and synthetic contract/regression CI: PASS.
- Production ECE threshold, sample counts, bin count and regime taxonomy: BLOCKED / NOT APPROVED. The values in unit fixtures are test-only and are not production recommendations.
- Real BTCUSDT OOS predictions, split manifest authenticity, temporal separation/leakage proof, frozen model/dataset provenance, artifact byte authentication, calibration uncertainty intervals and drift: NOT VERIFIED / NOT IMPLEMENTED.
- ECE/Brier passing synthetic tests does not prove real model calibration.
- No calibration attestation issued; no integration with `AIDynamicLeveragePolicy` or Coordinator.
- `AI_EXECUTION_ENABLED=false`; no DB, T0/T1, exchange, market-data or execution runtime touched.
- Gross notional exposure ceiling remains undefined.
- PR #95 remains OPEN / DRAFT / NOT MERGED; no merge/rebase.
- Current code/test/workflow verification SHA: `56da92b86dc75ad76e0b391854c2e672268178b1`.
- Branch HEAD before this state-note commit: `2937e7dc0979e1a92ce2bc7328b9dd39cb42b2ca`; this update advances the branch. The resulting commit SHA is recorded in the session response.
- Working-tree status: NOT VERIFIED (no local checkout inspected).

Next step: obtain explicit approval for production calibration gate policy (ECE maximum, Brier comparison protocol, minimum total and per LONG/SHORT × regime sample counts, bin count and regime taxonomy); then build an authenticated OOS split/data provenance validator before any attestation can be issued. Keep all runtime execution disabled.


## User-approved AI calibration gate policy — 2026-11-08

### Decision and implementation
User approved:
- Maximum ECE: `0.05`.
- Brier score must strictly beat the same-sample climatology/no-skill reference, overall and for every required directional/regime group.
- Minimum total OOS predictions: `1,000`.
- Minimum samples in each LONG/SHORT × regime group: `200`.

Implemented `approved_calibration_gate_policy(*, ece_bins, required_regimes)` in `quant_system/ai_calibration_evaluator.py`. It fixes only the approved numeric thresholds. It requires explicit caller-supplied bin count (1–100) and non-empty, unique regime names because those were not specified by the user. There are no implicit values for either. Multi-regime policies can require more than 1,000 total samples due to per-group minima.

Added tests covering the approved values, missing required arguments, invalid bin count, empty regimes and duplicate regimes.

### Scope boundaries
- This approves evaluator thresholds only; it does not attest that BTCUSDT predictions pass them.
- No actual OOS prediction dataset was evaluated.
- `out_of_sample=true` remains caller-provided and is not authenticated.
- Authenticated split/dataset/model/artifact provenance remains a separate required validator before any calibration attestation.
- No calibration attestation or leverage authorization issued.
- No integration into AI leverage, coordinator, paper bridge or runtime.
- `AI_EXECUTION_ENABLED=false`; no exchange, DB, T0/T1 or runtime touched.
- PR #95 remains OPEN / DRAFT / NOT MERGED; no merge or rebase.

### Verification state at handoff update
- Test-first change commit: `f065a71e8f5d1bb7b24f98eefddfcbd42b6f2b5c` (new tests import the not-yet-implemented policy factory).
- Implementation commit: `f4be0101380abe41b1c9d304815981d261d33e65`.
- Documentation update commit: `89e3ca65bb6003177fd7bff9bdf1bdc1fc3f5045`.
- Exact final code/test/workflow SHA and Actions run/artifact: PENDING verification; do not claim PASS until GitHub Actions completes on the exact code/test SHA.
- Working-tree status: NOT VERIFIED (GitHub API-only changes; no local checkout inspected).

Next: verify exact-head Actions for the approved policy implementation. Then implement an authenticated OOS provenance/split validator before considering any calibration attestation. Keep runtime execution disabled.


### Verification update — approved calibration gate

- Production gate factory: `approved_calibration_gate_policy(*, ece_bins, required_regimes)`.
- Code/test source commit: `f4be0101380abe41b1c9d304815981d261d33e65`.
- Test-first commit: `f065a71e8f5d1bb7b24f98eefddfcbd42b6f2b5c`; implementation follows in the code/test source commit above.
- PR-context workflow run: [42458576895](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42458576895), PR head SHA `f4be0101380abe41b1c9d304815981d261d33e65`, merge checkout `0d6c32b6d27c2bec2983937e602696ee73bb6bc4`, job `128662736759` SUCCESS.
- Follow-up PR-context workflow run: [42458607712](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42458607712), PR head SHA `55508e19617fc6cf7c0bf8c43090ae5f10b9fbdf`, merge checkout `401805e544800a0d12b72359931b75ccf6458124`, job `128662828359` SUCCESS.
- Follow-up job: py_compile PASS; evaluator 16/16; dynamic leverage 14/14; coordinator 11/11; dual ledger 23/23; legacy Phase 2 20/20; Phase 3 11/11; PaperLedger 18/18. **113/113 test invocations PASS.**
- Evidence artifact ID `13608826508`, name `t2-ai-intelligence-contracts-401805e544800a0d12b72359931b75ccf6458124`, GitHub digest `sha256:1898863091dcf09606d9d017d90e35a5366a8b763a44bc11a7173406fe68def1`.
- Artifact provenance: PR event, github/checked-out SHA `401805e544800a0d12b72359931b75ccf6458124`, `AI_EXECUTION_ENABLED=false`, database targets EMPTY, exchange credentials EMPTY.
- This is PR merge-context verification. It is not a direct push checkout of the PR head.
- Evidence/handoff commit: `55508e19617fc6cf7c0bf8c43090ae5f10b9fbdf`.
- Code and tests: PASS under PR merge-context CI. Actual BTCUSDT OOS calibration: NOT VERIFIED. Calibration attestation: NOT ISSUED.


## AI OOS provenance validator — implementation increment (2026-11-08)

### Scope and implementation
- Added `quant_system/ai_provenance_validator.py`: offline Ed25519 signed-manifest verification.
- Added `quant_system/test_ai_provenance_validator.py`: 14 synthetic contract tests.
- Added `quant_system/AI_PROVENANCE_VALIDATOR_2026-11-08.md`: schema, trust boundary, limitations and evidence.
- Added `cryptography>=44,<47` to `requirements.txt`.
- Updated `.github/workflows/t2-dual-signal-coordinator.yml` to install Ed25519 dependency, run/retain validator test log and compile both validator and test.

### Verifier contract
- Strict signed JSON envelope with canonical UTF-8 JSON manifest and Ed25519 signature.
- Trust roots are caller-supplied raw public keys indexed by key ID; no key material embedded in source.
- Manifest binds model, dataset, predictions, split protocol and calibration-report artifact SHA-256 + exact byte size.
- Rejects unknown/untrusted key, invalid signature/encoding, duplicate JSON keys, unknown manifest fields, missing/extra artifact roles, size/hash mismatch, invalid issue/expiry times, and declared train/OOS temporal overlap.
- Passing result sets `attestation_issued=false`; no trade authorization is produced.

### TDD and CI evidence
- RED test-first run [42458980940](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42458980940): expected import failure because validator module did not yet exist.
- Intermediate RED runs exposed implementation/test defects; the artifact-tamper test was corrected to change bytes without changing size so hash verification is isolated.
- Latest code commit: `9f019569b322077c9baf293d91eac6e0de600c63`.
- Latest test commit: `43f5581d564148b806bf6317cbfcdadfb45f881a`.
- Dependency commit: `60fd43510e5ada8631bf1022d1fd69948266016e`.
- Workflow commit: `784589cb71babe6992ee2baf4ce74baba8858ffd`.
- Final PR-context run [42459130878](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42459130878): PR head `784589cb71babe6992ee2baf4ce74baba8858ffd`; synthetic merge checkout `595896d2e3c27d6eda617bf8714d7466d87204f4`; job `128664429232` SUCCESS.
- Test counts: provenance 14/14; calibration evaluator 16/16; dynamic leverage 14/14; coordinator 11/11; dual ledger 23/23; Phase 2 20/20; Phase 3 11/11; PaperLedger 18/18. **127/127 total test invocations PASS**; py_compile PASS.
- Artifact ID `13608698028`, name `t2-ai-intelligence-contracts-595896d2e3c27d6eda617bf8714d7466d87204f4`, GitHub digest `sha256:a796c062ecaf39d562aae05deece36925ed74c49b9b9b85ad2929830516dffec`.
- Artifact includes provenance source, compile log and test logs. CI confirms `AI_EXECUTION_ENABLED=false`, database targets EMPTY and exchange credentials EMPTY.
- This is PR merge-context verification, not direct-push exact-head evidence.
- Evidence report commit: `d5455230535e88251a464d0cc71ab520124dc604`.

### Limits — do not overstate provenance verification
- No production trusted public key or independent signer is provisioned. Caller must load keys from an independently protected trust store; trust-store custody, rotation and revocation are not implemented.
- Temporal chronology is checked only against the signed manifest's declared timestamps. Dataset rows are not parsed to independently recompute date ranges.
- No proof yet of feature/label leakage, model training lineage, hyperparameter selection isolation, or that the exact model generated the supplied predictions.
- Calibration report bytes are hash-bound but its embedded evaluator report digest/metrics are not semantically reconciled against the prediction/outcome files.
- No real model, dataset, predictions, split protocol or calibration report were supplied.
- Calibration attestation: NOT ISSUED; leverage authorization: NOT ISSUED; runtime integration: NOT IMPLEMENTED.
- `AI_EXECUTION_ENABLED=false`; no database, T0/T1, exchange or runtime touched.
- PR #95 remains OPEN / DRAFT / NOT MERGED. No merge/rebase authorized.

Next: define and independently provision the trusted signer/key lifecycle, then extend verification to parse the actual dataset/prediction/report formats and reconcile timestamp coverage and report/input fingerprints. Only after those checks and a real OOS run can calibration attestation be considered.


## Row-level OOS prediction chronology — 2026-11-08

### Scope
- Extended `quant_system/ai_provenance_validator.py` to parse the signed `predictions` artifact as strict UTF-8 JSONL.
- Every prediction row must carry prediction timestamp, outcome-available timestamp, outcome, confidence, side, regime, model version and dataset version.
- Enforces prediction timestamp inside signed OOS interval; outcome resolution strictly after prediction and no later than OOS end; row model/dataset versions must match manifest.
- Rejects empty/malformed/blank/duplicate-key rows, invalid outcome/confidence/side/regime, and malformed temporal split before accessing split keys.
- No dataset-row parsing or market-price outcome recomputation is claimed.

### TDD and verification
- RED for malformed split: [42459595402](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42459595402), test source `b2a4ae69dbe1334f2ce36869e6c5c033253ac490`; validator test failed with the expected `KeyError: 'oos_start_ms'`.
- Fix commit: `07e8212e4723cc913e4d0a3b196212f134a8a23e`.
- Exact-source push run [42459618363](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42459618363), job `128665883617`, SUCCESS; checked-out SHA equals `07e8212e4723cc913e4d0a3b196212f134a8a23e`.
- PR-context run [42459622326](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42459622326), job `128665895716`, SUCCESS; synthetic merge checkout `1a04c7abf0464de74c534d3f4de3690f0606e1b7`.
- Test counts: provenance 23/23; calibration evaluator 16/16; dynamic leverage 14/14; coordinator 11/11; dual ledger 23/23; Phase 2 20/20; Phase 3 11/11; PaperLedger 18/18. **136/136 invocations PASS**, py_compile PASS.
- Push artifact ID `13609465168`, SHA-256 `e548da7a689ea9f0ee877d92f6baef6ffd849f08aeb4f453d2b4db1e37108b87`.
- PR artifact ID `13608987960`, SHA-256 `1ced67485be007d95bdbdd2503e5f8303b707dd5d17604e21651d1ca562104b1`.
- CI preflight records `AI_EXECUTION_ENABLED=false`, DB targets EMPTY, exchange credentials EMPTY.
- Evidence/report update commit: `645ccf1e9ac848ef5b629bf3927eeb9285b5777f`.

### Status and remaining gates
- Row-level prediction timestamp/identity checks: PASS under exact-source push and PR merge-context CI.
- Signed dataset artifact row/timestamp validation: NOT IMPLEMENTED.
- Prediction outcomes recomputed from OHLCV: NOT IMPLEMENTED.
- Calibration report metrics/input/report hash semantic reconciliation: NOT IMPLEMENTED.
- Leakage-free model training and OOS process: NOT VERIFIED.
- Production signer/trust root lifecycle: NOT CONFIGURED.
- Real BTCUSDT OOS artifacts: NOT PROVIDED.
- Calibration attestation: NOT ISSUED; AI leverage authorization: NOT ISSUED; runtime integration: NOT IMPLEMENTED.
- No T0/T1 data/runtime, DB, exchange, paper or live execution was touched. `AI_EXECUTION_ENABLED=false`.
- PR #95 remains OPEN / DRAFT / NOT MERGED.

### Next increment
Implement semantic reconciliation between the signed prediction JSONL and the signed calibration report: recompute the evaluator input fingerprint and report digest from the exact rows and explicit approved policy; reject any mismatch. Dataset row-level validation remains a separate subsequent gate.


### Session boundary snapshot — 2026-11-08 14:40 Asia/Ho_Chi_Minh

- Active repo: `kenznguyen/btcusdt-telegram-signals2`.
- Active branch: `feature/dual-strategy-phase22-preholdout-attestation-20261031`.
- Current PR head / branch HEAD: `ceee410b51a6e20572566d81c162bec702f1ae8c`.
- PR #95: OPEN / DRAFT / NOT MERGED; base `feature/dual-strategy-phase22-frozen-reproducibility-20261031`. No merge/rebase.
- Tested implementation source: `07e8212e4723cc913e4d0a3b196212f134a8a23e`.
- Evidence report commit: `645ccf1e9ac848ef5b629bf3927eeb9285b5777f`.
- This handoff update commit: `ceee410b51a6e20572566d81c162bec702f1ae8c`.
- Changed files in this increment: `quant_system/ai_provenance_validator.py`, `quant_system/test_ai_provenance_validator.py`, `quant_system/AI_PROVENANCE_VALIDATOR_2026-11-08.md`, `docs/T2_SESSION_HANDOFF_2026-11-08.md`; PR description updated.
- Working-tree status: NOT VERIFIED (GitHub API updates only; no local checkout inspected).
- Exact-source push CI [42459618363](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42459618363) SUCCESS; artifact `13609465168`, digest `sha256:e548da7a689ea9f0ee877d92f6baef6ffd849f08aeb4f453d2b4db1e37108b87`.
- PR merge-context CI [42459622326](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42459622326) SUCCESS; synthetic merge checkout `1a04c7abf0464de74c534d3f4de3690f0606e1b7`; artifact `13608987960`, digest `sha256:1ced67485be007d95bdbdd2503e5f8303b707dd5d17604e21651d1ca562104b1`.
- Total: 136/136 test invocations PASS; py_compile PASS. RED evidence for malformed split is run `42459595402`.
- `docs/PROJECT_SESSION_HANDOFF.md` was read from the repository default branch. It is not present on this T2 feature branch or its base branch; the T2-specific handoff remains the active branch record.
- Hard limits remain: `AI_EXECUTION_ENABLED=false`; no live orders, no paper runtime integration, no T0/T1 DB/Feeder/exchange activity, no actual OOS artifacts, no calibration attestation, no leverage authorization.
- Next permitted increment: semantic reconciliation of prediction JSONL with calibration evaluator report and explicit approved gate policy. Do not activate runtime or issue attestation based on synthetic tests.


## Calibration report semantic reconciliation — 2026-11-08

### Scope and contract
- `quant_system/ai_provenance_validator.py` now parses the signed calibration report as strict UTF-8 JSON; duplicate keys and non-finite JSON values fail closed.
- Requires explicit approved policy: ECE <= 0.05; at least 1,000 total OOS rows; at least 200 rows for each LONG/SHORT x declared regime; explicit `ece_bins` in [1,100] and explicit unique regime taxonomy.
- Reconstructs `CalibrationObservation` values from the exact signed prediction JSONL and calls the existing `CalibrationEvaluator`.
- Compares the full report object including accepted/reasons, sample and group counts, all metrics, input fingerprint, report digest, exact policy, and `trade_authorized=false` / `attestation_issued=false`.
- Mismatch, malformed report, or weakened policy rejects provenance verification.

### TDD and CI evidence
- RED: [42459991105](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42459991105), source `ae46e708d05a91e11c1a0d7b0e8476ce60c1c901`; four new semantic mismatch tests failed before implementation.
- GREEN exact source SHA: `b2623527add57002e8b32123c67f4484c88d0efa`.
- Exact-source push run [42460071397](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42460071397), job `128667260783`, SUCCESS; checked-out SHA equals source SHA.
- Tests: provenance 28/28; calibration evaluator 16/16; dynamic leverage 14/14; coordinator 11/11; dual ledger 23/23; Phase 2 20/20; Phase 3 11/11; PaperLedger 18/18. **141/141 test invocations PASS**; py_compile PASS.
- Artifact ID `13609103523`; digest `sha256:483a1d4952d7f578c7e4063d05d6efadfa4e1190937985fccc37a47cfe059062`.
- CI preflight: `AI_EXECUTION_ENABLED=false`, DB targets EMPTY, exchange credentials EMPTY.

### Status and limits
- Prediction JSONL ↔ calibration report semantic consistency: PASS on synthetic fixture.
- Actual BTCUSDT OOS report: NOT PROVIDED.
- Dataset candle rows/timestamps: NOT PARSED.
- Outcomes recomputed from OHLCV: NOT IMPLEMENTED.
- Feature/label leakage and model-to-prediction lineage: NOT VERIFIED.
- Production trust root/signer lifecycle: NOT CONFIGURED.
- Calibration attestation and AI leverage authorization: NOT ISSUED.
- Runtime integration: NOT IMPLEMENTED.
- No T0/T1 runtime, database, exchange, paper or live execution touched.
- PR #95 remains OPEN / DRAFT / NOT MERGED; no merge/rebase.

### Exact branch state at handoff update
- Active branch: `feature/dual-strategy-phase22-preholdout-attestation-20261031`.
- Implementation source SHA tested: `b2623527add57002e8b32123c67f4484c88d0efa`.
- Provenance report update commit: `b4b8f5b9d6b082588dc9b889e1f183bab3953a1c`.
- This handoff commit will be the branch HEAD after this documentation update.
- Working tree: NOT VERIFIED (GitHub API updates only).
- Next increment: define and validate a canonical dataset artifact row schema and independently reconcile candle timestamps/coverage to prediction timestamps and outcome-resolution windows. Do not recompute trade outcomes or issue attestation until market-data semantics, price basis, candle close-time convention and label horizon are explicit.
