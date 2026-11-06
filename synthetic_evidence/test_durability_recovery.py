import multiprocessing
import tempfile
import unittest
from pathlib import Path

from synthetic_evidence.shared_risk import (
    FileBackedSharedRiskAdmission, PortfolioSnapshot, RiskPolicy,
)


def _policy():
    return RiskPolicy(False, "100", 100, "10")


def _portfolio():
    return PortfolioSnapshot("0", 0, "0")


def _fault_worker(args):
    directory, intent_id, fault_at = args
    gate = FileBackedSharedRiskAdmission(directory, _policy(), _portfolio())
    gate.admit({
        "intent_id": intent_id, "source": "CORE", "side": "LONG", "notional": "10"
    }, fault_at=fault_at)


class DurabilityRecoveryAcceptanceTests(unittest.TestCase):
    def _crash_at(self, directory, intent_id, fault_at, exit_code):
        proc = multiprocessing.get_context("spawn").Process(
            target=_fault_worker, args=((directory, intent_id, fault_at),)
        )
        proc.start()
        proc.join(10)
        self.assertFalse(proc.is_alive(), f"fault worker hung at {fault_at}")
        self.assertEqual(proc.exitcode, exit_code)

    def test_restart_matrix_preserves_old_or_committed_state_at_each_write_boundary(self):
        cases = (
            ("after_temp_write", 93, 0),
            ("after_file_fsync", 94, 0),
            ("before_replace", 91, 0),
            ("after_replace", 92, 1),
            ("before_directory_fsync", 95, 1),
        )
        for fault_at, exit_code, expected_count in cases:
            with self.subTest(fault_at=fault_at), tempfile.TemporaryDirectory() as directory:
                gate = FileBackedSharedRiskAdmission(directory, _policy(), _portfolio())
                gate.initialize()
                self._crash_at(directory, fault_at, fault_at, exit_code)
                recovered = FileBackedSharedRiskAdmission(directory, _policy(), _portfolio())
                self.assertEqual(recovered.inspect()["open_reservation_count"], expected_count)
                recovered.recover()
                retry = recovered.admit({
                    "intent_id": fault_at, "source": "CORE",
                    "side": "LONG", "notional": "10"
                })
                self.assertEqual(retry["status"], "ACCEPTED")
                self.assertEqual(recovered.inspect()["open_reservation_count"], 1)

    def test_recovery_removes_orphan_temporary_files_without_changing_valid_state(self):
        with tempfile.TemporaryDirectory() as directory:
            gate = FileBackedSharedRiskAdmission(directory, _policy(), _portfolio())
            gate.initialize()
            self._crash_at(directory, "orphan", "after_file_fsync", 94)
            orphan = list(Path(directory).glob(".risk-state-*.tmp"))
            self.assertEqual(len(orphan), 1)

            recovered = FileBackedSharedRiskAdmission(directory, _policy(), _portfolio())
            before = recovered.inspect()
            recovered.recover()
            after = recovered.inspect()
            self.assertEqual(after, before)
            self.assertEqual(list(Path(directory).glob(".risk-state-*.tmp")), [])

    def test_multiple_restart_cycles_preserve_reservation_ledger_and_exposure(self):
        with tempfile.TemporaryDirectory() as directory:
            gate = FileBackedSharedRiskAdmission(directory, _policy(), _portfolio())
            gate.initialize()
            for index in range(5):
                decision = gate.admit({
                    "intent_id": f"restart-{index}", "source": "AI",
                    "side": "SHORT", "notional": "10"
                })
                self.assertEqual(decision["status"], "ACCEPTED")
                gate = FileBackedSharedRiskAdmission(directory, _policy(), _portfolio())
                self.assertEqual(gate.inspect()["open_reservation_count"], index + 1)
                gate.recover()

            state = gate.inspect()
            self.assertEqual(state["reserved_exposure"], "50")
            self.assertEqual(state["open_reservation_count"], 5)
            self.assertEqual(state["reservation_count"], 5)

    def test_recovery_refuses_corrupt_state_and_preserves_bytes_for_forensics(self):
        with tempfile.TemporaryDirectory() as directory:
            gate = FileBackedSharedRiskAdmission(directory, _policy(), _portfolio())
            gate.initialize()
            state_path = Path(directory) / "risk-state.json"
            state_path.write_text('{"partial":', encoding="utf-8")
            original = state_path.read_bytes()
            with self.assertRaisesRegex(ValueError, "state integrity"):
                gate.recover()
            self.assertEqual(state_path.read_bytes(), original)

    def test_recovery_refuses_missing_state_and_does_not_reinitialize(self):
        with tempfile.TemporaryDirectory() as directory:
            gate = FileBackedSharedRiskAdmission(directory, _policy(), _portfolio())
            gate.initialize()
            state_path = Path(directory) / "risk-state.json"
            state_path.unlink()
            with self.assertRaisesRegex(ValueError, "state missing"):
                gate.recover()
            self.assertFalse(state_path.exists())


if __name__ == "__main__":
    unittest.main()
