# AI Strategy GREEN-0 — Provider and Contract Inventory

**Status:** INVENTORY COMPLETE / POLICY AND PROVIDER FREEZE PARTIAL — OWNER DECISIONS REQUIRED  
**Date:** 2026-11-11  
**Branch:** `feature/t0-centralized-data-feeder-p1-20261101`  
**Reviewed HEAD before this report:** `e24e866eb2eb13cb0ff5efb54980b401a44ea101`  
**Scope authorization:** GREEN-0 inspection and documentation only. No production edits, tests, workflow, schema, migration, calibration, runtime or deployment.

## 1. Executive result

The repository already contains useful account-wide paper-risk primitives and strategy-scoped ledger reads. These should be reused rather than replaced by a parallel risk engine.

However, GREEN-0 cannot freeze a complete AI admission context yet. Calibration trust/compatibility, instrument trading rules, a versioned risk-policy snapshot, and AI DCA eligibility do not have an identified authoritative provider/contract in the reviewed implementation paths. These remain explicit blockers. No defaults are selected.

## 2. Provider map

| Contract input | Existing source/path | Observed behavior | GREEN-0 disposition |
|---|---|---|---|
| AI prediction artifact | `pipeline/api.py::context` → `load_report("FREQAI_REPORT_PATH")` | Server loads prediction artifact; caller cannot substitute it. | Existing source identified; artifact schema needs additive calibration evidence. |
| Model/training provenance | `freqai_bridge/exporter.py::make_prediction`; `pipeline/decision.py::_prediction` | Carries/checks model and strategy version, training dataset hash, trained-through and training-completion times, inference dataset/candle match. | Partial foundation only; no calibration provenance or calibration registry. |
| Calibrated confidence | Reviewed `freqai_bridge/exporter.py`, `pipeline/decision.py`, and prediction path | No calibrated confidence object, calibration version/method/hash, calibration dataset, sample/period or calibrated-at fields identified. | **BLOCKED — trusted calibration provider and artifact contract not found.** |
| Account risk / equity | `paper_execution.ledger::read_account_risk_snapshot(db_path, now_ms=...)` | Read-only account-wide snapshot; validates applied migration checksums, equity/mark/funding provenance and freshness; returns `riskReady`, `accountEquityQuote`, gross/reserved exposure, mark observation, dataset version, Kill Switch state and positions. | Existing provider identified for paper risk. It currently enforces a 30-minute mark freshness bound; do not silently replace it with the test fixture's 60-second value. |
| Account mark update | `pipeline.api::equity_snapshot` → `PaperLedger.record_account_mark` → `paper_execution.account_equity.record_account_mark` | Writes/reconciles an account-wide mark using canonical closed M15 data; this is a mutating update path, not the decision-time read provider. | Identified but not invoked in GREEN-0. Do not run or alter account state. |
| Shared Risk Engine | `paper_execution.ledger::PaperLedger._submit_scoped`; `paper_execution.equity`; `paper_execution.risk_control` | Under `BEGIN IMMEDIATE`, checks account equity/risk readiness, configured drawdown/day-loss/gross-exposure limits, 1% margin budget, strategy leverage, pending orders and Kill Switch/pause before reservation/fill. | Existing final admission authority identified. Extend/reuse it; do not build a parallel engine. |
| Kill Switch | `paper_execution.risk_control::snapshot/risk_block_reason`; account snapshot's `killSwitch` | Exposes paused/killed state; new exposure is blocked while risk-reducing operations remain possible. | Existing provider identified. |
| Risk policy version | `risk_policy.py`; `paper_execution.equity.parse_limits` | Constants include Core 13x and 1% margin budget; risk limits come from environment. No immutable `riskConfigVersion` or versioned AI policy snapshot identified. | **PARTIAL — source values exist, but no versioned policy identity.** Owner/provider contract needed before persistence or replay design. |
| AI ledger position | `paper_execution.ledger::read_snapshot(db_path, strategy_id="AI_FREQAI")` | Strategy-scoped read; dual-ledger snapshot exposes position and strategy state. | Existing provider identified; preserve AI-only position isolation. |
| Instrument rules | Reviewed AI decision/book and ledger admission paths | Book validation checks source, symbol, timestamps, bid/ask price and quantity. No authoritative BTCUSDT tick size, lot step, min quantity or minimum-notional provider identified in these paths. | **BLOCKED — instrument-rule source/version/freshness unresolved.** Do not derive filters from visible book depth. |
| AI DCA eligibility | `pipeline/decision.py::evaluate`; `PaperLedger._submit_scoped` | Decision currently proposes a fixed target base; ledger supports ENTRY/DCA/EXIT event semantics and guards DCA state, but no independent AI DCA signal/trigger policy is defined in the reviewed decision path. | **BLOCKED — owner must choose disabled for v1 or approve a separate AI DCA trigger contract.** |
| Intent idempotency | `PaperLedger._submit_scoped` | Existing intent identity/payload hash returns the original persisted order on exact replay and rejects reuse with a different payload. | Existing primitive identified; does not yet prove immutable calibration/equity/risk/instrument snapshot replay. |
| Reservation snapshot | Existing dual-ledger reservation/order path | Account-level reservation and exposure checks exist; full approved AI calibration/policy/equity/instrument snapshot fields and version references were not identified in the inspected API/decision contract. | **PARTIAL/BLOCKED — owner must choose full immutable snapshot vs versioned references; schema implications need separate approval.** |

