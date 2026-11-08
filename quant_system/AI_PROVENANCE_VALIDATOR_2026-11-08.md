# AI OOS Provenance Validator — 2026-11-08

## Purpose

`quant_system/ai_provenance_validator.py` verifies a signed evidence envelope for a frozen AI model and its OOS evaluation artifacts. It is an offline verifier only. It does not create or issue a calibration attestation and cannot authorize AI leverage, ENTRY/DCA, paper execution or live execution.

## Signed envelope contract

The envelope contains exactly:
- `manifest`: canonical JSON object.
- `signature`: base64-encoded Ed25519 signature over canonical UTF-8 JSON of the manifest (sorted keys, compact separators, no NaN).

The manifest has a strict schema:
- Schema version, key ID, model/strategy/dataset versions.
- Issue and expiry timestamps in Unix milliseconds.
- Temporal split declaration: `train_end_ms < oos_start_ms <= oos_end_ms`.
- Exactly five signed artifact descriptors: `model`, `dataset`, `predictions`, `split_protocol`, and `calibration_report`.
- Every artifact descriptor binds a lowercase SHA-256 digest and positive byte size.

The caller supplies the actual artifact bytes and a trusted-key map of `key_id -> raw 32-byte Ed25519 public key`. The verifier checks:
- Trusted key lookup and Ed25519 signature.
- Exact envelope/manifest/schema keys; duplicate JSON keys are rejected.
- Manifest issue/expiry time and the declared chronological split.
- Exact artifact role set, byte size and SHA-256 for every artifact.
- Any missing, extra, malformed, stale, altered or untrusted evidence fails closed.

## Trust and security boundary

The verifier embeds no private or public trust root. The caller must load trusted public keys from an independently protected trust store. The key map must not be supplied by the same untrusted bundle being verified. No production key has been provisioned; no signer identity, key rotation, revocation or compromise-recovery process has been approved.

A valid Ed25519 signature proves that the holder of the corresponding private key signed the manifest bytes. It does not, by itself, prove that the signer is an independent data custodian or that the signed claims are true.

## Explicit limitations

This first validator slice does **not**:
- Inspect dataset rows or independently recompute their timestamp ranges; temporal non-overlap is checked against the signed manifest declaration only.
- Prove no feature leakage, label leakage, hyperparameter-selection leakage, survivorship bias, or leakage in upstream training/prediction code.
- Recompute model training from source data or establish that the model artifact is the model that generated every prediction.
- Parse the calibration report and reconcile its embedded evaluator report digest/metrics with the signed prediction/outcome artifacts.
- Establish signer independence, secure key custody, key revocation or key rotation.
- Certify that the OOS sample is representative or that the model is statistically useful.

Therefore a passing result is **signed manifest + artifact-byte integrity + declared temporal-order verification only**. It is not proof of a leakage-free OOS experiment and is not sufficient to issue a calibration attestation.

## TDD and CI evidence

- RED test-first run: [42458980940](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42458980940), PR merge checkout `01e686ba90c379f7664372dcc6f78cdd3ac08e07`; 1 import error because the validator module did not yet exist.
- Intermediate RED runs exposed missing verified-artifact initialization and an artifact hash test that also changed byte length; the test was corrected to isolate hash mismatch from size mismatch.
- Final PR-context run: [42459130878](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42459130878), PR head `784589cb71babe6992ee2baf4ce74baba8858ffd`, synthetic merge checkout `595896d2e3c27d6eda617bf8714d7466d87204f4`, job `128664429232` SUCCESS.
- Provenance validator: 14/14 PASS.
- Calibration evaluator: 16/16 PASS.
- Dynamic leverage: 14/14 PASS.
- Coordinator: 11/11 PASS.
- Dual ledger: 23/23 PASS.
- Legacy Phase 2: 20/20 PASS.
- Legacy Phase 3: 11/11 PASS.
- PaperLedger: 18/18 PASS.
- Total: **127/127 test invocations PASS**; py_compile PASS.
- Artifact ID `13608698028`, name `t2-ai-intelligence-contracts-595896d2e3c27d6eda617bf8714d7466d87204f4`, GitHub digest `sha256:a796c062ecaf39d562aae05deece36925ed74c49b9b9b85ad2929830516dffec`.
- Artifact contains source provenance, compile log, provenance validator test log, calibration evaluator test log and dynamic leverage test log.
- CI preflight: `AI_EXECUTION_ENABLED=false`; database targets and exchange credentials EMPTY.
- This is PR merge-context evidence, not direct-push exact-head evidence.

