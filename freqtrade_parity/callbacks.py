"""Safety-first Freqtrade callback decision core; no exchange I/O."""
from .rules import StrategyRules

class PaperCallbackCore:
    def __init__(self):
        self.rules=StrategyRules()

    def dca_request(self,trade,row,side,average,balance,has_open_orders):
        if has_open_orders or getattr(trade,"has_open_orders",False):return None
        if trade.get_custom_data("chart_pro_dca_status") in ("REQUESTED","FILLED"):return None
        if getattr(trade,"nr_of_successful_entries",0)!=1:return None
        try:
            if any(row[k] is None for k in ("rsi","previous_rsi","adx","close","open_time")):return None
            roe=self.rules.roe(side,average,row["close"])
            if not self.rules.dca(side,roe,row["adx"],row["rsi"],row["previous_rsi"]):return None
            amount=trade.stake_amount*self.rules.p.dca_margin_ratio
            if amount<=0 or amount>max(0.,balance-trade.stake_amount)+1e-9:return None
            trade.set_custom_data("chart_pro_dca_status","REQUESTED")
            trade.set_custom_data("chart_pro_dca_candle",int(row["open_time"]))
            return amount,"kotlin_dca_once"
        except (TypeError,ValueError,KeyError,ZeroDivisionError):return None

    def exit_decision(self,side,average,row):
        keys=("open_time","open","low","high","close","rsi","previous_open","previous_close","h1_plus","h1_minus","h1_adx")
        if any(k not in row or row[k] is None for k in keys):return None
        try:
            r=self.rules
            emergency=r.emergency(side,row["low"],row["high"],average)
            soft=r.soft(side,row["low"],row["high"],row["open"],row["close"],row["previous_open"],row["previous_close"],
                        row["h1_plus"],row["h1_minus"],row["h1_adx"],average)
            tp=r.tp(side,row["rsi"],r.roe(side,average,row["close"]))
            kind=r.exit_priority(emergency,soft,tp)
            if kind is None:return None
            confirmed=int(row["open_time"])+(0 if emergency else 900000)
            return {"kind":kind,"candleTime":int(row["open_time"]),"confirmed_at_ms":confirmed}
        except (TypeError,ValueError,ZeroDivisionError):return None

    def custom_exit_reason(self,side,average,closed_candle):
        result=self.exit_decision(side,average,closed_candle)
        # Emergency must be handled by protective stop, not a delayed custom_exit.
        return result["kind"] if result and result["kind"]!="EMERGENCY SL" else None
