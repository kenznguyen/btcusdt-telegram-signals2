import unittest
from quant_engine.intrabar_audit import inspect_stop
class IntrabarTests(unittest.TestCase):
 def test_missing_m1_is_not_certified(self):
  event={"kind":"EMERGENCY SL","candleTime":0,"side":"LONG","price":93}
  self.assertFalse(inspect_stop(event,[],60000)["verified"])
 def test_intrabar_extreme_is_not_actual_fill(self):
  event={"kind":"SOFT SL","candleTime":0,"side":"LONG","price":97}
  candles=[{"open_time":i*300000,"open":99.,"low":95.-i,"high":101.} for i in range(3)]
  result=inspect_stop(event,candles,300000)
  self.assertTrue(result["verified"])
  self.assertEqual(result["intrabar_extreme"],93.)
  self.assertIsNone(result["actual_fill_price"])
  self.assertFalse(result["execution_verified"])
if __name__=="__main__":unittest.main()
