# Phase 7 — FreqAI temporal lineage diagnostics (paper-only)

Scope: verify that the SHA-bound FreqAI native forecast CSV can be *temporally*
associated with the logged rolling model-training windows. This is a **research
diagnostic, not a model-provenance or OOS certification**.

## Why this is necessary

The existing field \`model_identifier=chart-pro-okx-shadow-v1\` is a constant
FreqAI **configuration identifier**, not a unique trained LightGBM model ID.
The native backtest log contains training-window start/end dates, but the
prediction export does not include the actual model artifact hash, exact model
build used for each prediction, last training feature/label timestamp, or
purge/embargo evidence. An auditor must not infer these from one identifier.

The target \`&-future_return\` uses the price **4 candles ahead** (4 x M15 =
60 minutes). Predictions around a weekly training cutoff should be reported
for scrutiny. Their presence alone is not proof of leakage.

## Existing 180-day Codemagic evidence (2026-10-30)

- Source commit \`5a1c24e21eb332796b3a6eb202d6b2aec9882eef\`.
- Raw FreqAI prediction rows 20,225; accepted \`do_predict=1\`: 17,103;
  rejected/abstained: 3,122.
- 26 training windows logged (30-day train, 7-day backtest cadence).
- Every accepted forecast fell within one **inferred** post-training
  weekly interval. 103 accepted forecasts fall within the first four M15
  candles after such logged cutoffs. Neither fact verifies the model used
  or the training-label purge.
- CORE_ONLY +147.19 USDT, AI_ONLY -95.10 USDT and DUAL -95.04 USDT
  realized paper PnL **excluding funding**. Native Freqtrade entered no
  trades by design. AI promotion remains blocked.

## Codemagic workflow

On branch \`feature/dual-strategy-phase7-model-lineage-20261031\` run
\`dual-strategy-phase3-unit\`. Then manually trigger
\`dual-strategy-phase3-native-research\` with
\`PHASE3_DAYS=180\`, \`PHASE3_DETAIL_MINUTES=5\`,
\`PHASE3_DOWNLOAD_DAYS=220\`.

The job retains all previous Phase 4/5/6 safeguards, then writes:

\`artifacts/phase3/paper/phase7-inferred-model-lineage.json\`

For matching, previously downloaded native artifacts:

\`\`\`bash
python3 -m quant_system.phase7_model_lineage \
  --artifacts-root artifacts/phase3 \
  --config freqai_bridge/config.okx-research.json \
  --out artifacts/phase3/paper/phase7-inferred-model-lineage.json
\`\`\`

The report fails closed on mutated forecast SHA, wrong model config identifier,
duplicate prediction timestamps, invalid forecast origin, predictions before
first observed cutoff, missing Phase 6 report, or inconsistent train logs.
A green \`research_lineage_consistent\` is **not** \`oos_certified\`.

## Required before any genuine OOS certificate

Instrument the native FreqAI prediction boundary to capture actual individual
model artifact IDs/hashes, candle-to-trained-model association, training
feature maximum timestamp, last realized label timestamp and prediction
timestamp. Verify on independent held-out data that
\`latest_training_label_end < prediction_open_time\` and that the exact
configured embargo/purge covers the four-candle forward label horizon.
Require model provenance to be resistant to synthetic/replayed CSV injection.
Then compare *net* out-of-sample paper trading with funding, liquidation and
independent Kotlin/Freqtrade parity.

Never change CORE RSI/ADX/Smart DCA, Shared Risk admission, live-order guards,
Android APK/keystore, or the existing 360-day hard lock as part of this phase.
