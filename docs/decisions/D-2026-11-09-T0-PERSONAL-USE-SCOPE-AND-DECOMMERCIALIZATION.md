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

## 8. First-pass dependency audit (read-only, 2026-11-09)

### 8.1 Commercial capability search

A repository code-search pass for `tenant`, `billing`, `subscription`, `license`, `customer`, `SLA support tier`, `commercial readiness`, `onboarding entitlement payment`, `stripe invoice`, and `multi_tenant` returned:
- No results for tenant, billing, subscription, customer, SLA/support tier, onboarding/entitlement/payment, Stripe/invoice, or multi_tenant.
- One historical `license` match in `docs/PROJECT_SESSION_HANDOFF.md`, in an Android SDK license-acceptance setup context, not customer licensing.
- Commercial-readiness matches in historical project documentation, not a T0 runtime subsystem.

**Search limitation:** the GitHub code-search connector searches the repository's default branch, not the active feature branch. These zero-result searches are supporting evidence only and do not prove absence on this branch or in generated/runtime configuration. Full branch-wide absence remains NOT VERIFIED.

### 8.2 PostgreSQL / TimescaleDB dependency evidence

Current active-branch source confirms PostgreSQL is not merely dormant commercial scaffolding:
- `market_data/storage.py` selects SQLite by default but supports explicit PostgreSQL configuration via `MARKET_DATA_BACKEND=postgres` and `MARKET_DATA_POSTGRES_DSN`; blob `13fe1ae01ebb5318b69e69eef3e512d207f74c49`.
- `market_data/feeder_service.py` imports and composes `PostgresStore`, `PostgresLeaseStore`, `PostgresWriteGateway`, and a DB-clock lease adapter; blob `bdcecf6bc98a2ff070f83098d2c50154a160c99c`.
- `market_data/test_postgres_feeder_runtime.py` contains runtime composition and lease-authority contracts; blob `dba7b3a61b3963984c58309e7d334b61c0889256`.
- `market_data/test_postgres_feeder_runtime_lifecycle.py` contains disposable TimescaleDB lifecycle integration tests; blob `ff8458fd6250fca264799810d78b2566ebcfda10`.
- `.github/workflows/t0-manual-validation.yml` exposes an isolated `timescaledb-integration` gate; blob `395ae93274a9202f14ab63d528be5cd582c30149`.
- `requirements-market-data.txt` includes `psycopg[binary]`; blob `0c1b47046bc264be48fa9e11360ce3488046530d`.

Classification: **DEFER / REVIEW — NOT A COMMERCIALIZATION COMPONENT**. It has concrete source, test and workflow dependencies. Whether the personal system should retain PostgreSQL long term is a separate operational/cost/maintenance decision. Do not remove the adapter or driver as part of de-commercialization.

### 8.3 Kraken Spot dependency evidence

Current active-branch source confirms a distinct isolated market-data subsystem:
- `market_data/kraken_spot.py` — read-only source adapter; blob `d8191606d27617f964f23736e07fb7fe7458dc39`.
- `market_data/kraken_spot_store.py` — separate SQLite persistence with explicit canonical Binance DB separation; blob `1736935cf143c11f0789651b5ef80a1821aabbb8`.
- `market_data/kraken_spot_api.py` — separate read-only API; blob `5d8679f74fe5d4b70d89ba796f83550c6e1f2c58`.
- `market_data/test_kraken_spot.py` — adapter contract tests; blob `d60bcc62d68d3a49cec3ab518e1c6a41866c11ae`.
- `market_data/test_kraken_spot_store.py` — isolated persistence tests; blob `22dd48746e7b893523a8d8a728d37cccec85e9cb`.
- `market_data/test_kraken_spot_api.py` — API tests; blob `e004b16ea41e45749925e032d2d9cb2bffc14c16`.
- `.github/workflows/t0-manual-validation.yml` has separate `kraken-adapter`, `kraken-spot-sqlite`, and `kraken-spot-read-api` gates; blob `395ae93274a9202f14ab63d528be5cd582c30149`.

Classification: **DEFER / REVIEW — NOT A COMMERCIALIZATION COMPONENT**. It is isolated from Binance USD-M canonical storage and has dedicated test/workflow coverage. Its ongoing research value and maintenance burden have not yet been decided. Do not merge it into canonical Binance data or remove it without consumer inventory and owner approval.

