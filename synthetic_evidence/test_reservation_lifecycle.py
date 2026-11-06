import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

from synthetic_evidence.shared_risk import (
    SharedRiskAdmission, RiskPolicy, PortfolioSnapshot,
)


def policy(**overrides):
    values = {
        "kill_switch": False,
        "max_total_exposure": "100",
        "max_open_positions": 100,
        "max_daily_loss": "10",
    }
    values.update(overrides)
    return RiskPolicy(**values)


def portfolio(**overrides):
    values = {"current_exposure": "0", "open_positions": 0, "daily_loss": "0"}
    values.update(overrides)
    return PortfolioSnapshot(**values)


def intent(intent_id, notional="10"):
    return {"intent_id": intent_id, "source": "CORE", "side": "LONG", "notional": notional}


class ReservationLifecycleTests(unittest.TestCase):
    def test_concurrent_admission_never_exceeds_exposure_or_position_caps(self):
        gate = SharedRiskAdmission(
            policy(max_total_exposure="100", max_open_positions=100), portfolio()
        )
        barrier = threading.Barrier(40)

        def submit(index):
            barrier.wait()
            return gate.admit(intent(f"parallel-{index}"))

        with ThreadPoolExecutor(max_workers=40) as pool:
            results = list(pool.map(submit, range(40)))

        self.assertEqual(sum(item["status"] == "ACCEPTED" for item in results), 10)
        self.assertEqual(gate.reservation_count, 10)
        self.assertEqual(gate.reserved_exposure, "100")
        self.assertEqual(gate.open_reservation_count, 10)

    def test_concurrent_duplicate_delivery_creates_exactly_one_reservation(self):
        gate = SharedRiskAdmission(policy(), portfolio())
        barrier = threading.Barrier(32)

        def submit(_):
            barrier.wait()
            return gate.admit(intent("same-concurrent-id"))

        with ThreadPoolExecutor(max_workers=32) as pool:
            results = list(pool.map(submit, range(32)))

        self.assertTrue(all(result == results[0] for result in results))
        self.assertEqual(gate.reservation_count, 1)

    def test_release_returns_capacity_and_is_idempotent(self):
        gate = SharedRiskAdmission(policy(), portfolio())
        accepted = gate.admit(intent("release-me", "30"))
        reservation_id = accepted["reservation_id"]

        self.assertTrue(gate.release_reservation(reservation_id))
        self.assertFalse(gate.release_reservation(reservation_id))
        self.assertEqual(gate.reserved_exposure, "0")
        self.assertEqual(gate.open_reservation_count, 0)
        self.assertEqual(gate.reservation_count, 1)

        next_result = gate.admit(intent("after-release", "100"))
        self.assertEqual(next_result["status"], "ACCEPTED")

    def test_unknown_reservation_cannot_change_capacity(self):
        gate = SharedRiskAdmission(policy(), portfolio())
        self.assertFalse(gate.release_reservation("reservation:missing"))
        self.assertEqual(gate.reserved_exposure, "0")
        self.assertEqual(gate.open_reservation_count, 0)

    def test_expiry_releases_only_reservations_at_or_before_deadline(self):
        gate = SharedRiskAdmission(policy(), portfolio())
        start = datetime(2026, 11, 7, 0, 0, tzinfo=timezone.utc)
        first = gate.admit(intent("expires-first"), now_utc=start, reservation_ttl_seconds=60)
        second = gate.admit(intent("expires-later"), now_utc=start, reservation_ttl_seconds=120)

        expired = gate.expire_reservations(start.replace(second=59))
        self.assertEqual(expired, [])
        expired = gate.expire_reservations(start.replace(second=60))
        self.assertEqual(expired, [first["reservation_id"]])
        self.assertEqual(gate.open_reservation_count, 1)
        self.assertEqual(gate.reserved_exposure, "10")
        self.assertEqual(gate.reservation_status(second["reservation_id"]), "ACTIVE")

    def test_snapshot_restore_preserves_reservations_and_duplicate_idempotency(self):
        gate = SharedRiskAdmission(policy(), portfolio())
        original = gate.admit(intent("survive-restart", "25"))
        snapshot = gate.export_state()

        restored = SharedRiskAdmission.restore_state(snapshot)
        replayed = restored.admit(intent("survive-restart", "25"))

        self.assertEqual(replayed, original)
        self.assertEqual(restored.reservation_count, 1)
        self.assertEqual(restored.reserved_exposure, "25")
        self.assertEqual(restored.open_reservation_count, 1)

    def test_snapshot_rejects_tampered_exposure_or_reservation_state(self):
        gate = SharedRiskAdmission(policy(), portfolio())
        gate.admit(intent("integrity", "25"))
        snapshot = gate.export_state()
        snapshot["reserved_exposure"] = "999"

        with self.assertRaisesRegex(ValueError, "snapshot integrity"):
            SharedRiskAdmission.restore_state(snapshot)

    def test_restart_replay_after_release_does_not_reactivate_reservation(self):
        gate = SharedRiskAdmission(policy(), portfolio())
        accepted = gate.admit(intent("released-before-restart", "20"))
        gate.release_reservation(accepted["reservation_id"])

        restored = SharedRiskAdmission.restore_state(gate.export_state())
        duplicate = restored.admit(intent("released-before-restart", "20"))

        self.assertEqual(duplicate, accepted)
        self.assertEqual(restored.reservation_status(accepted["reservation_id"]), "RELEASED")
        self.assertEqual(restored.reserved_exposure, "0")


if __name__ == "__main__":
    unittest.main()
