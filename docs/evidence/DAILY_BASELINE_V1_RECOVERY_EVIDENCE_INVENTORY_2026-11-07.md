# Daily Baseline v1 Recovery — Repository Evidence Inventory

**Inspection status:** READ-ONLY SOURCE/SCHEMA INVENTORY  
**Result:** BLOCKED for v1-to-v2 historical recovery using repository-retained evidence alone.  
**No account database was opened. No migration, backfill, or data mutation was performed.**

## Exact source inspected

Branch: `feature/t0-centralized-data-feeder-p1-20261101`  
Branch HEAD at inspection start: `ae9ee62b27cb67de2df755dc1f524ae1558c93e5`

| File | Blob SHA | Relevant evidence |
|---|---|---|
| `paper_execution/account_history.py` | `6163065798b2386e1c466650048e40b7eab0d2eb` | v6 event journal, coverage and mark history; v7 per-ledger cutover snapshots; v9 immutable baseline audit |
| `paper_execution/ledger.py` | `0bc94ae0e704a69e253246a575991c1de436e0a4` | mutable current risk-state row; mutable order/audit tables; event journal writes |
| `paper_execution/funding.py` | `575758eb3223b4341ac37bad56d58e52539305c0` | immutable funding events/coverage; immutable cutover; cutover HWM snapshot; mutable risk-state refreshes |
| `paper_execution/equity.py` | `40d6566294355c646839614c92f8fba6116b582c` | legacy single-strategy equity history and first-observed daily baselines |
| `paper_execution/risk_control.py` | `3c76e462b0b4d924c2418842d95ed74285e2315d` | shared kill/pause latch; no historical account risk-state snapshots |

## Findings

### 1. Immutable evidence that exists

- v6 `paper_account_event_journal` is append-only and records event time, recorded time, strategy owner, order/intent/source IDs, signed fill/adjustment data, fee amount/currency (v8), source snapshot, payload hash and canonical payload.
- v6 `paper_account_history_coverage` is append-only and can attest VERIFIED/UNKNOWN execution and market-mark intervals independently for Core, AI and Legacy.
- v6 `paper_market_mark_history` is append-only, has a unique mark per effective timestamp, and records exact boundary mark, candle close, source snapshot, dataset version, hash and quality status.
- v7 `paper_account_cutover_ledger_snapshots` is append-only and stores Core/AI/Legacy positions, average entry, realized PnL, fees, funding and provenance at the one verified cutover.
- v4 funding events and funding coverage are append-only with source/recorded timestamps, coverage status, source snapshot and hash. Legacy events are marked `LEGACY_UNVERIFIED`; they cannot be treated as verified.
- v5 `paper_account_equity_cutovers` is append-only and stores cutover equity, mark, funding interval, HWM and daily baseline at cutover.
- v9 `paper_daily_equity_baselines` and `paper_daily_equity_baseline_audit` have immutable UPDATE/DELETE triggers. A v1 audit payload remains immutable, but it does not contain the v2 `riskState` snapshot.

These sources can support replay of some historical economics when complete coverage and provenance exist. Their presence does not prove the risk state at a later historical daily-baseline commit.

### 2. Required historical risk evidence is absent

- `paper_account_risk_state` is a single mutable row. Its HWM, daily baseline, last equity/mark, readiness, timestamp and version are overwritten as activity proceeds.
- No immutable per-day or per-version risk-state history table was found in the inspected `paper_execution` schema.
- The v7 per-ledger snapshots exist only at the cutover; they are not repeated at every daily baseline.
- `paper_account_equity_cutovers` preserves HWM/readiness inputs at the cutover only. It cannot establish HWM, readiness or `version` at a later daily baseline timestamp.
- The code increments the mutable risk-state version during fills/reductions and funding/equity refreshes, but those mutations do not create an immutable before/after risk-state snapshot.
- Therefore the historical `high_water_mark_quote`, `version` and `risk_ready` required by the v2 audit cannot be independently proven for a v1 baseline from these tables alone.

### 3. Other historical evidence limits

