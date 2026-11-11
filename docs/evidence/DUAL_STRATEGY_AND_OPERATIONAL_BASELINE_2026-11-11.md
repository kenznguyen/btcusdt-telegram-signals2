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


## Addendum — shared API surfaces after dual-ledger migration (2026-11-11)

A second static pass over the same pinned source snapshot identified additional consequences of DS-01:

- `/v1/paper/cancel` also calls the MANUAL `ledger()` instance. In the dual-ledger-aware `cancel()` implementation, the MANUAL compatibility path rejects an order whose document is owned by `STRATEGY_CORE` or `AI_FREQAI`. The API therefore lacks a correctly strategy-scoped cancellation path for dual-ledger orders.
- `equity_snapshot()` calls `ledger().record_equity()` on the MANUAL instance. `record_equity()` uses legacy `paper_state` and legacy equity history; it is not an account-scoped dual-ledger mark/equity update. The evaluate route also calls this legacy method before and after submit. A dedicated account-level mark/equity update path is therefore required before shared risk readiness can be relied upon after migration.
- The MANUAL instance remains appropriate only for explicitly supported legacy/account-wide controls whose implementation is designed to operate on the shared risk latch. It must not be reused as a Core/AI order writer or strategy-scoped cancel/read path.

Expanded DS-01 acceptance scope:
1. ENTRY/DCA/EXIT submission is constructed with the exact strategy identity and cannot be downgraded to MANUAL.
2. Cancellation verifies and uses the owning strategy identity; cross-strategy cancellation is rejected.
3. Core read path explicitly requests `STRATEGY_CORE`; AI read path explicitly requests `AI_FREQAI`.
4. Account mark/equity updates reconcile both strategy ledgers, legacy adjustments, funding and active reservations under the account-level transaction; missing inputs fail closed.
5. `/v1/paper`, `/v1/equity`, `/v1/signals`, `/v1/paper/evaluate` and cancellation responses expose clearly separated account aggregate and strategy-specific read models.
6. Kill Switch/pause behavior remains account-scoped and serializes atomically with strategy-scoped admission; valid reductions remain available under the defined policy.

These are source-level findings and proposed acceptance requirements only. No endpoint or test was executed during this review.


## Owner-approved DS-01 / DS-02 TDD implementation and verification — 2026-11-11

### Authority and scope
- Owner explicitly approved bounded TDD implementation for DS-01 and DS-02, including account Equity/mark and cancellation paths, paper-only, with no VPS/runtime changes, no canonical T0 data changes and no real orders.
- No approval was given for DS-03 sizing/leverage changes, account cutover, migration execution on VPS, runtime activation, deployment or live trading.
- Preserve the earlier Stage II A2.3 PAUSED decision and all prior evidence.

### Exact source and changed files
- Repository: `kenznguyen/btcusdt-telegram-signals2`
- Branch: `feature/t0-centralized-data-feeder-p1-20261101`
- Implementation/test source SHA: `4c8007e40f5c951a7644764756bf120c8b65c6d9`
- Relevant latest blobs at that source:
  - `pipeline/api.py`: `bbca4617c7e4d51b358dd07c914308dfc392e6cd`
  - `paper_execution/ledger.py`: `0588a141f13a88895c2ac84e1b53d4edf6b2466a`
  - `paper_execution/test_dual_strategy_api_red.py`: `c893a131c7c79e4b4ea021badb04a264a23cddee`
  - `paper_execution/test_dual_ledger_red.py`: `fc7c72a6603614beb8add40298ee286982851d05`
  - `pipeline/test_api.py`: `a5f4fcc78b189f3c3797e6d49eda744c31a85077`
  - `.github/workflows/dual-ledger-red.yml`: `f9a2ee5e38a633de5f6a45e5d9023bdd0c648c13`

### Implemented behavior
- API strategy writer selects `STRATEGY_CORE` or `AI_FREQAI` only when the complete nine-version Dual Ledger migration set is already applied with exact checksums. Scoped API construction is read-only and does not apply/repair migrations.
- If migration is absent, the existing legacy path remains in place. If migration evidence is partial or checksum-mismatched, API paths fail closed; they do not fall back to legacy or auto-migrate.
- Core decision reads the explicit Core ledger after migration; before migration it retains the legacy read path. AI and Core submission use their matching scoped writer only after owner-activated migration.
- Cancellation resolves the persisted `paper_orders.strategy_id`, then calls the matching scoped ledger. Missing/null/unverified owners and unsupported strategy identities are rejected; cancellation does not trust the order document alone.
- Account mark/equity update reconciles Core, AI and legacy-unattributed ledger values, legacy PnL/fee adjustments, funding and active/partial reservation balances in one account-level transaction. Persisted numeric values are bounded and invalid reservation states fail closed.
- Before a verified account equity cutover/daily baseline exists, the mark can be recorded but risk readiness remains false; no cutover or daily baseline is synthesized. Shared risk admission therefore remains blocked until the separately governed reconciliation is complete.
- `/v1/paper` exposes account, Core and AI read models separately after migration; legacy response is preserved before migration.
- Kill-switch reset readiness checks both strategy ledgers, all account pending orders (including unassigned legacy rows), and shared account risk readiness.

