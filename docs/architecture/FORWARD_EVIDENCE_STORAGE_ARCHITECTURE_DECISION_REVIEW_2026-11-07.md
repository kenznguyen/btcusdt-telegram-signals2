# Forward Evidence — Storage Architecture Decision Review (2026-11-07)

## Status

**ARCHITECTURE COMPARISON — DOCUMENTATION ONLY; NO PROVIDER SELECTED OR STORAGE AUTHORIZED.**

This review compares storage failure-domain patterns for prospective Root A and Root B evidence. It does not select a vendor, region, subscription, retention duration, or encryption/key service. It does not authorize account DB access, storage provisioning, credentials, source/schema changes, or runtime capture.

Constraints:
- PC-first development; no VPS/provider decision is implied.
- Paper Trading only; `ai_execution_enabled=false`.
- No exchange connectivity or live orders.
- T0 remains paused and is not part of this decision.
- Historical independent archive/checkpoint remains unavailable; Option A strict predecessor chain remains current.
- Prospective capture cannot retroactively prove missing history.

## 1. Decision objective

Choose a storage topology that can preserve two distinct evidence roots with:
- independent write identities and access-control boundaries;
- immutable/versioned retained bytes and auditable retention policy;
- read-back verification and restore capability;
- clearly stated failure domains and common-mode risks;
- predictable cost and operational burden for a single-user paper system;
- no dependency on GitHub Actions artifacts or the mutable account database as the evidence archive.

The objective is evidence integrity and recoverability, not high-frequency market-data hosting or a commercial multi-tenant service.

## 2. Storage pattern comparison

| Pattern | Root separation | Resistance to one credential compromise | Provider/admin common mode | Operational complexity | Cost tendency | Assessment |
|---|---|---|---|---|---|---|
| A. One local PC disk, two directories | None meaningful | Very low | Same OS/admin/device | Low | Lowest | REJECT for independent evidence; useful only as a transient spool/cache |
| B. One cloud account, two buckets/namespaces, separate service credentials and object lock | Logical separation only | Medium if IAM is correctly isolated | High: same account/provider/admin/billing/control plane | Low–medium | Low–medium | Minimum viable retention topology, but does not satisfy strong provider/admin independence |
| C. One provider, two separate cloud accounts/projects with distinct administrators/credentials and immutable retention | Stronger account/IAM separation | Medium–high | Medium–high: same provider/control plane and possible organization-level super-admin | Medium | Medium | Conditional option when provider diversity is impractical |
| D. Two providers, Root A and Root B in separate provider accounts, credentials, regions/control planes | Strong provider and account separation | High against one provider credential/account compromise | Lower, not zero: shared operator, upstream emitter, endpoint, legal jurisdiction or internet path may remain | High | Medium–high | STRONGEST prospective separation; more operational and recovery burden |
| E. Local durable spool plus one immutable cloud root | One durable remote root only | Medium for local failure, low for provider/admin compromise | Remote root remains single provider | Medium | Low–medium | Good buffering/availability pattern, not two independent evidence roots |
| F. Local spool plus two independently controlled remote roots | Two remote roots plus local recovery buffer | High if remote roots are separately administered | Shared operator/upstream emitter remains | High | Medium–high | Preferred target topology if the reliability benefit justifies cost and maintenance |

### Interpretation

- Two folders, two buckets, or two encryption keys do not automatically create independent evidence roots.
- Two cloud accounts under one organization may still share a super-admin or billing/control plane. The exact provider IAM model must be checked.
- Cross-provider storage reduces one-provider compromise risk but does not solve a compromised event emitter, shared operator, compromised endpoint, or false source event.
- A local PC disk is not a suitable sole archive: theft, disk failure, ransomware, OS administrator, and accidental cleanup can destroy both copies.
- GitHub and GitHub Actions remain for source, review, CI, and test provenance only.

## 3. Recommended staged topology

### Stage 0 — No persistent capture (current)

