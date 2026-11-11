# Dual-Strategy and T0/T1/T2 Repository Baseline — 2026-11-11

## Review scope and source identity

- Repository: `kenznguyen/btcusdt-telegram-signals2`.
- Branch: `feature/t0-centralized-data-feeder-p1-20261101`.
- Exact reviewed repository snapshot: `fa12771973680c94f8d75fd48e69dafed9750d68`.
- Mode: read-only GitHub source and evidence review.
- No code, tests, workflow, VPS, runtime, SQLite, canonical T0 data, credentials, paper ledger state, exchange state or deployment configuration was changed or executed.
- Stage II A2.3 remains PAUSED BY OWNER per the current handoff. This report does not reopen it.

## Executive disposition

**PARTIAL / IMPLEMENTATION PRESENT / END-TO-END DUAL-STRATEGY NOT VERIFIED.**

The repository is not starting Dual-Strategy from zero. It contains:
- a native RSI/ADX/Smart-DCA Strategy Core producer;
- an independent AI/FreqAI decision path;
- separate `STRATEGY_CORE` and `AI_FREQAI` paper ledger identities;
- an account-level shared risk/reservation model and Kill Switch;
- focused dual-ledger tests and a paper-only GitHub Actions workflow.

However, source inspection found integration defects and a material sizing-policy mismatch. The existence of unit tests and code does not establish that both strategies can safely submit through the live API path. Do not mark Dual-Strategy GREEN or activate it.

## T0 / T1 / T2 evidence baseline

### T0 — canonical data foundation

- Source and isolated CI contracts exist for SQLite, fenced single-writer ingestion, read-only candle access, API and recovery.
- `T0_FEEDER_RUNTIME_VERIFICATION_20261109.md` records **PARTIAL PASS** on source SHA `9ae2eeae4ece3d657781b68e96b6f4509cd95f24`: supervised feeder process, lease heartbeat, post-restart ingestion and two bounded M15/H1 coverage windows were observed.
- Scheduler completed-window state and full recovery-lookback coverage remain **NOT VERIFIED** in that report.
- These are dated, bounded observations, not current live-state proof for this review snapshot.

### T1 — futures collector

- Separate repository tested source: `4566cffbbcf8495182abbc0d3496fdc65709ac14`.
- Latest receipt records manual exact-SHA validation **7/7 commands PASS; 88 tests PASS / 0 FAIL**.
- GitHub Actions exact-SHA status is **NOT VERIFIED**; earlier dispatcher attempts failed before job creation.
- T1→T0/T2 integration is **NOT VERIFIED**.
- T1 activation/deployment remains **NOT AUTHORIZED / NOT PERFORMED**.
- Preserve the receipt's disk/cleanup caveats; do not treat manual validation as CI or integration acceptance.

### T2 — HTTP candle consumer

- HTTP Candle Client migration and focused test evidence record **45/45 focused tests PASS**, Freqtrade 2026.9 strategy-load smoke PASS, T2 HTTP wiring PASS and direct T0 SQLite dependency removal from T2 PASS.
- Live T0 endpoint / remote TLS and deployment environment were separately marked **NOT VERIFIED** in the HTTP migration evidence.
- A bounded VPS loopback verification dated 2026-11-09 records API authentication, loopback-only binding, M15/H1 reads, ingestion-lag validation and one-shot T2 context artifact as **PASS**.
- That loopback report records no GitHub workflow run and does not independently attest the process-loaded executable bytes. It is not evidence of full T1→T2 integration, FreqAI training/inference/OOS acceptance or production readiness.

## Dual-Strategy source inventory

Exact source blobs at the reviewed snapshot:
- `pipeline/core_strategy.py`: `b4266fc05ea41355ba9dcf6f15cb7b5a6d3800b0`.
- `pipeline/decision.py`: `e718756b415fc193a486900e7b84c2cf05e6a091`.
- `pipeline/api.py`: `0540540462b3710a25788e4ff47a88272b7ee9c3`.
- `paper_execution/ledger.py`: `0bc94ae0e704a69e253246a575991c1de436e0a4`.
- `paper_execution/test_dual_ledger_red.py`: `d8d6672c0f849b8dd1e5ae7fe2069e207defb3ed`.
- `paper_execution/test_dual_ledger_migration_red.py`: `a63ea885b96f67870794507ad09f646935ea2b51`.
- `.github/workflows/dual-ledger-red.yml`: `c7c3e16026c6b5f01b6be1a7d2f1c504a532607a`.

The Core producer computes RSI/ADX and Smart-DCA actions from validated M15/H1 windows. The AI decision function independently validates canonical candles, futures trade-flow snapshot, FreqAI prediction provenance and order-book snapshot. `signal_snapshot()` calls both streams independently. The dual-ledger storage schema contains `STRATEGY_CORE`, `AI_FREQAI` and `LEGACY_UNATTRIBUTED`; shared account risk, gross exposure, margin reservations, funding/equity readiness and Kill Switch state are represented at account scope.

