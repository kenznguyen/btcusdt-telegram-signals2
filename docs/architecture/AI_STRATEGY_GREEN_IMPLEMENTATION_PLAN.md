# AI Strategy GREEN Implementation Plan — Owner Review

**Status:** PLAN ONLY — OWNER REVIEW REQUIRED  
**Date:** 2026-11-11  
**Branch:** `feature/t0-centralized-data-feeder-p1-20261101`  
**Design authority:** `AI_STRATEGY_CONTRACT.md` and owner-approved `AI_STRATEGY_API_CONTRACT_PROPOSAL.md`  
**Current verified RED source SHA:** `d37c0d4b554bbdcb936c419ebc134c6a8ff28783`  
**Current verified RED run:** [42991526067](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42991526067)

This document sequences a possible GREEN implementation. It does not authorize production edits or select any unresolved policy/provider value.

## 1. Current baseline

- Decision API `pipeline/decision.py::evaluate` currently accepts the legacy inputs and does not accept `admission_context`.
- API ledger factory `pipeline/api.py::ledger` has no explicit `admitted_leverage` argument; non-Core strategy leverage can still be sourced from generic `LEVERAGE`.
- `paper_execution/ledger.py::PaperLedger` enforces positive leverage and pins Core to 13x, but does not enforce AI's [1x, 3x] domain.
- `pipeline/api.py::signal_snapshot` invokes Core and AI decisions separately. Existing E2E test demonstrates AI BUY with Core WAIT, AI ledger isolation and Shared Risk Engine rejection without a reservation.
- Current exact-SHA RED result: compile PASS; 46 tests, 5 assertion failures, 48 skips, 0 errors. The 48 skips are blocked on the missing admission-context API; they are not accepted behavior.
- No production code changes are part of this plan.

## 2. Mandatory owner/provider decisions before GREEN

These are blockers, not implementation defaults:

1. Calibration trust boundary: registry/manifest provider, artifact lookup and digest verification mechanism.
2. Calibration compatibility: authoritative model/strategy/training-dataset identifiers, label definition and forecast-horizon matching rules.
3. Calibration policy: numerical `C_min`, minimum sample count, minimum calibration duration and maximum calibration age. No values are proposed here.
4. Account-risk source: exact existing provider for reconciled equity, `riskReady`, observation timestamp, freshness limit, reconciliation state/version, risk configuration version and Kill Switch.
5. Instrument metadata: authoritative versioned BTCUSDT market/lot/tick/minimum-notional rule source and freshness semantics.
6. AI DCA v1: explicitly choose disabled for v1 or define a separate trigger/eligibility contract. Sizing formula alone is not a DCA strategy.
7. Reservation evidence: decide whether complete immutable inputs are persisted directly or through opaque versioned references. This may imply schema work and therefore needs separate authorization.

Until each mandatory input is resolved, the corresponding path must fail closed. Test fixture values are not production policy.

## 3. Proposed implementation sequence

### GREEN-0 — Provider and contract freeze (no code until resolved)

- Identify existing account-risk, instrument-rule, calibration registry and AI-ledger-position providers in the repository.
- Confirm their source-of-truth, freshness, versioning and failure semantics.
- Freeze the admission-context field contract and provider ownership.
- Explicitly defer AI DCA if its trigger policy is not approved.
- Deliverable: a short provider mapping and resolved/unresolved decision table.
- Exit: no hidden defaults; all mandatory dependencies have an owner and fail-closed behavior.

### GREEN-1 — Pure AI decision admission boundary

Target: `pipeline/decision.py::evaluate`.

- Add a single server-constructed admission context as an additive keyword-only input; retain legacy Core call behavior unchanged.
- Validate the context shape and required version identifiers.
- Validate calibrated confidence as a finite decimal, reject bool/non-finite/out-of-range values, and require configured `C_min`.
- Validate calibration provenance, hash/registry evidence, dataset/model/strategy/horizon compatibility, temporal OOS ordering, sample/period minimums and freshness from the approved providers/policy.
- Derive AI leverage only from the approved formula; never use generic `LEVERAGE`.
- Require fresh reconciled positive equity, `riskReady`, Kill Switch permission and versioned risk configuration.
- Compute ENTRY quantity from the 1% equity margin budget, admitted AI leverage, validated execution limit and lot-step floor. No valid quantity means no intent.
- Keep this function deterministic/pure with respect to provider access; providers construct the immutable context outside it.
- Exit tests: the previously skipped decision-level calibration, policy, freshness, price, instrument and sizing tests become executable and pass. No calibration value may be hard-coded.

