"""Phase 9 virtual BTCUSDT portfolio paper replay: 3 slots, 10% equity margin.

This is deliberately a SIDE-CAR RESEARCH simulator. The certified baseline
paper replay, native entry guards and production reservation ledger are not
changed. Multiple virtual BTC/USDT slots are not evidence of venue hedge-mode
or Freqtrade native multi-position support; no exchange orders are possible.
"""
from __future__ import annotations

from dataclasses import dataclass
import argparse
import csv
import json
import math
from pathlib import Path

from freqtrade_parity.rules import StrategyRules
from quant_system.dual_strategy import (
    Origin, Side, Signal, RiskSnapshot, admit, admit_adjustment, core_signal, _select
)
from quant_system.paper_backtest import (
    M15_MS, EVENT_FIELDS, TRADE_FIELDS, _source_signal, _sha, _pnl,
    validated_native_predictions, verify_native_prediction_evidence, closed_context
)
from quant_system.intrabar_audit import audit_history
from quant_system.native_dataset import training_window
from freqtrade_parity.dataset_io import read_closed_csv


@dataclass(frozen=True)
class PortfolioConfig:
    max_positions: int = 3
    entry_margin_pct: float = 0.10
    max_total_margin_pct: float = 0.60
    ai_slots_in_dual: int = 2

    def __post_init__(self):
        if (type(self.max_positions) is not int or self.max_positions != 3
            or type(self.ai_slots_in_dual) is not int or self.ai_slots_in_dual != 2
            or not math.isfinite(self.entry_margin_pct) or self.entry_margin_pct != .10
            or not math.isfinite(self.max_total_margin_pct)
            or self.max_total_margin_pct < self.max_positions*self.entry_margin_pct
            or self.max_total_margin_pct > .60):
            raise ValueError('UNAPPROVED_PAPER_PORTFOLIO_POLICY')


@dataclass
class PaperPosition:
    trade_id: str
    origin: str
    side: str
    entry_at_ms: int
    entry_price: float
    average: float
    quantity: float
    margin: float
    initial_margin: float
    entry_fee: float
    dca_count: int = 0
    dca_window_start: int | None = None
    dca_disabled: bool = False


