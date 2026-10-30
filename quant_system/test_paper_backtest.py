"""Paper replay contract; no exchange IO or production authorization."""
import csv
import math
import tempfile
import unittest
from pathlib import Path

from quant_system.paper_backtest import (
    validated_native_predictions, replay_candles, write_paper_outputs,
    verify_native_prediction_evidence,
)

M15 = 900_000
FIVE = 300_000
T0 = 1_800_000_000_000
HASH = 'sha256:' + 'a'*64
DETAIL = 'sha256:' + 'b'*64
MODEL = 'chart-pro-okx-shadow-v1'


def row(i, **changes):
    x = dict(open_time=T0+i*M15, open=100., high=101., low=99.,close=100.,volume=3.,closed=True,
             previous_rsi=39.,rsi=40.,adx=48.,previous_open=100.,previous_close=100.,
             h1_plus=26.,h1_minus=12.,h1_adx=27.,h1_source_open_time=T0-7_200_000)
    x.update(changes)
    return x


def fine(count, overrides=None):
    overrides = overrides or {}
    result=[]
    for i in range(count):
        for j in range(3):
            bar=dict(open_time=T0+i*M15+j*FIVE,open=100.,high=101.,low=99.,close=100.,volume=1.,closed=True)
            bar.update(overrides.get((i,j),{}))
            result.append(bar)
    return result


def pred(i, direction, *, close=100., do_predict=1, model=MODEL):
    return dict(open_time=T0+i*M15, open=100.,high=101.,low=99.,close=close,volume=3.,
                predicted_return=direction, do_predict=do_predict, model_identifier=model,
                source='freqai-native-backtest', pair='BTC/USDT:USDT')


