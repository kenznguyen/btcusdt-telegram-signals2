# T1 RET-03 Owner Input Resolution — Raw Exchange Observations

Date: 2026-11-10
Repository: kenznguyen/btcusdt-telegram-signals2
Branch: feature/t0-centralized-data-feeder-p1-20261101
Work type: documentation-only, static source/consumer dependency reconciliation
Baseline branch HEAD: c0823759c96362d79174b90d29ec4bde1c9b8ef3
Status: **T1 CLASS MAP COMPLETE — OWNER OBLIGATION INPUTS NOT PROVIDED — RET-03 OPEN — NO NUMERIC FLOOR SELECTED**

## 1. Scope and decision boundary

This record continues Stage A.2 Owner Input Resolution for RET-03, limited to T1 raw exchange observations. It separates the existing T1 intelligence CSV streams from the proposed T1 1m kline source-file product and from connection-lifecycle evidence.

This is a static review of repository documents and pinned source evidence only. It does not access the external T1 repository, VPS, runtime, CSV files, databases, exchange, consumer processes, providers, backups, recipients or legal sources. It does not perform an operational inventory or determine legal/contractual obligations.

Controlling constraints:
- Option C — No Destructive Authority remains in force.
- No archive, expiry, cleanup, compaction, vacuum, backup/replica removal, export mutation or deletion.
- No T1 collector activation, source/adapter implementation, scheduler, VPS action, exchange request, DB change or T0/T2 integration.
- T0 canonical candles and their availability/recovery copies remain protected and independently owned.
- T1 cannot write to or alter T0.
- CORE_LEDGER and AI_LEDGER remain separate; required T3 reconstruction/audit records remain protected.
- Owner waiver of independent human review does not waive substantive technical/evidence/authority requirements. Owner assessment is not independent assurance.
- Paper-only; `AI_EXECUTION_ENABLED=false`; no live orders.

## 2. Source baseline and inspected evidence

| Source | Blob SHA / pinned identity | Use in this analysis |
|---|---|---|
| Branch HEAD before this record | `c0823759c96362d79174b90d29ec4bde1c9b8ef3` | Frozen repository baseline |
| T1 producer-to-consumer dependency trace | `7eff3b98b94296dffc48e6badd59e38ea0ca1120` | Existing T1 paths, consumers, limitations and unknowns |
| T1 source-file contract v1.1 | `bafe555b6e3941bed4188575c7b7591c4ce3b473` | Separate proposed 1m kline product; DESIGN ONLY |
| Historical T1 source-file contract v1 | `c64d6da7b16e608ef5ccebafabce03e51960cfcc` | Historical/non-normative source contract; v1.1 supersedes producer contract |
| T1 manual VPS test receipt | `0f756f89140eb1272e0f30d7e9de332921581e17` | Bounded manual test provenance; not a complete operational inventory |
| Central Data Lifecycle Policy design | `9fd46c029cff643ccc35492fd09620581f6eff35` | Demand-based retention, no delete-after-read, separate evidence lifecycle |
| T0–T1–T2 data consumption architecture | `1b11883b9d2b93e3039d509ecaed98694afe430e` | T0/T1 ownership and consumer boundaries |
| T1 collector repository identity referenced by trace | `bc4f0ef633fbeee4a49defd72827f17162693805` | Pinned upstream collector source identity for CSV importer path |
| T1 1m kline producer source SHA described by v1.1 trace | `6e20fe94f3ad64cc450e73def80a167fe371e49e` | Historical source trace showing producer precision defect; not evidence of a corrected producer |

The source trace is the current consolidated evidence for the T1 paths. The v1.1 kline contract is a proposal, not proof that the proposed product exists or is running.

## 3. T1 data product classification

### 3.1 Existing futures-intelligence CSV observations

The repository trace confirms the importer accepts explicit CSV paths for four distinct feed types, a half-open time window and an output path. File flags may repeat for daily files. The importer validates exact headers, Binance futures BTCUSDT identity, UTC millisecond timestamp consistency, bounded file/row counts, numeric constraints, duplicate semantics, file stability during read and per-file SHA-256.

The importer emits a deterministic JSON intelligence snapshot with input-file hashes and per-feed coverage, but with:
- `quality=OBSERVED_ONLY`;
- `complete=false`;
- `continuityStatus=UNVERIFIED`;
- `connectionStatus=UNVERIFIABLE`.

