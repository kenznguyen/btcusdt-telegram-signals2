"""Report evidence with strict separation of live-market vs controlled scenarios."""
REQUIRED=("LONG ENTRY","SHORT ENTRY","DCA","TAKE PROFIT","SOFT SL","EMERGENCY SL")

def summarize(market,scenarios,paper):
    market=market if isinstance(market,dict) else {}
    scenarios=scenarios if isinstance(scenarios,dict) else {}
    paper=paper if isinstance(paper,dict) else {}
    market_ok=market.get("parity_verified") is True
    controlled_ok=(scenarios.get("controlled_branch_parity_verified") is True and
                   all(scenarios.get("cases",{}).get(name,{}).get("passed") is True
                       for name in ("DCA","SOFT SL","EMERGENCY SL")))
    paper_ok=(paper.get("paper_dca_e2e_verified") is True and
              paper.get("order_status")=="FILLED" and
              paper.get("restart_reconciliation") is True and
              paper.get("duplicate_dca_blocked") is True and
              paper.get("live_trading_supported") is False)
    coverage=market.get("coverage_matrix",{})
    if not isinstance(coverage,dict):coverage={}
    missing=[name for name in REQUIRED if not (isinstance(coverage.get(name),dict) and
            coverage[name].get("matched") is True and coverage[name].get("observed",0)>0)]
    blockers=[]
    if not market_ok:blockers.append("MARKET_TRACE_PARITY_NOT_VERIFIED")
    blockers.extend("MARKET_"+name.replace(" ","_")+"_NOT_OBSERVED" for name in missing)
    if not controlled_ok:blockers.append("CONTROLLED_BRANCH_PARITY_NOT_VERIFIED")
    if not paper_ok:blockers.append("PAPER_DCA_E2E_NOT_VERIFIED")
    # Full certification deliberately requires a separate runtime/coverage review.
    blockers.append("INDEPENDENT_FULL_CORE_REVIEW_REQUIRED")
    return {"parity_verified":market_ok,
            "controlled_branch_parity_verified":controlled_ok,
            "paper_dca_e2e_verified":paper_ok,
            "market_coverage_matrix":coverage,
            "full_core_parity_certified":False,
            "certification_blockers":blockers}
