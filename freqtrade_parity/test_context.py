import unittest
from freqtrade_parity.context import enrich_closed_m15

def candle(i,step,close=100.):
    return {"open_time":i*step,"open":close,"high":close+2,
            "low":close-2,"close":close,"volume":1.,"closed":True}

class ContextTest(unittest.TestCase):
    def test_h1_context_excludes_same_hour_and_never_uses_forming_bar(self):
        m15=[candle(i,900000,100.+i%8) for i in range(150)]
        h1=[candle(i,3600000,100.+i%7) for i in range(60)]
        baseline=enrich_closed_m15(m15,h1)
        target=baseline[140]
        self.assertEqual(target["h1_source_open_time"],(140//4-1)*3600000)
        h1.append({**candle(35,3600000,999999.),"closed":False})
        self.assertEqual(target,enrich_closed_m15(m15,h1)[140])
    def test_missing_ohlcv_and_unclosed_m15_are_never_filled_with_future_values(self):
        m15=[candle(i,900000,100.+i%5) for i in range(140)]
        h1=[candle(i,3600000,100.+i%9) for i in range(50)]
        m15[-1]["closed"]=False
        result=enrich_closed_m15(m15,h1)
        self.assertEqual(len(result),139)
        self.assertEqual(result[-1]["open_time"],138*900000)
        self.assertIsNone(result[0]["previous_rsi"])
        self.assertIsNone(result[0]["h1_adx"])
    def test_explicit_both_m15_h1_rows_required(self):
        self.assertEqual([],enrich_closed_m15([],[]))

if __name__=="__main__":
    unittest.main()
