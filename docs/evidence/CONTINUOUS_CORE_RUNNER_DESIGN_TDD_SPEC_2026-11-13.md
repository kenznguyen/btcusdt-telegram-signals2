# Continuous Core Runner — Design and TDD Specification

Date: 2026-11-13 (Asia/Ho_Chi_Minh)
Status: IMPLEMENTATION IN PROGRESS / C6.3 PRE-SUBMIT HOOK ADDED; C1-C8 NOT VERIFIED
Repository: kenznguyen/btcusdt-telegram-signals2
Branch: feature/core-operational-proof-20261112
Inspected source HEAD: d2e7f46c2a631a5673e56279fe80d9976891489a

## 1. Scope and invariants

This document specifies a paper-only continuous orchestration layer around the existing One-shot Core Runner. It does not authorize implementation, runtime activation, VPS deployment, services, systemd/autostart, or live trading.

Preserve:
- Strategy Core RSI + ADX + Smart DCA behavior and its current producer/adapter contract.
- Bundle v1 validation and provenance requirements.
- Shared Risk Engine, Kill Switch, 1% admission-time margin cap, and PaperLedger as the only paper-order admission/write path.
- `AI_EXECUTION_ENABLED=false`; no AI Strategy and no real exchange orders.
- T0 as an independent canonical data asset; no T0/T1/T2 changes in this workstream.

The continuous layer must call the existing one-shot decision boundary for one immutable, validated bundle at a time. It must not duplicate indicator logic, construct intents independently, bypass risk admission, or write directly to ledger tables.

## 2. Existing One-shot Runner and interface inspection

Inspected at source HEAD d2e7f46c2a631a5673e56279fe80d9976891489a:

| Component | Existing contract / behavior | Continuous implication |
|---|---|---|
| `core_runtime.__main__.main(argv, now_ms=None)` | Explicit `--run-once --config --bundle`; one invocation; exit 0 for NO_SIGNAL/PAPER_ACCEPTED, 2 otherwise | No loop, scheduler, signal handling, or continuous CLI mode exists |
| `core_runtime.one_shot.run_once(config_path, bundle_path, now_ms=None)` | Validates config, paper preflight, Bundle v1, current account-risk snapshot and Core paper state; calls Core producer and adapter; submits at most once | Reuse as the single-cycle executor; do not reimplement it |
| `core_runtime.input_bundle.validate_bundle` | Strict immutable Bundle v1 validation, market/candle/book/risk provenance, timestamps and digest | Every cycle must pass the existing validator before strategy evaluation |
| `core_runtime.adapter.producer_report_to_signal` | Pure strict mapping BUY/SELL/CLOSE to LONG/SHORT/FLAT; WAIT has no intent; rejects missing/mismatched provenance | Keep adapter as the only producer-to-signal translation |
| `pipeline.core_strategy.produce` | RSI/ADX/Smart DCA decision from validated M15/H1 windows, Core state and book | Strategy logic remains unchanged |
| `pipeline.core_signal.validate` | Validates actionable Core signal before ledger submission | Retain existing validation path |
| `paper_execution.ledger.PaperLedger.submit` | Scoped ledger transaction; intent ID primary key and payload hash; same intent+same payload returns prior order; same intent+different payload rejects; book snapshot reuse rejected | Existing ledger is the side-effect idempotency authority |
| `paper_execution.risk_control` / ledger risk admission | Kill/pause and shared risk checks occur inside ledger write transaction | Continuous runner must never pre-authorize or bypass this boundary |
| Existing CI workflow `.github/workflows/core-live-data-operational-proof.yml` | Runs Core, one-shot, Bundle, adapter, operational lifecycle and risk/ledger regressions; emits exact-SHA evidence | Extend/add a dedicated continuous contract job only after implementation approval |

### Existing proof reconciled

