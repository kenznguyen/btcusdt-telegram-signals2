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


### R22.2 historical hash interpretation correction (2026-11-07)

A further historical source audit found commit 0a0a9241c6679c0074aaa0831870d87e32872b18 (2026-10-31), which explicitly distinguishes the pinned source-JSON FreqAI hash from the FreqAI runtime hash recorded in the frozen metadata. Its Phase16 frozen-OOS gate pins:
- Source JSON FreqAI hash: sha256:ef8a29169e1a873a517d81869bcad05e0228c66ebdb381b26f5a5d28a167444a.
- Frozen metadata runtime FreqAI hash: sha256:a716c80fbb78b8d4bc8b436136912e93e6988a8cdf8d7d1945e8f512bcd6d852.

This exactly matches the R22.2 diagnostic's raw/resolved pre-FreqAI hash and expected frozen runtime hash. Therefore the previous statement that the tracked config snapshot itself does not reproduce metadata should not be interpreted as evidence that frozen metadata is wrong. The source JSON hash is reproduced; the metadata intentionally records a distinct post-FreqAI runtime configuration hash. The prior diagnostic correctly demonstrates that Configuration.from_files alone does not perform the historical FreqAI runtime mutation/resolution.

The remaining task is to identify the exact, source-backed transformation or historical config overlay that produced the runtime hash, then reproduce it using synthetic/local-only fixtures without starting a strategy, bot, backtest, training or retraining. Current upstream source inspection found a conditional DataKitchen default that inserts data_split_parameters.shuffle=false only when absent; the tracked source JSON already contains shuffle=false, so that single default does not explain the distinct hash. Do not invent a mutation, inject guessed defaults, replace the expected hash, or weaken the hash equality gate.

Corrected disposition: source JSON hash reproduction PASS; frozen runtime hash reproduction NOT VERIFIED / BLOCKED; runtime feature schema NOT VERIFIED; prospective OOS IN PROGRESS / NOT CERTIFIED. Historical metadata is not declared invalid based on this mismatch alone. The exact runtime transformation/overlay remains an open provenance question. No model, metadata, Core, backtest, or holdout changes; no bot start, exchange API call, training/retraining, persistent DB, T0 access, deployment or live execution.


### R22.3 — Historical FreqAI runtime transformation reproduced (2026-11-07)

#### Root cause

The earlier R22.2 probe used Freqtrade 2026.9 Configuration.from_files(), which loads and normalizes config files but does not execute the JSON Schema validation stage. The historical config snapshot is captured after Freqtrade has applied nested schema defaults.

Pinned upstream Freqtrade 2026.9 source confirms:
- Configuration.from_files() returns the loaded configuration from Configuration initialization without calling validate_config_schema().
- FreqtradeBot resolves the strategy and calls validate_config_consistency(config).
- validate_config_consistency() invokes validate_config_schema().
- FreqtradeValidator recursively inserts declared schema defaults into nested objects, including the FreqAI feature_parameters defaults.

R22.3 now applies the same pinned validate_config_schema() function directly to the isolated, stopped configuration object. It does not instantiate FreqtradeBot, load/start the strategy lifecycle, or start FreqAI.

#### Frozen hash reproduction

TDD RED:
- Test commit 8a670d5bf8a53951c3c712981caee2953be907d9.
- Direct push run 42319979203, job 128241905715: Freqtrade 2026.9 installation PASS; five existing tests PASS; new schema-validation helper import failed as expected.
- Artifact ID 13552447418; GitHub upload digest sha256:882a6ad38b79b57de6fb1150b017d7667e1f9e6103486cfafcdc7694060e72f5.

Schema-validation implementation:
- Commit 27f2c554b56792240a385ea439987fb8d210c065.
- Direct push run 42320096376, job 128242288536: Freqtrade 2026.9 installation PASS; 6/6 tests PASS; new test proves both frozen hashes match after schema validation. The standalone probe then exposed a separate script import-path issue before feature checks.
- Artifact ID 13552497112; GitHub upload digest sha256:f80834c6ff4bc7f52833e082fe6c9cceca14058dc79191bd38db8393f2422cf2.

#### Native FreqAI feature-schema verification

The previous probe generated the expected 20-column order with a local helper but did not execute FreqAI's own expansion method. R22.3 added a synthetic-only test through FreqaiDataKitchen.populate_features(), the actual ChartProFreqaiResearch feature methods, and Freqtrade's remove_special_chars_from_feature_names() normalization used before model fitting.

