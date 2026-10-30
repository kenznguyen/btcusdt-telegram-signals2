# Phase 11 — SHA-bound same-candle CORE / AI source-conflict reconciliation

This diagnostic is read-only and **does not** modify CORE RSI/ADX/Smart
DCA, FreqAI inference or any Shared Risk admission policy.

## Why Phase 11 exists

Phase 10's latest Codemagic OKX 180-day run (source SHA
`470a2966a5364b0d14dc592338dd8611d6712d20`) returned
`contention_audit_verified=true` but observed 17 filled CORE_ONLY entries
missing in DUAL:

- 15 with active opposite-side AI positions
- 1 with all three positions occupied
- 1 with no occupied DUAL positions at the CORE signal timestamp

A separate read of the SHA-pinned original FreqAI prediction CSV showed
that the last case (2026-09-24 14:45 UTC) involved CORE SHORT vs FreqAI
accepted prediction +0.002799645731... (AI LONG) on the same closed M15
candle. This is consistent with the existing `_select` SOURCE_CONFLICT
rule, not a free-slot allocation bug. It must be verified through a
reproducible Codemagic gate before calling the discrepancy explained.

## Independent checks

`quant_system/phase11_conflict_reconciliation.py` requires:

1. Phase 10 success and unchanged SHA-256 of its detailed CSV.
2. Phase 9 independent-audit and summary SHA-256 matching Phase 10.
3. Real native FreqAI 180-day OKX research success, consistent pair/model
   identifiers, matching dataset/detail claims and SHA-256 of the exact
   forecast file.
4. A single native forecast and canonical M15 candle for each Phase 10
   previously-unexplained CORE_ONLY decision, exactly one M15 interval
   before the CORE decision timestamp.
5. A permitted `do_predict=1`, absolute predicted return at least 0.002,
   and AI direction opposite the CORE direction. The OHLCV values of
   the native prediction must match the canonical historical candle.

If any unexplained missing CORE entry lacks a genuine opposite AI forecast,
the job returns nonzero rather than inventing a cause.

New artifacts under `artifacts/phase3/paper`:

- `portfolio-180-conflict-reconciliation.json`
- `portfolio-180-conflict-reconciliation.csv`
- `portfolio-180-conflict-reconciliation.log`

A passing report states only that **source conflict explains the previously
unclassified CORE_ONLY entry(s)**. It does not claim all CORE raw signals
have been observed, nor that counterfactually allowing both sources would
improve profitability.

## Codemagic

Branch: `feature/dual-strategy-phase11-conflict-reconciliation-20261031`

1. Run `dual-strategy-phase3-unit` for Python regression tests.
2. Then manually run `dual-strategy-phase3-native-research` with:
   `PHASE3_DAYS=180`, `PHASE3_DETAIL_MINUTES=5`,
   `PHASE3_DOWNLOAD_DAYS=220`.
3. The new Phase11 step executes **after Phase10** and will fail closed on
   mismatches. Inspect all resulting CSV/JSON reports, including flags
   `oos_certified=false`, `ai_promotion_eligible=false`,
   `ready_for_360=false` and `live_orders_enabled=false`.

The work after Phase11 remains a full independent inspection of actual
FreqAI feature/label train/test indices with a four-M15-candle label purge,
chronological OOS, Kotlin/native trade-bearing parity and complete
funding/mark/liquidation. The simulator's three virtual BTCUSDT slots
are not live exchange position-mode certification.
