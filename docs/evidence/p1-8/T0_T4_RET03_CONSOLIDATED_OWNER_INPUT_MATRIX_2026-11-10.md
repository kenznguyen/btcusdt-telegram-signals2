# T0–T4 RET-03 Consolidated Owner-Input Matrix

Date: 2026-11-10
Repository: `kenznguyen/btcusdt-telegram-signals2`
Branch: `feature/t0-centralized-data-feeder-p1-20261101`
Work type: documentation-only consolidation of Stage A.1–A.5
Frozen source baseline HEAD: `1f0ec96fb1a99406a484e6c4057db616583ec35e`
Status: **STAGE A.6 DOCUMENTARY CONSOLIDATION COMPLETE — RET-03 OPEN — NO NUMERIC FLOOR — NO DELETION ELIGIBILITY**

## 1. Purpose and decision boundary

This matrix consolidates the existing T0–T4 RET-03 owner-input analyses. It separates repository/source-confirmed facts from owner, legal, operational and runtime inputs that have not been supplied or verified. It is not a new retention policy, legal interpretation, complete runtime inventory, or authorization to implement lifecycle behavior.

Controlling decisions:
- RET-01 B / RET-02 B remain the ratified class policy.
- Option C — No Destructive Authority — remains controlling.
- The lifecycle independent-human-review gate is owner-waived; this does not waive substantive evidence, owner authority, technical verification, inventory, fail-closed behavior or exact-object/version requirements. Any self-assessment is labelled OWNER ASSESSMENT, not independent assurance.
- T0 canonical data and availability/recovery copies remain protected and independently owned.
- CORE_LEDGER and AI_LEDGER remain separate. Required T3 reconstruction/audit evidence remains protected.
- Unknown, unclassified, orphaned or incompletely inventoried objects/copies remain BLOCKED_UNKNOWN / protected.
- Paper-only; `AI_EXECUTION_ENABLED=false`; no live orders.

No numeric duration, TTL, expiry rule, deletion date, or deletion eligibility is approved by this document.

## 2. Frozen source records

| Stage | Report | Blob SHA | Baseline / limitation |
|---|---|---|---|
| A.1 | `T0_RET03_RET07_RETENTION_FLOOR_INPUT_GAP_ANALYSIS_2026-11-10.md` | `e26d056f9f0c2ea57a9951a650b29af11939c422` | Documentary class boundary and common missing-input analysis |
| A.2 | `T1_RET03_OWNER_INPUT_RESOLUTION_2026-11-10.md` | `061ea9340e07a9f633a8864928c945f44adc5295` | Static trace of existing T1 CSV/importer and separate proposed kline product |
| A.3 | `T2_RET03_OWNER_INPUT_RESOLUTION_2026-11-10.md` | `8d5a4172a28044539c8ccf451866b197735d1617` | Static source/consumer trace; external runtime/model directories not inspected |
| A.4 | `T3_RET03_OWNER_INPUT_RESOLUTION_2026-11-10.md` | `1b73122e1d7eb6d582462a3d8013d7b6f4f6edcb` | Static signal, risk, ledger, event and replay trace |
| A.5 | `T4_RET03_OWNER_INPUT_RESOLUTION_2026-11-10.md` | `cc6c0d9f193b1abb8194a6865cac43f9e8667466` | Static current React dashboard/API source trace; excludes Android Chart/Scanner and legacy standalone backtest page |

Controlling policy references:
- Lifecycle dependency/acceptance plan blob: `bfbd3ae5ec49e644632c72a1865745628ef574f3`.
- Lifecycle independent-review waiver blob: `555951e36f6365012cb5b9e48ba24e455b775d16`.
- P1.8.152 historical lifecycle reconciliation blob: `e1a4d95af216e94a58fa5528850fcd0c1ff465f8`.
- F-01–F-09 / P1.8.152–153 reconciliation blob: `3d084c04cd9712ed05d790ce5c431e988b64ce32`.

These report SHAs identify the exact report contents read for this consolidation. The per-stage source baselines differ; they are not represented as one simultaneous runtime snapshot.

## 3. Consolidated T0–T4 class and obligation matrix

