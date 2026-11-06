# Forward Evidence Storage — Vendor Security Review

Date: 2026-11-07
Status: DOCUMENTATION REVIEW — NO PROVIDER SELECTED OR TESTED

## 1. Scope

Reviewed official AWS S3 and Cloudflare R2 documentation for retention-lock semantics, administrative bypass, credentials, and audit evidence. This is a documentation review only. No account was created, no credentials were issued, and no live provider test was performed.

Candidates remain AWS S3 for Root A and Cloudflare R2 for Root B. This review does not approve purchase, provisioning, persistent storage, source/schema/workflow changes, or runtime capture. T0 remains paused; PAPER-only; `ai_execution_enabled=false`.

## 2. Findings — AWS S3 Object Lock

### 2.1 Compliance Mode

AWS documents that a version protected by Compliance Mode cannot be overwritten or permanently deleted by any user, including the AWS account root user, until retention expires. The documented exception is deletion of the associated AWS account itself. Governance Mode is weaker: a principal with `s3:BypassGovernanceRetention` can delete versions or shorten/remove retention, with explicit bypass request semantics.

Decision implication:
- For sealed Root A evidence, Compliance Mode is the required candidate mode; Governance Mode is not sufficient for the intended WORM assurance.
- The account itself remains a catastrophic control-plane failure boundary. A separate Root B must survive account loss/compromise.
- Account closure/deletion controls and break-glass administration need explicit review.

Sources:
- https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lock.html
- https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lock-managing.html
- https://docs.aws.amazon.com/AmazonS3/latest/userguide/troubleshoot-403-errors.html

### 2.2 Versioning, delete markers and immutable identity

Object Lock protects a specific object version. A simple DELETE can create a delete marker that hides the protected version from ordinary current-key reads; a new PUT can create a new version while the old version remains locked. Therefore:
- Every event segment and manifest must record exact bucket, key, version ID, size, digest, and retention metadata.
- Readers/recovery tooling must enumerate and verify versions, not trust the current key view.
- Manifests themselves must be sealed and version-addressed; mutable "latest" pointers are not authoritative evidence.
- Duplicate event IDs and no-overwrite behavior must be enforced by application-level conditional creation and verified by tests, not assumed from Object Lock.

Sources:
- https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lock.html
- https://docs.aws.amazon.com/AmazonS3/latest/userguide/troubleshoot-403-errors.html

### 2.3 Configuration lifecycle and replication

AWS states that after Object Lock is enabled on a bucket, Object Lock cannot be disabled and versioning cannot be suspended. For replication, both source and destination buckets must have Object Lock enabled; retention metadata is replicated, and the replication role needs retention/legal-hold read permissions.

Decision implication:
- Object Lock must be enabled at bucket creation/configuration stage, before evidence is accepted.
- Cross-account replication is not a substitute for independently operated Root B; replication shares a source control and replication trust path.
- Destination retention and recovery must be verified independently.

Sources:
- https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lock-configure.html
- https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lock-managing.html
- https://docs.aws.amazon.com/AmazonS3/latest/userguide/replication-requirements.html

## 3. Findings — Cloudflare R2 Bucket Locks

### 3.1 Retention protection

R2 Bucket Locks prevent deletion and overwriting of matching objects while an enabled rule applies. Rules can cover existing and new objects, and can retain for a duration, until a date, or indefinitely. Locked-object delete/overwrite attempts are rejected.

### 3.2 Administrative bypass / configuration risk

Cloudflare documentation explicitly provides operations to remove individual Bucket Lock rules or replace the complete lock configuration through the dashboard, Wrangler, or API. The lock update API is authorized by an API token. Thus Bucket Lock is an effective object-operation guard while configured, but it is not equivalent to S3 Compliance Mode's documented resistance to deletion by the account root user.

Decision implication:
- R2 remains a candidate for a secondary observer/checkpoint root, but must not be represented as independently immutable against a compromised account administrator.
- The runtime writer token must be restricted to bucket-item object operations; it must not have account-level storage-write or bucket-configuration rights.
- Lock configuration must be monitored out-of-band and changes must trigger immediate evidence-readiness failure and incident response.
- The account owner/admin remains a trusted control-plane principal; separate account ownership and recovery controls are required.

Sources:
- https://developers.cloudflare.com/r2/buckets/bucket-locks/
- https://developers.cloudflare.com/api/typescript/resources/r2/subresources/buckets/subresources/locks/methods/update/
- https://developers.cloudflare.com/r2/api/tokens/

### 3.3 Audit log limitations

Cloudflare R2 Data Access Logs are asynchronous and best effort; Cloudflare explicitly says events may be delayed or omitted and that requests returning HTTP 400 or greater are excluded. They are not a complete record of bucket activity.

Cloudflare Audit Logs v2 are retained for 18 months. The documentation states the UI query window is 90 days, full history requires API or Logpush, and GET/view actions plus 4xx responses are not logged in the described GA behavior. Therefore these logs are useful operational evidence but cannot be the sole immutable audit record for this system. Export them promptly to a separately controlled destination and retain application-signed evidence independently.

