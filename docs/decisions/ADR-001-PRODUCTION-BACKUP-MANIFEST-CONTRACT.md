# ADR-001 — Production Backup Manifest Contract and Recovery Boundary

## Status

**PROPOSED — NOT ACCEPTED.** This record captures source-grounded facts, required decisions and candidate constraints. It does not select a canonical database topology, authorize production backup/restore, or change runtime behavior.

## Date

2026-11-03

## Context

P5.4.7 through P5.4.19 implemented and validated fixture-only backup behavior. The fixture suite now binds per-store manifest metadata to physical and logical database content. That evidence is not sufficient to define a production recovery contract.

The repository currently has multiple storage patterns:

- SQLite candle storage: `market_data/store.py` creates the `candles` table through explicit `CandleStore.initialize_schema()`. The inspected source does not establish a production SQLite schema-version registry.
- PostgreSQL market-data migrations: `market_data/migrations.py` records `migration_id`, `checksum_sha256` and `applied_at` in `market_data.schema_migrations`. This is a concrete version authority for that PostgreSQL migration path.
- Paper ledger: `paper_execution/ledger.py` creates/ensures `paper_state`, `paper_orders`, `paper_books`, `paper_audit`, `paper_strategy_state` and shared risk/equity tables during `PaperLedger` construction. The inspected source does not establish a formal ledger migration registry.
- The fixture helper uses SQLite `PRAGMA user_version` as a controlled test field. That does not prove production code currently assigns or governs this value.
- `market_data/storage.py` supports SQLite by default and PostgreSQL by explicit configuration. The owner has clarified that T0 runs on Android and Android-hosted SQLite is the canonical T0 storage target. The exact Android filesystem path and whether market data and Paper Ledger share one physical SQLite file remain unresolved.
- The paper risk latch is persisted in the paper ledger database. Restoring that database can roll back its state unless a separate recovery control prevents writers from starting prematurely.

Therefore, a production manifest cannot safely treat a single integer called `schema_version`, a generic row count, or a shared barrier string as sufficient proof of a recoverable cross-store snapshot.

## Source-grounded constraints

1. **No implicit schema repair during verification.** The verifier must inspect an existing database read-only. It must not invoke constructors or helpers that create tables, seed singleton rows or repair missing state.
2. **Physical and logical integrity are separate.** Physical SHA-256 identifies the exact database image. A logical digest identifies a canonical schema/data projection. Both are required; updating a physical hash after a semantic mutation must not make the image acceptable.
3. **Schema version must come from the store's real migration authority.** Fixture `PRAGMA user_version` is not a production schema authority unless production migrations explicitly own and maintain it.
4. **High-water marks are domain-specific.** A sum of table row counts is only a fixture metric. It is not a durable sequence/cursor and must not be presented as one.
5. **A barrier identifier is evidence, not atomicity.** Two independent database snapshots do not become transactionally consistent merely because their manifest entries share a string.
6. **Restore must fail closed.** Missing, unknown, duplicate, mismatched or unrecognized store entries must prevent validation and all writer startup.
7. **Recovery controls cannot be trusted solely from restored state.** Lease fencing, restore epoch and Kill Switch recovery latch require an authority that cannot be rolled back by restoring the same database being protected.

## Decisions required before production implementation

### D1 — Canonical store topology and identity

**Owner-confirmed direction:** T0 runs on **Android**, with **SQLite on Android as the canonical T0 storage target**. Do not use the older PC-hosted T0 wording as the current decision. PC remains a separate compute/backtest environment and is not the T0 canonical writer by this decision.

**Still open:** the exact canonical Android filesystem path; whether Market Data and Paper Ledger share one physical SQLite file or use separate SQLite files; the exact location/ownership of the Feeder lease; and the backup destination/cadence/security policy. The earlier PC + same-store lease + daily-backup note is superseded where it conflicts with Android-first; do not carry its unresolved operational details forward as approved Android settings. PostgreSQL remains an opt-in/experimental adapter, not the selected T0 canonical backend.

Candidate manifest identity should name a logical role (for example, `market_data` or `paper_ledger`), backend type, stable opaque store ID and schema authority. It must not expose credentials or raw DSNs/absolute paths.

**Not decided:** canonical Android path, exact Market Data/Paper Ledger file topology, lease placement, store IDs, backup destination/cadence, encryption and retention policy.

### D2 — Per-store high-water semantics

Candidate requirements:

- **Market data:** identify each exchange/market/symbol/timeframe partition. Record a validated contiguous closed-candle cursor, expected interval/range, gap status and a deterministic partition digest. A maximum timestamp alone is insufficient when earlier gaps exist.
- **Paper ledger:** identify a monotonic transaction/audit cursor only if every state-changing write is proven to advance it atomically with the affected state. `paper_audit.id` is a candidate to investigate, not an accepted cursor contract.
- **Feeder lease:** record lease name, generation and ownership/fencing evidence separately from market-data cursor state. A restored generation must not authorize an old owner.
- **Risk and paper state:** bind state rows to the same database snapshot and recovery epoch; do not derive a cursor from table row counts.

