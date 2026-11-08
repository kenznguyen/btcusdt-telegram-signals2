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
