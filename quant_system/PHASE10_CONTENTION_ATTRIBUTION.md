# Phase 10 — kiểm toán CORE/AI position contention (3-slot paper, 180 ngày)

Phase 10 is a READ-ONLY source-attribution gate, not a trading policy change.
It continues Phase 9's virtual BTCUSDT shared portfolio: 3 concurrent slots,
10% current equity initial margin per entry, same-direction positions only,
AI-origin cap 2 in DUAL, one Smart DCA per trade, max 60% equity collateral.

## What it proves

- All SHA-256 checksums carried by the successful Phase 9 independent
  portfolio audit still match the 180-day paper outputs.
- Events build valid per-trade lifecycles (ENTRY/DCA/exit), ordered fills,
  <=3 concurrent positions, <=2 DUAL AI positions and no simultaneous
  opposite-side virtual positions.
- CORE_ONLY filled-entry (decision candle, side) is compared with CORE-origin
  DUAL filled entry. Entries present in CORE_ONLY but missing in DUAL are
  cross-referenced to the actual DUAL filled-position intervals:
  `full_position_slots`, `opposite_side_ai_occupied`,
  `opposite_side_core_occupied`, `same_side_ai_occupied_with_capacity`,
  `same_side_core_occupied_with_capacity`, or
  `unexplained_without_active_obstruction`.
- Each missing CORE_ONLY entry gets a row with decision timestamp, direction,
  occupying position count, occupying AI count and trade IDs.
- Missing/changed upstream evidence and lifecycle violations cause a
  nonzero exit; no test failure becomes approval.

## Evidence observed from uploaded Phase 9 180d artifacts (not a new run)

Canonical source dataset SHA:
`sha256:75483816eef2b2053f12e0795e386746803d5fd379a989de351f40c35c747849`

- CORE_ONLY filled entries: 29
- CORE entries in DUAL at matching decision timestamps: 15
- CORE_ONLY entries absent in DUAL: 14
- 13/14: DUAL holds an AI-origin *opposite-side* position at that timestamp
- 1/14: all 3 DUAL slots occupied (2 AI + 1 CORE)
- 0/14: no position-level explanation

Interpretation must be STRICTLY observational. These are **filled CORE_ONLY
entry opportunities**, not every raw RSI/ADX signal. Distinct CORE_ONLY and
DUAL accounts have different equity and active trade histories. A nearby
AI position proves occupancy at that timestamp, NOT that counterfactually
closing AI would have admitted/filled the CORE order. No new priority,
forced hedge/reverse, cancel, or AI suspension is authorized.

## Codemagic

Branch: `feature/dual-strategy-phase10-contention-attribution-20261031`

1. Run `dual-strategy-phase3-unit` for pure Python tests (the optional
   market fixture test skips when no 180d artifacts are present).
2. Manually run `dual-strategy-phase3-native-research`, setting:
   - `PHASE3_DAYS=180`
   - `PHASE3_DETAIL_MINUTES=5`
   - `PHASE3_DOWNLOAD_DAYS=220`
3. After Phase 4 through Phase 9 audits, Codemagic writes:
   - `artifacts/phase3/paper/portfolio-180-source-contention.json`
   - `artifacts/phase3/paper/portfolio-180-core-opportunity-attribution.csv`
   - `artifacts/phase3/paper/portfolio-180-source-contention.log`

To audit an already downloaded **SHA-matching** Phase 9 artifact folder:

```bash
python3 -m quant_system.phase10_contention \
  --paper-dir artifacts/phase3/paper \
  --out artifacts/phase3/paper/portfolio-180-source-contention.json \
  --details artifacts/phase3/paper/portfolio-180-core-opportunity-attribution.csv
```

## Unchanged safety rules and next research

Do not modify RSI + ADX + Smart DCA, TP/Soft/Emergency SL, Android APK,
Codemagic keystore, release configuration or production ReservationLedger.
All native exchange orders remain disabled.

Next independent investigations: actual FreqAI train/validation row indices,
label-horizon purge/leakage, model OOS; complete funding/mark/liquidation;
Kotlin-vs-native Freqtrade trade-bearing parity; exchange same-pair
multi-position/one-way/hedge behavior. No 360d or live trading until signed
independent approval. All certification flags remain false.
