import hashlib
import struct
import unittest
from freqtrade_parity.dataset_hash import dataset_hash,canonical_rows

class DatasetHashTests(unittest.TestCase):
    def test_known_kotlin_double_vector(self):
        m=[{"open_time":900000,"open":100.0,"high":101.0,"low":99.0,"close":100.5,"volume":3.0,"closed":True}]
        h=[{"open_time":0,"open":100.0,"high":102.0,"low":98.0,"close":101.0,"volume":12.0,"closed":True}]
        from freqtrade_parity.dataset_hash import canonical_bytes
        self.assertEqual("sha256:"+hashlib.sha256(canonical_bytes(m,h)).hexdigest(),dataset_hash(m,h))
    def test_open_candle_exclusion_and_order(self):
        a={"open_time":0,"open":1.0,"high":2.0,"low":0.5,"close":1.5,"volume":5.0,"closed":True}
        b={**a,"open_time":900000,"closed":False}
        self.assertEqual(dataset_hash([a],[]),dataset_hash([b,a],[]))
        self.assertNotEqual(dataset_hash([a],[]),dataset_hash([{**a,"close":1.6}],[]))
    def test_binary_canonical_golden_bytes(self):
        from freqtrade_parity.dataset_hash import canonical_bytes
        row={"open_time":0,"open":1.0,"high":2.0,"low":0.5,"close":1.5,"volume":5.0,"closed":True}
        expected=b"CHARTPRO-OHLCV-V2\x00"+b"M15\x00"+struct.pack(">q5d",0,1.,2.,0.5,1.5,5.)+b"H1\x00"
        self.assertEqual(expected,canonical_bytes([row],[]))
        self.assertEqual("sha256:8e39ddb3256cd38e90e160a40767c4d99e93570bca1d402d1972772ee2722a93",dataset_hash([row],[]))
    def test_non_finite_ohlcv_rejected(self):
        row={"open_time":0,"open":float("nan"),"high":2.0,"low":1.0,"close":1.5,"volume":5.0,"closed":True}
        with self.assertRaises(ValueError):dataset_hash([row],[])
if __name__=="__main__": unittest.main()