- GitHub Actions Core one-shot proof: run 43365609751, source 8f774d7103f54681497837c7e4fd7c2e1c38c754, SUCCESS, 18 workflow steps; artifact 14010098776, `core-first-code-operational-proof-43365609751`, SHA-256 `008a574ce79cb8ba4637f5b49ade49d95d6087e5e6ad2df408b2a7d3d183026b`.
- Later source HEAD d2e7f46c2a631a5673e56279fe80d9976891489a is four documentation-only commits beyond tested source 8f774d7; no intervening code changes were reported in the reconciled compare.
- Bounded ARM64 VPS manual test batch at source 562362a69d8455a34e08385d26a47fa21d2b50ed: 82/82 tests PASS; source unchanged.
- Bounded actual Core one-shot fixture: NO_SIGNAL / CORE_INDICATORS_WARMUP; no risk or ledger path exercised.
- Bounded warmed ENTRY fixture: actual Core BUY -> Shared Risk ACCEPT -> PaperLedger FILLED; 1 USDT margin reservation against 100 USDT equity; Core ledger position updated; AI ledger unchanged; temporary fixture database removed. AI execution remained false.
- These proofs establish One-shot behavior only. They do not prove a continuous process, scheduler, durable checkpoint, restart recovery, or C1-C8.

## 3. Design boundary and missing interfaces

No current interface provides:
1. Market-data/bundle acquisition and immutable bundle handoff to a continuous process.
2. Candle-close scheduler or monotonic wait loop.
3. Single-process ownership / duplicate runner exclusion.
4. Durable cycle journal/checkpoint.
5. Recovery/reconciliation of a cycle interrupted around ledger commit.
6. Graceful stop and bounded shutdown.

The bundle provider is therefore an explicit future adapter boundary, not an assumed capability of `run_once`. It must produce a complete Bundle v1 from already-authorized sources. It must not read or mutate canonical T0 directly unless the existing approved read interface is used; this design does not select or change the T0/T1 transport.

## 4. Proposed process lifecycle

Use an explicit state machine:

- `STOPPED`: no runner ownership.
- `STARTING`: validate config and acquire exclusive process ownership.
- `PREFLIGHT_BLOCKED`: paper config, AI-off, credentials, ledger, risk readiness or dependency preflight failed; no cycle starts.
- `WAITING_FOR_CANDLE`: wait for the next eligible closed M15 candle and bundle readiness.
- `CYCLE_CLAIMED`: atomically claim the candle-cycle key in the durable runner journal.
- `VALIDATING`: validate immutable bundle and freshness/provenance.
- `EXECUTING`: call existing one-shot executor once for this bundle.
- Terminal cycle outcomes: `NO_SIGNAL`, `PAPER_ACCEPTED`, `RISK_REJECTED`, `INPUT_REJECTED`, `FAILED`, `UNKNOWN_REQUIRES_RECONCILIATION`.
- `BACKOFF`: bounded retry delay for transient provider/process errors; no retry with a newly generated intent when outcome is unknown.
- `STOPPING`: stop claiming new cycles; finish or persist current cycle state; release process ownership.
- `STOPPED`: shutdown complete.

Transition rules:
- Startup never implies a trading cycle. Preflight must pass first.
- A failed preflight remains fail-closed; no bundle is consumed and no ledger call occurs.
- Only a newly closed M15 candle can create a new cycle.
- At most one active cycle per symbol/timeframe/strategy key.
- A graceful stop prevents new claims. It must not cancel or replay an in-flight ledger operation blindly.
- An unhandled exception after a possible ledger commit is UNKNOWN until reconciled by immutable intent identity / ledger state.
- Kill Switch and risk rejection are terminal outcomes for that attempt. They must not trigger an alternate strategy, bypass, or immediate resubmission.

## 5. Cadence and cycle identity

### Cadence

- Decision cadence is driven by closed BTCUSDT M15 candles, not by an arbitrary fixed-frequency trading loop.
- Scheduler waits for the next M15 close boundary plus a configurable bounded data-settlement allowance.
- Use wall-clock UTC timestamps for candle identity and freshness. Use a monotonic clock for sleep/deadline measurement so wall-clock adjustments do not cause tight loops or skipped waits.
- Re-check provider readiness after wake-up. If the expected candle is not closed, complete, validated and fresh, do not evaluate the strategy; remain waiting or enter bounded backoff.
- H1 context must satisfy the existing Bundle v1 eligibility rules; do not substitute an in-progress H1 candle.
- Settlement allowance, retry ceiling and backoff schedule are configuration decisions to be frozen during implementation design review; do not silently hard-code arbitrary values.

### Canonical cycle key

