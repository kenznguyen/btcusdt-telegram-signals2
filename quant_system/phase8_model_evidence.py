"""Phase 8: fail-closed per-candle native model evidence. Never OOS certification."""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import re
from pathlib import Path

HEX_SHA = re.compile(r'^sha256:[0-9a-f]{64}$')
FIELDS = ('open_time','model_identifier','model_sha256','fold_model_name',
          'training_end_ms','latest_train_feature_ms',
          'latest_observed_label_end_ms','configured_label_horizon_candles','do_predict')

class EvidenceError(ValueError):
    pass

def require(ok, reason):
    if not ok:
        raise EvidenceError(reason)

def booster_sha256(model):
    content = model.booster_.model_to_string()
    require(isinstance(content, str) and bool(content), 'EMPTY_NATIVE_MODEL_BOOSTER')
    return 'sha256:' + hashlib.sha256(content.encode('utf8')).hexdigest()

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b''):
            h.update(chunk)
    return 'sha256:' + h.hexdigest()

def obj(path):
    data=json.loads(path.read_text(encoding='utf8'))
    require(isinstance(data, dict), 'INVALID_REPORT_JSON')
    return data

def read_rows(path, cols):
    with path.open(newline='', encoding='utf8') as stream:
        reader=csv.DictReader(stream)
        require(reader.fieldnames is not None and set(cols).issubset(reader.fieldnames),
                'MISSING_REQUIRED_EVIDENCE_COLUMNS')
        rows=list(reader)
    require(all(None not in row and all(value is not None for value in row.values())
                for row in rows), 'MALFORMED_EVIDENCE_CSV')
    return rows

def ms(value):
    try:
        stamp=int(value)
        require(str(stamp)==str(value) and stamp>0, 'INVALID_EVIDENCE_TIMESTAMP')
        return stamp
    except (TypeError, ValueError, OverflowError) as exc:
        raise EvidenceError('INVALID_EVIDENCE_TIMESTAMP') from exc

