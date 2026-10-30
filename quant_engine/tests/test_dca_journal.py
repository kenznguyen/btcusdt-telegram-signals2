import json,sqlite3,tempfile,unittest
from pathlib import Path
from quant_engine.dca_state import DcaStore,StateConflict

class JournalRecoveryTests(unittest.TestCase):
 def test_real_paper_schema_recovery(self):
  with tempfile.TemporaryDirectory() as d:
   db=Path(d)/"dca.db";journal=Path(d)/"paper.db"
   with sqlite3.connect(journal) as c:
    c.execute("CREATE TABLE paper_orders(intent_id TEXT PRIMARY KEY,payload_hash TEXT,order_id TEXT,status TEXT,document TEXT)")
    def record(status,filled,remaining):
     x=dict(intentId="dca-t1",orderId="paper-fill-1",status=status,mode="PAPER",side="BUY",filledBase=filled,remainingBase=remaining,averagePrice="101",feeQuote="0.01")
     with sqlite3.connect(journal) as c:
      c.execute("INSERT OR REPLACE INTO paper_orders VALUES (?,?,?,?,?)",("dca-t1","hash","paper-fill-1",status,json.dumps(x)))
   with DcaStore(str(db)) as store:
    self.assertTrue(store.reserve_once("BTCUSDT","trade-1","m15:1"))
    store.bind_paper_intent("BTCUSDT","trade-1","dca-t1","LONG")
   with DcaStore(str(db)) as reopened:
    self.assertFalse(reopened.reserve_once("BTCUSDT","trade-1","m15:2"))
    self.assertFalse(reopened.reconcile_paper_fill("BTCUSDT","trade-1",journal))
    record("PARTIALLY_FILLED","0.01","0.02")
    self.assertFalse(reopened.reconcile_paper_fill("BTCUSDT","trade-1",journal))
    record("FILLED","0.03","0")
    self.assertTrue(reopened.reconcile_paper_fill("BTCUSDT","trade-1",journal))
    self.assertFalse(reopened.reconcile_paper_fill("BTCUSDT","trade-1",journal))
    self.assertEqual(reopened.read("BTCUSDT","trade-1")["status"],"FILLED")
 def test_reject_missing_journal_and_rebinding(self):
  with tempfile.TemporaryDirectory() as d, DcaStore(str(Path(d)/"state.db")) as store:
   store.reserve_once("BTCUSDT","t","c")
   store.bind_paper_intent("BTCUSDT","t","intent-a","SHORT")
   with self.assertRaises(StateConflict):store.bind_paper_intent("BTCUSDT","t","intent-b","SHORT")
   with self.assertRaises(StateConflict):store.reconcile_paper_fill("BTCUSDT","t",Path(d)/"missing.db")
if __name__=="__main__":unittest.main()