| Layer / class | Owner boundary and source-confirmed facts | Preservation purpose / dependencies | Positive terminal event required before any future floor can be assessed | Missing owner / evidence inputs | Current RET-03 disposition |
|---|---|---|---|---|---|
| **T0 canonical market data** (BTCUSDT M15/H1, source metadata, dataset versions, coverage/lineage) | T0 is the independent canonical data foundation. T4 candle API is a read-only presentation path; downstream consumers do not acquire T0 ownership. | Canonical market history, reproducible downstream decisions/research, provenance, integrity and recovery. T1/T2/T3/T4 consumers and derived artifacts may depend on it. | No finite terminal event is established in the inspected records. Canonical status and continuing availability/recovery purpose remain controlling. | Authoritative operational/research obligations, accountable owner/custodian attestations, complete downstream dependency graph and any legally applicable source-backed obligation have not been supplied here. | **PROTECTED / EXCLUDED** from ordinary class-wide deletion assessment. No floor or deletion eligibility. |
| **T0 availability and recovery copies** | Copies that preserve T0 availability, integrity, lineage or recovery remain T0-owned protected copies regardless of physical location. | Restore, continuity, integrity and reconstruction of canonical data. | Requires a proven replacement/recovery closure and approved policy basis; no such terminal event is evidenced. | Complete replica/backup/provider/restore-set inventory, copy lineage, recovery tests and owner-approved release criteria are absent. | **PROTECTED / EXCLUDED**; copy graph NOT VERIFIED. |
| **T1 raw exchange observations** (Trades, Funding, Open Interest, Liquidations CSV) | Existing importer is explicit-path / pull-CLI driven. Trade flow is consumed after quality gates in the traced decision path; Funding/OI/Liquidations are exposed to dashboard/downstream analysis in the inspected path. Snapshot quality is OBSERVED_ONLY, complete=false, continuity UNVERIFIED, connection UNVERIFIABLE. | Input lineage, source validation, research/replay, decision explanation, disputes, corrections and downstream snapshots. Hashes prove bytes read, not complete upstream transport. | Per-obligation closure for source validation, replay/correction, incident/dispute and downstream consumers; no common terminal event is proven. Successful import/read/ACK is not closure. | Actual CSV paths, rotations, file population, producer schedule/runtime, all consumers/copies/recipients, obligation sources, owner/custodian, start/end event semantics, holds and applicable jurisdiction/contract evidence. | **RETAIN / FLOOR_NOT_ESTABLISHED**; no delete-after-read, age-based or ACK-based deletion. |
| **T1 proposed 1m kline source-file product** | Contract v1.1 is DESIGN ONLY / NOT APPROVED FOR IMPLEMENTATION; distinct from existing CSV feeds and T0 canonical M15/H1. Pinned producer trace reported f64/12-decimal formatting and parse-failure-to-zero defect; correction is not evidenced. | If ever implemented: source-file provenance, exact decimal fidelity, producer watermark/offset, reconciliation and read-only cursor lineage. | No implemented product, accepted objects, consumer population or operational obligation is established; therefore no terminal event can be set. | Implementation approval, corrected producer source and proof, actual object/runtime inventory, consumers, owner and obligation evidence. | **NOT AN EXISTING ACCEPTED DATASET**; not retention-eligible; no floor. |
| **T1 connection-lifecycle sidecar evidence** | Separate offline reference component, not raw market observations and not integrated into importer/decision path; manifest unsigned. | Operational connection lifecycle and diagnostic evidence; governed under RET-07 evidence classes, not merged with market feed retention. | Evidence case/incident closure and any audit/security duty must be defined by an authoritative source. | Actual deployment/existence, custody, consumers, incident/audit obligations, evidence terminal/reopen/successor semantics and owner inputs. | **PROTECTED / RET-07 OPEN**; no expiry. |
| **T2 intermediate inference outputs** (ephemeral predictions / latest-output slot) | Prediction JSON is atomically replaced at a configured path; it is a latest-output slot, not append-only history. Strategy fail-closed behavior on unavailable/invalid inputs is source-confirmed. Actual runtime paths and artifact existence are not verified. | Distinguish transient computation from outputs consumed by a final signal, risk decision, ledger, model evaluation, audit or replay. Preserve lineage where consumed. | A candidate transient object would require proof it was never promoted/consumed and that no replay, audit, model-evaluation or incident dependency remains. No such global terminal event is established. | Actual model/report paths, immutable input/output lineage, full consumers/copies, promotion/consumption markers, owner-approved event semantics, model/replay duties and holds. | **OPEN / FLOOR_NOT_ESTABLISHED**. Replaceability or successful consumption does not authorize deletion. |
| **T2 feature/input snapshots and normalized inference inputs** | T2 depends on canonical T0 candles and T1 intelligence; snapshot identity and dataset versions bind downstream decisions. Runtime storage and all copies not inspected. | Reproduction and explanation of prediction/decision, model-input integrity, replay and discrepancy investigation. | Exact dependent decision/model/replay obligations must be closed with evidence; no closure proof is available. | Feature snapshot object inventory, transformation/config versions, source lineage, consumers, training/replay needs, holds and owner disposition. | **PROTECTED where decision/replay-linked; otherwise UNKNOWN / BLOCKED_UNKNOWN**. No floor. |
| **T2 model artifacts, training/evaluation/calibration and experiment evidence** | Model/training/evaluation provenance is a distinct lifecycle from ephemeral inference. Actual external model directories and training files were not inspected. | Reproducibility, model governance, validation/calibration, drift/incident analysis and lineage to predictions/decisions. | Model retirement alone is not a terminal event unless all reproducibility, audit, incident, regulatory/contract and dependent-decision obligations are proven closed. | Exact artifact/version inventory, training data and code/config lineage, experiment consumers, evaluation/calibration obligations, owner/custodian, hold and terminal event evidence. | **PROTECTED / NOT VERIFIED**; no floor or deletion eligibility. |
| **T3 signals, WAIT/rejected intents and strategy decisions** | Decision function emits PAPER BUY/SELL intent or WAIT. A durable complete history of every signal/WAIT/rejected intent was not established. | Explain both executed and non-executed outcomes; preserve strategy/model/data/snapshot identity and decision timestamps. | A signal's consumption or expiry is not terminal; requires closure of decision reconstruction, risk, audit and dispute obligations. | Complete append-only decision history, exact input/config versions, consumer/copy graph, owner obligation and terminal-event definitions. | **PROTECTED where persisted/decision-linked; completeness NOT VERIFIED**. |
| **T3 risk evaluations, admission/rejection, Kill Switch and reservations** | Shared risk checks are present; separate immutable/versioned journal of every full risk evaluation was not found. Orders/reservations are mutable current-state records. | Demonstrate why exposure was admitted, blocked or paused; preserve risk policy/config, account state and reservation transitions. | No risk/audit obligation closure event is evidenced; order expiry/cancel is not sufficient. | Complete risk-decision journal, policy/config versions, transitions, consumers, copy/restore inventory, owner and obligation evidence. | **PROTECTED / completeness NOT VERIFIED**. |
| **T3 CORE_LEDGER, AI_LEDGER, LEGACY_UNATTRIBUTED, orders, fills, fees, funding, equity, marks, audit, replay and reconciliation** | Dual-ledger ownership is separate. Fill events are journaled; order/reservation state is mutable. Replay validates selected coverage but does not prove full lifecycle replay or a second independent evidence root. T4 GET /v1/equity source path records equity history and daily baselines. | Paper-outcome reconstruction, PnL/risk/accounting, correction, audit, reconciliation, incident and recovery. | No single “trade complete”, fill, order expiry, day boundary or replay completion event closes all obligations. Requires complete correction/reconciliation and all applicable audit/recovery/hold obligations. | Complete durable lifecycle/event history, second evidence root, complete ledger/copy/backup/restore inventory, external statements if applicable, correction/successor semantics, trusted time, owner/legal/operational obligations. | **PROTECTED / EXCLUDED**; no post-use deletion. CORE_LEDGER and AI_LEDGER remain separate. |
| **T4 dashboard view state, SVG/read models and transient process caches** | React state is in memory; requests/API are no-store in source; no browser durable DB found in selected source. Three-second order-book process cache is source-confirmed. Actual deployment/browser/proxy/service-worker/log/capture copies not inspected. | Presentation only where no export, capture, independent consumer, T3 reference or recovery role exists. Fill-referenced book evidence is T3-protected. | For an individually identified object: proven process/session termination plus complete proof of no consumer, export, capture, fill/replay, security or recovery dependency. No class-wide terminal event established. | Actual runtime/build, browser and proxy/CDN/service-worker caches, logs, screenshots, downloads, operator captures, process lifecycle, cache object identity, T3 reference closure and full copy graph. | **CANDIDATE ONLY AFTER EXACT-OBJECT PROOF; presently UNKNOWN / BLOCKED_UNKNOWN**. No blanket expiry. |
| **T4 equity and audit views** | Dashboard polls nine endpoints every five seconds. GET /v1/equity calls PaperLedger.record_equity(), persisting paper_equity_history and paper_daily_baselines. Audit endpoint is a bounded 50-row view. | These are T3 risk/reconstruction/audit records, not disposable T4 presentation cache. Polling and display bounds do not change ownership. | Must follow T3 obligation closure; UI refresh, query limit or view replacement is not terminal. | Runtime invocation frequency, full persisted data/backup/copy inventory and T3 obligations remain NOT VERIFIED. | **T3 PROTECTED**; do not alter/delete to mask polling. |
| **T4 build, deployment, rollback and operator exports/captures** | Selected source did not show explicit export/download; deployed build hashes, CI artifacts, rollback copies and manual/external captures are unknown. | Reproducible deployment, rollback, security, incident, operator and downstream evidence where applicable. | Build supersession is not terminal until rollback, incident, audit, security and recipient obligations are closed. | Exact build/deployment hashes, CI artifact retention, hosting/CDN copies, rollback inventory, operator captures, recipients, export existence, owners and obligations. | **UNKNOWN / BLOCKED_UNKNOWN**; no deletion eligibility. |