- No storage provider, bucket, credential, retention lock, or writer is provisioned.
- Design and isolated disposable tests only after separately approved implementation scope.
- Do not place account event records in GitHub commits, issues, CI logs, or CI artifacts.

### Stage 1 — Isolated prototype (future approval required)

- Use synthetic fixtures only.
- Exercise Root A and Root B using separate local test processes and separate temporary directories/identities.
- Inject crashes, deletion, mutation, reordering, replay, lag, and restore faults.
- This stage proves software contracts only; it does not establish durable independent retention.

### Stage 2 — Controlled paper capture (future explicit approval required)

Preferred target:
- Root A: immutable object/event segments in provider/account A.
- Root B: observer checkpoint and retained input evidence in provider/account B, with distinct credentials and administrative control.
- Local PC: encrypted bounded spool/cache only; never the authoritative sole copy.
- Both roots: object versioning, retention lock/WORM where supported, server-side encryption, TLS, separate read/write identities, audit logs, and byte-level read-back verification.
- Signing key: separately controlled from both storage writer identities; key custody/recovery must be reviewed before relying on signed manifests.

If cross-provider operation is too expensive or complex, a two-account same-provider pattern may be considered only with an explicit residual-risk acceptance. Do not silently downgrade to two buckets in one account.

### Stage 3 — Operational qualification (future approval required)

- Demonstrate restore from each root independently.
- Prove one root remains readable and unmodifiable by the other root's writer identity.
- Test provider/account outage, credential revocation, retention policy drift, and admin compromise assumptions.
- Measure real storage, request, retrieval, egress, and minimum-retention charges before setting budgets.
- Record exact provider terms, object-lock semantics, region, account owner, recovery owner, and deletion/legal-hold process.
- Do not enable risk admission solely because storage health is green; all event completeness and account-risk checks still apply.

## 4. Minimum capability checklist for vendor evaluation

A candidate service must be evaluated against actual product documentation and account-specific configuration. Marketing labels such as "immutable" or "secure" are insufficient.

### Required
- Object versioning or equivalent immutable version identity.
- Retention lock/WORM with documented bypass/admin semantics.
- Separate service identities, scoped IAM and auditable policy changes.
- TLS in transit and encryption at rest.
- API support for conditional create/no-overwrite or equivalent append semantics.
- Stable object/version IDs and metadata.
- Read-back/download to verify exact stored bytes.
- Access logs for reads, writes, deletes, policy changes and administrative actions.
- Documented durability, availability, region and incident behavior.
- Export/restore path without requiring the original application database.
- Clear pricing for storage, requests, retrieval, egress, minimum duration, versioning and retention lock.
- Contractual terms covering data ownership, account closure, deletion, legal hold and provider access.

### Strongly preferred
- Separate accounts/tenants and independent administrative roles.
- Cross-region or cross-provider copy with separately retained manifests.
- Customer-controlled key options with tested recovery and rotation.
- Object lock configured at creation time or another safe mechanism preventing a post-upload immutability gap.
- Independent audit-log destination.
- Policy preventing a writer identity from shortening retention or deleting versions.

### Automatic disqualifiers
- Writer credentials can overwrite or permanently delete sealed evidence.
- Retention lock can be disabled by the same runtime identity that writes evidence.
- No reliable read-back/version identity.
- Provider terms or pricing cannot be determined.
- Data export/restore depends on a mutable account database that is not retained.
- One shared credential or admin role can silently modify both roots without independent audit.

## 5. Retention and cost model — no numeric commitment

Do not pick a retention duration or monthly budget before measuring actual paper event volume and reviewing provider pricing.

Measure:
- average and peak event bytes per event;
- events per day and segment/checkpoint sizes;
- manifest/signature/audit overhead;
- object count and request frequency;
- versioning and retention-lock storage multipliers;
- read-back audit frequency and restore volume;
- retrieval/egress costs and minimum storage duration;
- local spool capacity and maximum offline interval.

Calculate:
`monthly_total = storage + requests + retrieval + egress + key_management + audit + minimum_retention_fees`

