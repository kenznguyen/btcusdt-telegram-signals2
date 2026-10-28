"""FreqAI LightGBM research-only adapter. No BUY/SELL or real orders."""
from freqtrade.strategy import IStrategy
from freqtrade.enums import RunMode
from pandas import DataFrame
import talib.abstract as ta


class BtcFreqaiResearch(IStrategy):
    INTERFACE_VERSION = 3
    timeframe = "15m"
    can_short = True
    process_only_new_candles = True
    startup_candle_count = 240
    minimal_roi = {"0": 1000}
    stoploss = -0.99
    use_exit_signal = False

    def bot_start(self, **kwargs):
        if self.config.get("runmode") != RunMode.BACKTEST:
            raise RuntimeError("FreqAI research strictly BACKTEST ONLY")
        if self.config.get("trading_mode") != "futures":
            raise RuntimeError("Research requires Futures historical data")
        if not self.config.get("freqai", {}).get("enabled"):
            raise RuntimeError("FreqAI must be explicitly enabled")

    def feature_engineering_expand_all(self, dataframe: DataFrame,
                                       period: int, **kwargs) -> DataFrame:
        # All features use current/past CLOSED candles only.
        dataframe["%-rsi-period"] = ta.RSI(dataframe, timeperiod=period)
        dataframe["%-adx-period"] = ta.ADX(dataframe, timeperiod=period)
        dataframe["%-mfi-period"] = ta.MFI(dataframe, timeperiod=period)
        dataframe["%-relative-volume-period"] = (
            dataframe["volume"] /
            dataframe["volume"].rolling(period).mean()
        )
        middle = dataframe["close"].rolling(period).mean()
        std = dataframe["close"].rolling(period).std(ddof=0)
        dataframe["%-bb-width-period"] = 4.0 * std / middle
        dataframe["%-percent-b-period"] = (
            dataframe["close"] - (middle - 2.0 * std)
        ) / (4.0 * std.replace(0, float("nan")))
        return dataframe

    def feature_engineering_expand_basic(self, dataframe: DataFrame, **kwargs) -> DataFrame:
        dataframe["%-close-return"] = dataframe["close"].pct_change()
        dataframe["%-volume"] = dataframe["volume"]
        dataframe["%-range"] = (dataframe["high"] - dataframe["low"]) / dataframe["close"]
        return dataframe

    def feature_engineering_standard(self, dataframe: DataFrame, **kwargs) -> DataFrame:
        dataframe["%-hour-utc"] = dataframe["date"].dt.hour / 23.0
        return dataframe

    def set_freqai_targets(self, dataframe: DataFrame, **kwargs) -> DataFrame:
        # One target only: compatible with FreqAI LightGBMRegressor.
        # 4 closed 15m bars = 60-minute ahead realized return.
        dataframe["&-return-4m15"] = (
            dataframe["close"].shift(-4) / dataframe["close"] - 1.0
        )
        return dataframe

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return self.freqai.start(dataframe, metadata, self)

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["enter_long"] = 0
        dataframe["enter_short"] = 0
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["exit_long"] = 0
        dataframe["exit_short"] = 0
        return dataframe
