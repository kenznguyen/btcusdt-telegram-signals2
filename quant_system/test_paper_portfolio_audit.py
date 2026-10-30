"""Phase 9 synthetic paper accounting and independent multi-position audit."""
import csv
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from quant_system.paper_portfolio_audit import audit_portfolio
from quant_system.paper_portfolio import replay_portfolio
from quant_system.paper_backtest import EVENT_FIELDS,TRADE_FIELDS
from quant_system.test_paper_portfolio import candle,fine,prediction,SHA,DETAIL,MODEL

def save(path,rows,fields):
    with path.open('w',newline='',encoding='utf8') as f:
        writer=csv.DictWriter(f,fieldnames=fields)
        writer.writeheader();writer.writerows(rows)

def build(root):
    root=Path(root)
    paper=root/'paper'
    paper.mkdir()
    pred=root/'native-predictions.csv'
    pred.write_text('synthetic predictions, no native inference\n')
    ps='sha256:'+hashlib.sha256(pred.read_bytes()).hexdigest()
    native=root/'native-report.json'
    native.write_text(json.dumps(dict(
        core_native_runtime_succeeded=True,
        freqai_native_runtime_succeeded=True,
        dataset_sha256=SHA,detail_sha256=DETAIL,
        prediction_capture_sha256=ps)))
    summary=dict(phase='PHASE9_180_PAPER_ONLY',exchange='okx',
        dataset_sha256=SHA,detail_sha256=DETAIL,prediction_capture_sha256=ps,
        max_positions=3,entry_margin_pct=.1,max_total_margin_pct=.6,
        ai_slots_in_dual=2,full_core_parity_certified=False,
        ready_for_360=False,live_orders_enabled=False)
    candles=[candle(i) for i in range(6)]
    forecasts=[prediction(i) for i in range(5)]
    for mode in ('CORE_ONLY','AI_ONLY','DUAL'):
        result=replay_portfolio(candles,fine(6),forecasts,mode=mode,
            dataset_sha256=SHA,detail_sha256=DETAIL,model_identifier=MODEL)
        summary[mode]=result['report']
        stem='portfolio-'+mode.lower().replace('_','-')
        save(paper/(stem+'-events.csv'),result['events'],EVENT_FIELDS)
        save(paper/(stem+'-trades.csv'),result['trades'],TRADE_FIELDS)
        save(paper/(stem+'-equity.csv'),result['equity_curve'],
            list(result['equity_curve'][0]))
        (paper/(stem+'-report.json')).write_text(json.dumps(result['report']))
    (paper/'portfolio-180-summary.json').write_text(json.dumps(summary))
    return paper,native,pred

class PortfolioIndependentAuditTests(unittest.TestCase):
    def test_independent_audit_accepts_three_position_fixture_but_never_certifies(self):
        with tempfile.TemporaryDirectory() as root:
            folder,native,pred=build(root)
            report=audit_portfolio(folder,native,pred)
            self.assertTrue(report['paper_portfolio_integrity_verified'],report)
            self.assertEqual(report['modes']['AI_ONLY']['open_trades'],3)
            self.assertFalse(report['ready_for_360'])
            self.assertFalse(report['live_orders_enabled'])

    def test_tamper_entry_margin_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            folder,native,pred=build(root)
            path=folder/'portfolio-ai-only-events.csv'
            with path.open(newline='') as f: rows=list(csv.DictReader(f))
            rows[0]['margin_usdt']='50'
            save(path,rows,list(rows[0]))
            self.assertIn('ENTRY_NOT_TEN_PERCENT_EQUITY',
                audit_portfolio(folder,native,pred)['errors'])

    def test_tamper_report_trade_count_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            folder,native,pred=build(root)
            file=folder/'portfolio-dual-report.json'
            obj=json.loads(file.read_text())
            obj['trade_count_open']=100
            file.write_text(json.dumps(obj))
            self.assertIn('PORTFOLIO_MODE_REPORT_DIFFERENCE',
                audit_portfolio(folder,native,pred)['errors'])

    def test_missing_native_predictions_fail_closed(self):
        with tempfile.TemporaryDirectory() as root:
            folder,native,pred=build(root)
            pred.unlink()
            self.assertFalse(audit_portfolio(folder,native,pred)['paper_portfolio_integrity_verified'])

if __name__=='__main__':
    unittest.main()