def replay_portfolio(m15, fine, predictions, *, mode, dataset_sha256,
                     detail_sha256, model_identifier,
                     starting_balance=100., config=None):
    """Run separate virtual positions through shared collateral/position risk.

    All decisions use closed M15 and previous-closed H1. Entries, TP, soft SL
    and DCA fill at NEXT 5m open. Emergency stop checks intrabar 5m OHLC.
    The fill is MODELED, NOT an actual exchange execution or liquidation.
    """
    policy=config or PortfolioConfig()
    if not isinstance(policy,PortfolioConfig):
        raise ValueError('INVALID_PORTFOLIO_POLICY')
    if mode not in ('CORE_ONLY','AI_ONLY','DUAL') or not m15 or not fine:
        raise ValueError('INVALID_PAPER_PORTFOLIO_INPUT')
    dataset_sha256,detail_sha256=_sha(dataset_sha256),_sha(detail_sha256)
    cap=float(starting_balance)
    if not math.isfinite(cap) or not 0<cap<=1e6:
        raise ValueError('INVALID_STARTING_CAPITAL')
    start=m15[0]['open_time']
    if any(r.get('closed') is not True or r['open_time']!=start+i*M15_MS
           for i,r in enumerate(m15)):
        raise ValueError('INCOMPLETE_M15_REPLAY')
    if len(fine)!=len(m15)*3 or any(
        r.get('closed') is not True or r['open_time']!=start+i*300000
        for i,r in enumerate(fine)):
        raise ValueError('INCOMPLETE_5M_REPLAY')
    forecasts=validated_native_predictions(
        predictions,{r['open_time']:r for r in m15},model_identifier)
    rules=StrategyRules()
    positions={}
    pending={}
    events=[]
    trades=[]
    equity_curve=[]
    fees=realized=0.
    peak=cap
    used_ids=set()
    denied=limit_denials=ai_denials=collateral_denials=side_denials=0
    conflicts=dca_requests=dca_denied=0
    max_concurrent=0
    last_filled=-1

    def equity(mark):
        return cap+realized-fees+sum(_pnl(p,mark) for p in positions.values())

    def reserved():
        return sum(p.margin for p in positions.values())

    def available(mark):
        value=equity(mark)
        return max(0.,min(value-reserved(),
                          policy.max_total_margin_pct*value-reserved()))

    def risk_candidate(origin, stake, mark):
        # Always pass Shared Risk admission, plus portfolio exposure/collateral.
        value=equity(mark)
        return RiskSnapshot(data_fresh=True,state_reconciled=True,
            has_unresolved_reservation=False,active_positions=len(positions),
            max_positions=policy.max_positions,
            available_margin=available(mark),required_margin=stake,
            ai_model_validated=origin==Origin.AI),value

    def record(kind, p, timestamp, request, expected, actual, qty, stake, fee):
        nonlocal last_filled
        if timestamp<last_filled:
            raise ValueError('NONMONOTONIC_PORTFOLIO_FILLS')
        last_filled=timestamp
        event_id=f'{mode}:{p.trade_id}:{kind}:{timestamp}:{len(events)}'
        if event_id in used_ids:
            raise ValueError('DUPLICATE_PORTFOLIO_EVENT')
        used_ids.add(event_id)
        events.append(dict(event_id=event_id,kind=kind,origin=p.origin,side=p.side,
            trade_id=p.trade_id,candle_time=request['candle_time'],
            decision_at_ms=request['decision_ms'],
            confirmed_at_ms=request['confirmed_ms'],filled_at_ms=timestamp,
            expected_fill_price=expected,actual_fill_price=actual,
            fill_difference=actual-expected,fill_source='SIMULATED_OHLCV_5M',
            quantity_base=qty,margin_usdt=stake,fee_usdt=fee,
            dataset_sha256=dataset_sha256,detail_sha256=detail_sha256))

    def opening(request, bar):
        nonlocal fees,denied,limit_denials,ai_denials,collateral_denials,side_denials,max_concurrent
        origin=Origin(request['origin'])
        candidate=Signal(origin,Side(request['side']),request['decision_ms'],request['trade_id'])
        stake=request['margin']
        snapshot,current_equity=risk_candidate(origin,stake,bar['open'])
        if mode=='DUAL' and origin==Origin.AI and sum(
                p.origin=='AI' for p in positions.values())>=policy.ai_slots_in_dual:
            ai_denials+=1;denied+=1
            return
        if positions and any(p.side!=request['side'] for p in positions.values()):
            side_denials+=1;denied+=1
            return
        response=admit(candidate,snapshot)
        if not response.accepted or current_equity<=0 or stake<=0:
            denied+=1
            if response.reason=='POSITION_LIMIT':
                limit_denials+=1
            else:
                collateral_denials+=1
            return
        actual=rules.execution_fill(bar['open'],'BUY' if request['side']=='LONG' else 'SELL')
        qty=stake*rules.p.leverage/actual
        fee=qty*actual*rules.p.fee_rate
        if fee>=available(bar['open'])-stake+fee and current_equity<=fee:
            collateral_denials+=1;denied+=1;return
        p=PaperPosition(request['trade_id'],request['origin'],request['side'],
            bar['open_time'],actual,actual,qty,stake,stake,fee)
        positions[p.trade_id]=p
        fees+=fee
        record(request['kind'],p,bar['open_time'],request,request['expected'],
               actual,qty,stake,fee)
        max_concurrent=max(max_concurrent,len(positions))

    def dca_fill(request,bar):
        nonlocal fees,denied,dca_denied
        p=positions.get(request['trade_id'])
        if p is None or p.dca_count or p.side!=request['side']:
            return
        origin=Origin(p.origin)
        stake=request['margin']
        available_margin=available(bar['open'])
        candidate=Signal(origin,Side(p.side),request['decision_ms'],
                         'portfolio-dca:'+p.trade_id)
        # For EXISTING positions, admission must not consume an additional
        # position slot; the caller binds the exact live trade ID above.
        local=RiskSnapshot(True,True,False,1,1,available_margin,stake,
                           ai_model_validated=origin==Origin.AI)
        approved=admit_adjustment(candidate,local,
            position_side=Side(p.side),dca_count=p.dca_count)
        if not approved.accepted or stake<=0 or equity(bar['open'])<=0:
            denied+=1;dca_denied+=1;return
        actual=rules.execution_fill(bar['open'],'BUY' if p.side=='LONG' else 'SELL')
        qty=stake*rules.p.leverage/actual
        fee=qty*actual*rules.p.fee_rate
        new_qty=p.quantity+qty
        p.average=(p.average*p.quantity+actual*qty)/new_qty
        p.quantity=new_qty
        p.margin+=stake
        p.entry_fee+=fee
        p.dca_count=1
        p.dca_disabled=True
        fees+=fee
        record('DCA',p,bar['open_time'],request,request['expected'],actual,
               qty,stake,fee)

    def closing(request,bar,*,emergency=False):
        nonlocal realized,fees
        p=positions.get(request['trade_id'])
        if p is None:
            return
        threshold=rules.threshold_price(p.side,p.average,abs(rules.p.emergency_sl_roe))
        if emergency:
            expected=threshold
            reference=min(bar['open'],threshold) if p.side=='LONG' else max(bar['open'],threshold)
        else:
            expected=request['expected']
            reference=bar['open']
        actual=rules.execution_fill(reference,'SELL' if p.side=='LONG' else 'BUY')
        qty=p.quantity
        fee=qty*actual*rules.p.fee_rate
        gross=_pnl(p,actual)
        realized+=gross;fees+=fee
        trades.append(dict(trade_id=p.trade_id,origin=p.origin,side=p.side,
            entry_at_ms=p.entry_at_ms,exit_at_ms=bar['open_time'],
            entry_price=p.entry_price,exit_price=actual,
            exit_reason=request['kind'],dca_count=p.dca_count,
            margin_usdt=p.margin,gross_pnl_usdt=gross,fees_usdt=p.entry_fee+fee,
            net_pnl_ex_funding_usdt=gross-p.entry_fee-fee,
            roe_percent=100*gross/p.margin))
        record(request['kind'],p,bar['open_time'],request,expected,actual,
               qty,p.margin,fee)
        del positions[p.trade_id]

    def emergency_request(p,bar,row):
        if not rules.emergency(p.side,bar['low'],bar['high'],p.average):
            return None
        return dict(kind='EMERGENCY SL',origin=p.origin,side=p.side,
            trade_id=p.trade_id,margin=p.margin,
            expected=rules.threshold_price(p.side,p.average,abs(rules.p.emergency_sl_roe)),
            candle_time=row['open_time'],decision_ms=bar['open_time'],
            confirmed_ms=bar['open_time'])

    for i,row in enumerate(m15):
        bars=fine[3*i:3*i+3]
        for j,bar in enumerate(bars):
            if j==0:
                requests=list(pending.values())
                pending.clear()
                # Resolve risk-reducing exits first. Deterministic ordering
                # within the same 5m opening timestamp.
                requests.sort(key=lambda r:(
                    0 if r['kind'] in ('TAKE PROFIT','SOFT SL') else
                    1 if r['kind']=='DCA' else 2,r['trade_id']))
                for request in requests:
                    p=positions.get(request['trade_id'])
                    if p is not None:
                        trigger=emergency_request(p,bar,row)
                        if trigger is not None:
                            closing(trigger,bar,emergency=True)
                            continue
                    if request['kind'] in ('LONG ENTRY','SHORT ENTRY'):
                        opening(request,bar)
                    elif request['kind']=='DCA':
                        dca_fill(request,bar)
                    else:
                        closing(request,bar)
            for p in list(positions.values()):
                trigger=emergency_request(p,bar,row)
                if trigger is not None:
                    closing(trigger,bar,emergency=True)
                    pending.pop(p.trade_id,None)
        close_ms=row['open_time']+M15_MS
        marked=equity(row['close'])
        peak=max(peak,marked)
        equity_curve.append(dict(candle_close_ms=close_ms,
            equity_mtm_ex_funding_usdt=marked,
            unrealized_usdt=sum(_pnl(p,row['close']) for p in positions.values()),
            drawdown_usdt=peak-marked,open_position=bool(positions),
            open_positions=len(positions),reserved_margin_usdt=reserved()))
        for p in list(positions.values()):
            keys=('rsi','previous_open','previous_close',
                  'h1_plus','h1_minus','h1_adx')
            if any(row.get(key) is None for key in keys):
                continue
            soft=rules.soft(p.side,row['low'],row['high'],row['open'],row['close'],
                row['previous_open'],row['previous_close'],row['h1_plus'],
                row['h1_minus'],row['h1_adx'],p.average)
            tp=rules.tp(p.side,row['rsi'],
                        rules.roe(p.side,p.average,row['close']))
            kind=rules.exit_priority(False,soft,tp)
            if kind is not None:
                pending[p.trade_id]=dict(kind=kind,origin=p.origin,side=p.side,
                    trade_id=p.trade_id,margin=p.margin,expected=row['close'],
                    candle_time=row['open_time'],confirmed_ms=close_ms,
                    decision_ms=close_ms)
                continue
            if p.dca_disabled or p.dca_count:
                continue
            roe=rules.roe(p.side,p.average,row['close'])
            if p.dca_window_start is None and roe<=rules.p.dca_roe:
                p.dca_window_start=i
            if p.dca_window_start is None:
                continue
            if i-p.dca_window_start>=2:
                p.dca_disabled=True
                continue
            if (row.get('adx') is not None and row.get('previous_rsi') is not None
                and rules.dca(p.side,roe,row['adx'],row['rsi'],row['previous_rsi'])):
                stake=p.initial_margin*rules.p.dca_margin_ratio
                dca_requests+=1
                local=RiskSnapshot(True,True,False,1,1,available(row['close']),
                    stake,ai_model_validated=p.origin=='AI')
                candidate=Signal(Origin(p.origin),Side(p.side),close_ms,
                                 'paper-dca:'+p.trade_id)
                allow=admit_adjustment(candidate,local,
                    position_side=Side(p.side),dca_count=p.dca_count)
                if allow.accepted:
                    pending[p.trade_id]=dict(kind='DCA',origin=p.origin,side=p.side,
                        trade_id=p.trade_id,margin=stake,expected=row['close'],
                        candle_time=row['open_time'],confirmed_ms=close_ms,
                        decision_ms=close_ms)
                else:
                    denied+=1;dca_denied+=1
                p.dca_disabled=True
            elif i-p.dca_window_start==1:
                p.dca_disabled=True

        core=core_signal(row) if mode in ('CORE_ONLY','DUAL') else None
        forecast=forecasts.get(row['open_time']) if mode in ('AI_ONLY','DUAL') else None
        ai=_source_signal(row['open_time'],forecast,model_identifier,dataset_sha256)
        candidate=_select(core,ai,close_ms)
        if candidate.reason=='SOURCE_CONFLICT':
            conflicts+=1
        if candidate.action!='SELECTED':
            continue
        if mode=='DUAL' and candidate.selected.origin==Origin.AI and sum(
                p.origin=='AI' for p in positions.values())>=policy.ai_slots_in_dual:
            ai_denials+=1;denied+=1
            continue
        margin=marked*policy.entry_margin_pct
        if margin<=0:
            denied+=1;collateral_denials+=1;continue
        snapshot,current_eq=risk_candidate(candidate.selected.origin,margin,row['close'])
        admission=admit(candidate.selected,snapshot)
        if not admission.accepted:
            denied+=1
            if admission.reason=='POSITION_LIMIT':limit_denials+=1
            else:collateral_denials+=1
            continue
        if positions and any(p.side!=candidate.selected.side.value for p in positions.values()):
            side_denials+=1;denied+=1;continue
        trade_id=f'{mode}:{candidate.selected.signal_id}'
        if trade_id in positions or trade_id in pending:
            denied+=1;continue
        pending[trade_id]=dict(kind='LONG ENTRY' if candidate.selected.side==Side.LONG else 'SHORT ENTRY',
            origin=candidate.selected.origin.value,
            side=candidate.selected.side.value,trade_id=trade_id,
            margin=margin,expected=row['close'],candle_time=row['open_time'],
            decision_ms=close_ms,confirmed_ms=close_ms)
    report=dict(mode=mode,exchange='okx',symbol='BTC/USDT:USDT',days=180,
        dataset_sha256=dataset_sha256,detail_sha256=detail_sha256,
        starting_capital_usdt=cap,equity_mtm_ex_funding_usdt=equity_curve[-1]['equity_mtm_ex_funding_usdt'],
        realized_gross_pnl_usdt=realized,fees_usdt=fees,
        realized_net_ex_funding_usdt=realized-fees,
        max_drawdown_ex_funding_usdt=max(row['drawdown_usdt'] for row in equity_curve),
        trade_count_closed=len(trades),trade_count_open=len(positions),
        max_concurrent_positions=max_concurrent,
        max_positions=policy.max_positions,entry_margin_pct=policy.entry_margin_pct,
        max_total_margin_pct=policy.max_total_margin_pct,
        ai_slots_in_dual=policy.ai_slots_in_dual,
        source_conflicts=conflicts,risk_denials=denied,
        position_limit_denials=limit_denials,ai_source_slot_denials=ai_denials,
        collateral_denials=collateral_denials,opposite_side_denials=side_denials,
        dca_requests=dca_requests,dca_risk_denials=dca_denied,
        dca_filled=sum(x['kind']=='DCA' for x in events),
        unfilled_pending_order_count=len(pending),
        funding_mark_full_coverage_verified=False,liquidation_verified=False,
        exchange_fills_verified=False,freqai_oos_verified=False,
        native_trade_parity_verified=False,full_core_parity_certified=False,
        native_orders_enabled=False,live_orders_enabled=False,
        ready_for_360=False,
        simulator_scope='VIRTUAL_3_SLOTS_SAME_SIDE_PAPER_ONLY',
        fill_model='NEXT_5M_OPEN_5BPS_OR_INTRABAR_STOP')
    return dict(report=report,events=events,trades=trades,equity_curve=equity_curve)