## 3. Confirmed interface observations

### 3.1 AI decision boundary

- `pipeline.api::decide(data, timestamp)` calls `pipeline.decision.evaluate(..., target_base=...)`.
- `pipeline.decision::_prediction` validates prediction schema/timeframe, inference dataset, model/strategy identifiers, candle identity, trained-through cutoff, prediction freshness and training dataset hash.
- The current decision interface has no `admission_context` input and does not validate calibrated confidence or calibration registry evidence.
- The existing prediction exporter is a raw prediction/provenance boundary, not a calibration service.

### 3.2 Account risk and final admission

- The read-only `read_account_risk_snapshot` is the suitable existing account-risk read boundary to evaluate for GREEN wiring.
- It enforces the repository's current 30-minute mark freshness bound and returns account equity/risk readiness and Kill Switch state. The actual reservation path performs its own transaction-time checks.
- `PaperLedger._submit_scoped` currently recomputes account-level equity/exposure and applies `ORDER_MARGIN_BUDGET_PCT = 0.01`; it also checks strategy leverage and the risk latch before accepting exposure.
- `risk_policy.py` contains `CORE_LEVERAGE = 13` and `ORDER_MARGIN_BUDGET_PCT = 0.01`. The account risk limits are loaded from environment by `parse_limits`; a versioned immutable policy identifier was not identified.
- `read_snapshot(..., strategy_id="AI_FREQAI")` is available for the isolated AI position. Core and AI ledger identities must remain distinct.

### 3.3 Instrument rules and calibration

- The inspected order-book contract validates observed price levels and quantities. These are market-depth observations, not exchange trading filters.
- No trusted calibration artifact registry or calibration object is currently emitted by the inspected prediction exporter/decision path.
- No authoritative lot/tick/minimum-notional metadata provider was identified in the reviewed AI admission paths. This is a discovery result for the inspected paths, not proof that no unrelated repository file mentions exchange metadata.

## 4. GREEN-0 decision register

| ID | Required owner decision | Current state | Safe default until decided |
|---|---|---|---|
| G0-01 | Select trusted calibration registry/manifest and digest verification source | OPEN | No calibrated AI intent |
| G0-02 | Freeze exact model/strategy/training dataset/label/horizon compatibility rules | OPEN | Mismatch or absent provenance blocks |
| G0-03 | Set numerical `C_min`, minimum samples, calibration period and max age based on OOS evidence | OPEN | No AI intent; fixture values are not policy |
| G0-04 | Confirm account-risk provider and freshness semantics; add/identify versioned policy identity | Provider identified; version identity OPEN | Reuse existing snapshot and ledger recheck; do not invent version |
| G0-05 | Select authoritative BTCUSDT tick/lot/minimum-notional rules source and version/freshness | OPEN | No AI order intent |
| G0-06 | Decide AI DCA v1 disabled or approve independent trigger/eligibility contract | OPEN | No AI DCA |
| G0-07 | Choose full reservation snapshot persistence vs immutable version references | OPEN | No schema changes or migration |

