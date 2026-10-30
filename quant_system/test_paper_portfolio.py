"""Three shared paper slots and 10%-equity per entry — synthetic regression."""
import unittest
from quant_system.paper_portfolio import PortfolioConfig,replay_portfolio

M15=900000
T0=1800000000000
SHA='sha256:'+'a'*64
DETAIL='sha256:'+'b'*64
MODEL='chart-pro-okx-shadow-v1'

def candle(i,**opts):
    base=dict(open_time=T0+i*M15,open=100.,high=101.,low=99.,close=100.,
        volume=3.,closed=True,rsi=40.,previous_rsi=39.,adx=48.,
        previous_open=100.,previous_close=100.,
        h1_plus=30.,h1_minus=10.,h1_adx=28.,
        h1_source_open_time=T0-7200000)
    base.update(opts)
    return base

def fine(count,changes=None):
    changes=changes or {}
    bars=[]
    for i in range(count):
        for j in range(3):
            bar=dict(open_time=T0+i*M15+j*300000,open=100.,high=101.,
                     low=99.,close=100.,volume=1.,closed=True)
            bar.update(changes.get((i,j),{}))
            bars.append(bar)
    return bars

def prediction(i,value=.006):
    return dict(open_time=T0+i*M15,open=100.,high=101.,low=99.,
        close=100.,volume=3.,predicted_return=value,do_predict=1,
        model_identifier=MODEL,source='freqai-native-backtest',
        pair='BTC/USDT:USDT')

def run(candles,preds,mode='AI_ONLY',detail=None,config=None):
    return replay_portfolio(candles,detail or fine(len(candles)),preds,
        mode=mode,dataset_sha256=SHA,detail_sha256=DETAIL,
        model_identifier=MODEL,config=config or PortfolioConfig())

class ThreeSlotPaperTests(unittest.TestCase):
    def test_exact_three_slots_and_ten_percent_each_using_current_equity(self):
        candles=[candle(i) for i in range(6)]
        result=run(candles,[prediction(i) for i in range(5)])
        entry=[e for e in result['events'] if e['kind']=='LONG ENTRY']
        self.assertEqual(len(entry),3)
        self.assertAlmostEqual(entry[0]['margin_usdt'],10.,places=5)
        self.assertTrue(all(0<e['margin_usdt']<=10. for e in entry))
        self.assertEqual(result['report']['max_positions'],3)
        self.assertEqual(result['report']['entry_margin_pct'],.1)
        self.assertEqual(result['report']['trade_count_open'],3)
        self.assertGreaterEqual(result['report']['position_limit_denials'],1)
        self.assertEqual(max(x['open_positions'] for x in result['equity_curve']),3)

    def test_dual_reserves_one_core_slot_when_ai_occupies_two(self):
        candles=[candle(i) for i in range(6)]
        candles[2]=candle(2,previous_rsi=29.,rsi=31.)
        result=run(candles,[prediction(i) for i in range(5)],mode='DUAL')
        entry=[e for e in result['events'] if e['kind'].endswith('ENTRY')]
        self.assertEqual([e['origin'] for e in entry],['AI','AI','CORE'])
        self.assertEqual(result['report']['trade_count_open'],3)
        self.assertGreaterEqual(result['report']['ai_source_slot_denials'],1)

    def test_dca_is_single_adjustment_per_position_and_ten_percent_entry(self):
        candles=[candle(0),candle(1),candle(2,close=98.,rsi=32.,previous_rsi=31.),
                 candle(3,close=98.,rsi=33.,previous_rsi=32.),
                 candle(4,close=98.)]
        result=run(candles,[prediction(0)],detail=fine(5,{
            (2,0):dict(open=98.,high=99.,low=97.5,close=98.),
            (3,0):dict(open=98.,high=99.,low=97.5,close=98.)}))
        dca=[e for e in result['events'] if e['kind']=='DCA']
        self.assertLessEqual(len(dca),1)
        if dca:
            self.assertAlmostEqual(dca[0]['margin_usdt'],10.,places=4)
        self.assertEqual(result['report']['max_positions'],3)

    def test_emergency_sl_exits_each_position_independently(self):
        candles=[candle(i) for i in range(6)]
        detail=fine(6,{(4,0):dict(open=90.,high=92.,low=89.,close=90.)})
        result=run(candles,[prediction(i) for i in range(3)],detail=detail)
        exits=[e for e in result['events'] if e['kind']=='EMERGENCY SL']
        self.assertEqual(len(exits),3)
        self.assertEqual(len({e['trade_id'] for e in exits}),3)
        self.assertEqual(result['report']['trade_count_closed'],3)
        self.assertEqual(result['report']['trade_count_open'],0)
        self.assertTrue(all(e['actual_fill_price']<e['expected_fill_price']
                            for e in exits))

    def test_wrong_configuration_fails_closed(self):
        with self.assertRaises(ValueError):
            PortfolioConfig(max_positions=0)
        with self.assertRaises(ValueError):
            PortfolioConfig(entry_margin_pct=.5)
        with self.assertRaises(ValueError):
            PortfolioConfig(max_total_margin_pct=.2)

    def test_ai_always_passes_shared_margin_and_position_gate(self):
        candles=[candle(i) for i in range(6)]
        config=PortfolioConfig(max_positions=3,entry_margin_pct=.1,
                               max_total_margin_pct=.3,ai_slots_in_dual=2)
        result=run(candles,[prediction(i) for i in range(5)],config=config)
        self.assertLessEqual(result['report']['trade_count_open'],3)
        self.assertFalse(result['report']['native_orders_enabled'])
        self.assertFalse(result['report']['freqai_oos_verified'])
        self.assertFalse(result['report']['ready_for_360'])
        self.assertFalse(result['report']['liquidation_verified'])

if __name__=='__main__':
    unittest.main()
