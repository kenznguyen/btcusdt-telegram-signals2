# Dataset and Consumer Inventory — Static Repository Baseline

Date: 2026-11-09
Status: **PRELIMINARY STATIC INVENTORY — RUNTIME PRESENCE NOT VERIFIED**

## 1. Purpose and evidence boundary

This inventory records datasets, stores, producers, consumers, and evidence objects identifiable from the repository source and committed documentation at branch source SHA `da37b1dd5d86fc8c0854d8769804f1b7ddf99f87`.

This is a static source/document inspection only. It does not prove that any database, file, process, collector, endpoint, or artifact currently exists or is active on the VPS.

Not performed:
- no VPS/SSH connection or filesystem listing;
- no SQLite/PostgreSQL connection or query;
- no database creation, migration, write, sync, or integrity probe;
- no exchange/network probe;
- no Feeder, collector, Freqtrade, or paper runtime start;
- no model training, backtest, or live/paper order;
- no archive, vacuum, retention, cleanup, or deletion action.

Evidence classes used below:
- **Source-defined:** identified in code or migration files; runtime presence is not implied.
- **Documented historical:** recorded in a dated evidence document; not a claim about current state.
- **Design-only:** proposed contract or architecture, not proof of implementation.
- **Unknown:** repository evidence is insufficient.

## 2. Executive summary

The repository shows several distinct data domains, not one interchangeable database:

1. T0 canonical market candles and their provider/lease metadata.
2. T1 observed futures-intelligence snapshots imported from collector CSVs, plus a separate connection-lifecycle sidecar reference implementation.
3. T2 FreqAI input provenance and prediction artifacts consumed through the T0 read-only HTTP boundary.
4. Paper strategy/account ledgers and risk state in a separate SQLite persistence domain.
5. Synthetic CI evidence packages and design-only forward evidence retention proposals.

The actual current VPS inventory, PostgreSQL canonical status, active T1 capture files, paper database path, FreqAI artifact instances, backups, replicas, exports, and local copies are **NOT VERIFIED**. No retention period can safely be assigned from this static inventory.

## 3. Inventory by domain

### 3.1 T0 — canonical market data

| Item | Static evidence | Classification | Confidence / limitation |
|---|---|---|---|
| Canonical candle dataset | SQLite store creates/reads `candles`; PostgreSQL migration creates `market_data.candles` | Canonical operational | Source-defined; active backend not established |
| Instrument metadata | PostgreSQL migration creates `market_data.instruments`; SQLite store has candle metadata | Canonical metadata | Source-defined; current rows unknown |
| Feeder lease/fencing state | PostgreSQL migration creates `market_data.feeder_leases`; fenced writer migrations and code enforce lease authority | Operational control metadata | Source-defined; not market payload |
| Dataset identity | `datasetVersion` is a SHA-256 digest for the exact content/query window | Evidence/provenance metadata | Source-defined; not a whole-database digest |
| Read interface | `GET /v1/candles` read-only API and PostgreSQL/SQLite read adapters | Consumer interface | Source-defined; deployed endpoint not probed |
| SQLite storage | Code defaults to SQLite and expects configured `MARKET_DATA_DB` | Canonical candidate backend | Source-defined; current runtime file not checked |
| PostgreSQL/TimescaleDB storage | Opt-in adapter and migrations exist | Canonical candidate backend | Source-defined; canonical DB creation/provider remains unverified/paused |

**Source identity and scope:** the market-data README and candle metadata identify Binance USD-M perpetual BTCUSDT, M15/H1, with `ccxt.binanceusdm` provenance. This inventory does not authorize any new source probe, sync, or collector run.

**Historical VPS evidence:** `docs/evidence/t0/T0_FEEDER_SUPERVISED_RUNTIME_2026-11-08.md` records a supervised SQLite runtime at `/home/ubuntu/t0/app/.data/market-data.sqlite3`, with integrity/WAL and bounded M15/H1 progress checks. That is dated historical evidence only. It does not establish the current file, current process, current dataset extent, or current runtime source identity.