- TDD RED commit 7e99fa10902cb1c0e036ac5a52e93999d846c605.
- Direct push run 42320324256, job 128243049184: 8 tests executed; two expected ImportErrors confirmed the missing repository-root import helper and native DataKitchen feature helper. Artifact ID 13552447999; upload digest sha256:3a23911f5518c8debd0671c99ca4af5d86abfcb321736d55b60d35e5aba63b2f.
- Initial native DataKitchen implementation commit f2049ec1105167b2e51756b225381360648a553a.
- Run 42320481514, job 128243566904: 8 tests executed; one feature-schema comparison failed because the first probe version had not yet applied Freqtrade's colon-removal normalization. Artifact ID 13552841151; upload digest sha256:14793d111d4d68c71fd5e79db17f6f57d90c2f0a7d0e326b25703d0cf64a64f9.
- Added the same DataKitchen feature-name normalization as the historical backtest fitting path.

#### Final exact-source verification

- Final implementation source SHA: 4079212886d29e9943e791c8f206a4fc4cfdaece.
- Direct push workflow run 42320612784: SUCCESS.
- Job 128243995654: all steps SUCCESS; pinned Freqtrade 2026.9 installation PASS; unit tests 8/8 PASS; isolated runtime probe PASS; artifact upload PASS.
- PR-triggered duplicate run 42320620156: SUCCESS on the same head SHA. Direct push run remains the primary exact-head evidence.
- Artifact ID 13552174748; artifact name r22-2-phase22-runtime-4079212886d29e9943e791c8f206a4fc4cfdaece; GitHub upload digest sha256:918610a8661f947b463c758a98a80e580f80b44292f8830c68c860c9e7e56c27. Digest is GitHub upload metadata; payload bytes were not independently re-downloaded and re-hashed in this step.

Final probe output:
- Freqtrade version: 2026.9.
- Effective config SHA-256: c253091852b704c00fa33bd6fceb69fb4d480630da1645e3e35ebea13888bb72 — exact frozen metadata match.
- FreqAI config SHA-256: a716c80fbb78b8d4bc8b436136912e93e6988a8cdf8d7d1945e8f512bcd6d852 — exact frozen metadata match.
- Native FreqAI feature columns: 20; ordered feature schema equals frozen metadata.
- Feature schema source: FreqaiDataKitchen.populate_features + ChartProFreqaiResearch.feature_engineering_standard + Freqtrade feature-name normalization.
- Runtime config loader: PASS.
- Strategy feature methods: PASS_SYNTHETIC_ONLY.
- Exchange network calls: 0.
- Strategy started: false; backtest started: false; training started: false; retraining started: false; live orders enabled: false.
- OOS certified: false.

R22.3 disposition: PASS for reproducing the frozen post-schema-validation config hashes and the ordered 20-column feature schema using the pinned Freqtrade 2026.9 code and synthetic/local fixtures. This does not prove historical model retraining reproducibility, feature causality across the full historical dataset, scaler/transform fit boundaries, or prospective OOS performance. It does not certify Phase 22.

Next safe work: R22.4 read-only feature-causality and leakage audit, covering all 20 feature definitions, timestamp/closed-candle alignment, rolling-window causality, label horizon separation, purge boundary, and fit-only transforms. Do not train/retrain, run backtests, alter metadata/model/Core, touch the prospective holdout, access T0, or enable execution.


### R22.4 — Feature causality, label leakage and evidence integrity audit (2026-11-07)

#### Feature source and candle alignment

The frozen source at commit 082edc082996425f61f48c952be41fb037564103 defines 20 model features:
- Four right-aligned rolling features: relative close and relative volume at periods 14 and 28.
- Two basic features: close percentage change and raw volume.
- Twelve positive-lag copies: the six rolling/basic features shifted by 1 and 2 candles.
- Two timestamp features: day-of-week and hour-of-day.

No future shift, centered rolling window, backfill, or future target is used in the 20 source feature methods. The target is separately named &-future_return and is close[t+4]/close[t]-1 over four M15 candles. Freqtrade 2026.9 DataKitchen explicitly uses informative_df[indicators].shift(n) for n=1..include_shifted_candles; it does not shift feature columns negatively.

Closed-candle handling is source-verified for the pinned Freqtrade 2026.9 OKX path: Exchange's default ohlcv_partial_candle is true; OKX does not override it; _process_ohlcv_df drops the currently forming or not-yet-final last candle before ohlcv_to_dataframe. process_only_new_candles alone is not the closed-candle guarantee—the exchange OHLCV partial-candle filter is. This is source-level evidence, not a live exchange runtime test.

#### Label purge and fitted preprocessing

