"""Guarded Freqtrade callback shell. BACKTEST ONLY; intentionally cannot open trades.

The callback core is now callable through Freqtrade's method signatures. Native
entries stay disabled until true Kotlin/Freqtrade trace parity is available.
"""
from freqtrade.strategy import IStrategy
from pandas import DataFrame
from .callbacks import PaperCallbackCore

class ChartProParityDryRun(IStrategy):
    INTERFACE_VERSION=3
    timeframe="15m"
    can_short=True
    process_only_new_candles=True
    startup_candle_count=120
    position_adjustment_enable=True
    max_entry_position_adjustment=1
    stoploss=-0.90  # Freqtrade leveraged risk; Kotlin emergency ROE -90% at 13x
    use_custom_stoploss=False
    minimal_roi={"0": 100}
    use_exit_signal=True

    def bot_start(self, **kwargs):
        mode=getattr(self.config.get("runmode"),"value",self.config.get("runmode"))
        if mode not in ("backtest","hyperopt","dry_run") or self.config.get("dry_run") is not True:
            raise RuntimeError("Parity adapter accepts only backtest/hyperopt/dry_run with dry_run=true")
        if self.config.get("trading_mode")!="futures":
            raise RuntimeError("Requires futures research configuration")
        self._parity_core=PaperCallbackCore()

    def populate_indicators(self,dataframe:DataFrame,metadata:dict)->DataFrame:
        # No fabricated indicator signals. Historical OHLCV + H1 parity integration remains pending.
        return dataframe

    def populate_entry_trend(self,dataframe:DataFrame,metadata:dict)->DataFrame:
        dataframe["enter_long"]=0
        dataframe["enter_short"]=0
        return dataframe

    def populate_exit_trend(self,dataframe:DataFrame,metadata:dict)->DataFrame:
        dataframe["exit_long"]=0
        dataframe["exit_short"]=0
        return dataframe

    def confirm_trade_entry(self,*args,**kwargs):
        return False

    def leverage(self,pair,current_time,current_rate,proposed_leverage,max_leverage,entry_tag,side,**kwargs):
        return min(13.0,max_leverage)

    def adjust_trade_position(self,trade,current_time,current_rate,current_profit,
                              min_stake,max_stake,current_entry_rate,current_exit_rate,
                              current_entry_profit,current_exit_profit,**kwargs):
        # Do not generate orders until confirmed closed candle indicators and liquidity
        # metadata are wired from identical canonical Kotlin/Freqtrade OHLCV.
        return None

    def custom_exit(self,pair,trade,current_time,current_rate,current_profit,**kwargs):
        # Protective stoploss remains independent of close-confirmed exits.
        # No exchange orders can originate from this guarded strategy.
        return None
