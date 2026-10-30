"""Independent, offline consistency gate for 180-day CORE/AI/DUAL paper artifacts.

This audits exported *records*, not FreqAI predictive performance, Kotlin parity,
exchange fills, or the provenance of market data beyond supplied SHA attestations.
Never authorizes live trading or the 360-day research workflow.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

MODES = ('CORE_ONLY', 'AI_ONLY', 'DUAL')
EXITS = frozenset(('TAKE PROFIT', 'SOFT SL', 'EMERGENCY SL'))
CERTIFICATION_FLAGS = (
    'full_core_parity_certified', 'exchange_fills_verified',
    'funding_mark_full_coverage_verified', 'kotlin_trace_verified',
    'model_oos_verified', 'freqai_oos_verified', 'native_trade_parity_verified',
    'liquidation_verified', 'native_orders_enabled',
)


class AuditViolation(ValueError):
    """Machine-readable fail-closed reason for an invalid exported artifact."""


def require(condition, code):
    if not condition:
        raise AuditViolation(code)


def finite(value, code, *, lower=None):
    try:
        require(not isinstance(value, bool), code)
        number = float(value)
        require(math.isfinite(number) and (lower is None or number >= lower), code)
        return number
    except (ValueError, TypeError, OverflowError) as exc:
        raise AuditViolation(code) from exc


def count(value):
    require(type(value) is int and value >= 0, 'INVALID_REPORT_COUNT')
    return value


def number_equal(a, b):
    return math.isclose(finite(a, 'INVALID_NUMERIC_EVIDENCE'),
                        finite(b, 'INVALID_NUMERIC_EVIDENCE'), rel_tol=1e-8, abs_tol=1e-6)


def json_file(path):
    data = json.loads(path.read_text(encoding='utf-8'))
    require(isinstance(data, dict), 'INVALID_JSON_REPORT')
    return data


def csv_rows(path, required):
    with path.open(newline='', encoding='utf-8') as stream:
        reader = csv.DictReader(stream)
        require(reader.fieldnames is not None and len(set(reader.fieldnames)) == len(reader.fieldnames),
                'INVALID_CSV_HEADER')
        require(set(required).issubset(reader.fieldnames), 'MISSING_CSV_COLUMNS')
        rows = list(reader)
    require(all(None not in row and all(value is not None for value in row.values()) for row in rows),
            'MALFORMED_CSV_ROW')
    return rows


def sha_file(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return 'sha256:' + digest.hexdigest()


def sha_valid(value):
    return (isinstance(value, str) and len(value) == 71 and value.startswith('sha256:')
            and all(c in '0123456789abcdef' for c in value[7:]))


def no_escalated_claims(record):
    require(all(record.get(key) is not True for key in CERTIFICATION_FLAGS),
            'UNSUPPORTED_CERTIFICATION_CLAIM')


def audit_mode(folder, mode, summary, hashes):
    stem = 'paper-' + mode.lower().replace('_', '-')
    report_path = folder / (stem + '-report.json')
    report = json_file(report_path)
    require(report == summary[mode], 'MODE_REPORT_SUMMARY_MISMATCH')
    require(report.get('mode') == mode and report.get('days') == 180 and
            report.get('exchange') == 'okx' and report.get('symbol') == 'BTC/USDT:USDT',
            'WRONG_MODE_OR_MARKET')
    require(report.get('dataset_sha256') == summary['dataset_sha256'] and
            report.get('detail_sha256') == summary['detail_sha256'], 'MODE_DATASET_SHA_MISMATCH')
    no_escalated_claims(report)

    events_path = folder / (stem + '-events.csv')
    trades_path = folder / (stem + '-trades.csv')
    equity_path = folder / (stem + '-equity.csv')
    events = csv_rows(events_path, ('event_id','kind','origin','side','trade_id',
        'decision_at_ms','confirmed_at_ms','filled_at_ms','expected_fill_price',
        'actual_fill_price','fill_difference','fill_source','quantity_base',
        'margin_usdt','fee_usdt','dataset_sha256','detail_sha256'))
    trades = csv_rows(trades_path, ('trade_id','origin','side','entry_at_ms','exit_at_ms',
        'exit_reason','entry_price','exit_price','dca_count','gross_pnl_usdt',
        'fees_usdt','net_pnl_ex_funding_usdt'))
    equity = csv_rows(equity_path, ('candle_close_ms','equity_mtm_ex_funding_usdt',
        'unrealized_usdt','drawdown_usdt','open_position'))
    require(bool(equity), 'MISSING_EQUITY_SERIES')

    used = set()
    active_id = None
    entries, closed = {}, {}
    dca_count = {}
    last_fill = -1
    fees = 0.
    for event in events:
        event_id, trade_id, kind = event['event_id'], event['trade_id'], event['kind']
        require(bool(event_id) and event_id not in used, 'DUPLICATE_EVENT_ID')
        used.add(event_id)
        require(trade_id and event['origin'] in ('CORE', 'AI') and event['side'] in ('LONG', 'SHORT'),
                'INVALID_EVENT_ORIGIN_OR_SIDE')
        require(mode == 'DUAL' or event['origin'] == ('CORE' if mode == 'CORE_ONLY' else 'AI'),
                'CROSS_MODE_EVENT_ORIGIN')
        require(event['dataset_sha256'] == summary['dataset_sha256'] and
                event['detail_sha256'] == summary['detail_sha256'], 'EVENT_DATASET_SHA_MISMATCH')
        require(event['fill_source'] == 'SIMULATED_OHLCV_5M', 'UNVERIFIED_FILL_SOURCE')
        decision = finite(event['decision_at_ms'], 'INVALID_EVENT_TIME', lower=0)
        confirmed = finite(event['confirmed_at_ms'], 'INVALID_EVENT_TIME', lower=0)
        filled = finite(event['filled_at_ms'], 'INVALID_EVENT_TIME', lower=0)
        require(decision <= confirmed <= filled and filled >= last_fill, 'INVALID_EVENT_TIME')
        last_fill = filled
        expected = finite(event['expected_fill_price'], 'INVALID_FILL_PRICE', lower=1e-12)
        actual = finite(event['actual_fill_price'], 'INVALID_FILL_PRICE', lower=1e-12)
        require(number_equal(actual - expected, event['fill_difference']),
                'FILL_DIFFERENCE_MISMATCH')
        finite(event['quantity_base'], 'INVALID_EVENT_SIZE', lower=1e-12)
        finite(event['margin_usdt'], 'INVALID_EVENT_SIZE', lower=0)
        fees += finite(event['fee_usdt'], 'INVALID_EVENT_FEE', lower=0)
        if kind in ('LONG ENTRY', 'SHORT ENTRY'):
            require(active_id is None and trade_id not in entries, 'OVERLAPPING_OR_DUPLICATE_ENTRY')
            require(kind.split()[0] == event['side'], 'ENTRY_DIRECTION_MISMATCH')
            entries[trade_id] = event
            active_id = trade_id
            dca_count[trade_id] = 0
        elif kind == 'DCA':
            require(active_id == trade_id and dca_count[trade_id] == 0, 'INVALID_DCA_LIFECYCLE')
            require(entries[trade_id]['side'] == event['side'] and
                    entries[trade_id]['origin'] == event['origin'], 'INVALID_DCA_LIFECYCLE')
            dca_count[trade_id] = 1
        elif kind in EXITS:
            require(active_id == trade_id and trade_id not in closed, 'EXIT_WITHOUT_ENTRY')
            require(entries[trade_id]['side'] == event['side'] and
                    entries[trade_id]['origin'] == event['origin'], 'EXIT_WITHOUT_ENTRY')
            closed[trade_id] = event
            active_id = None
        else:
            raise AuditViolation('UNKNOWN_EVENT_KIND')

    require(count(report.get('trade_count_closed')) == len(closed) == len(trades),
            'CLOSED_TRADE_COUNT_MISMATCH')
    require(count(report.get('trade_count_open')) == int(active_id is not None),
            'OPEN_TRADE_COUNT_MISMATCH')
    require(count(report.get('dca_filled')) == sum(dca_count.values()),
            'DCA_COUNT_MISMATCH')
    require(count(report.get('dca_requests')) >=
            count(report.get('dca_risk_denials')) + sum(dca_count.values()),
            'DCA_REQUEST_ACCOUNTING_MISMATCH')
    require(number_equal(fees, report.get('fees_usdt')), 'EVENT_FEE_TOTAL_MISMATCH')
    gross = 0.
    traded = set()
    for trade in trades:
        ident = trade['trade_id']
        require(ident in closed and ident not in traded, 'PHANTOM_OR_DUPLICATE_CLOSED_TRADE')
        traded.add(ident)
        entry, exit_ = entries[ident], closed[ident]
        require(trade['origin'] == entry['origin'] and trade['side'] == entry['side'] and
                trade['exit_reason'] == exit_['kind'], 'TRADE_EVENT_MISMATCH')
        require(number_equal(trade['entry_at_ms'], entry['filled_at_ms']) and
                number_equal(trade['exit_at_ms'], exit_['filled_at_ms']) and
                number_equal(trade['entry_price'], entry['actual_fill_price']) and
                number_equal(trade['exit_price'], exit_['actual_fill_price']), 'TRADE_EVENT_MISMATCH')
        require(str(dca_count[ident]) == str(trade['dca_count']), 'TRADE_DCA_MISMATCH')
        pnl = finite(trade['gross_pnl_usdt'], 'INVALID_TRADE_PNL')
        cost = finite(trade['fees_usdt'], 'INVALID_TRADE_FEE', lower=0)
        require(number_equal(pnl-cost, trade['net_pnl_ex_funding_usdt']),
                'TRADE_NET_PNL_MISMATCH')
        gross += pnl
    require(number_equal(gross, report.get('realized_gross_pnl_usdt')) and
            number_equal(gross - fees, report.get('realized_net_ex_funding_usdt')),
            'REALIZED_PNL_ACCOUNTING_MISMATCH')

    highest = finite(report.get('starting_capital_usdt'), 'INVALID_CAPITAL', lower=1e-12)
    max_drawdown = 0.
    last_time = -1
    for point in equity:
        timestamp = finite(point['candle_close_ms'], 'INVALID_EQUITY_TIME', lower=0)
        require(timestamp > last_time, 'INVALID_EQUITY_TIME')
        last_time = timestamp
        value = finite(point['equity_mtm_ex_funding_usdt'], 'INVALID_EQUITY')
        highest = max(highest, value)
        drawdown = finite(point['drawdown_usdt'], 'INVALID_DRAWDOWN', lower=0)
        require(number_equal(drawdown, highest - value), 'DRAWDOWN_SERIES_MISMATCH')
        max_drawdown = max(max_drawdown, drawdown)
        require(point['open_position'] in ('True', 'False'), 'INVALID_EQUITY_POSITION_FLAG')
    require(number_equal(equity[-1]['equity_mtm_ex_funding_usdt'],
                         report.get('equity_mtm_ex_funding_usdt')) and
            number_equal(max_drawdown, report.get('max_drawdown_ex_funding_usdt')),
            'EQUITY_REPORT_MISMATCH')

    for path in (report_path, events_path, trades_path, equity_path):
        hashes[path.name] = sha_file(path)
    return dict(closed_trades=len(closed), open_trades=int(active_id is not None),
                fill_events=len(events), dca_fills=sum(dca_count.values()),
                emergency_sl_fills=sum(e['kind']=='EMERGENCY SL' for e in events),
                max_drawdown_ex_funding_usdt=max_drawdown,
                realized_net_ex_funding_usdt=finite(report['realized_net_ex_funding_usdt'], 'INVALID_NET_PNL'),
                initial_capital_usdt=finite(report['starting_capital_usdt'], 'INVALID_CAPITAL'))


def audit_180(paper_dir, native_report, prediction_csv):
    """Never elevate a paper integrity audit into an exchange/OOS certificate."""
    outcome = dict(schemaVersion=1, audit='PHASE3_180_ARTIFACT_CONSISTENCY',
                   artifact_integrity_verified=False, ready_for_360=False,
                   full_core_parity_certified=False, live_orders_enabled=False,
                   integrity_errors=[], research_blockers=[
                       'MODEL_OOS_NOT_VERIFIED', 'KOTLIN_NATIVE_TRADE_PARITY_NOT_VERIFIED',
                       'FUNDING_MARK_LIQUIDATION_NOT_VERIFIED', 'EXCHANGE_FILLS_NOT_VERIFIED',
                       'INDEPENDENT_OPERATOR_REVIEW_REQUIRED',
                   ], modes={}, artifact_sha256={})
    try:
        root = Path(paper_dir)
        summary_path = root / 'paper-180-summary.json'
        summary = json_file(summary_path)
        require(summary.get('schemaVersion') == 1 and summary.get('phase') == 'PAPER_180_ONLY' and
                summary.get('exchange') == 'okx' and
                summary.get('trading_mode') == 'OFFLINE_RESEARCH_NO_EXCHANGE_ORDERS' and
                summary.get('ohlcv_verified') is True, 'INVALID_PAPER_180_SUMMARY')
        no_escalated_claims(summary)
        require(sha_valid(summary.get('dataset_sha256')) and
                sha_valid(summary.get('detail_sha256')) and
                sha_valid(summary.get('prediction_capture_sha256')), 'INVALID_SOURCE_SHA')
        native = json_file(Path(native_report))
        require(native.get('exchange') == 'okx' and native.get('days') == 180 and
                native.get('detail_timeframe') == '5m' and
                native.get('core_native_runtime_succeeded') is True and
                native.get('freqai_native_runtime_succeeded') is True and
                native.get('prediction_capture_verified') is True and
                isinstance(native.get('prediction_model_identifier'), str) and
                bool(native['prediction_model_identifier']) and
                type(native.get('prediction_capture_accepted')) is int and
                native['prediction_capture_accepted'] > 0, 'INVALID_NATIVE_RESEARCH_EVIDENCE')
        require(native.get('dataset_sha256') == summary['dataset_sha256'] and
                native.get('detail_sha256') == summary['detail_sha256'], 'NATIVE_SOURCE_SHA_MISMATCH')
        prediction_sha = sha_file(Path(prediction_csv))
        require(prediction_sha == native.get('prediction_capture_sha256') ==
                summary['prediction_capture_sha256'], 'PREDICTION_SHA_MISMATCH')
        for mode in MODES:
            require(isinstance(summary.get(mode), dict), 'MISSING_MODE_REPORT')
            outcome['modes'][mode] = audit_mode(root, mode, summary, outcome['artifact_sha256'])
        require(summary.get('paper_trade_bearing_verified') is True and
                outcome['modes']['CORE_ONLY']['closed_trades'] > 0 and
                outcome['modes']['AI_ONLY']['closed_trades'] > 0,
                'PAPER_TRADE_BEARING_UNVERIFIED')
        outcome['artifact_sha256'][summary_path.name] = sha_file(summary_path)
        outcome['artifact_sha256'][Path(native_report).name] = sha_file(Path(native_report))
        outcome['artifact_sha256'][Path(prediction_csv).name] = prediction_sha
        if sum(x['dca_fills'] for x in outcome['modes'].values()) == 0:
            outcome['research_blockers'].append('MARKET_DCA_NOT_OBSERVED')
        if sum(x['emergency_sl_fills'] for x in outcome['modes'].values()) == 0:
            outcome['research_blockers'].append('MARKET_EMERGENCY_SL_NOT_OBSERVED')
        for mode in ('AI_ONLY', 'DUAL'):
            stats = outcome['modes'][mode]
            if stats['max_drawdown_ex_funding_usdt'] >= .5 * stats['initial_capital_usdt']:
                outcome['research_blockers'].append(mode+'_HIGH_DRAWDOWN')
        outcome['artifact_integrity_verified'] = True
    except AuditViolation as error:
        outcome['integrity_errors'].append(str(error))
    except (OSError, UnicodeError, ValueError, TypeError, KeyError, csv.Error) as error:
        outcome['integrity_errors'].append('MISSING_OR_MALFORMED_EVIDENCE')
        outcome['evidence_error_type'] = type(error).__name__
    return outcome


def main():
    parser = argparse.ArgumentParser(description='Independent 180d PAPER artifact integrity check; never live')
    parser.add_argument('--paper-dir', required=True)
    parser.add_argument('--native-report', required=True)
    parser.add_argument('--predictions', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    result = audit_180(args.paper_dir, args.native_report, args.predictions)
    dest = Path(args.out)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False)+'\n', encoding='utf-8')
    print(json.dumps({k: result[k] for k in ('artifact_integrity_verified',
                                            'ready_for_360','integrity_errors','research_blockers')},
                     sort_keys=True))
    return 0 if result['artifact_integrity_verified'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
