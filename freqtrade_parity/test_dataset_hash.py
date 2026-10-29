import hashlib
import unittest
from freqtrade_parity.dataset_hash import dataset_hash,canonical_rows

class DatasetHashTests(unittest.TestCase):
    def test_known_kotlin_double_vector(self):
        m=[{"open_time":900000,"open":100.0,"high":101.0,"low":99.0,"close":100.5,"volume":3.0,"closed":True}]
        h=[{"open_time":0,"open":100.0,"high":102.0,"low":98.0,"close":101.0,"volume":12.0,"closed":True}]
        payload="15m,900000,100.0,101.0,99.0,100.5,3.0\n1h,0,100.0,102.0,98.0,101.0,12.0"
        self.assertEqual("sha256:"+hashlib.sha256(payload.encode()).hexdigest(),dataset_hash(m,h))
    def test_open_candle_exclusion_and_order(self):
        a={"open_time":0,"open":1.0,"high":2.0,"low":0.5,"close":1.5,"volume":5.0,"closed":True}
        b={**a,"open_time":900000,"closed":False}
        self.assertEqual(dataset_hash([a],[]),dataset_hash([b,a],[]))
        self.assertNotEqual(dataset_hash([a],[]),dataset_hash([{**a,"close":1.6}],[]))
    def test_non_finite_ohlcv_rejected(self):
        row={"open_time":0,"open":float("nan"),"high":2.0,"low":1.0,"close":1.5,"volume":5.0,"closed":True}
        with self.assertRaises(ValueError):dataset_hash([row],[])
if __name__=="__main__": unittest.main()
