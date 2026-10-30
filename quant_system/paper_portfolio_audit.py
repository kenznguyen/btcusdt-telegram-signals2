"""Independent Phase 9 virtual multi-position audit; no native trade certification."""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

MODES=('CORE_ONLY','AI_ONLY','DUAL')
EXITS=('TAKE PROFIT','SOFT SL','EMERGENCY SL')

class PortfolioAuditError(ValueError):
    pass

def ensure(ok,message):
    if not ok:
        raise PortfolioAuditError(message)

def finite(value):
    try:
        num=float(value)
        ensure(math.isfinite(num), 'INVALID_PORTFOLIO_NUMBER')
        return num
    except (TypeError,ValueError,OverflowError) as exc:
        raise PortfolioAuditError('INVALID_PORTFOLIO_NUMBER') from exc

def close(a,b,atol=1e-6):
    return math.isclose(finite(a),finite(b),rel_tol=1e-8,abs_tol=atol)

def record(path):
    result=json.loads(path.read_text(encoding='utf8'))
    ensure(isinstance(result,dict),'INVALID_PORTFOLIO_JSON')
    return result

def csvfile(path,columns):
    with path.open(newline='',encoding='utf8') as file:
        reader=csv.DictReader(file)
        ensure(reader.fieldnames is not None and len(set(reader.fieldnames))==len(reader.fieldnames)
               and set(columns).issubset(reader.fieldnames),'INVALID_PORTFOLIO_CSV_COLUMNS')
        rows=list(reader)
    ensure(all(None not in row and all(value is not None for value in row.values())
               for row in rows),'MALFORMED_PORTFOLIO_CSV')
    return rows

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024*1024),b''):
            h.update(chunk)
    return 'sha256:'+h.hexdigest()

