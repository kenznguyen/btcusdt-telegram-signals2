# Phase 15 — Original frozen candidate's train-time preprocessing re-fit

**Not an OOS certificate, live-trading authorization or 360-day green light.**

Earlier evidence:
- Phase12: verified prefit TRAIN/TEST split and four-M15-label purge.
- Phase13B: witnessed actual native LightGBM X/y/sample_weight for each fold.
- Phase14: verified frozen fitted transforms on five model-inference candles.
- Frozen Git digest seal: `888efb11b613b42a2badb3bc8adfa19ff090f2bb`
  (GitHub timestamp 2026-10-30T22:50:49Z, before OOS start).
- Original candidate model SHA256:
  `918dc4737ee432df8f7f9d2c3e561ac3983aaf56d8791a731a55624ab836b81f`.

## Exact original fit evidence (not future market downloads)

Download `phase15-original-fit-evidence.zip` and upload **unchanged** to:
`research_evidence/phase15-original-fit-evidence.zip` on the Phase15 branch.

SHA-256 **must** equal:
`68c9c8b9ff00a8173bc267a3ac8cd1adba89772cb2be8813c3d3e4819610b323`.

The 3.3 MB ZIP contains the original model joblib, untouched metadata,
canonical closed OKX M15, full original Phase12 source-row sample ledger,
all original Phase13B matrix event references, and the latest model's two
real **FIT_TRAIN / FIT_TEST** NumPy archives; those were captured at the
actual LightGBM calls, *before* this Phase15 implementation existed.
The original source-row and event SHA256 have been independently checked
against the original native research JSON.

Manually run Codemagic workflow:
`dual-strategy-phase15-original-fit-causality`.
It hard-verifies original archive SHA, source commit, original pre-holdout
Git manifest and byte-exact candidate metadata before loading any joblib.
It installs pinned FreqAI, runs five fail-closed unit regression cases,
then performs a **research-only replay of FreqAI feature and label
preprocessing fit** from the source rows in the original dataset.

The verification requires:
1. Historical source timestamp identity, ordered TRAIN/TEST partition,
   actual close-to-future-close label value, label horizon and purged
   TRAIN/TEST boundary.
2. Fresh, unfitted FreqAI 2026.9 feature pipeline (variance threshold,
   scaler, dissimilarity index) and label scaler fit **only on original
   TRAIN X/y/w**. Neither TEST nor future/OOS rows may participate in fit.
3. **All** transformed 2,296 TRAIN and 572 VALIDATION rows' full
   X/y/sample_weight must reproduce the original native LightGBM input
   archive within strict tolerances.
4. Original joblib's fitted feature/label states must independently
   reproduce the native validation matrix, not merely five forecast rows.
5. Adversarially changing all raw OHLCV **after the original train cutoff**
   must not change any original prefit TRAIN or TEST feature vector.
6. Positive controls: changing an eligible TRAIN volume and TRAIN label
   MUST change fitted feature and label transformations, respectively.
   Without these controls, the future-invariance test is not trustworthy.

Expected report:
`artifacts/phase15/reports/phase15-original-fit-causality-audit.json`.
A PASS requires `fitted_training_time_causality_verified=true`
and `errors=[]`. These are **expected**, not yet demonstrated by native
Codemagic. A failing archive, source row, scaler, feature or label trace
MUST fail the manual workflow; no fallback to newly trained LightGBM.

Even a PASS is evidence only for the **last sealed original candidate fold**.
It is not retroactive observation of all 26 model-fit invocations and
cannot prove all historical fits or guarantee unseen-data performance.
Therefore `full_model_pipeline_causality_verified`,
`independent_oos_verified`, `oos_certified`,
`ai_promotion_eligible`, `ready_for_360`,
`full_core_parity_certified`, and `live_orders_enabled` remain false.

No changes to RSI/ADX/Smart DCA, Shared Risk, Android or APK signing.
No GitHub Actions execution; GitHub is source/evidence storage, Codemagic
is execution.