### 8.4 First-pass disposition

| Capability | First-pass result |
|---|---|
| Multi-tenant/customer isolation | No implementation found in bounded source review; repository-wide absence NOT VERIFIED |
| Billing/subscription/payment | No implementation found in bounded source review; repository-wide absence NOT VERIFIED |
| Customer audit portal | No implementation found in bounded source review; repository-wide absence NOT VERIFIED |
| Commercial customer SLA/support workflow | No implementation found in bounded source review; repository-wide absence NOT VERIFIED |
| Customer onboarding/licensing/package entitlement | No implementation found in bounded source review; repository-wide absence NOT VERIFIED |
| Commercial-only compliance/certification workflow | No T0 runtime subsystem identified; full repository absence NOT VERIFIED |
| PostgreSQL/TimescaleDB | DEFER / REVIEW; real source/test/workflow dependencies |
| Kraken Spot | DEFER / REVIEW; isolated source/test/workflow dependencies |
| Android commercial readiness/privacy/terms | OUTSIDE T0; retain separately |

No component currently meets the evidence threshold for REMOVE-CANDIDATE. The audit did not execute tests, dispatch workflows, inspect live runtime configuration, or access VPS/database state.

## 9. Adversarial self-review of the decision and first-pass audit (2026-11-09)

- Review type: adversarial self-review by the same assistant/work session that authored the record. This is **not an independent second-reviewer sign-off**.
- Reviewed the full decision record, the audit commit diff, the current branch tree at HEAD `b1345afdc5b467014e58624f6d86c6475537f497`, and the cited active-branch source/test/workflow files.

### Findings

| ID | Severity | Finding | Disposition |
|---|---|---|---|
| SR-01 | HIGH / acceptance blocker | GitHub code-search results used for commercial keyword absence target the repository default branch, not the active feature branch. They cannot establish branch-wide absence. | Correctly disclosed in §8.1. Keep commercial capability absence NOT VERIFIED. Requires branch-pinned source/config/workflow content audit. |
| SR-02 | MEDIUM | The recursive active-branch tree path-name scan found only `market_data/test_support.py` among commercial-keyword-like paths; this is a generic test-support filename, not evidence of customer support functionality. Path names alone cannot prove absence in file contents. | Treat as weak corroboration only; do not upgrade status. |
| SR-03 | MEDIUM | The bounded source list does not constitute a complete dependency graph across all 636 repository files, generated configuration, Android, T1/T2 consumers, deployment scripts, or runtime environment. | Keep dependency audit PARTIAL. Next audit must enumerate branch-pinned paths and inspect relevant content/config/workflows plus imports/references. |
| SR-04 | LOW | PostgreSQL and Kraken are classified DEFER / REVIEW, but the current evidence demonstrates technical presence and test/workflow wiring, not whether either is currently used by the owner's active runtime or research workflow. | Classification remains appropriate; do not claim operational use. Add explicit consumer/value assessment before any retention/removal decision. |
| SR-05 | LOW | Android commercial documents are outside T0 architecture, but may still have separate Android distribution/legal obligations. | Preserve separately; no deletion or legal conclusion implied. |

### Review axes

- **Correctness:** scope exclusions are distinct from implementation-presence claims; no unsupported absence assertion should be promoted to PASS.
- **Architecture:** single-owner scope preserves internal service authentication, T0 canonical ownership, read-only consumers, writer fencing and provenance.
- **Security/data integrity:** no proposed scope change weakens access control, signing/evidence custody, backup/recovery, or fail-closed behavior.
- **Completeness:** incomplete; branch-wide content/dependency audit and runtime consumer inventory are outstanding.
- **Verification:** no tests or Actions were run; documentation-only evidence cannot prove runtime behavior.

### Verdict

**SELF-REVIEW: CONDITIONAL PASS FOR SCOPE-BOUNDARY DOCUMENTATION; BLOCKED FOR INDEPENDENT ACCEPTANCE AND ANY REMOVAL.**

No critical contradiction was found in the written scope boundary. SR-01 and SR-03 remain acceptance blockers for claims that commercial capabilities are absent repository-wide. No REMOVE-CANDIDATE is established. A second reviewer who did not author this decision/audit must review the record and evidence before the audit can be marked independently reviewed.

