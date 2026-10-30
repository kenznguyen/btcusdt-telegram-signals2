# Phase 9 — 3 shared virtual positions, 10% equity initial margin

Scope: 180-day OFFLINE PAPER research only. Not an APK release, live order
feature, native Freqtrade multi-trade support or independent trade parity.

## Adopted parameters

- max_positions = 3 for the shared CORE + AI research portfolio.
- entry_margin_pct = 0.10 of *current mark-to-market account equity*
  at the confirmed, closed M15 signal candle, not 10% notional.
- 13x leverage is unchanged: at equity 100 USDT, the first position uses
  10 USDT margin and about 130 USDT notional exposure, excluding fees.
- In DUAL, at most 2 positions may be AI-origin; reserve 1 slot for CORE.
  AI_ONLY may fill all three. No cross-direction virtual positions are
  permitted simultaneously on the same BTC/USDT pair.
- DCA remains once per individual position when **existing** RSI/ADX/ROE
  rules permit it, 100% of that position's initial margin (e.g. 10 USDT).
- Total initial + DCA reserved margin is capped at 60% current equity at
  each proposed fill, with a separate cash/fee check. Existing positions
  are not retrospectively forced closed solely by the new cap.
- Emergency SL beats TP/Soft SL and pending DCA; each position maintains
  independent DCA/TP/SL lifecycle and trade ID.
- Models and signals still rely only on matching real native FreqAI
  prediction SHA / canonical OKX M15, H1 and 5m history.

## Why this is NOT yet an executable 3-trade Freqtrade portfolio

Phase 9 is a *virtual* sub-position simulation of the same BTCUSDT pair.
Real exchange one-way/hedge modes, margin aggregation, liquidation tiers,
funding, native Freqtrade trade lifecycle and Android Kotlin parity are
NOT certified. No production ReservationLedger or Android StrategyEngine
behavior is changed. The existing Phase 3-8 1-position backtest is
preserved unchanged as a baseline; Phase 9 outputs separate sidecar files.

## Evidence

On Codemagic branch
feature/dual-strategy-phase9-three-slots-ten-percent-20261031:

1. Run workflow dual-strategy-phase3-unit.
2. Manually run dual-strategy-phase3-native-research with
   PHASE3_DAYS=180, PHASE3_DETAIL_MINUTES=5, PHASE3_DOWNLOAD_DAYS=220.
3. Review artifacts/phase3/paper/portfolio-180-summary.json.
4. Review per-mode portfolio-core-only-*, portfolio-ai-only-*,
   portfolio-dual-* events/trades/equity/report files.
5. Require portfolio-180-independent-audit.json:
   paper_portfolio_integrity_verified=true, errors=[].

Independent audit verifies no more than 3 virtual positions, DUAL AI
slot cap, per-entry 10% of traced equity, single DCA per trade, margin
accounting, simulated fills, individual exit lifecycle, PnL, fees and
drawdown. Phase 9 changes do NOT certify FreqAI OOS, native trade parity
or exchange fills. ready_for_360, live_orders_enabled,
full_core_parity_certified always remain false.

## Risk example (equity 100 USDT)

- Each new entry: 10 USDT margin, ~130 USDT notional at 13x.
- 3 entries: about 30 USDT initial margin and ~390 USDT notional.
- If all 3 qualify for one equal-size DCA, total margin could
  approach 60 USDT and notional ~780 USDT, subject to shared gate.
- This does NOT mean that loss is limited to 10% per position.
  Gaps, correlated positions and leverage can erase account equity.

Existing CORE strategy RSI, ADX, H1 filter, Smart DCA, TP, Soft SL and
Emergency SL thresholds remain unchanged. No old APK feature removed.
