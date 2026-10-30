"""Phase 7: SHA-bound temporal FreqAI fold candidates; never OOS/model certification."""
from __future__ import annotations
import argparse
from bisect import bisect_right
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re

M15_MS = 900_000
DAY_MS = 86_400_000
TRAIN_PATTERN = re.compile(
    r'Training BTC/USDT:USDT, 1/1 pairs from '
    r'(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d) to '
    r'(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d), (\d+)/(\d+) trains'
)

class EvidenceError(ValueError):
    pass

def require(condition, reason):
    if not condition:
        raise EvidenceError(reason)

def json_data(path):
    obj = json.loads(path.read_text(encoding='utf8'))
    require(isinstance(obj, dict), 'INVALID_JSON_EVIDENCE')
    return obj

def digest(path):
    hasher = hashlib.sha256()
    with path.open('rb') as source:
        for block in iter(lambda: source.read(1024 * 1024), b''):
            hasher.update(block)
    return 'sha256:' + hasher.hexdigest()

def timestamp(value):
    try:
        number = int(value)
        require(str(number) == str(value) and number > 0 and number % M15_MS == 0,
                'INVALID_FORECAST_CANDLE_TIMESTAMP')
        return number
    except (TypeError, ValueError, OverflowError) as exc:
        raise EvidenceError('INVALID_FORECAST_CANDLE_TIMESTAMP') from exc

def log_ms(value):
    return int(datetime.strptime(value, '%Y-%m-%d %H:%M:%S').replace(
        tzinfo=timezone.utc).timestamp() * 1000)

def training_windows(path, train_days, backtest_days):
    matches = list(TRAIN_PATTERN.finditer(path.read_text(encoding='utf8', errors='replace')))
    require(bool(matches), 'MISSING_TRAINING_WINDOW_LOGS')
    windows = []
    for index, match in enumerate(matches):
        begin, end = log_ms(match[1]), log_ms(match[2])
        require(int(match[3]) == index + 1 and int(match[4]) == len(matches),
                'INCOMPLETE_TRAIN_LOG_SEQUENCE')
        require(end - begin == train_days * DAY_MS, 'INCORRECT_TRAINING_DURATION')
        if windows:
            require(end - windows[-1]['training_end_ms'] == backtest_days * DAY_MS,
                    'INCONSISTENT_TRAIN_WINDOW_STEP')
        windows.append(dict(fold_index=index + 1, training_start_ms=begin,
            training_end_ms=end, tentative_prediction_count=0, accepted_near_cutoff=0))
    return windows

