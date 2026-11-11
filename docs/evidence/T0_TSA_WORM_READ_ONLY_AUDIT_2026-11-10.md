# T0 TSA and WORM Read-Only Audit

- Date: 2026-11-10 UTC
- Repository: `kenznguyen/btcusdt-telegram-signals2`
- Branch: `feature/t0-centralized-data-feeder-p1-20261101`
- Source HEAD: `326ebd3723587323aa39660777becd44ed273105`
- Source tree: `4c48cfa3ea45c339f8c6b395f06ca6533252ba32` (`truncated=false`, 711 entries)
- Work type: bounded, read-only source and documentary review
- Overall verdict: **TSA PRODUCTION BLOCKED; WORM NOT IMPLEMENTED/NOT QUALIFIED FOR T0; T0 RETENTION POLICY PROTECTIVE BUT NOT A TECHNICAL WORM CONTROL**
- No source, schema, runtime, VPS, SQLite/PostgreSQL, Feeder, provider, credential, key, permission, workflow or data changes were made.

## 1. Executive result

The current T0 implementation is a canonical closed-candle market-data store and Feeder. The reviewed `market_data` source does not implement a TSA client/verifier, a signed immutable checkpoint, a timestamp outbox, or an RFC 3161 evidence archive. It also does not implement a WORM storage adapter or provider lock configuration.

TSA and WORM material in the repository is principally **target architecture, documentary policy, provider research, and synthetic evidence tooling**. It must not be represented as deployed T0 capability.

A critical scope distinction: the forward-evidence Root A/Root B WORM architecture concerns retained execution/evidence envelopes and independent observer checkpoints. The storage architecture decision explicitly says T0 is not part of that decision. It is not evidence that T0's canonical candle database is WORM-protected.

## 2. TSA findings

### TSA-01 — No production TSA path in T0 source (HIGH)

The branch-pinned source mapping in P1.8.77 identifies T0 as a candle-oriented store, not an event ledger with signed checkpoints. The current `market_data` inventory is consistent with that finding:

- `market_data/store.py` (`4e1b0c54bd56455abe5be0e5c7d0807e63e0bc78`) stores candle rows and computes `datasetVersion` as SHA-256 over a selected read-window response.
- `market_data/write_gateway.py` (`b2029d9db15fe39dcbe575acfeb6df1b16e16acd`) implements fenced candle writes and a SQLite WAL keeper; no TSA submission or token verification path is present.
- `market_data/feeder.py` (`935d295ef42c94482a48ce6ccdc927ebfa4c7e22`) schedules UTC candle windows and keeps the last-completed boundary in process memory.
- `market_data/feeder_service.py` (`bdcecf6bc98a2ff070f83098d2c50154a160c99c`) composes the Feeder runtime; it does not add a signed checkpoint/TSA lifecycle.
- PostgreSQL migrations 001–004 (`777d884d...`, `009474f...`, `1e08f77a...`, `cc79631a...`) define instruments/candles, leases, fenced candle writing and lease APIs; no TSA/checkpoint/evidence schema was identified.

Consequences:
- `datasetVersion` is not a whole-database digest, immutable checkpoint, signed object, or proof of durable commit.
- The in-memory scheduler boundary is not a durable V08 watermark/checkpoint.
- No durable timestamp-intent/outbox, RFC 3161 request/response store, TSA certificate-chain archive, OCSP/CRL archive, or independent TSA verifier exists in the inspected T0 source set.

### TSA-02 — Timestamp subject is not decided for T0 (HIGH)

P1.8.77 identifies two non-equivalent possible products:

A. Dataset/checkpoint proof-of-existence: a deterministic manifest commits to a defined, complete candle dataset/checkpoint; TSA proves that exact manifest commitment existed no later than the asserted `genTime`.

B. Signed-object historical verification: TSA imprint binds exact signature bytes and immutable verification context under P1.8.36/V07.

The current T0 candle path supplies neither a signed checkpoint nor the signer/key/revocation lifecycle required by B. A dataset digest under A must not be described as satisfying B. An explicit owner decision is required before source design: A, B, or two separately versioned products.

### TSA-03 — Durability and trusted-time gates remain open (HIGH)

P1.8.77 notes that source inspection does not establish project-specific SQLite `PRAGMA synchronous`, fsync, checkpoint policy, power-loss durability, or host/storage failure-domain guarantees. PostgreSQL transaction completion likewise does not by itself establish the required host-loss/power-loss guarantee or synchronous replication.

The WAL keeper work has disposable CI evidence (recorded in `docs/evidence/t0/T0_SQLITE_WAL_COLD_START_LIFECYCLE_2026-11-08.md`), but that evidence proves WAL sidecar lifecycle/read-only-reader behavior on disposable runners, not a production D0–D4 durability class or RPO.

