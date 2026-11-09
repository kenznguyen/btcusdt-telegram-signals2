# Commercial Scope — Branch-Pinned Content Audit (Phase 1)

Date: 2026-11-09 UTC  
Repository: `kenznguyen/btcusdt-telegram-signals2`  
Branch: `feature/t0-centralized-data-feeder-p1-20261101`  
Audit source commit: `1569dde41f8219cd6fbc9a52d126450715a7995a`  
Tree SHA: `4a0ec1c235aa0c12fa071b2a5c485b807a9f063a`  
Git Trees API: `truncated=false`; 706 tree entries, 636 tracked blobs.

## 1. Purpose and boundary

Continue the read-only repository audit for the six commercial-scope exclusions recorded in the T0 personal-use decision:
1. Multi-tenant architecture and customer-specific authorization / isolated tenancy.
2. Subscription, billing, payment processing, invoicing and plan entitlements.
3. Customer-facing audit portals or customer evidence workspaces.
4. Commercial customer SLAs, support tiers and customer-service workflows.
5. Customer onboarding, licensing, account provisioning and package management.
6. Compliance/certification workflows whose sole purpose is commercial sale, customer procurement or external service commitments.

The scope exclusions remain policy decisions. They are not evidence that an implementation exists or does not exist. This phase is a bounded content audit, not a repository-wide proof of absence.

## 2. Branch and change control

The branch was resolved through GitHub at exact HEAD `1569dde41f8219cd6fbc9a52d126450715a7995a`. Comparing prior audit anchor `31b5239a14b7a13c9f5a39a91a18d9627b7b8159` to this HEAD shows exactly two changed paths:
- `docs/PROJECT_SESSION_HANDOFF.md`
- `docs/evidence/t1/T1_MANUAL_VPS_TEST_RECEIPT_2026-11-09.md`

No application source, dependency manifest, workflow, Android implementation or deployment file changed between those two commits. The recursive tree at the current HEAD is complete (`truncated=false`).

## 3. Inspected source and configuration surfaces

Read exact-commit contents for:
- Root/service entrypoints: `README.md`, `app.py`, `bot.py`, `telegram_commands.py`.
- Integrations: `integrations/README.md`, `integrations/codemagic_client.py`, `integrations/hummingbot_bridge.py`.
- Dashboard: `control_dashboard/src/App.jsx`, `src/api.js`, `src/useTerminal.js`, README, `package.json`, and package-lock header/dependency graph.
- API/decision: `pipeline/api.py`, `pipeline/decision.py`, `pipeline/core_signal.py`.
- Market data: `market_data/api.py`, `storage.py`, `feeder_service.py`.
- Paper ledger: `paper_execution/ledger.py`, `account_history.py`, `risk_control.py`, `daily_baseline.py`, `daily_baseline_v1_recovery.py`, `equity.py`, `funding.py`, `replay_inputs.py`, `replay_reconciliation.py`.
- Research/data bridge: backtest entrypoints, `freqai_bridge/ChartProFreqaiResearch.py`, `context.py`, `exporter.py`, `http_candles.py`, `futures_intelligence/connection_events.py`, `import_collector.py`.
- Android: all 27 tracked Kotlin production source files, app/build Gradle files, main manifest and string resources.
- CI/deployment configuration: all 13 active `.github/workflows/*.yml` files, all 8 archived workflow YAML files plus archive README, `codemagic.yaml`, `ci/run-legacy.py`.
- Dependency manifests: root/web/market-data/CI/FreqAI/synthetic-evidence requirements, Android Gradle dependencies, dashboard package manifest/lock header, Rust sidecar Cargo manifest.
- Relevant documentation: Android commercial readiness, privacy policy, terms, T0 staging provider research, Codemagic setup, Five Layer architecture, dashboard/integrations READMEs, and the T0 personal-use decision.

This is not an exhaustive semantic review of all 636 blobs. Tests, generated evidence bundles, every document, every archived script and all external deployment/account state were not individually reviewed.

## 4. Findings

### F01 — Multi-tenant / customer isolation

**NOT FOUND IN INSPECTED APPLICATION SURFACES; REPOSITORY-WIDE ABSENCE NOT VERIFIED.**

