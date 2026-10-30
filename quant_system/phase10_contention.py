"""Phase 10 multi-slot CORE/AI contention audit — descriptive, never promotion.

Uses checksum-attested Phase9 *paper fills* and compares CORE_ONLY trade
entry timestamps to DUAL paper trade entries and DUAL's 3-slot occupancy.
CORE_ONLY entries are NOT all raw CORE signals, and occupancy is NOT a
counterfactual proof that a missed trade would have filled.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
from pathlib import Path

ENTRY=('LONG ENTRY','SHORT ENTRY')
EXIT=('TAKE PROFIT','SOFT SL','EMERGENCY SL')
EVENT_COLUMNS=('trade_id','kind','origin','side','decision_at_ms','filled_at_ms')

class ContentionError(ValueError):
    pass

def require(ok, code):
    if not ok:
        raise ContentionError(code)

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024*1024),b''):
            h.update(chunk)
    return 'sha256:'+h.hexdigest()

def readjson(path):
    data=json.loads(path.read_text(encoding='utf8'))
    require(isinstance(data,dict),'MALFORMED_JSON_EVIDENCE')
    return data

def readcsv(path):
    with path.open(newline='',encoding='utf8') as f:
        reader=csv.DictReader(f)
        require(reader.fieldnames is not None and
                len(reader.fieldnames)==len(set(reader.fieldnames)) and
                set(EVENT_COLUMNS).issubset(reader.fieldnames),
                'INVALID_PAPER_EVENT_COLUMNS')
        data=list(reader)
    require(all(None not in r and all(v is not None for v in r.values())
                for r in data), 'INVALID_PAPER_EVENT_ROW')
    return data

def number(value):
    try:
        n=int(value)
        require(str(n)==str(value) and n>=0,'INVALID_EVENT_TIME')
        return n
    except (ValueError,TypeError,OverflowError) as exc:
        raise ContentionError('INVALID_EVENT_TIME') from exc

def lifecycle(rows,mode):
    """Prove ordered, individually closed 3-slot virtual trade lifecycles."""
    open_positions={}
    used=set()
    intervals=[]
    entries=[]
    last=-1
    for row in rows:
        kind=row['kind']; origin=row['origin']; side=row['side'];tid=row['trade_id']
        require(kind in ENTRY+EXIT+('DCA',) and origin in ('CORE','AI') and
                side in ('LONG','SHORT') and bool(tid), 'INVALID_EVENT_IDENTITY')
        require((mode=='DUAL') or origin==('CORE' if mode=='CORE_ONLY' else 'AI'),
                'INVALID_EVENT_SOURCE')
        decision,filled=number(row['decision_at_ms']),number(row['filled_at_ms'])
        require(decision<=filled and filled>=last,'NONMONOTONIC_DUAL_EVENT'
                if mode=='DUAL' else 'NONMONOTONIC_PAPER_EVENT')
        last=filled
        if kind in ENTRY:
            require(kind.split()[0]==side and tid not in used and
                    len(open_positions)<3,
                    'OVERLAPPING_OR_DUPLICATE_ENTRY')
            require(not open_positions or all(x['side']==side
                    for x in open_positions.values()), 'OPPOSITE_SIDE_VIRTUAL_PORTFOLIO')
            if mode=='DUAL' and origin=='AI':
                require(sum(x['origin']=='AI' for x in open_positions.values())<2,
                        'AI_DUAL_SLOT_POLICY_VIOLATION')
            open_positions[tid]=dict(trade_id=tid,origin=origin,side=side,
                    start=filled,end=None,dca_count=0)
            used.add(tid)
            entries.append(row)
        elif kind=='DCA':
            require(tid in open_positions and
                    open_positions[tid]['origin']==origin and
                    open_positions[tid]['side']==side and
                    open_positions[tid]['dca_count']==0,
                    'INVALID_DCA_LIFECYCLE')
            open_positions[tid]['dca_count']=1
        else:
            require(tid in open_positions and
                    open_positions[tid]['origin']==origin and
                    open_positions[tid]['side']==side,
                    'ORPHAN_EXIT_OR_MISMATCHED_TRADE')
            trade=open_positions.pop(tid)
            trade['end']=filled
            intervals.append(trade)
    intervals.extend(open_positions.values())
    return entries,intervals,len(open_positions)

def audit_contention(folder):
    """Return (fail-closed report, missing-entry rows). NEVER change risk gates."""
    result=dict(schemaVersion=1,audit='PHASE10_CORE_AI_MULTISLOT_OCCUPANCY',
        contention_audit_verified=False,ready_for_360=False,
        full_core_parity_certified=False,live_orders_enabled=False,
        oos_certified=False,ai_promotion_eligible=False,
        errors=[],interpretation=(
            'Observational contrast of CORE_ONLY entry fills against DUAL '
            '3-slot position intervals; not all CORE raw signals, not a '
            'causal guarantee, and not a permission to enable hedge mode.'),
        risk_policy='UNMODIFIED_THREE_SLOTS_MAX_TWO_AI_SAME_SIDE_ONLY',
        research_blockers=['MODEL_OOS_NOT_CERTIFIED',
            'INDEPENDENT_KOTLIN_NATIVE_TRADE_PARITY_MISSING',
            'FUNDING_MARK_LIQUIDATION_INCOMPLETE',
            'EXCHANGE_POSITION_MODE_NOT_VERIFIED'])
    missing=[]
    try:
        root=Path(folder)
        upstream=readjson(root/'portfolio-180-independent-audit.json')
        require(upstream.get('paper_portfolio_integrity_verified') is True and
                upstream.get('errors')==[] and
                upstream.get('ready_for_360') is False and
                upstream.get('full_core_parity_certified') is False and
                upstream.get('live_orders_enabled') is False,
                'UPSTREAM_PHASE9_NOT_VERIFIED')
        hashes=upstream.get('artifact_sha256')
        require(isinstance(hashes,dict) and bool(hashes),
                'MISSING_UPSTREAM_HASHES')
        necessary=['portfolio-180-summary.json','portfolio-core-only-events.csv',
                   'portfolio-dual-events.csv','portfolio-ai-only-events.csv']
        require(all(x in hashes for x in necessary), 'MISSING_UPSTREAM_HASHES')
        # Verify all 13 upstream artifacts to detect mixed-run files.
        require(all(sha(root/name)==expected for name,expected in hashes.items()),
                'UPSTREAM_ARTIFACT_SHA_CHANGED')
        summary=readjson(root/'portfolio-180-summary.json')
        require(summary.get('phase')=='PHASE9_180_PAPER_ONLY' and
                summary.get('max_positions')==3 and
                summary.get('entry_margin_pct')==.1 and
                summary.get('ai_slots_in_dual')==2 and
                summary.get('ready_for_360') is False and
                summary.get('live_orders_enabled') is False,
                'UNAPPROVED_PORTFOLIO_CONFIG')
        core,_,core_open=lifecycle(readcsv(root/necessary[1]),'CORE_ONLY')
        dual,dual_intervals,dual_open=lifecycle(readcsv(root/necessary[2]),'DUAL')
        ai,_,ai_open=lifecycle(readcsv(root/necessary[3]),'AI_ONLY')
        for mode,entries,open_count in (
            ('CORE_ONLY',core,core_open),('DUAL',dual,dual_open),('AI_ONLY',ai,ai_open)):
            section=summary.get(mode)
            require(isinstance(section,dict) and
                    len(entries)==section.get('trade_count_closed',-1)+section.get('trade_count_open',-1) and
                    open_count==section.get('trade_count_open'),
                    'PORTFOLIO_EVENT_COUNT_MISMATCH')
        core_entries={(number(r['decision_at_ms']),r['side']):r for r in core}
        dual_core={(number(r['decision_at_ms']),r['side']):r for r in dual if r['origin']=='CORE'}
        require(len(core_entries)==len(core) and
                len(dual_core)==sum(r['origin']=='CORE' for r in dual),
                'DUPLICATE_SOURCE_ENTRY_CANDLE')
        categories={name:0 for name in ('full_position_slots',
            'opposite_side_ai_occupied','opposite_side_core_occupied',
            'same_side_ai_occupied_with_capacity',
            'same_side_core_occupied_with_capacity',
            'unexplained_without_active_obstruction')}
        for (t,side),entry in sorted(core_entries.items()):
            if (t,side) in dual_core:
                continue
            occupying=[p for p in dual_intervals if
                    p['start']<=t and (p['end'] is None or t<p['end'])]
            require(len(occupying)<=3,'DUAL_SLOTS_EXCEEDED')
            ai_occupied=[p for p in occupying if p['origin']=='AI']
            opp_ai=[p for p in ai_occupied if p['side']!=side]
            opp_core=[p for p in occupying if p['origin']=='CORE' and p['side']!=side]
            if len(occupying)==3:
                category='full_position_slots'
            elif opp_ai:
                category='opposite_side_ai_occupied'
            elif opp_core:
                category='opposite_side_core_occupied'
            elif ai_occupied:
                category='same_side_ai_occupied_with_capacity'
            elif occupying:
                category='same_side_core_occupied_with_capacity'
            else:
                category='unexplained_without_active_obstruction'
            categories[category]+=1
            missing.append(dict(core_decision_at_ms=t,core_side=side,
                category=category,occupied_positions=len(occupying),
                occupied_ai_positions=len(ai_occupied),
                occupying_trade_ids=';'.join(sorted(p['trade_id'] for p in occupying))))
        result.update(core_only_entries=len(core),dual_core_entries=len(dual_core),
            dual_ai_entries=sum(r['origin']=='AI' for r in dual),
            core_only_entries_matched_in_dual=len(set(core_entries)&set(dual_core)),
            core_only_entries_absent_in_dual=len(missing),
            dual_core_entries_not_seen_in_core_only=len(set(dual_core)-set(core_entries)),
            **categories,contention_audit_verified=True,
            phase9_summary_sha256=sha(root/'portfolio-180-summary.json'),
            phase9_audit_sha256=sha(root/'portfolio-180-independent-audit.json'))
    except ContentionError as exc:
        result['errors'].append(str(exc))
        missing=[]
    except (OSError,ValueError,TypeError,UnicodeError,KeyError,csv.Error,OverflowError) as exc:
        result['errors'].append('MISSING_OR_MALFORMED_PHASE9_EVIDENCE')
        result['error_type']=type(exc).__name__
        missing=[]
    return result,missing

def main():
    p=argparse.ArgumentParser(description='Phase10 read-only virtual BTCUSDT slot audit')
    p.add_argument('--paper-dir',required=True)
    p.add_argument('--out',required=True)
    p.add_argument('--details',required=True)
    args=p.parse_args()
    report,details=audit_contention(args.paper_dir)
    output=Path(args.out);detailpath=Path(args.details)
    output.parent.mkdir(parents=True,exist_ok=True)
    detailpath.parent.mkdir(parents=True,exist_ok=True)
    fieldnames=('core_decision_at_ms','core_side','category',
            'occupied_positions','occupied_ai_positions','occupying_trade_ids')
    with detailpath.open('w',newline='',encoding='utf8') as f:
        writer=csv.DictWriter(f,fieldnames=fieldnames)
        writer.writeheader();writer.writerows(details)
    report['details_csv_sha256']=sha(detailpath)
    output.write_text(json.dumps(report,sort_keys=True,indent=2,allow_nan=False)+'\n',
                      encoding='utf8')
    print(json.dumps({k:report[k] for k in ('contention_audit_verified',
          'core_only_entries_absent_in_dual','opposite_side_ai_occupied',
          'full_position_slots','errors') if k in report},sort_keys=True))
    return 0 if report['contention_audit_verified'] else 2

if __name__=='__main__':
    raise SystemExit(main())