## Current status

- Signed envelope verifier implementation: IMPLEMENTED.
- Synthetic contract tests and PR merge-context CI: PASS.
- Real model/dataset/OOS/prediction/report artifacts: NOT PROVIDED / NOT VERIFIED.
- Production trust root and independent signer: NOT CONFIGURED.
- True temporal split/leakage proof: NOT VERIFIED.
- Calibration attestation: NOT ISSUED.
- Leverage authorization or runtime integration: NOT IMPLEMENTED.
- AI execution remains disabled; no DB, T0/T1, exchange or execution runtime was touched.


## Row-level OOS prediction verification — 2026-11-08

### Added contract

The signed `predictions` artifact is now required to be UTF-8 JSONL. Each row must contain exactly:
- `prediction_timestamp_ms`
- `outcome_available_at_ms`
- `outcome` (integer 0 or 1)
- `confidence` (finite decimal in [0, 1])
- `side` (LONG or SHORT)
- `regime` (non-empty string)
- `model_version`
- `dataset_version`

The verifier rejects malformed/duplicate-key JSON rows, blank rows, empty files, prediction timestamps outside the signed OOS interval, outcome resolution at/before prediction time or after OOS end, and row-level model/dataset version mismatches. A malformed signed split is rejected before row-level timestamp access; it cannot raise a KeyError.

This is a row-level chronology and lineage consistency check for prediction records. It does not independently prove the timestamps or outcomes against the original market dataset.

### TDD evidence

- New row-level test contracts were added before the final implementation.
- RED run [42459595402](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42459595402), source `b2a4ae69dbe1334f2ce36869e6c5c033253ac490`: 23 tests, failed as expected with `KeyError: 'oos_start_ms'` for a malformed signed split.
- Final implementation commit/source SHA: `07e8212e4723cc913e4d0a3b196212f134a8a23e`.
- Exact-source push run [42459618363](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42459618363), job `128665883617`, SUCCESS. Checked-out SHA equals source SHA.
- PR-context run [42459622326](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42459622326), job `128665895716`, SUCCESS; synthetic merge checkout SHA `1a04c7abf0464de74c534d3f4de3690f0606e1b7`.
- Exact suite counts: provenance validator 23/23; calibration evaluator 16/16; dynamic leverage 14/14; coordinator 11/11; dual ledger 23/23; Phase 2 20/20; Phase 3 11/11; PaperLedger 18/18. **136/136 test invocations PASS**; py_compile PASS.
- Push artifact ID `13609465168`, name `t2-ai-intelligence-contracts-07e8212e4723cc913e4d0a3b196212f134a8a23e`, GitHub digest `sha256:e548da7a689ea9f0ee877d92f6baef6ffd849f08aeb4f453d2b4db1e37108b87`.
- PR artifact ID `13608987960`, name `t2-ai-intelligence-contracts-1a04c7abf0464de74c534d3f4de3690f0606e1b7`, GitHub digest `sha256:1ced67485be007d95bdbdd2503e5f8303b707dd5d17604e21651d1ca562104b1`.
- Both CI runs confirm `AI_EXECUTION_ENABLED=false`, database targets EMPTY, exchange credentials EMPTY.

### Remaining boundaries

