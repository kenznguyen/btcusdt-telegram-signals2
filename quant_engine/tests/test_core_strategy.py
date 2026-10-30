import unittest
from quant_engine.core_strategy import Config,State,Position,replay,fill,stop_fill,exit_fill
from quant_engine.core_indicators import indicator_series

class CorePortTests(unittest.TestCase):
    def test_kotlin_wilder_warmup_and_flat(self):
        candles=[dict(open_time=i*900000,open=100,high=102,low=98,close=100,volume=1,closed=True) for i in range(100)]
        p=indicator_series(candles)
        self.assertEqual(p[-1]["rsi"],50)
        self.assertIsNone(p[-1]["adx"])
    def test_emergency_before_rsi_warmup_and_without_h1(self):
        candles=[dict(open_time=i*900000,open=100,high=101,low=80 if i==1 else 99,close=90 if i==1 else 100,volume=1,closed=True) for i in range(25)]
        pos=Position("LONG",1,100,50,0,100,0)
        state,events=replay(candles,[],State(100,pos,0))
        self.assertIsNone(state.position)
        self.assertEqual(events[0]["kind"],"EMERGENCY SL")
        self.assertEqual(events[0]["candleTime"],900000)
    def test_excludes_forming_candles(self):
        candles=[dict(open_time=i*900000,open=100,high=101,low=99,close=100,volume=1,closed=True) for i in range(40)]
        prior=replay(candles,[])
        forming=dict(candles[-1],open_time=40*900000,low=1,closed=False)
        self.assertEqual(prior,replay(candles+[forming],[]))
    def test_kotlin_stop_slippage(self):
        self.assertAlmostEqual(stop_fill("LONG",97,100,Config()),97*(1-5/10000))
    def test_soft_sl_fills_only_at_confirmed_candle_close_from_pr67(self):
        cfg=Config()
        candle=dict(open=105.0,close=95.0)
        self.assertAlmostEqual(exit_fill('LONG','SOFT SL',candle,100.0,cfg),fill(95.0,'SELL',cfg))
        self.assertNotAlmostEqual(exit_fill('LONG','SOFT SL',candle,100.0,cfg),stop_fill('LONG',100.0*(1-35/1300),105.0,cfg))
    def test_state_resume_does_not_reprocess_same_candle(self):
        candles=[dict(open_time=i*900000,open=100,high=101,low=80 if i==31 else 99,close=100,volume=1,closed=True) for i in range(40)]
        start=State(100,Position("LONG",1,100,50,0,100,0),30*900000)
        end,events=replay(candles,[],start)
        again,duplicate=replay(candles,[],end)
        self.assertEqual(again,end)
        self.assertEqual(duplicate,[])

if __name__=="__main__":unittest.main()
