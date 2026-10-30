# Phase 2 — Dual-Strategy signal admission (research/paper only)

Source branch: `feature/freqtrade-strategy-parity-20261029`. This change is
intentionally **not** built from the old repository `main` snapshot, which lacks
the newer Freqtrade/FreqAI/Android modules.

## Three requested paths

1. **CORE:** `freqtrade_parity.ChartProParityDryRun._latest_closed_market_row`
   reads a fully closed Freqtrade M15 row. `quant_system.dual_strategy.core_signal`
   delegates entry decisions to the **existing**
   `freqtrade_parity.rules.StrategyRules.long_entry/short_entry` with the
   prior *closed* H1 indicator. There is no changed RSI, ADX, TP, DCA, margin,
   leverage, or SL threshold. Existing `PaperCallbackCore` remains the DCA/exit
   research implementation. No live execution path was altered.
2. **AI:** `freqai_bridge.ChartProFreqaiResearch` continues exporting actual
   FreqAI prediction artifacts in its established format. The coordinator
   checks those artifacts using `pipeline.decision._prediction`, canonical
   dataset checksums, training cutoffs, timestamps, `doPredict == 1`, and the
   existing 0.002 predicted-return threshold. This is a directional forecast,
   **not** a confidence probability. AI can produce LONG or SHORT with no CORE
   entry (e.g. absent/unchanged H1 or RSI conditions). Invalid/missing AI does
   not silently become a fake CORE or fabricated AI forecast.
3. **Shared risk:** CORE and AI candidates join at `PaperSignalCoordinator`.
   Opposite same-candle sides => `SOURCE_CONFLICT`, **WAIT**. Matching sides
   reserve exactly one paper signal (CORE has stable provenance priority). A
   solitary valid AI or CORE candidate can reserve if and only if the common
   risk snapshot is explicitly safe. Missing/unreconciled state, stale data,
   insufficient margin, position limits, and unvalidated AI block reservations.

## Durable reservation and duplicates

`ReservationLedger` is a SQLite WAL database with transactional
`BEGIN IMMEDIATE` and unique keys per signal and per BTCUSDT candle.
A second candle cannot reserve while a prior candle remains
`RESERVED` or `BOUND`, including after crash/restart. The same candle
can never reserve twice, even after the previous entry is reconciled.

Reservation is **not** a trade. A separate paper intent must be explicitly
bound with `bind(signal_id, paper_intent_id)`. Following a crash between reserve
and bind, the row stays `RESERVED`; do **not** retry, auto-cancel or invent an
intent. After checking external paper state, a human/operator can record
`CANCELLED` with evidence, or mark a genuinely bound intent `CLOSED`.
Do not store this database in ephemeral Codemagic workspace for real operation.

The Freqtrade adapter offers the explicit
`paper_dual_strategy_decision(pair,current_time,canonical_window,
freqai_prediction,risk_snapshot,reservation_ledger)` method. It never calls
any trade executor; it requires a caller-supplied canonical Binance market
window and a durable ledger. A Freqtrade OHLCV mismatch fails closed rather
than mixing different venues' candles. The previous native
`populate_entry_trend` flags remain `0`, and `confirm_trade_entry`
remains `False`. This boundary prevents accidental native orders while
event parity, actual callbacks, Stop Loss execution and paper ledger binding
are not yet certified.

## Test scope and build

Codemagic workflow: `dual-strategy-phase2` on branch
`feature/dual-strategy-phase2-20261030`.

```bash
python3 -m unittest quant_system.test_dual_strategy_phase2 \
  freqtrade_parity.test_rules freqtrade_parity.test_context \
  freqtrade_parity.test_callbacks freqtrade_parity.test_strategy_contract -v
```

Tests cover CORE-only, AI-only LONG/SHORT, opposite conflict, same-side merge,
AI model/provenance rejection, closed-candle and H1 barriers, risk denials,
restart after reserve without binding, binding/reconciliation, cross-candle
blocking and concurrent SQLite reservations.

**Not certified:** Freqtrade native executions, actual model accuracy/OOS
quality, liquidation/funding, Android integration, independent Kotlin-Freqtrade
event traces, realistic 1m/5m fill prices, 180/360-day trading performance, or
`full_core_parity_certified`. These gates remain false until independent
runtime evidence is available. Neither this PR nor Codemagic unit tests
constitute an auto-trading launch.
