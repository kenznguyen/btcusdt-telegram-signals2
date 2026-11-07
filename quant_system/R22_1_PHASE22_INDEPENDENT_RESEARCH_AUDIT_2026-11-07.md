# R22.1 — Phase 22 Independent Research Audit

Date: 2026-11-07 (Asia/Ho_Chi_Minh)

## Scope

Read-only source and provenance audit of the frozen Phase 22 LightGBM research line. This increment does not install packages, invoke Freqtrade, access T0, run backtests, train/tune models, open the prospective holdout, alter strategy/model/configuration, or enable execution.

Repository: `kenznguyen/btcusdt-telegram-signals2`
Branch: `feature/dual-strategy-phase22-preholdout-attestation-20261031`
Inspected source commit: `f0a66386c53afe0cbc5de1e182c83beed2b17600`
Project handoff read from default branch; blob SHA: `3e021fb5f1c37392a497b1fc684e2fc388b363c8`.

## Immutable baseline

- Model identifier: `chart-pro-okx-shadow-v1`.
- Frozen model bundle SHA-256: `918dc4737ee432df8f7f9d2c3e561ac3983aaf56d8791a731a55624ab836b81f`.
- Source commit bound by model metadata: `082edc082996425f61f48c952be41fb037564103`.
- Metadata effective config hash: `c253091852b704c00fa33bd6fceb69fb4d480630da1645e3e35ebea13888bb72`.
- Metadata effective FreqAI config hash: `a716c80fbb78b8d4bc8b436136912e93e6988a8cdf8d7d1945e8f512bcd6d852`.
- Ordered feature schema: 20 columns.
- Research venue: OKX USDT perpetual, `BTC/USDT:USDT`; M15 strategy timeframe, 5m detail.
- Prospective holdout protocol: `2026-11-04T00:00:00Z` to `2026-12-04T00:00:00Z`. At this audit date the holdout is still in progress. No OOS certification is claimed.

The frozen bundle, previous backtest outputs, Strategy Core and model metadata were not modified.

## Source-level findings

### 1. Historical configuration

Inspected `freqai_bridge/config.okx-research.json` (blob `bbccccb8fd6688c8b5b27fa6160b8068f3103f35`):

- `freqtrade[freqai]` version pin is `2026.9`.
- OKX isolated USDT futures; M15; BTC/USDT:USDT.
- `dry_run=true`, `force_entry_enable=false`.
- FreqAI: `train_period_days=30`, `backtest_period_days=7`, label horizon 4 candles, shifted candles 2, indicator periods 14 and 28, `test_size=0.2`, `shuffle=false`.
- The historical config also contains `live_retrain_hours=1` and `initial_state=running`. It is NOT SAFE TO START as-is. Do not start this config or a FreqAI process for this audit.

The historical Phase13B workflow passed this OKX config path to `quant_system.native_research`. This is source-level evidence of intended configuration, not proof of the exact runtime-resolved config used by the original run.

### 2. Label construction and split purge

Inspected:
- `freqai_bridge/ChartProFreqaiResearch.py`, blob `0ddaabca32e678bd1c6e181146c2f1418941c133`.
- `freqai_bridge/ChartProAuditLightGBMRegressor.py`, blob `83e93704ebc0c4a37054fe891e7cc2eff0121490`.
- `quant_system/phase12_purge.py`, blob `768a66362d5e78a21b2648eb258d3cd66e0a7956`.
- `quant_system/phase12_sample_identity.py`, blob `6823b56fa203b382fdd90d4519c3e1a6630af1c2`.
- `quant_system/phase12_training_audit.py`, blob `a8fc3cb0a2404650f84774ac10e87e8fb6f8cca2`.

Observed controls:
- Target is future close return using `close.shift(-horizon) / close - 1`; configured horizon is 4 M15 candles.
- The instrumentation intercepts the actual FreqAI train/test split and removes training rows whose label end reaches or crosses the first test feature opening, before the fitted feature/label scalers and LightGBM fit call.
- The split is required to be chronological and non-shuffled; the test fraction is fixed at 20%.
- The training audit reconstructs label values against candle prices and checks train/test timestamp separation and the four-candle label boundary.

Important limitation:
- This purge addresses label overlap at the internal fold train/test boundary. It does NOT turn that internal 20% test partition into an independent prospective OOS test.
- The training audit itself records blockers for full feature causality and independent OOS proof. It explicitly sets `oos_certified=false`.

