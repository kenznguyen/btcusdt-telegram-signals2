import unittest
from quant_engine.trace_gate import audit

class CoverageAuditTests(unittest.TestCase):
 def test_missing_dca_branch_does_not_establish_full_parity(self):
  base={"dataset_sha256":"sha256:"+"a"*64,"events":[
    dict(id="LONG:10",kind="LONG ENTRY",candleTime=10,side="LONG",price=100.,
         confirmed_at_ms=900010,fees=None,net_pnl=None)]}
  k=dict(base,engine="kotlin");p=dict(base,engine="python")
  self.assertEqual(audit(k,p),(True,"MATCH"))
  # Full certification deliberately separate and requires independent branch runs.
 def test_dca_trace_disagreement_blocks_observed_parity(self):
  base=dict(id="LONG:10",kind="DCA",candleTime=10,side="LONG",price=100.,
         confirmed_at_ms=900010,fees=None,net_pnl=None)
  k=dict(engine="kotlin",dataset_sha256="sha256:"+"a"*64,events=[base])
  p=dict(engine="python",dataset_sha256="sha256:"+"a"*64,events=[dict(base,price=99.)])
  self.assertFalse(audit(k,p)[0])
if __name__=="__main__":unittest.main()
