# Core-First Release Readiness and Dual-Strategy Phased Plan

Date: 2026-11-12 (Asia/Ho_Chi_Minh)
Repository: `kenznguyen/btcusdt-telegram-signals2`
Active branch: `feature/core-operational-proof-20261112`
Baseline source SHA: `755b6c4b783e873c5c9b023e4a4c0d8271a7748b`

## 1. Executive disposition

- Core code-level paper gate: **PASS**.
- Core-first paper release: **CONDITIONAL / PACKAGEABLE AS A PAPER-ONLY RELEASE CANDIDATE**.
- Production or live trading release: **BLOCKED**.
- AI Strategy execution: **OFFLINE / NOT AUTHORIZED**.
- No VPS/persistent runtime, canonical T0, T1/T2 runtime, exchange credentials, or real orders are authorized by this report.

This disposition is deliberately narrower than production readiness. The passing tests use disposable isolated SQLite fixtures and do not prove continuous runtime, host/power-loss recovery, filesystem fault tolerance, multi-host SQLite, real-market out-of-sample performance, or AI/Core execution contention.

## 2. Core-first evidence baseline

GitHub Actions run: https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/43232993104

- Event: `push`
- Branch: `feature/core-operational-proof-20261112`
- Exact checked-out source SHA: `755b6c4b783e873c5c9b023e4a4c0d8271a7748b`
- Job: `operational-proof` — SUCCESS
- Artifact: `core-first-code-operational-proof-43232993104`
- Artifact ID: `13951366739`
- Artifact size: 4,026 bytes
- GitHub artifact digest: `sha256:7d0fec151bc96f36e71d228c3c790e4f41ff48870b59d982a047f1be7ae35f49`
- Artifact expiry recorded by GitHub: 2026-11-19T14:01:48Z
- The digest is confirmed in workflow logs and artifact metadata. Payload download and independent checksum recomputation are **NOT VERIFIED**.

Test totals from exact-SHA job logs:

| Suite | Result |
|---|---:|
| Live-data probe contracts | 4/4 PASS |
| Core + signal regressions | 12/12 PASS |
| Core operational lifecycle/risk suite | 39/39 PASS |
| Shared risk + paper ledger suite | 28/28 PASS |
| Total | **83/83 PASS** |

Verified Core behaviors include ENTRY, DCA, LONG and SHORT paper position lifecycles, mark-to-market, EXIT, realized/unrealized PnL, fees, equity, Kill Switch, exposure reduction while killed, blocked risk increases, persisted/fail-closed risk latch, audit-failure behavior, and repeated mixed-writer contention within the tested fixtures.

CI safety markers:
- `AI_EXECUTION_ENABLED=false`
- `CANONICAL_T0_TOUCHED=false`
- `EXCHANGE_CREDENTIALS_USED=false`
- `REAL_ORDERS_SENT=false`
- `VPS_OR_PERSISTENT_RUNTIME_USED=false`

## 3. Release classification

| Release target | Status | Boundary |
|---|---|---|
| Core code-level paper candidate | PASS | Exact SHA and 83/83 CI evidence |
| Core-first paper package | CONDITIONAL | Artifact payload/hash verification and release manifest still required |
| Persistent/continuous paper runtime | NOT VERIFIED | No current persistent runtime evidence |
| Production readiness | BLOCKED | Runtime, recovery, OOS and operational gates incomplete |
| Live trading | BLOCKED / OUT OF SCOPE | No live orders or exchange execution |

Do not describe the current branch as a production release. Do not enable a deployment workflow or merge solely on the basis of the 83 passing tests.

## 4. Existing Dual-Strategy foundation

Source inspection on the baseline branch confirms:
- `paper_execution/ledger.py` supports strategy-scoped ledger access and intent provenance fields including strategy/model/dataset versions and input snapshot identity.
- `paper_execution/risk_control.py` implements a persistent Kill Switch state shared through the account database.
- `paper_execution/test_dual_ledger_red.py` contains dual-ledger contract tests, including independent Core/AI positions in one account database, separate strategy state, and 1% admission-time equity reservation assertions.