The snapshot's availability time is import/server time; importing old source rows does not make the underlying market events fresh.

| Feed | Current evidenced consumer use | Retention implication (not a duration) |
|---|---|---|
| Trades | Decision module consumes trade flow only after quality gates | Preserve source observations while their exact snapshot/decision, replay, investigation or source-validation dependencies remain unresolved |
| Funding | Exposed for dashboard/downstream analysis; not currently direction-setting in the traced decision module | Dashboard use alone does not prove all consumers or downstream copies; consumer and research dependencies are not fully inventoried |
| Open Interest | Exposed for dashboard/downstream analysis; not currently direction-setting in the traced decision module | Same limitation; sample timestamp semantics and exact downstream use need owner/consumer confirmation |
| Liquidations | Exposed for dashboard/downstream analysis; rows have no unique event ID and importer does not invent one | Preserve source identity and original rows; do not infer event uniqueness or deduplication semantics from timestamps alone |

These are current code-path observations, not owner-approved statements that no other use exists. The trace itself says actual runtime scheduling, operator process, file locations and artifact existence remain unknown.

### 3.2 Proposed T1 1m kline source-file product

The v1.1 document is explicitly DESIGN ONLY / NOT APPROVED FOR IMPLEMENTATION. It describes a separate Binance USD-M BTCUSDT 1m kline product with:
- versioned manifest and exact product/endpoint/symbol identity;
- FINAL_ONLY rows;
- producer-owned committed offset and watermark;
- reconciliation-backed source health;
- durable publication/receipt ordering;
- exact decimal preservation;
- bounded read-only consumer cursor semantics.

It is not the existing four-feed intelligence CSV importer and is not T0 canonical M15/H1 data. The trace found no accepted in-repository adapter or promotion path. The historical v1 contract is explicitly archival/non-normative for the producer contract.

The proposed kline contract expressly states that it does not authorize deletion, archive, cleanup, vacuum, compaction or backup expiry. Its recovery section requires preserving uncommitted tail bytes for diagnosis/quarantine; it does not authorize truncation/deletion.

A prior pinned producer trace found a confirmed precision defect: decimal fields were parsed through `f64`, formatted to 12 fractional digits, and parse failures substituted with `0.0`. The v1.1 contract says this must be corrected and proven before any implementation acceptance. This analysis does not claim that correction has occurred.

**Disposition:** classify as a separate proposed T1 source product, not as an existing retention-eligible dataset. No retention floor can be calculated for a product whose implementation, actual objects, consumers and operation are not established.

### 3.3 Connection-lifecycle sidecar evidence

The Rust sidecar writer/validator is a separate offline reference component. The upstream collector does not write it; it is not integrated into the importer, quality or decision path. Its manifest is unsigned and a SHA-256 digest alone is not producer authentication. It is evidence about connection lifecycle, not raw market observations.

Do not merge its lifecycle evidence with the four CSV feeds or the proposed 1m kline product. Its retention belongs to the RET-07 evidence-group assessment, not this T1 raw-observation floor.

## 4. Producer-to-consumer and demand findings

### 4.1 Confirmed

- Existing CSV importer is pull/CLI driven and requires explicit input paths, time window and output path.
- The repository trace did not establish an in-repository scheduler, watched-directory consumer or automatic CLI invocation.
- The importer computes source file hashes and content-identified snapshots, but this is provenance of bytes read, not proof of complete upstream transport.
- Trade-ID gap counts are local observations; absence of an observed gap does not prove transport continuity.
- Funding/OI timestamps and liquidation observations have their own limitations.
- The decision module uses trade flow only after quality gates; funding/OI/liquidations are exposed for dashboard/downstream analysis in the inspected path.
- Snapshot publication uses a temporary file, file fsync and atomic replacement; this does not prove source CSV durability or producer completeness.
- T0 candles remain a separate canonical data source. T1's proposed 1m klines do not replace T0.
- The trace marks actual producer runtime, source CSV set/path/rotation, operational schedule, API environment path and continuous producer-to-consumer edge as NOT VERIFIED.

### 4.2 Not established