- `paper_audit` is created as a normal table without immutable UPDATE/DELETE triggers. It records order, funding and cutover events, but is not a tamper-resistant risk-state history.
- `paper_orders` stores aggregate order/fill state and is updated for lifecycle changes. It is not a complete immutable per-fill source for older history.
- `paper_equity_history` and `paper_daily_baselines` are legacy single-strategy history. The former is not protected by immutable triggers; the latter can be updated when an earlier observation arrives. Neither certifies the dual-ledger account HWM/version at a v1 baseline.
- v8 intentionally leaves historical fee currency unknown rather than guessing. Any pre-v8 journal row without explicit USDT currency blocks a complete fee reconciliation.
- Source payload hashes in local tables are syntax/provenance fields; repository code does not retrieve original external payload bytes and independently rehash them. The evidence manifest's raw-byte rehash attestation cannot be inferred from a stored hash string.

## Manifest assessment

| Manifest requirement | Repository-only result |
|---|---|
| Baseline row + immutable v1 audit pair | Schema supports it; actual persistent rows not inspected |
| Replay inputs, per-ledger cutover snapshots | Schema supports these sources; historical interval completeness not proven here |
| Continuous execution/funding coverage | Schema and validators support proof; actual persistent coverage not inspected |
| Exact boundary mark | Schema supports it; actual persistent mark not inspected |
| Independently verified historical risk snapshot at v1 baseline time | **NOT FOUND** |
| Original source payload bytes rehashed | **NOT AVAILABLE from repository schema/code alone** |

**Overall:** `BLOCKED`. The pure manifest assessor must not be given `risk_state.independently_verified=true` or raw-byte rehash attestations unless independently retained evidence is actually produced and verified. A current mutable risk row, cutover-only snapshot, audit digest, or legacy equity history cannot substitute for missing historical risk state.

## Safe handling

1. Keep v1 rows immutable and fail-closed.
2. Do not synthesize historical HWM, version, readiness, mark provenance, fee currency, or missing events.
3. Do not infer authenticity from stored hash syntax.
4. If independent external evidence is later found, assemble the manifest and assess it read-only; a positive result permits manual review only.
5. Any conversion/reconciliation transaction requires a separate explicit approval and its own RED/GREEN tests.

## Scope limits

This was a source/schema inspection only. It did not inspect a persistent account DB, enumerate real v1 rows, verify live data availability, migrate, backfill, deploy, connect to an exchange, or place orders. T0 remains paused; paper-only execution and `ai_execution_enabled=false` remain unchanged.


## 2026-11-07 — Independent archive/checkpoint repository scan

A second read-only inventory was performed against the recursive Git tree at branch commit 2eb17051dd93a9c36b1e9be45333168793546702 after the Dual Reconstruction contract was committed.

- Git tree contained 279 paths and was not truncated.
- No tracked files with database, SQLite, JSONL/NDJSON, CSV, Parquet, Arrow, archive, binary payload, checksum-manifest, or equivalent raw event/checkpoint data extensions were found.
- The evidence directory contains documentation reports/manifests, not a retained raw event archive or independent account checkpoint.
- The tree contains source code for the event journal, funding, ledger and baseline logic; source code is not a second evidence root.
- The scan does not enumerate or download GitHub Actions artifact payloads, private Project attachments, local PC/Android files, or any separately retained external archive. Those sources remain NOT INSPECTED.
- The prior immutable event journal/coverage/mark tables and cutover snapshots described above are schema capabilities. Because the persistent account DB was not opened, their actual rows, completeness, raw source bytes, and independence from a second checkpoint remain NOT VERIFIED.

**Result:** INDEPENDENT_SECOND_ROOT_NOT_FOUND_IN_TRACKED_GIT_TREE. The repository alone currently provides no discoverable separately retained event archive/checkpoint suitable for Reconstruction B. This does not prove that no such evidence exists outside the tracked Git tree. Do not treat a pair of computations over the mutable account DB as independent verification. Keep the candidate BLOCKED unless an external retained evidence root is identified and byte-verified.

No account DB was opened; no artifacts were downloaded; no source, schema, tests, workflow, migration, or data were changed.


## 2026-11-07 — GitHub Actions artifact metadata review

Read-only artifact metadata was checked for five prior T1 verification runs. No artifact ZIP was downloaded or extracted.

