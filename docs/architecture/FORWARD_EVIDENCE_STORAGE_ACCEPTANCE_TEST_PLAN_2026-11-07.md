# Forward Evidence Storage — Acceptance Test Plan

Date: 2026-11-07
Status: DOCUMENTATION DRAFT — NOT APPROVED FOR PROVISIONING OR IMPLEMENTATION

## 1. Purpose and scope

Define a vendor-neutral qualification plan for the prospective Pattern F evidence architecture:
- Root A: append-only event journal and immutable source segments.
- Root B: separately operated observer, independent reducer/projection, and retained checkpoints.
- Local PC: encrypted, bounded spool only; not an authoritative archive.

The prior vendor shortlist (AWS S3 as a possible Root A candidate and Cloudflare R2 as a possible Root B candidate) is a research hypothesis only. Neither provider, region, account, product tier, nor configuration is selected or approved by this document.

This plan is documentation-only. It does not authorize account creation, purchase, credentials, storage access, source/schema/workflow changes, database access, runtime capture, or exposure-policy changes. T0 remains paused. Paper-only; `ai_execution_enabled=false`.

## 2. Qualification principles

1. Test actual configured behavior, not product labels or marketing claims.
2. A PASS must be tied to exact provider product, region, account separation, policy snapshot, test date, test identity, object/version IDs, and evidence hashes.
3. Root A and Root B must be independently readable and recoverable. One root's writer identity must not administer or delete the other.
4. Root B must consume committed event envelopes and retain its own evidence; it must not rebuild its checkpoint by querying mutable account DB rows.
5. Hash equality proves byte equality for the compared bytes; it does not independently prove event authenticity or completeness.
6. A second copy is not an independent evidence root unless its trust boundary, credentials, retention, and recovery path are documented.
7. Missing evidence, ambiguous provider semantics, or untested administrative bypass behavior means NOT VERIFIED or BLOCKED, never PASS.

## 3. Test matrix