- Phase12's four-candle target is checked against source close[t+4]/close[t]-1.
- The custom fit hook wraps DataKitchen.make_train_test_datasets and removes the chronological TRAIN suffix for which feature_open + 4*M15 is not strictly earlier than first TEST feature open. The purge occurs before fit_labels(), feature_pipeline.fit_transform(), label_pipeline.fit_transform(), and LightGBM.fit().
- Freqtrade 2026.9 BaseRegressionModel fits feature and label pipelines on TRAIN only, then transforms TEST using the fitted pipelines. DataKitchen.fit_labels() estimates label mean/std from train_labels only.
- Phase16 independently replayed all 26 historical folds from original native FIT_TRAIN/FIT_TEST X/y/weights and reconstructed source samples: 59,696 TRAIN rows, 14,825 validation rows, 52 fit archives, all 26 native X/y/weight replays, future-only intervention invariant in all 26 folds, and eligible TRAIN positive controls detected in all 26 folds. Errors were empty.
- Independent Phase16 summary commit 0978727223c528d941bf3005362c4e494df89d2d, server commit time 2026-10-31T02:09:59Z. Pre-holdout research-only release gate commit 409d446bb186a8e2ea0189df26057a9df7e839de, server commit time 2026-10-31T02:10:30Z.
- Phase14's fitted inference pipeline audit reports 5 historical witness rows, 10 feature comparisons, 5 label comparisons, and 5 accepted forecast replays with no errors.

#### Remaining full-pipeline limitation

The above evidence does not permit setting full_model_pipeline_causality_verified=true. The Phase16 code explicitly retains blocker NOT_ALL_OF_ORIGINAL_UPSTREAM_FEATURE_CONSTRUCTION_FIT_OBSERVED. Its all-26-fold refit reconstructs features through the strategy feature_matrix helper, not through FreqaiDataKitchen.populate_features on the complete original 180-day canonical dataset. R22.3 verified native DataKitchen expansion and exact 20-column order on synthetic candles only. Thus:
- Strategy source-feature causality across historical fold rows: PASS within the Phase16 evidence scope.
- Fit-only preprocessing replay and future-suffix intervention across 26 folds: PASS within the Phase16 evidence scope.
- Native DataKitchen historical 180-day feature values reconciled to every original FIT matrix: NOT VERIFIED.
- Full model pipeline causality: NOT VERIFIED.

#### Frozen model binary preservation blocker

The current GitHub copy at research_evidence/frozen-model/phase13b-20261104/original-frozen-model.joblib has Git blob SHA-1 91283dde513e24b9f87a936220a09e5f78612a49. The Phase14 blocker investigation records its byte SHA-256 as 51c847... and explicitly states it does not match the registered candidate bundle SHA-256 918dc4737ee432df8f7f9d2c3e561ac3983aaf56d8791a731a55624ab836b81f. Do not load this copy.

A separate original evidence archive is already committed before holdout:
- Archive upload commit 2ec6890f20931cb859c3eb48309842002fae6459, server time 2026-10-30T23:47:56Z, Git blob SHA-1 17ec47fcbab047a540b1b1d2faad6a73182b5ab5.
- Independent Phase14 binary attestation, included in pre-holdout release-gate commit 409d446..., records archive SHA-256 b64f39bd70c27c8d6abed1795ee06504c108eed42ebdab98ce375a6449b5b035 and states the archive contains the original candidate at artifacts/phase3/native/phase13b-unsealed-model-candidate.joblib with SHA-256 918dc4737ee432df8f7f9d2c3e561ac3983aaf56d8791a731a55624ab836b81f.
- This attestation is strong historical provenance, but the archive and embedded candidate bytes have not yet been independently re-hashed by the current R22 GitHub Actions workflow. No restoration or overwrite is authorized by this audit.

#### OOS gate compatibility

The Phase16 pre-holdout approval is research-only and explicitly does not certify OOS. The current Phase22 verify_oos_eligibility implementation also expects a separately sealed OOS protocol and attestation fields historical_protocol_sha256 and oos_protocol_sha256. The registered pre-holdout-attestation.json at commit f9591bcda1b11f15a549f397aa211259346ed3f9 does not contain those fields; the tracked phase13b-oos-protocol.json remains PRE_REGISTERED_PROTOCOL_CANDIDATE_NOT_SEALED. Therefore the Phase22 OOS eligibility verifier is NOT VERIFIED / currently incompatible with the registered attestation schema. Do not use it to authorize a holdout run until the schema and external commit proofs are reconciled.

R22.4 disposition:
- Source feature definitions and positive-lag semantics: PASS by source audit.
- Four-candle target and chronological purge contract: PASS within Phase12/Phase16 evidence.
- All-26-fold fitted preprocessing replay and future-only interventions: PASS within the SHA-bound Phase16 report scope.
- Pinned Freqtrade 2026.9 OKX incomplete-candle filter: SOURCE-VERIFIED.
- Native DataKitchen real 180-day feature-value reconciliation: NOT VERIFIED.
- Full model pipeline causality: NOT VERIFIED.
- Current repo joblib copy: BLOCKED / digest mismatch.
- Original archive provenance: PRE-HOLDOUT ATTESTED; independent current-workflow re-hash pending.
- Phase22 OOS eligibility gate: NOT VERIFIED / attestation schema mismatch.
- Independent prospective OOS: IN PROGRESS / NOT CERTIFIED.

