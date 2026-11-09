# T3 RET-03 Owner Input Resolution — Paper Trading Reconstruction (2026-11-10)

## 1. Status and scope

**Stage A.4 documentary/source trace: COMPLETE.**  
**T3 RET-03: OPEN / FLOOR_NOT_ESTABLISHED.**  
**No numeric retention floor or TTL selected. No object is deletion-eligible.**

Repository: `kenznguyen/btcusdt-telegram-signals2`  
Branch: `feature/t0-centralized-data-feeder-p1-20261101`  
Source baseline HEAD: `77c6892efb7107f91c2aa5d20e33187e856a36a9`

This is a static repository analysis of the signal decision path, paper ledger, risk controls, event journal, replay loader, replay engine, and architecture contracts. It does not establish that the code is deployed, that a paper account database exists or is current, or that every runtime consumer/copy is represented in the repository.

No persistent paper database, VPS, runtime, provider, external account statement, exchange, backup, replica, export, or recipient was accessed. No inventory, test, GitHub Actions dispatch, migration, source/config/workflow/permission change, restore, or destructive operation was performed.

## 2. Exact source records inspected

| Source | Blob SHA |
|---|---|
| `docs/architecture/DUAL_LEDGER_CONTRACT.md` | `e41e544efc6c1ae17596cb92a2cc38f86412ebb5` |
| `docs/architecture/DUAL_RECONSTRUCTION_VERIFICATION_CONTRACT_2026-11-07.md` | `07510e060c17854ca70ec1e83078dc66af302602` |
| `docs/FIVE_LAYER_PAPER_RUNBOOK.md` | fetched at source baseline; not used to assert runtime state |
| `paper_execution/README.md` | `3f8fd2d51f945c27d9af866b7f2636b8d174dd4d` |
| `paper_execution/ledger.py` | `0bc94ae0e704a69e253246a575991c1de436e0a4` |
| `paper_execution/risk_control.py` | `3c76e462b0b4d924c2418842d95ed74285e2315d` |
| `paper_execution/account_history.py` | `6163065798b2386e1c466650048e40b7eab0d2eb` |
| `paper_execution/replay_inputs.py` | `e32ec695546086449b35e43d8ae0d51f4dc32c27` |
| `paper_execution/replay_reconciliation.py` | `68a59b3938a28055e4d2b27733efcdb643127ea8` |
| `pipeline/decision.py` | `e718756b415fc193a486900e7b84c2cf05e6a091` |
| `paper_execution/test_dual_ledger_red.py` | `d8d6672c0f849b8dd1e5ae7fe2069e207defb3ed` |
| `paper_execution/test_account_history_replay_red.py` | `9aa296ed2bc2c735ef98f28f44f486a58e911331` |
| `paper_execution/test_risk_control.py` | `69c9177a249369f52d0c81e442c9c4583c9f5b77` |

The dual-ledger and reconstruction documents are design contracts, not proof that all contract requirements are implemented or operationally accepted.

## 3. T3 object and event map

### 3.1 Signal / strategy intent

- `pipeline.decision.evaluate()` validates prediction, order-book and intelligence inputs, then returns a PAPER BUY/SELL intent or WAIT.
- The generated intent includes strategy/model/data/snapshot identity and decision/expiry timestamps. It is passed to the paper execution path.
- The inspected decision function does not itself persist a durable signal history or an append-only signal-decision record.
- The downstream `paper_orders` row stores the intent identity/hash and an order document. This is not equivalent to preserving every pre-execution signal, WAIT result, rejected intent, or every input artifact version.

**Classification:** final accepted signal/intent and its exact source lineage are decision evidence; protect them. The complete signal/WAIT/rejected-intent history and consumer graph are NOT VERIFIED. A consumed signal or expired intent is not, by itself, a terminal retention event.

### 3.2 Shared risk decision

- The dual-ledger submission path performs account-wide checks before exposure increase: account readiness/cutover/funding coverage, equity, HWM/daily loss, gross exposure, active reservations, margin reservation, Kill Switch/pause and intent expiry.
- The admission result is reflected in the persisted order status/reason and reservation state. The inspected source set does not establish a separate immutable, versioned risk-decision journal that records every evaluated input, policy/config version, calculation, threshold result and rejection independently of the order document.
- The persistent risk-control latch is shared account state. Kill/pause changes are state transitions; the separate risk-control module does not provide a full append-only history of every risk evaluation.