## 4. Cross-layer dependency and non-terminal events

The following dependency edges prevent a “consumed = disposable” interpretation:

1. T0 canonical candles and lineage feed T1/T2 analysis and T3 decisions; T4 renders a bounded read view. T4 display limits do not alter T0 obligations.
2. T1 observations feed T2 intelligence/prediction context and decision evaluation. T1 snapshot hashes identify bytes read but do not prove upstream completeness.
3. T2 predictions, model versions, training lineage and input dataset versions feed strategy decisions; decision-linked artifacts may become T3 reconstruction evidence.
4. T3 signal, risk, order, reservation, fill, fee, funding, equity and reconciliation records depend on source snapshots and must remain reconstructible across Core/AI ledgers.
5. T4 GET /v1/equity is a read-shaped API operation with a persistent T3 side effect; request method, polling cadence or frontend ownership does not make the resulting rows T4 cache.
6. Book snapshots referenced by T3 fills cannot be treated as transient solely because the API process cache is three seconds.

None of the following is a positive terminal event by itself: successful read, consumer ACK, completed import/job, prediction replacement, model completion/retirement, signal consumption, order expiry/cancel, fill completion, day boundary, replay run, cache TTL, dashboard polling, bounded query/display limit, deployment supersession or presumed rebuildability.

