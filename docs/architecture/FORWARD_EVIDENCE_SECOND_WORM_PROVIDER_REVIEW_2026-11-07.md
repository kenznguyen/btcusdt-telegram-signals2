# Forward Evidence Storage — Second WORM Provider Qualification Review

Date: 2026-11-07
Scope: documentation-only review of Google Cloud Storage Bucket Lock and Azure Blob immutable storage as potential cross-provider Root B candidates alongside AWS S3 Object Lock Compliance Mode as the preferred Root A candidate.

## 1. Decision summary

- **Google Cloud Storage Bucket Lock: QUALIFIED FOR DISPOSABLE TEST DESIGN; NOT TESTED.** A locked bucket retention policy cannot be removed or shortened. The bucket cannot be deleted while retained objects remain. Google automatically applies a lien intended to block project deletion; a project owner or organization administrator can remove that lien, so this is not protection against every organization-level administrator action.
- **Azure Blob immutable storage: QUALIFIED FOR DISPOSABLE TEST DESIGN; NOT TESTED.** Locked time-based retention policies cannot be deleted or shortened (the interval may be extended within documented limits). Microsoft documents that storage-account deletion fails while a container has a locked time-based retention policy and retained blobs; version-level immutable storage also blocks account deletion while protected containers/versions remain. The exact behavior must be tested against the selected scope, account configuration, and API/portal deletion paths.
- **Cloudflare R2: RETAIN ONLY AS A LOWER-ASSURANCE FALLBACK.** Its bucket lock rules can be removed or replaced by authorized bucket-configuration administrators, unlike the irreversible retention locks documented by GCS and Azure.
- **No final Root B selection.** GCS and Azure both merit synthetic-data qualification. Neither is proven independent until separate account ownership, administrative recovery, restore, audit export, region and cost are tested.

## 2. Google Cloud Storage Bucket Lock

Official documentation states:
- A bucket retention policy prevents objects from being deleted or replaced before the retention age.
- Once locked, the policy cannot be removed or reduced; it can only be increased.
- The bucket cannot be deleted until every object has met retention and been deleted.
- Locking applies a project lien that blocks the project-delete permission. Google notes that an owner or organization administrator must remove the lien before project deletion; the documentation recommends that this authority sit outside the IT accountability chain.
- Object Versioning does not protect against deletion of the entire bucket. Soft delete is recommended for recovery from accidental or malicious deletion, but it is not a substitute for a separately administered immutable root.
- Data Access audit logs are disabled by default and must be explicitly enabled. Admin Activity logs are enabled by default. Cloud Audit Logs have documented coverage restrictions; logs should be exported to a separately controlled destination.

Security interpretation:
- Strong object-retention control against bucket-level deletion during retention.
- Project lien adds a second deletion barrier, but a sufficiently privileged project/org authority can remove the lien. Treat project/org administrators and billing/recovery identities as a critical trust boundary.
- Require version/generation-addressed object references, independent audit export and a restore test. Do not use a mutable object-name pointer as the evidence identity.

Sources:
- https://docs.cloud.google.com/storage/docs/bucket-lock
- https://docs.cloud.google.com/storage/docs/using-bucket-lock
- https://docs.cloud.google.com/storage/docs/object-versioning
- https://docs.cloud.google.com/storage/docs/audit-logging
- https://docs.cloud.google.com/storage/docs/org-policy-constraints

## 3. Azure Blob immutable storage

Official documentation states:
- Immutable Blob Storage supports time-based retention and legal holds. During an active policy, protected data cannot be modified or deleted.
- A locked time-based policy cannot be deleted or shortened; documented guidance permits extension only within a bounded number of changes.
- At container scope, Microsoft documents that deleting the container fails while blobs remain, and deleting the storage account fails while a container has a locked time-based retention policy.
- At version scope, a protected blob version cannot be deleted; overwrites create new versions where versioning applies. Microsoft documents account deletion failure when version-level immutable storage is enabled or when locked-retention versions remain.
- Blob soft delete is recommended as an additional recovery control. Resource Manager account locks alone do not protect blob data; WORM policy is the data-plane control.

