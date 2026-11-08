# T2 Prediction / Candle Timestamp Semantics Audit — 2026-11-08

## Scope
Read-only inspection of the active T2 branch at HEAD `a34c04f817316c5145616e41e2d6417ee3cb936d`. No source code, T0/T1 runtime, database, feeder, exchange, paper runtime or live runtime was changed or accessed.

## Evidence inspected
- `quant_system/t0_freqtrade_adapter.py` (blob `4df40d0e364a185dad98b774c1664a1fa119685f`).
- `quant_system/ai_provenance_validator.py` (blob `2cbf1d13ded45a1216b2d2bb4582c0fe2cc2ecf4`).
- `quant_system/test_t0_freqtrade_adapter.py` (blob `02b24af0e597f8be4863fb4c9323799075d86f6c`).
- `market_data/api.py` (blob `9d0c8ccb0a5b3b7cad26ebb217d1cbd15701c85f`).
- `quant_system/F0_F1_T0_FREQTRADE_READ_ONLY_AUDIT_2026-11-07.md` (blob `88772c5c28f434a8afebef0133fe102693ca106a`).
- Active T2 handoff and provenance test fixtures.

## Timestamp facts established by existing code
1. T0 snapshots use timeframe intervals: M15 = 900,000 ms; H1 = 3,600,000 ms.
2. Candle `openTimeMs` is the interval start.
3. T0 adapter validates `closeTimeMs == openTimeMs + interval`. This is an exclusive interval-end boundary, not an exchange-style inclusive last millisecond.
4. Adjacent rows are contiguous: the next candle's `openTimeMs` equals the previous candle's `closeTimeMs`.
5. `availableAtMs` must be an integer and must be greater than or equal to `closeTimeMs`.
6. The candle must have `isClosed=true`, `availabilityKind=FIRST_OBSERVED`, and `quality=VALIDATED`.
7. If snapshot `asOfMs` is present, each candle's `availableAtMs` must be no later than that cutoff.
8. T0 API exposes optional `asOfMs`; the offline adapter validates the saved snapshot and does not query runtime state.

## Current T2 validation gap
- Prediction rows contain `prediction_timestamp_ms` and `outcome_available_at_ms`.
- Current validator checks prediction timestamp against the signed OOS interval and both M15/H1 *coverage envelopes*. It does not check per-candle `availableAtMs` relative to the prediction timestamp.
- It does not establish which final M15/H1 candle (or feature window) was actually consumed for each prediction.
- Repository search did not establish a producer-side contract defining whether `prediction_timestamp_ms` means candle open, candle close, feature cutoff, decision time, or model emission time.
- The signed bundle contains complete timeframe snapshots, potentially including candles later than a given prediction. Snapshot membership alone is not evidence that future rows were excluded from model features.

## Safe conclusion
**Timestamp semantics are PARTIALLY ESTABLISHED, not sufficient for candle-level no-lookahead proof.**
The T0 candle interval and availability conventions are explicit. The prediction timestamp's meaning and the per-row feature cutoff/consumed-candle identity are not.

Do not implement a guessed rule such as `prediction_timestamp_ms == candle closeTimeMs`, or merely require that it fall inside both coverage envelopes. Do not infer a label horizon or outcome price basis.

## Proposed fail-closed row contract (requires user confirmation)
- Define `prediction_timestamp_ms` as the UTC millisecond instant when the model decision/prediction is emitted (decision time), not a candle timestamp.
- Add explicit per-timeframe consumed-candle cutoffs to every prediction row, for M15 and H1. Each cutoff should identify the last candle actually admitted to features, preferably by both `openTimeMs` and `closeTimeMs` (and/or the exact source snapshot fingerprint).
- Validator should require the referenced candle to exist in the matching snapshot, be closed and validated, and have `availableAtMs <= prediction_timestamp_ms`.
- Validator should reject any referenced candle outside the signed OOS window policy, missing candle, duplicate/ambiguous reference, wrong timeframe, or candle available after decision time.
- This establishes temporal availability of declared feature inputs only. It still does not prove model code consumed only those inputs, absence of hidden leakage, or outcome-label correctness; those need separate reproducible training/inference evidence.

## Status
- Timestamp convention in T0 snapshot: **PASS — established from code**.
- Meaning of `prediction_timestamp_ms`: **NOT DEFINED**.
- Per-row consumed M15/H1 feature cutoff: **NOT IMPLEMENTED / NOT DEFINED**.
- Candle-level no-lookahead verification: **NOT VERIFIED**.
- Tests/workflows: **NOT RUN** (read-only audit).
- No T0/T1 runtime/DB/Feeder/exchange access; `AI_EXECUTION_ENABLED=false`; no paper/live runtime; no attestation or leverage authorization.
- PR #95 remains OPEN / DRAFT / NOT MERGED.
