# AI Strategy Research Gate R1 — Freeze Proposal

**Status:** PROPOSAL ONLY / OWNER DECISIONS REQUIRED  
**Date:** 2026-11-11  
**Branch:** `feature/t0-centralized-data-feeder-p1-20261101`  
**Parent protocol:** `docs/architecture/AI_STRATEGY_RESEARCH_EVALUATION_CONTRACT.md`  
**Purpose:** Prepare a reproducible, bounded offline research configuration. This proposal does not freeze experiment inputs and does not authorize R2 execution.

## 1. Decision principles

R1 must freeze the dataset identity, point-in-time feature inventory, primary label/horizon, chronological split plan, execution-cost model and acceptance thresholds before any R2 experiment. A choice is not frozen merely because it appears in this proposal.

Recommendations below are deliberately conservative and are subject to owner approval plus artifact-level verification. If the required source evidence is absent, the item remains BLOCKED rather than being filled with an assumption.

## 2. Dataset proposal

**Recommended scope:** BTCUSDT only; 15m decision timeframe with 1h context; read-only immutable T0-derived research bundle.

Candidate bundle identifier already used by the project architecture: `T0_M15_H1_DATASET_BUNDLE_V1`. Its actual availability, content digest, covered UTC interval, row counts, gap report, schema version and provenance must be verified from the bundle manifest before it can be frozen.

Proposed constraints:
- No direct write access to T0 and no changes to T0 schema, retention, lease, feeder or canonical DB.
- Do not create a new export or copy data until the exact approved read-only extraction path and scope are reviewed.
- Exclude incomplete candles at each decision timestamp. Define candle-close availability and any publication delay explicitly.
- Record exact UTC start/end, digest, row counts, missing intervals, duplicate/out-of-order counts and source/version.
- If the candidate bundle is absent, stale, incomplete or not immutable, stop R1 dataset freeze and request a separate data preparation decision. Do not silently substitute exchange downloads, synthetic data or another timeframe.

**Owner decision D1:** approve this candidate bundle and timeframe scope, subject to manifest verification; or nominate another immutable bundle.

## 3. Feature inventory proposal

Start with a small, auditable market-only feature set. Do not use account state, Core position/order/ledger, future labels, or any feature whose point-in-time availability cannot be proven.

Candidate features, computed only from completed bars:
- M15: close-to-close returns over 1, 4 and 16 bars; normalized candle body and high-low range; rolling realized volatility; ATR-normalized range; volume relative to a trailing-only baseline.
- H1: close-to-close returns over 1 and 4 completed bars; ATR/normalized range; trailing realized volatility; trailing volume ratio.
- Optional regime descriptors: trailing volatility percentile and trailing trend-strength measure, calculated using past-only windows and frozen definitions.

All rolling windows must be trailing, with explicit warm-up and missing-value behavior. H1 values join to M15 by backward/as-of timestamp only and become available only after the H1 candle is complete. Normalization parameters are fit on training data only and then applied unchanged to later partitions.

Do not add order-book, funding, open-interest, liquidation or external sentiment features in the first research pass. Such sources introduce additional availability, coverage and provenance risks and should require a separate amendment.

**Owner decision D2:** approve this restricted OHLCV-derived candidate inventory, or request changes before feature schema freeze.

## 4. Label and horizon proposal

**Recommended primary candidate:** fixed-horizon directional outcome over 16 completed M15 bars (4 hours), using the first executable reference price after the signal becomes available and a conservative executable exit reference at the horizon. Compute gross return and net return separately.

Proposed label classes:
- LONG: forward net return exceeds a pre-registered positive neutral band.
- SHORT: forward net return is below the corresponding negative band.
- WAIT/NEUTRAL: return remains within the band.

The neutral band must account for round-trip fees, spread, slippage and funding where applicable. Its numeric value cannot be set until fee tier and execution-cost assumptions are evidenced and approved. Do not use same-close fills unless the signal availability and fill model demonstrate that the close was executable after signal generation.

Secondary sensitivity only (not for selecting the final model): 4-hour versus 1-hour and 8-hour horizons may be reported only if they are pre-registered before training. The primary horizon remains the sole basis for the headline acceptance decision.

Alternative label family: barrier-based outcome. Defer it from the first pass to avoid multiple degrees of freedom; it may be proposed later with a separate owner-approved contract amendment.

Purge every sample whose forward label interval overlaps a later split. Embargo at least the maximum label horizon plus the documented data-availability/execution delay.

**Owner decision D3:** approve 4-hour fixed-horizon as primary and neutral-band three-class labeling; or select a different primary horizon/label before any model fitting.

## 5. Chronological split proposal

Do not invent calendar boundaries until the verified dataset coverage is known.

Recommended split method: expanding walk-forward development folds followed by one untouched final chronological holdout. Suggested proportions for planning only:
- earliest 60%: initial training region;
- next 15%: chronological validation/model selection;
- next 10%: separate calibration region;
- latest 15%: untouched final holdout.

These proportions are not yet frozen. Exact UTC boundaries must be derived from verified bundle coverage, then adjusted for warm-up, label purge and embargo. Require at least two chronological validation folds if the available coverage permits; otherwise mark the evidence limitation and do not claim robust walk-forward validation.

No training label may extend into validation/calibration/holdout. Calibration must be later than the base model's fit cutoff and disjoint from model training. The final holdout is opened once after all model, feature, label, cost and threshold decisions are frozen.

**Owner decision D4:** approve these planning proportions as the starting split design, subject to coverage and sample-count feasibility; exact timestamps remain pending dataset inspection.