class PaperReplayTests(unittest.TestCase):
    def run_mode(self, m15, mode, preds=(), detail=None):
        return replay_candles(m15, detail or fine(len(m15)), preds, mode=mode,
                              dataset_sha256=HASH,detail_sha256=DETAIL,model_identifier=MODEL)

    def test_core_entry_on_next_candle_open_and_price_reconciliation(self):
        candles=[row(0,previous_rsi=29.,rsi=31.),row(1),row(2)]
        result=self.run_mode(candles,'CORE_ONLY')
        events=result['events']
        entries=[x for x in events if x['kind']=='LONG ENTRY']
        self.assertEqual(len(entries),1)
        event=entries[0]
        self.assertEqual(event['decision_at_ms'],T0+M15)
        self.assertEqual(event['filled_at_ms'],T0+M15)
        self.assertEqual(event['expected_fill_price'],100.)
        self.assertAlmostEqual(event['actual_fill_price'],100.05)
        self.assertAlmostEqual(event['fill_difference'],0.05)
        self.assertEqual(event['fill_source'],'SIMULATED_OHLCV_5M')
        self.assertFalse(result['report']['exchange_fills_verified'])
        self.assertEqual(result['report']['trade_count_open'],1)

    def test_independent_ai_long_when_core_has_no_signal(self):
        candles=[row(0),row(1),row(2)]
        result=self.run_mode(candles,'AI_ONLY',[pred(0,0.006)])
        entries=[x for x in result['events'] if x['kind']=='LONG ENTRY']
        self.assertEqual(len(entries),1)
        self.assertEqual(entries[0]['origin'],'AI')
        self.assertEqual(entries[0]['filled_at_ms'],T0+M15)
        self.assertFalse(result['report']['freqai_oos_verified'])

    def test_ai_only_short_and_no_core(self):
        result=self.run_mode([row(0),row(1)],'AI_ONLY',[pred(0,-0.006)])
        self.assertEqual([e['kind'] for e in result['events']],['SHORT ENTRY'])

    def test_dual_disagree_blocks_both_but_independent_modes_still_work(self):
        candles=[row(0,previous_rsi=29.,rsi=31.),row(1)]
        predictions=[pred(0,-0.006)]
        self.assertEqual(self.run_mode(candles,'DUAL',predictions)['events'],[])
        self.assertEqual(self.run_mode(candles,'DUAL',predictions)['report']['source_conflicts'],1)
        self.assertEqual(len(self.run_mode(candles,'CORE_ONLY',predictions)['events']),1)
        self.assertEqual(len(self.run_mode(candles,'AI_ONLY',predictions)['events']),1)

    def test_gap_emergency_stop_priority_intrabar_and_fill_difference(self):
        candles=[row(0),row(1),row(2,low=90.)]
        detail=fine(3,{(2,0):dict(open=90.,high=94.,low=89.,close=90.)})
        # Simulate an AI entry at t0 -> first fill t1; stop touch t2 at open gap.
        result=self.run_mode(candles,'AI_ONLY',[pred(0,0.008)],detail)
        events=result['events']
        self.assertEqual([e['kind'] for e in events],['LONG ENTRY','EMERGENCY SL'])
        stop=events[1]
        self.assertAlmostEqual(stop['expected_fill_price'],
                               events[0]['actual_fill_price']*(1-.9/13),places=5)
        self.assertLess(stop['actual_fill_price'],stop['expected_fill_price'])
        self.assertAlmostEqual(stop['fill_difference'],stop['actual_fill_price']-stop['expected_fill_price'])
        self.assertEqual(stop['filled_at_ms'],T0+2*M15)
        self.assertEqual(result['report']['trade_count_closed'],1)

    def test_soft_stop_and_take_profit_fill_only_after_close(self):
        tp_candles=[row(0), row(1,high=102.,close=101.,rsi=78.),row(2)]
        tp=self.run_mode(tp_candles,'AI_ONLY',[pred(0,0.006)])
        self.assertEqual([e['kind'] for e in tp['events']],['LONG ENTRY','TAKE PROFIT'])
        self.assertEqual(tp['events'][1]['confirmed_at_ms'],T0+2*M15)
        self.assertEqual(tp['events'][1]['filled_at_ms'],T0+2*M15)
        self.assertEqual(tp['events'][1]['expected_fill_price'],101.)
        self.assertAlmostEqual(tp['events'][1]['actual_fill_price'],99.95)

    def test_gap_through_emergency_overrides_prior_confirmed_tp(self):
        candles=[row(0),row(1,close=101.,rsi=78.),row(2)]
        detail=fine(3,{(2,0):dict(open=90.,high=91.,low=89.,close=90.)})
        result=self.run_mode(candles,'AI_ONLY',[pred(0,.006)],detail)
        self.assertEqual([x['kind'] for x in result['events']],
                         ['LONG ENTRY','EMERGENCY SL'])
        self.assertLess(result['events'][1]['actual_fill_price'],
                        result['events'][1]['expected_fill_price'])

    def test_dca_one_shot_and_margin_preserved(self):
        candles=[row(0),row(1),row(2,close=98.,rsi=32.,previous_rsi=31.),
                 row(3,close=98.,rsi=33.,previous_rsi=32.),row(4,close=98.)]
        detail=fine(5)
        result=self.run_mode(candles,'AI_ONLY',[pred(0,0.006)],detail)
        dca=[e for e in result['events'] if e['kind']=='DCA']
        self.assertLessEqual(len(dca),1)
        if dca:
            self.assertAlmostEqual(dca[0]['margin_usdt'],50.)

    def test_reject_prediction_with_foreign_pair_model_or_candle(self):
        candles=[row(0),row(1)]
        for value in [pred(0,.006,model='foreign'),{**pred(0,.006),'pair':'ETH/USDT:USDT'},
                      pred(0,0.006,close=99.)]:
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    self.run_mode(candles,'AI_ONLY',[value])

    def test_rejected_do_predict_does_not_generate_trade(self):
        result=self.run_mode([row(0),row(1)],'AI_ONLY',[pred(0,.006,do_predict=0)])
        self.assertEqual(result['events'],[])
        self.assertEqual(result['report']['ai_prediction_count'],0)

    def test_duplicate_prediction_timestamps_must_agree(self):
        with self.assertRaisesRegex(ValueError,'CONFLICTING'):
            self.run_mode([row(0),row(1)],'AI_ONLY',[pred(0,.006),pred(0,-.006)])

    def test_no_prediction_no_ai_trades_no_invented_fill(self):
        result=self.run_mode([row(0),row(1)],'AI_ONLY',[])
        self.assertEqual(result['events'],[])
        self.assertEqual(result['report']['ai_prediction_count'],0)

    def test_native_capture_must_match_successful_research_report(self):
        import hashlib
        import json
        with tempfile.TemporaryDirectory() as d:
            folder=Path(d)
            prediction=folder/'freqai.csv'
            manifest=folder/'native-report.json'
            prediction.write_text('actual-model-output',encoding='utf8')
            with self.assertRaisesRegex(ValueError,'MISSING_NATIVE'):
                verify_native_prediction_evidence(prediction,manifest,HASH,DETAIL,MODEL)
            expected='sha256:'+hashlib.sha256(prediction.read_bytes()).hexdigest()
            verified=dict(exchange='okx',days=180,detail_timeframe='5m',
                dataset_sha256=HASH,detail_sha256=DETAIL,
                core_native_runtime_succeeded=True,freqai_native_runtime_succeeded=True,
                prediction_capture_verified=True,prediction_model_identifier=MODEL,
                prediction_capture_sha256=expected,prediction_capture_accepted=1)
            manifest.write_text(json.dumps(verified))
            self.assertEqual(verify_native_prediction_evidence(prediction,manifest,HASH,DETAIL,MODEL),expected)
            prediction.write_text('tampered after training')
            with self.assertRaisesRegex(ValueError,'INVALID_NATIVE'):
                verify_native_prediction_evidence(prediction,manifest,HASH,DETAIL,MODEL)

    def test_manual_outputs_are_sidecar_research_only(self):
        result=self.run_mode([row(0),row(1)],'AI_ONLY',[pred(0,.006)])
        with tempfile.TemporaryDirectory() as directory:
            paths=write_paper_outputs(Path(directory),result,'AI_ONLY')
            self.assertIn('events',paths)
            with Path(paths['events']).open() as file:
                rows=list(csv.DictReader(file))
            self.assertIn('expected_fill_price',rows[0])
            self.assertIn('actual_fill_price',rows[0])
            self.assertIn('fill_difference',rows[0])
            self.assertEqual(rows[0]['fill_source'],'SIMULATED_OHLCV_5M')

if __name__=='__main__': unittest.main()