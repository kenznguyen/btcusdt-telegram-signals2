# ADR-001 — Production Backup Manifest Contract and Recovery Boundary

## Status

**PARTIALLY ACCEPTED — D1 host/physical topology; D2–D7 architecture contracts ACCEPTED.** The owner has accepted Android-hosted SQLite as canonical T0 storage, one shared physical SQLite file for Market Data plus Paper Ledger, all D2 decisions, D3.1–D3.6 and supplements A–E, D4.1–D4.7, D5.1–D5.4, D6.1–D6.7 and D7.1–D7.6. Implementation and operational authorization remain separate. This ADR does not authorize production backup/restore, canonical database creation/opening, Feeder activation, exchange connectivity or writer activation.

## Date

2026-11-03

## Current consolidated decision index — P5.4.79 (2026-11-04)

This index is authoritative for the current owner-decision status. Earlier sections below preserve the status as it was recorded at their original dates; any older "PROPOSED", "NOT DECIDED" or "pending" statements are historical snapshots and are superseded by the later decision records listed here. Do not interpret those historical statements as current status.

| Contract | Current owner status | Boundary |
|---|---|---|
| D1 — Android canonical host/shared SQLite topology | PARTIALLY ACCEPTED | Exact Android DB path, stable identity and writer composition remain open |
| D2.1–D2.5 — cursor/ledger/risk/lease vector | APPROVED | Architecture only |
| D3.1–D3.6 + supplements A–E — snapshot barrier | APPROVED | Architecture only |
| D4.1–D4.7 — schema migration authority | APPROVED | DDL/runtime/lock/reconciliation details open |
| D5.1–D5.4 — digest layers | APPROVED | Canonical envelope/runtime/introspection details open |
| D6.1–D6.7 — restore epoch/fencing/Kill Switch | APPROVED | External authority and runtime protocol details open |
| D7.1–D7.6 — backup security/retention/RPO/RTO/authorization | APPROVED | Provider, key custody, retention values, numerical RPO/RTO and approver roles unselected |

**Cross-contract review:** `docs/evidence/P5.4.79-D2-D7-CROSS-CONTRACT-CONSISTENCY-AND-FIXTURE-PLAN-2026-11-04.md`. Digest-domain clarification proposal: `docs/evidence/P5.4.80-DIGEST-DOMAINS-AND-AUTHENTICATED-BACKUP-MANIFEST-PROPOSAL-2026-11-04.md` (**PROPOSED / NOT APPROVED**).
Architecture is coherent with explicit open design blockers. P5.4.80 proposes separate SHA-256 domains for the verified pre-encryption SQLite snapshot image and the encrypted destination object, with an authenticated manifest binding both; this clarification is pending owner approval and does not amend D5/D7 decisions.

**Current verification state:** fixture acceptance tests are specified in P5.4.79 (60 cases) but NOT IMPLEMENTED / NOT RUN. GitHub Actions NOT RUN for P5.4.79. Production implementation remains BLOCKED. No canonical DB/device/PC/production storage/key material/Feeder/exchange/backup/restore/writer was accessed. Keep `AI_EXECUTION_ENABLED=false`; paper-only.

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

**Owner-confirmed topology:** Android-hosted SQLite is canonical, and **Market Data plus Paper Ledger use one shared physical SQLite database file**. This supersedes both the prior PC-hosted T0 wording and the unaccepted proposal to split the two domains into separate SQLite files. PC remains a separate compute/backtest environment and is not the T0 canonical writer by this decision.

**Still open:** the exact canonical Android filesystem path; the exact tables/domain ownership and transaction boundaries within the shared file; Feeder lease placement and fencing ownership; backup destination/cadence/security policy. PostgreSQL remains an opt-in/experimental adapter, not the selected T0 canonical backend.

Candidate manifest identity should name a logical role (for example, `market_data` or `paper_ledger`), backend type, stable opaque store ID and schema authority. It must not expose credentials or raw DSNs/absolute paths.

**Decided:** one Android-hosted SQLite file shared by Market Data and Paper Ledger.

**Not decided:** canonical Android path, exact schema/domain ownership and transaction boundaries, lease placement, stable store ID, backup destination/cadence, encryption and retention policy.

### D2 — Per-store high-water semantics

Candidate requirements:

- **Market data:** identify each exchange/market/symbol/timeframe partition. Record a validated contiguous closed-candle cursor, expected interval/range, gap status and a deterministic partition digest. A maximum timestamp alone is insufficient when earlier gaps exist.
- **Paper ledger:** identify a monotonic transaction/audit cursor only if every state-changing write is proven to advance it atomically with the affected state. `paper_audit.id` is a candidate to investigate, not an accepted cursor contract.
- **Feeder lease:** record lease name, generation and ownership/fencing evidence separately from market-data cursor state. A restored generation must not authorize an old owner.
- **Risk and paper state:** bind state rows to the same database snapshot and recovery epoch; do not derive a cursor from table row counts.

**OWNER-APPROVED (2026-11-04):** All five D2 decisions are approved:
1. Market Data uses a per-partition contiguous closed-candle cursor; gap/backfill coverage is recorded separately.
2. Paper Ledger uses a dedicated monotonic commit sequence with a stable idempotency key and same-transaction advancement of affected state and audit. `paper_audit.id` alone is not accepted as the cursor.
3. Risk State changes in the same transaction are bound to the corresponding Ledger sequence; independently committed risk-only transitions require their own monotonic risk version committed with the risk mutation and audit.
4. Feeder Lease generation remains separate from data cursors; the canonical host validates fencing generation at every canonical write boundary.
5. The D2 manifest evidence is a vector of domain cursors/evidence. It is descriptive only and does not prove atomic snapshot consistency; D3 remains required.

**Still to specify before implementation:** exact partition enum/canonical identity fields, cursor schema and retention, sequence allocation/storage details, full mutation-coverage proof, independent risk-only transition contract, lease authority/location and generation persistence. Approval of D2 semantics does not approve schema/migration/runtime implementation or operational activation.

### D3 — Global snapshot barrier and cross-domain consistency

**OWNER-APPROVED (2026-11-04):** The owner explicitly approved D3.1–D3.6 and all supplemental conditions A–E, with no additional notes. The full decision record and fixture-only acceptance plan are in `docs/evidence/P5.4.70-D3-SNAPSHOT-BARRIER-CROSS-DOMAIN-CONSISTENCY-PROPOSAL-2026-11-04.md`.

Approved contract:

1. **D3.1 — Host-owned barrier and drain:** One regular Android Canonical Host-owned write barrier covers every included canonical mutation domain. Close admission to new writes and drain all admitted transactions. Timeout or uncertain transaction outcome aborts snapshot establishment.
2. **D3.2 — SQLite capture method:** Use one SQLite read snapshot plus SQLite Online Backup API (or documented platform-supported equivalent). Do not copy only the main DB file or independently copy DB/WAL/SHM.
3. **D3.3 — Same-snapshot evidence:** Capture the complete D2 evidence vector and manifest metadata from the same SQLite read transaction. Timestamps are diagnostic only, not ordering authority.
4. **D3.4 — Staging and publication:** Capture into staging, verify integrity and domain invariants, then atomically publish the immutable backup and manifest. No manifest may reference partial or unverified output.
5. **D3.5 — Fail-closed recovery:** Stale fencing, unknown transaction outcome, process death while barrier is held, backup/verification/publication failure or uncertain barrier release fail closed. Writers remain blocked until safe ownership and recovery reconciliation are proven.
6. **D3.6 — Consistency boundary:** D3 covers the shared SQLite file only. External lease authority, restore epoch, Kill Switch/recovery latch, app configuration and exchange state are not claimed as part of this snapshot.

Approved supplemental conditions:
- **A — Barrier duration:** Minimize write-pause duration and measure admission wait/capture duration. Never reopen writers automatically after timeout or uncertain state.
- **B — Immutable backup identity:** Record unique Backup ID, Barrier ID, source database identity, D2 vector, physical SHA-256, verification result and completion state. Filename/timestamp alone is not identity.
- **C — Preserve last known-good backup:** Do not replace/delete the selected verified backup until the new backup is fully verified and published.
- **D — Layered verification:** SQLite integrity check is necessary but insufficient. Also verify foreign-key/domain invariants, Ledger sequence/audit consistency, Risk State↔Ledger sequence, Market Data cursor↔gap/backfill and isolated-copy openability. Verification must not invoke repair/constructor paths.
- **E — Snapshot is not restore proof:** D3 establishes snapshot validity only. Successful restore is not claimed; restore/recovery proof remains under D6/D7 and separate authorization.