`binance:USDT_PERPETUAL:BTCUSDT:15m:<candleOpenTimeMs>:STRATEGY_CORE`

Persist the key alongside:
- immutable `bundleId` and bundle content SHA-256;
- M15 candle open/close times and dataset versions;
- T1 order-book snapshot ID;
- runner source SHA and config digest;
- cycle state, timestamps, attempt count, runId, intentId (when present), ledger order reference and terminal result.

One canonical bundle is accepted for one cycle key. If the same cycle key arrives with a different bundleId or conflicting provenance, do not silently replace the claimed input. Mark conflict and fail closed for operator/reconciliation.

## 6. Checkpoint and duplicate prevention

### Durable journal

Use a dedicated runner-state journal interface with atomic uniqueness on cycle key. The exact storage implementation and location are not yet frozen. It must be isolated from T0 canonical storage and must not mutate T0. Journal writes must be durable before a cycle is considered claimed.

Minimum record:
- cycle key (unique);
- bundleId, bundle hash and immutable bundle location/reference;
- state and state version;
- created/updated timestamps;
- runId, intentId, orderId/reservationId when available;
- terminal outcome and stable reason code.

### Idempotency authority

- The journal prevents two runner instances from claiming the same candle-cycle key.
- PaperLedger remains the authoritative protection against duplicate paper side effects: its intent identity/payload-hash behavior must be retained and tested.
- The Core producer's actionable intent identity must be stable when replaying the same immutable bundle. A retry must reuse the same bundle and intent identity, never mint a new intent for the same decision.
- The ledger's book-snapshot reuse guard is a secondary defense, not a substitute for intent idempotency.
- Same intentId with changed payload is a hard conflict; never overwrite or reinterpret it.

### Commit/recovery ordering

1. Persist immutable bundle bytes and verify their digest.
2. Atomically claim cycle key and persist `CYCLE_CLAIMED` plus bundle reference/hash.
3. Persist `EXECUTING` before calling the one-shot executor.
4. Invoke one-shot once with the exact immutable bundle.
5. Persist returned run/result and terminal outcome.
6. Advance the completed-candle checkpoint only after the outcome is terminal and reconciled.

The journal and PaperLedger are separate transactional resources unless implementation proves otherwise. Therefore recovery must explicitly handle the crash window after ledger commit but before journal terminal update:
- Reopen the exact persisted bundle.
- Recompute/verify its digest and cycle identity.
- Reuse the same intent identity.
- Query/reconcile the ledger's existing intent/order before deciding whether a retry is needed.
- If ledger outcome cannot be established, set `UNKNOWN_REQUIRES_RECONCILIATION`, block new cycle claims, and fail closed.
- Do not advance the candle checkpoint based solely on process exit code or a missing journal update.

A read-only ledger lookup/reconciliation interface by intentId is a required interface gap to resolve before implementation if current ledger APIs cannot establish the outcome safely. Do not query SQLite by ad-hoc SQL from the continuous orchestrator.

## 7. Recovery policy

- Startup scans incomplete journal records before accepting new candles.
- `CYCLE_CLAIMED` with no execution marker: validate the persisted bundle and resume that exact cycle.
- `EXECUTING`: reconcile by stable intentId against PaperLedger; if no intent was generated, rerun only if the execution boundary proves no ledger submission occurred; otherwise mark UNKNOWN.
- Terminal journal state: do not replay.
- Corrupt/missing bundle, digest mismatch, cycle-key mismatch, config/source incompatibility, ledger unreadable, or unresolved commit status: fail closed and block new cycles.
- Recovery must never synthesize missing candles, book snapshots, risk snapshots, provenance, intent IDs or fills.
- Recovery must not delete, compact or rewrite canonical market data, audit records, ledger history or evidence.

## 8. C1-C8 RED test specification

All tests below are required to be written first and demonstrated RED against the current codebase before implementation. Tests should prefer real stateful components and temporary databases; mock only external bundle-provider/clock boundaries.

### C1 — Cadence and stable cycle
- C1.1 A cycle is not started before the M15 candle is closed and the configured settlement/readiness policy passes.
- C1.2 Multiple scheduler wakeups for the same closed candle produce one cycle claim.
- C1.3 A delayed wake-up processes the latest eligible closed candle without evaluating an in-progress candle.
- C1.4 Wall-clock jumps do not create a busy loop, double cycle or skipped monotonic deadline.
- C1.5 H1 eligibility follows Bundle v1 rules; no in-progress H1 substitution.

