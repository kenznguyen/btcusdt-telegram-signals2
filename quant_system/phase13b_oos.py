"""Phase13B prospective OOS pre-registration, candidate SHA, and dataset gate.

A proposal is not a seal. A model is only frozen when a *separate* immutable
Git commit (and external GitHub timestamp review) records its exact bundle SHA
BEFORE the prospective window opens. This module never sets OOS certified.
"""
from __future__ import annotations
import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from quant_system.phase13b_matrix import matrix_digest

def _load(path):
    data=json.loads(Path(path).read_text(encoding="utf8"))
    if not isinstance(data,dict):
        raise ValueError("PHASE13B_INVALID_JSON")
    return data

def _time(value):
    return datetime.fromisoformat(value.replace("Z","+00:00"))

def _base():
    return dict(candidate_sha_verified=False,sealed_in_git=False,
        holdout_dataset_timebase_verified=False,independent_oos_verified=False,
        oos_certified=False,ai_promotion_eligible=False,
        ready_for_360=False,full_core_parity_certified=False,
        live_orders_enabled=False,errors=[],
        blockers=["MODEL_SHA_MUST_BE_SEALED_IN_A_PRE_HOLDOUT_GIT_COMMIT",
                  "MODEL_AND_PREPROCESSOR_LOCK_NOT_YET_EXTERNALLY_VERIFIED",
                  "UNTOUCHED_FUTURE_HOLDOUT_NOT_YET_EVALUATED",
                  "FUNDING_LIQUIDATION_AND_EXECUTION_UNVERIFIED"])

def verify_candidate(protocol_path,metadata_path,bundle_path):
    out=_base()
    try:
        p=_load(protocol_path);m=_load(metadata_path);bundle=Path(bundle_path)
        start=_time(p["holdout_start_utc"])
        end=_time(p["holdout_end_utc"])
        if (p.get("protocol")!="PHASE13B_PROSPECTIVE_FROZEN_MODEL_OOS"
            or p.get("sealed_in_git") is not False
            or (end-start).total_seconds()!=30*86400
            or not isinstance(p.get("model_identifier"),str)
            or p.get("model_identifier")!=m.get("model_identifier")):
            raise ValueError("PHASE13B_PROTOCOL_NOT_APPROVED")
        if (m.get("proposal_only") is not True or
            m.get("sealed_in_git") is not False or
            m.get("candidate_path")!=bundle.name):
            raise ValueError("PHASE13B_UNTRUSTED_CANDIDATE_METADATA")
        if (not bundle.is_file() or bundle.is_symlink() or
                matrix_digest(bundle)!=m.get("candidate_sha256")):
            raise ValueError("PHASE13B_CANDIDATE_SHA_MISMATCH")
        stamp=int(start.timestamp()*1000)
        if (type(m.get("training_end_ms")) is not int or
            type(m.get("latest_observed_label_end_ms")) is not int or
            m["latest_observed_label_end_ms"]>=m["training_end_ms"] or
            m["training_end_ms"]>=stamp):
            raise ValueError("PHASE13B_FROZEN_TRAINING_CUTOFF_INVALID")
        if (not isinstance(m.get("source_commit_sha"),str) or
            len(m["source_commit_sha"])!=40 or
            not isinstance(m.get("model_sha256"),str) or
            len(m["model_sha256"])!=71 or
            not isinstance(m.get("ordered_feature_columns"),list) or
            not m["ordered_feature_columns"]):
            raise ValueError("PHASE13B_MODEL_PROVENANCE_INCOMPLETE")
        out.update(candidate_sha_verified=True,
            candidate_sha256=matrix_digest(bundle),
            candidate_metadata_sha256=matrix_digest(metadata_path),
            protocol_sha256=matrix_digest(protocol_path),
            model_sha256=m["model_sha256"],source_commit_sha=m["source_commit_sha"],
            model_training_end_ms=m["training_end_ms"],
            feature_columns=m["ordered_feature_columns"],
            holdout_start_utc=p["holdout_start_utc"],
            holdout_end_utc=p["holdout_end_utc"])
    except (OSError,ValueError,TypeError,KeyError,OverflowError) as exc:
        out["errors"].append(str(exc)[:150])
    return out

