"""Synthetic Phase 5 source contention regression; no live or historical claims."""
import csv
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from quant_system.paper_contention_audit import audit_contention


def write(path, rows):
    with path.open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def fixture(directory):
    root = Path(directory)
    summary = dict(phase='PAPER_180_ONLY', paper_trade_bearing_verified=True,
        CORE_ONLY={'trade_count_closed':2}, AI_ONLY={'trade_count_closed':1},
        DUAL={'trade_count_closed':1,'source_conflicts':0})
    (root/'paper-180-summary.json').write_text(json.dumps(summary))
    def event(kind, origin, trade, decided, filled, side):
        return dict(kind=kind,origin=origin,trade_id=trade,
                    decision_at_ms=decided,filled_at_ms=filled,side=side)
    core = [event('LONG ENTRY','CORE','c1',900000,900000,'LONG'),
            event('TAKE PROFIT','CORE','c1',1800000,1800000,'LONG'),
            event('SHORT ENTRY','CORE','c2',2700000,2700000,'SHORT'),
            event('TAKE PROFIT','CORE','c2',3600000,3600000,'SHORT')]
    ai = [event('SHORT ENTRY','AI','a1',0,0,'SHORT'),
          event('TAKE PROFIT','AI','a1',1800000,1800000,'SHORT')]
    dual = ai + core[2:]
    for mode,events in [('core-only',core),('ai-only',ai),('dual',dual)]:
        write(root/f'paper-{mode}-events.csv',events)
    names=['paper-180-summary.json','paper-core-only-events.csv',
           'paper-ai-only-events.csv','paper-dual-events.csv']
    hashes={name:'sha256:'+hashlib.sha256((root/name).read_bytes()).hexdigest()
            for name in names}
    upstream=dict(artifact_integrity_verified=True,ready_for_360=False,
                  full_core_parity_certified=False,artifact_sha256=hashes)
    (root/'paper-180-independent-audit.json').write_text(json.dumps(upstream))
    return root


class PaperContentionAuditTest(unittest.TestCase):
    def test_ai_occupancy_blocks_one_core_only_entry_without_source_conflict(self):
        with tempfile.TemporaryDirectory() as directory:
            audit=audit_contention(fixture(directory))
            self.assertTrue(audit['contention_audit_verified'], audit)
            self.assertEqual(audit['core_only_entries'],2)
            self.assertEqual(audit['core_entries_in_dual'],1)
            self.assertEqual(audit['core_entries_blocked_by_ai_position'],1)
            self.assertEqual(audit['dual_entries_by_origin'],{'CORE':1,'AI':1})
            self.assertEqual(audit['source_conflicts_reported'],0)
            self.assertFalse(audit['ready_for_360'])
            self.assertFalse(audit['full_core_parity_certified'])

    def test_tamper_after_phase4_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root=fixture(directory)
            with (root/'paper-dual-events.csv').open('a') as output:
                output.write('INVALID\\n')
            self.assertIn('ARTIFACT_CHANGED_AFTER_PHASE4_AUDIT',
                          audit_contention(root)['errors'])

    def test_upstream_audit_must_have_passed(self):
        with tempfile.TemporaryDirectory() as directory:
            root=fixture(directory)
            file=root/'paper-180-independent-audit.json'
            obj=json.loads(file.read_text())
            obj['artifact_integrity_verified']=False
            file.write_text(json.dumps(obj))
            self.assertIn('PHASE4_AUDIT_NOT_VERIFIED',audit_contention(root)['errors'])

    def test_reversed_dual_fill_timestamps_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root=fixture(directory)
            file=root/'paper-dual-events.csv'
            with file.open(newline='') as input_file:
                rows=list(csv.DictReader(input_file))
            rows[1]['filled_at_ms']='3000000'
            write(file,rows)
            upstream=root/'paper-180-independent-audit.json'
            obj=json.loads(upstream.read_text())
            obj['artifact_sha256'][file.name]='sha256:'+hashlib.sha256(file.read_bytes()).hexdigest()
            upstream.write_text(json.dumps(obj))
            self.assertIn('DUAL_POSITION_LIFECYCLE_INVALID',
                          audit_contention(root)['errors'])

    def test_missing_upstream_artifact_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root=fixture(directory)
            (root/'paper-180-independent-audit.json').unlink()
            self.assertFalse(audit_contention(root)['contention_audit_verified'])


if __name__=='__main__':
    unittest.main()
