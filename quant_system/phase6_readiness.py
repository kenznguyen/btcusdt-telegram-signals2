"""Phase 6: read-only 180-day research diagnostics, NOT OOS certification."""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re

DAY_MS = 86_400_000
MODES = ("CORE_ONLY", "AI_ONLY", "DUAL")
TRAIN_RE = re.compile(
    r"Training BTC/USDT:USDT, 1/1 pairs from (\d{4}-\d\d-\d\d \d\d:\d\d:\d\d) "
    r"to (\d{4}-\d\d-\d\d \d\d:\d\d:\d\d), (\d+)/(\d+) trains"
)


class EvidenceError(ValueError):
    pass


def require(ok, reason):
    if not ok:
        raise EvidenceError(reason)


def sha(path):
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(block)
    return "sha256:" + hasher.hexdigest()


def data(path):
    obj = json.loads(path.read_text(encoding="utf8"))
    require(isinstance(obj, dict), "INVALID_EVIDENCE_JSON")
    return obj


def numeric(value):
    try:
        require(not isinstance(value, bool), "INVALID_NUMERIC_REPORT")
        n = float(value)
        require(math.isfinite(n), "INVALID_NUMERIC_REPORT")
        return n
    except (TypeError, ValueError, OverflowError) as error:
        raise EvidenceError("INVALID_NUMERIC_REPORT") from error


def millisecond(value):
    try:
        n = int(value)
        require(str(n) == str(value) and n >= 0, "INVALID_EVENT_TIMESTAMP")
        return n
    except (TypeError, ValueError, OverflowError) as error:
        raise EvidenceError("INVALID_EVENT_TIMESTAMP") from error


def train_windows(logfile, start, end):
    text = logfile.read_text(encoding="utf8", errors="replace")
    windows = []
    for match in TRAIN_RE.finditer(text):
        values = []
        for ts in match.group(1, 2):
            values.append(int(datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
                              .replace(tzinfo=timezone.utc).timestamp() * 1000))
        begin, until = values
        require(begin < until and until <= end, "TRAIN_WINDOW_OUTSIDE_REPLAY")
        require(20 * DAY_MS <= until - begin <= 45 * DAY_MS,
                "UNEXPECTED_TRAIN_WINDOW_LENGTH")
        windows.append(dict(start_ms=begin, end_ms=until,
                            index=int(match.group(3)), total=int(match.group(4))))
    require(bool(windows), "MISSING_FREQAI_TRAINING_WINDOWS")
    require(all(w["index"] == i + 1 for i, w in enumerate(windows)),
            "NONSEQUENTIAL_TRAIN_LOG")
    require(all(w["end_ms"] > windows[i-1]["end_ms"]
                for i, w in enumerate(windows) if i > 0),
            "NONMONOTONIC_TRAIN_WINDOWS")
    require(windows[0]["end_ms"] <= start, "TRAINING_NOT_BEFORE_FIRST_TEST_WINDOW")
    require(windows[-1]["total"] == len(windows), "INCOMPLETE_FREQAI_TRAINING_LOG")
    return windows