P1.8.152 still records:
- V07 trusted-time/revocation: **BLOCKED** (trust authority/profile, trust-anchor lifecycle, TSA protocol, algorithms/encoding, uncertainty, revocation semantics, freshness/propagation/equality and provider proof remain open).
- V08 checkpoint/seal: **OPEN/BLOCKED** (actual durable commit/seal ordering, ordering token, partition progress, watermark/lateness and clock parameters remain open).
- Restore: **OPEN/BLOCKED**; recorded RPO/RTO values are planning targets, not measured capability or approved SLOs.

### TSA-04 — Architecture is sound as a target boundary, not an implementation (DESIGN PASS / PRODUCTION BLOCKED)

P1.8.67 specifies TSA as optional, asynchronous and outside the authoritative T0 write path. TSA outage must not stop valid T0 ingestion. It requires durable intent, exact immutable-object binding, handling unknown submission outcomes and duplicates, preservation of raw tokens and historical OCSP/CRL material, and independent local verification.

P1.8.68 records an independent static review PASS of that architecture. P1.8.77 subsequently maps it against actual T0 source and finds implementation incompatibility/gaps. These are compatible findings: **the target architecture passed documentary review; production integration did not.**

Provider status:
- No TSA provider selected.
- GlobalSign is only the strongest documentary follow-up candidate in P1.8.64, not an approved provider.
- DigiCert remains a candidate with material public-document gaps.
- Sectigo's reviewed CPS restricts its TSA use to software signing with a Sectigo Code Signing Certificate.
- No provider contact, TSA request, OCSP query, certificate operation or interoperability test was performed.

## 3. WORM findings

### WORM-01 — No WORM control in T0 canonical storage (HIGH)

No WORM adapter, Object Lock/Bucket Lock policy, immutable storage account, or retention-lock configuration is present in the reviewed `market_data` source/migrations. SQLite WAL, transaction fencing, PostgreSQL lease fencing and Git history are not WORM.

T0's primary candle store remains an operational canonical database. WORM, if later required, should be treated as a separately governed evidence/archive copy and must not be inserted into the Feeder's synchronous write path.

### WORM-02 — Forward-evidence WORM architecture is not T0 WORM (HIGH)

The forward-evidence documents describe:
- Root A: append-only execution/evidence journal and immutable source segments.
- Root B: separately operated observer, independent reducer/projection and retained checkpoints.

The architecture decision review recommends a local encrypted spool plus two remote roots in separately controlled accounts as a target only; it explicitly excludes T0 from that decision. The Root B design is not proof of a second independent external source or of T0 candle immutability.

### WORM-03 — Provider candidates are not selected or tested (HIGH)

Documentary dispositions:
- AWS S3 Object Lock **Compliance Mode**: preferred Root A candidate; not selected or tested. Governance Mode is insufficient for the stated admin-resistance target. Account deletion remains a catastrophic failure boundary.
- Google Cloud Storage Bucket Lock: candidate for Root B disposable synthetic qualification; not tested. A privileged project/organization administrator can remove the project lien, so the administrative boundary remains material.
- Azure Blob immutable storage: candidate for Root B disposable synthetic qualification; not tested. Container-level and version-level semantics must be chosen and tested separately.
- Cloudflare R2 Bucket Locks: lower-assurance/conditional fallback. Authorized administrators can remove or replace lock rules; R2 is not equivalent to S3 Compliance Mode against account-admin compromise. Its Data Access Logs are best-effort and Audit Logs v2 have documented coverage/retention limits.

No Root B provider is finally selected. Two-root independence, separate ownership/admin/recovery identities, audit export, restore, provider exit, region and cost are not proven. The acceptance plan's ST-01–ST-20 remain a test plan, not executed evidence.

### WORM-04 — Synthetic evidence retention explicitly says NOT_WORM (HIGH)

`synthetic_evidence/trust_lifecycle.py` (`6d4e2cc481ea1ad45522a0f95e97660a8de22a77`) builds/verifies a synthetic retention manifest whose fields explicitly identify:
- `retention_class: GIT_HISTORY`;
- `immutability: NOT_WORM`;
- `actions_artifact_retention_days: 7`.

`synthetic_evidence/README.md` (`ccdb94fb8c42eab141ab5b375364dd1f9490782e`) says the generator is synthetic-only, has no account DB/network/cloud-provider/credential/runtime integration, and that local replay does not prove Root B process/admin/provider independence or provider durability. The SQLite Root B checkpoint store is a synthetic crash/durability model, not provider WORM. The offline verification script validates a GitHub artifact attestation against a pinned Sigstore root; it is not an RFC 3161 TSA client.

Therefore GitHub history and Actions artifacts provide useful source/provenance evidence, but **must not be called WORM storage**.

## 4. T0 retention and destructive-authority boundary

P1.8.143 records owner-ratified RET-01 B and RET-02 B:

- T0 canonical data is protected by default from routine, automatic or scheduled deletion.
- T0 canonical data and its availability/recovery copies are excluded from ordinary class-wide deletion review.
- Only specified noncanonical classes/copies may enter a future read-only exact-object/version eligibility assessment; that does not make them eligible by default.
- Any narrow legal/security exception requires separate evidence, competent review and a new explicit owner decision.

