"""Shared risk for one in-position Smart DCA; defaults remain immutable."""
from dataclasses import replace
import unittest

from quant_system.dual_strategy import (
    Origin, Side, Signal, RiskSnapshot, admit, admit_adjustment,
)


class AdjustmentRiskTest(unittest.TestCase):
    def setUp(self):
        self.signal = Signal(Origin.CORE, Side.LONG, 1_800_000_900_000, 'dca:research-long')
        self.risk = RiskSnapshot(data_fresh=True, state_reconciled=True,
            has_unresolved_reservation=False,active_positions=1,max_positions=1,
            available_margin=70.,required_margin=50.,ai_model_validated=False)

    def test_initial_entry_gate_still_rejects_full_slot(self):
        self.assertEqual(admit(self.signal,self.risk).reason,'POSITION_LIMIT')

    def test_existing_same_side_one_dca_passes_shared_margin_gate(self):
        result=admit_adjustment(self.signal,self.risk,position_side=Side.LONG,dca_count=0)
        self.assertTrue(result.accepted)

    def test_reject_wrong_side_and_multiple_dca(self):
        self.assertFalse(admit_adjustment(self.signal,self.risk,position_side=Side.SHORT,dca_count=0).accepted)
        self.assertFalse(admit_adjustment(self.signal,self.risk,position_side=Side.LONG,dca_count=1).accepted)

    def test_reject_short_collateral_and_unreconciled_state(self):
        self.assertEqual(admit_adjustment(self.signal,replace(self.risk,available_margin=40.),
            position_side=Side.LONG,dca_count=0).reason,'INSUFFICIENT_MARGIN')
        self.assertEqual(admit_adjustment(self.signal,replace(self.risk,has_unresolved_reservation=True),
            position_side=Side.LONG,dca_count=0).reason,'UNRECONCILED_STATE')

    def test_ai_requires_model_validation_for_dca_too(self):
        signal=replace(self.signal,origin=Origin.AI)
        self.assertEqual(admit_adjustment(signal,self.risk,position_side=Side.LONG,dca_count=0).reason,
                         'AI_NOT_VALIDATED')

if __name__=='__main__':unittest.main()