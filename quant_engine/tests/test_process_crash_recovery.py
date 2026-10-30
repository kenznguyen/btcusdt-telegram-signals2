"""Process-death DCA recovery against genuine PaperLedger and SQLite, controlled book."""
import json,os,subprocess,sys,tempfile,unittest
from pathlib import Path
from quant_engine.dca_state import DcaStore

SCRIPT=r'''
import os,sys
from pathlib import Path
from quant_engine.dca_state import DcaStore
from paper_execution.ledger import PaperLedger
root=Path(sys.argv[1]);stage=sys.argv[2];now=1800000000000
def intent(target):
 return dict(intentId="dca-crash",symbol="BTCUSDT",exchange="binance",marketType="USDT_PERPETUAL",
 strategyVersion="test",modelVersion="none",datasetVersion="controlled",targetPositionBase=target,
 limitPrice="100.1",decisionAtMs=now-100,validUntilMs=now+30000,
 inputSnapshotId="controlled",mode="PAPER")
def book(ts):
 return dict(source="hummingbot",connector="binance_perpetual",symbol="BTCUSDT",observedAtMs=ts,
 bids=[dict(price="100",quantity="1")],asks=[dict(price="100.1",quantity="1")])
ledger=PaperLedger(root/"paper.sqlite",max_position_base="1")
ledger.submit({**intent("0.1"),"intentId":"entry-crash"},book(now),now)
with DcaStore(str(root/"dca.sqlite")) as store:
 assert store.reserve_once("BTCUSDT","trade-crash","m15:1")
 if stage!="reservation":
  assert store.bind_paper_intent("BTCUSDT","trade-crash","dca-crash","LONG")
 if stage=="submit":
  assert ledger.submit(intent("0.2"),book(now+1),now+1)["status"]=="FILLED"
 if stage=="confirmation":
  assert ledger.submit(intent("0.2"),book(now+1),now+1)["status"]=="FILLED"
  assert store.reconcile_paper_fill("BTCUSDT","trade-crash",root/"paper.sqlite")
os._exit(47)
'''

class ProcessCrashRecovery(unittest.TestCase):
 def test_killed_after_reservation_submit_and_confirmation(self):
  source=os.environ.get("QUANT_PAPER_SOURCE")
  if not source:
   if os.environ.get("QUANT_REQUIRE_PAPER_E2E")=="1":self.fail("PaperLedger required")
   self.skipTest("requires genuine PR67 PaperLedger")
  sys.path.insert(0,source)
  try:
   from paper_execution.ledger import PaperLedger
   for stage in ("reservation","submit","confirmation"):
    with self.subTest(stage=stage),tempfile.TemporaryDirectory() as temp:
     root=Path(temp)
     env=dict(os.environ,PYTHONPATH=os.pathsep.join([os.getcwd(),source]))
     run=subprocess.run([sys.executable,"-c",SCRIPT,str(root),stage],env=env,
                        capture_output=True,text=True,timeout=30)
     self.assertEqual(run.returncode,47,run.stderr)
     with DcaStore(str(root/"dca.sqlite")) as state:
      self.assertFalse(state.reserve_once("BTCUSDT","trade-crash","m15:2"))
      status=state.read("BTCUSDT","trade-crash")["status"]
      if stage=="reservation":
       self.assertEqual(status,"RESERVED")
       with self.assertRaises(Exception):
        state.reconcile_paper_fill("BTCUSDT","trade-crash",root/"paper.sqlite")
      else:
       self.assertEqual(state.reconcile_paper_fill("BTCUSDT","trade-crash",root/"paper.sqlite"),
                        stage=="submit")
       self.assertEqual(state.read("BTCUSDT","trade-crash")["status"],"FILLED")
       self.assertFalse(state.reconcile_paper_fill("BTCUSDT","trade-crash",root/"paper.sqlite"))
     position=PaperLedger(root/"paper.sqlite",max_position_base="1").snapshot()["positionBase"]
     self.assertEqual(position,"0.1" if stage=="reservation" else "0.2")
     evidence_dir=os.environ.get("QUANT_CRASH_EVIDENCE_DIR")
     if evidence_dir:
      import shutil
      dest=Path(evidence_dir)/stage;dest.mkdir(parents=True,exist_ok=True)
      for f in ("dca.sqlite","paper.sqlite"):
       with __import__("sqlite3").connect(root/f) as conn:
        with __import__("sqlite3").connect(dest/f) as backup:
         conn.backup(backup)
      (dest/"result.json").write_text(json.dumps(dict(stage=stage,exit_code=47,
        position=position,no_duplicate_reservation=True,verified=True),indent=2)+"\n")
  finally:
   sys.path.remove(source)
if __name__=="__main__":unittest.main()