### GREEN-2 — AI ledger leverage isolation

Targets: `pipeline/api.py::ledger`, `paper_execution/ledger.py::PaperLedger`.

- Add explicit AI admitted-leverage input to the AI ledger factory.
- Require it for `AI_FREQAI`; reject missing/invalid values and values outside inclusive [1x, 3x].
- Do not fall back to environment `LEVERAGE` for AI.
- Preserve Core fixed 13x and existing MANUAL behavior.
- Keep ledger independently enforcing the AI leverage domain even if API validation is bypassed.
- Do not alter database schema or migrations in this phase.
- Exit tests: explicit AI leverage factory behavior and [1x,3x] ledger boundary tests pass; Core 13x regression passes.

### GREEN-3 — Shared Risk Engine admission and reservation consistency

- Connect the valid AI candidate to the existing account-scoped Shared Risk Engine and Kill Switch; do not create a parallel risk engine.
- Independently recompute the 1% margin budget against current reconciled equity at reservation/admission time.
- Reject stale/unready equity, changed risk state, invalid leverage, exposure/liquidity constraints or Kill Switch denial.
- Ensure a rejection creates no partial reservation, fill or exposure increase.
- Ensure AI position/DCA state is isolated from Core.
- Do not add persistence fields or schema changes until the snapshot-persistence decision is approved.
- Exit tests: E2E AI BUY/Core WAIT writes only to AI ledger; Shared Risk Engine/Kill Switch rejection leaves no reservation/fill; Core state unchanged.

### GREEN-4 — Reservation replay and snapshot evidence (separate gate if schema is needed)

- Implement immutable replay evidence only after the owner chooses full snapshot persistence versus versioned references.
- Enforce idempotent intent replay: same intent identity and same payload returns the original result; same identity with changed payload rejects.
- If a schema migration is required, stop and request separate migration approval before writing it.
- Exit tests: retry/replay cannot silently change calibration, leverage, equity, risk-policy, price, lot rules or quantity.

### GREEN-5 — Regression and paper-only acceptance

- Run focused AI tests and the full existing `paper_execution` suite.
- Verify Core RSI/ADX/Smart-DCA predicates, fixed 13x leverage and ROE/TP/DCA/SL semantics remain unchanged.
- Verify `AI_EXECUTION_ENABLED=false`, no exchange credentials and no live execution path.
- Run Freqtrade strategy-load/compatibility smoke only if the changed interface is used by that integration.
- Record exact source SHA, workflow run, test counts, artifact ID/digest and PASS/FAIL/BLOCKED/NOT VERIFIED.
- No backtest/OOS acceptance, feature activation, VPS, migration/cutover or deployment is implied by this phase.

## 4. Change boundaries

Allowed only after separate GREEN approval:
- The decision API and AI policy validation.
- AI ledger factory and AI-only leverage validation.
- Wiring through existing Shared Risk Engine.
- Tests and documentation needed for the above.

Not included:
- Strategy Core signal logic, RSI/ADX/Smart-DCA predicates or ROE semantics.
- T0 canonical data, T1 collector, T2 data transport or their runtime.
- Database/schema migration, calibration training, model retraining or OOS acceptance.
- AI DCA activation without its own approved trigger contract.
- VPS/runtime changes, systemd/autostart, deployment, exchange connectivity or live orders.

## 5. Approval gates

| Gate | Scope | Status |
|---|---|---|
| A | AI Strategy API Contract design | APPROVED |
| B | RED test-only refinement | COMPLETED for currently exposed API; dependent tests remain skipped |
| C0 | Resolve providers and policy decisions | PENDING OWNER REVIEW |
| C1 | GREEN decision boundary | NOT AUTHORIZED |
| C2 | AI ledger leverage isolation | NOT AUTHORIZED |
| C3 | Shared Risk Engine wiring | NOT AUTHORIZED |
| C4 | Reservation snapshot/idempotency/schema | NOT AUTHORIZED; separate migration approval if required |
| C5 | Paper-only regression acceptance | NOT AUTHORIZED |
| D | Migration, backtest/OOS acceptance, VPS/runtime, deployment or activation | NOT AUTHORIZED |