def inspect_lineage(root_dir, config_path):
    """Model folds are INFERRED from timestamps, not observed model artifact IDs.

    FreqAI's constant identifier and training-log chronology are not sufficient
    to prove the model that predicted any row or that future labels were purged.
    """
    output = dict(schemaVersion=1, audit='PHASE7_INFERRED_FREQAI_TEMPORAL_LINEAGE',
        research_lineage_consistent=False, per_prediction_model_verified=False,
        purged_label_horizon_verified=False, oos_certified=False,
        ai_promotion_eligible=False, ready_for_360=False,
        full_core_parity_certified=False, live_orders_enabled=False, errors=[],
        blockers=['NO_PER_PREDICTION_MODEL_ARTIFACT_ID',
            'NO_OBSERVED_TRAINING_FEATURE_AND_LABEL_CUTOFF',
            'NO_INDEPENDENT_PURGED_HORIZON_EVIDENCE',
            'NO_INDEPENDENT_OOS_TRADING_AND_LIQUIDATION_EVIDENCE'],
        interpretation=('Fold indices are candidates inferred from train-log timestamps, '
            'NOT attested FreqAI model IDs or purged-label proof.'))
    try:
        root = Path(root_dir)
        config_file = Path(config_path)
        phase6 = json_data(root / 'paper/phase6-research-readiness.json')
        require(phase6.get('research_report_verified') is True and
            phase6.get('oos_certified') is False and
            phase6.get('ready_for_360') is False and
            phase6.get('full_core_parity_certified') is False,
            'PHASE6_READINESS_NOT_VERIFIED')
        config = json_data(config_file)
        settings = config.get('freqai')
        require(isinstance(settings, dict) and settings.get('enabled') is True,
                'INVALID_FREQAI_RESEARCH_CONFIG')
        horizon = settings.get('feature_parameters', {}).get('label_period_candles')
        require(type(horizon) is int and 1 <= horizon <= 48, 'INVALID_LABEL_HORIZON')
        train_days = settings.get('train_period_days')
        backtest_days = settings.get('backtest_period_days')
        require(type(train_days) is int and train_days >= 1 and
                type(backtest_days) is int and backtest_days >= 1,
                'INVALID_TRAIN_PERIOD_CONFIG')
        model = settings.get('identifier')
        require(isinstance(model, str) and bool(model), 'INVALID_MODEL_IDENTIFIER')
        native = json_data(root / 'native/native-research-180.json')
        predictions = root / 'native/freqai-native-predictions.csv'
        native_log = root / 'native/freqai-native-180.log'
        require(native.get('core_native_runtime_succeeded') is True and
                native.get('freqai_native_runtime_succeeded') is True and
                native.get('prediction_capture_verified') is True and
                native.get('full_core_parity_certified') is False and
                native.get('freqai_oos_verified') is False,
                'INVALID_NATIVE_RESEARCH_STATUS')
        require(native.get('prediction_capture_sha256') == digest(predictions),
                'NATIVE_PREDICTION_SHA_MISMATCH')
        require(native.get('prediction_model_identifier') == model,
                'PREDICTION_MODEL_IDENTIFIER_MISMATCH')
        windows = training_windows(native_log, train_days, backtest_days)
        require(phase6.get('freqai', {}).get('training_windows_observed') == len(windows),
                'PHASE6_TRAIN_WINDOW_COUNT_MISMATCH')
        ends = [w['training_end_ms'] for w in windows]
        counts = [0 for _ in windows]
        accepted, total, boundary_count, abstain = 0, 0, 0, 0
        seen = set()
        with predictions.open(newline='', encoding='utf8') as stream:
            reader = csv.DictReader(stream)
            required = {'open_time', 'predicted_return', 'do_predict',
                        'model_identifier', 'source', 'pair'}
            require(reader.fieldnames is not None and required.issubset(reader.fieldnames),
                    'MISSING_PREDICTION_COLUMNS')
            for row in reader:
                require(None not in row and all(v is not None for v in row.values()),
                        'MALFORMED_PREDICTION_ROW')
                opened = timestamp(row['open_time'])
                require(opened not in seen, 'DUPLICATE_NATIVE_PREDICTION_TIME')
                seen.add(opened)
                total += 1
                require(row['model_identifier'] == model,
                        'PREDICTION_MODEL_IDENTIFIER_MISMATCH')
                require(row['source'] == 'freqai-native-backtest' and
                        row['pair'] == 'BTC/USDT:USDT', 'INVALID_FREQAI_SOURCE')
                require(row['do_predict'] in ('1', '0', '-1', '-2'),
                        'INVALID_FREQAI_DO_PREDICT')
                if row['do_predict'] != '1':
                    require(not row['predicted_return'], 'REJECTED_WITH_FORECAST_VALUE')
                    abstain += 1
                    continue
                require(bool(row['predicted_return']), 'ACCEPTED_WITHOUT_FORECAST')
                fold_idx = bisect_right(ends, opened) - 1
                require(fold_idx >= 0, 'ACCEPTED_BEFORE_FIRST_TRAIN_CUTOFF')
                require(opened < ends[fold_idx] + backtest_days * DAY_MS,
                        'ACCEPTED_OUTSIDE_INFERRED_TEST_WINDOW')
                counts[fold_idx] += 1
                accepted += 1
                if opened < ends[fold_idx] + horizon * M15_MS:
                    boundary_count += 1
                    windows[fold_idx]['accepted_near_cutoff'] += 1
                windows[fold_idx]['tentative_prediction_count'] += 1
        require(type(native.get('prediction_capture_rows')) is int and
                total == native['prediction_capture_rows'] and
                type(native.get('prediction_capture_accepted')) is int and
                accepted == native['prediction_capture_accepted'] and
                accepted == phase6.get('freqai', {}).get('accepted_forecasts'),
                'NATIVE_PREDICTION_COUNT_MISMATCH')
        output.update(research_lineage_consistent=True, total_captured_rows=total,
            accepted_forecasts=accepted, abstentions=abstain,
            observed_train_windows=len(windows),
            configured_label_horizon_candles=horizon,
            label_horizon_minutes=15 * horizon,
            boundary_horizon_forecasts=boundary_count,
            tentative_fold_counts=counts, tentative_fold_windows=windows,
            evidence_sha256=dict(predictions=digest(predictions),
                native_log=digest(native_log), config=digest(config_file)))
    except EvidenceError as exc:
        output['errors'].append(str(exc))
    except (OSError, UnicodeError, ValueError, TypeError, KeyError, csv.Error) as exc:
        output['errors'].append('MISSING_OR_MALFORMED_EVIDENCE')
        output['evidence_error_type'] = type(exc).__name__
    return output

def main():
    parser = argparse.ArgumentParser(description='Offline FreqAI temporal lineage diagnostics')
    parser.add_argument('--artifacts-root', required=True)
    parser.add_argument('--config', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    result = inspect_lineage(args.artifacts_root, args.config)
    dest = Path(args.out)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False)+'\n',
                    encoding='utf8')
    print(json.dumps({k:result[k] for k in
        ('research_lineage_consistent', 'accepted_forecasts',
         'boundary_horizon_forecasts', 'per_prediction_model_verified',
         'oos_certified', 'ready_for_360', 'errors') if k in result}, sort_keys=True))
    return 0 if result['research_lineage_consistent'] else 2

if __name__ == '__main__':
    raise SystemExit(main())