## 5. Recommended contract freeze proposal

1. Reuse `read_account_risk_snapshot` as the read-only account-risk provider, subject to explicit owner confirmation of its existing 30-minute freshness semantics; do not introduce a second equity calculator.
2. Keep `PaperLedger._submit_scoped` and its account-scoped transaction as the final Shared Risk Engine admission boundary. It must independently recalculate at reservation time.
3. Reuse `read_snapshot(..., strategy_id="AI_FREQAI")` for AI position only.
4. Keep calibration registry, instrument rules and AI DCA as unresolved blockers until authoritative providers/policies are named.
5. Do not add a synthetic risk-config version, calibration registry, exchange filters, C_min, thresholds or DCA trigger merely to make the interface complete.
6. Do not implement or migrate reservation snapshot fields until G0-07 is explicitly decided and any schema work is separately approved.

## 6. Verification and limits

- Method: read-only source inspection at the exact branch HEAD and fetch of the named source files.
- No tests were run because this gate is provider/contract discovery only.
- No workflow was dispatched.
- No production code or tests changed.
- No database was opened or modified; no account mark, risk state, Kill Switch, order or reservation was touched.
- No T0/T1/T2 runtime, VPS, exchange endpoint, credentials, calibration training, backtest, migration, deployment or live trading was accessed or performed.
- This report does not certify runtime provider health, current account equity readiness, calibration quality, exchange filter accuracy or production readiness.

**Disposition:** GREEN-0 source inventory **COMPLETE**; provider/policy freeze **PARTIAL / BLOCKED ON OWNER DECISIONS G0-01–G0-07**. GREEN-1 through GREEN-5 remain NOT AUTHORIZED.


## 7. Owner decisions — GREEN-0 bounded disposition (2026-11-11)

**Owner approval recorded:** the following provider/policy dispositions are approved as a design freeze only.

- **G0-04 — account risk and Shared Risk Engine:** reuse `paper_execution.ledger::read_account_risk_snapshot` as the existing read-only account-risk source; reuse `PaperLedger._submit_scoped` as the final transaction-time Shared Risk Engine admission authority; preserve account-wide equity/exposure checks and the existing 1% margin budget. Do not introduce a second equity calculator or parallel risk engine. The inspected 30-minute mark-freshness behavior is a current implementation fact, **not** an owner-approved AI freshness policy threshold. AI-specific freshness semantics and immutable risk-policy version identity remain unresolved and must fail closed where required.
- **G0-06 — AI DCA v1:** disabled. The independent AI strategy may produce LONG/SHORT ENTRY intents only. It must not produce or increase exposure through AI DCA in v1. Reopening AI DCA requires a separate trigger/eligibility contract and explicit approval.
- **G0-01/G0-02/G0-03/G0-05 — calibration and instrument rules:** remain blocked. No AI trade intent may be admitted until a trusted calibration registry/manifest and digest verification, provenance compatibility rules, evidence-based calibration thresholds, and authoritative versioned BTCUSDT tick/lot/minimum-notional rules are defined and verified. No synthetic registry, C_min, thresholds or exchange filters may be invented.
- **G0-07 — reservation evidence:** deferred. No choice between full immutable snapshots and versioned references is made here. No schema change or migration is authorized.

**Scope boundary:** this approval resolves only the dispositions above. It does not authorize GREEN-1 through GREEN-5, production code/test edits, schema/database work, migration, calibration training, model changes, backtest/OOS acceptance, feature activation, T0/T1/T2 runtime, VPS, deployment, exchange connectivity or live orders. Paper-only posture and `AI_EXECUTION_ENABLED=false` remain unchanged.

