# Phase 14 — Frozen fitted preprocessing causality (research-only)

The independent pre-holdout digest seal is Git commit
https://github.com/kenznguyen/btcusdt-telegram-signals2/commit/888efb11b613b42a2badb3bc8adfa19ff090f2bb,
on branch freeze/phase13b-20261104-candidate-082edc0.
GitHub reported commit timestamp 2026-10-30 22:50:49 UTC, before the
holdout opens on 2026-11-04 00:00 UTC.

Sealed ORIGINAL model provenance:
- source SHA: 082edc082996425f61f48c952be41fb037564103
- bundle SHA-256: 918dc4737ee432df8f7f9d2c3e561ac3983aaf56d8791a731a55624ab836b81f
- metadata SHA-256: 07e9c1b65df7a477de8ee14c51d47325932e6bf9a0732f3ea64e3118abcac3e5
- protocol SHA-256: b10d63c952a40fa70a3d4dfed2d952d676a888a0f72832734d3ff8d8c14c5b6e
- Booster SHA, training cutoff and ordered 20-feature schema are in the manifest.

**Digest registration is not full model storage.** The original joblib has NOT
yet been archived into GitHub by the connector. The metadata field
sealed_in_git=false faithfully describes the older pre-seal run.

## Manual Codemagic verification

1. Upload phase14-frozen-original-evidence.zip to the Phase14 feature
   branch at research_evidence/phase14-frozen-original-evidence.zip.
   SHA-256 MUST be 4758457154f8a23f92e0b48e0122cec0e4d5b92b813c9bed7fe4358c11008c7d.
   It is a 945KB original-evidence subset with source SHA, original model,
   matching metadata, native report, canonical M15, Phase13B audit,
   all matrix event references and frozen model PREDICT NPZ. It does not
   retrain or modify the candidate.
2. Manually run Codemagic dual-strategy-phase14-frozen-preprocessing.
   It checks exact ZIP SHA before processing, fetches the IMMUTABLE seal
   commit, verifies byte-identical metadata and then installs FreqAI 2026.9.
   No exchange data download, no new model training, no live orders.
3. The native audit reconstructs the exact 20 source features from the
   original closed OKX candles and compares five selected frozen-model
   timestamps. Each actually fitted DataSieve transform is cloned and
   tested on the current row and on the same row with altered FUTURE
   rows. Its output must agree with previously captured LightGBM X and
   the native do_predict flag. A fitted label inverse transformation
   must also be unaffected by appended future label values.
4. Read artifacts/phase14/report/phase14-frozen-preprocessing-audit.json.
   Only fitted_preprocessing_prefix_invariance_verified=true and
   errors=[] is evidence of this LIMITED inference transformer audit.

This audit deliberately leaves full_model_pipeline_causality_verified=false
because historical FIT/scaler causality across all training prefixes remains
untested. independent_oos_verified, oos_certified, ai_promotion_eligible,
ready_for_360, full_core_parity_certified and live_orders_enabled remain false.
Never treat a unit test PASS, manifest creation, or historical backtest PnL
as an independent OOS or authorization for live trading.
