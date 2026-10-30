"""Phase13B pre-registration may only become eligible after external Git seal."""
import json
import tempfile
import unittest
from pathlib import Path

from quant_system.phase13b_oos import prepare_seal, verify_candidate, check_holdout_csv
from quant_system.phase13b_matrix import matrix_digest

class Phase13BOOSGateTest(unittest.TestCase):
    def setUp(self):
        self.t=tempfile.TemporaryDirectory()
        self.root=Path(self.t.name)
        self.protocol=self.root/"protocol.json"
        self.protocol.write_text(json.dumps({
            "schemaVersion":1,"protocol":"PHASE13B_PROSPECTIVE_FROZEN_MODEL_OOS",
            "holdout_start_utc":"2026-11-04T00:00:00Z",
            "holdout_end_utc":"2026-12-04T00:00:00Z",
            "holdout_days":30,
            "model_identifier":"chart-pro-okx-shadow-v1",
            "sealed_in_git":False
        }))
        self.bundle=self.root/"frozen.joblib"
        self.bundle.write_bytes(b"local private test bundle")
        self.meta=self.root/"candidate.json"
        self.meta.write_text(json.dumps({
            "proposal_only":True,"sealed_in_git":False,
            "candidate_sha256":matrix_digest(self.bundle),
            "source_commit_sha":"a"*40,"model_sha256":"sha256:"+"b"*64,
            "model_identifier":"chart-pro-okx-shadow-v1",
            "training_end_ms":1793000000000,
            "latest_observed_label_end_ms":1792999000000,
            "created_at_utc":"2026-10-31T00:00:00Z",
            "freqai_config_sha256":"sha256:"+"c"*64,
            "ordered_feature_columns":["%-x"],"candidate_path":"frozen.joblib"
        }))

    def tearDown(self):self.t.cleanup()

    def test_candidate_not_independent_oos_even_if_bundle_exists(self):
        result=verify_candidate(self.protocol,self.meta,self.bundle)
        self.assertTrue(result["candidate_sha_verified"])
        self.assertFalse(result["sealed_in_git"])
        self.assertFalse(result["independent_oos_verified"])
        self.assertFalse(result["ready_for_360"])

    def test_proposal_never_marks_sealed_by_itself(self):
        seal=prepare_seal(self.protocol,self.meta,self.bundle)
        self.assertTrue(seal["candidate_sha256"].startswith("sha256:"))
        self.assertEqual(seal["model_identifier"],"chart-pro-okx-shadow-v1")
        self.assertFalse(seal["sealed_in_git"])
        self.assertIsNone(seal["seal_git_commit"])

    def test_candidate_produced_after_holdout_start_denied(self):
        meta=json.loads(self.meta.read_text())
        meta["created_at_utc"]="2026-11-05T00:00:00Z"
        self.meta.write_text(json.dumps(meta))
        result=verify_candidate(self.protocol,self.meta,self.bundle)
        self.assertFalse(result["candidate_sha_verified"])
        self.assertIn("PHASE13B_CANDIDATE_CREATED_AFTER_OOS_START",result["errors"])

    def test_tampered_bundle_cannot_be_frozen(self):
        self.bundle.write_bytes(b"not original")
        result=verify_candidate(self.protocol,self.meta,self.bundle)
        self.assertIn("PHASE13B_CANDIDATE_SHA_MISMATCH",result["errors"])
        self.assertFalse(result["candidate_sha_verified"])

    def test_holdout_wrong_date_and_gap_denied(self):
        path=self.root/"holdout.csv"
        path.write_text("open_time,close,closed\n900000,30000,1\n")
        verdict=check_holdout_csv(self.protocol,path)
        self.assertFalse(verdict["holdout_dataset_timebase_verified"])
        self.assertIn("PHASE13B_HOLDOUT_LENGTH_INVALID",verdict["errors"])

if __name__=="__main__":unittest.main()
