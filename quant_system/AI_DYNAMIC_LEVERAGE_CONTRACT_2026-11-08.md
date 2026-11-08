# AI Dynamic Leverage Contract — 2026-11-08

## Approved policy

- AI leverage bounds: **min=1x, max=3x**.
- Confidence-to-leverage mapping: **linear**.
- Strategy Core leverage is not an input or fallback for AI.
- A confidence-domain floor and ceiling must be supplied explicitly by a future AI calibration/configuration package. This contract intentionally does not hard-code the previously discussed 0.60/0.90 proposal.
- Any invalid configuration, confidence, calibration attestation, identity, provenance, or validity window rejects the leverage decision.

## Contract

Implementation: `quant_system/ai_dynamic_leverage.py`.

The policy accepts:
- Explicit fixed 1x and 3x bounds.
- Explicit confidence floor/ceiling in [0, 1], with floor < ceiling.
- Finite confidence inside that configured domain.
- Calibration attestation with matching model version, strategy version and dataset version.
- SHA-256-shaped report and protocol fingerprints.
- Explicit `out_of_sample=true`, `leakage_free=true`, and `acceptance_passed=true`.
- A validation timestamp not in the future and a non-expired attestation.

Linear mapping:

`L = 1 + 2 × (confidence - confidence_floor) / (confidence_ceiling - confidence_floor)`

The result is checked against [1x, 3x]. Decimal arithmetic is used; no implicit rounding or Core leverage fallback is applied.

## Independent validation boundary

The unit contract verifies the policy's behavior and fail-closed input handling. It does **not** itself:
- Compute calibration metrics (ECE, Brier score, reliability curves, etc.).
- Establish the acceptance thresholds or minimum out-of-sample sample size.
- Prove that a supplied report/protocol hash matches downloaded artifact bytes.
- Establish calibration quality separately by LONG/SHORT or market regime.
- Verify the truth of the attestation booleans or cryptographically authenticate the attestation.
- Select confidence-domain endpoints from empirical data.

Those remain independent calibration evidence requirements. Until the user approves numeric calibration acceptance criteria and the calibration evaluator produces matching evidence, no real calibration can be marked accepted for trading.

## Runtime and execution boundary

- The policy is a pure, standalone contract and is not wired into `DualStrategySignalCoordinator`, legacy `dual_strategy.py`, `paper_bridge.py`, or any execution path.
- No AI ENTRY/DCA runtime was activated.
- `AI_EXECUTION_ENABLED=false`; no exchange credentials, database targets, exchange calls, market-data sync, or live orders are used by this contract workflow.
- Leverage does not bypass the shared risk engine, 1% combined-equity margin admission, gross exposure accounting, Kill Switch, or reconciliation.
- Gross notional exposure ceiling remains undefined and blocks later paper-runtime certification.

## Tests and evidence

- RED: run [42457533430](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42457533430), source `004eaf3c0870f11692174c27669c5bd4021275b9`; the new independent suite exposed a dataset-provenance mismatch not being rejected (13 passed, 1 failed).
- Initial GREEN: run [42457536254](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42457536254), exact source `685abd9cf214566e2c653af4b04171e1c42241b5`; independent leverage suite 14/14 PASS, coordinator/ledger/legacy regressions also passed. No artifacts were produced.
- Updated fixed-bound validation: run [42457578245](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42457578245), exact source `617ceea8e9669b701dbeae36acae16666b769970`; SUCCESS. Final provenance-type hardening is later than this run and requires the newest run to complete before claiming final exact-head PASS.
- Final exact-source CI for the latest provenance-type hardening is pending at the time of this report; record its result in the next update.

## Status

- Linear policy contract: IMPLEMENTED.
- Approved bounds 1x–3x: ENFORCED.
- Confidence domain endpoints: CONFIGURATION REQUIRED / NOT APPROVED.
- Calibration acceptance metrics and sample-size thresholds: BLOCKED ON USER SPECIFICATION.
- Actual calibration artifact and OOS performance: NOT VERIFIED.
- Runtime integration and paper execution: NOT IMPLEMENTED / DISABLED.
- Live execution: DISABLED.
