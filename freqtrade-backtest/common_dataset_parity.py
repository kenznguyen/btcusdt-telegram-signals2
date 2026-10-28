"""Prepare a fail-closed parity handoff on one immutable OKX Futures OHLCV dataset.

Android StrategyEngine must replay the exported CSVs and return its event JSON.
This report never calls Freqtrade trades Android results without Kotlin proof.
"""
import argparse
import hashlib
import json
from pathlib import Path


def verify_manifest(root):
    manifest = json.loads((root / "shared-ohlcv-manifest.json").read_text())
    datasets = manifest["datasets"]
    if set(datasets) != {"5m", "15m", "1h"}:
        raise ValueError("All shared 5m, 15m, 1h frames required")
    for timeframe, entry in datasets.items():
        actual = hashlib.sha256((root / entry["file"]).read_bytes()).hexdigest()
        if actual != entry["sha256"]:
            raise ValueError(f"Shared OHLCV checksum mismatch: {timeframe}")
    return {k: entry["sha256"] for k, entry in datasets.items()}


def compare_events(android_events, freqtrade_events):
    """Only compare explicit common-schema event records, never infer from PnL."""
    def index(events):
        out = {}
        for event in events:
            key = (str(event["timestamp_ms"]), event["side"], event["type"])
            if key in out:
                raise ValueError("Duplicate event key")
            out[key] = event
        return out
    android = index(android_events)
    freqtrade = index(freqtrade_events)
    keys = sorted(set(android) | set(freqtrade))
    result = []
    for key in keys:
        a = android.get(key)
        f = freqtrade.get(key)
        status = ("android_only" if f is None else
                  "freqtrade_only" if a is None else
                  "missing_fill_price" if a.get("price") is None or f.get("price") is None else
                  "price_disagreement" if abs(float(a["price"]) - float(f["price"])) > 1e-8 else
                  "quantity_disagreement" if a.get("quantity") is not None and f.get("quantity") is not None
                      and abs(float(a["quantity"]) - float(f["quantity"])) > 1e-10 else
                  "missing_quantity" if a.get("quantity") is None or f.get("quantity") is None else
                  "matched")
        result.append({"key": key, "status": status,
                       "android_price": a.get("price") if a else None,
                       "freqtrade_price": f.get("price") if f else None,
                       "android_quantity": a.get("quantity") if a else None,
                       "freqtrade_quantity": f.get("quantity") if f else None})
    return {"events": result,
            "all_events_match": bool(result) and all(x["status"] == "matched" for x in result),
            "event_count": len(result)}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--ohlcv", required=True, type=Path)
    p.add_argument("--android-events", type=Path)
    p.add_argument("--freqtrade-events", type=Path)
    p.add_argument("--output", required=True, type=Path)
    args = p.parse_args()
    checksums = verify_manifest(args.ohlcv)
    report = {"shared_ohlcv_sha256": checksums,
              "android_replay_provided": bool(args.android_events),
              "freqtrade_events_provided": bool(args.freqtrade_events),
              "parity_verified": False}
    if args.android_events and args.freqtrade_events:
        comparison = compare_events(json.loads(args.android_events.read_text()),
                                    json.loads(args.freqtrade_events.read_text()))
        report["comparison"] = comparison
        report["parity_verified"] = comparison["all_events_match"]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("Android-Kotlin parity verified:", report["parity_verified"])


if __name__ == "__main__":
    main()