**Consistency guarantee:** the intended contract is one point-in-time snapshot of the shared SQLite file, including all included Market Data, Paper Ledger, Risk State and audit state. WAL-backed committed state must be captured through the supported SQLite backup mechanism. The D2 vector must be read from the same read snapshot.

**Not decided / implementation details remain open:** exact SQLite API and runtime version; Android wrapper and connection lifecycle; barrier marker/control-record storage; maximum pause duration and availability objectives; staging/publication mechanism; interrupted-process reconciliation implementation. D4 schema authority, D5 canonicalization, D6 external restore epoch/lease re-fencing/Kill Switch gate and D7 backup destination/security/retention/RPO/RTO remain separate unresolved decisions.

**Fixture-only acceptance plan:** 20 scenarios are specified in P5.4.70. They are not implemented or executed by this owner-decision update. No workflow or test result is claimed.

**Decision boundary:** D3 is ACCEPTED as an architecture contract only. It does not authorize code, schema, migration, IPC or runtime implementation; canonical DB access; Feeder startup; exchange connectivity; market-data synchronization; backup/restore execution; writer activation or live execution. Keep `AI_EXECUTION_ENABLED=false`; paper-only.

### D4 — Schema-version authority

**PROPOSED — OWNER DECISION REQUIRED (P5.4.71, 2026-11-04).** Full design and source-grounded review: `docs/evidence/P5.4.71-D4-SQLITE-SCHEMA-VERSION-AUTHORITY-PROPOSAL-2026-11-04.md`. No D4 approval is inferred.

Proposed contract for the owner-selected single shared Android SQLite file:

1. **One database-wide migration authority:** one `schema_migrations` registry governs all schema changes across Market Data, Paper Ledger, Risk State and shared tables. No independent module registries may define competing global schema versions.
2. **Immutable migration identity:** each migration has a unique immutable ID, strictly increasing sequence, owner domain and SHA-256 of exact migration bytes. Applied IDs/checksums/order are append-only; a correction is a new forward migration.
3. **Atomic application:** schema DDL and its registry row commit in the same SQLite transaction through an explicit canonical-host maintenance operation. No constructor, read, ordinary write or startup health check migrates implicitly.
4. **Authority over `PRAGMA user_version`:** the registry is authoritative. `user_version` may be a same-transaction compatibility mirror only; otherwise it is diagnostic and cannot establish schema version. A mismatch is never silently repaired.
5. **Legacy adoption:** an existing database without accepted registry evidence is `LEGACY / UNVERSIONED`. Adoption requires read-only schema/data inventory and a separately approved baseline; no inferred version, auto-stamping or repair.
6. **Read-only verification:** inspect an existing database without constructors/ensure helpers or writes. Missing registry, unknown migration, checksum/sequence mismatch, schema drift or uncertain migration outcome fails closed and blocks dependent writers/snapshot acceptance.
7. **D3 integration:** the same-read-transaction snapshot manifest records the migration authority identity and exact applied migration-chain evidence. Physical digest and migration-chain evidence are complementary, not interchangeable.

**Source observations (reviewed, not runtime-tested):**
- `market_data/store.py` blob `b28601aed70097afcb7a4eea2dd93ed163ae1cec`: explicit SQLite candle table creation, no SQLite migration registry in that file.
- `paper_execution/ledger.py` blob `68209ce48a6e5e9a995f93167684133e41cc7f55`: constructor creates/ensures Paper Ledger tables/indexes and seeds legacy state; this is not a formal versioned migration authority.
- `market_data/migrations.py` blob `5ff71e3ffa9e7c14d26d09f3881313bbbdc3bef0`: migration ID/checksum registry exists for PostgreSQL only; it does not govern Android SQLite.
- `market_data/storage.py` blob `99b66a4d183b8664f28d6638d8d87416d32847c9`: SQLite adapter is the default for that module and PostgreSQL is opt-in; no shared SQLite schema registry is established by this facade.

**Still open even if the proposal is approved:** exact registry DDL and migration naming/packaging; SQLite runtime/API version and transactional DDL proof; lock/busy/timeout behavior; legacy baseline adoption procedure; reader/app compatibility metadata; schema-drift canonicalization shared with D5; interruption and ambiguous-commit reconciliation.

