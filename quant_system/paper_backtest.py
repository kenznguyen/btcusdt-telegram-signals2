"""Deterministic, OFFLINE CORE / FreqAI paper replay with OHLCV detail fills.

No exchange client, broker, Freqtrade native entries, or simulated order book.
Uses existing StrategyRules + CORE signal and Shared Risk admit/_select. Native
FreqAI predictions are research artifacts, NOT proven live predictions.
"""
from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path

from freqtrade_parity.dataset_io import read_closed_csv
from freqtrade_parity.indicators import indicator_series
from freqtrade_parity.rules import StrategyRules
from quant_system.dual_strategy import (
    Origin, Side, Signal, RiskSnapshot, admit, admit_adjustment, core_signal, _select,
)
from quant_system.intrabar_audit import audit_history
from quant_system.native_dataset import training_window

M15_MS = 900_000
H1_MS = 3_600_000
AI_THRESHOLD = 0.002  # Existing dual-strategy AI trigger, NOT a new CORE threshold.
MODES = ('CORE_ONLY', 'AI_ONLY', 'DUAL')
FILL_SOURCE = 'SIMULATED_OHLCV_5M'
EVENT_FIELDS = ('event_id', 'kind', 'origin', 'side', 'trade_id', 'candle_time',
    'decision_at_ms', 'confirmed_at_ms', 'filled_at_ms', 'expected_fill_price',
    'actual_fill_price', 'fill_difference', 'fill_source', 'quantity_base',
    'margin_usdt', 'fee_usdt', 'dataset_sha256', 'detail_sha256')
TRADE_FIELDS = ('trade_id', 'origin', 'side', 'entry_at_ms', 'exit_at_ms',
    'entry_price', 'exit_price', 'exit_reason', 'dca_count', 'margin_usdt',
    'gross_pnl_usdt', 'fees_usdt', 'net_pnl_ex_funding_usdt', 'roe_percent')
EQUITY_FIELDS = ('candle_close_ms', 'equity_mtm_ex_funding_usdt',
                 'unrealized_usdt', 'drawdown_usdt', 'open_position')


def _finite(value, what):
    if isinstance(value, bool):
        raise ValueError('INVALID_'+what)
    try:
        value = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError('INVALID_'+what) from exc
    if not math.isfinite(value):
        raise ValueError('INVALID_'+what)
    return value


def _sha(value):
    if not isinstance(value, str) or len(value) != 71 or not value.startswith('sha256:') or any(
        char not in '0123456789abcdef' for char in value[7:]
    ):
        raise ValueError('UNVERIFIED_DATASET_SHA256')
    return value


def _same_price(a, b):
    return math.isclose(float(a), float(b), rel_tol=1e-10, abs_tol=1e-8)


def validated_native_predictions(rows, candle_lookup, model_identifier):
    """Require real source-tagged FreqAI output matched to raw OKX M15 candles.

    This is **research provenance**, not an independent model OOS certificate.
    do_predict=0 is a rejection/abstention, never silently becomes a trade.
    """
    if not isinstance(model_identifier, str) or not model_identifier.strip():
        raise ValueError('MISSING_FREQAI_MODEL_IDENTIFIER')
    accepted = {}
    seen = {}
    for record in rows:
        if not isinstance(record, dict):
            raise ValueError('INVALID_NATIVE_FREQAI_ROW')
        try:
            opened = int(record['open_time'])
            if str(record['open_time']) != str(opened) or opened % M15_MS:
                raise ValueError('INVALID_FREQAI_TIME')
            if record.get('source') != 'freqai-native-backtest' or record.get('pair') != 'BTC/USDT:USDT':
                raise ValueError('WRONG_FREQAI_PREDICTION_ORIGIN')
            if record.get('model_identifier') != model_identifier:
                raise ValueError('WRONG_FREQAI_MODEL')
            raw = candle_lookup.get(opened)
            if raw is None:
                # Native FreqAI can include training/warmup rows. Never turn
                # them into historical decisions outside the audited period.
                continue
            for name in ('open', 'high', 'low', 'close', 'volume'):
                if not _same_price(_finite(record[name], 'FREQAI_OHLCV'),raw[name]):
                    raise ValueError('FREQAI_MARKET_DATA_MISMATCH')
            flag = str(record['do_predict'])
            if flag not in ('-2','-1','0','1'):
                raise ValueError('INVALID_FREQAI_DO_PREDICT')
            if flag != '1':
                if opened in seen and seen[opened] != ('REJECTED',):
                    raise ValueError('CONFLICTING_FREQAI_PREDICTIONS')
                seen[opened] = ('REJECTED',)
                continue
            forecast = _finite(record['predicted_return'], 'FREQAI_FORECAST')
            if opened in seen and seen[opened] != ('ACCEPTED', forecast):
                raise ValueError('CONFLICTING_FREQAI_PREDICTIONS')
            seen[opened] = ('ACCEPTED', forecast)
            if abs(forecast) > 10:
                raise ValueError('UNREASONABLE_FREQAI_FORECAST')
            prior = accepted.get(opened)
            if prior is not None and prior != forecast:
                raise ValueError('CONFLICTING_FREQAI_PREDICTIONS')
            accepted[opened] = forecast
        except (KeyError, OverflowError, TypeError) as exc:
            raise ValueError('INVALID_NATIVE_FREQAI_ROW') from exc
    return accepted


