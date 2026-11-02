"""SWG-F RED contracts for Paper writer admission and drain.

Static source-contract tests only: no runtime imports, SQLite, network, or Feeder.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
GATEWAY = ROOT / "paper_execution" / "writer_gate.py"


def gateway_source():
    if not GATEWAY.is_file():
        return ""
    return GATEWAY.read_text(encoding="utf-8")


class PaperWriterIsolationRedContracts(unittest.TestCase):
    def test_swg_f01_writer_gate_module_exists(self):
        self.assertTrue(
            GATEWAY.is_file(),
            "SWG-F01: independent Paper writer gate is not implemented",
        )

    def test_swg_f02_admission_is_open_state_only_and_returns_token(self):
        text = gateway_source()
        self.assertIn("admit_writer", text, "SWG-F02: admission API missing")
        self.assertIn("OPEN", text, "SWG-F02: OPEN state missing")
        self.assertIn("writer_token", text, "SWG-F02: generation-bound token missing")

    def test_swg_f03_drain_closes_admission_before_waiting(self):
        text = gateway_source()
        self.assertIn("begin_drain", text, "SWG-F03: drain API missing")
        self.assertIn("DRAINING", text, "SWG-F03: DRAINING state missing")
        self.assertIn("in_flight", text, "SWG-F03: in-flight writer accounting missing")

    def test_swg_f04_drained_requires_zero_in_flight_writers(self):
        text = gateway_source()
        self.assertIn("DRAINED", text, "SWG-F04: DRAINED state missing")
        self.assertIn("wait_for_drain", text, "SWG-F04: drain completion barrier missing")
        self.assertIn("in_flight == 0", text, "SWG-F04: zero-writer completion condition missing")

    def test_swg_f05_timeout_fails_closed_without_reopening(self):
        text = gateway_source()
        self.assertIn("timeout", text.lower(), "SWG-F05: bounded drain timeout missing")
        self.assertIn("DRAIN_TIMEOUT", text, "SWG-F05: explicit timeout result missing")
        self.assertIn("fail_closed", text, "SWG-F05: timeout fail-closed behavior missing")

    def test_swg_f06_stale_generation_token_cannot_commit_or_release(self):
        text = gateway_source()
        self.assertIn("generation", text, "SWG-F06: writer generation missing")
        self.assertIn("validate_writer_token", text, "SWG-F06: token validation missing")
        self.assertIn("STALE_WRITER", text, "SWG-F06: stale writer rejection missing")

    def test_swg_f07_release_is_idempotent_and_never_underflows(self):
        text = gateway_source()
        self.assertIn("release_writer", text, "SWG-F07: release API missing")
        self.assertIn("idempotent", text.lower(), "SWG-F07: idempotent release contract missing")
        self.assertIn("underflow", text.lower(), "SWG-F07: in-flight underflow guard missing")

    def test_swg_f08_reopen_requires_settled_outcome_and_zero_writers(self):
        text = gateway_source()
        self.assertIn("reopen", text.lower(), "SWG-F08: reopen API missing")
        self.assertIn("settled", text.lower(), "SWG-F08: migration outcome settlement missing")
        self.assertIn("in_flight == 0", text, "SWG-F08: reopen zero-writer guard missing")
        self.assertIn("generation += 1", text, "SWG-F08: reopen generation advance missing")

    def test_swg_f09_paper_gate_is_not_a_t0_lease_authority(self):
        text = gateway_source()
        self.assertIn("paper_only", text, "SWG-F09: explicit Paper-only scope missing")
        self.assertNotIn("authorize_t0_write", text, "SWG-F09: Paper gate exposes T0 write authority")

    def test_swg_f10_paper_ledger_mutations_require_writer_admission(self):
        ledger = (ROOT / "paper_execution" / "ledger.py").read_text(encoding="utf-8")
        self.assertIn(
            "writer_gate",
            ledger,
            "SWG-F10: PaperLedger mutations are not bound to writer admission",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