- The paper ledger has an `account_id` column family, but the inspected dual-ledger schema defines `paper_accounts.account_id INTEGER PRIMARY KEY CHECK(account_id=1)`, inserts only account 1, and its account/strategy state queries use the fixed account 1.
- The schema therefore represents one internal PAPER account with strategy-separated ledgers, not a demonstrated multi-customer tenancy implementation.
- The inspected common API uses environment-configured shared Bearer tokens (`MARKET_DATA_TOKEN` for reads and a distinct `CONTROL_TOKEN` for paper controls). No per-customer identity, tenant resolution, customer role model or tenant-scoped authorization was found in the inspected API paths.
- Do not mistake `account_id` for proof of multi-tenancy. Conversely, do not claim global absence until remaining source/configuration surfaces are audited.

Key evidence:
- `paper_execution/ledger.py`, blob `0bc94ae0e704a69e253246a575991c1de436e0a4`: singleton account constraint, account-1 insert, strategy ledgers.
- `pipeline/api.py`, blob `0540540462b3710a25788e4ff47a88272b7ee9c3`: shared environment Bearer-token checks; no tenant identity in inspected routes.
- `market_data/api.py`, blob `81733c9b6de811cbebb2f5d472d41f37f337990c`: one configured API token and canonical BTCUSDT read-only surface.

### F02 — Billing / subscription / payment / entitlement

**NOT FOUND IN INSPECTED APPLICATION CODE OR DEPENDENCY MANIFESTS; REPOSITORY-WIDE ABSENCE NOT VERIFIED.**

- Inspected Android Gradle dependencies do not include Google Play Billing or a payment SDK.
- Dashboard dependencies are React, React DOM and Vite; inspected Python, Rust and Android dependency manifests contain no Stripe/Paddle/payment gateway SDK.
- No checkout, payment webhook, invoice generation, paid-plan entitlement or subscription lifecycle was found in the inspected application source/configuration.
- `docs/T0_STAGING_PROVIDER_RESEARCH.md` contains provider billing, invoice, checkout and payment language for infrastructure cost estimates. It is infrastructure procurement research, and explicitly records provisioning/trial/payment as NOT AUTHORIZED; it is not customer billing.
- Android `COMMERCIAL_READINESS.md` describes paid/free features, refund policy and payment collection as decisions/future conditions, not an implemented payment flow.

Key evidence:
- `android-app/app/build.gradle.kts`, blob `a8380f336774f99d8dbc8272831c9408aa1fbc6f`.
- `control_dashboard/package.json`, blob `b457cb2187bbd282d078bd719d4cedf78cc415eb`.
- `docs/T0_STAGING_PROVIDER_RESEARCH.md`, blob `f511b259daf576f44037399555045a1c45a00f1f`.
- `android-app/COMMERCIAL_READINESS.md`, blob `9532b34f4a7c1dcac571b9ba4fe5064fa2cfc324`.

### F03 — Customer portal / customer evidence workspace

**NOT FOUND IN INSPECTED SURFACES; REPOSITORY-WIDE ABSENCE NOT VERIFIED.**

- `control_dashboard` is named and packaged as `five-layer-paper-control`; its inspected app/API surfaces expose internal market-data, signal, paper-ledger, equity, audit and control views.
- The common API serves its own static dashboard under `/control`; protected API routes use shared environment Bearer tokens. No customer workspace routing, tenant selector, customer-specific evidence sharing or customer account portal was found in inspected files.
- The existence of a dashboard or an internal `/v1/audit` route does not make it a customer audit portal.

Key evidence:
- `control_dashboard/package.json`, blob `b457cb2187bbd282d078bd719d4cedf78cc415eb`.
- `control_dashboard/src/App.jsx`, blob `f549fa442f23d39b0caec5a822dbd1ad3b25bc75`.
- `pipeline/api.py`, blob `0540540462b3710a25788e4ff47a88272b7ee9c3`.

### F04 — Commercial customer SLA / support tiers

**NOT FOUND IN INSPECTED APPLICATION SURFACES; REPOSITORY-WIDE ABSENCE NOT VERIFIED.**

- Inspected workflows are engineering validation, release signing, integration or manual test gates; no customer support-tier workflow or commercial SLA enforcement was found.
- Provider SLA language in staging research refers to infrastructure vendor claims and is explicitly not treated as evidence that T0 meets operational targets.
- Internal freshness, backup, RPO/RTO and readiness targets remain reliability controls, not customer service commitments.
- Android commercial-readiness document lists support procedures/contact and customer-support coverage as unfinished release checklist items, not an active support system.

Key evidence:
- All 13 active workflow YAML files and all 8 archived workflow YAML files were fetched at the exact audit commit.
- `docs/T0_STAGING_PROVIDER_RESEARCH.md`, blob `f511b259daf576f44037399555045a1c45a00f1f`.
- `android-app/COMMERCIAL_READINESS.md`, blob `9532b34f4a7c1dcac571b9ba4fe5064fa2cfc324`.