def closed_context(m15, h1):
    """Efficient strict previous-closed-H1 join matching kotlin parity module."""
    mi = indicator_series(m15)
    hi = indicator_series(h1)
    indexed=[]
    last_hour=-1
    for i, candle in enumerate(m15):
        bucket=candle['open_time'] - candle['open_time'] % H1_MS
        while last_hour+1 < len(h1) and h1[last_hour+1]['open_time'] < bucket:
            last_hour += 1
        previous = m15[i-1] if i else {}
        prior = mi[i-1] if i else {}
        info = hi[last_hour] if last_hour >= 0 else {}
        indexed.append({**candle,
            'rsi':mi[i]['rsi'], 'adx':mi[i]['adx'],
            'previous_rsi':prior.get('rsi'),
            'previous_open':previous.get('open'),
            'previous_close':previous.get('close'),
            'h1_plus':info.get('plus_di'),
            'h1_minus':info.get('minus_di'),
            'h1_adx':info.get('adx'),
            'h1_source_open_time':h1[last_hour]['open_time'] if last_hour >= 0 else None,
        })
    return indexed


@dataclass
class Position:
    trade_id: str
    origin: str
    side: str
    entry_at_ms: int
    entry_price: float
    quantity: float
    average: float
    margin: float
    entry_fee: float
    dca_count: int = 0
    dca_window_start: int | None = None
    dca_disabled: bool = False


def _source_signal(opened, forecast, model_id, data_sha):
    if forecast is None or abs(forecast) < AI_THRESHOLD:
        return None
    side=Side.LONG if forecast > 0 else Side.SHORT
    end=opened+M15_MS
    raw=f'{data_sha}|{model_id}|{opened}|{forecast:.17g}|{side.value}'
    return Signal(Origin.AI, side, end, 'freqai-paper:'+hashlib.sha256(raw.encode()).hexdigest())


def _snap(equity, required, active, origin):
    return RiskSnapshot(data_fresh=True,state_reconciled=True,
        has_unresolved_reservation=False,active_positions=active,max_positions=1,
        available_margin=max(0.,equity),required_margin=required,
        # Accepted only for *offline research* from an audited native FreqAI
        # trace, never for the production/online FreqAI risk path.
        ai_model_validated=origin == Origin.AI)


def _pnl(position, price):
    return (price-position.average)*position.quantity*(1 if position.side=='LONG' else -1)


