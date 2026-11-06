import multiprocessing
import os
import tempfile
import unittest
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from synthetic_evidence.shared_risk import (
    FileBackedSharedRiskAdmission, RiskPolicy, PortfolioSnapshot,
)


def _policy():
    return RiskPolicy(False, "100", 100, "10")


def _portfolio():
    return PortfolioSnapshot("0", 0, "0")


def _admit_worker(args):
    directory, intent_id = args
    gate = FileBackedSharedRiskAdmission(directory, _policy(), _portfolio())
    return gate.admit({
        "intent_id": intent_id, "source": "AI", "side": "LONG", "notional": "10"
    })


def _crash_worker(args):
    directory, intent_id, fault_at = args
    gate = FileBackedSharedRiskAdmission(directory, _policy(), _portfolio())
    gate.admit({
        "intent_id": intent_id, "source": "CORE", "side": "SHORT", "notional": "25"
    }, fault_at=fault_at)


class CrossProcessAtomicityTests(unittest.TestCase):
    def test_independent_processes_cannot_overreserve_shared_exposure(self):
        with tempfile.TemporaryDirectory() as directory:
            FileBackedSharedRiskAdmission(directory, _policy(), _portfolio()).initialize()
            with ProcessPoolExecutor(max_workers=20) as pool:
                results = list(pool.map(_admit_worker, [(directory, f"mp-{i}") for i in range(20)]))

            self.assertEqual(sum(r["status"] == "ACCEPTED" for r in results), 10)
            gate = FileBackedSharedRiskAdmission(directory, _policy(), _portfolio())
            state = gate.inspect()
            self.assertEqual(state["reserved_exposure"], "100")
            self.assertEqual(state["open_reservation_count"], 10)

    def test_independent_processes_cannot_overrun_position_cap(self):
        policy = RiskPolicy(False, "1000", 6, "10")
        with tempfile.TemporaryDirectory() as directory:
            FileBackedSharedRiskAdmission(directory, policy, _portfolio()).initialize()
            with ProcessPoolExecutor(max_workers=16) as pool:
                results = list(pool.map(
                    lambda_args_worker,
                    [(directory, f"cap-{i}", policy) for i in range(16)],
                ))

            self.assertEqual(sum(r["status"] == "ACCEPTED" for r in results), 6)
            gate = FileBackedSharedRiskAdmission(directory, policy, _portfolio())
            self.assertEqual(gate.inspect()["open_reservation_count"], 6)

    def test_crash_before_atomic_replace_keeps_old_state_and_retry_commits_once(self):
        with tempfile.TemporaryDirectory() as directory:
            FileBackedSharedRiskAdmission(directory, _policy(), _portfolio()).initialize()
            proc = multiprocessing.get_context("spawn").Process(
                target=_crash_worker, args=((directory, "before-replace", "before_replace"),)
            )
            proc.start()
            proc.join(10)
            self.assertEqual(proc.exitcode, 91)

            gate = FileBackedSharedRiskAdmission(directory, _policy(), _portfolio())
            self.assertEqual(gate.inspect()["open_reservation_count"], 0)
            result = gate.admit({
                "intent_id": "before-replace", "source": "CORE",
                "side": "SHORT", "notional": "25"
            })
            self.assertEqual(result["status"], "ACCEPTED")
            self.assertEqual(gate.inspect()["open_reservation_count"], 1)

    def test_crash_after_atomic_replace_is_committed_and_retry_is_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            proc = multiprocessing.get_context("spawn").Process(
                target=_crash_worker, args=((directory, "after-replace", "after_replace"),)
            )
            proc.start()
            proc.join(10)
            self.assertEqual(proc.exitcode, 92)

            gate = FileBackedSharedRiskAdmission(directory, _policy(), _portfolio())
            self.assertEqual(gate.inspect()["open_reservation_count"], 1)
            result = gate.admit({
                "intent_id": "after-replace", "source": "CORE",
                "side": "SHORT", "notional": "25"
            })
            self.assertEqual(result["status"], "ACCEPTED")
            self.assertEqual(gate.inspect()["open_reservation_count"], 1)

    def test_truncated_or_corrupt_state_is_rejected_not_silently_reset(self):
        with tempfile.TemporaryDirectory() as directory:
            gate = FileBackedSharedRiskAdmission(directory, _policy(), _portfolio())
            gate.initialize()
            state_path = Path(directory) / "risk-state.json"
            state_path.write_text('{"truncated":', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "state integrity"):
                gate.inspect()

    def test_missing_state_after_initialization_is_not_treated_as_fresh_state(self):
        with tempfile.TemporaryDirectory() as directory:
            gate = FileBackedSharedRiskAdmission(directory, _policy(), _portfolio())
            gate.initialize()
            (Path(directory) / "risk-state.json").unlink()
            with self.assertRaisesRegex(ValueError, "state missing"):
                gate.inspect()


def lambda_args_worker(args):
    directory, intent_id, policy = args
    gate = FileBackedSharedRiskAdmission(directory, policy, _portfolio())
    return gate.admit({
        "intent_id": intent_id, "source": "CORE", "side": "LONG", "notional": "10"
    })


if __name__ == "__main__":
    unittest.main()