def audit_mode(folder,mode,summary):
    prefix='portfolio-'+mode.lower().replace('_','-')
    report_path=folder/(prefix+'-report.json')
    report=record(report_path)
    ensure(report==summary[mode],'PORTFOLIO_MODE_REPORT_DIFFERENCE')
    ensure(report.get('mode')==mode and report.get('exchange')=='okx'
        and report.get('days')==180 and
        report.get('dataset_sha256')==summary['dataset_sha256'] and
        report.get('detail_sha256')==summary['detail_sha256'],
        'PORTFOLIO_WRONG_MODE_OR_DATASET')
    ensure(report.get('max_positions')==3 and report.get('entry_margin_pct')==.10
        and .30<=report.get('max_total_margin_pct',0)<=.60
        and report.get('ai_slots_in_dual')==2,'PORTFOLIO_RISK_POLICY_MISMATCH')
    for flag in ('live_orders_enabled','native_orders_enabled',
                 'ready_for_360','full_core_parity_certified',
                 'freqai_oos_verified','exchange_fills_verified',
                 'liquidation_verified'):
        ensure(report.get(flag) is False,'PORTFOLIO_UNSUPPORTED_CERTIFICATION')
    eventfile=folder/(prefix+'-events.csv')
    tradefile=folder/(prefix+'-trades.csv')
    equityfile=folder/(prefix+'-equity.csv')
    events=csvfile(eventfile,('event_id','kind','origin','side','trade_id',
        'decision_at_ms','confirmed_at_ms','filled_at_ms','expected_fill_price',
        'actual_fill_price','fill_difference','fee_usdt','margin_usdt',
        'dataset_sha256','detail_sha256','fill_source'))
    trades=csvfile(tradefile,('trade_id','origin','side','entry_at_ms',
        'exit_at_ms','exit_reason','entry_price','exit_price','dca_count',
        'margin_usdt','gross_pnl_usdt','fees_usdt','net_pnl_ex_funding_usdt'))
    equity=csvfile(equityfile,('candle_close_ms','equity_mtm_ex_funding_usdt',
        'unrealized_usdt','drawdown_usdt','open_position','open_positions',
        'reserved_margin_usdt'))
    ensure(bool(equity),'MISSING_PORTFOLIO_EQUITY')
    equity_by_time={}
    peak=finite(report['starting_capital_usdt'])
    maxdd=0.
    last=-1
    for point in equity:
        ts=int(point['candle_close_ms'])
        ensure(ts>last,'REVERSED_PORTFOLIO_EQUITY')
        last=ts
        equity_by_time[ts]=point
        eq=finite(point['equity_mtm_ex_funding_usdt'])
        peak=max(peak,eq)
        dd=peak-eq
        ensure(close(dd,point['drawdown_usdt']),'PORTFOLIO_DRAWDOWN_MISMATCH')
        maxdd=max(maxdd,dd)
        n=int(point['open_positions'])
        ensure(0<=n<=3 and (point['open_position']=='True')==(n>0),
               'INVALID_PORTFOLIO_EQUITY_POSITION_COUNT')
        ensure(finite(point['reserved_margin_usdt'])>=0,
               'INVALID_PORTFOLIO_RESERVED_MARGIN')
    active={}
    entered={}
    exited={}
    dcas={}
    fees=0.
    last_event=-1
    ids=set()
    for e in events:
        kind=e['kind']
        trade_id=e['trade_id']
        filled=int(e['filled_at_ms'])
        decision=int(e['decision_at_ms'])
        confirm=int(e['confirmed_at_ms'])
        ensure(filled>=last_event and decision<=confirm<=filled,
               'PORTFOLIO_EVENT_TIME_MISMATCH')
        last_event=filled
        ensure(e['event_id'] not in ids and bool(e['event_id']),
               'PORTFOLIO_DUPLICATE_EVENT')
        ids.add(e['event_id'])
        ensure(e['origin'] in ('CORE','AI') and e['side'] in ('LONG','SHORT'),
               'PORTFOLIO_EVENT_ORIGIN_INVALID')
        if mode!='DUAL':
            ensure(e['origin']==('CORE' if mode=='CORE_ONLY' else 'AI'),
                   'PORTFOLIO_EVENT_WRONG_SOURCE')
        ensure(e['dataset_sha256']==summary['dataset_sha256']
               and e['detail_sha256']==summary['detail_sha256']
               and e['fill_source']=='SIMULATED_OHLCV_5M',
               'PORTFOLIO_UNVERIFIED_FILL')
        ensure(close(finite(e['actual_fill_price'])-finite(e['expected_fill_price']),
                     e['fill_difference']),'PORTFOLIO_FILL_DIFFERENCE_MISMATCH')
        fee=finite(e['fee_usdt'])
        ensure(fee>=0 and finite(e['margin_usdt'])>0,'INVALID_PORTFOLIO_FEES_OR_MARGIN')
        fees+=fee
        if kind in ('LONG ENTRY','SHORT ENTRY'):
            ensure(trade_id not in entered and len(active)<3,
                   'PORTFOLIO_OVERLAPPING_OR_DUPLICATE_ENTRY')
            ensure(e['side']==kind.split()[0] and
                   not any(x['side']!=e['side'] for x in active.values()),
                   'PORTFOLIO_OPPOSITE_SIDES')
            if mode=='DUAL' and e['origin']=='AI':
                ensure(sum(x['origin']=='AI' for x in active.values())<2,
                       'PORTFOLIO_AI_SLOT_VIOLATION')
            snapshot=equity_by_time.get(decision)
            ensure(snapshot is not None and
                   close(finite(snapshot['equity_mtm_ex_funding_usdt'])*.10,
                         e['margin_usdt']),
                   'ENTRY_NOT_TEN_PERCENT_EQUITY')
            active[trade_id]=e
            entered[trade_id]=e
            dcas[trade_id]=0
        elif kind=='DCA':
            ensure(trade_id in active and dcas.get(trade_id)==0 and
                   active[trade_id]['side']==e['side'] and
                   active[trade_id]['origin']==e['origin'] and
                   close(e['margin_usdt'],active[trade_id]['margin_usdt']),
                   'PORTFOLIO_INVALID_DCA')
            dcas[trade_id]=1
        elif kind in EXITS:
            ensure(trade_id in active and trade_id not in exited and
                   active[trade_id]['origin']==e['origin'] and
                   active[trade_id]['side']==e['side'],
                   'PORTFOLIO_INVALID_EXIT')
            exited[trade_id]=e
            del active[trade_id]
        else:
            raise PortfolioAuditError('UNKNOWN_PORTFOLIO_EVENT_KIND')
    ensure(len(trades)==len(exited)==report.get('trade_count_closed') and
           len(active)==report.get('trade_count_open') and
           len(active)<=3,'PORTFOLIO_TRADE_COUNT_MISMATCH')
    ensure(sum(dcas.values())==report.get('dca_filled') and
           report.get('dca_requests',-1)>=sum(dcas.values())+
              report.get('dca_risk_denials',-1),
           'PORTFOLIO_DCA_COUNT_MISMATCH')
    ensure(close(fees,report['fees_usdt']),'PORTFOLIO_FEE_ACCOUNTING_MISMATCH')
    gross=0.
    verified=set()
    for t in trades:
        k=t['trade_id']
        ensure(k in exited and k not in verified,'PORTFOLIO_PHANTOM_TRADE')
        verified.add(k)
        entry=entered[k]
        leave=exited[k]
        ensure(t['origin']==entry['origin'] and t['side']==entry['side'] and
               t['exit_reason']==leave['kind'] and
               close(t['entry_at_ms'],entry['filled_at_ms']) and
               close(t['exit_at_ms'],leave['filled_at_ms']) and
               close(t['entry_price'],entry['actual_fill_price']) and
               close(t['exit_price'],leave['actual_fill_price']) and
               int(t['dca_count'])==dcas[k],'PORTFOLIO_TRADE_EVENT_MISMATCH')
        g=finite(t['gross_pnl_usdt'])
        gross+=g
        ensure(close(g-finite(t['fees_usdt']),t['net_pnl_ex_funding_usdt']),
               'PORTFOLIO_TRADE_PNL_MISMATCH')
    ensure(close(gross,report['realized_gross_pnl_usdt']) and
           close(gross-fees,report['realized_net_ex_funding_usdt']) and
           close(maxdd,report['max_drawdown_ex_funding_usdt']) and
           close(equity[-1]['equity_mtm_ex_funding_usdt'],
                 report['equity_mtm_ex_funding_usdt']),
           'PORTFOLIO_REPORT_ACCOUNTING_MISMATCH')
    ensure(int(equity[-1]['open_positions'])==len(active) and
           close(equity[-1]['reserved_margin_usdt'],
                 sum(finite(entered[k]['margin_usdt'])*(1+dcas[k]) for k in active)),
           'PORTFOLIO_FINAL_RESERVED_MARGIN_MISMATCH')
    return dict(closed_trades=len(exited),open_trades=len(active),
                filled_dcas=sum(dcas.values()),events=len(events),
                max_drawdown_usdt=maxdd,sha256={
                    path.name:sha(path) for path in
                    (report_path,eventfile,tradefile,equityfile)})