| Run ID | Source SHA | Artifact ID | Name | Size | ZIP SHA-256 digest | Expires |
|---|---|---:|---|---:|---|---|
| 42277853667 | 7cddb5eacfd70f5bc886bc03f672177cdf3f8f2a | 13533807345 | dual-ledger-red-evidence-7cddb5eacfd70f5bc886bc03f672177cdf3f8f2a | 8,452 B | fb41913d0826f836adf7b6c460efc6bd3d41f6af41f5e976764cc099c00376c9 | 2026-11-13 19:14:23 UTC |
| 42279162334 | fbf74c5d72ee977651b8075f13dadf9763b4b272 | 13534541826 | dual-ledger-red-evidence-fbf74c5d72ee977651b8075f13dadf9763b4b272 | 8,919 B | ac769ba03c657a4361d72eef3f794ac005cada4108395fc85e4719d6f1ea1ff0 | 2026-11-13 19:23:14 UTC |
| 42279706472 | 4eac10b704882c7f14901400be9d76465b0ffc44 | 13534577603 | dual-ledger-red-evidence-4eac10b704882c7f14901400be9d76465b0ffc44 | 8,971 B | f098522daedc72098025bf1cdd43efb4315e68f8613cfe0a10ce3865fe09955e | 2026-11-13 19:26:57 UTC |
| 42280083080 | f7df95c2ff2008aa88923b3242b1486c096d9342 | 13533829670 | dual-ledger-red-evidence-f7df95c2ff2008aa88923b3242b1486c096d9342 | 9,017 B | 518596b09e16712d2c5ed157baa85168fd6c960ffbf5a7414ee9d6d547195275 | 2026-11-13 19:29:36 UTC |
| 42276535949 | e06b28b740590b99c4c930004bf547c8fccbaf99 | 13533163461 | dual-ledger-red-evidence-e06b28b740590b99c4c930004bf547c8fccbaf99 | 8,189 B | 62557812142e7aa84aa238c4c6a4dd99a851c9116beeeca2dd1a1893abc0f88e | 2026-11-13 19:05:23 UTC |

Assessment:
- All five artifacts are named as CI RED evidence and are tied to specific test source SHAs. Their small sizes and names identify them as test evidence packages, not as retained account event archives/checkpoints.
- The artifact digest is the SHA-256 of the GitHub Actions artifact archive. It does not establish that the archive contains original account event bytes or a separately retained account checkpoint.
- Artifact payloads were not downloaded or inspected; content-level classification is therefore NOT VERIFIED.
- These artifacts are useful for source/test provenance and historical CI audit only. They are not eligible as Replay A or Reconstruction B evidence roots based on metadata alone.
- They remain unexpired at the time of inspection; retention ends on 2026-11-13 UTC as listed above.

**Result unchanged:** no independent account event archive/checkpoint has been identified. The five CI artifacts do not clear the Dual Reconstruction evidence gate.


## 2026-11-07 — CI artifact producer workflow inspection

Inspected `.github/workflows/dual-ledger-red.yml` at branch HEAD `88a0235df85ba15eeb194e4f013d7ecab444543d` (workflow blob `c7c3e16026c6b5f01b6be1a7d2f1c504a532607a`).

The workflow establishes:
- `PAPER_DB`, `MARKET_DATA_DB`, Binance credentials, and OKX credentials are explicitly empty.
- Preflight logs `DUAL_LEDGER_MODE=PAPER_ONLY`, exact source SHA, and `DUAL_LEDGER_EXTERNAL_SERVICES=NONE`.
- It compiles test/source files and runs focused + full `paper_execution` unittest suites.
- The artifact upload allowlist contains only four text logs: `dual-ledger-preflight.log`, `dual-ledger-compile.log`, `dual-ledger-red-tests.log`, and `paper-execution-regression.log`.
- No account database, event journal export, account checkpoint, market data payload, or raw trading record is included in this workflow's artifact path list.

This workflow-level inspection independently confirms that artifacts named `dual-ledger-red-evidence-<SHA>` are test/provenance logs by design, not an account event archive or account checkpoint. Payload download is unnecessary for this classification. It does not establish whether other workflows, private artifacts, or external storage contain a separate evidence root.