**Fixture-only acceptance plan:** 20 cases are specified in P5.4.71 and are NOT IMPLEMENTED / NOT RUN. No GitHub Actions run or artifact is claimed.

**Decision boundary:** D4 remains PROPOSED / NOT APPROVED. This proposal does not authorize code/schema/migration implementation, canonical DB access, Android device access, Feeder activation, exchange connectivity, synchronization, backup/restore or writer activation. Keep `AI_EXECUTION_ENABLED=false`; paper-only.

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
- **Limitations:** this only applies to state truly stored in that database; external configs, lease owners, exchange inputs and control-plane latches remain outside it. WAL and writer-barrier handling still need proof.
- **Status:** **SELECTED by owner for T0 Android storage topology.** This selects the physical file topology only; it does not approve production backup/restore implementation or prove snapshot consistency.

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
- D2–D7 architecture decisions are owner-approved; unresolved implementation and operational details remain production blockers. Use the current consolidated decision index above, not historical pending-status text below.
- Fixture-only CI may continue with additional negative tests, but must not imply operational readiness.
- No production DB access, canonical path probing, Android filesystem access, Feeder startup, exchange connection, restore or writer activation is authorized by this ADR.

## Acceptance gate for a future production design

Before implementation, obtain explicit approval for:
- [ ] canonical store topology and stable store identities;
- [x] D2 domain-specific high-water/cursor semantics (owner-approved 2026-11-04);
- [x] D3 global barrier and shared-file consistency model (owner-approved 2026-11-04);
- [x] D4 database-wide SQLite schema-version authority and migration ownership (D4.1–D4.7 owner-approved 2026-11-04; implementation details remain open);
- [x] canonicalization and digest-layer contract (D5.1–D5.4 owner-approved 2026-11-04; exact serialization/runtime specification and fixture proof remain open);
- [x] external restore epoch, lease re-fencing and Kill Switch recovery gate (D6.1–D6.7 owner-approved 2026-11-04; concrete authority and runtime protocols remain open);
- [x] D7 backup destination/security/retention/RPO/RTO/restore-authorization policy (D7.1–D7.6 owner-approved 2026-11-04; operational values and provider remain unselected).

Until all are resolved, production implementation status is **BLOCKED**.


## Clarification — T0 host decision (2026-11-03)

The owner confirmed: **T0 uses Android-hosted SQLite, with Market Data and Paper Ledger in one shared physical SQLite file.** This supersedes the earlier PC-hosted T0 statement and the unaccepted split-file proposal. The decision does not establish an exact Android path or lease location, and does not approve production backup/restore or runtime activation.


## Clarification — shared SQLite topology decision (2026-11-03)

The owner explicitly selected **one shared SQLite database file on Android** for both T0 Market Data and Paper Ledger. This is now the accepted D1 physical-file topology. The exact canonical Android path, schema/domain boundaries, lease placement/fencing, backup destination/security/retention and production recovery controls remain unresolved. Production implementation remains blocked pending the remaining D1 details and D2–D7 approvals.


## Owner decision — D2 high-water semantics (2026-11-04)

The owner explicitly approved all five D2 decisions in the project conversation on 2026-11-04 (Asia/Ho_Chi_Minh), with no additional notes:

- **D2.1 APPROVED:** Market Data cursor is contiguous, closed-candle and partition-scoped; gaps/backfill are represented separately.
- **D2.2 APPROVED:** Paper Ledger has a dedicated monotonic commit sequence, stable idempotency and atomic state/audit advancement. `paper_audit.id` alone is insufficient.
- **D2.3 APPROVED:** Same-transaction Risk State changes bind to the Ledger sequence; independent risk-only commits require a separate monotonic risk version and audit.
- **D2.4 APPROVED:** Lease generation is independent from data cursors; host-side fencing is checked on every canonical write.
- **D2.5 APPROVED:** Manifest carries a domain-cursor evidence vector. It is not proof of atomic snapshot consistency; D3 must define the barrier/consistency contract.

**Decision boundary (historical D2/D3 record, reconciled 2026-11-04):** D2 and D3 are ACCEPTED. D4.1–D4.7 are now ACCEPTED by explicit owner decision recorded below. D5–D7 remain NOT DECIDED. Exact implementation fields, schemas, migration runner details, transaction boundaries, lease authority and operational policy remain open where stated above. D2/D3/D4 architecture approval does not authorize code/runtime implementation, canonical DB access, Feeder activation, exchange connectivity, synchronization, backup/restore, writer activation or live execution. Keep `AI_EXECUTION_ENABLED=false`; paper-only.


