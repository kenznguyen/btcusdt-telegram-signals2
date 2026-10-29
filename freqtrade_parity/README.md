# StrategyEngine Kotlin → Freqtrade research parity

## Safety boundary
Android remains the production signal UI. This branch is an **offline research port in progress**, not a full Freqtrade strategy, not an executable backtest and not an approved equivalent engine. There is no exchange order endpoint, API credential or live trading path. The pre-existing `ChartProFreqaiResearch` remains prediction-only, with native entries disabled.

The first port is `freqtrade_parity/rules.py`: immutable parameters and matching decision helpers from `android-app/.../StrategyEngine.kt`. Python tests in `test_rules.py` run via Codemagic `freqtrade-strategy-parity`.

## Required for complete conversion
- Port precise Kotlin Wilder RSI, DMI/ADX, closed M15 candle handling, prior **closed** H1 hour mapping and indicator warmup. Avoid TA-Lib substitution until parity is proven.
- Port full position/state transitions, entry sizing, one-shot DCA, event order, execution slippage, synthetic equity and cooldown semantics.
- Map execution to Freqtrade 2026.9 hooks carefully; for testing `dry_run` and exchange-independent backtest only. No `trade` command or live config; no live API credentials.
- Preserve risk precedence: EMERGENCY SL > SOFT SL > TAKE PROFIT > entry/DCA. Emergency may require finer `--timeframe-detail 1m` data; document OHLC ambiguity and gap-risk mismatch.
- Export actual event traces from *both* Android Kotlin and Python for identical checksum-pinned OHLCV, and compare all five event classes, timestamps, price/qty, margin, fees and net PnL. Distinguish signal parity from fill parity.
- Trace-verification gate must require real nonempty traces, canonical checksum and matching schema/parameters; missing evidence means `parity_verified: false`. The current elementary `compare_event_traces` is deliberately **not** a certification of Freqtrade runtime parity.
- Only after event parity, run native Freqtrade backtests 180/360 days with funding, stop fills, liquidation and mark-to-market drawdown reviews.

## Source defaults checked against Kotlin
13x leverage, RSI(14), DMI(14), ADX smoothing(14), H1 ADX > 20, LONG RSI cross above 30, SHORT RSI cross below 70, TP +5% ROE + RSI 76/24, DCA -20% ROE + ADX >45 + RSI direction, soft stop -35% ROE + reversal + two candle bodies + H1 ADX >35, emergency -90% ROE, initial stake 50% of balance, DCA stake 100% of initial, fee 0.0005 and slippage 5 bps.

## CI
Codemagic: `freqtrade-strategy-parity` (offline Python) and `android-chart-pro-debug` (Android tests and APKs) on this branch. Neither run has been verified for this head yet. GitHub is source/PR storage only.

## Wilder implementation delivered in this increment
`freqtrade_parity/indicators.py` now implements Kotlin-style RMA seeding and gaps, RSI, true-range directional movement, DI, DX and ADX. `prior_closed_h1_index` excludes the current H1 bucket and unclosed H1 bars. The Codemagic offline workflow runs `test_indicators` alongside rules tests.

## Remaining blockers (not completed)
A full native Freqtrade position lifecycle, DCA and stop callback adapter, signed shared OHLCV dataset, genuine paired Kotlin/Freqtrade trace exports and 180/360-day Freqtrade backtests are **not yet implemented/verified**. Do not claim parity or profitability. The source branch remains draft and has no live trading.

## Position/fill simulation increment
`position.py` is an **offline adapter**, not Freqtrade native callbacks. It mirrors Kotlin entry sizing (50% balance and 13x leverage), DCA only once via immutable `dca_used`, exit precedence (Emergency > Soft > TP), candle-close soft/TP fill estimates, and emergency threshold/open-gap estimate. `reconcile_fills` pairs trace entries with strict ID/kind/candleTime keys and returns `expected_fill_price`, `actual_fill_price`, and `fill_difference` without inventing missing fills.

Timing fields are simulation semantics: emergency threshold recognition is intrabar from OHLC; without 1m/5m detail the actual crossing sequence and true fill time are unknown. Soft/TP confirm only at M15 close. A production Freqtrade callback port must use stateful trade custom data and verify no duplicate DCA on callback repeats, including process restarts. This increment has not done so.

**Important:** These offline unit tests are not actual independent Kotlin/Freqtrade execution traces, do not verify parity, and do not establish realistic fills, funding, liquidation or 180/360-day performance.
