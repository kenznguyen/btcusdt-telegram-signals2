"""Closed-candle CORE lifecycle ported from StrategyEngine.kt PR #32.
Offline paper simulation only; no exchange or live-order capability.
"""
from dataclasses import dataclass, replace
from .core_indicators import indicator_series

@dataclass(frozen=True)
class Config:
    leverage:float=13.; h1_adx_entry:float=20.; long_rsi_entry:float=30.; short_rsi_entry:float=70.
    long_rsi_tp:float=76.; short_rsi_tp:float=24.; tp_roe:float=5.; dca_roe:float=-20.
    dca_adx:float=45.; long_dca_rsi:float=20.; short_dca_rsi:float=80.
    soft_sl_roe:float=-35.; emergency_sl_roe:float=-90.; soft_sl_adx:float=35.
    entry_margin_pct:float=.5; dca_margin_ratio:float=1.; fee_rate:float=.0005; slippage_bps:float=5.

@dataclass(frozen=True)
class Position:
    side:str; qty:float; avg_entry:float; initial_margin:float; dca_margin:float
    entry_notional:float; entry_time:int; dca_used:bool=False

@dataclass(frozen=True)
class State:
    balance:float=100.; position:Position|None=None; last_processed_open_time:int=0

def roe(side, avg, price, cfg):
    return (price-avg if side=="LONG" else avg-price)/avg*cfg.leverage*100

def threshold(side,avg,absolute_roe,cfg):
    move=abs(absolute_roe)/(100*cfg.leverage)
    return avg*(1-move if side=="LONG" else 1+move)

def fill(price,action,cfg):
    slip=max(0.,cfg.slippage_bps)/10000
    return price*(1+slip if action=="BUY" else 1-slip)

def stop_fill(side,stop,opened,cfg):
    return fill(min(opened,stop) if side=="LONG" else max(opened,stop),
                "SELL" if side=="LONG" else "BUY",cfg)

def replay(m15,h1, state=None, cfg=None):
    cfg=cfg or Config(); state=state or State(); events=[]
    candles=sorted((c for c in m15 if c["closed"]),key=lambda c:c["open_time"])
    hours=sorted((c for c in h1 if c["closed"]),key=lambda c:c["open_time"])
    if len(candles)<2:return state,events
    mi=indicator_series(candles);hi=indicator_series(hours)
    hidx=0
    for i,c in enumerate(candles):
        t=c["open_time"]
        if i==0 or t<=state.last_processed_open_time:continue
        prior=mi[i-1]["rsi"]; current=mi[i]["rsi"]; adx=mi[i]["adx"]
        has_rsi=prior is not None and current is not None
        if not has_rsi and state.position is None:
            state=replace(state,last_processed_open_time=t);continue
        bucket=t-t%3600000
        while hidx+1<len(hours) and hours[hidx+1]["open_time"]<bucket:hidx+=1
        prior_hour=hours[hidx]["open_time"]<bucket if hours else False
        hp=hi[hidx]["plus_di"] if prior_hour else None
        hm=hi[hidx]["minus_di"] if prior_hour else None
        ha=hi[hidx]["adx"] if prior_hour else None
        has_h=all(x is not None for x in (hp,hm,ha))
        go_long=bool(has_rsi and has_h and adx is not None and hp>hm and ha>cfg.h1_adx_entry and prior<=cfg.long_rsi_entry and current>cfg.long_rsi_entry)
        go_short=bool(has_rsi and has_h and adx is not None and hm>hp and ha>cfg.h1_adx_entry and prior>=cfg.short_rsi_entry and current<cfg.short_rsi_entry)
        p=state.position;exited=False
        if p:
            r=roe(p.side,p.avg_entry,c["close"],cfg)
            emergency_price=threshold(p.side,p.avg_entry,cfg.emergency_sl_roe,cfg)
            soft_price=threshold(p.side,p.avg_entry,cfg.soft_sl_roe,cfg)
            emergency=c["low"]<=emergency_price if p.side=="LONG" else c["high"]>=emergency_price
            prev=candles[i-1]
            reversal=bool(has_h and ha>cfg.soft_sl_adx and (hm>hp if p.side=="LONG" else hp>hm))
            soft=bool(reversal and ((c["low"]<=soft_price and c["open"]>c["close"] and prev["close"]<prev["open"]) if p.side=="LONG" else (c["high"]>=soft_price and c["close"]>c["open"] and prev["close"]>prev["open"])))
            tp=bool(current is not None and r>=cfg.tp_roe and (current>=cfg.long_rsi_tp if p.side=="LONG" else current<=cfg.short_rsi_tp))
            reason="EMERGENCY SL" if emergency else "SOFT SL" if soft else "TAKE PROFIT" if tp else None
            if reason:
                price=stop_fill(p.side,emergency_price if emergency else soft_price,c["open"],cfg) if (emergency or soft) else fill(c["close"],"SELL" if p.side=="LONG" else "BUY",cfg)
                gross=(price-p.avg_entry if p.side=="LONG" else p.avg_entry-price)*p.qty
                fees=(p.entry_notional+price*p.qty)*cfg.fee_rate
                state=replace(state,balance=state.balance+gross-fees,position=None)
                events.append(dict(kind=reason,side=p.side,price=price,candleTime=t,netPnl=gross-fees,fees=fees))
                exited=True
        if state.position is None and not exited and state.balance>0 and (go_long or go_short):
            side="LONG" if go_long else "SHORT"
            price=fill(c["close"],"BUY" if side=="LONG" else "SELL",cfg)
            margin=state.balance*cfg.entry_margin_pct
            qty=margin*cfg.leverage/price
            state=replace(state,position=Position(side,qty,price,margin,0.,qty*price,t))
            events.append(dict(kind=side+" ENTRY",side=side,price=price,candleTime=t))
        elif state.position is not None and not exited:
            p=state.position
            if not p.dca_used and adx is not None and current is not None and prior is not None:
                r=roe(p.side,p.avg_entry,c["close"],cfg)
                qualifies= r<=cfg.dca_roe and adx>cfg.dca_adx and ((current>cfg.long_dca_rsi and current>prior) if p.side=="LONG" else (current<cfg.short_dca_rsi and current<prior))
                margin=p.initial_margin*cfg.dca_margin_ratio
                if qualifies and margin>0 and margin<=max(0.,state.balance-p.initial_margin-p.dca_margin)+1e-9:
                    price=fill(c["close"],"BUY" if p.side=="LONG" else "SELL",cfg)
                    added=margin*cfg.leverage/price
                    qty=p.qty+added
                    avg=(p.avg_entry*p.qty+price*added)/qty
                    state=replace(state,position=replace(p,qty=qty,avg_entry=avg,dca_margin=p.dca_margin+margin,entry_notional=p.entry_notional+price*added,dca_used=True))
                    events.append(dict(kind="DCA",side=p.side,price=price,candleTime=t))
        state=replace(state,last_processed_open_time=t)
    return state,events
