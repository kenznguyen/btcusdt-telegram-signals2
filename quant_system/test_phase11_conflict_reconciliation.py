"""Synthetic Phase11 conflict-evidence tests; never enable OOS/live orders."""
import csv
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from quant_system.phase11_conflict_reconciliation import audit_conflicts

DAY=900000
T0=1800000000000
SHA='sha256:'+'a'*64
DETAIL='sha256:'+'b'*64
MODEL='chart-pro-okx-shadow-v1'

def digest(path):
    return 'sha256:'+hashlib.sha256(path.read_bytes()).hexdigest()

def csv_write(path,rows,fields):
    with path.open('w',newline='',encoding='utf8') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)

def evidence(folder,forecast='.003',flag='1',side='SHORT'):
    root=Path(folder)
    paper=root/'paper';paper.mkdir()
    native=root/'native';native.mkdir()
    canonical=root/'canonical';canonical.mkdir()
    candle=dict(open_time=str(T0),open='100',high='101',low='99',
        close='100.5',volume='123')
    csv_write(canonical/'15m.csv',[candle],list(candle))
    pred=dict(**candle,predicted_return=forecast,do_predict=flag,
        model_identifier=MODEL,source='freqai-native-backtest',
        pair='BTC/USDT:USDT')
    pred_path=native/'freqai-native-predictions.csv'
    csv_write(pred_path,[pred],list(pred))
    native_report=native/'native-research-180.json'
    native_report.write_text(json.dumps(dict(
        dataset_sha256=SHA,detail_sha256=DETAIL,
        prediction_capture_verified=True,
        freqai_native_runtime_succeeded=True,
        core_native_runtime_succeeded=True,
        prediction_capture_sha256=digest(pred_path),
        prediction_model_identifier=MODEL,
        freqai_oos_verified=False,full_core_parity_certified=False)))
    summary=paper/'portfolio-180-summary.json'
    summary.write_text(json.dumps(dict(
        phase='PHASE9_180_PAPER_ONLY',dataset_sha256=SHA,
        detail_sha256=DETAIL,prediction_capture_sha256=digest(pred_path),
        max_positions=3,entry_margin_pct=.1,
        ready_for_360=False,live_orders_enabled=False)))
    independent=paper/'portfolio-180-independent-audit.json'
    independent.write_text(json.dumps(dict(
        paper_portfolio_integrity_verified=True,
        ready_for_360=False,live_orders_enabled=False,
        full_core_parity_certified=False,errors=[])))
    attribution=paper/'portfolio-180-core-opportunity-attribution.csv'
    event=dict(core_decision_at_ms=str(T0+DAY),core_side=side,
        category='unexplained_without_active_obstruction',
        occupied_positions='0',occupied_ai_positions='0',
        occupying_trade_ids='')
    csv_write(attribution,[event],list(event))
    p10=paper/'portfolio-180-source-contention.json'
    p10.write_text(json.dumps(dict(
        contention_audit_verified=True,errors=[],
        ready_for_360=False,full_core_parity_certified=False,
        live_orders_enabled=False,oos_certified=False,
        unexplained_without_active_obstruction=1,
        core_only_entries_absent_in_dual=1,
        details_csv_sha256=digest(attribution),
        phase9_audit_sha256=digest(independent),
        phase9_summary_sha256=digest(summary))))
    return paper,pred_path,native_report,canonical/'15m.csv'

class Phase11Test(unittest.TestCase):
    def test_opposite_accepted_ai_forecast_reconciles_source_conflict(self):
        with tempfile.TemporaryDirectory() as root:
            paper,pred,native,market=evidence(root)
            result,details=audit_conflicts(paper,pred,native,market)
            self.assertTrue(result['source_conflict_reconciliation_verified'],result)
            self.assertEqual(result['source_conflict_reclassified'],1)
            self.assertEqual(result['remaining_unexplained'],0)
            self.assertEqual(details[0]['new_category'],'SAME_CANDLE_CORE_AI_SOURCE_CONFLICT')
            self.assertFalse(result['oos_certified'])
            self.assertFalse(result['ready_for_360'])

    def test_phase10_missing_or_true_oos_flag_must_still_fail_closed(self):
        # A real Phase 10 attestation must explicitly deny OOS certification.
        # The fixture must never weaken the Phase 11 fail-closed gate.
        with tempfile.TemporaryDirectory() as root:
            paper,pred,native,market=evidence(root)
            path=paper/'portfolio-180-source-contention.json'
            baseline=json.loads(path.read_text())
            for invalid in (None,True):
                with self.subTest(oos_certified=invalid):
                    tampered=dict(baseline)
                    if invalid is None:
                        tampered.pop('oos_certified',None)
                    else:
                        tampered['oos_certified']=invalid
                    path.write_text(json.dumps(tampered))
                    result,_=audit_conflicts(paper,pred,native,market)
                    self.assertFalse(result['source_conflict_reconciliation_verified'])
                    self.assertIn('UPSTREAM_PHASE10_NOT_VERIFIED',result['errors'])
            path.write_text(json.dumps(baseline))
            passed,_=audit_conflicts(paper,pred,native,market)
            self.assertTrue(passed['source_conflict_reconciliation_verified'],passed)

    def test_same_direction_keeps_unexplained_and_fails_closed(self):
        with tempfile.TemporaryDirectory() as root:
            paper,pred,native,market=evidence(root,forecast='-.004')
            result,_=audit_conflicts(paper,pred,native,market)
            self.assertFalse(result['source_conflict_reconciliation_verified'])
            self.assertEqual(result['remaining_unexplained'],1)
            self.assertIn('CORE_ENTRY_DISPLACEMENT_UNRESOLVED',result['errors'])

    def test_nonaccepted_ai_signal_does_not_reconcile(self):
        with tempfile.TemporaryDirectory() as root:
            paper,pred,native,market=evidence(root,forecast='',flag='0')
            result,_=audit_conflicts(paper,pred,native,market)
            self.assertFalse(result['source_conflict_reconciliation_verified'])

    def test_prediction_sha_modified_fails_closed(self):
        with tempfile.TemporaryDirectory() as root:
            paper,pred,native,market=evidence(root)
            pred.write_text(pred.read_text()+'\\n')
            result,_=audit_conflicts(paper,pred,native,market)
            self.assertIn('NATIVE_FORECAST_SHA_MISMATCH',result['errors'])

    def test_raw_candle_not_matching_prediction_fails_closed(self):
        with tempfile.TemporaryDirectory() as root:
            paper,pred,native,market=evidence(root)
            content=market.read_text().replace('100.5','105.5')
            market.write_text(content)
            result,_=audit_conflicts(paper,pred,native,market)
            self.assertIn('NATIVE_FORECAST_CANDLE_MISMATCH',result['errors'])

    def test_tampered_phase10_detail_sha_fails_closed(self):
        with tempfile.TemporaryDirectory() as root:
            paper,pred,native,market=evidence(root)
            csvpath=paper/'portfolio-180-core-opportunity-attribution.csv'
            csvpath.write_text(csvpath.read_text()+'\\n')
            result,_=audit_conflicts(paper,pred,native,market)
            self.assertIn('PHASE10_DETAILS_SHA_MISMATCH',result['errors'])

if __name__=='__main__':
    unittest.main()
