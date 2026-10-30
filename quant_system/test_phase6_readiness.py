"""Synthetic Phase 6 test cases; no historical model performance claims."""
import csv
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from quant_system.phase6_readiness import assess_readiness

DAY = 86_400_000
START = 1777824000000
END = START + 180 * DAY


def sha(path):
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def save_csv(path, rows):
    with path.open("w", newline="", encoding="utf8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def fixture(folder):
    root = Path(folder)
    paper, native = root / "paper", root / "native"
    paper.mkdir()
    native.mkdir()
    summary = dict(phase="PAPER_180_ONLY", start_ms=START, end_ms=END,
                   paper_trade_bearing_verified=True, exchange="okx",
                   dataset_sha256="sha256:" + "a" * 64,
                   detail_sha256="sha256:" + "b" * 64)
    hashes = {}
    for mode in ("CORE_ONLY", "AI_ONLY", "DUAL"):
        slug = mode.lower().replace("_", "-")
        filename = "paper-" + slug + "-trades.csv"
        trade = dict(trade_id=mode + ":1", entry_at_ms=START + 5 * DAY,
                     exit_at_ms=START + 7 * DAY,
                     net_pnl_ex_funding_usdt=10 if mode == "CORE_ONLY" else -30)
        save_csv(paper / filename, [trade])
        hashes[filename] = sha(paper / filename)
        event_name = "paper-" + slug + "-events.csv"
        save_csv(paper / event_name, [dict(trade_id=mode + ":1",
                                          kind="LONG ENTRY", fee_usdt="0")])
        hashes[event_name] = sha(paper / event_name)
        summary[mode] = dict(trade_count_closed=1, trade_count_open=0,
            realized_net_ex_funding_usdt=trade["net_pnl_ex_funding_usdt"],
            max_drawdown_ex_funding_usdt=10 if mode == "CORE_ONLY" else 95,
            starting_capital_usdt=100)
    summary_path = paper / "paper-180-summary.json"
    summary_path.write_text(json.dumps(summary), encoding="utf8")
    hashes[summary_path.name] = sha(summary_path)
    (paper / "paper-180-independent-audit.json").write_text(json.dumps({
        "artifact_integrity_verified":True, "ready_for_360":False,
        "full_core_parity_certified":False, "artifact_sha256":hashes
    }))
    (paper / "paper-180-source-contention.json").write_text(json.dumps({
        "contention_audit_verified":True, "errors":[],
        "ready_for_360":False, "full_core_parity_certified":False,
        "core_entries_blocked_by_ai_position":1
    }))
    (native / "freqai-native-180.log").write_text(
        "2026-10-30 - INFO - Training 1 timeranges\n"
        "2026-10-30 - INFO - Training BTC/USDT:USDT, 1/1 pairs from "
        "2026-04-03 16:00:00 to 2026-05-03 16:00:00, 1/1 trains\n"
    )
    (native / "native-research-180.json").write_text(json.dumps({
        "core_native_runtime_succeeded":True,
        "freqai_native_runtime_succeeded":True,
        "freqai_oos_verified":False, "full_core_parity_certified":False,
        "funding_mark_full_coverage_verified":False,
        "prediction_capture_accepted":1,
        "dataset_sha256":summary["dataset_sha256"],
        "detail_sha256":summary["detail_sha256"]
    }))
    return root


class Phase6ReadinessTest(unittest.TestCase):
    def test_valid_research_is_still_not_oos_certified(self):
        with tempfile.TemporaryDirectory() as temp:
            result = assess_readiness(fixture(temp))
            self.assertTrue(result["research_report_verified"], result)
            self.assertEqual(len(result["modes"]["AI_ONLY"]["windows"]), 6)
            self.assertEqual(result["modes"]["AI_ONLY"]["closed_trades"], 1)
            self.assertEqual(result["modes"]["AI_ONLY"]["net_pnl_ex_funding_usdt"], -30)
            self.assertEqual(result["freqai"]["training_windows_observed"], 1)
            self.assertFalse(result["oos_certified"])
            self.assertFalse(result["ai_promotion_eligible"])
            self.assertFalse(result["ready_for_360"])
            self.assertIn("NO_PREDICTION_TO_MODEL_FOLD_PROVENANCE", result["blockers"])

    def test_open_entry_fee_reconciles_with_account_pnl(self):
        with tempfile.TemporaryDirectory() as temp:
            root = fixture(temp)
            name = "paper-ai-only-events.csv"
            path = root / "paper" / name
            with path.open(newline="") as stream:
                rows = list(csv.DictReader(stream))
            rows.append(dict(trade_id="AI_ONLY:open", kind="LONG ENTRY", fee_usdt=".25"))
            save_csv(path, rows)
            summary_path = root / "paper/paper-180-summary.json"
            summary = json.loads(summary_path.read_text())
            summary["AI_ONLY"]["trade_count_open"] = 1
            summary["AI_ONLY"]["realized_net_ex_funding_usdt"] = -30.25
            summary_path.write_text(json.dumps(summary))
            upstream_path = root / "paper/paper-180-independent-audit.json"
            upstream = json.loads(upstream_path.read_text())
            for filename in (name, "paper-180-summary.json"):
                upstream["artifact_sha256"][filename] = sha(root / "paper" / filename)
            upstream_path.write_text(json.dumps(upstream))
            result = assess_readiness(root)
            self.assertTrue(result["research_report_verified"], result)
            self.assertAlmostEqual(result["modes"]["AI_ONLY"]["open_entry_fees_usdt"], .25)
            self.assertAlmostEqual(result["modes"]["AI_ONLY"]["net_pnl_ex_funding_usdt"], -30.25)

    def test_trade_file_tamper_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = fixture(temp)
            path = root / "paper/paper-ai-only-trades.csv"
            path.write_text(path.read_text() + "injected\n")
            self.assertIn("PHASE4_EVIDENCE_CHANGED", assess_readiness(root)["errors"])

    def test_invalid_upstream_phase5_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = fixture(temp)
            path = root / "paper/paper-180-source-contention.json"
            obj = json.loads(path.read_text())
            obj["contention_audit_verified"] = False
            path.write_text(json.dumps(obj))
            self.assertIn("PHASE5_CONTENTION_NOT_VERIFIED", assess_readiness(root)["errors"])

    def test_forged_pnl_report_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = fixture(temp)
            path = root / "paper/paper-180-summary.json"
            obj = json.loads(path.read_text())
            obj["DUAL"]["realized_net_ex_funding_usdt"] = 100
            path.write_text(json.dumps(obj))
            upstream_path = root / "paper/paper-180-independent-audit.json"
            upstream = json.loads(upstream_path.read_text())
            upstream["artifact_sha256"][path.name] = sha(path)
            upstream_path.write_text(json.dumps(upstream))
            self.assertIn("TRADE_PNL_REPORT_MISMATCH", assess_readiness(root)["errors"])

    def test_training_window_after_cutoff_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = fixture(temp)
            path = root / "native/freqai-native-180.log"
            path.write_text(path.read_text() +
                "2026-10-30 - Training BTC/USDT:USDT, 1/1 pairs from "
                "2026-10-29 16:00:00 to 2026-11-29 16:00:00, 2/2 trains\n")
            self.assertIn("TRAIN_WINDOW_OUTSIDE_REPLAY", assess_readiness(root)["errors"])

    def test_missing_native_report_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = fixture(temp)
            (root / "native/native-research-180.json").unlink()
            self.assertFalse(assess_readiness(root)["research_report_verified"])


if __name__ == "__main__":
    unittest.main()
