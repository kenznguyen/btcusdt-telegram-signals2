import unittest
from pipeline.core_strategy import indicators, produce


def candles(count, interval, start=1_700_000_000_000, trend=1.0):
    rows=[]
    price=100.0
    for i in range(count):
        opened=start+i*interval
        price += trend * (0.15 if i%7 else 0.3)
        rows.append({"openTimeMs":opened,"closeTimeMs":opened+interval,"availableAtMs":opened+interval,
          "open":str(price-0.05),"high":str(price+0.2),"low":str(price-0.2),"close":str(price),"volume":"1","isClosed":True})
    return rows


def window(rows, timeframe):
    return {"timeframe":timeframe,"candles":rows,"coverage":{"expected":len(rows),"returned":len(rows),"complete":True},
      "datasetVersion":"sha256:"+"a"*64}


class CoreStrategyTest(unittest.TestCase):
    def test_indicators_produce_finite_rsi_adx_and_di_after_warmup(self):
        values=indicators(candles(100,900_000))
        self.assertIsNotNone(values[-1]["rsi"])
        self.assertIsNotNone(values[-1]["adx"])
        self.assertIsNotNone(values[-1]["plus_di"])
        self.assertIsNotNone(values[-1]["minus_di"])

    def test_missing_or_incomplete_market_windows_never_generate_intent(self):
        now=1_700_000_000_000+500*900_000
        m15=window(candles(100,900_000), "15m")
        h1=window(candles(100,3_600_000), "1h")
        m15["coverage"]["complete"]=False
        result=produce(m15,h1,{"positionBase":"0","averageEntryPrice":"0","realizedPnlQuote":"0","feesQuote":"0"},
          {"owner":None,"dcaUsed":False},None,now)
        self.assertEqual(result["action"],"WAIT")
        self.assertIsNone(result["intent"])

    def test_producer_requires_book_for_executable_intents(self):
        start=1_700_000_000_000
        m15rows=candles(120,900_000,start)
        h1rows=candles(120,3_600_000,start)
        now=m15rows[-1]["closeTimeMs"]
        result=produce(window(m15rows,"15m"),window(h1rows,"1h"),
          {"positionBase":"0","averageEntryPrice":"0","realizedPnlQuote":"0","feesQuote":"0"},
          {"owner":None,"dcaUsed":False},None,now)
        self.assertEqual(result["action"],"WAIT")
        self.assertEqual(result["reason"],"CORE_ORDER_BOOK_UNAVAILABLE")


if __name__ == "__main__":
    unittest.main()