### Next read-only work

1. Perform a branch-pinned content audit over relevant source, configuration, docs, workflows, Android, T1/T2 interfaces and deployment manifests.
2. Build exact import/reference edges for PostgreSQL and Kraken Spot, including consumer entrypoints and CI gates.
3. Determine whether Kraken Spot has an actual personal research consumer and whether PostgreSQL is a supported target or merely an optional adapter.
4. Obtain an independent second-reviewer verdict.
5. Keep all physical removal and runtime/data lifecycle actions unauthorized pending exact-scope owner approval.

## 10. Branch-pinned content audit (read-only, 2026-11-09)

- Audit target: exact branch HEAD `a1053f40a2f762af52237401da2a0d00c4e813b1`.
- Retrieved recursive Git tree successfully: `truncated=false`, 636 tracked blob paths.
- All 13 active `.github/workflows/*.yml` files were fetched by exact commit ref and checked for the excluded commercial capability terms. No relevant matches were found. Workflows remain CI/manual engineering validation; T0 workflows include isolated Kraken and TimescaleDB gates, and T2 HTTP consumer gates.
- Branch-pinned T0 runtime surface checked: `market_data/api.py`, `storage.py`, `postgres.py`, `feeder.py`, `feeder_service.py`, `store.py`, `write_gateway.py`, `kraken_spot.py`, `kraken_spot_api.py`, and `kraken_spot_store.py`. No multi-tenant, billing, subscription, customer onboarding, customer licensing, entitlement, customer SLA/support tier, payment, customer audit portal, or commercial certification implementation terms were found. One `certificate` match in `feeder_service.py` is production PostgreSQL TLS certificate/hostname verification, a security control.
- Branch-pinned T2/dashboard surface checked: `freqai_bridge/ChartProFreqaiResearch.py`, `context.py`, `exporter.py`, `http_candles.py`, `config.research.json`, `control_dashboard/package.json`, `control_dashboard/src/App.jsx`, and `control_dashboard/src/api.js`. No excluded commercial capability terms were found.
- Branch-pinned Android docs/config checked: `android-app/COMMERCIAL_READINESS.md`, `PRIVACY_POLICY.md`, `TERMS_OF_USE.md`, `README.md`, app Gradle config and Android manifest. The explicit commercial-readiness/paid commercialization checklist exists only as an Android release/product document and is outside T0. Android terms contain third-party copyright/licence notices, not a customer licensing system. These files are retained; no change is authorized.
- Additional false-positive/context checks:
  - `futures_intelligence/README.md` uses “subscription set” in the WebSocket market-data topic/subscription sense, not a paid subscription.
  - `docs/T0_STAGING_PROVIDER_RESEARCH.md` uses billing/invoice/payment in cloud infrastructure cost/provider research; it explicitly records provisioning/trial/payment as NOT AUTHORIZED. This is not customer billing.
  - `docs/architecture/T0_T1_T2_DATA_CONSUMPTION_ARCHITECTURE_2026-11-08.md` refers to model certification, not commercial certification.
  - `market_data/test_support.py` is a generic test-support filename; it is not a customer-support workflow.
- Branch-pinned T0 architecture/security docs checked: Candle Contract v1, T0/T1/T2 consumption architecture, Shared Data Foundation, API domain selection criteria, production security/backup/RPO/RTO, staging acceptance checklist and staging provider research. Matches for certificate/TLS, infrastructure billing or model certification are security/provider/research context, not customer commercial subsystems.
- Dependency evidence reaffirmed: PostgreSQL source and runtime composition are concrete; Kraken has a separate adapter/store/API and dedicated test/workflow coverage. Their active use/value remains unverified.

### Updated branch-pinned audit verdict

- No evidence of a T0 customer-facing commercial subsystem was found in the inspected branch-pinned T0 runtime, active workflow, T2/dashboard, or architecture/security surfaces.
- The Android commercial-readiness checklist is real but belongs to Android release/product documentation, not T0.
- This is a **bounded content audit**, not proof over every one of the 636 files. Not every blob was fetched or semantically reviewed; broad non-T0 Python modules, Android implementation files, archived workflows, deployment/runtime files, generated artifacts and external consumer repositories remain incompletely inspected.
- Therefore: **T0 commercial subsystem presence: NOT FOUND IN INSPECTED SURFACE; REPOSITORY-WIDE ABSENCE: NOT VERIFIED.** The previous HIGH blocker is narrowed but not closed.
- No tests, GitHub Actions runs, provider calls, VPS/runtime/DB inspections, or mutations were performed. No workflow run/artifact is claimed. All work is read-only source inspection.
- No REMOVE-CANDIDATE is established. No source deletion, workflow deletion, documentation deletion, runtime change, or data lifecycle action is authorized.