The current `test_dual_ledger_red.py` contains 61 test methods. The workflow is configured for isolated Python 3.12 paper-only execution with empty DB/API credential environment variables, focused dual-ledger/migration tests, full `paper_execution` regression and artifact upload. **No workflow run/result for this exact reviewed HEAD is established by this read-only review.** Historical migration-plan evidence reports older exact-SHA test results (34/34 focused and 69/69 full at SHA `8dadd35b7e9e0174efab70c425eab53bca99fa34`); do not transfer those results to the current snapshot.

## Findings — blockers before Dual-Strategy can be accepted

### DS-01 — API writer is still constructed as MANUAL

- `pipeline/api.py:ledger()` constructs `PaperLedger(...)` without a `strategy_id`, so the constructor uses its default `MANUAL`.
- The evaluate route later calls `ledger().submit(..., strategy_id="STRATEGY_CORE" or "AI_FREQAI")`.
- `PaperLedger.submit()` selects the scoped dual-ledger path only when the ledger instance itself was constructed with a strategy in `DUAL_STRATEGIES`. A MANUAL instance instead checks for the dual-ledger migration and raises `DUAL_LEDGER_MIGRATION_ACTIVE_MANUAL_WRITE_BLOCKED` once that migration exists.
- Therefore the current API evaluate route is not correctly wired to the strategy-scoped writer after dual-ledger migration. This is a static source finding; no runtime reproduction was executed.

### DS-02 — Core reads the legacy aggregate snapshot, not its own strategy ledger

- `core_decide()` calls `read_snapshot(db_path)` without a strategy ID.
- `read_snapshot()` only reads `paper_strategy_ledgers` when passed an explicit `STRATEGY_CORE` or `AI_FREQAI`; without it, the function returns the legacy `paper_state` / `paper_strategy_state` view.
- Consequently Core signal generation is not currently bound to its own isolated ledger state. This violates the dual-ledger ownership contract and can produce stale/wrong position and DCA context after migration.
- Static source finding only; no runtime reproduction was executed.

### DS-03 — Core sizing conflicts with the current owner risk direction

- `pipeline/core_strategy.py` defaults `LEVERAGE=13` and `ENTRY_MARGIN_PCT=0.50` (50% of the producer's equity basis).
- The current owner-approved risk direction is a maximum margin reservation of 1% of portfolio equity for each new ENTRY/DCA. The dual-ledger tests also assert 1% admission-time equity margin reservation.
- The producer's 50% margin calculation and fixed 13x leverage are therefore not reconciled with the current risk policy. The shared risk engine must remain authoritative and reject unsafe intents; sizing must be corrected/reconciled before Core can be accepted. Do not change Strategy Core's RSI/ADX/Smart-DCA signal rules as part of resolving sizing.

### DS-04 — Contract and implementation records are stale/inconsistent

- `DUAL_LEDGER_CONTRACT.md` still says implementation not started.
- `DUAL_LEDGER_SCHEMA_MIGRATION_PLAN.md` has a base authorization section saying implementation/database changes are unauthorized, but later appendices record separate owner approvals, implementation SHAs and passing historical test counts.
- Current code contains the dual-ledger schema and integration surfaces, so these documents need a single append-only status reconciliation with exact source/test pins before any implementation increment.

## Recommended next sequence (documentation and isolated verification first)

1. Freeze the above source findings and exact source pins in the handoff.
2. Prepare a narrow correction contract for DS-01/DS-02: explicit strategy-scoped writer construction and explicit `read_snapshot(..., strategy_id="STRATEGY_CORE")` for Core state. Define tests for both API routes, independent positions/DCA state, restart/reopen and shared risk.
3. Reconcile DS-03 against the current 1%-of-equity-per-new-order margin policy and the AI 1x–3x sizing-only policy. Do not preserve a fixed 13x Core default by inertia.
4. Reconcile DS-04 documentation against actual implementation history.
5. After contract review, propose a bounded TDD code increment and exact-SHA paper-only CI run. No VPS deployment or runtime activation is included.

## Safety and authority boundary

- Paper-only remains mandatory: `AI_EXECUTION_ENABLED=false`; no live orders or exchange execution.
- No VPS restart/autostart/systemd or T0/T1 activation.
- No canonical T0 SQLite/lease/fencing mutation, data deletion, credential changes, or trust/custody state mutation.
- This read-only assessment does not itself authorize source-code fixes, schema changes, workflow dispatch, runtime activation or trading.
- Stage II A2.3 remains PAUSED BY OWNER.
