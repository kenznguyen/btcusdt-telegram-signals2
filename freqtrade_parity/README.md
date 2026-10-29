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