**Classification:** risk decisions, admission inputs, risk config/version, reservation decisions and Kill Switch/pause transitions are protected T3 governance/account evidence. Rejected/blocked decisions also matter to explain why no trade occurred. No risk-evaluation history can be treated as disposable based on the current source trace.

### 3.3 Paper order lifecycle and reservations

- `paper_orders` stores order/intent identity, strategy ownership, status and serialized document. The execution code updates order status/document on expiry and cancellation; therefore the current row is a mutable current-state representation, not a demonstrated append-only order lifecycle history.
- `paper_risk_reservations` stores account/strategy ownership, reservation kind/status, reserved and remaining margin/notional, leverage, equity basis, risk config version and expiry. The implementation changes reservation state as fills, cancellation and expiry occur.
- README documents expiry behavior: only unfilled remaining reservation is released; filled position/PnL/fees persist; read-only snapshots do not perform expiry writes. An expired/canceled order does not erase the preceding intent, admission or fill history.
- The dual-ledger contract requires order lifecycle, reservation and ledger writes to share one atomic transaction. This is a design requirement; source-level presence is not a production durability/recovery proof.

**Classification:** order identity, every lifecycle transition, reservation admission/consumption/release, and associated evidence are protected. Current mutable order/reservation rows alone do not prove complete historical lifecycle reconstruction.

### 3.4 Fill / execution simulation

- Paper execution simulates limit fills against a captured visible-depth book snapshot; it is explicitly not exchange execution evidence.
- Each simulated fill level is written as a `FILL` row in `paper_account_event_journal`, with event ID, strategy owner, order/intent/source event IDs, event/recorded times, signed quantity, price, fee/currency, source, book snapshot ID and canonical payload digest.
- The account event journal has update/delete immutability triggers. Fill events are replay inputs.
- The referenced book snapshot ID and digest do not by themselves prove that the original complete book bytes, sequence continuity, capture provenance or external liquidity existed. README explicitly limits the model to paper simulation.
- The replay engine applies individual fills in deterministic order and computes position, average entry, realized PnL and fees. Funding is replayed separately with explicit provenance/coverage.

**Classification:** fill events, fees, funding events, source snapshot references, canonical payloads/digests and coverage evidence are protected reconstruction inputs. No post-use deletion is allowed by this analysis.

### 3.5 Reconciliation and paper outcome

- Replay inputs are loaded from read-only SQLite snapshots. The loader validates schema migration identities, immutable cutover snapshots, execution/funding/market-mark coverage, event hashes, source references, event/recorded times, late arrivals and exact strategy set.
- The replay engine independently replays CORE, AI and LEGACY_UNATTRIBUTED ledger state, then calculates aggregate realized/unrealized PnL, fees, funding and equity at a UTC boundary.
- The reconstruction contract requires separate evidence roots for Replay A and Reconstruction B; identical mutable rows or two exports from the same mutable source are only internal consistency, not independent reconstruction.
- Required replay events include fills/partials, reductions/closures, reversals, DCA fills, fees, funding, order lifecycle, reservations, mark/equity observations, legacy adjustments and linked corrections. Missing fills/fees/funding, ambiguous ordering, late events, gaps, unknown ownership or incomplete coverage must block reconciliation.
- The current replay implementation's execution-event path accepts `FILL` event type. It does not demonstrate full replay of every order/risk/reservation lifecycle transition or a second independently retained evidence root.

**Classification:** cutover snapshots, account/ledger event history, daily baselines, market marks, coverage proofs, replay inputs/results, reconciliation reports, correction chains, manifests and independent evidence roots remain protected for as long as paper outcome, risk, audit or recovery obligations depend on them.

## 4. Critical gaps between the required T3 record and the traced implementation

