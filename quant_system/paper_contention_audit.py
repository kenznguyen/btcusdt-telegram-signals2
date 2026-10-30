"""Offline post-Phase-4 source contention audit, never a trading authorization.

Measures observed CORE_ONLY entry timestamps absent in DUAL and whether an AI
position filled in DUAL occupied the single shared slot. This does not measure
all raw CORE signals and cannot prove out-of-sample performance or trade parity.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

ENTRY_KINDS = ('LONG ENTRY', 'SHORT ENTRY')
EXIT_KINDS = ('TAKE PROFIT', 'SOFT SL', 'EMERGENCY SL')


class ContentionError(ValueError):
    pass


def require(condition, reason):
    if not condition:
        raise ContentionError(reason)


def read_json(path):
    obj = json.loads(path.read_text(encoding='utf8'))
    require(isinstance(obj, dict), 'INVALID_REPORT')
    return obj


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b''):
            h.update(chunk)
    return 'sha256:' + h.hexdigest()


def read_events(path):
    with path.open(newline='', encoding='utf8') as file:
        reader = csv.DictReader(file)
        require(reader.fieldnames and set(('kind','origin','trade_id','decision_at_ms',
                'filled_at_ms','side')).issubset(reader.fieldnames), 'MISSING_EVENT_COLUMNS')
        rows = list(reader)
    require(all(None not in row and all(value is not None for value in row.values())
                for row in rows), 'INVALID_EVENT_CSV')
    return rows


def timestamp(value):
    try:
        number = int(value)
        require(str(number) == str(value) and number >= 0, 'INVALID_EVENT_TIMESTAMP')
        return number
    except (ValueError, TypeError, OverflowError) as exc:
        raise ContentionError('INVALID_EVENT_TIMESTAMP') from exc


def parse_entries(rows, mode):
    entries = []
    for row in rows:
        kind = row['kind']
        require(kind in ENTRY_KINDS + EXIT_KINDS + ('DCA',), 'UNKNOWN_EVENT_KIND')
        require(row['origin'] in ('AI','CORE'), 'INVALID_EVENT_ORIGIN')
        require(row['side'] in ('LONG','SHORT') and bool(row['trade_id']),
                'INVALID_EVENT_IDENTITY')
        if mode == 'CORE_ONLY':
            require(row['origin'] == 'CORE', 'INVALID_CORE_ONLY_ORIGIN')
        if mode == 'AI_ONLY':
            require(row['origin'] == 'AI', 'INVALID_AI_ONLY_ORIGIN')
        if kind in ENTRY_KINDS:
            require(kind.split()[0] == row['side'], 'ENTRY_DIRECTION_MISMATCH')
            require(timestamp(row['decision_at_ms']) <= timestamp(row['filled_at_ms']),
                    'INVALID_EVENT_TIMESTAMP')
            entries.append(row)
    return entries


def build_intervals(rows):
    """Half-open intervals of actual DUAL simulated fills."""
    intervals = []
    active = None
    last_fill = -1
    for row in rows:
        filled = timestamp(row['filled_at_ms'])
        require(filled >= last_fill, 'DUAL_POSITION_LIFECYCLE_INVALID')
        last_fill = filled
        kind = row['kind']
        if kind in ENTRY_KINDS:
            require(active is None, 'DUAL_POSITION_LIFECYCLE_INVALID')
            active = dict(start=filled, origin=row['origin'], side=row['side'],
                          trade_id=row['trade_id'])
        elif kind in EXIT_KINDS:
            require(active is not None and active['trade_id'] == row['trade_id'],
                    'DUAL_POSITION_LIFECYCLE_INVALID')
            require(active['origin'] == row['origin'] and active['side'] == row['side'],
                    'DUAL_POSITION_LIFECYCLE_INVALID')
            intervals.append(dict(active, end=filled))
            active = None
        elif kind == 'DCA':
            require(active is not None and active['trade_id'] == row['trade_id'] and
                    active['origin'] == row['origin'] and active['side'] == row['side'],
                    'DUAL_POSITION_LIFECYCLE_INVALID')
        else:
            raise ContentionError('UNKNOWN_EVENT_KIND')
    if active is not None:
        intervals.append(dict(active, end=None))
    return intervals


def audit_contention(directory):
    result = dict(schemaVersion=1, audit='PHASE5_PAPER_SOURCE_CONTENTION',
                  contention_audit_verified=False, ready_for_360=False,
                  full_core_parity_certified=False, live_orders_enabled=False,
                  errors=[], interpretation='Observed CORE_ONLY entries vs DUAL position intervals; '
                  'not all raw CORE signals or native Freqtrade trade parity.')
    try:
        folder = Path(directory)
        upstream = read_json(folder / 'paper-180-independent-audit.json')
        require(upstream.get('artifact_integrity_verified') is True and
                upstream.get('ready_for_360') is False and
                upstream.get('full_core_parity_certified') is False,
                'PHASE4_AUDIT_NOT_VERIFIED')
        files = ['paper-180-summary.json','paper-core-only-events.csv',
                 'paper-ai-only-events.csv','paper-dual-events.csv']
        hashes = upstream.get('artifact_sha256') or {}
        require(all(hashes.get(f) == digest(folder / f) for f in files),
                'ARTIFACT_CHANGED_AFTER_PHASE4_AUDIT')
        summary = read_json(folder / files[0])
        require(summary.get('phase') == 'PAPER_180_ONLY' and
                summary.get('paper_trade_bearing_verified') is True,
                'NO_VALID_180_PAPER_REPORT')
        core = read_events(folder / files[1])
        ai = read_events(folder / files[2])
        dual = read_events(folder / files[3])
        core_entries = parse_entries(core, 'CORE_ONLY')
        ai_entries = parse_entries(ai, 'AI_ONLY')
        dual_entries = parse_entries(dual, 'DUAL')
        intervals = build_intervals(dual)
        dual_core = {timestamp(x['decision_at_ms']) for x in dual_entries
                     if x['origin'] == 'CORE'}
        core_times = {timestamp(x['decision_at_ms']) for x in core_entries}
        require(len(core_times) == len(core_entries) and len(dual_core) == sum(
                x['origin'] == 'CORE' for x in dual_entries), 'DUPLICATE_ENTRY_TIMESTAMPS')
        counts = {'CORE':0,'AI':0}
        for entry in dual_entries:
            counts[entry['origin']] += 1
        breakdown = dict(blocked_by_ai=0, blocked_by_core=0,
                         not_explained_by_occupied_slot=0)
        missed = []
        for entry in core_entries:
            ts = timestamp(entry['decision_at_ms'])
            if ts in dual_core:
                continue
            occupying = [i for i in intervals if i['start'] <= ts and
                         (i['end'] is None or ts < i['end'])]
            require(len(occupying) <= 1, 'DUAL_POSITION_LIFECYCLE_INVALID')
            if occupying:
                prior = occupying[0]
                category = 'blocked_by_ai' if prior['origin'] == 'AI' else 'blocked_by_core'
            else:
                prior = None
                category = 'not_explained_by_occupied_slot'
            breakdown[category] += 1
            missed.append(dict(core_decision_at_ms=ts, core_side=entry['side'],
                               classification=category,
                               occupying_origin=prior['origin'] if prior else None,
                               occupying_trade_id=prior['trade_id'] if prior else None))
        result.update(core_only_entries=len(core_entries),
                      ai_only_entries=len(ai_entries), dual_entries=len(dual_entries),
                      dual_entries_by_origin=counts,
                      core_entries_in_dual=len(dual_core & core_times),
                      core_only_entries_absent_from_dual=len(missed),
                      core_entries_blocked_by_ai_position=breakdown['blocked_by_ai'],
                      core_entries_blocked_by_core_position=breakdown['blocked_by_core'],
                      core_entry_absences_unexplained=breakdown['not_explained_by_occupied_slot'],
                      source_conflicts_reported=summary.get('DUAL',{}).get('source_conflicts'),
                      missed_core_only_entries=missed,
                      active_slot_policy='ONE_SHARED_POSITION',
                      contention_audit_verified=True)
    except ContentionError as exc:
        result['errors'].append(str(exc))
    except (OSError, UnicodeError, ValueError, TypeError, KeyError, csv.Error) as exc:
        result['errors'].append('MISSING_OR_MALFORMED_ARTIFACT')
        result['error_type'] = type(exc).__name__
    return result


def main():
    p = argparse.ArgumentParser(description='Offline CORE-vs-AI paper position contention audit')
    p.add_argument('--paper-dir', required=True)
    p.add_argument('--out', required=True)
    args = p.parse_args()
    result = audit_contention(args.paper_dir)
    target = Path(args.out)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, sort_keys=True, indent=2, allow_nan=False) + '\n')
    print(json.dumps({k:result[k] for k in ('contention_audit_verified','errors',
          'ready_for_360','core_entries_blocked_by_ai_position') if k in result},
          sort_keys=True))
    return 0 if result['contention_audit_verified'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
