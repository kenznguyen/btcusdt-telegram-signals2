"""Phase 11: SHA-bound evidence for previously unexplained CORE/AI conflicts.

Read-only. Never changes position routing, exchange orders, CORE thresholds,
portfolio sizing, model validation, or OOS certification.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

M15_MS=900000
AI_THRESHOLD=.002
RECLASSIFIED='SAME_CANDLE_CORE_AI_SOURCE_CONFLICT'

class EvidenceError(ValueError):
    pass

def require(ok,reason):
    if not ok:
        raise EvidenceError(reason)

def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024*1024),b''):
            h.update(block)
    return 'sha256:'+h.hexdigest()

def json_file(path):
    x=json.loads(Path(path).read_text(encoding='utf8'))
    require(isinstance(x,dict),'INVALID_JSON_EVIDENCE')
    return x

def csv_rows(path,required):
    with Path(path).open(newline='',encoding='utf8') as f:
        reader=csv.DictReader(f)
        require(reader.fieldnames is not None and
                len(set(reader.fieldnames))==len(reader.fieldnames) and
                set(required).issubset(reader.fieldnames),
                'INVALID_EVIDENCE_CSV_COLUMNS')
        rows=list(reader)
    require(all(None not in row and all(v is not None for v in row.values())
                for row in rows),'INVALID_EVIDENCE_CSV_ROW')
    return rows

def stamp(value):
    try:
        value=int(value)
        require(value>0 and value%M15_MS==0,'INVALID_CANDLE_TIMESTAMP')
        return value
    except (TypeError,ValueError,OverflowError) as exc:
        raise EvidenceError('INVALID_CANDLE_TIMESTAMP') from exc

def price(value):
    try:
        value=float(value)
        require(math.isfinite(value),'INVALID_MARKET_NUMBER')
        return value
    except (TypeError,ValueError,OverflowError) as exc:
        raise EvidenceError('INVALID_MARKET_NUMBER') from exc

def audit_conflicts(paper_dir,predictions,native_report,canonical_m15):
    result=dict(schemaVersion=1,audit='PHASE11_SHA_BOUND_SOURCE_CONFLICT_RECONCILIATION',
        source_conflict_reconciliation_verified=False,ready_for_360=False,
        full_core_parity_certified=False,live_orders_enabled=False,
        oos_certified=False,ai_promotion_eligible=False,errors=[],
        interpretation=('Only previously unexplained filled CORE_ONLY entry '
            'timestamps are checked against actual SHA-pinned native FreqAI '
            'predictions at the same closed M15 signal. No alternate trading '
            'policy, hedging or counterfactual PnL is inferred.'),
        blockers=['TRAINING_LABEL_PURGE_NOT_INDEPENDENTLY_VERIFIED',
                  'NATIVE_MULTIPOSITION_TRADE_PARITY_MISSING',
                  'FUNDING_MARK_LIQUIDATION_NOT_FULLY_VERIFIED'])
    details=[]
    try:
        paper=Path(paper_dir)
        phase10=json_file(paper/'portfolio-180-source-contention.json')
        require(phase10.get('contention_audit_verified') is True and
                phase10.get('errors')==[] and
                phase10.get('ready_for_360') is False and
                phase10.get('oos_certified') is False and
                phase10.get('live_orders_enabled') is False,
                'UPSTREAM_PHASE10_NOT_VERIFIED')
        detailpath=paper/'portfolio-180-core-opportunity-attribution.csv'
        require(digest(detailpath)==phase10.get('details_csv_sha256'),
                'PHASE10_DETAILS_SHA_MISMATCH')
        phase9_audit=paper/'portfolio-180-independent-audit.json'
        phase9_summary=paper/'portfolio-180-summary.json'
        require(digest(phase9_audit)==phase10.get('phase9_audit_sha256') and
                digest(phase9_summary)==phase10.get('phase9_summary_sha256'),
                'PHASE9_SHA_MISMATCH')
        independent=json_file(phase9_audit)
        require(independent.get('paper_portfolio_integrity_verified') is True and
                independent.get('errors')==[],
                'UPSTREAM_PHASE9_NOT_VERIFIED')
        summary=json_file(phase9_summary)
        native=json_file(native_report)
        require(native.get('core_native_runtime_succeeded') is True and
                native.get('freqai_native_runtime_succeeded') is True and
                native.get('prediction_capture_verified') is True and
                native.get('freqai_oos_verified') is False and
                native.get('full_core_parity_certified') is False and
                summary.get('dataset_sha256')==native.get('dataset_sha256') and
                summary.get('detail_sha256')==native.get('detail_sha256'),
                'UNTRUSTED_NATIVE_RESEARCH_SOURCE')
        expected=digest(predictions)
        require(native.get('prediction_capture_sha256')==expected and
                summary.get('prediction_capture_sha256')==expected,
                'NATIVE_FORECAST_SHA_MISMATCH')
        model=native.get('prediction_model_identifier')
        require(isinstance(model,str) and bool(model),'MISSING_MODEL_IDENTIFIER')
        unresolved=csv_rows(detailpath,(
            'core_decision_at_ms','core_side','category','occupied_positions'))
        missing=[row for row in unresolved if
                 row['category']=='unexplained_without_active_obstruction']
        require(len(missing)==phase10.get('unexplained_without_active_obstruction'),
                'PHASE10_UNEXPLAINED_COUNT_MISMATCH')
        forecasts=csv_rows(predictions,(
            'open_time','open','high','low','close','volume',
            'do_predict','predicted_return','model_identifier','source','pair'))
        allcandles=csv_rows(canonical_m15,(
            'open_time','open','high','low','close','volume'))
        wanted={stamp(row['core_decision_at_ms'])-M15_MS for row in missing}
        pred_by_time={}
        raw_by_time={}
        for row in forecasts:
            t=stamp(row['open_time'])
            if t in wanted:
                require(t not in pred_by_time,'DUPLICATE_FREQAI_CANDLE')
                pred_by_time[t]=row
        for row in allcandles:
            t=stamp(row['open_time'])
            if t in wanted:
                require(t not in raw_by_time,'DUPLICATE_CANONICAL_CANDLE')
                raw_by_time[t]=row
        reclassified=0
        for row in missing:
            end=stamp(row['core_decision_at_ms'])
            opened=end-M15_MS
            side=row['core_side']
            require(side in ('LONG','SHORT') and
                    row['occupied_positions']=='0',
                    'PHASE10_UNKNOWN_ROW_INVALID')
            native_row=pred_by_time.get(opened)
            raw=raw_by_time.get(opened)
            require(native_row is not None and raw is not None,
                    'MISSING_CORRESPONDING_NATIVE_CANDLE')
            require(native_row['model_identifier']==model and
                    native_row['source']=='freqai-native-backtest' and
                    native_row['pair']=='BTC/USDT:USDT',
                    'INVALID_NATIVE_FREQAI_SOURCE')
            for col in ('open','high','low','close','volume'):
                require(math.isclose(price(native_row[col]),price(raw[col]),
                        rel_tol=1e-10,abs_tol=1e-8),
                        'NATIVE_FORECAST_CANDLE_MISMATCH')
            value=None
            ai_side=None
            if native_row['do_predict']=='1':
                value=price(native_row['predicted_return'])
                if abs(value)>=AI_THRESHOLD:
                    ai_side='LONG' if value>0 else 'SHORT'
            else:
                require(native_row['do_predict'] in ('0','-1','-2') and
                        native_row['predicted_return']=='',
                        'INVALID_FREQAI_ABSTENTION')
            category=(RECLASSIFIED if ai_side is not None and ai_side!=side
                      else 'UNRESOLVED_AFTER_FREQAI_SOURCE_CHECK')
            reclassified+=int(category==RECLASSIFIED)
            details.append(dict(core_decision_at_ms=end,
                freqai_forecast_open_ms=opened,core_side=side,
                native_freqai_do_predict=native_row['do_predict'],
                native_freqai_predicted_return=(
                    '' if value is None else format(value,'.17g')),
                ai_side=(ai_side or ''),new_category=category))
        remaining=len(missing)-reclassified
        result.update(phase10_unexplained_before=len(missing),
            source_conflict_reclassified=reclassified,
            remaining_unexplained=remaining,
            phase10_core_only_absent_in_dual=phase10.get('core_only_entries_absent_in_dual'),
            prediction_capture_sha256=expected,
            phase10_audit_sha256=digest(paper/'portfolio-180-source-contention.json'),
            canonical_m15_sha256=digest(canonical_m15),
            source_conflict_reconciliation_verified=(remaining==0))
        if remaining:
            result['errors'].append('CORE_ENTRY_DISPLACEMENT_UNRESOLVED')
    except EvidenceError as exc:
        result['errors'].append(str(exc))
        details=[]
    except (OSError,ValueError,TypeError,KeyError,UnicodeError,OverflowError,csv.Error) as exc:
        result['errors'].append('MISSING_OR_MALFORMED_CONFLICT_EVIDENCE')
        result['error_type']=type(exc).__name__
        details=[]
    return result,details

def main():
    p=argparse.ArgumentParser(description='Read-only FreqAI opposite-source conflict evidence')
    p.add_argument('--paper-dir',required=True)
    p.add_argument('--predictions',required=True)
    p.add_argument('--native-report',required=True)
    p.add_argument('--canonical-m15',required=True)
    p.add_argument('--out',required=True)
    p.add_argument('--details',required=True)
    a=p.parse_args()
    report,rows=audit_conflicts(a.paper_dir,a.predictions,a.native_report,
                                a.canonical_m15)
    target=Path(a.out);target.parent.mkdir(parents=True,exist_ok=True)
    details=Path(a.details);details.parent.mkdir(parents=True,exist_ok=True)
    columns=('core_decision_at_ms','freqai_forecast_open_ms','core_side',
             'native_freqai_do_predict','native_freqai_predicted_return',
             'ai_side','new_category')
    with details.open('w',newline='',encoding='utf8') as f:
        writer=csv.DictWriter(f,fieldnames=columns)
        writer.writeheader();writer.writerows(rows)
    report['detail_csv_sha256']=digest(details)
    target.write_text(json.dumps(report,indent=2,sort_keys=True,allow_nan=False)+'\n',
                      encoding='utf8')
    print(json.dumps({k:report[k] for k in
        ('source_conflict_reconciliation_verified',
        'source_conflict_reclassified','remaining_unexplained',
        'ready_for_360','errors') if k in report},sort_keys=True))
    return 0 if report['source_conflict_reconciliation_verified'] else 2

if __name__=='__main__':
    raise SystemExit(main())
