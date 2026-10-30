"""Fail-closed, synthetic fixtures for Phase 3 180-day artifact audit."""
import csv
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from quant_system.paper_audit import audit_180

MODES = ('CORE_ONLY', 'AI_ONLY', 'DUAL')
DATA = 'sha256:' + 'a' * 64
DETAIL = 'sha256:' + 'b' * 64
PREDICTION = 'freqai-native-predictions.csv'


def save_csv(path, fields, rows):
    with path.open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def fixture(directory):
    root = Path(directory)
    prediction = root / PREDICTION
    prediction.write_text('genuine capture fixture, not a model\n', encoding='utf8')
    pred_sha = 'sha256:' + hashlib.sha256(prediction.read_bytes()).hexdigest()
    native = dict(exchange='okx', days=180, detail_timeframe='5m', dataset_sha256=DATA,
                  detail_sha256=DETAIL, core_native_runtime_succeeded=True,
                  freqai_native_runtime_succeeded=True, prediction_capture_verified=True,
                  prediction_capture_sha256=pred_sha, prediction_capture_accepted=1,
                  prediction_model_identifier='chart-pro-okx-shadow-v1')
    (root / 'native-research-180.json').write_text(json.dumps(native), encoding='utf8')
    summary = dict(schemaVersion=1, phase='PAPER_180_ONLY', exchange='okx',
                   dataset_sha256=DATA, detail_sha256=DETAIL, prediction_capture_sha256=pred_sha,
                   ohlcv_verified=True, paper_trade_bearing_verified=True,
                   full_core_parity_certified=False, exchange_fills_verified=False,
                   funding_mark_full_coverage_verified=False, kotlin_trace_verified=False,
                   model_oos_verified=False,
                   trading_mode='OFFLINE_RESEARCH_NO_EXCHANGE_ORDERS')
    for mode in MODES:
        stem = 'paper-' + mode.lower().replace('_', '-')
        trade_id = mode + ':trade'
        events = [dict(event_id=mode+':entry', kind='LONG ENTRY', origin='AI' if mode!='CORE_ONLY' else 'CORE',
                       side='LONG', trade_id=trade_id, candle_time=0, decision_at_ms=900000,
                       confirmed_at_ms=900000, filled_at_ms=900000, expected_fill_price=100,
                       actual_fill_price=100.05, fill_difference=.05, fill_source='SIMULATED_OHLCV_5M',
                       quantity_base=1, margin_usdt=50, fee_usdt=.05, dataset_sha256=DATA,
                       detail_sha256=DETAIL),
                  dict(event_id=mode+':exit', kind='TAKE PROFIT', origin='AI' if mode!='CORE_ONLY' else 'CORE',
                       side='LONG', trade_id=trade_id, candle_time=900000, decision_at_ms=1800000,
                       confirmed_at_ms=1800000, filled_at_ms=1800000, expected_fill_price=102,
                       actual_fill_price=101.95, fill_difference=-.05, fill_source='SIMULATED_OHLCV_5M',
                       quantity_base=1, margin_usdt=50, fee_usdt=.05, dataset_sha256=DATA,
                       detail_sha256=DETAIL)]
        save_csv(root / (stem+'-events.csv'), list(events[0]), events)
        trades = [dict(trade_id=trade_id, origin=events[0]['origin'], side='LONG', entry_at_ms=900000,
                       exit_at_ms=1800000, entry_price=100.05, exit_price=101.95,
                       exit_reason='TAKE PROFIT', dca_count=0, margin_usdt=50,
                       gross_pnl_usdt=1.9, fees_usdt=.1,
                       net_pnl_ex_funding_usdt=1.8, roe_percent=3.8)]
        save_csv(root / (stem+'-trades.csv'), list(trades[0]), trades)
        equity = [dict(candle_close_ms=900000, equity_mtm_ex_funding_usdt=100,
                       unrealized_usdt=0, drawdown_usdt=0, open_position=False),
                  dict(candle_close_ms=1800000, equity_mtm_ex_funding_usdt=101.8,
                       unrealized_usdt=0, drawdown_usdt=0, open_position=False)]
        save_csv(root / (stem+'-equity.csv'), list(equity[0]), equity)
        report = dict(mode=mode, exchange='okx', symbol='BTC/USDT:USDT', days=180,
                      dataset_sha256=DATA, detail_sha256=DETAIL, starting_capital_usdt=100,
                      equity_mtm_ex_funding_usdt=101.8, realized_gross_pnl_usdt=1.9,
                      fees_usdt=.1, realized_net_ex_funding_usdt=1.8,
                      max_drawdown_ex_funding_usdt=0., trade_count_closed=1, trade_count_open=0,
                      dca_requests=0, dca_risk_denials=0, dca_filled=0,
                      funding_mark_full_coverage_verified=False, liquidation_verified=False,
                      exchange_fills_verified=False, freqai_oos_verified=False,
                      native_trade_parity_verified=False, full_core_parity_certified=False,
                      native_orders_enabled=False)
        (root / (stem+'-report.json')).write_text(json.dumps(report), encoding='utf8')
        summary[mode] = report
    (root / 'paper-180-summary.json').write_text(json.dumps(summary), encoding='utf8')
    return root