**Important separation:** `candles` is the market payload; instrument metadata, lease/fencing rows, API health, and runtime logs are not additional candle datasets. They have separate lifecycle purposes.

### 3.2 T1 — futures intelligence and collector evidence

| Item | Static evidence | Classification | Confidence / limitation |
|---|---|---|---|
| Trades CSV inputs | `futures_intelligence/import_collector.py` reads bounded CSV inputs | Raw source observations | Source-defined; actual CSV files not inventoried |
| Funding CSV inputs | Same importer; funding coverage/provenance fields | Raw source observations | Source-defined; coverage unknown |
| Open-interest CSV inputs | Same importer | Raw source observations | Source-defined; coverage unknown |
| Liquidation CSV inputs | Same importer | Raw source observations | Source-defined; importer validates observed fields | 
| Intelligence snapshot | Importer creates a bounded JSON snapshot with source commit, input-file hashes, coverage, quality `OBSERVED_ONLY`, and deterministic snapshot identity | Derived/observed intelligence | Source-defined; output path and actual snapshot files unknown |
| Connection lifecycle sidecar | Rust writer creates append-only JSONL events and a separate manifest with byte size, digest, event count, session/source identity, watermark, subscriptions | Evidence | Portable reference implementation; not integrated into upstream collector |
| Upstream collector runtime | Separate repository is referenced by source/evidence | Producer process | Not started or contacted by this inventory |

The Rust sidecar is not the same dataset as the CSV market observations. Its purpose is transport/session lifecycle evidence. The implementation evidence explicitly records that upstream integration and live operation were not complete at the time of that evidence.

The importer labels its output `OBSERVED_ONLY`; it must not be treated as a complete exchange tape or as proof of complete market coverage.

### 3.3 T2 — FreqAI data and model provenance

| Item | Static evidence | Classification | Confidence / limitation |
|---|---|---|---|
| T0 candle input | `freqai_bridge/context.py` uses `CandleHttpClient` and the T0 read-only HTTP boundary | Consumed canonical dataset | Source-defined; live endpoint not checked |
| Training dataset provenance | README requires actual training dataset manifest/fingerprint and model provenance | Evidence/lineage | Contract/documented; actual manifests not inventoried |
| Prediction artifact | Exporter writes configured JSON artifact; README default is `.data/freqai-prediction.json` | Derived/ephemeral output | Source-defined; actual artifact presence unknown |
| Model and experiment artifacts | Freqtrade/FreqAI workflow and config reference model/training paths | Derived/model evidence | Exact runtime path, versions, and retention unknown |

**T2 integration correction:** current source files `freqai_bridge/context.py` and `ChartProFreqaiResearch.py` use the HTTP candle client. The earlier T0 read-only contract document still contains a stale section claiming T2 directly reads SQLite and needs migration. Later T2 migration evidence records that the HTTP context migration and direct-SQLite-removal acceptance passed at its recorded source SHA. The live T0 endpoint, remote TLS, and deployed environment remain NOT VERIFIED. This inventory does not run the migration tests again.

### 3.4 Paper strategy/account state

| Item | Static evidence | Classification | Confidence / limitation |
|---|---|---|---|
| Strategy ledgers | `paper_execution/ledger.py` contains queries for `paper_strategy_ledgers` and strategy state | Operational paper state | Code-defined; live DB/path unknown |
| Account/risk state | Queries include `paper_accounts`, `paper_account_risk_state`, `paper_account_equity_cutovers`, `paper_account_config` | Operational risk state | Code-defined; deployed schema/state unknown |
| Reservations and book liquidity | Queries include `paper_risk_reservations`, `paper_book_level_reservations`, `paper_legacy_book_consumptions`, `paper_books` | Operational reservation state | Code-defined; live records unknown |
| Orders and audit | Queries include `paper_orders`, `paper_audit`, `paper_account_event_journal` | Operational/evidence state | Code-defined; actual journal completeness unknown |
| Equity/funding | Queries include `paper_equity_history`, `paper_funding_coverage`, `paper_funding_events`, `paper_account_adjustments`, `paper_execution.daily_baseline` | Financial reconstruction evidence | Code-defined; coverage and completeness unknown |

