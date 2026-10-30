import unittest
from unittest.mock import patch
from quant_engine.core_strategy import State,Position,replay

def candle(i, *, o=100.,h=101.,l=99.,c=100.):
 return dict(open_time=i*900000,open=o,high=h,low=l,close=c,volume=1.,closed=True)
def hourly(i):
 return dict(open_time=i*3600000,open=100.,high=101.,low=99.,close=100.,volume=1.,closed=True)
def points(n,*,rsi=40.,adx=50.,plus=40.,minus=10.):
 return [dict(rsi=rsi,adx=adx,plus_di=plus,minus_di=minus) for _ in range(n)]

class IndependentCoreBranchTests(unittest.TestCase):
 def run_with(self,m15,h1,initial,m15points,h1points):
  with patch("quant_engine.core_strategy.indicator_series",side_effect=[m15points,h1points]):
   return replay(m15,h1,initial)
 def test_dca_only_once_even_if_next_candle_qualifies(self):
  m=[candle(4*i) for i in range(3)]
  m[1]=candle(4,o=99.,h=100.,l=97.,c=98.)
  m[2]=candle(8,o=99.,h=100.,l=97.,c=98.)
  # 1h time bucket must have prior H1 data
  h=[hourly(0),hourly(1)]
  init=State(100,Position("LONG",1.,100.,50.,0.,100.,0),0)
  x=[dict(rsi=v,adx=50.,plus_di=40.,minus_di=10.) for v in (19.,25.,27.)]
  state,events=self.run_with(m,h,init,x,points(2))
  self.assertEqual([e["kind"] for e in events],["DCA"])
  self.assertTrue(state.position.dca_used)
  self.assertEqual(state.position.dca_margin,50.)
 def test_soft_sl_on_two_bearish_candles_with_h1_reversal(self):
  m=[candle(4*i) for i in range(3)]
  m[0]=candle(0,o=102.,h=103.,l=99.,c=101.)
  m[1]=candle(4,o=102.,h=103.,l=99.,c=101.)
  m[2]=candle(8,o=100.,h=101.,l=96.,c=97.)
  h=[hourly(0),hourly(1)]
  init=State(100,Position("LONG",1.,100.,50.,0.,100.,0),4*900000)
  _,ev=self.run_with(m,h,init,points(3),points(2,plus=5.,minus=40.))
  self.assertEqual([e["kind"] for e in ev],["SOFT SL"])
  self.assertAlmostEqual(ev[0]["price"],97.*(1.-5./10000.))
 def test_emergency_overrides_soft_and_tp_even_without_hourly(self):
  m=[candle(0,o=102.,h=103.,l=99.,c=101.),candle(4,o=100.,h=102.,l=90.,c=101.)]
  init=State(100,Position("LONG",1.,100.,50.,0.,100.,0),0)
  _,ev=self.run_with(m,[],init,points(2,rsi=90.),[])
  self.assertEqual([e["kind"] for e in ev],["EMERGENCY SL"])
if __name__=="__main__":unittest.main()
