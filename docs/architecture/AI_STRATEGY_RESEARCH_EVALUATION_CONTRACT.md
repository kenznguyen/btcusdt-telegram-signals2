# AI Strategy Research & Evaluation Contract

**Status:** OWNER-APPROVED RESEARCH SCOPE; protocol proposal for review, not a frozen model specification  
**Date:** 2026-11-11  
**Branch:** `feature/t0-centralized-data-feeder-p1-20261101`  
**Scope:** Offline research and evaluation of an independent BTCUSDT LONG/SHORT signal producer. No production implementation or trading activation.

## 1. Purpose and decision boundary

The research question is whether an AI Strategy can produce independently useful LONG/SHORT signals, including while Strategy Core (RSI + ADX + Smart DCA) is WAIT, after realistic execution costs and across distinct market regimes.

The research must not assume that a model is useful because it predicts direction in-sample, agrees with Core, or emits a high raw score. It must establish:
- what information was available at each decision timestamp;
- how a signal and its outcome label are defined;
- whether evaluation is genuinely chronological and out-of-sample;
- whether net results remain useful after costs and operational constraints;
- whether calibrated confidence is reliable enough for later risk admission.

This contract authorizes research protocol and evaluation design only. It does not authorize model training, production source changes, GREEN implementation, numerical `C_min`, calibration-policy thresholds, feature activation, VPS/runtime, exchange connectivity or orders.

## 2. Strategy independence and signal semantics

1. AI Strategy is a separate signal producer; it is not merely an AI filter or veto over Core.
2. It must be possible to emit AI LONG or SHORT while Core is WAIT. Core output, position, DCA state and ledger must not be prerequisites for AI signal generation.
3. AI may consume approved market data and derived features that are also available to Core, but its decision rule, model version, signal record and evaluation results must be separately attributable.
4. A research signal is an immutable timestamped hypothesis, not an order. Minimum record: symbol, timeframe, decision timestamp, data-as-of timestamp, direction (LONG/SHORT/WAIT), model/strategy version, feature-set version, raw score, label/horizon version and reason/provenance.
5. No signal may use a candle, book observation, funding value, mark price or feature that was not actually available by its decision timestamp. Candle close semantics and publication/availability delay must be explicit.
6. Signal generation and risk admission are separate. Any later trade intent remains subject to calibrated-confidence admission, the shared account-risk snapshot, Shared Risk Engine, Kill Switch, instrument constraints and AI ledger. A research PASS never bypasses those controls.

## 3. Data boundary and point-in-time integrity

- Use only an explicitly approved, immutable research dataset/bundle and record its exact ID, content digest, source, symbol, timeframe, range and schema/version.
- T0 remains the independent canonical data foundation. Research must consume a read-only derived/exported bundle; it must not mutate, delete, migrate, compact or otherwise alter T0.
- Candidate initial market context is BTCUSDT 15m and 1h. This is a research candidate, not authorization to add data sources or change T0 collection.
- Every feature must have a documented formula, source fields, timeframe, warm-up, missing-data behavior, availability timestamp and version.
- Joins across timeframes must be backward/as-of joins. A 1h candle is unavailable until its close and publication rule say it is available; never forward-fill a future higher-timeframe value into earlier rows.
- No future candle, centered rolling window, full-sample normalization, future-derived regime label, revised data unavailable at the time, or target-derived feature may enter inference features.
- Missing, stale, duplicated, out-of-order or gap-affected inputs must be represented and handled deterministically. Do not silently synthesize canonical observations.
- Keep a frozen manifest for each experiment: dataset bundle IDs/digests, code commit, feature schema, label definition, split boundaries, dependency versions, random seeds and run configuration.

## 4. Label and forecast contract

Before fitting any model, freeze the target definition and forecast horizon. A label specification must define:
- decision timestamp and executable reference price;
- direction target (LONG/SHORT) and any neutral/no-trade class;
- forecast horizon in elapsed time and/or completed bars;
- entry/exit price convention and the handling of gaps, missing bars and delisted/invalid periods;
- fee, spread, slippage and funding assumptions used in economic labels;
- whether stop/target barriers are used, their exact formulas and which price stream triggers them;
- treatment of overlapping labels and the purge/embargo interval.

The study should compare a small, predeclared set of economically interpretable label candidates (for example, fixed-horizon net return and a barrier-based outcome) rather than repeatedly changing labels to improve results. Select one primary label/horizon before the final holdout is opened. Label horizon and direction semantics must match the eventual prediction and calibration artifact.

No label may cross a split boundary in a way that leaks future outcome information into training or calibration. Purge overlapping training examples and apply an embargo at least as long as the maximum label horizon plus any required execution/availability delay. Document exact boundary arithmetic.

## 5. Chronological evaluation protocol

Use chronological partitions only; random train/test splitting is prohibited for the primary evidence.

Required stages:
1. **Development/training:** fit model parameters and any feature selection using only the training interval.
2. **Validation/model selection:** select architecture and hyperparameters using rolling or expanding chronological validation folds. Every fold must preserve label purge/embargo.
3. **Calibration:** fit the confidence transformation on a separate later interval not used to fit the base model. Calibration data must not overlap training labels and must satisfy the temporal embargo.
4. **Final untouched holdout:** evaluate once after model, features, labels, thresholds and calibration method are frozen. Repeated peeking or tuning on the holdout invalidates it; a new later holdout is then required.
5. **Walk-forward robustness:** report each chronological fold separately and aggregate only after disclosing fold-level dispersion.

Record for every split: exact UTC start/end, row count, label count, excluded/purged count, dataset digest, model fit cutoff, calibration interval and embargo. Do not use the final holdout to select `C_min`, model version, label, features or calibration method.

