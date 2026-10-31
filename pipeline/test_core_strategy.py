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

    def test_valid_entry_signal_waits_when_execution_book_is_missing(self):
        from unittest.mock import patch
        start=1_700_000_000_000
        m15rows=candles(120,900_000,start)
        now=m15rows[-1]["closeTimeMs"]
        h1_start=(now//3_600_000*3_600_000)-120*3_600_000
        h1rows=candles(120,3_600_000,h1_start)
        m15_values=[{"rsi":20.0,"adx":25.0} for _ in m15rows]
        m15_values[-2]={"rsi":29.0,"adx":25.0}
        m15_values[-1]={"rsi":35.0,"adx":30.0}
        h1_values=[{"plus_di":40.0,"minus_di":10.0,"adx":30.0} for _ in h1rows]
        with patch("pipeline.core_strategy.indicators", side_effect=[m15_values,h1_values]):
            result=produce(window(m15rows,"15m"),window(h1rows,"1h"),
              {"positionBase":"0","averageEntryPrice":"0","realizedPnlQuote":"0","feesQuote":"0"},
              {"owner":None,"dcaUsed":False},None,now,initial_capital="0.01",max_position_base="0.01")
        self.assertEqual(result["action"],"BUY")
        self.assertEqual(result["reason"],"CORE_ORDER_BOOK_UNAVAILABLE")
        self.assertIsNone(result["intent"])

    def test_native_core_produces_valid_long_intent_on_entry_cross(self):
        from unittest.mock import patch
        from pipeline.core_signal import validate
        start=1_700_000_000_000
        m15rows=candles(120,900_000,start)
        now=m15rows[-1]["closeTimeMs"]
        h1_start=(now//3_600_000*3_600_000)-120*3_600_000
        h1rows=candles(120,3_600_000,h1_start)
        m15_values=[{"rsi":20.0,"adx":25.0} for _ in m15rows]
        m15_values[-2]={"rsi":29.0,"adx":25.0}
        m15_values[-1]={"rsi":35.0,"adx":30.0}
        h1_values=[{"plus_di":40.0,"minus_di":10.0,"adx":30.0} for _ in h1rows]
        close=float(m15rows[-1]["close"])
        book={"source":"hummingbot","connector":"binance_perpetual","symbol":"BTCUSDT",
              "observedAtMs":now-1000,"bids":[{"price":str(close-0.01),"quantity":"1"}],
              "asks":[{"price":str(close+0.01),"quantity":"1"}]}
        with patch("pipeline.core_strategy.indicators",side_effect=[m15_values,h1_values]):
            result=produce(window(m15rows,"15m"),window(h1rows,"1h"),
                {"positionBase":"0","averageEntryPrice":"0","realizedPnlQuote":"0","feesQuote":"0"},
                {"owner":None,"dcaUsed":False},book,now,initial_capital="100",max_position_base="10")
        self.assertEqual(result["action"],"BUY")
        self.assertEqual(result["reason"],"RSI_ADX_ENTRY")
        self.assertIsNotNone(result["intent"])
        self.assertEqual(validate(result["intent"],now)["action"],"BUY")
        self.assertEqual(result["intent"]["source"],"STRATEGY_CORE")

    def test_native_core_emits_smart_dca_intent_using_initial_margin(self):
        from unittest.mock import patch
        start=1_700_000_000_000
        m15rows=candles(120,900_000,start)
        now=m15rows[-1]["closeTimeMs"]
        h1_start=(now//3_600_000*3_600_000)-120*3_600_000
        h1rows=candles(120,3_600_000,h1_start)
        close=float(m15rows[-1]["close"])
        average=close/0.98
        m15_values=[{"rsi":30.0,"adx":50.0} for _ in m15rows]
        m15_values[-2]={"rsi":29.0,"adx":50.0}
        m15_values[-1]={"rsi":35.0,"adx":50.0}
        h1_values=[{"plus_di":40.0,"minus_di":10.0,"adx":30.0} for _ in h1rows]
        book={"source":"hummingbot","connector":"binance_perpetual","symbol":"BTCUSDT",
              "observedAtMs":now-1000,"bids":[{"price":str(close-0.01),"quantity":"1"}],
              "asks":[{"price":str(close+0.01),"quantity":"1"}]}
        with patch("pipeline.core_strategy.indicators",side_effect=[m15_values,h1_values]):
            result=produce(window(m15rows,"15m"),window(h1rows,"1h"),
                {"positionBase":"0.01","averageEntryPrice":str(average),"realizedPnlQuote":"0","feesQuote":"0"},
                {"owner":"STRATEGY_CORE","dcaUsed":False,"initialMarginQuote":"50"},book,now)
        self.assertEqual(result["reason"],"DCA")
        self.assertEqual(result["action"],"BUY")
        self.assertGreater(float(result["intent"]["targetPositionBase"]),0.01)

    def test_native_core_prioritizes_emergency_soft_stop_and_take_profit_exits(self):
        from unittest.mock import patch
        start=1_700_000_000_000
        m15rows=candles(120,900_000,start)
        now=m15rows[-1]["closeTimeMs"]
        h1_start=(now//3_600_000*3_600_000)-120*3_600_000
        h1rows=candles(120,3_600_000,h1_start)
        close=float(m15rows[-1]["close"])
        h1_bear=[{"plus_di":10.0,"minus_di":40.0,"adx":40.0} for _ in h1rows]
        h1_bull=[{"plus_di":40.0,"minus_di":10.0,"adx":40.0} for _ in h1rows]
        book={"source":"hummingbot","connector":"binance_perpetual","symbol":"BTCUSDT",
              "observedAtMs":now-1000,"bids":[{"price":str(close-0.01),"quantity":"1"}],
              "asks":[{"price":str(close+0.01),"quantity":"1"}]}
        def evaluate_case(side, average, candle_open, candle_close, candle_low, candle_high, rsi, h1_values):
            m15rows[-1].update(open=str(candle_open),close=str(candle_close),low=str(candle_low),high=str(candle_high))
            m15_values=[{"rsi":rsi,"adx":30.0} for _ in m15rows]
            m15_values[-2]={"rsi":rsi-1 if side=="LONG" else rsi+1,"adx":30.0}
            with patch("pipeline.core_strategy.indicators",side_effect=[m15_values,h1_values]):
                return produce(window(m15rows,"15m"),window(h1rows,"1h"),
                    {"positionBase":"0.01" if side=="LONG" else "-0.01","averageEntryPrice":str(average),
                     "realizedPnlQuote":"0","feesQuote":"0"},
                    {"owner":"STRATEGY_CORE","dcaUsed":True,"initialMarginQuote":"50"},book,now)
        # Emergency threshold is evaluated before the Soft SL threshold.
        emergency_average=close/0.90
        emergency=evaluate_case("LONG",emergency_average,close,close,emergency_average*0.89,close,
                                 50.0,h1_bear)
        self.assertEqual(emergency["reason"],"EMERGENCY_SL")
        self.assertEqual(emergency["action"],"CLOSE")
        # Soft SL needs two bearish M15 candles and an H1 reversal above its ADX threshold.
        soft_average=close/0.96
        m15rows[-2].update(open=str(close+1),close=str(close))
        soft=evaluate_case("LONG",soft_average,close+1,close,soft_average*0.96,close+2,
                           50.0,h1_bear)
        self.assertEqual(soft["reason"],"SOFT_SL")
        self.assertEqual(soft["action"],"CLOSE")
        # TP requires RSI threshold and ROE >= +5%.
        tp_average=close/1.01
        take=evaluate_case("LONG",tp_average,close-1,close,close-2,close+1,80.0,h1_bull)
        self.assertEqual(take["reason"],"TAKE_PROFIT")
        self.assertEqual(take["action"],"CLOSE")


if __name__ == "__main__":
    unittest.main()
