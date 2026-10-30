"""Fail-closed event reconciliation; inputs must come from independently captured traces."""
from .rules import compare_event_traces

def reconcile_trace_envelopes(kotlin_trace,freqtrade_trace,dataset_sha256):
    gate=compare_event_traces(kotlin_trace,freqtrade_trace,dataset_sha256)
    if not isinstance(kotlin_trace,dict) or not isinstance(freqtrade_trace,dict):
        return {"parity_verified":False,"reason":gate["reason"],"trades":[]}
    if gate["reason"] in ("WRONG_ENGINE","DATASET_MISMATCH","INVALID_DATASET_CHECKSUM","MISSING_TRACE_PROVENANCE"):
        return {"parity_verified":False,"reason":gate["reason"],"trades":[]}
    def index(trace):
        result={}
        for item in trace.get("events",[]):
            if not isinstance(item,dict):continue
            key=(item.get("id"),item.get("kind"),item.get("candleTime"))
            if key in result:raise ValueError("duplicate event identity")
            result[key]=item
        return result
    expected=index(kotlin_trace);actual=index(freqtrade_trace)
    report=[]
    for key in sorted(set(expected)|set(actual),key=str):
        a=expected.get(key);b=actual.get(key)
        ep=a.get("price") if a else None
        ap=b.get("price") if b else None
        diff=ap-ep if type(ep) in (int,float) and type(ap) in (int,float) else None
        confirmed_a=a.get("confirmed_at_ms") if a else None
        confirmed_b=b.get("confirmed_at_ms") if b else None
        match=a is not None and b is not None and diff is not None and abs(diff)<1e-8 and confirmed_a==confirmed_b
        report.append({"id":key[0],"kind":key[1],"candleTime":key[2],
                       "expected_fill_price":ep,"actual_fill_price":ap,"fill_difference":diff,
                       "expected_confirmed_at_ms":confirmed_a,"actual_confirmed_at_ms":confirmed_b,
                       "fill_match":match})
    verified=bool(report) and all(row["fill_match"] for row in report) and gate["parity_verified"]
    return {"parity_verified":verified,"reason":"MATCH" if verified else "MISMATCH_OR_INCOMPLETE",
            "dataset_sha256":dataset_sha256,"trades":report}
