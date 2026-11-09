# T0 Personal-Use Scope and De-commercialization Decision

- Date: 2026-11-09
- Repository: `kenznguyen/btcusdt-telegram-signals2`
- Branch: `feature/t0-centralized-data-feeder-p1-20261101`
- Decision type: owner scope boundary; documentation-only
- Status: **SCOPE CONFIRMED; DEPENDENCY AUDIT PARTIAL; NO REMOVAL AUTHORIZED**

## 1. Owner scope

T0 is an independently owned canonical market-data foundation for one personal system owner and the project's internal T1/T2 consumers. T0 is not a SaaS product, multi-customer service, subscription product, or commercial data platform.

The following capabilities are explicitly OUT OF SCOPE for T0:

1. Multi-tenant architecture and customer-specific authorization/isolated tenancy.
2. Subscription, billing, payment processing, invoicing, and plan entitlements.
3. Customer-facing audit portals or customer evidence workspaces.
4. Commercial customer SLAs, support tiers, and customer-service workflows.
5. Customer onboarding, licensing, account provisioning, and package management.
6. Compliance programs, certifications, and attestations whose sole purpose is commercial sale, customer procurement, or external service commitments.

These are scope exclusions, not findings that each capability currently exists in source code. The current bounded source inventory did not establish an implemented T0 billing, subscription, multi-tenant, or customer-portal subsystem. Do not create removal commits for absent capabilities.

## 2. Non-commercial does not mean low-assurance

The scope exclusions do not weaken controls required to protect the owner's data asset. The following remain IN SCOPE:

- Canonical source/market identity and strict separation of Binance USD-M BTCUSDT from other venues and market types.
- Closed-candle validation, timestamp semantics, first-observed availability, coverage/gap reporting, freshness and provenance.
- Atomic writes, single-writer ownership, lease/generation fencing, conflict detection and fail-closed recovery.
- T0-owned canonical storage and read-only consumer interfaces; T1/T2 must not gain direct canonical database write access.
- Authentication, least privilege, secret hygiene, TLS where crossing host boundaries, and separate reader/writer/migration authority.
- Backup, integrity verification, recovery, restore evidence and lifecycle controls appropriate to a single-owner system.
- Offline tests, GitHub Actions CI, exact-SHA evidence, independent review and honest PASS/BLOCKED/NOT VERIFIED claims.
- L4-Minimum owner-controlled evidence custody, signing separation, exact-object binding, offline verification, independent readback/recovery, key/trust lifecycle, append-only evidence history and fail-closed verdicts.

No deletion, retention shortening, archive, cleanup, compaction, vacuum, backup expiry, replica removal, or other destructive data lifecycle operation is authorized by this scope decision.

## 3. T0 component classification

| Component / capability | Classification | Rationale and action |
|---|---|---|
| Multi-tenant/customer isolation | OUT-OF-SCOPE | No multi-customer service is intended. Do not implement tenancy layers. |
| Billing/subscription/payment | OUT-OF-SCOPE | No paid plans, payment flow or entitlement engine is required. |
| Customer audit portal | OUT-OF-SCOPE | Owner-controlled evidence and offline verification remain required; a customer portal is not. |
| Customer SLA/support tiers | OUT-OF-SCOPE | No customer service commitment. Preserve internal operational targets and incident evidence where needed for reliability. |
| Customer onboarding/licensing/package management | OUT-OF-SCOPE | No external customer provisioning or licensing system. |
| Commercial-only compliance/certification | OUT-OF-SCOPE | Do not build certification workflows solely to sell a service. Preserve security and evidence controls justified by data integrity and owner independence. |
| T0 Binance USD-M ingestion and canonical identity | KEEP | Core data asset; source identity must not be mixed with spot/other venues. |
| SQLite canonical backend | KEEP | Current default backend and personal-use baseline. No migration implied. |
| Read-only Candle API | KEEP | Explicit T0/T1/T2 boundary; authentication and consumer contract remain necessary. |
| Lease, heartbeat, atomic writer fencing | KEEP | Protects canonical single-writer integrity, not commercial tenancy. |
| Provenance, data quality, gap recovery | KEEP | Required to assess whether data is usable and reproducible. |
| Backup, restore, integrity and recovery | KEEP | Required to protect the owner's independent data asset. |
| PostgreSQL/TimescaleDB adapter and migrations | DEFER / REVIEW | Optional backend capability, not inherently commercial. Keep until consumer/deployment/test dependency and maintenance cost are audited. No removal approved. |
| Kraken Spot isolated adapter/store/API | DEFER / REVIEW | Separate non-canonical market source, not a SaaS feature. Determine whether it has an active research consumer before deciding to retain or remove. Must never merge into Binance USD-M canonical data. |
| Android commercial readiness/privacy/terms documents | OUTSIDE T0 SCOPE; RETAIN SEPARATELY | Product-distribution documents are not T0 architecture. This decision does not delete or rewrite Android documents. |

