# Core-First Quant Architecture Decision

- Decision ID: CORE_FIRST_ARCHITECTURE_DECISION
- Owner decision date: 2026-11-12
- Repository: `kenznguyen/btcusdt-telegram-signals2`
- Active branch: `feature/t0-centralized-data-feeder-p1-20261101`
- Decision status: **APPROVED — architecture direction**
- Implementation status: **NOT STARTED by this decision**

## 1. Decision

Adopt a **Core-First Quant System** as the current project priority. The existing Strategy Core (RSI + ADX + Smart DCA) is the only strategy in the paper-trading decision path. AI Strategy is deferred to offline research and must not create, authorize, or submit paper orders through the trading path until a separate owner decision reopens that scope.

This is a prioritization and architecture decision. It does not claim that Strategy Core is profitable, validated, or ready for live trading.

## 2. Target architecture

1. **T0 — Data Foundation:** independent canonical market-data source; preserve its data integrity, lineage, recovery and ownership boundaries.
2. **Strategy Core:** RSI + ADX + Smart DCA remains the sole strategy producing paper-trading intents.
3. **T3 — Shared Risk Engine:** retain the common final risk authority, including Kill Switch and existing risk controls. No parallel risk engine.
4. **Paper Execution:** paper-only; no live orders or exchange execution.
5. **T4 — Dashboard:** minimum observability for data health, Core signals, paper positions, risk decisions and performance.
6. **AI Strategy:** offline research only; no participation in the paper execution path while deferred.

T1 remains inactive unless a separate evidence-based need and bounded approval are established.

## 3. Priority order

1. Restore and verify T0 data availability through a separately approved, bounded collection decision.
2. Verify Strategy Core behavior and its data dependencies.
3. Verify Shared Risk Engine behavior, including fail-closed and Kill Switch cases.
4. Conduct paper-only evaluation of Core after the data and risk gates are satisfied.
5. Keep T4 limited to operationally useful observability.
6. Reassess AI only when real-market OOS evidence can establish incremental value over Core.

## 4. AI deferral boundary

While this decision is in force:

- Do not connect AI Strategy to the trading or paper-submit path.
- Do not create AI Ledger entries or AI orders from candidate signals.
- Do not enable `AI_EXECUTION_ENABLED`; it remains `false`.
- Do not treat synthetic data, synthetic OOS results, fixtures, or CI success as real-market OOS evidence.
- Preserve existing AI source, contracts, tests and historical evidence; do not delete or roll back completed work.
- AI offline research and deterministic synthetic engineering tests may be retained as non-admission activities, but they cannot produce `OOS_VERIFIED`, establish production thresholds, or authorize trading.
- Pause further production-oriented AI admission, registry lifecycle, trusted-time, key-enrollment and leverage-policy implementation until the owner explicitly reopens that workstream.

This decision supersedes the previous AI workstream prioritization for the current phase. It does not erase the historical three-group authorization record; it places production-oriented AI admission work on hold.

## 5. Unchanged safety and ownership constraints

- Paper-only; no live trading, real orders, exchange execution or production trading claims.
- T0 remains an independent canonical data asset. No schema change, canonical mutation, deletion, migration, restore or alternate writer is authorized here.
- No VPS provisioning, runtime deployment, service restart, exchange collection, credentials or infrastructure changes are authorized here.
- No changes to T0/T1/T2 source behavior, Strategy Core logic, CANCEL behavior, database schema, ledgers, Shared Risk Engine or Kill Switch are authorized by this architecture decision.
- Existing Shared Risk controls remain authoritative for any future permitted paper intent. The previously recorded 1% account-equity margin budget remains unchanged; this decision does not relax or reinterpret it.
- Keep all existing explicit approval gates for T0 collection and runtime actions.

## 6. Reopening criteria for AI

AI may be reconsidered only after a separate owner review has evidence for:

1. Reproducible, real BTCUSDT market-data lineage and a frozen evaluation contract.
2. Chronological holdout and embargo integrity with sample-level lineage.
3. Real-market OOS metrics, uncertainty and comparison against the same-population Core/baseline.
4. Demonstrable incremental value over Core, not merely a successful pipeline or synthetic test.
5. Complete, authoritative admission and risk integration contracts, with thresholds supported by evidence and separately approved.
6. Continued fail-closed behavior and paper-only operation.

No numeric threshold is set by this decision.

## 7. Verification and status

- This is a documentation/architecture decision only.
- No source code, tests, workflows, dependencies, schemas, data, runtime or trading behavior are changed.
- Tests/workflows: **NOT RUN** (documentation-only).
- Core runtime/data readiness: **NOT VERIFIED** by this decision.
- Shared Risk runtime behavior: **NOT VERIFIED** by this decision.
- AI production admission: **DEFERRED / BLOCKED**.
- Next step: separately scope the minimum Core-first readiness and evidence work, starting with T0 data reacquisition only after its own explicit approval.