## 11. Follow-on deployment, archived workflow and consumer audit (read-only, 2026-11-09)

### 11.1 Exact branch pin and repository surface

- Branch HEAD at audit start: `ae545616ed5c35767d6f3c00ad77f4deac7bb79f`; tree SHA: `755db16daeef9454c23bae36789afc6953522214`.
- Git Trees API returned `truncated=false` and 636 tracked file paths.
- The active `.github/workflows/` directory contains 13 workflow YAML files. This count is a tracked-tree observation, not a claim that every workflow has recently executed successfully.
- Archived GitHub Actions references are under `ci/archive/github-actions/`, outside GitHub's active workflow discovery path. Their README says the archived definitions are historical and not executed by GitHub, but also says Codemagic runs jobs and points to Codemagic setup. That operational statement conflicts with the owner's current direction that GitHub Actions is the primary CI and Codemagic is deprecated/legacy fallback. Treat the README as stale documentation pending a separate documentation decision; do not infer that Codemagic account workflows are active or inactive from repository files alone.
- `codemagic.yaml` remains tracked (blob `c8626f8b6b55fa7d76cd885a63beb60413d6fd77`) and defines multiple Codemagic workflows, including canonical market data, TimescaleDB, and manual Kraken jobs. This is configuration presence only; external Codemagic account state and actual execution are NOT VERIFIED.
- `ci/run-legacy.py` (blob `2537a750beacea99a8aedd9981b466af99f8da7e`) explicitly describes a bounded Codemagic task and does not call the GitHub Actions API. Its presence is legacy integration code, not evidence of a commercial subsystem.
- `ci/test_ci_policy.py` (blob `42b2c4164b28e1dac32457f36435d05207350714`) asserts that `.github/workflows/` contains no YAML files. That assertion is inconsistent with the same pinned tree, which contains 13 active workflow YAML files. The test is also included in the Codemagic `canonical-market-data` script via discovery of `ci/test_*.py`. This is a concrete CI-policy/configuration inconsistency and a likely failure if that Codemagic job runs against this exact tree; it was not executed here. Do not silently alter CI or workflow configuration as part of this de-commercialization audit.

### 11.2 Deployment and archived workflow findings

- No Docker Compose, Dockerfile, Kubernetes/Helm, Terraform, Ansible, Render/Fly/Railway manifest or conventional systemd unit file was found by the bounded tracked-path scan. This is a path-name scan only and does not prove deployment configuration is absent from scripts, external repositories, or the VPS.
- Relevant tracked deployment evidence includes `.github/workflows/t0-systemd-feeder-api-integration.yml`, `ci/t0_systemd_feeder_api_integration.py`, `ops/ssh/t0-readonly-preflight.sh`, and T0/T2 deployment-gate documentation. These are reliability/integration controls, not customer-commercial features.
- Archived workflow files reviewed include the archive README, market-data CI, T0 single-writer gateway, and dashboard backtest definitions. They are outside the active GitHub workflow directory. Their historical job contents do not establish an active production deployment.
- No archived workflow or deployment path is a REMOVE-CANDIDATE based on this audit.

### 11.3 PostgreSQL/TimescaleDB consumer and capability graph