Security interpretation:
- Strong candidate because the provider documents both data immutability and storage-account deletion barriers under specified conditions.
- Qualification must choose and test one exact model: container-level WORM or version-level WORM. Do not mix their semantics.
- Test every deletion path (container, account, subscription/resource group) with retained synthetic objects, and record the precise conditions under which the control blocks deletion.
- Legal hold is administratively clearable and must not be mistaken for an irreversible time-based lock.
- Keep management-plane administrator, subscription owner, billing owner and recovery identities separate from the object writer. Export Azure Activity Logs and relevant storage diagnostics to a separate account/provider.

Sources:
- https://learn.microsoft.com/en-us/azure/storage/blobs/immutable-storage-overview
- https://learn.microsoft.com/en-us/azure/storage/blobs/immutable-container-level-worm-policies
- https://learn.microsoft.com/en-us/azure/storage/blobs/immutable-version-level-worm-policies
- https://learn.microsoft.com/en-us/azure/storage/blobs/security-recommendations
- https://learn.microsoft.com/en-us/azure/storage/common/lock-account-resource

## 4. Comparative disposition

| Dimension | Google Cloud Storage Bucket Lock | Azure Blob immutable storage | Cloudflare R2 |
|---|---|---|---|
| Retention lock irreversible | Yes; cannot reduce/remove | Yes; locked time-based policy cannot be deleted/shortened | Lock rules can be administratively removed/replaced |
| Bucket/container deletion during retention | Blocked while retained objects remain | Blocked under documented locked-container/version conditions | Depends on active lock rule and administration |
| Parent project/account deletion barrier | Project lien; privileged owner/org admin can remove | Account deletion blocked under documented locked-policy conditions | No equivalent irreversible retention barrier established in this review |
| Version identity | Generation/version identity required | Blob version ID required for version-scope mode | Must be independently qualified |
| Audit controls | Admin Activity default; Data Access must be enabled; export separately | Azure Activity Logs + storage diagnostics; export separately | Native logs have known completeness/retention gaps |
| Candidate status | Root B candidate | Root B candidate | Lower-assurance fallback |

No provider is immune to provider-wide failure, legal/contractual account suspension, compromised external identity, or common upstream event fabrication. Cross-provider separation reduces common provider failure but does not create independent economic truth.

## 5. Recommendation

1. Keep AWS S3 Compliance Mode as the preferred Root A candidate, not selected or tested.
2. Advance **GCS Bucket Lock and Azure Blob immutable storage as the two Root B candidates** for a later, controlled, synthetic-data qualification. Do not choose between them from documentation alone.
3. Prefer an account structure in which the Root B project/subscription, billing owner, recovery identity, and immutable-storage administrator are independently controlled from Root A and the application writer.
4. Keep Cloudflare R2 only as a fallback if its lower resistance to lock-policy administration is explicitly accepted.
5. Do not infer that a provider's compliance certification or product feature proves this system's independent restore, correct event capture, or account-level security.

## 6. Required acceptance-plan additions

Add provider-specific tests:
- GCS: prove policy lock is irreversible; deny policy reduction/removal; deny object replacement/deletion during retention; verify bucket deletion block; verify project lien; test and document authorized lien removal and project deletion; enable Data Access audit logs; export logs out-of-project; restore exact object generations.
- Azure: test both container- and version-scope policy only if each is a candidate; lock policy and verify shortening/deletion denial; test protected version overwrite/delete semantics; test container and storage-account deletion denial with retained synthetic objects; test behavior after retention expiry; export management/data-plane audit evidence separately.
- Both: writer cannot modify retention, IAM, project/subscription, billing or audit export; privileged admin actions alert an independent monitor; exact version/generation, size, digest and retention metadata are bound in signed manifests; restore from a clean separately administered identity.

## 7. Status and boundaries

- Documentation review: PASS.
- GCS and Azure: candidates for disposable synthetic-data testing only; NOT TESTED.
- AWS S3 Compliance Mode: preferred Root A candidate; NOT TESTED.
- Cloudflare R2: lower-assurance fallback.
- Provider pair selection, accounts, region, budget, retention, key custody: NOT DECIDED.
- Purchase, account creation, credentials, provisioning, storage access and persistent capture: NOT AUTHORIZED.
- CI: NOT RUN (documentation-only).
- Source/schema/workflow/database/runtime: unchanged.
- Historical Dual Reconstruction: UNAVAILABLE / BLOCKED; Option A unchanged.
- T0 paused; PAPER-only; `ai_execution_enabled=false`.
