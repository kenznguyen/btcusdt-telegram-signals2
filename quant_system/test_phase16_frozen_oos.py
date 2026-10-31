"""Phase16 RED: untouched 30-day fixed-model OOS protocol and timebase."""
import unittest
from datetime import datetime,timezone
from quant_system.phase16_frozen_oos import (
    OOSContractError, verify_oos_schedule, verify_exact_closed_timebase,
    verify_shared_risk_protocol, verify_registered_fold_gate,
)

START=1793750400000
END=1796342400000

class FrozenOOSContracts(unittest.TestCase):
    def protocol(self):
        return dict(protocol="PHASE13B_PROSPECTIVE_FROZEN_MODEL_OOS",
            holdout_start_utc="2026-11-04T00:00:00Z",
            holdout_end_utc="2026-12-04T00:00:00Z",
            holdout_days=30,model_identifier="chart-pro-okx-shadow-v1",
            holdout_data_already_used_for_model_selection=False,
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

    def test_frozen_forecast_provenance_requires_explicit_selector(self):
        from quant_system.paper_backtest import validated_native_predictions
        t=START
        candle=dict(open_time=t,open=100.,high=101.,low=99.,
                    close=100.,volume=1.,closed=True)
        row=dict(candle,source="freqai-frozen-oos",
                 pair="BTC/USDT:USDT",model_identifier="chart-pro-okx-shadow-v1",
                 do_predict=1,predicted_return=.02)
        self.assertEqual(validated_native_predictions(
            [row],{t:candle},"chart-pro-okx-shadow-v1",
            allowed_source="freqai-frozen-oos"),{t:.02})
        with self.assertRaisesRegex(ValueError,
                                    "WRONG_FREQAI_PREDICTION_ORIGIN"):
            validated_native_predictions(
                [row],{t:candle},"chart-pro-okx-shadow-v1")

    def test_preholdout_gate_requires_exact_native_evidence_sha(self):
        original=dict(
            all_26_folds_fitting_time_verified=True,folds_verified=26,
            total_reproduced_train_rows=59696,
            total_reproduced_validation_rows=14825,
            native_report_sha256="sha256:0a414da0d4e8567c39ae1e2c066e4703f9fff5450933c8a0e011b911b5920e01",
            original_bundle_sha256="sha256:918dc4737ee432df8f7f9d2c3e561ac3983aaf56d8791a731a55624ab836b81f",
            source_commit_sha="082edc082996425f61f48c952be41fb037564103",
            errors=[])
        approved=dict(
            approved_phase16_report_sha256="sha256:"+"c"*64,
            reviewed_native_original_report_sha256=original["native_report_sha256"],
            approved_historical_fold_count=26,
            original_seal_commit="888efb11b613b42a2badb3bc8adfa19ff090f2bb",
            original_bundle_sha256=original["original_bundle_sha256"],
            original_source_commit_sha=original["source_commit_sha"],
            oos_no_retraining=True,no_real_orders=True,research_only=True)
        self.assertTrue(verify_registered_fold_gate(
            original,approved,"sha256:"+"c"*64))
        changed=dict(original,native_report_sha256="sha256:"+"f"*64)
        with self.assertRaisesRegex(
                OOSContractError,"OOS_ALL_26_FOLD_RELEASE_GATE_NOT_SIGNED"):
            verify_registered_fold_gate(changed,approved,"sha256:"+"c"*64)
        wrong=dict(approved,approved_historical_fold_count=25)
        with self.assertRaisesRegex(
                OOSContractError,"OOS_ALL_26_FOLD_RELEASE_GATE_NOT_SIGNED"):
            verify_registered_fold_gate(original,wrong,"sha256:"+"c"*64)
        with self.assertRaisesRegex(
                OOSContractError,"OOS_ALL_26_FOLD_RELEASE_GATE_NOT_SIGNED"):
            verify_registered_fold_gate(original,approved,"sha256:"+"d"*64)

    def test_forbidden_retraining_or_live_enabling(self):
        p=self.protocol()
        p["frozen_model_policy"]["retrain_inside_holdout"]=True
        with self.assertRaisesRegex(OOSContractError,
                                    "OOS_TRAINING_OR_ORDER_ENABLED"):
            verify_shared_risk_protocol(p)

if __name__=="__main__":
    unittest.main()