**Status:** G0-04 provider/engine reuse APPROVED with freshness/versioning caveat; G0-06 AI DCA v1 DISABLED; G0-01/02/03/05 BLOCKED; G0-07 DEFERRED. GREEN implementation NOT AUTHORIZED.


## 8. Additional read-only source inventory — calibration and instrument rules (2026-11-11)

**Scope:** repository tree and selected source/documentation inspection at branch HEAD `723570f845c0f52ef5776218cc5486f8864e72f8`. No external exchange request was made; no provider was invoked.

### Calibration source

- `freqai_bridge/exporter.py::make_prediction` publishes raw prediction plus model/strategy versions, training dataset hash, training cutoff and training completion time.
- `pipeline/decision.py::_prediction` validates those prediction/training provenance fields, but has no calibrated-confidence field or calibration artifact reference.
- `freqai_bridge/README.md` requires a trainer-produced provenance sidecar; it explicitly does not certify training-job truthfulness. The inspected sidecar contract contains no calibration registry, calibration dataset, label/horizon calibration manifest, sample count, calibration period or calibrated-at timestamp.
- No trusted calibration registry/manifest or digest-verification provider was found in the inspected FreqAI exporter, decision, API and repository paths.

**Disposition:** G0-01/G0-02/G0-03 remain **BLOCKED**. Raw predicted return and FreqAI `do_predict` are not calibrated confidence and must not be substituted. No AI trade intent until a trusted calibration artifact/provider and compatible temporal OOS provenance are supplied. No C_min or threshold chosen.

### BTCUSDT instrument metadata

- `market_data/binance_connectivity_probe.py::probe_rest` already names the public Binance USD-M `/fapi/v1/exchangeInfo` endpoint.
- Its current `validate_exchange_info` only verifies that BTCUSDT is TRADING, PERPETUAL, BTC/USDT margined/quoted in the expected assets. It does **not** extract or validate `PRICE_FILTER`, `LOT_SIZE`, `MARKET_LOT_SIZE`, `MIN_NOTIONAL`/notional constraints, precision, metadata version or freshness.
- `integrations/hummingbot_bridge.py` supplies an observed order-book snapshot (bid/ask levels and retrieval timestamp); it is not a source of exchange trading filters.
- The inspected AI decision path validates positive order-book prices/quantities only. Those observations cannot be treated as tick/lot/minimum-notional rules.
- No existing authoritative, versioned instrument-rule provider was identified in the inspected paths.

**Candidate source, not yet accepted as an implementation/provider:** Binance USD-M `/fapi/v1/exchangeInfo`, filtered to BTCUSDT and parsed from the exchange's actual symbol filters. A future read-only adapter would need strict filter presence/type/positivity checks, symbol/contract/status checks, deterministic canonical digest/version, observation time/freshness, and fail-closed handling of missing/unknown filter types. Do not infer rules from configured decimal precision or book depth.

**Disposition:** G0-05 remains **BLOCKED**. The current connectivity probe is not an instrument-rule provider and has not been extended.

### Verification and boundaries

- Source inventory only; no tests run and no workflow dispatched.
- No production source or test files changed.
- No Binance network request, API credential, exchange connection, calibration training, model loading or backtest performed.
- No database, T0/T1/T2 runtime, VPS, deployment, order or reservation accessed or changed.

**Result:** calibration provider **NOT FOUND** in inspected paths; instrument provider **NOT FOUND**. Binance `exchangeInfo` is a plausible authoritative upstream candidate but remains unimplemented and unverified for filter completeness. G0-01/02/03/05 remain BLOCKED; GREEN-1..5 remain NOT AUTHORIZED.


## GREEN-0 design contracts drafted — 2026-11-11

