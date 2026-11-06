# Forward Evidence Capture & Retention Protocol (2026-11-07)

## Status

**PROPOSAL — DOCUMENTATION ONLY; NOT APPROVED FOR SOURCE, SCHEMA, WORKFLOW, STORAGE, OR RUNTIME IMPLEMENTATION.**

This protocol is prospective. It can preserve evidence for events generated after a separately approved implementation and activation date. It cannot recreate missing historical fills, fees, funding, marks, reservations, HWM, daily baselines, or account state.

Current policy remains Option A (strict predecessor chain). Historical v1 baseline reconstruction remains unavailable/blocked because no independent archive or checkpoint exists. No epoch activation, HWM reset, Daily Loss reset, or risk-increase authorization follows from this document.

Paper-only constraints remain: no exchange connectivity, no live orders, and `ai_execution_enabled=false`. T0 is out of scope and remains paused.

## 1. Objective and assurance boundary

Preserve enough immutable, provenance-bound evidence to:
1. replay each Core, AI, and Legacy ledger deterministically;
2. independently corroborate the replay using a separately captured projection/checkpoint;
3. identify missing, duplicated, late, reordered, or altered events;
4. reproduce account equity, gross exposure, reservations, fees, funding, and risk references at an exact UTC boundary;
5. prove which software, configuration, precision rules, and evidence bytes produced each result.

This is a **paper-system integrity protocol**, not proof of exchange execution or real-world account balances. Since the system must not connect to exchanges or place real orders, no document produced here may be described as exchange-verified.

### 1.1 Evidence independence levels

Use explicit classifications; do not collapse them into one PASS:

- **LEVEL 0 — Mutable-source export:** two exports/replays derived from the same mutable DB. Internal consistency only; never an independent root.
- **LEVEL 1 — Independent retention:** immutable event evidence and a separately stored, independently captured observer checkpoint, with separate process identity, storage namespace, credentials, and write path. This detects later mutation and many projection defects, but both paths may share a common upstream event emitter.
- **LEVEL 2 — Independent source corroboration:** a second authoritative source independently records the economic event. This may be unavailable in the paper-only architecture. Do not claim LEVEL 2 without evidence.

The proposed paper implementation can target LEVEL 1. It must disclose the shared upstream event-emitter trust boundary. A second calculation over the same mutable SQLite rows does not qualify, even if it runs in a separate process.

## 2. Proposed capture topology

Two evidence roots are required, with a third optional manifest/approval record:

### Root A — immutable execution event journal

- Produced at the paper execution state-transition boundary, not reconstructed later by querying current position rows.
- Append-only, sequence-numbered, hash-linked event envelopes.
- Records accepted/rejected intents, risk decisions, order lifecycle, fills/partial fills, DCA, reductions, reversals, reservations, fees, funding, marks, corrections, and kill-switch transitions.
- Durable acknowledgement is required before the corresponding state transition is reported as durably committed.
- Corrections append a superseding event; prior bytes are never overwritten.

### Root B — independent observer projection and checkpoint

- A separate observer process consumes the committed event envelope stream; it must not query the mutable account DB to manufacture a checkpoint.
- Maintains its own projection state using a separately implemented reducer and separate storage namespace.
- Periodically emits immutable checkpoints and a consumed-event watermark, including the last contiguous journal sequence/hash.
- Captures raw event envelopes as received or retains immutable references to Root A segment digests so that its checkpoint can be traced to exact inputs.
- Uses separate service identity/credentials and write permissions. It must not share the writer's DB file, SQLite WAL, mutable tables, or filesystem write credentials.
- If the observer falls behind, detects a sequence/hash gap, or cannot persist a checkpoint, it reports degraded/not-ready; it must never silently skip ahead.

Root B is an independent retention and computation path, not an independent external economic source. Both roots may share the event emitter. That common-mode limitation must appear in every verification report.

### Storage boundary