- The signed `dataset` artifact is still opaque bytes; its individual candle rows and timestamps are not parsed or reconciled with prediction rows.
- Prediction outcome labels are not independently recomputed from market prices.
- The validator does not prove no feature/label leakage, no hyperparameter-selection leakage, or that the signed model actually generated the predictions.
- Calibration report contents and evaluator `input_sha256`/`report_sha256` are not yet semantically reconciled to the prediction rows.
- No real BTCUSDT model, dataset, predictions, split protocol or calibration report were supplied.
- No production trust root or independent signer is provisioned.
- Calibration attestation remains NOT ISSUED; AI leverage authorization and runtime integration remain NOT IMPLEMENTED.


## Calibration report semantic reconciliation — 2026-11-08

### Implemented contract

The signed `calibration_report` artifact is now parsed as strict UTF-8 JSON with duplicate-key and non-finite-number rejection. The report must contain the exact schema and explicitly declare the approved gate policy:
- `max_ece = 0.05`
- `min_total_samples = 1000`
- `min_group_samples = 200`
- `ece_bins` explicitly supplied in [1, 100]
- non-empty, unique `required_regimes`

The validator reconstructs calibration observations from the exact signed prediction JSONL rows, runs the existing `CalibrationEvaluator`, and compares the complete report: accepted state, reasons, sample/group counts, all metrics, `input_sha256`, `report_sha256`, policy, and the false trade/attestation flags. Any mismatch rejects the provenance verification. No calibration attestation is issued.

### TDD and exact-source CI

- RED test run [42459991105](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42459991105), source `ae46e708d05a91e11c1a0d7b0e8476ce60c1c901`: four new semantic mismatch contracts failed as expected before implementation.
- GREEN implementation source SHA: `b2623527add57002e8b32123c67f4484c88d0efa`.
- Exact-source push run [42460071397](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42460071397), job `128667260783`, SUCCESS; `github_sha` and `checked_out_sha` both equal the source SHA.
- Suite counts: provenance validator 28/28; calibration evaluator 16/16; dynamic leverage 14/14; coordinator 11/11; dual ledger 23/23; Phase 2 20/20; Phase 3 11/11; PaperLedger 18/18. **141/141 test invocations PASS**; py_compile PASS.
- Artifact ID `13609103523`, name `t2-ai-intelligence-contracts-b2623527add57002e8b32123c67f4484c88d0efa`, digest `sha256:483a1d4952d7f578c7e4063d05d6efadfa4e1190937985fccc37a47cfe059062`.
- CI preflight confirms `AI_EXECUTION_ENABLED=false`, DB targets EMPTY, exchange credentials EMPTY.

### Remaining boundaries

- This proves internal consistency between the signed prediction JSONL and signed calibration report, not that predictions/outcomes are true or that the dataset is authentic.
- Dataset rows and candle timestamps remain opaque; prediction outcomes are not recomputed from OHLCV.
- No proof of feature/label leakage absence, training lineage, or model-to-prediction execution identity.
- No real BTCUSDT OOS artifacts or production trust root/independent signer were supplied.
- Calibration attestation NOT ISSUED; leverage authorization NOT ISSUED; runtime integration NOT IMPLEMENTED.


## Signed T0 M15+H1 dataset bundle verification — 2026-11-08

### Bundle contract

The signed `dataset` artifact is now a strict UTF-8 JSON bundle with exactly these top-level fields:

- `schema_version=1`
- `format=T0_M15_H1_DATASET_BUNDLE_V1`
- `source=T0_CANONICAL_BINANCE_USDT_PERPETUAL`
- `exchange=binance`, `marketType=USDT_PERPETUAL`, `symbol=BTCUSDT`
- `snapshots`: exactly `15m` and `1h`, each embedding its existing T0 API snapshot payload unchanged
- `datasetVersion`: aggregate SHA-256 identifier

Each embedded snapshot is passed through the existing `quant_system.t0_freqtrade_adapter._validate_snapshot` contract. This reuses the established T0 checks for its per-timeframe identity, snapshot fingerprint, exact complete coverage, contiguous candle timestamps, closed/validated status, availability chronology, OHLC bounds and decimal-string values. The validator does not connect to T0 or an exchange.