def audit_mode(root, summary, mode, attestations, start, end):
    slug = mode.lower().replace("_", "-")
    filename = "paper-" + slug + "-trades.csv"
    path = root / filename
    require(attestations.get(filename) == sha(path), "PHASE4_EVIDENCE_CHANGED")
    with path.open(newline="", encoding="utf8") as stream:
        reader = csv.DictReader(stream)
        require(reader.fieldnames is not None and
                set(("trade_id", "entry_at_ms", "exit_at_ms",
                     "net_pnl_ex_funding_usdt")).issubset(reader.fieldnames),
                "TRADE_EVIDENCE_INCOMPLETE")
        trades = list(reader)
    require(all(None not in row for row in trades), "MALFORMED_TRADE_ROW")
    windows = [dict(window_index=i + 1, start_ms=start + i * 30 * DAY_MS,
                    end_ms=start + (i + 1) * 30 * DAY_MS, closed_trades=0,
                    net_pnl_ex_funding_usdt=0.0, win_trades=0, loss_trades=0)
               for i in range(6)]
    closed_ids = set()
    for row in trades:
        ident = row["trade_id"]
        require(bool(ident) and ident not in closed_ids, "DUPLICATE_TRADE_ID")
        closed_ids.add(ident)
        stamp = millisecond(row["entry_at_ms"])
        finish = millisecond(row["exit_at_ms"])
        require(start <= stamp < end and stamp <= finish <= end, "TRADE_OUTSIDE_REPLAY")
        pnl = numeric(row["net_pnl_ex_funding_usdt"])
        w = windows[min(5, (stamp - start) // (30 * DAY_MS))]
        w["closed_trades"] += 1
        w["net_pnl_ex_funding_usdt"] += pnl
        w["win_trades"] += int(pnl > 0)
        w["loss_trades"] += int(pnl < 0)

    closed_net = sum(w["net_pnl_ex_funding_usdt"] for w in windows)
    # The account immediately deducts entry fees of positions still OPEN.
    # Those fees are omitted from the closed trade CSV, so reconcile them
    # against checksum-attested events instead of reporting false mismatches.
    events_name = "paper-" + slug + "-events.csv"
    events_path = root / events_name
    require(attestations.get(events_name) == sha(events_path),
            "PHASE4_EVIDENCE_CHANGED")
    with events_path.open(newline="", encoding="utf8") as stream:
        reader = csv.DictReader(stream)
        require(reader.fieldnames and
                set(("trade_id", "kind", "fee_usdt")).issubset(reader.fieldnames),
                "EVENT_EVIDENCE_INCOMPLETE")
        events = list(reader)
    require(all(None not in row for row in events), "MALFORMED_EVENT_ROW")
    opened = {e["trade_id"] for e in events
              if e["kind"] in ("LONG ENTRY", "SHORT ENTRY")}
    open_ids = opened - closed_ids
    open_fees = sum(numeric(e["fee_usdt"]) for e in events
                    if e["trade_id"] in open_ids and
                    e["kind"] in ("LONG ENTRY", "SHORT ENTRY", "DCA"))
    require(open_fees >= 0, "INVALID_OPEN_POSITION_FEES")
    total = closed_net - open_fees
    record = summary.get(mode)
    require(isinstance(record, dict), "MISSING_STRATEGY_REPORT")
    require(len(trades) == record.get("trade_count_closed") and
            len(open_ids) == record.get("trade_count_open") and
            math.isclose(total, numeric(record.get("realized_net_ex_funding_usdt")),
                         rel_tol=1e-8, abs_tol=1e-6), "TRADE_PNL_REPORT_MISMATCH")
    return dict(closed_trades=len(trades), closed_trade_net_pnl_usdt=closed_net,
                open_entry_fees_usdt=open_fees, net_pnl_ex_funding_usdt=total,
                max_drawdown_ex_funding_usdt=numeric(record.get("max_drawdown_ex_funding_usdt")),
                starting_capital_usdt=numeric(record.get("starting_capital_usdt")),
                windows=windows)


def assess_readiness(folder):
    root = Path(folder)
    result = dict(schemaVersion=1, audit="PHASE6_RESEARCH_DIAGNOSTICS",
        research_report_verified=False, oos_certified=False,
        ai_promotion_eligible=False, ready_for_360=False,
        full_core_parity_certified=False, live_orders_enabled=False,
        blockers=["NO_PREDICTION_TO_MODEL_FOLD_PROVENANCE",
                  "NO_PURGED_LABEL_HORIZON_ATTESTATION",
                  "INDEPENDENT_OOS_PERFORMANCE_UNVERIFIED",
                  "NATIVE_TRADE_PARITY_UNVERIFIED",
                  "FUNDING_MARK_LIQUIDATION_UNVERIFIED",
                  "EXCHANGE_EXECUTION_FILLS_UNVERIFIED"],
        errors=[], modes={}, freqai={})
    try:
        paper = root / "paper"
        native = root / "native"
        upstream = data(paper / "paper-180-independent-audit.json")
        require(upstream.get("artifact_integrity_verified") is True and
                upstream.get("full_core_parity_certified") is False and
                upstream.get("ready_for_360") is False, "PHASE4_AUDIT_NOT_VERIFIED")
        phase5 = data(paper / "paper-180-source-contention.json")
        require(phase5.get("contention_audit_verified") is True and
                phase5.get("errors") == [] and phase5.get("ready_for_360") is False,
                "PHASE5_CONTENTION_NOT_VERIFIED")
        summary_file = paper / "paper-180-summary.json"
        hashes = upstream.get("artifact_sha256") or {}
        require(hashes.get(summary_file.name) == sha(summary_file),
                "PHASE4_EVIDENCE_CHANGED")
        summary = data(summary_file)
        require(summary.get("phase") == "PAPER_180_ONLY" and
                summary.get("paper_trade_bearing_verified") is True,
                "PAPER_180_NOT_TRADE_BEARING")
        start = millisecond(summary.get("start_ms"))
        end = millisecond(summary.get("end_ms"))
        require(end - start == 180 * DAY_MS, "INVALID_180_DAY_WINDOW")
        research = data(native / "native-research-180.json")
        require(research.get("core_native_runtime_succeeded") is True and
                research.get("freqai_native_runtime_succeeded") is True and
                research.get("freqai_oos_verified") is False and
                research.get("full_core_parity_certified") is False and
                research.get("funding_mark_full_coverage_verified") is False,
                "INCONSISTENT_NATIVE_RESEARCH_PROVENANCE")
        require(research.get("dataset_sha256") == summary.get("dataset_sha256") and
                research.get("detail_sha256") == summary.get("detail_sha256") and
                type(research.get("prediction_capture_accepted")) is int and
                research["prediction_capture_accepted"] > 0,
                "MISMATCHED_NATIVE_DATASET")
        windows = train_windows(native / "freqai-native-180.log", start, end)
        result["freqai"] = dict(training_windows_observed=len(windows),
            first_train_end_ms=windows[0]["end_ms"],
            last_train_end_ms=windows[-1]["end_ms"],
            accepted_forecasts=research["prediction_capture_accepted"],
            per_prediction_training_fold_mapping_verified=False,
            interpretation="Training log windows; not causal/OOS certification")
        result["modes"] = {mode: audit_mode(paper, summary, mode, hashes, start, end)
                           for mode in MODES}
        if result["modes"]["AI_ONLY"]["net_pnl_ex_funding_usdt"] < 0:
            result["blockers"].append("AI_ONLY_NEGATIVE_REALIZED_PAPER_PNL")
        if result["modes"]["DUAL"]["net_pnl_ex_funding_usdt"] < 0:
            result["blockers"].append("DUAL_NEGATIVE_REALIZED_PAPER_PNL")
        if phase5.get("core_entries_blocked_by_ai_position", 0) > 0:
            result["blockers"].append("CORE_ENTRIES_DISPLACED_BY_AI_POSITION")
        result["research_report_verified"] = True
    except EvidenceError as error:
        result["errors"].append(str(error))
    except (OSError, UnicodeError, ValueError, TypeError, KeyError, csv.Error) as error:
        result["errors"].append("MISSING_OR_MALFORMED_ARTIFACT")
        result["evidence_error_type"] = type(error).__name__
    return result


def main():
    parser = argparse.ArgumentParser(description="Read-only Phase 6 research diagnostics")
    parser.add_argument("--artifacts-root", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    result = assess_readiness(args.artifacts_root)
    dest = Path(args.out)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n",
                    encoding="utf8")
    print(json.dumps({key: result[key] for key in
                      ("research_report_verified", "oos_certified",
                       "ai_promotion_eligible", "ready_for_360", "errors")},
                     sort_keys=True))
    return 0 if result["research_report_verified"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