## Owner decision — D4 SQLite schema-version authority (2026-11-04)

The owner explicitly approved D4.1–D4.7 as specified in `docs/evidence/P5.4.71-D4-SQLITE-SCHEMA-VERSION-AUTHORITY-PROPOSAL-2026-11-04.md`, without amendments. The approved contract establishes one database-wide SQLite `schema_migrations` authority; immutable migration IDs, ordered sequence, owner domain and exact-byte SHA-256; atomic DDL and registry advancement; registry authority with `PRAGMA user_version` optional mirror/diagnostic only; explicit read-only legacy inventory and separately approved baseline adoption; read-only fail-closed verification; and D3 same-snapshot migration-chain evidence.

**Decision boundary:** D4 architecture is ACCEPTED. Exact DDL, packaging, SQLite runtime/transaction/lock contract, schema canonicalization, reader compatibility, timeout and interruption recovery remain implementation/design work. This approval does not authorize code or schema implementation, migration execution, canonical DB access, Android device access, Feeder startup, exchange connectivity, data synchronization, backup/restore, writer activation or live execution. Fixture tests remain NOT IMPLEMENTED / NOT RUN. D5–D7 remain unresolved. Keep `AI_EXECUTION_ENABLED=false`; paper-only.


## D5 proposal reference (2026-11-04)

P5.4.73 proposes the canonicalization and digest layers for owner review: physical snapshot digest, D4 migration-chain digest, logical schema digest, and a separately optional logical row/data digest. It proposes SHA-256, a versioned deterministic envelope, conservative SQLite schema SQL byte identity plus structured introspection, runtime identity recording, no initial cross-backend equivalence claim, and fail-closed handling. This is **PROPOSED / NOT APPROVED**; it does not alter the accepted D4 contract or authorize implementation.


## Owner decision — D5 canonicalization and digest layers (2026-11-04)

The owner explicitly approved D5.1–D5.4 as specified in `docs/evidence/P5.4.73-D5-CANONICALIZATION-AND-DIGEST-RULES-PROPOSAL-2026-11-04.md`, without amendments. Accepted layers: exact-byte physical snapshot SHA-256; ordered D4 migration-chain digest; versioned logical SQLite schema digest using conservative schema SQL bytes plus structured introspection and recorded runtime identity; and optional logical row/data digest excluded from initial mandatory scope. The accepted contract also prohibits initial SQLite/PostgreSQL equivalence claims, requires explicit algorithm/canonicalization identity, and fails closed on unknown or ambiguous inputs.

**Decision boundary:** D5 architecture is ACCEPTED. Exact canonical envelope grammar/framing, canonicalization identifier/version value, runtime pinning, introspection schema, virtual-table inventory and digest composition remain to be specified and covered by disposable fixture tests. No code implementation, canonical DB access, migration execution, Android device access, Feeder startup, exchange connectivity, synchronization, backup/restore, writer activation or live execution is authorized. D5 fixture tests remain NOT IMPLEMENTED / NOT RUN. D6–D7 remain unresolved. Keep `AI_EXECUTION_ENABLED=false`; paper-only.


## D6 proposal reference (2026-11-04)

P5.4.75 proposes an external monotonic Restore Epoch Authority, external Recovery Latch, positive proof that prior owners stopped/fenced, isolated staging and verified publication, lease-generation re-fencing above restored/external floors, invalidation of stale intents/capabilities/market assumptions, and Kill Switch retention through readiness checks and separate authenticated acknowledgement. D6 is **PROPOSED / NOT APPROVED**; no restore or writer operation is authorized.


## Owner decision — D6 restore epoch and recovery fencing (2026-11-04)

The owner explicitly approved D6.1–D6.7 as specified in `docs/evidence/P5.4.75-D6-RESTORE-EPOCH-LEASE-REFENCING-KILL-SWITCH-PROPOSAL-2026-11-04.md`, without amendments. The accepted architecture requires external monotonic restore-epoch and recovery-latch authorities; proof that prior owners are stopped/fenced; idempotent irreversible epoch allocation; isolated staging and verified publication; lease re-fencing above restored and externally issued generations; invalidation of stale intents/capabilities/market assumptions; Kill Switch retention through readiness and separate authenticated acknowledgement; separate latch release, Kill Switch clearing and writer admission decisions; and fail-closed recovery.