The aggregate dataset fingerprint is SHA-256 over canonical compact sorted-key UTF-8 JSON containing the fixed bundle identity and the `datasetVersion` values for both snapshots. The signed manifest's `dataset_version` must equal this aggregate identifier.

### Prediction-to-dataset coverage checks

- Every prediction timestamp must fall inside the inclusive coverage envelope `[startMs, endMs]` of both the M15 and H1 snapshots.
- Every `outcome_available_at_ms` must fall inside the M15 snapshot coverage envelope.
- Missing timeframe, wrong snapshot identity/timeframe, malformed/duplicate-key JSON, invalid embedded snapshot, aggregate fingerprint mismatch, and manifest/bundle version mismatch fail closed.
- Coverage envelope checks establish only that the event timestamp lies within the declared snapshot window. They do not assert the exact candle-selection/close-time convention or prove that the feature set was available to the model at prediction time.
- Outcome labels are not recomputed from OHLCV. Price basis, label horizon and exact candle-close semantics remain unspecified and out of scope.

### TDD and CI evidence

- RED after fixture migration: [42460744680](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42460744680), source `dc0dc6674d36a353da4f8a5b316da1a971f5c452`; exactly five new bundle/coverage tests failed before validator implementation. The older first RED run [42460661166](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42460661166) also contained a stale legacy fixture and is retained as intermediate evidence, not the final RED baseline.
- Validator implementation commit/source: `9d738f82e0ee9ce6e255581d077561eaf51bf67c`.
- Additional manifest binding and duplicate-key tests: `a0abc63017cb3a8855018a47d3410e04d55b770b`; fixture correction: `9103c0c15b63bdace4b17301a7d5b4540634e28a`.
- Exact-source push CI [42460912700](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42460912700), job `128669809731`, SUCCESS; `github_sha` and `checked_out_sha` both equal `9103c0c15b63bdace4b17301a7d5b4540634e28a`.
- PR-context CI [42460914804](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42460914804), job `128669816763`, SUCCESS; synthetic merge checkout `122fe436fc8f91dc93c6b5216d72100120bcfcd9`.
- Test counts: provenance validator 35/35; calibration evaluator 16/16; dynamic leverage 14/14; coordinator 11/11; dual ledger 23/23; Phase 2 20/20; Phase 3 11/11; PaperLedger 18/18. **148/148 test invocations PASS**; py_compile PASS.
- Push artifact ID `13609334289`, digest `sha256:2b4a1fe0661b6d2b5e3d346099132a15225df15467aba68f1be557ccfcd71d68`.
- PR artifact ID `13609383998`, digest `sha256:45bb8bc1263550f93091db26b8310433581ff34ce29d7d718cfc5332e113c697`.
- Both runs confirm `AI_EXECUTION_ENABLED=false`, database targets EMPTY and exchange credentials EMPTY.

### Status and boundaries

- Signed M15+H1 bundle schema, both embedded T0 snapshot checks, aggregate fingerprint, manifest binding and prediction/outcome coverage-envelope checks: PASS on synthetic fixtures.
- Real BTCUSDT OOS dataset and predictions: NOT PROVIDED / NOT VERIFIED.
- Dataset authenticity beyond supplied signer trust and artifact hashes: NOT VERIFIED.
- Exact feature-time/candle-close alignment and label semantics: NOT VERIFIED.
- Outcome recomputation from OHLCV and feature/label leakage analysis: NOT IMPLEMENTED.
- Production trust root and independent signer lifecycle: NOT CONFIGURED.
- Calibration attestation: NOT ISSUED; AI leverage authorization: NOT ISSUED; runtime integration: NOT IMPLEMENTED.
- No T0/T1 DB, feeder, exchange, paper or live execution touched.
- `AI_EXECUTION_ENABLED=false`; PR #95 remains OPEN / DRAFT / NOT MERGED.
