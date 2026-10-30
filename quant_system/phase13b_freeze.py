"""Phase13B pre-seal model candidate: paper only, never automatically OOS approved.

Frozen candidate contains LightGBM estimator AND fitted DataSieve feature/label
pipelines. The bundle is a trusted LOCAL joblib file: unpickle ONLY after
external GitHub commit-time + SHA attestation, never from unknown uploads.
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from quant_system.phase13b_matrix import MatrixEvidenceError,check,matrix_digest

def _canonical_sha(value):
    return "sha256:"+hashlib.sha256(json.dumps(value,
        sort_keys=True,separators=(",",":"),allow_nan=False).encode("utf8")).hexdigest()

def capture_candidate(directory,*,model,pipeline,label_pipeline,
                      meta,source_commit_sha,config,model_sha256,columns):
    import joblib
    root=Path(directory)
    check(isinstance(source_commit_sha,str) and
          len(source_commit_sha)==40 and
          all(c in "0123456789abcdef" for c in source_commit_sha),
          "OOS_CANDIDATE_MISSING_SOURCE_COMMIT")
    check(isinstance(meta,dict) and
          isinstance(meta.get("training_end_ms"),int) and
          isinstance(meta.get("latest_observed_label_end_ms"),int) and
          meta["latest_observed_label_end_ms"]<meta["training_end_ms"],
          "OOS_CANDIDATE_NONCAUSAL_TRAINING")
    check(isinstance(columns,list) and columns and
          len(set(columns))==len(columns),"OOS_CANDIDATE_INVALID_SCHEMA")
    path=root/"phase13b-unsealed-model-candidate.joblib"
    evidence=root/"phase13b-unsealed-model-candidate.json"
    if evidence.exists():
        current=json.loads(evidence.read_text(encoding="utf8"))
        cutoff=current.get("training_end_ms")
        check(isinstance(cutoff,int),"OOS_CANDIDATE_BAD_PREVIOUS_CUTOFF")
        if meta["training_end_ms"]<=cutoff:
            return current
    root.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix(".partial")
    check(not temp.exists() and not path.is_symlink(),
          "OOS_CANDIDATE_UNSAFE_PATH")
    payload={"model":model,"feature_pipeline":pipeline,
             "label_pipeline":label_pipeline,
             "source_commit_sha":source_commit_sha,
             "training_end_ms":meta["training_end_ms"],
             "model_sha256":model_sha256,
             "ordered_features":columns,
             "model_identifier":meta["model_identifier"]}
    try:
        joblib.dump(payload,temp,compress=3)
        with temp.open("rb") as file:
            os.fsync(file.fileno())
        os.replace(temp,path)
    finally:
        temp.unlink(missing_ok=True)
    result=dict(schemaVersion=1,
        proposal_only=True,sealed_in_git=False,oos_certified=False,
        source_commit_sha=source_commit_sha,
        training_end_ms=meta["training_end_ms"],
        latest_observed_label_end_ms=meta["latest_observed_label_end_ms"],
        model_identifier=meta["model_identifier"],
        fold_model_name=meta["fold_model_name"],
        model_sha256=model_sha256,
        ordered_feature_columns=columns,
        freqai_config_sha256=_canonical_sha(config["freqai"]),
        config_sha256=_canonical_sha(config),
        candidate_path=path.name,
        candidate_sha256=matrix_digest(path),
        created_at_utc=datetime.now(timezone.utc).isoformat())
    temp_meta=evidence.with_suffix(".partial")
    try:
        with temp_meta.open("x",encoding="utf8") as file:
            file.write(json.dumps(result,sort_keys=True,indent=2,allow_nan=False)+"\n")
            file.flush();os.fsync(file.fileno())
        os.replace(temp_meta,evidence)
    finally:
        temp_meta.unlink(missing_ok=True)
    return result