### 3. Feature and matrix evidence

Feature source uses:
- Relative close to rolling mean.
- Relative volume to rolling mean.
- Percentage change and raw volume.
- Day-of-week and hour-of-day.
- FreqAI expands features using configured timeframes, periods and shifted candles.

The visible feature expressions are causal by inspection (rolling/current and past observations, no explicit negative shift). This is NOT a complete feature-causality proof: effective expanded column ordering, pipeline behavior, all actual fit/predict matrices and every transform boundary still require runtime evidence.

Inspected `quant_system/phase13b_matrix.py`, blob `9550c6b69c0732703d85b070006217cb4b2a355c`. It captures actual LightGBM fit/eval matrices and prediction features/flags, but its own module contract says capture is evidence, not proof of scaler/feature causality or OOS.

### 4. Effective configuration hash

Inspected `quant_system/phase13b_freeze.py`, blob `1add637dea547e6d85f0525f7ce0d23e57d6a95d`, and the custom model instrumentation.

The metadata hashes canonical JSON objects derived from effective runtime configuration, not raw JSON file bytes. The historical raw OKX config SHA-256 is `81229b2321adc1345735e476051dec3e9df6065944b2cff6d5cb8dbad8a41e7d`; it is not comparable to either metadata runtime hash. Effective config hash reproduction remains NOT VERIFIED.

## Findings and status

| Audit item | Status | Reason |
|---|---|---|
| Frozen model identity and immutable baseline | PASS — metadata scope | Exact model ID and bundle/config hashes recorded in existing evidence |
| Historical OKX config intent | SOURCE-VERIFIED | Historical workflow passes the OKX config path; actual resolved runtime object not retained here |
| Label horizon and target definition | SOURCE-VERIFIED | Four M15 candles; forward close-return target |
| Internal train/test label purge | SOURCE-VERIFIED | Explicit chronological purge before scaler/model fit |
| Label value reconstruction controls | SOURCE-VERIFIED | Audit checks raw labels against candle prices and timestamps |
| Feature causality | NOT VERIFIED | Source expressions look causal, but full effective feature/pipeline runtime is not independently proven |
| Effective Freqtrade config hashes | NOT VERIFIED | Requires pinned 2026.9 loader/runtime object or original captured snapshot |
| Historical run reproducibility | NOT VERIFIED | Original full run logs/artifacts/runtime environment not independently replayed in this increment |
| Prospective OOS | IN PROGRESS / NOT CERTIFIED | Holdout closes 2026-12-04 UTC |
| Current Freqtrade runtime | NOT RUN | No package install or CLI invocation authorized/performed |

## CI evidence boundary

Current inspected source commit `f0a66386c53afe0cbc5de1e182c83beed2b17600` has GitHub Actions run `42315157767` for the F1 T0-to-Freqtrade adapter workflow, conclusion SUCCESS. This is unrelated to Phase 22 model/runtime acceptance and is not counted as Phase 22 test evidence.

Previously recorded Phase 22 unit tests (15/15 PASS) remain historical test evidence only; this R22.1 audit did not rerun them and does not upgrade them into runtime/OOS certification.

## Next steps

1. Recover original Phase 22 run manifest, complete logs, artifact inventory and effective runtime config snapshot, if retained. Verify each against exact source/data/model hashes.
2. If the original effective config snapshot is unavailable, request separate approval for a disposable GitHub Actions job pinned to `freqtrade[freqai]==2026.9`. It must use synthetic/local fixtures only, contain no exchange credentials, make no network exchange calls, not start a strategy, not start retraining, and not access T0.
3. Independently verify the complete effective feature schema and transform order against actual pinned runtime matrices.
4. Preserve the existing holdout boundary. Do not tune, retrain, select features, or change thresholds using holdout observations before its close.
5. Only after these checks, decide whether a controlled historical reproduction is justified. Any new model or research run must use a separate version, dataset manifest and output directory; never overwrite the frozen baseline.

## Safety boundary

- T0 remains PAUSED and untouched.
- Strategy Core, Phase 22 frozen bundle, historical backtests and model parameters remain unchanged.
- T1 Shared Risk Engine and paper ledger remain untouched.
- `AI_EXECUTION_ENABLED=false`; native Freqtrade entries remain disabled.
- No paper runtime, exchange connection, live order, production database, deployment or VPS operation was performed or authorized.

