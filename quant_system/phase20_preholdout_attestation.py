"""Phase20: independently registered historical native forecast proof receipt.

Recomputes the exact Phase19 JSON hash; never loads models, exchange or OOS.
This does not establish prospective model performance or native trade parity.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

START=1793750400000
STEP=900000
REPORT_SHA='sha256:f5fe8a4dcd5780088069373472dad2f3f87ecec6a7c21e0ff3897373bb5bd415'
MODEL_SHA='sha256:918dc4737ee432df8f7f9d2c3e561ac3983aaf56d8791a731a55624ab836b81f'
MATRIX_SHA='sha256:382546af84244b97fc553eddc5ad02e3da7383e8384dd6e93196cf7f7f38edf7'
PREDICTION_SHA='sha256:973dd79862ce17c3b20791f849c627261e94cef896bd9b83b7068ec003019f52'
FIRST=1792965600000
ZIP_SHA='sha256:fb33f1490cd3c995fa2d325561138d1d7a4e32f1be4e63dee28d7f1fc457b2ce'
SOURCE_SHA='082edc082996425f61f48c952be41fb037564103'
SEAL_COMMIT='888efb11b613b42a2badb3bc8adfa19ff090f2bb'
APPROVAL_COMMIT='409d446bb186a8e2ea0189df26057a9df7e839de'
COUNT=480
ACCEPTED=471

class Phase20AttestationError(ValueError):
    pass

def require(ok, code):
    if not ok:
        raise Phase20AttestationError(code)

def validate_contents(d):
    """Validate every original native historical row and all safety flags."""
    require(isinstance(d,dict) and
            d.get('audit')=='PHASE19_ORIGINAL_LAST_FOLD_NATIVE_PREDICTION_RECONCILIATION' and
            d.get('errors')==[] and
            d.get('model_identifier')=='chart-pro-okx-shadow-v1' and
            d.get('original_model_bundle_sha256')==MODEL_SHA and
            d.get('original_native_matrix_ledger_sha256')==MATRIX_SHA and
            d.get('original_native_predict_trace_sha256')==PREDICTION_SHA,
            'PHASE20_ORIGINAL_MODEL_OR_TRACE_CHANGED')
    require(all(d.get(flag) is True for flag in (
            'original_last_fold_native_predict_x_verified',
            'original_last_fold_native_forecasts_verified',
            'native_last_fold_prediction_reconciled')),
            'PHASE20_NATIVE_PREDICT_NOT_RECONCILED')
    require(all(d.get(flag) is False for flag in (
            'independent_oos_verified','oos_certified','ai_promotion_eligible',
            'ready_for_360','full_core_parity_certified','live_orders_enabled')),
            'PHASE20_UNAUTHORIZED_CERTIFICATION_OR_ORDER')
    rows=d.get('rows')
    require(type(d.get('original_native_predict_count')) is int and
            d['original_native_predict_count']==COUNT and
            isinstance(rows,list) and len(rows)==COUNT and
            d.get('first_native_predict_open_ms')==FIRST and
            d.get('last_native_predict_open_ms')==FIRST+(COUNT-1)*STEP and
            FIRST+(COUNT-1)*STEP+STEP<=START,
            'PHASE20_HISTORICAL_WINDOW_OR_ROW_COUNT_CHANGED')
    seen_accept=0
    for i,row in enumerate(rows):
        require(isinstance(row,dict) and
                type(row.get('open_time_ms')) is int and
                row['open_time_ms']==FIRST+i*STEP and
                type(row.get('do_predict')) is int and
                row['do_predict'] in (-2,-1,0,1) and
                type(row.get('accepted_forecast')) is bool and
                row['accepted_forecast']==(row['do_predict']==1),
                'PHASE20_HISTORICAL_ROW_IDENTITY_OR_FLAG_CHANGED')
        seen_accept+=row['accepted_forecast']
    require(seen_accept==ACCEPTED and
            d.get('accepted_native_predict_count')==ACCEPTED and
            d.get('rejected_native_predict_count')==COUNT-ACCEPTED,
            'PHASE20_HISTORICAL_ACCEPT_REJECT_COUNT_CHANGED')
    return {'original_native_predict_count':COUNT,
            'accepted_native_predict_count':ACCEPTED,
            'rejected_native_predict_count':COUNT-ACCEPTED,
            'first_native_predict_open_ms':FIRST,
            'last_native_predict_open_ms':FIRST+(COUNT-1)*STEP}

def validate_receipt(report_path, receipt_path):
    receipt=json.loads(Path(receipt_path).read_text(encoding='utf8'))
    require(isinstance(receipt,dict) and
            receipt.get('schemaVersion')==1 and
            receipt.get('original_phase19_report_sha256')==REPORT_SHA and
            receipt.get('original_phase19_uploaded_artifacts_zip_sha256')==ZIP_SHA and
            receipt.get('original_source_commit_sha')==SOURCE_SHA and
            receipt.get('original_model_seal_commit_sha')==SEAL_COMMIT and
            receipt.get('research_only_preholdout_approval_commit_sha')==APPROVAL_COMMIT and
            receipt.get('original_native_predict_rows')==COUNT and
            receipt.get('original_native_accepted_rows')==ACCEPTED and
            receipt.get('original_native_rejected_rows')==COUNT-ACCEPTED and
            receipt.get('first_native_predict_open_ms')==FIRST and
            receipt.get('last_native_predict_open_ms')==FIRST+(COUNT-1)*STEP and
            all(receipt.get(key) is False for key in ('independent_oos_verified',
                'oos_certified','ai_promotion_eligible','live_orders_enabled')) and
            receipt.get('original_frozen_model_bundle_sha256')==MODEL_SHA and
            receipt.get('original_native_matrix_ledger_sha256')==MATRIX_SHA and
            receipt.get('original_native_prediction_trace_sha256')==PREDICTION_SHA and
            receipt.get('holdout_start_utc')=='2026-11-04T00:00:00Z' and
            receipt.get('holdout_end_utc')=='2026-12-04T00:00:00Z' and
            receipt.get('review_class')=='PREHOLDOUT_HISTORICAL_ONLY',
            'PHASE20_REGISTERED_EVIDENCE_RECEIPT_CHANGED')
    raw=Path(report_path).read_bytes()
    actual='sha256:'+hashlib.sha256(raw).hexdigest()
    require(actual==REPORT_SHA,'PHASE20_ORIGINAL_REPORT_BYTE_SHA_MISMATCH')
    d=json.loads(raw)
    return validate_contents(d)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--phase19-report',required=True)
    parser.add_argument('--receipt',required=True)
    parser.add_argument('--out',required=True)
    args=parser.parse_args()
    result=dict(schemaVersion=1,audit='PHASE20_PREHOLDOUT_HISTORICAL_EVIDENCE_ATTESTATION',
                original_phase19_report_sha256=REPORT_SHA,
                native_historical_evidence_locked=False,
                oos_certified=False,independent_oos_verified=False,
                ai_promotion_eligible=False,live_orders_enabled=False,
                errors=[],blockers=['PROSPECTIVE_OOS_NOT_YET_COMPLETE',
                                   'NATIVE_TRADE_AND_EXCHANGE_PARITY_NOT_CERTIFIED'])
    try:
        counts=validate_receipt(args.phase19_report,args.receipt)
        result.update(counts)
        result['native_historical_evidence_locked']=True
    except (OSError,TypeError,ValueError,KeyError,UnicodeError) as exc:
        result['errors'].append(str(exc) if isinstance(exc,Phase20AttestationError)
                                else 'PHASE20_INVALID_OR_MISSING_EVIDENCE')
    target=Path(args.out)
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'native_historical_evidence_locked':
                       result['native_historical_evidence_locked'],
                       'errors':result['errors']},sort_keys=True))
    return 0 if result['native_historical_evidence_locked'] else 2

if __name__=='__main__':
    raise SystemExit(main())
