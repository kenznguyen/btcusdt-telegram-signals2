"""End-to-end PAPER DCA: actual PaperLedger.submit -> process restart -> reconcile.

Requires QUANT_PAPER_SOURCE pointing to a checked-out PR67 tree. No live exchange.
"""
import os,sys,tempfile,unittest
from pathlib import Path
from quant_engine.dca_state import DcaStore

class PaperDcaEndToEnd(unittest.TestCase):
    def test_submit_restart_journal_and_idempotency(self):
        source=os.environ.get("QUANT_PAPER_SOURCE")
        if not source:
            if os.environ.get("QUANT_REQUIRE_PAPER_E2E") == "1":
                self.fail("PR67 PaperLedger source absent in mandatory integration step")
            self.skipTest("PR67 PaperLedger source absent; run dedicated CI integration step")
        sys.path.insert(0,source)
        try:
            from paper_execution.ledger import PaperLedger
            with tempfile.TemporaryDirectory() as tmp:
                dca_path=Path(tmp)/"dca.sqlite"
                paper_path=Path(tmp)/"paper.sqlite"
                ledger=PaperLedger(paper_path,max_position_base="1",fee_rate="0.0005")
                now=1800000000000
                def intent(identifier,target):
                    return dict(intentId=identifier,symbol="BTCUSDT",exchange="binance",
                        marketType="USDT_PERPETUAL",strategyVersion="quant-test",
                        modelVersion="none",datasetVersion="test:controlled",
                        targetPositionBase=target,limitPrice="100.1",decisionAtMs=now-100,
                        validUntilMs=now+30000,inputSnapshotId="controlled-test",mode="PAPER")
                def book(ts):
                    return dict(source="hummingbot",connector="binance_perpetual",
                        symbol="BTCUSDT",observedAtMs=ts,
                        bids=[dict(price="100",quantity="1")],
                        asks=[dict(price="100.1",quantity="1")])
                opening=ledger.submit(intent("entry-t1","0.1"),book(now),now)
                self.assertEqual(opening["status"],"FILLED")
                with DcaStore(str(dca_path)) as store:
                    self.assertTrue(store.reserve_once("BTCUSDT","trade-1","m15:1"))
                    self.assertTrue(store.bind_paper_intent("BTCUSDT","trade-1","dca-t1","LONG"))
                self.assertEqual(PaperLedger(paper_path,max_position_base="1").snapshot()["positionBase"],"0.1")
                # True paper submit, not hand-written paper_orders SQL.
                filled=ledger.submit(intent("dca-t1","0.2"),book(now+1),now+1)
                self.assertEqual(filled["status"],"FILLED")
                self.assertEqual(filled["filledBase"],"0.1")
                with DcaStore(str(dca_path)) as reopened:
                    self.assertFalse(reopened.reserve_once("BTCUSDT","trade-1","m15:2"))
                    self.assertTrue(reopened.reconcile_paper_fill("BTCUSDT","trade-1",paper_path))
                    self.assertFalse(reopened.reconcile_paper_fill("BTCUSDT","trade-1",paper_path))
                    self.assertEqual(reopened.read("BTCUSDT","trade-1")["fill_id"],filled["orderId"])
                # Submission retry is idempotent against persisted PaperLedger.
                after_restart=PaperLedger(paper_path,max_position_base="1")
                self.assertEqual(after_restart.submit(intent("dca-t1","0.2"),None,now+90000)["orderId"],filled["orderId"])
                snapshot=after_restart.snapshot()
                self.assertEqual(snapshot["positionBase"],"0.2")
                self.assertFalse(snapshot["liveTradingSupported"])
        finally:
            sys.path.remove(source)
if __name__=="__main__":unittest.main()