| ID | Test | Procedure / evidence required | PASS condition | Failure disposition |
|---|---|---|---|---|
| ST-01 | Account and admin separation | Inventory account owners, billing owners, recovery identities, MFA, admin roles, break-glass identities, and audit destinations for both roots | No shared routine admin or writer credential; cross-root access is explicit, separately approved, and auditable | BLOCKED if one ordinary credential can silently administer both roots |
| ST-02 | Writer least privilege | Attempt only authorized create/read operations, then test overwrite, delete, retention change, policy change, and account-level administration using writer identities in an isolated test bucket | Writer can perform only its declared operations; denied operations are logged | BLOCKED if writer can bypass retention or permanently delete sealed evidence |
| ST-03 | Object immutability | Create versioned test objects; attempt overwrite/delete before and during retention using writer and separately authorized admin identities; capture provider responses and audit logs | Retained version remains byte-identical and undeletable under the declared threat model; bypass semantics are documented | BLOCKED if retention can be silently shortened or bypassed by runtime writer |
| ST-04 | Retention lock activation timing | Verify whether lock applies at object creation, bucket default, or after upload; test the interval before retention becomes effective | No unprotected acceptance window for evidence declared immutable | BLOCKED if a writer can replace/delete evidence before lock takes effect |
| ST-05 | Version identity and conditional append | Upload duplicate event/object IDs, conditional-create conflicts, and attempted overwrite; record stable version IDs | Duplicate/replay is rejected or deterministically recognized; every accepted version has stable identity | BLOCKED on ambiguous overwrite or version identity |
| ST-06 | Root A independent restore | Restore a selected sealed event segment and manifest using a recovery identity that does not depend on the application DB; verify bytes and hashes | Exact bytes and manifest are recovered; source DB is not required | NOT VERIFIED until a full restore is demonstrated |
| ST-07 | Root B independent restore | Restore observer inputs, reducer output, checkpoint and manifest without Root A's application credentials or mutable account DB | Root B can be inspected and recovered under its own documented path; dependency on Root A is explicit | BLOCKED if Root B is only a re-export from mutable DB rows |
| ST-08 | Cross-root isolation | Revoke Root A writer credentials and test Root B read/restore; separately revoke Root B writer credentials and test Root A read/restore | Compromise/revocation of one writer does not destroy access to the other root | BLOCKED if credentials or control plane are shared without accepted residual risk |
| ST-09 | Read-back integrity | Download each sealed object/version; compute SHA-256 from retrieved bytes; compare with signed manifest and independently recorded digest | All bytes match; mismatches are retained as incidents, never overwritten in place | BLOCKED on any unexplained mismatch |
| ST-10 | Manifest authenticity and key separation | Verify signature using a public verification key; test signing-key access boundaries, rotation, recovery, revocation and compromise procedure | Signing identity is separate from both storage writers; recovery and revocation are demonstrated | NOT VERIFIED if only an unsigned hash manifest exists or key custody is untested |
| ST-11 | Event sequence and replay | Inject duplicate IDs, repeated sequence numbers, gaps, out-of-order delivery, and replayed envelopes in synthetic tests | Duplicates are idempotently handled; gaps/out-of-order conditions are surfaced and cannot be marked complete | BLOCKED if missing events can be silently skipped |
| ST-12 | Root B lag and outage | Simulate delayed observer, unavailable provider, retry exhaustion and recovery; measure watermarks and lag | Distinct Root A/Root B watermarks are visible; proposed 5-minute warning / 15-minute exposure block are tested only after explicit policy approval | NOT RUN until thresholds are approved; fail closed for new exposure when evidence readiness is unknown |
| ST-13 | Partial upload and crash | Terminate upload/client at each stage; restart and reconcile multipart/incomplete objects | No partial object is treated as sealed evidence; retry is idempotent and auditable | BLOCKED if incomplete bytes can be accepted as complete |
| ST-14 | Local spool bounds | Fill spool to configured limits; simulate PC loss, disk full, clock rollback and network outage | Spool is encrypted, bounded, observable; no silent deletion; remote acknowledgement is required before eviction | BLOCKED if spool overflow loses unacknowledged events |
| ST-15 | Recovery from one-root loss | Make one root unavailable or treat it as compromised; recover and inspect the other root | Remaining root remains independently readable; certification state is downgraded and incident recorded | BLOCKED if both roots share an unrecognized single failure domain |
| ST-16 | Retention and legal hold | Verify minimum retention, legal hold, expiry, deletion authorization, and account-closure behavior against current terms and configured policy | Data lifecycle is deterministic, documented and compatible with required retention | BLOCKED until legal/retention requirements are decided |
| ST-17 | Region and jurisdiction | Capture provider region identifiers, data-location guarantees, replication behavior, subprocessors and contractual terms | Actual location and cross-region behavior meet an explicitly approved jurisdiction policy | NOT VERIFIED while Singapore is only a preference and exact placement is unconfirmed |
| ST-18 | Cost envelope | Measure synthetic event sizes, object count, write/read/list requests, retention versions, retrieval, egress, key management and full restore | Normal, 2x, 10x and restore scenarios fit a separately approved budget with no surprise minimums | BLOCKED if projected spend exceeds approved cap or pricing is unclear |
| ST-19 | Audit trail | Inspect immutable/auditable records for writes, reads, denied deletes, policy edits, key operations and admin actions | Security-relevant operations are attributable and exportable to a separately protected destination | BLOCKED if privileged changes cannot be reconstructed |
| ST-20 | Provider exit | Export all retained objects, versions, manifests and metadata to a neutral destination; verify hashes and restore | Exit does not depend on a proprietary mutable DB; source remains intact until destination acceptance | NOT VERIFIED until full export/restore drill passes |

## 4. Candidate-specific qualification notes

### AWS S3 candidate

Verify, against current official documentation and an isolated account:
- Versioning state and exact Object Lock mode supported by the selected bucket.
- Compliance Mode versus Governance Mode semantics, including every bypass path.
- Whether Object Lock is enabled at bucket creation and how default retention applies.
- Object retention, Legal Hold, version deletion, lifecycle and replication interactions.
- IAM policy boundaries, root-account recovery, CloudTrail/audit coverage, and region selection.
- Full cost model: storage class, requests, retrieval, data transfer, versioning, retention, audit and key management.

Do not assume that enabling Object Lock alone proves account-level immutability or independent administration.

### Cloudflare R2 candidate

Verify, against current official documentation and an isolated account:
- Bucket Lock retention semantics, scope, activation timing and bypass/admin behavior.
- Object versioning and stable object/version identity available for the intended workflow.
- API token scope and separation from account-level administrators.
- Auditability of object writes, deletes, policy changes and administrative actions.
- Actual data-location controls and whether APAC preference guarantees a specific jurisdiction.
- Full cost model: storage class, Class A/B operations, retrieval, egress, retention and any related account charges.

Do not treat an APAC location hint as a guaranteed Singapore residency commitment.