### F05 — Customer onboarding / licensing / package entitlement

**NOT FOUND IN INSPECTED APPLICATION SURFACES; REPOSITORY-WIDE ABSENCE NOT VERIFIED.**

- Android `COMMERCIAL_READINESS.md` lists future release, support, paid/free, refund and licensing considerations; the document itself states it is operational guidance, not a claim of readiness or implementation.
- Android `TERMS_OF_USE.md` contains ownership and third-party licence notices, not a customer licence issuance/validation system.
- No customer registration, invitation, organization provisioning, licence key issuance/validation, package entitlement or customer onboarding flow was found in inspected Android, API, bot, dashboard and workflow surfaces.
- App signing secrets and release workflows are release engineering, not customer licensing.

Key evidence:
- `android-app/COMMERCIAL_READINESS.md`, blob `9532b34f4a7c1dcac571b9ba4fe5064fa2cfc324`.
- `android-app/TERMS_OF_USE.md`, blob `c1e30a0da62c38bfa6c4bb30f0ed32bc5656e0a6`.
- `android-app/app/build.gradle.kts`, blob `a8380f336774f99d8dbc8272831c9408aa1fbc6f`.

### F06 — Commercial-only compliance / certification

**NO COMMERCIAL CERTIFICATION WORKFLOW IDENTIFIED IN INSPECTED SURFACES; REPOSITORY-WIDE ABSENCE NOT VERIFIED.**

- Synthetic evidence, provenance, signing, verification and retention contracts are technical assurance controls for data integrity, auditability and owner-controlled evidence. Their presence is not evidence of a customer-facing certification service.
- Model certification language in architecture research is not commercial certification.
- No customer procurement/certification portal or commercial attestation delivery workflow was found in the inspected application surfaces.

## 5. False positives / semantic distinctions

- `account_id` in paper execution is a fixed singleton account key, not proof of multiple tenants.
- `payment`, `invoice`, `billing` and `checkout` in provider research refer to infrastructure procurement/cost, not customer payments.
- `license` in Android terms refers to ownership/third-party licence notices, not customer licence management.
- `subscription` in market-data/WebSocket documentation can refer to subscribing to a feed/topic; that is not a paid subscription plan.
- `SLA` in provider research is an infrastructure-vendor statement, not a commercial customer SLA.
- Internal dashboard audit and synthetic evidence attestation are owner/reliability functions, not customer-facing audit or certification products.

## 6. Phase result

| Capability group | Inspected-surface result | Repository-wide result |
|---|---|---|
| Multi-tenant/customer isolation | Not found; singleton paper account and shared-token API observed | NOT VERIFIED |
| Billing/subscription/payment/entitlement | Not found in inspected code/manifests | NOT VERIFIED |
| Customer portal/evidence workspace | Not found; internal paper control dashboard observed | NOT VERIFIED |
| Commercial SLA/support tiers | Not found; internal/provider operational targets observed | NOT VERIFIED |
| Customer onboarding/licensing/package entitlement | Not found; Android future-readiness checklist observed | NOT VERIFIED |
| Commercial-only compliance/certification | Not found; technical assurance controls observed | NOT VERIFIED |

**Overall: PARTIAL — no implemented commercial subsystem was identified in the inspected surfaces. This is not sufficient to declare the entire repository free of these capabilities.**

## 7. Verification and authorization status

- Read-only GitHub source/config/document inspection only.
- Tests NOT RUN.
- GitHub Actions NOT DISPATCHED; no workflow run or artifact is claimed.
- No VPS, runtime, database, external provider account or external repository inspection.
- No source, configuration, dependency, workflow, deployment, data, credential, key, permission or runtime changes.
- No deletion or destructive operation.
- No REMOVE-CANDIDATE established. No removal proposal authorized.
- Option C — No Destructive Authority — remains in force.

## 8. Remaining audit work

1. Complete semantic review of remaining non-test source and configuration files not individually fetched in this phase.
2. Review remaining documentation and generated/configuration artifacts for dormant or indirect commercial capabilities.
3. Inspect deployment scripts and external integration boundaries; repository files cannot establish external account/runtime state.
4. Trace every possible customer/account identity and authorization symbol across all source, tests, migrations and configuration before closing F01.
5. Keep all six repository-wide absence claims NOT VERIFIED until the full content/dependency audit and coverage accounting are complete.
