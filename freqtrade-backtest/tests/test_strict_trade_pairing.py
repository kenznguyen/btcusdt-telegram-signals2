import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from strict_trade_pairing import pair_trade_events

def e(t, typ, price, qty=1, side="LONG"):
    return {"timestamp_ms": t, "type": typ, "side": side, "price": price, "quantity": qty}

class StrictTradePairingTest(unittest.TestCase):
    def test_exact_trade(self):
        android = [e(100,"ENTRY",100),e(200,"DCA",98),e(300,"TP",101,2)]
        report = pair_trade_events(android, list(android))
        self.assertTrue(report["parity_verified"])
        self.assertEqual(1, len(report["trades"]))
        self.assertEqual([],report["trades"][0]["differences"])
    def test_time_and_fill_differences_reported(self):
        android = [e(100,"ENTRY",100),e(200,"SOFT_SL",95)]
        ft = [e(105,"ENTRY",101),e(210,"SOFT_SL",94)]
        report = pair_trade_events(android,ft)
        self.assertFalse(report["parity_verified"])
        self.assertTrue(report["trades"][0]["differences"])
    def test_liquidation_is_not_emergency_stop(self):
        android=[e(100,"ENTRY",100),e(200,"EMERGENCY_SL",90)]
        ft=[e(100,"ENTRY",100),e(200,"LIQUIDATION",90)]
        self.assertFalse(pair_trade_events(android,ft)["parity_verified"])
    def test_absent_trace_fails(self):
        self.assertFalse(pair_trade_events([],[])["parity_verified"])
        self.assertFalse(pair_trade_events([e(100,"ENTRY",100)],[])["parity_verified"])
if __name__=="__main__":
    unittest.main()