### C2 — Duplicate candle and signal prevention
- C2.1 Two concurrent runner instances cannot both claim the same canonical cycle key.
- C2.2 Restart/re-delivery of the same candle and bundle does not create a second ledger order.
- C2.3 Same cycle key with a different bundleId/content hash is a conflict and fails closed.
- C2.4 Same intentId and same payload replays the existing ledger result.
- C2.5 Same intentId with a changed payload is rejected and never overwrites the original order.

### C3 — Missing, invalid and stale data fail closed
- C3.1 Missing M15/H1 bundle, missing book or unavailable provider produces no Core call and no ledger write.
- C3.2 Unclosed, gapped, incomplete, stale or future-dated candles are rejected.
- C3.3 Stale/future T1 book, broken continuity, invalid snapshot identity or insufficient depth is rejected.
- C3.4 Invalid risk snapshot, stale account state, or changed Core paper state is rejected before submit.
- C3.5 Provider timeout/reconnect does not reuse stale cached data as fresh.

### C4 — Conflicting inputs/signals
- C4.1 Two different bundle identities for the same cycle key are not both evaluated.
- C4.2 Contradictory actionable outcomes for one cycle key are rejected as conflict; no "last writer wins".
- C4.3 A cycle already claimed/executing cannot be replaced by a later-arriving opposite signal.
- C4.4 Core position ownership/state conflict is rejected by existing validation/ledger policy; no AI fallback or strategy substitution.

### C5 — Risk Engine rejection
- C5.1 Kill Switch active -> ledger rejects; no fill, no new cycle-side effect, terminal RISK_REJECTED.
- C5.2 Risk pause/limit breach/exposure cap -> no paper fill and reason is preserved.
- C5.3 Risk rejection does not trigger a bypass, retry with altered size, or alternate strategy.
- C5.4 A rejected intent is not reported as PAPER_ACCEPTED and does not advance position state.

### C6 — Restart and recovery
- C6.1 Restart with no active cycle resumes waiting without replaying terminal cycles.
- C6.2 Restart after claim but before execution resumes the exact persisted bundle.
- C6.3 Crash after ledger commit but before journal terminal write reconciles the existing order and does not duplicate it.
- C6.4 Corrupt/missing bundle or unreadable ledger leaves cycle UNKNOWN/BLOCKED and prevents new claims.
- C6.5 Graceful stop during wait exits promptly without claiming a new cycle.
- C6.6 Graceful stop during execution does not interrupt or duplicate the ledger side effect.

### C7 — Checkpoint and idempotency
- C7.1 Cycle claim is atomic under concurrent processes.
- C7.2 Checkpoint advances only after a terminal, reconciled result.
- C7.3 A terminal NO_SIGNAL is checkpointed and is not reevaluated after restart.
- C7.4 Replaying the same immutable bundle reuses stable run/intent identities and prior ledger result.
- C7.5 Journal/ledger disagreement blocks progress until reconciled.
- C7.6 Journal corruption or version mismatch fails closed; no automatic reset that loses dedupe history.

### C8 — Kill Switch and shutdown safety
- C8.1 Kill Switch is rechecked at the ledger transaction boundary; runner-side cached readiness cannot override it.
- C8.2 Kill Switch active during an in-flight scheduling window prevents new risk-increasing submission.
- C8.3 Kill Switch does not block safe process shutdown or read-only reconciliation.
- C8.4 Runner stop/kill state prevents new cycle claims and remains paper-only.
- C8.5 AI execution environment/config override and exchange credentials continue to fail closed.

## 9. GREEN acceptance criteria

The implementation may be considered GREEN only when all are true:

1. All C1-C8 RED tests first fail for the intended missing behavior, then pass after implementation.
2. Existing One-shot, Bundle v1, Core strategy, adapter, risk, ledger, short lifecycle, DCA and account-risk regression suites remain green.
3. Concurrency tests prove exactly one journal claim for one cycle key.
4. Crash-injection tests cover every boundary before/after journal claim, before/after ledger submit, and before/after terminal checkpoint.
5. Crash-after-ledger-commit test proves no duplicate order/fill and reconciles the original ledger result.
6. Stale/missing/invalid data, conflicting bundle, risk rejection and Kill Switch cases all fail closed.
7. Terminal outcomes are deterministic and replay-safe; no cycle is silently skipped or processed twice.
8. No source changes to Strategy Core, T0/T1/T2, or AI strategy are required for orchestration; if required, stop and request a new scope.
9. `AI_EXECUTION_ENABLED=false`, no exchange credentials/connections, no live order endpoints and no real orders are asserted in tests and CI.
10. Full repository CI and dedicated Continuous Runner CI pass on the exact branch head SHA; no skipped/xfail tests are accepted for C1-C8.
11. Evidence artifact contains source SHA, branch, workflow run/job IDs, test names/counts, C1-C8 verdicts, safety assertions, and artifact SHA-256/digest/expiry.
12. Runtime/VPS activation remains a separate approval gate even after code/CI GREEN.

Any unknown ledger outcome, journal conflict, missing provenance or risk readiness failure is BLOCKED, not GREEN.

## 10. CI evidence requirements

Add a dedicated CI job/workflow only after implementation is separately authorized. It should:
- Run deterministic unit tests for state machine, cadence and cycle-key construction.
- Run temporary-SQLite integration tests for atomic claim, restart, journal recovery and ledger idempotency.
- Run crash-injection and concurrent-process tests.
- Run existing One-shot/Core/Risk/Ledger regression suites.
- Compile/import all changed modules.
- Emit a machine-readable verdict for C1 through C8, plus aggregate `CONTINUOUS_CORE_RUNNER=PASS|FAIL`.
- Record exact `git rev-parse HEAD`, branch, workflow run URL/ID, event, job IDs/conclusions, Python/platform/dependency versions, test totals and artifact metadata.
- Assert `AI_EXECUTION_ENABLED=false`, `REAL_ORDERS_SENT=false`, `EXCHANGE_CONNECTIONS_USED=false`, `T0_CANONICAL_MUTATED=false`, `VPS_RUNTIME_USED=false`.
- Upload logs, JUnit/unittest output, crash/concurrency evidence and JSON summary as one traceable artifact; record artifact ID/name/digest/expiry and independently verify downloaded bytes before claiming payload verification.

CI GREEN proves code and isolated fixtures only. It does not authorize or prove continuous runtime activation, VPS deployment, systemd/autostart, T0/T1/T2 activation, AI strategy or live trading.

## 11. Current disposition and next gate

- One-shot Runner and current interfaces: INSPECTED.
- Existing One-shot evidence: PASS within the bounded scopes recorded above.
- Continuous Runner architecture: DESIGN COMPLETE.
- C1-C8 RED tests: SPECIFIED / NOT WRITTEN / NOT RUN.
- Continuous Runner implementation: NOT AUTHORIZED.
- Continuous CI: NOT IMPLEMENTED.
- Continuous runtime/VPS/service/autostart: NOT AUTHORIZED.
- AI strategy/execution and real orders: NOT AUTHORIZED.

Next gate: owner review of this design and a separate explicit approval for implementation of the Continuous Core Runner on the same branch. Implementation must begin with C1-C8 RED tests and must stop if an unresolved interface requires modifying protected layers.


## Addendum — pre-ledger intent persistence hook (2026-11-13)