## 5. Test execution controls

Before any live provider test, a separate approval must define:
- disposable test accounts/buckets and non-sensitive synthetic payloads;
- exact provider, product, region and account ownership;
- maximum spend and automatic budget alerts;
- test identities and least-privilege policies;
- approved retention duration and deletion/legal-hold semantics;
- signing-key generation, backup and recovery procedure;
- test window, cleanup plan for non-retained test objects, and incident contact.

No canonical paper account data, exchange credentials, T0 database, or production runtime may be used in qualification.

## 6. Acceptance gate

A candidate pair may be recommended for a controlled paper-capture pilot only when:
- all mandatory tests ST-01 through ST-11 and ST-13 through ST-20 are PASS;
- ST-12 thresholds have been explicitly approved and the lag/outage test passes;
- each result is tied to exact configuration and retained evidence;
- cross-provider/common-emitter limitations are stated;
- cost and jurisdiction are approved;
- a separate user approval authorizes provisioning and a later approval authorizes persistent capture.

Any BLOCKED or NOT VERIFIED mandatory test prevents acceptance. A successful storage test does not by itself authorize exposure increases, epoch activation, HWM reset, or Daily Loss baseline changes.

## 7. Current disposition

- Acceptance plan: DOCUMENTED DRAFT.
- AWS S3 / Cloudflare R2: CANDIDATES ONLY; NOT SELECTED.
- Cross-provider separation: RECOMMENDED TARGET; NOT APPROVED.
- Budget, retention, jurisdiction, lag thresholds, key custody: UNDECIDED.
- Provider accounts, purchase, credentials, provisioning: NOT AUTHORIZED.
- Test execution: NOT RUN.
- Source/schema/workflow/database/runtime: UNCHANGED.
- Historical Dual Reconstruction: UNAVAILABLE / BLOCKED.
- Option A strict predecessor chain: UNCHANGED.
- T0: PAUSED; Paper-only; `ai_execution_enabled=false`.


## 8. Vendor-review amendments (2026-11-07)

The subsequent official-documentation review identified additional mandatory tests:
- AWS Compliance Mode: verify delete/retention-change denial for bucket admin, IAM admin, and account root during retention; document deletion of the associated AWS account as a catastrophic exception.
- AWS version visibility: test simple DELETE/delete-marker behavior and prove recovery enumerates exact retained version IDs.
- AWS manifest identity: verify a new PUT cannot silently change the authoritative manifest reference; immutable manifests must be version-addressed and sealed.
- R2 lock-policy administration: prove lock-rule removal/replacement requires a separately held administrator and triggers an out-of-band alert/readiness failure.
- R2 writer scope: prove object writer token cannot edit bucket lock configuration, create/delete buckets, or administer the account.
- R2 audit gaps: demonstrate that best-effort Data Access Logs and Audit Logs v2 omissions are not treated as complete evidence; export required audit records to a separately controlled destination.
- Audit retention: qualify export beyond Cloudflare's documented 18-month native retention if longer audit retention is required.

See `docs/architecture/FORWARD_EVIDENCE_STORAGE_VENDOR_SECURITY_REVIEW_2026-11-07.md` for source-backed findings. These amendments are test requirements only; no tests were executed.


## 9. P1.3 second WORM provider amendments (2026-11-07)

The documentation review added Google Cloud Storage Bucket Lock and Azure Blob immutable storage as Root B candidates for synthetic-data qualification. Neither is selected or tested. AWS S3 Compliance Mode remains the preferred Root A candidate; Cloudflare R2 remains a lower-assurance fallback.

### Google Cloud Storage Bucket Lock
- Verify a locked retention policy cannot be reduced or removed by bucket administrators or project IAM principals.
- Verify object overwrite/delete and bucket deletion are blocked while retained objects remain.
- Verify the project lien is present and blocks project deletion; separately test the privileged owner/organization-admin lien-removal path and record that residual risk.
- Verify Object Versioning does not protect against whole-bucket deletion; test soft-delete recovery separately.
- Enable Data Access audit logs (disabled by default), retain Admin Activity logs, and export both to a separately controlled project/account. Test documented audit coverage gaps.
- Restore exact object generations and validate signed manifest references, size and SHA-256.

