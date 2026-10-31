# Phase 21 — preserve the exact original fitted LightGBM bundle

Research-only, manual Codemagic workflow. GitHub stores the immutable source
and verified model bytes; Codemagic performs extraction and native checks.
No GitHub Actions workflow is introduced.

## Source identity

- Original archive: `research_evidence/phase14-frozen-original-evidence.zip`
- Archive SHA-256: `b64f39bd70c27c8d6abed1795ee06504c108eed42ebdab98ce375a6449b5b035`
- Original model SHA-256:
  `918dc4737ee432df8f7f9d2c3e561ac3983aaf56d8791a731a55624ab836b81f`
- Original model size: 436,330 bytes
- Source commit: `082edc082996425f61f48c952be41fb037564103`
- Pre-holdout seal commit: `888efb11b613b42a2badb3bc8adfa19ff090f2bb`
- Registered metadata SHA-256:
  `07e9c1b65df7a477de8ee14c51d47325932e6bf9a0732f3ea64e3118abcac3e5`
- Registered protocol SHA-256:
  `b10d63c952a40fa70a3d4dfed2d952d676a888a0f72832734d3ff8d8c14c5b6e`

## Codemagic execution

Select branch
`feature/dual-strategy-phase21-original-model-preservation-20261031`
and manually run workflow
`dual-strategy-phase21-preserve-original-model`.

Before running, add a masked Codemagic environment variable
`GITHUB_PUSH_TOKEN` with repository Contents read/write permission.
The token is used only by this manual workflow to push the verified model
and provenance files to the same feature branch. Never put the token in Git.

The workflow:
1. Checks the exact Phase14 ZIP SHA, ZIP integrity, model size and model SHA.
2. Retrieves the three pre-holdout seal files from the immutable seal commit
   and byte-compares the original metadata.
3. Runs the existing Phase14 fitted-pipeline audit. The audit must report
   `fitted_preprocessing_prefix_invariance_verified=true`,
   `errors=[]`, the exact model SHA and source commit.
4. Only after the SHA gate, the existing Phase14 audit loads the trusted
   joblib and checks the LightGBM Booster, ordered feature schema, fitted
   DataSieve feature pipeline (`const/scaler/di`), and fitted label scaler.
   It compares native feature rows and forecasts and applies future-suffix
   interventions to the feature and label pipelines.
5. Copies the exact model bytes, sealed metadata, protocol, seal manifest,
   and Phase14 audit report to
   `research_evidence/frozen-model/phase13b-20261104/`.
6. Creates SHA256SUMS, commits the files, pushes without force, then reads
   the committed model back from Git and verifies the remote branch SHA.

## Required acceptance

The Codemagic run is successful only when it records
`PHASE21_FITTED_PIPELINE_VERIFIED` and
`PHASE21_GITHUB_MODEL_PRESERVATION_VERIFIED`, with the committed model
SHA exactly matching the registered value. Inspect the uploaded build logs,
report and repository commit before treating preservation as complete.

If any SHA, size, metadata, source commit, model fingerprint, fitted pipeline,
or audit field differs, the workflow must fail closed. Do not regenerate,
retrain, reserialize, replace or force-push the original model.

## Explicit non-goals and safety

This phase does not run the prospective holdout, train or fit any model,
change CORE RSI/ADX/Smart DCA, change AI signal rules, change Shared Risk,
or authorize AI promotion or live orders.

The untouched OOS protocol remains 2026-11-04T00:00:00Z through
2026-12-04T00:00:00Z. Do not start it early, inspect its future data,
retrain on it, or tune any strategy/model parameter from its results.
`independent_oos_verified=false`, `oos_certified=false`,
`ai_promotion_eligible=false`, and `live_orders_enabled=false` remain
mandatory.