**Decision boundary:** D6 architecture is ACCEPTED. Concrete authority implementation, stop-proof protocol, epoch API, publication mechanism, lease encoding, invalidation inventory, acknowledgement role/credentials, audit store and retry state machine remain open. This approval does not authorize restore, epoch allocation, lease mutation, Kill Switch clearing, canonical DB access, device access, Feeder/exchange/sync operations or writer activation. D6 fixture tests remain NOT IMPLEMENTED / NOT RUN. D7 remains unresolved. Keep `AI_EXECUTION_ENABLED=false`; paper-only.


## D7 proposal reference (2026-11-04)

P5.4.77 proposes separate canonical/staging/published-backup/recovery-audit trust boundaries; independent immutable destination with authenticated manifest and read-back verification; authenticated encryption and separate auditable key custody; protected last-known-good retention and deletion controls; explicit measurable RPO/RTO values; and authenticated restore authorization with separate readiness, latch, Kill Switch and writer gates. D7 is **ACCEPTED (architecture/policy only)**. Destination/provider, key custody, retention schedule, numerical RPO/RTO and approver roles remain unselected. No backup or restore operation is authorized.


## D7 owner decision record — P5.4.78 (2026-11-04)

**Status: ACCEPTED (architecture/policy only).** The owner approved D7.1–D7.6 exactly as proposed in `docs/evidence/P5.4.77-D7-BACKUP-SECURITY-RETENTION-RPO-RTO-RESTORE-AUTHORIZATION-PROPOSAL-2026-11-04.md`, without amendments. The accepted contract requires independent backup trust boundaries, authenticated immutable backup publication with read-back verification, encryption and separate auditable key custody, protected last-known-good retention, explicit measurable RPO/RTO targets, and authenticated restore approval with independent readiness/latch/Kill Switch/writer gates. Destination/provider, cryptographic suite/key custody, retention values, numerical RPO/RTO, approver roles and cost remain unselected. This decision does not authorize production backup/restore or runtime changes.


## P5.4.80 — Digest domains and authenticated manifest proposal (2026-11-04)

P5.4.80 proposes distinct `snapshot_image_sha256` (exact SQLite backup image bytes before encryption) and `encrypted_object_sha256` (exact encrypted payload bytes independently verified by full destination read-back). An authenticated versioned manifest binds both digests, lengths, Backup ID, immutable object ID/version and D2–D5 evidence. Payload and manifest are separate logical immutable objects; only their fully verified pair becomes AVAILABLE. Restore order: authenticate manifest → verify encrypted object → decrypt → verify snapshot image → D2/D3/D4/D5/domain checks → D6 restore staging/gates. Sixteen additional fixture cases are proposed.

**Status: PROPOSED / NOT APPROVED.** Cryptographic suite, manifest authentication mechanism/encoding, key custody and storage provider remain unselected. No implementation, key provisioning, storage provisioning or backup/restore is authorized.


## P5.4.80 owner decision — digest domains and authenticated manifest (2026-11-04)

**Status: ACCEPTED (architecture/contract only).** The owner explicitly approved P5.4.80 D1–D5 without amendments. The accepted contract distinguishes `snapshot_image_sha256` over exact verified SQLite snapshot-image bytes before encryption from `encrypted_object_sha256` over exact encrypted payload bytes independently verified by complete destination read-back. An authenticated versioned manifest binds both digest domains and lengths, Backup ID, immutable payload object ID/version and D2–D5 evidence. Payload and manifest are separate logical immutable objects; only the fully durable and verified pair may become AVAILABLE. Restore verification order is manifest authentication → encrypted object identity/digest/length → decryption → snapshot-image digest → D2/D3/D4/D5 and domain verification → D6 isolated staging and separate authorization/fencing gates. Sixteen fixture acceptance cases are accepted into the plan.

**Decision boundary:** P5.4.80 approval is an architecture/contract clarification only. It does not select cryptographic algorithms, signature/MAC mechanism or canonical encoding, key custody/escrow/rotation, storage provider, object-store atomicity implementation, retention values or numerical RPO/RTO. Those remain open. It does not authorize implementation, fixture execution, key or storage provisioning, canonical DB access, production backup/restore, Kill Switch/latch changes or writer activation. Keep `AI_EXECUTION_ENABLED=false`; paper-only.