| Area | What is present | Gap / status |
|---|---|---|
| Signal history | Decision function emits PAPER intent; order row stores submitted intent | No durable complete history of emitted signals, WAITs, non-submitted or rejected evaluations established — NOT VERIFIED |
| Signal-to-ledger lineage | intent/order IDs, strategy/model/dataset/snapshot fields | Exact immutable binding across every decision input, risk decision, order, fills and reconciliation output not proven — PARTIAL |
| Risk decision evidence | Admission logic, order reason/status, shared risk state and reservations | No separate immutable record of every risk evaluation and its full input/config/result set found — NOT VERIFIED |
| Order lifecycle | Mutable order row/document, audit inserts, reservations | Complete append-only transition journal and replay of cancel/reject/expire/reopen/retry transitions not established — NOT VERIFIED |
| Fill events | Append-only FILL journal with payload digest and provenance references | Underlying book snapshot bytes/copy chain and completeness not proven — PARTIAL |
| Reservation lifecycle | Reservation state, expiry, book-level reservations | Full immutable transition history and independent replay coverage not established — NOT VERIFIED |
| Fees/funding | Fee fields on fill; funding events and coverage/provenance | Historical completeness and external source-byte custody not established — NOT VERIFIED |
| Reconciliation | Deterministic replay function, read-only input loader, cutover snapshots and daily baseline records | Production execution, full lifecycle replay, independent evidence roots and operational reconciliation are NOT VERIFIED |
| Audit/corrections | Paper audit inserts and linked correction requirements in contract | Complete immutable audit/correction chain and all consumers/copies not established — NOT VERIFIED |
| Restore/recovery | Contracts describe required restore and replay evidence | Actual restore sets, backups, recovery tests and independent retained copies not inventoried — NOT VERIFIED |

A digest proves the digest of the bytes hashed; it does not independently prove upstream completeness, authenticity, custody or that all required records were captured.

## 5. Protected classes and provisional classification

The following are protected and excluded from any class-wide delete-after-use policy:

1. `CORE_LEDGER`, `AI_LEDGER`, and `LEGACY_UNATTRIBUTED` accounting state.
2. Strategy signals/intents, including decisions that were rejected, blocked, expired or not submitted where needed to explain strategy behavior.
3. Shared Risk Engine decisions, risk inputs/config snapshots, Kill Switch/pause and risk-readiness history.
4. Orders and every lifecycle transition; fills and partial fills; cancellations, rejections, expiries and retries.
5. Margin/exposure/book-depth reservations and their admission, consumption and release history.
6. Fees, funding, marks, equity observations, cutover snapshots and account adjustments.
7. Event journal, paper audit, coverage, manifests, replay inputs/results, reconciliation reports, correction/supersession links and required T3/T4 reconstruction outputs.
8. Backups, restore sets, independent evidence copies and governance/audit/security/incident evidence while obligations remain open.
9. Unknown, orphaned, unclassified, incompletely inventoried or externally copied records.

Potentially regenerable dashboard/read-model/cache artifacts may only be assessed later as individually identified noncanonical objects after exact lineage, consumer closure, source recoverability, copy graph, holds and owner authority are proven. This report does not designate any T3 object as eligible.

## 6. RET-03 owner-input matrix for T3

| Required input | Evidence available | Missing input | Status |
|---|---|---|---|
| Purpose | Paper strategy execution, account risk, accounting and daily equity reconstruction | Owner-approved purpose/obligation per event/artifact class and consumer | PARTIAL |
| Authority / obligation source | Repository design contracts and source behavior | Authoritative operational, audit, security, contractual or competent legal determination where applicable | NOT PROVIDED |
| Owner / custodian | Core/AI/Legacy code ownership boundaries | Accountable owner/custodian for every DB, journal, artifact, backup, export and recipient | NOT PROVIDED |
| Exact scope | Table/field/event identities defined in source | Actual account DB, row population, versions, paths, copies, snapshots, recipients and coverage | NOT VERIFIED |
| Start event | Event time, recorded time, cutover and coverage timestamps exist | Owner-approved start event per signal, risk decision, order, fill, reservation, reconciliation and obligation | OPEN |
| Terminal event | Order states include FILLED/PARTIAL/CANCELED/EXPIRED/REJECTED | Positive closure event for decision explanation, replay, dispute, audit, correction, incident and recovery obligations; order terminal state is not global obligation closure | OPEN |
| Duration / numeric floor | No approved class-specific floor found in inspected T3 records | Source-backed minimum duration and rationale for each object/obligation | NOT PROVIDED |
| Replay completeness | FILL and funding replay; coverage/watermark checks | Complete immutable lifecycle/risk/reservation stream, all event classes, deterministic ordering and exact correction handling | NOT VERIFIED |
| Independent reconstruction | Contract requires separate evidence roots | Actual independent retained root, storage identity, custody, readback and reproducible second path | NOT VERIFIED |
| Consumer closure | Known paper ledger, risk, replay and dashboard interfaces | Complete runtime consumer/dependency registry and exact release evidence | NOT VERIFIED |
| Copies / restore | Contracts describe independent roots and restore requirements | Actual DB/WAL, backup, snapshot, artifact, cache, export, replica, restore-set and external-recipient graph | NOT VERIFIED |
| Holds | No T3-specific hold disposition established | Competent authority, exact scope, hold/release evidence and reopen/successor rules | NOT PROVIDED |
| Trusted time / ordering | event_at_ms, recorded_at_ms, event IDs, coverage watermark and UTC boundaries | Approved trusted-time authority, uncertainty, sequence semantics and durable proof for terminal events | OPEN |
| Owner disposition | No T3 retention-floor decision found | Explicit owner disposition tied to exact immutable object/version and authoritative basis | NOT PROVIDED |

