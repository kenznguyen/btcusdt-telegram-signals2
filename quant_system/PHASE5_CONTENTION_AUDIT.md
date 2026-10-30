# Phase 5 — independent CORE/AI source contention report

This is a **paper-only attribution audit**, built on Phase 4's independently
checksum-verified 180-day CORE_ONLY, AI_ONLY and DUAL event files. It does
not alter StrategyRules, FreqAI predictions, Shared Risk admission, max
positions, Smart DCA, stops or any Android release. It does not enable native
Freqtrade orders, live trading, or 360-day research.

## Observed on 2026-10-30 uploaded Codemagic artifacts

- CORE_ONLY entered 24 positions.
- DUAL entered 76 positions: 73 AI and 3 CORE.
- 21 of those 24 CORE_ONLY entry decision timestamps were **not**
  selected in DUAL, because DUAL already held an AI paper position.
- DUAL `source_conflicts=0` does **not** describe this same-account
  occupancy; it describes same-timestamp opposing entry arbitration only.
- DUAL's similar performance to AI_ONLY is therefore expected from the
  one-shared-position policy, not proof that independent AI improved CORE.

These are comparisons of **observed CORE_ONLY entries**, not every raw CORE
indicator signal. Because the separate accounts have different position
paths, the counts are not a causal performance counterfactual.

## How to run

Select Codemagic branch `feature/dual-strategy-phase5-contention-audit-20261030`.
Run `dual-strategy-phase3-unit` (new synthetic unit tests), then the manual
`dual-strategy-phase3-native-research` with `PHASE3_DAYS=180`,
`PHASE3_DETAIL_MINUTES=5`, `PHASE3_DOWNLOAD_DAYS=220`.

The manual workflow now verifies Phase 4 artifacts and checks their SHA
**again** before the source-contention audit. It saves
`artifacts/phase3/paper/paper-180-source-contention.json` and log.

From an already collected 180-day artifact directory:

```bash
python3 -m quant_system.paper_contention_audit \
  --paper-dir artifacts/phase3/paper \
  --out artifacts/phase3/paper/paper-180-source-contention.json
```

A successful result includes `core_entries_blocked_by_ai_position` and
`missed_core_only_entries` with each candle timestamp and the occupying
AI trade ID. Missing or modified Phase 4 evidence fails closed.

The existing max-one-position rule remains intact; allowing two simultaneously
open strategy positions would require new portfolio-wide exposure, leverage,
liquidation, restart and collateral tests. Do **not** silently open a second
position or close an AI position merely to improve the CORE_ONLY result.

Always retain `ready_for_360=false`, `full_core_parity_certified=false`,
`live_orders_enabled=false`. Walk-forward OOS, Kotlin/Freqtrade trade parity,
funding, mark and liquidation remain independent blockers.
