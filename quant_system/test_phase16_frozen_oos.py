"""Phase16 RED: untouched 30-day fixed-model OOS protocol and timebase."""
import unittest
from datetime import datetime,timezone
from quant_system.phase16_frozen_oos import (
    OOSContractError, verify_oos_schedule, verify_exact_closed_timebase,
    verify_shared_risk_protocol,
)

START=1793750400000
END=1796342400000

class FrozenOOSContracts(unittest.TestCase):
    def protocol(self):
        return dict(protocol="PHASE13B_PROSPECTIVE_FROZEN_MODEL_OOS",
            holdout_start_utc="2026-11-04T00:00:00Z",
            holdout_end_utc="2026-12-04T00:00:00Z",
            holdout_days=30,model_identifier="chart-pro-okx-shadow-v1",
            frozen_model_policy=dict(retrain_inside_holdout=False,
                tune_parameters_using_holdout=False,
                change_strategy_or_features_after_seal=False),
            evaluation=dict(modes=["CORE_ONLY","AI_ONLY","DUAL"],
                initial_equity_usdt=100,futures_leverage=13,
                entry_margin_fraction_of_equity=.1,
                max_total_margin_fraction_of_equity=.6,max_positions=3,
                max_ai_origin_positions_in_dual=2,max_dca_per_position=1,
                fee_per_side_fraction=.0005,no_real_orders=True))

    def test_immutable_pre_registered_dates(self):
        p=self.protocol()
        self.assertEqual(verify_oos_schedule(
            p,now=datetime(2026,12,4,tzinfo=timezone.utc)),(START,END))
        p["holdout_start_utc"]="2026-11-05T00:00:00Z"
        with self.assertRaisesRegex(OOSContractError,"OOS_PROTOCOL_CHANGED"):
            verify_oos_schedule(p,now=datetime(2026,12,5,tzinfo=timezone.utc))

    def test_early_verification_is_not_a_valid_holdout(self):
        with self.assertRaisesRegex(OOSContractError,
                                    "OOS_WINDOW_NOT_COMPLETE"):
            verify_oos_schedule(self.protocol(),
                now=datetime(2026,11,30,tzinfo=timezone.utc))

    def test_strict_closed_candle_rows(self):
        rows=[dict(open_time=START+i*900000,open=100.,high=101.,
            low=99.,close=100.,volume=1.,closed=True) for i in range(2880)]
        self.assertEqual(verify_exact_closed_timebase(
            rows,start=START,end=END,step=900000),2880)
        rows[70]["closed"]=False
        with self.assertRaisesRegex(OOSContractError,
                                    "OOS_GAP_OR_OPEN_CANDLE"):
            verify_exact_closed_timebase(rows,start=START,end=END,
                                         step=900000)

    def test_shared_risk_locked_to_protocol(self):
        self.assertTrue(verify_shared_risk_protocol(self.protocol()))
        p=self.protocol()
        p["evaluation"]["max_ai_origin_positions_in_dual"]=3
        with self.assertRaisesRegex(OOSContractError,
                                    "OOS_SHARED_RISK_CHANGED"):
            verify_shared_risk_protocol(p)

    def test_forbidden_retraining_or_live_enabling(self):
        p=self.protocol()
        p["frozen_model_policy"]["retrain_inside_holdout"]=True
        with self.assertRaisesRegex(OOSContractError,
                                    "OOS_TRAINING_OR_ORDER_ENABLED"):
            verify_shared_risk_protocol(p)

if __name__=="__main__":
    unittest.main()
