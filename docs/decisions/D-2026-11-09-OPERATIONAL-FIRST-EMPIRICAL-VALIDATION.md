# Decision D-2026-11-09 — Operational First, Empirical Validation

Date: 2026-11-09 (Asia/Ho_Chi_Minh)
Status: APPROVED STRATEGIC DIRECTION
Scope: Project prioritization and acceptance gates only. This decision does not authorize production activation, live trading, destructive data operations, or any unlisted runtime change.

## Decision

Prioritize completing the minimum reliable operating system before further strategy optimization or feature expansion. After the operating baseline is stable and observable, evaluate Strategy Core and the independent AI Strategy using newly collected operational data in paper mode.

The objective is to move from design/backtest-led confidence to evidence-backed operational reliability and empirical strategy evaluation. Delivery volume or feature count is no longer the primary progress metric.

## Required sequence

1. **T0 data integrity** — complete publication visibility/durability ordering, writer fencing and generation ownership, explicit WINDOW_GAP semantics, FINAL_ONLY and interval validation, product identity, manifest/fixture consistency, and independent review on the exact resulting SHA. T0 remains an independent data asset and canonical source.
2. **T1 collection reliability** — complete collector lifecycle, event ordering/timestamps, reconnect and loss detection, coverage/continuity evidence, and source-specific validation. Existing P1.8/P1.9 blockers and independent-review requirements remain binding; this decision does not waive them.
3. **T2 Dual-Strategy Intelligence** — preserve Strategy Core (RSI + ADX + Smart DCA) and the independent AI LONG/SHORT strategy with separate attribution/ledgers. Both must pass through the same Shared Risk Engine and Kill Switch.
4. **Integrated operations** — validate service connectivity, health/readiness, observability, resource limits, restart/recovery/fencing, and consistency of required state and backups.
5. **Paper operation and baseline capture** — run against real market data but simulated execution only. Record every candidate signal, admission/rejection reason, risk decision, simulated fill, fee/slippage assumption, position lifecycle, DCA event, and outcome with source/data/model/config provenance.
6. **Empirical evaluation** — assess Core, AI, risk controls, DCA, and system reliability separately and jointly. Segment results by LONG/SHORT and market regime; account for fees/slippage and dependent observations; use out-of-sample/walk-forward evidence where applicable.
7. **Controlled optimization** — change one bounded factor at a time, preserve the baseline, test and compare against it, and retain only changes supported by reproducible evidence.

## Acceptance gates

- No progression to broad paper evaluation while critical data-integrity or fencing defects remain open.
- No strategy result is accepted if its input data, model/config lineage, signal timestamp, or simulated execution assumptions cannot be traced.
- Record rejected signals as well as accepted trades; otherwise selection bias will distort evaluation of the Risk Engine.
- Keep Core and AI performance attribution separate. AI value is measured by incremental risk-adjusted portfolio contribution after the shared risk gate, not raw signal count or prediction accuracy alone.
- Technical reliability metrics and trading-performance metrics must be reported separately.
- Do not optimize during baseline collection except to correct a safety, correctness, or data-integrity defect; record any such intervention and its affected interval.
- Use sufficient observations and market-regime coverage rather than a calendar deadline to decide whether evidence is adequate.
- No live orders. Keep `ai_execution_enabled=false`. Paper/signal-only remains the execution boundary.
- T0 remains independent. Do not weaken its data-integrity guarantees to improve throughput or commercial delivery speed.
- Data retention/deletion, archive, cleanup, compaction, backup expiry, and key destruction remain governed by their separate approvals; this decision grants no destructive authority.

## Metrics to collect

- **T0:** continuity, gaps, freshness/lag, validation failures, publication durability, fencing/recovery outcomes.
- **T1:** event coverage/loss, reconnects, ordering anomalies, latency, source divergence and collector uptime.
- **Core / AI:** candidate signals, accepted/rejected signals, LONG/SHORT attribution, expectancy, profit factor, win rate and sample coverage.
- **Risk / portfolio:** rejection reasons, exposure, margin use, drawdown, tail loss, DCA depth/frequency and Kill Switch behavior.
- **Execution simulation:** fees, slippage, fill assumptions, missed/partial simulated fills and sensitivity to assumptions.
- **System:** availability, restart/recovery time, resource use, alert correctness and trace completeness.

## Verification record

- Decision approved by user in conversation on 2026-11-09.
- Documentation-only record. No source code, tests, workflows, runtime configuration, VPS, database, Feeder, exchange connection, market-data synchronization, paper ledger, or trading state changed.
- Tests: NOT RUN. GitHub Actions: NOT DISPATCHED. Workflow run: NONE. Artifact: NONE.
- This is a prioritization/acceptance decision, not evidence that any phase is complete or PASS.
- Existing workstream blockers, exact-SHA review requirements, and approvals remain in force.

## Next step

Continue the currently active T0/T1 contract work on the existing branch. Close its documented correctness findings and obtain independent review against the exact final SHA before implementation/activation gates are reconsidered. Do not open a parallel branch or PR for this decision.
