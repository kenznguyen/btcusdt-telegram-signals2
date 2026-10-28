# Strategy parity audit (in progress)

## Confirmed from repository
- Android `StrategyMonitorService.kt` instantiates `StrategyEngine()` and calls `processClosedCandles(m15, h1, state)`.
- Monitor filters `m15` candles using `closed`; it persists `StrategyState` to SharedPreferences.
- Android monitor fetches 500 M15 and H1 candles and polls every 15 seconds.
- Python `bot.py` uses OKX BTC-USDT-SWAP history candles and requires confirmed, closed candles.
- Python defaults include leverage 13, initial capital 100, entry margin 50%, DCA ROE -20%, TP ROE 5%, soft SL ROE -35%, emergency SL ROE -90%, fee rate 0.0005.

## Not yet confirmed
- The exact Kotlin source file implementing `StrategyEngine`, its indicator calculations, intrabar fill order, DCA eligibility and entry thresholds.
- Whether Android and Python use identical data sources, rounding, fees and timestamps.
- Whether Freqtrade's standard callbacks can replicate margin accounting and intrabar priority without custom simulation.

## Mandatory parity gates
1. Resolve the Kotlin `StrategyEngine` implementation and freeze its source commit.
2. Replay identical closed M15/H1 candles into both engines, with no future H1 leakage.
3. Compare ordered events: ENTRY, DCA, TP, SOFT_SL, EMERGENCY_SL, including price and timestamp.
4. Compare position quantity, average entry, margin, ROE, fee and equity after each event.
5. Reject verified=true until every discrepancy is documented and approved.
6. Never expose exchange order endpoints or credentials in this subsystem.

The report contract validator checks shape only, not strategy equivalence.