### CI evidence
- Dual Ledger workflow: [run 42970058846](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42970058846)
  - Exact source SHA: `4c8007e40f5c951a7644764756bf120c8b65c6d9`
  - Compile: PASS
  - Focused DS-01/DS-02 contract: PASS
  - Full `paper_execution` regression: **298 tests PASS**
  - Artifact ID: `13832762848`
  - Artifact SHA-256: `13a2f8ed2757beb61cdeb63f082725e82b8c66158c99b53479462482a403a81e`
- T0 Single Writer Gateway workflow: [run 42969831047](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42969831047), exact source SHA `978f27b6418b0e350ebe851c74bcc498c350e7ba`: all jobs PASS, including paper consumer, static Gateway, T1 offline fixtures, provider bootstrap and TimescaleDB integration.
- T2 Freqtrade 2026.9 strategy-load smoke: [run 42969831103](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42969831103), exact source SHA `978f27b6418b0e350ebe851c74bcc498c350e7ba`: PASS.
- T0/T2 workflow SHAs are recorded separately and are not represented as the exact DS-01/DS-02 source SHA.

### Disposition and limits
- DS-01 API writer, cancellation, account mark/equity and separate read-model implementation: **PASS — source/CI scope only**.
- DS-02 Core strategy-scoped read path: **PASS — source/CI scope only**.
- Runtime activation / account migration / cutover / funding readiness: **NOT AUTHORIZED / NOT PERFORMED / NOT VERIFIED**. Risk readiness remains fail-closed until the owner separately approves and completes the cutover/funding evidence process.
- DS-03 Core sizing/leverage reconciliation: **BLOCKED**, unchanged.
- DS-04 contract-document status reconciliation: **OPEN**.
- No VPS process, T0 canonical DB, lease/fencing state, T1 activation, exchange credential, live order or deployment setting was changed. CI tests used isolated temporary paper databases only.


## Final review and refactor verification — 2026-11-11

### Final exact source
- Final implementation/test source SHA: `8d9eee6cd503237f8b8a398fcaf1e055dfa9d644`
- Relevant final blobs:
  - `pipeline/api.py`: `bbca4617c7e4d51b358dd07c914308dfc392e6cd`
  - `paper_execution/ledger.py`: `38f71f974068eb12c56dd2174a4200d07c4c98bf`
  - `paper_execution/account_equity.py`: `9971dae4592f07fe7bd2315c0f1ec1daf97af8d1`
  - `paper_execution/test_dual_strategy_api_red.py`: `66aec77ed281b16a2c44fa61176d5c5766afdfe8`
  - `paper_execution/test_dual_ledger_red.py`: `2be7188537911615b7df387d33835c281878ecc7`
  - `pipeline/test_api.py`: `11de4dd3b945554ae6c7d6354049331a3aeb96d9`
  - `.github/workflows/dual-ledger-red.yml`: `f9a2ee5e38a633de5f6a45e5d9023bdd0c648c13`

### Code review and structural adjustment
- Reviewed correctness, readability, architecture, security and performance against the owner-approved DS-01/DS-02 scope.
- Account equity/mark logic was extracted from the large ledger module into `paper_execution/account_equity.py`; ledger aggregation and active-reservation reconciliation are separate named helpers.
- The API only accepts persisted order ownership, uses read-only migration/checksum checks and fails closed on missing/partial/mismatched evidence. SQL remains parameterized; persisted numeric inputs use bounded decimal validation. No dependency was added.
- No Critical/Required review finding remains within the approved DS-01/DS-02 scope. DS-03 and DS-04 remain outside this implementation increment.

### Final CI evidence
- Dual Ledger workflow: [run 42971136555](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42971136555)
  - Exact source SHA: `8d9eee6cd503237f8b8a398fcaf1e055dfa9d644`
  - Compile: PASS
  - Focused DS-01/DS-02 contract: PASS
  - Full `paper_execution` regression: **300 tests PASS**
  - Artifact ID: `13833202840`
  - Artifact SHA-256: `0eb0bbb6ad5bfbca27c9665e06548a11dba37e2d25d4939ea891301a6054f506`
- T0 Single Writer Gateway workflow: [run 42970832396](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42970832396), exact source SHA `e99daf3f491014aa302af52629d0598d6404dbaa`: all jobs PASS, including five-layer paper consumer regressions, Gateway contracts, T1 offline fixtures, restricted provider bootstrap and TimescaleDB integration.
- T2 Freqtrade 2026.9 strategy-load smoke: [run 42970832365](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42970832365), exact source SHA `e99daf3f491014aa302af52629d0598d6404dbaa`: PASS.
- T0/T2 runs are pinned to their actual source SHA; they are not claimed as runs against the later paper_execution-only refactor commits.

### Final disposition
- DS-01 and DS-02: **PASS — source and isolated CI scope**.
- Legacy mode without migration remains intact; explicit Core/AI scope requires complete pre-existing migration evidence; API constructor is read-only; no automatic migration or account cutover.
- Account equity/mark reconciles both strategy ledgers, legacy adjustments, funding and active reservations in one transaction. Without verified cutover/daily baseline, risk readiness stays false.
- Runtime/VPS activation, database migration, account cutover/funding proof, deployment and live execution: **NOT AUTHORIZED / NOT PERFORMED / NOT VERIFIED**.
- DS-03: **BLOCKED**. DS-04: **OPEN**.
- No canonical T0 DB, leases/fencing, VPS process, T1 activation, credentials, exchange state or live orders were changed. All paper DB mutations were confined to disposable CI fixtures.