def replay_candles(m15, fine, predictions, *, mode, dataset_sha256,
                   detail_sha256, model_identifier, starting_balance=100.):
    """Run a single 1-position research account for one strategy universe.

    Decision: *closed* M15; entry/DCA/TP/soft fill: next detail bar OPEN;
    emergency: first 5m/1m candle touching stop (gap conservative).
    The field actual_fill_price is the **simulated**, NOT exchange actual price.
    """
    if mode not in MODES or not m15 or not fine:
        raise ValueError('INVALID_PAPER_MODE_OR_DATA')
    dataset_sha256, detail_sha256 = _sha(dataset_sha256), _sha(detail_sha256)
    rules=StrategyRules()
    cap=_finite(starting_balance, 'STARTING_CAPITAL')
    if cap <= 0 or cap > 1e6:
        raise ValueError('INVALID_STARTING_CAPITAL')
    start=m15[0]['open_time']
    lookup={c['open_time']:c for c in m15}
    if len(lookup)!=len(m15):
        raise ValueError('DUPLICATE_M15')
    for i, r in enumerate(m15):
        if r.get('closed') is not True or r['open_time'] != start + i*M15_MS:
            raise ValueError('INCOMPLETE_M15_REPLAY')
    stride=M15_MS//(fine[1]['open_time']-fine[0]['open_time']) if len(fine)>1 else 0
    if stride not in (3,15) or len(fine)!=stride*len(m15):
        raise ValueError('INVALID_FINE_CANDLE_RATIO')
    for i, candle in enumerate(fine):
        if candle.get('closed') is not True or candle['open_time'] != start+i*(M15_MS//stride):
            raise ValueError('INCOMPLETE_FINE_REPLAY')
    forecasts=validated_native_predictions(predictions,lookup,model_identifier)
    events, trades, equity_curve=[],[],[]
    account_realized, account_fees = 0.,0.
    pos=None
    pending=None
    peak=cap
    conflicts=denied=dca_denied=dca_requests=0
    used_ids=set()
    last_fill_ms=None

    def emitted(kind, origin, side, trade_id, candle_time, decision_ms, confirmed_ms,
                filled_ms, expected, actual, qty, margin, fee):
        nonlocal last_fill_ms
        event_id=f'{mode}:{trade_id}:{kind}:{filled_ms}:{len(events)}'
        if event_id in used_ids:
            raise ValueError('DUPLICATE_PAPER_EVENT')
        used_ids.add(event_id)
        obj=dict(event_id=event_id,kind=kind,origin=origin,side=side,
                 trade_id=trade_id,candle_time=candle_time,
                 decision_at_ms=decision_ms,confirmed_at_ms=confirmed_ms,
                 filled_at_ms=filled_ms,expected_fill_price=expected,
                 actual_fill_price=actual,fill_difference=actual-expected,
                 fill_source=f'SIMULATED_OHLCV_{M15_MS//stride//60_000}M',
                 quantity_base=qty,margin_usdt=margin,fee_usdt=fee,
                 dataset_sha256=dataset_sha256,detail_sha256=detail_sha256)
        events.append(obj)
        if last_fill_ms is not None and filled_ms < last_fill_ms:
            raise ValueError('REVERSED_PAPER_FILL_TIME')
        last_fill_ms=filled_ms

    def execute_fill(request, candle, *, emergency=False):
        nonlocal pos, pending, account_realized, account_fees
        kind=request['kind']; side=request['side']
        filled_at=candle['open_time']
        expected=request['expected']
        if emergency:
            reference=min(candle['open'],expected) if side=='LONG' else max(candle['open'],expected)
        else:
            reference=candle['open']
        actual=rules.execution_fill(reference, 'BUY' if (kind.endswith('ENTRY') or kind=='DCA') and side=='LONG' or kind in ('TAKE PROFIT','SOFT SL','EMERGENCY SL') and side=='SHORT' else 'SELL')
        if not math.isfinite(actual) or actual<=0:
            raise ValueError('INVALID_PAPER_FILL')
        if kind in ('LONG ENTRY','SHORT ENTRY'):
            if pos is not None:
                raise ValueError('PAPER_OVERLAP')
            margin=request['margin']
            qty=margin*rules.p.leverage/actual
            fee=qty*actual*rules.p.fee_rate
            account_fees+=fee
            pos=Position(request['trade_id'],request['origin'],side,filled_at,actual,qty,actual,margin,fee)
        elif kind=='DCA':
            if pos is None or pos.trade_id!=request['trade_id'] or pos.dca_count:
                raise ValueError('INVALID_DCA_STATE')
            margin=request['margin']
            qty=margin*rules.p.leverage/actual
            fee=qty*actual*rules.p.fee_rate
            account_fees+=fee
            pos.average=(pos.average*pos.quantity+actual*qty)/(pos.quantity+qty)
            pos.quantity+=qty
            pos.margin+=margin
            pos.entry_fee+=fee
            pos.dca_count=1
            pos.dca_disabled=True
        else:
            if pos is None or pos.trade_id!=request['trade_id']:
                raise ValueError('UNMATCHED_EXIT')
            qty=pos.quantity
            margin=pos.margin
            fee=qty*actual*rules.p.fee_rate
            gross=_pnl(pos,actual)
            account_fees+=fee
            account_realized+=gross
            trades.append(dict(trade_id=pos.trade_id,origin=pos.origin,side=pos.side,
                entry_at_ms=pos.entry_at_ms,exit_at_ms=filled_at,
                entry_price=pos.entry_price,exit_price=actual,exit_reason=kind,
                dca_count=pos.dca_count,margin_usdt=pos.margin,
                gross_pnl_usdt=gross,fees_usdt=pos.entry_fee+fee,
                net_pnl_ex_funding_usdt=gross-pos.entry_fee-fee,
                roe_percent=100*gross/pos.margin))
            pos=None
        emitted(kind,request['origin'],side,request['trade_id'],
            request['candle_time'],request['decision_ms'],request['confirmed_ms'],
            filled_at,expected,actual,qty,margin,fee)

    for i,row in enumerate(m15):
        bars=fine[i*stride:(i+1)*stride]
        for j,bar in enumerate(bars):
            # Stop wins over an already queued DCA at the SAME detail candle.
            def stop_request():
                if pos is None:
                    return None
                threshold=rules.threshold_price(pos.side,pos.average,abs(rules.p.emergency_sl_roe))
                if not rules.emergency(pos.side,bar['low'],bar['high'],pos.average):
                    return None
                return dict(kind='EMERGENCY SL',origin=pos.origin,side=pos.side,
                    trade_id=pos.trade_id,margin=pos.margin,expected=threshold,
                    candle_time=row['open_time'],decision_ms=bar['open_time'],
                    confirmed_ms=bar['open_time'])

            if j==0 and pending is not None:
                if pending['kind']=='DCA':
                    emergency_now=stop_request()
                    if emergency_now is not None:
                        pending=None
                        execute_fill(emergency_now,bar,emergency=True)
                        continue
                    if pos is None or pos.dca_count:
                        raise ValueError('PAPER_DCA_OUT_OF_SEQUENCE')
                    free=cap+account_realized-account_fees+_pnl(pos,bar['open'])-pos.margin
                    candidate=Signal(Origin(pos.origin),Side(pos.side),
                        pending['decision_ms'], f"paper-dca:{pos.trade_id}:{pending['decision_ms']}")
                    snapshot=_snap(free,pending['margin'],1,candidate.origin)
                    allowed=admit_adjustment(candidate,snapshot,
                        position_side=Side(pos.side),dca_count=pos.dca_count)
                    if allowed.accepted and free+1e-9>=pending['margin']:
                        execute_fill(pending,bar)
                    else:
                        denied+=1
                        dca_denied+=1
                    pending=None
                else:
                    # A gap THROUGH Emergency SL at the first tradable open
                    # overrides a previously confirmed TP/Soft SL. Otherwise
                    # those confirmed orders fill at the next 5m open before
                    # any unknown intrabar high/low movement.
                    if (pending['kind'] in ('SOFT SL','TAKE PROFIT') and pos is not None):
                        threshold=rules.threshold_price(pos.side,pos.average,
                            abs(rules.p.emergency_sl_roe))
                        gapped = (bar['open']<=threshold if pos.side=='LONG'
                                  else bar['open']>=threshold)
                        if gapped:
                            emergency_now=stop_request()
                            if emergency_now is None:
                                raise ValueError('GAP_STOP_WITHOUT_TRIGGER')
                            pending=None
                            execute_fill(emergency_now,bar,emergency=True)
                            continue
                    execute_fill(pending,bar)
                    pending=None
            emergency_now=stop_request()
            if emergency_now is not None:
                execute_fill(emergency_now,bar,emergency=True)
                pending=None
                continue
        close_ms=row['open_time']+M15_MS
        floating=_pnl(pos,row['close']) if pos is not None else 0.
        equity=cap+account_realized-account_fees+floating
        peak=max(peak,equity)
        equity_curve.append(dict(candle_close_ms=close_ms,
            equity_mtm_ex_funding_usdt=equity,unrealized_usdt=floating,
            drawdown_usdt=peak-equity,open_position=pos is not None))
        if pos is not None:
            # Emergency already checked on all finer candles. M15 close is
            # needed for Soft SL, Take Profit and any DCA signal.
            keys=('rsi','previous_open','previous_close','h1_plus','h1_minus','h1_adx')
            if any(row.get(k) is None for k in keys):
                continue
            soft=rules.soft(pos.side,row['low'],row['high'],row['open'],row['close'],
                row['previous_open'],row['previous_close'],row['h1_plus'],row['h1_minus'],
                row['h1_adx'],pos.average)
            tp=rules.tp(pos.side,row['rsi'],rules.roe(pos.side,pos.average,row['close']))
            kind=rules.exit_priority(False,soft,tp)
            if kind is not None:
                pending=dict(kind=kind,origin=pos.origin,side=pos.side,trade_id=pos.trade_id,
                    expected=row['close'],margin=pos.margin,candle_time=row['open_time'],
                    confirmed_ms=close_ms,decision_ms=close_ms)
                continue
            if pos.dca_disabled or pos.dca_count:
                continue
            roe=rules.roe(pos.side,pos.average,row['close'])
            if pos.dca_window_start is None and roe<=rules.p.dca_roe:
                pos.dca_window_start=i
            if pos.dca_window_start is None:
                continue
            if i-pos.dca_window_start>=2:
                pos.dca_disabled=True
                continue
            if (row.get('adx') is not None and row.get('previous_rsi') is not None and
                rules.dca(pos.side,roe,row['adx'],row['rsi'],row['previous_rsi'])):
                stake=pos.margin*rules.p.dca_margin_ratio
                if stake>0:
                    dca_requests+=1
                    free=equity-pos.margin
                    request=Signal(Origin(pos.origin),Side(pos.side),close_ms,
                        f"paper-dca:{pos.trade_id}:{close_ms}")
                    allowance=admit_adjustment(request,
                        _snap(free,stake,1,request.origin),
                        position_side=Side(pos.side),dca_count=pos.dca_count)
                    if allowance.accepted:
                        pending=dict(kind='DCA',origin=pos.origin,side=pos.side,
                            trade_id=pos.trade_id,margin=stake,expected=row['close'],
                            candle_time=row['open_time'],decision_ms=close_ms,
                            confirmed_ms=close_ms)
                    else:
                        denied+=1
                        dca_denied+=1
                    pos.dca_disabled=True
            elif i-pos.dca_window_start==1:
                pos.dca_disabled=True
            continue
        # Enqueue a new trade only when no earlier order/position is active.
        if pending is not None:
            continue
        core=core_signal(row) if mode in ('CORE_ONLY','DUAL') else None
        forecast=forecasts.get(row['open_time']) if mode in ('AI_ONLY','DUAL') else None
        ai=_source_signal(row['open_time'],forecast,model_identifier,dataset_sha256)
        candidate=_select(core,ai,close_ms)
        if candidate.reason=='SOURCE_CONFLICT':
            conflicts+=1
        if candidate.action!='SELECTED':
            continue
        margin=max(0.,equity)*rules.p.entry_margin_pct
        risk=_snap(equity,margin,0,candidate.selected.origin)
        allow=admit(candidate.selected,risk)
        if not allow.accepted or margin<=0 or margin>equity:
            denied+=1
            continue
        side=candidate.selected.side.value
        trade_id=f'{mode}:{candidate.selected.signal_id}'
        pending=dict(kind='LONG ENTRY' if side=='LONG' else 'SHORT ENTRY',
            origin=candidate.selected.origin.value,side=side,
            trade_id=trade_id,margin=margin,expected=row['close'],
            candle_time=row['open_time'],confirmed_ms=close_ms,decision_ms=close_ms)

    closing_equity=equity_curve[-1]['equity_mtm_ex_funding_usdt']
    reported={
        'mode':mode,'exchange':'okx','symbol':'BTC/USDT:USDT','days':None,
        'dataset_sha256':dataset_sha256,'detail_sha256':detail_sha256,
        'starting_capital_usdt':cap,'equity_mtm_ex_funding_usdt':closing_equity,
        'realized_gross_pnl_usdt':account_realized,'fees_usdt':account_fees,
        'realized_net_ex_funding_usdt':account_realized-account_fees,
        'max_drawdown_ex_funding_usdt':max(x['drawdown_usdt'] for x in equity_curve),
        'trade_count_closed':len(trades),'trade_count_open':int(pos is not None),
        'source_conflicts':conflicts,'risk_denials':denied,
        'dca_requests':dca_requests,'dca_risk_denials':dca_denied,
        'dca_filled':sum(e['kind']=='DCA' for e in events),
        'ai_prediction_count':len(forecasts),
        'unfilled_pending_order_count':int(pending is not None),
        'funding_mark_full_coverage_verified':False,
        'liquidation_verified':False,'exchange_fills_verified':False,
        'freqai_oos_verified':False,'native_trade_parity_verified':False,
        'full_core_parity_certified':False,'native_orders_enabled':False,
        'fill_model':f'NEXT_{M15_MS//stride//60_000}M_OPEN_5BPS_OR_INTRABAR_STOP',
        'ai_provenance_scope':'NATIVE_RESEARCH_ONLY_NOT_MODEL_OOS_ATTESTATION',
    }
    return {'report':reported,'events':events,'trades':trades,'equity_curve':equity_curve}


def write_paper_outputs(directory,result,mode):
    target=Path(directory)
    target.mkdir(parents=True,exist_ok=True)
    if mode not in MODES or result['report']['mode']!=mode:
        raise ValueError('REPORT_MODE_MISMATCH')
    slug=mode.lower().replace('_','-')
    result_paths={}
    for name,rows,fields in [('events',result['events'],EVENT_FIELDS),
                             ('trades',result['trades'],TRADE_FIELDS),
                             ('equity',result['equity_curve'],EQUITY_FIELDS)]:
        path=target/f'paper-{slug}-{name}.csv'
        with path.open('w',newline='',encoding='utf-8') as source:
            writer=csv.DictWriter(source,fieldnames=fields,extrasaction='raise')
            writer.writeheader()
            writer.writerows(rows)
        result_paths[name]=str(path)
    path=target/f'paper-{slug}-report.json'
    path.write_text(json.dumps(result['report'],indent=2,sort_keys=True,allow_nan=False),encoding='utf-8')
    result_paths['report']=str(path)
    return result_paths


def verify_native_prediction_evidence(predictions_path, native_report_path,
                                     dataset_sha256, detail_sha256, model_identifier):
    """Require a successful FreqAI native report and checksum-matched CSV."""
    if native_report_path is None:
        raise ValueError('MISSING_NATIVE_FREQAI_PROVENANCE')
    captured=Path(predictions_path)
    reportfile=Path(native_report_path)
    if not captured.is_file() or not reportfile.is_file():
        raise ValueError('MISSING_NATIVE_FREQAI_PROVENANCE')
    report=json.loads(reportfile.read_text(encoding='utf-8'))
    expected='sha256:'+hashlib.sha256(captured.read_bytes()).hexdigest()
    if (report.get('exchange')!='okx' or report.get('days')!=180 or
        report.get('detail_timeframe')!='5m' or
        report.get('dataset_sha256')!=dataset_sha256 or
        report.get('detail_sha256')!=detail_sha256 or
        report.get('core_native_runtime_succeeded') is not True or
        report.get('freqai_native_runtime_succeeded') is not True or
        report.get('prediction_capture_verified') is not True or
        report.get('prediction_model_identifier')!=model_identifier or
        report.get('prediction_capture_sha256')!=expected or
        type(report.get('prediction_capture_accepted')) is not int or
        report['prediction_capture_accepted']<=0):
        raise ValueError('INVALID_NATIVE_FREQAI_PROVENANCE')
    return expected


def run_180(input_dir,predictions_path,outdir,*,native_report_path=None,
            detail_minutes=5,expected_model='chart-pro-okx-shadow-v1'):
    """Strict 180-day gate. 360-day execution is intentionally NOT enabled."""
    if detail_minutes!=5:
        raise ValueError('PAPER_5M_ONLY_UNTIL_INTRABAR_VALIDATION')
    root=Path(input_dir)
    m15_path,h1_path,fine_path=(root/'15m.csv',root/'1h.csv',root/'5m.csv')
    checked=audit_history(m15_path,h1_path,fine_path,days=180,detail_minutes=5)
    training_window(m15_path,h1_path,days=180,warmup_days=35)
    manifest=json.loads((root/'native-export-report.json').read_text())
    import hashlib
    claims=dict(exchange='okx',symbol='BTC/USDT:USDT',marketType='USDT_PERPETUAL',
        dataset_sha256=checked['dataset_sha256'],detail_sha256=checked['detail_sha256'])
    lineage='sha256:'+hashlib.sha256(json.dumps(claims,sort_keys=True,
        separators=(',',':')).encode()).hexdigest()
    if any(manifest.get(k)!=v for k,v in claims.items()) or (
        manifest.get('provenance_sha256')!=lineage or not manifest.get('ohlcv_verified')
    ):
        raise ValueError('PAPER_DATASET_PROVENANCE_MISMATCH')
    all_m15=read_closed_csv(m15_path,M15_MS)
    all_h1=read_closed_csv(h1_path,H1_MS)
    context=closed_context(all_m15,all_h1)
    start,end=checked['start_ms'],checked['end_ms']
    m15=[x for x in context if start<=x['open_time']<end]
    fine=[x for x in read_closed_csv(fine_path,300_000) if start<=x['open_time']<end]
    prediction_sha=verify_native_prediction_evidence(predictions_path,native_report_path,
        checked['dataset_sha256'],checked['detail_sha256'],expected_model)
    with Path(predictions_path).open(newline='',encoding='utf-8') as handle:
        raw_preds=list(csv.DictReader(handle))
    if not raw_preds:
        raise ValueError('NO_REAL_FREQAI_NATIVE_PREDICTIONS')
    outputs={}
    report=dict(schemaVersion=1,phase='PAPER_180_ONLY',exchange='okx',
        dataset_sha256=checked['dataset_sha256'],detail_sha256=checked['detail_sha256'],
        start_ms=start,end_ms=end,ohlcv_verified=True,
        prediction_capture_sha256=prediction_sha,
        full_core_parity_certified=False,exchange_fills_verified=False,
        funding_mark_full_coverage_verified=False,
        kotlin_trace_verified=False,model_oos_verified=False,
        trading_mode='OFFLINE_RESEARCH_NO_EXCHANGE_ORDERS')
    for mode in MODES:
        result=replay_candles(m15,fine,raw_preds,mode=mode,
            dataset_sha256=checked['dataset_sha256'],
            detail_sha256=checked['detail_sha256'],model_identifier=expected_model)
        result['report']['days']=180
        outputs[mode]=write_paper_outputs(outdir,result,mode)
        report[mode]=result['report']
    report['paper_trade_bearing_verified']=all(
        report[m]['trade_count_closed']>0
        for m in ('CORE_ONLY','AI_ONLY'))
    dest=Path(outdir)/'paper-180-summary.json'
    dest.write_text(json.dumps(report,sort_keys=True,indent=2,allow_nan=False),encoding='utf-8')
    return report


def main():
    p=argparse.ArgumentParser(description='Offline 180d CORE+AI shadow paper replay; NO LIVE ORDERS')
    p.add_argument('--days',required=True,type=int,choices=[180])
    p.add_argument('--dataset-dir',required=True)
    p.add_argument('--predictions',required=True)
    p.add_argument('--native-report',required=True)
    p.add_argument('--out-dir',required=True)
    p.add_argument('--model-identifier',default='chart-pro-okx-shadow-v1')
    args=p.parse_args()
    report=run_180(args.dataset_dir,args.predictions,args.out_dir,
                   native_report_path=args.native_report,
                   expected_model=args.model_identifier)
    print(json.dumps({k:report[k] for k in ('phase','paper_trade_bearing_verified',
        'dataset_sha256','full_core_parity_certified')},sort_keys=True))
    return 0 if report['paper_trade_bearing_verified'] else 2

if __name__=='__main__':
    raise SystemExit(main())