Next safe step R22.5: use a disposable GitHub Actions job to hash the pre-holdout Phase14 archive and stream-hash its embedded candidate, metadata and protocol without unpickling. Compare the embedded candidate to the registered SHA and separately report the current repo copy mismatch. Do not restore/overwrite the model file without explicit approval. Do not read holdout candles, retrain, backtest, tune, access T0, or enable execution.


### R22.5 — Phase14 original archive and frozen bundle byte verification (2026-11-07)

A disposable GitHub Actions workflow was added to hash the pre-holdout Phase14 ZIP and stream-hash its embedded files. The workflow uses only Python standard-library ZIP/crypto operations; it does not extract archive members or unpickle/load the joblib model.

TDD and workflow evidence:
- RED test-only commit 31f0144f4b368f3054d2ffc2f194b70636193483; R22.5 run 42321362140, job 128246431636: expected import failure because the archive-audit module was not implemented yet.
- Initial implementation run 42321424726, job 128246639237: 5/5 unit tests PASS; archive probe correctly stopped because the pre-registered protocol is a separate sealed repository file, not a member attested as contained in the ZIP. The verifier was corrected to hash the protocol file separately rather than assume it is inside the archive.
- Final source SHA c81f886a8012274dbd1abb6e93f36c1a2eb6d8fe.
- Final direct push run 42321514294, job 128246931676: SUCCESS; 6/6 unit tests PASS; archive/member/protocol verification PASS; artifact upload PASS.
- Artifact ID 13552773238; name r22-5-phase14-archive-integrity-c81f886a8012274dbd1abb6e93f36c1a2eb6d8fe; GitHub upload digest sha256:61ed1fd22fac1f4789f1890c88355e3bee2227b1c63f156b99b379f005038031.

Exact byte-level results from the workflow report:
- Phase14 archive SHA-256 b64f39bd70c27c8d6abed1795ee06504c108eed42ebdab98ce375a6449b5b035 — PASS.
- Phase14 archive Git blob SHA-1 17ec47fcbab047a540b1b1d2faad6a73182b5ab5 — PASS.
- Embedded original model member artifacts/phase3/native/phase13b-unsealed-model-candidate.joblib SHA-256 918dc4737ee432df8f7f9d2c3e561ac3983aaf56d8791a731a55624ab836b81f — PASS.
- Embedded candidate metadata SHA-256 07e9c1b65df7a477de8ee14c51d47325932e6bf9a0732f3ea64e3118abcac3e5 — PASS.
- Separate sealed protocol file research_evidence/frozen-model/phase13b-20261104/phase13b-oos-protocol.json SHA-256 b10d63c952a40fa70a3d4dfed2d952d676a888a0f72832734d3ff8d8c14c5b6e — PASS.
- Current repo copy original-frozen-model.joblib raw SHA-256 is also 918dc4737ee432df8f7f9d2c3e561ac3983aaf56d8791a731a55624ab836b81f and its Git blob SHA-1 is 91283dde513e24b9f87a936220a09e5f78612a49. It matches the registered bundle bytes.
- archive_integrity_verified=true; current_repo_bundle_matches_registered=true; restoration_required=false; archive_extracted=false; unpickle_performed=false.

Important correction: the older phase14-blocker-investigation.json records the same current Git blob SHA-1 91283dde... but reports raw SHA-256 51c8474d... and RESTORE_REQUIRED. The R22.5 disposable GitHub Actions run directly hashes the exact checked-out file bytes and proves the raw SHA-256 is 918dc473... matching the registered model. The old 51c8474d... value is therefore superseded and must not be used to classify the current repository copy as corrupt. The historical investigation JSON is left unchanged; this section records the later exact-byte correction.

R22.5 disposition: original Phase14 archive, embedded candidate, metadata, separate protocol, and current repo model copy byte identities PASS within the verified SHA scope. No model restoration or modification was needed; no joblib loading/unpickling occurred.

Remaining blockers unchanged: full_model_pipeline_causality_verified=false; real 180-day FreqaiDataKitchen feature-value reconciliation NOT VERIFIED; Phase22 OOS eligibility attestation schema mismatch NOT VERIFIED; prospective OOS IN PROGRESS / NOT CERTIFIED; funding/mark/liquidation and Kotlin parity pending.

Next safe work R22.6: use the verified pre-holdout archive's historical canonical M15 file and pinned Freqtrade 2026.9 DataKitchen to compare all 20 native expanded feature values against the Phase13/15 strategy reconstruction over the complete historical 180-day dataset. No model loading, training, backtest, exchange access, holdout reads, T0 access, or live execution.
