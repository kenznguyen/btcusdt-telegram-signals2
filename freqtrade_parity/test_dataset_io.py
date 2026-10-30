import csv
import json
import tempfile
import unittest
from pathlib import Path
from freqtrade_parity.dataset_io import read_closed_csv, generate_manifest

class CanonicalInputTest(unittest.TestCase):
    def test_rejects_gaps_duplicate_and_forming_candle(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"m15.csv"
            self.write(p,[[0,1,2,.5,1.5,5,1],[900000,1,2,.5,1.5,5,1]])
            rows=read_closed_csv(p,900000)
            self.assertEqual(2,len(rows))
            self.write(p,[[0,1,2,.5,1.5,5,1],[1800000,1,2,.5,1.5,5,1]])
            with self.assertRaises(ValueError):read_closed_csv(p,900000)
            self.write(p,[[0,1,2,.5,1.5,5,1],[0,1,2,.5,1.5,5,1]])
            with self.assertRaises(ValueError):read_closed_csv(p,900000)
            self.write(p,[[0,1,2,.5,1.5,5,1],[900000,1,2,.5,1.5,5,0]])
            with self.assertRaises(ValueError):read_closed_csv(p,900000)
    def test_manifest_requires_both_timeframes(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"m15.csv";h=Path(tmp)/"h1.csv"
            self.write(p,[[0,1,2,.5,1.5,5,1]])
            self.write(h,[[0,1,2,.5,1.5,5,1]])
            manifest=generate_manifest(p,h)
            self.assertEqual("CHARTPRO-OHLCV-V2",manifest["format"])
            self.assertEqual(1,manifest["m15_count"])
            self.assertEqual(1,manifest["h1_count"])
            self.assertTrue(manifest["dataset_sha256"].startswith("sha256:"))
    def write(self,path,rows):
        with path.open("w",newline="") as f:
            w=csv.writer(f);w.writerow(["open_time","open","high","low","close","volume","closed"]);w.writerows(rows)

if __name__=="__main__":unittest.main()
