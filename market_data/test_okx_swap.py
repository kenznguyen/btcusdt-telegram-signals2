import unittest
from market_data.okx_swap import OkxSwapAdapter

START = 1_800_000_000_000
STEP = 900_000
INSTRUMENT = {
    "instId":"BTC-USDT-SWAP","instType":"SWAP","ctType":"linear",
    "state":"live","baseCcy":"BTC","quoteCcy":"USDT","settleCcy":"USDT",
}

def row(opened, confirm="1"):
    return [str(opened),"100.00","105.00","99.00","102.00","12","1.250","125.000",confirm]

class FakeOKX:
    def __init__(self, rows=None, instrument=None, server=None):
        self.rows = rows if rows is not None else []
        self.instrument = instrument if instrument is not None else INSTRUMENT
        self.server = server if server is not None else START + 10*STEP
        self.calls = []
    def __call__(self, path, params):
        self.calls.append((path,params))
        if path.endswith("/instruments"): return [self.instrument]
        if path.endswith("/time"): return [{"ts":str(self.server)}]
        if path.endswith("/candles"): return self.rows
        raise AssertionError(path)

class OkxSwapAdapterTests(unittest.TestCase):
    def test_maps_contract_volume_to_btc_and_quote_turnover(self):
        fake=FakeOKX([row(START+STEP),row(START)])
        candles=OkxSwapAdapter(fake).fetch_closed_window("15m",START,START+2*STEP,now_ms=START+3*STEP)
        self.assertEqual([c.open_time_ms for c in candles],[START,START+STEP])
        self.assertEqual(candles[0].volume_btc,"1.250")
        self.assertEqual(candles[0].turnover_usdt,"125.000")
        self.assertEqual(candles[0].as_dict()["exchange"],"okx")
        self.assertEqual(fake.calls[-1][1]["instId"],"BTC-USDT-SWAP")

    def test_requires_exchange_confirm_flag_and_server_clock(self):
        fake=FakeOKX([row(START,"1"),row(START+STEP,"1")],server=START+STEP+100)
        result=OkxSwapAdapter(fake).fetch_closed_window("15m",START,START+2*STEP,now_ms=START+2*STEP)
        self.assertEqual([c.open_time_ms for c in result],[START])

    def test_rejects_inactive_or_non_linear_instrument(self):
        for field,value in (("state","suspend"),("ctType","inverse"),("settleCcy","BTC")):
            bad=dict(INSTRUMENT); bad[field]=value
            with self.subTest(field=field), self.assertRaises(ValueError):
                OkxSwapAdapter(FakeOKX(instrument=bad)).fetch_closed_window("15m",START,START+STEP,now_ms=START+STEP)

    def test_rejects_malformed_confirmation_and_ohlc(self):
        malformed=row(START); malformed[8]="2"
        bad_ohlc=row(START); bad_ohlc[3]="106"
        for rows in ([malformed],[bad_ohlc]):
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                OkxSwapAdapter(FakeOKX(rows)).fetch_closed_window("15m",START,START+STEP,now_ms=START+STEP)

    def test_rejects_duplicate_timestamps(self):
        with self.assertRaisesRegex(ValueError,"Duplicate"):
            OkxSwapAdapter(FakeOKX([row(START),row(START)])).fetch_closed_window("15m",START,START+STEP,now_ms=START+STEP)

    def test_limits_window_to_one_exchange_page(self):
        with self.assertRaisesRegex(ValueError,"page limit"):
            OkxSwapAdapter(FakeOKX()).fetch_closed_window("15m",START,START+301*STEP,now_ms=START+302*STEP)

if __name__ == "__main__":
    unittest.main()