## 5. Shared missing inputs required for any future class-specific floor

For each exact class and object/version/copy, the owner must supply or identify authoritative evidence for:

1. Purpose and obligation basis: precise operational/research/reproducibility/contract/legal/audit/security/incident/recovery purpose, authoritative source/version/scope, and competent attribution for any legal basis.
2. Accountable owner and custodian, including authority to attest and authoritative source system.
3. Exact object/version/copy scope, locations, systems, consumers, recipients, jurisdictions and explicit exclusions.
4. Start event with exact semantics, source, timestamp domain and trusted-time basis.
5. Positive typed terminal event(s), proof source, successor/recurrence semantics and treatment of unresolved/indefinite obligations.
6. Class-specific minimum duration and rationale, if any, from authoritative owner/obligation evidence. No value may be inferred from implementation defaults or operational convenience.
7. All dependencies, holds, disputes, corrections, investigations, audits, recovery and security obligations.
8. Complete consumer/copy/backup/replica/export/cache/restore/recipient graph and evidence that graph closure is complete.
9. Evidence custody, integrity, provenance, access, readback and retention of the evidence needed to prove compliance.
10. Explicit owner disposition tied to an immutable exact-object/version baseline. A floor is not deletion authorization.

A finite candidate floor remains unavailable if any source obligation is ACTIVE, INDEFINITE or UNKNOWN; any recurring/successor obligation is unresolved; a hold/dependency remains; source manifest or copy/restore graph is incomplete; or time/order evidence is uncertain. Required result remains FLOOR_NOT_ESTABLISHED / RETAIN / BLOCKED.