No numeric floor, TTL, grace period, expiry rule or terminal-obligation duration is inferred from order `validUntilMs`, reservation expiry, daily UTC boundaries, framework defaults, or the fact that a replay completed.

## 7. Required owner inputs before any finite floor assessment

1. Identify the authoritative owner and custodian for the account, ledgers, journals, risk controls, replay artifacts and each copy.
2. Define exact signal/risk/order/fill/reservation/reconciliation object classes and their immutable identifiers/version boundaries.
3. Supply the obligation basis and purpose for strategy explanation, accounting, performance claims, risk governance, audit, security, incidents, recovery and disputes.
4. Define class-specific start and positive terminal events, including late fills/events, corrections, reopened investigations, model/strategy successors and unresolved reservations.
5. Approve deterministic replay completeness: all required event classes, event ordering, source coverage, duplicate/late-event handling, fee/funding provenance and correction semantics.
6. Identify immutable signal-to-risk-to-order-to-fill-to-reconciliation lineage, including rejected/no-trade decisions and the exact strategy/model/dataset/config/book inputs.
7. Establish the two distinct evidence roots required by the reconstruction contract, their custodians, storage/failure domains, exact byte digests and readback.
8. Provide actual runtime consumer, database, WAL, backup, replica, cache, export, restore and external-recipient inventory under separate bounded authorization.
9. Identify applicable holds and competent release authority; specify reopen/successor behavior.
10. Provide a source-backed duration rationale for each obligation. If no authoritative basis exists, leave the floor open.

## 8. Stage A.4 result and controls

- **T3 source/contract map:** DOCUMENTED.
- **T3 lifecycle and reconstruction dependency map:** DOCUMENTED at source/design level.
- **T3 RET-03:** OPEN / FLOOR_NOT_ESTABLISHED.
- **Numeric retention floor / TTL:** NONE SELECTED.
- **Deletion eligibility:** NONE.
- **Tests:** NOT RUN; this increment is documentation-only.
- **GitHub Actions:** NOT DISPATCHED; no workflow run or artifact claimed.
- **Runtime/database/VPS/provider/consumer/copy inventory:** NOT PERFORMED.
- **Independent evidence-root verification / restore / reconciliation execution:** NOT PERFORMED.
- **Legal or contractual determination:** NOT PERFORMED.
- **Source, schema, workflow, config, permission, runtime and data:** UNCHANGED.
- **Archive, expiry, cleanup, compaction, vacuum, backup/replica removal, export mutation, restore mutation and deletion:** NOT AUTHORIZED / NOT EXECUTED.

Option C — No Destructive Authority — remains in force. The lifecycle independent-review waiver removes only the human reviewer gate; it does not waive owner authority, substantive evidence, technical separation, inventory, replay completeness, exact-object binding, fail-closed requirements or destructive-operation prohibitions. CORE_LEDGER, AI_LEDGER, required T3 reconstruction/audit evidence, T0 independence, paper-only mode and `AI_EXECUTION_ENABLED=false` remain unchanged.

**Final status: STAGE A.4 DOCUMENTARY TRACE COMPLETE — T3 RET-03 OPEN — NO NUMERIC FLOOR — NO DELETE-AFTER-USE AUTHORITY.**
