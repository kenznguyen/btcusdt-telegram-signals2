import unittest
from freqtrade_parity.reconciliation import reconcile_trace_envelopes

class TraceReportTest(unittest.TestCase):
    def test_matching_events_prices_and_times(self):
        h="sha256:"+"a"*64
        a={"engine":"kotlin","dataset_sha256":h,"events":[{"kind":"DCA","candleTime":900000,"id":"p1","price":100.0,"confirmed_at_ms":1800000}]}
        b={"engine":"freqtrade","dataset_sha256":h,"events":[{"kind":"DCA","candleTime":900000,"id":"p1","price":100.5,"confirmed_at_ms":1800000}]}
        report=reconcile_trace_envelopes(a,b,h)
        self.assertFalse(report["parity_verified"])
        self.assertEqual(0.5,report["trades"][0]["fill_difference"])
        self.assertEqual(100.,report["trades"][0]["expected_fill_price"])
        self.assertEqual(100.5,report["trades"][0]["actual_fill_price"])
    def test_unmatched_exits_block_parity(self):
        h="sha256:"+"b"*64
        a={"engine":"kotlin","dataset_sha256":h,"events":[{"kind":"SOFT SL","candleTime":1,"id":"p1","price":100.,"confirmed_at_ms":2}]}
        b={"engine":"freqtrade","dataset_sha256":h,"events":[{"kind":"TAKE PROFIT","candleTime":1,"id":"p1","price":100.,"confirmed_at_ms":2}]}
        result=reconcile_trace_envelopes(a,b,h)
        self.assertFalse(result["parity_verified"])
        self.assertEqual(2,len(result["trades"]))
    def test_empty_and_invalid_provenance_fail_closed(self):
        h="sha256:"+"c"*64
        self.assertFalse(reconcile_trace_envelopes(None,None,h)["parity_verified"])
        self.assertFalse(reconcile_trace_envelopes({"engine":"kotlin","dataset_sha256":h,"events":[]},{"engine":"freqtrade","dataset_sha256":h,"events":[]},h)["parity_verified"])

if __name__=="__main__":unittest.main()
