"""Runtime contract tests for P5.2.5 GREEN.

These tests intentionally target the planned public contracts. They are expected
to fail against the RED baseline until the runtime modules are implemented.
They use only temporary SQLite files and in-process synchronization.
"""
import tempfile
import threading
import time
import unittest
from pathlib import Path

try:
    from paper_execution.writer_gate import PaperWriterGate, WriterGateError
except ModuleNotFoundError as exc:
    if exc.name != "paper_execution.writer_gate":
        raise
    PaperWriterGate = WriterGateError = None


class PaperWriterGateRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.gate = PaperWriterGate(scope="paper_only") if PaperWriterGate else None

    def test_paper_writer_gate_contract_module_is_present(self):
        self.assertIsNotNone(PaperWriterGate,
            "CONTRACT RED: paper_execution.writer_gate module/API is not implemented")

    @unittest.skipIf(PaperWriterGate is None, "Writer Gate contract module is absent; explicit RED assertion covers this")

    def test_admission_returns_opaque_generation_bound_token(self):
        token = self.gate.admit_writer()
        self.assertIsNotNone(token)
        self.assertNotIsInstance(token, dict)
        self.assertEqual(self.gate.active_writers, 1)
        self.gate.release_writer(token)
        self.assertEqual(self.gate.active_writers, 0)

    def test_drain_closes_admission_before_waiting_for_existing_writer(self):
        token = self.gate.admit_writer()
        result = []
        thread = threading.Thread(target=lambda: result.append(self.gate.begin_drain(timeout_seconds=1)))
        thread.start()
        deadline = time.monotonic() + 1
        while self.gate.state != "DRAINING" and time.monotonic() < deadline:
            time.sleep(0.001)
        self.assertEqual(self.gate.state, "DRAINING")
        with self.assertRaises(WriterGateError):
            self.gate.admit_writer()
        self.gate.release_writer(token)
        thread.join(timeout=2)
        self.assertFalse(thread.is_alive())
        self.assertEqual(self.gate.state, "DRAINED")
        self.assertEqual(result, ["DRAINED"])

    def test_drain_timeout_is_fail_closed_and_does_not_reopen(self):
        token = self.gate.admit_writer()
        with self.assertRaises(TimeoutError):
            self.gate.begin_drain(timeout_seconds=0.01)
        self.assertEqual(self.gate.state, "DRAINING")
        with self.assertRaises(WriterGateError):
            self.gate.admit_writer()
        self.gate.release_writer(token)
        self.assertEqual(self.gate.state, "DRAINING")
        self.gate.reopen(authorized=True)
        self.assertEqual(self.gate.state, "OPEN")

    def test_release_is_idempotent_and_cannot_underflow(self):
        token = self.gate.admit_writer()
        self.gate.release_writer(token)
        self.gate.release_writer(token)
        self.assertEqual(self.gate.active_writers, 0)

    def test_token_from_another_gate_is_rejected(self):
        foreign = PaperWriterGate(scope="paper_only").admit_writer()
        with self.assertRaises(WriterGateError):
            self.gate.validate_writer(foreign)
    
    def test_wrong_scope_cannot_authorize_t0(self):
        self.assertEqual(self.gate.scope, "paper_only")
        with self.assertRaises(WriterGateError):
            self.gate.authorize_scope("t0_canonical")

    def test_stale_generation_token_cannot_validate_after_reopen(self):
        token = self.gate.admit_writer()
        self.gate.release_writer(token)
        self.gate.begin_drain(timeout_seconds=0.1)
        self.gate.reopen(authorized=True)
        with self.assertRaises(WriterGateError):
            self.gate.validate_writer(token)

    def test_reopen_requires_drained_state_and_explicit_authorization(self):
        with self.assertRaises(WriterGateError):
            self.gate.reopen(authorized=True)
        self.gate.begin_drain(timeout_seconds=0.1)
        with self.assertRaises(WriterGateError):
            self.gate.reopen(authorized=False)
        self.gate.reopen(authorized=True)
        self.assertEqual(self.gate.state, "OPEN")


if __name__ == "__main__":
    unittest.main()
