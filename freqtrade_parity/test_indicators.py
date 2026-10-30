import unittest
from freqtrade_parity.indicators import kotlin_rma, indicator_series, prior_closed_h1_index

class IndicatorParityTest(unittest.TestCase):
    def test_kotlin_rma_seeds_after_n_valid_values_and_carries_gaps(self):
        self.assertEqual(kotlin_rma([None, 1., 2., None, 3., 6.], 3),
                         [None, None, None, None, 2., 10. / 3.])
    def test_h1_excludes_same_hour_and_open_hour(self):
        hours = [{"open_time": h*3600000, "closed": True} for h in range(5)]
        self.assertEqual(prior_closed_h1_index(4*3600000+900000, hours), 3)
        self.assertEqual(prior_closed_h1_index(0, hours), None)
        self.assertEqual(prior_closed_h1_index(3*3600000, hours), 2)
        self.assertIsNone(prior_closed_h1_index(900000, [{"open_time":0,"closed":False}]))
    def test_wilder_indicator_warmup_and_flat_candles(self):
        rows = [{"open_time":i*900000,"open":100.,"high":101.,"low":99.,
                 "close":100.,"volume":10.,"closed":True} for i in range(75)]
        result=indicator_series(rows)
        self.assertEqual(len(result),75)
        self.assertEqual(result[0]["rsi"], None)
        self.assertEqual(result[-1]["rsi"],50.)
        self.assertIsNone(result[-1]["adx"])
    def test_open_candles_not_part_of_indicator_series(self):
        rows=[{"open_time":i*900000,"open":100.,"high":102.,"low":98.,
               "close":100. + i%5,"volume":1.,"closed":True} for i in range(90)]
        a=indicator_series(rows)
        rows[-1]["closed"]=False
        b=indicator_series(rows)
        self.assertEqual(len(a),90)
        self.assertEqual(len(b),89)

if __name__=="__main__":
    unittest.main()