class Audit180Tests(unittest.TestCase):
    def check(self, root):
        return audit_180(root, root / 'native-research-180.json', root / PREDICTION)

    def test_synthetic_fixture_passes_integrity_but_not_360_certification(self):
        with tempfile.TemporaryDirectory() as temp:
            result = self.check(fixture(temp))
            self.assertTrue(result['artifact_integrity_verified'], result)
            self.assertFalse(result['ready_for_360'])
            self.assertFalse(result['full_core_parity_certified'])
            self.assertIn('MODEL_OOS_NOT_VERIFIED', result['research_blockers'])

    def test_reject_modified_fill_difference(self):
        with tempfile.TemporaryDirectory() as temp:
            root = fixture(temp)
            path = root/'paper-ai-only-events.csv'
            with path.open(newline='', encoding='utf-8') as stream:
                rows = list(csv.DictReader(stream))
            rows[0]['fill_difference'] = '-100'
            save_csv(path, list(rows[0]), rows)
            result = self.check(root)
            self.assertFalse(result['artifact_integrity_verified'])
            self.assertIn('FILL_DIFFERENCE_MISMATCH', result['integrity_errors'])

    def test_reject_duplicate_event_identifier(self):
        with tempfile.TemporaryDirectory() as temp:
            root = fixture(temp)
            path = root/'paper-dual-events.csv'
            with path.open(newline='', encoding='utf-8') as stream:
                rows = list(csv.DictReader(stream))
            rows[1]['event_id'] = rows[0]['event_id']
            save_csv(path, list(rows[0]), rows)
            self.assertIn('DUPLICATE_EVENT_ID', self.check(root)['integrity_errors'])

    def test_reject_native_capture_tampering(self):
        with tempfile.TemporaryDirectory() as temp:
            root = fixture(temp)
            (root / PREDICTION).write_text('modified predictions')
            self.assertIn('PREDICTION_SHA_MISMATCH', self.check(root)['integrity_errors'])

    def test_reject_phantom_closed_trade_count(self):
        with tempfile.TemporaryDirectory() as temp:
            root = fixture(temp)
            path = root/'paper-core-only-report.json'
            report = json.loads(path.read_text())
            report['trade_count_closed'] = 2
            path.write_text(json.dumps(report))
            self.assertIn('MODE_REPORT_SUMMARY_MISMATCH', self.check(root)['integrity_errors'])

    def test_reject_unsupported_exchange_fill_claim(self):
        with tempfile.TemporaryDirectory() as temp:
            root = fixture(temp)
            path = root/'paper-180-summary.json'
            report = json.loads(path.read_text())
            report['exchange_fills_verified'] = True
            path.write_text(json.dumps(report))
            self.assertIn('UNSUPPORTED_CERTIFICATION_CLAIM', self.check(root)['integrity_errors'])

    def test_missing_or_malformed_evidence_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = fixture(temp)
            (root / 'paper-dual-equity.csv').unlink()
            self.assertFalse(self.check(root)['artifact_integrity_verified'])
        with tempfile.TemporaryDirectory() as temp:
            root = fixture(temp)
            (root / 'paper-180-summary.json').write_text('{')
            self.assertFalse(self.check(root)['artifact_integrity_verified'])


if __name__ == '__main__':
    unittest.main()