**Result:** `DUAL_LEDGER_RED_ARTIFACTS_ARE_TEST_LOGS`. They are not eligible for Replay A or Reconstruction B. No artifact payload was downloaded; no database was opened.


## 2026-11-07 — Remaining workflow artifact allowlist review

Inspected every workflow file under `.github/workflows/` at branch HEAD `88a0235df85ba15eeb194e4f013d7ecab444543d`. Relevant artifact upload allowlists classify as follows:

| Workflow | Uploaded artifact content | Account event/checkpoint evidence? |
|---|---|---|
| `dual-ledger-red.yml` | Preflight, compile, focused test, full regression logs | No |
| `p5-3-11-g2-integration-green.yml` | Source SHA, isolation, compile, gateway/feeder/T0/consumer test logs, verdict | No |
| `paper-writer-isolation-red.yml` | Static contract test log | No |
| `t0-manual-validation.yml` | Source SHA, isolation/runtime/config reports, component/provider/SQLite/Timescale test logs | No |
| `t0-postgres16-grantor-repro.yml` | PostgreSQL grantor reproduction log | No |
| `t0-single-writer-gateway-red.yml` | T0 preflight, compile, contract/behavior/health/restart/market-data tests; disposable Timescale integration logs; paper consumer test log | No |
| `android-release-pair.yml` | Signed APKs, source identity manifest, release-pair manifest, Android test results/reports | No |

The T0 PostgreSQL/Timescale workflows use disposable test databases and upload test logs, not account trading history. The Android release artifact contains application binaries and test reports, not a historical account archive/checkpoint. No workflow upload allowlist identifies raw Core/AI/Legacy events, fills, positions, funding/fee records, or an independently retained account snapshot.

**Repository CI artifact search conclusion:** no currently tracked workflow is configured to publish a qualifying Replay A event archive or Reconstruction B account checkpoint. This is based on workflow source allowlists, not on inspection of every historical artifact payload. It does not rule out private Project files, local PC/Android exports, or external archival storage.

Result: `NO_QUALIFYING_ACCOUNT_EVIDENCE_ARTIFACT_IN_TRACKED_WORKFLOWS`. Keep the independent reconstruction gate BLOCKED; do not use CI logs, APKs, or disposable T0 test database evidence as account history.


## 2026-11-07 — User confirmation: no independent archive/checkpoint currently exists

- User confirmed that no independent event archive or checkpoint is currently available.
- Combined with the tracked Git tree inventory and workflow artifact allowlist review, there is no identified second evidence root available for historical Dual Reconstruction at this time.
- Historical reconstruction/independent verification is therefore **UNAVAILABLE / BLOCKED**, not merely awaiting another repository search. Do not manufacture a second root by exporting the same mutable account DB, replaying CI fixtures, or treating CI logs as account history.
- Preserve Option A (strict predecessor chain) as the current operational policy. Do not activate a new epoch, reset HWM/daily baseline, or admit new exposure based on an unverified anchor.
- A future independently retained archive/checkpoint can support a new review only from the point it is actually captured and retained with independent provenance; it cannot retroactively prove missing historical events.
- Forward-looking work may specify a capture/retention protocol, but no source/schema/database writer or persistent storage changes are authorized by this confirmation.


## 2026-11-07 — Prospective evidence capture protocol drafted

Created `docs/architecture/FORWARD_EVIDENCE_CAPTURE_RETENTION_PROTOCOL_2026-11-07.md`, commit `8601a6922fcaa41cf35e58431480f3ae4b832088`.

The proposal defines:
- Root A: append-only, hash-linked execution event journal at the paper state-transition boundary.
- Root B: separate observer process, independently implemented projection/checkpoint, separate storage namespace and credentials; it consumes committed event envelopes and does not query mutable account DB rows.
- Explicit assurance levels: mutable-source exports are internal consistency only; independent retention/capture is LEVEL 1 with a disclosed common event-emitter trust boundary; independent external economic source would be LEVEL 2 and is not available/assumed.
- Canonical event provenance, event sequence, idempotency, durability ordering, checkpoint cadence, UTC boundary handling, immutable manifests, storage controls, recovery behavior, monitoring, and acceptance tests.
- A staged approval ladder from architecture/storage review through isolated tests and only later separately authorized persistent paper capture.

