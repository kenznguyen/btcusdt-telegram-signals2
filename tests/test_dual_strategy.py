import unittest

from quant_system.dual_strategy import Origin, Side, Signal, RiskSnapshot, admit


class DualStrategyAdmissionTests(unittest.TestCase):
    def setUp(self):
        self.safe = RiskSnapshot(
            data_fresh=True,
            state_reconciled=True,
            has_unresolved_reservation=False,
            active_positions=0,
            max_positions=1,
            available_margin=100.0,
            required_margin=50.0,
            ai_model_validated=True,
        )

    def test_ai_long_without_core_signal_is_admitted(self):
        signal = Signal(Origin.AI, Side.LONG, 1793376000000, "ai-1", 0.78)
        self.assertTrue(admit(signal, self.safe).accepted)

    def test_ai_short_without_core_signal_is_admitted(self):
        signal = Signal(Origin.AI, Side.SHORT, 1793376000000, "ai-2", 0.81)
        self.assertTrue(admit(signal, self.safe).accepted)

    def test_core_signal_does_not_require_ai_validation(self):
        from dataclasses import replace
        signal = Signal(Origin.CORE, Side.SHORT, 1793376000000, "core-1")
        self.assertTrue(admit(signal, replace(self.safe, ai_model_validated=False)).accepted)

    def test_unvalidated_ai_is_rejected(self):
        from dataclasses import replace
        signal = Signal(Origin.AI, Side.LONG, 1793376000000, "ai-3", 0.9)
        self.assertEqual(admit(signal, replace(self.safe, ai_model_validated=False)).reason, "AI_NOT_VALIDATED")

    def test_crash_after_reservation_fails_closed(self):
        from dataclasses import replace
        signal = Signal(Origin.CORE, Side.LONG, 1793376000000, "core-2")
        self.assertEqual(admit(signal, replace(self.safe, has_unresolved_reservation=True)).reason, "UNRECONCILED_STATE")

    def test_stale_data_fails_closed(self):
        from dataclasses import replace
        signal = Signal(Origin.CORE, Side.LONG, 1793376000000, "core-3")
        self.assertEqual(admit(signal, replace(self.safe, data_fresh=False)).reason, "STALE_DATA")

    def test_position_limit_is_shared(self):
        from dataclasses import replace
        signal = Signal(Origin.AI, Side.LONG, 1793376000000, "ai-4", 0.7)
        self.assertEqual(admit(signal, replace(self.safe, active_positions=1)).reason, "POSITION_LIMIT")

    def test_insufficient_margin_is_shared(self):
        from dataclasses import replace
        signal = Signal(Origin.CORE, Side.LONG, 1793376000000, "core-4")
        self.assertEqual(admit(signal, replace(self.safe, available_margin=0)).reason, "INSUFFICIENT_MARGIN")


if __name__ == "__main__":
    unittest.main()
