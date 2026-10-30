"""Phase13: SHA-bound retrospective 30d stability; NOT an independent OOS test.

Uses actual virtual portfolio MTM equity, including open positions, and
refuses to turn reused model-development history into an untouched holdout.
Only paper research. No orders or strategy threshold changes.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

M15_MS = 900_000
WINDOW = 30 * 24 * 4
MODES = ("core-only", "ai-only", "dual")

class Phase13Error(ValueError):
    pass

def require(ok, reason):
    if not ok:
        raise Phase13Error(reason)

def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as src:
        for block in iter(lambda: src.read(1024 * 1024), b""):
            digest.update(block)
    return "sha256:" + digest.hexdigest()

def load_json(path):
    result = json.loads(Path(path).read_text(encoding="utf8"))
    require(isinstance(result, dict), "INVALID_PHASE13_JSON")
    return result

def read_equity(path):
    with Path(path).open(newline="", encoding="utf8") as stream:
        reader = csv.DictReader(stream)
        require(reader.fieldnames is not None and set((
            "candle_close_ms", "equity_mtm_ex_funding_usdt"
        )).issubset(reader.fieldnames), "INVALID_PHASE13_EQUITY_HEADER")
        out = []
        for row in reader:
            require(None not in row and all(v is not None for v in row.values()),
                    "MALFORMED_PHASE13_EQUITY_ROW")
            try:
                timestamp = int(row["candle_close_ms"])
                equity = float(row["equity_mtm_ex_funding_usdt"])
            except (ValueError, TypeError, OverflowError) as error:
                raise Phase13Error("INVALID_PHASE13_EQUITY_VALUE") from error
            require(str(timestamp) == row["candle_close_ms"] and
                    math.isfinite(equity) and equity > 0,
                    "INVALID_PHASE13_EQUITY_VALUE")
            out.append((timestamp, equity))
    require(len(out) == 6 * WINDOW, "PHASE13_EXPECTED_EXACT_180D_M15_EQUITY")
    require(all(b[0] - a[0] == M15_MS for a, b in zip(out, out[1:])),
            "PHASE13_EQUITY_GAP_OR_DUPLICATE")
    return out

def windows(equity, initial):
    previous = initial
    output = []
    for index in range(6):
        part = equity[index * WINDOW : (index + 1) * WINDOW]
        require(len(part) == WINDOW, "PHASE13_INCOMPLETE_WINDOW")
        peak = previous
        drawdown = 0.0
        for _, point in part:
            peak = max(peak, point)
            drawdown = max(drawdown, peak - point)
        ending = part[-1][1]
        output.append({
            "segment": index + 1,
            "start_ms": part[0][0],
            "end_ms": part[-1][0],
            "start_equity_usdt": round(previous, 8),
            "end_equity_usdt": round(ending, 8),
            "change_usdt": round(ending - previous, 8),
            "return_pct": round(100 * (ending / previous - 1.0), 6),
            "max_drawdown_usdt": round(drawdown, 8),
            "max_drawdown_pct_start_equity": round(100 * drawdown / previous, 6),
        })
        previous = ending
    return output

def inspect_stability(artifacts_root):
    result = dict(
        schemaVersion=1,
        audit="PHASE13_RETROSPECTIVE_EQUITY_STABILITY",
        retrospective_stability_verified=False,
        independent_oos_verified=False,
        oos_certified=False,
        feature_causality_verified=False,
        ai_promotion_eligible=False,
        ready_for_360=False,
        full_core_parity_certified=False,
        live_orders_enabled=False,
        blockers=[
            "REUSED_DEVELOPMENT_HISTORY_NOT_AN_INDEPENDENT_OOS_HOLDOUT",
            "FULL_FEATURE_PIPELINE_CAUSALITY_NOT_YET_VERIFIED",
            "FUNDING_LIQUIDATION_AND_NATIVE_PARITY_NOT_VERIFIED",
        ],
        errors=[],
    )
    try:
        root = Path(artifacts_root)
        phase12 = load_json(root / "paper/phase12-native-fit-label-audit.json")
        native = load_json(root / "native/native-research-180.json")
        require(phase12.get("actual_fit_sample_lineage_verified") is True and
                phase12.get("label_reconstruction_verified") is True and
                phase12.get("train_test_label_purge_verified") is True and
                phase12.get("errors") == [] and
                native.get("core_native_runtime_succeeded") is True and
                native.get("freqai_native_runtime_succeeded") is True,
                "PHASE13_PHASE12_NATIVE_NOT_VERIFIED")
        require(sha(root / "canonical/15m.csv") ==
                phase12.get("canonical_m15_sha256"),
                "PHASE13_CANONICAL_SHA_MISMATCH")
        cohort = {}
        dataset_sha = native.get("dataset_sha256")
        detail_sha = native.get("detail_sha256")
        require(isinstance(dataset_sha, str) and
                isinstance(detail_sha, str) and
                dataset_sha.startswith("sha256:") and
                detail_sha.startswith("sha256:"),
                "PHASE13_INVALID_NATIVE_SHA")
        span = None
        for mode in MODES:
            report_path = root / ("paper/portfolio-" + mode + "-report.json")
            csv_path = root / ("paper/portfolio-" + mode + "-equity.csv")
            paper = load_json(report_path)
            require(paper.get("mode") == mode.replace("-", "_").upper() and
                    paper.get("dataset_sha256") == dataset_sha and
                    paper.get("detail_sha256") == detail_sha and
                    paper.get("starting_capital_usdt") == 100.0 and
                    paper.get("freqai_oos_verified") is False and
                    paper.get("live_orders_enabled") is False,
                    "PHASE13_PORTFOLIO_PROVENANCE_MISMATCH")
            curve = read_equity(csv_path)
            dates = (curve[0][0], curve[-1][0])
            require(span is None or span == dates,
                    "PHASE13_PORTFOLIO_TIMEBASE_MISMATCH")
            span = dates
            segments = windows(curve, 100.0)
            require(math.isclose(curve[-1][1],
                    float(paper["equity_mtm_ex_funding_usdt"]),
                    rel_tol=0, abs_tol=1e-7),
                    "PHASE13_END_EQUITY_MISMATCH")
            peak = 100.0
            full_dd = 0.0
            for _, value in curve:
                peak = max(peak, value)
                full_dd = max(full_dd, peak - value)
            require(math.isclose(full_dd,
                    float(paper["max_drawdown_ex_funding_usdt"]),
                    rel_tol=0, abs_tol=1e-6),
                    "PHASE13_FULL_DRAWDOWN_MISMATCH")
            negatives = sum(s["return_pct"] < 0 for s in segments)
            cohort[mode.replace("-", "_").upper()] = {
                "equity_sha256": sha(csv_path),
                "portfolio_report_sha256": sha(report_path),
                "segments": segments,
                "negative_30d_segments": negatives,
                "worst_30d_return_pct": min(s["return_pct"] for s in segments),
                "best_30d_return_pct": max(s["return_pct"] for s in segments),
                "max_drawdown_usdt": round(full_dd, 8),
                "max_drawdown_pct_initial_capital": round(full_dd, 6),
                "final_equity_usdt": round(curve[-1][1], 8),
            }
        result.update(
            retrospective_stability_verified=True,
            dataset_sha256=dataset_sha,
            detail_sha256=detail_sha,
            canonical_m15_sha256=phase12["canonical_m15_sha256"],
            phase12_report_sha256=sha(root / "paper/phase12-native-fit-label-audit.json"),
            first_equity_candle_close_ms=span[0],
            last_equity_candle_close_ms=span[1],
            segments_30_days=6,
            modes=cohort,
        )
    except Phase13Error as exc:
        result["errors"].append(str(exc))
    except (OSError, UnicodeError, ValueError, TypeError, KeyError, csv.Error,
            OverflowError, ZeroDivisionError) as exc:
        result["errors"].append("PHASE13_MISSING_OR_MALFORMED_EVIDENCE")
        result["error_type"] = type(exc).__name__
    return result

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifacts-root", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    result = inspect_stability(args.artifacts_root)
    target = Path(args.out)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, indent=2, sort_keys=True,
                                 allow_nan=False) + "\n", encoding="utf8")
    print(json.dumps({k: result[k] for k in
                      ("retrospective_stability_verified", "independent_oos_verified",
                       "errors", "ready_for_360")}, sort_keys=True))
    return 0 if result["retrospective_stability_verified"] and not result["errors"] else 2

if __name__ == "__main__":
    raise SystemExit(main())
