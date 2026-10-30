"""Consolidated evidence never turns controlled scenarios into market certification."""
import unittest
from quant_engine.evidence_summary import summarize


class EvidenceSummaryTests(unittest.TestCase):
    def setUp(self):
        self.market={"parity_verified":True,"reason":"MATCH","coverage_matrix":{
            "LONG ENTRY":{"observed":1,"matched":True},
            "SHORT ENTRY":{"observed":0,"matched":False},
            "DCA":{"observed":0,"matched":False},
            "TAKE PROFIT":{"observed":1,"matched":True},
            "SOFT SL":{"observed":0,"matched":False},
            "EMERGENCY SL":{"observed":0,"matched":False},
        }}
        self.scenarios={"controlled_branch_parity_verified":True,
            "cases":{name:{"passed":True,"reason":"MATCH","scenario_type":"CONTROLLED_SYNTHETIC"}
                     for name in ("SHORT ENTRY","DCA","SOFT SL","EMERGENCY SL")}}
        self.paper={"paper_dca_e2e_verified":True,"order_status":"FILLED",
                    "restart_reconciliation":True,"duplicate_dca_blocked":True,
                    "live_trading_supported":False}

    def test_all_scenarios_do_not_replace_missing_market_coverage(self):
        report=summarize(self.market,self.scenarios,self.paper)
        self.assertTrue(report["parity_verified"])
        self.assertTrue(report["controlled_branch_parity_verified"])
        self.assertTrue(report["paper_dca_e2e_verified"])
        self.assertFalse(report["full_core_parity_certified"])
        self.assertIn("MARKET_SHORT_ENTRY_NOT_OBSERVED",report["certification_blockers"])
        self.assertNotIn("CONTROLLED_BRANCH_PARITY_NOT_VERIFIED",report["certification_blockers"])

    def test_missing_paper_proof_fails_closed(self):
        report=summarize(self.market,self.scenarios,None)
        self.assertFalse(report["paper_dca_e2e_verified"])
        self.assertIn("PAPER_DCA_E2E_NOT_VERIFIED",report["certification_blockers"])
        self.assertFalse(report["full_core_parity_certified"])

    def test_wrong_paper_mode_is_rejected(self):
        paper=dict(self.paper,live_trading_supported=True)
        report=summarize(self.market,self.scenarios,paper)
        self.assertFalse(report["paper_dca_e2e_verified"])

    def test_missing_independent_trace_fails_closed(self):
        report=summarize({"parity_verified":False},self.scenarios,self.paper)
        self.assertFalse(report["parity_verified"])
        self.assertIn("MARKET_TRACE_PARITY_NOT_VERIFIED",report["certification_blockers"])

if __name__=="__main__":unittest.main()
