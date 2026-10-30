"""Offline Kotlin-equivalent position decisions. Not an order submitting Freqtrade strategy."""
from dataclasses import dataclass,replace
from .rules import StrategyRules

@dataclass(frozen=True)
class Position:
    side: str
    qty: float
    avg_entry: float
    initial_margin: float
    dca_margin: float
    entry_notional: float
    entry_time: int
    dca_used: bool = False

class PaperPositionAdapter:
    def __init__(self, rules=None):
        self.rules=rules or StrategyRules()
    def open(self,side,balance,price,at_ms):
        if side not in ("LONG","SHORT") or balance<=0 or price<=0:raise ValueError("invalid entry")
        margin=balance*self.rules.p.entry_margin_pct
        fill=self.rules.execution_fill(price,"BUY" if side=="LONG" else "SELL")
        qty=margin*self.rules.p.leverage/fill
        return Position(side,qty,fill,margin,0.,qty*fill,at_ms)
    def dca(self,pos,price,at_ms,*,adx,rsi,previous_rsi,balance=100.):
        if pos.dca_used or not self.rules.dca(pos.side,self.rules.roe(pos.side,pos.avg_entry,price),adx,rsi,previous_rsi):
            return pos
        margin=pos.initial_margin*self.rules.p.dca_margin_ratio
        if margin<=0 or margin>max(0.,balance-pos.initial_margin-pos.dca_margin)+1e-9:
            return pos
        fill=self.rules.execution_fill(price,"BUY" if pos.side=="LONG" else "SELL")
        additional=margin*self.rules.p.leverage/fill
        qty=pos.qty+additional
        return replace(pos,qty=qty,avg_entry=(pos.avg_entry*pos.qty+fill*additional)/qty,
                       dca_margin=pos.dca_margin+margin,entry_notional=pos.entry_notional+fill*additional,
                       dca_used=True)
    def exit_on_candle(self,pos,open_time,opened,low,high,close,*,rsi,previous_open,previous_close,
                       h1_plus,h1_minus,h1_adx):
        r=self.rules
        emergency=r.emergency(pos.side,low,high,pos.avg_entry)
        soft=r.soft(pos.side,low,high,opened,close,previous_open,previous_close,
                    h1_plus,h1_minus,h1_adx,pos.avg_entry)
        tp=r.tp(pos.side,rsi,r.roe(pos.side,pos.avg_entry,close))
        reason=r.exit_priority(emergency,soft,tp)
        if reason is None:return None
        expected=(r.stop_fill(pos.side,r.threshold_price(pos.side,pos.avg_entry,abs(r.p.emergency_sl_roe)),opened)
                  if emergency else r.execution_fill(close,"SELL" if pos.side=="LONG" else "BUY"))
        confirmed_at=open_time if emergency else open_time+900000
        return {"kind":reason,"side":pos.side,"candleTime":open_time,
                "confirmed_at_ms":confirmed_at,"simulated_fill_at_ms":confirmed_at,
                "expected_fill_price":expected,"actual_fill_price":None,"fill_difference":None,
                "fill_source":"KOTLIN_OHLC_ESTIMATE" if emergency else "CANDLE_CLOSE_SIMULATION"}

def reconcile_fills(expected,actual):
    by_id={}
    for row in actual:
        key=(row["id"],row["kind"],row["candleTime"])
        if key in by_id:raise ValueError("duplicate actual fill")
        by_id[key]=row
    output=[]
    for row in expected:
        key=(row["id"],row["kind"],row["candleTime"])
        found=by_id.pop(key,None)
        target=float(row["price"])
        observed=float(found["price"]) if found is not None else None
        output.append({"id":row["id"],"kind":row["kind"],"candleTime":row["candleTime"],
                       "expected_fill_price":target,"actual_fill_price":observed,
                       "fill_difference":None if observed is None else observed-target,
                       "fill_match":observed is not None and abs(observed-target)<1e-8})
    for row in by_id.values():
        output.append({"id":row["id"],"kind":row["kind"],"candleTime":row["candleTime"],
                       "expected_fill_price":None,"actual_fill_price":float(row["price"]),
                       "fill_difference":None,"fill_match":False})
    return output