- Root A and Root B must be retained in separate storage namespaces and separate access-control domains. Prefer separate storage services or accounts where feasible; if only one provider is available, require separate immutable object namespaces, distinct credentials, retention lock, and independent access audit.
- The mutable trading database is not the evidence archive.
- GitHub source control and CI artifacts are not account event storage.
- CI artifacts may carry test evidence only; never write account records, keys, or live runtime state to CI artifacts.
- No storage provider or paid service is selected by this proposal.

## 3. Canonical event envelope

Every captured event must carry the following logical fields. Exact serialization and schema version require a later API/schema design review.

| Field | Requirement |
|---|---|
| `event_id` | Globally unique, immutable ID; idempotency key for duplicate delivery. |
| `account_id` | Stable paper-account identity; never a personal identifier. |
| `ledger_owner` | Exactly CORE_LEDGER, AI_LEDGER, or LEGACY_UNATTRIBUTED. |
| `event_type` | Versioned enumerated type; unknown types fail closed. |
| `schema_version` | Explicit envelope schema version. |
| `event_at_ms` | Economic event time in UTC epoch milliseconds. |
| `recorded_at_ms` | Time the authoritative writer committed/accepted the event. |
| `source_sequence` | Monotonic per-account sequence with no silent reuse. |
| `correlation_id` | Links intent, risk decision, reservation, order, fills, fees, and release. |
| `causation_id` | Identifies the immediate preceding event, where applicable. |
| `instrument` | Exact instrument and market type for price/quantity events. |
| `quote_currency` | Explicit currency for all monetary values. |
| `payload` | Canonical typed fields; decimal values encoded as decimal strings, never binary float JSON. |
| `previous_event_hash` | Hash of the preceding envelope in the same sequence chain. |
| `event_hash` | SHA-256 of the canonical envelope excluding this field. |
| `producer_id` | Writer identity and build/source provenance. |
| `config_digest` | Digest of effective strategy/risk/configuration values relevant to the event. |

Do not include API keys, passwords, signing secrets, personal data, or unnecessary device identifiers.

### 3.1 Required event families

At minimum, capture:
- intent created, validated, rejected, admitted;
- risk snapshot/version and each risk decision, including reason codes;
- exposure reservation created, partially consumed, released, expired;
- order submitted to the paper simulator, accepted, partially filled, filled, canceled, rejected;
- every fill as an individual immutable event;
- position increase, reduction, closure, DCA, and reversal;
- realized PnL, unrealized mark observation, fees, funding, and explicit adjustment;
- kill-switch state changes and readiness transitions;
- daily baseline/HWM candidate, validation, acceptance/rejection, and source references;
- late event, gap detection, replay start/end, observer checkpoint, and correction/supersession.

A requested action is not a fill. An order intent, candle touch, or simulated target price must never be promoted to an executed fill without a corresponding paper-simulator fill event.

### 3.2 Numeric and time rules

- Use decimal strings and declared instrument quantity/price precision.
- Store UTC epoch milliseconds; preserve original source timestamp and timezone metadata if input was not UTC.
- No implicit zero for missing fee/funding/amount. Use explicit status such as UNKNOWN and block dependent verification.
- Same-time events require a source-defined sequence. Database row order or retrieval order is not a tie-breaker.
- Event IDs and source sequence values are immutable. Corrections use new IDs and explicit references to superseded events.

## 4. Durability, ordering, and idempotency

1. Allocate a monotonically increasing account sequence inside the serialized writer transaction.
2. Create a canonical envelope and hash-link it to the prior event.
3. Persist the event to Root A's append-only journal using a durable commit protocol.
4. Only after durable journal acknowledgement may the writer confirm the economic state transition as committed. If the journal is unavailable, fail closed for exposure increases; reductions/closures may follow the existing safety policy but must also be journaled or be reported as not durably evidenced.
5. Deliver the exact committed envelope to Root B using at-least-once delivery.
6. Root B deduplicates by `event_id`, verifies sequence and hash continuity, and commits its projection/checkpoint atomically with its consumed watermark.
7. Re-delivery of an identical event is idempotent. Same ID with different bytes/hash is a critical integrity fault.
8. A gap, chain mismatch, duplicate sequence with different identity, or observer checkpoint mismatch sets evidence readiness false and blocks new exposure.