**Status:** documentation proposal only. No source, schema, workflow, storage, DB, or runtime changes. No provider/cost selected. Does not recreate historical data or change Option A. User approval is still required at each future implementation/storage/activation gate.


## 2026-11-07 — Forward evidence threat model reviewed

Created `docs/architecture/FORWARD_EVIDENCE_THREAT_MODEL_REVIEW_2026-11-07.md`, commit `61c152d138336915a9e6fc68b05c04d19e6dde86`.

The review records 30 threats, including fabricated upstream events, shared administrator/credential compromise, mutable-source observer contamination, hash-vs-authenticity confusion, signing-key loss/compromise, sequence/replay faults, writer/outbox crash split-brain, observer lag, common-mode reducer defects, clock/UTC errors, late events, unknown fee/funding, ownership errors, storage outage/retention deletion, compromised builds, privacy leakage, and false-green monitoring.

Critical trust-boundary conclusion: Root A and Root B may independently retain and compute, but they share the upstream event emitter and potentially host/operator/provider control planes. LEVEL 1 is not independent economic-source verification. SHA-256 proves byte integrity only; authenticated manifests require a separately controlled signing identity, whose key custody remains a trust dependency.

Open decisions are explicitly left unresolved: provider/region, storage-domain separation, retention, Root B lag threshold/outage policy, durability SLA, key custody, clock skew, RPO/RTO, privacy classification, and atomic outbox architecture.

Status: **PASS — threat model documented. NOT VERIFIED — security controls/tests are not implemented or run.** No source, schema, workflow, storage, DB, or runtime changes; no provider selected; no persistent access authorized.


## 2026-11-07 — Forward evidence storage architecture comparison

Created `docs/architecture/FORWARD_EVIDENCE_STORAGE_ARCHITECTURE_DECISION_REVIEW_2026-11-07.md`, commit `d3b9cecea912bba6172b68d2c6fa4d35842682a6`.

Compared six storage patterns: local-only; two namespaces in one cloud account; separate accounts under one provider; two providers; local spool plus one remote root; and local spool plus two separately controlled remote roots.

Recommendation is conditional Pattern F (encrypted bounded local spool plus two remote roots in separately controlled provider accounts, preferably across providers). Pattern C (separate accounts under one provider) is a fallback only with explicit residual-risk acceptance. Two buckets in one account are not sufficient for a strong independence claim. Local PC storage is not an authoritative archive.

Defined capability requirements, disqualifiers, failure-domain behavior, retention/cost measurement inputs, restore requirements, and decisions required before vendor shortlist. No provider, region, retention duration, budget, credentials, or service was selected.

Status: **PASS — architecture comparison documented. NOT APPROVED — vendor selection, purchase, provisioning, storage access, or runtime capture.** No source/schema/workflow/DB/runtime changes. Historical evidence remains unavailable; Option A unchanged.


## 2026-11-07 — Forward evidence storage acceptance plan

Created `docs/architecture/FORWARD_EVIDENCE_STORAGE_ACCEPTANCE_TEST_PLAN_2026-11-07.md`, commit `41d67ea9b57b6398506e4d539d0e62723e33bc51`.

The vendor-neutral plan defines 20 qualification tests covering account/admin separation, least privilege, object immutability and lock activation timing, version identity, independent restore of both roots, cross-root isolation, read-back SHA-256, signing-key separation, event sequence/replay, observer lag/outage, partial upload/crash, local spool bounds, one-root loss, retention/legal hold, region/jurisdiction, cost envelope, audit trail, and provider exit.

It includes candidate-specific verification questions for AWS S3 and Cloudflare R2, but explicitly classifies both as candidates only. It does not select a provider, region, account, retention period, budget, lag threshold, or key custody model. The proposed 5-minute warning / 15-minute block remains unapproved and must not be treated as runtime configuration.

Acceptance requires exact configuration provenance and passing mandatory tests using disposable accounts and synthetic data. No canonical account data, T0 database, exchange credentials, or production runtime may be used.

