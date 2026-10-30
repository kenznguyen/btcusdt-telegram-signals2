"""Phase 10 regression: source occupancy is descriptive and SHA-pinned."""
import csv
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from quant_system.phase10_contention import audit_contention

S=900000

def rows(path, fields, values):
    with path.open('w',newline='',encoding='utf8') as f:
        writer=csv.DictWriter(f,fieldnames=fields)
        writer.writeheader()
        writer.writerows(values)

def sha(path):
    return 'sha256:'+hashlib.sha256(path.read_bytes()).hexdigest()

def ev(trade_id,ts,kind,origin,side):
    return dict(trade_id=trade_id,kind=kind,origin=origin,side=side,
        decision_at_ms=str(ts),filled_at_ms=str(ts))

def fixture(path):
    root=Path(path)
    paper=root/'paper'
    paper.mkdir()
    # Four CORE_ONLY independent entry events, one present in DUAL,
    # one opposed by AI LONG, one during three occupied slots, one
    # without a visible position-level reason in DUAL.
    core=[]
    for i,(t,side) in enumerate(((1,'LONG'),(6,'SHORT'),(13,'LONG'),(16,'LONG'))):
        tid='CORE'+str(i)
        core.extend([ev(tid,t*S,side+' ENTRY','CORE',side),
                     ev(tid,(t+1)*S,'TAKE PROFIT','CORE',side)])
    dual=[
        ev('DCORE',1*S,'LONG ENTRY','CORE','LONG'),
        ev('DCORE',2*S,'TAKE PROFIT','CORE','LONG'),
        ev('A1',5*S,'LONG ENTRY','AI','LONG'),
        ev('A1',8*S,'TAKE PROFIT','AI','LONG'),
        ev('A2',10*S,'LONG ENTRY','AI','LONG'),
        ev('A3',11*S,'LONG ENTRY','AI','LONG'),
        ev('C2',12*S,'LONG ENTRY','CORE','LONG'),
        ev('A2',14*S,'SOFT SL','AI','LONG'),
        ev('A3',14*S,'SOFT SL','AI','LONG'),
        ev('C2',14*S,'SOFT SL','CORE','LONG'),
    ]
    files={}
    for mode,events in (('core-only',core),('dual',dual),('ai-only',[])):
        name=f'portfolio-{mode}-events.csv'
        p=paper/name
        rows(p,['trade_id','kind','origin','side','decision_at_ms','filled_at_ms'],events)
        files[name]=sha(p)
    summary=dict(phase='PHASE9_180_PAPER_ONLY',max_positions=3,
        entry_margin_pct=.1,ai_slots_in_dual=2,
        ready_for_360=False,full_core_parity_certified=False,
        live_orders_enabled=False,
        dataset_sha256='sha256:'+'a'*64,detail_sha256='sha256:'+'b'*64,
        CORE_ONLY=dict(trade_count_closed=4,trade_count_open=0),
        AI_ONLY=dict(trade_count_closed=0,trade_count_open=0),
        DUAL=dict(trade_count_closed=5,trade_count_open=0))
    s=paper/'portfolio-180-summary.json'
    s.write_text(json.dumps(summary))
    files[s.name]=sha(s)
    (paper/'portfolio-180-independent-audit.json').write_text(json.dumps(dict(
        paper_portfolio_integrity_verified=True,errors=[],ready_for_360=False,
        full_core_parity_certified=False,live_orders_enabled=False,
        artifact_sha256=files)))
    return paper

class Phase10Test(unittest.TestCase):
    def test_opposite_ai_full_and_unexplained_are_distinct(self):
        with tempfile.TemporaryDirectory() as temp:
            p=fixture(temp)
            r,details=audit_contention(p)
            self.assertTrue(r['contention_audit_verified'],r)
            self.assertEqual(r['core_only_entries'],4)
            self.assertEqual(r['core_only_entries_matched_in_dual'],1)
            self.assertEqual(r['core_only_entries_absent_in_dual'],3)
            self.assertEqual(r['opposite_side_ai_occupied'],1)
            self.assertEqual(r['full_position_slots'],1)
            self.assertEqual(r['unexplained_without_active_obstruction'],1)
            self.assertEqual(len(details),3)
            self.assertFalse(r['ready_for_360'])

    def test_tampered_events_fail_upstream_hash(self):
        with tempfile.TemporaryDirectory() as temp:
            p=fixture(temp);f=p/'portfolio-dual-events.csv'
            f.write_text(f.read_text()+'tampered\n')
            r,_=audit_contention(p)
            self.assertFalse(r['contention_audit_verified'])
            self.assertIn('UPSTREAM_ARTIFACT_SHA_CHANGED',r['errors'])

    def test_reversed_or_overlapping_dual_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            p=fixture(temp);f=p/'portfolio-dual-events.csv'
            with f.open(newline='') as src:
                evs=list(csv.DictReader(src))
            evs[3]['filled_at_ms']=str(1*S)
            rows(f,list(evs[0]),evs)
            upstream=p/'portfolio-180-independent-audit.json'
            manifest=json.loads(upstream.read_text())
            manifest['artifact_sha256'][f.name]=sha(f)
            upstream.write_text(json.dumps(manifest))
            r,_=audit_contention(p)
            self.assertFalse(r['contention_audit_verified'])
            self.assertIn('NONMONOTONIC_DUAL_EVENT',r['errors'])

    def test_missing_phase9_or_bad_flags_fail_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            p=fixture(temp)
            up=p/'portfolio-180-independent-audit.json'
            obj=json.loads(up.read_text())
            obj['paper_portfolio_integrity_verified']=False
            up.write_text(json.dumps(obj))
            self.assertIn('UPSTREAM_PHASE9_NOT_VERIFIED',
                          audit_contention(p)[0]['errors'])

    def test_actual_180d_evidence_observes_fourteen_absences(self):
        # This test is optional offline integration; Codemagic unit jobs
        # have no market artifacts and therefore use the synthetic tests.
        p=Path(__file__).resolve().parents[1]/'evidence/artifacts/phase3/paper'
        if not p.exists():
            self.skipTest('Offline 180d evidence not mounted')
        report,_=audit_contention(p)
        self.assertTrue(report['contention_audit_verified'],report)
        self.assertEqual(report['core_only_entries'],29)
        self.assertEqual(report['core_only_entries_matched_in_dual'],15)
        self.assertEqual(report['core_only_entries_absent_in_dual'],14)
        self.assertEqual(report['opposite_side_ai_occupied'],13)
        self.assertEqual(report['full_position_slots'],1)
        self.assertEqual(report['unexplained_without_active_obstruction'],0)

if __name__=='__main__':
    unittest.main()
