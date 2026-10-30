"""Phase12 fail-closed independent audit of FreqAI fit() TRAIN/TEST label rows.

Only verifies observed sample timestamps and a 4-M15-candle target against
canonical OHLCV; never certifies features, OOS performance or live trading.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,math,re
from collections import defaultdict
from pathlib import Path

M15=900000
ROWS=('fold_model_name','model_identifier','model_sha256','row_kind',
      'feature_open_ms','label_end_ms','observed_raw_label',
      'expected_recomputed_label','feature_close','future_close',
      'training_end_ms','horizon_candles')
SHA=re.compile(r'^sha256:[0-9a-f]{64}$')

class TrainEvidenceError(ValueError):
    pass

def check(value,reason):
    if not value: raise TrainEvidenceError(reason)

def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return 'sha256:'+h.hexdigest()

def read_json(path):
    x=json.loads(Path(path).read_text(encoding='utf8'))
    check(isinstance(x,dict),'INVALID_RESEARCH_JSON')
    return x

def read_csv(path,columns):
    with Path(path).open(newline='',encoding='utf8') as f:
        reader=csv.DictReader(f)
        check(reader.fieldnames is not None and
              len(set(reader.fieldnames))==len(reader.fieldnames) and
              set(columns).issubset(reader.fieldnames),'INVALID_RESEARCH_CSV_HEADER')
        out=list(reader)
    check(all(None not in x and all(v is not None for v in x.values())
              for x in out),'INVALID_RESEARCH_CSV_ROW')
    return out

def integer(x):
    try:
        n=int(x)
        check(str(n)==str(x) and n>=0,'INVALID_SAMPLE_TIMESTAMP')
        return n
    except (TypeError,ValueError,OverflowError) as e:
        raise TrainEvidenceError('INVALID_SAMPLE_TIMESTAMP') from e

def number(x):
    try:
        v=float(x)
        check(math.isfinite(v),'INVALID_LABEL_OR_MARKET_PRICE')
        return v
    except (TypeError,ValueError,OverflowError) as e:
        raise TrainEvidenceError('INVALID_LABEL_OR_MARKET_PRICE') from e

def equal(a,b):
    return math.isclose(number(a),number(b),rel_tol=1e-10,abs_tol=1e-10)

def audit_training_samples(artifacts_root):
    out=dict(schemaVersion=1,audit='PHASE12_NATIVE_FIT_TRAIN_TEST_LABEL_ROWS',
       actual_fit_sample_lineage_verified=False,label_reconstruction_verified=False,
       train_test_label_purge_verified=False,oos_certified=False,
       ai_promotion_eligible=False,ready_for_360=False,
       full_core_parity_certified=False,live_orders_enabled=False,
       errors=[],blockers=['FULL_FEATURE_CAUSALITY_NOT_VERIFIED',
       'TRAIN_TEST_SPLIT_NOT_AN_INDEPENDENT_OOS_PROOF',
       'NATIVE_TRADING_PARITY_NOT_VERIFIED','FUNDING_LIQUIDATION_NOT_VERIFIED'])
    try:
        root=Path(artifacts_root)
        phase8=read_json(root/'paper/phase8-native-model-evidence.json')
        phase11=read_json(root/'paper/portfolio-180-conflict-reconciliation.json')
        native=read_json(root/'native/native-research-180.json')
        check(phase8.get('native_model_lineage_verified') is True and
              phase8.get('errors')==[] and
              phase11.get('source_conflict_reconciliation_verified') is True and
              phase11.get('errors')==[] and
              native.get('core_native_runtime_succeeded') is True and
              native.get('freqai_native_runtime_succeeded') is True and
              native.get('freqai_oos_verified') is False and
              native.get('full_core_parity_certified') is False,
              'PHASE8_OR_11_OR_NATIVE_NOT_VERIFIED')
        # A postfit observation error may be suppressed by FreqAI native
        # training internals. Never certify a partial or failed fit trace.
        check(native.get('phase12_observer_failure_count')==0,
              'PHASE12_FIT_OBSERVER_REPORTED_ERROR')
        file=root/'native/freqai-native-training-samples.csv'
        lineage=root/'native/freqai-native-model-lineage.csv'
        pred=root/'native/freqai-native-predictions.csv'
        check(digest(file)==native.get('phase12_training_samples_sha256'),
              'PHASE12_TRAINING_SAMPLES_SHA_MISMATCH')
        check(digest(lineage)==native.get('phase8_model_lineage_sha256')==
              phase8.get('evidence_sha256',{}).get('lineage'),
              'PHASE8_MODEL_SHA_MISMATCH')
        check(digest(pred)==native.get('prediction_capture_sha256')==
              phase8.get('evidence_sha256',{}).get('predictions'),
              'NATIVE_PREDICTION_SHA_MISMATCH')
        samples=read_csv(file,ROWS)
        traces=read_csv(lineage,('fold_model_name','model_sha256',
              'model_identifier','training_end_ms','open_time',
              'configured_label_horizon_candles'))
        check(bool(samples) and bool(traces),'NO_NATIVE_FIT_SAMPLES')
        models={};first_prediction={}
        for row in traces:
            key=(row['fold_model_name'],row['model_sha256'])
            check(SHA.fullmatch(key[1]) is not None,'INVALID_TRAIN_MODEL_SHA')
            meta=(integer(row['training_end_ms']),row['model_identifier'],
                  integer(row['configured_label_horizon_candles']))
            check(key not in models or models[key]==meta,
                  'INCONSISTENT_PHASE8_MODEL_FOLD')
            models[key]=meta
            stamp=integer(row['open_time'])
            first_prediction[key]=min(stamp,first_prediction.get(key,stamp))
        prices={}
        for row in read_csv(root/'canonical/15m.csv',
                            ('open_time','close','closed')):
            t=integer(row['open_time'])
            check(t%M15==0 and t not in prices and
                  row['closed'] in ('True','true','1'),'INVALID_CANONICAL_M15')
            value=number(row['close'])
            check(value>0,'INVALID_CANONICAL_PRICE')
            prices[t]=value
        groups=defaultdict(lambda:{'TRAIN':set(),'TEST':set()})
        train_count=test_count=0
        for row in samples:
            key=(row['fold_model_name'],row['model_sha256'])
            check(key in models,'UNLINKED_ACTUAL_FIT_MODEL')
            cutoff,model_id,horizon=models[key]
            kind=row['row_kind']
            check(kind in ('TRAIN','TEST') and
                  row['model_identifier']==model_id and
                  integer(row['training_end_ms'])==cutoff and
                  integer(row['horizon_candles'])==horizon==4,
                  'INVALID_FIT_SAMPLE_METADATA')
            stamp=integer(row['feature_open_ms'])
            label_end=integer(row['label_end_ms'])
            check(stamp%M15==0 and
                  label_end==stamp+horizon*M15 and
                  label_end<cutoff and
                  label_end<first_prediction[key],
                  'ACTUAL_FIT_LABEL_LOOKAHEAD')
            check(stamp not in groups[key][kind],
                  'DUPLICATE_FIT_SAMPLE_TIMESTAMP')
            groups[key][kind].add(stamp)
            check(stamp in prices and label_end in prices,
                  'MISSING_TARGET_RECONSTRUCTION_CANDLE')
            observed=prices[label_end]/prices[stamp]-1
            check(equal(prices[stamp],row['feature_close']) and
                  equal(prices[label_end],row['future_close']) and
                  equal(observed,row['observed_raw_label']) and
                  equal(observed,row['expected_recomputed_label']),
                  'NATIVE_FIT_LABEL_VALUE_MISMATCH')
            if kind=='TRAIN':train_count+=1
            else:test_count+=1
        check(set(groups)==set(models),'UNOBSERVED_MODEL_FIT_SAMPLES')
        overlaps=[]
        for key,parts in groups.items():
            train,test=parts['TRAIN'],parts['TEST']
            check(bool(train) and bool(test),'MISSING_TRAIN_TEST_PARTITION')
            check(train.isdisjoint(test),'TRAIN_TEST_ROW_OVERLAP')
            check(max(train)<min(test),'NONCHRONOLOGICAL_FIT_PARTITION')
            if max(train)+4*M15>=min(test):
                overlaps.append(key[0])
        out.update(actual_fit_sample_lineage_verified=True,
            label_reconstruction_verified=True,
            train_test_label_purge_verified=not overlaps,
            train_rows=train_count,test_rows=test_count,
            model_fold_count=len(models),
            train_test_boundary_overlap_fold_count=len(overlaps),
            overlapping_fold_names=sorted(overlaps),
            training_samples_sha256=digest(file),
            canonical_m15_sha256=digest(root/'canonical/15m.csv'))
        if overlaps:
            out['errors'].append('TRAIN_TEST_LABEL_HORIZON_NOT_PURGED')
    except TrainEvidenceError as e:
        out['errors'].append(str(e))
    except (OSError,UnicodeError,ValueError,TypeError,KeyError,
            csv.Error,OverflowError) as e:
        out['errors'].append('MISSING_OR_MALFORMED_PHASE12_EVIDENCE')
        out['error_type']=type(e).__name__
    return out

def main():
    p=argparse.ArgumentParser(description='SHA-pinned observed LightGBM fit-row audit')
    p.add_argument('--artifacts-root',required=True)
    p.add_argument('--out',required=True)
    args=p.parse_args()
    result=audit_training_samples(args.artifacts_root)
    file=Path(args.out);file.parent.mkdir(parents=True,exist_ok=True)
    file.write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n')
    print(json.dumps({k:result[k] for k in
          ('actual_fit_sample_lineage_verified','train_test_label_purge_verified',
           'errors','ready_for_360')}))
    return 0 if result['actual_fit_sample_lineage_verified'] and not result['errors'] else 2

if __name__=='__main__':
    raise SystemExit(main())