- Owner explicitly approved the additional One-shot interface change: optional `on_intent_prepared` callback in `core_runtime/one_shot.py`.
- Implemented `run_once(..., on_intent_prepared=None)`. For an actionable validated Core intent, the callback receives the exact validated `intent` object after Core signal validation and before PaperLedger construction/submission. The callback can durably persist `intentId`, `bundleId` (from its immutable cycle context) and `cycleKey` (from the Continuous Runner context).
- If the callback is absent, existing One-shot behavior is preserved. If it is non-callable or raises, the runner returns `RUN_FAILED / INTENT_PREPARE_CALLBACK_FAILED` and does not construct or call PaperLedger.
- Added three One-shot contract tests: callback runs before submit and sees the same intent ID; callback failure aborts before Ledger construction; omitted callback preserves existing behavior.
- Commits on the existing branch: tests `b06c97179afa4fa2d46bea19af7eef4e209cc893`; implementation `14df039546990c3bb16952aaa17a34175631d5c6`. Implementation file blob: `683e1a96061724c265bb6bf8dcdc956f9c18acfb`; test file blob: `8123bd6e9b6b3d0c356c462969658a56b8305762`.
- The existing Core operational workflow includes `pipeline.test_core_runtime_one_shot`, so the new tests are in its existing test command path. No workflow run/job log/artifact has yet been retrieved for these commits; test execution status is **NOT VERIFIED**.
- This hook closes the missing pre-submit identity persistence interface, but it does not itself implement the durable Continuous Runner journal or crash recovery. C6.3 end-to-end reconciliation remains **NOT VERIFIED**.
- No Strategy Core, Risk Engine, PaperLedger schema/behavior, T0/T1/T2, AI strategy, VPS runtime, service, exchange connection or real-order behavior was changed.
- Next: implement and test the journal/recovery layer, then C1-C8 in RED-first order. Maintain paper-only and `AI_EXECUTION_ENABLED=false`; runtime activation remains separately gated.

## Addendum — journal and M15 cadence implementation evidence (2026-11-13)

- Owner approved automatic continuation through Continuous Core Runner GREEN, within the existing paper-only code/CI scope. Runtime/VPS/service activation remains separately gated.
- Durable journal implementation now exists in core_runtime/continuous_journal.py. It uses a dedicated SQLite file, WAL, busy timeout, BEGIN IMMEDIATE, unique cycle_key, exact-input idempotency, conflict rejection, compare-and-swap state transitions, terminal replay rejection and pre-submit intent persistence.
- Cadence helpers now exist in core_runtime/continuous_cadence.py. They validate Bundle v1 before cycle identity construction, calculate latest eligible closed M15 candle and next close+settlement deadline, and wait against a monotonic deadline.
- RED was observed for missing journal module (run 43411595131), missing transition API (run 43414066659), missing cadence module (run 43414221740), and missing record_intent API (run 43414485163).
- Component GREEN baseline: run 43414415701, job 131848574931, source SHA 4fa3064903e041862fbb07ad2285ac400688de90, SUCCESS. Cadence tests 5/5 PASS; journal tests 6/6 PASS; all existing regression workflow steps also SUCCESS.
- Artifact 14030612833, core-first-code-operational-proof-43414415701, SHA-256 28d3365ab0b371c50c8df072a3e49c201379de1468e8841c068da625c8037aa8, expires 2026-11-20T11:06:55Z.
- The later journal test for pre-submit intent persistence was RED at source 35c795096634a4dde3d7b20e26b3f9cb352fba01. Implementation commit 83124de4e69a49ff828da3529d22c542d23e587a adds record_intent; test result is pending.
- Orchestration tests have been added in core_runtime/test_continuous_runner.py, and the workflow includes their execution step. A previous run was cancelled before that step executed; the corrected workflow run is pending.
- Component disposition: cadence PASS; journal claim/state transition PASS at the stated baseline; intent persistence implementation committed / test NOT VERIFIED; continuous orchestration and crash recovery NOT IMPLEMENTED / NOT VERIFIED; full C1-C8 GREEN NOT ACHIEVED.
- CI summary defect: One-shot unittest output reports 14 tests, while the workflow's status script still checks 11. This must be corrected before final acceptance.
- Continue with RED-first verification of intent persistence and orchestration tests, then implement the minimum runner and recovery behavior. Do not alter Strategy Core, Shared Risk Engine, PaperLedger schema/behavior, T0/T1/T2, or AI Strategy. If a protected interface change proves necessary, stop and request approval. Maintain AI_EXECUTION_ENABLED=false and no live orders or VPS runtime.


## Addendum — orchestration, real-ledger recovery and checkpoint (2026-11-13)

