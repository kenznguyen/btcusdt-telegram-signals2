import unittest

from synthetic_evidence.shared_risk import SharedRiskAdmission, RiskPolicy, PortfolioSnapshot


def policy(**overrides):
    values = {
        "kill_switch": False,
        "max_total_exposure": "100",
        "max_open_positions": 5,
        "max_daily_loss": "10",
    }
    values.update(overrides)
    return RiskPolicy(**values)


def portfolio(**overrides):
    values = {
        "current_exposure": "0",
        "open_positions": 0,
        "daily_loss": "0",
    }
    values.update(overrides)
    return PortfolioSnapshot(**values)


def intent(intent_id="intent-1", source="CORE", notional="10", side="LONG"):
    return {
        "intent_id": intent_id,
        "source": source,
        "side": side,
        "notional": notional,
    }


class SharedRiskAdmissionTests(unittest.TestCase):
    def test_core_and_ai_intents_use_the_same_admission_contract(self):
        gate = SharedRiskAdmission(policy(), portfolio())
        core = gate.admit(intent("core-1", "CORE", "10"))
        ai = gate.admit(intent("ai-1", "AI", "15", "SHORT"))
        self.assertEqual(core["status"], "ACCEPTED")
        self.assertEqual(ai["status"], "ACCEPTED")
        self.assertEqual(core["risk_gate"], "SHARED")
        self.assertEqual(ai["risk_gate"], "SHARED")
        self.assertEqual(core["reservation_id"], "reservation:core-1")
        self.assertEqual(ai["reservation_id"], "reservation:ai-1")

    def test_kill_switch_rejects_core_and_ai_intents(self):
        gate = SharedRiskAdmission(policy(kill_switch=True), portfolio())
        for source in ("CORE", "AI"):
            with self.subTest(source=source):
                result = gate.admit(intent(source.lower(), source))
                self.assertEqual(result["status"], "REJECTED")
                self.assertEqual(result["reason"], "KILL_SWITCH_ACTIVE")
                self.assertIsNone(result["reservation_id"])

    def test_total_exposure_cap_rejects_intent_that_would_exceed_limit(self):
        gate = SharedRiskAdmission(policy(max_total_exposure="100"), portfolio(current_exposure="95"))
        result = gate.admit(intent(notional="5.01"))
        self.assertEqual(result["reason"], "MAX_TOTAL_EXPOSURE")

    def test_exact_exposure_limit_is_admitted(self):
        gate = SharedRiskAdmission(policy(max_total_exposure="100"), portfolio(current_exposure="90"))
        self.assertEqual(gate.admit(intent(notional="10"))["status"], "ACCEPTED")

    def test_open_position_limit_rejects_new_intent(self):
        gate = SharedRiskAdmission(policy(max_open_positions=2), portfolio(open_positions=2))
        self.assertEqual(gate.admit(intent())["reason"], "MAX_OPEN_POSITIONS")

    def test_daily_loss_limit_rejects_when_limit_is_reached(self):
        gate = SharedRiskAdmission(policy(max_daily_loss="10"), portfolio(daily_loss="10"))
        self.assertEqual(gate.admit(intent())["reason"], "DAILY_LOSS_LIMIT")

    def test_identical_duplicate_intent_returns_original_reservation(self):
        gate = SharedRiskAdmission(policy(), portfolio())
        first = gate.admit(intent("same"))
        second = gate.admit(intent("same"))
        self.assertEqual(first, second)
        self.assertEqual(gate.reservation_count, 1)

    def test_same_intent_id_with_changed_bytes_is_rejected(self):
        gate = SharedRiskAdmission(policy(), portfolio())
        gate.admit(intent("same", notional="10"))
        with self.assertRaisesRegex(ValueError, "changed bytes"):
            gate.admit(intent("same", notional="11"))

    def test_invalid_source_side_and_non_positive_notional_are_rejected(self):
        gate = SharedRiskAdmission(policy(), portfolio())
        for candidate in (
            intent("bad-source", "LEGACY"),
            intent("bad-side", "AI", side="BUY"),
            intent("bad-amount", "CORE", notional="0"),
        ):
            with self.subTest(candidate=candidate):
                result = gate.admit(candidate)
                self.assertEqual(result["status"], "REJECTED")
                self.assertIsNone(result["reservation_id"])

    def test_batch_routes_both_strategy_sources_through_one_shared_gate(self):
        gate = SharedRiskAdmission(policy(), portfolio())
        results = gate.admit_batch(
            core_intents=[intent("core", "CORE")],
            ai_intents=[intent("ai", "AI")],
        )
        self.assertEqual([item["risk_gate"] for item in results], ["SHARED", "SHARED"])
        self.assertEqual(gate.reservation_count, 2)

    def test_reservation_is_not_created_for_any_rejected_intent(self):
        gate = SharedRiskAdmission(policy(kill_switch=True), portfolio())
        gate.admit(intent())
        self.assertEqual(gate.reservation_count, 0)


if __name__ == "__main__":
    unittest.main()