Important boundary:
- G3 verified that the global Kill Switch is visible to the AI read-only snapshot while AI order count remains zero.
- G3 did **not** exercise AI admission or AI execution.
- Only selected dual-ledger tests were included in the 28-test shared-risk/paper-ledger CI group. The entire dual-ledger contract suite is not thereby certified.
- Separate per-ledger reservation tests do not, by themselves, prove an account-wide aggregate margin cap under concurrent Core and AI admission. That invariant must be explicitly specified and tested before AI paper execution.

## 5. Phased completion plan

### Phase 0 — Freeze and preserve Core-first baseline
Status: **PASS for the code-level paper gate; release packaging CONDITIONAL**.

Scope:
- Preserve Core RSI + ADX + Smart DCA behavior and current risk controls.
- Treat SHA `755b6c4b783e873c5c9b023e4a4c0d8271a7748b` as the current evidence baseline.
- Do not mix AI feature work into Core baseline changes.
- Independently retrieve the CI artifact, verify ZIP integrity and recompute its SHA-256.
- Produce a paper-only release manifest identifying source SHA, workflow run, artifact, tests, configuration defaults and explicit disabled capabilities.

Exit criteria:
- Artifact bytes independently verified against the recorded digest.
- Release manifest committed with exact source and evidence references.
- No deployment/live capability enabled.

### Phase 1 — Complete Core-first paper release package
Status: **NOT STARTED / BLOCKED on packaging evidence**.

Scope:
- Package only the existing Core-first paper capability.
- Verify clean installation/build in an isolated environment and deterministic configuration defaults.
- Confirm no live exchange execution path is reachable from the paper package.
- Record known limitations and rollback/disable procedure.

Exit criteria:
- Reproducible package and exact-SHA CI evidence.
- Paper-only configuration and safety assertions verified.
- Release review explicitly labels the package as paper-only, not production/live.

### Phase 2 — Shared Risk Engine and dual-ledger contract
Status: **PARTIAL**.

Scope:
- Preserve independent Core and AI strategy ledgers.
- Preserve one account-level Kill Switch and fail-closed risk state.
- Specify account-wide exposure, reserved margin, realized/unrealized PnL and equity semantics across both ledgers.
- Resolve whether the 1% admission-time equity reservation is an order-level limit plus a separate account-wide aggregate cap; prevent independent ledgers from silently multiplying the account budget.
- Test duplicate intents, stale snapshots, transaction serialization, partial fills, exits, reversals, and Kill Switch races across strategies.

Exit criteria:
- Full dual-ledger suite passes, not only selected tests.
- Cross-strategy concurrent admissions cannot exceed the approved account-level risk budget.
- Kill Switch and pause behavior are consistent across Core and AI.
- No AI strategy execution is enabled during this phase.

### Phase 3 — Independent AI signal generation (signal-only)
Status: **NOT VERIFIED / NOT STARTED as an independent strategy release**.

Scope:
- Add an AI signal producer independent of Core signal conditions.
- AI can emit its own LONG, SHORT, or NO_SIGNAL result even when Core emits no signal.
- Signal records must include model version, dataset version, input snapshot identity, decision timestamp, validity window, direction, confidence and reason/provenance.
- Missing model, invalid calibration, stale/incomplete input, invalid output or provenance mismatch must fail closed to NO_SIGNAL.
- No ledger admission or order creation in this phase.

Exit criteria:
- Unit and integration tests prove AI signal independence from Core.
- Both LONG and SHORT and Core-no-signal/AI-signal cases are covered.
- Out-of-sample evaluation, leakage controls, calibration and model provenance are documented.
- AI remains signal-only; `AI_EXECUTION_ENABLED=false`.