def run_portfolio_180(input_dir,predictions_path,native_report_path,outdir,
                      model_identifier='chart-pro-okx-shadow-v1'):
    """Run only with 180d verified raw OKX candles and native prediction SHA."""
    root=Path(input_dir)
    checked=audit_history(root/'15m.csv',root/'1h.csv',root/'5m.csv',
                          days=180,detail_minutes=5)
    training_window(root/'15m.csv',root/'1h.csv',days=180,warmup_days=35)
    manifest=json.loads((root/'native-export-report.json').read_text())
    claims=dict(exchange='okx',symbol='BTC/USDT:USDT',
                marketType='USDT_PERPETUAL',
                dataset_sha256=checked['dataset_sha256'],
                detail_sha256=checked['detail_sha256'])
    import hashlib
    digest='sha256:'+hashlib.sha256(json.dumps(
        claims,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    if any(manifest.get(k)!=v for k,v in claims.items()) or (
        manifest.get('provenance_sha256')!=digest or not manifest.get('ohlcv_verified')):
        raise ValueError('PORTFOLIO_DATASET_PROVENANCE_MISMATCH')
    native_sha=verify_native_prediction_evidence(predictions_path,native_report_path,
        checked['dataset_sha256'],checked['detail_sha256'],model_identifier)
    context=closed_context(
        read_closed_csv(root/'15m.csv',M15_MS),read_closed_csv(root/'1h.csv',3600000))
    start,end=checked['start_ms'],checked['end_ms']
    candles=[r for r in context if start<=r['open_time']<end]
    detail=[r for r in read_closed_csv(root/'5m.csv',300000)
            if start<=r['open_time']<end]
    with Path(predictions_path).open(newline='',encoding='utf8') as f:
        forecasts=list(csv.DictReader(f))
    out=Path(outdir)
    out.mkdir(parents=True,exist_ok=True)
    summary=dict(schemaVersion=1,phase='PHASE9_180_PAPER_ONLY',
        exchange='okx',dataset_sha256=checked['dataset_sha256'],
        detail_sha256=checked['detail_sha256'],prediction_capture_sha256=native_sha,
        max_positions=3,entry_margin_pct=.10,max_total_margin_pct=.60,
        ai_slots_in_dual=2,full_core_parity_certified=False,
        ready_for_360=False,live_orders_enabled=False,
        funding_mark_full_coverage_verified=False,exchange_fills_verified=False)
    for mode in ('CORE_ONLY','AI_ONLY','DUAL'):
        result=replay_portfolio(candles,detail,forecasts,mode=mode,
            dataset_sha256=checked['dataset_sha256'],
            detail_sha256=checked['detail_sha256'],model_identifier=model_identifier)
        summary[mode]=result['report']
        stem='portfolio-'+mode.lower().replace('_','-')
        for kind,rows,fields in (
            ('events',result['events'],EVENT_FIELDS),
            ('trades',result['trades'],TRADE_FIELDS),
            ('equity',result['equity_curve'],tuple(result['equity_curve'][0]))):
            path=out/(stem+'-'+kind+'.csv')
            with path.open('w',newline='',encoding='utf8') as f:
                writer=csv.DictWriter(f,fieldnames=fields)
                writer.writeheader();writer.writerows(rows)
        (out/(stem+'-report.json')).write_text(
            json.dumps(result['report'],sort_keys=True,indent=2,allow_nan=False))
    (out/'portfolio-180-summary.json').write_text(
        json.dumps(summary,sort_keys=True,indent=2,allow_nan=False))
    return summary

def main():
    p=argparse.ArgumentParser(description='Experimental 3-position 10%%-equity paper portfolio')
    p.add_argument('--dataset-dir',required=True)
    p.add_argument('--predictions',required=True)
    p.add_argument('--native-report',required=True)
    p.add_argument('--out-dir',required=True)
    a=p.parse_args()
    report=run_portfolio_180(a.dataset_dir,a.predictions,a.native_report,a.out_dir)
    print(json.dumps({k:report[k] for k in ('phase','max_positions',
                                            'entry_margin_pct','ready_for_360')},
                     sort_keys=True))
    return 0

if __name__=='__main__':
    raise SystemExit(main())