**Status:** PASS — documentation draft committed. NOT RUN — provider tests. NOT APPROVED — provider selection, purchase, account creation, credentials, provisioning, source/schema/workflow/database/runtime changes, or persistent capture. Historical Dual Reconstruction remains UNAVAILABLE / BLOCKED; Option A unchanged. T0 remains paused; PAPER-only; `ai_execution_enabled=false`.


## 2026-11-07 — Vendor security review

Created `docs/architecture/FORWARD_EVIDENCE_STORAGE_VENDOR_SECURITY_REVIEW_2026-11-07.md`, commit `13c6f8b5ca63bab0950a1e0d56e0321d6fd88500`.

Official documentation review findings:
- AWS S3 Compliance Mode provides stronger documented object-version WORM protection than Governance Mode, including resistance to delete by the account root during retention; deletion of the associated AWS account is a catastrophic exception.
- S3 Object Lock protects specific versions; simple DELETE can create a delete marker and new PUTs can create new versions. Recovery and manifests must bind exact version IDs.
- Cloudflare R2 Bucket Lock rules protect objects while active but can be removed/replaced by authorized bucket-configuration administration. R2 is therefore only a conditional Root B candidate, not equivalent to S3 Compliance Mode against admin compromise.
- R2 Data Access Logs are best effort and omit HTTP 400+; Cloudflare Audit Logs v2 have 18-month retention and documented coverage gaps. They cannot be the sole complete evidence record.
- Revised recommendation: AWS S3 Compliance Mode remains preferred Root A candidate; R2 is conditional Root B candidate, with asymmetry explicitly disclosed. If admin-compromise resistance is required for both roots, reconsider a second separately administered WORM-capable root.

Acceptance plan amended with additional mandatory tests for S3 delete markers/version IDs, account-level bypass boundaries, R2 lock-rule administration, writer token scope, audit-log omissions and external audit retention. Amendment commit: `a6cbbd84771fe6b5f3943131eeafd83f05f353e4`.

**Status:** PASS — official documentation review and test-plan amendment recorded. NOT VERIFIED — live account behavior, region, cost, key custody, and independent restore. NOT APPROVED — provider selection, account creation, purchase, credentials, provisioning, or capture. No source/schema/workflow/database/runtime changes. Historical Dual Reconstruction remains UNAVAILABLE / BLOCKED; Option A unchanged; T0 paused; PAPER-only; `ai_execution_enabled=false`.


## 2026-11-07 — Second WORM provider review (P1.3)

Created `docs/architecture/FORWARD_EVIDENCE_SECOND_WORM_PROVIDER_REVIEW_2026-11-07.md`, commit `952d8a4a86c25a86979d8826620375b9459de517`.

Official documentation review compared Google Cloud Storage Bucket Lock and Azure Blob immutable storage as potential cross-provider Root B candidates alongside AWS S3 Compliance Mode as the preferred Root A candidate. GCS locked bucket retention cannot be reduced or removed and applies a project lien, but a sufficiently privileged project owner/organization administrator can remove the lien. Azure locked time-based WORM policies cannot be shortened/deleted; Microsoft documents storage-account deletion barriers while protected containers/versions remain, subject to exact policy scope and conditions. Cloudflare R2 remains a lower-assurance fallback because its lock rules can be administratively changed.

Acceptance plan amended with GCS policy/lien/audit/version restore tests, Azure container/version WORM and account-deletion tests, and cross-provider admin separation/clean-room restore tests. Amendment commit: `67c8304f91f0c6e318d6cb59ff8a119342654452`.

**Status:** PASS — official-documentation comparison and test-plan amendment committed. NOT VERIFIED — live provider behavior, project/account deletion paths, restore, audit export, region, cost, and key custody. NOT APPROVED — provider selection, account creation, purchase, credentials, provisioning, storage access, or persistent capture. No source/schema/workflow/database/runtime changes. No CI run (documentation-only). Historical Dual Reconstruction remains UNAVAILABLE / BLOCKED; Option A unchanged; T0 paused; PAPER-only; `ai_execution_enabled=false`.