Overall R22.1 disposition: **PARTIAL PASS — SOURCE AUDIT ONLY**. Historical runtime reproducibility, complete feature causality, effective config hash reproduction and OOS remain NOT VERIFIED.


## 2026-11-07 — R22.2 runtime config snapshot provenance correction

### Historical caller traced

The prior R22.2 diagnosis that the historical freeze hashes the entire `config` object was incorrect for the Phase13B execution path. Exact historical source at commit `082edc082996425f61f48c952be41fb037564103`, file `freqai_bridge/ChartProAuditLightGBMRegressor.py` (blob `83e93704ebc0c4a37054fe891e7cc2eff0121490`), shows `_capture_phase13b_predict()` builds `config_snapshot` with exactly five fields:
- `freqai`: `self.config["freqai"]`
- `exchange`: a new object containing only `name`
- `timeframe`
- `dry_run`
- `force_entry_enable`

It passes that snapshot to `capture_candidate()`. The snapshot shape in the original probe was therefore correct. The remaining mismatch was the object source: the original probe hashed a subset taken from raw JSON, while the historical caller hashes the five-field snapshot derived from Freqtrade's resolved `self.config`.

### R22.2 implementation correction

- Added `runtime_config_snapshot(config)` to encode the exact historical five-field shape.
- The probe now invokes pinned Freqtrade 2026.9 `Configuration.from_files()` first and derives the hash snapshot from `loaded.get_config()`, rather than from raw JSON.
- The temporary config copy changes only `initial_state` to `stopped`. The `freqai` object, including `live_retrain_hours`, is preserved because it is part of the frozen hash. Configuration loading does not start a bot, strategy, exchange connection or retraining lifecycle.
- Metadata and frozen model hashes were not changed.
- Added regression coverage for the historical five-field snapshot and preservation of frozen FreqAI config fields.

### TDD evidence

- RED test commit: `709b4c05094177a5831c1e54a608bc85470ad925`.
- Direct push workflow: run `42317353456`, job `128233132789`, conclusion FAILURE as expected for RED. Unit test import failed because `runtime_config_snapshot` had not yet been implemented. This is the deliberate failing test evidence, not a runtime acceptance result.
- RED artifact: ID `13551780814`; SHA-256 `10f698b1d48fde7d41984c0c258794d3200d1d88d15f8cd8fffc26023daa32e5`.
- GREEN implementation commit: `74f566ed6066d42107e2d83fa37ba624e5bbcfca`.
- Follow-up test/config preservation commit: `1336841a869899ffc9460f1b7ed90af472fcca9c`.
- At report update time, direct push R22.2 run `42317382779` and PR-context run `42317388653` on source SHA `1336841a869899ffc9460f1b7ed90af472fcca9c` were still IN PROGRESS. No GREEN result is claimed yet.

### Current disposition

| Item | Status |
|---|---|
| Historical five-field snapshot structure | SOURCE-VERIFIED |
| Freqtrade-resolved config object used by the isolated probe | IMPLEMENTED; runtime verification pending |
| RED regression evidence | PASS (expected failure reproduced) |
| Unit tests on corrected source | IN PROGRESS |
| Effective config hash reproduction | NOT VERIFIED |
| Runtime feature schema | NOT VERIFIED |
| OOS certification | NOT CERTIFIED; holdout remains open |

Safety boundaries unchanged: no strategy start, backtest, training/retraining, exchange calls, T0 access, persistent database, deployment, VPS operation or live execution. `AI_EXECUTION_ENABLED=false`; model, Strategy Core, prior backtests and holdout are unchanged.


### R22.2 runtime loader API correction (2026-11-07)

The first implementation attempt used `Configuration.from_files(["--config", path])` and treated the return value as a Configuration instance. Inspection of the pinned upstream Freqtrade 2026.9 source (`freqtrade/configuration/configuration.py`, tag `2026.9`) proves `from_files()` is a static method that accepts a list of config file paths and returns the resolved config dictionary directly. The isolated run confirmed the mismatch: Freqtrade raised `OperationalException: Config file "--config" not found`.

