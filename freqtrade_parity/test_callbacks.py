import unittest
from types import SimpleNamespace
from freqtrade_parity.callbacks import PaperCallbackCore

class FakeTrade:
    def __init__(self):
        self.custom={}
        self.stake_amount=50.
        self.nr_of_successful_entries=1
        self.has_open_orders=False
        self.is_short=False
    def get_custom_data(self,key,default=None):
        return self.custom.get(key,default)
    def set_custom_data(self,key,value):
        self.custom[key]=value

class CallbackTests(unittest.TestCase):
    def test_dca_persists_request_and_is_not_repeated_after_restart(self):
        trade=FakeTrade()
        row={"open_time":1800000,"close":97000.,"rsi":24.,"previous_rsi":23.,"adx":46.}
        a=PaperCallbackCore()
        self.assertEqual((50.,"kotlin_dca_once"),a.dca_request(trade,row,"LONG",100000.,100.,False))
        self.assertIsNone(PaperCallbackCore().dca_request(trade,row,"LONG",100000.,100.,False))
        self.assertEqual("REQUESTED",trade.custom["chart_pro_dca_status"])

    def test_filled_dca_also_blocks_restart_and_pending_blocks_requests(self):
        trade=FakeTrade()
        row={"open_time":1800000,"close":97000.,"rsi":24.,"previous_rsi":23.,"adx":46.}
        self.assertIsNone(PaperCallbackCore().dca_request(trade,row,"LONG",100000.,100.,True))
        trade.has_open_orders=False
        trade.nr_of_successful_entries=2
        self.assertIsNone(PaperCallbackCore().dca_request(trade,row,"LONG",100000.,100.,False))

    def test_exit_priority_and_confirmed_close(self):
        core=PaperCallbackCore()
        candle={"open_time":1800000,"open":100000.,"high":105000.,"low":92000.,"close":101000.,
                "rsi":80.,"previous_open":102000.,"previous_close":101000.,
                "h1_plus":10.,"h1_minus":25.,"h1_adx":40.}
        result=core.exit_decision("LONG",100000.,candle)
        self.assertEqual("EMERGENCY SL",result["kind"])
        self.assertIsNone(core.custom_exit_reason("LONG",100000.,candle))
        candle.update(low=97000.,close=98000.,rsi=45.)
        result=core.exit_decision("LONG",100000.,candle)
        self.assertEqual("SOFT SL",result["kind"])
        self.assertEqual(2700000,result["confirmed_at_ms"])
        self.assertEqual("SOFT SL",core.custom_exit_reason("LONG",100000.,candle))

    def test_no_signal_without_complete_closed_candle_context(self):
        self.assertIsNone(PaperCallbackCore().custom_exit_reason("LONG",100000.,{"open_time":0}))

if __name__=="__main__":
    unittest.main()