def audit_native_model_evidence(folder):
    root=Path(folder)
    report=dict(schemaVersion=1, audit='PHASE8_NATIVE_MODEL_FINGERPRINT_LINK',
        native_model_lineage_verified=False, purged_label_horizon_verified=False,
        oos_certified=False, ai_promotion_eligible=False,
        ready_for_360=False, full_core_parity_certified=False,
        live_orders_enabled=False, errors=[],
        interpretation=('Fingerprint produced by in-memory booster during native predict; '
                        'not independent training-data/purge/OOS proof.'),
        blockers=['NO_INDEPENDENT_TRAINING_DATA_ATTESTATION',
                  'NO_INDEPENDENT_PURGE_EMBARGO_EVIDENCE',
                  'NO_OOS_PERFORMANCE_CERTIFICATE',
                  'NATIVE_TRADE_PARITY_AND_FUNDING_LIQUIDATION_UNVERIFIED'])
    try:
        phase7=obj(root/'paper/phase7-inferred-model-lineage.json')
        require(phase7.get('research_lineage_consistent') is True and
                phase7.get('oos_certified') is False and
                phase7.get('ready_for_360') is False and
                phase7.get('per_prediction_model_verified') is False,
                'PHASE7_NOT_VERIFIED')
        native=obj(root/'native/native-research-180.json')
        require(native.get('freqai_native_runtime_succeeded') is True and
                native.get('core_native_runtime_succeeded') is True and
                native.get('freqai_oos_verified') is False and
                native.get('full_core_parity_certified') is False,
                'NATIVE_RESEARCH_NOT_VERIFIED')
        predpath=root/'native/freqai-native-predictions.csv'
        require(sha(predpath)==native.get('prediction_capture_sha256') and
                sha(predpath)==phase7.get('evidence_sha256',{}).get('predictions'),
                'NATIVE_PREDICTION_SHA_MISMATCH')
        preds=read_rows(predpath,('open_time','model_identifier','do_predict',
                                  'source','pair','predicted_return'))
        tracepath=root/'native/freqai-native-model-lineage.csv'
        require(sha(tracepath)==native.get('phase8_model_lineage_sha256'),
                'NATIVE_MODEL_LINEAGE_SHA_MISMATCH')
        lineage=read_rows(tracepath,FIELDS)
        traces={}
        models={}
        for line in lineage:
            stamp=ms(line['open_time'])
            require(stamp not in traces, 'DUPLICATE_MODEL_PREDICTION_TIME')
            require(HEX_SHA.fullmatch(line['model_sha256']) is not None,
                    'INVALID_MODEL_FINGERPRINT')
            require(line['model_identifier'] and line['fold_model_name'] and
                    line['do_predict'] in ('1','0','-1','-2'),
                    'INVALID_MODEL_TRACE_ROW')
            trainend=ms(line['training_end_ms'])
            feature=ms(line['latest_train_feature_ms'])
            labelend=ms(line['latest_observed_label_end_ms'])
            require(labelend <= trainend and feature < trainend and
                    trainend <= stamp and labelend < stamp,
                    'NONCAUSAL_MODEL_LABEL_BOUNDARY')
            require(line['configured_label_horizon_candles'].isdigit() and
                    1<=int(line['configured_label_horizon_candles'])<=48,
                    'INVALID_MODEL_LABEL_HORIZON')
            key=(line['fold_model_name'],line['model_sha256'])
            meta=(trainend,feature,labelend,int(line['configured_label_horizon_candles']))
            if key in models:
                require(models[key]==meta, 'MODEL_FINGERPRINT_METADATA_CHANGED')
            else:
                models[key]=meta
            traces[stamp]=line
        seen=set()
        accepted=0
        for pred in preds:
            stamp=ms(pred['open_time'])
            require(stamp not in seen, 'DUPLICATE_NATIVE_PREDICTION_TIME')
            seen.add(stamp)
            if pred['do_predict']!='1':
                continue
            accepted+=1
            line=traces.get(stamp)
            require(line is not None, 'MISSING_ACCEPTED_MODEL_LINEAGE')
            require(line['do_predict']=='1' and
                    line['model_identifier']==pred['model_identifier'],
                    'MODEL_PREDICTION_ROW_MISMATCH')
        require(len(preds)==native.get('prediction_capture_rows') and
                accepted==native.get('prediction_capture_accepted') and
                accepted==phase7.get('accepted_forecasts'),
                'NATIVE_PREDICTION_COUNT_MISMATCH')
        require(set(traces).issubset(seen), 'ORPHAN_NATIVE_MODEL_LINEAGE')
        require(bool(models), 'NO_MODEL_FINGERPRINTS')
        report.update(native_model_lineage_verified=True,
            matched_accepted_forecasts=accepted,
            emitted_lineage_rows=len(traces),
            unique_model_fingerprints=len({r['model_sha256'] for r in traces.values()}),
            unique_fold_model_pairs=len(models),
            evidence_sha256=dict(predictions=sha(predpath),lineage=sha(tracepath)))
    except EvidenceError as exc:
        report['errors'].append(str(exc))
    except (OSError,UnicodeError,ValueError,TypeError,KeyError,csv.Error,AttributeError) as exc:
        report['errors'].append('MISSING_OR_MALFORMED_MODEL_EVIDENCE')
        report['evidence_error_type']=type(exc).__name__
    return report

def main():
    parser=argparse.ArgumentParser(description='Offline FreqAI native model fingerprint audit')
    parser.add_argument('--artifacts-root',required=True)
    parser.add_argument('--out',required=True)
    args=parser.parse_args()
    result=audit_native_model_evidence(args.artifacts_root)
    out=Path(args.out)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n',
                   encoding='utf8')
    print(json.dumps({k:result[k] for k in
                      ('native_model_lineage_verified','errors','oos_certified','ready_for_360')},
                     sort_keys=True))
    return 0 if result['native_model_lineage_verified'] else 2

if __name__=='__main__':
    raise SystemExit(main())
