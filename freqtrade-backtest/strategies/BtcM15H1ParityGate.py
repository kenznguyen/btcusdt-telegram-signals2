"""Freqtrade adapter scaffold: intentionally refuses to trade until parity is proven.

The Android StrategyEngine remains the authoritative signal source.  A strategy
implementation must not be invented from defaults or incomplete documentation.
"""
from freqtrade.strategy import IStrategy
from pandas import DataFrame


class BtcM15H1ParityGate(IStrategy):
    INTERFACE_VERSION = 3
    timeframe = "15m"
    can_short = True
    startup_candle_count = 500
    minimal_roi = {"0": 1000}
    stoploss = -0.99
    use_exit_signal = True
    process_only_new_candles = True

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # No signals until the Android StrategyEngine logic is fully ported.
        dataframe["enter_long"] = 0
        dataframe["enter_short"] = 0
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["exit_long"] = 0
        dataframe["exit_short"] = 0
        return dataframe
