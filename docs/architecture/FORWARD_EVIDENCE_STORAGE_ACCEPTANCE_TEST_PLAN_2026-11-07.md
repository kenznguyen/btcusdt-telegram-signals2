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