## 6. Resolution classification: repository-resolvable vs external owner inputs

### 6.1 Resolvable by further bounded repository-document review (no runtime inference)

- Locate and reconcile any additional already-committed authoritative owner decisions or contract documents for specific purpose, obligation, start/end semantics and class scope.
- Reconcile T2 report details and any extant source contracts without treating design-only proposals as implementation evidence.
- Map repository-declared consumers, config keys, schema relations, workflow artifact references and documented backup/restore roles where present.
- Reconcile the T3 event/replay contract gaps against the exact source implementation; record mismatches, not assumptions.
- Locate source-backed owner/custodian role declarations if they already exist in versioned governance records.

These steps may reduce documentary ambiguity but cannot establish actual runtime paths, deployed objects, external copies, legal obligations or operational completeness.

### 6.2 Requires explicit owner / operational / competent legal or contractual evidence

- Named accountable owner/custodian and authority for each class.
- Actual T1 CSV, T2 model/prediction, T3 paper DB and T4 deployed/browser/proxy/export object population and locations.
- Complete live consumers, recipients, backup/replica/restore/export/cache and external-provider copy graph.
- Actual start/terminal events, recurring duties, dispute/incident/audit/recovery holds and source-backed duration basis.
- Applicable legal/contractual obligations and jurisdictional interpretation from a competent source.
- Evidence that an object was never promoted/consumed or that all dependent decisions, ledgers, audits and restores are closed.
- Any approval to change policy, authorize inventory beyond existing documentary scope, or permit a future mutation.

No external owner/legal/operational input is assumed present merely because a repository field or environment variable exists.

## 7. Stage A.6 outcome and status

| Criterion | Result |
|---|---|
| T0–T4 documentary classes consolidated | **PASS — DOCUMENTARY ONLY** |
| Source-backed facts separated from runtime/owner/legal unknowns | **PASS — within inspected report scope** |
| Cross-layer dependencies and non-terminal events mapped | **PASS — documentary map** |
| Complete consumer/copy/restore inventory | **NOT VERIFIED** |
| Authoritative class-specific obligation basis and owner inputs | **NOT PROVIDED / OPEN** |
| Numeric retention floors / TTL / expiry rules | **NONE APPROVED** |
| Deletion eligibility | **NONE** |
| RET-03 | **OPEN / FLOOR_NOT_ESTABLISHED** |
| RET-07 | **OPEN** |
| Tests | **NOT RUN** |
| GitHub Actions | **NOT DISPATCHED; no run or artifact claimed** |
| Runtime/VPS/database/provider/legal/inventory probes | **NOT PERFORMED** |
| Source/schema/config/workflow/permission/runtime/data changes | **NONE** |
| Archive, expiry, cleanup, compaction, vacuum, backup/replica removal, export mutation or deletion | **NOT AUTHORIZED / NOT EXECUTED** |

## 8. Next bounded step

Stage A documentary work may proceed only by locating already-committed authoritative owner/obligation records that resolve a specific missing input. If no such record exists, record the exact input as NOT PROVIDED and stop for that class; do not fabricate a duration or terminal event. After documentary inputs are complete, RET-06 and RET-08 remain separate Stage A items under the lifecycle dependency plan. Stage B technical contracts and Stage C inventory/enforcement require their own bounded scope and authorization as stated in that plan.

**Final disposition: T0–T4 RET-03 CONSOLIDATED — OPEN / FLOOR_NOT_ESTABLISHED — NO NUMERIC FLOOR — NO DELETE-AFTER-USE AUTHORITY — OPTION C UNCHANGED.**