The exact atomicity boundary between journal commit and mutable ledger state is a major implementation design item. A transactional outbox or equivalent recoverable protocol must be evaluated; a best-effort dual write is not acceptable. This proposal does not choose or implement that mechanism.

## 5. Checkpoint cadence and boundary capture

Proposed defaults for later review, not approved runtime values:

- Continuous event capture for every state transition.
- Observer checkpoint at least every 15 minutes and after each UTC day boundary.
- Additional checkpoint after a material lifecycle event: restart/recovery, kill-switch transition, migration, or account reconciliation.
- At 00:00:00.000 UTC, record a boundary checkpoint with exact event watermark, last event hash, open positions, open orders, remaining quantities, reservations, marks, equity components, fees/funding coverage, HWM and daily baseline references.
- The boundary snapshot must state whether the mark is exact-boundary and source-valid. Never interpolate an unverified mark.
- Events with `event_at_ms < B` contribute to opening state; events with `event_at_ms >= B` belong to the new period, consistent with the Dual Reconstruction contract.
- Late pre-boundary events invalidate the candidate checkpoint and require replay plus a new immutable manifest. Never edit the old checkpoint.

A checkpoint is not an anchor merely because it exists. It becomes a candidate only after Root A/Root B continuity, coverage, provenance, and reconciliation checks pass.

## 6. Immutable package and manifest format

Each sealed evidence package should contain:
- canonical event segment(s) or immutable segment references;
- Root B checkpoint and observer watermark;
- account/ledger identity and quote currency;
- first/last sequence, first/last event IDs, event count;
- coverage interval, gap/overlap/late-event report;
- schema and canonicalization versions;
- producer source SHA and build identity;
- effective config and risk-policy digests;
- instrument precision/rounding metadata;
- mark IDs and dataset digests;
- fee/funding coverage and explicit unknowns;
- previous package/root digest and current Merkle/root digest;
- capture time, seal time, storage object version/retention metadata;
- verification report and its status.

Compute SHA-256 from the exact bytes read back from retained storage, not from a digest copied out of the mutable DB. Verify every component digest and the root manifest after upload and during scheduled audits.

A manifest must not claim completeness when the sequence range contains a gap or when fee/funding/mark coverage is unknown. Store explicit completeness flags and reasons.

## 7. Retention, immutability, and access controls

Proposed minimum controls:
- object versioning plus retention lock/WORM where supported;
- no overwrite/delete permission for the writer or observer identities;
- separate read and write identities for Root A and Root B;
- append-only audit of reads, writes, retention changes, and administrative actions;
- encryption in transit and at rest;
- periodic restore/read-back verification;
- retention period and deletion policy selected only after cost, legal, and operational review;
- no secrets in evidence packages or GitHub commits;
- documented key rotation and recovery without rewriting old evidence;
- alerts for storage unavailability, retention-policy changes, digest mismatch, and observer lag.

A storage administrator who can alter both roots remains a common-mode risk. Record this limitation; do not overstate tamper-proofing.

## 8. Recovery and verification behavior

On startup/recovery:
1. Read the last sealed Root A segment and Root B checkpoint.
2. Verify byte hashes, manifest root, sequence continuity, and schema/canonicalization compatibility.
3. Compare Root B's consumed watermark and last event hash with Root A.
4. Replay only the unconsumed contiguous suffix.
5. Rebuild the observer projection deterministically and compare it with the next checkpoint.
6. If there is any gap, conflicting duplicate, unknown event type, missing monetary amount, late event, invalid hash, or incompatible precision, mark evidence NOT_READY/BLOCKED.
7. Never skip an event or reset sequence to make recovery succeed.
8. A repair is a new immutable correction/recovery record with provenance; never rewrite old evidence.