Sources:
- https://developers.cloudflare.com/r2/buckets/data-access-logs/
- https://developers.cloudflare.com/fundamentals/account/account-security/audit-logs/

## 4. Comparative security disposition

| Dimension | AWS S3 Object Lock | Cloudflare R2 Bucket Locks | Review result |
|---|---|---|---|
| Prevent overwrite/delete while locked | Yes, per protected version | Yes, for objects covered by active rule | Both qualify for isolated tests |
| Resistance to account administrator | Compliance Mode protects object versions even from account root; account deletion remains catastrophic | Lock rules can be removed/rewritten by authorized account/API administration | AWS stronger for primary WORM |
| Version semantics | Version ID required; delete markers can hide retained versions | Lock applies to matching objects; exact versioning/restore behavior must be verified for intended workflow | R2 needs additional qualification |
| Lock configuration permanence | Cannot disable Object Lock or suspend versioning after enabled | Rules can be removed or replaced | Material difference |
| Audit completeness | Must separately configure and protect AWS audit evidence | R2 data logs best effort; audit logs have documented coverage/retention limits | Neither provider log alone is the evidence archive |
| Independent recovery | Must be demonstrated | Must be demonstrated | NOT VERIFIED for both |
| Cross-provider independence | Distinct provider from R2 | Distinct provider from AWS | Reduces common provider risk, not common emitter risk |

## 5. Revised recommendation

1. Retain AWS S3 Compliance Mode as the preferred Root A candidate, subject to isolated account-level tests, exact version handling, independent restore, account-closure safeguards, and full cost review.
2. Keep Cloudflare R2 as a conditional Root B candidate only. Its Bucket Lock rules do not provide the same documented admin-resistance property as S3 Compliance Mode. Root B's lock policy must be continuously monitored through a separate control path; R2 provider audit logs alone are insufficient.
3. Do not describe the pair as two equally immutable roots. State the asymmetry explicitly in the assurance model.
4. If the required threat model includes compromise of either provider account administrator, R2 is not yet qualified as a WORM-equivalent second root. Reconsider a second independently administered S3 Compliance Mode account/provider or another service with documented admin-resistant retention.
5. No provider selection can be finalized without testing account separation, policy bypass, object restore, signing-key custody, log export, region, and cost.

## 6. Required additions to acceptance testing

Add mandatory tests:
- Verify S3 Compliance Mode cannot be shortened/deleted by bucket admin, IAM admin, and account root during retention; separately document account deletion as catastrophic.
- Verify simple DELETE creates a delete marker and recovery tooling still finds the exact retained version.
- Verify a new PUT cannot silently replace the authoritative manifest reference.
- Verify R2 lock rule removal/replacement requires a separately held administrative identity and causes an alert/evidence-readiness failure.
- Verify R2 object writer token cannot edit bucket lock configuration or delete buckets.
- Verify R2 Data Access Logs gaps and Audit Logs v2 omissions are detected as known limitations; export relevant logs to a separately controlled archive.
- Verify Cloudflare audit retention export beyond 18 months if a longer audit retention requirement is adopted.

## 7. Current disposition

- Vendor documentation review: PASS — findings documented.
- AWS S3 Compliance Mode: PREFERRED ROOT A CANDIDATE; NOT SELECTED OR TESTED.
- Cloudflare R2: CONDITIONAL ROOT B CANDIDATE; NOT SELECTED OR TESTED.
- Equal-strength two-root immutability: NOT ESTABLISHED.
- Account compromise resistance: NOT VERIFIED by live tests.
- Pricing, Singapore residency, retention, key custody: NOT APPROVED / NOT VERIFIED.
- Accounts, purchase, credentials, provisioning, storage access: NOT AUTHORIZED.
- Acceptance test execution: NOT RUN.
- Source/schema/workflow/database/runtime: UNCHANGED.
- Historical Dual Reconstruction: UNAVAILABLE / BLOCKED.
- Option A strict predecessor chain: UNCHANGED.
- T0: PAUSED; PAPER-only; `ai_execution_enabled=false`.

## 8. Official source index

- AWS S3 Object Lock: https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lock.html
- AWS Object Lock considerations: https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lock-managing.html
- AWS Object Lock configuration: https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lock-configure.html
- AWS Object Lock troubleshooting: https://docs.aws.amazon.com/AmazonS3/latest/userguide/troubleshoot-403-errors.html
- Cloudflare R2 Bucket Locks: https://developers.cloudflare.com/r2/buckets/bucket-locks/
- Cloudflare R2 API tokens: https://developers.cloudflare.com/r2/api/tokens/
- Cloudflare R2 Data Access Logs: https://developers.cloudflare.com/r2/buckets/data-access-logs/
- Cloudflare Audit Logs v2: https://developers.cloudflare.com/fundamentals/account/account-security/audit-logs/