## 6. Baselines and comparison design

Compare AI against, at minimum:
- **Always-flat/no-trade baseline**, including the cost of any proposed activity;
- **Strategy Core parity baseline** using the existing RSI + ADX + Smart DCA behavior without changing its parameters or semantics;
- **Simple predeclared directional baseline** (e.g. a fixed-horizon momentum rule) to test whether model complexity adds value.

Report AI standalone results and conditional slices:
- all eligible timestamps;
- Core=WAIT timestamps;
- Core=LONG/SHORT timestamps;
- AI/Core agreement and disagreement;
- LONG and SHORT separately;
- high/low volatility and trend/range regimes, with regime definitions fixed using information available at the time.

Do not claim independence merely because outputs differ. Demonstrate that AI decisions are generated without reading Core position/order/ledger state, and show results on Core=WAIT intervals.

## 7. Metrics and economic realism

Report sample counts and uncertainty intervals, not only point estimates. Required signal/statistical metrics:
- LONG/SHORT/WAIT counts, coverage, class balance and per-direction precision/recall;
- confusion matrix and a suitable threshold-independent metric (e.g. PR-AUC) where class prevalence makes it informative;
- calibration reliability (reliability diagram, Brier score and/or log loss) on untouched data;
- performance by fold, direction, regime and Core-state slice.

Required economic metrics, after realistic costs:
- gross and net return, expectancy per trade, profit factor and win/loss distribution;
- fees, spread, slippage, funding and turnover assumptions separately;
- maximum drawdown, time under water, exposure and adverse/favorable excursion where measurable;
- trade frequency, average holding time, missed/overlapping signals and capacity constraints;
- sensitivity to worse-than-base spread/slippage/funding assumptions.

Execution simulation must use only information available at the decision time and a conservative fill model. A close-price signal cannot assume a fill at that same close unless the execution convention proves that price was attainable after the signal became available. Include latency and next-executable-price assumptions.

No universal numerical pass threshold is set in this document. Thresholds must be pre-registered in a separate owner-reviewed evaluation policy before the final holdout is evaluated. Do not select thresholds after seeing holdout outcomes.

## 8. Calibration and downstream risk boundary

- Raw model score, predicted return, classifier margin and `do_predict` are not calibrated confidence.
- Calibration is a separate fitted transformation using its own later, disjoint data interval.
- Each inference's calibrated confidence must bind to the exact approved calibration artifact digest/version and compatible model, strategy, dataset lineage, label and horizon.
- Report calibration quality overall and by LONG/SHORT, regime and confidence bucket. A single aggregate score can conceal directional miscalibration.
- The existing GitHub append-only registry + offline Ed25519 direction is the selected architecture direction, but its manifest/canonicalization and key lifecycle remain proposals pending freeze. Cryptographic validity does not establish statistical calibration quality.
- Numerical `C_min`, minimum calibration sample count/period, maximum age and acceptable calibration error remain unset. They require evidence and separate owner approval.
- AI DCA remains disabled in v1. Research may study signals for ENTRY only; it must not imply DCA authorization.
- Even after a research pass, any future ENTRY intent must pass the shared risk controls and paper-only ledger. Research approval is not GREEN implementation or execution approval.

## 9. Failure, invalidation and stop conditions

Mark an experiment INVALID / NOT ACCEPTABLE if any of the following occurs:
- future data or revised/unavailable observations leak into features or labels;
- split boundaries, embargo or label overlap cannot be reconstructed;
- model/feature/label/config or dataset digest is missing;
- holdout has been used for repeated selection;
- execution costs/fill assumptions are omitted or materially optimistic;
- class/sample counts are too small to support the stated conclusion;
- results depend on one fold, one direction or one market regime without that limitation being explicit;
- the AI signal path depends on Core position/order/ledger state while claiming independence;
- artifact/calibration provenance cannot be tied to the exact model and dataset.

Missing evidence is NOT VERIFIED, not PASS. A failed experiment is retained with its exact configuration and evidence; do not delete or rewrite unfavorable runs.

## 10. Deliverables and staged gates

**Research Gate R0 — protocol design (this increment):**
- record scope, data boundary, point-in-time rules, label/split requirements, baselines, metrics and stop conditions;
- no model training, code or backtest run.

**Research Gate R1 — owner review/freeze:**
- approve exact dataset bundle(s), feature inventory, label/horizon, cost/fill model, chronological split schedule and pre-registered metric thresholds;
- approve only the research execution scope, not production implementation.

**Research Gate R2 — offline experiment:**
- build reproducible research-only pipeline and run pre-registered experiments against frozen data;
- preserve all runs and artifacts; report per-fold and per-direction results;
- no production signal path, risk admission or VPS runtime.

**Research Gate R3 — independent evidence review:**
- audit point-in-time correctness, leakage, cost realism, reproducibility and statistical claims;
- decide whether evidence supports further calibration-policy design.

**Research Gate R4 — separate owner decision:**
- decide whether to proceed to calibration contract freeze and later GREEN planning. A research PASS does not automatically authorize GREEN-1..5.

## 11. Approval boundary

This document is the R0 research protocol deliverable. The owner has approved preparing this protocol and recording the scope. Exact data bundle, features, labels/horizon, split dates, cost model and numerical acceptance thresholds are not frozen by that approval. R1 review is required before any experiment execution.

Not authorized: production code edits, test/CI changes, model training, backtest execution, calibration training, choosing `C_min`, registry/key implementation or ceremony, schema/database changes, T0/T1/T2 runtime, VPS, deployment, exchange connectivity, feature activation, live orders or any destructive data operation.

Paper-only remains in force and `AI_EXECUTION_ENABLED=false`.