Owner approved design/documentation only. Added:
- `docs/architecture/AI_CALIBRATION_ARTIFACT_CONTRACT.md`: logical trusted calibration artifact and registry requirements, provenance/temporal OOS compatibility, confidence validation, policy binding and fail-closed behavior. No provider, schema, method or thresholds selected.
- `docs/architecture/BINANCE_USDM_INSTRUMENT_RULES_CONTRACT.md`: read-only candidate source `/fapi/v1/exchangeInfo`, BTCUSDT filter requirements, normalization/version/digest/freshness and fail-closed semantics. No adapter or network request.

Both documents remain design proposals. G0-01/02/03 and G0-05 remain BLOCKED pending provider/policy decisions. No code, tests, workflow, exchange request, DB, runtime, VPS or deployment action occurred. GREEN-1..5 remain NOT AUTHORIZED.


## 9. GREEN-0 design verification — calibration trust and Binance USDⓈ-M filters (2026-11-11)

### Calibration registry recommendation

A low-cost, personal-system proposal was evaluated: repository-backed append-only registry records, compact manifest/calibration-transform/evaluation artifacts, offline Ed25519 signing of canonical manifest digests, and pinned public-key verification in future read-only consumers. Private signing material must remain offline and must never enter GitHub Actions, repository contents, VPS or runtime.

Trust must be separated into:
- content integrity: digest of exact artifact bytes;
- publisher authorization: signature checked against a pinned trusted public key and explicit key lifecycle;
- statistical validity: reproducible OOS evaluation, dataset lineage, disjoint calibration/training windows, horizon-aware embargo and owner-approved promotion.

A signature does not prove calibration quality or leakage-free data. A digest does not prove publisher authority. The calibration artifact should contain the score-to-probability transform and evaluation evidence; each inference carries its own calibrated confidence bound to the exact artifact ID/version/digest. The artifact must not be modeled as one static confidence value.

This is a recommendation only. Repository-backed registry, offline Ed25519 trust root, schema/canonicalization, calibration method, OOS protocol and numeric thresholds remain owner decisions. No key, registry, artifact or calibration pipeline was created.

### Binance USDⓈ-M official documentation check

Official Binance USDⓈ-M Futures common-definition documentation was reviewed at https://developers.binance.com/zh-CN/docs/products/derivatives-trading-usds-futures/common-definition (localized official page, displayed last modified 2026-08-08). Confirmed semantics:
- `PRICE_FILTER`: each minPrice/maxPrice/tickSize may be zero to disable that individual rule; enabled price alignment is `(price - minPrice) % tickSize == 0`.
- `LOT_SIZE`: quantity must satisfy min/max and `(quantity - minQty) % stepSize == 0`.
- `MARKET_LOT_SIZE` is distinct and applies to market orders.
- `PERCENT_PRICE` constrains limit price against mark price, introducing a separate dynamic mark-price and freshness dependency.
- USDⓈ-M `MIN_NOTIONAL` uses a documented `notional` field. Do not assume Spot `NOTIONAL` schema/semantics.
- `MAX_NUM_ORDERS` and `MAX_NUM_ALGO_ORDERS` are order/account-state constraints, not static tick/lot metadata.

The previous contract's blanket positive-only validation for all tick/filter values was corrected. The instrument contract now records field-specific disabled semantics and correct LOT_SIZE arithmetic.

**Limit:** this was documentation review only. No `/fapi/v1/exchangeInfo` request was made; no live BTCUSDT filters, response schema instance, update time or endpoint behavior were independently fetched. Therefore official docs support the semantics, but endpoint/provider correctness and current instrument values remain NOT VERIFIED.

### GREEN-0 disposition

- Calibration design: architecture recommendation available; trusted provider/key owner and policy remain unresolved. G0-01/02/03 BLOCKED.
- Instrument rules: official filter semantics reviewed and contract corrected; Binance exchangeInfo candidate remains unaccepted and no endpoint data fetched. G0-05 BLOCKED.
- No code/tests/workflow, API request, exchange connection, database/schema/migration, T0/T1/T2 runtime, VPS, deployment, calibration/model or live order action occurred.