## P5.4.81 — Cryptographic profile and key lifecycle proposal (2026-11-04)

P5.4.81 proposes AES-256-GCM envelope encryption with a unique random 256-bit DEK per Backup ID, 96-bit nonce, full 128-bit authentication tag and versioned AAD; Ed25519 signatures over the P5.4.80 canonical manifest using a signing key separate from the payload KEK; external KMS/HSM-managed KEK and signing-key custody; key rotation/revocation/destruction safeguards; strict identity separation; and fail-closed handling. It proposes 20 additional fixture cases (96 total after approval).

**Status: PROPOSED / NOT APPROVED.** No cryptographic suite or key lifecycle is selected until explicit owner approval. Provider support, Android/JVM compatibility, applicable compliance constraints, KMS/HSM vendor, custody jurisdiction, escrow, operational roles and audit integration remain open. This proposal does not authorize key generation/provisioning, code or fixture implementation, production KMS/storage access, backup/restore or runtime changes. CI remains fake-key/fake-storage only. Keep AI_EXECUTION_ENABLED=false; paper-only.


## P5.4.81 owner decision — cryptographic profile and key lifecycle (2026-11-04)

**Status: ACCEPTED (cryptographic architecture/profile only).** The owner approved P5.4.81.1–.5 without amendments. The accepted profile is AES-256-GCM envelope encryption with a unique random 256-bit DEK per Backup ID, 96-bit nonce, full 128-bit authentication tag and versioned AAD; Ed25519 signatures over canonical P5.4.80 manifest bytes using a signing key separate from the payload KEK; separate KEK, DEK and signing-key roles; explicit trusted public-key set; lifecycle, rotation, revocation, destruction and identity-separation safeguards; fail-closed behavior; and 20 additional fixture-only acceptance cases (96 total specified).

**Decision boundary:** KMS/HSM vendor, storage provider, custody jurisdiction, escrow/recovery method, concrete manifest serialization implementation, operational roles and audit integration remain unselected. This approval does not authorize key generation/provisioning, production KMS/HSM or storage access, fixture execution, canonical DB access, backup/restore or runtime changes. Keep CI on fake keys/fake storage only; keep AI_EXECUTION_ENABLED=false and paper-only.


## P5.4.82 — Provider-neutral key custody and recovery (2026-11-04)

**Status: PROPOSED / NOT APPROVED.** See `docs/evidence/P5.4.82-PROVIDER-NEUTRAL-KEY-CUSTODY-AND-RECOVERY-ARCHITECTURE-PROPOSAL-2026-11-04.md`.

The proposal defines logical KMS/HSM adapter boundaries, key inventory metadata, workload identity separation, per-backup DEK lifecycle, KEK/signing-key rotation, break-glass recovery case controls, two-person approval as a proposed default, append-only audit evidence, fail-closed handling and CI fake-provider isolation. It does not select a recovery model, provider, jurisdiction, quorum/roles, audit sink or federation mechanism.

This proposal does not amend approved P5.4.81 and does not authorize implementation, fixture execution, provider selection/provisioning, key generation, production access, canonical DB access, backup/restore or runtime changes. The approved fixture inventory remains 96 specified / NOT IMPLEMENTED / NOT RUN. Keep AI_EXECUTION_ENABLED=false; paper-only.


## P5.4.82A — Key custody open-decision matrix (2026-11-04)

**Status: DECISION SUPPORT ONLY / NOT AN APPROVAL.** See `docs/evidence/P5.4.82A-KEY-CUSTODY-OPEN-DECISION-MATRIX-2026-11-04.md`. The matrix frames ten unresolved decisions (recovery model, quorum/roles, jurisdiction/account ownership, audit sink, KEK rotation, signing-key revocation, workload identity, RPO/RTO, Android/JVM crypto qualification and wrapped-DEK metadata) with options, trade-offs and non-binding discussion defaults. It does not select any option, provider, jurisdiction, policy or implementation. P5.4.82 remains PROPOSED / NOT APPROVED; P5.4.81 remains approved and unchanged. No implementation, fixture execution, provider selection/provisioning or production access authorized.