**Requested next decision:** approve or revise this implementation sequence and resolve GREEN-0 provider/policy ownership. Approval of this plan alone must not be interpreted as approval to edit production code. GREEN requires a separate explicit authorization naming the permitted gates.


## GREEN-0 provider inventory — 2026-11-11

**Owner authorized GREEN-0 inspection/documentation only.** The source inventory is recorded in `docs/evidence/AI_STRATEGY_GREEN0_PROVIDER_CONTRACT_FREEZE_2026-11-11.md`.

- Existing account-risk read provider: `paper_execution.ledger::read_account_risk_snapshot`; existing final transaction-time admission: `PaperLedger._submit_scoped`; existing account policy constant: `ORDER_MARGIN_BUDGET_PCT=0.01`; existing Core leverage: 13x.
- Existing AI ledger position read: `read_snapshot(..., strategy_id="AI_FREQAI")`; existing Kill Switch: `paper_execution.risk_control`.
- Current account snapshot freshness is 30 minutes. It includes account equity, gross/reserved exposure, mark observation, dataset version and Kill Switch state, but no immutable risk-policy version identifier was identified.
- Current prediction/export path has training provenance but no calibrated-confidence artifact or trusted calibration registry.
- No authoritative BTCUSDT tick/lot/minimum-notional provider was identified in the inspected AI admission paths.
- AI ledger supports DCA event mechanics, but the AI decision path does not define an independent DCA trigger/eligibility policy.
- Existing intent replay hashes payload identity and rejects changed-payload reuse; complete immutable calibration/equity/risk/instrument snapshot replay is not yet established.

**GREEN-0 disposition:** source inventory COMPLETE; provider/policy freeze PARTIAL and BLOCKED on owner decisions G0-01–G0-07 in the evidence report. No defaults selected. No tests/workflow run; no code, schema, DB, migration, calibration, model, T0/T1/T2, VPS/runtime, deployment or exchange state changed.

The existing 1% reservation budget, Core 13x and account-risk provider are identified; this does not authorize implementation. GREEN-1 through GREEN-5 remain NOT AUTHORIZED.


## Owner decision record — 2026-11-11

The owner approved a bounded GREEN-0 design disposition:

1. Reuse the existing `read_account_risk_snapshot` read provider and `PaperLedger._submit_scoped` final Shared Risk Engine; do not add a parallel equity calculator or risk engine. Existing 30-minute mark freshness is observed source behavior only, not an approved AI policy threshold. AI freshness semantics and immutable risk-policy version identity remain open.
2. Disable AI DCA in v1. AI may produce independent LONG/SHORT ENTRY intents; DCA remains unavailable until a separate trigger/eligibility contract is approved.
3. Keep AI trade admission blocked until trusted calibration registry/digest verification, provenance compatibility, evidence-based calibration thresholds, and authoritative versioned BTCUSDT instrument filters are resolved.
4. Defer reservation snapshot design. No schema or migration.

This is a documentation/design decision only. GREEN-1..5, production code/tests, schema/database, migration, calibration/model work, backtest/OOS acceptance, feature activation, T0/T1/T2 runtime, VPS, deployment, exchange connectivity and live orders remain NOT AUTHORIZED. `AI_EXECUTION_ENABLED=false` remains in force.


## Additional GREEN-0 inventory — 2026-11-11

Read-only inspection at source HEAD `723570f845c0f52ef5776218cc5486f8864e72f8`:

- Calibration: `freqai_bridge.exporter.make_prediction` and `pipeline.decision._prediction` carry raw prediction and training provenance only. No calibrated-confidence artifact, trusted registry/manifest or digest-verification provider was found in the inspected paths. Raw predicted return and `do_predict` cannot substitute for calibrated confidence. G0-01/02/03 remain BLOCKED.
- Instrument rules: `market_data.binance_connectivity_probe.probe_rest` already queries Binance USD-M `/fapi/v1/exchangeInfo`, but `validate_exchange_info` checks only BTCUSDT contract/status/assets and does not parse trading filters. Hummingbot order-book data is not exchange filter metadata. No authoritative versioned tick/lot/minimum-notional provider was found. G0-05 remains BLOCKED.
- Binance `/fapi/v1/exchangeInfo` is recorded only as a candidate upstream for a future read-only filter adapter, not as an existing provider or verified source in this system.
- No tests/workflow, network request, source-code edit, DB/runtime/VPS action or exchange interaction occurred. GREEN implementation remains NOT AUTHORIZED.


## GREEN-0 design contracts drafted — 2026-11-11

Owner approved the next GREEN-0 step as documentation/design and source-contract inspection only. Two design contracts were added:

- `docs/architecture/AI_CALIBRATION_ARTIFACT_CONTRACT.md`: trusted registry/manifest boundary, artifact identity/digest, model/training/calibration provenance, temporal OOS checks, confidence validation, versioned policy inputs and fail-closed behavior. No registry, schema, calibration method or numeric threshold was selected.
- `docs/architecture/BINANCE_USDM_INSTRUMENT_RULES_CONTRACT.md`: candidate Binance USD-M `/fapi/v1/exchangeInfo` source, BTCUSDT identity, required price/lot/notional filters, normalized version/digest, freshness and fail-closed validation. No adapter or network request was made; endpoint remains a candidate pending owner confirmation.

These are design proposals, not implementation specifications frozen for coding. Open choices include registry/trust root and artifact schema; calibration method/OOS lineage and thresholds; exact supported exchange filter variants, order-type scope, canonical digest and freshness policy.

**Status:** GREEN-0 design deliverables WRITTEN; calibration provider G0-01/02/03 BLOCKED; instrument provider G0-05 BLOCKED; no adapter implementation authorized. GREEN-1..5 remain NOT AUTHORIZED.


## GREEN-0 source/design verification follow-up — 2026-11-11

- Calibration trust recommendation: for this personal low-cost deployment, evaluate a repository-backed append-only manifest/artifact registry with offline Ed25519 signing, pinned public-key verification and explicit promotion/revocation. Separate byte integrity, publisher authority and statistical/OOS validity. The calibration artifact is a score-to-probability transform plus evaluation evidence; each inference carries its own calibrated confidence tied to that exact artifact. No provider/key/schema/method/threshold has been approved.
- Binance USDⓈ-M official documentation review corrected the instrument proposal: PRICE_FILTER zero fields disable individual rules; LOT_SIZE uses `(quantity - minQty) % stepSize == 0`; MARKET_LOT_SIZE is market-only; PERCENT_PRICE needs fresh mark-price data; USDⓈ-M MIN_NOTIONAL uses its own documented `notional` field. Order-count filters are account/open-order-state constraints, not static sizing filters.
- The official documentation was reviewed, but no live `/fapi/v1/exchangeInfo` call or BTCUSDT filter retrieval occurred. G0-05 remains BLOCKED; live source/response validation NOT VERIFIED.
- GREEN-0 design review only; no adapter, calibration pipeline, code/tests/workflow, schema/DB, network/exchange, T0/T1/T2, VPS or deployment action. GREEN-1..5 remain NOT AUTHORIZED.


## Owner decision — calibration registry direction approved (2026-11-11)

Owner approved the **GitHub append-only Registry + offline Ed25519 signing** architecture direction.

Scope of approval:
- versioned immutable manifest/artifact/evaluation records in GitHub;
- offline Ed25519 signing of canonical manifest digest;
- pinned public-key verification by future read-only consumers;
- append-only promotion, revocation, supersession and key lifecycle evidence;
- private signing key excluded from repository, CI/GitHub Actions, VPS and runtime.

This is not implementation authorization. Registry path, manifest schema/canonicalization, key ceremony and rotation/revocation details, verifier workflow/provider, calibration method/OOS protocol and numerical thresholds remain open. No keys or registry were created. G0-01/02/03 remain BLOCKED pending full contract freeze and later implementation approval.
