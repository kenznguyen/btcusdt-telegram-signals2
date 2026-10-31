"""Phase20 pre-holdout native proof receipt: strict anti-forgery regressions."""
import json
import tempfile
from pathlib import Path
import unittest
from quant_system.phase20_preholdout_attestation import (
    validate_contents, validate_receipt, Phase20AttestationError,
    FIRST, STEP, COUNT, ACCEPTED, REPORT_SHA, MODEL_SHA,
    MATRIX_SHA, PREDICTION_SHA,
)

def fixture():
    return dict(audit='PHASE19_ORIGINAL_LAST_FOLD_NATIVE_PREDICTION_RECONCILIATION',
        errors=[],model_identifier='chart-pro-okx-shadow-v1',
        original_model_bundle_sha256=MODEL_SHA,
        original_native_matrix_ledger_sha256=MATRIX_SHA,
        original_native_predict_trace_sha256=PREDICTION_SHA,
        original_last_fold_native_predict_x_verified=True,
        original_last_fold_native_forecasts_verified=True,
        native_last_fold_prediction_reconciled=True,
        independent_oos_verified=False,oos_certified=False,
        ai_promotion_eligible=False,ready_for_360=False,
        full_core_parity_certified=False,live_orders_enabled=False,
        original_native_predict_count=COUNT,
        accepted_native_predict_count=ACCEPTED,
        rejected_native_predict_count=COUNT-ACCEPTED,
        first_native_predict_open_ms=FIRST,
        last_native_predict_open_ms=FIRST+(COUNT-1)*STEP,
        rows=[dict(open_time_ms=FIRST+i*STEP,do_predict=1 if i<ACCEPTED else 0,
                   accepted_forecast=i<ACCEPTED) for i in range(COUNT)])

class Phase20ReceiptTests(unittest.TestCase):
    def test_exact_historical_counts_are_reconstructed(self):
        self.assertEqual(validate_contents(fixture())['accepted_native_predict_count'],471)

    def test_missing_or_reordered_candle_fails(self):
        x=fixture(); x['rows'][77]['open_time_ms']+=STEP
        with self.assertRaisesRegex(Phase20AttestationError,'ROW_IDENTITY'):
            validate_contents(x)

    def test_duplicate_or_truncated_native_rows_fails(self):
        x=fixture(); x['rows'].pop(12)
        with self.assertRaisesRegex(Phase20AttestationError,'ROW_COUNT'):
            validate_contents(x)

    def test_malformed_prediction_flag_fails(self):
        x=fixture(); x['rows'][11]['do_predict']=7
        with self.assertRaisesRegex(Phase20AttestationError,'ROW_IDENTITY'):
            validate_contents(x)

    def test_flag_claim_and_counts_must_match(self):
        x=fixture(); x['rows'][6]['accepted_forecast']=False
        with self.assertRaisesRegex(Phase20AttestationError,'ROW_IDENTITY'):
            validate_contents(x)
        x=fixture(); x['rejected_native_predict_count']=8
        with self.assertRaisesRegex(Phase20AttestationError,'ACCEPT_REJECT'):
            validate_contents(x)

    def test_unauthorized_oos_or_live_upgrade_fails(self):
        for flag in ('independent_oos_verified','ai_promotion_eligible','live_orders_enabled'):
            with self.subTest(flag=flag):
                x=fixture(); x[flag]=True
                with self.assertRaisesRegex(Phase20AttestationError,'UNAUTHORIZED'):
                    validate_contents(x)

    def test_native_parity_false_fails(self):
        x=fixture(); x['original_last_fold_native_forecasts_verified']=False
        with self.assertRaisesRegex(Phase20AttestationError,'NOT_RECONCILED'):
            validate_contents(x)

    def test_matrix_or_trace_hash_altered_fails(self):
        x=fixture(); x['original_native_matrix_ledger_sha256']='sha256:'+'0'*64
        with self.assertRaisesRegex(Phase20AttestationError,'MODEL_OR_TRACE_CHANGED'):
            validate_contents(x)

    def test_registered_receipt_cannot_be_self_replaced(self):
        rpath=Path(__file__).resolve().parents[1]/'research_seals/phase20-native-predict-preholdout.json'
        registered=json.loads(rpath.read_text())
        with tempfile.TemporaryDirectory() as root:
            receipt=Path(root)/'receipt.json'; report=Path(root)/'report.json'
            receipt.write_text(json.dumps(registered)); report.write_text(json.dumps(fixture()))
            with self.assertRaisesRegex(Phase20AttestationError,'BYTE_SHA_MISMATCH'):
                validate_receipt(report,receipt)
            registered['original_phase19_report_sha256']='sha256:'+'0'*64
            receipt.write_text(json.dumps(registered))
            with self.assertRaisesRegex(Phase20AttestationError,'REGISTERED_EVIDENCE'):
                validate_receipt(report,receipt)

    def test_registered_preholdout_receipt_is_fixed(self):
        rpath=Path(__file__).resolve().parents[1]/'research_seals/phase20-native-predict-preholdout.json'
        registered=json.loads(rpath.read_text())
        self.assertEqual(registered['original_phase19_report_sha256'],REPORT_SHA)
        self.assertEqual(registered['original_native_predict_rows'],480)
        self.assertFalse(registered['oos_certified'])

if __name__=='__main__':
    unittest.main()
