import unittest
from quant_engine.signal_router import Candidate, resolve, RiskPolicy, approve


class SignalRouterTests(unittest.TestCase):
    def test_agreement_creates_one_confirmed_intent(self):
        x = resolve(Candidate("CORE", "LONG"), Candidate("AI_NATIVE", "LONG"))
        self.assertEqual((x.origin, x.direction), ("CONFIRMED", "LONG"))

    def test_conflicting_signals_never_open(self):
        x = resolve(Candidate("CORE", "LONG"), Candidate("AI_NATIVE", "SHORT"))
        self.assertEqual(x.status, "CONFLICT")
        self.assertFalse(approve(x, RiskPolicy()).approved)

    def test_ai_native_without_core_is_independent(self):
        x = resolve(None, Candidate("AI_NATIVE", "SHORT"))
        self.assertEqual((x.origin, x.direction), ("AI_NATIVE", "SHORT"))

    def test_ai_requires_valid_prediction(self):
        x = resolve(None, Candidate("AI_NATIVE", "LONG", valid=False))
        self.assertFalse(approve(x, RiskPolicy()).approved)

    def test_core_only_keeps_its_origin(self):
        x = resolve(Candidate("CORE", "LONG"), None)
        self.assertEqual(x.origin, "CORE")

    def test_no_signal_denied(self):
        self.assertFalse(approve(resolve(None, None), RiskPolicy()).approved)

    def test_paper_only(self):
        x = resolve(Candidate("CORE", "LONG"), None)
        self.assertFalse(approve(x, RiskPolicy(execution_mode="LIVE")).approved)

    def test_no_new_entries_if_position_open(self):
        x = resolve(None, Candidate("AI_NATIVE", "LONG"))
        self.assertFalse(approve(x, RiskPolicy(position_open=True)).approved)


if __name__ == "__main__":
    unittest.main()
