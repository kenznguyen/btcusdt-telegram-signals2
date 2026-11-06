# Forward Evidence Storage — Cost Model and Budget Gate

Date: 2026-11-07
Scope: vendor-neutral cost model for AWS S3 Compliance Mode (Root A) and Google Cloud Storage Bucket Lock / Azure Blob immutable storage (Root B candidates). Documentation only.

## 1. Decision status

- No provider or region is selected.
- No monthly budget is approved. A USD 5/month ceiling discussed as a possible research constraint is illustrative only and is not an authorization or a proven feasible budget.
- No pricing quote is certified for Singapore or any other region.
- No account, storage resource, credential, purchase, test, or persistent capture is authorized.
- The cost model is a decision framework; it does not claim that any candidate fits a particular budget.

## 2. Cost model

Calculate each root independently, then add shared operating costs and any cross-provider transfer.

Monthly total:

C_total = C_rootA + C_rootB + C_spool + C_signing_KMS + C_audit + C_network + C_restore_test + C_tax + C_support

For each cloud root:

C_root = C_capacity + C_requests + C_retrieval + C_egress + C_replication + C_versioning + C_immutability_related + C_monitoring

Do not assume a component is free because the provider does not show a separate WORM surcharge. Immutable retention can increase the number of simultaneously retained versions and prevent early deletion.

### Required workload inputs

| Input | Symbol | Required evidence |
|---|---|---|
| New evidence bytes per day | D | Measured serialized event + manifest + signature bytes |
| Object count per day | N | Measured object granularity and batching |
| Average object size | S | Distribution, not only mean |
| Retention duration | R | Explicit policy decision; currently undecided |
| Version multiplier | V | Measured overwrite/retry/version behavior; target should avoid mutable overwrites |
| Read/list requests per month | Qr/Ql | Restore and monitoring design |
| Write requests per month | Qw | Upload, multipart, manifest and checkpoint operations |
| Restore volume and frequency | Grestore/Frestore | Acceptance-test plan |
| Audit log volume | Gaudit | Measured from enabled required audit categories |
| Egress volume | Ge | Clean-room restore and cross-provider transfer design |
| Region and redundancy | L | Exact region/SKU and contractual residency statement |
| Key operations | K | Signing/KMS key design and request volume |

### Capacity projection

For constant daily intake and a retention window of R days:

- Retained payload at steady state (approximate): D × R.
- Add measured manifests, signatures, indexes, audit evidence, object metadata/version overhead and safety margin.
- If retention is indefinite, storage grows without a bounded steady state. Do not model it as a fixed-size bucket.
- During initial ramp-up, average monthly stored bytes differ from end-of-month capacity; use daily cohort accounting for a precise estimate.
- Root A and Root B each retain their own copy. Do not count one root's bytes as covering both roots.

### Request and recovery projection

- Count every event object, batch, manifest, checkpoint, read-back verification, listing, retry, multipart operation and audit export.
- Model routine health checks separately from full restore drills.
- Include a full clean-room restore at least once in qualification cost, including reads, egress, temporary destination capacity and verification operations.
- Keep Root B observer/audit evidence and provider logs in their own cost line items.
- Use actual provider SKU meters; do not equate an API call with a single billable transaction without checking provider operation classification.

## 3. Candidate-specific cost drivers

### AWS S3 Compliance Mode — Root A candidate

Include:
- S3 storage class and exact region rate.
- PUT/COPY/POST/LIST and GET request classes.
- Data retrieval and minimum storage-duration/early deletion charges for selected storage classes.
- Internet and cross-region transfer.
- CloudTrail data events and any additional audit/log storage.
- KMS requests/key costs, if customer-managed keys are selected.
- Versioned objects and retained delete-marker/version behavior.
- Independent restore and lifecycle/retention administration.

AWS publishes separate storage, request, retrieval, transfer and feature pricing. CloudTrail data events delivered through trails are separately charged; the published example rate is $0.10 per 100,000 data events, before S3 log storage and other costs. Reconfirm exact current SKU and region before quote acceptance.

### Google Cloud Storage Bucket Lock — Root B candidate

Include:
- Standard/Nearline/Coldline/Archive capacity in the exact region.
- Class A and Class B operation counts.
- Retrieval fees for colder classes.
- Internet egress and any inter-region replication.
- Data Access audit log ingestion and retention; these logs are disabled by default for most services.
- Cloud Logging export, log bucket retention, CMEK and KMS if used.
- Soft-delete/versioning overhead and generation-addressed restore.
- Project lien monitoring and independent alerting.

Official pricing separates storage, operations, retrieval and network usage. Standard regional operations are priced differently from dual/multi-region operations. Cloud Logging lists a free monthly ingestion allowance for some log storage, then per-GiB ingestion and extended-retention charges; verify current eligibility and billing scope.

### Azure Blob immutable storage — Root B candidate

