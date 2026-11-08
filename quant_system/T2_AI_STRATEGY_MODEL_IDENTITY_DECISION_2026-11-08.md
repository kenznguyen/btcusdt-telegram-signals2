# T2 AI Strategy Model Identity and Architecture Decision — 2026-11-08

## Scope

Read-only identity inspection of the frozen Phase22/Phase13B LightGBM candidate and its registered training lineage. This increment records the architecture boundary for the independent AI Strategy. No model bytes were loaded or modified; no training, inference, backtest, T0/T1 access, database, exchange, paper runtime or live execution was performed.

## Exact identity evidence

The frozen candidate metadata at `research_evidence/frozen-model/phase13b-20261104/model-candidate-metadata.json` (Git blob `33acca8aac89f0639694efc84fcff76ddf68d989`) declares:

- Model identifier: `chart-pro-okx-shadow-v1`.
- Candidate bundle SHA-256: `918dc4737ee432df8f7f9d2c3e561ac3983aaf56d8791a731a55624ab836b81f`.
- Booster SHA-256: `39963da56ba2fc1ddcfb3928beb7c50e2ec03a5864e4ddf565029ea56ff1faed`.
- Source commit: `082edc082996425f61f48c952be41fb037564103`.
- Research config SHA-256: `c253091852b704c00fa33bd6fceb69fb4d480630da1645e3e35ebea13888bb72`.
- FreqAI config SHA-256: `a716c80fbb78b8d4bc8b436136912e93e6988a8cdf8d7d1945e8f512bcd6d852`.
- Metadata explicitly marks `proposal_only=true`, `sealed_in_git=false`, and `oos_certified=false`.

The registered seal manifest (blob `2cb9e71ead98568d3fa9c68f504170b12c6bd00d`) binds the same candidate bundle SHA and model identifier. It describes an OKX Phase13B pre-holdout candidate, not an OOS-certified/promotable model. It explicitly leaves `full_model_pipeline_causality_verified=false`, `independent_oos_verified=false`, `oos_certified=false`, and `ai_promotion_eligible=false`.

The preserved-model report `quant_system/PHASE21_ORIGINAL_MODEL_PRESERVATION.md` (blob `bf0baf29724276191528f502e56acf5f83d3ea2c`) independently records the same original bundle SHA, size 436,330 bytes, source commit and registered config/protocol fingerprints. The Phase22 frozen-bundle SHA prefix previously recorded for this project (`918dc473`) matches this exact candidate-bundle SHA prefix. The repository metadata therefore identifies that frozen bundle as the existing `chart-pro-okx-shadow-v1` legacy research candidate; it is not evidence of a separately trained AI Strategy model.

## Legacy training/label contract found

The tracked legacy research pipeline and audit establish only for this legacy model:

- Venue/market: OKX USDT perpetual, BTCUSDT.
- Timeframe: M15.
- Target: `close.shift(-horizon) / close - 1`.
- Configured horizon: 4 M15 candles.
- Label end: `feature_open_ms + 4 * 900000`.
- Fit purge boundary: `max(TRAIN label_end) < min(TEST feature start)`.

Evidence:
- `ChartProFreqaiResearch.py`, blob `0ddaabca32e678bd1c6e181146c2f1418941c133`.
- `config.okx-research.json`, blob `bbccccb8fd6688c8b5b27fa6160b8068f3103f35`.
- `PHASE12_ACTUAL_FIT_LABEL_PURGE.md`, blob `905a51fce85dcbaee4756389e058db0370676783`.
- `phase12_training_audit.py`, blob `a8fc3cb0a2404650f84774ac10e87e8fb6f8cca2`.

These facts are specific to the legacy model. They must not be copied into the independent AI Strategy contract merely because the frozen candidate bundle SHA prefix matches.

## Architecture decision

**DECISION: keep the independent AI Strategy on a distinct model identity and distinct fitted model artifact/training run. Do not promote or silently reuse `chart-pro-okx-shadow-v1` / the Phase22 frozen legacy candidate as the AI Strategy model.**

Rationale:
1. The frozen candidate is explicitly an OKX legacy research candidate and is not OOS-certified.
2. Its model/config/label lineage is not currently bound to the new AI Strategy signed manifest.
3. Reusing its 4-candle M15 label/purge rule without an explicit identity binding would create an unsupported provenance assumption.
4. A separate identity allows independent training lineage, data/venue/timeframe declarations, label semantics, split/purge policy, calibration and leverage acceptance.

This decision does **not** require inventing a new model algorithm or label horizon now. The AI Strategy model identifier, venue/data source, feature schema, target/label formula, price basis, outcome-availability semantics, horizon, training cutoff, purge/embargo, and fit pipeline must be declared from the actual implementation and evidence before an OOS protocol can be sealed.

## Required binding for the future signed manifest

The signed manifest/protocol must bind at minimum:
- immutable AI model ID/version and model artifact SHA-256 + exact byte size;
- training source commit and training pipeline/config hashes;
- dataset identity/version and venue/market/symbol/timeframe coverage;
- ordered feature schema and feature availability/cutoff semantics;
- label schema, price basis, candle boundary convention, horizon or per-row label-end/availability;
- chronological train/validation/OOS boundaries and actual fit cutoff;
- purge/embargo rule derived from the declared label availability;
- prediction artifact identity and model/dataset version equality.

A passing signature/hash check alone does not prove truthful training lineage or absence of hidden leakage. Independent source/fit evidence remains required.

## Status

- Legacy frozen candidate identity: **IDENTIFIED**.
- Match between recorded Phase22 frozen SHA prefix and legacy candidate SHA prefix: **MATCH**.
- Legacy model OOS/promotion eligibility: **NOT CERTIFIED**.
- Independent AI Strategy model identity/artifact: **NOT CREATED / NOT VERIFIED**.
- Independent AI label contract and fit lineage: **NOT DEFINED / NOT VERIFIED**.
- Semantic OOS leakage certification: **BLOCKED**.
- Calibration attestation / AI leverage authorization: **NOT ISSUED**.
- Runtime integration: **NOT IMPLEMENTED**.
- `AI_EXECUTION_ENABLED=false`; no T0/T1, DB, feeder, exchange, paper or live runtime touched.

## Next step

Specify and implement the independent AI Strategy's training-data/label contract from its intended model pipeline, then add signed-manifest model identity binding and semantic split/purge validation. Do not change the legacy frozen candidate or start OOS evaluation until the new protocol is sealed and its provenance is independently verified.