**Not decided:** exact cursor fields, partition keys, monotonicity source, retention behavior or proof that every mutation is represented.

### D3 — Global snapshot barrier and cross-store consistency

A production design must specify:
- how all writers are paused or fenced;
- how the coordinator allocates a globally unique barrier ID;
- how each store proves it captured a snapshot after the barrier and before writers resume;
- how per-store high-water values and transaction boundaries are recorded;
- what recovery does if only a subset of stores reaches the barrier.

A barrier ID alone is not proof of a distributed transaction. If the stores cannot participate in a true distributed snapshot, the system must state the weaker consistency model and define reconciliation/rollback behavior.

**Not decided:** global coordinator, writer pause/fence mechanism, consistency model or failure recovery policy.

### D4 — Schema-version authority

Candidate direction:
- PostgreSQL: use the existing migration ID plus checksum registry, with a stable ordered set of applied migrations.
- SQLite market data and paper ledger: first introduce an explicit, owned migration/version authority or prove that `PRAGMA user_version` is maintained transactionally by every supported migration. Do not infer production version from fixture values.

**Not decided:** migration mechanism for SQLite, ownership, compatibility policy or upgrade/downgrade guarantees.

### D5 — Canonicalization and logical identity

The manifest contract must define deterministic encoding for:
- schema objects and migration identity;
- table/column ordering and SQLite/PostgreSQL type representation;
- row ordering and primary-key identity;
- NULL, bytes, decimals, timestamps, JSON and numeric normalization;
- excluded volatile fields, if any, with an explicit reason.

A canonicalization version must be stored in the manifest so that a future algorithm change cannot silently reinterpret old digests.

**Not decided:** canonicalization format/version, cross-backend equivalence or whether logical hashes are per-table, per-partition and per-store.

### D6 — Restore epoch, lease re-fencing and Kill Switch recovery

Candidate minimum recovery gate:
1. Stop and prove all prior writers/owners stopped.
2. Enter an external maintenance/recovery latch that is not part of the restored snapshot.
3. Allocate a monotonic restore epoch from an authority outside the restored stores.
4. Restore and verify every required store against one accepted manifest/barrier.
5. Re-fence lease generations above every restored generation and invalidate stale intents/book snapshots.
6. Assert the Kill Switch before any writer can start.
7. Require an explicit authorized acknowledgement/readiness check before clearing the external latch or Kill Switch.

**Not decided:** epoch authority, external latch location, owner-stop proof, reset approver and operational recovery procedure.

### D7 — Backup destination, security and service objectives

Still required: destination and ownership, encryption at rest/in transit, key management, retention, immutability, off-host copy, backup frequency, RPO, RTO, restore drills and evidence retention.

**Not decided:** all operational values and approvals.

## Alternatives considered

### One shared SQLite database

- **Potential benefit:** one SQLite Online Backup API snapshot can capture market data and paper state from a single database file.
- **Limitations:** this only applies if all relevant state is truly in that database; external configs, lease owners, exchange inputs and control-plane latches remain outside it. WAL and writer-barrier handling still need proof.
- **Status:** not selected. This remains a viable candidate for Android-hosted SQLite, but has not been approved.

### Split SQLite/PostgreSQL stores

- **Potential benefit:** independently scalable market-data storage and paper ledger.
- **Limitations:** requires a global barrier, per-store cursor contract, failure protocol and explicit statement of cross-store consistency. Separate snapshots are not automatically atomic.
- **Status:** not selected. No cross-backend or split-file topology is approved.

### Manifest-only shared barrier

- **Potential benefit:** easy to serialize and verify.
- **Rejected as a sufficient recovery contract:** metadata equality cannot prove writers were fenced or that snapshots represent one consistent point in time.

## Consequences

- P5.4.18/P5.4.19 fixture results remain valid only for the exact tested fixture behavior.
- Production manifest schema and publisher/consumer must not be implemented by copying the fixture manifest and relabeling its row-count sum as a production cursor.
- The next engineering gate is a reviewed, approved decision for D1–D7. Any unresolved item remains a production blocker.
- Fixture-only CI may continue with additional negative tests, but must not imply operational readiness.
- No production DB access, canonical path probing, Android filesystem access, Feeder startup, exchange connection, restore or writer activation is authorized by this ADR.

## Acceptance gate for a future production design

Before implementation, obtain explicit approval for:
- [ ] canonical store topology and stable store identities;
- [ ] domain-specific monotonic high-water/cursor definitions;
- [ ] global barrier and cross-store consistency model;
- [ ] schema-version authorities and migration ownership;
- [ ] canonicalization version and digest rules;
- [ ] external restore epoch, lease re-fencing and Kill Switch gate;
- [ ] destination, encryption, retention, RPO/RTO and restore approver.

Until all are resolved, production implementation status is **BLOCKED**.


## Clarification — T0 host decision (2026-11-03)

The owner corrected the prior PC-hosted wording: **T0 uses Android; Android-hosted SQLite is the canonical target.** This supersedes the earlier PC-hosted T0 statement. This clarification does not decide whether Market Data and Paper Ledger share one SQLite file, does not establish an exact Android path or lease location, and does not approve production backup/restore or runtime activation.