Estimate at least:
- normal month;
- 2x observed event volume;
- 10x burst/recovery month;
- full restore of Root A and Root B;
- retention-policy migration to another provider.

Use measured payload sizes from synthetic tests first. Do not create a persistent account archive merely to estimate costs. Do not infer an acceptable budget from the user's earlier infrastructure research.

## 6. Failure-domain and recovery policy

| Failure | Required behavior |
|---|---|
| Local PC lost | Recover from retained remote roots; local spool is non-authoritative |
| Root A provider unavailable | No new exposure under proposed fail-closed policy; continue only safety reductions/closures according to separately approved behavior |
| Root B provider unavailable or stale | Independent verification NOT READY; proposed block on increases pending explicit risk-policy approval |
| One credential compromised | Revoke affected identity; preserve other root; incident review; no automatic root rebuild |
| One provider account/admin compromised | Treat that root as suspect; preserve the other root and audit records; no certification until re-established |
| Both roots inaccessible | Evidence NOT READY; block increases; preserve current risk safety controls |
| Hash/signature mismatch | INCIDENT; freeze certification; retain all variants; no in-place repair |
| Retention lock missing or weakened | NOT READY; do not seal/accept new evidence as immutable |
| Cross-provider replication lag | Report separate watermarks; never claim both roots current until verified |
| Provider migration | Copy exact retained bytes; verify destination digests and manifests; keep source intact until explicit acceptance |

A backup is not independent merely because it is a second copy. The destination must have a separately understood failure domain and its own verified retention controls.

## 7. Decision recommendation

**Recommended architecture target: Pattern F — local encrypted spool plus two remote roots in separately controlled provider accounts, preferably across providers.**

Reasons:
- local PC supports development and bounded offline buffering without becoming the authoritative archive;
- separate remote roots reduce one credential/provider/account compromise risk;
- Root B remains an independently retained observer projection rather than a second export from the same mutable DB;
- staged adoption allows synthetic testing before any persistent account data exists.

This is a target recommendation only. It is not a provider selection, budget approval, purchase authorization, or permission to provision storage.

**Fallback:** Pattern C (separate accounts under one provider) may be evaluated if cross-provider operation is disproportionate, but the shared provider/admin risk must be explicitly accepted. Pattern B (two buckets in one account) is not sufficient for the intended strong independence claim.

## 8. Decisions required before vendor shortlist

1. Is cross-provider separation required, or is separate-account same-provider separation acceptable with documented residual risk?
2. What maximum monthly spend is authorized for prospective paper evidence retention? No amount is assumed here.
3. What retention duration and deletion/legal-hold requirements apply?
4. Who owns provider accounts, billing, recovery credentials, and emergency admin access?
5. Is the user's PC allowed to hold only an encrypted bounded spool, with remote stores authoritative?
6. Which data region/jurisdiction is acceptable?
7. What Root B lag and outage duration should block new exposure?
8. Which key custody model is acceptable, and who can recover keys?

These decisions are not implied by asking to continue. If not decided, keep the design at Stage 0.

## 9. Current disposition

- Storage pattern comparison: **DOCUMENTED**.
- Recommended target: **Pattern F, conditional and not approved**.
- Fallback: **Pattern C, residual risk must be accepted**.
- Provider/region/account: **NOT SELECTED**.
- Retention duration/budget: **NOT APPROVED**.
- Credentials/provisioning: **NOT AUTHORIZED**.
- Source/schema/workflow/runtime: **UNCHANGED**.
- Persistent DB/account data access: **NOT AUTHORIZED**.
- Historical Dual Reconstruction: **UNAVAILABLE / BLOCKED**.
- Current baseline policy: **Option A — strict predecessor chain**.
- T0: **PAUSED / OUT OF SCOPE**.
- Execution: **PAPER ONLY; ai_execution_enabled=false**.

Next step after review is to decide the open constraints. Only then prepare a vendor shortlist from current official pricing and capability documentation. Do not provision or write code as part of this decision.