## 6. Execution-cost and fill proposal

Use a conservative, transparent, parameterized model. Do not hardcode unsupported fee rates.

Required inputs to freeze from evidence:
- actual applicable maker/taker fee schedule for the intended paper simulation assumption;
- bid/ask spread proxy and its source/availability timestamp;
- slippage model, including a stressed scenario;
- funding rate and funding timestamp convention for any position spanning funding events;
- decision-to-order latency and first executable price convention;
- partial-fill, no-fill, gap and missing-observation handling.

Report at least base and adverse-cost scenarios. If historical bid/ask or other execution data is unavailable in the approved bundle, disclose the limitation and use a conservative pre-registered proxy with sensitivity analysis; do not present it as observed spread or actual fill evidence.

No assumption of zero fees, zero slippage, guaranteed close-price fills or omitted funding is acceptable.

**Owner decision D5:** approve the cost-model framework; actual parameter values remain blocked pending source evidence and explicit selection.

## 7. Baselines and evaluation slices

Required baselines:
1. Always-flat/no-trade.
2. Existing Strategy Core RSI + ADX + Smart DCA parity baseline, unchanged.
3. One simple trailing-only directional momentum baseline, with its exact formula and threshold frozen before final evaluation.

Required slices:
- all eligible timestamps;
- Core=WAIT;
- Core LONG and Core SHORT separately;
- AI LONG, AI SHORT and AI WAIT;
- AI/Core agreement and disagreement;
- volatility and trend/range regimes, with past-only regime definitions.

AI signal generation must be demonstrably independent of Core state. The Core=WAIT slice is a key research question, not a post-hoc optional chart.

## 8. Acceptance thresholds — proposal, not numerical freeze

Before final holdout evaluation, register numerical thresholds for:
- minimum eligible and labeled sample counts overall and per direction;
- minimum count and coverage in Core=WAIT slice;
- maximum calibration error and minimum calibration sample count;
- minimum net expectancy / return after base and adverse costs;
- maximum drawdown and exposure limits;
- minimum number of positive chronological folds and permitted fold dispersion;
- uncertainty interval method and confidence level;
- minimum incremental value versus both Core parity and simple baseline.

Do not select thresholds after inspecting holdout results. Prefer thresholds tied to risk and practical utility rather than optimizing a single metric. If sample size is insufficient for a directional or regime slice, mark it NOT VERIFIED; do not merge slices to manufacture a pass.

**Owner decision D6:** approve the threshold categories and the rule that numerical values must be pre-registered after data/cost evidence is available. Numeric thresholds are not supplied by this proposal.

## 9. R1 readiness checklist

R1 may be marked FROZEN only when all of the following are recorded with evidence:
- [ ] Exact immutable bundle ID, digest, schema, UTC coverage, row counts and gap/quality report verified.
- [ ] Point-in-time feature schema and formulas versioned; H1 as-of join and warm-up rules explicit.
- [ ] Primary label, executable price convention, horizon and neutral band frozen.
- [ ] Split timestamps, purge/embargo arithmetic and minimum sample feasibility documented.
- [ ] Fee, spread, slippage, funding, latency and fill assumptions evidenced and frozen.
- [ ] Baselines, evaluation slices, metrics, uncertainty method and numerical acceptance thresholds pre-registered.
- [ ] Experiment manifest template identifies code SHA, data digests, config, dependencies and random seeds.
- [ ] Owner explicitly approves the complete R1 configuration and separately authorizes bounded R2 offline execution.

Until all checklist items pass, R1 is PENDING and R2 is NOT AUTHORIZED.

## 10. Current status and non-authorizations

This document is a proposal to support owner decisions. It does not create or inspect a dataset, run a backtest, train a model, fit calibration, choose `C_min`, or create experiment artifacts.

No production code, tests, CI workflow, database/schema/migration, T0/T1/T2 runtime, VPS, deployment, exchange connectivity, feature activation, order or destructive data operation is authorized. T0 remains independent and unchanged. Strategy Core remains unchanged. AI DCA remains disabled in v1. Paper-only remains in force and `AI_EXECUTION_ENABLED=false`.


## 11. Owner decision recorded — dataset integrity policy

**Decision:** APPROVED IN PRINCIPLE (2026-11-11).

The owner accepts a lightweight SHA-256 + manifest integrity and provenance policy for AI Research datasets:
- Each immutable dataset bundle has a stable dataset ID and a manifest.
- The manifest records source, symbol, timeframes, UTC coverage, schema version, file inventory, row/candle counts, quality/gap report and creation metadata where available.
- Each bundle file is hashed with SHA-256; the manifest itself is also hashed and its digest is recorded in the experiment record.
- Research runs record the dataset ID, manifest digest and relevant file digests alongside source-code SHA and experiment configuration.
- Existing bundles are never silently overwritten. A changed dataset is represented by a new immutable version/ID.
- SHA-256 is an integrity comparison, not proof that the source data is correct, complete, authentic or statistically suitable. Source provenance and quality checks remain separate requirements.
- Keep the implementation minimal; do not introduce a new service or infrastructure solely for this policy.

**Boundary:** This approval does not confirm that `T0_M15_H1_DATASET_BUNDLE_V1` exists, does not approve reading/exporting/copying T0 data, and does not freeze D1's exact bundle digest, coverage or quality. Those require a separately scoped, read-only verification step and evidence. D1 remains PARTIALLY DECIDED; R1 is not frozen and R2 remains NOT AUTHORIZED.
