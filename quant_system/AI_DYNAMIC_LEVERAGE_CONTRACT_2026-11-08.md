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
- Exact-source push run: [42457686964](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42457686964), source/head/checked-out SHA `ccc182378772a25f2afb475b4070d281222d7f7f`, conclusion SUCCESS; job `128660101285` SUCCESS. Logs confirm AI leverage 14/14, coordinator 11/11, dual-ledger 23/23, legacy Phase 2 20/20, Phase 3 11/11, and PaperLedger 18/18 — **97/97 test invocations PASS**.
- Artifact: ID `13607992537`, name `t2-ai-dynamic-leverage-ccc182378772a25f2afb475b4070d281222d7f7f`, GitHub digest `sha256:3d2c14ea53cdf1e12633c6fbe1f2f540b052c2a6ae16bcfecae8e915f6112cce`. The artifact ZIP was downloaded and independently hashed; computed SHA-256 matched the GitHub digest. Its contents record event=push, github_sha=checked_out_sha=`ccc182378772a25f2afb475b4070d281222d7f7f`, `AI_EXECUTION_ENABLED=false`, empty DB targets and empty exchange credentials; test log records 14/14 PASS.
- PR merge-context run: [42457691928](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42457691928), PR head SHA `ccc182378772a25f2afb475b4070d281222d7f7f`, checked-out synthetic merge SHA `443b08f5e94c584aba75d232f6e86609a43d7ef8`, conclusion SUCCESS; same six suites 97/97 PASS. This is merge-context evidence, not direct-head evidence.
- PR artifact ID `13608346507`, name `t2-ai-dynamic-leverage-443b08f5e94c584aba75d232f6e86609a43d7ef8`, GitHub digest `sha256:31b28ed5130b7523e25f853f02c691e32014fec857698a21472c1e5c32bf9004`. Exact-head evidence is the push artifact above.
- Earlier exact-source run [42457596650](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42457596650) at SHA `6bb1ecd899e9857dfef80635c4d53a745f7c2662` also passed 97/97 before artifact-evidence workflow hardening.

## Status

- Linear policy contract: IMPLEMENTED.
- Approved bounds 1x–3x: ENFORCED.
- Confidence domain endpoints: CONFIGURATION REQUIRED / NOT APPROVED.
- Calibration acceptance metrics and sample-size thresholds: BLOCKED ON USER SPECIFICATION.
- Actual calibration artifact and OOS performance: NOT VERIFIED.
- Runtime integration and paper execution: NOT IMPLEMENTED / DISABLED.
- Live execution: DISABLED.