The Dual Ledger Contract defines independent `CORE_LEDGER` and `AI_LEDGER` domains with a shared account risk boundary. This database is not T0 market storage and must not be treated as a disposable cache.

The existence of query/schema references in source is not proof that a persistent paper database is initialized or that all migrations/acceptance gates are complete. The actual configured database path, row counts, current migration version, and runtime status remain unknown.

### 3.5 Evidence and governance artifacts

| Item | Repository evidence | Classification | Lifecycle note |
|---|---|---|---|
| P1.8 synthetic evidence bundles | Committed ZIPs, hashes, attestations, trust-root snapshots under `docs/evidence/p1-8/` | Test/synthetic evidence | Not account events or production market data |
| GitHub Actions artifacts | Workflow evidence documents record test artifact IDs/digests | CI evidence | Not an account event store or runtime database |
| Forward execution evidence design | `FORWARD_EVIDENCE_CAPTURE_RETENTION_PROTOCOL_2026-11-07.md` | Design-only | Explicitly proposed/not implemented |
| Dataset manifests and lineage | Defined across architecture contracts and importer outputs | Evidence/metadata | Actual complete system registry is not present/verified |
| Lifecycle policy/consumer/deletion records | New design documents only | Governance design | No central registry or lifecycle engine implementation is established |

The forward evidence proposal explicitly distinguishes mutable trading database state from independent evidence storage and says GitHub source control/CI artifacts are not account event storage. Its proposed Root A/Root B implementation is not activated by this inventory.

### 3.6 T4 and presentation/read models

A complete current T4 dataset/store inventory cannot be established from the reviewed evidence. The architecture assigns T4 read models and presentation caches as derived/read-only outputs, but this is a target responsibility map. No current authoritative T4 store, production consumer registry, or deployed lifecycle boundary is verified here.

Legacy UI/dashboard files in the repository must not be assumed to be the canonical T4 implementation or to own source datasets.

## 4. Consumer and dependency map (static)

| Consumer | Source dataset | Expected boundary | Current evidence status |
|---|---|---|---|
| T0 validation/recovery | T0 candle and source metadata | Producer-internal scoped reads | Logical target; actual dependency records unknown |
| T1 importer/intelligence | Collector CSV observations | Versioned input hashes and bounded snapshot | Importer source exists; actual CSV/snapshot inventory unknown |
| T2 FreqAI | T0 candles | Read-only HTTP Candle Contract v1 | Source integration and historical CI evidence; live endpoint NOT VERIFIED |
| Paper strategy/risk | T0/T1 context, strategy/model inputs, book/funding observations | Exact input snapshot/provenance and paper account boundary | Source/contract evidence; active dependency records unknown |
| T4 read models | Approved T0–T3 status and datasets | Read-only views | Target architecture only; deployed map unknown |
| Research/backtest | Exact market windows and model/strategy versions | Reproducible pinned versions | Contract intent; actual inventory of retained windows/artifacts unknown |

No consumer dependency registry is present or verified. The table records expected/observed code relationships, not registered dependency records.

## 5. Storage and copy inventory gaps

The following are not discoverable with sufficient confidence from static source inspection:

- current VPS files, mounts, volume identities, sizes, and exact dataset coverage;
- whether SQLite or PostgreSQL is currently the canonical T0 backend;
- all SQLite files and database paths used by paper execution or research;
- all active T1 CSV inputs, JSON snapshots, sidecar JSONL files, and manifests;
- all FreqAI/Freqtrade model, training, cache, and prediction artifacts;
- all T3/T4 stores, exports, read models, and UI caches;
- replicas, snapshots, backups, object-store versions, local copies, and external exports;
- exact dataset/version dependencies for each running consumer;
- current owner/steward, classification, sensitivity, holds, and recovery obligations for every deployed dataset;
- proof that any dataset is safely rebuildable or restorable.

Unknown copies and unknown dependencies must remain protected. Absence from GitHub source is not evidence that a runtime copy does not exist.

## 6. Data classification baseline — provisional

