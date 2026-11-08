# T2 OOS Temporal Boundary and Leakage Audit — 2026-11-08

## Scope
Read-only audit of the current signed provenance validator, prediction JSONL contract, temporal split manifest, dataset bundle and test fixtures. No runtime, T0/T1 data service, database, exchange or paper execution was accessed.

## Source inspected
- Branch: `feature/dual-strategy-phase22-preholdout-attestation-20261031`
- Implementation under review: `quant_system/ai_provenance_validator.py`
- Test fixtures: `quant_system/test_ai_provenance_validator.py`
- Prior implementation source: `d9765fa786e89d756d059450f149383dc9067636`
- Prior evidence/handoff at audit start: branch HEAD `f718e230be792c8933f66e5b03be101b28858c6e`

## Confirmed controls
1. Signed manifest temporal split requires integer `train_end_ms < oos_start_ms <= oos_end_ms`.
2. Every prediction timestamp is checked against inclusive `[oos_start_ms, oos_end_ms]`.
3. Every prediction's M15/H1 feature cutoff resolves to an exact candle in its corresponding signed snapshot.
4. Referenced candles must be closed, `FIRST_OBSERVED`, `VALIDATED`, and have `availableAtMs <= prediction_timestamp_ms`.
5. Outcome availability must be strictly after prediction time and no later than OOS end.
6. The M15/H1 snapshot and aggregate dataset fingerprints are verified.

## Leakage controls not established
- The `split_protocol` artifact is currently treated as opaque bytes: artifact hash/size are verified, but its content is not parsed or semantically reconciled with manifest split fields.
- The model artifact is also opaque; its training-data lineage and fit cutoff are not independently reconstructed.
- No contract specifies label horizon, label construction, price basis, or the time at which a training label becomes fully observable.
- Consequently, no valid purge/embargo interval can be derived. Requiring feature candles to predate `oos_start_ms` would be incorrect for walk-forward OOS inference, where prior OOS candles may legitimately be used as causal features.
- Feature cutoff metadata is a signed declaration; the validator cannot prove the model implementation actually consumed only the declared candles or exclude hidden features/leakage.
- Prediction row ordering, same-timestamp multi-row semantics and uniqueness identity are not specified. The validator must not impose a uniqueness/order rule without a row identity and event cardinality contract.
- No actual BTCUSDT training dataset, split protocol, model or OOS prediction artifact was supplied. Existing fixtures are synthetic and the split_protocol fixture is placeholder bytes.

## Decision
**BLOCKED — semantic OOS leakage certification.** Existing temporal and feature-availability checks remain valid as limited chronology checks, but they do not establish purge/embargo correctness or absence of training/label leakage.

No code changes or tests were run for this audit because the missing semantics are contract-level, not safely inferable from repository code.

## Required contract before implementation
The following must be defined from the actual training pipeline, not guessed:
1. Canonical machine-readable split_protocol schema and its relationship to the signed manifest's split boundaries.
2. Training sample/label timestamp semantics: what timestamp represents sample start, feature cutoff, label start, and label fully-available time.
3. Actual label horizon or per-sample label end/availability field, plus price basis and candle boundary convention.
4. Purge/embargo policy and whether it is fixed-duration or derived from each sample's label end.
5. Whether same-timestamp predictions are allowed and the stable row identity/cardinality (if ordering/duplicate checks are required).

Once defined, add RED tests for inconsistent split manifests, training-label overlap with OOS, insufficient purge/embargo, and prediction boundary violations; then implement parser/reconciliation fail-closed.

## Safety and project status
- `AI_EXECUTION_ENABLED=false`.
- No T0/T1 DB, feeder, exchange, paper or live runtime accessed.
- No calibration attestation or AI leverage authorization issued.
- PR #95 remains OPEN / DRAFT / NOT MERGED.

## Cross-check against existing Phase13B protocol — not reusable as AI contract
A separate repository protocol was inspected: `research_evidence/frozen-model/phase13b-20261104/phase13b-oos-protocol.json` (blob SHA `0dbf07b12ccb4d4675f34827298456e8d7c69fb7`). It declares:
- model identifier `chart-pro-okx-shadow-v1`, venue OKX USDT perpetual;
- `label_horizon_m15_candles=4`;
- `all_training_labels_end_before_holdout_start=true`;
- no holdout rows for training/scalers.

However, that artifact is a separate Phase13B prospective protocol candidate, explicitly `PRE_REGISTERED_PROTOCOL_CANDIDATE_NOT_SEALED`, with model seal/source/bundle fields still null. It is not the signed split_protocol artifact for the new independent AI strategy and must not be silently reused to define that strategy's label horizon, price basis, purge or embargo. Its own related Phase14 evidence also states full model-pipeline fit causality is not certified. This cross-check therefore does not change the BLOCKED decision.