def prepare_seal(protocol_path,metadata_path,bundle_path):
    """Git registration proposal: NOT signed, NOT independently attested."""
    verified=verify_candidate(protocol_path,metadata_path,bundle_path)
    if not verified["candidate_sha_verified"]:
        raise ValueError("PHASE13B_CANNOT_PROPOSE_INVALID_CANDIDATE:"+",".join(verified["errors"]))
    metadata=_load(metadata_path)
    return dict(schemaVersion=1,
        seal_proposal_only=True,sealed_in_git=False,seal_git_commit=None,
        proposed_at_utc=datetime.now(timezone.utc).isoformat(),
        protocol_sha256=verified["protocol_sha256"],
        candidate_sha256=verified["candidate_sha256"],
        candidate_metadata_sha256=verified["candidate_metadata_sha256"],
        source_commit_sha=verified["source_commit_sha"],
        model_sha256=verified["model_sha256"],
        freqai_config_sha256=metadata["freqai_config_sha256"],
        model_identifier=metadata["model_identifier"],
        training_end_ms=verified["model_training_end_ms"],
        feature_columns=verified["feature_columns"],
        holdout_start_utc=verified["holdout_start_utc"],
        holdout_end_utc=verified["holdout_end_utc"],
        oos_certified=False,ready_for_360=False,live_orders_enabled=False)

def check_holdout_csv(protocol_path,canonical_m15_path):
    out=_base()
    try:
        protocol=_load(protocol_path)
        start=int(_time(protocol["holdout_start_utc"]).timestamp()*1000)
        end=int(_time(protocol["holdout_end_utc"]).timestamp()*1000)
        rows=[]
        with Path(canonical_m15_path).open(newline="",encoding="utf8") as source:
            reader=csv.DictReader(source)
            if not set(("open_time","close","closed")).issubset(reader.fieldnames or []):
                raise ValueError("PHASE13B_HOLDOUT_CSV_SCHEMA_INVALID")
            for row in reader:
                rows.append(row)
        if len(rows)!=2880 or end-start!=2880*900000:
            raise ValueError("PHASE13B_HOLDOUT_LENGTH_INVALID")
        for i,row in enumerate(rows):
            if (int(row["open_time"])!=start+i*900000 or
                row["closed"] not in ("True","true","1") or
                not 0<float(row["close"])<1e9):
                raise ValueError("PHASE13B_HOLDOUT_GAP_OPEN_OR_INVALID_PRICE")
        out["holdout_dataset_timebase_verified"]=True
        out["holdout_m15_sha256"]=matrix_digest(canonical_m15_path)
        out["holdout_row_count"]=len(rows)
        # A valid timebase does not prove dataset was untouched,
        # no holdout retraining, funding coverage or trading performance.
    except (OSError,ValueError,TypeError,KeyError,OverflowError) as exc:
        out["errors"].append(str(exc)[:150])
    return out

def main():
    cli=argparse.ArgumentParser()
    cli.add_argument("--protocol",required=True)
    cli.add_argument("--candidate-metadata",required=True)
    cli.add_argument("--bundle",required=True)
    cli.add_argument("--out",required=True)
    args=cli.parse_args()
    result=verify_candidate(args.protocol,args.candidate_metadata,args.bundle)
    if result["candidate_sha_verified"]:
        result["seal_proposal"]=prepare_seal(
            args.protocol,args.candidate_metadata,args.bundle)
    output=Path(args.out)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,indent=2,sort_keys=True,
                                 allow_nan=False)+"\n",encoding="utf8")
    print(json.dumps({k:result[k] for k in (
        "candidate_sha_verified","sealed_in_git","oos_certified","errors"
    )},sort_keys=True))
    return 0 if result["candidate_sha_verified"] else 2

if __name__=="__main__":raise SystemExit(main())