| Dataset group | Provisional class | Default lifecycle stance |
|---|---|---|
| T0 candles | Canonical | Protect; no deletion decision |
| T0 instruments/quality/provenance | Canonical metadata/evidence | Protect until dependencies and audit needs are inventoried |
| T0 lease/runtime control state | Operational ephemeral/control metadata | Separate lifecycle from market payload; no cleanup rule approved |
| T1 collector CSV observations | Raw source observations | Demand/lineage review required; do not assume expendable after import |
| T1 JSON intelligence snapshot | Derived observed dataset | Preserve source file hashes, coverage, source commit, and snapshot identity |
| T1 connection sidecar + manifest | Evidence | Preserve integrity and session/source provenance |
| T2 training/model/experiment provenance | Model/reproducibility evidence | Preserve exact input and transformation identities |
| T2 prediction artifact | Derived/ephemeral candidate | Not disposable until downstream signal/risk consumers and reproducibility needs are known |
| Paper ledger/orders/risk reservations/event journal | Operational state + decision evidence | Treat as protected; never classify as cache |
| Synthetic CI evidence | Test evidence | Govern separately from production/account evidence |
| T4 read models/cache | Derived/ephemeral candidate | Rebuildability and downstream dependency proof required |

These are provisional functional classes. Sensitivity labels, retention floors, numeric durations, archive tiers, and deletion permissions are not assigned.

## 7. Findings and blockers

1. **No authoritative runtime inventory.** Source reveals data structures and configured paths, not the live contents of VPS storage.
2. **No central consumer registry.** Dependencies are architectural concepts; active registrations are not present/verified.
3. **No full copy inventory.** Backups, replicas, exports, and local copies are unknown.
4. **T1 sidecar is not operationally integrated.** The Rust reference writer exists, but upstream collector integration is explicitly not complete in the recorded evidence.
5. **T2 documentation drift.** The old T0 read-only contract still states direct SQLite use, while later source and T2 evidence record migration to HTTP. That contract document needs a documentation-only status correction with exact superseding evidence references.
6. **Paper evidence archive gap.** Forward evidence capture remains proposal-only; GitHub artifacts and mutable ledger storage cannot be assumed to provide independent long-term evidence retention.
7. **T4 actual dataset map unavailable.** The target architecture exists, but current authoritative stores/consumers are not established.

## 8. Required next evidence phase — read-only only

Before assigning retention values, a separately approved read-only inventory capture should record:

- exact VPS source checkout SHA and timestamp;
- exact paths and metadata for configured databases/artifacts, without opening or modifying databases unless a separate read-only procedure is approved;
- database provider identity, schema/migration version, table/object names, sizes, and coverage metadata;
- dataset ID/version/digest and producer/steward where available;
- consumer/job identities, exact version references, and purpose;
- backup/replica/export inventory and restore evidence;
- lineage/rebuildability and unresolved holds;
- source/evidence freshness and provenance limitations.

This is a proposal for a future evidence-gathering step, not permission to connect to the VPS or inspect storage now. User authorization is required before any remote inspection. No exchange/network probe, sync, collector run, database open/query, or runtime action is implied.

## 9. Acceptance and status

- [x] Static repository source and documentation inventory completed for T0, T1, T2, paper state, and evidence domains.
- [x] Source-defined objects distinguished from historical runtime evidence and design-only proposals.
- [x] Unknown runtime presence, copies, consumers, and dependencies explicitly marked NOT VERIFIED.
- [x] No numeric retention period or cleanup policy assigned.
- [x] No database, VPS, exchange, collector, or runtime accessed.
- [x] No source/schema/API/workflow/runtime or data lifecycle operation changed.

**Status: STATIC INVENTORY BASELINE COMPLETE — RUNTIME INVENTORY NOT VERIFIED — NO LIFECYCLE ACTION AUTHORIZED.**

Next: documentation-only correction of the stale T0 Read-only Candle Contract v1 status text, then seek explicit approval before any read-only VPS/storage inventory. Do not proceed to retention values, archive, vacuum, cleanup, or deletion based only on this static baseline.