### Phase 4 — AI paper admission through Shared Risk Engine
Status: **BLOCKED until Phases 2 and 3 pass**.

Scope:
- Route every AI signal through the same account-level risk admission contract used by Core.
- Reject stale, duplicate, expired, uncalibrated, over-budget or risk-blocked signals.
- Keep Core and AI positions/ledgers independently attributable while aggregating account-wide risk.
- Test Core/AI concurrent ENTRY, DCA, EXIT, reversal, reservation release and Kill Switch races on disposable fixtures.

Exit criteria:
- No AI intent can bypass Shared Risk Engine.
- Account-wide risk cap remains invariant under concurrent Core/AI submissions.
- AI paper lifecycle is verified end-to-end.
- Still no live execution or persistent runtime.

### Phase 5 — Integrated Dual-Strategy validation
Status: **BLOCKED until Phase 4 passes**.

Scope:
- Compare Core-only, AI-only signal stream and combined Core + AI behavior on identical time-aligned datasets.
- Use out-of-sample and walk-forward evaluation with leakage/purge controls.
- Report fees, slippage assumptions, funding, drawdown, turnover, exposure, trade count and strategy-level plus account-level equity.
- Test prolonged contention and failure/recovery scenarios in isolated environments.

Exit criteria:
- Reproducible evidence supports the combined design without hiding strategy-level losses or aggregate risk.
- No production claim based solely on backtest or unit tests.

### Phase 6 — Runtime, recovery and operational readiness
Status: **NOT VERIFIED / SEPARATE APPROVAL REQUIRED**.

Scope:
- Only after earlier phases pass, separately assess T0/T1/T2 integration, deployment parity, persistent runtime, observability, backup/restore, process crash, host/power-loss and filesystem recovery.
- The deleted former Scaleway VPS is not an available test environment; no replacement is assumed.
- No systemd/autostart or live trading is implied.

Exit criteria:
- Exact deployed source/config provenance and continuous runtime evidence.
- Recovery and operational gates pass on an explicitly approved environment.
- A separate owner decision authorizes any deployment or live capability. This roadmap itself grants no such authorization.

## 6. Global invariants for every phase

1. Core RSI + ADX + Smart DCA remains unchanged unless a separately scoped defect is demonstrated and approved.
2. AI is an independent signal strategy, not merely a Core signal scorer.
3. Every signal that may become a paper trade must pass Shared Risk Engine admission.
4. Core and AI ledgers remain separately attributable; account-level risk is aggregated.
5. Kill Switch is account-wide, persistent and fail-closed.
6. Missing/corrupt risk state, model, calibration, dataset provenance or input snapshot must fail closed.
7. No real orders, live trading, exchange execution credentials, VPS/runtime activation or canonical T0 mutation under this plan.
8. After each meaningful increment, record scope, exact source SHA, workflow/run, artifact/checksum, tests, PASS/BLOCKED/NOT VERIFIED status, next step and restrictions in this handoff/evidence docs; commit on the existing active branch.

## 7. Immediate next actions

1. Complete Phase 0 artifact payload verification and Core paper release manifest.
2. Finish Phase 2 dual-ledger/account-wide risk contract before AI paper admission.
3. Then implement Phase 3 independent AI signal-only producer.
4. Do not start Phase 4 execution until Phase 2 and Phase 3 exit criteria are proven.

## 8. Current source and evidence identity

- Repository: `kenznguyen/btcusdt-telegram-signals2`
- Branch: `feature/core-operational-proof-20261112`
- Baseline source SHA: `755b6c4b783e873c5c9b023e4a4c0d8271a7748b`
- Workflow run: `43232993104`
- Artifact ID: `13951366739`
- Artifact digest: `sha256:7d0fec151bc96f36e71d228c3c790e4f41ff48870b59d982a047f1be7ae35f49`
- No PR created or merged as part of this assessment.
