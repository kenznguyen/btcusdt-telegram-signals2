# ADR — Route Futures Collector Data Through T0

Date: 2026-11-17 (Asia/Ho_Chi_Minh)
Status: **DECISION ACCEPTED — DESIGN ONLY; NOT IMPLEMENTED**

## 1. Decision

All raw Futures Collector feeds intended for the five-layer system must enter the system through T0 before they are consumed by T1.

Target flow:

`Binance Futures → Futures Collector → T0 ingestion / canonical data foundation → T1 Futures Intelligence → T2 AI Strategy`

T0 also supplies canonical candles directly to T2 Strategy Core and AI Strategy. T1 publishes versioned Intelligence outputs for T2 AI; those derived outputs do not replace canonical market data.

## 2. Responsibilities and boundaries

- **Futures Collector:** captures source events and delivers raw feed batches to an approved T0 ingestion interface.
- **T0:** owns ingestion, validation, normalization, provenance, quality/coverage metadata, persistence, dataset identity/versioning, and read contracts for accepted feeds.
- **T1:** consumes approved T0 datasets through read-only contracts, computes Futures Intelligence, and publishes its own versioned derived report.
- **T2 Core:** consumes canonical candles from T0; it does not depend on T1.
- **T2 AI:** consumes canonical candles from T0 and derived Intelligence from T1.
- **T3:** receives only intents admitted by the shared risk boundary; this ADR does not authorize execution changes.

T1–T4 consumers must not write to or delete canonical T0 datasets. T1 writes derived outputs under its own producer identity and storage contract; it must not write Intelligence results back into canonical T0 datasets.

## 3. Governance compatibility

This ADR defines the ingestion and consumption path; it does not change the logical data ownership or lifecycle-governance decision in [SHARED_DATA_FOUNDATION_LIFECYCLE_ADR_2026-11-08.md](SHARED_DATA_FOUNDATION_LIFECYCLE_ADR_2026-11-08.md).

The following remain in force:

- Shared logical data ownership and centralized lifecycle governance.
- T0 remains the canonical market-data foundation and canonical producer.
- Shared ownership does not grant consumers shared write authority.
- A read or consumer ACK is not deletion authorization.
- No delete-after-read behavior; retention and deletion require their separately approved policy and safety gates.

## 4. Current implementation versus target

The current T1 importer (`futures_intelligence/import_collector.py`) reads Futures Collector CSV files directly. That is the existing implementation, not the accepted target data path.

The current CSV flow must remain intact until a separately reviewed migration is implemented and validated. This ADR does not authorize:
- changing or deleting existing CSV data;
- modifying the collector, T0 schema, canonical database, writer, lease, or API;
- changing T0/T1/T2 runtime processes or deploying services;
- introducing a new database, message broker, or transport;
- changing T2 strategy behavior or AI admission;
- enabling live trading or real orders.

## 5. Required design before implementation

A follow-on implementation proposal must specify and test:

1. T0 raw-feed dataset schemas and stable dataset identity/version.
2. An authenticated, bounded ingestion contract with idempotency and duplicate handling.
3. Source timestamps versus receive/availability timestamps and clock-quality semantics.
4. Provenance, coverage, gap, freshness, and quality states for trades, funding, OI, and liquidation feeds.
5. Atomic batch acceptance, partial-failure behavior, replay/backfill, and recovery.
6. Read-only T1 consumer contract and versioned Intelligence output manifest.
7. Storage/resource limits and retention dependencies, consistent with the shared lifecycle ADR.
8. Disposable-fixture tests and GitHub Actions evidence for the exact source SHA.

No direct T1 read of T0's internal database tables is implied. T1 must use a documented T0 contract; the transport and physical storage boundary remain open for a separate design decision.

## 6. Sequencing and acceptance

- Complete **Core First** on the existing branch `feature/core-operational-proof-20261112` before implementing this migration.
- Preserve the existing CSV importer and data during the transition.
- Implement only after the T0 ingestion/read contracts, migration plan, tests, independent review, and explicit approval are complete.
- Paper-only remains in force. No live trading, real orders, or runtime activation is authorized by this ADR.

## 7. Decision status

| Item | Status |
|---|---|
| Futures Collector raw feeds enter through T0 in target architecture | ACCEPTED |
| T0 canonical ingestion and read-contract boundary | ACCEPTED |
| T1 reads accepted T0 datasets read-only | ACCEPTED |
| T1 derived Intelligence is separate from canonical T0 data | ACCEPTED |
| Existing CSV importer remains unchanged pending migration | ACCEPTED |
| T0 ingestion schema and API contract | DESIGN REQUIRED |
| Physical transport and storage implementation | OPEN |
| Source/runtime changes and migration execution | NOT AUTHORIZED |
| Live execution / real orders | NOT AUTHORIZED |