The existing Shared Risk Engine remains fail-closed. Evidence readiness is an additional prerequisite, not a replacement for equity, exposure, drawdown, daily loss, funding, fee, or Kill Switch checks. Risk reductions/closures retain the existing safety allowance.

## 9. Operational monitoring

Expose read-only evidence health metrics:
- Root A last durable sequence/time/hash;
- Root B last consumed sequence/time/hash;
- observer lag and checkpoint age;
- sequence gap and hash-chain fault counts;
- unsealed segment age;
- last successful read-back verification;
- fee/funding/mark coverage status;
- late-event count;
- storage capacity/availability and retention-lock status;
- evidence readiness state and exact blocking reason.

A green storage heartbeat is not evidence completeness. Health must distinguish storage availability, chain integrity, event coverage, and reconstruction readiness.

## 10. Acceptance tests required before any implementation approval

Design-level test cases:
- duplicate identical event delivery is idempotent;
- same event ID with changed bytes is rejected;
- sequence gap, duplicate sequence, out-of-order event, and hash-chain break block readiness;
- writer crash before journal commit produces no committed economic transition;
- writer crash after journal commit but before ledger update recovers exactly once;
- observer crash before projection/checkpoint commit replays the event once;
- observer crash after commit but before acknowledgement does not double-apply;
- Root A unavailable blocks exposure increases;
- Root B unavailable/lagging blocks independent verification and, per approved policy, new exposure;
- disk full, timeout, permission loss, and retention-lock failure are fail-closed;
- late pre-boundary event invalidates prior candidate;
- unknown fee/funding/mark precision remains UNKNOWN, never zero;
- independent reducer catches deliberately injected projection defects;
- two roots have separate storage identities/credentials and cannot overwrite each other;
- read-back hash verification detects altered/truncated objects;
- restore from retained packages reproduces the same state and digests;
- UTC boundary and exact event ordering are deterministic;
- Core/AI/Legacy ownership isolation and account-level aggregation remain correct;
- no test or recovery path connects to an exchange or emits a live order.

Acceptance must run on exact source SHA in GitHub Actions after implementation is separately approved. Test fixtures and CI artifacts remain test evidence, not account evidence.

## 11. Rollout gates (future, separate approvals)

| Gate | Scope | Required approval |
|---|---|---|
| G0 | Review this protocol and threat model | Architecture approval |
| G1 | Select storage provider, retention, cost, access owners | Storage/security approval |
| G2 | Define event envelope/API and atomic journal/outbox design | Interface + data-integrity approval |
| G3 | Implement Root A in isolated tests only | Source implementation approval |
| G4 | Implement independent Root B reducer/checkpoint in isolated tests | Source implementation approval |
| G5 | Test crash/restart, corruption, contention, restore, and exact-SHA CI | Test acceptance approval |
| G6 | Authorize persistent storage provisioning and controlled paper capture | Explicit persistent-storage/runtime approval |
| G7 | Observe prospective capture and independently verify first complete period | Evidence acceptance approval |
| G8 | Separately review any epoch/risk-policy change | Explicit risk-policy and activation approval |

Passing one gate does not imply approval for the next. No automatic migration, account DB opening, historical backfill, epoch activation, HWM reset, exposure increase, deployment, exchange connection, or live execution is implied.

## 12. Current decision

- Historical independent archive/checkpoint: **NONE AVAILABLE** (user-confirmed).
- Historical Dual Reconstruction: **UNAVAILABLE / BLOCKED**.
- Current baseline policy: **Option A — strict predecessor chain**.
- Forward capture protocol: **PROPOSED / NOT IMPLEMENTED**.
- Persistent storage provider/cost: **NOT SELECTED**.
- Source/schema/runtime changes: **NOT AUTHORIZED**.
- T0: **PAUSED / OUT OF SCOPE**.
- Execution: **PAPER ONLY; ai_execution_enabled=false**.

The next decision, if implementation is desired, is a review of the threat model and selection of storage/retention constraints. It is not permission to modify source or open a persistent database.
