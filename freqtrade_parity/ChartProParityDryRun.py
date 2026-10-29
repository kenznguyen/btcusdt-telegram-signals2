"""Guarded Freqtrade callback shell. BACKTEST ONLY; intentionally cannot open trades.

The callback core is now callable through Freqtrade's method signatures. Native
entries stay disabled until true Kotlin/Freqtrade trace parity is available.
"""
from freqtrade.strategy import IStrategy
from pandas import DataFrame
from freqtrade_parity.callbacks import PaperCallbackCore

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

    def informative_pairs(self):
        pairs=self.dp.current_whitelist() if self.dp is not None else []
        return [(pair, "1h") for pair in pairs]

    def populate_indicators(self,dataframe:DataFrame,metadata:dict)->DataFrame:
        from freqtrade_parity.context import enrich_closed_m15
        if self.dp is None or dataframe.empty:
            return dataframe
        h1=self.dp.get_pair_dataframe(pair=metadata["pair"],timeframe="1h")
        if h1 is None or h1.empty:
            return dataframe
        def records(frame):
            return [{"open_time":int(row["date"].timestamp()*1000),
                     "open":float(row["open"]),"high":float(row["high"]),
                     "low":float(row["low"]),"close":float(row["close"]),
                     "volume":float(row["volume"]),"closed":True}
                    for _,row in frame.iterrows()]
        context=enrich_closed_m15(records(dataframe),records(h1))
        by_time={row["open_time"]:row for row in context}
        keys=("rsi","adx","previous_rsi","previous_open","previous_close",
              "h1_plus","h1_minus","h1_adx","h1_source_open_time")
        for key in keys:
            dataframe[key]=[by_time.get(int(date.timestamp()*1000),{}).get(key)
                            for date in dataframe["date"]]
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

    def _latest_closed_context(self,pair,current_time):
        if self.dp is None:
            return None
        dataframe,_=self.dp.get_analyzed_dataframe(pair,self.timeframe)
        if dataframe is None or len(dataframe)<2:
            return None
        row=dataframe.iloc[-1]
        date=row.get("date")
        if date is None or getattr(date,"tzinfo",None) is None:
            return None
        open_ms=int(date.timestamp()*1000)
        if open_ms+900000>int(current_time.timestamp()*1000):
            return None
        columns=("open","high","low","close","rsi","adx","previous_rsi",
                 "previous_open","previous_close","h1_plus","h1_minus","h1_adx")
        if any(col not in row or row[col] is None for col in columns):
            return None
        import math
        if any(not math.isfinite(float(row[col])) for col in columns):
            return None
        return {"open_time":open_ms,**{col:float(row[col]) for col in columns}}

    def adjust_trade_position(self,trade,current_time,current_rate,current_profit,
                              min_stake,max_stake,current_entry_rate,current_exit_rate,
                              current_entry_profit,current_exit_profit,**kwargs):
        row=self._latest_closed_context(trade.pair,current_time)
        if row is None:
            return None
        # A historical imported trade is necessary: new entries are intentionally disabled.
        side="SHORT" if trade.is_short else "LONG"
        balance=self.wallets.get_total_stake_amount()
        core=getattr(self,"_parity_core",PaperCallbackCore())
        request=core.dca_request(trade,row,side,trade.open_rate, balance,
                                 getattr(trade,"has_open_orders",True))
        if request is None:return None
        amount,tag=request
        if amount<min_stake or (max_stake is not None and amount>max_stake):
            # Fail closed. REQUESTED marker remains persisted to prevent retries.
            return None
        return amount,tag

    def custom_exit(self,pair,trade,current_time,current_rate,current_profit,**kwargs):
        row=self._latest_closed_context(pair,current_time)
        if row is None:return None
        core=getattr(self,"_parity_core",PaperCallbackCore())
        return core.custom_exit_reason("SHORT" if trade.is_short else "LONG",trade.open_rate,row)