## 4. Bounded source/document inventory reviewed

The following repository files were inspected as a bounded first-pass inventory on the active branch:

- `market_data/README.md`
- `market_data/api.py`
- `market_data/storage.py`
- `market_data/postgres.py`
- `market_data/write_gateway.py`
- `market_data/kraken_spot.py`
- `market_data/kraken_spot_api.py`
- `market_data/kraken_spot_store.py`
- `docs/T0_PRODUCTION_SECURITY_BACKUP_RPO_RTO.md`
- `docs/T0_STAGING_ACCEPTANCE_CHECKLIST.md`
- `docs/T0_STAGING_PROVIDER_RESEARCH.md`
- `docs/evidence/t0/T0_INTERNAL_API_SECURITY_REVIEW_2026-11-08.md`
- `docs/architecture/T0_API_DOMAIN_SELECTION_CRITERIA_2026-11-08.md`
- `docs/architecture/T0_T1_T2_DATA_CONSUMPTION_ARCHITECTURE_2026-11-08.md`
- `android-app/COMMERCIAL_READINESS.md`
- `android-app/PRIVACY_POLICY.md`
- `android-app/TERMS_OF_USE.md`

This inventory is not a repository-wide dependency proof. It does not establish that no commercial-related identifiers, dormant code, workflows, configuration, or indirect dependencies exist elsewhere. A repository-wide symbol/config/workflow/dependency search and consumer graph are still required before any physical removal.

## 5. Removal gates

A component may be proposed for physical removal only after all of the following:

1. Exact path, symbols, configuration keys, workflows, docs, and runtime references are inventoried.
2. Direct and transitive dependencies across T0, T1, T2, Android, tests and CI are mapped.
3. The component is shown to be either absent, unused, or solely commercial-purpose; convenience or apparent redundancy is insufficient.
4. Data ownership, provenance, integrity, security, recovery and single-writer controls are shown not to depend on it.
5. A minimal removal plan and rollback/recovery plan are reviewed.
6. Independent adversarial review finds no unresolved high/critical dependency or safety issue.
7. Owner explicitly approves the exact paths and operation before source deletion or runtime changes.
8. GitHub Actions validates the exact resulting commit SHA; evidence records workflow run/artifact where available.

If a capability is absent, mark it OUT-OF-SCOPE / NOT PRESENT rather than deleting unrelated abstractions. If a capability has legitimate personal-use reliability value, retain it even if it resembles an enterprise feature.

## 6. Current status and limits

- Owner scope boundary: CONFIRMED in conversation on 2026-11-09.
- First-pass source/document inventory: PARTIAL.
- Multi-tenant/billing/customer portal implementation absence across entire repository: NOT VERIFIED.
- PostgreSQL and Kraken dependency necessity: NOT VERIFIED; DEFERRED.
- Physical source/document removal: NOT AUTHORIZED.
- Runtime/VPS/database/Feeder/T0/T1/T2 changes: NOT AUTHORIZED.
- GitHub Actions: NOT DISPATCHED for this documentation-only record; no workflow run or artifact is claimed.
- Tests: NOT RUN.
- No code, schema, API, workflow, configuration, credential, permission, data or runtime changes.
- `AI_EXECUTION_ENABLED=false`; paper-only; no live orders.
- Option C — No Destructive Authority — remains in force.

## 7. Next step

Perform a repository-wide read-only dependency audit for the six excluded commercial capability groups, and a separate dependency/consumer audit for PostgreSQL/TimescaleDB and Kraken Spot. Produce exact path/symbol/workflow references and classify each finding KEEP, DEFER, OUT-OF-SCOPE, NOT PRESENT, or REMOVE-CANDIDATE. Do not remove or modify anything until that audit has an independent review and a separate exact-scope owner approval.