### Azure Blob immutable storage
- Select exact policy scope before testing: container-level WORM or version-level WORM. Do not assume identical semantics.
- Verify a locked time-based retention policy cannot be deleted or shortened; verify extension limits and legal-hold distinction.
- With retained synthetic blobs present, test container deletion and storage-account deletion through all supported management paths; record exact policy state and API responses.
- For version-scope mode, verify protected version deletion is denied and overwrite creates a distinct version; restore the exact version ID.
- Test expiry behavior, blob soft-delete recovery, and the separate effect of Resource Manager account locks.
- Export Azure management-plane Activity Logs and relevant storage diagnostics to a separately controlled account/provider.

### Cross-provider administrative separation
- For either GCS or Azure, prove the application writer cannot change retention, IAM, project/subscription ownership, billing, recovery identities or audit export.
- Prove privileged retention, IAM, lien, subscription and account actions alert an independently administered monitor.
- Bind immutable object identity (version/generation), byte length, SHA-256, retention metadata and signed manifest to every accepted evidence object.
- Perform clean-room restore using an identity that is not an administrator of either the source account or application host.

Reference: `docs/architecture/FORWARD_EVIDENCE_SECOND_WORM_PROVIDER_REVIEW_2026-11-07.md`.

These are test requirements only. No provider test, account creation, purchase, credential issuance, provisioning or persistent capture is authorized by this amendment.


## 10. P1.4 cost-model amendments (2026-11-07)

Reference: `docs/architecture/FORWARD_EVIDENCE_STORAGE_COST_MODEL_2026-11-07.md`.

Add mandatory cost qualification evidence before any candidate pair is accepted:
- Produce a region/SKU-specific quote for capacity, operations/transactions, retrieval, egress, replication/redundancy, versioning, audit logs, KMS/key operations, restore and tax.
- Measure event bytes, object counts, batching, manifest/checkpoint overhead, version multiplier and required audit volume using synthetic payloads; do not infer from guessed event sizes.
- Calculate retention-horizon accumulation for both roots separately. If retention is indefinite, model unbounded growth rather than a fixed bucket size.
- Include one full clean-room restore and post-restore verification in one-time and recurring cost scenarios.
- Produce pilot/expected/stress scenarios with source price timestamp, exact region/SKU, currency, tax/free-tier assumptions and retained calculator output.
- Demonstrate that the application writer cannot evade client-side request/byte ceilings. Configure provider quotas/restrictions where supported and out-of-band billing alerts.
- Prove the stop procedure disables further writes independently of budget alerts; reconcile final billing after usage reports settle.
- Treat budget notifications as alerts, not hard caps. AWS and Azure budget notifications can lag or do not stop consumption; Google spend caps are service-eligibility limited and enforcement is not instantaneous.
- Never delete or weaken retained WORM evidence to meet a budget. A candidate exceeding the approved budget is disqualified or requires a new explicit budget approval.

The USD 5/month figure is an illustrative research ceiling only. It is not approved, not a provider quote, and not demonstrated feasible. No account, purchase, provider test or persistent capture is authorized by this amendment.


## 11. P1.5 synthetic envelope and recovery contract amendments (2026-11-07)

Reference: `docs/architecture/FORWARD_EVIDENCE_ENVELOPE_RECOVERY_REQUIREMENTS_2026-11-07.md`.

Add these mandatory vendor-neutral acceptance tests before any source implementation or provider qualification:

- JCS canonicalization: RFC 8785 golden vectors, cross-language byte equivalence, UTF-8/no-BOM/no-trailing-newline, duplicate-key and invalid-Unicode rejection.
- Project canonical profile: reject financial floats, unsafe integer numbers, NaN/Infinity, ambiguous null/omission, unknown unversioned fields and invalid decimal-string grammar.
- Exact hash/signature vectors: verify domain-separated SHA-256 and Ed25519 message bytes; reject changed payload, hash, signature, key ID, revoked/unknown key and incorrect signing-time key status.
- Stream integrity: verify genesis sentinel, monotonic 20-digit sequence, previous-hash linkage, same-ID/same-bytes idempotency, same-ID/different-bytes rejection, duplicate-sequence rejection and gap blocking.
- Late events/corrections: preserve original event time and actual commit time; append corrections/supersessions without rewriting history; invalidate affected UTC boundary checkpoints.
- Manifest integrity: canonical signed manifest, event count, sequence range, byte length, segment SHA-256, previous manifest hash, exact object version/generation, retention read-back and non-authoritative mutable pointer behavior.
- Root B isolation: demonstrate that Root B cannot read the mutable account DB and can consume only committed Root A envelopes; verify separate reducer/checkpoint identity and receipt coverage.
- Replay safety: duplicate receipt, observer crash before/after checkpoint commit, acknowledgement loss and replay must not double-apply or skip committed events.
- Recovery completeness: cover Core, AI, Legacy/account-level ownership, fills, partial fills, order lifecycle, reservations, fees, funding, marks, config, risk decisions, Kill Switch, HWM and daily UTC baselines; UNKNOWN is never converted to zero.
- Fail-closed/backpressure: Root A/Root B outage, lag, sequence/hash/signature fault, spool full, disk full, key loss, retention drift and uncertain durable commit block new exposure increases; reductions/closures require a durable evidence path.
- RPO/RTO and restore: measure Root A durability, Root B catch-up, detection and clean-room restore against separately approved numeric thresholds. Do not use candidate bands as approved targets.
- Retention/key lifecycle: verify exact policy by evidence category, legal hold, key rotation/revocation history, public-key verification and clean-room decrypt/restore.
- Synthetic workload: derive bytes/day, objects/day, p95/max segment size, request counts, Root B throughput, spool growth and full restore cost from deterministic fixtures and exact source SHA.