Include:
- Hot/Cool/Cold/Archive tier capacity in the exact region and redundancy SKU.
- Write/read/list/delete/metadata transaction classes.
- Data retrieval and outbound bandwidth.
- Version-level WORM extra retained versions, if that model is selected.
- Azure Monitor / diagnostic log ingestion and retention, where used.
- Key Vault key operations and key retention/recovery.
- Archive rehydration, priority retrieval and early deletion fees.
- Independent restore and management-plane audit export.

Microsoft documents no extra capacity surcharge solely for immutable storage, but version-level WORM can increase capacity due to additional versions. Archive-tier blobs have a 180-day minimum storage period; early deletion or tier changes can incur charges. Archive is unsuitable for immediate restore and must not be selected solely for low headline storage price.

## 4. Pricing evidence and limitations

Official pricing sources reviewed on 2026-11-07:

- AWS S3: https://aws.amazon.com/s3/pricing/
- AWS CloudTrail: https://aws.amazon.com/cloudtrail/pricing/
- Google Cloud Storage: https://cloud.google.com/storage/pricing
- Google Cloud Logging: https://cloud.google.com/logging
- Google Data Access audit logs: https://docs.cloud.google.com/logging/docs/audit/configure-data-access
- Azure Blob cost model: https://learn.microsoft.com/en-us/azure/storage/common/storage-plan-manage-costs
- Azure immutable storage pricing: https://learn.microsoft.com/en-us/azure/storage/blobs/immutable-storage-overview
- Azure Monitor: https://azure.microsoft.com/en-us/pricing/details/monitor/
- Azure Archive rehydration and minimum duration: https://learn.microsoft.com/en-us/azure/storage/blobs/archive-rehydrate-overview

Pricing pages are dynamic, may vary by region, currency, contract, storage redundancy, account type, free-tier eligibility and tax. Public pages reviewed do not provide a complete, directly comparable, locked configuration quote for this workload in Singapore. Azure public pricing pages may render region/SKU rates through a calculator rather than a fixed value in the documentation. Therefore no single per-GB quote is copied into this decision record.

## 5. Budget controls — alerts are not hard caps

- AWS Budgets notifications can lag usage/billing updates; budget monitoring does not guarantee that charges stop at the threshold.
- Azure Cost Management budgets notify; they do not stop resources or consumption.
- Google alerts-only budgets do not cap usage. Google documents spend-cap budgets only for eligible services; do not assume Cloud Storage is eligible. Even spend caps are not instantaneous and overages can still be billed.

A budget alert must therefore not be treated as a hard spending ceiling. Before a live pilot, require:
1. Separate disposable billing scope/account/project/subscription for qualification.
2. Explicit maximum authorized spend and test end date.
3. Low-volume synthetic workload with client-side byte/request ceilings.
4. Provider-side quotas or service restrictions where supported, plus out-of-band billing alerts.
5. An operator-controlled stop procedure and independent confirmation that writers are disabled.
6. Post-test bill reconciliation after provider billing data settles.
7. No automatic deletion of retained WORM evidence to reduce costs.

## 6. Scenario worksheet — values intentionally unfilled

No workload measurement or retention decision currently exists. Populate this worksheet only after the evidence envelope and retention policy are approved.

| Scenario | Daily new bytes | Daily objects | Retention | Restore drill | Purpose |
|---|---:|---:|---|---|---|
| Pilot | TBD | TBD | TBD | TBD | Disposable synthetic-data qualification |
| Expected | TBD | TBD | TBD | TBD | Bounded paper capture forecast |
| Stress | TBD | TBD | TBD | TBD | 2x/10x growth and restore-cost envelope |

For each scenario, calculate monthly and retention-horizon totals separately for Root A and each Root B candidate. Report low/expected/high estimates and the price timestamp, region, SKU, currency, taxes, free-tier assumptions and calculator export. Include cost per million events and cost per retained GiB-month as normalized measures, but do not use them as substitutes for the full bill.

## 7. Selection gates

A candidate cannot be recommended as affordable until:
- Exact region and redundancy SKU are selected for quote comparison.
- Retention and legal-hold requirements are defined.
- Measured event size, object batching and audit volume are available.
- Storage, request, retrieval, transfer, logging, key, restore and tax costs are included.
- Expected and stress scenarios fit an explicitly approved monthly and one-time test budget.
- A cost overrun does not trigger deletion or weakening of WORM retention.
- Restore latency and cost satisfy recovery requirements.

A low-cost tier that makes evidence unavailable during the required recovery window is a disqualifier, not a saving.

## 8. Current disposition

- Cost model: DOCUMENTED.
- Exact monthly estimate: NOT VERIFIED — workload and region inputs missing.
- Singapore price comparison: NOT VERIFIED — exact SKU/quote not established.
- USD 5/month: illustrative proposal only; NOT APPROVED and not demonstrated feasible.
- GCS vs Azure affordability: NOT DECIDED.
- Provider selection, purchase, accounts, credentials, provisioning, provider tests and persistent capture: NOT AUTHORIZED.
- CI: NOT RUN (documentation-only).
- Source/schema/workflow/database/runtime: unchanged.
- Historical Dual Reconstruction: UNAVAILABLE / BLOCKED; Option A unchanged.
- T0 paused; PAPER-only; `ai_execution_enabled=false`.