This is a governance protection, **not technical WORM enforcement**. P1.8.152 records RET-03 and RET-06–RET-10 still open/not verified; no numeric retention floor or object's eligibility is established. Option C — No Destructive Authority — remains in force; archive and irreversible transitions remain non-executable.

## 5. Consolidated status

| Component/claim | Status | Basis |
|---|---|---|
| TSA target architecture | PASS — documentary/static only | P1.8.67 and P1.8.68 |
| TSA mapped to current T0 | BLOCKED | P1.8.77; no signed checkpoint/outbox/RFC 3161 path |
| TSA provider/profile/trust/revocation | BLOCKED / OPEN | P1.8.64–65 and P1.8.152 |
| T0 durable checkpoint/seal | OPEN / BLOCKED | P1.8.77 and P1.8.152 |
| WORM in T0 canonical store | NOT IMPLEMENTED / NOT VERIFIED | Current `market_data` source/migrations |
| Forward-evidence WORM provider research | DOCUMENTARY REVIEW COMPLETE; candidates only | Storage vendor and second-provider reviews |
| Root A/Root B provider qualification | NOT RUN | Acceptance plan ST-01–ST-20 |
| Synthetic local Root B | PASS only as synthetic model | Not provider/admin/process independent |
| GitHub/Actions evidence as WORM | REJECTED CLAIM | Retention manifest explicitly says NOT_WORM |
| T0 retention policy | OWNER-RATIFIED PROTECTION | RET-01 B; not technical WORM |
| Runtime copies/provider inventory | NOT PERFORMED / NOT VERIFIED | P1.8.152 |
| Independent second review of this audit | NOT PERFORMED | This is a bounded review, not an independent review |

## 6. Recommended next gates (no execution authorized)

1. Resolve the owner-level TSA subject decision for T0: dataset manifest/checkpoint (A), signed-object historical verification (B), or two separately versioned products.
2. Before any TSA implementation proposal, define the exact immutable object, canonical bytes, completeness/membership, durable-commit boundary, outbox recovery, timestamp profile and historical revocation contract. Keep TSA asynchronous and off the Feeder write path.
3. Make an explicit scope decision whether WORM is required for T0 canonical market data itself or only for separately governed evidence/archive copies. Do not conflate the forward-evidence Root A/Root B proposal with T0.
4. If WORM is required, choose a provider-neutral threat model first, then separately approve a disposable synthetic qualification plan. No provider/account/region purchase or provisioning is implied.
5. Preserve T0 canonical data and its recovery copies. Do not add automatic deletion/expiry or irreversible retention locks without separate review and explicit authorization.

## 7. Verification and authorization

- Source ref: `326ebd3723587323aa39660777becd44ed273105`; tree: `4c48cfa3ea45c339f8c6b395f06ca6533252ba32`.
- Inspected source/document blobs are identified above and in P1.8.77 / referenced records.
- Tests: **NOT RUN** (read-only audit).
- GitHub Actions: **NOT DISPATCHED**; no workflow run or artifact.
- Runtime/database/provider/credential/key/permission inventory: **NOT PERFORMED**.
- TSA calls, OCSP/CRL queries, provider contact, account provisioning, restore and fault injection: **NOT AUTHORIZED / NOT PERFORMED**.
- Source/schema/API/runtime/VPS/Feeder/SQLite/PostgreSQL/data changes: **NONE**.
- Archive, cleanup, vacuum, compaction, backup expiry, replica removal and deletion: **NOT AUTHORIZED / NOT EXECUTED**.
- `AI_EXECUTION_ENABLED=false`; paper-only; no live orders.
- Option C — No Destructive Authority — remains in force.

**Final verdict: BOUNDED READ-ONLY AUDIT COMPLETE — TSA PRODUCTION BLOCKED — WORM NOT IMPLEMENTED/NOT QUALIFIED FOR T0 — NO RUNTIME OR DESTRUCTIVE ACTION.**


## Superseding owner decision — Option C revoked (2026-11-11)

The project owner explicitly revoked **Option C — No Destructive Authority** on 2026-11-11. This dated owner decision supersedes the earlier approval/rule in this historical record wherever it states that Option C remains in force, is the current default, or prohibits all destructive authority. Current governance status: **Option C REVOKED**.

The revocation removes Option C as a blanket prohibition; it does not itself authorize a particular deletion, archive, cleanup, expiry, vacuum, compaction, replica removal, export mutation, provider operation or other destructive transition. Each concrete operation remains subject to a separate explicit approval with exact target/data class, scope, preconditions, expected effect, verification, dependencies and recovery/rollback plan. T0 canonical SQLite/candles, lease/fencing state, CORE_LEDGER, AI_LEDGER, audit/reconstruction/recovery evidence, owner custody records and trust evidence are not presumed disposable. Paper-only status and `AI_EXECUTION_ENABLED=false` remain unchanged. This governance change does not establish technical enforcement, L4 control PASS, independent assurance, or permission to change runtime/provider credentials.