Policy notes:
- Candidate RPO-A zero applies only to events acknowledged as durably committed by Root A; it is not yet qualified.
- Root B unavailable/behind is proposed to block new exposure increases immediately until contiguous verification catches up. This is a reliability-first proposal, not an approved runtime threshold.
- Candidate observation bands of 1/5/15 minutes are planning comparisons only. The previously documented 5-minute warning/15-minute block remains unapproved and must not be silently adopted.
- Candidate retention horizons 1/3/7 years and indefinite are comparison inputs only. No legal retention rule or jurisdiction is assumed.
- No provider, region, budget, account, credential, source implementation, schema migration, runtime capture or provider test is authorized by these test-plan amendments.


## 12. P1.6 deterministic synthetic fixture and measurement gates (2026-11-07)

Reference: `docs/architecture/FORWARD_EVIDENCE_SYNTHETIC_FIXTURE_MEASUREMENT_SPEC_2026-11-07.md`.

Before generator implementation or provider-specific tests, require:
1. Immutable run descriptor with fixture spec version, generator source/build SHA, fixed 256-bit seed, fixed UUID namespace, fixed UTC base time, event mix, payload profile, canonicalization/hash profile and segment policy.
2. Pure deterministic generation: HMAC-SHA-256 counter stream with domain-separated labels; UUIDv5 event IDs; fixed timestamps; stable stream sequencing and tie-break order; exact decimal strings. No wall clock, platform PRNG, filesystem order or runtime scheduling dependence.
3. Clean event distribution covering all P1.5 event classes plus separate negative vectors. Negative/invalid records must not contaminate clean baseline size/volume statistics.
4. Payload cohorts SMALL/MEDIAN/LARGE and separate STRESS cases; scale profiles 1k/10k/100k events plus burst and recovery fixtures. These are proposed test inputs, not measured workload.
5. JCS canonical event bytes, transport envelope bytes, segment bytes and signed manifest bytes measured separately. Report min/median/p90/p95/p99/max with sample counts and class/cohort identity.
6. Segment batching matrix B1 100/1 MiB, B2 500/4 MiB, B3 1,000/8 MiB, B4 5,000/32 MiB. These are comparison candidates only, not runtime settings.
7. Synthetic daily volume calculation from measured event mix and byte sizes; report Root A and Root B separately, include manifests/checkpoints/audit/version copies, retry/read-back and restore/egress inputs.
8. Cost worksheet must specify exact provider/account boundary, region/jurisdiction, SKU/storage class, WORM scope, versioning, requests, retrieval, egress, KMS, audit, restore, taxes/FX, quote date and confidence. Singapore is not a default region.
9. Throughput and recovery measurements include canonicalization, hash/sign/verify, segment sealing, Root B replay, clean-room restore, spool growth and backlog catch-up; retain all runs, failures and environment details.
10. Result bundle must include generator/build SHA, seed, fixture digest, machine-readable raw samples, summary, failure report and SHA-256 manifest.
11. Provider qualification remains blocked until synthetic fixture determinism, size/volume and restore inputs are measured and independently reproduced, and provider/account/region/budget are separately approved.

No generator or benchmark is implemented/executed by this amendment. No price is calculated without measured workload and sourced exact SKU quote. No provider, region, retention, budget, account, credential, provisioning, source implementation, persistent capture or runtime change is authorized.