The inspected evidence does not establish:
- the actual set of CSV files currently retained or their storage locations;
- whether daily files are rotated, overwritten, archived, copied or retained indefinitely;
- the actual capture start/end events or a reliable source-side completeness boundary;
- a complete consumer register for each feed and exact time range;
- all downstream snapshots, exports, dashboards, research runs, model/decision records or external recipients;
- the end of replay, source-dispute, correction, quality investigation, research or reproducibility obligations;
- whether any data is subject to a legal, contractual, audit, incident, security or recovery hold;
- an accountable owner and competent authority for each obligation;
- an approved minimum duration, TTL or terminal event for any feed.

No missing item is inferred from the current importer behavior.

## 5. RET-03 obligation input matrix for T1

| Required input | Evidence currently available | Missing owner/source input | Status |
|---|---|---|---|
| Purpose per feed | Trade-flow decision path; funding/OI/liquidation dashboard/downstream exposure | Owner-confirmed exhaustive purpose and any off-path research/benchmark/investigation uses | PARTIAL / NOT VERIFIED |
| Authoritative obligation source | Repository code/design and lifecycle policy design only | Applicable owner-approved operational/research contract, legal/contractual determination where applicable, audit/security/incident obligations | NOT PROVIDED |
| Accountable owner/custodian | Producer and consumer components identified | Named accountable role and authority to attest to each feed's obligations and source-of-truth location | NOT PROVIDED |
| Exact scope | Feed types and BTCUSDT futures identity in importer | Exact dataset/version, partition/file, object identity, source/copy, time-range and recipient scope | PARTIAL |
| Start event | Source rows have UTC millisecond timestamps; snapshot has import/server availability time | Owner-approved event semantics for each obligation; event time vs capture/commit/import time | OPEN |
| Terminal event | No terminal event established by static trace | Positive authoritative end event for replay, correction, consumer, research, investigation, audit and recovery duties | OPEN |
| Minimum duration | No approved numeric value in inspected records | Owner/source-backed duration and rationale per feed/obligation | NOT PROVIDED |
| Completeness and continuity | `complete=false`, continuity unverified, connection unverifiable; source hashes | Authoritative source reconciliation and capture continuity evidence; exact completeness boundary | NOT VERIFIED |
| Correction/replay obligations | Importer duplicate and file-stability validation; kline design has correction/quarantine rules | Owner-defined correction windows, source-dispute handling, replay/reprocessing requirements and end evidence for the four CSV feeds | NOT PROVIDED |
| Consumer dependency closure | One inspected decision path and dashboard/downstream exposure | Complete consumer/recipient list and exact version/purpose dependency release evidence | NOT VERIFIED |
| Copy/backup/restore graph | Not established by trace | Exact source files, snapshots, caches, exports, backups, replicas, restore sets and external copies | NOT VERIFIED; inventory not authorized here |
| Holds and legal/contract scope | No scoped hold determination in inspected T1 evidence | Competent owner/legal/security/audit authority and exact scope/release evidence where applicable | NOT PROVIDED |
| Clock/trusted time | UTC millisecond source fields; import/server availability time | Trusted-time source, uncertainty, event ordering and V07/V08-compatible evidence for terminal events | OPEN / BLOCKED |
| Compliance evidence | Input hashes, snapshot content identity, pinned collector SHA | Immutable obligation manifest, authoritative end-event proof, full lineage and evidence-custody requirements | PARTIAL / NOT VERIFIED |
| Owner disposition | No T1-specific numeric retention approval found | Explicit owner decision for policy semantics and numeric floor, bound to exact version/scope | NOT PROVIDED |

## 6. T1-specific questions that require owner input

Before a finite RET-03 floor could even be proposed, the owner must provide or identify authoritative answers to these questions:

1. **Trades:** Are the observations retained for trade-flow decision replay, research, source reconciliation, incident investigation or other purposes beyond the currently traced decision path? Which exact outputs/runs depend on each input window?
2. **Funding:** Which dashboards, research jobs, reports or experiments consume the feed? Are historical funding observations required to reproduce any strategy/risk/backtest claim? What closes each dependency?
3. **Open Interest:** Which downstream consumers and research obligations apply? Which timestamp represents the observation event and which timestamp represents import/publication?
4. **Liquidations:** What is the source's stable row identity or duplicate policy? Since the importer does not invent a unique event ID, what evidence can distinguish repeated observations from distinct events? No identity rule may be guessed.
5. **Source files:** What is the authoritative producer/capture location and who controls it? What are the actual partition and rotation semantics? The current trace does not establish actual files or their rotation.
6. **Capture completeness:** What source-side evidence proves capture continuity and the end of an observation window? Hashes and local trade-ID gap counts are insufficient by themselves.
7. **Consumer closure:** Who can attest that every consumer has released its exact dataset/version/purpose dependency? A job completion, read, download or ACK is not by itself a deletion trigger.
8. **Obligations and holds:** Which source-backed operational, research, audit, security, incident, contractual or legal obligations apply, if any? Any legal conclusion must be supplied by a competent authority; this record does not infer jurisdiction or law.
9. **Start/end and duration:** What exact event starts each obligation, what positive evidence closes it, whether it recurs/reopens, and what source justifies any minimum duration?
10. **Copies:** Which snapshots, exports, local copies, backups, replicas and recipient copies exist? This requires a separate bounded inventory authorization; none is granted here.

## 7. Retention posture pending owner inputs

The current safe posture is:

- **T1 CSV raw observations:** RETAIN / FLOOR_NOT_ESTABLISHED for purposes of lifecycle eligibility; no age-based, read-based or ACK-based deletion.
- **T1 intelligence snapshots:** treat separately as derived analytical outputs with their own input-file hashes, quality state and decision/research lineage. Do not assume a snapshot is disposable because it can be regenerated; prove source availability, exact transformation/version and all dependencies first.
- **T1 1m kline proposal:** DESIGN ONLY; not an existing eligible data product. Preserve the contract and evidence as governance records; do not implement or promote it under this task.
- **Connection sidecar and validation reports:** separate RET-07 evidence group; no expiry decision in this RET-03 record.
- **Unknown files/copies/recipients:** protected and BLOCKED_UNKNOWN until a separately authorized inventory and owner adjudication establish identity and scope.

A consumer release, source file hash, successful import, snapshot replacement, daily partition boundary, local age, or absence of a known consumer does not establish a retention terminal event.

## 8. Stage A.2 outcome

**T1 data-product map:** DOCUMENTED for the in-repository source paths described by the pinned trace.

**T1 obligation resolution:** NOT COMPLETE. The authoritative owner inputs needed to establish purposes, scope, start/end events, duration bases, consumer closure, copy graph and holds were not present in the inspected repository records and were not supplied in this task.

**RET-03 for T1:** OPEN — FLOOR_NOT_ESTABLISHED — NO NUMERIC FLOOR / TTL SELECTED.

No T1 data class or object is made deletion-eligible. No inference is made that T1 data may be deleted after use. The central lifecycle policy's demand-based rule remains controlling: a read, download, successful job or consumer ACK is never by itself a deletion trigger.

## 9. Verification, provenance and limits

- Repository branch baseline: `c0823759c96362d79174b90d29ec4bde1c9b8ef3`.
- Exact source blobs are listed in §2.
- Work performed: GitHub document retrieval and static documentary analysis only.
- Tests: **NOT RUN**.
- GitHub Actions: **NOT DISPATCHED**; no workflow run or artifact.
- External T1 repository, VPS, runtime, CSV files, DB, provider, exchange and consumers: **NOT ACCESSED**.
- Operational data/copy/backup/recipient inventory: **NOT PERFORMED**.
- Legal/contractual determination: **NOT PERFORMED**.
- Source, workflow, schema, API, adapter, runtime, permissions, credentials and data: **UNCHANGED**.
- T1 collector activation, implementation, staging, restore, fault injection and destructive tests: **NOT AUTHORIZED / NOT PERFORMED**.
- Archive, expiry, cleanup, compaction, vacuum, backup/replica removal, export mutation and deletion: **NOT AUTHORIZED / NOT EXECUTED**.
- Option C, T0 independence, separate ledgers, paper-only and `AI_EXECUTION_ENABLED=false` remain unchanged.

**Final status: T1 RET-03 STATIC CLASS/DEPENDENCY MAP COMPLETE — OWNER INPUTS NOT PROVIDED — RET-03 OPEN — NO NUMERIC FLOOR OR DESTRUCTIVE AUTHORITY.**