- Implemented core_runtime/continuous_runner.py as an explicitly invoked, paper-only M15 scheduler. It validates Bundle v1, checks close+settlement, stores immutable content-addressed bundle bytes outside T0, claims one cycle in the separate SQLite journal, calls the existing One-shot Runner with the pre-submit intent callback, records terminal outcomes and supports graceful stop.
- Recovery verifies bundle digest, cycle identity, source/config provenance and reads the existing PaperLedger audit through the read-only paginated read_audit API. If an intent exists but audit reconciliation is unavailable or no matching event is found, it returns BLOCKED; it never blindly submits a second order. If a cycle is proven pre-submit (no intent persisted), it can resume the exact stored bundle.
- RED/GREEN evidence for this stage:
  - RED for missing orchestration module: run 43414864777, source dfc2f1e877d4c4ea1e5f7d56affd3191a777872c.
  - GREEN regression run 43415365632, job 131851922969, source SHA 8f1e916d07001e8330972b75a95d2d666b73a04b, SUCCESS. Cadence 5/5, journal 7/7, orchestration 12/12; all existing workflow regression steps SUCCESS.
  - Artifact 14031547436, core-first-code-operational-proof-43415365632, SHA-256 3fca466c9b9389eade70a5bc99252ce3a211003ec543feca1eb6c1d7ecccd20a, expires 2026-11-20T11:13:44Z.
- The 12 orchestration tests include a real fixture PaperLedger submit followed by an injected process interruption after the actual commit. Recovery locates the order by intentId in the real audit and reconciles PAPER_ACCEPTED without a second submit. Core ledger remains one order; AI ledger remains zero orders.
- Checkpoint tests were added before implementation. RED run 43415426955 at source ddef24fdc68fb55cdba7c59ce3f6399d574d498d failed because get_checkpoint was not yet implemented. Commit 5d3e2987d952de0aaf125bf69d6d2bfc7ea0e52d adds a dedicated checkpoint table, get_checkpoint readback and atomic monotonic advancement in the same transaction as reconciled terminal transitions. Run 43415771895 at this source was in progress at last read.
- CI reporting was corrected in commit 5f49c98cde4f8bc03d67626db5052f16543ae4e8: One-shot test count now expects 14 rather than stale 11; continuous component logs are compiled/archived and verdicted.
- Current disposition: cadence PASS; durable claims/transitions/intent persistence PASS; orchestration and actual ledger recovery PASS; checkpoint implementation committed / NOT VERIFIED; full C1-C8 GREEN remains pending.
- Continue RED-first for remaining lifecycle, idempotency, provenance and checkpoint cases. Do not modify Strategy Core, Shared Risk Engine, PaperLedger schema/behavior, T0/T1/T2 or AI Strategy. If a protected interface change is required, stop and seek approval. Keep AI_EXECUTION_ENABLED=false, no VPS activation, no exchange connections and no real orders.


## Addendum — checkpoint component GREEN (2026-11-13)

- RED: run 43415426955 at source ddef24fdc68fb55cdba7c59ce3f6399d574d498d failed because ContinuousJournal.get_checkpoint was absent.
- GREEN: run 43415771895, job 131853156497, exact source SHA 5d3e2987d952de0aaf125bf69d6d2bfc7ea0e52d, SUCCESS. Cadence 5/5, journal 10/10, orchestration 12/12; all existing Core/One-shot/Bundle/adapter/PaperLedger/risk/T1-T2 regression steps SUCCESS.
- Artifact 14031268827, core-first-code-operational-proof-43415771895, SHA-256 ee56dec1d12da849a8e271000d74c382a0adea04fba09210016c98fad0f00d76, expires 2026-11-20T11:16:45Z.
- Checkpoint table and get_checkpoint readback were implemented in commit 5d3e2987d952de0aaf125bf69d6d2bfc7ea0e52d. The checkpoint is advanced in the same transaction as a reconciled NO_SIGNAL, PAPER_ACCEPTED or RISK_REJECTED terminal state, and it never regresses for late completion of an older candle. UNKNOWN_REQUIRES_RECONCILIATION, INPUT_REJECTED and FAILED do not advance it.
- CI status script now expects the actual 14 One-shot tests, and the artifact includes the cadence/journal/orchestration logs. The run above completed SUCCESS with the corrected workflow.
- Remaining implementation/test work: exclusive process ownership, config digest revalidation, terminal journal-vs-ledger reconciliation, runner Kill Switch integration, claim-before-execution recovery, and corrupted-bundle recovery. Full C1-C8 GREEN is not yet achieved.