- Source SHA: `1336841a869899ffc9460f1b7ed90af472fcca9c`.
- Direct push run: `42317382779`; job `128233378295`; Freqtrade 2026.9 install PASS; unit tests 4/4 PASS; runtime probe BLOCKED at config loader API invocation.
- Artifact ID: `13551960123`; SHA-256 `f2506abd118d6ecd01249e1d5829f8f944e8bea5ccf299b041584541b4bf0f3e`.
- Corrected source commit: `795109b42dfcb50eb14b5766aeab2133d96f5ac3`; now calls `Configuration.from_files([str(safe_path)])` and consumes the returned dictionary.
- New direct push run: `42317541165` on exact source SHA `795109b42dfcb50eb14b5766aeab2133d96f5ac3`; IN PROGRESS at this report update. No runtime hash or feature schema PASS is claimed.


### R22.2 isolated user-data directory correction (2026-11-07)

The corrected `Configuration.from_files([path])` API reached the pinned Freqtrade loader, but the run stopped because the repository checkout does not contain the default `user_data` directory. This is a local loader precondition, not a config hash mismatch. Pinned upstream Freqtrade 2026.9 source `freqtrade/configuration/directory_operations.py` confirms `create_userdata_dir(..., create_dir=False)` requires an existing directory and then creates only its required subdirectories.

- Source SHA: `795109b42dfcb50eb14b5766aeab2133d96f5ac3`.
- Run `42317541165`, job `128233773628`: Freqtrade 2026.9 install PASS; unit tests 4/4 PASS; runtime probe BLOCKED before hash comparison with `OperationalException` stating default `user_data` directory does not exist; artifact upload PASS.
- Artifact ID `13551556394`; SHA-256 `22f5dc1f5c34fc5ba9e31b2acbff3b2fcebcd54b76f04f9928bb5a7b7636b130`.
- Correction on new source: `build_runtime_config()` now points `user_data_dir` to an isolated temporary directory created by the probe. No persistent repository user_data directory or DB is created. Unit test asserts the isolated path. Commits: `ce886367fe53b658e965e6efeafa1d7b2f798d6d`, `93db167089fa0bda3c3203f2ad829ef84ce7b7c2`.
- Workflow runs on corrected code: push run `42317804086` and PR run `42317809077`, source SHA `ce886367fe53b658e965e6efeafa1d7b2f798d6d`; both IN PROGRESS at report update. The subsequent test-only commit `93db167...` may trigger another run.

Current disposition: effective config hash NOT VERIFIED; runtime feature schema NOT VERIFIED; OOS NOT CERTIFIED. No metadata/model/Core/backtest/holdout changes; no bot start, exchange call, training, persistent DB, T0 access, deployment or live execution.


### R22.2 runtime hash mismatch diagnosis and instrumentation (2026-11-07)

The isolated user_data correction is effective: Freqtrade 2026.9 loads the stopped configuration, resolves the temporary data directory, and confirms OKX support. The remaining runtime blocker is specifically the frozen effective-config hash comparison.

- Exact failing run 42317814579, job 128235016501, checked out source SHA 93db167089fa0bda3c3203f2ad829ef84ce7b7c2. Freqtrade 2026.9 install PASS; four existing unit tests 4/4 PASS; isolated preflight PASS; runtime stopped at PHASE22_EFFECTIVE_CONFIG_HASH_MISMATCH. It did not reach the feature-schema check.
- Artifact ID 13551926335; GitHub upload SHA-256 c7228b636eedbc40d1bb6ddfcf1e7f106af4513d2ba6bc0aebbaa81aa0a3a8e9. Artifact payload was downloaded and inspected; it confirms exact source SHA, paper-only preflight, successful pinned install, and the hash assertion failure. The GitHub upload digest is not independently recomputed from the ZIP bytes.
- Reconfirmed the historical snapshot contract against source SHA 082edc082996425f61f48c952be41fb037564103: the historical capture caller hashes exactly five fields (freqai, exchange name only, timeframe, dry_run, force_entry_enable). The probe already builds that same five-field shape from Freqtrade's resolved config. The remaining mismatch is not the snapshot shape or the missing user_data directory.
- Added TDD coverage for diagnostics on the existing workflow-executed test module. RED run 42318389589, job 128236629997, source SHA 80514cec38b31d16aac67310065cd0bb40ec0ba6: expected ImportError because config_hash_diagnostics had not yet been implemented. The separate initial test file was not discovered by the workflow's explicit test command and was removed; it is not accepted as test evidence.
- Diagnostic implementation commit: 4c676508b6181a06c226f6fbaf7b050ce5ba41ba. Its run 42318496128, job 128237004043, installed Freqtrade 2026.9 and ran five tests, but one diagnostic test failed because the expected list-diff path did not match the helper's indexed path output. Runtime probe was therefore not reached. Artifact ID 13551762708; upload SHA-256 6828447c3fce989773d80239af72354e35e7d4c499444404d556112098430233.
- Corrected list-diff path reporting in commit 5c1f8432b399c0e71464187cc8fe4fd0a1b7fb6e. The diagnostic output is designed to emit only expected/actual config hashes and differing field paths, not raw config values or credentials.
- At this report update, exact-source push run 42318631847 for SHA 5c1f8432b399c0e71464187cc8fe4fd0a1b7fb6e was IN PROGRESS; PR run 42318638339 was PENDING. No runtime hash diagnosis or feature-schema result is yet available for this corrected diagnostic version.