- `market_data/storage.py` (blob `13fe1ae01ebb5318b69e69eef3e512d207f74c49`) imports both SQLite and PostgreSQL adapters, defaults to SQLite, and supports explicit `MARKET_DATA_BACKEND=postgres` plus `MARKET_DATA_POSTGRES_DSN`.
- `market_data/feeder_service.py` (blob `bdcecf6bc98a2ff070f83098d2c50154a160c99c`) has an explicit PostgreSQL production composition path: PostgreSQL candle store, DB-clock lease store, and transactionally fenced PostgreSQL write gateway on the same DSN. It enforces `sslmode=verify-full` and a remote hostname for PostgreSQL production configuration.
- `market_data/postgres.py` (blob `2fe27fe2d066dda0c192a381b72d27404487b800`) contains read, lease, and fenced write adapter code. It is therefore more than a read-only optional adapter.
- Runtime composition and lease contracts are in `market_data/test_postgres_feeder_runtime.py` (blob `dba7b3a61b3963984c58309e7d334b61c0889256`); disposable TimescaleDB lifecycle integration is in `market_data/test_postgres_feeder_runtime_lifecycle.py` (blob `ff8458fd6250fca264799810d78b2566ebcfda10`).
- Active GitHub workflow coverage includes the `timescaledb-integration` manual gate in `.github/workflows/t0-manual-validation.yml` (blob `395ae93274a9202f14ab63d528be5cd582c30149`) and the separate PostgreSQL grantor reproduction workflow `.github/workflows/t0-postgres16-grantor-repro.yml` (tree entry present at the pinned commit). The lifecycle test is explicitly guarded by a disposable test DSN; it is not proof of a live production database.
- Classification: **KEEP AS SUPPORTED OPTIONAL BACKEND / DEFER OPERATIONAL ADOPTION DECISION**. The code supports a complete alternate T0 runtime path, while SQLite remains the default. Actual owner runtime selection, deployed PostgreSQL use, and cost/maintenance trade-off remain NOT VERIFIED. No PostgreSQL removal is justified.

### 11.4 Kraken Spot consumer and capability graph

- The isolated adapter, store and API are `market_data/kraken_spot.py` (blob `d8191606d27617f964f23736e07fb7fe7458dc39`), `market_data/kraken_spot_store.py` (blob `1736935cf143c11f0789651b5ef80a1821aabbb8`), and `market_data/kraken_spot_api.py` (blob `5d8679f74fe5d4b70d89ba796f83550c6e1f2c58`).
- The store requires a separate on-disk SQLite database and explicitly checks separation from the Binance canonical database. The API is a separate WSGI app at `/v1/kraken-spot/candles`; its module documentation says it does not call the canonical Binance API/storage factory, Futures strategy, backtest or paper execution.
- Dedicated tests exist: adapter `market_data/test_kraken_spot.py` (blob `d60bcc62d68d3a49cec3ab518e1c6a41866c11ae`), store `market_data/test_kraken_spot_store.py` (blob `22dd48746e7b893523a8d8a728d37cccec85e9cb`), and read API `market_data/test_kraken_spot_api.py` (blob `e004b16ea41e45749925e032d2d9cb2bffc14c16`). The active T0 manual workflow exposes three separate Kraken gates.
- The tracked path inventory shows Kraken-specific implementation, tests, docs and workflow references, but no separate consumer module name. The bounded file review found no demonstrated T1/T2/Futures consumer. This does not prove that no external client, manual research workflow, or dynamically configured consumer exists.
- Classification: **DEFER / REVIEW; ISOLATED PERSONAL RESEARCH CAPABILITY, CONSUMER VALUE NOT VERIFIED**. Do not merge with Binance USD-M canonical data or remove until the owner confirms whether Kraken Spot research is wanted and any external/manual consumer is inventoried.

### 11.5 Verdict, coverage limits and next gate

- Branch-pinned path/deployment inventory: COMPLETE for the 636-path Git tree; semantic content audit: PARTIAL.
- Archived workflow review: PARTIAL; four representative files reviewed, not every archived YAML/script.
- PostgreSQL code-level dependency graph: STRONG EVIDENCE of an implemented optional full runtime backend; actual deployment/selection NOT VERIFIED.
- Kraken code-level isolation: CONFIRMED in inspected adapter/store/API/tests/workflow; external/manual research consumer and value NOT VERIFIED.
- CI policy inconsistency: FOUND; exact test and tracked workflow directory contradict. No test execution or CI dispatch was performed.
- Commercial subsystem absence repository-wide: NOT VERIFIED.
- No REMOVE-CANDIDATE established. No source, config, workflow, deployment, data or runtime changes authorized or performed. No tests, Actions run or artifact claimed.
- Next gate: resolve the CI policy inconsistency in a separately scoped CI-maintenance task; complete the Kraken external/manual consumer inventory and owner value decision; then obtain a genuinely independent second review. Any removal still requires exact-path owner authorization. Option C — No Destructive Authority — remains in force.
