# AI Calibration Evaluator — 2026-11-08

## Purpose and boundary

`quant_system/ai_calibration_evaluator.py` is an offline evaluator for already-produced AI probability predictions. It does not train/retrain a model, load T0, connect to an exchange, submit paper/live orders, or authorize trading.

`CalibrationEvaluation.accepted` means only that the supplied observations passed the explicitly supplied metric gates. It never issues a `CalibrationAttestation`, never sets trade authorization, and is not sufficient by itself to allow AI leverage or ENTRY/DCA.

## Metrics

- **ECE**: equal-width expected calibration error, with an explicitly configured bin count. Each bin contributes its sample fraction multiplied by the absolute difference between mean confidence and observed positive rate.
- **Brier score**: mean squared probability error.
- **Reference Brier score**: climatology/no-skill reference calculated from the observed positive prevalence within the same evaluated sample/group. Acceptance requires the model Brier score to be strictly lower.
- Metrics are calculated overall and independently for every required LONG/SHORT × declared regime group.

## Explicit gate policy (no defaults)

The user approved the following production gate thresholds on 2026-11-08:
- `max_ece=0.05`.
- `min_total_samples=1000`.
- `min_group_samples=200` for every LONG/SHORT × regime group.
- Brier score must strictly beat the same-sample climatology/no-skill reference, overall and in every required group.

`approved_calibration_gate_policy(ece_bins=..., required_regimes=...)` supplies those fixed approved thresholds. It deliberately requires the caller to provide:
- `ece_bins` (integer 1–100).
- `required_regimes` (non-empty, unique, explicit regime taxonomy).

Neither the bin count nor regime taxonomy was part of the user's approval; neither has a default. A policy with multiple regimes may require more than 1,000 total observations because every LONG/SHORT × regime group independently needs at least 200 samples.

## Fail-closed behavior

The evaluator rejects:
- Missing/invalid policy or empty observations.
- Any observation not explicitly marked out-of-sample; it does not silently filter in-sample rows.
- Invalid labels/probabilities, unknown direction, or undeclared regime.
- Missing LONG/SHORT × required-regime groups.
- Total or per-group sample counts below the configured minimum.
- ECE above the configured maximum.
- Brier score that does not strictly beat the per-group/overall reference baseline.

The report has deterministic SHA-256 fingerprints:
- `input_sha256`: canonical ordered normalized observations.
- `report_sha256`: evaluation status, reasons, metrics, input fingerprint, and explicit gate policy.

## Important verification limitations

This evaluator does **not** prove:
- That `out_of_sample=true` is truthful or that the split is temporally/leakage-safe. The upstream split manifest and dataset provenance must be independently verified.
- That the supplied predictions came from the claimed model/version/dataset; model, strategy, dataset, split-manifest and artifact byte provenance still need a separate signed/verified evidence envelope.
- That the approved ECE/Brier/sample thresholds are statistically suitable for the actual BTCUSDT data; approval fixes policy values, not their empirical validity.
- That each market regime taxonomy is complete or stable over time.
- Confidence intervals, bootstrap uncertainty, multiple-comparison corrections, drift, or post-calibration stability.

Do not convert this evaluator's accepted result directly into a leverage attestation. A separate evidence validator must authenticate the input artifacts, frozen model identity, split protocol, temporal separation, and approved gate policy.

## Runtime boundary

- No integration into `AIDynamicLeveragePolicy`, `DualStrategySignalCoordinator`, legacy strategy, paper bridge, or execution runtime.
- `AI_EXECUTION_ENABLED=false`; no DB targets or exchange credentials in CI.
- No T0/T1 data/runtime changes.
- No paper or live order execution.

## TDD / CI evidence

- RED import contract: run [42457995143](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42457995143), source `bd7ea4c74e9f3f0cc6ba16188a01e19b108cb22f`; failed because evaluator module did not exist.
- RED behavioral test: run [42458033277](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42458033277), source `cab0d34102c7da884c820662ae5d4b5df34d1b52`; test import succeeded and exposed the first evaluator acceptance-path failure.
- RED fixture refinement runs: [42458082523](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42458082523), [42458142080](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42458142080); exposed incorrect synthetic calibration expectations (not implementation acceptance claims).
- First exact-source GREEN before artifact-log hardening: [42458190901](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42458190901), source `8e94fa36d9086b0e9340abc243a437950ee8fd0b`; all suites passed: evaluator 14/14, leverage 14/14, coordinator 11/11, dual ledger 23/23, Phase 2 20/20, Phase 3 11/11, PaperLedger 18/18 (111 total invocations).
- Final exact-source push run: [42458217777](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42458217777), source/head/checked-out SHA `56da92b86dc75ad76e0b391854c2e672268178b1`, conclusion SUCCESS; job `128661678013` SUCCESS.
- Logs confirm py_compile PASS; calibration evaluator 14/14; dynamic leverage 14/14; coordinator 11/11; dual ledger 23/23; Phase 2 20/20; Phase 3 11/11; PaperLedger 18/18 — **111/111 test invocations PASS**.
- Exact-head artifact: ID `13608870606`, name `t2-ai-intelligence-contracts-56da92b86dc75ad76e0b391854c2e672268178b1`, GitHub digest `sha256:ba6de2deb3deefdc3ab8715571a2dc167ec6b577f8d50b2c56a9ae43b16b1284`. The downloaded ZIP was independently SHA-256 hashed; result matched the GitHub digest. Its contents include the exact source provenance, compile log, and both test logs; calibration evaluator log records 14/14 PASS.
- Preflight artifact records event=push, github_sha=checked_out_sha=`56da92b86dc75ad76e0b391854c2e672268178b1`, `AI_EXECUTION_ENABLED=false`, empty database targets and empty exchange credentials.
- PR merge-context run: [42458221166](https://github.com/kenznguyen/btcusdt-telegram-signals2/actions/runs/42458221166), PR head SHA `56da92b86dc75ad76e0b391854c2e672268178b1`, synthetic merge checkout SHA `8033250cc6179eb23397f54ea603a38458f13a9b`, conclusion SUCCESS. This is merge-context evidence, not direct-head evidence.

## Current status

- Evaluator implementation: IMPLEMENTED.
- Unit tests + exact-source CI: PASS at SHA `56da92b86dc75ad76e0b391854c2e672268178b1`; 111/111 invocations PASS and artifact payload digest independently matched.
- Approved threshold policy factory: IMPLEMENTED; ECE 0.05, total OOS 1,000, each LONG/SHORT × regime group 200, strict Brier improvement.
- Bin count and regime taxonomy: CONFIGURATION REQUIRED; no defaults.
- Real OOS dataset and calibration quality: NOT VERIFIED.
- Real OOS dataset and calibration quality: NOT VERIFIED.
- OOS split and source provenance authenticity: NOT VERIFIED.
- Leverage attestation integration: NOT IMPLEMENTED.
- Runtime: DISABLED.