def audit_portfolio(folder,native_report,predictions_path):
    output=dict(schemaVersion=1,audit='PHASE9_3_POSITION_10PCT_PAPER',
        paper_portfolio_integrity_verified=False,
        full_core_parity_certified=False,live_orders_enabled=False,
        ready_for_360=False,errors=[],modes={},artifact_sha256={})
    try:
        directory=Path(folder)
        summary_path=directory/'portfolio-180-summary.json'
        summary=record(summary_path)
        ensure(summary.get('phase')=='PHASE9_180_PAPER_ONLY' and
               summary.get('exchange')=='okx' and
               summary.get('max_positions')==3 and
               summary.get('entry_margin_pct')==.10 and
               summary.get('max_total_margin_pct')==.60 and
               summary.get('ai_slots_in_dual')==2 and
               summary.get('full_core_parity_certified') is False and
               summary.get('ready_for_360') is False and
               summary.get('live_orders_enabled') is False,
               'INVALID_PORTFOLIO_SUMMARY')
        native=record(Path(native_report))
        ensure(native.get('freqai_native_runtime_succeeded') is True and
               native.get('core_native_runtime_succeeded') is True and
               native.get('dataset_sha256')==summary.get('dataset_sha256') and
               native.get('detail_sha256')==summary.get('detail_sha256') and
               native.get('prediction_capture_sha256')==
                  summary.get('prediction_capture_sha256')==sha(Path(predictions_path)),
               'PORTFOLIO_NATIVE_DATASET_OR_PREDICTION_SHA')
        for mode in MODES:
            output['modes'][mode]=audit_mode(directory,mode,summary)
        output['artifact_sha256'][summary_path.name]=sha(summary_path)
        for mode in MODES:
            output['artifact_sha256'].update(output['modes'][mode]['sha256'])
        output['paper_portfolio_integrity_verified']=True
    except PortfolioAuditError as exc:
        output['errors'].append(str(exc))
    except (OSError,UnicodeError,ValueError,TypeError,KeyError,OverflowError,csv.Error) as exc:
        output['errors'].append('PORTFOLIO_EVIDENCE_MISSING_OR_MALFORMED')
        output['error_type']=type(exc).__name__
    return output

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--paper-dir',required=True)
    parser.add_argument('--native-report',required=True)
    parser.add_argument('--predictions',required=True)
    parser.add_argument('--out',required=True)
    args=parser.parse_args()
    result=audit_portfolio(args.paper_dir,args.native_report,args.predictions)
    target=Path(args.out)
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(result,sort_keys=True,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:result[k] for k in
        ('paper_portfolio_integrity_verified','ready_for_360','errors')}))
    return 0 if result['paper_portfolio_integrity_verified'] else 2

if __name__=='__main__':
    raise SystemExit(main())
