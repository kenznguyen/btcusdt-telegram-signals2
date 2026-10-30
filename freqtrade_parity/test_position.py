import unittest
from freqtrade_parity.position import Position, PaperPositionAdapter, reconcile_fills

class PositionAdapterTest(unittest.TestCase):
    def test_dca_only_once_even_when_callback_repeats(self):
        adapter=PaperPositionAdapter()
        pos=adapter.open("LONG",100.,100000.,900000)
        first=adapter.dca(pos,97000.,1800000,adx=46,rsi=24,previous_rsi=23)
        self.assertTrue(first.dca_used)
        second=adapter.dca(first,96000.,1800000,adx=50,rsi=25,previous_rsi=24)
        self.assertIs(first,second)

    def test_emergency_wins_over_soft_and_tp(self):
        adapter=PaperPositionAdapter()
        pos=adapter.open("LONG",100.,100000.,900000)
        out=adapter.exit_on_candle(pos,1800000,100000.,92000.,105000.,101000.,rsi=80.,
            previous_open=102000.,previous_close=101000.,
            h1_plus=10.,h1_minus=25.,h1_adx=40.)
        self.assertEqual("EMERGENCY SL",out["kind"])
        self.assertEqual(1800000,out["confirmed_at_ms"])

    def test_soft_stop_is_confirmed_on_close_not_intrabar_threshold(self):
        adapter=PaperPositionAdapter()
        pos=adapter.open("LONG",100.,100000.,900000)
        out=adapter.exit_on_candle(pos,1800000,100000.,97000.,100500.,98000.,rsi=45.,
            previous_open=101000.,previous_close=100000.,
            h1_plus=10.,h1_minus=25.,h1_adx=40.)
        self.assertEqual("SOFT SL",out["kind"])
        self.assertEqual(2700000,out["confirmed_at_ms"])
        self.assertEqual(2700000,out["simulated_fill_at_ms"])
        self.assertAlmostEqual(98000.*(1.-0.0005),out["expected_fill_price"])

    def test_fill_reconciliation_preserves_mismatch(self):
        pairs=reconcile_fills([{"id":"a","kind":"SOFT SL","candleTime":1,"price":100.}],
                              [{"id":"a","kind":"SOFT SL","candleTime":1,"price":99.}])
        self.assertEqual(-1.,pairs[0]["fill_difference"])
        self.assertEqual(100.,pairs[0]["expected_fill_price"])
        self.assertEqual(99.,pairs[0]["actual_fill_price"])
        self.assertFalse(pairs[0]["fill_match"])

if __name__=="__main__":
    unittest.main()