Current disposition: runtime config hash NOT VERIFIED / BLOCKED pending exact-SHA workflow; runtime feature schema NOT VERIFIED; OOS remains IN PROGRESS / NOT CERTIFIED. No frozen metadata/model/Core/backtest/holdout changes; no strategy start, exchange API call, training/retraining, persistent DB, T0 access, deployment or live execution. Next step: inspect the diagnostic hash/path output from the exact-SHA workflow, then reconcile only the provenance discrepancy—never replace the frozen expected hashes or weaken the equality check.


### R22.2 exact-source hash diagnostic result (2026-11-07)

Exact-source direct push verification for diagnostic commit 5c1f8432b399c0e71464187cc8fe4fd0a1b7fb6e completed with the following result:

- Run 42318631847, job 128237448084: Freqtrade 2026.9 installation PASS; all five probe unit tests PASS; isolated paper-only preflight PASS; runtime hash gate FAIL as expected. The runtime did not proceed to feature-schema validation.
- Expected frozen config hash: sha256:c253091852b704c00fa33bd6fceb69fb4d480630da1645e3e35ebea13888bb72.
- Actual Freqtrade-resolved five-field config hash: sha256:0c8974fc45d7b996ab879e78e7047b47a1cdddd4a265d9694192723bc8921893.
- Expected frozen FreqAI subtree hash: sha256:a716c80fbb78b8d4bc8b436136912e93e6988a8cdf8d7d1945e8f512bcd6d852.
- Actual resolved FreqAI subtree hash: sha256:ef8a29169e1a873a517d81869bcad05e0228c66ebdb381b26f5a5d28a167444a.
- Raw tracked FreqAI subtree hash is also sha256:ef8a29169e1a873a517d81869bcad05e0228c66ebdb381b26f5a5d28a167444a; runtime_vs_raw_diff_paths is empty. Therefore Freqtrade's isolated Configuration.from_files loader did not change the five-field snapshot or FreqAI subtree. The tracked config snapshot itself does not reproduce the frozen metadata hashes.
- This establishes a frozen-config provenance discrepancy, not yet its historical cause. Possibilities still requiring evidence include an unrecorded config overlay or a mutation later in the historical FreqAI lifecycle. The current safe probe does not start a strategy or FreqAI training lifecycle, so it cannot distinguish those explanations. Do not rewrite metadata hashes or assume the discrepancy is harmless.
- Artifact ID 13551632525; GitHub upload digest sha256:2d964df0ec9c16e3f4afaf648aa9337341e7c87a4a348bddeb0993970e18bfe4. Artifact ZIP was downloaded and independently SHA-256 recomputed; local digest matched the GitHub digest exactly.
- Artifact confirms source SHA 5c1f8432b399c0e71464187cc8fe4fd0a1b7fb6e, AI_EXECUTION_ENABLED=false, no exchange credentials, no database targets, five unit tests passing, and the hash mismatch diagnostics above.

Disposition: effective-config provenance BLOCKED; runtime feature schema NOT VERIFIED; prospective OOS remains IN PROGRESS / NOT CERTIFIED. Do not change the frozen metadata, model bundle, Core strategy, prior backtests, or holdout. Next safe research step is a read-only provenance trace of the historical candidate-generation command/config inputs and any runtime config mutation path. No strategy start, exchange API call, training/retraining, persistent DB, T0 access, deployment or live execution is authorized by this result.
